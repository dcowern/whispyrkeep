"""
Serializers for characters app.

Handles CharacterSheet CRUD serialization with SRD validation.
"""

from rest_framework import serializers

from apps.characters.models import CharacterSheet
from apps.characters.services import CharacterValidationService


class CharacterListSerializer(serializers.ModelSerializer):
    """Serializer for character list view - minimal fields."""

    class Meta:
        model = CharacterSheet
        fields = (
            "id",
            "name",
            "species",
            "character_class",
            "subclass",
            "level",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CharacterDetailSerializer(serializers.ModelSerializer):
    """Serializer for character detail view - all fields."""

    validation_warnings = serializers.SerializerMethodField()

    class Meta:
        model = CharacterSheet
        fields = (
            "id",
            "user",
            "universe",
            "name",
            "species",
            "character_class",
            "subclass",
            "background",
            "level",
            "ability_scores_json",
            "skills_json",
            "proficiencies_json",
            "features_json",
            "spellbook_json",
            "equipment_json",
            "homebrew_overrides_json",
            "created_at",
            "updated_at",
            "validation_warnings",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at", "validation_warnings")

    def get_validation_warnings(self, obj) -> list[str]:
        """Run validation and return any warnings."""
        service = CharacterValidationService(universe=obj.universe)
        result = service.validate(
            name=obj.name,
            species=obj.species,
            character_class=obj.character_class,
            background=obj.background,
            level=obj.level,
            subclass=obj.subclass,
            ability_scores=obj.ability_scores_json,
            skills=obj.skills_json,
            spellbook=obj.spellbook_json,
        )
        return result.warnings


class CharacterCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new characters with validation."""

    class Meta:
        model = CharacterSheet
        fields = (
            "universe",
            "name",
            "species",
            "character_class",
            "subclass",
            "background",
            "level",
            "ability_scores_json",
            "skills_json",
            "proficiencies_json",
            "features_json",
            "spellbook_json",
            "equipment_json",
            "homebrew_overrides_json",
        )

    def validate(self, attrs):
        """Validate character data against SRD rules."""
        universe = attrs.get("universe")
        service = CharacterValidationService(universe=universe)

        result = service.validate(
            name=attrs.get("name", ""),
            species=attrs.get("species", ""),
            character_class=attrs.get("character_class", ""),
            background=attrs.get("background", ""),
            level=attrs.get("level", 1),
            subclass=attrs.get("subclass", ""),
            ability_scores=attrs.get("ability_scores_json"),
            skills=attrs.get("skills_json"),
            spellbook=attrs.get("spellbook_json"),
        )

        if not result.is_valid:
            # Convert validation errors to DRF format
            errors = {}
            for error in result.errors:
                if error.field not in errors:
                    errors[error.field] = []
                errors[error.field].append(error.message)
            raise serializers.ValidationError(errors)

        # Store warnings for later access
        self._validation_warnings = result.warnings
        return attrs

    def create(self, validated_data):
        """Create character with the authenticated user."""
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class CharacterUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing characters."""

    class Meta:
        model = CharacterSheet
        fields = (
            "universe",
            "name",
            "species",
            "character_class",
            "subclass",
            "background",
            "level",
            "ability_scores_json",
            "skills_json",
            "proficiencies_json",
            "features_json",
            "spellbook_json",
            "equipment_json",
            "homebrew_overrides_json",
        )

    def validate(self, attrs):
        """Validate updated character data."""
        # Merge with existing data for partial updates
        instance = self.instance
        name = attrs.get("name", instance.name if instance else "")
        species = attrs.get("species", instance.species if instance else "")
        character_class = attrs.get(
            "character_class", instance.character_class if instance else ""
        )
        background = attrs.get("background", instance.background if instance else "")
        level = attrs.get("level", instance.level if instance else 1)
        subclass = attrs.get("subclass", instance.subclass if instance else "")
        universe = attrs.get("universe", instance.universe if instance else None)
        ability_scores = attrs.get(
            "ability_scores_json", instance.ability_scores_json if instance else {}
        )
        skills = attrs.get("skills_json", instance.skills_json if instance else {})
        spellbook = attrs.get(
            "spellbook_json", instance.spellbook_json if instance else {}
        )

        service = CharacterValidationService(universe=universe)
        result = service.validate(
            name=name,
            species=species,
            character_class=character_class,
            background=background,
            level=level,
            subclass=subclass,
            ability_scores=ability_scores,
            skills=skills,
            spellbook=spellbook,
        )

        if not result.is_valid:
            errors = {}
            for error in result.errors:
                if error.field not in errors:
                    errors[error.field] = []
                errors[error.field].append(error.message)
            raise serializers.ValidationError(errors)

        self._validation_warnings = result.warnings
        return attrs
