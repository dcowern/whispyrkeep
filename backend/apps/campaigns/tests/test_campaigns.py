"""
Tests for campaign models and API.

Tests Campaign, TurnEvent, and CanonicalCampaignState.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.campaigns.models import Campaign, CanonicalCampaignState, TurnEvent
from apps.campaigns.services.state_service import CampaignState, StateService
from apps.characters.models import CharacterSheet
from apps.universes.models import Universe

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create test user."""
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
        tone_profile_json={"grimdark_cozy": 0.5},
        rules_profile_json={"failure_style": "fail_forward"},
    )


@pytest.fixture
def character(user, universe):
    """Create test character."""
    return CharacterSheet.objects.create(
        user=user,
        universe=universe,
        name="Test Hero",
        species="Human",
        character_class="Fighter",
        background="Soldier",
        level=5,
        ability_scores_json={
            "str": 16,
            "dex": 14,
            "con": 14,
            "int": 10,
            "wis": 12,
            "cha": 8,
        },
    )


@pytest.fixture
def campaign(user, universe, character):
    """Create test campaign."""
    return Campaign.objects.create(
        user=user,
        universe=universe,
        character_sheet=character,
        title="Test Campaign",
        mode="scenario",
        target_length="medium",
        failure_style="fail_forward",
        content_rating="PG13",
    )


@pytest.mark.django_db
class TestCampaignModel:
    """Tests for Campaign model."""

    def test_create_campaign(self, user, universe, character):
        """Test creating a campaign."""
        campaign = Campaign.objects.create(
            user=user,
            universe=universe,
            character_sheet=character,
            title="New Campaign",
        )

        assert campaign.id is not None
        assert campaign.title == "New Campaign"
        assert campaign.status == "active"
        assert campaign.mode == "scenario"

    def test_campaign_str(self, campaign):
        """Test campaign string representation."""
        assert str(campaign) == "Test Campaign (active)"

    def test_campaign_choices(self, campaign):
        """Test campaign choice values."""
        campaign.mode = "campaign"
        campaign.target_length = "long"
        campaign.failure_style = "strict_raw"
        campaign.content_rating = "R"
        campaign.status = "paused"
        campaign.save()

        campaign.refresh_from_db()
        assert campaign.mode == "campaign"
        assert campaign.target_length == "long"
        assert campaign.failure_style == "strict_raw"
        assert campaign.content_rating == "R"
        assert campaign.status == "paused"


@pytest.mark.django_db
class TestTurnEventModel:
    """Tests for TurnEvent model."""

    def test_create_turn_event(self, campaign):
        """Test creating a turn event."""
        turn = TurnEvent.objects.create(
            campaign=campaign,
            turn_index=1,
            user_input_text="I search the room",
            llm_response_text="You find a hidden door...",
            canonical_state_hash="abc123",
        )

        assert turn.id is not None
        assert turn.turn_index == 1

    def test_turn_event_ordering(self, campaign):
        """Test turn events are ordered by index."""
        TurnEvent.objects.create(
            campaign=campaign,
            turn_index=2,
            user_input_text="Input 2",
            llm_response_text="Response 2",
            canonical_state_hash="hash2",
        )
        TurnEvent.objects.create(
            campaign=campaign,
            turn_index=1,
            user_input_text="Input 1",
            llm_response_text="Response 1",
            canonical_state_hash="hash1",
        )

        turns = list(TurnEvent.objects.filter(campaign=campaign))
        assert turns[0].turn_index == 1
        assert turns[1].turn_index == 2

    def test_turn_event_unique_together(self, campaign):
        """Test turn index is unique per campaign."""
        TurnEvent.objects.create(
            campaign=campaign,
            turn_index=1,
            user_input_text="Input",
            llm_response_text="Response",
            canonical_state_hash="hash",
        )

        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            TurnEvent.objects.create(
                campaign=campaign,
                turn_index=1,
                user_input_text="Another input",
                llm_response_text="Another response",
                canonical_state_hash="hash2",
            )


