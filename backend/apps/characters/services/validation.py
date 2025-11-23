"""
Character validation service for SRD 5.2 rule enforcement.

This service validates character data against SRD rules and homebrew content
from the universe catalog. It provides comprehensive validation for:
- Basic character info (species, class, background existence)
- Ability scores (valid ranges, standard array/point buy)
- Skills (valid skill names, proficiency limits)
- Spells (class access, level requirements)
- Equipment (item existence in catalog)
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from apps.srd.models import CharacterClass, Skill, Subclass

if TYPE_CHECKING:
    from apps.characters.models import CharacterSheet
    from apps.universes.models import Universe


@dataclass
class ValidationError:
    """A single validation error."""

    field: str
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of character validation."""

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def add_error(
        self,
        field: str,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Add a validation error."""
        self.errors.append(
            ValidationError(
                field=field,
                code=code,
                message=message,
                details=details or {},
            )
        )
        self.is_valid = False

    def add_warning(
        self,
        field: str,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Add a validation warning (doesn't fail validation)."""
        self.warnings.append(
            ValidationError(
                field=field,
                code=code,
                message=message,
                details=details or {},
            )
        )

    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False


# SRD 5.2 ability score constraints
ABILITY_SCORE_MIN = 1
ABILITY_SCORE_MAX = 30
ABILITY_SCORE_NAMES = ["str", "dex", "con", "int", "wis", "cha"]

# Standard array values (SRD 5.2)
STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

# Point buy constraints (SRD 5.2)
POINT_BUY_MIN = 8
POINT_BUY_MAX = 15
POINT_BUY_TOTAL = 27
POINT_BUY_COSTS = {
    8: 0,
    9: 1,
    10: 2,
    11: 3,
    12: 4,
    13: 5,
    14: 7,
    15: 9,
}

# Spell slot progression for full casters (SRD 5.2)
FULL_CASTER_SPELL_SLOTS = {
    1: {1: 2},
    2: {1: 3},
    3: {1: 4, 2: 2},
    4: {1: 4, 2: 3},
    5: {1: 4, 2: 3, 3: 2},
    6: {1: 4, 2: 3, 3: 3},
    7: {1: 4, 2: 3, 3: 3, 4: 1},
    8: {1: 4, 2: 3, 3: 3, 4: 2},
    9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
    10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
    11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
    12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
    13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
    14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
    15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
    16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
    17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
    18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
    19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
    20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},
}

# Full caster classes
FULL_CASTER_CLASSES = ["Bard", "Cleric", "Druid", "Sorcerer", "Wizard"]

# Half caster classes (get spells at level 2)
HALF_CASTER_CLASSES = ["Paladin", "Ranger"]

# Subclass levels by class
SUBCLASS_LEVELS = {
    "Barbarian": 3,
    "Bard": 3,
    "Cleric": 1,
    "Druid": 2,
    "Fighter": 3,
    "Monk": 3,
    "Paladin": 3,
    "Ranger": 3,
    "Rogue": 3,
    "Sorcerer": 1,
    "Warlock": 1,
    "Wizard": 2,
}


