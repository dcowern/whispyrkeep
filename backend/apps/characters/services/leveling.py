"""
Leveling service for SRD 5.2 character progression.

Handles level up mechanics, XP thresholds, hit point calculations,
and multiclass requirements following SRD 5.2 rules.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from apps.srd.models import CharacterClass

if TYPE_CHECKING:
    from apps.characters.models import CharacterSheet


# SRD 5.2 XP thresholds for each level
XP_THRESHOLDS = {
    1: 0,
    2: 300,
    3: 900,
    4: 2700,
    5: 6500,
    6: 14000,
    7: 23000,
    8: 34000,
    9: 48000,
    10: 64000,
    11: 85000,
    12: 100000,
    13: 120000,
    14: 140000,
    15: 165000,
    16: 195000,
    17: 225000,
    18: 265000,
    19: 305000,
    20: 355000,
}

# Hit die by class name (SRD 5.2)
CLASS_HIT_DICE = {
    "Barbarian": 12,
    "Bard": 8,
    "Cleric": 8,
    "Druid": 8,
    "Fighter": 10,
    "Monk": 8,
    "Paladin": 10,
    "Ranger": 10,
    "Rogue": 8,
    "Sorcerer": 6,
    "Warlock": 8,
    "Wizard": 6,
}

# Minimum ability scores for multiclassing (SRD 5.2)
MULTICLASS_REQUIREMENTS = {
    "Barbarian": {"str": 13},
    "Bard": {"cha": 13},
    "Cleric": {"wis": 13},
    "Druid": {"wis": 13},
    "Fighter": {"str": 13},  # or DEX 13
    "Monk": {"dex": 13, "wis": 13},
    "Paladin": {"str": 13, "cha": 13},
    "Ranger": {"dex": 13, "wis": 13},
    "Rogue": {"dex": 13},
    "Sorcerer": {"cha": 13},
    "Warlock": {"cha": 13},
    "Wizard": {"int": 13},
}

# Fighter can multiclass with STR or DEX
FIGHTER_MULTICLASS_ALT = {"dex": 13}


@dataclass
class LevelUpResult:
    """Result of a level up operation."""

    success: bool
    new_level: int
    hp_gained: int
    hit_die_added: str
    message: str
    errors: list[str]


@dataclass
class XPInfo:
    """Information about character's XP status."""

    current_xp: int
    current_level: int
    xp_for_next_level: int
    xp_needed: int
    can_level_up: bool


