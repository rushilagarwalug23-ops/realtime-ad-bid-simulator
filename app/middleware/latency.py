"""Latency tracking middleware."""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class LatencyMiddleware(BaseHTTPMiddleware):
    """Middleware to inject X-Response-Time-Ms header."""
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers['X-Response-Time-Ms'] = f'{duration_ms:.2f}'
        return response
