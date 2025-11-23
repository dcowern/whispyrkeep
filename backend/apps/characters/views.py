"""
Character API views.

Provides ViewSets for character CRUD operations with validation support.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CharacterSheet
from .serializers import (
    CharacterConditionSerializer,
    CharacterSheetCreateSerializer,
    CharacterSheetSerializer,
    CharacterSheetSummarySerializer,
    CharacterUpdateHPSerializer,
)
from .services.validation import CharacterValidationService


class CharacterSheetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CharacterSheet CRUD operations.

    Endpoints:
        GET    /api/characters/              - List user's characters
        POST   /api/characters/              - Create new character
        GET    /api/characters/{id}/         - Get character details
        PUT    /api/characters/{id}/         - Update character
        PATCH  /api/characters/{id}/         - Partial update character
        DELETE /api/characters/{id}/         - Delete character
        POST   /api/characters/{id}/validate/ - Validate character
        POST   /api/characters/{id}/hp/      - Update HP (damage/heal)
        POST   /api/characters/{id}/condition/ - Add/remove condition
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return characters owned by the current user."""
        return CharacterSheet.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return CharacterSheetSummarySerializer
        elif self.action == "create":
            return CharacterSheetCreateSerializer
        return CharacterSheetSerializer

    def perform_create(self, serializer):
        """Create character with current user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def validate(self, request, pk=None):
        """
        Validate character against SRD rules.

        POST /api/characters/{id}/validate/

        Optional query params:
            - strict_ability_scores: Enforce standard array/point buy
            - skip_spells: Skip spell validation
            - skip_equipment: Skip equipment validation

        Returns:
            {
                "is_valid": true/false,
                "errors": [...],
                "warnings": [...]
            }
        """
        character = self.get_object()

        # Get validation options from query params
        strict = request.query_params.get("strict_ability_scores", "false").lower() == "true"
        validate_spells = request.query_params.get("skip_spells", "false").lower() != "true"
        validate_equipment = (
            request.query_params.get("skip_equipment", "false").lower() != "true"
        )

        # Create validator with universe context if character has one
        validator = CharacterValidationService(universe=character.universe)

        # Run validation
        result = validator.validate(
            character,
            validate_spells=validate_spells,
            validate_equipment=validate_equipment,
            strict_ability_scores=strict,
        )

        # Format response
        response_data = {
            "is_valid": result.is_valid,
            "errors": [
                {
                    "field": e.field,
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
                for e in result.errors
            ],
            "warnings": [
                {
                    "field": w.field,
                    "code": w.code,
                    "message": w.message,
                    "details": w.details,
                }
                for w in result.warnings
            ],
        }

        return Response(
            response_data,
            status=status.HTTP_200_OK if result.is_valid else status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @action(detail=True, methods=["post"])
    def hp(self, request, pk=None):
        """
        Update character HP (damage or healing).

        POST /api/characters/{id}/hp/

        Body options:
            - hit_points_current: Set current HP directly
            - hit_points_temp: Set temp HP directly
            - damage: Apply damage amount
            - healing: Apply healing amount

        Damage is applied to temp HP first, then current HP.
        Healing cannot exceed max HP.

        Returns the updated character.
        """
        character = self.get_object()
        serializer = CharacterUpdateHPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Direct HP setting
        if "hit_points_current" in data:
            character.hit_points_current = min(data["hit_points_current"], character.hit_points_max)

        if "hit_points_temp" in data:
            character.hit_points_temp = data["hit_points_temp"]

        # Apply damage (temp HP absorbs first)
        if "damage" in data:
            damage = data["damage"]
            if character.hit_points_temp > 0:
                temp_absorbed = min(damage, character.hit_points_temp)
                character.hit_points_temp -= temp_absorbed
                damage -= temp_absorbed
            character.hit_points_current = max(0, character.hit_points_current - damage)

        # Apply healing (cannot exceed max HP)
        if "healing" in data:
            character.hit_points_current = min(
                character.hit_points_current + data["healing"],
                character.hit_points_max,
            )

        character.save()

        return Response(CharacterSheetSerializer(character).data)

    @action(detail=True, methods=["post"])
    def condition(self, request, pk=None):
        """
        Add or remove a condition from the character.

        POST /api/characters/{id}/condition/

        Body:
            {
                "condition": "poisoned",
                "action": "add" | "remove"
            }

        Returns the updated character.
        """
        character = self.get_object()
        serializer = CharacterConditionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        condition = data["condition"].lower()
        action_type = data["action"]

        # Ensure conditions_json is a list
        if not isinstance(character.conditions_json, list):
            character.conditions_json = []

        conditions = character.conditions_json.copy()

        if action_type == "add":
            if condition not in conditions:
                conditions.append(condition)
        elif action_type == "remove" and condition in conditions:
            conditions.remove(condition)

        character.conditions_json = conditions
        character.save()

        return Response(CharacterSheetSerializer(character).data)

    @action(detail=True, methods=["post"])
    def rest(self, request, pk=None):
        """
        Apply rest effects to the character.

        POST /api/characters/{id}/rest/

        Body:
            {
                "rest_type": "short" | "long"
            }

        Short rest:
            - Can spend hit dice to recover HP

        Long rest:
            - Recover all HP
            - Recover half of max hit dice (rounded down)
            - Reset spell slots to max

        Returns the updated character.
        """
        character = self.get_object()
        rest_type = request.data.get("rest_type", "short")

        if rest_type == "long":
            # Recover all HP
            character.hit_points_current = character.hit_points_max
            character.hit_points_temp = 0

            # Recover half of max hit dice
            if isinstance(character.hit_dice_json, dict):
                hit_dice = character.hit_dice_json.copy()
                for _die_type, data in hit_dice.items():
                    if isinstance(data, dict):
                        max_dice = data.get("max", 0)
                        recovery = max(1, max_dice // 2)
                        current_spent = data.get("spent", 0)
                        data["spent"] = max(0, current_spent - recovery)
                character.hit_dice_json = hit_dice

            # Reset spell slots
            if isinstance(character.spellbook_json, dict) and "spell_slots" in character.spellbook_json:
                spellbook = character.spellbook_json.copy()
                for _level, slots in spellbook.get("spell_slots", {}).items():
                    if isinstance(slots, dict):
                        slots["used"] = 0
                character.spellbook_json = spellbook

            # Clear death saves
            character.death_saves_json = {"successes": 0, "failures": 0}

            character.save()

        return Response(CharacterSheetSerializer(character).data)
