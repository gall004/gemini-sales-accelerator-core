"""Opportunity ORM model.

Maps to the `opportunities` table. Replaces legacy Salesforce Opportunity
standard object + custom field (Gemini_Recommended_Action__c).
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Opportunity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """CRM Opportunity entity linked to an Account."""

    __tablename__ = "opportunities"

    # ── Identity ─────────────────────────────────────────────────────────
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL")
    )
    external_id: Mapped[str | None] = mapped_column(String(255))
    source_system: Mapped[str | None] = mapped_column(String(50))

    # ── Opportunity Data ─────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage_name: Mapped[str | None] = mapped_column(String(100))
    amount: Mapped[float | None] = mapped_column(Numeric(15, 2))
    close_date: Mapped[date | None] = mapped_column(Date)
    last_activity_date: Mapped[date | None] = mapped_column(Date)

    # ── AI Enrichment ────────────────────────────────────────────────────
    recommended_action: Mapped[str | None] = mapped_column(
        Text, comment="AI-generated next action from stalled pipeline analysis"
    )

    # ── Relationships ────────────────────────────────────────────────────
    account = relationship("Account", back_populates="opportunities")

    # ── Indexes ──────────────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_opportunities_account", "account_id"),
        Index(
            "idx_opportunities_external",
            "source_system",
            "external_id",
            unique=True,
        ),
    )
