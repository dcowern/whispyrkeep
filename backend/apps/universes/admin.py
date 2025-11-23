"""Admin configuration for universes app."""

from django.contrib import admin

from apps.universes.models import Universe, UniverseHardCanonDoc


@admin.register(Universe)
class UniverseAdmin(admin.ModelAdmin):
    """Admin for universes."""

    list_display = ("name", "user", "is_archived", "created_at")
    list_filter = ("is_archived", "created_at")
    search_fields = ("name", "user__email", "description")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(UniverseHardCanonDoc)
class UniverseHardCanonDocAdmin(admin.ModelAdmin):
    """Admin for hard canon documents."""

    list_display = ("title", "universe", "source_type", "never_compact", "created_at")
    list_filter = ("source_type", "never_compact", "created_at")
    search_fields = ("title", "universe__name")
    readonly_fields = ("id", "checksum", "created_at")
