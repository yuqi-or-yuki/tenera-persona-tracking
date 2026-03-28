from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class Entity(Base, TimestampMixin):
    """An entity is an arbitrary key-value property attached to a persona.

    Entities are the building blocks for persona profiles. The key can be anything
    (e.g. "plan", "company", "role", "favorite_color") and the value can be any string.
    Each key is unique per persona — setting the same key again overwrites the value.

    Unlike PostHog's JSONB approach, entities are stored as individual rows so we can
    track when each property was set/changed via timestamps.
    """

    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    persona_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    persona: Mapped["Persona"] = relationship("Persona", back_populates="entities")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("persona_id", "key", name="uq_persona_entity_key"),
    )
