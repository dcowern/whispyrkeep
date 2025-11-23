from django.urls import path

from apps.llm_config import views

urlpatterns = [
    path("config/", views.LlmConfigListCreateView.as_view(), name="llm_config_list"),
    path("config/<uuid:pk>/", views.LlmConfigDetailView.as_view(), name="llm_config_detail"),
    path("models/", views.LlmModelListView.as_view(), name="llm_model_list"),
    path("validate/", views.LlmEndpointValidateView.as_view(), name="llm_config_validate"),
]
