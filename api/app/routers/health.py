"""Health check router.

Provides a lightweight endpoint for Docker health checks, Cloud Run
readiness probes, and client connectivity verification.
"""

from fastapi import APIRouter

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    summary="Health Check",
    response_model=dict,
)
async def health_check() -> dict:
    """Return service health status.

    Does not require authentication. Used by Docker HEALTHCHECK,
    Cloud Run readiness probes, and load balancers.
    """
    return {"status": "ok", "service": "gemini-sales-accelerator-core"}
