"""
Tests for Universe API endpoints.

Tests CRUD operations for universes and hard canon documents.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.universes.models import (
    HomebrewSpecies,
    Universe,
    UniverseHardCanonDoc,
)

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
        description="A test universe for API testing",
        tone_profile_json={"grimdark_cozy": 0.5},
        rules_profile_json={"encumbrance": "standard"},
    )


@pytest.fixture
def other_universe(other_user):
    """Create universe owned by another user."""
    return Universe.objects.create(
        user=other_user,
        name="Other Universe",
        description="Belongs to another user",
    )


@pytest.mark.django_db
class TestUniverseListEndpoint:
    """Tests for GET /api/universes/."""

    def test_list_requires_auth(self, api_client):
        """Test that list endpoint requires authentication."""
        response = api_client.get("/api/universes/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_returns_user_universes(self, authenticated_client, universe):
        """Test that list returns only user's universes."""
        response = authenticated_client.get("/api/universes/")

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        assert len(results) >= 1
        assert any(u["id"] == str(universe.id) for u in results)

    def test_list_excludes_other_users_universes(
        self, authenticated_client, universe, other_universe
    ):
        """Test that list excludes other users' universes."""
        response = authenticated_client.get("/api/universes/")

        results = response.data.get("results", response.data)
        universe_ids = [u["id"] for u in results]
        assert str(universe.id) in universe_ids
        assert str(other_universe.id) not in universe_ids

    def test_list_search_by_name(self, authenticated_client, user):
        """Test searching universes by name."""
        Universe.objects.create(user=user, name="Fantasy World")
        Universe.objects.create(user=user, name="Sci-Fi World")

        response = authenticated_client.get("/api/universes/", {"search": "Fantasy"})

        results = response.data.get("results", response.data)
        assert all("Fantasy" in u["name"] for u in results)

    def test_list_ordering(self, authenticated_client, user):
        """Test ordering universes."""
        Universe.objects.create(user=user, name="A World")
        Universe.objects.create(user=user, name="Z World")

        response = authenticated_client.get("/api/universes/", {"ordering": "name"})

        results = response.data.get("results", response.data)
        names = [u["name"] for u in results]
        assert names == sorted(names)


