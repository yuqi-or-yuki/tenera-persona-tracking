"""Clustering service — orchestrates clustering runs and persists results."""

import json
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.cluster import ClusterAssignment, ClusterRun
from app.models.entity import Entity
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
                # Auto-detect optimal K
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
        )
        db.add(run)
        await db.flush()

        # Store assignments
        for persona_id, label in zip(result["persona_ids"], result["labels"]):
            cluster_name = result["cluster_names"].get(label, f"Cluster {label}")
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
            "cluster_names": result["cluster_names"],
        }
