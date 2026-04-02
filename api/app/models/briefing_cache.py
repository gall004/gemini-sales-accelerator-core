"""Briefing Cache ORM model.

Maps to the `briefing_cache` table. Replaces the legacy pattern of storing
AI_Briefing_Cache__c / Briefing_Last_Updated__c directly as fields on
Account, Contact, and Opportunity records in Salesforce.

This dedicated table enables TTL-based cache management, historical briefing
snapshots, and entity-type-agnostic storage.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class BriefingCache(UUIDPrimaryKeyMixin, Base):
    """Cached AI briefing with TTL expiration.

    Uses a polymorphic (entity_type, entity_id) pattern to associate
    briefings with accounts, contacts, or opportunities without separate
    junction tables.
    """

    __tablename__ = "briefing_cache"

    # ── Polymorphic Entity Reference ─────────────────────────────────────
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="account, contact, or opportunity",
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="FK to accounts, contacts, or opportunities",
    )

    # ── Briefing Content ─────────────────────────────────────────────────
    briefing_markdown: Mapped[str | None] = mapped_column(
        Text, comment="Full AI briefing in Markdown"
    )
    contact_briefing_markdown: Mapped[str | None] = mapped_column(
        Text, comment="Contact-specific executive briefing"
    )

    # ── AI Enrichment Snapshot ───────────────────────────────────────────
    p2b_score: Mapped[int | None] = mapped_column(
        Integer, comment="Propensity to Buy at generation time (0-100)"
    )
    account_signal: Mapped[str | None] = mapped_column(
        Text, comment="Strategic signal snapshot"
    )
    why_we_matter: Mapped[str | None] = mapped_column(
        Text, comment="Value proposition statement"
    )
    anticipated_objection: Mapped[str | None] = mapped_column(
        Text, comment="Most likely executive objection"
    )
    objection_pivot: Mapped[str | None] = mapped_column(
        Text, comment="Strategic pivot to redirect"
    )
    suggested_contacts_json: Mapped[str | None] = mapped_column(
        Text, comment="Buying committee suggestions JSON"
    )

    # ── Cache TTL ────────────────────────────────────────────────────────
    cache_ttl_days: Mapped[int] = mapped_column(
        Integer, server_default="7", nullable=False
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="generated_at + cache_ttl_days interval",
    )

    # ── Metadata ─────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Indexes ──────────────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_briefing_cache_entity", "entity_type", "entity_id"),
        Index(
            "idx_briefing_cache_lookup",
            "entity_type",
            "entity_id",
            "expires_at",
        ),
    )
