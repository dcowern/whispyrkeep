"""
URL configuration for WhispyrKeep project.

API routes are versioned under /api/v1/
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from whispyrkeep.health import health_check, readiness_check

urlpatterns = [
    # Health checks (unauthenticated)
    path("health/", health_check, name="health_check"),
    path("health/ready/", readiness_check, name="readiness_check"),
    # Admin
    path("admin/", admin.site.urls),
    # JWT Authentication
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # API v1 endpoints
    path("api/auth/", include("apps.accounts.urls")),
    path("api/llm/", include("apps.llm_config.urls")),
    path("api/characters/", include("apps.characters.urls")),
    path("api/universes/", include("apps.universes.urls")),
    path("api/campaigns/", include("apps.campaigns.urls")),
    path("api/exports/", include("apps.exports.urls")),
]
