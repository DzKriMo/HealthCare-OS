"""
Production security + observability middleware.

SecurityHeadersMiddleware  — CSP, HSTS, X-Frame-Options, etc.
RateLimitMiddleware        — per-IP + per-endpoint Redis-backed rate limiting.
StructuredLoggingMiddleware — JSON request/response logs with correlation IDs.
BruteForceMiddleware       — login endpoint lockout after N failures.
"""
import json
import logging
import time
import uuid
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger("healthcare_os.requests")


# ── Security Headers ──────────────────────────────────────────────────────────

class SecurityHeadersMiddleware:
    """Add security headers to every response (P1.3, P1.2)."""

    CSP = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none';"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy"] = self.CSP
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if not settings.DEBUG:
            response["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        return response


# ── Rate Limiting ─────────────────────────────────────────────────────────────

# (path_prefix, max_requests, window_seconds)
RATE_LIMIT_RULES = [
    ("/api/auth/login/", 5, 60),
    ("/api/auth/token/refresh/", 20, 60),
    ("/api/", 300, 60),
]


def _rate_limit_key(ip: str, path: str) -> str:
    return f"rl:{ip}:{path}"


class RateLimitMiddleware:
    """Redis-backed per-IP rate limiting (P1.4)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self._get_ip(request)
        path = request.path

        for prefix, limit, window in RATE_LIMIT_RULES:
            if path.startswith(prefix):
                key = _rate_limit_key(ip, prefix)
                count = cache.get(key, 0)
                if count >= limit:
                    return JsonResponse(
                        {"error": {"type": "RateLimitExceeded", "detail": "Too many requests."}},
                        status=429,
                    )
                # Increment; set TTL only on first hit
                if count == 0:
                    cache.set(key, 1, timeout=window)
                else:
                    cache.incr(key)
                break

        return self.get_response(request)

    @staticmethod
    def _get_ip(request) -> str:
        xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
        return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "")


# ── Brute-Force Protection ────────────────────────────────────────────────────

BRUTE_FORCE_MAX = 5
BRUTE_FORCE_LOCKOUT = 900  # 15 minutes


def _bf_key(ip: str) -> str:
    return f"bf:{ip}"


def record_failed_login(ip: str) -> bool:
    """Increment failure counter. Returns True if account should be locked."""
    key = _bf_key(ip)
    count = cache.get(key, 0) + 1
    cache.set(key, count, timeout=BRUTE_FORCE_LOCKOUT)
    return count >= BRUTE_FORCE_MAX


def clear_failed_logins(ip: str) -> None:
    cache.delete(_bf_key(ip))


def is_login_locked(ip: str) -> bool:
    return (cache.get(_bf_key(ip)) or 0) >= BRUTE_FORCE_MAX


class BruteForceMiddleware:
    """Block IPs that have exceeded failed login attempts (P6.2)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/api/auth/login/" and request.method == "POST":
            ip = RateLimitMiddleware._get_ip(request)
            if is_login_locked(ip):
                return JsonResponse(
                    {
                        "error": {
                            "type": "AccountLocked",
                            "detail": "Too many failed attempts. Try again in 15 minutes.",
                        }
                    },
                    status=429,
                )
        return self.get_response(request)


# ── Structured Logging ────────────────────────────────────────────────────────

class StructuredLoggingMiddleware:
    """Emit one JSON log line per request with correlation ID (P2.1)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.correlation_id = correlation_id

        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)

        tenant_id = getattr(getattr(request, "tenant", None), "id", None)
        user_id = (
            str(request.user.id)
            if hasattr(request, "user") and request.user.is_authenticated
            else None
        )

        logger.info(
            json.dumps({
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "tenant_id": str(tenant_id) if tenant_id else None,
                "user_id": user_id,
                "ip": RateLimitMiddleware._get_ip(request),
            })
        )

        response["X-Correlation-ID"] = correlation_id
        return response