class CharacterValidationService:
    """
    Service for validating character sheets against SRD 5.2 rules.

    This service can validate characters with or without a universe context.
    When a universe is provided, homebrew content from that universe is also
    considered valid.

    Example:
        >>> from apps.characters.services import CharacterValidationService
        >>> validator = CharacterValidationService(universe=my_universe)
        >>> result = validator.validate(character_sheet)
        >>> if not result.is_valid:
        ...     for error in result.errors:
        ...         print(f"{error.field}: {error.message}")
    """

    def __init__(self, universe: "Universe | None" = None):
        """
        Initialize the validation service.

        Args:
            universe: Optional universe for homebrew content validation.
                     If None, only SRD content is considered valid.
        """
        self.universe = universe
        self._catalog = None

    @property
    def catalog(self):
        """Lazy-load the catalog service if universe is provided."""
        if self._catalog is None and self.universe is not None:
            from apps.universes.services.catalog import CatalogService

            self._catalog = CatalogService(self.universe)
        return self._catalog

    def validate(
        self,
        character: "CharacterSheet",
        *,
        validate_spells: bool = True,
        validate_equipment: bool = True,
        strict_ability_scores: bool = False,
    ) -> ValidationResult:
        """
        Perform full validation on a character sheet.

        Args:
            character: The CharacterSheet to validate
            validate_spells: Whether to validate spellbook contents
            validate_equipment: Whether to validate equipment items
            strict_ability_scores: Enforce standard array or point buy

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(is_valid=True)

        # Validate basic info
        result.merge(self.validate_basic_info(character))

        # Validate ability scores
        result.merge(
            self.validate_ability_scores(
                character.ability_scores_json,
                strict=strict_ability_scores,
            )
        )

        # Validate level
        result.merge(self.validate_level(character))

        # Validate skills
        result.merge(self.validate_skills(character.skills_json))

        # Validate subclass if present
        if character.subclass:
            result.merge(
                self.validate_subclass(
                    character.character_class,
                    character.subclass,
                    character.level,
                )
            )

        # Validate spells if requested
        if validate_spells and character.spellbook_json:
            result.merge(
                self.validate_spellbook(
                    character.spellbook_json,
                    character.character_class,
                    character.level,
                )
            )

        # Validate equipment if requested
        if validate_equipment and character.equipment_json:
            result.merge(self.validate_equipment(character.equipment_json))

        return result

    def validate_basic_info(self, character: "CharacterSheet") -> ValidationResult:
        """
        Validate basic character info (species, class, background).

        Checks that these values exist in either SRD or homebrew catalog.
        """
        result = ValidationResult(is_valid=True)

        # Validate species
        if not self._species_exists(character.species):
            result.add_error(
                field="species",
                code="invalid_species",
                message=f"Species '{character.species}' not found in SRD or homebrew catalog",
                details={"species": character.species},
            )

        # Validate class
        if not self._class_exists(character.character_class):
            result.add_error(
                field="character_class",
                code="invalid_class",
                message=f"Class '{character.character_class}' not found in SRD or homebrew catalog",
                details={"class": character.character_class},
            )

        # Validate background
        if not self._background_exists(character.background):
            result.add_error(
                field="background",
                code="invalid_background",
                message=f"Background '{character.background}' not found in SRD or homebrew catalog",
                details={"background": character.background},
            )

        return result

    def validate_ability_scores(
        self,
        ability_scores: dict[str, int],
        *,
        strict: bool = False,
    ) -> ValidationResult:
        """
        Validate ability scores.

        Args:
            ability_scores: Dict of ability abbreviations to scores
            strict: If True, enforce standard array or point buy

        Returns:
            ValidationResult with any errors
        """
        result = ValidationResult(is_valid=True)

        if not ability_scores:
            result.add_error(
                field="ability_scores_json",
                code="missing_ability_scores",
                message="Ability scores are required",
            )
            return result

        # Check all abilities are present
        for ability in ABILITY_SCORE_NAMES:
            if ability not in ability_scores:
                result.add_error(
                    field="ability_scores_json",
                    code="missing_ability",
                    message=f"Missing ability score: {ability.upper()}",
                    details={"ability": ability},
                )

        # Check score ranges
        for ability, score in ability_scores.items():
            if ability.lower() not in ABILITY_SCORE_NAMES:
                result.add_warning(
                    field="ability_scores_json",
                    code="unknown_ability",
                    message=f"Unknown ability score: {ability}",
                    details={"ability": ability},
                )
                continue

            if not isinstance(score, int):
                result.add_error(
                    field="ability_scores_json",
                    code="invalid_score_type",
                    message=f"Ability score for {ability.upper()} must be an integer",
                    details={"ability": ability, "value": score},
                )
            elif score < ABILITY_SCORE_MIN or score > ABILITY_SCORE_MAX:
                result.add_error(
                    field="ability_scores_json",
                    code="score_out_of_range",
                    message=f"Ability score for {ability.upper()} must be between "
                    f"{ABILITY_SCORE_MIN} and {ABILITY_SCORE_MAX}",
                    details={"ability": ability, "score": score},
                )

        # Strict mode: validate against standard array or point buy
        if strict and result.is_valid:
            scores = [ability_scores.get(a, 0) for a in ABILITY_SCORE_NAMES]

            # Check if matches standard array
            is_standard_array = sorted(scores) == sorted(STANDARD_ARRAY)

            # Check if valid point buy
            is_valid_point_buy = self._is_valid_point_buy(scores)

            if not is_standard_array and not is_valid_point_buy:
                result.add_warning(
                    field="ability_scores_json",
                    code="non_standard_scores",
                    message="Ability scores don't match standard array or point buy",
                    details={
                        "scores": ability_scores,
                        "standard_array": STANDARD_ARRAY,
                        "point_buy_range": f"{POINT_BUY_MIN}-{POINT_BUY_MAX}",
                    },
                )

        return result

    def _is_valid_point_buy(self, scores: list[int]) -> bool:
        """Check if scores could be from point buy system."""
        # All scores must be in point buy range
        for score in scores:
            if score < POINT_BUY_MIN or score > POINT_BUY_MAX:
                return False

        # Check total points
        total_points = sum(POINT_BUY_COSTS.get(s, 100) for s in scores)
        return total_points == POINT_BUY_TOTAL

    def validate_level(self, character: "CharacterSheet") -> ValidationResult:
        """Validate character level is in valid range."""
        result = ValidationResult(is_valid=True)

        if character.level < 1:
            result.add_error(
                field="level",
                code="level_too_low",
                message="Character level must be at least 1",
                details={"level": character.level},
            )
        elif character.level > 20:
            result.add_error(
                field="level",
                code="level_too_high",
                message="Character level cannot exceed 20",
                details={"level": character.level},
            )

        # Validate multiclass levels if present
        if character.multiclass_json:
            total_levels = sum(character.multiclass_json.values())
            if total_levels != character.level:
                result.add_error(
                    field="multiclass_json",
                    code="multiclass_level_mismatch",
                    message="Sum of multiclass levels must equal total level",
                    details={
                        "total_level": character.level,
                        "multiclass_sum": total_levels,
                        "multiclass": character.multiclass_json,
                    },
                )

            # Check each class exists
            for class_name in character.multiclass_json:
                if not self._class_exists(class_name):
                    result.add_error(
                        field="multiclass_json",
                        code="invalid_multiclass",
                        message=f"Multiclass '{class_name}' not found in catalog",
                        details={"class": class_name},
                    )

        return result

    def validate_skills(self, skills_json: dict[str, dict]) -> ValidationResult:
        """
        Validate skill proficiencies.

        Args:
            skills_json: Dict of skill names to proficiency info

        Returns:
            ValidationResult with any errors
        """
        result = ValidationResult(is_valid=True)

        # Get valid skill names from SRD
        valid_skills = set(Skill.objects.values_list("name", flat=True))
        valid_skills_lower = {s.lower() for s in valid_skills}

        for skill_name, skill_info in skills_json.items():
            # Check skill exists
            if skill_name.lower() not in valid_skills_lower:
                result.add_warning(
                    field="skills_json",
                    code="unknown_skill",
                    message=f"Unknown skill: {skill_name}",
                    details={"skill": skill_name},
                )

            # Validate skill info structure
            if not isinstance(skill_info, dict):
                result.add_error(
                    field="skills_json",
                    code="invalid_skill_info",
                    message=f"Skill info for '{skill_name}' must be a dictionary",
                    details={"skill": skill_name, "value": skill_info},
                )
            elif "proficient" not in skill_info:
                result.add_warning(
                    field="skills_json",
                    code="missing_proficient_flag",
                    message=f"Skill '{skill_name}' missing 'proficient' flag",
                    details={"skill": skill_name},
                )

            # Check expertise requires proficiency
            if (
                isinstance(skill_info, dict)
                and skill_info.get("expertise")
                and not skill_info.get("proficient")
            ):
                result.add_error(
                    field="skills_json",
                    code="expertise_without_proficiency",
                    message=f"Skill '{skill_name}' has expertise but not proficiency",
                    details={"skill": skill_name},
                )

        return result

    def validate_subclass(
        self,
        class_name: str,
        subclass_name: str,
        level: int,
    ) -> ValidationResult:
        """
        Validate subclass selection.

        Args:
            class_name: The character's primary class
            subclass_name: The selected subclass name
            level: The character's level

        Returns:
            ValidationResult with any errors
        """
        result = ValidationResult(is_valid=True)

        # Check if class can have a subclass at this level
        subclass_level = SUBCLASS_LEVELS.get(class_name, 3)
        if level < subclass_level:
            result.add_warning(
                field="subclass",
                code="subclass_level_requirement",
                message=f"{class_name} doesn't get a subclass until level {subclass_level}",
                details={
                    "class": class_name,
                    "subclass": subclass_name,
                    "current_level": level,
                    "subclass_level": subclass_level,
                },
            )

        # Check subclass exists and belongs to class
        if not self._subclass_exists(subclass_name, class_name):
            result.add_error(
                field="subclass",
                code="invalid_subclass",
                message=f"Subclass '{subclass_name}' not found for class '{class_name}'",
                details={"class": class_name, "subclass": subclass_name},
            )

        return result

    def validate_spellbook(
        self,
        spellbook: dict,
        class_name: str,
        level: int,
    ) -> ValidationResult:
        """
        Validate spellbook contents.

        Args:
            spellbook: The spellbook_json from character
            class_name: The character's primary class
            level: The character's level

        Returns:
            ValidationResult with any errors
        """
        result = ValidationResult(is_valid=True)

        # Check spellcasting ability is valid
        spellcasting_ability = spellbook.get("spellcasting_ability")
        if spellcasting_ability and spellcasting_ability.lower() not in ABILITY_SCORE_NAMES:
            result.add_error(
                field="spellbook_json.spellcasting_ability",
                code="invalid_spellcasting_ability",
                message=f"Invalid spellcasting ability: {spellcasting_ability}",
                details={"ability": spellcasting_ability},
            )

        # Check spell slots
        spell_slots = spellbook.get("spell_slots", {})
        for slot_level, slot_info in spell_slots.items():
            try:
                slot_level_int = int(slot_level)
                if slot_level_int < 1 or slot_level_int > 9:
                    result.add_error(
                        field="spellbook_json.spell_slots",
                        code="invalid_slot_level",
                        message=f"Invalid spell slot level: {slot_level}",
                        details={"level": slot_level},
                    )
            except (ValueError, TypeError):
                result.add_error(
                    field="spellbook_json.spell_slots",
                    code="invalid_slot_level_type",
                    message=f"Spell slot level must be a number: {slot_level}",
                    details={"level": slot_level},
                )

            # Check used doesn't exceed max
            if isinstance(slot_info, dict):
                max_slots = slot_info.get("max", 0)
                used_slots = slot_info.get("used", 0)
                if used_slots > max_slots:
                    result.add_error(
                        field="spellbook_json.spell_slots",
                        code="slots_overused",
                        message=f"Level {slot_level} slots used ({used_slots}) exceeds max ({max_slots})",
                        details={
                            "level": slot_level,
                            "max": max_slots,
                            "used": used_slots,
                        },
                    )

        # Check max spell level for class/level
        max_spell_level = self._get_max_spell_level(class_name, level)
        for slot_level_str in spell_slots:
            try:
                slot_level = int(slot_level_str)
                if slot_level > max_spell_level:
                    result.add_warning(
                        field="spellbook_json.spell_slots",
                        code="spell_level_too_high",
                        message=f"Level {slot_level} spells not available for level {level} {class_name}",
                        details={
                            "slot_level": slot_level,
                            "max_spell_level": max_spell_level,
                            "class": class_name,
                            "character_level": level,
                        },
                    )
            except (ValueError, TypeError):
                pass

        # Validate known spells exist in catalog
        spells_known = spellbook.get("spells_known", [])
        for spell_name in spells_known:
            if not self._spell_exists(spell_name):
                result.add_warning(
                    field="spellbook_json.spells_known",
                    code="unknown_spell",
                    message=f"Spell '{spell_name}' not found in catalog",
                    details={"spell": spell_name},
                )

        return result

    def _get_max_spell_level(self, class_name: str, level: int) -> int:
        """Get the maximum spell level available for a class at a given level."""
        if class_name in FULL_CASTER_CLASSES:
            slots = FULL_CASTER_SPELL_SLOTS.get(level, {})
            if slots:
                return max(int(k) for k in slots)
            return 0
        elif class_name in HALF_CASTER_CLASSES:
            # Half casters get spells at level 2
            if level < 2:
                return 0
            # Approximate: half casters progress at half rate
            effective_level = (level + 1) // 2
            slots = FULL_CASTER_SPELL_SLOTS.get(effective_level, {})
            if slots:
                return max(int(k) for k in slots)
            return 0
        # Other classes (Fighter, Rogue subclasses) - varies
        return 4  # Default to max 4th level spells

    def validate_equipment(self, equipment: dict) -> ValidationResult:
        """
        Validate equipment items exist in catalog.

        Args:
            equipment: The equipment_json from character

        Returns:
            ValidationResult with any errors
        """
        result = ValidationResult(is_valid=True)

        inventory = equipment.get("inventory", [])
        for item_entry in inventory:
            if not isinstance(item_entry, dict):
                continue

            item_name = item_entry.get("name")
            if item_name and not self._item_exists(item_name):
                result.add_warning(
                    field="equipment_json.inventory",
                    code="unknown_item",
                    message=f"Item '{item_name}' not found in catalog",
                    details={"item": item_name},
                )

        return result

    # ==================== Catalog Lookups ====================

    def _species_exists(self, name: str) -> bool:
        """Check if species exists in SRD or homebrew catalog."""
        from apps.srd.models import Species

        if Species.objects.filter(name__iexact=name).exists():
            return True

        if self.catalog:
            entry = self.catalog.get_species_by_name(name)
            return entry is not None

        return False

    def _class_exists(self, name: str) -> bool:
        """Check if class exists in SRD or homebrew catalog."""
        if CharacterClass.objects.filter(name__iexact=name).exists():
            return True

        if self.catalog:
            entry = self.catalog.get_class_by_name(name)
            return entry is not None

        return False

    def _background_exists(self, name: str) -> bool:
        """Check if background exists in SRD or homebrew catalog."""
        from apps.srd.models import Background

        if Background.objects.filter(name__iexact=name).exists():
            return True

        if self.catalog:
            entry = self.catalog.get_background_by_name(name)
            return entry is not None

        return False

    def _subclass_exists(self, name: str, class_name: str) -> bool:
        """Check if subclass exists and belongs to the class."""
        if Subclass.objects.filter(
            name__iexact=name,
            character_class__name__iexact=class_name,
        ).exists():
            return True

        if self.catalog:
            entry = self.catalog.get_subclass_by_name(name, class_name)
            return entry is not None

        return False

    def _spell_exists(self, name: str) -> bool:
        """Check if spell exists in SRD or homebrew catalog."""
        from apps.srd.models import Spell

        if Spell.objects.filter(name__iexact=name).exists():
            return True

        if self.catalog:
            entry = self.catalog.get_spell_by_name(name)
            return entry is not None

        return False

    def _item_exists(self, name: str) -> bool:
        """Check if item exists in SRD or homebrew catalog."""
        from apps.srd.models import Item

        if Item.objects.filter(name__iexact=name).exists():
            return True

        if self.catalog:
            entry = self.catalog.get_item_by_name(name)
            return entry is not None

        return False
