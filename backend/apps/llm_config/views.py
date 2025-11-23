"""LLM Configuration views - Placeholder implementations."""

from rest_framework import generics, status
from rest_framework.response import Response


class LlmConfigListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/llm/config - List and create LLM configs."""

    def list(self, request, *args, **kwargs):
        return Response(
            {"detail": "LLM config list - to be implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class LlmConfigDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/llm/config/{id} - Manage specific config."""

    def retrieve(self, request, *args, **kwargs):
        return Response(
            {"detail": "LLM config detail - to be implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
