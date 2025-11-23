"""
SRD-ish Calendar Module.

Implements a fantasy calendar system based on SRD 5.2 conventions:
- 365-day year
- 12 months
- 7-day weeks

Ticket: 6.0.1

Based on SYSTEM_DESIGN.md section 11.1 Calendar.
"""

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class MonthConfig:
    """Configuration for a calendar month."""

    name: str
    days: int
    season: str  # "spring", "summer", "autumn", "winter"


# Default SRD-ish month configuration
DEFAULT_MONTHS: tuple[MonthConfig, ...] = (
    MonthConfig(name="Deepwinter", days=30, season="winter"),
    MonthConfig(name="Clawfrost", days=30, season="winter"),
    MonthConfig(name="Thawmelt", days=31, season="spring"),
    MonthConfig(name="Greengrass", days=30, season="spring"),
    MonthConfig(name="Mirthal", days=31, season="spring"),
    MonthConfig(name="Summertide", days=30, season="summer"),
    MonthConfig(name="Highsun", days=31, season="summer"),
    MonthConfig(name="Latesummer", days=31, season="summer"),
    MonthConfig(name="Harvestglow", days=30, season="autumn"),
    MonthConfig(name="Leaffall", days=30, season="autumn"),
    MonthConfig(name="Frostdawn", days=30, season="autumn"),
    MonthConfig(name="Winternight", days=31, season="winter"),
)

DEFAULT_WEEKDAYS: tuple[str, ...] = (
    "Moonday",
    "Towerday",
    "Wingsday",
    "Thunderday",
    "Starday",
    "Swordsday",
    "Godsday",
)


