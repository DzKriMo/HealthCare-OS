"""
Root-level views: health check + metrics endpoints (P2.2, P2.6).
"""
from django.db import connections
from django_redis import get_redis_connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import HttpResponse


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Deep health check for k8s liveness/readiness probes (P2.6).

    Covers DB, Redis (+ memory), Celery workers, and MinIO/S3 connectivity.

    GET /api/health/
    """
    checks = {
        "status": "healthy",
        "version": "0.1.0",
        "checks": {},
    }

    # Database
    try:
        connections["default"].cursor().execute("SELECT 1")
        checks["checks"]["database"] = "ok"
    except Exception as e:
        checks["status"] = "unhealthy"
        checks["checks"]["database"] = str(e)

    # Redis + memory usage
    try:
        redis_conn = get_redis_connection("default")
        redis_conn.ping()
        info = redis_conn.info("memory")
        checks["checks"]["redis"] = "ok"
        checks["checks"]["redis_memory_mb"] = round(
            info.get("used_memory", 0) / (1024 * 1024), 1
        )
    except Exception as e:
        checks["status"] = "degraded"
        checks["checks"]["redis"] = str(e)

    # Celery workers
    try:
        from healthcare_os.celery import app as celery_app

        pong = celery_app.control.ping(timeout=1.0)
        checks["checks"]["celery_workers"] = len(pong)
    except Exception as e:
        checks["checks"]["celery_workers"] = f"unknown: {e}"

    # MinIO / S3
    try:
        from django.core.files.storage import default_storage

        default_storage.exists("healthcheck-probe")
        checks["checks"]["object_storage"] = "ok"
    except Exception as e:
        checks["checks"]["object_storage"] = f"unavailable: {e}"

    status_code = 200 if checks["status"] == "healthy" else 503
    return Response(checks, status=status_code)


@api_view(["GET"])
@permission_classes([AllowAny])
def metrics(request):
    """
    Prometheus text-format metrics (P2.2).

    Exposes lightweight app-level gauges without requiring django-prometheus.
    Scrape target: GET /api/metrics/
    """
    from django.contrib.auth import get_user_model
    from tenancy.models import Tenant

    lines = []

    def gauge(name, value, help_text):
        lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")

    try:
        gauge("healthcare_tenants_total", Tenant.objects.count(), "Total tenants")
        gauge("healthcare_users_total", get_user_model().objects.count(), "Total users")
    except Exception:
        pass

    try:
        redis_conn = get_redis_connection("default")
        used = redis_conn.info("memory").get("used_memory", 0)
        gauge("healthcare_redis_used_bytes", used, "Redis memory in bytes")
    except Exception:
        pass

    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; version=0.0.4")
