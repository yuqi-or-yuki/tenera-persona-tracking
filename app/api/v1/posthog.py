"""PostHog integration API endpoints.

Allows users to connect their PostHog account and query events/persons.
When connected, this acts as a tool that can be activated to answer
questions about user events using live PostHog data.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.integrations.posthog_client import PostHogClient
from app.models.posthog import PostHogConnection
from app.schemas.posthog import (
    PostHogConnectRequest,
    PostHogConnectionResponse,
    PostHogEventResponse,
    PostHogEventsRequest,
    PostHogPersonResponse,
    PostHogStatusResponse,
)

router = APIRouter(
    prefix="/posthog", tags=["posthog"], dependencies=[Depends(verify_api_key)]
)


async def _get_connection(db: AsyncSession) -> PostHogConnection:
    """Get the active PostHog connection or raise 404."""
    result = await db.execute(
        select(PostHogConnection).order_by(PostHogConnection.created_at.desc()).limit(1)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(
            status_code=404,
            detail="PostHog not connected. Use POST /api/v1/posthog/connect first.",
        )
    return conn


def _make_client(conn: PostHogConnection) -> PostHogClient:
    return PostHogClient(
        api_key=conn.api_key, project_id=conn.project_id, api_host=conn.api_host
    )


# --- Connection management ---


@router.get("/status", response_model=PostHogStatusResponse)
async def get_status(db: AsyncSession = Depends(get_db)):
    """Check if PostHog is connected."""
    result = await db.execute(
        select(PostHogConnection).order_by(PostHogConnection.created_at.desc()).limit(1)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        return PostHogStatusResponse(connected=False)
    return PostHogStatusResponse(
        connected=True,
        project_id=conn.project_id,
        project_name=conn.project_name,
        api_host=conn.api_host,
    )


@router.post("/connect", response_model=PostHogConnectionResponse, status_code=201)
async def connect(body: PostHogConnectRequest, db: AsyncSession = Depends(get_db)):
    """Connect to PostHog by validating credentials and storing the connection."""
    client = PostHogClient(
        api_key=body.api_key, project_id=body.project_id, api_host=body.api_host
    )

    # Validate the connection
    try:
        project_info = await client.validate()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to PostHog: {e}",
        )

    # Remove any existing connections (one connection at a time)
    existing = await db.execute(select(PostHogConnection))
    for old in existing.scalars().all():
        await db.delete(old)

    conn = PostHogConnection(
        api_key=body.api_key,
        project_id=body.project_id,
        api_host=body.api_host,
        project_name=project_info.get("name"),
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)

    return conn


@router.delete("/connect", status_code=204)
async def disconnect(db: AsyncSession = Depends(get_db)):
    """Disconnect from PostHog."""
    result = await db.execute(select(PostHogConnection))
    for conn in result.scalars().all():
        await db.delete(conn)
    await db.commit()


# --- Event queries (the "tool" that activates when connected) ---


@router.get("/events", response_model=List[PostHogEventResponse])
async def query_events(
    distinct_id: Optional[str] = Query(None, description="Filter by user distinct_id"),
    event: Optional[str] = Query(None, description="Filter by event name"),
    after: Optional[str] = Query(None, description="ISO 8601 — events after"),
    before: Optional[str] = Query(None, description="ISO 8601 — events before"),
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Query events from PostHog. Only works when connected.

    This is the primary tool endpoint — when a user asks about events,
    this fetches live data from their PostHog instance.
    """
    conn = await _get_connection(db)
    client = _make_client(conn)

    try:
        events = await client.get_events(
            distinct_id=distinct_id, event=event, after=after, before=before, limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"PostHog query failed: {e}")

    return [
        PostHogEventResponse(
            id=e.get("id"),
            distinct_id=e.get("distinct_id", ""),
            event=e.get("event", ""),
            timestamp=e.get("timestamp", ""),
            properties=e.get("properties", {}),
        )
        for e in events
    ]


@router.get("/persons", response_model=List[PostHogPersonResponse])
async def query_persons(
    search: Optional[str] = Query(None, description="Search by distinct_id, email, or name"),
    distinct_id: Optional[str] = Query(None, description="Exact match on distinct_id"),
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Query persons from PostHog."""
    conn = await _get_connection(db)
    client = _make_client(conn)

    try:
        persons = await client.get_persons(
            search=search, distinct_id=distinct_id, limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"PostHog query failed: {e}")

    return [
        PostHogPersonResponse(
            uuid=p.get("uuid"),
            distinct_ids=p.get("distinct_ids", []),
            properties=p.get("properties", {}),
            created_at=p.get("created_at"),
        )
        for p in persons
    ]


@router.get("/event-definitions", response_model=List[dict])
async def get_event_definitions(db: AsyncSession = Depends(get_db)):
    """List all event names defined in the PostHog project."""
    conn = await _get_connection(db)
    client = _make_client(conn)

    try:
        definitions = await client.get_event_definitions()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"PostHog query failed: {e}")

    return [
        {"name": d.get("name", ""), "volume_30_day": d.get("volume_30_day")}
        for d in definitions
    ]


@router.post("/sync", response_model=dict)
async def sync_persons_to_personas(
    limit: int = Query(default=100, le=500, description="Max persons to sync"),
    db: AsyncSession = Depends(get_db),
):
    """Sync PostHog persons into local personas.

    Fetches persons from PostHog and creates/updates corresponding
    personas with their properties as entities. This bridges PostHog
    data into the persona tracking system.
    """
    from app.models.entity import Entity
    from app.models.persona import Persona

    conn = await _get_connection(db)
    client = _make_client(conn)

    try:
        ph_persons = await client.get_persons(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"PostHog query failed: {e}")

    created = 0
    updated = 0

    for ph_person in ph_persons:
        distinct_ids = ph_person.get("distinct_ids", [])
        if not distinct_ids:
            continue

        distinct_id = distinct_ids[0]
        props = ph_person.get("properties", {})

        # Find or create persona
        result = await db.execute(
            select(Persona).where(Persona.distinct_id == distinct_id)
        )
        persona = result.scalar_one_or_none()

        if not persona:
            name = props.get("name") or props.get("email") or distinct_id
            persona = Persona(distinct_id=distinct_id, name=name)
            db.add(persona)
            await db.flush()
            created += 1
        else:
            updated += 1

        # Sync properties as entities (skip internal PostHog props starting with $)
        for key, value in props.items():
            if key.startswith("$") or value is None:
                continue

            str_value = str(value)
            existing = await db.execute(
                select(Entity).where(
                    Entity.persona_id == persona.id, Entity.key == key
                )
            )
            entity = existing.scalar_one_or_none()
            if entity:
                entity.value = str_value
            else:
                db.add(Entity(persona_id=persona.id, key=key, value=str_value))

    await db.commit()

    return {
        "synced": created + updated,
        "created": created,
        "updated": updated,
        "source": f"PostHog ({conn.project_name or conn.project_id})",
    }
