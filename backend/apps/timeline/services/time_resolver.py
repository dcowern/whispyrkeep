"""
Relative Time Resolver.

Resolves relative time placements for scenarios:
- "after X"
- "before X"
- "N years after/before"

Ticket: 6.1.1

Based on SYSTEM_DESIGN.md section 11.3 Scenario Placement.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Self

from .calendar import CalendarConfig, UniverseTime, TimeDelta, CalendarService, DEFAULT_CALENDAR_CONFIG


class TimeAnchorType(str, Enum):
    """Type of time anchor."""

    EVENT = "event"  # Named event in timeline
    ABSOLUTE = "absolute"  # Specific date
    CAMPAIGN = "campaign"  # Relative to a campaign's start/end


@dataclass
class TimeAnchor:
    """
    A named point in time that can be referenced.

    Used for scenario placement relative to known events.
    """

    id: str
    name: str
    time: UniverseTime
    anchor_type: TimeAnchorType = TimeAnchorType.EVENT
    description: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id,
            "name": self.name,
            "time": self.time.to_dict(),
            "anchor_type": self.anchor_type.value,
            "description": self.description,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Reconstruct from dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            time=UniverseTime.from_dict(data["time"]),
            anchor_type=TimeAnchorType(data.get("anchor_type", "event")),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )


class TimeReferenceType(str, Enum):
    """Type of time reference for scenario placement."""

    ABSOLUTE = "absolute"  # Specific date
    AFTER_EVENT = "after_event"  # After a named event
    BEFORE_EVENT = "before_event"  # Before a named event
    AFTER_CURRENT = "after_current"  # After current universe time
    RELATIVE_YEARS = "relative_years"  # N years from reference


@dataclass
class TimeReference:
    """
    A reference to a point in time, possibly relative.

    Used when setting up a scenario's start time.
    """

    reference_type: TimeReferenceType
    anchor_id: str | None = None  # ID of anchor event (for after_event, before_event)
    offset: TimeDelta | None = None  # Offset from reference
    absolute_time: UniverseTime | None = None  # For absolute references

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "reference_type": self.reference_type.value,
            "anchor_id": self.anchor_id,
            "offset": self.offset.to_dict() if self.offset else None,
            "absolute_time": self.absolute_time.to_dict() if self.absolute_time else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Reconstruct from dict."""
        return cls(
            reference_type=TimeReferenceType(data["reference_type"]),
            anchor_id=data.get("anchor_id"),
            offset=TimeDelta.from_dict(data["offset"]) if data.get("offset") else None,
            absolute_time=UniverseTime.from_dict(data["absolute_time"])
            if data.get("absolute_time")
            else None,
        )

    @classmethod
    def absolute(cls, time: UniverseTime) -> Self:
        """Create an absolute time reference."""
        return cls(
            reference_type=TimeReferenceType.ABSOLUTE,
            absolute_time=time,
        )

    @classmethod
    def after_event(cls, anchor_id: str, offset: TimeDelta | None = None) -> Self:
        """Create a reference after a named event."""
        return cls(
            reference_type=TimeReferenceType.AFTER_EVENT,
            anchor_id=anchor_id,
            offset=offset,
        )

    @classmethod
    def before_event(cls, anchor_id: str, offset: TimeDelta | None = None) -> Self:
        """Create a reference before a named event."""
        return cls(
            reference_type=TimeReferenceType.BEFORE_EVENT,
            anchor_id=anchor_id,
            offset=offset,
        )

    @classmethod
    def after_current(cls, offset: TimeDelta | None = None) -> Self:
        """Create a reference relative to current universe time."""
        return cls(
            reference_type=TimeReferenceType.AFTER_CURRENT,
            offset=offset,
        )

    @classmethod
    def years_from_event(cls, anchor_id: str, years: int) -> Self:
        """Create a reference N years from an event."""
        offset = TimeDelta(years=abs(years))
        if years >= 0:
            return cls(
                reference_type=TimeReferenceType.AFTER_EVENT,
                anchor_id=anchor_id,
                offset=offset,
            )
        else:
            return cls(
                reference_type=TimeReferenceType.BEFORE_EVENT,
                anchor_id=anchor_id,
                offset=offset,
            )


@dataclass
class TimeResolutionResult:
    """Result of resolving a time reference."""

    success: bool
    resolved_time: UniverseTime | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    anchor_used: TimeAnchor | None = None

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "success": self.success,
            "resolved_time": self.resolved_time.to_dict() if self.resolved_time else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "anchor_used": self.anchor_used.to_dict() if self.anchor_used else None,
        }


