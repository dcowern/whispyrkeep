"""
Tests for accounts models.

Tests the User model with UUID, settings_json, and custom fields.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Tests for the custom User model."""

    def test_create_user(self):
        """Test creating a standard user."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            display_name="Test User",
        )

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.display_name == "Test User"
        assert user.check_password("testpass123")
        assert not user.is_staff
        assert not user.is_superuser
        assert user.is_active

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )

        assert admin.email == "admin@example.com"
        assert admin.is_staff
        assert admin.is_superuser
        assert admin.is_active

    def test_user_uuid_pk(self):
        """Test that user has UUID primary key."""
        user = User.objects.create_user(
            username="uuidtest",
            email="uuid@example.com",
            password="testpass123",
        )

        # UUID should be a valid UUID string (36 chars with hyphens)
        assert len(str(user.id)) == 36
        assert "-" in str(user.id)

    def test_user_email_unique(self):
        """Test that email must be unique."""
        User.objects.create_user(
            username="user1",
            email="unique@example.com",
            password="testpass123",
        )

        with pytest.raises(Exception):  # IntegrityError
            User.objects.create_user(
                username="user2",
                email="unique@example.com",
                password="testpass123",
            )

    def test_settings_json_default(self):
        """Test settings_json has empty dict default."""
        user = User.objects.create_user(
            username="settingstest",
            email="settings@example.com",
            password="testpass123",
        )

        assert user.settings_json == {}

    def test_settings_json_properties(self):
        """Test settings_json property accessors."""
        user = User.objects.create_user(
            username="propstest",
            email="props@example.com",
            password="testpass123",
        )

        # Test defaults
        assert user.ui_mode == "dark"
        assert user.nd_options == {}
        assert user.safety_defaults == {"content_rating": "PG13"}

        # Test with custom settings
        user.settings_json = {
            "ui_mode": "light",
            "nd_options": {"low_stim_mode": True},
            "safety_defaults": {"content_rating": "R"},
        }
        user.save()

        assert user.ui_mode == "light"
        assert user.nd_options == {"low_stim_mode": True}
        assert user.safety_defaults == {"content_rating": "R"}

    def test_user_str(self):
        """Test user string representation."""
        user = User.objects.create_user(
            username="strtest",
            email="str@example.com",
            password="testpass123",
            display_name="Display Name",
        )

        assert str(user) == "Display Name"

        # Without display name, should use email
        user2 = User.objects.create_user(
            username="strtest2",
            email="str2@example.com",
            password="testpass123",
        )

        assert str(user2) == "str2@example.com"
