"""
URL configuration for Universe and Homebrew APIs.

Provides nested routes for universe-scoped homebrew content:
- /api/universes/
- /api/universes/{id}/homebrew/species/
- /api/universes/{id}/homebrew/spells/
- /api/universes/{id}/homebrew/items/
- etc.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from . import views

# Main router for universes
router = DefaultRouter()
router.register(r"", views.UniverseViewSet, basename="universe")

# Nested router for homebrew content under universes
universe_router = routers.NestedDefaultRouter(router, r"", lookup="universe")
universe_router.register(r"canon", views.UniverseHardCanonDocViewSet, basename="universe-canon")
universe_router.register(
    r"homebrew/species",
    views.HomebrewSpeciesViewSet,
    basename="universe-homebrew-species",
)
universe_router.register(
    r"homebrew/spells",
    views.HomebrewSpellViewSet,
    basename="universe-homebrew-spells",
)
universe_router.register(
    r"homebrew/items",
    views.HomebrewItemViewSet,
    basename="universe-homebrew-items",
)
universe_router.register(
    r"homebrew/monsters",
    views.HomebrewMonsterViewSet,
    basename="universe-homebrew-monsters",
)
universe_router.register(
    r"homebrew/feats",
    views.HomebrewFeatViewSet,
    basename="universe-homebrew-feats",
)
universe_router.register(
    r"homebrew/backgrounds",
    views.HomebrewBackgroundViewSet,
    basename="universe-homebrew-backgrounds",
)
universe_router.register(
    r"homebrew/classes",
    views.HomebrewClassViewSet,
    basename="universe-homebrew-classes",
)
universe_router.register(
    r"homebrew/subclasses",
    views.HomebrewSubclassViewSet,
    basename="universe-homebrew-subclasses",
)

urlpatterns = [
    # Worldgen endpoints (must be before router to avoid being caught by UUID lookup)
    path("worldgen/", views.WorldgenView.as_view(), name="universe_worldgen"),
    path("worldgen/preview/", views.WorldgenPreviewView.as_view(), name="universe_worldgen_preview"),
    # Worldgen session endpoints for AI collaboration
    path("worldgen/llm-status/", views.WorldgenLlmStatusView.as_view(), name="worldgen_llm_status"),
    path("worldgen/sessions/", views.WorldgenSessionListView.as_view(), name="worldgen_session_list"),
    path(
        "worldgen/sessions/<uuid:session_id>/",
        views.WorldgenSessionDetailView.as_view(),
        name="worldgen_session_detail",
    ),
    path(
        "worldgen/sessions/<uuid:session_id>/chat/",
        views.WorldgenSessionChatView.as_view(),
        name="worldgen_session_chat",
    ),
    path(
        "worldgen/sessions/<uuid:session_id>/update/",
        views.WorldgenSessionUpdateView.as_view(),
        name="worldgen_session_update",
    ),
    path(
        "worldgen/sessions/<uuid:session_id>/mode/",
        views.WorldgenSessionModeView.as_view(),
        name="worldgen_session_mode",
    ),
    path(
        "worldgen/sessions/<uuid:session_id>/finalize/",
        views.WorldgenSessionFinalizeView.as_view(),
        name="worldgen_session_finalize",
    ),
    path(
        "worldgen/sessions/<uuid:session_id>/assist/",
        views.WorldgenSessionAiAssistView.as_view(),
        name="worldgen_session_assist",
    ),
    # Router URLs
    path("", include(router.urls)),
    path("", include(universe_router.urls)),
    # Lore endpoints (Epic 5)
    path("<uuid:pk>/lore/upload/", views.LoreUploadView.as_view(), name="lore_upload"),
    path("<uuid:pk>/lore/", views.LoreListView.as_view(), name="lore_list"),
    path("<uuid:pk>/lore/query/", views.LoreQueryView.as_view(), name="lore_query"),
    path("<uuid:pk>/lore/stats/", views.LoreStatsView.as_view(), name="lore_stats"),
    # Placeholder views for future epics
    path("<uuid:pk>/timeline/", views.TimelineView.as_view(), name="universe_timeline"),
    # Export endpoint (Epic 11)
    path("<uuid:pk>/export/", views.UniverseExportView.as_view(), name="universe_export"),
]
