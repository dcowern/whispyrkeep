"""
Serializers for LLM Endpoint Configuration.

Handles encryption/decryption of API keys during serialization.
"""

from rest_framework import serializers

from apps.llm_config.encryption import encrypt_api_key
from apps.llm_config.models import LlmEndpointConfig


class LlmEndpointConfigSerializer(serializers.ModelSerializer):
    """
    Serializer for LlmEndpointConfig.

    API key is write-only; never exposed in responses.
    """

    api_key = serializers.CharField(
        write_only=True,
        required=True,
        help_text="API key (will be encrypted at rest)",
    )
    has_api_key = serializers.SerializerMethodField()

    class Meta:
        model = LlmEndpointConfig
        fields = (
            "id",
            "provider_name",
            "base_url",
            "api_key",
            "has_api_key",
            "default_model",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "has_api_key", "created_at", "updated_at")

    def get_has_api_key(self, obj) -> bool:
        """Indicate if an API key is stored without exposing it."""
        return bool(obj.api_key_encrypted)

    def validate_api_key(self, value):
        """Validate API key is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("API key cannot be empty.")
        return value.strip()

    def validate_base_url(self, value):
        """Validate base_url for custom providers."""
        return value.strip() if value else ""

    def create(self, validated_data):
        """Create config with encrypted API key."""
        api_key = validated_data.pop("api_key")
        validated_data["api_key_encrypted"] = encrypt_api_key(api_key)
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update config, re-encrypting API key if provided."""
        if "api_key" in validated_data:
            api_key = validated_data.pop("api_key")
            validated_data["api_key_encrypted"] = encrypt_api_key(api_key)
        return super().update(instance, validated_data)


class LlmEndpointConfigUpdateSerializer(LlmEndpointConfigSerializer):
    """Serializer for updates where API key is optional."""

    api_key = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="API key (leave empty to keep existing)",
    )

    def validate_api_key(self, value):
        """Allow empty for updates (keeps existing key)."""
        if value:
            return value.strip()
        return value
