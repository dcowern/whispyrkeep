"""
Serializers for accounts app.

Handles User registration, profile, and settings serialization.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "password",
            "password_confirm",
            "display_name",
        )
        extra_kwargs = {
            "email": {"required": True},
            "username": {"required": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
            display_name=validated_data.get("display_name", ""),
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile - read and update."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "display_name",
            "settings_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "email", "created_at", "updated_at")


class UserSettingsSerializer(serializers.ModelSerializer):
    """Serializer for user settings updates only."""

    class Meta:
        model = User
        fields = ("settings_json",)

    def validate_settings_json(self, value):
        """Validate settings structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Settings must be a JSON object.")

        # Validate ui_mode
        if "ui_mode" in value and value["ui_mode"] not in ("dark", "light"):
            raise serializers.ValidationError(
                {"ui_mode": "Must be 'dark' or 'light'."}
            )

        # Validate nd_options structure
        if "nd_options" in value:
            nd = value["nd_options"]
            if not isinstance(nd, dict):
                raise serializers.ValidationError(
                    {"nd_options": "Must be a JSON object."}
                )
            valid_nd_keys = {
                "low_stim_mode",
                "concise_recap",
                "decision_menu_mode",
                "dyslexia_font",
                "font_size",
                "line_spacing",
            }
            for key in nd:
                if key not in valid_nd_keys:
                    raise serializers.ValidationError(
                        {"nd_options": f"Unknown option: {key}"}
                    )

        # Validate safety_defaults
        if "safety_defaults" in value:
            safety = value["safety_defaults"]
            if not isinstance(safety, dict):
                raise serializers.ValidationError(
                    {"safety_defaults": "Must be a JSON object."}
                )
            if "content_rating" in safety:
                valid_ratings = ("G", "PG", "PG13", "R", "NC17")
                if safety["content_rating"] not in valid_ratings:
                    raise serializers.ValidationError(
                        {"safety_defaults": f"Invalid content_rating. Must be one of: {valid_ratings}"}
                    )

        # Validate endpoint preference
        if "endpoint_pref" in value:
            endpoint_pref = value["endpoint_pref"]
            if isinstance(endpoint_pref, str):
                # Legacy string-based setting; allow passthrough until user updates.
                endpoint_pref = {"model": endpoint_pref, "manual": True}
                value["endpoint_pref"] = endpoint_pref

            if not isinstance(endpoint_pref, dict):
                raise serializers.ValidationError(
                    {"endpoint_pref": "Must be a JSON object."}
                )

            provider = endpoint_pref.get("provider")
            if provider and provider not in {
                "openai",
                "anthropic",
                "meta",
                "mistral",
                "google",
                "custom",
            }:
                raise serializers.ValidationError(
                    {"endpoint_pref": "Invalid provider selection."}
                )

            if provider == "custom" and not endpoint_pref.get("base_url"):
                raise serializers.ValidationError(
                    {"endpoint_pref": "Custom providers require a base_url."}
                )

            compatibility = endpoint_pref.get("compatibility")
            if compatibility and compatibility not in {"openai", "anthropic", "google"}:
                raise serializers.ValidationError(
                    {"endpoint_pref": "Invalid compatibility value."}
                )

            if "model" in endpoint_pref and not isinstance(endpoint_pref.get("model"), str):
                raise serializers.ValidationError(
                    {"endpoint_pref": "Model must be a string if provided."}
                )

            max_tokens = endpoint_pref.get("max_tokens")
            if max_tokens is not None:
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    raise serializers.ValidationError(
                        {"endpoint_pref": "max_tokens must be a positive integer if provided."}
                    )

            temperature = endpoint_pref.get("temperature")
            if temperature is not None:
                try:
                    temp_val = float(temperature)
                except (TypeError, ValueError):
                    raise serializers.ValidationError(
                        {"endpoint_pref": "temperature must be a number if provided."}
                    )
                if temp_val < 0 or temp_val > 2:
                    raise serializers.ValidationError(
                        {"endpoint_pref": "temperature must be between 0 and 2."}
                    )

        return value
