from django.urls import path

from apps.characters import views

urlpatterns = [
    path("", views.CharacterListCreateView.as_view(), name="character_list"),
    path("<uuid:id>/", views.CharacterDetailView.as_view(), name="character_detail"),
]
