"""
API tests for Character endpoints.

Tests CRUD operations, validation endpoint, HP management, and conditions.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.characters.models import CharacterSheet
from apps.srd.models import Background, CharacterClass, Species

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testapi",
        email="api@test.com",
        password="testpass123",
    )


@pytest.fixture
def other_user(db):
    """Create another user for permission tests."""
    return User.objects.create_user(
        username="otheruser",
        email="other@test.com",
        password="testpass123",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Create authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def srd_data(db):
    """Create minimal SRD data for validation."""
    Species.objects.create(name="Human", size="medium", speed=30)
    CharacterClass.objects.create(name="Fighter", hit_die=10)
    Background.objects.create(name="Soldier")
    return True


@pytest.fixture
def character(user, srd_data):
    """Create a test character."""
    return CharacterSheet.objects.create(
        user=user,
        name="Test Hero",
        species="Human",
        character_class="Fighter",
        background="Soldier",
        level=5,
        hit_points_max=44,
        hit_points_current=44,
        hit_points_temp=0,
        ability_scores_json={
            "str": 16,
            "dex": 14,
            "con": 14,
            "int": 10,
            "wis": 12,
            "cha": 8,
        },
        skills_json={
            "Athletics": {"proficient": True, "expertise": False},
        },
        proficiencies_json={
            "saving_throws": ["str", "con"],
        },
        hit_dice_json={"d10": {"max": 5, "spent": 2}},
        spellbook_json={},
        equipment_json={},
        conditions_json=[],
    )


class TestCharacterList:
    """Tests for character list endpoint."""

    def test_list_requires_auth(self, api_client):
        """List endpoint requires authentication."""
        url = reverse("character-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_empty(self, authenticated_client):
        """List returns empty when no characters."""
        url = reverse("character-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_list_own_characters_only(self, authenticated_client, character, other_user, srd_data):
        """List only shows characters owned by current user."""
        # Create character for other user
        CharacterSheet.objects.create(
            user=other_user,
            name="Other Character",
            species="Human",
            character_class="Fighter",
            background="Soldier",
        )

        url = reverse("character-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Test Hero"

    def test_list_returns_summary_serializer(self, authenticated_client, character):
        """List returns summary data, not full character."""
        url = reverse("character-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Summary fields present
        assert "name" in response.data[0]
        assert "level" in response.data[0]
        # Full fields not present
        assert "backstory" not in response.data[0]
        assert "ability_scores_json" not in response.data[0]


class TestCharacterCreate:
    """Tests for character creation."""

    def test_create_requires_auth(self, api_client, srd_data):
        """Create requires authentication."""
        url = reverse("character-list")
        data = {
            "name": "New Character",
            "species": "Human",
            "character_class": "Fighter",
            "background": "Soldier",
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_minimal_character(self, authenticated_client, srd_data):
        """Create character with minimal required fields."""
        url = reverse("character-list")
        data = {
            "name": "Minimal Character",
            "species": "Human",
            "character_class": "Fighter",
            "background": "Soldier",
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Minimal Character"
        assert "id" in response.data

    def test_create_with_ability_scores(self, authenticated_client, srd_data):
        """Create character with ability scores."""
        url = reverse("character-list")
        data = {
            "name": "Strong Fighter",
            "species": "Human",
            "character_class": "Fighter",
            "background": "Soldier",
            "ability_scores_json": {
                "str": 16,
                "dex": 14,
                "con": 14,
                "int": 10,
                "wis": 12,
                "cha": 8,
            },
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["ability_scores_json"]["str"] == 16

    def test_create_missing_required_fields(self, authenticated_client, srd_data):
        """Create fails with missing required fields."""
        url = reverse("character-list")
        data = {"name": "Incomplete"}
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCharacterDetail:
    """Tests for character detail endpoint."""

    def test_detail_requires_auth(self, api_client, character):
        """Detail requires authentication."""
        url = reverse("character-detail", kwargs={"pk": character.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_own_character(self, authenticated_client, character):
        """Can get own character details."""
        url = reverse("character-detail", kwargs={"pk": character.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Hero"
        # Full serializer fields present
        assert "ability_scores_json" in response.data
        assert "proficiency_bonus" in response.data

    def test_cannot_get_other_users_character(
        self, authenticated_client, other_user, srd_data
    ):
        """Cannot get another user's character."""
        other_char = CharacterSheet.objects.create(
            user=other_user,
            name="Private Character",
            species="Human",
            character_class="Fighter",
            background="Soldier",
        )
        url = reverse("character-detail", kwargs={"pk": other_char.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCharacterUpdate:
    """Tests for character update."""

    def test_update_character(self, authenticated_client, character):
        """Can update own character."""
        url = reverse("character-detail", kwargs={"pk": character.id})
        data = {"name": "Updated Hero", "level": 6}
        response = authenticated_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Hero"
        assert response.data["level"] == 6

    def test_update_invalid_level(self, authenticated_client, character):
        """Cannot update to invalid level."""
        url = reverse("character-detail", kwargs={"pk": character.id})
        data = {"level": 25}
        response = authenticated_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_update_other_users_character(
        self, authenticated_client, other_user, srd_data
    ):
        """Cannot update another user's character."""
        other_char = CharacterSheet.objects.create(
            user=other_user,
            name="Private Character",
            species="Human",
            character_class="Fighter",
            background="Soldier",
        )
        url = reverse("character-detail", kwargs={"pk": other_char.id})
        response = authenticated_client.patch(url, {"name": "Hacked"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCharacterDelete:
    """Tests for character deletion."""

    def test_delete_character(self, authenticated_client, character, user):
        """Can delete own character."""
        char_id = character.id
        url = reverse("character-detail", kwargs={"pk": char_id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CharacterSheet.objects.filter(id=char_id).exists()

    def test_cannot_delete_other_users_character(
        self, authenticated_client, other_user, srd_data
    ):
        """Cannot delete another user's character."""
        other_char = CharacterSheet.objects.create(
            user=other_user,
            name="Private Character",
            species="Human",
            character_class="Fighter",
            background="Soldier",
        )
        url = reverse("character-detail", kwargs={"pk": other_char.id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert CharacterSheet.objects.filter(id=other_char.id).exists()


class TestCharacterValidation:
    """Tests for validation endpoint."""

    def test_validate_valid_character(self, authenticated_client, character):
        """Validation passes for valid character."""
        url = reverse("character-validate", kwargs={"pk": character.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_valid"] is True

    def test_validate_returns_errors(self, authenticated_client, user, srd_data):
        """Validation returns errors for invalid character."""
        char = CharacterSheet.objects.create(
            user=user,
            name="Invalid Character",
            species="InvalidSpecies",
            character_class="InvalidClass",
            background="InvalidBackground",
            ability_scores_json={
                "str": 10,
                "dex": 10,
                "con": 10,
                "int": 10,
                "wis": 10,
                "cha": 10,
            },
        )
        url = reverse("character-validate", kwargs={"pk": char.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.data["is_valid"] is False
        assert len(response.data["errors"]) > 0


class TestCharacterHP:
    """Tests for HP management endpoint."""

    def test_apply_damage(self, authenticated_client, character):
        """Can apply damage to character."""
        url = reverse("character-hp", kwargs={"pk": character.id})
        response = authenticated_client.post(url, {"damage": 10}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["hit_points_current"] == 34  # 44 - 10

    def test_damage_absorbed_by_temp_hp(self, authenticated_client, character):
        """Temp HP absorbs damage first."""
        character.hit_points_temp = 5
        character.save()

        url = reverse("character-hp", kwargs={"pk": character.id})
        response = authenticated_client.post(url, {"damage": 8}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["hit_points_temp"] == 0  # 5 absorbed
        assert response.data["hit_points_current"] == 41  # 44 - 3 remaining damage

    def test_apply_healing(self, authenticated_client, character):
        """Can apply healing to character."""
        character.hit_points_current = 20
        character.save()

        url = reverse("character-hp", kwargs={"pk": character.id})
        response = authenticated_client.post(url, {"healing": 15}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["hit_points_current"] == 35  # 20 + 15

    def test_healing_cannot_exceed_max(self, authenticated_client, character):
        """Healing cannot exceed max HP."""
        character.hit_points_current = 40
        character.save()

        url = reverse("character-hp", kwargs={"pk": character.id})
        response = authenticated_client.post(url, {"healing": 100}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["hit_points_current"] == 44  # Capped at max

    def test_set_hp_directly(self, authenticated_client, character):
        """Can set HP directly."""
        url = reverse("character-hp", kwargs={"pk": character.id})
        response = authenticated_client.post(
            url, {"hit_points_current": 25}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["hit_points_current"] == 25


class TestCharacterConditions:
    """Tests for condition management endpoint."""

    def test_add_condition(self, authenticated_client, character):
        """Can add a condition."""
        url = reverse("character-condition", kwargs={"pk": character.id})
        response = authenticated_client.post(
            url, {"condition": "poisoned", "action": "add"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "poisoned" in response.data["conditions_json"]

    def test_remove_condition(self, authenticated_client, character):
        """Can remove a condition."""
        character.conditions_json = ["poisoned", "frightened"]
        character.save()

        url = reverse("character-condition", kwargs={"pk": character.id})
        response = authenticated_client.post(
            url, {"condition": "poisoned", "action": "remove"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "poisoned" not in response.data["conditions_json"]
        assert "frightened" in response.data["conditions_json"]

    def test_add_duplicate_condition_ignored(self, authenticated_client, character):
        """Adding duplicate condition is ignored."""
        character.conditions_json = ["poisoned"]
        character.save()

        url = reverse("character-condition", kwargs={"pk": character.id})
        response = authenticated_client.post(
            url, {"condition": "poisoned", "action": "add"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["conditions_json"].count("poisoned") == 1


class TestCharacterRest:
    """Tests for rest endpoint."""

    def test_long_rest_restores_hp(self, authenticated_client, character):
        """Long rest restores all HP."""
        character.hit_points_current = 20
        character.save()

        url = reverse("character-rest", kwargs={"pk": character.id})
        response = authenticated_client.post(url, {"rest_type": "long"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["hit_points_current"] == 44  # Fully restored

    def test_long_rest_recovers_hit_dice(self, authenticated_client, character):
        """Long rest recovers half of max hit dice."""
        url = reverse("character-rest", kwargs={"pk": character.id})
        response = authenticated_client.post(url, {"rest_type": "long"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        # Had 5 max, 2 spent. Recover 2 (half of 5). Now 0 spent.
        assert response.data["hit_dice_json"]["d10"]["spent"] == 0

    def test_long_rest_resets_spell_slots(self, authenticated_client, character):
        """Long rest resets spell slots."""
        character.spellbook_json = {
            "spell_slots": {
                "1": {"max": 4, "used": 3},
                "2": {"max": 2, "used": 2},
            }
        }
        character.save()

        url = reverse("character-rest", kwargs={"pk": character.id})
        response = authenticated_client.post(url, {"rest_type": "long"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["spellbook_json"]["spell_slots"]["1"]["used"] == 0
        assert response.data["spellbook_json"]["spell_slots"]["2"]["used"] == 0

    def test_long_rest_clears_death_saves(self, authenticated_client, character):
        """Long rest clears death saves."""
        character.death_saves_json = {"successes": 2, "failures": 1}
        character.save()

        url = reverse("character-rest", kwargs={"pk": character.id})
        response = authenticated_client.post(url, {"rest_type": "long"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["death_saves_json"]["successes"] == 0
        assert response.data["death_saves_json"]["failures"] == 0
