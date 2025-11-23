"""
LLM Configuration views.

Endpoints for managing user's LLM endpoint configurations.
API keys are encrypted at rest and never exposed in responses.
"""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.llm_config.models import LlmEndpointConfig
from apps.llm_config.serializers import (
    LlmEndpointConfigSerializer,
    LlmEndpointConfigUpdateSerializer,
)


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
