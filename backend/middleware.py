import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from backend.logging_config import get_logger

logger = get_logger("http")


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
