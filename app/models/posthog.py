from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, generate_uuid


class PostHogConnection(Base):
    """Stores PostHog API credentials for event data integration.

    When a user connects their PostHog account, we store the credentials here.
    This enables the event query tool — when a user asks about events,
    we can fetch live data from PostHog.
    """

    __tablename__ = "posthog_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    api_key: Mapped[str] = mapped_column(Text, nullable=False)  # Personal API key (phx_...)
    project_id: Mapped[str] = mapped_column(String(50), nullable=False)
    api_host: Mapped[str] = mapped_column(
        String(255), nullable=False, default="https://us.i.posthog.com"
    )
    project_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
