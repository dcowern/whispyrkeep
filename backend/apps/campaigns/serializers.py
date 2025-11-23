"""
Serializers for Campaign API.

Handles serialization for campaigns, turns, and state snapshots.
"""

from rest_framework import serializers

from apps.campaigns.models import Campaign, CanonicalCampaignState, TurnEvent
from apps.characters.models import CharacterSheet
from apps.universes.models import Universe


class CampaignListSerializer(serializers.ModelSerializer):
    """Serializer for campaign list view."""

    universe_name = serializers.CharField(source="universe.name", read_only=True)
    character_name = serializers.CharField(source="character_sheet.name", read_only=True)
    turn_count = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            "id",
            "title",
            "universe",
            "universe_name",
            "character_sheet",
            "character_name",
            "mode",
            "target_length",
            "status",
            "content_rating",
            "turn_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_turn_count(self, obj):
        """Get the number of turns in this campaign."""
        return obj.turns.count()


class CampaignDetailSerializer(serializers.ModelSerializer):
    """Serializer for campaign detail view."""

    universe_name = serializers.CharField(source="universe.name", read_only=True)
    character_name = serializers.CharField(source="character_sheet.name", read_only=True)
    turn_count = serializers.SerializerMethodField()
    current_turn_index = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            "id",
            "title",
            "universe",
            "universe_name",
            "character_sheet",
            "character_name",
            "mode",
            "target_length",
            "failure_style",
            "content_rating",
            "start_universe_time",
            "status",
            "turn_count",
            "current_turn_index",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_turn_count(self, obj):
        """Get the number of turns in this campaign."""
        return obj.turns.count()

    def get_current_turn_index(self, obj):
        """Get the current turn index."""
        latest = obj.turns.order_by("-turn_index").first()
        return latest.turn_index if latest else 0


class CampaignCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating campaigns."""

    universe = serializers.PrimaryKeyRelatedField(
        queryset=Universe.objects.all(),
    )
    character_sheet = serializers.PrimaryKeyRelatedField(
        queryset=CharacterSheet.objects.all(),
    )

    class Meta:
        model = Campaign
        fields = [
            "title",
            "universe",
            "character_sheet",
            "mode",
            "target_length",
            "failure_style",
            "content_rating",
            "start_universe_time",
        ]

    def validate_universe(self, value):
        """Validate user owns the universe."""
        user = self.context["request"].user
        if value.user != user:
            raise serializers.ValidationError("You do not own this universe")
        return value

    def validate_character_sheet(self, value):
        """Validate user owns the character."""
        user = self.context["request"].user
        if value.user != user:
            raise serializers.ValidationError("You do not own this character")
        return value

    def validate(self, data):
        """Cross-field validation."""
        # If universe has a specific content rating, campaign can't exceed it
        # (This is a placeholder for future rating enforcement)
        return data

    def create(self, validated_data):
        """Create campaign with user."""
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class CampaignUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating campaigns."""

    class Meta:
        model = Campaign
        fields = [
            "title",
            "mode",
            "target_length",
            "failure_style",
            "content_rating",
            "status",
        ]


class TurnEventSerializer(serializers.ModelSerializer):
    """Serializer for turn events."""

    class Meta:
        model = TurnEvent
        fields = [
            "id",
            "campaign",
            "turn_index",
            "user_input_text",
            "llm_response_text",
            "roll_spec_json",
            "roll_results_json",
            "state_patch_json",
            "canonical_state_hash",
            "lore_deltas_json",
            "universe_time_after_turn",
            "created_at",
        ]
        read_only_fields = fields


class TurnEventSummarySerializer(serializers.ModelSerializer):
    """Serializer for turn event summaries (list view)."""

    class Meta:
        model = TurnEvent
        fields = [
            "id",
            "turn_index",
            "user_input_text",
            "llm_response_text",
            "universe_time_after_turn",
            "created_at",
        ]


class CanonicalStateSerializer(serializers.ModelSerializer):
    """Serializer for canonical campaign state."""

    class Meta:
        model = CanonicalCampaignState
        fields = [
            "id",
            "campaign",
            "turn_index",
            "state_json",
            "created_at",
        ]
        read_only_fields = fields


class CampaignStateResponseSerializer(serializers.Serializer):
    """Serializer for campaign state API response."""

    campaign_id = serializers.UUIDField()
    turn_index = serializers.IntegerField()
    state = serializers.DictField()
    character_state = serializers.DictField()
    universe_time = serializers.DictField()
    is_snapshot = serializers.BooleanField()
