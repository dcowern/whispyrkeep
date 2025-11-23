"""
LLM Configuration views.

Endpoints for managing user's LLM endpoint configurations.
API keys are encrypted at rest and never exposed in responses.
"""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.llm_config.models import LlmEndpointConfig
from apps.llm_config.serializers import (
    LlmEndpointConfigSerializer,
    LlmEndpointConfigUpdateSerializer,
    LlmEndpointProbeSerializer,
)
from apps.llm_config.services import (
    LlmEndpointError,
    fetch_models,
    resolve_endpoint,
    validate_endpoint,
)
from apps.llm_config.encryption import encrypt_api_key, decrypt_api_key


class LlmConfigListCreateView(generics.ListCreateAPIView):
    """
    GET/POST /api/llm/config - List and create LLM configs.

    GET: List all LLM configurations for the current user.
    POST: Create a new LLM configuration with encrypted API key.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = LlmEndpointConfigSerializer

    def get_queryset(self):
        """Return only configs belonging to the current user."""
        return LlmEndpointConfig.objects.filter(user=self.request.user)


class LlmConfigDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/llm/config/{id} - Manage specific config.

    GET: Retrieve config details (API key is never exposed).
    PUT/PATCH: Update config. API key can be updated or left unchanged.
    DELETE: Remove the configuration.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only configs belonging to the current user."""
        return LlmEndpointConfig.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use update serializer for PUT/PATCH."""
        if self.request.method in ("PUT", "PATCH"):
            return LlmEndpointConfigUpdateSerializer
        return LlmEndpointConfigSerializer

    def destroy(self, request, *args, **kwargs):
        """Delete the config and return success message."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "LLM configuration deleted."},
            status=status.HTTP_200_OK,
        )


class LlmModelListView(APIView):
    """POST /api/llm/models - List models for a provider/base URL."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LlmEndpointProbeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        provider, resolved_base, resolved_compat = resolve_endpoint(
            data["provider"], data.get("base_url"), data.get("compatibility")
        )

        try:
            models = fetch_models(
                provider=provider,
                base_url=resolved_base,
                compatibility=resolved_compat,
                api_key=data.get("api_key"),
            )
        except LlmEndpointError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "models": models,
                "resolved_base_url": resolved_base,
                "compatibility": resolved_compat,
            },
            status=status.HTTP_200_OK,
        )


class LlmEndpointValidateView(APIView):
    """POST /api/llm/validate - Validate endpoint + optional model before saving."""

    permission_classes = [IsAuthenticated]

    def _get_stored_api_key(self, user, provider: str) -> str | None:
        """Return decrypted API key for a provider if it exists."""
        config = (
            LlmEndpointConfig.objects.filter(
                user=user,
                provider_name=provider,
                is_active=True,
            )
            .order_by("-updated_at")
            .first()
        )
        if config and config.api_key_encrypted:
            try:
                return decrypt_api_key(config.api_key_encrypted)
            except Exception:  # pragma: no cover - defensive
                return None
        return None

    def _persist_config(self, user, provider: str, base_url: str, model: str | None, api_key: str | None):
        """Create or update the user's active config for this provider."""
        config, _ = LlmEndpointConfig.objects.get_or_create(
            user=user,
            provider_name=provider,
            defaults={
                "base_url": base_url or "",
                "default_model": model or "",
            },
        )

        if base_url:
            config.base_url = base_url
        if model:
            config.default_model = model
        if api_key:
            config.api_key_encrypted = encrypt_api_key(api_key)

        config.save()
        return config

    def _requires_api_key(self, provider: str) -> bool:
        """Return True if the provider requires an API key."""
        return provider != "custom"

    def post(self, request, *args, **kwargs):
        serializer = LlmEndpointProbeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        api_key = (data.get("api_key") or "").strip()
        if not api_key:
            api_key = self._get_stored_api_key(request.user, data["provider"])

        if self._requires_api_key(data["provider"]) and not api_key:
            return Response(
                {
                    "success": False,
                    "message": "API key is required for this provider.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = validate_endpoint(
                provider=data["provider"],
                base_url=data.get("base_url"),
                compatibility=data.get("compatibility"),
                api_key=api_key,
                model_name=data.get("model") or None,
                max_tokens=data.get("max_tokens"),
                temperature=data.get("temperature"),
            )
        except LlmEndpointError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
        )

        # Persist the configuration and key (if provided) for the user.
        config = self._persist_config(
            user=request.user,
            provider=data["provider"],
            base_url=result.get("resolved_base_url") or data.get("base_url") or "",
            model=data.get("model") or None,
            api_key=(data.get("api_key") or "").strip() or None,
        )

        return Response(
            {
                "success": True,
                "message": "Endpoint verified and settings saved.",
                "has_api_key": bool(config.api_key_encrypted),
                **result,
            },
            status=status.HTTP_200_OK,
        )
