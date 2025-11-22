"""Character views - Placeholder implementations."""

from rest_framework import generics, status
from rest_framework.response import Response


class CharacterListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/characters - List and create characters."""

    def list(self, request, *args, **kwargs):
        return Response(
            {"detail": "Character list - to be implemented in Epic 3"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class CharacterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/characters/{id}."""

    def retrieve(self, request, *args, **kwargs):
        return Response(
            {"detail": "Character detail - to be implemented in Epic 3"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
