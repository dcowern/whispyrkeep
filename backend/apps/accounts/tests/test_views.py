"""
Tests for accounts views.

Tests for auth endpoints: register, login, logout, and profile views.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestRegisterView:
    """Tests for POST /api/auth/register/."""

    def test_register_success(self, api_client):
        """Test successful user registration."""
        url = reverse("register")
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "display_name": "New User",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == "newuser@example.com"
        assert response.data["username"] == "newuser"
        assert response.data["display_name"] == "New User"
        assert "id" in response.data
        assert "message" in response.data

        # Verify user was created
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_register_password_mismatch(self, api_client):
        """Test registration fails with mismatched passwords."""
        url = reverse("register")
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!",
            "password_confirm": "DifferentPass!",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in response.data

    def test_register_duplicate_email(self, api_client, user):
        """Test registration fails with duplicate email."""
        url = reverse("register")
        data = {
            "email": user.email,  # Use existing user's email
            "username": "differentuser",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLoginView:
    """Tests for POST /api/auth/login/."""

    def test_login_success(self, api_client, user):
        """Test successful login returns JWT tokens."""
        url = reverse("login")
        data = {
            "email": user.email,
            "password": "testpass123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_invalid_password(self, api_client, user):
        """Test login fails with invalid password."""
        url = reverse("login")
        data = {
            "email": user.email,
            "password": "wrongpassword",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_invalid_email(self, api_client):
        """Test login fails with non-existent email."""
        url = reverse("login")
        data = {
            "email": "nonexistent@example.com",
            "password": "anypassword",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_credentials(self, api_client):
        """Test login fails with missing credentials."""
        url = reverse("login")

        response = api_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogoutView:
    """Tests for POST /api/auth/logout/."""

    def test_logout_success(self, api_client, user):
        """Test successful logout blacklists refresh token."""
        # First login to get tokens
        login_url = reverse("login")
        login_data = {
            "email": user.email,
            "password": "testpass123",
        }
        login_response = api_client.post(login_url, login_data, format="json")
        refresh_token = login_response.data["refresh"]
        access_token = login_response.data["access"]

        # Now logout
        logout_url = reverse("logout")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_data = {"refresh": refresh_token}

        response = api_client.post(logout_url, logout_data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Logout successful."

        # Verify refresh token is blacklisted (can't be used again)
        refresh_url = reverse("token_refresh")
        api_client.credentials()  # Clear auth header
        refresh_response = api_client.post(
            refresh_url, {"refresh": refresh_token}, format="json"
        )
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_missing_refresh_token(self, authenticated_client):
        """Test logout fails without refresh token."""
        url = reverse("logout")

        response = authenticated_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Refresh token is required" in response.data["detail"]

    def test_logout_invalid_refresh_token(self, authenticated_client):
        """Test logout fails with invalid refresh token."""
        url = reverse("logout")
        data = {"refresh": "invalid-token"}

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_requires_authentication(self, api_client):
        """Test logout requires authentication."""
        url = reverse("logout")
        data = {"refresh": "some-token"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfileView:
    """Tests for GET/PUT/PATCH /api/auth/me/."""

    def test_get_profile(self, authenticated_client, user):
        """Test getting current user profile."""
        url = reverse("user_profile")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
        assert response.data["username"] == user.username
        assert response.data["display_name"] == user.display_name
        assert "id" in response.data
        assert "settings_json" in response.data

    def test_get_profile_unauthenticated(self, api_client):
        """Test profile requires authentication."""
        url = reverse("user_profile")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_patch(self, authenticated_client, user):
        """Test partial profile update."""
        url = reverse("user_profile")
        data = {"display_name": "Updated Name"}

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["display_name"] == "Updated Name"

        # Verify in database
        user.refresh_from_db()
        assert user.display_name == "Updated Name"

    def test_update_profile_settings(self, authenticated_client, user):
        """Test updating user settings."""
        url = reverse("user_profile")
        data = {
            "settings_json": {
                "ui_mode": "light",
                "nd_options": {"low_stim_mode": True},
            }
        }

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["settings_json"]["ui_mode"] == "light"

    def test_cannot_change_email(self, authenticated_client, user):
        """Test that email cannot be changed via profile update."""
        url = reverse("user_profile")
        original_email = user.email
        data = {"email": "newemail@example.com"}

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        # Email should not have changed
        user.refresh_from_db()
        assert user.email == original_email


@pytest.mark.django_db
class TestUserSettingsView:
    """Tests for GET/PUT/PATCH /api/auth/settings/."""

    def test_get_settings(self, authenticated_client, user):
        """Test getting user settings."""
        url = reverse("user_settings")

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)

    def test_get_settings_unauthenticated(self, api_client):
        """Test settings requires authentication."""
        url = reverse("user_settings")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_settings_put(self, authenticated_client, user):
        """Test full settings replacement with PUT."""
        url = reverse("user_settings")
        data = {
            "ui_mode": "light",
            "nd_options": {"low_stim_mode": True},
            "safety_defaults": {"content_rating": "PG"},
        }

        response = authenticated_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["ui_mode"] == "light"
        assert response.data["nd_options"]["low_stim_mode"] is True
        assert response.data["safety_defaults"]["content_rating"] == "PG"

    def test_update_settings_patch_merge(self, authenticated_client, user):
        """Test partial settings update with merge behavior."""
        url = reverse("user_settings")

        # First set some initial settings
        user.settings_json = {
            "ui_mode": "dark",
            "nd_options": {"low_stim_mode": False, "font_size": 14},
        }
        user.save()

        # Patch with partial update
        data = {"nd_options": {"low_stim_mode": True}}

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        # Original ui_mode should be preserved
        assert response.data["ui_mode"] == "dark"
        # nd_options should be merged
        assert response.data["nd_options"]["low_stim_mode"] is True
        assert response.data["nd_options"]["font_size"] == 14

    def test_update_settings_invalid_ui_mode(self, authenticated_client):
        """Test validation rejects invalid ui_mode."""
        url = reverse("user_settings")
        data = {"ui_mode": "invalid"}

        response = authenticated_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_settings_invalid_content_rating(self, authenticated_client):
        """Test validation rejects invalid content_rating."""
        url = reverse("user_settings")
        data = {"safety_defaults": {"content_rating": "XXX"}}

        response = authenticated_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_settings_invalid_nd_option(self, authenticated_client):
        """Test validation rejects unknown nd_options."""
        url = reverse("user_settings")
        data = {"nd_options": {"unknown_option": True}}

        response = authenticated_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
