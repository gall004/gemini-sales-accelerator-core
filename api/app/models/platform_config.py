"""Platform Config ORM model.

Maps to the `platform_config` table. Replaces the legacy Salesforce
Gemini_Config__mdt Custom Metadata Type with a key-value config store.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PlatformConfig(Base):
    """Key-value configuration store.

    Replaces Gemini_Config__mdt. Runtime values (model names, cache TTLs,
    feature flags) are stored here and read by services at request time.
    """

    __tablename__ = "platform_config"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(
        String(50), comment="gcp, ai, cache, auth, feature"
    )
    description: Mapped[str | None] = mapped_column(
        Text, comment="Human-readable description"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
