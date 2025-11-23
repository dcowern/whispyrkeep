"""
Tests for content filtering service.
"""

import pytest

from apps.safety.models import RatingProfile
from apps.safety.services.content_filter import ContentFilter, FilterResult


class TestRatingProfile:
    """Tests for RatingProfile model."""

    def test_get_existing_profile(self):
        """Test getting an existing rating profile."""
        profile = RatingProfile.get("PG13")
        assert profile.code == "PG13"
        assert profile.name == "Parents Strongly Cautioned"

    def test_get_unknown_profile_returns_default(self):
        """Test that unknown rating returns PG13 as default."""
        profile = RatingProfile.get("UNKNOWN")
        assert profile.code == "PG13"

    def test_all_profiles_returns_list(self):
        """Test that all_profiles returns complete list."""
        profiles = RatingProfile.all_profiles()
        assert len(profiles) >= 5
        codes = [p.code for p in profiles]
        assert "G" in codes
        assert "PG" in codes
        assert "PG13" in codes
        assert "R" in codes
        assert "NC17" in codes

    def test_g_rating_restrictions(self):
        """Test that G rating has strictest restrictions."""
        profile = RatingProfile.get("G")
        assert not profile.allow_graphic_violence
        assert not profile.allow_gore
        assert not profile.allow_mild_profanity
        assert not profile.allow_strong_profanity
        assert not profile.allow_suggestive_content
        assert not profile.allow_intense_horror

    def test_nc17_rating_allows_all(self):
        """Test that NC17 allows all content."""
        profile = RatingProfile.get("NC17")
        assert profile.allow_graphic_violence
        assert profile.allow_gore
        assert profile.allow_mild_profanity
        assert profile.allow_strong_profanity
        assert profile.allow_suggestive_content
        assert profile.allow_explicit_content


class TestContentFilter:
    """Tests for ContentFilter service."""

    def test_filter_no_changes_for_clean_text(self):
        """Test that clean text passes through unchanged."""
        filter = ContentFilter("PG13")
        result = filter.filter("The hero walks into the tavern.")

        assert result.is_clean
        assert not result.was_modified
        assert result.filtered_text == result.original_text
        assert result.blocked_terms_found == []

    def test_filter_blocks_profanity_for_g_rating(self):
        """Test that G rating blocks mild profanity."""
        filter = ContentFilter("G")
        result = filter.filter("The damn goblin escaped!")

        assert result.was_modified
        assert "damn" in result.blocked_terms_found
        assert "d**n" in result.filtered_text

    def test_filter_allows_profanity_for_r_rating(self):
        """Test that R rating allows profanity."""
        filter = ContentFilter("R")
        result = filter.filter("The damn goblin escaped!")

        assert result.is_clean
        assert result.filtered_text == result.original_text

    def test_filter_blocks_gore_for_pg(self):
        """Test that PG blocks gore descriptions."""
        filter = ContentFilter("PG")
        result = filter.filter("The monster's entrails spill onto the floor.")

        assert result.was_modified
        assert len(result.blocked_terms_found) > 0

    def test_filter_allows_gore_for_r(self):
        """Test that R rating allows gore."""
        filter = ContentFilter("R")
        result = filter.filter("The monster's entrails spill onto the floor.")

        assert result.is_clean

    def test_check_content_returns_violations(self):
        """Test check_content identifies violations."""
        filter = ContentFilter("G")
        passes, violations = filter.check_content("What the hell happened here?")

        assert not passes
        assert len(violations) > 0

    def test_check_content_passes_for_clean(self):
        """Test check_content passes for clean content."""
        filter = ContentFilter("G")
        passes, violations = filter.check_content("The wizard cast a spell.")

        assert passes
        assert violations == []

    def test_system_prompt_additions_for_g(self):
        """Test system prompt additions are generated for G rating."""
        filter = ContentFilter("G")
        additions = filter.get_system_prompt_additions()

        assert "G" in additions
        assert "General Audiences" in additions
        assert "No profanity" in additions
        assert "No gore" in additions

    def test_system_prompt_additions_for_r(self):
        """Test system prompt additions for R rating are permissive."""
        filter = ContentFilter("R")
        additions = filter.get_system_prompt_additions()

        assert "R" in additions
        assert "Restricted" in additions
        # R rating should not have many restrictions listed
        assert "No profanity" not in additions

    def test_redaction_preserves_length(self):
        """Test that redaction keeps word visually similar."""
        filter = ContentFilter("G")
        result = filter.filter("That's damn annoying.")

        # "damn" should become "d**n"
        assert "d**n" in result.filtered_text

    def test_multiple_violations_detected(self):
        """Test that multiple violations are all detected."""
        filter = ContentFilter("G")
        result = filter.filter("The damn goblin from hell attacked!")

        assert result.was_modified
        assert len(result.blocked_terms_found) >= 2

    def test_case_insensitive_filtering(self):
        """Test that filtering is case-insensitive."""
        filter = ContentFilter("G")
        result1 = filter.filter("DAMN it!")
        result2 = filter.filter("Damn it!")
        result3 = filter.filter("damn it!")

        assert result1.was_modified
        assert result2.was_modified
        assert result3.was_modified


class TestFilterResult:
    """Tests for FilterResult dataclass."""

    def test_is_clean_when_not_modified(self):
        """Test is_clean returns True when not modified."""
        result = FilterResult(
            original_text="Hello world",
            filtered_text="Hello world",
            was_modified=False,
            blocked_terms_found=[],
            content_warnings=[],
            rating_code="PG13",
        )
        assert result.is_clean

    def test_is_clean_false_when_modified(self):
        """Test is_clean returns False when modified."""
        result = FilterResult(
            original_text="Hello damn world",
            filtered_text="Hello d**n world",
            was_modified=True,
            blocked_terms_found=["damn"],
            content_warnings=["blocked_keyword"],
            rating_code="G",
        )
        assert not result.is_clean