@dataclass
class CalendarConfig:
    """
    Configuration for a universe's calendar system.

    Stored in Universe.calendar_profile_json.
    """

    months: tuple[MonthConfig, ...] = DEFAULT_MONTHS
    weekdays: tuple[str, ...] = DEFAULT_WEEKDAYS
    epoch_name: str = "Age of Heroes"  # Name for the current era
    epoch_year_offset: int = 0  # Year 1 of this epoch = real year epoch_year_offset

    @property
    def days_per_year(self) -> int:
        """Total days in a year."""
        return sum(m.days for m in self.months)

    @property
    def days_per_week(self) -> int:
        """Days in a week."""
        return len(self.weekdays)

    def get_month(self, month_index: int) -> MonthConfig:
        """Get month by 1-based index."""
        if not 1 <= month_index <= len(self.months):
            raise ValueError(f"Invalid month index: {month_index}")
        return self.months[month_index - 1]

    def get_month_by_name(self, name: str) -> MonthConfig | None:
        """Get month by name (case-insensitive)."""
        name_lower = name.lower()
        for month in self.months:
            if month.name.lower() == name_lower:
                return month
        return None

    def get_month_index(self, name: str) -> int | None:
        """Get 1-based month index by name."""
        name_lower = name.lower()
        for i, month in enumerate(self.months, 1):
            if month.name.lower() == name_lower:
                return i
        return None

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "months": [
                {"name": m.name, "days": m.days, "season": m.season}
                for m in self.months
            ],
            "weekdays": list(self.weekdays),
            "epoch_name": self.epoch_name,
            "epoch_year_offset": self.epoch_year_offset,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Reconstruct from dict."""
        if not data:
            return cls()

        months = tuple(
            MonthConfig(
                name=m["name"],
                days=m["days"],
                season=m.get("season", "spring"),
            )
            for m in data.get("months", [])
        ) or DEFAULT_MONTHS

        weekdays = tuple(data.get("weekdays", [])) or DEFAULT_WEEKDAYS

        return cls(
            months=months,
            weekdays=weekdays,
            epoch_name=data.get("epoch_name", "Age of Heroes"),
            epoch_year_offset=data.get("epoch_year_offset", 0),
        )


# Default calendar configuration
DEFAULT_CALENDAR_CONFIG = CalendarConfig()


@dataclass
class UniverseTime:
    """
    Represents a point in time within a universe.

    Stored in universe.current_universe_time and campaign state.

    Time is stored as:
    - year: The year number (can be negative for BC-style dates)
    - month: 1-12
    - day: 1-N (varies by month)
    - hour: 0-23
    - minute: 0-59
    """

    year: int = 1
    month: int = 1
    day: int = 1
    hour: int = 0
    minute: int = 0

    def __post_init__(self):
        """Validate time components."""
        if not 1 <= self.month <= 12:
            raise ValueError(f"Month must be 1-12, got {self.month}")
        if not 1 <= self.day <= 31:
            raise ValueError(f"Day must be 1-31, got {self.day}")
        if not 0 <= self.hour <= 23:
            raise ValueError(f"Hour must be 0-23, got {self.hour}")
        if not 0 <= self.minute <= 59:
            raise ValueError(f"Minute must be 0-59, got {self.minute}")

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "hour": self.hour,
            "minute": self.minute,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Reconstruct from dict."""
        if not data:
            return cls()
        return cls(
            year=data.get("year", 1),
            month=data.get("month", 1),
            day=data.get("day", 1),
            hour=data.get("hour", 0),
            minute=data.get("minute", 0),
        )

    def to_total_minutes(self, calendar: CalendarConfig | None = None) -> int:
        """
        Convert to total minutes from epoch for comparison.

        This allows easy comparison and arithmetic on times.
        """
        if calendar is None:
            calendar = DEFAULT_CALENDAR_CONFIG

        # Calculate days from years
        days = self.year * calendar.days_per_year

        # Add days from months
        for i in range(self.month - 1):
            days += calendar.months[i].days

        # Add days in current month
        days += self.day - 1

        # Convert to minutes
        minutes = days * 24 * 60
        minutes += self.hour * 60
        minutes += self.minute

        return minutes

    @classmethod
    def from_total_minutes(
        cls,
        total_minutes: int,
        calendar: CalendarConfig | None = None,
    ) -> Self:
        """Reconstruct from total minutes."""
        if calendar is None:
            calendar = DEFAULT_CALENDAR_CONFIG

        # Extract minutes and hours
        minute = total_minutes % 60
        total_hours = total_minutes // 60
        hour = total_hours % 24
        total_days = total_hours // 24

        # Calculate year
        days_per_year = calendar.days_per_year
        year = total_days // days_per_year
        remaining_days = total_days % days_per_year

        # Calculate month and day
        month = 1
        for m in calendar.months:
            if remaining_days < m.days:
                break
            remaining_days -= m.days
            month += 1

        day = remaining_days + 1

        return cls(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
        )

    def __lt__(self, other: Self) -> bool:
        """Compare times."""
        return self.to_total_minutes() < other.to_total_minutes()

    def __le__(self, other: Self) -> bool:
        """Compare times."""
        return self.to_total_minutes() <= other.to_total_minutes()

    def __gt__(self, other: Self) -> bool:
        """Compare times."""
        return self.to_total_minutes() > other.to_total_minutes()

    def __ge__(self, other: Self) -> bool:
        """Compare times."""
        return self.to_total_minutes() >= other.to_total_minutes()

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, UniverseTime):
            return NotImplemented
        return self.to_total_minutes() == other.to_total_minutes()


