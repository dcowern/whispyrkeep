"""
Character API URL configuration.

Uses DRF routers to generate CRUD endpoints for CharacterSheet.
"""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"", views.CharacterSheetViewSet, basename="character")

urlpatterns = router.urls
