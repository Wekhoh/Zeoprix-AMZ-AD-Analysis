import re
import uuid
import time
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from backend.logging_config import get_logger

logger = get_logger("http")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_date_param(value: str | None, param_name: str = "date") -> None:
    """Validate a YYYY-MM-DD date string. Raises HTTPException 422 on invalid format."""
    if value is None:
        return
    if not _DATE_RE.match(value):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid date format for '{param_name}': expected YYYY-MM-DD, got '{value}'",
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 1)

        # Only log API requests, not static files
        if request.url.path.startswith("/api"):
            logger.info(
                f"{request_id} | {request.method} {request.url.path}"
                f" | {response.status_code} | {duration}ms"
            )

        response.headers["X-Request-ID"] = request_id
        return response
