"""
Tests for the calendar module.

Ticket: 6.0.1
"""

import pytest

from apps.timeline.services.calendar import (
    CalendarConfig,
    CalendarService,
    DEFAULT_CALENDAR_CONFIG,
    DEFAULT_MONTHS,
    MonthConfig,
    TimeDelta,
    UniverseTime,
)


class TestUniverseTime:
    """Tests for UniverseTime dataclass."""

    def test_default_time(self):
        """Test default time values."""
        time = UniverseTime()
        assert time.year == 1
        assert time.month == 1
        assert time.day == 1
        assert time.hour == 0
        assert time.minute == 0

    def test_custom_time(self):
        """Test custom time values."""
        time = UniverseTime(year=1023, month=7, day=14, hour=19, minute=20)
        assert time.year == 1023
        assert time.month == 7
        assert time.day == 14
        assert time.hour == 19
        assert time.minute == 20

    def test_invalid_month_raises(self):
        """Test that invalid month raises ValueError."""
        with pytest.raises(ValueError, match="Month must be 1-12"):
            UniverseTime(month=0)
        with pytest.raises(ValueError, match="Month must be 1-12"):
            UniverseTime(month=13)

    def test_invalid_day_raises(self):
        """Test that invalid day raises ValueError."""
        with pytest.raises(ValueError, match="Day must be 1-31"):
            UniverseTime(day=0)
        with pytest.raises(ValueError, match="Day must be 1-31"):
            UniverseTime(day=32)

    def test_invalid_hour_raises(self):
        """Test that invalid hour raises ValueError."""
        with pytest.raises(ValueError, match="Hour must be 0-23"):
            UniverseTime(hour=-1)
        with pytest.raises(ValueError, match="Hour must be 0-23"):
            UniverseTime(hour=24)

    def test_invalid_minute_raises(self):
        """Test that invalid minute raises ValueError."""
        with pytest.raises(ValueError, match="Minute must be 0-59"):
            UniverseTime(minute=-1)
        with pytest.raises(ValueError, match="Minute must be 0-59"):
            UniverseTime(minute=60)

    def test_to_dict(self):
        """Test serialization to dict."""
        time = UniverseTime(year=1023, month=7, day=14, hour=19, minute=20)
        d = time.to_dict()
        assert d == {
            "year": 1023,
            "month": 7,
            "day": 14,
            "hour": 19,
            "minute": 20,
        }

    def test_from_dict(self):
        """Test deserialization from dict."""
        d = {"year": 1023, "month": 7, "day": 14, "hour": 19, "minute": 20}
        time = UniverseTime.from_dict(d)
        assert time.year == 1023
        assert time.month == 7
        assert time.day == 14
        assert time.hour == 19
        assert time.minute == 20

    def test_from_dict_empty(self):
        """Test deserialization from empty dict uses defaults."""
        time = UniverseTime.from_dict({})
        assert time.year == 1
        assert time.month == 1
        assert time.day == 1

    def test_comparison_operators(self):
        """Test time comparison operators."""
        earlier = UniverseTime(year=1000, month=1, day=1)
        later = UniverseTime(year=1000, month=1, day=2)
        same = UniverseTime(year=1000, month=1, day=1)

        assert earlier < later
        assert later > earlier
        assert earlier <= later
        assert later >= earlier
        assert earlier == same
        assert earlier <= same
        assert earlier >= same

    def test_to_total_minutes_roundtrip(self):
        """Test conversion to minutes and back."""
        original = UniverseTime(year=1023, month=7, day=14, hour=19, minute=20)
        minutes = original.to_total_minutes()
        restored = UniverseTime.from_total_minutes(minutes)

        assert restored.year == original.year
        assert restored.month == original.month
        assert restored.day == original.day
        assert restored.hour == original.hour
        assert restored.minute == original.minute


