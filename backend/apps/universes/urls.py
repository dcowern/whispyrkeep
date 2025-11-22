from django.urls import path

from apps.universes import views

urlpatterns = [
    path("", views.UniverseListCreateView.as_view(), name="universe_list"),
    path("<uuid:pk>/", views.UniverseDetailView.as_view(), name="universe_detail"),
    path("<uuid:pk>/worldgen/", views.WorldgenView.as_view(), name="universe_worldgen"),
    path("<uuid:pk>/lore/upload/", views.LoreUploadView.as_view(), name="lore_upload"),
    path("<uuid:pk>/lore/", views.LoreListView.as_view(), name="lore_list"),
    path("<uuid:pk>/timeline/", views.TimelineView.as_view(), name="universe_timeline"),
]
