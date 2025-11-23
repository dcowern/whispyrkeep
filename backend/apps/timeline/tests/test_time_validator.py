"""
Tests for the monotonic time validator.

Ticket: 6.0.2
"""


from apps.timeline.services.calendar import TimeDelta, UniverseTime
from apps.timeline.services.time_validator import TimeValidationResult, TimeValidator


class TestTimeValidationResult:
    """Tests for TimeValidationResult."""

    def test_valid_result(self):
        """Test creating a valid result."""
        result = TimeValidationResult(valid=True)
        assert result.valid is True
        assert result.success is True
        assert result.errors == []
        assert result.warnings == []

    def test_add_error_invalidates(self):
        """Test that adding an error invalidates the result."""
        result = TimeValidationResult(valid=True)
        result.add_error("Something went wrong")
        assert result.valid is False
        assert "Something went wrong" in result.errors

    def test_add_warning_keeps_valid(self):
        """Test that adding a warning keeps result valid."""
        result = TimeValidationResult(valid=True)
        result.add_warning("Be careful")
        assert result.valid is True
        assert "Be careful" in result.warnings

    def test_to_dict(self):
        """Test serialization to dict."""
        result = TimeValidationResult(valid=True)
        result.add_warning("A warning")
        d = result.to_dict()
        assert d["valid"] is True
        assert "A warning" in d["warnings"]


class TestTimeValidator:
    """Tests for TimeValidator."""

    def test_validate_time_advance_valid(self):
        """Test validating a valid time advance."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=1)
        new = UniverseTime(year=1000, month=1, day=2)

        result = validator.validate_time_advance(current, new)
        assert result.valid is True

    def test_validate_time_advance_same_time_valid(self):
        """Test that same time is valid (no change)."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=1)
        new = UniverseTime(year=1000, month=1, day=1)

        result = validator.validate_time_advance(current, new)
        assert result.valid is True

    def test_validate_time_advance_backwards_invalid(self):
        """Test that going backwards is invalid."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=2)
        new = UniverseTime(year=1000, month=1, day=1)

        result = validator.validate_time_advance(current, new)
        assert result.valid is False
        assert any("backwards" in err.lower() for err in result.errors)

    def test_validate_time_advance_large_jump_warning(self):
        """Test that large time jumps produce warnings."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=1)
        new = UniverseTime(year=1002, month=1, day=1)  # 2 years

        result = validator.validate_time_advance(current, new)
        assert result.valid is True
        assert len(result.warnings) > 0

    def test_validate_time_advance_excessive_jump_invalid(self):
        """Test that excessive time jumps are invalid."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=1)
        new = UniverseTime(year=1200, month=1, day=1)  # 200 years

        result = validator.validate_time_advance(current, new)
        assert result.valid is False
        assert any("too large" in err.lower() for err in result.errors)

    def test_validate_time_delta_valid(self):
        """Test validating a valid time delta."""
        validator = TimeValidator()
        delta = TimeDelta(days=5, hours=3)

        result = validator.validate_time_delta(delta)
        assert result.valid is True

    def test_validate_time_delta_negative_invalid(self):
        """Test that negative deltas are invalid."""
        validator = TimeValidator()
        delta = TimeDelta(days=-1)

        result = validator.validate_time_delta(delta)
        assert result.valid is False
        assert any("negative" in err.lower() for err in result.errors)

    def test_validate_time_delta_excessive_invalid(self):
        """Test that excessive deltas are invalid."""
        validator = TimeValidator()
        delta = TimeDelta(years=150)

        result = validator.validate_time_delta(delta)
        assert result.valid is False
        assert any("too large" in err.lower() for err in result.errors)

    def test_validate_time_patch_absolute_valid(self):
        """Test validating a valid absolute time patch."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=1)
        patch = {"year": 1000, "month": 1, "day": 2, "hour": 5, "minute": 30}

        result = validator.validate_time_patch(current, patch)
        assert result.valid is True

    def test_validate_time_patch_delta_valid(self):
        """Test validating a valid delta time patch."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=1)
        patch = {"days": 5, "hours": 3}

        result = validator.validate_time_patch(current, patch)
        assert result.valid is True

    def test_validate_time_patch_mixed_invalid(self):
        """Test that mixing absolute and delta keys is invalid."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=1)
        patch = {"year": 1000, "days": 5}  # Mixed!

        result = validator.validate_time_patch(current, patch)
        assert result.valid is False
        assert any("mix" in err.lower() for err in result.errors)

    def test_validate_time_patch_empty_invalid(self):
        """Test that empty patch is invalid."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=1)

        result = validator.validate_time_patch(current, {})
        assert result.valid is False

    def test_validate_time_patch_backwards_invalid(self):
        """Test that backwards absolute patch is invalid."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=2)
        patch = {"year": 1000, "month": 1, "day": 1}

        result = validator.validate_time_patch(current, patch)
        assert result.valid is False

    def test_validate_scenario_start_time_valid(self):
        """Test validating a valid scenario start time."""
        validator = TimeValidator()
        universe_time = UniverseTime(year=1000, month=1, day=1)
        scenario_time = UniverseTime(year=1000, month=6, day=1)

        result = validator.validate_scenario_start_time(universe_time, scenario_time)
        assert result.valid is True

    def test_validate_scenario_start_time_past_invalid(self):
        """Test that starting in the past is invalid by default."""
        validator = TimeValidator()
        universe_time = UniverseTime(year=1000, month=6, day=1)
        scenario_time = UniverseTime(year=1000, month=1, day=1)

        result = validator.validate_scenario_start_time(universe_time, scenario_time)
        assert result.valid is False

    def test_validate_scenario_start_time_past_allowed(self):
        """Test that past is allowed when explicitly enabled."""
        validator = TimeValidator()
        universe_time = UniverseTime(year=1000, month=6, day=1)
        scenario_time = UniverseTime(year=1000, month=1, day=1)

        result = validator.validate_scenario_start_time(
            universe_time, scenario_time, allow_past=True
        )
        assert result.valid is True
        assert len(result.warnings) > 0

    def test_apply_time_patch_delta(self):
        """Test applying a delta time patch."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=1, hour=10, minute=0)
        patch = {"hours": 5, "minutes": 30}

        new_time, result = validator.apply_time_patch(current, patch)
        assert result.valid is True
        assert new_time.hour == 15
        assert new_time.minute == 30

    def test_apply_time_patch_absolute(self):
        """Test applying an absolute time patch."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=1)
        patch = {"year": 1000, "month": 2, "day": 15, "hour": 12, "minute": 0}

        new_time, result = validator.apply_time_patch(current, patch)
        assert result.valid is True
        assert new_time.year == 1000
        assert new_time.month == 2
        assert new_time.day == 15

    def test_apply_time_patch_invalid_returns_current(self):
        """Test that invalid patch returns current time."""
        validator = TimeValidator()
        current = UniverseTime(year=1000, month=1, day=2)
        patch = {"year": 1000, "month": 1, "day": 1}  # Backwards

        new_time, result = validator.apply_time_patch(current, patch)
        assert result.valid is False
        assert new_time == current
