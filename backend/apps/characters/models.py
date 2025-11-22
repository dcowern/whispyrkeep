"""
Character model - Player character sheets.

Based on SYSTEM_DESIGN.md section 5.1 CharacterSheet entity.
"""

import uuid

from django.conf import settings
from django.db import models


class CharacterSheet(models.Model):
    """
    Player character sheet with SRD 5.2 attributes.

    To be fully implemented in Epic 3.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="characters",
    )
    universe = models.ForeignKey(
        "universes.Universe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="characters",
    )
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50)
    character_class = models.CharField(max_length=50)
    subclass = models.CharField(max_length=50, blank=True)
    background = models.CharField(max_length=50)
    level = models.PositiveIntegerField(default=1)
    ability_scores_json = models.JSONField(default=dict)
    skills_json = models.JSONField(default=dict)
    proficiencies_json = models.JSONField(default=dict)
    features_json = models.JSONField(default=dict)
    spellbook_json = models.JSONField(default=dict)
    equipment_json = models.JSONField(default=dict)
    homebrew_overrides_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Character Sheet"
        verbose_name_plural = "Character Sheets"

    def __str__(self):
        return f"{self.name} (Level {self.level} {self.character_class})"
