"""
SRD Catalog API views.

Read-only endpoints for accessing SRD 5.2 reference data.
All endpoints are publicly accessible (no authentication required)
as SRD data is open reference material.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import (
    AbilityScore,
    Background,
    CharacterClass,
    Condition,
    DamageType,
    Feat,
    Item,
    ItemCategory,
    Monster,
    MonsterType,
    Skill,
    Species,
    Spell,
    SpellSchool,
    Subclass,
)
from .serializers import (
    AbilityScoreSerializer,
    BackgroundSerializer,
    CharacterClassSerializer,
    ConditionSerializer,
    DamageTypeSerializer,
    FeatSerializer,
    ItemCategorySerializer,
    ItemSerializer,
    ItemSummarySerializer,
    MonsterSerializer,
    MonsterSummarySerializer,
    MonsterTypeSerializer,
    SkillSerializer,
    SpeciesSerializer,
    SpellSchoolSerializer,
    SpellSerializer,
    SpellSummarySerializer,
    SubclassSerializer,
)


class AbilityScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/ability-scores - List all ability scores.
    GET /api/srd/ability-scores/{id} - Retrieve specific ability score.
    """

    queryset = AbilityScore.objects.all()
    serializer_class = AbilityScoreSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Small fixed dataset


class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/skills - List all skills.
    GET /api/srd/skills/{id} - Retrieve specific skill.

    Filter by ability score using ?ability_score=<id>
    """

    queryset = Skill.objects.select_related("ability_score").all()
    serializer_class = SkillSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Small fixed dataset
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["ability_score"]


class ConditionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/conditions - List all conditions.
    GET /api/srd/conditions/{id} - Retrieve specific condition.
    """

    queryset = Condition.objects.all()
    serializer_class = ConditionSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Small fixed dataset


class DamageTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/damage-types - List all damage types.
    GET /api/srd/damage-types/{id} - Retrieve specific damage type.
    """

    queryset = DamageType.objects.all()
    serializer_class = DamageTypeSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Small fixed dataset


class SpeciesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/species - List all playable species.
    GET /api/srd/species/{id} - Retrieve specific species.

    Search by name using ?search=<term>
    Filter by size using ?size=<small|medium|large>
    """

    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["size"]
    search_fields = ["name"]


class CharacterClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/classes - List all character classes.
    GET /api/srd/classes/{id} - Retrieve specific class with features.

    Search by name using ?search=<term>
    """

    queryset = CharacterClass.objects.prefetch_related(
        "subclasses",
        "saving_throw_proficiencies",
    ).select_related(
        "primary_ability",
        "spellcasting_ability",
    ).all()
    serializer_class = CharacterClassSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    @action(detail=True, methods=["get"])
    def subclasses(self, request, pk=None):
        """GET /api/srd/classes/{id}/subclasses - List subclasses for a class."""
        character_class = self.get_object()
        subclasses = character_class.subclasses.all()
        serializer = SubclassSerializer(subclasses, many=True)
        return Response(serializer.data)


class SubclassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/subclasses - List all subclasses.
    GET /api/srd/subclasses/{id} - Retrieve specific subclass.

    Filter by class using ?character_class=<id>
    """

    queryset = Subclass.objects.select_related("character_class").all()
    serializer_class = SubclassSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["character_class"]
    search_fields = ["name"]


class BackgroundViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/backgrounds - List all backgrounds.
    GET /api/srd/backgrounds/{id} - Retrieve specific background.

    Search by name using ?search=<term>
    """

    queryset = Background.objects.prefetch_related("skill_proficiencies").all()
    serializer_class = BackgroundSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class SpellSchoolViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/spell-schools - List all spell schools.
    GET /api/srd/spell-schools/{id} - Retrieve specific spell school.
    """

    queryset = SpellSchool.objects.all()
    serializer_class = SpellSchoolSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Small fixed dataset


class SpellViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/spells - List all spells (paginated).
    GET /api/srd/spells/{id} - Retrieve specific spell.

    Filter by:
    - level: ?level=0 (cantrips), ?level=1, etc.
    - school: ?school=<id>
    - concentration: ?concentration=true/false
    - ritual: ?ritual=true/false
    - classes: ?classes=<id> (spells available to a class)

    Search by name using ?search=<term>
    """

    queryset = Spell.objects.select_related(
        "school",
        "damage_type",
    ).prefetch_related("classes").all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["level", "school", "concentration", "ritual", "classes"]
    search_fields = ["name"]
    ordering_fields = ["level", "name"]
    ordering = ["level", "name"]

    def get_serializer_class(self):
        """Use summary serializer for list view."""
        if self.action == "list":
            return SpellSummarySerializer
        return SpellSerializer


class ItemCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/item-categories - List all item categories.
    GET /api/srd/item-categories/{id} - Retrieve specific category.
    """

    queryset = ItemCategory.objects.all()
    serializer_class = ItemCategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Small fixed dataset


class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/items - List all items (paginated).
    GET /api/srd/items/{id} - Retrieve specific item with weapon/armor stats.

    Filter by:
    - category: ?category=<id>
    - rarity: ?rarity=common/uncommon/rare/very_rare/legendary/artifact
    - magical: ?magical=true/false

    Search by name using ?search=<term>
    """

    queryset = Item.objects.select_related(
        "category",
        "weapon_stats",
        "weapon_stats__damage_type",
        "armor_stats",
    ).all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "rarity", "magical"]
    search_fields = ["name"]
    ordering_fields = ["name", "cost_gp", "rarity"]
    ordering = ["name"]

    def get_serializer_class(self):
        """Use summary serializer for list view."""
        if self.action == "list":
            return ItemSummarySerializer
        return ItemSerializer


class MonsterTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/monster-types - List all monster types.
    GET /api/srd/monster-types/{id} - Retrieve specific monster type.
    """

    queryset = MonsterType.objects.all()
    serializer_class = MonsterTypeSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Small fixed dataset


class MonsterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/monsters - List all monsters (paginated).
    GET /api/srd/monsters/{id} - Retrieve specific monster with full stats.

    Filter by:
    - monster_type: ?monster_type=<id>
    - size: ?size=tiny/small/medium/large/huge/gargantuan
    - challenge_rating: ?challenge_rating=0.5 (exact match)
    - challenge_rating__lte: ?challenge_rating__lte=5 (CR 5 or lower)
    - challenge_rating__gte: ?challenge_rating__gte=10 (CR 10 or higher)

    Search by name using ?search=<term>
    """

    queryset = Monster.objects.select_related(
        "monster_type",
    ).prefetch_related(
        "damage_vulnerabilities",
        "damage_resistances",
        "damage_immunities",
        "condition_immunities",
    ).all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "monster_type": ["exact"],
        "size": ["exact"],
        "challenge_rating": ["exact", "lte", "gte"],
    }
    search_fields = ["name"]
    ordering_fields = ["challenge_rating", "name", "hit_points"]
    ordering = ["challenge_rating", "name"]

    def get_serializer_class(self):
        """Use summary serializer for list view."""
        if self.action == "list":
            return MonsterSummarySerializer
        return MonsterSerializer


class FeatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/srd/feats - List all feats.
    GET /api/srd/feats/{id} - Retrieve specific feat.

    Search by name using ?search=<term>
    """

    queryset = Feat.objects.all()
    serializer_class = FeatSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
