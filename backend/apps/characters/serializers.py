"""
Serializers for CharacterSheet API.

Provides full CRUD serializers for character sheets with validation support.
"""

from rest_framework import serializers

from .models import CharacterSheet


class CharacterSheetSerializer(serializers.ModelSerializer):
    """
    Full serializer for CharacterSheet model.

    Includes all fields and handles JSON field validation.
    """

    # Computed properties (read-only)
    proficiency_bonus = serializers.IntegerField(read_only=True)
    is_multiclass = serializers.BooleanField(read_only=True)

    class Meta:
        model = CharacterSheet
        fields = [
            # Core identification
            "id",
            "user",
            "universe",
            # Basic info
            "name",
            "species",
            "character_class",
            "subclass",
            "background",
            "alignment",
            "size",
            # Level and XP
            "level",
            "experience_points",
            "multiclass_json",
            # Hit Points
            "hit_points_max",
            "hit_points_current",
            "hit_points_temp",
            "hit_dice_json",
            # Core stats
            "ability_scores_json",
            "skills_json",
            "proficiencies_json",
            # Speed and movement
            "speed",
            "speed_modifiers_json",
            # Defense
            "armor_class",
            "armor_class_base",
            "initiative_bonus",
            # Features and abilities
            "features_json",
            # Magic
            "spellbook_json",
            # Equipment
            "equipment_json",
            # Personality
            "personality_json",
            # Homebrew overrides
            "homebrew_overrides_json",
            # Conditions and status
            "conditions_json",
            "death_saves_json",
            # Character notes
            "backstory",
            "notes",
            "appearance",
            # Inspiration
            "has_inspiration",
            # Timestamps
            "created_at",
            "updated_at",
            # Computed properties
            "proficiency_bonus",
            "is_multiclass",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def validate_level(self, value):
        """Validate level is between 1 and 20."""
        if value < 1 or value > 20:
            raise serializers.ValidationError("Level must be between 1 and 20")
        return value

    def validate_ability_scores_json(self, value):
        """Validate ability scores structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Ability scores must be a dictionary")

        required_abilities = ["str", "dex", "con", "int", "wis", "cha"]
        for ability in required_abilities:
            if ability not in value:
                raise serializers.ValidationError(f"Missing ability score: {ability}")
            score = value[ability]
            if not isinstance(score, int) or score < 1 or score > 30:
                raise serializers.ValidationError(
                    f"Ability score for {ability} must be integer between 1 and 30"
                )

        return value

    def validate_multiclass_json(self, value):
        """Validate multiclass JSON structure."""
        if not value:
            return value

        if not isinstance(value, dict):
            raise serializers.ValidationError("Multiclass data must be a dictionary")

        for class_name, level in value.items():
            if not isinstance(level, int) or level < 1:
                raise serializers.ValidationError(
                    f"Multiclass level for {class_name} must be a positive integer"
                )

        return value

    def validate(self, attrs):
        """Cross-field validation."""
        # Validate multiclass levels sum to total level
        multiclass = attrs.get("multiclass_json")
        level = attrs.get("level")

        if multiclass and level:
            total_multiclass = sum(multiclass.values())
            if total_multiclass != level:
                raise serializers.ValidationError({
                    "multiclass_json": (
                        f"Multiclass levels ({total_multiclass}) "
                        f"must sum to total level ({level})"
                    )
                })

        return attrs

    def create(self, validated_data):
        """Create character with current user."""
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class CharacterSheetSummarySerializer(serializers.ModelSerializer):
    """
    Summary serializer for character list views.

    Includes only essential fields for display in lists.
    """

    proficiency_bonus = serializers.IntegerField(read_only=True)

    class Meta:
        model = CharacterSheet
        fields = [
            "id",
            "name",
            "species",
            "character_class",
            "subclass",
            "level",
            "hit_points_current",
            "hit_points_max",
            "proficiency_bonus",
            "updated_at",
        ]


class CharacterSheetCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for character creation with minimal required fields.

    Used when creating a new character with defaults.
    """

    class Meta:
        model = CharacterSheet
        fields = [
            "name",
            "species",
            "character_class",
            "background",
            "universe",
            # Optional at creation
            "subclass",
            "alignment",
            "size",
            "level",
            "ability_scores_json",
        ]
        extra_kwargs = {
            "subclass": {"required": False},
            "alignment": {"required": False},
            "size": {"required": False},
            "level": {"required": False},
            "ability_scores_json": {"required": False},
        }

    def create(self, validated_data):
        """Create character with current user."""
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class CharacterUpdateHPSerializer(serializers.Serializer):
    """Serializer for updating character HP."""

    hit_points_current = serializers.IntegerField(min_value=0, required=False)
    hit_points_temp = serializers.IntegerField(min_value=0, required=False)
    damage = serializers.IntegerField(min_value=0, required=False)
    healing = serializers.IntegerField(min_value=0, required=False)


class CharacterConditionSerializer(serializers.Serializer):
    """Serializer for adding/removing conditions."""

    condition = serializers.CharField(max_length=50)
    action = serializers.ChoiceField(choices=["add", "remove"])


class CharacterValidationSerializer(serializers.Serializer):
    """
    Serializer for validation endpoint response.

    Returns validation results for a character sheet.
    """

    is_valid = serializers.BooleanField()
    errors = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )
    warnings = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )
