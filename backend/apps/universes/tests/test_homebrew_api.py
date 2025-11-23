"""
API tests for homebrew content endpoints.

Tests CRUD operations for all homebrew content types including:
- Authentication requirements
- User ownership scoping
- Locking functionality
- Filtering and search
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.srd.models import (
    Condition,
    DamageType,
    ItemCategory,
    MonsterType,
    SpellSchool,
)
from apps.universes.models import (
    HomebrewFeat,
    HomebrewItem,
    HomebrewMonster,
    HomebrewSpecies,
    HomebrewSpell,
    Universe,
)

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        username="testuser",
    )


@pytest.fixture
def other_user(db):
    """Create another test user."""
    return User.objects.create_user(
        email="other@example.com",
        password="testpass123",
        username="otheruser",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def universe(user):
    """Create a test universe."""
    return Universe.objects.create(
        user=user,
        name="Test Universe",
        description="A universe for testing",
    )


@pytest.fixture
def other_universe(other_user):
    """Create a universe owned by another user."""
    return Universe.objects.create(
        user=other_user,
        name="Other Universe",
        description="Belongs to another user",
    )


@pytest.fixture
def spell_school(db):
    """Create a test spell school."""
    return SpellSchool.objects.create(name="Evocation")


@pytest.fixture
def damage_type(db):
    """Create a test damage type."""
    return DamageType.objects.create(name="Fire")


@pytest.fixture
def item_category(db):
    """Create a test item category."""
    return ItemCategory.objects.create(name="Weapon")


@pytest.fixture
def monster_type(db):
    """Create a test monster type."""
    return MonsterType.objects.create(name="Dragon")


@pytest.fixture
def condition(db):
    """Create a test condition."""
    return Condition.objects.create(
        name="Frightened",
        description="The creature is frightened",
    )


# ==================== Universe API Tests ====================


@pytest.mark.django_db
class TestUniverseAPI:
    """Tests for Universe CRUD endpoints."""

    def test_list_universes_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot list universes."""
        response = api_client.get("/api/universes/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_universes(self, authenticated_client, universe):
        """Test listing user's universes."""
        response = authenticated_client.get("/api/universes/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Test Universe"

    def test_list_universes_only_own(self, authenticated_client, universe, other_universe):
        """Test that users only see their own universes."""
        response = authenticated_client.get("/api/universes/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Test Universe"

    def test_create_universe(self, authenticated_client):
        """Test creating a new universe."""
        response = authenticated_client.post(
            "/api/universes/",
            {
                "name": "New Universe",
                "description": "A brand new universe",
                "tone_profile_json": {"grimdark": 0.3},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Universe"
        assert Universe.objects.filter(name="New Universe").exists()

    def test_get_universe(self, authenticated_client, universe):
        """Test retrieving a specific universe."""
        response = authenticated_client.get(f"/api/universes/{universe.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Universe"

    def test_update_universe(self, authenticated_client, universe):
        """Test updating a universe."""
        response = authenticated_client.patch(
            f"/api/universes/{universe.id}/",
            {"description": "Updated description"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        universe.refresh_from_db()
        assert universe.description == "Updated description"

    def test_delete_universe(self, authenticated_client, universe):
        """Test deleting a universe."""
        response = authenticated_client.delete(f"/api/universes/{universe.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Universe.objects.filter(id=universe.id).exists()

    def test_cannot_access_other_users_universe(self, authenticated_client, other_universe):
        """Test that users cannot access another user's universe."""
        response = authenticated_client.get(f"/api/universes/{other_universe.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ==================== Homebrew Species API Tests ====================


@pytest.mark.django_db
class TestHomebrewSpeciesAPI:
    """Tests for HomebrewSpecies CRUD endpoints."""

    def test_list_species_empty(self, authenticated_client, universe):
        """Test listing species when none exist."""
        response = authenticated_client.get(
            f"/api/universes/{universe.id}/homebrew/species/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    def test_create_species(self, authenticated_client, universe):
        """Test creating a homebrew species."""
        response = authenticated_client.post(
            f"/api/universes/{universe.id}/homebrew/species/",
            {
                "name": "Starborn",
                "description": "A celestial species",
                "source_type": "homebrew",
                "power_tier": "standard",
                "size": "medium",
                "speed": 30,
                "ability_bonuses": {"wis": 2, "cha": 1},
                "darkvision": 60,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Starborn"
        assert HomebrewSpecies.objects.filter(name="Starborn").exists()

    def test_get_species(self, authenticated_client, universe):
        """Test retrieving a specific species."""
        species = HomebrewSpecies.objects.create(
            universe=universe,
            name="Test Species",
            size="medium",
        )
        response = authenticated_client.get(
            f"/api/universes/{universe.id}/homebrew/species/{species.id}/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Species"

    def test_update_species(self, authenticated_client, universe):
        """Test updating a species."""
        species = HomebrewSpecies.objects.create(
            universe=universe,
            name="Test Species",
            size="medium",
        )
        response = authenticated_client.patch(
            f"/api/universes/{universe.id}/homebrew/species/{species.id}/",
            {"speed": 35},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        species.refresh_from_db()
        assert species.speed == 35

    def test_delete_species(self, authenticated_client, universe):
        """Test deleting a species."""
        species = HomebrewSpecies.objects.create(
            universe=universe,
            name="Test Species",
            size="medium",
        )
        response = authenticated_client.delete(
            f"/api/universes/{universe.id}/homebrew/species/{species.id}/"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not HomebrewSpecies.objects.filter(id=species.id).exists()

    def test_cannot_modify_locked_species(self, authenticated_client, universe):
        """Test that locked species cannot be modified."""
        species = HomebrewSpecies.objects.create(
            universe=universe,
            name="Locked Species",
            size="medium",
            is_locked=True,
        )
        response = authenticated_client.patch(
            f"/api/universes/{universe.id}/homebrew/species/{species.id}/",
            {"speed": 35},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== Homebrew Spell API Tests ====================


@pytest.mark.django_db
class TestHomebrewSpellAPI:
    """Tests for HomebrewSpell CRUD endpoints."""

    def test_create_spell(self, authenticated_client, universe, spell_school, damage_type):
        """Test creating a homebrew spell."""
        response = authenticated_client.post(
            f"/api/universes/{universe.id}/homebrew/spells/",
            {
                "name": "Celestial Burst",
                "description": "A burst of celestial energy",
                "level": 3,
                "school_id": spell_school.id,
                "casting_time": "1 action",
                "range": "60 feet",
                "duration": "Instantaneous",
                "damage_type_id": damage_type.id,
                "dice_expression": "6d8",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Celestial Burst"
        assert response.data["level"] == 3

    def test_filter_spells_by_level(self, authenticated_client, universe, spell_school):
        """Test filtering spells by level."""
        HomebrewSpell.objects.create(
            universe=universe,
            name="Cantrip",
            level=0,
            school=spell_school,
            casting_time="1 action",
            range="Self",
            duration="1 minute",
        )
        HomebrewSpell.objects.create(
            universe=universe,
            name="First Level",
            level=1,
            school=spell_school,
            casting_time="1 action",
            range="Self",
            duration="1 hour",
        )

        response = authenticated_client.get(
            f"/api/universes/{universe.id}/homebrew/spells/?level=0"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Cantrip"


# ==================== Homebrew Item API Tests ====================


@pytest.mark.django_db
class TestHomebrewItemAPI:
    """Tests for HomebrewItem CRUD endpoints."""

    def test_create_weapon(self, authenticated_client, universe, item_category, damage_type):
        """Test creating a homebrew weapon."""
        response = authenticated_client.post(
            f"/api/universes/{universe.id}/homebrew/items/",
            {
                "name": "Celestial Blade",
                "category_id": item_category.id,
                "rarity": "rare",
                "magical": True,
                "is_weapon": True,
                "weapon_type": "martial_melee",
                "damage_dice": "1d10",
                "damage_type_id": damage_type.id,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Celestial Blade"
        assert response.data["is_weapon"] is True

    def test_filter_items_by_rarity(self, authenticated_client, universe, item_category):
        """Test filtering items by rarity."""
        HomebrewItem.objects.create(
            universe=universe,
            name="Common Item",
            category=item_category,
            rarity="common",
        )
        HomebrewItem.objects.create(
            universe=universe,
            name="Rare Item",
            category=item_category,
            rarity="rare",
        )

        response = authenticated_client.get(
            f"/api/universes/{universe.id}/homebrew/items/?rarity=rare"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Rare Item"


# ==================== Homebrew Monster API Tests ====================


@pytest.mark.django_db
class TestHomebrewMonsterAPI:
    """Tests for HomebrewMonster CRUD endpoints."""

    def test_create_monster(self, authenticated_client, universe, monster_type):
        """Test creating a homebrew monster."""
        response = authenticated_client.post(
            f"/api/universes/{universe.id}/homebrew/monsters/",
            {
                "name": "Star Drake",
                "monster_type_id": monster_type.id,
                "size": "huge",
                "armor_class": 18,
                "hit_points": 200,
                "hit_dice": "17d12+85",
                "speed": {"walk": 40, "fly": 80},
                "ability_scores": {"str": 22, "dex": 14, "con": 20, "int": 16, "wis": 18, "cha": 20},
                "challenge_rating": "12.00",
                "experience_points": 8400,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Star Drake"
        assert response.data["challenge_rating"] == "12.00"

    def test_filter_monsters_by_cr(self, authenticated_client, universe, monster_type):
        """Test filtering monsters by challenge rating."""
        HomebrewMonster.objects.create(
            universe=universe,
            name="Low CR Monster",
            monster_type=monster_type,
            size="small",
            armor_class=10,
            hit_points=10,
            hit_dice="2d6",
            challenge_rating=Decimal("0.5"),
            experience_points=100,
        )
        HomebrewMonster.objects.create(
            universe=universe,
            name="High CR Monster",
            monster_type=monster_type,
            size="huge",
            armor_class=18,
            hit_points=200,
            hit_dice="17d12",
            challenge_rating=Decimal("15.00"),
            experience_points=13000,
        )

        response = authenticated_client.get(
            f"/api/universes/{universe.id}/homebrew/monsters/?challenge_rating__lte=5"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Low CR Monster"


# ==================== Homebrew Feat API Tests ====================


@pytest.mark.django_db
class TestHomebrewFeatAPI:
    """Tests for HomebrewFeat CRUD endpoints."""

    def test_create_feat(self, authenticated_client, universe):
        """Test creating a homebrew feat."""
        response = authenticated_client.post(
            f"/api/universes/{universe.id}/homebrew/feats/",
            {
                "name": "Celestial Blessing",
                "description": "You have been blessed",
                "prerequisites": {"level": 4},
                "benefits": ["Gain darkvision 60 feet", "Learn light cantrip"],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Celestial Blessing"


# ==================== Lock Homebrew Tests ====================


@pytest.mark.django_db
class TestLockHomebrew:
    """Tests for the lock_homebrew action."""

    def test_lock_homebrew(self, authenticated_client, universe, spell_school, monster_type, item_category):
        """Test locking all homebrew content for a universe."""
        # Create some unlocked homebrew content
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Unlocked Species",
            size="medium",
            is_locked=False,
        )
        HomebrewSpell.objects.create(
            universe=universe,
            name="Unlocked Spell",
            level=1,
            school=spell_school,
            casting_time="1 action",
            range="Self",
            duration="1 hour",
            is_locked=False,
        )
        HomebrewFeat.objects.create(
            universe=universe,
            name="Unlocked Feat",
            is_locked=False,
        )

        response = authenticated_client.post(
            f"/api/universes/{universe.id}/lock_homebrew/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "locked_counts" in response.data
        assert response.data["locked_counts"]["species"] == 1
        assert response.data["locked_counts"]["spells"] == 1
        assert response.data["locked_counts"]["feats"] == 1

        # Verify content is actually locked
        species = HomebrewSpecies.objects.get(name="Unlocked Species")
        assert species.is_locked is True


# ==================== Search and Filter Tests ====================


@pytest.mark.django_db
class TestSearchAndFilter:
    """Tests for search and filter functionality."""

    def test_search_species_by_name(self, authenticated_client, universe):
        """Test searching species by name."""
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Starborn",
            size="medium",
        )
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Earthkin",
            size="medium",
        )

        response = authenticated_client.get(
            f"/api/universes/{universe.id}/homebrew/species/?search=star"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Starborn"

    def test_filter_by_source_type(self, authenticated_client, universe):
        """Test filtering by source_type."""
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Homebrew Species",
            size="medium",
            source_type="homebrew",
        )
        HomebrewSpecies.objects.create(
            universe=universe,
            name="SRD Derived Species",
            size="medium",
            source_type="srd_derived",
        )

        response = authenticated_client.get(
            f"/api/universes/{universe.id}/homebrew/species/?source_type=homebrew"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Homebrew Species"

    def test_filter_by_power_tier(self, authenticated_client, universe):
        """Test filtering by power_tier."""
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Weak Species",
            size="small",
            power_tier="weak",
        )
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Legendary Species",
            size="medium",
            power_tier="legendary",
        )

        response = authenticated_client.get(
            f"/api/universes/{universe.id}/homebrew/species/?power_tier=legendary"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Legendary Species"
