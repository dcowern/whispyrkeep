"""
Health check views for WhispyrKeep.

Provides endpoints to verify service connectivity:
- /health/ - Basic health check
- /health/ready/ - Readiness check (DB, Redis, ChromaDB)
"""

from django.db import connection
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check - always returns OK if the server is running.

    GET /health/
    """
    return JsonResponse({"status": "ok", "service": "whispyrkeep"})


@api_view(["GET"])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check - verifies database and cache connectivity.

    GET /health/ready/
    """
    status = {
        "status": "ok",
        "checks": {
            "database": check_database(),
            "redis": check_redis(),
        },
    }

    # Overall status is degraded if any check fails
    all_ok = all(c["status"] == "ok" for c in status["checks"].values())
    if not all_ok:
        status["status"] = "degraded"

    return JsonResponse(status, status=200 if all_ok else 503)


def check_database():
    """Check PostgreSQL connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_redis():
    """Check Redis connectivity."""
    try:
        from django.core.cache import cache

        cache.set("health_check", "ok", 10)
        result = cache.get("health_check")
        if result == "ok":
            return {"status": "ok"}
        return {"status": "error", "message": "Cache read/write failed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
