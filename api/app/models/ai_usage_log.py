"""AI Usage Log ORM model.

Maps to the `ai_usage_logs` table. Replaces the legacy Salesforce
AI_Usage_Log__c custom object with enhanced granularity: per-request
token breakdown (input/output), model name tracking, agent ID tracking,
and JSONB metadata for extensibility.

Logs are written asynchronously to avoid blocking the request path.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class AIUsageLog(UUIDPrimaryKeyMixin, Base):
    """Telemetry record for every AI API invocation.

    Captures latency, token consumption, cache status, and error context
    for admin observability dashboards and cost tracking.
    """

    __tablename__ = "ai_usage_logs"

    # ── Request Identity ─────────────────────────────────────────────────
    endpoint: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Briefing Agent, Chat Agent, Raw Model",
    )
    operation: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Briefing, Chat, Enrichment, SmartRouter",
    )
    user_identifier: Mapped[str | None] = mapped_column(
        String(255), comment="Email or API key identity"
    )

    # ── Entity Context ───────────────────────────────────────────────────
    entity_type: Mapped[str | None] = mapped_column(
        String(50), comment="account, contact, opportunity"
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # ── Performance Metrics ──────────────────────────────────────────────
    tokens_used: Mapped[int | None] = mapped_column(
        Integer, comment="Total token consumption"
    )
    input_tokens: Mapped[int | None] = mapped_column(
        Integer, comment="Prompt token count"
    )
    output_tokens: Mapped[int | None] = mapped_column(
        Integer, comment="Completion token count"
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer, comment="Round-trip time in milliseconds"
    )

    # ── Cache & Status ───────────────────────────────────────────────────
    cache_hit: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        server_default="success",
        nullable=False,
        comment="success or error",
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    # ── Model & Agent Tracking ───────────────────────────────────────────
    model_name: Mapped[str | None] = mapped_column(
        String(100), comment="e.g. gemini-2.5-pro, gemini-2.0-flash"
    )
    agent_id: Mapped[str | None] = mapped_column(
        String(255), comment="Reasoning Engine ID"
    )

    # ── Extensibility ────────────────────────────────────────────────────
    request_metadata: Mapped[dict | None] = mapped_column(
        JSONB, comment="Additional context (source_system, request params, etc.)"
    )

    # ── Timestamp ────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Indexes ──────────────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_ai_usage_logs_created", "created_at"),
        Index("idx_ai_usage_logs_user", "user_identifier", "created_at"),
        Index("idx_ai_usage_logs_entity", "entity_type", "entity_id"),
    )
