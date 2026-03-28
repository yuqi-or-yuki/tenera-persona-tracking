from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ClusterRunRequest(BaseModel):
    algorithm: str = Field(default="kmeans", description="kmeans, hdbscan, or kprototypes")
    params: Optional[Dict[str, Any]] = Field(
        default=None, description="Algorithm params (e.g. n_clusters, min_cluster_size)"
    )


class ClusterAssignmentResponse(BaseModel):
    persona_id: str
    distinct_id: Optional[str] = None
    persona_name: Optional[str] = None
    cluster_label: int
    cluster_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ClusterRunResponse(BaseModel):
    id: str
    algorithm: str
    params: Optional[str] = None
    num_clusters: int
    num_personas: int
    silhouette_score: Optional[str] = None
    calinski_harabasz: Optional[str] = None
    davies_bouldin: Optional[str] = None
    created_at: datetime
    assignments: List[ClusterAssignmentResponse] = []

    model_config = {"from_attributes": True}


class ClusterRunSummary(BaseModel):
    id: str
    algorithm: str
    num_clusters: int
    num_personas: int
    silhouette_score: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduleRequest(BaseModel):
    cron: str = Field(..., examples=["0 2 * * *"], description="Cron expression (5-field)")
    algorithm: str = Field(default="kmeans")
    params: Optional[Dict[str, Any]] = None


class ScheduleResponse(BaseModel):
    enabled: bool
    cron: str
    algorithm: str
    params: Dict[str, Any] = {}
