"""
Campaign and turn event models.

Based on SYSTEM_DESIGN.md section 5.1 Campaign, TurnEvent, CanonicalCampaignState.
"""

import uuid

from django.conf import settings
from django.db import models


class Campaign(models.Model):
    """
    A playable campaign/scenario in a universe.

    To be fully implemented in Epic 7.
    """

    MODE_CHOICES = [
        ("scenario", "One-shot Scenario"),
        ("campaign", "Full Campaign"),
    ]

    LENGTH_CHOICES = [
        ("short", "Short (5-10 turns)"),
        ("medium", "Medium (20-50 turns)"),
        ("long", "Long (100+ turns)"),
        ("custom", "Custom"),
    ]

    FAILURE_STYLE_CHOICES = [
        ("fail_forward", "Fail Forward"),
        ("strict_raw", "Strict RAW"),
    ]

    RATING_CHOICES = [
        ("G", "G - General"),
        ("PG", "PG - Parental Guidance"),
        ("PG13", "PG-13"),
        ("R", "R - Restricted"),
        ("NC17", "NC-17 - Adults Only"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("ended", "Ended"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    universe = models.ForeignKey(
        "universes.Universe",
        on_delete=models.CASCADE,
        related_name="campaigns",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campaigns",
    )
    character_sheet = models.ForeignKey(
        "characters.CharacterSheet",
        on_delete=models.PROTECT,
        related_name="campaigns",
    )
    title = models.CharField(max_length=200)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="scenario")
    target_length = models.CharField(max_length=20, choices=LENGTH_CHOICES, default="medium")
    failure_style = models.CharField(
        max_length=20, choices=FAILURE_STYLE_CHOICES, default="fail_forward"
    )
    content_rating = models.CharField(max_length=10, choices=RATING_CHOICES, default="PG13")
    start_universe_time = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Campaign"
        verbose_name_plural = "Campaigns"

    def __str__(self):
        return f"{self.title} ({self.status})"


class TurnEvent(models.Model):
    """
    Event-sourced turn delta - the core gameplay record.

    To be fully implemented in Epic 8.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="turns",
    )
    turn_index = models.PositiveIntegerField()
    user_input_text = models.TextField()
    llm_response_text = models.TextField()
    roll_spec_json = models.JSONField(default=dict)
    roll_results_json = models.JSONField(default=dict)
    state_patch_json = models.JSONField(default=dict)
    canonical_state_hash = models.CharField(max_length=64)
    lore_deltas_json = models.JSONField(default=list)
    universe_time_after_turn = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Turn Event"
        verbose_name_plural = "Turn Events"
        ordering = ["campaign", "turn_index"]
        unique_together = ["campaign", "turn_index"]

    def __str__(self):
        return f"Turn {self.turn_index} - {self.campaign.title}"


class CanonicalCampaignState(models.Model):
    """
    Snapshot of campaign state for fast loads.

    To be fully implemented in Epic 7.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="state_snapshots",
    )
    turn_index = models.PositiveIntegerField()
    state_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Canonical Campaign State"
        verbose_name_plural = "Canonical Campaign States"
        ordering = ["campaign", "-turn_index"]

    def __str__(self):
        return f"State at turn {self.turn_index} - {self.campaign.title}"
