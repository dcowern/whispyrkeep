"""
Tests for LLM Configuration API views.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.llm_config.encryption import encrypt_api_key
from apps.llm_config.models import LlmEndpointConfig


@pytest.fixture(autouse=True)
def kms_secret_setting(settings):
    """Set KMS_SECRET for all tests in this module."""
    settings.KMS_SECRET = "test-kms-secret-key"


@pytest.mark.django_db
class TestLlmConfigListCreateView:
    """Tests for GET/POST /api/llm/config/."""

    def test_list_configs_empty(self, authenticated_client):
        """Test listing configs when user has none."""
        url = reverse("llm_config_list")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    def test_list_configs_returns_user_configs_only(self, authenticated_client, user):
        """Test that only user's configs are returned."""
        # Create config for this user
        LlmEndpointConfig.objects.create(
            user=user,
            provider_name="openai",
            api_key_encrypted=encrypt_api_key("sk-test-key"),
            default_model="gpt-4",
        )

        url = reverse("llm_config_list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["provider_name"] == "openai"
        # API key should not be exposed
        assert "api_key" not in response.data["results"][0]
        assert response.data["results"][0]["has_api_key"] is True

    def test_create_config(self, authenticated_client):
        """Test creating a new LLM config."""
        url = reverse("llm_config_list")
        data = {
            "provider_name": "openai",
            "base_url": "",
            "api_key": "sk-test-new-key",
            "default_model": "gpt-4-turbo",
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["provider_name"] == "openai"
        assert response.data["default_model"] == "gpt-4-turbo"
        assert response.data["has_api_key"] is True
        assert "api_key" not in response.data  # Never exposed

        # Verify in database
        config = LlmEndpointConfig.objects.get(id=response.data["id"])
        assert config.api_key_encrypted is not None

    def test_create_config_requires_api_key(self, authenticated_client):
        """Test that API key is required for creation."""
        url = reverse("llm_config_list")
        data = {
            "provider_name": "openai",
            "default_model": "gpt-4",
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_config_unauthenticated(self, api_client):
        """Test that authentication is required."""
        url = reverse("llm_config_list")
        data = {
            "provider_name": "openai",
            "api_key": "sk-test",
            "default_model": "gpt-4",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLlmConfigDetailView:
    """Tests for GET/PUT/PATCH/DELETE /api/llm/config/{id}/."""

    @pytest.fixture
    def llm_config(self, user):
        """Create a test LLM config."""
        return LlmEndpointConfig.objects.create(
            user=user,
            provider_name="openai",
            api_key_encrypted=encrypt_api_key("sk-original-key"),
            default_model="gpt-4",
            is_active=True,
        )

    def test_retrieve_config(self, authenticated_client, llm_config):
        """Test retrieving a specific config."""
        url = reverse("llm_config_detail", kwargs={"pk": llm_config.id})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["provider_name"] == "openai"
        assert response.data["has_api_key"] is True
        assert "api_key" not in response.data

    def test_update_config_full(self, authenticated_client, llm_config):
        """Test full update with PUT."""
        url = reverse("llm_config_detail", kwargs={"pk": llm_config.id})
        data = {
            "provider_name": "anthropic",
            "api_key": "sk-new-anthropic-key",
            "default_model": "claude-3-opus",
            "is_active": False,
        }

        response = authenticated_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["provider_name"] == "anthropic"
        assert response.data["default_model"] == "claude-3-opus"
        assert response.data["is_active"] is False

    def test_update_config_partial_without_api_key(self, authenticated_client, llm_config):
        """Test partial update without changing API key."""
        url = reverse("llm_config_detail", kwargs={"pk": llm_config.id})
        original_encrypted = llm_config.api_key_encrypted
        data = {"default_model": "gpt-4-turbo"}

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["default_model"] == "gpt-4-turbo"

        # API key should be unchanged
        llm_config.refresh_from_db()
        assert llm_config.api_key_encrypted == original_encrypted

    def test_update_config_with_new_api_key(self, authenticated_client, llm_config):
        """Test updating the API key."""
        url = reverse("llm_config_detail", kwargs={"pk": llm_config.id})
        original_encrypted = llm_config.api_key_encrypted
        data = {"api_key": "sk-brand-new-key"}

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # API key should be changed
        llm_config.refresh_from_db()
        assert llm_config.api_key_encrypted != original_encrypted

    def test_delete_config(self, authenticated_client, llm_config):
        """Test deleting a config."""
        url = reverse("llm_config_detail", kwargs={"pk": llm_config.id})

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert "deleted" in response.data["message"].lower()

        # Verify deleted
        assert not LlmEndpointConfig.objects.filter(id=llm_config.id).exists()

    def test_cannot_access_other_users_config(self, api_client, llm_config):
        """Test that users cannot access other users' configs."""
        # Create and authenticate as a different user
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="otherpass123",
        )
        api_client.force_authenticate(user=other_user)

        url = reverse("llm_config_detail", kwargs={"pk": llm_config.id})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestLlmEndpointDiscoveryViews:
    """Tests for model discovery and validation helpers."""

    def test_list_models_maps_brand_url(self, authenticated_client, monkeypatch):
        """Default providers should map to known base URLs and return parsed models."""

        called = {}

        def fake_get(url, headers=None, params=None, timeout=None):  # pragma: no cover - monkeypatched
            called["url"] = url

            class Resp:
                status_code = 200

                def json(self):
                    return {"data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}]}

            return Resp()

        monkeypatch.setattr("apps.llm_config.services.requests.get", fake_get)

        url = reverse("llm_model_list")
        response = authenticated_client.post(
            url,
            {"provider": "openai", "api_key": "sk-test"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert called["url"] == "https://api.openai.com/v1/models"
        assert response.data["models"] == ["gpt-4o", "gpt-4o-mini"]

    def test_validate_endpoint_falls_back_to_probe(self, authenticated_client, monkeypatch):
        """If model listing fails, validation should probe the provided model."""

        def fake_get(url, headers=None, params=None, timeout=None):  # pragma: no cover - monkeypatched
            from requests import RequestException

            raise RequestException("boom")

        class FakeResp:
            status_code = 200
            text = "ok"

            def json(self):
                return {}

        monkeypatch.setattr("apps.llm_config.services.requests.get", fake_get)
        monkeypatch.setattr("apps.llm_config.services.requests.post", lambda *args, **kwargs: FakeResp())

        url = reverse("llm_config_validate")
        response = authenticated_client.post(
            url,
            {
                "provider": "custom",
                "base_url": "https://local.llm",
                "compatibility": "openai",
                "model": "my-local-model",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_validate_requires_base_url_for_custom(self, authenticated_client):
        """Custom providers must supply a base_url."""

        url = reverse("llm_config_validate")
        response = authenticated_client.post(
            url,
            {"provider": "custom", "model": "foo"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
