"""Briefings router — /api/v1/briefings endpoints.

Thin transport layer (architecture.md §3). Parses HTTP request, calls
the briefing service, returns the response. No business logic here.
"""

from fastapi import APIRouter, status

from app.dependencies import AuthenticatedKey, DbSession
from app.schemas.briefing import BriefingGenerateRequest, BriefingResponse
from app.services import briefing_service

router = APIRouter(prefix="/api/v1/briefings", tags=["Briefings"])


@router.post(
    "/generate",
    response_model=BriefingResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate an AI Strategic Briefing",
    description=(
        "Accepts account and contact context inline, upserts the account, "
        "checks the briefing cache, and returns a cached or freshly generated "
        "AI briefing."
    ),
)
async def generate_briefing(
    request: BriefingGenerateRequest,
    db: DbSession,
    _api_key: AuthenticatedKey,
) -> BriefingResponse:
    """Generate or retrieve a cached AI strategic briefing.

    Args:
        request: Validated briefing generation request body.
        db: Injected async database session.
        _api_key: Validated API key (unused but enforces auth).

    Returns:
        BriefingResponse with briefing content and cache metadata.
    """
    return await briefing_service.generate_briefing(db, request)
