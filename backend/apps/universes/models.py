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
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.universe.name})"


class WorldgenSession(models.Model):
    """
    Persistent session for AI-assisted universe building.

    Stores conversation history, draft universe data, and step completion status.
    Users can resume sessions and switch between AI and manual modes.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"

    class Mode(models.TextChoices):
        AI_COLLAB = "ai_collab", "AI Collaboration"
        MANUAL = "manual", "Manual"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="worldgen_sessions",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    mode = models.CharField(
        max_length=20,
        choices=Mode.choices,
        default=Mode.AI_COLLAB,
    )

    # Draft universe data - structured JSON holding all fields
    draft_data_json = models.JSONField(
        default=dict,
        help_text="Draft universe data: name, description, tone, rules, calendar, lore, homebrew",
    )

    # Step completion tracking
    step_status_json = models.JSONField(
        default=dict,
        help_text="Completion status per step: {step_name: {complete: bool, fields: {...}}}",
    )

    # Conversation history for AI collaboration
    conversation_json = models.JSONField(
        default=list,
        help_text="Array of {role: 'user'|'assistant', content: str, timestamp: str}",
    )

    # Link to resulting universe when finalized
    resulting_universe = models.ForeignKey(
        Universe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="worldgen_session",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Worldgen Session"
        verbose_name_plural = "Worldgen Sessions"
        ordering = ["-updated_at"]

    def __str__(self):
        name = self.draft_data_json.get("basics", {}).get("name", "Untitled")
        return f"Worldgen: {name} ({self.status})"

    def get_step_status(self, step_name: str) -> dict:
        """Get the status of a specific step."""
        return self.step_status_json.get(step_name, {"complete": False, "fields": {}})

    def set_step_status(self, step_name: str, complete: bool, fields: dict = None):
        """Update the status of a specific step."""
        self.step_status_json[step_name] = {
            "complete": complete,
            "fields": fields or {},
        }

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        from datetime import datetime, timezone

        if not isinstance(self.conversation_json, list):
            self.conversation_json = []
        self.conversation_json.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    @property
    def all_steps_complete(self) -> bool:
        """Check if all required steps are complete."""
        required_steps = ["basics", "tone", "rules"]
        return all(
            self.step_status_json.get(step, {}).get("complete", False)
            for step in required_steps
        )


class LoreSession(models.Model):
    """
    Session for developing lore documents through AI-assisted chat.

    Similar to WorldgenSession, this tracks conversation history and draft documents.
    Users can develop multiple lore documents in a session before finalizing them
    as UniverseHardCanonDoc entries.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lore_sessions",
    )
    universe = models.ForeignKey(
        Universe,
        on_delete=models.CASCADE,
        related_name="lore_sessions",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    # Current document being developed
    current_document_json = models.JSONField(
        default=dict,
        help_text="Current document draft: {title: str, content: str, tags: list[str]}",
    )

    # Conversation history
    conversation_json = models.JSONField(
        default=list,
        help_text="Array of {role: 'user'|'assistant', content: str, timestamp: str}",
    )

    # All documents created in this session (before finalization)
    draft_documents_json = models.JSONField(
        default=list,
        help_text="Array of draft documents: [{title, content, tags}, ...]",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lore Session"
        verbose_name_plural = "Lore Sessions"
        ordering = ["-updated_at"]

    def __str__(self):
        doc_count = len(self.draft_documents_json) if self.draft_documents_json else 0
        return f"Lore Session ({self.universe.name}) - {doc_count} docs"

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        from datetime import datetime, timezone

        if not isinstance(self.conversation_json, list):
            self.conversation_json = []
        self.conversation_json.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def save_current_document(self):
        """Save the current document to draft_documents list."""
        if self.current_document_json and self.current_document_json.get("title"):
            if not isinstance(self.draft_documents_json, list):
                self.draft_documents_json = []
            self.draft_documents_json.append(self.current_document_json.copy())
            self.current_document_json = {}

    def start_new_document(self, title: str = ""):
        """Start a new document, saving current if it has content."""
        if self.current_document_json and self.current_document_json.get("content"):
            self.save_current_document()
        self.current_document_json = {
            "title": title,
            "content": "",
            "tags": [],
        }


# Import homebrew models to make them available from this module
from .homebrew_models import (  # noqa: E402, F401
    HomebrewBackground,
    HomebrewBase,
    HomebrewClass,
    HomebrewFeat,
    HomebrewItem,
    HomebrewMonster,
    HomebrewSpecies,
    HomebrewSpell,
    HomebrewSubclass,
)
