"""
Character Leveling Service.

Handles SRD 5.2 leveling mechanics including:
- XP thresholds for level progression
- Hit point calculations
- Proficiency bonus by level
- Ability Score Improvements
- Feature unlocks by level
"""

import random
from dataclasses import dataclass

from apps.characters.models import CharacterSheet
from apps.srd.models import CharacterClass

# SRD 5.2 Experience Point thresholds for each level
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

# Proficiency bonus by level
PROFICIENCY_BONUS = {
    1: 2,
    2: 2,
    3: 2,
    4: 2,
    5: 3,
    6: 3,
    7: 3,
    8: 3,
    9: 4,
    10: 4,
    11: 4,
    12: 4,
    13: 5,
    14: 5,
    15: 5,
    16: 5,
    17: 6,
    18: 6,
    19: 6,
    20: 6,
}

# Levels at which Ability Score Improvements are granted (standard classes)
ASI_LEVELS = {4, 8, 12, 16, 19}

# Fighter gets extra ASIs
FIGHTER_ASI_LEVELS = {4, 6, 8, 12, 14, 16, 19}

# Rogue gets an extra ASI
ROGUE_ASI_LEVELS = {4, 8, 10, 12, 16, 19}


@dataclass
class LevelUpResult:
    """Result of a level-up operation."""

    success: bool
    new_level: int
    hp_increase: int
    proficiency_bonus: int
    features_gained: list[str]
    can_select_asi: bool
    can_select_subclass: bool
    errors: list[str]
    messages: list[str]


@dataclass
class HitPointCalculation:
    """Hit point calculation result."""

    hit_die: int
    constitution_modifier: int
    roll_result: int | None  # None if using average
    total: int
    used_average: bool


