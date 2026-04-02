"""Briefing service — core business logic for briefing generation.

Owns account upsert, cache lookup, and briefing generation orchestration.
The router calls this service — it never touches the ORM directly.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.briefing_cache import BriefingCache
from app.schemas.briefing import BriefingGenerateRequest, BriefingResponse

logger = logging.getLogger(__name__)


async def generate_briefing(
    db: AsyncSession,
    request: BriefingGenerateRequest,
) -> BriefingResponse:
    """Generate or retrieve a cached AI strategic briefing.

    Orchestrates the full pipeline: upsert account → check cache →
    generate (or return cached) → return response.

    Args:
        db: Async database session (injected by the router).
        request: Validated briefing request with account/contact context.

    Returns:
        BriefingResponse with cached or freshly generated briefing.
    """
    account = await _upsert_account(db, request)

    if not request.force_refresh:
        cached = await _get_cached_briefing(
            db, request.entity_type, account.id
        )
        if cached is not None:
            logger.info(
                "Cache hit for %s %s",
                request.entity_type,
                account.name,
                extra={"account_id": str(account.id), "cache_hit": True},
            )
            return _cache_to_response(cached, cache_hit=True)

    new_cache = await _create_placeholder_briefing(db, request, account)

    logger.info(
        "Briefing generated for %s",
        account.name,
        extra={"account_id": str(account.id), "cache_hit": False},
    )
    return _cache_to_response(new_cache, cache_hit=False)


async def _upsert_account(
    db: AsyncSession,
    request: BriefingGenerateRequest,
) -> Account:
    """Upsert an account by (source_system, external_id).

    If external_id is provided, attempts a lookup. On miss, creates a new
    record. On hit, updates mutable fields without overwriting existing AI
    enrichment data (defensive-programming.md §3).

    Args:
        db: Async database session.
        request: Validated briefing request.

    Returns:
        The upserted Account ORM instance.
    """
    account: Account | None = None

    if request.external_id:
        result = await db.execute(
            select(Account).where(
                Account.source_system == request.source_system,
                Account.external_id == request.external_id,
            )
        )
        account = result.scalar_one_or_none()

    if account is None:
        account = Account(
            external_id=request.external_id,
            source_system=request.source_system,
            name=request.account.name,
            industry=request.account.industry,
            type=request.account.type,
            annual_revenue=request.account.annual_revenue,
            number_of_employees=request.account.number_of_employees,
            website=request.account.website,
            phone=request.account.phone,
            billing_address=request.account.billing_address,
        )
        db.add(account)
        await db.flush()
        await db.refresh(account)
    else:
        account.name = request.account.name
        if request.account.industry is not None:
            account.industry = request.account.industry
        if request.account.type is not None:
            account.type = request.account.type
        if request.account.annual_revenue is not None:
            account.annual_revenue = request.account.annual_revenue
        if request.account.number_of_employees is not None:
            account.number_of_employees = request.account.number_of_employees
        if request.account.website is not None:
            account.website = request.account.website
        await db.flush()
        await db.refresh(account)

    return account


async def _get_cached_briefing(
    db: AsyncSession,
    entity_type: str,
    entity_id: uuid.UUID,
) -> BriefingCache | None:
    """Return the most recent non-expired cached briefing, or None.

    Args:
        db: Async database session.
        entity_type: The entity type to filter by.
        entity_id: The entity UUID to filter by.

    Returns:
        A BriefingCache instance or None if no valid cache exists.
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(BriefingCache)
        .where(
            BriefingCache.entity_type == entity_type,
            BriefingCache.entity_id == entity_id,
            BriefingCache.expires_at > now,
        )
        .order_by(BriefingCache.generated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _create_placeholder_briefing(
    db: AsyncSession,
    request: BriefingGenerateRequest,
    account: Account,
) -> BriefingCache:
    """Create a placeholder briefing cache entry.

    Phase 1 placeholder — Phase 2 replaces this with a real Vertex AI call.

    Args:
        db: Async database session.
        request: Validated briefing request.
        account: The upserted Account instance.

    Returns:
        The newly created BriefingCache instance.
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=7)

    contact_briefing = None
    if request.contact:
        first = request.contact.first_name or ""
        contact_briefing = f"Contact briefing for {first} {request.contact.last_name}"

    new_cache = BriefingCache(
        entity_type=request.entity_type,
        entity_id=account.id,
        briefing_markdown=(
            "⏳ **Briefing generation is not yet wired.** "
            "This placeholder confirms the API pipeline, database upsert, "
            "and cache layer are functioning correctly.\n\n"
            f"**Account:** {request.account.name}\n"
            f"**Industry:** {request.account.industry or 'Not specified'}\n"
            f"**Source:** {request.source_system}"
        ),
        contact_briefing_markdown=contact_briefing,
        p2b_score=None,
        account_signal=None,
        why_we_matter=None,
        anticipated_objection=None,
        objection_pivot=None,
        suggested_contacts_json=None,
        cache_ttl_days=7,
        generated_at=now,
        expires_at=expires,
    )
    db.add(new_cache)
    await db.flush()
    await db.refresh(new_cache)
    return new_cache


def _cache_to_response(
    cache: BriefingCache,
    cache_hit: bool,
) -> BriefingResponse:
    """Convert a BriefingCache ORM instance to a BriefingResponse.

    Args:
        cache: The BriefingCache instance to convert.
        cache_hit: Whether this response was served from cache.

    Returns:
        A BriefingResponse Pydantic model.
    """
    return BriefingResponse(
        id=cache.id,
        entity_type=cache.entity_type,
        entity_id=cache.entity_id,
        briefing_markdown=cache.briefing_markdown,
        contact_briefing_markdown=cache.contact_briefing_markdown,
        p2b_score=cache.p2b_score,
        account_signal=cache.account_signal,
        why_we_matter=cache.why_we_matter,
        anticipated_objection=cache.anticipated_objection,
        objection_pivot=cache.objection_pivot,
        suggested_contacts=None,  # Parse from JSON in Phase 2
        generated_at=cache.generated_at,
        expires_at=cache.expires_at,
        cache_hit=cache_hit,
    )
