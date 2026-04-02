"""ORM model registry.

Import all models here so Alembic and SQLAlchemy's metadata.create_all()
discover them. Any new model MUST be imported in this file.
"""

from app.models.base import Base
from app.models.account import Account
from app.models.contact import Contact
from app.models.opportunity import Opportunity
from app.models.briefing_cache import BriefingCache
from app.models.ai_usage_log import AIUsageLog
from app.models.platform_config import PlatformConfig

__all__ = [
    "Base",
    "Account",
    "Contact",
    "Opportunity",
    "BriefingCache",
    "AIUsageLog",
    "PlatformConfig",
]
