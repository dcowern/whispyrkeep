"""
Safety and content moderation models.

Implements rating profiles for content filtering (Epic 13).
"""

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True)
class RatingProfile:
    """
    Content guidelines for a specific rating level.

    Defines what content is allowed/forbidden at each rating tier.
    Based on film/TV rating systems with RPG-specific adaptations.
    """

    code: str
    name: str
    description: str

    # Violence settings
    allow_combat_descriptions: bool
    allow_graphic_violence: bool
    allow_gore: bool
    allow_torture_descriptions: bool

    # Language settings
    allow_mild_profanity: bool
    allow_strong_profanity: bool

    # Mature themes
    allow_alcohol_tobacco: bool
    allow_drug_references: bool
    allow_romantic_tension: bool
    allow_suggestive_content: bool
    allow_explicit_content: bool

    # Horror/scary content
    allow_mild_horror: bool
    allow_intense_horror: bool
    allow_body_horror: bool

    # Dark themes
    allow_death_references: bool
    allow_death_descriptions: bool
    allow_suicide_references: bool
    allow_abuse_references: bool

    # Keywords to filter from output
    blocked_keywords: tuple[str, ...] = field(default_factory=tuple)

    # Content warnings to include
    content_warnings_required: bool = False

    # Registry of all profiles
    _registry: ClassVar[dict[str, "RatingProfile"]] = {}

    def __post_init__(self):
        """Register profile in class registry."""
        RatingProfile._registry[self.code] = self

    @classmethod
    def get(cls, code: str) -> "RatingProfile":
        """Get a rating profile by its code."""
        if code not in cls._registry:
            # Default to PG13 if unknown rating
            return cls._registry.get("PG13", list(cls._registry.values())[0])
        return cls._registry[code]

    @classmethod
    def all_profiles(cls) -> list["RatingProfile"]:
        """Return all registered profiles."""
        return list(cls._registry.values())


# Define standard rating profiles
RATING_G = RatingProfile(
    code="G",
    name="General Audiences",
    description="Content suitable for all ages. No violence, profanity, or mature themes.",
    allow_combat_descriptions=True,
    allow_graphic_violence=False,
    allow_gore=False,
    allow_torture_descriptions=False,
    allow_mild_profanity=False,
    allow_strong_profanity=False,
    allow_alcohol_tobacco=False,
    allow_drug_references=False,
    allow_romantic_tension=False,
    allow_suggestive_content=False,
    allow_explicit_content=False,
    allow_mild_horror=False,
    allow_intense_horror=False,
    allow_body_horror=False,
    allow_death_references=True,
    allow_death_descriptions=False,
    allow_suicide_references=False,
    allow_abuse_references=False,
    blocked_keywords=(
        "blood", "gore", "guts", "viscera", "entrails", "dismember",
        "damn", "hell", "bastard", "ass",
    ),
)

RATING_PG = RatingProfile(
    code="PG",
    name="Parental Guidance",
    description="Some content may not be suitable for young children. Mild violence and themes.",
    allow_combat_descriptions=True,
    allow_graphic_violence=False,
    allow_gore=False,
    allow_torture_descriptions=False,
    allow_mild_profanity=True,
    allow_strong_profanity=False,
    allow_alcohol_tobacco=True,
    allow_drug_references=False,
    allow_romantic_tension=True,
    allow_suggestive_content=False,
    allow_explicit_content=False,
    allow_mild_horror=True,
    allow_intense_horror=False,
    allow_body_horror=False,
    allow_death_references=True,
    allow_death_descriptions=True,
    allow_suicide_references=False,
    allow_abuse_references=False,
    blocked_keywords=(
        "gore", "guts", "viscera", "entrails", "dismember",
        "fuck", "shit", "bitch",
    ),
)

RATING_PG13 = RatingProfile(
    code="PG13",
    name="Parents Strongly Cautioned",
    description="Some content may be inappropriate for children under 13. Moderate violence and themes.",
    allow_combat_descriptions=True,
    allow_graphic_violence=True,
    allow_gore=False,
    allow_torture_descriptions=False,
    allow_mild_profanity=True,
    allow_strong_profanity=False,
    allow_alcohol_tobacco=True,
    allow_drug_references=True,
    allow_romantic_tension=True,
    allow_suggestive_content=True,
    allow_explicit_content=False,
    allow_mild_horror=True,
    allow_intense_horror=True,
    allow_body_horror=False,
    allow_death_references=True,
    allow_death_descriptions=True,
    allow_suicide_references=True,
    allow_abuse_references=False,
    blocked_keywords=(
        "viscera", "entrails", "dismember",
        "fuck", "shit",
    ),
    content_warnings_required=True,
)

RATING_R = RatingProfile(
    code="R",
    name="Restricted",
    description="Mature content. Strong violence, language, and adult themes.",
    allow_combat_descriptions=True,
    allow_graphic_violence=True,
    allow_gore=True,
    allow_torture_descriptions=True,
    allow_mild_profanity=True,
    allow_strong_profanity=True,
    allow_alcohol_tobacco=True,
    allow_drug_references=True,
    allow_romantic_tension=True,
    allow_suggestive_content=True,
    allow_explicit_content=False,
    allow_mild_horror=True,
    allow_intense_horror=True,
    allow_body_horror=True,
    allow_death_references=True,
    allow_death_descriptions=True,
    allow_suicide_references=True,
    allow_abuse_references=True,
    blocked_keywords=(),
    content_warnings_required=True,
)

RATING_NC17 = RatingProfile(
    code="NC17",
    name="Adults Only",
    description="No restrictions. All content types allowed.",
    allow_combat_descriptions=True,
    allow_graphic_violence=True,
    allow_gore=True,
    allow_torture_descriptions=True,
    allow_mild_profanity=True,
    allow_strong_profanity=True,
    allow_alcohol_tobacco=True,
    allow_drug_references=True,
    allow_romantic_tension=True,
    allow_suggestive_content=True,
    allow_explicit_content=True,
    allow_mild_horror=True,
    allow_intense_horror=True,
    allow_body_horror=True,
    allow_death_references=True,
    allow_death_descriptions=True,
    allow_suicide_references=True,
    allow_abuse_references=True,
    blocked_keywords=(),
    content_warnings_required=False,
)
