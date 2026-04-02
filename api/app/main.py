"""Gemini Sales Accelerator Core — FastAPI Application.

Application factory with lifespan management, CORS, global error handling,
and router registration. This is the single entry point for uvicorn.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware.error_handler import global_exception_handler
from app.routers.health import router as health_router
from app.routers.briefings import router as briefings_router

settings = get_settings()

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle.

    Startup: Log boot info, verify database connectivity.
    Shutdown: Dispose database engine and close Redis pool.
    """
    logger.info(
        "🚀 Starting %s v%s [env=%s]",
        settings.app_name,
        settings.app_version,
        settings.app_env,
    )

    # Verify database connectivity at startup
    from app.database import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        logger.info("✅ Database connection verified")
    except Exception as e:
        logger.error("❌ Database connection failed: %s", str(e))
        raise

    # Verify Redis connectivity at startup
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        logger.info("✅ Redis connection verified")
    except Exception as e:
        logger.warning("⚠️  Redis connection failed (non-fatal): %s", str(e))

    yield

    # Shutdown
    logger.info("🛑 Shutting down %s", settings.app_name)
    from app.database import engine

    await engine.dispose()


# ── Application Factory ─────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Headless AI Enterprise Platform — REST API for Gemini-powered "
        "sales intelligence. Decoupled from any specific frontend."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Apps Script, Salesforce, and custom web apps need cross-origin access.
# In production, replace "*" with explicit allowed origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Exception Handler ────────────────────────────────────────────────
app.add_exception_handler(Exception, global_exception_handler)

# ── Router Registration ─────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(briefings_router)


# ── Root Redirect ────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API docs."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
