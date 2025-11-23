"""Admin configuration for characters app."""

from django.contrib import admin

from apps.characters.models import CharacterSheet


@admin.register(CharacterSheet)
class CharacterSheetAdmin(admin.ModelAdmin):
    """Admin for character sheets."""

    list_display = ("name", "character_class", "level", "user", "created_at")
    list_filter = ("character_class", "level", "created_at")
    search_fields = ("name", "user__email", "species", "background")
    readonly_fields = ("id", "created_at", "updated_at")
