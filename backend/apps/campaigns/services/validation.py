"""
Patch and Roll Validation Service.

Validates LLM output against schema and game rules:
- Roll spec validation
- State patch validation
- Lore delta validation

Ticket: 8.3.1

Based on SYSTEM_DESIGN.md sections 6.2, 7.2, 7.4.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from apps.timeline.services import TimeValidator, UniverseTime


class RollType(str, Enum):
    """Valid roll types."""

    ABILITY_CHECK = "ability_check"
    SAVING_THROW = "saving_throw"
    ATTACK_ROLL = "attack_roll"
    DAMAGE_ROLL = "damage_roll"


class PatchOperation(str, Enum):
    """Valid patch operations."""

    REPLACE = "replace"
    ADD = "add"
    REMOVE = "remove"
    ADVANCE_TIME = "advance_time"


class AdvantageState(str, Enum):
    """Advantage states for rolls."""

    NONE = "none"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"


VALID_ABILITIES = {"str", "dex", "con", "int", "wis", "cha"}

VALID_SKILLS = {
    "acrobatics",
    "animal_handling",
    "arcana",
    "athletics",
    "deception",
    "history",
    "insight",
    "intimidation",
    "investigation",
    "medicine",
    "nature",
    "perception",
    "performance",
    "persuasion",
    "religion",
    "sleight_of_hand",
    "stealth",
    "survival",
}

# Valid paths for state patches (regex patterns)
VALID_PATCH_PATHS = [
    r"^/party/player/hp/current$",
    r"^/party/player/hp/temp$",
    r"^/party/player/conditions$",
    r"^/party/player/conditions/\d+$",
    r"^/party/player/resources/hit_dice/[^/]+/spent$",
    r"^/party/player/resources/spell_slots/\d+/used$",
    r"^/party/player/inventory$",
    r"^/party/player/inventory/\d+$",
    r"^/party/player/money/[a-z]+$",
    r"^/world/location_id$",
    r"^/world/zones/[^/]+/flags/[^/]+$",
    r"^/world/zones/[^/]+/npcs_present$",
    r"^/world/quests$",
    r"^/world/quests/\d+$",
    r"^/world/quests/\d+/stage$",
    r"^/world/quests/\d+/flags/[^/]+$",
    r"^/world/npcs/[^/]+/status$",
    r"^/world/npcs/[^/]+/attitude$",
    r"^/world/npcs/[^/]+/location_id$",
    r"^/world/npcs/[^/]+/knowledge_flags$",
    r"^/world/npcs/[^/]+/knowledge_flags/\d+$",
    r"^/world/factions/[^/]+/[^/]+$",
    r"^/world/global_flags/[^/]+$",
]


@dataclass
class ValidationResult:
    """Result of a validation check."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.valid

    def add_error(self, error: str) -> "ValidationResult":
        self.errors.append(error)
        self.valid = False
        return self

    def add_warning(self, warning: str) -> "ValidationResult":
        self.warnings.append(warning)
        return self

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another result into this one."""
        if not other.valid:
            self.valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class RollValidator:
    """Validates roll request specifications."""

    def validate_roll_request(self, roll: dict) -> ValidationResult:
        """
        Validate a single roll request.

        Args:
            roll: Roll request dict from LLM

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        # Required fields
        if "id" not in roll:
            result.add_error("Roll request missing 'id' field")

        if "type" not in roll:
            result.add_error("Roll request missing 'type' field")
            return result

        roll_type = roll.get("type")
        try:
            roll_type_enum = RollType(roll_type)
        except ValueError:
            result.add_error(
                f"Invalid roll type: {roll_type}. "
                f"Valid types: {[t.value for t in RollType]}"
            )
            return result

        # Type-specific validation
        if roll_type_enum == RollType.ABILITY_CHECK:
            result.merge(self._validate_ability_check(roll))
        elif roll_type_enum == RollType.SAVING_THROW:
            result.merge(self._validate_saving_throw(roll))
        elif roll_type_enum == RollType.ATTACK_ROLL:
            result.merge(self._validate_attack_roll(roll))
        elif roll_type_enum == RollType.DAMAGE_ROLL:
            result.merge(self._validate_damage_roll(roll))

        # Validate advantage if present
        advantage = roll.get("advantage", "none")
        try:
            AdvantageState(advantage)
        except ValueError:
            result.add_error(
                f"Invalid advantage state: {advantage}. "
                f"Valid states: {[a.value for a in AdvantageState]}"
            )

        return result

    def _validate_ability_check(self, roll: dict) -> ValidationResult:
        """Validate an ability check roll."""
        result = ValidationResult(valid=True)

        ability = roll.get("ability")
        if not ability:
            result.add_error("Ability check missing 'ability' field")
        elif ability.lower() not in VALID_ABILITIES:
            result.add_error(
                f"Invalid ability: {ability}. Valid: {VALID_ABILITIES}"
            )

        skill = roll.get("skill")
        if skill and skill.lower() not in VALID_SKILLS:
            result.add_error(
                f"Invalid skill: {skill}. Valid: {VALID_SKILLS}"
            )

        dc = roll.get("dc")
        if dc is not None:
            if not isinstance(dc, int) or dc < 1 or dc > 40:
                result.add_error(f"Invalid DC: {dc}. Must be integer 1-40")

        return result

    def _validate_saving_throw(self, roll: dict) -> ValidationResult:
        """Validate a saving throw roll."""
        result = ValidationResult(valid=True)

        ability = roll.get("ability")
        if not ability:
            result.add_error("Saving throw missing 'ability' field")
        elif ability.lower() not in VALID_ABILITIES:
            result.add_error(
                f"Invalid ability: {ability}. Valid: {VALID_ABILITIES}"
            )

        dc = roll.get("dc")
        if dc is None:
            result.add_error("Saving throw missing 'dc' field")
        elif not isinstance(dc, int) or dc < 1 or dc > 40:
            result.add_error(f"Invalid DC: {dc}. Must be integer 1-40")

        return result

    def _validate_attack_roll(self, roll: dict) -> ValidationResult:
        """Validate an attack roll."""
        result = ValidationResult(valid=True)

        if "attacker" not in roll:
            result.add_error("Attack roll missing 'attacker' field")

        if "target" not in roll:
            result.add_error("Attack roll missing 'target' field")

        return result

    def _validate_damage_roll(self, roll: dict) -> ValidationResult:
        """Validate a damage roll."""
        result = ValidationResult(valid=True)

        # Damage rolls should reference an attack or have a dice expression
        dice = roll.get("dice")
        attack_ref = roll.get("attack_ref")

        if not dice and not attack_ref:
            result.add_warning(
                "Damage roll has neither 'dice' expression nor 'attack_ref'"
            )

        if dice:
            # Validate dice expression (e.g., "2d6+3")
            if not re.match(r"^\d+d\d+(\+\d+)?$", str(dice)):
                result.add_error(
                    f"Invalid dice expression: {dice}. Expected format like '2d6' or '2d6+3'"
                )

        return result

    def validate_roll_requests(self, rolls: list[dict]) -> ValidationResult:
        """Validate a list of roll requests."""
        result = ValidationResult(valid=True)

        if not isinstance(rolls, list):
            result.add_error("roll_requests must be a list")
            return result

        seen_ids = set()
        for i, roll in enumerate(rolls):
            if not isinstance(roll, dict):
                result.add_error(f"Roll request {i} is not a dict")
                continue

            roll_result = self.validate_roll_request(roll)
            if not roll_result.valid:
                for error in roll_result.errors:
                    result.add_error(f"Roll {i}: {error}")
            result.warnings.extend(roll_result.warnings)

            # Check for duplicate IDs
            roll_id = roll.get("id")
            if roll_id in seen_ids:
                result.add_error(f"Duplicate roll ID: {roll_id}")
            elif roll_id:
                seen_ids.add(roll_id)

        return result


