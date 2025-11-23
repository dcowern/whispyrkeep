"""
Tests for worldgen service and endpoint.

Tests universe creation with LLM-powered worldgen.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.universes.models import Universe, UniverseHardCanonDoc
from apps.universes.services.worldgen import WorldgenRequest, WorldgenService

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
def authenticated_client(api_client, user):
    """Create authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def worldgen_service(user):
    """Create worldgen service."""
    return WorldgenService(user)


@pytest.fixture
def basic_worldgen_request():
    """Create basic worldgen request."""
    return WorldgenRequest(
        name="Test World",
        description="A test fantasy world",
        grimdark_cozy=0.5,
        comedy_serious=0.5,
        low_high_magic=0.7,
        themes=["adventure", "magic"],
    )


@pytest.mark.django_db
class TestWorldgenRequest:
    """Tests for WorldgenRequest dataclass."""

    def test_default_values(self):
        """Test default values for worldgen request."""
        request = WorldgenRequest(name="Test")

        assert request.grimdark_cozy == 0.5
        assert request.comedy_serious == 0.5
        assert request.low_high_magic == 0.5
        assert request.rules_strictness == "standard"
        assert request.homebrew_amount == "moderate"
        assert request.generate_species is True
        assert request.max_species == 3

    def test_custom_values(self):
        """Test custom values for worldgen request."""
        request = WorldgenRequest(
            name="Custom World",
            grimdark_cozy=0.2,
            low_high_magic=0.9,
            themes=["horror", "mystery"],
            rules_strictness="strict",
            max_species=5,
        )

        assert request.grimdark_cozy == 0.2
        assert request.low_high_magic == 0.9
        assert request.themes == ["horror", "mystery"]
        assert request.rules_strictness == "strict"
        assert request.max_species == 5


@pytest.mark.django_db
class TestWorldgenService:
    """Tests for WorldgenService."""

    def test_service_initialization(self, user):
        """Test service initializes correctly."""
        service = WorldgenService(user)
        assert service.user == user
        assert service.llm_config is None  # No LLM config by default

    def test_validate_request_valid(self, worldgen_service):
        """Test validation of valid request."""
        request = WorldgenRequest(name="Valid World")
        errors = worldgen_service._validate_request(request)
        assert len(errors) == 0

    def test_validate_request_empty_name(self, worldgen_service):
        """Test validation rejects empty name."""
        request = WorldgenRequest(name="")
        errors = worldgen_service._validate_request(request)
        assert any("name is required" in e for e in errors)

    def test_validate_request_long_name(self, worldgen_service):
        """Test validation rejects name over 200 chars."""
        request = WorldgenRequest(name="A" * 201)
        errors = worldgen_service._validate_request(request)
        assert any("200 characters" in e for e in errors)

    def test_validate_request_invalid_slider(self, worldgen_service):
        """Test validation rejects invalid slider values."""
        request = WorldgenRequest(name="Test", grimdark_cozy=1.5)
        errors = worldgen_service._validate_request(request)
        assert any("grimdark_cozy" in e for e in errors)

    def test_build_tone_profile(self, worldgen_service, basic_worldgen_request):
        """Test tone profile building."""
        profile = worldgen_service._build_tone_profile(basic_worldgen_request)

        assert profile["grimdark_cozy"] == 0.5
        assert profile["low_high_magic"] == 0.7
        assert profile["themes"] == ["adventure", "magic"]

    def test_build_rules_profile_standard(self, worldgen_service):
        """Test rules profile for standard strictness."""
        request = WorldgenRequest(name="Test", rules_strictness="standard")
        profile = worldgen_service._build_rules_profile(request)

        assert profile["encumbrance"] == "variant"
        assert profile["flanking"] is True
        assert profile["multiclassing"] is True

    def test_build_rules_profile_strict(self, worldgen_service):
        """Test rules profile for strict strictness."""
        request = WorldgenRequest(name="Test", rules_strictness="strict")
        profile = worldgen_service._build_rules_profile(request)

        assert profile["encumbrance"] == "standard"
        assert profile["rest_variant"] == "gritty"
        assert profile["flanking"] is False

    def test_build_rules_profile_loose(self, worldgen_service):
        """Test rules profile for loose strictness."""
        request = WorldgenRequest(name="Test", rules_strictness="loose")
        profile = worldgen_service._build_rules_profile(request)

        assert profile["encumbrance"] == "ignored"
        assert profile["rest_variant"] == "epic"

    def test_generate_creates_universe(self, worldgen_service, basic_worldgen_request):
        """Test generate creates a universe."""
        result = worldgen_service.generate(basic_worldgen_request)

        assert result.success is True
        assert result.universe_id is not None
        assert Universe.objects.filter(id=result.universe_id).exists()

    def test_generate_creates_hard_canon_doc(
        self, worldgen_service, basic_worldgen_request
    ):
        """Test generate creates world overview document."""
        result = worldgen_service.generate(basic_worldgen_request)

        assert result.success is True
        universe = Universe.objects.get(id=result.universe_id)
        assert universe.hard_canon_docs.count() >= 1
        assert universe.hard_canon_docs.filter(source_type="worldgen").exists()

    def test_generate_sets_tone_profile(
        self, worldgen_service, basic_worldgen_request
    ):
        """Test generate sets tone profile on universe."""
        result = worldgen_service.generate(basic_worldgen_request)

        universe = Universe.objects.get(id=result.universe_id)
        assert universe.tone_profile_json["low_high_magic"] == 0.7
        assert universe.tone_profile_json["themes"] == ["adventure", "magic"]

    def test_generate_sets_rules_profile(self, worldgen_service):
        """Test generate sets rules profile on universe."""
        request = WorldgenRequest(
            name="Rules Test",
            rules_strictness="strict",
            homebrew_amount="minimal",
        )
        result = worldgen_service.generate(request)

        universe = Universe.objects.get(id=result.universe_id)
        assert universe.rules_profile_json["homebrew_amount"] == "minimal"

    def test_generate_validation_failure(self, worldgen_service):
        """Test generate returns errors for invalid request."""
        request = WorldgenRequest(name="")
        result = worldgen_service.generate(request)

        assert result.success is False
        assert len(result.errors) > 0

    def test_generate_includes_warning_without_llm(
        self, worldgen_service, basic_worldgen_request
    ):
        """Test generate warns when no LLM config is available."""
        result = worldgen_service.generate(basic_worldgen_request)

        assert result.success is True
        assert any("No LLM configuration" in w for w in result.warnings)

    def test_preview_valid_request(self, worldgen_service, basic_worldgen_request):
        """Test preview returns expected info."""
        preview = worldgen_service.preview(basic_worldgen_request)

        assert preview["valid"] is True
        assert preview["universe_name"] == "Test World"
        assert "tone_profile" in preview
        assert "rules_profile" in preview
        assert "content_to_generate" in preview
        assert preview["llm_available"] is False

    def test_preview_invalid_request(self, worldgen_service):
        """Test preview returns errors for invalid request."""
        request = WorldgenRequest(name="")
        preview = worldgen_service.preview(request)

        assert preview["valid"] is False
        assert "errors" in preview

    def test_build_worldgen_prompt(self, worldgen_service, basic_worldgen_request):
        """Test LLM prompt is built correctly."""
        prompt = worldgen_service._build_worldgen_prompt(basic_worldgen_request)

        assert "Test World" in prompt
        assert "A test fantasy world" in prompt
        assert "high magic" in prompt.lower()  # 0.7 = high magic
        assert "species" in prompt.lower()