@pytest.mark.django_db
class TestCampaignListAPI:
    """Tests for campaign list API."""

    def test_list_campaigns_unauthenticated(self, api_client):
        """Test list requires authentication."""
        response = api_client.get("/api/campaigns/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_campaigns_empty(self, authenticated_client):
        """Test list returns empty for new user."""
        response = authenticated_client.get("/api/campaigns/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_list_campaigns(self, authenticated_client, campaign):
        """Test list returns user's campaigns."""
        response = authenticated_client.get("/api/campaigns/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["title"] == "Test Campaign"

    def test_list_excludes_other_users(
        self, authenticated_client, campaign, other_user, universe, character
    ):
        """Test list excludes other users' campaigns."""
        # Create character for other user
        other_character = CharacterSheet.objects.create(
            user=other_user,
            name="Other Hero",
            species="Elf",
            character_class="Wizard",
            background="Sage",
        )

        # Create other user's campaign
        Campaign.objects.create(
            user=other_user,
            universe=universe,
            character_sheet=other_character,
            title="Other Campaign",
        )

        response = authenticated_client.get("/api/campaigns/")
        assert len(response.data) == 1
        assert response.data[0]["title"] == "Test Campaign"


@pytest.mark.django_db
class TestCampaignCreateAPI:
    """Tests for campaign creation API."""

    def test_create_campaign(self, authenticated_client, universe, character):
        """Test creating a campaign."""
        data = {
            "title": "New Adventure",
            "universe": str(universe.id),
            "character_sheet": str(character.id),
            "mode": "scenario",
            "target_length": "short",
            "failure_style": "fail_forward",
            "content_rating": "PG",
        }

        response = authenticated_client.post("/api/campaigns/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Adventure"

    def test_create_campaign_creates_initial_state(
        self, authenticated_client, universe, character
    ):
        """Test creating campaign creates initial state snapshot."""
        data = {
            "title": "Stateful Campaign",
            "universe": str(universe.id),
            "character_sheet": str(character.id),
        }

        response = authenticated_client.post("/api/campaigns/", data, format="json")
        campaign_id = response.data["id"]

        # Check snapshot was created
        assert CanonicalCampaignState.objects.filter(
            campaign_id=campaign_id, turn_index=0
        ).exists()

    def test_create_campaign_invalid_universe(
        self, authenticated_client, character, other_user
    ):
        """Test cannot create campaign with universe user doesn't own."""
        other_universe = Universe.objects.create(
            user=other_user,
            name="Other Universe",
        )

        data = {
            "title": "Invalid Campaign",
            "universe": str(other_universe.id),
            "character_sheet": str(character.id),
        }

        response = authenticated_client.post("/api/campaigns/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCampaignDetailAPI:
    """Tests for campaign detail API."""

    def test_get_campaign(self, authenticated_client, campaign):
        """Test getting campaign details."""
        response = authenticated_client.get(f"/api/campaigns/{campaign.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Test Campaign"

    def test_get_campaign_not_found(self, authenticated_client):
        """Test 404 for nonexistent campaign."""
        import uuid

        response = authenticated_client.get(f"/api/campaigns/{uuid.uuid4()}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_campaign(self, authenticated_client, campaign):
        """Test updating campaign."""
        data = {"title": "Updated Title", "status": "paused"}
        response = authenticated_client.put(
            f"/api/campaigns/{campaign.id}/", data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated Title"
        assert response.data["status"] == "paused"

    def test_delete_campaign(self, authenticated_client, campaign):
        """Test deleting campaign."""
        campaign_id = campaign.id
        response = authenticated_client.delete(f"/api/campaigns/{campaign_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert not Campaign.objects.filter(id=campaign_id).exists()


@pytest.mark.django_db
class TestCampaignStateAPI:
    """Tests for campaign state API."""

    def test_get_state(self, authenticated_client, campaign):
        """Test getting campaign state."""
        # Create initial state
        state_service = StateService()
        initial_state = state_service.get_initial_state(campaign)
        state_service.save_snapshot(campaign, initial_state, force=True)

        response = authenticated_client.get(f"/api/campaigns/{campaign.id}/state/")
        assert response.status_code == status.HTTP_200_OK
        assert "state" in response.data
        assert "character_state" in response.data

    def test_get_state_not_found(self, authenticated_client):
        """Test 404 for nonexistent campaign state."""
        import uuid

        response = authenticated_client.get(f"/api/campaigns/{uuid.uuid4()}/state/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestStateService:
    """Tests for StateService."""

    @pytest.fixture
    def state_service(self):
        """Create state service."""
        return StateService()

    def test_get_initial_state(self, state_service, campaign):
        """Test getting initial state."""
        state = state_service.get_initial_state(campaign)

        assert state.campaign_id == str(campaign.id)
        assert state.turn_index == 0
        assert state.character_state["name"] == "Test Hero"
        assert state.character_state["level"] == 5

    def test_state_to_dict(self, state_service, campaign):
        """Test state serialization."""
        state = state_service.get_initial_state(campaign)
        data = state.to_dict()

        assert "character_state" in data
        assert "world_state" in data
        assert "universe_time" in data

    def test_state_from_dict(self, state_service, campaign):
        """Test state deserialization."""
        state = state_service.get_initial_state(campaign)
        data = state.to_dict()

        restored = CampaignState.from_dict(data)
        assert restored.campaign_id == state.campaign_id
        assert restored.character_state == state.character_state

    def test_save_snapshot(self, state_service, campaign):
        """Test saving state snapshot."""
        state = state_service.get_initial_state(campaign)
        snapshot = state_service.save_snapshot(campaign, state, force=True)

        assert snapshot is not None
        assert snapshot.turn_index == 0

    def test_replay_empty_campaign(self, state_service, campaign):
        """Test replaying campaign with no turns."""
        result = state_service.replay_to_turn(campaign)

        assert result.success is True
        assert result.turn_index == 0
        assert result.turns_replayed == 0

    def test_state_hash(self, state_service, campaign):
        """Test state hash computation."""
        state = state_service.get_initial_state(campaign)
        hash1 = state.compute_hash()
        hash2 = state.compute_hash()

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex
