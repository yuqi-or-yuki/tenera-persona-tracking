from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class Persona(Base, TimestampMixin):
    """A persona represents a tracked identity — a user, customer, or any entity you want to track.

    Similar to PostHog's "Person", but designed as the first-class primitive.
    Each persona has a unique distinct_id (your user ID, email, etc.) and
    can have arbitrary entities (key-value properties) attached to it.
    """

    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    distinct_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    entities: Mapped[list["Entity"]] = relationship(  # noqa: F821
        "Entity", back_populates="persona", cascade="all, delete-orphan", lazy="selectin"
    )
    events: Mapped[list["Event"]] = relationship(  # noqa: F821
        "Event", back_populates="persona", cascade="all, delete-orphan", lazy="selectin"
    )
