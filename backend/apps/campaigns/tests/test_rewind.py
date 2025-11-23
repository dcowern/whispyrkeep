"""
Tests for campaign rewind functionality.

Tests Epic 10.0.1 - Rewind endpoint and Epic 10.0.2 - Lore invalidation.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.campaigns.models import Campaign, CanonicalCampaignState, TurnEvent
from apps.campaigns.services.rewind_service import RewindService
from apps.characters.models import CharacterSheet
from apps.lore.models import LoreChunk
from apps.universes.models import Universe

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        display_name="Test User",
    )


@pytest.fixture
def other_user(db):
    """Create another test user."""
    return User.objects.create_user(
        username="otheruser",
        email="other@example.com",
        password="testpass123",
        display_name="Other User",
    )


@pytest.fixture
def universe(db, user):
    """Create a test universe."""
    return Universe.objects.create(
        user=user,
        name="Test Universe",
        description="A test universe",
        current_universe_time={"year": 1000, "month": 1, "day": 1},
    )


@pytest.fixture
def character(db, user):
    """Create a test character."""
    return CharacterSheet.objects.create(
        user=user,
        name="Test Character",
        species="Human",
        character_class="Fighter",
        background="Soldier",
        level=1,
        ability_scores_json={"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 8},
    )


@pytest.fixture
def campaign(db, user, universe, character):
    """Create a test campaign."""
    return Campaign.objects.create(
        user=user,
        universe=universe,
        character_sheet=character,
        title="Test Campaign",
        mode="campaign",
        status="active",
        start_universe_time={"year": 1000, "month": 1, "day": 1},
    )


@pytest.fixture
def campaign_with_turns(db, campaign):
    """Create a campaign with multiple turns."""
    turns = []
    for i in range(1, 6):  # Create 5 turns
        turn = TurnEvent.objects.create(
            campaign=campaign,
            turn_index=i,
            user_input_text=f"Player action {i}",
            llm_response_text=f"DM response {i}",
            roll_spec_json={},
            roll_results_json={},
            state_patch_json={"test": f"patch_{i}"},
            canonical_state_hash=f"hash_{i}",
            lore_deltas_json=[{"type": "soft_lore", "text": f"Lore from turn {i}"}],
            universe_time_after_turn={"year": 1000, "month": 1, "day": i},
        )
        turns.append(turn)

    # Create some state snapshots
    CanonicalCampaignState.objects.create(
        campaign=campaign,
        turn_index=0,
        state_json={"initial": True},
    )
    CanonicalCampaignState.objects.create(
        campaign=campaign,
        turn_index=3,
        state_json={"turn": 3},
    )

    return campaign, turns


@pytest.fixture
def campaign_with_lore(db, campaign_with_turns):
    """Create campaign with associated lore chunks."""
    campaign, turns = campaign_with_turns

    # Create lore chunks for each turn
    for turn in turns:
        LoreChunk.objects.create(
            universe=campaign.universe,
            chunk_type="soft_lore",
            source_ref=str(turn.id),
            text=f"Lore from turn {turn.turn_index}",
            tags_json=["test"],
        )

    return campaign, turns


# =============================================================================
# RewindService Unit Tests
# =============================================================================


class TestRewindServiceValidation:
    """Tests for RewindService validation logic."""

    def test_validate_rewind_success(self, db, campaign_with_turns):
        """Test validation passes for valid rewind target."""
        campaign, turns = campaign_with_turns
        service = RewindService()

        error = service._validate_rewind(campaign, target_turn_index=3)
        assert error is None

    def test_validate_rewind_to_zero(self, db, campaign_with_turns):
        """Test validation passes for rewinding to turn 0."""
        campaign, turns = campaign_with_turns
        service = RewindService()

        error = service._validate_rewind(campaign, target_turn_index=0)
        assert error is None

    def test_validate_rewind_ended_campaign(self, db, campaign_with_turns):
        """Test validation fails for ended campaigns."""
        campaign, turns = campaign_with_turns
        campaign.status = "ended"
        campaign.save()

        service = RewindService()
        error = service._validate_rewind(campaign, target_turn_index=3)

        assert error == "Cannot rewind an ended campaign"

    def test_validate_rewind_negative_index(self, db, campaign_with_turns):
        """Test validation fails for negative turn index."""
        campaign, turns = campaign_with_turns
        service = RewindService()

        error = service._validate_rewind(campaign, target_turn_index=-1)
        assert error == "Target turn index must be non-negative"

    def test_validate_rewind_future_turn(self, db, campaign_with_turns):
        """Test validation fails for future turn index."""
        campaign, turns = campaign_with_turns
        service = RewindService()

        error = service._validate_rewind(campaign, target_turn_index=10)
        assert "greater than current turn" in error

    def test_validate_rewind_nonexistent_turn(self, db, campaign):
        """Test validation fails when target turn doesn't exist."""
        # Create only turn 1 and 3, but not 2
        TurnEvent.objects.create(
            campaign=campaign,
            turn_index=1,
            user_input_text="Action 1",
            llm_response_text="Response 1",
            canonical_state_hash="hash1",
        )
        TurnEvent.objects.create(
            campaign=campaign,
            turn_index=3,
            user_input_text="Action 3",
            llm_response_text="Response 3",
            canonical_state_hash="hash3",
        )

        service = RewindService()
        error = service._validate_rewind(campaign, target_turn_index=2)

        assert error == "Turn 2 does not exist"


