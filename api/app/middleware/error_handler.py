"""Global exception handler middleware.

Catches unhandled exceptions and returns consistent JSON error responses.
Prevents stack traces from leaking to clients in production.
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions.

    Logs the full traceback server-side and returns a sanitized JSON
    response to the client. Never exposes internal error details.
    """
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again.",
            "type": "internal_error",
        },
    )
