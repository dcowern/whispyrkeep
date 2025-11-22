"""
User model and profile for WhispyrKeep.

Based on SYSTEM_DESIGN.md section 5.1 User entity.
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with UUID primary key and settings JSON field.

    Fields from spec:
    - id (uuid pk)
    - email (unique)
    - password_hash (handled by AbstractUser)
    - display_name
    - created_at
    - settings_json (ui mode, ND options, safety defaults, endpoint prefs)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100, blank=True)
    settings_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="User preferences: UI mode, ND options, safety defaults, endpoint prefs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.display_name or self.email

    @property
    def ui_mode(self):
        return self.settings_json.get("ui_mode", "dark")

    @property
    def nd_options(self):
        return self.settings_json.get("nd_options", {})

    @property
    def safety_defaults(self):
        return self.settings_json.get("safety_defaults", {"content_rating": "PG13"})