class TestTimeDelta:
    """Tests for TimeDelta dataclass."""

    def test_default_delta(self):
        """Test default delta values."""
        delta = TimeDelta()
        assert delta.years == 0
        assert delta.months == 0
        assert delta.days == 0
        assert delta.hours == 0
        assert delta.minutes == 0

    def test_custom_delta(self):
        """Test custom delta values."""
        delta = TimeDelta(years=1, months=2, days=10, hours=5, minutes=30)
        assert delta.years == 1
        assert delta.months == 2
        assert delta.days == 10
        assert delta.hours == 5
        assert delta.minutes == 30

    def test_to_total_minutes(self):
        """Test conversion to total minutes."""
        delta = TimeDelta(days=1, hours=2, minutes=30)
        minutes = delta.to_total_minutes()
        # 1 day = 24*60 = 1440 minutes
        # 2 hours = 120 minutes
        # 30 minutes
        assert minutes == 1440 + 120 + 30

    def test_from_dict(self):
        """Test deserialization from dict."""
        d = {"days": 5, "hours": 3}
        delta = TimeDelta.from_dict(d)
        assert delta.days == 5
        assert delta.hours == 3
        assert delta.minutes == 0


class TestCalendarConfig:
    """Tests for CalendarConfig."""

    def test_default_config(self):
        """Test default calendar configuration."""
        config = CalendarConfig()
        assert len(config.months) == 12
        assert len(config.weekdays) == 7
        assert config.days_per_year == 365
        assert config.days_per_week == 7

    def test_days_per_year(self):
        """Test total days calculation."""
        config = DEFAULT_CALENDAR_CONFIG
        total = sum(m.days for m in config.months)
        assert config.days_per_year == total
        assert config.days_per_year == 365

    def test_get_month_by_index(self):
        """Test getting month by 1-based index."""
        config = CalendarConfig()
        month = config.get_month(1)
        assert month.name == "Deepwinter"

        month = config.get_month(12)
        assert month.name == "Winternight"

    def test_get_month_invalid_index_raises(self):
        """Test that invalid month index raises ValueError."""
        config = CalendarConfig()
        with pytest.raises(ValueError):
            config.get_month(0)
        with pytest.raises(ValueError):
            config.get_month(13)

    def test_get_month_by_name(self):
        """Test getting month by name."""
        config = CalendarConfig()
        month = config.get_month_by_name("Greengrass")
        assert month is not None
        assert month.days == 30

        # Case insensitive
        month = config.get_month_by_name("GREENGRASS")
        assert month is not None

    def test_to_dict_from_dict_roundtrip(self):
        """Test serialization roundtrip."""
        config = CalendarConfig()
        d = config.to_dict()
        restored = CalendarConfig.from_dict(d)

        assert len(restored.months) == len(config.months)
        assert len(restored.weekdays) == len(config.weekdays)
        assert restored.epoch_name == config.epoch_name


