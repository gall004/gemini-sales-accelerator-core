"""Contact ORM model.

Maps to the `contacts` table. Replaces legacy Salesforce Contact standard
object. Linked to Account via foreign key.
"""

import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Contact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """CRM Contact entity linked to an Account."""

    __tablename__ = "contacts"

    # ── Identity ─────────────────────────────────────────────────────────
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL")
    )
    external_id: Mapped[str | None] = mapped_column(String(255))
    source_system: Mapped[str | None] = mapped_column(String(50))

    # ── Contact Info ─────────────────────────────────────────────────────
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))

    # ── Relationships ────────────────────────────────────────────────────
    account = relationship("Account", back_populates="contacts")

    # ── Indexes ──────────────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_contacts_account", "account_id"),
        Index("idx_contacts_external", "source_system", "external_id", unique=True),
    )
