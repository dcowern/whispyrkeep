"""
Tests for the relative time resolver.

Ticket: 6.1.1
"""

import pytest

from apps.timeline.services.calendar import TimeDelta, UniverseTime
from apps.timeline.services.time_resolver import (
    TimeAnchor,
    TimeAnchorType,
    TimeReference,
    TimeReferenceType,
    TimeResolver,
)


class TestTimeAnchor:
    """Tests for TimeAnchor."""

    def test_create_anchor(self):
        """Test creating a time anchor."""
        time = UniverseTime(year=1000, month=6, day=15)
        anchor = TimeAnchor(
            id="war_start",
            name="Start of the Great War",
            time=time,
            description="The war began",
        )

        assert anchor.id == "war_start"
        assert anchor.name == "Start of the Great War"
        assert anchor.time.year == 1000
        assert anchor.anchor_type == TimeAnchorType.EVENT

    def test_anchor_to_dict_from_dict(self):
        """Test anchor serialization roundtrip."""
        time = UniverseTime(year=1000, month=6, day=15)
        anchor = TimeAnchor(
            id="war_start",
            name="Start of the Great War",
            time=time,
            description="The war began",
            tags=["war", "history"],
        )

        d = anchor.to_dict()
        restored = TimeAnchor.from_dict(d)

        assert restored.id == anchor.id
        assert restored.name == anchor.name
        assert restored.time == anchor.time
        assert restored.tags == anchor.tags


class TestTimeReference:
    """Tests for TimeReference."""

    def test_absolute_reference(self):
        """Test creating an absolute time reference."""
        time = UniverseTime(year=1000, month=1, day=1)
        ref = TimeReference.absolute(time)

        assert ref.reference_type == TimeReferenceType.ABSOLUTE
        assert ref.absolute_time == time

    def test_after_event_reference(self):
        """Test creating an after-event reference."""
        ref = TimeReference.after_event("war_start")

        assert ref.reference_type == TimeReferenceType.AFTER_EVENT
        assert ref.anchor_id == "war_start"

    def test_after_event_with_offset(self):
        """Test after-event reference with offset."""
        offset = TimeDelta(years=5)
        ref = TimeReference.after_event("war_start", offset)

        assert ref.reference_type == TimeReferenceType.AFTER_EVENT
        assert ref.anchor_id == "war_start"
        assert ref.offset.years == 5

    def test_before_event_reference(self):
        """Test creating a before-event reference."""
        ref = TimeReference.before_event("war_start")

        assert ref.reference_type == TimeReferenceType.BEFORE_EVENT
        assert ref.anchor_id == "war_start"

    def test_after_current_reference(self):
        """Test creating an after-current reference."""
        ref = TimeReference.after_current()

        assert ref.reference_type == TimeReferenceType.AFTER_CURRENT

    def test_years_from_event_positive(self):
        """Test years_from_event with positive years."""
        ref = TimeReference.years_from_event("war_start", 5)

        assert ref.reference_type == TimeReferenceType.AFTER_EVENT
        assert ref.offset.years == 5

    def test_years_from_event_negative(self):
        """Test years_from_event with negative years."""
        ref = TimeReference.years_from_event("war_start", -5)

        assert ref.reference_type == TimeReferenceType.BEFORE_EVENT
        assert ref.offset.years == 5

    def test_reference_to_dict_from_dict(self):
        """Test reference serialization roundtrip."""
        ref = TimeReference.after_event("war_start", TimeDelta(years=5))

        d = ref.to_dict()
        restored = TimeReference.from_dict(d)

        assert restored.reference_type == ref.reference_type
        assert restored.anchor_id == ref.anchor_id
        assert restored.offset.years == ref.offset.years


