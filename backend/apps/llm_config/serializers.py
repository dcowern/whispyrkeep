"""
Serializers for LLM Endpoint Configuration.

Handles encryption/decryption of API keys during serialization.
"""

from rest_framework import serializers

from apps.llm_config.encryption import encrypt_api_key
from apps.llm_config.models import LlmEndpointConfig
from apps.llm_config.services import DEFAULT_BRAND_ENDPOINTS, DEFAULT_COMPATIBILITY


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


class LlmEndpointProbeSerializer(serializers.Serializer):
    """Serializer for listing models and validating endpoint settings."""

    provider = serializers.ChoiceField(
        choices=["openai", "anthropic", "meta", "mistral", "google", "custom"],
        help_text="Provider name or custom endpoint",
    )
    base_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="Base URL; required for custom providers",
    )
    compatibility = serializers.ChoiceField(
        choices=["openai", "anthropic", "google"],
        required=False,
        help_text="Protocol compatibility for the endpoint",
    )
    api_key = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="API key used to talk to the provider (not persisted)",
    )
    model = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional model name to validate",
    )
    max_tokens = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Optional max_tokens to send during probe; omitted when not provided.",
    )
    temperature = serializers.FloatField(
        required=False,
        help_text="Optional temperature to send during probe; omitted when not provided.",
    )

    def validate(self, attrs):
        provider = attrs.get("provider", "")
        base_url = attrs.get("base_url", "")

        if provider == "custom" and not base_url:
            raise serializers.ValidationError(
                {"base_url": "Base URL is required for custom providers."}
            )

        if provider != "custom":
            attrs["base_url"] = base_url or DEFAULT_BRAND_ENDPOINTS.get(provider, "")
            attrs["compatibility"] = attrs.get("compatibility") or DEFAULT_COMPATIBILITY.get(
                provider, "openai"
            )
        else:
            attrs["compatibility"] = attrs.get("compatibility") or "openai"

        return attrs
