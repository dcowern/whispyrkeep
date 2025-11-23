from django.urls import path

from apps.llm_config import views

urlpatterns = [
    path("config/", views.LlmConfigListCreateView.as_view(), name="llm_config_list"),
    path("config/<uuid:pk>/", views.LlmConfigDetailView.as_view(), name="llm_config_detail"),
]
