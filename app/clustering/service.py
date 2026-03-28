"""Clustering service — orchestrates clustering runs and persists results."""

import json
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.cluster import ClusterAssignment, ClusterRun
from app.models.persona import Persona


async def _get_all_personas_with_entities(db: AsyncSession) -> list:
    """Fetch all personas with their entities as dicts."""
    result = await db.execute(select(Persona))
    personas = result.scalars().all()

    persona_dicts = []
    for p in personas:
        entities = []
        for e in p.entities:
            entities.append({"key": e.key, "value": e.value})
        persona_dicts.append({
            "id": p.id,
            "distinct_id": p.distinct_id,
            "name": p.name,
            "entities": entities,
        })

    return persona_dicts


async def run_clustering_from_db(
    algorithm: str = "kmeans", params: Optional[Dict] = None
) -> Dict[str, Any]:
    """Run clustering on all personas in the database and store results."""
    from app.clustering.engine import (
        find_optimal_k,
        run_hdbscan,
        run_kmeans,
        run_kprototypes,
    )

    params = params or {}

    async with async_session() as db:
        personas = await _get_all_personas_with_entities(db)

        if len(personas) < 2:
            raise ValueError("Need at least 2 personas with entities to cluster")

        # Run the selected algorithm
        if algorithm == "kmeans":
            if "n_clusters" not in params:
                optimal = find_optimal_k(personas)
                params["n_clusters"] = optimal["optimal_k"]
            result = run_kmeans(personas, **params)
        elif algorithm == "hdbscan":
            result = run_hdbscan(personas, **params)
        elif algorithm == "kprototypes":
            if "n_clusters" not in params:
                optimal = find_optimal_k(personas)
                params["n_clusters"] = optimal["optimal_k"]
            result = run_kprototypes(personas, **params)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        # Build cluster groups for NER + LLM summarization
        personas_by_id = {p["id"]: p for p in personas}
        cluster_groups: Dict[int, Any] = {}
        for persona_id, label in zip(result["persona_ids"], result["labels"]):
            if label not in cluster_groups:
                cluster_groups[label] = {
                    "name": result["cluster_names"].get(label, f"Cluster {label}"),
                    "member_ids": [],
                }
            cluster_groups[label]["member_ids"].append(persona_id)

        # NER + LLM summarization (gracefully skipped if no API key)
        from app.clustering.llm import summarize_clusters
        summaries = summarize_clusters(cluster_groups, personas_by_id)

        # Store the run
        run = ClusterRun(
            algorithm=result["algorithm"],
            params=json.dumps(result["params"]),
            num_clusters=result["num_clusters"],
            num_personas=len(personas),
            silhouette_score=str(result["metrics"].get("silhouette_score", ""))
            if result.get("metrics")
            else None,
            calinski_harabasz=str(result["metrics"].get("calinski_harabasz", ""))
            if result.get("metrics")
            else None,
            davies_bouldin=str(result["metrics"].get("davies_bouldin", ""))
            if result.get("metrics")
            else None,
            cluster_summaries=json.dumps({str(k): v for k, v in summaries.items()}) if summaries else None,
        )
        db.add(run)
        await db.flush()

        # Store assignments — use LLM name if available, fall back to auto-generated
        for persona_id, label in zip(result["persona_ids"], result["labels"]):
            llm_result = summaries.get(label, {})
            cluster_name = (
                llm_result.get("name")
                or result["cluster_names"].get(label, f"Cluster {label}")
            )
            assignment = ClusterAssignment(
                run_id=run.id,
                persona_id=persona_id,
                cluster_label=label,
                cluster_name=cluster_name,
            )
            db.add(assignment)

        await db.commit()

        return {
            "run_id": run.id,
            "algorithm": result["algorithm"],
            "num_clusters": result["num_clusters"],
            "num_personas": len(personas),
            "metrics": result.get("metrics", {}),
            "cluster_names": {
                label: (summaries.get(label, {}).get("name") or name)
                for label, name in result["cluster_names"].items()
            },
            "cluster_summaries": summaries,
        }
