"""Admin configuration for universes app."""

from django.contrib import admin

from apps.universes.models import (
    HomebrewBackground,
    HomebrewClass,
    HomebrewFeat,
    HomebrewItem,
    HomebrewMonster,
    HomebrewSpecies,
    HomebrewSpell,
    HomebrewSubclass,
    Universe,
    UniverseHardCanonDoc,
)


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


class HomebrewBaseAdmin(admin.ModelAdmin):
    """Base admin for all homebrew models."""

    list_filter = ("source_type", "power_tier", "is_locked", "created_at")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(HomebrewSpecies)
class HomebrewSpeciesAdmin(HomebrewBaseAdmin):
    """Admin for homebrew species."""

    list_display = ("name", "universe", "source_type", "power_tier", "size", "is_locked")
    search_fields = ("name", "universe__name", "description")


@admin.register(HomebrewSpell)
class HomebrewSpellAdmin(HomebrewBaseAdmin):
    """Admin for homebrew spells."""

    list_display = ("name", "universe", "level", "school", "source_type", "is_locked")
    list_filter = HomebrewBaseAdmin.list_filter + ("level", "school", "concentration", "ritual")
    search_fields = ("name", "universe__name", "description")


@admin.register(HomebrewItem)
class HomebrewItemAdmin(HomebrewBaseAdmin):
    """Admin for homebrew items."""

    list_display = ("name", "universe", "category", "rarity", "magical", "is_locked")
    list_filter = HomebrewBaseAdmin.list_filter + ("category", "rarity", "magical", "is_weapon", "is_armor")
    search_fields = ("name", "universe__name", "description")


@admin.register(HomebrewMonster)
class HomebrewMonsterAdmin(HomebrewBaseAdmin):
    """Admin for homebrew monsters."""

    list_display = ("name", "universe", "monster_type", "challenge_rating", "size", "is_locked")
    list_filter = HomebrewBaseAdmin.list_filter + ("monster_type", "size")
    search_fields = ("name", "universe__name", "description")


@admin.register(HomebrewFeat)
class HomebrewFeatAdmin(HomebrewBaseAdmin):
    """Admin for homebrew feats."""

    list_display = ("name", "universe", "source_type", "power_tier", "is_locked")
    search_fields = ("name", "universe__name", "description")


@admin.register(HomebrewBackground)
class HomebrewBackgroundAdmin(HomebrewBaseAdmin):
    """Admin for homebrew backgrounds."""

    list_display = ("name", "universe", "source_type", "feature_name", "is_locked")
    search_fields = ("name", "universe__name", "description", "feature_name")


@admin.register(HomebrewClass)
class HomebrewClassAdmin(HomebrewBaseAdmin):
    """Admin for homebrew classes."""

    list_display = ("name", "universe", "hit_die", "source_type", "is_locked")
    search_fields = ("name", "universe__name", "description")


@admin.register(HomebrewSubclass)
class HomebrewSubclassAdmin(HomebrewBaseAdmin):
    """Admin for homebrew subclasses."""

    list_display = ("name", "universe", "parent_class", "srd_parent_class_name", "is_locked")
    search_fields = ("name", "universe__name", "description", "srd_parent_class_name")
