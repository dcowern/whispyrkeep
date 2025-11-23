"""
Content filtering service for LLM outputs.

Filters content based on campaign rating profiles (Epic 13).
"""

import re
from dataclasses import dataclass
from typing import Optional

from apps.safety.models import RatingProfile


@dataclass
class FilterResult:
    """Result of content filtering operation."""

    original_text: str
    filtered_text: str
    was_modified: bool
    blocked_terms_found: list[str]
    content_warnings: list[str]
    rating_code: str

    @property
    def is_clean(self) -> bool:
        """Check if no modifications were needed."""
        return not self.was_modified


class ContentFilter:
    """
    Content filter for LLM narrative outputs.

    Applies rating-based content filtering to ensure narratives
    comply with the campaign's content rating.
    """

    # Patterns for detecting potentially problematic content
    GORE_PATTERNS = [
        r"\b(entrails|viscera|guts|intestines)\s+(spill|pour|hang)",
        r"\b(dismember|decapitat|eviscerat)\w*\b",
        r"\b(blood|gore)\s+(spray|splash|pool|gush)\w*",
    ]

    PROFANITY_MILD = ["damn", "hell", "crap", "bastard", "ass"]
    PROFANITY_STRONG = ["fuck", "shit", "bitch", "asshole", "goddamn"]

    SUGGESTIVE_PATTERNS = [
        r"\b(moan|groan)\w*\s+(with pleasure|seductively)",
        r"\b(caress|fondle|stroke)\w*\s+(body|skin|thigh)",
        r"\b(undress|disrobe)\w*",
    ]

    EXPLICIT_PATTERNS = [
        r"\bsex(ual)?\s+(act|intercourse|scene)",
        r"\b(penetrat|thrust|orgasm)\w*\b",
    ]

    HORROR_INTENSE_PATTERNS = [
        r"\b(maggot|worm)s?\s+(crawl|writhe|burst)",
        r"\b(rot|decay)\w*\s+(flesh|corpse|body)",
        r"\b(terror|horror)\s+(grip|seize|overwhelm)",
    ]

    BODY_HORROR_PATTERNS = [
        r"\b(flesh|skin)\s+(melt|peel|slough)",
        r"\b(bone)s?\s+(crack|snap|protrude)",
        r"\btransform\w*\s+(grotesque|hideous|monstrous)",
    ]

    def __init__(self, rating_code: str):
        """
        Initialize filter with a rating profile.

        Args:
            rating_code: The content rating code (G, PG, PG13, R, NC17)
        """
        self.profile = RatingProfile.get(rating_code)
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns based on rating profile."""
        self._blocked_patterns: list[tuple[re.Pattern, str]] = []

        # Blocked keywords from profile
        if self.profile.blocked_keywords:
            pattern = r"\b(" + "|".join(re.escape(kw) for kw in self.profile.blocked_keywords) + r")\b"
            self._blocked_patterns.append(
                (re.compile(pattern, re.IGNORECASE), "blocked_keyword")
            )

        # Gore patterns
        if not self.profile.allow_gore:
            for pattern in self.GORE_PATTERNS:
                self._blocked_patterns.append(
                    (re.compile(pattern, re.IGNORECASE), "gore")
                )

        # Profanity patterns
        if not self.profile.allow_strong_profanity:
            pattern = r"\b(" + "|".join(re.escape(p) for p in self.PROFANITY_STRONG) + r")\b"
            self._blocked_patterns.append(
                (re.compile(pattern, re.IGNORECASE), "strong_profanity")
            )

        if not self.profile.allow_mild_profanity:
            pattern = r"\b(" + "|".join(re.escape(p) for p in self.PROFANITY_MILD) + r")\b"
            self._blocked_patterns.append(
                (re.compile(pattern, re.IGNORECASE), "mild_profanity")
            )

        # Suggestive content
        if not self.profile.allow_suggestive_content:
            for pattern in self.SUGGESTIVE_PATTERNS:
                self._blocked_patterns.append(
                    (re.compile(pattern, re.IGNORECASE), "suggestive")
                )

        # Explicit content
        if not self.profile.allow_explicit_content:
            for pattern in self.EXPLICIT_PATTERNS:
                self._blocked_patterns.append(
                    (re.compile(pattern, re.IGNORECASE), "explicit")
                )

        # Horror patterns
        if not self.profile.allow_intense_horror:
            for pattern in self.HORROR_INTENSE_PATTERNS:
                self._blocked_patterns.append(
                    (re.compile(pattern, re.IGNORECASE), "intense_horror")
                )

        if not self.profile.allow_body_horror:
            for pattern in self.BODY_HORROR_PATTERNS:
                self._blocked_patterns.append(
                    (re.compile(pattern, re.IGNORECASE), "body_horror")
                )

    def filter(self, text: str) -> FilterResult:
        """
        Filter text according to rating profile.

        Args:
            text: The narrative text to filter

        Returns:
            FilterResult with filtered text and metadata
        """
        blocked_terms: list[str] = []
        content_warnings: list[str] = set()
        filtered = text

        # Check all blocked patterns
        for pattern, category in self._blocked_patterns:
            matches = pattern.findall(filtered)
            if matches:
                for match in matches:
                    blocked_terms.append(str(match) if isinstance(match, str) else match[0])
                content_warnings.add(category)
                # Replace with asterisks (keeping first and last letter)
                filtered = pattern.sub(lambda m: self._redact(m.group()), filtered)

        was_modified = filtered != text

        return FilterResult(
            original_text=text,
            filtered_text=filtered,
            was_modified=was_modified,
            blocked_terms_found=blocked_terms,
            content_warnings=list(content_warnings),
            rating_code=self.profile.code,
        )

    def _redact(self, word: str) -> str:
        """Redact a word, keeping first and last character."""
        if len(word) <= 2:
            return "*" * len(word)
        return word[0] + "*" * (len(word) - 2) + word[-1]

    def check_content(self, text: str) -> tuple[bool, list[str]]:
        """
        Check if content passes rating requirements.

        Returns:
            Tuple of (passes, list of violations)
        """
        violations = []

        for pattern, category in self._blocked_patterns:
            if pattern.search(text):
                violations.append(category)

        return len(violations) == 0, violations

    def get_system_prompt_additions(self) -> str:
        """
        Generate system prompt additions for LLM based on rating.

        Returns guidance text to include in system prompts to help
        the LLM generate rating-appropriate content.
        """
        lines = [
            f"Content Rating: {self.profile.name} ({self.profile.code})",
            f"Description: {self.profile.description}",
            "",
            "Content Guidelines:",
        ]

        # Violence guidelines
        if not self.profile.allow_graphic_violence:
            lines.append("- Keep violence abstract and non-graphic")
        if not self.profile.allow_gore:
            lines.append("- No gore, blood descriptions, or graphic injury details")
        if not self.profile.allow_torture_descriptions:
            lines.append("- No torture or extended suffering descriptions")

        # Language guidelines
        if not self.profile.allow_mild_profanity:
            lines.append("- No profanity of any kind")
        elif not self.profile.allow_strong_profanity:
            lines.append("- Mild profanity only (damn, hell); no strong profanity")

        # Horror guidelines
        if not self.profile.allow_mild_horror:
            lines.append("- No scary or horror content")
        elif not self.profile.allow_intense_horror:
            lines.append("- Mild suspense only; no intense horror or terror")
        if not self.profile.allow_body_horror:
            lines.append("- No body horror or grotesque transformations")

        # Mature content guidelines
        if not self.profile.allow_suggestive_content:
            lines.append("- No suggestive or romantic content beyond mild tension")
        elif not self.profile.allow_explicit_content:
            lines.append("- Romance can be implied but never explicit")

        # Substance guidelines
        if not self.profile.allow_alcohol_tobacco:
            lines.append("- No references to alcohol or tobacco use")
        if not self.profile.allow_drug_references:
            lines.append("- No drug references or substance abuse")

        # Dark themes
        if not self.profile.allow_suicide_references:
            lines.append("- No references to suicide or self-harm")
        if not self.profile.allow_abuse_references:
            lines.append("- No references to abuse")

        return "\n".join(lines)


def create_filter_for_campaign(campaign) -> ContentFilter:
    """
    Create a ContentFilter for a specific campaign.

    Args:
        campaign: Campaign model instance

    Returns:
        ContentFilter configured for the campaign's rating
    """
    return ContentFilter(campaign.content_rating)