class TestRewindServiceExecution:
    """Tests for RewindService rewind execution."""

    @patch("apps.campaigns.services.rewind_service.LoreService")
    def test_rewind_deletes_turns_after_target(self, mock_lore_service, db, campaign_with_turns):
        """Test that rewind deletes all turns after target."""
        campaign, turns = campaign_with_turns
        mock_lore_service.return_value.invalidate_turn_lore.return_value = 0

        service = RewindService()
        result = service.rewind_to_turn(campaign, target_turn_index=2)

        assert result.success
        assert result.turns_deleted == 3  # Turns 3, 4, 5 deleted
        assert TurnEvent.objects.filter(campaign=campaign).count() == 2
        assert TurnEvent.objects.filter(campaign=campaign, turn_index__gt=2).count() == 0

    @patch("apps.campaigns.services.rewind_service.LoreService")
    def test_rewind_deletes_snapshots_after_target(self, mock_lore_service, db, campaign_with_turns):
        """Test that rewind deletes snapshots after target."""
        campaign, turns = campaign_with_turns
        mock_lore_service.return_value.invalidate_turn_lore.return_value = 0

        service = RewindService()
        result = service.rewind_to_turn(campaign, target_turn_index=1)

        assert result.success
        assert result.snapshots_deleted == 1  # Snapshot at turn 3 deleted
        assert CanonicalCampaignState.objects.filter(campaign=campaign, turn_index__gt=1).count() == 0

    @patch("apps.campaigns.services.rewind_service.LoreService")
    def test_rewind_to_zero_deletes_all_turns(self, mock_lore_service, db, campaign_with_turns):
        """Test that rewinding to 0 deletes all turns."""
        campaign, turns = campaign_with_turns
        mock_lore_service.return_value.invalidate_turn_lore.return_value = 0

        service = RewindService()
        result = service.rewind_to_turn(campaign, target_turn_index=0)

        assert result.success
        assert result.turns_deleted == 5
        assert TurnEvent.objects.filter(campaign=campaign).count() == 0

    @patch("apps.campaigns.services.rewind_service.LoreService")
    def test_rewind_invalidates_lore(self, mock_lore_service, db, campaign_with_turns):
        """Test that rewind calls lore invalidation for deleted turns."""
        campaign, turns = campaign_with_turns
        mock_instance = mock_lore_service.return_value
        mock_instance.invalidate_turn_lore.return_value = 1

        service = RewindService()
        result = service.rewind_to_turn(campaign, target_turn_index=2)

        assert result.success
        assert mock_instance.invalidate_turn_lore.call_count == 3  # Called for turns 3, 4, 5

    @patch("apps.campaigns.services.rewind_service.LoreService")
    def test_rewind_returns_new_state(self, mock_lore_service, db, campaign_with_turns):
        """Test that rewind returns the new state after rewind."""
        campaign, turns = campaign_with_turns
        mock_lore_service.return_value.invalidate_turn_lore.return_value = 0

        service = RewindService()
        result = service.rewind_to_turn(campaign, target_turn_index=2)

        assert result.success
        assert result.new_state is not None
        assert result.new_state.turn_index == 2


class TestRewindServiceLoreIntegration:
    """Integration tests for rewind with actual lore service."""

    def test_rewind_deletes_lore_chunks(self, db, campaign_with_lore):
        """Test that rewind actually deletes lore chunks from DB."""
        campaign, turns = campaign_with_lore

        # Verify lore exists before rewind
        assert LoreChunk.objects.filter(universe=campaign.universe).count() == 5

        # Mock only ChromaDB operations
        with patch.object(RewindService, "_get_lore_service") as mock_get_lore:
            # Use real lore service but mock ChromaDB
            from apps.lore.services.lore_service import LoreService
            lore_svc = LoreService()
            lore_svc.chroma = MagicMock()
            mock_get_lore.return_value = lore_svc

            service = RewindService()
            service.lore_service = lore_svc
            result = service.rewind_to_turn(campaign, target_turn_index=2)

        assert result.success
        # Lore for turns 3, 4, 5 should be deleted
        assert LoreChunk.objects.filter(universe=campaign.universe).count() == 2


# =============================================================================
# API Endpoint Tests
# =============================================================================


