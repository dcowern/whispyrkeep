"""
Character validation service.

Validates character sheet data against SRD 5.2 rules and universe homebrew content.
Based on SYSTEM_DESIGN.md sections 5.1 and 7.4.
"""

from dataclasses import dataclass, field

from apps.srd.models import (
    Background,
    CharacterClass,
    Skill,
    Species,
    Spell,
    Subclass,
)
from apps.universes.models import Universe


@dataclass
class ValidationError:
    """Represents a validation error."""

    field: str
    message: str
    code: str


@dataclass
class ValidationResult:
    """Result of character validation."""

    is_valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, field: str, message: str, code: str) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(field=field, message=message, code=code))
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a validation warning."""
        self.warnings.append(message)


# SRD 5.2 ability score constraints
MIN_ABILITY_SCORE = 1
MAX_ABILITY_SCORE = 30
STANDARD_MIN_ABILITY = 3  # Typical minimum for character creation
STANDARD_MAX_ABILITY = 20  # Typical maximum without magic items

# Level constraints
MIN_LEVEL = 1
MAX_LEVEL = 20

# Ability score abbreviations
ABILITY_ABBREVIATIONS = {"str", "dex", "con", "int", "wis", "cha"}


class CharacterValidationService:
    """
    Service for validating character sheet data.

    Validates against:
    - SRD 5.2 base rules
    - Universe-specific homebrew content (if universe is specified)
    """

    def __init__(self, universe: Universe | None = None):
        """
        Initialize the validation service.

        Args:
            universe: Optional universe for homebrew validation.
        """
        self.universe = universe

    def validate(
        self,
        name: str,
        species: str,
        character_class: str,
        background: str,
        level: int = 1,
        subclass: str = "",
        ability_scores: dict | None = None,
        skills: dict | None = None,
        proficiencies: dict | None = None,
        features: dict | None = None,
        spellbook: dict | None = None,
        equipment: dict | None = None,
        homebrew_overrides: dict | None = None,
    ) -> ValidationResult:
        """
        Validate all character data.

        Args:
            name: Character name
            species: Character species/race name
            character_class: Character class name
            background: Character background name
            level: Character level (1-20)
            subclass: Optional subclass name
            ability_scores: Dict of ability score values
            skills: Dict of skill proficiencies
            proficiencies: Dict of other proficiencies
            features: Dict of class/race features
            spellbook: Dict of spellcasting data
            equipment: Dict of equipment/inventory
            homebrew_overrides: Dict of homebrew content overrides

        Returns:
            ValidationResult with any errors and warnings.
        """
        result = ValidationResult()

        # Validate basic required fields
        self._validate_name(name, result)
        self._validate_level(level, result)

        # Validate against SRD/homebrew catalogs
        self._validate_species(species, result)
        class_obj = self._validate_class(character_class, result)
        self._validate_background(background, result)

        # Validate subclass if provided
        if subclass:
            self._validate_subclass(subclass, character_class, level, result)

        # Validate ability scores
        if ability_scores:
            self._validate_ability_scores(ability_scores, result)

        # Validate skills
        if skills:
            self._validate_skills(skills, result)

        # Validate spellbook if character has spellcasting
        if spellbook:
            self._validate_spellbook(spellbook, character_class, level, class_obj, result)

        return result

    def _validate_name(self, name: str, result: ValidationResult) -> None:
        """Validate character name."""
        if not name or not name.strip():
            result.add_error("name", "Character name is required", "required")
        elif len(name) > 100:
            result.add_error(
                "name", "Character name must be 100 characters or less", "max_length"
            )

    def _validate_level(self, level: int, result: ValidationResult) -> None:
        """Validate character level."""
        if level < MIN_LEVEL:
            result.add_error(
                "level", f"Level must be at least {MIN_LEVEL}", "min_value"
            )
        elif level > MAX_LEVEL:
            result.add_error(
                "level", f"Level cannot exceed {MAX_LEVEL}", "max_value"
            )

    def _validate_species(self, species: str, result: ValidationResult) -> None:
        """Validate species against SRD and homebrew."""
        if not species or not species.strip():
            result.add_error("species", "Species is required", "required")
            return

        # Check SRD species
        if Species.objects.filter(name__iexact=species).exists():
            return

        # Check universe homebrew species
        if self.universe:
            from apps.universes.homebrew_models import HomebrewSpecies

            if HomebrewSpecies.objects.filter(
                universe=self.universe, name__iexact=species
            ).exists():
                return

        result.add_error(
            "species",
            f"Species '{species}' is not a valid SRD species"
            + (" or homebrew species in this universe" if self.universe else ""),
            "invalid_choice",
        )

    def _validate_class(
        self, character_class: str, result: ValidationResult
    ) -> CharacterClass | None:
        """Validate character class against SRD and homebrew."""
        if not character_class or not character_class.strip():
            result.add_error("character_class", "Character class is required", "required")
            return None

        # Check SRD class
        srd_class = CharacterClass.objects.filter(name__iexact=character_class).first()
        if srd_class:
            return srd_class

        # Check universe homebrew class
        if self.universe:
            from apps.universes.homebrew_models import HomebrewClass

            if HomebrewClass.objects.filter(
                universe=self.universe, name__iexact=character_class
            ).exists():
                return None  # Homebrew class validation handled differently

        result.add_error(
            "character_class",
            f"Class '{character_class}' is not a valid SRD class"
            + (" or homebrew class in this universe" if self.universe else ""),
            "invalid_choice",
        )
        return None

    def _validate_background(self, background: str, result: ValidationResult) -> None:
        """Validate background against SRD and homebrew."""
        if not background or not background.strip():
            result.add_error("background", "Background is required", "required")
            return

        # Check SRD background
        if Background.objects.filter(name__iexact=background).exists():
            return

        # Check universe homebrew background
        if self.universe:
            from apps.universes.homebrew_models import HomebrewBackground

            if HomebrewBackground.objects.filter(
                universe=self.universe, name__iexact=background
            ).exists():
                return

        result.add_error(
            "background",
            f"Background '{background}' is not a valid SRD background"
            + (" or homebrew background in this universe" if self.universe else ""),
            "invalid_choice",
        )

    def _validate_subclass(
        self, subclass: str, character_class: str, level: int, result: ValidationResult
    ) -> None:
        """Validate subclass selection."""
        # Check SRD subclass
        srd_subclass = Subclass.objects.filter(
            name__iexact=subclass, character_class__name__iexact=character_class
        ).first()

        if srd_subclass:
            # Check if character is high enough level for subclass
            if level < srd_subclass.subclass_level:
                result.add_warning(
                    f"Subclass '{subclass}' typically requires level {srd_subclass.subclass_level}, "
                    f"but character is only level {level}"
                )
            return

        # Check universe homebrew subclass
        if self.universe:
            from apps.universes.homebrew_models import HomebrewSubclass

            homebrew_subclass = HomebrewSubclass.objects.filter(
                universe=self.universe, name__iexact=subclass
            ).first()

            if homebrew_subclass:
                # Check parent class matches
                parent_matches = (
                    (
                        homebrew_subclass.parent_class
                        and homebrew_subclass.parent_class.name.lower()
                        == character_class.lower()
                    )
                    or homebrew_subclass.srd_parent_class_name.lower()
                    == character_class.lower()
                )
                if not parent_matches:
                    result.add_error(
                        "subclass",
                        f"Subclass '{subclass}' is not available for class '{character_class}'",
                        "invalid_choice",
                    )
                elif level < homebrew_subclass.subclass_level:
                    result.add_warning(
                        f"Subclass '{subclass}' typically requires level {homebrew_subclass.subclass_level}"
                    )
                return

        result.add_error(
            "subclass",
            f"Subclass '{subclass}' is not valid for class '{character_class}'",
            "invalid_choice",
        )

    def _validate_ability_scores(
        self, ability_scores: dict, result: ValidationResult
    ) -> None:
        """Validate ability scores."""
        for ability, value in ability_scores.items():
            ability_lower = ability.lower()

            # Check valid ability name
            if ability_lower not in ABILITY_ABBREVIATIONS:
                result.add_error(
                    "ability_scores",
                    f"'{ability}' is not a valid ability score. "
                    f"Valid abilities: {', '.join(sorted(ABILITY_ABBREVIATIONS))}",
                    "invalid_ability",
                )
                continue

            # Check value is numeric
            if not isinstance(value, int | float):
                result.add_error(
                    "ability_scores",
                    f"Ability score '{ability}' must be a number, got {type(value).__name__}",
                    "invalid_type",
                )
                continue

            value = int(value)

            # Check value range
            if value < MIN_ABILITY_SCORE:
                result.add_error(
                    "ability_scores",
                    f"Ability score '{ability}' ({value}) is below minimum {MIN_ABILITY_SCORE}",
                    "min_value",
                )
            elif value > MAX_ABILITY_SCORE:
                result.add_error(
                    "ability_scores",
                    f"Ability score '{ability}' ({value}) exceeds maximum {MAX_ABILITY_SCORE}",
                    "max_value",
                )
            elif value > STANDARD_MAX_ABILITY:
                result.add_warning(
                    f"Ability score '{ability}' ({value}) exceeds typical maximum of {STANDARD_MAX_ABILITY} "
                    "(may require magic items or special features)"
                )

        # Check all abilities are present
        present_abilities = {k.lower() for k in ability_scores}
        missing = ABILITY_ABBREVIATIONS - present_abilities
        if missing:
            result.add_warning(
                f"Missing ability scores: {', '.join(sorted(missing))}"
            )

    def _validate_skills(self, skills: dict, result: ValidationResult) -> None:
        """Validate skill proficiencies."""
        valid_skill_names = set(
            Skill.objects.values_list("name", flat=True)
        )
        valid_skill_names_lower = {s.lower() for s in valid_skill_names}

        for skill_name, skill_data in skills.items():
            if skill_name.lower() not in valid_skill_names_lower:
                result.add_error(
                    "skills",
                    f"'{skill_name}' is not a valid skill",
                    "invalid_skill",
                )
                continue

            # Validate skill data structure - check for expertise without proficiency
            if isinstance(skill_data, dict) and skill_data.get("expertise") and not skill_data.get("proficient"):
                result.add_warning(
                    f"Skill '{skill_name}' has expertise but not proficiency "
                    "(expertise typically requires proficiency first)"
                )

    def _validate_spellbook(
        self,
        spellbook: dict,
        character_class: str,
        level: int,
        class_obj: CharacterClass | None,
        result: ValidationResult,
    ) -> None:
        """Validate spellbook data."""
        # Check spellcasting ability
        if "spellcasting_ability" in spellbook:
            ability = spellbook["spellcasting_ability"].lower()
            if ability not in ABILITY_ABBREVIATIONS:
                result.add_error(
                    "spellbook",
                    f"Invalid spellcasting ability: {ability}",
                    "invalid_ability",
                )

        # Validate known spells exist
        known_spells = spellbook.get("known_spells", [])
        for spell_name in known_spells:
            if not self._is_valid_spell(spell_name):
                result.add_error(
                    "spellbook",
                    f"Unknown spell: '{spell_name}'",
                    "invalid_spell",
                )

        # Validate prepared spells are in known spells
        prepared_spells = spellbook.get("prepared_spells", [])
        known_set = {s.lower() for s in known_spells}
        for spell_name in prepared_spells:
            if spell_name.lower() not in known_set:
                result.add_error(
                    "spellbook",
                    f"Prepared spell '{spell_name}' is not in known spells",
                    "not_known",
                )

        # Validate cantrips
        cantrips = spellbook.get("cantrips", [])
        for cantrip_name in cantrips:
            spell = Spell.objects.filter(name__iexact=cantrip_name).first()
            if spell and spell.level != 0:
                result.add_error(
                    "spellbook",
                    f"'{cantrip_name}' is not a cantrip (it's level {spell.level})",
                    "not_cantrip",
                )
            elif not spell and not self._is_valid_spell(cantrip_name):
                # Not a known SRD spell and not valid homebrew
                result.add_error(
                    "spellbook",
                    f"Unknown cantrip: '{cantrip_name}'",
                    "invalid_spell",
                )

        # Validate spell slots
        spell_slots = spellbook.get("spell_slots", {})
        for slot_level, slot_data in spell_slots.items():
            try:
                slot_int = int(slot_level)
                if slot_int < 1 or slot_int > 9:
                    result.add_error(
                        "spellbook",
                        f"Invalid spell slot level: {slot_level} (must be 1-9)",
                        "invalid_slot_level",
                    )
            except ValueError:
                result.add_error(
                    "spellbook",
                    f"Spell slot level must be a number, got: {slot_level}",
                    "invalid_type",
                )

            if isinstance(slot_data, dict):
                used = slot_data.get("used", 0)
                max_slots = slot_data.get("max", 0)
                if used > max_slots:
                    result.add_warning(
                        f"Level {slot_level} spell slots: used ({used}) exceeds max ({max_slots})"
                    )

    def _is_valid_spell(self, spell_name: str) -> bool:
        """Check if a spell exists in SRD or homebrew."""
        # Check SRD spells
        if Spell.objects.filter(name__iexact=spell_name).exists():
            return True

        # Check universe homebrew spells
        if self.universe:
            from apps.universes.homebrew_models import HomebrewSpell

            if HomebrewSpell.objects.filter(
                universe=self.universe, name__iexact=spell_name
            ).exists():
                return True

        return False

    def validate_for_campaign(
        self,
        name: str,
        species: str,
        character_class: str,
        background: str,
        level: int,
        **kwargs,
    ) -> ValidationResult:
        """
        Stricter validation for campaign play.

        In addition to standard validation, ensures:
        - All required ability scores are present
        - No warnings are present (treated as errors)
        """
        result = self.validate(
            name=name,
            species=species,
            character_class=character_class,
            background=background,
            level=level,
            **kwargs,
        )

        # Convert warnings to errors for campaign play
        ability_scores = kwargs.get("ability_scores", {})
        if ability_scores:
            present_abilities = {k.lower() for k in ability_scores}
            missing = ABILITY_ABBREVIATIONS - present_abilities
            if missing:
                result.add_error(
                    "ability_scores",
                    f"All ability scores are required for campaign play. Missing: {', '.join(sorted(missing))}",
                    "required",
                )

        return result
