"""
Tests for export functionality.

Tests Epic 11 - Export job model, universe export, and campaign export.
"""

import json
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.campaigns.models import Campaign, TurnEvent
from apps.characters.models import CharacterSheet
from apps.exports.models import ExportJob
from apps.exports.services.export_service import (
    CampaignExporter,
    ExportService,
    UniverseExporter,
)
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
        description="A universe for testing exports",
        tone_profile_json={
            "grimdark_cozy": 0.5,
            "comedy_serious": 0.7,
            "low_high_magic": 0.8,
        },
        rules_profile_json={"strictness": "standard"},
        current_universe_time={"year": 1000, "month": 1, "day": 1},
    )


@pytest.fixture
def character(db, user):
    """Create a test character."""
    return CharacterSheet.objects.create(
        user=user,
        name="Test Hero",
        species="Human",
        character_class="Fighter",
        background="Soldier",
        level=5,
        ability_scores_json={
            "str": 16, "dex": 14, "con": 14,
            "int": 10, "wis": 12, "cha": 8
        },
    )


@pytest.fixture
def campaign(db, user, universe, character):
    """Create a test campaign."""
    return Campaign.objects.create(
        user=user,
        universe=universe,
        character_sheet=character,
        title="Test Adventure",
        mode="campaign",
        status="active",
        content_rating="PG13",
        start_universe_time={"year": 1000, "month": 1, "day": 1},
    )


@pytest.fixture
def campaign_with_turns(db, campaign):
    """Create a campaign with turns."""
    for i in range(1, 4):
        TurnEvent.objects.create(
            campaign=campaign,
            turn_index=i,
            user_input_text=f"Player does action {i}",
            llm_response_text=f"DM describes outcome {i}",
            roll_spec_json={},
            roll_results_json=[{"description": f"Roll {i}", "total": 10 + i}],
            state_patch_json={},
            canonical_state_hash=f"hash_{i}",
            universe_time_after_turn={"year": 1000, "month": 1, "day": i},
        )
    return campaign


# =============================================================================
# ExportJob Model Tests
# =============================================================================


class TestExportJobModel:
    """Tests for ExportJob model."""

    def test_create_export_job(self, db, user, universe):
        """Test creating an export job."""
        job = ExportJob.objects.create(
            user=user,
            export_type="universe",
            target_id=universe.id,
            format="json",
            status="pending",
        )

        assert job.id is not None
        assert job.export_type == "universe"
        assert job.format == "json"
        assert job.status == "pending"

    def test_export_job_str(self, db, user, universe):
        """Test export job string representation."""
        job = ExportJob.objects.create(
            user=user,
            export_type="campaign",
            target_id=universe.id,
            format="md",
            status="completed",
        )

        assert "campaign" in str(job)
        assert "md" in str(job)
        assert "completed" in str(job)


# =============================================================================
# UniverseExporter Tests
# =============================================================================


class TestUniverseExporter:
    """Tests for UniverseExporter."""

    def test_export_universe_to_json(self, db, universe):
        """Test exporting universe to JSON."""
        exporter = UniverseExporter(universe)
        result = exporter.to_json()

        assert result.success
        assert result.content_type == "application/json"
        assert result.filename.endswith(".json")

        # Parse and verify content
        data = json.loads(result.content)
        assert data["export_metadata"]["export_type"] == "universe"
        assert data["universe"]["name"] == "Test Universe"
        assert "srd_attribution" in data["export_metadata"]

    def test_export_universe_to_markdown(self, db, universe):
        """Test exporting universe to Markdown."""
        exporter = UniverseExporter(universe)
        result = exporter.to_markdown()

        assert result.success
        assert result.content_type == "text/markdown"
        assert result.filename.endswith(".md")

        # Verify markdown content
        assert "# Test Universe" in result.content
        assert "A universe for testing exports" in result.content
        assert "SRD 5.2" in result.content  # Attribution

    def test_export_universe_includes_tone_profile(self, db, universe):
        """Test that tone profile is included in export."""
        exporter = UniverseExporter(universe)
        result = exporter.to_json()

        data = json.loads(result.content)
        assert data["universe"]["tone_profile"]["grimdark_cozy"] == 0.5


# =============================================================================
# CampaignExporter Tests
# =============================================================================


class TestCampaignExporter:
    """Tests for CampaignExporter."""

    def test_export_campaign_to_json(self, db, campaign_with_turns):
        """Test exporting campaign to JSON."""
        exporter = CampaignExporter(campaign_with_turns)
        result = exporter.to_json()

        assert result.success
        assert result.content_type == "application/json"

        data = json.loads(result.content)
        assert data["export_metadata"]["export_type"] == "campaign"
        assert data["campaign"]["title"] == "Test Adventure"
        assert data["character"]["name"] == "Test Hero"
        assert data["total_turns"] == 3

    def test_export_campaign_to_markdown(self, db, campaign_with_turns):
        """Test exporting campaign to Markdown."""
        exporter = CampaignExporter(campaign_with_turns)
        result = exporter.to_markdown()

        assert result.success
        assert result.content_type == "text/markdown"

        # Verify markdown content
        assert "# Test Adventure" in result.content
        assert "Test Hero" in result.content
        assert "Player does action 1" in result.content
        assert "Turn 1" in result.content

    def test_export_campaign_includes_turns(self, db, campaign_with_turns):
        """Test that all turns are included in export."""
        exporter = CampaignExporter(campaign_with_turns)
        result = exporter.to_json()

        data = json.loads(result.content)
        assert len(data["turns"]) == 3
        assert data["turns"][0]["turn_index"] == 1
        assert data["turns"][2]["turn_index"] == 3


# =============================================================================
# ExportService Tests
# =============================================================================


