"""
Lore chunk model for tracking embedded lore.

Based on SYSTEM_DESIGN.md section 5.1 LoreChunk entity.
To be fully implemented in Epic 5.
"""

import uuid

from django.db import models


class LoreChunk(models.Model):
    """
    A chunk of lore text for vector embedding.
    """

    CHUNK_TYPES = [
        ("hard_canon", "Hard Canon"),
        ("soft_lore", "Soft Lore"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    universe = models.ForeignKey(
        "universes.Universe",
        on_delete=models.CASCADE,
        related_name="lore_chunks",
    )
    chunk_type = models.CharField(max_length=20, choices=CHUNK_TYPES)
    source_ref = models.CharField(max_length=100, help_text="doc id or turn id")
    text = models.TextField()
    tags_json = models.JSONField(default=list)
    time_range_json = models.JSONField(
        default=dict,
        help_text="start_year, end_year, in_universe_date",
    )
    is_compacted = models.BooleanField(default=False)
    supersedes_chunk = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="superseded_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lore Chunk"
        verbose_name_plural = "Lore Chunks"

    def __str__(self):
        return f"{self.chunk_type}: {self.text[:50]}..."
