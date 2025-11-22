"""Universe views - Placeholder implementations."""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView


class UniverseListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/universes."""

    def list(self, request, *args, **kwargs):
        return Response(
            {"detail": "Universe list - to be implemented in Epic 4"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class UniverseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/universes/{id}."""

    def retrieve(self, request, *args, **kwargs):
        return Response(
            {"detail": "Universe detail - to be implemented in Epic 4"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class WorldgenView(APIView):
    """POST /api/universes/{id}/worldgen - LLM co-write."""

    def post(self, request, pk):
        return Response(
            {"detail": "Worldgen - to be implemented in Epic 4"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class LoreUploadView(APIView):
    """POST /api/universes/{id}/lore/upload."""

    def post(self, request, pk):
        return Response(
            {"detail": "Lore upload - to be implemented in Epic 5"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class LoreListView(APIView):
    """GET /api/universes/{id}/lore."""

    def get(self, request, pk):
        return Response(
            {"detail": "Lore list - to be implemented in Epic 5"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class TimelineView(APIView):
    """GET /api/universes/{id}/timeline."""

    def get(self, request, pk):
        return Response(
            {"detail": "Timeline - to be implemented in Epic 6"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