class LevelingService:
    """
    Service for handling character leveling mechanics.

    Based on SRD 5.2 rules for character advancement.
    """

    def get_level_for_xp(self, xp: int) -> int:
        """
        Get the character level for a given XP total.

        Args:
            xp: Total experience points

        Returns:
            Character level (1-20)
        """
        level = 1
        for lvl, threshold in sorted(XP_THRESHOLDS.items()):
            if xp >= threshold:
                level = lvl
            else:
                break
        return min(level, 20)

    def get_xp_for_level(self, level: int) -> int:
        """
        Get the XP required to reach a specific level.

        Args:
            level: Target level (1-20)

        Returns:
            XP threshold for that level
        """
        return XP_THRESHOLDS.get(level, 0)

    def get_xp_to_next_level(self, current_level: int, current_xp: int) -> int | None:
        """
        Get XP needed to reach the next level.

        Args:
            current_level: Current character level
            current_xp: Current XP total

        Returns:
            XP needed, or None if at max level
        """
        if current_level >= 20:
            return None
        next_threshold = XP_THRESHOLDS.get(current_level + 1, 0)
        return max(0, next_threshold - current_xp)

    def get_proficiency_bonus(self, level: int) -> int:
        """
        Get proficiency bonus for a given level.

        Args:
            level: Character level (1-20)

        Returns:
            Proficiency bonus value
        """
        return PROFICIENCY_BONUS.get(min(max(level, 1), 20), 2)

    def calculate_ability_modifier(self, score: int) -> int:
        """
        Calculate ability modifier from ability score.

        Args:
            score: Ability score (1-30)

        Returns:
            Ability modifier
        """
        return (score - 10) // 2

    def calculate_hp_increase(
        self,
        hit_die: int,
        constitution_modifier: int,
        use_average: bool = True,
        seed: int | None = None,
    ) -> HitPointCalculation:
        """
        Calculate HP increase for leveling up.

        Args:
            hit_die: Size of hit die (d6, d8, d10, d12)
            constitution_modifier: CON modifier to add
            use_average: If True, use average roll; if False, roll die
            seed: Optional RNG seed for deterministic rolling

        Returns:
            HitPointCalculation with details
        """
        if use_average:
            # SRD average is (die / 2) + 1, rounded up for odd dice
            die_average = (hit_die // 2) + 1
            roll_result = None
        else:
            if seed is not None:
                random.seed(seed)
            roll_result = random.randint(1, hit_die)
            die_average = roll_result

        # Minimum HP gain is 1, even with negative CON modifier
        total = max(1, die_average + constitution_modifier)

        return HitPointCalculation(
            hit_die=hit_die,
            constitution_modifier=constitution_modifier,
            roll_result=roll_result,
            total=total,
            used_average=use_average,
        )

    def can_level_up(self, character: CharacterSheet, new_xp: int) -> bool:
        """
        Check if character can level up with given XP.

        Args:
            character: Character to check
            new_xp: New XP total

        Returns:
            True if character can level up
        """
        if character.level >= 20:
            return False
        next_level_xp = XP_THRESHOLDS.get(character.level + 1, float("inf"))
        return new_xp >= next_level_xp

    def get_asi_levels_for_class(self, class_name: str) -> set[int]:
        """
        Get levels at which a class gets Ability Score Improvements.

        Args:
            class_name: Character class name

        Returns:
            Set of levels with ASI
        """
        class_lower = class_name.lower()
        if class_lower == "fighter":
            return FIGHTER_ASI_LEVELS
        elif class_lower == "rogue":
            return ROGUE_ASI_LEVELS
        else:
            return ASI_LEVELS

    def get_subclass_level_for_class(self, class_name: str) -> int:
        """
        Get the level at which a class chooses its subclass.

        Args:
            class_name: Character class name

        Returns:
            Level at which subclass is chosen
        """
        # Most classes choose at level 3, but some vary
        special_subclass_levels = {
            "cleric": 1,  # Divine Domain at level 1
            "sorcerer": 1,  # Sorcerous Origin at level 1
            "warlock": 1,  # Otherworldly Patron at level 1
            "wizard": 2,  # Arcane Tradition at level 2
        }
        return special_subclass_levels.get(class_name.lower(), 3)

    def level_up(
        self,
        character: CharacterSheet,
        use_average_hp: bool = True,
        hp_roll_seed: int | None = None,
    ) -> LevelUpResult:
        """
        Process a level-up for a character.

        Args:
            character: Character to level up
            use_average_hp: If True, use average HP; if False, roll
            hp_roll_seed: Optional seed for deterministic HP roll

        Returns:
            LevelUpResult with all level-up information
        """
        errors = []
        messages = []

        # Check if can level up
        if character.level >= 20:
            return LevelUpResult(
                success=False,
                new_level=character.level,
                hp_increase=0,
                proficiency_bonus=self.get_proficiency_bonus(character.level),
                features_gained=[],
                can_select_asi=False,
                can_select_subclass=False,
                errors=["Character is already at maximum level (20)"],
                messages=[],
            )

        new_level = character.level + 1

        # Get class info for hit die
        hit_die = self._get_hit_die_for_class(character.character_class)

        # Calculate CON modifier
        con_score = character.ability_scores_json.get("con", 10)
        con_modifier = self.calculate_ability_modifier(con_score)

        # Calculate HP increase
        hp_calc = self.calculate_hp_increase(
            hit_die=hit_die,
            constitution_modifier=con_modifier,
            use_average=use_average_hp,
            seed=hp_roll_seed,
        )

        if hp_calc.used_average:
            messages.append(
                f"HP increased by {hp_calc.total} (average {hit_die // 2 + 1} + {con_modifier} CON)"
            )
        else:
            messages.append(
                f"HP increased by {hp_calc.total} (rolled {hp_calc.roll_result} + {con_modifier} CON)"
            )

        # Check for proficiency bonus increase
        old_prof = self.get_proficiency_bonus(character.level)
        new_prof = self.get_proficiency_bonus(new_level)
        if new_prof > old_prof:
            messages.append(f"Proficiency bonus increased to +{new_prof}")

        # Check for ASI
        asi_levels = self.get_asi_levels_for_class(character.character_class)
        can_select_asi = new_level in asi_levels
        if can_select_asi:
            messages.append(
                "Ability Score Improvement available! "
                "Increase one ability by 2, or two abilities by 1 each, "
                "or select a feat."
            )

        # Check for subclass selection
        subclass_level = self.get_subclass_level_for_class(character.character_class)
        can_select_subclass = new_level == subclass_level and not character.subclass
        if can_select_subclass:
            messages.append(
                f"Subclass selection available for {character.character_class}!"
            )

        # Get features gained at this level
        features_gained = self._get_features_for_level(
            character.character_class, new_level
        )
        if features_gained:
            messages.append(f"New features: {', '.join(features_gained)}")

        return LevelUpResult(
            success=True,
            new_level=new_level,
            hp_increase=hp_calc.total,
            proficiency_bonus=new_prof,
            features_gained=features_gained,
            can_select_asi=can_select_asi,
            can_select_subclass=can_select_subclass,
            errors=errors,
            messages=messages,
        )

    def apply_level_up(
        self,
        character: CharacterSheet,
        use_average_hp: bool = True,
        hp_roll_seed: int | None = None,
    ) -> LevelUpResult:
        """
        Apply level-up to character and save.

        Args:
            character: Character to level up
            use_average_hp: If True, use average HP; if False, roll
            hp_roll_seed: Optional seed for deterministic HP roll

        Returns:
            LevelUpResult with all level-up information
        """
        result = self.level_up(
            character,
            use_average_hp=use_average_hp,
            hp_roll_seed=hp_roll_seed,
        )

        if result.success:
            # Update character level
            character.level = result.new_level

            # Update features if we track them in features_json
            if result.features_gained:
                features = character.features_json.copy()
                for feature in result.features_gained:
                    # Add feature with basic structure
                    feature_key = feature.lower().replace(" ", "_").replace("'", "")
                    if feature_key not in features:
                        features[feature_key] = {
                            "name": feature,
                            "level_gained": result.new_level,
                        }
                character.features_json = features

            character.save()

        return result

    def _get_hit_die_for_class(self, class_name: str) -> int:
        """Get hit die size for a class."""
        # Try to get from database first
        srd_class = CharacterClass.objects.filter(name__iexact=class_name).first()
        if srd_class:
            return srd_class.hit_die

        # Fallback to known values
        hit_dice = {
            "barbarian": 12,
            "fighter": 10,
            "paladin": 10,
            "ranger": 10,
            "bard": 8,
            "cleric": 8,
            "druid": 8,
            "monk": 8,
            "rogue": 8,
            "warlock": 8,
            "sorcerer": 6,
            "wizard": 6,
        }
        return hit_dice.get(class_name.lower(), 8)  # Default to d8

    def _get_features_for_level(self, class_name: str, level: int) -> list[str]:
        """
        Get class features gained at a specific level.

        This is a simplified implementation. In a full system,
        this would query the SRD database for class features.
        """
        # Try to get from database
        srd_class = CharacterClass.objects.filter(name__iexact=class_name).first()
        if srd_class and srd_class.features:
            features_at_level = []
            for feature in srd_class.features:
                if isinstance(feature, dict) and feature.get("level") == level:
                    features_at_level.append(feature.get("name", "Unknown Feature"))
            return features_at_level

        # Fallback: return empty list (features not loaded)
        return []

    def get_level_summary(self, level: int, class_name: str) -> dict:
        """
        Get a summary of what a character has at a given level.

        Args:
            level: Character level
            class_name: Character class name

        Returns:
            Dict with level summary information
        """
        return {
            "level": level,
            "proficiency_bonus": self.get_proficiency_bonus(level),
            "xp_required": self.get_xp_for_level(level),
            "xp_to_next": (
                self.get_xp_for_level(level + 1) - self.get_xp_for_level(level)
                if level < 20
                else None
            ),
            "hit_die": f"d{self._get_hit_die_for_class(class_name)}",
            "asi_levels_remaining": [
                lvl
                for lvl in self.get_asi_levels_for_class(class_name)
                if lvl > level
            ],
            "next_asi_level": next(
                (
                    lvl
                    for lvl in sorted(self.get_asi_levels_for_class(class_name))
                    if lvl > level
                ),
                None,
            ),
        }
