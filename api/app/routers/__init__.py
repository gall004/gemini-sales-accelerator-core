"""Router registry."""

from app.routers.health import router as health_router
from app.routers.briefings import router as briefings_router

__all__ = ["health_router", "briefings_router"]
