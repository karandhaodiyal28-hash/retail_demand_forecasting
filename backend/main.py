"""FastAPI application entrypoint.

Wires up:
  * CORS restricted to configured origins
  * Trusted-host middleware (defence-in-depth against host-header attacks)
  * Security response headers (CSP, X-Frame-Options, HSTS, ...)
  * Slowapi rate limiting (per IP)
  * Request body size limit (DoS hardening)
  * Exception handlers that never leak internals
  * Routers: /auth, /products, /sales, /forecast, /inventory, /reports, /dashboard
"""
from __future__ import annotations
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .database import init_db
from .routers import auth, products, sales, forecast, inventory, reports, dashboard


# ----- logging -----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
logger = logging.getLogger("retail_forecast")


# ----- request size limit middleware -----
class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with bodies larger than the configured limit (DoS hardening)."""

    def __init__(self, app, max_bytes: int):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        if request.method in {"POST", "PUT", "PATCH"}:
            cl = request.headers.get("content-length")
            if cl is not None:
                try:
                    if int(cl) > self.max_bytes:
                        return JSONResponse(
                            status_code=413,
                            content={"detail": f"Request body exceeds {self.max_bytes} bytes"},
                        )
                except ValueError:
                    pass
        return await call_next(request)


# ----- security headers middleware -----
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "X-XSS-Protection": "1; mode=block",
    # NOTE: HSTS only effective over HTTPS — emit anyway for hardening
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self';"
    ),
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp: Response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            resp.headers.setdefault(k, v)
        return resp


# ----- request-id middleware -----
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request.state.request_id = rid
        resp = await call_next(request)
        resp.headers["x-request-id"] = rid
        return resp


# ----- lifespan -----
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialised at %s", settings.DATABASE_URL)
    yield


# ----- create app -----
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI/ML retail demand forecasting & inventory optimisation API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    max_age=600,
)

# Security / utility middleware (order matters — outermost first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.MAX_UPLOAD_BYTES)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # tighten in prod

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ----- exception handlers (don't leak internals) -----
def _json_safe(value):
    """Recursively convert values to JSON-safe primitives."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return str(value)


@app.exception_handler(RequestValidationError)
async def _validation_handler(_: Request, exc: RequestValidationError):
    safe_errors = _json_safe(exc.errors())
    return JSONResponse(status_code=422, content={"detail": "Validation error", "errors": safe_errors})


@app.exception_handler(Exception)
async def _generic_handler(_: Request, exc: Exception):
    rid = getattr(_.state, "request_id", None) if _ else None
    logger.exception("Unhandled error [rid=%s]: %s", rid, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": rid})


# ----- root + health -----
@app.get("/", tags=["meta"])
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


# ----- routers -----
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(sales.router, prefix=settings.API_V1_PREFIX)
app.include_router(forecast.router, prefix=settings.API_V1_PREFIX)
app.include_router(inventory.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
