"""Briefing service — proxy to Vertex AI Reasoning Engines.

Owns: cache lookup, agent routing, response mapping.
Does NOT own: system prompts, model selection, generate_content calls.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.account import Account
from app.models.briefing_cache import BriefingCache
from app.models.platform_config import PlatformConfig
from app.schemas.briefing import BriefingGenerateRequest, BriefingResponse
from app.services.account_service import upsert_account
from app.services.agent_client import (
    AgentInvocationError,
    query_reasoning_engine,
)
from app.services.telemetry import log_ai_usage

logger = logging.getLogger(__name__)


async def generate_briefing(
    db: AsyncSession, request: BriefingGenerateRequest,
) -> BriefingResponse:
    """Orchestrate: upsert → cache check → agent invoke → return."""
    settings = get_settings()
    account = await upsert_account(db, request)

    if not request.force_refresh:
        cached = await _get_cached_briefing(
            db, request.entity_type, account.id
        )
        if cached is not None:
            logger.info(
                "Cache hit for %s %s", request.entity_type, account.name,
                extra={"account_id": str(account.id), "cache_hit": True},
            )
            return _cache_to_response(cached, cache_hit=True)

    cache = await _invoke_and_cache(db, request, account, settings)
    logger.info(
        "Briefing generated for %s", account.name,
        extra={"account_id": str(account.id), "cache_hit": False},
    )
    return _cache_to_response(cache, cache_hit=False)



async def _invoke_and_cache(
    db: AsyncSession, request: BriefingGenerateRequest,
    account: Account, settings: Settings,
) -> BriefingCache:
    """Resolve agent, invoke it, cache + log the result."""
    agent_id = await _resolve_agent_id(db, request, settings)

    if agent_id is None:
        logger.warning("No agent_id configured — returning placeholder")
        return await _create_fallback(db, request, account, is_error=False)

    try:
        result = await query_reasoning_engine(
            project_id=settings.gcp_project_id,
            location=settings.gcp_location,
            agent_id=agent_id,
            input_text=_build_agent_input(request),
        )
        cache = await _persist_briefing(
            db, request, account, result["output"], settings,
        )
        asyncio.create_task(log_ai_usage(
            endpoint="Briefing Agent", operation="Briefing",
            entity_type=request.entity_type, entity_id=account.id,
            agent_id=agent_id, latency_ms=result["latency_ms"],
            ai_output=result["output"], model_name=settings.gemini_model_name,
            source_system=request.source_system,
            account_name=request.account.name,
            campaign_context=request.campaign_context,
        ))
        return cache

    except AgentInvocationError as exc:
        logger.error(
            "Agent failed for %s: %s", account.name, str(exc),
            extra={"agent_id": agent_id, "account_id": str(account.id)},
        )
        asyncio.create_task(log_ai_usage(
            endpoint="Briefing Agent", operation="Briefing",
            entity_type=request.entity_type, entity_id=account.id,
            agent_id=agent_id, latency_ms=0, ai_output={},
            model_name=settings.gemini_model_name,
            source_system=request.source_system,
            account_name=request.account.name,
            campaign_context=request.campaign_context,
            status="error", error_message=str(exc),
        ))
        return await _create_fallback(
            db, request, account, is_error=True, error_msg=str(exc),
        )


async def _resolve_agent_id(
    db: AsyncSession, request: BriefingGenerateRequest, settings: Settings,
) -> str | None:
    """Resolve agent: request.agent_id → platform_config → settings."""
    if request.agent_id:
        return request.agent_id

    result = await db.execute(
        select(PlatformConfig.value).where(
            PlatformConfig.key == "default_briefing_agent_id"
        )
    )
    config_value = result.scalar_one_or_none()
    return config_value or settings.briefing_agent_engine_id


def _build_agent_input(request: BriefingGenerateRequest) -> str:
    """Marshal account/contact/campaign data into agent input text."""
    parts = [
        f"Generate a strategic sales briefing for entity_type: "
        f"{request.entity_type}",
        "", "<CRM_DATA>",
        f"Account Name: {request.account.name}",
    ]
    acct = request.account
    if acct.industry:
        parts.append(f"Industry: {acct.industry}")
    if acct.type:
        parts.append(f"Account Type: {acct.type}")
    if acct.annual_revenue is not None:
        parts.append(f"Annual Revenue: ${acct.annual_revenue:,.0f}")
    if acct.number_of_employees is not None:
        parts.append(f"Employees: {acct.number_of_employees:,}")
    if acct.website:
        parts.append(f"Website: {acct.website}")

    if request.contact:
        first = request.contact.first_name or ""
        parts += ["", f"Contact: {first} {request.contact.last_name}".strip()]
        if request.contact.title:
            parts.append(f"Title: {request.contact.title}")
        if request.contact.email:
            parts.append(f"Email: {request.contact.email}")

    parts.append("</CRM_DATA>")
    if request.campaign_context:
        parts += ["", f"Campaign/Product Focus: {request.campaign_context}"]

    return "\n".join(parts)



def _safe_int(value: object) -> int | None:
    """Safely coerce to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


