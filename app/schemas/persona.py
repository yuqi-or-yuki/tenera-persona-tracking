from datetime import datetime

from pydantic import BaseModel, Field


# --- Entity schemas ---


class EntitySet(BaseModel):
    """Set one or more key-value entities on a persona."""

    key: str = Field(..., max_length=255, examples=["plan"])
    value: str = Field(..., examples=["enterprise"])


class EntityResponse(BaseModel):
    id: str
    key: str
    value: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Event schemas ---


class EventCreate(BaseModel):
    """Track an event for a persona."""

    event_type: str = Field(..., max_length=255, examples=["page_view"])
    properties: dict | None = Field(default=None, examples=[{"page": "/pricing"}])
    timestamp: datetime | None = Field(
        default=None, description="ISO 8601 timestamp. Defaults to now if omitted."
    )


class EventResponse(BaseModel):
    id: str
    event_type: str
    properties: dict | None = None
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- Persona schemas ---


class PersonaCreate(BaseModel):
    """Create a new persona (tracked identity)."""

    distinct_id: str = Field(
        ..., max_length=255, description="Your unique user identifier (user ID, email, etc.)"
    )
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    entities: list[EntitySet] | None = Field(
        default=None, description="Initial key-value entities to set on the persona."
    )


class PersonaUpdate(BaseModel):
    """Update a persona's core fields."""

    name: str | None = None
    description: str | None = None


class PersonaResponse(BaseModel):
    id: str
    distinct_id: str
    name: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime
    entities: list[EntityResponse] = []

    model_config = {"from_attributes": True}


class PersonaListResponse(BaseModel):
    results: list[PersonaResponse]
    count: int
