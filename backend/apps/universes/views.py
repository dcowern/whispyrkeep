"""
Views for universe and homebrew content APIs.

Provides CRUD endpoints for managing universes and their homebrew content.
All endpoints require authentication and are scoped to the authenticated user.
"""

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
