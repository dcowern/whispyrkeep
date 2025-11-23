"""
Campaign views - CRUD operations and state management.

Based on SYSTEM_DESIGN.md Epic 7 requirements.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.campaigns.models import Campaign, TurnEvent
from apps.campaigns.serializers import (
    CampaignCreateSerializer,
    CampaignDetailSerializer,
    CampaignListSerializer,
    CampaignUpdateSerializer,
    TurnEventSummarySerializer,
)
from apps.campaigns.services.state_service import StateService


class CampaignListCreateView(APIView):
    """
    GET /api/campaigns/ - List user's campaigns
    POST /api/campaigns/ - Create a new campaign
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List user's campaigns."""
        campaigns = Campaign.objects.filter(user=request.user).select_related(
            "universe", "character_sheet"
        ).order_by("-updated_at")

        # Apply filters
        status_filter = request.query_params.get("status")
        if status_filter:
            campaigns = campaigns.filter(status=status_filter)

        universe_filter = request.query_params.get("universe")
        if universe_filter:
            campaigns = campaigns.filter(universe_id=universe_filter)

        serializer = CampaignListSerializer(campaigns, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new campaign."""
        serializer = CampaignCreateSerializer(
            data=request.data,
            context={"request": request},
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        campaign = serializer.save()

        # Create initial state snapshot
        state_service = StateService()
        initial_state = state_service.get_initial_state(campaign)
        state_service.save_snapshot(campaign, initial_state, force=True)

        return Response(
            CampaignDetailSerializer(campaign).data,
            status=status.HTTP_201_CREATED,
        )


class CampaignDetailView(APIView):
    """
    GET /api/campaigns/{id}/ - Get campaign details
    PUT /api/campaigns/{id}/ - Update campaign
    DELETE /api/campaigns/{id}/ - Delete campaign
    """

    permission_classes = [IsAuthenticated]

    def get_campaign(self, request, pk):
        """Get campaign owned by user."""
        try:
            return Campaign.objects.select_related(
                "universe", "character_sheet"
            ).get(id=pk, user=request.user)
        except Campaign.DoesNotExist:
            return None

    def get(self, request, pk):
        """Get campaign details."""
        campaign = self.get_campaign(request, pk)
        if not campaign:
            return Response(
                {"error": "Campaign not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CampaignDetailSerializer(campaign)
        return Response(serializer.data)

    def put(self, request, pk):
        """Update campaign."""
        campaign = self.get_campaign(request, pk)
        if not campaign:
            return Response(
                {"error": "Campaign not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CampaignUpdateSerializer(
            campaign, data=request.data, partial=True
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(CampaignDetailSerializer(campaign).data)

    def patch(self, request, pk):
        """Partial update campaign."""
        return self.put(request, pk)

    def delete(self, request, pk):
        """Delete campaign."""
        campaign = self.get_campaign(request, pk)
        if not campaign:
            return Response(
                {"error": "Campaign not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        campaign.delete()
        return Response(
            {"message": "Campaign deleted successfully"},
            status=status.HTTP_200_OK,
        )


class TurnView(APIView):
    """POST /api/campaigns/{id}/turn - Submit player turn."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Submit a player turn - to be implemented in Epic 8."""
        return Response(
            {"detail": "Turn submission - to be implemented in Epic 8"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class TurnListView(APIView):
    """GET /api/campaigns/{id}/turns - Get turn history."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get turn history for a campaign."""
        try:
            campaign = Campaign.objects.get(id=pk, user=request.user)
        except Campaign.DoesNotExist:
            return Response(
                {"error": "Campaign not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        turns = TurnEvent.objects.filter(campaign=campaign).order_by("turn_index")

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
        turns = turns[offset:offset + limit]

        serializer = TurnEventSummarySerializer(turns, many=True)
        return Response({
            "count": campaign.turns.count(),
            "results": serializer.data,
        })


class StateView(APIView):
    """
    GET /api/campaigns/{id}/state - Get current campaign state.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get current campaign state."""
        try:
            campaign = Campaign.objects.select_related(
                "universe", "character_sheet"
            ).get(id=pk, user=request.user)
        except Campaign.DoesNotExist:
            return Response(
                {"error": "Campaign not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        state_service = StateService()
        state_response = state_service.get_state_for_response(campaign)

        return Response(state_response)


class DiceLogView(APIView):
    """GET /api/campaigns/{id}/dice-log - Get dice roll history."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get dice roll history - to be implemented in Epic 8."""
        return Response(
            {"detail": "Dice log - to be implemented in Epic 8"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class RewindView(APIView):
    """POST /api/campaigns/{id}/rewind - Rewind to turn."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Rewind campaign to a previous turn - to be implemented in Epic 10."""
        return Response(
            {"detail": "Rewind - to be implemented in Epic 10"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