class TestTimeResolver:
    """Tests for TimeResolver."""

    @pytest.fixture
    def resolver_with_anchors(self):
        """Create a resolver with some anchors."""
        resolver = TimeResolver()

        # Add some anchors
        resolver.add_anchor(
            TimeAnchor(
                id="founding",
                name="Kingdom Founding",
                time=UniverseTime(year=100, month=1, day=1),
            )
        )
        resolver.add_anchor(
            TimeAnchor(
                id="war_start",
                name="Great War Start",
                time=UniverseTime(year=500, month=6, day=15),
            )
        )
        resolver.add_anchor(
            TimeAnchor(
                id="war_end",
                name="Great War End",
                time=UniverseTime(year=510, month=3, day=22),
            )
        )

        return resolver

    def test_add_and_get_anchor(self):
        """Test adding and retrieving an anchor."""
        resolver = TimeResolver()
        anchor = TimeAnchor(
            id="test",
            name="Test Event",
            time=UniverseTime(year=1000),
        )

        resolver.add_anchor(anchor)
        retrieved = resolver.get_anchor("test")

        assert retrieved is not None
        assert retrieved.name == "Test Event"

    def test_get_anchor_by_name(self):
        """Test getting anchor by name."""
        resolver = TimeResolver()
        anchor = TimeAnchor(
            id="test",
            name="Test Event",
            time=UniverseTime(year=1000),
        )
        resolver.add_anchor(anchor)

        retrieved = resolver.get_anchor_by_name("Test Event")
        assert retrieved is not None
        assert retrieved.id == "test"

        # Case insensitive
        retrieved = resolver.get_anchor_by_name("test event")
        assert retrieved is not None

    def test_remove_anchor(self):
        """Test removing an anchor."""
        resolver = TimeResolver()
        anchor = TimeAnchor(
            id="test",
            name="Test Event",
            time=UniverseTime(year=1000),
        )
        resolver.add_anchor(anchor)

        assert resolver.remove_anchor("test") is True
        assert resolver.get_anchor("test") is None
        assert resolver.remove_anchor("test") is False  # Already removed

    def test_list_anchors_sorted(self, resolver_with_anchors):
        """Test that anchors are listed in chronological order."""
        anchors = resolver_with_anchors.list_anchors()

        assert len(anchors) == 3
        assert anchors[0].id == "founding"  # Year 100
        assert anchors[1].id == "war_start"  # Year 500
        assert anchors[2].id == "war_end"  # Year 510

    def test_resolve_absolute(self, resolver_with_anchors):
        """Test resolving an absolute time reference."""
        time = UniverseTime(year=1000, month=1, day=1)
        ref = TimeReference.absolute(time)

        result = resolver_with_anchors.resolve(ref)

        assert result.success is True
        assert result.resolved_time == time

    def test_resolve_after_current(self, resolver_with_anchors):
        """Test resolving a reference relative to current time."""
        current = UniverseTime(year=1000, month=1, day=1)
        ref = TimeReference.after_current(TimeDelta(days=29))

        result = resolver_with_anchors.resolve(ref, current)

        assert result.success is True
        assert result.resolved_time.month == 1  # Still month 1 (30 days max)
        assert result.resolved_time.day == 30

    def test_resolve_after_current_no_current_fails(self, resolver_with_anchors):
        """Test that after_current fails without current time."""
        ref = TimeReference.after_current()

        result = resolver_with_anchors.resolve(ref, None)

        assert result.success is False
        assert len(result.errors) > 0

    def test_resolve_after_event(self, resolver_with_anchors):
        """Test resolving a reference after an event."""
        ref = TimeReference.after_event("war_start")

        result = resolver_with_anchors.resolve(ref)

        assert result.success is True
        assert result.resolved_time.year == 500
        assert result.resolved_time.month == 6
        assert result.anchor_used.id == "war_start"

    def test_resolve_after_event_with_offset(self, resolver_with_anchors):
        """Test resolving after an event with offset."""
        ref = TimeReference.after_event("war_start", TimeDelta(years=5))

        result = resolver_with_anchors.resolve(ref)

        assert result.success is True
        assert result.resolved_time.year == 505

    def test_resolve_before_event(self, resolver_with_anchors):
        """Test resolving a reference before an event."""
        ref = TimeReference.before_event("war_start", TimeDelta(years=10))

        result = resolver_with_anchors.resolve(ref)

        assert result.success is True
        assert result.resolved_time.year == 490  # 500 - 10

    def test_resolve_unknown_anchor_fails(self, resolver_with_anchors):
        """Test that unknown anchor fails."""
        ref = TimeReference.after_event("unknown_event")

        result = resolver_with_anchors.resolve(ref)

        assert result.success is False
        assert any("unknown" in err.lower() for err in result.errors)

    def test_resolve_before_epoch_fails(self, resolver_with_anchors):
        """Test that going before epoch fails."""
        ref = TimeReference.before_event("founding", TimeDelta(years=200))

        result = resolver_with_anchors.resolve(ref)

        assert result.success is False
        assert any("before epoch" in err.lower() for err in result.errors)

    def test_find_conflicts_no_conflicts(self, resolver_with_anchors):
        """Test finding conflicts when there are none."""
        proposed = UniverseTime(year=600, month=1, day=1)
        existing = [
            (
                UniverseTime(year=500, month=1, day=1),
                UniverseTime(year=510, month=1, day=1),
            ),
        ]

        conflicts = resolver_with_anchors.find_conflicts(proposed, None, existing)

        assert len(conflicts) == 0

    def test_find_conflicts_with_overlap(self, resolver_with_anchors):
        """Test finding conflicts when there is overlap."""
        proposed = UniverseTime(year=505, month=1, day=1)
        duration = TimeDelta(years=10)
        existing = [
            (
                UniverseTime(year=500, month=1, day=1),
                UniverseTime(year=510, month=1, day=1),
            ),
        ]

        conflicts = resolver_with_anchors.find_conflicts(
            proposed, duration, existing
        )

        assert len(conflicts) > 0
        assert any("overlap" in c.lower() for c in conflicts)

    def test_get_timeline(self, resolver_with_anchors):
        """Test getting timeline entries."""
        timeline = resolver_with_anchors.get_timeline()

        assert len(timeline) == 3
        assert timeline[0]["id"] == "founding"
        assert timeline[0]["type"] == "anchor"

    def test_get_timeline_filtered_by_year(self, resolver_with_anchors):
        """Test filtering timeline by year range."""
        timeline = resolver_with_anchors.get_timeline(year_start=400)

        assert len(timeline) == 2  # Only war_start and war_end

    def test_export_anchors(self, resolver_with_anchors):
        """Test exporting anchors."""
        exported = resolver_with_anchors.export_anchors()

        assert len(exported) == 3
        assert all("id" in a and "name" in a and "time" in a for a in exported)

    def test_load_anchors_from_universe(self):
        """Test loading anchors from universe data."""
        resolver = TimeResolver()

        universe_data = {
            "timeline_anchors": [
                {
                    "id": "event1",
                    "name": "Event 1",
                    "time": {"year": 100, "month": 1, "day": 1},
                    "anchor_type": "event",
                    "description": "",
                    "tags": [],
                },
                {
                    "id": "event2",
                    "name": "Event 2",
                    "time": {"year": 200, "month": 1, "day": 1},
                    "anchor_type": "event",
                    "description": "",
                    "tags": [],
                },
            ]
        }

        resolver.load_anchors_from_universe(universe_data)

        assert len(resolver.list_anchors()) == 2
        assert resolver.get_anchor("event1") is not None
        assert resolver.get_anchor("event2") is not None
