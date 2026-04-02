"""Account ORM model.

Maps to the `accounts` table. Replaces legacy Salesforce Account standard
object + custom fields (P2B_Score__c, Account_Signal__c, etc.).
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Account(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """CRM Account entity with AI enrichment fields.

    Supports multi-source upsert via (source_system, external_id) unique
    constraint — the same account can be synced from Salesforce, Google
    Sheets, or any future frontend.
    """

    __tablename__ = "accounts"

    # ── Identity ─────────────────────────────────────────────────────────
    external_id: Mapped[str | None] = mapped_column(String(255))
    source_system: Mapped[str | None] = mapped_column(
        String(50), comment="salesforce, google_sheets, hubspot, etc."
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Firmographics ────────────────────────────────────────────────────
    industry: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[str | None] = mapped_column(
        String(50), comment="Customer, Prospect, Partner"
    )
    annual_revenue: Mapped[float | None] = mapped_column(Numeric(15, 2))
    number_of_employees: Mapped[int | None] = mapped_column(Integer)
    website: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(50))
    billing_address: Mapped[str | None] = mapped_column(
        Text, comment="JSON or structured address"
    )

    # ── AI Enrichment ────────────────────────────────────────────────────
    p2b_score: Mapped[int | None] = mapped_column(
        Integer, comment="Propensity to Buy (0-100)"
    )
    account_signal: Mapped[str | None] = mapped_column(
        Text, comment="AI-generated strategic signal"
    )
    suggested_contacts_json: Mapped[str | None] = mapped_column(
        Text, comment="Cached buying committee JSON"
    )
    enrichment_last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # ── Relationships ────────────────────────────────────────────────────
    contacts = relationship("Contact", back_populates="account", lazy="selectin")
    opportunities = relationship(
        "Opportunity", back_populates="account", lazy="selectin"
    )

    # ── Indexes ──────────────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_accounts_external", "source_system", "external_id", unique=True),
    )