class TestExportService:
    """Tests for ExportService."""

    def test_create_universe_export_job(self, db, universe):
        """Test creating universe export job."""
        service = ExportService()
        job = service.create_universe_export_job(universe, "json")

        assert job.export_type == "universe"
        assert job.target_id == universe.id
        assert job.format == "json"
        assert job.status == "pending"

    def test_create_campaign_export_job(self, db, campaign):
        """Test creating campaign export job."""
        service = ExportService()
        job = service.create_campaign_export_job(campaign, "md")

        assert job.export_type == "campaign"
        assert job.target_id == campaign.id
        assert job.format == "md"
        assert job.status == "pending"

    def test_execute_universe_export(self, db, universe):
        """Test executing universe export job."""
        service = ExportService()
        job = service.create_universe_export_job(universe, "json")
        result = service.execute_export(job)

        assert result.success
        job.refresh_from_db()
        assert job.status == "completed"

    def test_execute_campaign_export(self, db, campaign_with_turns):
        """Test executing campaign export job."""
        service = ExportService()
        job = service.create_campaign_export_job(campaign_with_turns, "md")
        result = service.execute_export(job)

        assert result.success
        job.refresh_from_db()
        assert job.status == "completed"

    def test_export_job_failure(self, db, user):
        """Test export job failure with invalid target."""
        job = ExportJob.objects.create(
            user=user,
            export_type="universe",
            target_id=uuid.uuid4(),  # Non-existent universe
            format="json",
            status="pending",
        )

        service = ExportService()
        result = service.execute_export(job)

        assert not result.success
        job.refresh_from_db()
        assert job.status == "failed"


# =============================================================================
# API Endpoint Tests
# =============================================================================


class TestUniverseExportEndpoint:
    """Tests for universe export API endpoint."""

    def test_export_requires_auth(self, api_client, universe):
        """Test that export requires authentication."""
        response = api_client.post(
            f"/api/universes/{universe.id}/export/",
            {"format": "json"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_export_universe_json(self, api_client, user, universe):
        """Test exporting universe to JSON via API."""
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/universes/{universe.id}/export/",
            {"format": "json"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "completed"
        assert "job_id" in response.data
        assert "download_url" in response.data

    def test_export_universe_markdown(self, api_client, user, universe):
        """Test exporting universe to Markdown via API."""
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/universes/{universe.id}/export/",
            {"format": "md"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_export_other_users_universe(self, api_client, other_user, universe):
        """Test that users cannot export others' universes."""
        api_client.force_authenticate(user=other_user)
        response = api_client.post(
            f"/api/universes/{universe.id}/export/",
            {"format": "json"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCampaignExportEndpoint:
    """Tests for campaign export API endpoint."""

    def test_export_requires_auth(self, api_client, campaign):
        """Test that export requires authentication."""
        response = api_client.post(
            f"/api/campaigns/{campaign.id}/export/",
            {"format": "json"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_export_campaign_json(self, api_client, user, campaign_with_turns):
        """Test exporting campaign to JSON via API."""
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/campaigns/{campaign_with_turns.id}/export/",
            {"format": "json"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "completed"

    def test_export_campaign_markdown(self, api_client, user, campaign_with_turns):
        """Test exporting campaign to Markdown via API."""
        api_client.force_authenticate(user=user)
        response = api_client.post(
            f"/api/campaigns/{campaign_with_turns.id}/export/",
            {"format": "md"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED


class TestExportJobEndpoints:
    """Tests for export job management endpoints."""

    def test_list_export_jobs(self, api_client, user, universe):
        """Test listing user's export jobs."""
        # Create some jobs
        service = ExportService()
        service.create_universe_export_job(universe, "json")
        service.create_universe_export_job(universe, "md")

        api_client.force_authenticate(user=user)
        response = api_client.get("/api/exports/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_get_export_job_status(self, api_client, user, universe):
        """Test getting export job status."""
        service = ExportService()
        job = service.create_universe_export_job(universe, "json")

        api_client.force_authenticate(user=user)
        response = api_client.get(f"/api/exports/{job.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(job.id)

    def test_delete_export_job(self, api_client, user, universe):
        """Test deleting an export job."""
        service = ExportService()
        job = service.create_universe_export_job(universe, "json")

        api_client.force_authenticate(user=user)
        response = api_client.delete(f"/api/exports/{job.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert not ExportJob.objects.filter(id=job.id).exists()

    def test_cannot_access_other_users_jobs(self, api_client, other_user, user, universe):
        """Test that users cannot access others' export jobs."""
        service = ExportService()
        job = service.create_universe_export_job(universe, "json")

        api_client.force_authenticate(user=other_user)
        response = api_client.get(f"/api/exports/{job.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# SRD Attribution Tests
# =============================================================================


class TestSRDAttribution:
    """Tests for SRD attribution in exports."""

    def test_universe_json_includes_attribution(self, db, universe):
        """Test that universe JSON export includes SRD attribution."""
        exporter = UniverseExporter(universe)
        result = exporter.to_json()

        data = json.loads(result.content)
        assert "SRD 5.2" in data["export_metadata"]["srd_attribution"]
        assert "Creative Commons" in data["export_metadata"]["srd_attribution"]

    def test_universe_markdown_includes_attribution(self, db, universe):
        """Test that universe Markdown export includes SRD attribution."""
        exporter = UniverseExporter(universe)
        result = exporter.to_markdown()

        assert "SRD 5.2" in result.content
        assert "Creative Commons" in result.content

    def test_campaign_json_includes_attribution(self, db, campaign):
        """Test that campaign JSON export includes SRD attribution."""
        exporter = CampaignExporter(campaign)
        result = exporter.to_json()

        data = json.loads(result.content)
        assert "SRD 5.2" in data["export_metadata"]["srd_attribution"]
