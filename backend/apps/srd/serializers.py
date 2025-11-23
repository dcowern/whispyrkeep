"""
Serializers for SRD catalog API.

These serializers provide read-only access to SRD 5.2 reference data.
"""

from rest_framework import serializers

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


class AbilityScoreSerializer(serializers.ModelSerializer):
    """Serializer for ability scores."""

    class Meta:
        model = AbilityScore
        fields = ("id", "abbreviation", "name", "description")


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for skills."""

    ability_score = AbilityScoreSerializer(read_only=True)
    ability_score_id = serializers.PrimaryKeyRelatedField(
        queryset=AbilityScore.objects.all(),
        source="ability_score",
        write_only=True,
    )

    class Meta:
        model = Skill
        fields = ("id", "name", "ability_score", "ability_score_id", "description")


class SkillSummarySerializer(serializers.ModelSerializer):
    """Minimal skill serializer for nested use."""

    ability = serializers.CharField(source="ability_score.abbreviation", read_only=True)

    class Meta:
        model = Skill
        fields = ("id", "name", "ability")


class ConditionSerializer(serializers.ModelSerializer):
    """Serializer for conditions."""

    class Meta:
        model = Condition
        fields = ("id", "name", "description", "effects")


class DamageTypeSerializer(serializers.ModelSerializer):
    """Serializer for damage types."""

    class Meta:
        model = DamageType
        fields = ("id", "name", "description")


class SpeciesSerializer(serializers.ModelSerializer):
    """Serializer for playable species/races."""

    class Meta:
        model = Species
        fields = (
            "id",
            "name",
            "description",
            "size",
            "speed",
            "ability_bonuses",
            "traits",
            "languages",
            "darkvision",
        )


class SubclassSerializer(serializers.ModelSerializer):
    """Serializer for subclasses."""

    class Meta:
        model = Subclass
        fields = (
            "id",
            "name",
            "character_class",
            "description",
            "subclass_level",
            "features",
        )


class SubclassSummarySerializer(serializers.ModelSerializer):
    """Minimal subclass serializer for nested use."""

    class Meta:
        model = Subclass
        fields = ("id", "name", "subclass_level")


class CharacterClassSerializer(serializers.ModelSerializer):
    """Serializer for character classes."""

    primary_ability = AbilityScoreSerializer(read_only=True)
    spellcasting_ability = AbilityScoreSerializer(read_only=True)
    saving_throw_proficiencies = AbilityScoreSerializer(many=True, read_only=True)
    subclasses = SubclassSummarySerializer(many=True, read_only=True)

    class Meta:
        model = CharacterClass
        fields = (
            "id",
            "name",
            "description",
            "hit_die",
            "primary_ability",
            "spellcasting_ability",
            "saving_throw_proficiencies",
            "armor_proficiencies",
            "weapon_proficiencies",
            "tool_proficiencies",
            "skill_choices",
            "starting_equipment",
            "features",
            "subclasses",
        )


class CharacterClassSummarySerializer(serializers.ModelSerializer):
    """Minimal class serializer for nested use."""

    class Meta:
        model = CharacterClass
        fields = ("id", "name", "hit_die")


class BackgroundSerializer(serializers.ModelSerializer):
    """Serializer for backgrounds."""

    skill_proficiencies = SkillSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Background
        fields = (
            "id",
            "name",
            "description",
            "skill_proficiencies",
            "tool_proficiencies",
            "languages",
            "equipment",
            "feature_name",
            "feature_description",
            "suggested_characteristics",
        )


class SpellSchoolSerializer(serializers.ModelSerializer):
    """Serializer for spell schools."""

    class Meta:
        model = SpellSchool
        fields = ("id", "name", "description")


class SpellSerializer(serializers.ModelSerializer):
    """Serializer for spells."""

    school = SpellSchoolSerializer(read_only=True)
    damage_type = DamageTypeSerializer(read_only=True)
    classes = CharacterClassSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Spell
        fields = (
            "id",
            "name",
            "level",
            "school",
            "casting_time",
            "range",
            "components",
            "duration",
            "concentration",
            "ritual",
            "description",
            "higher_levels",
            "classes",
            "damage_type",
            "dice_expression",
        )


class SpellSummarySerializer(serializers.ModelSerializer):
    """Minimal spell serializer for listing."""

    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = Spell
        fields = ("id", "name", "level", "school_name", "concentration", "ritual")


class ItemCategorySerializer(serializers.ModelSerializer):
    """Serializer for item categories."""

    class Meta:
        model = ItemCategory
        fields = ("id", "name", "description")


class WeaponStatsSerializer(serializers.ModelSerializer):
    """Serializer for weapon statistics."""

    damage_type = DamageTypeSerializer(read_only=True)

    class Meta:
        model = Weapon
        fields = (
            "weapon_type",
            "damage_dice",
            "damage_type",
            "properties",
            "range_normal",
            "range_long",
            "versatile_dice",
        )


class ArmorStatsSerializer(serializers.ModelSerializer):
    """Serializer for armor statistics."""

    class Meta:
        model = Armor
        fields = (
            "armor_type",
            "base_ac",
            "dex_bonus",
            "strength_requirement",
            "stealth_disadvantage",
            "don_time",
            "doff_time",
        )


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for items."""

    category = ItemCategorySerializer(read_only=True)
    weapon_stats = WeaponStatsSerializer(read_only=True)
    armor_stats = ArmorStatsSerializer(read_only=True)

    class Meta:
        model = Item
        fields = (
            "id",
            "name",
            "category",
            "description",
            "cost_gp",
            "weight_lb",
            "rarity",
            "magical",
            "requires_attunement",
            "attunement_requirements",
            "properties",
            "weapon_stats",
            "armor_stats",
        )


class ItemSummarySerializer(serializers.ModelSerializer):
    """Minimal item serializer for listing."""

    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Item
        fields = ("id", "name", "category_name", "cost_gp", "rarity", "magical")


class MonsterTypeSerializer(serializers.ModelSerializer):
    """Serializer for monster types."""

    class Meta:
        model = MonsterType
        fields = ("id", "name", "description")


class MonsterSerializer(serializers.ModelSerializer):
    """Serializer for monsters."""

    monster_type = MonsterTypeSerializer(read_only=True)
    damage_vulnerabilities = DamageTypeSerializer(many=True, read_only=True)
    damage_resistances = DamageTypeSerializer(many=True, read_only=True)
    damage_immunities = DamageTypeSerializer(many=True, read_only=True)
    condition_immunities = ConditionSerializer(many=True, read_only=True)

    class Meta:
        model = Monster
        fields = (
            "id",
            "name",
            "monster_type",
            "size",
            "alignment",
            "armor_class",
            "armor_description",
            "hit_points",
            "hit_dice",
            "speed",
            "ability_scores",
            "saving_throws",
            "skills",
            "damage_vulnerabilities",
            "damage_resistances",
            "damage_immunities",
            "condition_immunities",
            "senses",
            "languages",
            "challenge_rating",
            "experience_points",
            "traits",
            "actions",
            "reactions",
            "legendary_actions",
            "description",
        )


class MonsterSummarySerializer(serializers.ModelSerializer):
    """Minimal monster serializer for listing."""

    monster_type_name = serializers.CharField(source="monster_type.name", read_only=True)

    class Meta:
        model = Monster
        fields = (
            "id",
            "name",
            "monster_type_name",
            "size",
            "challenge_rating",
            "hit_points",
        )


class FeatSerializer(serializers.ModelSerializer):
    """Serializer for feats."""

    class Meta:
        model = Feat
        fields = ("id", "name", "description", "prerequisites", "benefits")