class TestRewindEndpoint:
    """Tests for the rewind API endpoint."""

    def test_rewind_requires_authentication(self, api_client, campaign):
        """Test that rewind endpoint requires authentication."""
        response = api_client.post(
            f"/api/campaigns/{campaign.id}/rewind/",
            {"turn_index": 0},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("apps.campaigns.services.rewind_service.LoreService")
    def test_rewind_success(self, mock_lore_service, api_client, user, campaign_with_turns):
        """Test successful rewind via API."""
        campaign, turns = campaign_with_turns
        mock_lore_service.return_value.invalidate_turn_lore.return_value = 0

        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/campaigns/{campaign.id}/rewind/",
            {"turn_index": 2},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["target_turn_index"] == 2
        assert response.data["turns_deleted"] == 3

    def test_rewind_not_found(self, api_client, user):
        """Test rewind returns 404 for non-existent campaign."""
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/campaigns/{uuid.uuid4()}/rewind/",
            {"turn_index": 0},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_rewind_other_users_campaign(self, api_client, other_user, campaign):
        """Test that users cannot rewind other users' campaigns."""
        api_client.force_authenticate(user=other_user)
        response = api_client.post(
            f"/api/campaigns/{campaign.id}/rewind/",
            {"turn_index": 0},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_rewind_missing_turn_index(self, api_client, user, campaign):
        """Test rewind fails without turn_index."""
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/campaigns/{campaign.id}/rewind/",
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rewind_negative_turn_index(self, api_client, user, campaign):
        """Test rewind fails with negative turn_index."""
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/campaigns/{campaign.id}/rewind/",
            {"turn_index": -1},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.campaigns.services.rewind_service.LoreService")
    def test_rewind_ended_campaign_fails(self, mock_lore_service, api_client, user, campaign_with_turns):
        """Test rewind fails for ended campaigns."""
        campaign, turns = campaign_with_turns
        campaign.status = "ended"
        campaign.save()

        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/campaigns/{campaign.id}/rewind/",
            {"turn_index": 2},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "Cannot rewind an ended campaign" in response.data["errors"]


class TestRewindableturnsEndpoint:
    """Tests for the GET rewindable turns endpoint."""

    def test_get_rewindable_turns_requires_auth(self, api_client, campaign):
        """Test that getting rewindable turns requires authentication."""
        response = api_client.get(f"/api/campaigns/{campaign.id}/rewind/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_rewindable_turns_success(self, api_client, user, campaign_with_turns):
        """Test getting list of rewindable turns."""
        campaign, turns = campaign_with_turns

        api_client.force_authenticate(user=user)
        response = api_client.get(f"/api/campaigns/{campaign.id}/rewind/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["campaign_id"] == str(campaign.id)
        assert response.data["current_turn_index"] == 5
        assert len(response.data["turns"]) == 5

    def test_get_rewindable_turns_empty_campaign(self, api_client, user, campaign):
        """Test getting rewindable turns for campaign with no turns."""
        api_client.force_authenticate(user=user)
        response = api_client.get(f"/api/campaigns/{campaign.id}/rewind/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["current_turn_index"] == 0
        assert len(response.data["turns"]) == 0

    def test_get_rewindable_turns_with_limit(self, api_client, user, campaign_with_turns):
        """Test limiting rewindable turns."""
        campaign, turns = campaign_with_turns

        api_client.force_authenticate(user=user)
        response = api_client.get(f"/api/campaigns/{campaign.id}/rewind/?limit=3")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["turns"]) == 3


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestRewindEdgeCases:
    """Tests for edge cases in rewind functionality."""

    @patch("apps.campaigns.services.rewind_service.LoreService")
    def test_rewind_to_current_turn_no_op(self, mock_lore_service, db, campaign_with_turns):
        """Test rewinding to current turn is essentially a no-op."""
        campaign, turns = campaign_with_turns
        mock_lore_service.return_value.invalidate_turn_lore.return_value = 0

        service = RewindService()
        result = service.rewind_to_turn(campaign, target_turn_index=5)

        assert result.success
        assert result.turns_deleted == 0
        assert TurnEvent.objects.filter(campaign=campaign).count() == 5

    @patch("apps.campaigns.services.rewind_service.LoreService")
    def test_rewind_empty_campaign(self, mock_lore_service, db, campaign):
        """Test rewinding campaign with no turns."""
        mock_lore_service.return_value.invalidate_turn_lore.return_value = 0

        service = RewindService()
        result = service.rewind_to_turn(campaign, target_turn_index=0)

        assert result.success
        assert result.turns_deleted == 0

    @patch("apps.campaigns.services.rewind_service.LoreService")
    def test_rewind_paused_campaign(self, mock_lore_service, db, campaign_with_turns):
        """Test rewinding paused campaign succeeds."""
        campaign, turns = campaign_with_turns
        campaign.status = "paused"
        campaign.save()
        mock_lore_service.return_value.invalidate_turn_lore.return_value = 0

        service = RewindService()
        result = service.rewind_to_turn(campaign, target_turn_index=2)

        assert result.success
        assert result.turns_deleted == 3
