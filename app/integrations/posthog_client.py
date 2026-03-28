"""PostHog API client for fetching persons and events.

Matches Tenera's PostHog integration pattern:
- Bearer token auth with personal API key
- Supports US, EU, and self-hosted instances
- Fetches persons, events, and person properties
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30


class PostHogClient:
    """Client for PostHog REST API."""

    def __init__(self, api_key: str, project_id: str, api_host: str = "https://us.i.posthog.com"):
        self.api_key = api_key
        self.project_id = project_id
        self.api_host = api_host.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.api_host}/api/projects/{self.project_id}{path}"

    async def validate(self) -> Dict[str, Any]:
        """Validate the connection by fetching project info."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(
                f"{self.api_host}/api/projects/{self.project_id}/",
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return {"id": data.get("id"), "name": data.get("name", "Unknown")}

    async def get_persons(
        self,
        search: Optional[str] = None,
        distinct_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch persons from PostHog."""
        params = {"limit": limit}
        if search:
            params["search"] = search
        if distinct_id:
            params["distinct_id"] = distinct_id

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(
                self._url("/persons/"), headers=self._headers, params=params
            )
            resp.raise_for_status()
            return resp.json().get("results", [])

    async def get_person_by_distinct_id(self, distinct_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single person by their distinct_id."""
        persons = await self.get_persons(distinct_id=distinct_id)
        return persons[0] if persons else None

    async def get_events(
        self,
        distinct_id: Optional[str] = None,
        event: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch events from PostHog.

        Args:
            distinct_id: Filter by user's distinct_id
            event: Filter by event name (e.g. "$pageview")
            after: ISO 8601 datetime — events after this time
            before: ISO 8601 datetime — events before this time
            limit: Max results (PostHog max is 100 per page)
        """
        params = {"limit": min(limit, 100)}
        if distinct_id:
            params["distinct_id"] = distinct_id
        if event:
            params["event"] = event
        if after:
            params["after"] = after
        if before:
            params["before"] = before

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(
                self._url("/events/"), headers=self._headers, params=params
            )
            resp.raise_for_status()
            return resp.json().get("results", [])

    async def get_event_definitions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch event definitions (list of event names in the project)."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(
                self._url("/event_definitions/"),
                headers=self._headers,
                params={"limit": limit},
            )
            resp.raise_for_status()
            return resp.json().get("results", [])

    async def hogql_query(self, query: str) -> List[List[Any]]:
        """Execute a HogQL query (PostHog's SQL-like query language)."""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                self._url("/query/"),
                headers=self._headers,
                json={"query": {"kind": "HogQLQuery", "query": query}},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
