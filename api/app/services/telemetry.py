"""AI usage telemetry — non-blocking logging to ai_usage_logs.

Per observability-and-docs.md §5: every AI call is logged with token counts,
latency, agent_id, and status. Logging failures never block the API response.
"""

import logging

from app.models.ai_usage_log import AIUsageLog

logger = logging.getLogger(__name__)


async def log_ai_usage(
    *,
    endpoint: str,
    operation: str,
    entity_type: str,
    entity_id: object,
    agent_id: str,
    latency_ms: int,
    ai_output: dict,
    model_name: str,
    source_system: str,
    account_name: str,
    campaign_context: str | None = None,
    status: str = "success",
    error_message: str | None = None,
) -> None:
    """Persist an AI usage log entry in a dedicated session.

    Uses its own session factory so failures here never roll back the
    main request transaction.
    """
    try:
        from app.database import async_session_factory

        async with async_session_factory() as session:
            entry = AIUsageLog(
                endpoint=endpoint,
                operation=operation,
                entity_type=entity_type,
                entity_id=entity_id,
                tokens_used=_safe_int(ai_output.get("tokens_used")),
                input_tokens=_safe_int(ai_output.get("input_tokens")),
                output_tokens=_safe_int(ai_output.get("output_tokens")),
                latency_ms=latency_ms,
                cache_hit=False,
                status=status,
                error_message=error_message,
                model_name=ai_output.get("model_name", model_name),
                agent_id=agent_id,
                request_metadata={
                    "source_system": source_system,
                    "account_name": account_name,
                    "campaign_context": campaign_context,
                },
            )
            session.add(entry)
            await session.commit()
    except Exception as exc:
        logger.warning(
            "Failed to log AI usage: %s",
            str(exc),
            extra={"agent_id": agent_id},
        )


def _safe_int(value: object) -> int | None:
    """Safely coerce a value to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