class PatchValidator:
    """Validates state patch operations."""

    def __init__(self, current_state: dict | None = None):
        """
        Initialize the validator.

        Args:
            current_state: Current canonical state for context-aware validation
        """
        self.current_state = current_state or {}
        self.time_validator = TimeValidator()

    def validate_patch(self, patch: dict) -> ValidationResult:
        """
        Validate a single state patch.

        Args:
            patch: Patch dict from LLM

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        # Required fields
        if "op" not in patch:
            result.add_error("Patch missing 'op' field")
            return result

        op = patch.get("op")
        try:
            op_enum = PatchOperation(op)
        except ValueError:
            result.add_error(
                f"Invalid operation: {op}. "
                f"Valid operations: {[o.value for o in PatchOperation]}"
            )
            return result

        # Operation-specific validation
        if op_enum == PatchOperation.ADVANCE_TIME:
            result.merge(self._validate_advance_time(patch))
        else:
            result.merge(self._validate_standard_patch(patch, op_enum))

        return result

    def _validate_advance_time(self, patch: dict) -> ValidationResult:
        """Validate an advance_time patch."""
        result = ValidationResult(valid=True)

        value = patch.get("value")
        if not value:
            result.add_error("advance_time patch missing 'value' field")
            return result

        if not isinstance(value, dict):
            result.add_error("advance_time value must be a dict")
            return result

        # Validate time delta
        valid_keys = {"years", "months", "days", "hours", "minutes"}
        for key in value:
            if key not in valid_keys:
                result.add_error(f"Invalid time key: {key}. Valid: {valid_keys}")

            val = value[key]
            if not isinstance(val, int) or val < 0:
                result.add_error(f"Time value '{key}' must be non-negative integer")

        # Check against current time if available
        current_time_data = self.current_state.get("universe_time")
        if current_time_data:
            current_time = UniverseTime.from_dict(current_time_data)
            time_result = self.time_validator.validate_time_patch(current_time, value)
            result.merge(
                ValidationResult(
                    valid=time_result.valid,
                    errors=time_result.errors,
                    warnings=time_result.warnings,
                )
            )

        return result

    def _validate_standard_patch(
        self, patch: dict, op: PatchOperation
    ) -> ValidationResult:
        """Validate a standard (replace/add/remove) patch."""
        result = ValidationResult(valid=True)

        path = patch.get("path")
        if not path:
            result.add_error("Patch missing 'path' field")
            return result

        # Validate path format
        if not path.startswith("/"):
            result.add_error(f"Patch path must start with '/': {path}")

        # Validate path against allowed patterns
        path_valid = False
        for pattern in VALID_PATCH_PATHS:
            if re.match(pattern, path):
                path_valid = True
                break

        if not path_valid:
            result.add_error(f"Invalid or disallowed patch path: {path}")

        # Validate value for non-remove operations
        if op != PatchOperation.REMOVE:
            if "value" not in patch:
                result.add_error(f"Patch operation '{op.value}' requires 'value' field")
            else:
                result.merge(self._validate_value(path, patch["value"]))

        return result

    def _validate_value(self, path: str, value: Any) -> ValidationResult:
        """Validate a patch value based on the path."""
        result = ValidationResult(valid=True)

        # HP validation
        if "/hp/current" in path or "/hp/temp" in path:
            if not isinstance(value, int) or value < 0:
                result.add_error(f"HP value must be non-negative integer: {value}")

        # Conditions validation
        if path.endswith("/conditions"):
            if not isinstance(value, list):
                result.add_error("Conditions must be a list")
            elif not all(isinstance(c, str) for c in value):
                result.add_error("Each condition must be a string")

        # Status validation
        if path.endswith("/status"):
            valid_statuses = {"alive", "dead", "unconscious", "missing", "unknown"}
            if value not in valid_statuses:
                result.add_warning(f"Unusual NPC status: {value}")

        # Attitude validation
        if path.endswith("/attitude"):
            valid_attitudes = {
                "hostile",
                "unfriendly",
                "neutral",
                "friendly",
                "helpful",
            }
            if value not in valid_attitudes:
                result.add_warning(f"Unusual NPC attitude: {value}")

        return result

    def validate_patches(self, patches: list[dict]) -> ValidationResult:
        """Validate a list of patches."""
        result = ValidationResult(valid=True)

        if not isinstance(patches, list):
            result.add_error("patches must be a list")
            return result

        for i, patch in enumerate(patches):
            if not isinstance(patch, dict):
                result.add_error(f"Patch {i} is not a dict")
                continue

            patch_result = self.validate_patch(patch)
            if not patch_result.valid:
                for error in patch_result.errors:
                    result.add_error(f"Patch {i}: {error}")
            result.warnings.extend(patch_result.warnings)

        return result


class LoreDeltaValidator:
    """Validates lore delta entries."""

    VALID_LORE_TYPES = {"hard_canon", "soft_lore"}

    def validate_lore_delta(self, delta: dict) -> ValidationResult:
        """Validate a single lore delta."""
        result = ValidationResult(valid=True)

        # Type validation
        lore_type = delta.get("type")
        if not lore_type:
            result.add_error("Lore delta missing 'type' field")
        elif lore_type not in self.VALID_LORE_TYPES:
            result.add_error(
                f"Invalid lore type: {lore_type}. "
                f"Valid: {self.VALID_LORE_TYPES}"
            )

        # Hard canon should be rare
        if lore_type == "hard_canon":
            result.add_warning(
                "hard_canon lore should be used sparingly for verified facts only"
            )

        # Text validation
        text = delta.get("text")
        if not text:
            result.add_error("Lore delta missing 'text' field")
        elif len(text) > 2000:
            result.add_error("Lore delta text too long (max 2000 chars)")

        # Tags validation
        tags = delta.get("tags", [])
        if not isinstance(tags, list):
            result.add_error("Lore delta 'tags' must be a list")
        elif not all(isinstance(t, str) for t in tags):
            result.add_error("Each tag must be a string")

        # Time reference validation
        time_ref = delta.get("time_ref")
        if time_ref:
            if not isinstance(time_ref, dict):
                result.add_error("Lore delta 'time_ref' must be a dict")
            else:
                try:
                    UniverseTime.from_dict(time_ref)
                except (ValueError, TypeError) as e:
                    result.add_error(f"Invalid time_ref: {e}")

        return result

    def validate_lore_deltas(self, deltas: list[dict]) -> ValidationResult:
        """Validate a list of lore deltas."""
        result = ValidationResult(valid=True)

        if not isinstance(deltas, list):
            result.add_error("lore_deltas must be a list")
            return result

        for i, delta in enumerate(deltas):
            if not isinstance(delta, dict):
                result.add_error(f"Lore delta {i} is not a dict")
                continue

            delta_result = self.validate_lore_delta(delta)
            if not delta_result.valid:
                for error in delta_result.errors:
                    result.add_error(f"Lore delta {i}: {error}")
            result.warnings.extend(delta_result.warnings)

        return result


class LLMOutputValidator:
    """Validates complete LLM output."""

    def __init__(self, current_state: dict | None = None):
        """Initialize validators."""
        self.roll_validator = RollValidator()
        self.patch_validator = PatchValidator(current_state)
        self.lore_validator = LoreDeltaValidator()

    def validate_json_output(self, json_data: dict) -> ValidationResult:
        """
        Validate the DM_JSON portion of LLM output.

        Args:
            json_data: Parsed JSON from LLM response

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        if not isinstance(json_data, dict):
            result.add_error("DM_JSON must be a JSON object")
            return result

        # Validate roll_requests
        if "roll_requests" in json_data:
            result.merge(
                self.roll_validator.validate_roll_requests(json_data["roll_requests"])
            )

        # Validate patches
        if "patches" in json_data:
            result.merge(self.patch_validator.validate_patches(json_data["patches"]))

        # Validate lore_deltas
        if "lore_deltas" in json_data:
            result.merge(
                self.lore_validator.validate_lore_deltas(json_data["lore_deltas"])
            )

        return result
