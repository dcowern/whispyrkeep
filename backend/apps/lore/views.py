"""
Views for Lore API.

Provides endpoints for hard canon document upload and lore retrieval.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lore.serializers import (
    HardCanonDocListSerializer,
    HardCanonDocSerializer,
    HardCanonDocUploadSerializer,
    LoreContextSerializer,
    LoreIngestionResultSerializer,
    LoreQuerySerializer,
    LoreStatsSerializer,
)
from apps.lore.services.lore_service import LoreService
from apps.universes.models import Universe, UniverseHardCanonDoc


class UniverseHardCanonListView(APIView):
    """
    List hard canon documents for a universe.

    GET /api/universes/{universe_id}/hard-canon/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, universe_id):
        """List hard canon documents for a universe."""
        try:
            universe = Universe.objects.get(id=universe_id, user=request.user)
        except Universe.DoesNotExist:
            return Response(
                {"error": "Universe not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        docs = UniverseHardCanonDoc.objects.filter(universe=universe).order_by("-created_at")
        serializer = HardCanonDocListSerializer(docs, many=True)

        return Response(serializer.data)


class UniverseHardCanonUploadView(APIView):
    """
    Upload a hard canon document to a universe.

    POST /api/universes/{universe_id}/hard-canon/upload/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, universe_id):
        """Upload a new hard canon document."""
        try:
            universe = Universe.objects.get(id=universe_id, user=request.user)
        except Universe.DoesNotExist:
            return Response(
                {"error": "Universe not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = HardCanonDocUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Use lore service to ingest
        service = LoreService()
        result = service.ingest_hard_canon(
            universe=universe,
            title=serializer.validated_data["title"],
            raw_text=serializer.validated_data["raw_text"],
            source_type=serializer.validated_data["source_type"],
            tags=serializer.validated_data.get("tags", []),
            never_compact=serializer.validated_data["never_compact"],
        )

        result_serializer = LoreIngestionResultSerializer(result)

        if result.success:
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(result_serializer.data, status=status.HTTP_400_BAD_REQUEST)


class HardCanonDocDetailView(APIView):
    """
    Retrieve, update, or delete a hard canon document.

    GET/DELETE /api/universes/{universe_id}/hard-canon/{doc_id}/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, universe_id, doc_id):
        """Get a hard canon document."""
        try:
            universe = Universe.objects.get(id=universe_id, user=request.user)
            doc = UniverseHardCanonDoc.objects.get(id=doc_id, universe=universe)
        except Universe.DoesNotExist:
            return Response(
                {"error": "Universe not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except UniverseHardCanonDoc.DoesNotExist:
            return Response(
                {"error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = HardCanonDocSerializer(doc)
        return Response(serializer.data)

    def delete(self, request, universe_id, doc_id):
        """Delete a hard canon document."""
        try:
            universe = Universe.objects.get(id=universe_id, user=request.user)
            doc = UniverseHardCanonDoc.objects.get(id=doc_id, universe=universe)
        except Universe.DoesNotExist:
            return Response(
                {"error": "Universe not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except UniverseHardCanonDoc.DoesNotExist:
            return Response(
                {"error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        service = LoreService()
        success = service.delete_hard_canon_doc(doc)

        if success:
            return Response(
                {"message": "Document deleted successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Failed to delete document"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UniverseLoreQueryView(APIView):
    """
    Query lore for a universe.

    POST /api/universes/{universe_id}/lore/query/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, universe_id):
        """Query universe lore."""
        try:
            universe = Universe.objects.get(id=universe_id, user=request.user)
        except Universe.DoesNotExist:
            return Response(
                {"error": "Universe not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LoreQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = LoreService()
        context = service.get_lore_context(
            universe=universe,
            query=serializer.validated_data["query"],
            max_chunks=serializer.validated_data["max_chunks"],
            include_soft_lore=serializer.validated_data["include_soft_lore"],
            prioritize_hard_canon=serializer.validated_data["prioritize_hard_canon"],
        )

        result_serializer = LoreContextSerializer(context)
        return Response(result_serializer.data)


class UniverseLoreStatsView(APIView):
    """
    Get lore statistics for a universe.

    GET /api/universes/{universe_id}/lore/stats/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, universe_id):
        """Get lore statistics."""
        try:
            universe = Universe.objects.get(id=universe_id, user=request.user)
        except Universe.DoesNotExist:
            return Response(
                {"error": "Universe not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        service = LoreService()
        stats = service.get_universe_lore_stats(universe)

        serializer = LoreStatsSerializer(stats)
        return Response(serializer.data)
