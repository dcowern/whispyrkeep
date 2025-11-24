"""
Views for universe and homebrew content APIs.

Provides CRUD endpoints for managing universes and their homebrew content.
All endpoints require authentication and are scoped to the authenticated user.
"""
import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    HomebrewBackground,
    HomebrewClass,
    HomebrewFeat,
    HomebrewItem,
    HomebrewMonster,
    HomebrewSpecies,
    HomebrewSpell,
    HomebrewSubclass,
    Universe,
    UniverseHardCanonDoc,
)
from .serializers import (
    HomebrewBackgroundSerializer,
    HomebrewBackgroundSummarySerializer,
    HomebrewClassSerializer,
    HomebrewClassSummarySerializer,
    HomebrewFeatSerializer,
    HomebrewFeatSummarySerializer,
    HomebrewItemSerializer,
    HomebrewItemSummarySerializer,
    HomebrewMonsterSerializer,
    HomebrewMonsterSummarySerializer,
    HomebrewSpeciesSerializer,
    HomebrewSpeciesSummarySerializer,
    HomebrewSpellSerializer,
    HomebrewSpellSummarySerializer,
    HomebrewSubclassSerializer,
    HomebrewSubclassSummarySerializer,
    UniverseHardCanonDocSerializer,
    UniverseSerializer,
    UniverseSummarySerializer,
)

logger = logging.getLogger(__name__)


class UniverseViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for universes.

    GET /api/universes/ - List user's universes
    POST /api/universes/ - Create a new universe
    GET /api/universes/{id}/ - Get universe details
    PUT /api/universes/{id}/ - Update universe
    PATCH /api/universes/{id}/ - Partial update
    DELETE /api/universes/{id}/ - Delete universe (cascades to homebrew)

    Additional actions:
    POST /api/universes/{id}/lock_homebrew/ - Lock all homebrew content
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter universes to those owned by the authenticated user."""
        return Universe.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use summary serializer for list views."""
        if self.action == "list":
            return UniverseSummarySerializer
        return UniverseSerializer

    def perform_create(self, serializer):
        """Set the user when creating a universe."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def lock_homebrew(self, request, pk=None):
        """
        Lock all homebrew content for this universe.

        This is typically called after universe creation is complete
        to prevent further modifications to homebrew content.
        """
        universe = self.get_object()

        # Lock all homebrew content
        locked_counts = {}
        homebrew_models = [
            ("species", HomebrewSpecies),
            ("spells", HomebrewSpell),
            ("items", HomebrewItem),
            ("monsters", HomebrewMonster),
            ("feats", HomebrewFeat),
            ("backgrounds", HomebrewBackground),
            ("classes", HomebrewClass),
            ("subclasses", HomebrewSubclass),
        ]

        for name, model in homebrew_models:
            count = model.objects.filter(universe=universe, is_locked=False).update(
                is_locked=True
            )
            locked_counts[name] = count

        return Response({
            "message": "All homebrew content has been locked.",
            "locked_counts": locked_counts,
        })


class UniverseHardCanonDocViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for hard canon documents.

    GET /api/universes/{universe_id}/canon/ - List canon docs
    POST /api/universes/{universe_id}/canon/ - Create canon doc
    GET /api/universes/{universe_id}/canon/{id}/ - Get canon doc
    PUT /api/universes/{universe_id}/canon/{id}/ - Update canon doc
    DELETE /api/universes/{universe_id}/canon/{id}/ - Delete canon doc
    """

    serializer_class = UniverseHardCanonDocSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["source_type", "never_compact"]
    search_fields = ["title", "raw_text"]

    def get_queryset(self):
        """Filter to canon docs for the specified universe owned by user."""
        universe_id = self.kwargs.get("universe_pk")
        return UniverseHardCanonDoc.objects.filter(
            universe_id=universe_id,
            universe__user=self.request.user,
        )

    def perform_create(self, serializer):
        """Set the universe when creating a canon doc."""
        universe_id = self.kwargs.get("universe_pk")
        universe = Universe.objects.get(id=universe_id, user=self.request.user)
        serializer.save(universe=universe)


class HomebrewBaseViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for homebrew content.

    Provides common functionality for all homebrew endpoints:
    - Scoped to a specific universe
    - User ownership validation
    - List/detail serializer switching
    - Standard filtering and search
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["source_type", "power_tier", "is_locked"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["name"]

    # Override in subclasses
    model_class = None
    detail_serializer_class = None
    summary_serializer_class = None

    def get_queryset(self):
        """Filter to homebrew content for the specified universe owned by user."""
        universe_id = self.kwargs.get("universe_pk")
        return self.model_class.objects.filter(
            universe_id=universe_id,
            universe__user=self.request.user,
        )

    def get_serializer_class(self):
        """Use summary serializer for list views."""
        if self.action == "list":
            return self.summary_serializer_class
        return self.detail_serializer_class

    def perform_create(self, serializer):
        """Set the universe when creating homebrew content."""
        universe_id = self.kwargs.get("universe_pk")
        universe = Universe.objects.get(id=universe_id, user=self.request.user)
        serializer.save(universe=universe)


class HomebrewSpeciesViewSet(HomebrewBaseViewSet):
    """
    CRUD operations for homebrew species.

    GET /api/universes/{universe_id}/homebrew/species/ - List species
    POST /api/universes/{universe_id}/homebrew/species/ - Create species
    GET /api/universes/{universe_id}/homebrew/species/{id}/ - Get species
    PUT/PATCH /api/universes/{universe_id}/homebrew/species/{id}/ - Update
    DELETE /api/universes/{universe_id}/homebrew/species/{id}/ - Delete
    """

    model_class = HomebrewSpecies
    detail_serializer_class = HomebrewSpeciesSerializer
    summary_serializer_class = HomebrewSpeciesSummarySerializer
    filterset_fields = HomebrewBaseViewSet.filterset_fields + ["size"]


class HomebrewSpellViewSet(HomebrewBaseViewSet):
    """
    CRUD operations for homebrew spells.

    Filter by level, school, concentration, ritual.
    """

    model_class = HomebrewSpell
    detail_serializer_class = HomebrewSpellSerializer
    summary_serializer_class = HomebrewSpellSummarySerializer
    filterset_fields = HomebrewBaseViewSet.filterset_fields + [
        "level",
        "school",
        "concentration",
        "ritual",
    ]
    ordering_fields = HomebrewBaseViewSet.ordering_fields + ["level"]
    ordering = ["level", "name"]

    def get_queryset(self):
        """Add select_related for spell school."""
        return super().get_queryset().select_related("school", "damage_type")


class HomebrewItemViewSet(HomebrewBaseViewSet):
    """
    CRUD operations for homebrew items.

    Filter by category, rarity, magical status, weapon/armor type.
    """

    model_class = HomebrewItem
    detail_serializer_class = HomebrewItemSerializer
    summary_serializer_class = HomebrewItemSummarySerializer
    filterset_fields = HomebrewBaseViewSet.filterset_fields + [
        "category",
        "rarity",
        "magical",
        "is_weapon",
        "is_armor",
    ]

    def get_queryset(self):
        """Add select_related for category and damage type."""
        return super().get_queryset().select_related("category", "damage_type")


class HomebrewMonsterViewSet(HomebrewBaseViewSet):
    """
    CRUD operations for homebrew monsters.

    Filter by monster type, size, challenge rating.
    """

    model_class = HomebrewMonster
    detail_serializer_class = HomebrewMonsterSerializer
    summary_serializer_class = HomebrewMonsterSummarySerializer
    filterset_fields = {
        "source_type": ["exact"],
        "power_tier": ["exact"],
        "is_locked": ["exact"],
        "monster_type": ["exact"],
        "size": ["exact"],
        "challenge_rating": ["exact", "lte", "gte"],
    }
    ordering_fields = HomebrewBaseViewSet.ordering_fields + [
        "challenge_rating",
        "hit_points",
    ]
    ordering = ["challenge_rating", "name"]

    def get_queryset(self):
        """Add select_related and prefetch_related for monster relationships."""
        return (
            super()
            .get_queryset()
            .select_related("monster_type")
            .prefetch_related(
                "damage_vulnerabilities",
                "damage_resistances",
                "damage_immunities",
                "condition_immunities",
            )
        )


class HomebrewFeatViewSet(HomebrewBaseViewSet):
    """CRUD operations for homebrew feats."""

    model_class = HomebrewFeat
    detail_serializer_class = HomebrewFeatSerializer
    summary_serializer_class = HomebrewFeatSummarySerializer


class HomebrewBackgroundViewSet(HomebrewBaseViewSet):
    """CRUD operations for homebrew backgrounds."""

    model_class = HomebrewBackground
    detail_serializer_class = HomebrewBackgroundSerializer
    summary_serializer_class = HomebrewBackgroundSummarySerializer


class HomebrewClassViewSet(HomebrewBaseViewSet):
    """CRUD operations for homebrew classes."""

    model_class = HomebrewClass
    detail_serializer_class = HomebrewClassSerializer
    summary_serializer_class = HomebrewClassSummarySerializer
    filterset_fields = HomebrewBaseViewSet.filterset_fields + ["hit_die"]


class HomebrewSubclassViewSet(HomebrewBaseViewSet):
    """
    CRUD operations for homebrew subclasses.

    Filter by parent class (homebrew or SRD).
    """

    model_class = HomebrewSubclass
    detail_serializer_class = HomebrewSubclassSerializer
    summary_serializer_class = HomebrewSubclassSummarySerializer
    filterset_fields = HomebrewBaseViewSet.filterset_fields + [
        "parent_class",
        "srd_parent_class_name",
    ]

    def get_queryset(self):
        """Add select_related for parent class."""
        return super().get_queryset().select_related("parent_class")


# ==================== Placeholder Views for Future Epics ====================


class WorldgenView(APIView):
    """
    POST /api/universes/worldgen/ - Create universe with LLM worldgen.

    Creates a new universe with AI-generated homebrew content.
    Requires the user to have an active LLM configuration for full functionality.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a universe with worldgen.

        Request body:
        {
            "name": "Universe Name",
            "description": "Optional description",
            "grimdark_cozy": 0.5,
            "comedy_serious": 0.5,
            "low_high_magic": 0.5,
            "sandbox_railroad": 0.5,
            "combat_roleplay": 0.5,
            "themes": ["adventure", "mystery"],
            "rules_strictness": "standard",
            "homebrew_amount": "moderate",
            "generate_species": true,
            "generate_spells": true,
            "max_species": 3,
            "max_spells": 5,
            ...
        }

        Returns:
        - 201: Universe created with generated content
        - 400: Validation errors
        """
        from .services.worldgen import WorldgenRequest, WorldgenService

        # Extract request data
        data = request.data
        try:
            worldgen_request = WorldgenRequest(
                name=data.get("name", ""),
                description=data.get("description", ""),
                grimdark_cozy=float(data.get("grimdark_cozy", 0.5)),
                comedy_serious=float(data.get("comedy_serious", 0.5)),
                low_high_magic=float(data.get("low_high_magic", 0.5)),
                sandbox_railroad=float(data.get("sandbox_railroad", 0.5)),
                combat_roleplay=float(data.get("combat_roleplay", 0.5)),
                themes=data.get("themes", []),
                rules_strictness=data.get("rules_strictness", "standard"),
                homebrew_amount=data.get("homebrew_amount", "moderate"),
                generate_species=data.get("generate_species", True),
                generate_classes=data.get("generate_classes", False),
                generate_backgrounds=data.get("generate_backgrounds", True),
                generate_spells=data.get("generate_spells", True),
                generate_items=data.get("generate_items", True),
                generate_monsters=data.get("generate_monsters", True),
                generate_feats=data.get("generate_feats", True),
                max_species=int(data.get("max_species", 3)),
                max_classes=int(data.get("max_classes", 0)),
                max_backgrounds=int(data.get("max_backgrounds", 2)),
                max_spells=int(data.get("max_spells", 5)),
                max_items=int(data.get("max_items", 5)),
                max_monsters=int(data.get("max_monsters", 5)),
                max_feats=int(data.get("max_feats", 3)),
                seed=data.get("seed"),
            )
        except (ValueError, TypeError) as e:
            return Response(
                {"errors": [f"Invalid request data: {str(e)}"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Run worldgen
        service = WorldgenService(request.user)
        result = service.generate(worldgen_request)

        if not result.success:
            return Response(
                {"errors": result.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Return created universe info
        return Response(
            {
                "universe_id": result.universe_id,
                "created_content": result.created_content,
                "warnings": result.warnings,
            },
            status=status.HTTP_201_CREATED,
        )


class WorldgenPreviewView(APIView):
    """
    POST /api/universes/worldgen/preview/ - Preview worldgen without creating.

    Returns what would be generated based on the parameters.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Preview worldgen parameters."""
        from .services.worldgen import WorldgenRequest, WorldgenService

        data = request.data
        try:
            worldgen_request = WorldgenRequest(
                name=data.get("name", "Preview Universe"),
                description=data.get("description", ""),
                grimdark_cozy=float(data.get("grimdark_cozy", 0.5)),
                comedy_serious=float(data.get("comedy_serious", 0.5)),
                low_high_magic=float(data.get("low_high_magic", 0.5)),
                sandbox_railroad=float(data.get("sandbox_railroad", 0.5)),
                combat_roleplay=float(data.get("combat_roleplay", 0.5)),
                themes=data.get("themes", []),
                rules_strictness=data.get("rules_strictness", "standard"),
                homebrew_amount=data.get("homebrew_amount", "moderate"),
                generate_species=data.get("generate_species", True),
                generate_classes=data.get("generate_classes", False),
                generate_backgrounds=data.get("generate_backgrounds", True),
                generate_spells=data.get("generate_spells", True),
                generate_items=data.get("generate_items", True),
                generate_monsters=data.get("generate_monsters", True),
                generate_feats=data.get("generate_feats", True),
                max_species=int(data.get("max_species", 3)),
                max_classes=int(data.get("max_classes", 0)),
                max_backgrounds=int(data.get("max_backgrounds", 2)),
                max_spells=int(data.get("max_spells", 5)),
                max_items=int(data.get("max_items", 5)),
                max_monsters=int(data.get("max_monsters", 5)),
                max_feats=int(data.get("max_feats", 3)),
            )
        except (ValueError, TypeError) as e:
            return Response(
                {"errors": [f"Invalid request data: {str(e)}"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = WorldgenService(request.user)
        preview = service.preview(worldgen_request)

        return Response(preview, status=status.HTTP_200_OK)


class LoreUploadView(APIView):
    """
    POST /api/universes/{id}/lore/upload.

    Upload a hard canon document to a universe.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Upload a new hard canon document."""
        from apps.lore.serializers import (
            HardCanonDocUploadSerializer,
            LoreIngestionResultSerializer,
        )
        from apps.lore.services.lore_service import LoreService

        try:
            universe = Universe.objects.get(id=pk, user=request.user)
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


class LoreListView(APIView):
    """
    GET /api/universes/{id}/lore.

    List hard canon documents for a universe.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """List hard canon documents for a universe."""
        from apps.lore.serializers import HardCanonDocListSerializer

        try:
            universe = Universe.objects.get(id=pk, user=request.user)
        except Universe.DoesNotExist:
            return Response(
                {"error": "Universe not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        docs = UniverseHardCanonDoc.objects.filter(universe=universe).order_by("-created_at")
        serializer = HardCanonDocListSerializer(docs, many=True)

        return Response(serializer.data)


class LoreQueryView(APIView):
    """
    POST /api/universes/{id}/lore/query.

    Query lore for a universe using semantic search.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Query universe lore."""
        from apps.lore.serializers import LoreContextSerializer, LoreQuerySerializer
        from apps.lore.services.lore_service import LoreService

        try:
            universe = Universe.objects.get(id=pk, user=request.user)
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


class LoreStatsView(APIView):
    """
    GET /api/universes/{id}/lore/stats.

    Get lore statistics for a universe.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get lore statistics."""
        from apps.lore.serializers import LoreStatsSerializer
        from apps.lore.services.lore_service import LoreService

        try:
            universe = Universe.objects.get(id=pk, user=request.user)
        except Universe.DoesNotExist:
            return Response(
                {"error": "Universe not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        service = LoreService()
        stats = service.get_universe_lore_stats(universe)

        serializer = LoreStatsSerializer(stats)
        return Response(serializer.data)


class TimelineView(APIView):
    """GET /api/universes/{id}/timeline."""

    def get(self, request, pk):
        return Response(
            {"detail": "Timeline - to be implemented in Epic 6"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class UniverseExportView(APIView):
    """
    POST /api/universes/{id}/export - Export universe.

    Exports universe data to JSON or Markdown format.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Create an export job for the universe."""
        from apps.exports.serializers import ExportRequestSerializer
        from apps.exports.services.export_service import ExportService

        try:
            universe = Universe.objects.get(id=pk, user=request.user)
        except Universe.DoesNotExist:
            return Response(
                {"error": "Universe not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ExportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        export_format = serializer.validated_data["format"]

        # Create export job
        service = ExportService()
        job = service.create_universe_export_job(universe, export_format)

        # For small exports, run synchronously
        # For larger exports, queue async task
        result = service.execute_export(job)

        if result.success:
            return Response({
                "job_id": str(job.id),
                "status": job.status,
                "message": "Export completed successfully",
                "download_url": f"/api/exports/{job.id}/?download=true",
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "job_id": str(job.id),
                "status": job.status,
                "errors": result.errors,
            }, status=status.HTTP_400_BAD_REQUEST)


# ==================== Worldgen Session Views ====================


class WorldgenSessionListView(APIView):
    """
    GET /api/universes/worldgen/sessions/ - List user's draft sessions
    POST /api/universes/worldgen/sessions/ - Create new session
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List user's draft worldgen sessions."""
        from .serializers import WorldgenSessionSummarySerializer
        from .services.worldgen_chat import WorldgenChatService

        service = WorldgenChatService(request.user)
        sessions = service.list_sessions()
        serializer = WorldgenSessionSummarySerializer(sessions, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new worldgen session."""
        from .serializers import (
            WorldgenSessionCreateSerializer,
            WorldgenSessionSerializer,
        )
        from .services.worldgen_chat import WorldgenChatService

        create_serializer = WorldgenSessionCreateSerializer(data=request.data)
        if not create_serializer.is_valid():
            return Response(create_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = WorldgenChatService(request.user)

        # Check if LLM is configured for AI collab mode
        mode = create_serializer.validated_data["mode"]
        if mode == "ai_collab" and not service.has_llm_config():
            return Response(
                {"error": "No LLM endpoint configured. Please configure an LLM endpoint in settings."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = service.create_session(mode=mode)
        serializer = WorldgenSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WorldgenSessionDetailView(APIView):
    """
    GET /api/universes/worldgen/sessions/{id}/ - Get session details
    DELETE /api/universes/worldgen/sessions/{id}/ - Abandon session
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        """Get session details."""
        from .serializers import WorldgenSessionSerializer
        from .services.worldgen_chat import WorldgenChatService

        service = WorldgenChatService(request.user)
        session = service.get_session(session_id)

        if not session:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = WorldgenSessionSerializer(session)
        return Response(serializer.data)

    def delete(self, request, session_id):
        """Abandon a session."""
        from .services.worldgen_chat import WorldgenChatService

        service = WorldgenChatService(request.user)
        try:
            service.abandon_session(session_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class WorldgenSessionChatView(APIView):
    """
    POST /api/universes/worldgen/sessions/{id}/chat/ - Send chat message (SSE streaming)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        """Send a chat message and stream the response via SSE."""
        import json
        from django.http import StreamingHttpResponse
        from .serializers import WorldgenChatMessageSerializer
        from .services.worldgen_chat import WorldgenChatService

        serializer = WorldgenChatMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = WorldgenChatService(request.user)
        session = service.get_session(session_id)

        if not session:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not service.has_llm_config():
            return Response(
                {"error": "No LLM endpoint configured"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        def event_stream():
            """Generate SSE events from chat stream."""
            try:
                for event in service.send_message_stream(
                    session_id, serializer.validated_data["message"]
                ):
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as e:
                logger.exception("Worldgen chat stream failed for session %s", session_id)
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class WorldgenSessionUpdateView(APIView):
    """
    PATCH /api/universes/worldgen/sessions/{id}/update/ - Update step data directly
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, session_id):
        """Update step data directly (for manual mode)."""
        from .serializers import WorldgenSessionSerializer, WorldgenStepUpdateSerializer
        from .services.worldgen_chat import WorldgenChatService

        serializer = WorldgenStepUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = WorldgenChatService(request.user)
        try:
            session = service.update_draft_data(
                session_id,
                serializer.validated_data["step"],
                serializer.validated_data["data"],
            )
            result_serializer = WorldgenSessionSerializer(session)
            return Response(result_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class WorldgenSessionModeView(APIView):
    """
    POST /api/universes/worldgen/sessions/{id}/mode/ - Switch mode
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        """Switch between AI collab and manual mode."""
        from .serializers import WorldgenSessionSerializer
        from .services.worldgen_chat import WorldgenChatService

        new_mode = request.data.get("mode")
        if new_mode not in ("ai_collab", "manual"):
            return Response(
                {"error": "Mode must be 'ai_collab' or 'manual'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = WorldgenChatService(request.user)

        # Check LLM config when switching to AI mode
        if new_mode == "ai_collab" and not service.has_llm_config():
            return Response(
                {"error": "No LLM endpoint configured"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session = service.switch_mode(session_id, new_mode)
            serializer = WorldgenSessionSerializer(session)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class WorldgenSessionFinalizeView(APIView):
    """
    POST /api/universes/worldgen/sessions/{id}/finalize/ - Create universe from session
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        """Finalize session and create universe."""
        from .serializers import UniverseSerializer
        from .services.worldgen_chat import WorldgenChatService

        service = WorldgenChatService(request.user)
        try:
            universe = service.finalize_session(session_id)
            serializer = UniverseSerializer(universe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WorldgenSessionAiAssistView(APIView):
    """
    POST /api/universes/worldgen/sessions/{id}/assist/ - Get AI help for a specific step
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        """Get AI assistance for a step (streaming SSE)."""
        import json
        from django.http import StreamingHttpResponse
        from .serializers import WorldgenAiAssistSerializer
        from .services.worldgen_chat import WorldgenChatService

        serializer = WorldgenAiAssistSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = WorldgenChatService(request.user)
        session = service.get_session(session_id)

        if not session:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not service.has_llm_config():
            return Response(
                {"error": "No LLM endpoint configured"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        def event_stream():
            """Generate SSE events from AI assist stream."""
            try:
                for event in service.get_ai_assist(
                    session_id,
                    serializer.validated_data["step"],
                    serializer.validated_data.get("field"),
                    serializer.validated_data.get("message"),
                ):
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class WorldgenLlmStatusView(APIView):
    """
    GET /api/universes/worldgen/llm-status/ - Check if LLM is configured
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Check if user has an active LLM configuration."""
        from .services.worldgen_chat import WorldgenChatService

        service = WorldgenChatService(request.user)
        return Response({
            "configured": service.has_llm_config(),
        })
