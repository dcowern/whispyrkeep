"""
Tests for accounts serializers.

Tests UserRegistrationSerializer, UserProfileSerializer, UserSettingsSerializer.
"""

import pytest
from django.contrib.auth import get_user_model

from apps.accounts.serializers import (
    UserProfileSerializer,
    UserRegistrationSerializer,
    UserSettingsSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistrationSerializer:
    """Tests for UserRegistrationSerializer."""

    def test_valid_registration(self):
        """Test valid user registration data."""
        data = {
            "email": "new@example.com",
            "username": "newuser",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "display_name": "New User",
        }
        serializer = UserRegistrationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        user = serializer.save()

        assert user.email == "new@example.com"
        assert user.username == "newuser"
        assert user.display_name == "New User"
        assert user.check_password("SecurePass123!")

    def test_password_mismatch(self):
        """Test that mismatched passwords fail validation."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!",
            "password_confirm": "DifferentPass123!",
        }
        serializer = UserRegistrationSerializer(data=data)

        assert not serializer.is_valid()
        assert "password_confirm" in serializer.errors

    def test_weak_password(self):
        """Test that weak passwords fail validation."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "123",
            "password_confirm": "123",
        }
        serializer = UserRegistrationSerializer(data=data)

        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_missing_required_fields(self):
        """Test that missing required fields fail validation."""
        data = {"display_name": "Test"}
        serializer = UserRegistrationSerializer(data=data)

        assert not serializer.is_valid()
        assert "email" in serializer.errors
        assert "username" in serializer.errors
        assert "password" in serializer.errors


@pytest.mark.django_db
class TestUserProfileSerializer:
    """Tests for UserProfileSerializer."""

    def test_serialize_user(self):
        """Test serializing a user."""
        user = User.objects.create_user(
            username="serializetest",
            email="serialize@example.com",
            password="testpass123",
            display_name="Serialize User",
        )
        serializer = UserProfileSerializer(user)
        data = serializer.data

        assert data["email"] == "serialize@example.com"
        assert data["username"] == "serializetest"
        assert data["display_name"] == "Serialize User"
        assert "id" in data
        assert "created_at" in data

    def test_update_profile(self):
        """Test updating user profile."""
        user = User.objects.create_user(
            username="updatetest",
            email="update@example.com",
            password="testpass123",
        )
        serializer = UserProfileSerializer(
            user, data={"display_name": "Updated Name"}, partial=True
        )

        assert serializer.is_valid()
        updated_user = serializer.save()

        assert updated_user.display_name == "Updated Name"

    def test_email_readonly(self):
        """Test that email cannot be changed via serializer."""
        user = User.objects.create_user(
            username="readonlytest",
            email="readonly@example.com",
            password="testpass123",
        )
        serializer = UserProfileSerializer(
            user, data={"email": "changed@example.com"}, partial=True
        )

        assert serializer.is_valid()
        updated_user = serializer.save()

        # Email should not have changed
        assert updated_user.email == "readonly@example.com"


@pytest.mark.django_db
class TestUserSettingsSerializer:
    """Tests for UserSettingsSerializer."""

    def test_valid_settings(self):
        """Test valid settings update."""
        user = User.objects.create_user(
            username="settingstest",
            email="settings@example.com",
            password="testpass123",
        )
        data = {
            "settings_json": {
                "ui_mode": "light",
                "nd_options": {"low_stim_mode": True},
                "safety_defaults": {"content_rating": "PG"},
            }
        }
        serializer = UserSettingsSerializer(user, data=data)

        assert serializer.is_valid(), serializer.errors
        updated_user = serializer.save()

        assert updated_user.settings_json["ui_mode"] == "light"
        assert updated_user.settings_json["nd_options"]["low_stim_mode"] is True

    def test_invalid_ui_mode(self):
        """Test that invalid ui_mode fails validation."""
        user = User.objects.create_user(
            username="invalidui",
            email="invalidui@example.com",
            password="testpass123",
        )
        data = {"settings_json": {"ui_mode": "invalid"}}
        serializer = UserSettingsSerializer(user, data=data)

        assert not serializer.is_valid()

    def test_invalid_content_rating(self):
        """Test that invalid content_rating fails validation."""
        user = User.objects.create_user(
            username="invalidrating",
            email="invalidrating@example.com",
            password="testpass123",
        )
        data = {"settings_json": {"safety_defaults": {"content_rating": "XXX"}}}
        serializer = UserSettingsSerializer(user, data=data)

        assert not serializer.is_valid()

    def test_invalid_nd_option(self):
        """Test that unknown nd_options fail validation."""
        user = User.objects.create_user(
            username="invalidnd",
            email="invalidnd@example.com",
            password="testpass123",
        )
        data = {"settings_json": {"nd_options": {"unknown_option": True}}}
        serializer = UserSettingsSerializer(user, data=data)

        assert not serializer.is_valid()
