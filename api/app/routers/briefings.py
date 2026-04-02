"""Briefings router — /api/v1/briefings endpoints.

Handles briefing generation, cache retrieval, and force-refresh. This router
is a thin transport layer — all business logic lives in the service layer
(to be wired in Phase 2).
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import AuthenticatedKey, DbSession
from app.models.account import Account
from app.models.briefing_cache import BriefingCache
from app.schemas.briefing import (
    BriefingGenerateRequest,
    BriefingResponse,
)

router = APIRouter(prefix="/api/v1/briefings", tags=["Briefings"])


@router.post(
    "/generate",
    response_model=BriefingResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate an AI Strategic Briefing",
    description=(
        "Accepts account and contact context inline, upserts the account, "
        "checks the briefing cache, and returns a cached or freshly generated "
        "AI briefing. Vertex AI agent integration will be wired in Phase 2."
    ),
)
async def generate_briefing(
    request: BriefingGenerateRequest,
    db: DbSession,
    _api_key: AuthenticatedKey,
) -> BriefingResponse:
    """Generate or retrieve a cached AI strategic briefing.

    Phase 1: Upserts the account and returns a placeholder briefing.
    Phase 2: Wires in Vertex AI agent call + Redis hot cache.
    """
    # ── Step 1: Upsert Account ───────────────────────────────────────────
    account = await _upsert_account(db, request)

    # ── Step 2: Check Briefing Cache ─────────────────────────────────────
    if not request.force_refresh:
        cached = await _get_cached_briefing(
            db, request.entity_type, account.id
        )
        if cached is not None:
            return BriefingResponse(
                id=cached.id,
                entity_type=cached.entity_type,
                entity_id=cached.entity_id,
                briefing_markdown=cached.briefing_markdown,
                contact_briefing_markdown=cached.contact_briefing_markdown,
                p2b_score=cached.p2b_score,
                account_signal=cached.account_signal,
                why_we_matter=cached.why_we_matter,
                anticipated_objection=cached.anticipated_objection,
                objection_pivot=cached.objection_pivot,
                suggested_contacts=None,  # Parse JSON in Phase 2
                generated_at=cached.generated_at,
                expires_at=cached.expires_at,
                cache_hit=True,
            )

    # ── Step 3: Generate Briefing (Phase 2 — Vertex AI agent call) ───────
    # For now, create a placeholder cache entry to validate the full pipeline.
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=7)

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
        contact_briefing_markdown=(
            f"Contact briefing for "
            f"{request.contact.first_name or ''} {request.contact.last_name}"
            if request.contact
            else None
        ),
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

    return BriefingResponse(
        id=new_cache.id,
        entity_type=new_cache.entity_type,
        entity_id=new_cache.entity_id,
        briefing_markdown=new_cache.briefing_markdown,
        contact_briefing_markdown=new_cache.contact_briefing_markdown,
        p2b_score=new_cache.p2b_score,
        account_signal=new_cache.account_signal,
        why_we_matter=new_cache.why_we_matter,
        anticipated_objection=new_cache.anticipated_objection,
        objection_pivot=new_cache.objection_pivot,
        suggested_contacts=None,
        generated_at=new_cache.generated_at,
        expires_at=new_cache.expires_at,
        cache_hit=False,
    )


# ── Private Helpers ──────────────────────────────────────────────────────────


async def _upsert_account(
    db: DbSession,
    request: BriefingGenerateRequest,
) -> Account:
    """Upsert an account by (source_system, external_id).

    If external_id is provided, attempts a lookup. On miss, creates a new
    record. On hit, updates mutable fields (revenue, employees, etc.) without
    overwriting existing AI enrichment data.
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
        # Create new account
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
        # Update mutable fields — never overwrite AI enrichment with None
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
    db: DbSession,
    entity_type: str,
    entity_id: uuid.UUID,
) -> BriefingCache | None:
    """Return the most recent non-expired cached briefing, or None."""
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