@pytest.mark.django_db
class TestUniverseCreateEndpoint:
    """Tests for POST /api/universes/."""

    def test_create_requires_auth(self, api_client):
        """Test that create endpoint requires authentication."""
        response = api_client.post("/api/universes/", {"name": "Test"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_universe_success(self, authenticated_client, user):
        """Test creating a universe."""
        data = {
            "name": "New Universe",
            "description": "A brand new world",
        }
        response = authenticated_client.post("/api/universes/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Universe"
        assert Universe.objects.filter(name="New Universe", user=user).exists()

    def test_create_universe_with_profiles(self, authenticated_client):
        """Test creating universe with tone and rules profiles."""
        data = {
            "name": "Configured Universe",
            "tone_profile_json": {"grimdark_cozy": 0.3, "comedy_serious": 0.7},
            "rules_profile_json": {"encumbrance": "variant", "flanking": True},
            "calendar_profile_json": {"calendar_type": "custom", "months_per_year": 13},
        }
        response = authenticated_client.post("/api/universes/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["tone_profile_json"]["grimdark_cozy"] == 0.3
        assert response.data["rules_profile_json"]["flanking"] is True

    def test_create_universe_missing_name(self, authenticated_client):
        """Test creating universe without name fails."""
        response = authenticated_client.post(
            "/api/universes/", {"description": "No name"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUniverseDetailEndpoint:
    """Tests for GET /api/universes/{id}/."""

    def test_detail_requires_auth(self, api_client, universe):
        """Test that detail endpoint requires authentication."""
        response = api_client.get(f"/api/universes/{universe.id}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_detail_returns_universe(self, authenticated_client, universe):
        """Test retrieving universe details."""
        response = authenticated_client.get(f"/api/universes/{universe.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Universe"
        assert "tone_profile_json" in response.data
        assert "rules_profile_json" in response.data

    def test_detail_404_for_nonexistent(self, authenticated_client):
        """Test 404 for nonexistent universe."""
        import uuid

        fake_id = uuid.uuid4()
        response = authenticated_client.get(f"/api/universes/{fake_id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_404_for_other_users_universe(
        self, authenticated_client, other_universe
    ):
        """Test 404 for another user's universe."""
        response = authenticated_client.get(f"/api/universes/{other_universe.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUniverseUpdateEndpoint:
    """Tests for PUT/PATCH /api/universes/{id}/."""

    def test_update_requires_auth(self, api_client, universe):
        """Test that update endpoint requires authentication."""
        response = api_client.put(
            f"/api/universes/{universe.id}/", {"name": "Updated"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_full_update_universe(self, authenticated_client, universe):
        """Test full update of universe."""
        data = {
            "name": "Updated Universe",
            "description": "New description",
            "tone_profile_json": {"grimdark_cozy": 0.9},
            "rules_profile_json": {"encumbrance": "ignored"},
        }
        response = authenticated_client.put(
            f"/api/universes/{universe.id}/", data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Universe"
        assert response.data["tone_profile_json"]["grimdark_cozy"] == 0.9

    def test_partial_update_universe(self, authenticated_client, universe):
        """Test partial update of universe."""
        response = authenticated_client.patch(
            f"/api/universes/{universe.id}/",
            {"description": "Partially updated"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["description"] == "Partially updated"
        assert response.data["name"] == "Test Universe"  # Unchanged

    def test_cannot_update_other_users_universe(
        self, authenticated_client, other_universe
    ):
        """Test cannot update another user's universe."""
        response = authenticated_client.patch(
            f"/api/universes/{other_universe.id}/",
            {"name": "Stolen"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_archive_universe(self, authenticated_client, universe):
        """Test archiving a universe."""
        response = authenticated_client.patch(
            f"/api/universes/{universe.id}/",
            {"is_archived": True},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_archived"] is True


@pytest.mark.django_db
class TestUniverseDeleteEndpoint:
    """Tests for DELETE /api/universes/{id}/."""

    def test_delete_requires_auth(self, api_client, universe):
        """Test that delete endpoint requires authentication."""
        response = api_client.delete(f"/api/universes/{universe.id}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_universe(self, authenticated_client, universe):
        """Test deleting a universe."""
        universe_id = universe.id
        response = authenticated_client.delete(f"/api/universes/{universe_id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Universe.objects.filter(id=universe_id).exists()

    def test_delete_cascades_to_homebrew(self, authenticated_client, universe):
        """Test that deleting universe cascades to homebrew."""
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Test Species",
            size="medium",
        )
        universe_id = universe.id
        species_count_before = HomebrewSpecies.objects.filter(
            universe_id=universe_id
        ).count()
        assert species_count_before == 1

        authenticated_client.delete(f"/api/universes/{universe_id}/")

        species_count_after = HomebrewSpecies.objects.filter(
            universe_id=universe_id
        ).count()
        assert species_count_after == 0

    def test_cannot_delete_other_users_universe(
        self, authenticated_client, other_universe
    ):
        """Test cannot delete another user's universe."""
        response = authenticated_client.delete(f"/api/universes/{other_universe.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Universe.objects.filter(id=other_universe.id).exists()


@pytest.mark.django_db
class TestLockHomebrewEndpoint:
    """Tests for POST /api/universes/{id}/lock_homebrew/."""

    def test_lock_homebrew_requires_auth(self, api_client, universe):
        """Test that lock_homebrew requires authentication."""
        response = api_client.post(f"/api/universes/{universe.id}/lock_homebrew/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_lock_homebrew_success(self, authenticated_client, universe):
        """Test locking homebrew content."""
        # Create some unlocked homebrew
        species = HomebrewSpecies.objects.create(
            universe=universe,
            name="Unlocked Species",
            size="medium",
            is_locked=False,
        )

        response = authenticated_client.post(
            f"/api/universes/{universe.id}/lock_homebrew/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "locked_counts" in response.data

        species.refresh_from_db()
        assert species.is_locked is True

    def test_lock_homebrew_reports_counts(self, authenticated_client, universe):
        """Test that lock_homebrew reports locked counts."""
        HomebrewSpecies.objects.create(
            universe=universe, name="Species 1", size="medium", is_locked=False
        )
        HomebrewSpecies.objects.create(
            universe=universe, name="Species 2", size="small", is_locked=False
        )

        response = authenticated_client.post(
            f"/api/universes/{universe.id}/lock_homebrew/"
        )

        assert response.data["locked_counts"]["species"] == 2


@pytest.mark.django_db
class TestHardCanonDocEndpoints:
    """Tests for hard canon document endpoints."""

    def test_create_canon_doc(self, authenticated_client, universe):
        """Test creating a hard canon document."""
        data = {
            "source_type": "upload",
            "title": "World History",
            "raw_text": "In the beginning...",
        }
        response = authenticated_client.post(
            f"/api/universes/{universe.id}/canon/", data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "World History"

    def test_list_canon_docs(self, authenticated_client, universe):
        """Test listing canon documents."""
        UniverseHardCanonDoc.objects.create(
            universe=universe,
            source_type="upload",
            title="Doc 1",
            raw_text="...",
            checksum="abc",
        )
        UniverseHardCanonDoc.objects.create(
            universe=universe,
            source_type="worldgen",
            title="Doc 2",
            raw_text="...",
            checksum="def",
        )

        response = authenticated_client.get(f"/api/universes/{universe.id}/canon/")

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        assert len(results) == 2

    def test_filter_canon_docs_by_source_type(self, authenticated_client, universe):
        """Test filtering canon docs by source type."""
        UniverseHardCanonDoc.objects.create(
            universe=universe,
            source_type="upload",
            title="Upload Doc",
            raw_text="...",
            checksum="abc",
        )
        UniverseHardCanonDoc.objects.create(
            universe=universe,
            source_type="worldgen",
            title="Worldgen Doc",
            raw_text="...",
            checksum="def",
        )

        response = authenticated_client.get(
            f"/api/universes/{universe.id}/canon/", {"source_type": "upload"}
        )

        results = response.data.get("results", response.data)
        assert len(results) == 1
        assert results[0]["title"] == "Upload Doc"

    def test_cannot_access_other_users_canon_docs(
        self, authenticated_client, other_universe
    ):
        """Test cannot access another user's canon docs."""
        UniverseHardCanonDoc.objects.create(
            universe=other_universe,
            source_type="upload",
            title="Private Doc",
            raw_text="...",
            checksum="abc",
        )

        response = authenticated_client.get(
            f"/api/universes/{other_universe.id}/canon/"
        )

        # Should return empty list (filtered by ownership)
        results = response.data.get("results", response.data)
        assert len(results) == 0
