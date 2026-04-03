"""Shared test fixtures — async client, test database, dependency overrides.

Per testing-standards.md §6: each test runs against an isolated database
state. No test depends on data from another test.

Uses NullPool to prevent connection persistence across event loops.
"""

import os

# ── Configure test environment BEFORE any app imports ────────────────────────
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://gsa_user:gsa_local_password"
    "@postgres:5432/gsa_core_test"
)
os.environ["DATABASE_URL_SYNC"] = (
    "postgresql://gsa_user:gsa_local_password"
    "@postgres:5432/gsa_core_test"
)
os.environ["API_KEY"] = "test_api_key_12345"
os.environ["APP_ENV"] = "test"
os.environ["REDIS_URL"] = "redis://redis:6379/1"
os.environ["LOG_LEVEL"] = "WARNING"

from collections.abc import AsyncGenerator  # noqa: E402

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402

import app.database as db_module  # noqa: E402
from app.models.base import Base  # noqa: E402

# ── Table names for cleanup ─────────────────────────────────────────────────

_TABLES_TO_TRUNCATE = (
    "briefing_cache",
    "contacts",
    "opportunities",
    "ai_usage_logs",
    "accounts",
    "platform_config",
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Replace the module-level engine and create tables.

    Uses NullPool to avoid connection-caching across event loop boundaries.
    """
    # Dispose the import-time engine
    old_engine = db_module.engine
    await old_engine.dispose()

    # Create test engine with NullPool — no cached connections
    test_engine = create_async_engine(
        os.environ["DATABASE_URL"], echo=False, poolclass=NullPool
    )
    test_factory = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Patch both database module attributes
    db_module.engine = test_engine
    db_module.async_session_factory = test_factory

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client with clean table state."""
    from app.main import app

    async with db_module.async_session_factory() as session:
        for table_name in _TABLES_TO_TRUNCATE:
            await session.execute(
                text(f"TRUNCATE TABLE {table_name} CASCADE")
            )
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

from unittest.mock import AsyncMock, patch  # noqa: E402

# ── Mock Agent Response ──────────────────────────────────────────────────────

MOCK_AGENT_RESPONSE = {
    "briefing": (
        "### Strategic Overview\n"
        "Acme Corp is aggressively expanding its cloud infrastructure.\n\n"
        "### High-Impact Discovery Questions\n"
        "1. **How** is your team evaluating vendor consolidation?\n"
        "2. **What** KPIs are driving your digital transformation?\n"
        "3. **Why** has the board prioritized AI adoption this quarter?"
    ),
    "contactBriefing": (
        "### Strategic Account Summary\n"
        "- Jane Doe leads engineering transformation.\n\n"
        "### Recommended Opening\n"
        "Your recent infrastructure review suggests urgency."
    ),
    "p2bScore": 78,
    "accountSignal": "Expanding cloud spend by 40% YoY.",
    "whyWeMatter": "Our platform cuts integration time by 60%.",
    "anticipatedObjection": "We already have an in-house solution.",
    "objectionPivot": "Most teams find they save 200+ engineering hours.",
    "suggestedContacts": [
        {"title": "VP of Engineering", "reason": "Technical decision maker"},
        {"title": "CFO", "reason": "Budget authority for cloud spend"},
    ],
}


@pytest_asyncio.fixture(autouse=True)
async def mock_agent_client():
    """Patch agent_client.query_reasoning_engine for all tests.

    Returns a realistic structured JSON response so tests validate
    the full pipeline without real Vertex AI calls.
    """
    mock_result = {
        "output": MOCK_AGENT_RESPONSE.copy(),
        "latency_ms": 1234,
    }
    with patch(
        "app.services.briefing_service.query_reasoning_engine",
        new_callable=AsyncMock,
        return_value=mock_result,
    ) as mock_fn:
        yield mock_fn


# ── Auth Header Helper ──────────────────────────────────────────────────────

VALID_API_KEY = "test_api_key_12345"
AUTH_HEADERS = {"X-API-Key": VALID_API_KEY}

