"""
Character views - CRUD operations for player characters.

Endpoints:
- GET /api/characters/ - List current user's characters
- POST /api/characters/ - Create new character
- GET /api/characters/{id}/ - Get character details
- PUT/PATCH /api/characters/{id}/ - Update character
- DELETE /api/characters/{id}/ - Delete character
"""

from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.characters.models import CharacterSheet
from apps.characters.serializers import (
    CharacterCreateSerializer,
    CharacterDetailSerializer,
    CharacterListSerializer,
    CharacterUpdateSerializer,
)


class CharacterFilter(filters.FilterSet):
    """Filter for character list."""

    name = filters.CharFilter(lookup_expr="icontains")
    species = filters.CharFilter(lookup_expr="iexact")
    character_class = filters.CharFilter(lookup_expr="iexact")
    level_min = filters.NumberFilter(field_name="level", lookup_expr="gte")
    level_max = filters.NumberFilter(field_name="level", lookup_expr="lte")
    universe = filters.UUIDFilter()

    class Meta:
        model = CharacterSheet
        fields = ["name", "species", "character_class", "level_min", "level_max", "universe"]


class CharacterListCreateView(generics.ListCreateAPIView):
    """
    GET /api/characters/ - List current user's characters.
    POST /api/characters/ - Create a new character.

    Query parameters for filtering:
    - name: Filter by name (case-insensitive contains)
    - species: Filter by species (exact match)
    - character_class: Filter by class (exact match)
    - level_min: Minimum level
    - level_max: Maximum level
    - universe: Filter by universe ID
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CharacterFilter

    def get_queryset(self):
        """Return characters owned by the current user."""
        return CharacterSheet.objects.filter(user=self.request.user).order_by(
            "-updated_at"
        )

    def get_serializer_class(self):
        """Use different serializers for list and create."""
        if self.request.method == "POST":
            return CharacterCreateSerializer
        return CharacterListSerializer

    def create(self, request, *args, **kwargs):
        """Create a new character for the current user."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        character = serializer.save()

        # Return the full detail serializer with the created character
        detail_serializer = CharacterDetailSerializer(character)
        response_data = detail_serializer.data

        # Add any validation warnings to the response
        if hasattr(serializer, "_validation_warnings") and serializer._validation_warnings:
            response_data["validation_warnings"] = serializer._validation_warnings

        return Response(response_data, status=status.HTTP_201_CREATED)


class CharacterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/characters/{id}/ - Get character details.
    PUT/PATCH /api/characters/{id}/ - Update character.
    DELETE /api/characters/{id}/ - Delete character.

    Only the character's owner can access/modify it.
    """

    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        """Return characters owned by the current user."""
        return CharacterSheet.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use different serializers for retrieve and update."""
        if self.request.method in ("PUT", "PATCH"):
            return CharacterUpdateSerializer
        return CharacterDetailSerializer

    def update(self, request, *args, **kwargs):
        """Update character with validation."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return full detail serializer with updated data
        detail_serializer = CharacterDetailSerializer(instance)
        response_data = detail_serializer.data

        # Add any validation warnings
        if hasattr(serializer, "_validation_warnings") and serializer._validation_warnings:
            response_data["validation_warnings"] = serializer._validation_warnings

        return Response(response_data)

    def destroy(self, request, *args, **kwargs):
        """Delete a character."""
        instance = self.get_object()
        character_name = instance.name
        self.perform_destroy(instance)
        return Response(
            {"message": f"Character '{character_name}' deleted successfully."},
            status=status.HTTP_200_OK,
        )
