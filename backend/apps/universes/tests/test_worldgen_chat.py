"""
Tests for Worldgen Chat Service and API endpoints.
"""

import json
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.universes.models import WorldgenSession, Universe
from apps.universes.schemas import StepName, check_step_completion, validate_step_data


User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email="test@example.com",
        username="testuser",
        password="testpass123",
    )


@pytest.fixture
def api_client(user):
    """Create an authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def worldgen_session(user):
    """Create a test worldgen session."""
    return WorldgenSession.objects.create(
        user=user,
        mode="ai_collab",
        draft_data_json={
            "basics": {"name": "Test Universe"},
            "tone": {"darkness": 50, "humor": 50, "realism": 50, "magic_level": 50},
            "rules": {"permadeath": False, "critical_fumbles": False, "encumbrance": False},
        },
        step_status_json={
            "basics": {"complete": True, "fields": {"name": True, "description": False}},
            "tone": {"complete": True, "fields": {"darkness": True, "humor": True, "realism": True, "magic_level": True}},
            "rules": {"complete": True, "fields": {"permadeath": True, "critical_fumbles": True, "encumbrance": True}},
            "calendar": {"complete": False, "fields": {}},
            "lore": {"complete": False, "fields": {}},
            "homebrew": {"complete": False, "fields": {}},
        },
        conversation_json=[],
    )


# ==================== Model Tests ====================


class TestWorldgenSessionModel:
    """Tests for WorldgenSession model."""

    def test_create_session(self, user):
        """Test creating a worldgen session."""
        session = WorldgenSession.objects.create(
            user=user,
            mode="ai_collab",
        )
        assert session.id is not None
        assert session.status == "draft"
        assert session.mode == "ai_collab"
        assert session.draft_data_json == {}
        assert session.conversation_json == []

    def test_session_str(self, user):
        """Test string representation."""
        session = WorldgenSession.objects.create(
            user=user,
            draft_data_json={"basics": {"name": "My World"}},
        )
        assert "My World" in str(session)

    def test_add_message(self, user):
        """Test adding messages to conversation."""
        session = WorldgenSession.objects.create(user=user)
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there!")
        session.save()

        session.refresh_from_db()
        assert len(session.conversation_json) == 2
        assert session.conversation_json[0]["role"] == "user"
        assert session.conversation_json[0]["content"] == "Hello"
        assert session.conversation_json[1]["role"] == "assistant"

    def test_set_step_status(self, user):
        """Test setting step status."""
        session = WorldgenSession.objects.create(user=user)
        session.set_step_status("basics", True, {"name": True, "description": False})
        session.save()

        session.refresh_from_db()
        assert session.step_status_json["basics"]["complete"] is True
        assert session.step_status_json["basics"]["fields"]["name"] is True

    def test_all_steps_complete(self, worldgen_session):
        """Test all_steps_complete property."""
        assert worldgen_session.all_steps_complete is True

        # Remove completion from a required step
        worldgen_session.step_status_json["basics"]["complete"] = False
        assert worldgen_session.all_steps_complete is False


# ==================== Schema Tests ====================


class TestStepSchemas:
    """Tests for step schemas and validation."""

    def test_validate_basics_step(self):
        """Test validation for basics step."""
        valid_data = {"name": "Test Universe", "description": "A test universe"}
        is_valid, errors = validate_step_data(StepName.BASICS, valid_data)
        assert is_valid is True
        assert errors == []

    def test_validate_basics_missing_required(self):
        """Test validation fails when name is missing."""
        invalid_data = {"description": "A test universe"}
        is_valid, errors = validate_step_data(StepName.BASICS, invalid_data)
        assert is_valid is False
        assert any("name" in err for err in errors)

    def test_validate_tone_step(self):
        """Test validation for tone step."""
        valid_data = {
            "darkness": 50,
            "humor": 50,
            "realism": 50,
            "magic_level": 50,
            "themes": ["exploration", "mystery"],
        }
        is_valid, errors = validate_step_data(StepName.TONE, valid_data)
        assert is_valid is True

    def test_validate_tone_out_of_range(self):
        """Test tone validation fails for out-of-range values."""
        invalid_data = {"darkness": 150, "humor": 50, "realism": 50, "magic_level": 50}
        is_valid, errors = validate_step_data(StepName.TONE, invalid_data)
        assert is_valid is False
        assert any("darkness" in err for err in errors)

    def test_check_step_completion_basics(self):
        """Test step completion check for basics."""
        complete_data = {"name": "Test", "description": "Desc"}
        is_complete, fields = check_step_completion(StepName.BASICS, complete_data)
        assert is_complete is True
        assert fields["name"] is True

        incomplete_data = {"description": "Desc"}
        is_complete, fields = check_step_completion(StepName.BASICS, incomplete_data)
        assert is_complete is False
        assert fields["name"] is False


# ==================== API Tests ====================


@pytest.mark.django_db
class TestWorldgenSessionAPI:
    """Tests for worldgen session API endpoints."""

    def test_list_sessions_empty(self, api_client):
        """Test listing sessions when none exist."""
        url = reverse("worldgen_session_list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_list_sessions(self, api_client, worldgen_session):
        """Test listing sessions."""
        url = reverse("worldgen_session_list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(worldgen_session.id)

    def test_create_session_manual(self, api_client):
        """Test creating a manual session."""
        url = reverse("worldgen_session_list")
        response = api_client.post(url, {"mode": "manual"})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["mode"] == "manual"
        assert response.data["status"] == "draft"

    def test_create_session_ai_no_llm_config(self, api_client):
        """Test creating an AI session without LLM config fails."""
        url = reverse("worldgen_session_list")
        response = api_client.post(url, {"mode": "ai_collab"})
        # Should fail because no LLM endpoint is configured
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "LLM" in response.data.get("error", "")

    def test_get_session(self, api_client, worldgen_session):
        """Test getting session details."""
        url = reverse("worldgen_session_detail", kwargs={"session_id": worldgen_session.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(worldgen_session.id)
        assert response.data["draft_data_json"]["basics"]["name"] == "Test Universe"

    def test_get_session_not_found(self, api_client):
        """Test getting non-existent session."""
        url = reverse("worldgen_session_detail", kwargs={"session_id": "00000000-0000-0000-0000-000000000000"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_session(self, api_client, worldgen_session):
        """Test abandoning a session."""
        url = reverse("worldgen_session_detail", kwargs={"session_id": worldgen_session.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Check session is now abandoned
        worldgen_session.refresh_from_db()
        assert worldgen_session.status == "abandoned"

    def test_update_step_data(self, api_client, worldgen_session):
        """Test updating step data directly."""
        url = reverse("worldgen_session_update", kwargs={"session_id": worldgen_session.id})
        response = api_client.patch(url, {
            "step": "basics",
            "data": {"description": "Updated description"},
        }, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["draft_data_json"]["basics"]["description"] == "Updated description"

    def test_switch_mode(self, api_client, worldgen_session):
        """Test switching session mode."""
        url = reverse("worldgen_session_mode", kwargs={"session_id": worldgen_session.id})
        response = api_client.post(url, {"mode": "manual"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["mode"] == "manual"

    def test_finalize_session(self, api_client, worldgen_session):
        """Test finalizing a session to create universe."""
        url = reverse("worldgen_session_finalize", kwargs={"session_id": worldgen_session.id})
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Test Universe"

        # Check universe was created
        assert Universe.objects.filter(name="Test Universe").exists()

        # Check session is completed
        worldgen_session.refresh_from_db()
        assert worldgen_session.status == "completed"

    def test_finalize_incomplete_session(self, api_client, user):
        """Test finalizing an incomplete session fails."""
        incomplete_session = WorldgenSession.objects.create(
            user=user,
            draft_data_json={"basics": {}},  # Missing required name
            step_status_json={"basics": {"complete": False, "fields": {}}},
        )
        url = reverse("worldgen_session_finalize", kwargs={"session_id": incomplete_session.id})
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_llm_status(self, api_client):
        """Test checking LLM status."""
        url = reverse("worldgen_llm_status")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "configured" in response.data


# ==================== Authentication Tests ====================


@pytest.mark.django_db
class TestWorldgenAuthRequired:
    """Tests for authentication requirements."""

    def test_list_sessions_unauthenticated(self):
        """Test listing sessions without auth fails."""
        client = APIClient()
        url = reverse("worldgen_session_list")
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_session_unauthenticated(self):
        """Test creating session without auth fails."""
        client = APIClient()
        url = reverse("worldgen_session_list")
        response = client.post(url, {"mode": "manual"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
