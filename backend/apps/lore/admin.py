"""Admin configuration for lore app."""

from django.contrib import admin

from apps.lore.models import LoreChunk


@admin.register(LoreChunk)
class LoreChunkAdmin(admin.ModelAdmin):
    """Admin for lore chunks."""

    list_display = ("chunk_type", "universe", "is_compacted", "created_at")
    list_filter = ("chunk_type", "is_compacted", "created_at")
    search_fields = ("text", "universe__name", "source_ref")
    readonly_fields = ("id", "created_at")
