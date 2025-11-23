"""Admin configuration for LLM config app."""

from django.contrib import admin

from apps.llm_config.models import LlmEndpointConfig


@admin.register(LlmEndpointConfig)
class LlmEndpointConfigAdmin(admin.ModelAdmin):
    """Admin for LLM endpoint configurations."""

    list_display = ("provider_name", "default_model", "user", "is_active", "created_at")
    list_filter = ("provider_name", "is_active", "created_at")
    search_fields = ("user__email", "provider_name", "default_model")
    readonly_fields = ("id", "created_at", "updated_at")

    # Never show encrypted API key
    exclude = ("api_key_encrypted",)
