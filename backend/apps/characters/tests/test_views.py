"""
Tests for character API views.

Tests the CharacterSheet CRUD endpoints.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.characters.models import CharacterSheet
from apps.universes.models import Universe

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def user():
    """Create test user."""
    return User.objects.create_user(
        username="testplayer",
        email="player@example.com",
        password="testpass123",
        display_name="Test Player",
    )


@pytest.fixture
def other_user():
    """Create another test user."""
    return User.objects.create_user(
        username="otherplayer",
        email="other@example.com",
        password="testpass123",
        display_name="Other Player",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Create authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def universe(user):
    """Create test universe."""
    return Universe.objects.create(
        user=user,
        name="Test Universe",
        description="A test universe",
    )


@pytest.fixture
def character(user, universe):
    """Create test character."""
    return CharacterSheet.objects.create(
        user=user,
        universe=universe,
        name="Test Character",
        species="Human",
        character_class="Fighter",
        background="Soldier",
        level=5,
        ability_scores_json={
            "str": 16,
            "dex": 14,
            "con": 12,
            "int": 10,
            "wis": 8,
            "cha": 15,
        },
    )


@pytest.fixture
def other_character(other_user):
    """Create character owned by another user."""
    return CharacterSheet.objects.create(
        user=other_user,
        name="Other Character",
        species="Elf",
        character_class="Wizard",
        background="Sage",
        level=3,
    )


@pytest.mark.django_db
class TestCharacterListEndpoint:
    """Tests for GET /api/characters/."""

    def test_list_requires_auth(self, api_client):
        """Test that list endpoint requires authentication."""
        response = api_client.get(reverse("character_list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_returns_user_characters(self, authenticated_client, character):
        """Test that list returns only user's characters."""
        response = authenticated_client.get(reverse("character_list"))

        assert response.status_code == status.HTTP_200_OK
        # Check that character is in results
        results = response.data.get("results", response.data)
        assert len(results) >= 1
        assert any(c["id"] == str(character.id) for c in results)

    def test_list_excludes_other_users_characters(
        self, authenticated_client, character, other_character
    ):
        """Test that list excludes other users' characters."""
        response = authenticated_client.get(reverse("character_list"))

        results = response.data.get("results", response.data)
        character_ids = [c["id"] for c in results]
        assert str(character.id) in character_ids
        assert str(other_character.id) not in character_ids

    def test_list_filtering_by_name(self, authenticated_client, character, user):
        """Test filtering characters by name."""
        # Create another character
        CharacterSheet.objects.create(
            user=user,
            name="Another Hero",
            species="Dwarf",
            character_class="Cleric",
            background="Acolyte",
        )

        response = authenticated_client.get(
            reverse("character_list"), {"name": "Test"}
        )

        results = response.data.get("results", response.data)
        assert len(results) == 1
        assert results[0]["name"] == "Test Character"

    def test_list_filtering_by_level_range(self, authenticated_client, character, user):
        """Test filtering characters by level range."""
        # Create low level character
        CharacterSheet.objects.create(
            user=user,
            name="Newbie",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=1,
        )

        response = authenticated_client.get(
            reverse("character_list"), {"level_min": 3}
        )

        results = response.data.get("results", response.data)
        # Should only return character with level >= 3
        for char in results:
            assert char["level"] >= 3


