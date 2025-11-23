"""
Monotonic Time Validator.

Ensures universe time never decreases in canonical state.

Ticket: 6.0.2

Based on SYSTEM_DESIGN.md section 11.2 Monotonic Rule.
"""

from dataclasses import dataclass, field
from typing import Self

from .calendar import DEFAULT_CALENDAR_CONFIG, CalendarConfig, TimeDelta, UniverseTime


@dataclass
class TimeValidationResult:
    """Result of a time validation check."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Alias for valid."""
        return self.valid

    def add_error(self, error: str) -> Self:
        """Add an error message."""
        self.errors.append(error)
        self.valid = False
        return self

    def add_warning(self, warning: str) -> Self:
        """Add a warning message."""
        self.warnings.append(warning)
        return self

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class TimeValidator:
    """
    Validates time operations to ensure monotonicity.

    The monotonic rule states:
    - Universe time never decreases in canonical state
    - Rewind rewrites history (all later TurnEvents are deleted)
    - Universe current time resets to snapshot time on rewind

    This validator checks:
    - Time advancement patches are valid
    - Time doesn't go backwards
    - Time deltas are reasonable
    """

    # Maximum time jump allowed in a single turn (prevents runaway)
    MAX_SINGLE_TURN_YEARS = 100
    MAX_SINGLE_TURN_DAYS = 365 * MAX_SINGLE_TURN_YEARS

    def __init__(self, calendar_config: CalendarConfig | None = None):
        """Initialize with calendar configuration."""
        self.calendar = calendar_config or DEFAULT_CALENDAR_CONFIG

    def validate_time_advance(
        self,
        current_time: UniverseTime,
        new_time: UniverseTime,
    ) -> TimeValidationResult:
        """
        Validate that a time advancement is monotonic.

        Args:
            current_time: Current universe time
            new_time: Proposed new time

        Returns:
            TimeValidationResult with validation status
        """
        result = TimeValidationResult(valid=True)

        # Check monotonicity - new time must be >= current time
        current_minutes = current_time.to_total_minutes(self.calendar)
        new_minutes = new_time.to_total_minutes(self.calendar)

        if new_minutes < current_minutes:
            result.add_error(
                f"Time cannot go backwards. Current: {current_time.to_dict()}, "
                f"Proposed: {new_time.to_dict()}"
            )
            return result

        # Check for excessive time jump
        diff_minutes = new_minutes - current_minutes
        diff_days = diff_minutes // (24 * 60)

        if diff_days > self.MAX_SINGLE_TURN_DAYS:
            result.add_error(
                f"Time jump too large: {diff_days} days exceeds maximum of "
                f"{self.MAX_SINGLE_TURN_DAYS} days ({self.MAX_SINGLE_TURN_YEARS} years)"
            )
            return result

        # Add warnings for large but valid jumps
        if diff_days > 365:
            result.add_warning(
                f"Large time jump: {diff_days} days ({diff_days // 365} years)"
            )
        elif diff_days > 30:
            result.add_warning(f"Significant time jump: {diff_days} days")

        return result

    def validate_time_delta(
        self,
        delta: TimeDelta,
    ) -> TimeValidationResult:
        """
        Validate a time delta before applying.

        Args:
            delta: Proposed time delta

        Returns:
            TimeValidationResult with validation status
        """
        result = TimeValidationResult(valid=True)

        # Check for negative values
        if delta.years < 0:
            result.add_error(f"Negative years not allowed: {delta.years}")
        if delta.months < 0:
            result.add_error(f"Negative months not allowed: {delta.months}")
        if delta.days < 0:
            result.add_error(f"Negative days not allowed: {delta.days}")
        if delta.hours < 0:
            result.add_error(f"Negative hours not allowed: {delta.hours}")
        if delta.minutes < 0:
            result.add_error(f"Negative minutes not allowed: {delta.minutes}")

        if not result.valid:
            return result

        # Check for excessive delta
        total_minutes = delta.to_total_minutes(self.calendar)
        total_days = total_minutes // (24 * 60)

        if total_days > self.MAX_SINGLE_TURN_DAYS:
            result.add_error(
                f"Time delta too large: {total_days} days exceeds maximum of "
                f"{self.MAX_SINGLE_TURN_DAYS} days"
            )
            return result

        # Warnings for large deltas
        if delta.years > 10:
            result.add_warning(f"Large time delta: {delta.years} years")
        elif total_days > 365:
            result.add_warning(f"Large time delta: {total_days} days")

        return result

    def validate_time_patch(
        self,
        current_time: UniverseTime,
        patch_value: dict,
    ) -> TimeValidationResult:
        """
        Validate a time patch from LLM output.

        The patch can be:
        - An absolute time: {"year": Y, "month": M, "day": D, "hour": H, "minute": M}
        - A delta: {"minutes": N} or {"hours": N} or {"days": N} etc.

        Args:
            current_time: Current universe time
            patch_value: The patch value to validate

        Returns:
            TimeValidationResult with validation status
        """
        result = TimeValidationResult(valid=True)

        if not patch_value:
            result.add_error("Empty time patch")
            return result

        # Check if it's a delta patch (has duration keys but not date keys)
        duration_keys = {"years", "months", "days", "hours", "minutes"}
        date_keys = {"year", "month", "day", "hour", "minute"}

        patch_keys = set(patch_value.keys())
        has_duration = bool(patch_keys & duration_keys)
        has_date = bool(patch_keys & date_keys)

        if has_duration and has_date:
            result.add_error(
                "Time patch cannot mix duration keys (years, months, days, hours, minutes) "
                "with absolute time keys (year, month, day, hour, minute)"
            )
            return result

        if has_duration:
            # It's a delta patch
            try:
                delta = TimeDelta.from_dict(patch_value)
            except (ValueError, TypeError) as e:
                result.add_error(f"Invalid time delta: {e}")
                return result

            delta_result = self.validate_time_delta(delta)
            if not delta_result.valid:
                return delta_result

            result.warnings.extend(delta_result.warnings)

        elif has_date:
            # It's an absolute time patch
            try:
                new_time = UniverseTime.from_dict(patch_value)
            except (ValueError, TypeError) as e:
                result.add_error(f"Invalid absolute time: {e}")
                return result

            advance_result = self.validate_time_advance(current_time, new_time)
            if not advance_result.valid:
                return advance_result

            result.warnings.extend(advance_result.warnings)

        else:
            result.add_error(
                f"Time patch must contain duration keys ({duration_keys}) "
                f"or absolute time keys ({date_keys})"
            )

        return result

    def validate_scenario_start_time(
        self,
        universe_current_time: UniverseTime,
        scenario_start_time: UniverseTime,
        allow_past: bool = False,
    ) -> TimeValidationResult:
        """
        Validate a scenario's start time relative to universe time.

        Args:
            universe_current_time: Current universe time
            scenario_start_time: Proposed scenario start time
            allow_past: Whether to allow starting in the past

        Returns:
            TimeValidationResult with validation status
        """
        result = TimeValidationResult(valid=True)

        universe_minutes = universe_current_time.to_total_minutes(self.calendar)
        scenario_minutes = scenario_start_time.to_total_minutes(self.calendar)

        if not allow_past and scenario_minutes < universe_minutes:
            result.add_error(
                "Scenario cannot start before current universe time. "
                f"Universe: {universe_current_time.to_dict()}, "
                f"Scenario: {scenario_start_time.to_dict()}"
            )
        elif scenario_minutes < universe_minutes:
            result.add_warning(
                "Scenario starts in the universe's past. "
                "This may cause lore conflicts."
            )

        return result

    def apply_time_patch(
        self,
        current_time: UniverseTime,
        patch_value: dict,
    ) -> tuple[UniverseTime, TimeValidationResult]:
        """
        Validate and apply a time patch.

        Args:
            current_time: Current universe time
            patch_value: The patch value to apply

        Returns:
            Tuple of (new_time, validation_result)
        """
        # First validate
        result = self.validate_time_patch(current_time, patch_value)
        if not result.valid:
            return current_time, result

        # Determine patch type and apply
        duration_keys = {"years", "months", "days", "hours", "minutes"}
        patch_keys = set(patch_value.keys())

        if patch_keys & duration_keys:
            # Delta patch
            delta = TimeDelta.from_dict(patch_value)
            from .calendar import CalendarService

            service = CalendarService(self.calendar)
            new_time = service.advance_time(current_time, delta)
        else:
            # Absolute time patch
            new_time = UniverseTime.from_dict(patch_value)

        return new_time, result
