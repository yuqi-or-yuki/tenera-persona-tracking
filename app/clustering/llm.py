"""LLM integration for cluster NER + summarization via litellm.

Pipeline (runs after clustering):
1. NER  — extract named entities (orgs, industries, locations) from member data
2. Name + Summary — LLM generates a short human-readable name and 2-sentence insight

Using litellm so the model is swappable via LLM_MODEL in .env.
"""

import json
import logging
import re
from typing import Any, Dict, List

import litellm

from app.core.config import settings

logger = logging.getLogger(__name__)

litellm.drop_params = True  # ignore unsupported params silently


# ---------------------------------------------------------------------------
# NER helpers (lightweight regex/heuristic — no extra deps)
# ---------------------------------------------------------------------------

_ORG_SUFFIXES = re.compile(
    r"\b(inc\.?|llc\.?|ltd\.?|corp\.?|co\.?|gmbh|ag|plc|group|holdings|technologies|tech|labs|studio|studios|solutions|consulting|services|partners|ventures|capital)\b",
    re.IGNORECASE,
)

_INDUSTRY_KEYWORDS = {
    "tech", "software", "saas", "hardware", "fintech", "healthtech", "edtech",
    "finance", "banking", "insurance", "healthcare", "medical", "pharma",
    "education", "retail", "ecommerce", "logistics", "manufacturing", "media",
    "legal", "government", "nonprofit", "real estate", "energy", "consulting",
}


def _ner_from_entities(members: List[Dict]) -> Dict[str, List[str]]:
    """Extract named entities from persona entity values heuristically."""
    orgs, industries, locations, other = set(), set(), set(), set()

    for m in members:
        for e in m.get("entities", []):
            key = e.get("key", "").lower()
            val = str(e.get("value", "")).strip()

            if not val or val in ("_unknown_", "none", "null"):
                continue

            if key in ("company", "organization", "org", "employer"):
                orgs.add(val)
            elif key in ("industry", "sector", "vertical"):
                industries.add(val)
            elif key in ("country", "region", "city", "location", "state"):
                locations.add(val)
            elif _ORG_SUFFIXES.search(val):
                orgs.add(val)
            elif val.lower() in _INDUSTRY_KEYWORDS:
                industries.add(val)
            elif key not in ("plan", "monthly_spend", "company_size", "mrr", "arr"):
                other.add(f"{key}={val}")

    return {
        "organizations": sorted(orgs),
        "industries": sorted(industries),
        "locations": sorted(locations),
        "other": sorted(other),
    }


# ---------------------------------------------------------------------------
# LLM summarization
# ---------------------------------------------------------------------------


def summarize_clusters(
    clusters: Dict[int, Dict[str, Any]],
    personas_by_id: Dict[str, Dict],
) -> Dict[int, Dict[str, str]]:
    """Generate an LLM name + summary for each cluster.

    Args:
        clusters: {label: {"name": str, "member_ids": [persona_id, ...]}}
        personas_by_id: {persona_id: {"name", "distinct_id", "entities": [...]}}

    Returns:
        {label: {"name": "Short Cohort Name", "summary": "..."}}
    """
    has_key = settings.azure_api_key or settings.anthropic_api_key
    if not has_key:
        logger.warning("No LLM API key set — skipping cluster summaries")
        return {}

    results: Dict[int, Dict[str, str]] = {}

    for label, group in clusters.items():
        members = [
            personas_by_id[pid]
            for pid in group.get("member_ids", [])
            if pid in personas_by_id
        ]
        if not members:
            continue

        ner = _ner_from_entities(members)

        member_lines = []
        for m in members:
            entities_str = ", ".join(
                f"{e['key']}={e['value']}" for e in m.get("entities", [])
            )
            member_lines.append(f"- {m.get('name') or m.get('distinct_id', '?')}: {entities_str}")

        prompt = f"""You are analyzing a B2B SaaS cohort cluster.

Members ({len(members)}):
{chr(10).join(member_lines)}

Named entities extracted (NER):
- Industries: {', '.join(ner['industries']) or 'none'}
- Organizations: {', '.join(ner['organizations']) or 'none'}
- Locations: {', '.join(ner['locations']) or 'none'}
- Other signals: {', '.join(ner['other'][:10]) or 'none'}

Tasks:
1. Give this cohort a short, human-readable name (3-5 words, title case, e.g. "Enterprise Tech Accounts" or "SMB Finance Free Tier").
2. Write a concise 2-sentence business summary. Focus on who they are and one actionable insight (upsell, churn risk, expansion, etc.).

Respond with JSON only: {{"name": "...", "summary": "..."}}"""

        try:
            kwargs = dict(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250,
            )
            if settings.azure_api_key:
                kwargs["api_key"] = settings.azure_api_key
                kwargs["api_base"] = settings.azure_api_base
                kwargs["api_version"] = settings.azure_api_version
            elif settings.anthropic_api_key:
                kwargs["api_key"] = settings.anthropic_api_key
            response = litellm.completion(**kwargs)
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw.strip())
            results[label] = {
                "name": parsed.get("name", group["name"]),
                "summary": parsed.get("summary", ""),
            }
        except Exception as exc:
            logger.error("LLM summarization failed for cluster %s: %s", label, exc)
            results[label] = {"name": group["name"], "summary": ""}

    return results
