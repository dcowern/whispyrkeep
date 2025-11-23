"""Admin configuration for SRD models."""

from django.contrib import admin

from .models import (
    AbilityScore,
    Armor,
    Background,
    CharacterClass,
    Condition,
    DamageType,
    Feat,
    Item,
    ItemCategory,
    Monster,
    MonsterType,
    Skill,
    Species,
    Spell,
    SpellSchool,
    Subclass,
    Weapon,
)


@admin.register(AbilityScore)
class AbilityScoreAdmin(admin.ModelAdmin):
    list_display = ("abbreviation", "name")
    search_fields = ("name", "abbreviation")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "ability_score")
    list_filter = ("ability_score",)
    search_fields = ("name",)


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(DamageType)
class DamageTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ("name", "size", "speed", "darkvision")
    list_filter = ("size",)
    search_fields = ("name",)


@admin.register(CharacterClass)
class CharacterClassAdmin(admin.ModelAdmin):
    list_display = ("name", "hit_die", "primary_ability", "spellcasting_ability")
    list_filter = ("hit_die",)
    search_fields = ("name",)


@admin.register(Subclass)
class SubclassAdmin(admin.ModelAdmin):
    list_display = ("name", "character_class", "subclass_level")
    list_filter = ("character_class", "subclass_level")
    search_fields = ("name",)


@admin.register(Background)
class BackgroundAdmin(admin.ModelAdmin):
    list_display = ("name", "feature_name")
    search_fields = ("name", "feature_name")


@admin.register(SpellSchool)
class SpellSchoolAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Spell)
class SpellAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "school", "casting_time", "concentration", "ritual")
    list_filter = ("level", "school", "concentration", "ritual")
    search_fields = ("name",)
    filter_horizontal = ("classes",)


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "cost_gp", "rarity", "magical")
    list_filter = ("category", "rarity", "magical", "requires_attunement")
    search_fields = ("name",)


@admin.register(Weapon)
class WeaponAdmin(admin.ModelAdmin):
    list_display = ("item", "weapon_type", "damage_dice", "damage_type")
    list_filter = ("weapon_type", "damage_type")
    search_fields = ("item__name",)


@admin.register(Armor)
class ArmorAdmin(admin.ModelAdmin):
    list_display = ("item", "armor_type", "base_ac", "stealth_disadvantage")
    list_filter = ("armor_type", "stealth_disadvantage")
    search_fields = ("item__name",)


@admin.register(MonsterType)
class MonsterTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Monster)
class MonsterAdmin(admin.ModelAdmin):
    list_display = ("name", "monster_type", "size", "challenge_rating", "hit_points")
    list_filter = ("monster_type", "size", "challenge_rating")
    search_fields = ("name",)


@admin.register(Feat)
class FeatAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
