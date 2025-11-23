"""
URL configuration for Lore API.

All lore endpoints are nested under universes.
"""

from django.urls import path

from apps.lore import views

urlpatterns = [
    # Hard Canon Documents
    path(
        "<uuid:universe_id>/hard-canon/",
        views.UniverseHardCanonListView.as_view(),
        name="universe_hard_canon_list",
    ),
    path(
        "<uuid:universe_id>/hard-canon/upload/",
        views.UniverseHardCanonUploadView.as_view(),
        name="universe_hard_canon_upload",
    ),
    path(
        "<uuid:universe_id>/hard-canon/<uuid:doc_id>/",
        views.HardCanonDocDetailView.as_view(),
        name="hard_canon_doc_detail",
    ),
    # Lore Query & Stats
    path(
        "<uuid:universe_id>/lore/query/",
        views.UniverseLoreQueryView.as_view(),
        name="universe_lore_query",
    ),
    path(
        "<uuid:universe_id>/lore/stats/",
        views.UniverseLoreStatsView.as_view(),
        name="universe_lore_stats",
    ),
]
