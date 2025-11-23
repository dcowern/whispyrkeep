"""
URL configuration for SRD catalog API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AbilityScoreViewSet,
    BackgroundViewSet,
    CharacterClassViewSet,
    ConditionViewSet,
    DamageTypeViewSet,
    FeatViewSet,
    ItemCategoryViewSet,
    ItemViewSet,
    MonsterTypeViewSet,
    MonsterViewSet,
    SkillViewSet,
    SpeciesViewSet,
    SpellSchoolViewSet,
    SpellViewSet,
    SubclassViewSet,
)

router = DefaultRouter()
router.register(r"ability-scores", AbilityScoreViewSet, basename="abilityscore")
router.register(r"skills", SkillViewSet, basename="skill")
router.register(r"conditions", ConditionViewSet, basename="condition")
router.register(r"damage-types", DamageTypeViewSet, basename="damagetype")
router.register(r"species", SpeciesViewSet, basename="species")
router.register(r"classes", CharacterClassViewSet, basename="characterclass")
router.register(r"subclasses", SubclassViewSet, basename="subclass")
router.register(r"backgrounds", BackgroundViewSet, basename="background")
router.register(r"spell-schools", SpellSchoolViewSet, basename="spellschool")
router.register(r"spells", SpellViewSet, basename="spell")
router.register(r"item-categories", ItemCategoryViewSet, basename="itemcategory")
router.register(r"items", ItemViewSet, basename="item")
router.register(r"monster-types", MonsterTypeViewSet, basename="monstertype")
router.register(r"monsters", MonsterViewSet, basename="monster")
router.register(r"feats", FeatViewSet, basename="feat")

urlpatterns = [
    path("", include(router.urls)),
]