@dataclass
class TimeDelta:
    """
    Represents a duration of time.

    Used for advancing time in game.
    """

    years: int = 0
    months: int = 0
    days: int = 0
    hours: int = 0
    minutes: int = 0

    def to_total_minutes(self, calendar: CalendarConfig | None = None) -> int:
        """Convert to total minutes."""
        if calendar is None:
            calendar = DEFAULT_CALENDAR_CONFIG

        total = self.minutes
        total += self.hours * 60
        total += self.days * 24 * 60

        # Approximate months (use average month length)
        avg_month_days = calendar.days_per_year / len(calendar.months)
        total += int(self.months * avg_month_days * 24 * 60)

        # Years
        total += self.years * calendar.days_per_year * 24 * 60

        return total

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Reconstruct from dict."""
        if not data:
            return cls()
        return cls(
            years=data.get("years", 0),
            months=data.get("months", 0),
            days=data.get("days", 0),
            hours=data.get("hours", 0),
            minutes=data.get("minutes", 0),
        )

    def to_dict(self) -> dict:
        """Convert to dict."""
        return {
            "years": self.years,
            "months": self.months,
            "days": self.days,
            "hours": self.hours,
            "minutes": self.minutes,
        }


class CalendarService:
    """
    Service for calendar and time operations.

    Handles:
    - Time arithmetic (advancing time)
    - Time formatting
    - Season determination
    - Week day calculation
    """

    def __init__(self, calendar_config: CalendarConfig | None = None):
        """Initialize with calendar configuration."""
        self.calendar = calendar_config or DEFAULT_CALENDAR_CONFIG

    def advance_time(self, current: UniverseTime, delta: TimeDelta) -> UniverseTime:
        """
        Advance time by a delta.

        Args:
            current: Current universe time
            delta: Duration to advance

        Returns:
            New UniverseTime after advancement
        """
        total_minutes = current.to_total_minutes(self.calendar)
        delta_minutes = delta.to_total_minutes(self.calendar)
        new_total = total_minutes + delta_minutes

        return UniverseTime.from_total_minutes(new_total, self.calendar)

    def time_between(
        self,
        start: UniverseTime,
        end: UniverseTime,
    ) -> TimeDelta:
        """
        Calculate the duration between two times.

        Args:
            start: Start time
            end: End time

        Returns:
            TimeDelta representing the difference
        """
        start_minutes = start.to_total_minutes(self.calendar)
        end_minutes = end.to_total_minutes(self.calendar)
        diff_minutes = end_minutes - start_minutes

        if diff_minutes < 0:
            raise ValueError("End time must be after start time")

        # Convert back to components
        years = diff_minutes // (self.calendar.days_per_year * 24 * 60)
        remaining = diff_minutes % (self.calendar.days_per_year * 24 * 60)

        days = remaining // (24 * 60)
        remaining = remaining % (24 * 60)

        hours = remaining // 60
        minutes = remaining % 60

        return TimeDelta(
            years=years,
            days=days,
            hours=hours,
            minutes=minutes,
        )

    def get_weekday(self, time: UniverseTime) -> str:
        """
        Get the weekday name for a given time.

        Args:
            time: The universe time

        Returns:
            Name of the weekday
        """
        total_days = time.to_total_minutes(self.calendar) // (24 * 60)
        weekday_index = total_days % self.calendar.days_per_week
        return self.calendar.weekdays[weekday_index]

    def get_season(self, time: UniverseTime) -> str:
        """
        Get the season for a given time.

        Args:
            time: The universe time

        Returns:
            Season name
        """
        month = self.calendar.get_month(time.month)
        return month.season

    def format_time(
        self,
        time: UniverseTime,
        include_time: bool = True,
        include_weekday: bool = True,
    ) -> str:
        """
        Format a universe time as a human-readable string.

        Args:
            time: The universe time
            include_time: Include hour:minute
            include_weekday: Include weekday name

        Returns:
            Formatted string like "Moonday, 14 Greengrass 1023, 19:20"
        """
        parts = []

        if include_weekday:
            parts.append(f"{self.get_weekday(time)},")

        month_name = self.calendar.get_month(time.month).name
        parts.append(f"{time.day} {month_name} {time.year}")

        if include_time:
            parts.append(f"{time.hour:02d}:{time.minute:02d}")

        return " ".join(parts)

    def format_short(self, time: UniverseTime) -> str:
        """
        Format as a short date string.

        Returns:
            String like "14/4/1023"
        """
        return f"{time.day}/{time.month}/{time.year}"

    def get_year_progress(self, time: UniverseTime) -> float:
        """
        Get the progress through the current year as a fraction.

        Args:
            time: The universe time

        Returns:
            Float between 0.0 and 1.0
        """
        # Days elapsed in current year
        days_elapsed = 0
        for i in range(time.month - 1):
            days_elapsed += self.calendar.months[i].days
        days_elapsed += time.day - 1

        # Add partial day
        day_fraction = (time.hour * 60 + time.minute) / (24 * 60)
        days_elapsed += day_fraction

        return days_elapsed / self.calendar.days_per_year

    def short_rest_duration(self) -> TimeDelta:
        """Get the standard short rest duration (1 hour)."""
        return TimeDelta(hours=1)

    def long_rest_duration(self) -> TimeDelta:
        """Get the standard long rest duration (8 hours)."""
        return TimeDelta(hours=8)
