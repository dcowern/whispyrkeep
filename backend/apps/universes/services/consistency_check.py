"""
Consistency Check Service for Universe Worldgen.

Compares fields across a universe draft for contradictions using LLM analysis.
Uses smart grouping to compare related fields within groups and key cross-group pairs.

Tickets: Worldgen consistency check feature
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations
from typing import Any, Generator

from apps.campaigns.services.llm_client import (
    LLMClient,
    LLMClientConfig,
    LLMError,
    Message,
)
from apps.llm_config.models import LlmEndpointConfig
from apps.universes.models import WorldgenSession

logger = logging.getLogger(__name__)


class CheckStatus(str, Enum):
    """Status of a consistency check."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONFLICT_FOUND = "conflict_found"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ConflictResult:
    """Result of checking a field pair for conflicts."""

    field_a: str
    field_b: str
    field_a_label: str
    field_b_label: str
    has_conflict: bool
    conflict_description: str | None = None
    suggested_resolution: str | None = None
    resolution_target: str | None = None  # 'a', 'b', or 'both'


@dataclass
class CheckProgress:
    """Progress state of a consistency check."""

    check_id: str
    status: CheckStatus
    total_pairs: int
    checked_pairs: int
    current_pair: str | None = None
    current_conflict: ConflictResult | None = None
    conflicts_found: int = 0
    conflicts_resolved: int = 0
    error_message: str | None = None


# Field groupings for smart comparison
FIELD_GROUPS = {
    "basics": [
        "basics.name",
        "basics.description",
    ],
    "lore": [
        "lore.world_timeline",
        "lore.regional_histories",
        "lore.legendary_figures",
        "lore.political_history",
        "lore.geography",
        "lore.regions_settlements",
        "lore.cultures_peoples",
        "lore.factions_religions",
        "lore.mysterious_lands",
        "lore.political_leaders",
        "lore.leader_agendas",
        "lore.regional_tensions",
        "lore.faction_conflicts",
    ],
    "homebrew": [
        "homebrew.species",
        "homebrew.classes",
        "homebrew.spells",
        "homebrew.items",
        "homebrew.monsters",
        "homebrew.feats",
        "homebrew.backgrounds",
    ],
}

# Cross-group pairs to check (field_a, field_b)
CROSS_GROUP_PAIRS = [
    # Basics vs Lore - name consistency
    ("basics.name", "lore.world_timeline"),
    ("basics.name", "lore.regional_histories"),
    ("basics.name", "lore.geography"),
    ("basics.name", "lore.regions_settlements"),
    ("basics.description", "lore.world_timeline"),
    ("basics.description", "lore.cultures_peoples"),
    # Lore vs Homebrew - faction/species alignment
    ("lore.factions_religions", "homebrew.species"),
    ("lore.factions_religions", "homebrew.backgrounds"),
    ("lore.cultures_peoples", "homebrew.species"),
    ("lore.cultures_peoples", "homebrew.backgrounds"),
    # Political consistency
    ("lore.political_leaders", "lore.factions_religions"),
    ("lore.leader_agendas", "lore.faction_conflicts"),
]

# Human-readable labels for fields
FIELD_LABELS = {
    "basics.name": "Universe Name",
    "basics.description": "Universe Description",
    "lore.world_timeline": "World Timeline",
    "lore.regional_histories": "Regional Histories",
    "lore.legendary_figures": "Legendary Figures & Myths",
    "lore.political_history": "Political History",
    "lore.geography": "Geography",
    "lore.regions_settlements": "Regions & Settlements",
    "lore.cultures_peoples": "Cultures & Peoples",
    "lore.factions_religions": "Factions & Religions",
    "lore.mysterious_lands": "Mysterious Lands",
    "lore.political_leaders": "Political Leaders",
    "lore.leader_agendas": "Leader Agendas",
    "lore.regional_tensions": "Regional Tensions",
    "lore.faction_conflicts": "Faction Conflicts",
    "homebrew.species": "Custom Species",
    "homebrew.classes": "Custom Classes",
    "homebrew.spells": "Custom Spells",
    "homebrew.items": "Custom Items",
    "homebrew.monsters": "Custom Monsters",
    "homebrew.feats": "Custom Feats",
    "homebrew.backgrounds": "Custom Backgrounds",
}