class TestCalendarService:
    """Tests for CalendarService."""

    def test_advance_time_minutes(self):
        """Test advancing time by minutes."""
        service = CalendarService()
        start = UniverseTime(year=1, month=1, day=1, hour=0, minute=0)
        delta = TimeDelta(minutes=30)

        result = service.advance_time(start, delta)
        assert result.minute == 30
        assert result.hour == 0

    def test_advance_time_hours(self):
        """Test advancing time by hours."""
        service = CalendarService()
        start = UniverseTime(year=1, month=1, day=1, hour=10, minute=0)
        delta = TimeDelta(hours=5)

        result = service.advance_time(start, delta)
        assert result.hour == 15
        assert result.day == 1

    def test_advance_time_hours_overflow(self):
        """Test advancing time with hour overflow."""
        service = CalendarService()
        start = UniverseTime(year=1, month=1, day=1, hour=22, minute=0)
        delta = TimeDelta(hours=5)

        result = service.advance_time(start, delta)
        assert result.hour == 3
        assert result.day == 2

    def test_advance_time_days(self):
        """Test advancing time by days."""
        service = CalendarService()
        start = UniverseTime(year=1, month=1, day=15, hour=0, minute=0)
        delta = TimeDelta(days=10)

        result = service.advance_time(start, delta)
        assert result.day == 25
        assert result.month == 1

    def test_advance_time_month_overflow(self):
        """Test advancing time with month overflow."""
        service = CalendarService()
        # Deepwinter has 30 days
        start = UniverseTime(year=1, month=1, day=25, hour=0, minute=0)
        delta = TimeDelta(days=10)

        result = service.advance_time(start, delta)
        assert result.month == 2
        assert result.day == 5

    def test_advance_time_year_overflow(self):
        """Test advancing time with year overflow."""
        service = CalendarService()
        start = UniverseTime(year=1, month=12, day=25, hour=0, minute=0)
        delta = TimeDelta(days=10)

        result = service.advance_time(start, delta)
        assert result.year == 2
        assert result.month == 1

    def test_time_between(self):
        """Test calculating time between two points."""
        service = CalendarService()
        start = UniverseTime(year=1, month=1, day=1, hour=0, minute=0)
        end = UniverseTime(year=1, month=1, day=2, hour=2, minute=30)

        delta = service.time_between(start, end)
        assert delta.days == 1
        assert delta.hours == 2
        assert delta.minutes == 30

    def test_time_between_raises_for_backwards(self):
        """Test that time_between raises for backwards time."""
        service = CalendarService()
        start = UniverseTime(year=1, month=1, day=2)
        end = UniverseTime(year=1, month=1, day=1)

        with pytest.raises(ValueError, match="End time must be after start time"):
            service.time_between(start, end)

    def test_get_weekday(self):
        """Test getting weekday name."""
        service = CalendarService()
        time = UniverseTime(year=1, month=1, day=1)
        weekday = service.get_weekday(time)
        assert weekday in service.calendar.weekdays

    def test_get_season(self):
        """Test getting season."""
        service = CalendarService()

        # Deepwinter is winter
        time = UniverseTime(year=1, month=1, day=1)
        assert service.get_season(time) == "winter"

        # Greengrass is spring
        time = UniverseTime(year=1, month=4, day=1)
        assert service.get_season(time) == "spring"

        # Highsun is summer
        time = UniverseTime(year=1, month=7, day=1)
        assert service.get_season(time) == "summer"

        # Harvestglow is autumn
        time = UniverseTime(year=1, month=9, day=1)
        assert service.get_season(time) == "autumn"

    def test_format_time(self):
        """Test time formatting."""
        service = CalendarService()
        time = UniverseTime(year=1023, month=4, day=14, hour=19, minute=20)

        formatted = service.format_time(time)
        assert "14" in formatted
        assert "Greengrass" in formatted
        assert "1023" in formatted
        assert "19:20" in formatted

    def test_format_short(self):
        """Test short time formatting."""
        service = CalendarService()
        time = UniverseTime(year=1023, month=4, day=14)

        formatted = service.format_short(time)
        assert formatted == "14/4/1023"

    def test_get_year_progress(self):
        """Test year progress calculation."""
        service = CalendarService()

        # Start of year
        time = UniverseTime(year=1, month=1, day=1, hour=0, minute=0)
        progress = service.get_year_progress(time)
        assert progress == pytest.approx(0.0, abs=0.01)

        # Mid year (approximately)
        time = UniverseTime(year=1, month=7, day=1)
        progress = service.get_year_progress(time)
        assert 0.4 < progress < 0.6

    def test_short_rest_duration(self):
        """Test short rest duration."""
        service = CalendarService()
        delta = service.short_rest_duration()
        assert delta.hours == 1

    def test_long_rest_duration(self):
        """Test long rest duration."""
        service = CalendarService()
        delta = service.long_rest_duration()
        assert delta.hours == 8