@pytest.mark.django_db
class TestWorldgenEndpoint:
    """Tests for worldgen API endpoint."""

    def test_worldgen_requires_auth(self, api_client):
        """Test worldgen endpoint requires authentication."""
        response = api_client.post(
            "/api/universes/worldgen/", {"name": "Test"}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_worldgen_creates_universe(self, authenticated_client):
        """Test worldgen endpoint creates universe."""
        data = {
            "name": "API Universe",
            "description": "Created via API",
            "grimdark_cozy": 0.3,
            "low_high_magic": 0.8,
            "themes": ["steampunk"],
        }
        response = authenticated_client.post(
            "/api/universes/worldgen/", data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert "universe_id" in response.data
        assert Universe.objects.filter(id=response.data["universe_id"]).exists()

    def test_worldgen_validation_error(self, authenticated_client):
        """Test worldgen returns errors for invalid data."""
        response = authenticated_client.post(
            "/api/universes/worldgen/", {"name": ""}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data

    def test_worldgen_invalid_slider_value(self, authenticated_client):
        """Test worldgen handles invalid slider values."""
        data = {
            "name": "Invalid Slider",
            "grimdark_cozy": 2.0,  # Invalid - should be 0-1
        }
        response = authenticated_client.post(
            "/api/universes/worldgen/", data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_worldgen_preview_requires_auth(self, api_client):
        """Test preview endpoint requires authentication."""
        response = api_client.post(
            "/api/universes/worldgen/preview/", {"name": "Test"}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_worldgen_preview_success(self, authenticated_client):
        """Test preview endpoint returns preview data."""
        data = {
            "name": "Preview World",
            "grimdark_cozy": 0.2,
            "themes": ["horror"],
        }
        response = authenticated_client.post(
            "/api/universes/worldgen/preview/", data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["universe_name"] == "Preview World"
        assert "content_to_generate" in response.data

    def test_worldgen_preview_does_not_create(self, authenticated_client, user):
        """Test preview does not create a universe."""
        initial_count = Universe.objects.filter(user=user).count()

        authenticated_client.post(
            "/api/universes/worldgen/preview/",
            {"name": "Should Not Create"},
            format="json",
        )

        assert Universe.objects.filter(user=user).count() == initial_count