CONSISTENCY_CHECK_PROMPT = """You are checking a universe's content for internal contradictions.

Compare these two pieces of content:

=== FIELD A: {field_a_label} ===
{field_a_content}

=== FIELD B: {field_b_label} ===
{field_b_content}

Analyze for contradictions such as:
- Conflicting facts (dates, names, locations, numbers)
- Inconsistent descriptions (same entity described differently)
- Logical impossibilities (events that couldn't both happen)
- Timeline inconsistencies

IMPORTANT: Only flag ACTUAL contradictions, not:
- Different aspects of the same topic
- Complementary information
- Varying levels of detail
- Information that could coexist

Respond in JSON format only:
{{
  "has_conflict": true or false,
  "conflict_description": "Brief description of the contradiction" or null,
  "suggested_resolution": "Specific suggestion for how to fix it" or null,
  "resolution_target": "a" or "b" or "both" or null
}}"""


class ConsistencyCheckService:
    """
    Service for checking consistency across universe draft fields.

    Usage:
        service = ConsistencyCheckService(user, session)
        check_id = service.start_check()

        # Poll for progress
        progress = service.get_progress(check_id)

        # When conflict found, resolve it
        service.resolve_conflict(check_id, action='accept', field_updates={...})

        # Continue checking
        progress = service.continue_check(check_id)
    """

    # In-memory storage for check state (in production, use Redis or DB)
    _active_checks: dict[str, CheckProgress] = {}
    _check_generators: dict[str, Generator] = {}

    def __init__(self, user, session: WorldgenSession):
        """Initialize the service."""
        self.user = user
        self.session = session
        self.llm_config = self._get_llm_config()

    def _get_llm_config(self) -> LlmEndpointConfig | None:
        """Get user's active LLM configuration."""
        return LlmEndpointConfig.objects.filter(
            user=self.user,
            is_active=True,
        ).first()

    def _get_field_value(self, field_path: str) -> str | None:
        """Get the value of a field from the session draft data."""
        parts = field_path.split(".")
        if len(parts) != 2:
            return None

        step, field_name = parts
        step_data = self.session.draft_data_json.get(step, {})
        value = step_data.get(field_name)

        if value is None or value == "":
            return None

        # Convert to string if needed
        if isinstance(value, (list, dict)):
            return json.dumps(value, indent=2)

        return str(value)

    def _get_field_label(self, field_path: str) -> str:
        """Get human-readable label for a field."""
        return FIELD_LABELS.get(field_path, field_path)

    def get_comparison_pairs(self) -> list[tuple[str, str]]:
        """
        Generate list of field pairs to compare based on smart grouping.

        Returns pairs where both fields have content.
        """
        pairs = []

        # Within-group comparisons
        for group_name, fields in FIELD_GROUPS.items():
            # Get fields that have content
            fields_with_content = [
                f for f in fields if self._get_field_value(f)
            ]
            # Generate all pairs within this group
            pairs.extend(combinations(fields_with_content, 2))

        # Cross-group comparisons
        for field_a, field_b in CROSS_GROUP_PAIRS:
            # Only include if both fields have content
            if self._get_field_value(field_a) and self._get_field_value(field_b):
                # Avoid duplicates
                if (field_a, field_b) not in pairs and (field_b, field_a) not in pairs:
                    pairs.append((field_a, field_b))

        return pairs

    def check_pair(self, field_a: str, field_b: str) -> ConflictResult:
        """
        Compare two fields for contradictions using LLM.

        Args:
            field_a: Path to first field (e.g., "lore.factions_religions")
            field_b: Path to second field

        Returns:
            ConflictResult with analysis
        """
        content_a = self._get_field_value(field_a) or ""
        content_b = self._get_field_value(field_b) or ""
        label_a = self._get_field_label(field_a)
        label_b = self._get_field_label(field_b)

        # Skip if either field is empty
        if not content_a or not content_b:
            return ConflictResult(
                field_a=field_a,
                field_b=field_b,
                field_a_label=label_a,
                field_b_label=label_b,
                has_conflict=False,
            )

        if not self.llm_config:
            raise LLMError("No LLM configuration found")

        # Build prompt
        prompt = CONSISTENCY_CHECK_PROMPT.format(
            field_a_label=label_a,
            field_a_content=content_a,
            field_b_label=label_b,
            field_b_content=content_b,
        )

        # Call LLM
        config = LLMClientConfig.from_endpoint_config(self.llm_config)
        with LLMClient(config) as client:
            response = client.chat(
                [Message(role="user", content=prompt)],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=500,
            )

        # Parse response
        try:
            # Extract JSON from response
            response_text = response.content.strip()
            # Handle case where LLM wraps JSON in markdown code block
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.startswith("```") and not in_json:
                        in_json = True
                        continue
                    elif line.startswith("```") and in_json:
                        break
                    elif in_json:
                        json_lines.append(line)
                response_text = "\n".join(json_lines)

            result = json.loads(response_text)

            return ConflictResult(
                field_a=field_a,
                field_b=field_b,
                field_a_label=label_a,
                field_b_label=label_b,
                has_conflict=result.get("has_conflict", False),
                conflict_description=result.get("conflict_description"),
                suggested_resolution=result.get("suggested_resolution"),
                resolution_target=result.get("resolution_target"),
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            # Return no conflict if we can't parse
            return ConflictResult(
                field_a=field_a,
                field_b=field_b,
                field_a_label=label_a,
                field_b_label=label_b,
                has_conflict=False,
            )

    def start_check(self) -> str:
        """
        Start a new consistency check.

        Returns:
            check_id for tracking progress
        """
        check_id = str(uuid.uuid4())
        pairs = self.get_comparison_pairs()

        progress = CheckProgress(
            check_id=check_id,
            status=CheckStatus.PENDING,
            total_pairs=len(pairs),
            checked_pairs=0,
            conflicts_found=0,
            conflicts_resolved=0,
        )

        self._active_checks[check_id] = progress

        # Create generator for incremental checking
        def check_generator():
            nonlocal progress
            progress.status = CheckStatus.IN_PROGRESS

            for i, (field_a, field_b) in enumerate(pairs):
                # Update current pair
                progress.current_pair = f"{self._get_field_label(field_a)} vs {self._get_field_label(field_b)}"
                progress.checked_pairs = i

                try:
                    result = self.check_pair(field_a, field_b)

                    if result.has_conflict:
                        progress.status = CheckStatus.CONFLICT_FOUND
                        progress.current_conflict = result
                        progress.conflicts_found += 1
                        yield progress
                        # Wait for resolution before continuing
                        return

                except LLMError as e:
                    logger.error(f"LLM error checking {field_a} vs {field_b}: {e}")
                    progress.status = CheckStatus.FAILED
                    progress.error_message = str(e)
                    yield progress
                    return

                progress.checked_pairs = i + 1

            # All pairs checked
            progress.status = CheckStatus.COMPLETED
            progress.current_pair = None
            yield progress

        self._check_generators[check_id] = check_generator()

        return check_id

    def get_progress(self, check_id: str) -> CheckProgress | None:
        """Get current progress of a check."""
        return self._active_checks.get(check_id)

    def continue_check(self, check_id: str) -> CheckProgress | None:
        """
        Continue a check after resolving a conflict.

        Returns updated progress, or None if check not found.
        """
        progress = self._active_checks.get(check_id)
        generator = self._check_generators.get(check_id)

        if not progress or not generator:
            return None

        # Clear current conflict
        progress.current_conflict = None
        progress.status = CheckStatus.IN_PROGRESS

        try:
            # Advance to next result
            next(generator)
        except StopIteration:
            progress.status = CheckStatus.COMPLETED

        return progress

    def resolve_conflict(
        self,
        check_id: str,
        action: str,
        field_updates: dict[str, Any] | None = None,
    ) -> CheckProgress | None:
        """
        Resolve a conflict and continue checking.

        Args:
            check_id: The check ID
            action: 'accept' to use AI suggestion, 'edit' for manual updates
            field_updates: Dict of {field_path: new_value} for manual edits

        Returns:
            Updated progress after resolution
        """
        progress = self._active_checks.get(check_id)
        if not progress or progress.status != CheckStatus.CONFLICT_FOUND:
            return None

        conflict = progress.current_conflict
        if not conflict:
            return None

        # Apply resolution
        if action == "accept" and conflict.suggested_resolution:
            # Auto-apply suggestion based on resolution_target
            # For now, we'll just mark it resolved and let frontend handle the update
            pass
        elif action == "edit" and field_updates:
            # Apply manual field updates
            for field_path, new_value in field_updates.items():
                parts = field_path.split(".")
                if len(parts) == 2:
                    step, field_name = parts
                    if step not in self.session.draft_data_json:
                        self.session.draft_data_json[step] = {}
                    self.session.draft_data_json[step][field_name] = new_value

            self.session.save()

        progress.conflicts_resolved += 1

        # Continue checking
        return self.continue_check(check_id)

    def cancel_check(self, check_id: str) -> bool:
        """Cancel an active check."""
        if check_id in self._active_checks:
            del self._active_checks[check_id]
        if check_id in self._check_generators:
            del self._check_generators[check_id]
        return True
