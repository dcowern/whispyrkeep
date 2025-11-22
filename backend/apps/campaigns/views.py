"""Campaign views - Placeholder implementations."""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView


class CampaignListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/campaigns."""

    def list(self, request, *args, **kwargs):
        return Response(
            {"detail": "Campaign list - to be implemented in Epic 7"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class CampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/campaigns/{id}."""

    def retrieve(self, request, *args, **kwargs):
        return Response(
            {"detail": "Campaign detail - to be implemented in Epic 7"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class TurnView(APIView):
    """POST /api/campaigns/{id}/turn - Submit player turn."""

    def post(self, request, pk):
        return Response(
            {"detail": "Turn submission - to be implemented in Epic 8"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class TurnListView(APIView):
    """GET /api/campaigns/{id}/turns - Get turn history."""

    def get(self, request, pk):
        return Response(
            {"detail": "Turn history - to be implemented in Epic 8"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class StateView(APIView):
    """GET /api/campaigns/{id}/state - Get current state."""

    def get(self, request, pk):
        return Response(
            {"detail": "Campaign state - to be implemented in Epic 7"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class DiceLogView(APIView):
    """GET /api/campaigns/{id}/dice-log."""

    def get(self, request, pk):
        return Response(
            {"detail": "Dice log - to be implemented in Epic 8"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class RewindView(APIView):
    """POST /api/campaigns/{id}/rewind - Rewind to turn."""

    def post(self, request, pk):
        return Response(
            {"detail": "Rewind - to be implemented in Epic 10"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
