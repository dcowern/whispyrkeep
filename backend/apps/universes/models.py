"""
Universe models - World settings and hard canon documents.

Based on SYSTEM_DESIGN.md section 5.1 Universe and UniverseHardCanonDoc entities.
"""

import uuid

from django.conf import settings
from django.db import models


class Universe(models.Model):
    """
    A reusable world setting with tone/rules profiles.

    To be fully implemented in Epic 4.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="universes",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    tone_profile_json = models.JSONField(
        default=dict,
        help_text="Sliders: grimdark/cozy, comedy/serious, low/high magic, etc.",
    )
    rules_profile_json = models.JSONField(
        default=dict,
        help_text="SRD baseline + homebrew overrides",
    )
    calendar_profile_json = models.JSONField(
        default=dict,
        help_text="SRD-ish calendar configuration",
    )
    current_universe_time = models.JSONField(
        default=dict,
        help_text="Current in-universe datetime",
    )
    canonical_lore_version = models.PositiveIntegerField(default=0)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Universe"
        verbose_name_plural = "Universes"

    def __str__(self):
        return self.name


class UniverseHardCanonDoc(models.Model):
    """
    Hard canon documents that are never contradicted.

    To be fully implemented in Epic 5.
    """

    SOURCE_TYPES = [
        ("upload", "User Upload"),
        ("worldgen", "World Generation"),
        ("user_edit", "User Edit"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    universe = models.ForeignKey(
        Universe,
        on_delete=models.CASCADE,
        related_name="hard_canon_docs",
    )
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    title = models.CharField(max_length=200)
    raw_text = models.TextField()
    checksum = models.CharField(max_length=64)
    never_compact = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Hard Canon Document"
        verbose_name_plural = "Hard Canon Documents"

    def __str__(self):
        return f"{self.title} ({self.universe.name})"