@pytest.mark.django_db
class TestCharacterCreateEndpoint:
    """Tests for POST /api/characters/."""

    def test_create_requires_auth(self, api_client):
        """Test that create endpoint requires authentication."""
        response = api_client.post(
            reverse("character_list"),
            {"name": "Test", "species": "Human", "character_class": "Fighter", "background": "Soldier"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_character_success(self, authenticated_client, user, srd_data):
        """Test creating a character."""
        data = {
            "name": "New Character",
            "species": "Human",
            "character_class": "Fighter",
            "background": "Soldier",
            "level": 3,
            "ability_scores_json": {
                "str": 16,
                "dex": 14,
                "con": 12,
                "int": 10,
                "wis": 8,
                "cha": 15,
            },
        }
        response = authenticated_client.post(
            reverse("character_list"), data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Character"
        assert response.data["level"] == 3
        assert str(response.data["user"]) == str(user.id)

    def test_create_character_with_universe(self, authenticated_client, universe, srd_data):
        """Test creating a character tied to a universe."""
        data = {
            "name": "Universe Character",
            "species": "Human",
            "character_class": "Fighter",
            "background": "Soldier",
            "universe": str(universe.id),
        }
        response = authenticated_client.post(
            reverse("character_list"), data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data["universe"]) == str(universe.id)

    def test_create_character_missing_required_fields(self, authenticated_client):
        """Test creating character with missing fields fails."""
        data = {"name": "Incomplete"}
        response = authenticated_client.post(
            reverse("character_list"), data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_character_invalid_level(self, authenticated_client):
        """Test creating character with invalid level fails."""
        data = {
            "name": "Bad Level",
            "species": "Human",
            "character_class": "Fighter",
            "background": "Soldier",
            "level": 25,  # Invalid - max is 20
        }
        response = authenticated_client.post(
            reverse("character_list"), data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCharacterDetailEndpoint:
    """Tests for GET /api/characters/{id}/."""

    def test_detail_requires_auth(self, api_client, character):
        """Test that detail endpoint requires authentication."""
        response = api_client.get(
            reverse("character_detail", kwargs={"id": character.id})
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_detail_returns_character(self, authenticated_client, character):
        """Test retrieving character details."""
        response = authenticated_client.get(
            reverse("character_detail", kwargs={"id": character.id})
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Character"
        assert response.data["level"] == 5
        assert "ability_scores_json" in response.data

    def test_detail_404_for_nonexistent(self, authenticated_client):
        """Test 404 for nonexistent character."""
        import uuid

        fake_id = uuid.uuid4()
        response = authenticated_client.get(
            reverse("character_detail", kwargs={"id": fake_id})
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_404_for_other_users_character(
        self, authenticated_client, other_character
    ):
        """Test 404 for another user's character."""
        response = authenticated_client.get(
            reverse("character_detail", kwargs={"id": other_character.id})
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCharacterUpdateEndpoint:
    """Tests for PUT/PATCH /api/characters/{id}/."""

    def test_update_requires_auth(self, api_client, character):
        """Test that update endpoint requires authentication."""
        response = api_client.put(
            reverse("character_detail", kwargs={"id": character.id}),
            {"name": "Updated"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_full_update_character(self, authenticated_client, character, srd_data):
        """Test full update of character."""
        data = {
            "name": "Updated Character",
            "species": "Human",
            "character_class": "Fighter",
            "background": "Soldier",
            "level": 10,
            "ability_scores_json": {
                "str": 18,
                "dex": 14,
                "con": 14,
                "int": 10,
                "wis": 10,
                "cha": 12,
            },
        }
        response = authenticated_client.put(
            reverse("character_detail", kwargs={"id": character.id}),
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Character"
        assert response.data["level"] == 10

    def test_partial_update_character(self, authenticated_client, character, srd_data):
        """Test partial update of character."""
        response = authenticated_client.patch(
            reverse("character_detail", kwargs={"id": character.id}),
            {"level": 8},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["level"] == 8
        assert response.data["name"] == "Test Character"  # Unchanged

    def test_cannot_update_other_users_character(
        self, authenticated_client, other_character
    ):
        """Test cannot update another user's character."""
        response = authenticated_client.patch(
            reverse("character_detail", kwargs={"id": other_character.id}),
            {"level": 20},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCharacterDeleteEndpoint:
    """Tests for DELETE /api/characters/{id}/."""

    def test_delete_requires_auth(self, api_client, character):
        """Test that delete endpoint requires authentication."""
        response = api_client.delete(
            reverse("character_detail", kwargs={"id": character.id})
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_character(self, authenticated_client, character, user):
        """Test deleting a character."""
        character_id = character.id
        response = authenticated_client.delete(
            reverse("character_detail", kwargs={"id": character_id})
        )

        assert response.status_code == status.HTTP_200_OK
        assert "deleted" in response.data["message"].lower()
        assert not CharacterSheet.objects.filter(id=character_id).exists()

    def test_cannot_delete_other_users_character(
        self, authenticated_client, other_character
    ):
        """Test cannot delete another user's character."""
        response = authenticated_client.delete(
            reverse("character_detail", kwargs={"id": other_character.id})
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        # Character should still exist
        assert CharacterSheet.objects.filter(id=other_character.id).exists()