class TimeResolver:
    """
    Resolves relative time references to absolute times.

    Handles scenario placement relative to:
    - Named events in the timeline
    - Current universe time
    - Specific absolute dates
    """

    def __init__(
        self,
        calendar_config: CalendarConfig | None = None,
        anchors: list[TimeAnchor] | None = None,
    ):
        """
        Initialize the resolver.

        Args:
            calendar_config: Calendar configuration for time math
            anchors: List of known time anchors (events)
        """
        self.calendar = calendar_config or DEFAULT_CALENDAR_CONFIG
        self.calendar_service = CalendarService(self.calendar)
        self._anchors: dict[str, TimeAnchor] = {}

        if anchors:
            for anchor in anchors:
                self._anchors[anchor.id] = anchor

    def add_anchor(self, anchor: TimeAnchor) -> None:
        """Add a time anchor."""
        self._anchors[anchor.id] = anchor

    def remove_anchor(self, anchor_id: str) -> bool:
        """Remove a time anchor."""
        if anchor_id in self._anchors:
            del self._anchors[anchor_id]
            return True
        return False

    def get_anchor(self, anchor_id: str) -> TimeAnchor | None:
        """Get an anchor by ID."""
        return self._anchors.get(anchor_id)

    def get_anchor_by_name(self, name: str) -> TimeAnchor | None:
        """Get an anchor by name (case-insensitive)."""
        name_lower = name.lower()
        for anchor in self._anchors.values():
            if anchor.name.lower() == name_lower:
                return anchor
        return None

    def list_anchors(self) -> list[TimeAnchor]:
        """Get all anchors sorted by time."""
        return sorted(
            self._anchors.values(),
            key=lambda a: a.time.to_total_minutes(self.calendar),
        )

    def resolve(
        self,
        reference: TimeReference,
        current_universe_time: UniverseTime | None = None,
    ) -> TimeResolutionResult:
        """
        Resolve a time reference to an absolute time.

        Args:
            reference: The time reference to resolve
            current_universe_time: Current universe time (for relative refs)

        Returns:
            TimeResolutionResult with resolved time or errors
        """
        if reference.reference_type == TimeReferenceType.ABSOLUTE:
            return self._resolve_absolute(reference)

        elif reference.reference_type == TimeReferenceType.AFTER_CURRENT:
            return self._resolve_after_current(reference, current_universe_time)

        elif reference.reference_type == TimeReferenceType.AFTER_EVENT:
            return self._resolve_after_event(reference)

        elif reference.reference_type == TimeReferenceType.BEFORE_EVENT:
            return self._resolve_before_event(reference)

        else:
            return TimeResolutionResult(
                success=False,
                errors=[f"Unknown reference type: {reference.reference_type}"],
            )

    def _resolve_absolute(self, reference: TimeReference) -> TimeResolutionResult:
        """Resolve an absolute time reference."""
        if not reference.absolute_time:
            return TimeResolutionResult(
                success=False,
                errors=["Absolute reference missing absolute_time"],
            )

        return TimeResolutionResult(
            success=True,
            resolved_time=reference.absolute_time,
        )

    def _resolve_after_current(
        self,
        reference: TimeReference,
        current_time: UniverseTime | None,
    ) -> TimeResolutionResult:
        """Resolve a reference relative to current universe time."""
        if not current_time:
            return TimeResolutionResult(
                success=False,
                errors=["After-current reference requires current universe time"],
            )

        if reference.offset:
            resolved = self.calendar_service.advance_time(
                current_time, reference.offset
            )
        else:
            resolved = current_time

        return TimeResolutionResult(
            success=True,
            resolved_time=resolved,
        )

    def _resolve_after_event(self, reference: TimeReference) -> TimeResolutionResult:
        """Resolve a reference after a named event."""
        if not reference.anchor_id:
            return TimeResolutionResult(
                success=False,
                errors=["After-event reference missing anchor_id"],
            )

        anchor = self._anchors.get(reference.anchor_id)
        if not anchor:
            return TimeResolutionResult(
                success=False,
                errors=[f"Unknown anchor: {reference.anchor_id}"],
            )

        if reference.offset:
            resolved = self.calendar_service.advance_time(anchor.time, reference.offset)
        else:
            resolved = anchor.time

        return TimeResolutionResult(
            success=True,
            resolved_time=resolved,
            anchor_used=anchor,
        )

    def _resolve_before_event(self, reference: TimeReference) -> TimeResolutionResult:
        """Resolve a reference before a named event."""
        if not reference.anchor_id:
            return TimeResolutionResult(
                success=False,
                errors=["Before-event reference missing anchor_id"],
            )

        anchor = self._anchors.get(reference.anchor_id)
        if not anchor:
            return TimeResolutionResult(
                success=False,
                errors=[f"Unknown anchor: {reference.anchor_id}"],
            )

        if reference.offset:
            # Subtract the offset by going backwards in time
            offset_minutes = reference.offset.to_total_minutes(self.calendar)
            anchor_minutes = anchor.time.to_total_minutes(self.calendar)
            resolved_minutes = anchor_minutes - offset_minutes

            if resolved_minutes < 0:
                return TimeResolutionResult(
                    success=False,
                    errors=[
                        f"Resulting time would be before epoch "
                        f"(anchor: {anchor.time.to_dict()}, offset: {reference.offset.to_dict()})"
                    ],
                )

            resolved = UniverseTime.from_total_minutes(resolved_minutes, self.calendar)
        else:
            resolved = anchor.time

        return TimeResolutionResult(
            success=True,
            resolved_time=resolved,
            anchor_used=anchor,
        )

    def find_conflicts(
        self,
        proposed_time: UniverseTime,
        duration_estimate: TimeDelta | None = None,
        existing_scenarios: list[tuple[UniverseTime, UniverseTime]] | None = None,
    ) -> list[str]:
        """
        Find potential timeline conflicts for a proposed scenario.

        Args:
            proposed_time: Proposed start time
            duration_estimate: Estimated scenario duration
            existing_scenarios: List of (start, end) times for existing scenarios

        Returns:
            List of conflict descriptions (empty if no conflicts)
        """
        conflicts = []

        if not existing_scenarios:
            return conflicts

        # Calculate proposed end time
        if duration_estimate:
            proposed_end = self.calendar_service.advance_time(
                proposed_time, duration_estimate
            )
        else:
            # Default to 1 day for conflict detection
            proposed_end = self.calendar_service.advance_time(
                proposed_time, TimeDelta(days=1)
            )

        proposed_start_minutes = proposed_time.to_total_minutes(self.calendar)
        proposed_end_minutes = proposed_end.to_total_minutes(self.calendar)

        for i, (start, end) in enumerate(existing_scenarios):
            start_minutes = start.to_total_minutes(self.calendar)
            end_minutes = end.to_total_minutes(self.calendar)

            # Check for overlap
            if proposed_start_minutes < end_minutes and proposed_end_minutes > start_minutes:
                conflicts.append(
                    f"Overlaps with existing scenario {i + 1} "
                    f"({start.to_dict()} - {end.to_dict()})"
                )

        return conflicts

    def get_timeline(
        self,
        include_anchors: bool = True,
        year_start: int | None = None,
        year_end: int | None = None,
    ) -> list[dict]:
        """
        Get a chronological timeline of events.

        Args:
            include_anchors: Include anchor events
            year_start: Filter to events after this year
            year_end: Filter to events before this year

        Returns:
            List of timeline entries sorted by time
        """
        entries = []

        if include_anchors:
            for anchor in self._anchors.values():
                if year_start and anchor.time.year < year_start:
                    continue
                if year_end and anchor.time.year > year_end:
                    continue

                entries.append({
                    "type": "anchor",
                    "id": anchor.id,
                    "name": anchor.name,
                    "time": anchor.time.to_dict(),
                    "description": anchor.description,
                    "tags": anchor.tags,
                })

        # Sort by time
        entries.sort(
            key=lambda e: UniverseTime.from_dict(e["time"]).to_total_minutes(
                self.calendar
            )
        )

        return entries

    def load_anchors_from_universe(self, universe_data: dict) -> None:
        """
        Load time anchors from universe timeline data.

        Args:
            universe_data: Universe dict with timeline_anchors field
        """
        anchors_data = universe_data.get("timeline_anchors", [])
        for anchor_data in anchors_data:
            anchor = TimeAnchor.from_dict(anchor_data)
            self._anchors[anchor.id] = anchor

    def export_anchors(self) -> list[dict]:
        """Export all anchors as dicts."""
        return [anchor.to_dict() for anchor in self.list_anchors()]
