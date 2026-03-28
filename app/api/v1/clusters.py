"""Clustering API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.models.cluster import ClusterAssignment, ClusterRun
from app.models.persona import Persona
from app.schemas.cluster import (
    ClusterAssignmentResponse,
    ClusterRunRequest,
    ClusterRunResponse,
    ClusterRunSummary,
    ScheduleRequest,
    ScheduleResponse,
)

router = APIRouter(prefix="/clusters", tags=["clusters"], dependencies=[Depends(verify_api_key)])


@router.post("/run", response_model=dict, status_code=201)
async def trigger_clustering(body: ClusterRunRequest):
    """Trigger a clustering run on all personas."""
    from app.clustering.service import run_clustering_from_db

    try:
        result = await run_clustering_from_db(
            algorithm=body.algorithm, params=body.params or {}
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/runs", response_model=List[ClusterRunSummary])
async def list_runs(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List past clustering runs."""
    result = await db.execute(
        select(ClusterRun).order_by(ClusterRun.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.get("/latest", response_model=Optional[ClusterRunResponse])
async def get_latest_run(db: AsyncSession = Depends(get_db)):
    """Get the most recent clustering run with assignments."""
    result = await db.execute(
        select(ClusterRun).order_by(ClusterRun.created_at.desc()).limit(1)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="No clustering runs found")

    return await _enrich_run(run, db)


@router.get("/runs/{run_id}", response_model=ClusterRunResponse)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific clustering run with assignments."""
    run = await db.get(ClusterRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return await _enrich_run(run, db)


async def _enrich_run(run: ClusterRun, db: AsyncSession) -> ClusterRunResponse:
    """Enrich cluster assignments with persona details."""
    enriched_assignments = []
    for a in run.assignments:
        persona = await db.get(Persona, a.persona_id)
        enriched_assignments.append(
            ClusterAssignmentResponse(
                persona_id=a.persona_id,
                distinct_id=persona.distinct_id if persona else None,
                persona_name=persona.name if persona else None,
                cluster_label=a.cluster_label,
                cluster_name=a.cluster_name,
            )
        )

    return ClusterRunResponse(
        id=run.id,
        algorithm=run.algorithm,
        params=run.params,
        num_clusters=run.num_clusters,
        num_personas=run.num_personas,
        silhouette_score=run.silhouette_score,
        calinski_harabasz=run.calinski_harabasz,
        davies_bouldin=run.davies_bouldin,
        created_at=run.created_at,
        assignments=enriched_assignments,
    )


# --- Schedule ---


@router.get("/schedule", response_model=ScheduleResponse)
async def get_schedule():
    """Get the current clustering schedule."""
    from app.clustering.scheduler import get_schedule

    return get_schedule()


@router.post("/schedule", response_model=ScheduleResponse)
async def set_schedule(body: ScheduleRequest):
    """Set or update the clustering cron schedule."""
    from app.clustering.scheduler import update_schedule

    try:
        config = update_schedule(body.cron, body.algorithm, body.params)
        return config
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/schedule", response_model=ScheduleResponse)
async def delete_schedule():
    """Disable the clustering schedule."""
    from app.clustering.scheduler import disable_schedule

    config = disable_schedule()
    return config
