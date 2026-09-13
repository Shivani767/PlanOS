"""PlanOS database models."""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from planos.app.db.session import Base, generate_uuid


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="VIEWER")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    organization = relationship("Organization", back_populates="users")


# Re-export models from submodules for convenient access
from planos.app.models.agent import Agent, AgentRun, AgentStep
from planos.app.models.approval import ApprovalRequest
from planos.app.models.audit import AuditLog
from planos.app.models.change_set import ChangeSet
from planos.app.models.checkpoint import Checkpoint
from planos.app.models.dimension import Department, Product, Region, TimePeriod
from planos.app.models.import_job import ImportJob
from planos.app.models.job import Job
from planos.app.models.knowledge import (
    IdempotencyRecord,
    KnowledgeChunk,
    KnowledgeDocument,
    MemoryEntry,
)
from planos.app.models.plan import Plan, PlanVersion
from planos.app.models.planning_data import PlanningData
from planos.app.models.scenario import Scenario, ScenarioChange, ScenarioResult
from planos.app.models.tool_call import ToolCall

__all__ = [
    "Organization", "User", "Agent", "AgentRun", "AgentStep", "ApprovalRequest",
    "AuditLog", "ChangeSet", "Checkpoint", "Department", "Product", "Region",
    "TimePeriod", "ImportJob", "Job", "IdempotencyRecord", "KnowledgeChunk",
    "KnowledgeDocument", "MemoryEntry", "Plan", "PlanVersion", "PlanningData",
    "Scenario", "ScenarioChange", "ScenarioResult", "ToolCall",
]
