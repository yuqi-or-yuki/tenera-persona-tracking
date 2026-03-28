from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid


class ClusterRun(Base):
    """A clustering run — one execution of a clustering algorithm."""

    __tablename__ = "cluster_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)  # kmeans, hdbscan, kprototypes
    params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string of params
    num_clusters: Mapped[int] = mapped_column(Integer, nullable=False)
    num_personas: Mapped[int] = mapped_column(Integer, nullable=False)
    silhouette_score: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    calinski_harabasz: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    davies_bouldin: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    cluster_summaries: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: {"label": "summary"}
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    assignments: Mapped[List["ClusterAssignment"]] = relationship(
        "ClusterAssignment", back_populates="run", cascade="all, delete-orphan", lazy="selectin"
    )


class ClusterAssignment(Base):
    """Maps a persona to a cluster within a run."""

    __tablename__ = "cluster_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cluster_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    persona_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cluster_label: Mapped[int] = mapped_column(Integer, nullable=False)
    cluster_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    run: Mapped["ClusterRun"] = relationship("ClusterRun", back_populates="assignments")