class LevelingService:
    """
    Service for handling character leveling and progression.

    Provides methods for:
    - Checking level up eligibility
    - Performing level ups
    - XP management
    - Multiclass requirements validation

    Example:
        >>> service = LevelingService()
        >>> xp_info = service.get_xp_info(character)
        >>> if xp_info.can_level_up:
        ...     result = service.level_up(character)
    """

    def get_level_for_xp(self, xp: int) -> int:
        """
        Get the level a character should be at given their XP.

        Args:
            xp: Total experience points

        Returns:
            The level (1-20) the character should be at
        """
        level = 1
        for lvl in range(2, 21):
            if xp >= XP_THRESHOLDS[lvl]:
                level = lvl
            else:
                break
        return level

    def get_xp_for_level(self, level: int) -> int:
        """
        Get the XP required to reach a specific level.

        Args:
            level: Target level (1-20)

        Returns:
            Total XP required
        """
        return XP_THRESHOLDS.get(level, XP_THRESHOLDS[20])

    def get_xp_info(self, character: "CharacterSheet") -> XPInfo:
        """
        Get comprehensive XP information for a character.

        Args:
            character: The character to check

        Returns:
            XPInfo with current status and next level requirements
        """
        current_xp = character.experience_points
        current_level = character.level

        # XP needed for next level
        if current_level >= 20:
            xp_for_next = XP_THRESHOLDS[20]
            xp_needed = 0
            can_level_up = False
        else:
            xp_for_next = XP_THRESHOLDS[current_level + 1]
            xp_needed = max(0, xp_for_next - current_xp)
            can_level_up = current_xp >= xp_for_next

        return XPInfo(
            current_xp=current_xp,
            current_level=current_level,
            xp_for_next_level=xp_for_next,
            xp_needed=xp_needed,
            can_level_up=can_level_up,
        )

    def add_xp(self, character: "CharacterSheet", xp_amount: int) -> XPInfo:
        """
        Add XP to a character.

        Args:
            character: The character to award XP to
            xp_amount: Amount of XP to add

        Returns:
            Updated XPInfo
        """
        character.experience_points += xp_amount
        character.save()
        return self.get_xp_info(character)

    def can_level_up(self, character: "CharacterSheet") -> bool:
        """Check if character has enough XP to level up."""
        if character.level >= 20:
            return False
        return character.experience_points >= XP_THRESHOLDS[character.level + 1]

    def get_hit_die_for_class(self, class_name: str) -> int:
        """
        Get the hit die size for a class.

        Args:
            class_name: Name of the class

        Returns:
            Hit die size (6, 8, 10, or 12)
        """
        # Check local mapping first
        if class_name in CLASS_HIT_DICE:
            return CLASS_HIT_DICE[class_name]

        # Try to get from database for homebrew classes
        try:
            char_class = CharacterClass.objects.get(name__iexact=class_name)
            return char_class.hit_die
        except CharacterClass.DoesNotExist:
            # Default to d8 for unknown classes
            return 8

    def calculate_hp_gain(
        self,
        class_name: str,
        constitution_modifier: int,
        *,
        roll_result: int | None = None,
        use_average: bool = True,
    ) -> int:
        """
        Calculate HP gained on level up.

        Args:
            class_name: Class being leveled
            constitution_modifier: Character's CON modifier
            roll_result: Actual dice roll (if not using average)
            use_average: If True, use fixed average instead of roll

        Returns:
            HP gained (minimum 1)
        """
        hit_die = self.get_hit_die_for_class(class_name)

        if use_average:
            # SRD 5.2 average: (die / 2) + 1
            hp_from_die = (hit_die // 2) + 1
        elif roll_result is not None:
            hp_from_die = roll_result
        else:
            hp_from_die = (hit_die // 2) + 1

        # Total HP gained = die result + CON modifier (minimum 1)
        return max(1, hp_from_die + constitution_modifier)

    def level_up(
        self,
        character: "CharacterSheet",
        class_name: str | None = None,
        *,
        use_average_hp: bool = True,
        hp_roll: int | None = None,
    ) -> LevelUpResult:
        """
        Level up a character.

        Args:
            character: Character to level up
            class_name: Class to gain level in (for multiclass)
                       If None, uses primary class
            use_average_hp: Use average HP instead of rolling
            hp_roll: Actual HP roll result (if not using average)

        Returns:
            LevelUpResult with success status and details
        """
        errors = []

        # Check max level
        if character.level >= 20:
            return LevelUpResult(
                success=False,
                new_level=character.level,
                hp_gained=0,
                hit_die_added="",
                message="Character is already at maximum level (20)",
                errors=["max_level_reached"],
            )

        # Determine class to level
        level_class = class_name or character.character_class

        # Check multiclass requirements if leveling a different class
        if level_class != character.character_class:
            multiclass_errors = self.check_multiclass_requirements(
                character, level_class
            )
            if multiclass_errors:
                errors.extend(multiclass_errors)
                return LevelUpResult(
                    success=False,
                    new_level=character.level,
                    hp_gained=0,
                    hit_die_added="",
                    message=f"Multiclass requirements not met for {level_class}",
                    errors=errors,
                )

        # Calculate HP gain
        con_mod = character.get_ability_modifier("con")
        hp_gained = self.calculate_hp_gain(
            level_class,
            con_mod,
            roll_result=hp_roll,
            use_average=use_average_hp,
        )

        # Get hit die type
        hit_die_size = self.get_hit_die_for_class(level_class)
        hit_die = f"d{hit_die_size}"

        # Update character
        character.level += 1
        character.hit_points_max += hp_gained
        character.hit_points_current += hp_gained  # Gain HP immediately

        # Update multiclass tracking
        if level_class != character.character_class:
            if not character.multiclass_json:
                # First multiclass - initialize with existing class levels
                character.multiclass_json = {character.character_class: character.level - 1}
            multiclass = character.multiclass_json.copy()
            multiclass[level_class] = multiclass.get(level_class, 0) + 1
            character.multiclass_json = multiclass

        # Update hit dice
        hit_dice = character.hit_dice_json.copy() if character.hit_dice_json else {}
        die_key = hit_die
        if die_key in hit_dice:
            hit_dice[die_key]["max"] = hit_dice[die_key].get("max", 0) + 1
        else:
            hit_dice[die_key] = {"max": 1, "spent": 0}
        character.hit_dice_json = hit_dice

        character.save()

        return LevelUpResult(
            success=True,
            new_level=character.level,
            hp_gained=hp_gained,
            hit_die_added=hit_die,
            message=f"Successfully leveled up to {character.level} in {level_class}",
            errors=[],
        )

    def check_multiclass_requirements(
        self,
        character: "CharacterSheet",
        target_class: str,
    ) -> list[str]:
        """
        Check if character meets multiclass requirements.

        Args:
            character: Character attempting to multiclass
            target_class: Class to multiclass into

        Returns:
            List of error messages (empty if requirements met)
        """
        errors = []

        # Get requirements for target class
        requirements = MULTICLASS_REQUIREMENTS.get(target_class, {})

        # Special case: Fighter can use STR or DEX
        if target_class == "Fighter":
            str_score = character.ability_scores_json.get("str", 0)
            dex_score = character.ability_scores_json.get("dex", 0)
            if str_score < 13 and dex_score < 13:
                errors.append(f"{target_class} requires STR 13 or DEX 13")
        else:
            # Check standard requirements
            for ability, min_score in requirements.items():
                actual_score = character.ability_scores_json.get(ability, 0)
                if actual_score < min_score:
                    errors.append(
                        f"{target_class} requires {ability.upper()} {min_score} "
                        f"(you have {actual_score})"
                    )

        # Also check requirements for leaving current class
        current_class = character.character_class
        current_reqs = MULTICLASS_REQUIREMENTS.get(current_class, {})

        if current_class == "Fighter":
            str_score = character.ability_scores_json.get("str", 0)
            dex_score = character.ability_scores_json.get("dex", 0)
            if str_score < 13 and dex_score < 13:
                errors.append(f"To multiclass from {current_class}, need STR 13 or DEX 13")
        else:
            for ability, min_score in current_reqs.items():
                actual_score = character.ability_scores_json.get(ability, 0)
                if actual_score < min_score:
                    errors.append(
                        f"To multiclass from {current_class}, need {ability.upper()} {min_score} "
                        f"(you have {actual_score})"
                    )

        return errors

    def get_proficiency_bonus(self, level: int) -> int:
        """
        Get proficiency bonus for a given level.

        Args:
            level: Character level (1-20)

        Returns:
            Proficiency bonus (+2 to +6)
        """
        return (level - 1) // 4 + 2

    def calculate_first_level_hp(
        self,
        class_name: str,
        constitution_modifier: int,
    ) -> int:
        """
        Calculate starting HP for a first level character.

        At first level, characters get maximum HP:
        hit die max + CON modifier

        Args:
            class_name: Character's class
            constitution_modifier: CON modifier

        Returns:
            Starting HP
        """
        hit_die = self.get_hit_die_for_class(class_name)
        return max(1, hit_die + constitution_modifier)

    def sync_level_with_xp(self, character: "CharacterSheet") -> int:
        """
        Sync character level with their XP.

        This is useful when XP is awarded directly and the level
        should automatically update.

        Args:
            character: Character to sync

        Returns:
            Number of levels gained (can be 0)
        """
        expected_level = self.get_level_for_xp(character.experience_points)
        levels_gained = 0

        while character.level < expected_level:
            result = self.level_up(character)
            if result.success:
                levels_gained += 1
            else:
                break

        return levels_gained
