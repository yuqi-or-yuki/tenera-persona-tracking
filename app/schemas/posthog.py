from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PostHogConnectRequest(BaseModel):
    api_key: str = Field(..., description="PostHog personal API key (phx_...)")
    project_id: str = Field(..., description="PostHog project ID")
    api_host: str = Field(
        default="https://us.i.posthog.com",
        description="PostHog API host (us.i.posthog.com, eu.i.posthog.com, or self-hosted)",
    )


class PostHogConnectionResponse(BaseModel):
    id: str
    project_id: str
    api_host: str
    project_name: Optional[str]
    created_at: datetime
    connected: bool = True

    model_config = {"from_attributes": True}


class PostHogEventsRequest(BaseModel):
    distinct_id: Optional[str] = Field(None, description="Filter by user distinct_id")
    event: Optional[str] = Field(None, description="Filter by event name (e.g. $pageview)")
    after: Optional[str] = Field(None, description="ISO 8601 datetime — events after")
    before: Optional[str] = Field(None, description="ISO 8601 datetime — events before")
    limit: int = Field(default=50, le=100)


class PostHogPersonResponse(BaseModel):
    uuid: Optional[str] = None
    distinct_ids: List[str] = []
    properties: Dict[str, Any] = {}
    created_at: Optional[str] = None


class PostHogEventResponse(BaseModel):
    id: Optional[str] = None
    distinct_id: str
    event: str
    timestamp: str
    properties: Dict[str, Any] = {}


class PostHogStatusResponse(BaseModel):
    connected: bool
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    api_host: Optional[str] = None
