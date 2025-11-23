"""Admin configuration for campaigns app."""

from django.contrib import admin

from apps.campaigns.models import Campaign, CanonicalCampaignState, TurnEvent


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Admin for campaigns."""

    list_display = ("title", "universe", "user", "mode", "status", "created_at")
    list_filter = ("mode", "status", "failure_style", "content_rating", "created_at")
    search_fields = ("title", "user__email", "universe__name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(TurnEvent)
class TurnEventAdmin(admin.ModelAdmin):
    """Admin for turn events."""

    list_display = ("campaign", "turn_index", "created_at")
    list_filter = ("created_at",)
    search_fields = ("campaign__title", "user_input_text")
    readonly_fields = ("id", "canonical_state_hash", "created_at")
    ordering = ("campaign", "turn_index")


@admin.register(CanonicalCampaignState)
class CanonicalCampaignStateAdmin(admin.ModelAdmin):
    """Admin for campaign state snapshots."""

    list_display = ("campaign", "turn_index", "created_at")
    list_filter = ("created_at",)
    search_fields = ("campaign__title",)
    readonly_fields = ("id", "created_at")