async def _persist_briefing(
    db: AsyncSession, request: BriefingGenerateRequest,
    account: Account, ai_output: dict, settings: Settings,
) -> BriefingCache:
    """Map agent response to BriefingCache (handles camelCase + snake_case)."""
    now = datetime.now(timezone.utc)
    ttl = settings.briefing_cache_ttl_days

    suggested = ai_output.get("suggestedContacts") or ai_output.get(
        "suggested_contacts"
    )
    cache = BriefingCache(
        entity_type=request.entity_type, entity_id=account.id,
        briefing_markdown=(
            ai_output.get("briefing") or ai_output.get("briefing_markdown")
        ),
        contact_briefing_markdown=(
            ai_output.get("contactBriefing")
            or ai_output.get("contact_briefing_markdown")
        ),
        p2b_score=_safe_int(
            ai_output.get("p2bScore") or ai_output.get("p2b_score")
        ),
        account_signal=(
            ai_output.get("accountSignal") or ai_output.get("account_signal")
        ),
        why_we_matter=(
            ai_output.get("whyWeMatter") or ai_output.get("why_we_matter")
        ),
        anticipated_objection=(
            ai_output.get("anticipatedObjection")
            or ai_output.get("anticipated_objection")
        ),
        objection_pivot=(
            ai_output.get("objectionPivot")
            or ai_output.get("objection_pivot")
        ),
        suggested_contacts_json=(
            json.dumps(suggested) if suggested else None
        ),
        cache_ttl_days=ttl, generated_at=now,
        expires_at=now + timedelta(days=ttl),
    )
    db.add(cache)
    await db.flush()
    await db.refresh(cache)
    return cache


async def _create_fallback(
    db: AsyncSession, request: BriefingGenerateRequest,
    account: Account, *, is_error: bool, error_msg: str | None = None,
) -> BriefingCache:
    """Create placeholder (no agent) or degraded (agent failed) briefing."""
    now = datetime.now(timezone.utc)
    if is_error:
        markdown = (
            "⚠️ **Briefing generation temporarily unavailable.** "
            "The AI agent could not be reached. Please try again.\n\n"
            f"**Account:** {request.account.name}\n"
            f"**Error:** {error_msg}"
        )
        expires = now + timedelta(hours=1)
    else:
        markdown = (
            "⏳ **No Briefing Agent configured.** Set "
            "`BRIEFING_AGENT_ENGINE_ID` or add "
            "`default_briefing_agent_id` to `platform_config`.\n\n"
            f"**Account:** {request.account.name}\n"
            f"**Industry:** {request.account.industry or 'Not specified'}\n"
            f"**Source:** {request.source_system}"
        )
        expires = now + timedelta(days=7)

    cache = BriefingCache(
        entity_type=request.entity_type, entity_id=account.id,
        briefing_markdown=markdown, contact_briefing_markdown=None,
        cache_ttl_days=0 if is_error else 7,
        generated_at=now, expires_at=expires,
    )
    db.add(cache)
    await db.flush()
    await db.refresh(cache)
    return cache



async def _get_cached_briefing(
    db: AsyncSession, entity_type: str, entity_id: uuid.UUID,
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


def _cache_to_response(
    cache: BriefingCache, cache_hit: bool,
) -> BriefingResponse:
    """Convert BriefingCache ORM → BriefingResponse Pydantic."""
    suggested = None
    if cache.suggested_contacts_json:
        try:
            suggested = json.loads(cache.suggested_contacts_json)
        except (json.JSONDecodeError, ValueError):
            suggested = None

    return BriefingResponse(
        id=cache.id, entity_type=cache.entity_type,
        entity_id=cache.entity_id,
        briefing_markdown=cache.briefing_markdown,
        contact_briefing_markdown=cache.contact_briefing_markdown,
        p2b_score=cache.p2b_score, account_signal=cache.account_signal,
        why_we_matter=cache.why_we_matter,
        anticipated_objection=cache.anticipated_objection,
        objection_pivot=cache.objection_pivot,
        suggested_contacts=suggested,
        generated_at=cache.generated_at, expires_at=cache.expires_at,
        cache_hit=cache_hit,
    )
