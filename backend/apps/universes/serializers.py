"""
Serializers for universe and homebrew content APIs.

Provides full CRUD serializers for homebrew content and read-only
serializers for universe and hard canon documents.
"""

from rest_framework import serializers

from apps.srd.serializers import (
    ConditionSerializer,
    DamageTypeSerializer,
    ItemCategorySerializer,
    MonsterTypeSerializer,
    SpellSchoolSerializer,
)

from .models import (
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

# ==================== Universe Serializers ====================


class UniverseSerializer(serializers.ModelSerializer):
    """Full serializer for Universe model."""

    class Meta:
        model = Universe
        fields = [
            "id",
            "name",
            "description",
            "tone_profile_json",
            "rules_profile_json",
            "calendar_profile_json",
            "current_universe_time",
            "canonical_lore_version",
            "is_archived",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "canonical_lore_version", "created_at", "updated_at"]


class UniverseSummarySerializer(serializers.ModelSerializer):
    """Minimal serializer for Universe list views."""

    class Meta:
        model = Universe
        fields = ["id", "name", "description", "is_archived", "created_at"]


class UniverseHardCanonDocSerializer(serializers.ModelSerializer):
    """Serializer for hard canon documents."""

    class Meta:
        model = UniverseHardCanonDoc
        fields = [
            "id",
            "universe",
            "source_type",
            "title",
            "raw_text",
            "checksum",
            "never_compact",
            "created_at",
        ]
        # universe is read-only since it's set from the URL in nested routes
        read_only_fields = ["id", "universe", "checksum", "created_at"]


# ==================== Base Homebrew Serializer ====================


class HomebrewBaseSerializer(serializers.ModelSerializer):
    """
    Base serializer for homebrew content.

    Handles common fields and validation for all homebrew models.
    """

    class Meta:
        fields = [
            "id",
            "universe",
            "name",
            "description",
            "source_type",
            "power_tier",
            "suggested_level_min",
            "suggested_level_max",
            "is_locked",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "universe", "created_at", "updated_at"]

    def validate(self, attrs):
        """Validate homebrew content."""
        # Prevent editing locked content
        if self.instance and self.instance.is_locked:
            raise serializers.ValidationError(
                "Cannot modify locked homebrew content. "
                "This content was locked after universe creation."
            )

        # Validate level band
        level_min = attrs.get(
            "suggested_level_min",
            self.instance.suggested_level_min if self.instance else 1,
        )
        level_max = attrs.get(
            "suggested_level_max",
            self.instance.suggested_level_max if self.instance else 20,
        )
        if level_min > level_max:
            raise serializers.ValidationError({
                "suggested_level_min": "Minimum level cannot exceed maximum level."
            })

        return attrs


# ==================== HomebrewSpecies Serializers ====================


class HomebrewSpeciesSerializer(HomebrewBaseSerializer):
    """Full serializer for HomebrewSpecies."""

    class Meta(HomebrewBaseSerializer.Meta):
        model = HomebrewSpecies
        fields = HomebrewBaseSerializer.Meta.fields + [
            "size",
            "speed",
            "ability_bonuses",
            "traits",
            "languages",
            "darkvision",
        ]


class HomebrewSpeciesSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for HomebrewSpecies list views."""

    class Meta:
        model = HomebrewSpecies
        fields = ["id", "name", "source_type", "power_tier", "size", "speed"]


# ==================== HomebrewSpell Serializers ====================


class HomebrewSpellSerializer(HomebrewBaseSerializer):
    """Full serializer for HomebrewSpell."""

    school = SpellSchoolSerializer(read_only=True)
    school_id = serializers.PrimaryKeyRelatedField(
        queryset=SpellSchoolSerializer.Meta.model.objects.all(),
        source="school",
        write_only=True,
    )
    damage_type = DamageTypeSerializer(read_only=True)
    damage_type_id = serializers.PrimaryKeyRelatedField(
        queryset=DamageTypeSerializer.Meta.model.objects.all(),
        source="damage_type",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta(HomebrewBaseSerializer.Meta):
        model = HomebrewSpell
        fields = HomebrewBaseSerializer.Meta.fields + [
            "level",
            "school",
            "school_id",
            "casting_time",
            "range",
            "components",
            "duration",
            "concentration",
            "ritual",
            "higher_levels",
            "damage_type",
            "damage_type_id",
            "dice_expression",
            "class_restrictions",
        ]


class HomebrewSpellSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for HomebrewSpell list views."""

    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = HomebrewSpell
        fields = [
            "id",
            "name",
            "level",
            "school_name",
            "concentration",
            "ritual",
            "source_type",
        ]


# ==================== HomebrewItem Serializers ====================


class HomebrewItemSerializer(HomebrewBaseSerializer):
    """Full serializer for HomebrewItem."""

    category = ItemCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ItemCategorySerializer.Meta.model.objects.all(),
        source="category",
        write_only=True,
    )
    damage_type = DamageTypeSerializer(read_only=True)
    damage_type_id = serializers.PrimaryKeyRelatedField(
        queryset=DamageTypeSerializer.Meta.model.objects.all(),
        source="damage_type",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta(HomebrewBaseSerializer.Meta):
        model = HomebrewItem
        fields = HomebrewBaseSerializer.Meta.fields + [
            "category",
            "category_id",
            "cost_gp",
            "weight_lb",
            "rarity",
            "magical",
            "requires_attunement",
            "attunement_requirements",
            "properties",
            # Weapon fields
            "is_weapon",
            "weapon_type",
            "damage_dice",
            "damage_type",
            "damage_type_id",
            "weapon_properties",
            "range_normal",
            "range_long",
            # Armor fields
            "is_armor",
            "armor_type",
            "base_ac",
            "dex_bonus",
            "strength_requirement",
            "stealth_disadvantage",
        ]

    def validate(self, attrs):
        """Validate item-specific fields."""
        attrs = super().validate(attrs)

        is_weapon = attrs.get("is_weapon", self.instance.is_weapon if self.instance else False)
        is_armor = attrs.get("is_armor", self.instance.is_armor if self.instance else False)

        if is_weapon and is_armor:
            raise serializers.ValidationError(
                "An item cannot be both a weapon and armor."
            )

        if is_weapon:
            if not attrs.get("weapon_type") and not (self.instance and self.instance.weapon_type):
                raise serializers.ValidationError({
                    "weapon_type": "Weapon type is required for weapons."
                })
            if not attrs.get("damage_dice") and not (self.instance and self.instance.damage_dice):
                raise serializers.ValidationError({
                    "damage_dice": "Damage dice is required for weapons."
                })

        if is_armor:
            if not attrs.get("armor_type") and not (self.instance and self.instance.armor_type):
                raise serializers.ValidationError({
                    "armor_type": "Armor type is required for armor."
                })
            base_ac = attrs.get("base_ac", self.instance.base_ac if self.instance else None)
            if base_ac is None:
                raise serializers.ValidationError({
                    "base_ac": "Base AC is required for armor."
                })

        return attrs


class HomebrewItemSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for HomebrewItem list views."""

    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = HomebrewItem
        fields = [
            "id",
            "name",
            "category_name",
            "rarity",
            "magical",
            "is_weapon",
            "is_armor",
            "source_type",
        ]


# ==================== HomebrewMonster Serializers ====================


class HomebrewMonsterSerializer(HomebrewBaseSerializer):
    """Full serializer for HomebrewMonster."""

    monster_type = MonsterTypeSerializer(read_only=True)
    monster_type_id = serializers.PrimaryKeyRelatedField(
        queryset=MonsterTypeSerializer.Meta.model.objects.all(),
        source="monster_type",
        write_only=True,
    )
    damage_vulnerabilities = DamageTypeSerializer(many=True, read_only=True)
    damage_vulnerability_ids = serializers.PrimaryKeyRelatedField(
        queryset=DamageTypeSerializer.Meta.model.objects.all(),
        source="damage_vulnerabilities",
        write_only=True,
        many=True,
        required=False,
    )
    damage_resistances = DamageTypeSerializer(many=True, read_only=True)
    damage_resistance_ids = serializers.PrimaryKeyRelatedField(
        queryset=DamageTypeSerializer.Meta.model.objects.all(),
        source="damage_resistances",
        write_only=True,
        many=True,
        required=False,
    )
    damage_immunities = DamageTypeSerializer(many=True, read_only=True)
    damage_immunity_ids = serializers.PrimaryKeyRelatedField(
        queryset=DamageTypeSerializer.Meta.model.objects.all(),
        source="damage_immunities",
        write_only=True,
        many=True,
        required=False,
    )
    condition_immunities = ConditionSerializer(many=True, read_only=True)
    condition_immunity_ids = serializers.PrimaryKeyRelatedField(
        queryset=ConditionSerializer.Meta.model.objects.all(),
        source="condition_immunities",
        write_only=True,
        many=True,
        required=False,
    )

    class Meta(HomebrewBaseSerializer.Meta):
        model = HomebrewMonster
        fields = HomebrewBaseSerializer.Meta.fields + [
            "monster_type",
            "monster_type_id",
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
            "damage_vulnerability_ids",
            "damage_resistances",
            "damage_resistance_ids",
            "damage_immunities",
            "damage_immunity_ids",
            "condition_immunities",
            "condition_immunity_ids",
            "senses",
            "languages",
            "challenge_rating",
            "experience_points",
            "traits",
            "actions",
            "reactions",
            "legendary_actions",
            "lair_actions",
            "regional_effects",
        ]


class HomebrewMonsterSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for HomebrewMonster list views."""

    monster_type_name = serializers.CharField(source="monster_type.name", read_only=True)

    class Meta:
        model = HomebrewMonster
        fields = [
            "id",
            "name",
            "monster_type_name",
            "challenge_rating",
            "size",
            "hit_points",
            "source_type",
        ]


# ==================== HomebrewFeat Serializers ====================


class HomebrewFeatSerializer(HomebrewBaseSerializer):
    """Full serializer for HomebrewFeat."""

    class Meta(HomebrewBaseSerializer.Meta):
        model = HomebrewFeat
        fields = HomebrewBaseSerializer.Meta.fields + [
            "prerequisites",
            "benefits",
            "ability_score_increase",
        ]


class HomebrewFeatSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for HomebrewFeat list views."""

    class Meta:
        model = HomebrewFeat
        fields = ["id", "name", "source_type", "power_tier"]


# ==================== HomebrewBackground Serializers ====================


class HomebrewBackgroundSerializer(HomebrewBaseSerializer):
    """Full serializer for HomebrewBackground."""

    class Meta(HomebrewBaseSerializer.Meta):
        model = HomebrewBackground
        fields = HomebrewBaseSerializer.Meta.fields + [
            "skill_proficiencies",
            "tool_proficiencies",
            "languages",
            "equipment",
            "feature_name",
            "feature_description",
            "suggested_characteristics",
        ]


class HomebrewBackgroundSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for HomebrewBackground list views."""

    class Meta:
        model = HomebrewBackground
        fields = ["id", "name", "source_type", "feature_name"]


# ==================== HomebrewClass Serializers ====================


class HomebrewClassSerializer(HomebrewBaseSerializer):
    """Full serializer for HomebrewClass."""

    class Meta(HomebrewBaseSerializer.Meta):
        model = HomebrewClass
        fields = HomebrewBaseSerializer.Meta.fields + [
            "hit_die",
            "primary_ability",
            "saving_throw_proficiencies",
            "armor_proficiencies",
            "weapon_proficiencies",
            "tool_proficiencies",
            "skill_choices",
            "starting_equipment",
            "spellcasting_ability",
            "features",
            "subclass_level",
            "spell_slots",
        ]


class HomebrewClassSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for HomebrewClass list views."""

    class Meta:
        model = HomebrewClass
        fields = ["id", "name", "source_type", "hit_die", "spellcasting_ability"]


# ==================== HomebrewSubclass Serializers ====================


class HomebrewSubclassSerializer(HomebrewBaseSerializer):
    """Full serializer for HomebrewSubclass."""

    parent_class = HomebrewClassSummarySerializer(read_only=True)
    parent_class_id = serializers.PrimaryKeyRelatedField(
        queryset=HomebrewClass.objects.all(),
        source="parent_class",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta(HomebrewBaseSerializer.Meta):
        model = HomebrewSubclass
        fields = HomebrewBaseSerializer.Meta.fields + [
            "parent_class",
            "parent_class_id",
            "srd_parent_class_name",
            "subclass_level",
            "features",
        ]

    def validate(self, attrs):
        """Validate that either parent_class or srd_parent_class_name is provided."""
        attrs = super().validate(attrs)

        parent_class = attrs.get(
            "parent_class",
            self.instance.parent_class if self.instance else None,
        )
        srd_parent = attrs.get(
            "srd_parent_class_name",
            self.instance.srd_parent_class_name if self.instance else "",
        )

        if not parent_class and not srd_parent:
            raise serializers.ValidationError(
                "Either parent_class or srd_parent_class_name must be provided."
            )

        if parent_class and srd_parent:
            raise serializers.ValidationError(
                "Cannot specify both parent_class and srd_parent_class_name."
            )

        return attrs


class HomebrewSubclassSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for HomebrewSubclass list views."""

    parent_class_name = serializers.CharField(
        source="parent_class.name",
        read_only=True,
        default=None,
    )

    class Meta:
        model = HomebrewSubclass
        fields = [
            "id",
            "name",
            "source_type",
            "parent_class_name",
            "srd_parent_class_name",
        ]
