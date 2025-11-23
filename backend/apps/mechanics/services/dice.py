"""
Dice Roller Service.

Provides deterministic dice rolling for SRD 5.2 mechanics.
All rolls can be seeded for reproducibility in testing.

Ticket: 9.0.1

Based on SYSTEM_DESIGN.md section 7.3 Deterministic Functions.
"""

import random
import re
from dataclasses import dataclass, field
from enum import Enum


class AdvantageState(str, Enum):
    """Advantage state for d20 rolls."""

    NONE = "none"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"


@dataclass
class DieRoll:
    """Result of a single die roll."""

    die_size: int
    result: int

    def __post_init__(self):
        if self.die_size < 1:
            raise ValueError(f"Die size must be at least 1, got {self.die_size}")
        if self.result < 1 or self.result > self.die_size:
            raise ValueError(
                f"Result {self.result} is out of range for d{self.die_size}"
            )


@dataclass
class RollResult:
    """Result of a dice roll operation."""

    total: int
    rolls: list[DieRoll] = field(default_factory=list)
    modifier: int = 0
    natural_roll: int | None = None  # For d20 rolls, the actual die result
    advantage_state: AdvantageState = AdvantageState.NONE
    discarded_rolls: list[DieRoll] = field(default_factory=list)
    is_critical: bool = False  # Natural 20 on d20
    is_fumble: bool = False  # Natural 1 on d20

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total": self.total,
            "rolls": [{"die_size": r.die_size, "result": r.result} for r in self.rolls],
            "modifier": self.modifier,
            "natural_roll": self.natural_roll,
            "advantage_state": self.advantage_state.value,
            "discarded_rolls": [
                {"die_size": r.die_size, "result": r.result}
                for r in self.discarded_rolls
            ],
            "is_critical": self.is_critical,
            "is_fumble": self.is_fumble,
        }


@dataclass
class DiceExpression:
    """
    Parsed dice expression like "2d6+3" or "1d20".

    Supports:
    - NdM: Roll N dice of size M (e.g., 2d6)
    - NdM+X: Roll N dice of size M, add X (e.g., 2d6+3)
    - NdM-X: Roll N dice of size M, subtract X (e.g., 2d6-1)
    - Multiple groups: 1d8+2d6+5 (parsed left to right)
    """

    num_dice: int
    die_size: int
    modifier: int = 0

    # Pattern: captures NdM optionally followed by +/-X
    _PATTERN = re.compile(r"^(\d+)d(\d+)(?:([+-])(\d+))?$", re.IGNORECASE)
    _MULTI_PATTERN = re.compile(r"(\d+d\d+|\d+)([+-])?", re.IGNORECASE)

    def __post_init__(self):
        if self.num_dice < 1:
            raise ValueError(f"Number of dice must be at least 1, got {self.num_dice}")
        if self.die_size < 1:
            raise ValueError(f"Die size must be at least 1, got {self.die_size}")

    @classmethod
    def parse(cls, expression: str) -> "DiceExpression":
        """
        Parse a dice expression string.

        Args:
            expression: String like "2d6+3", "1d20", "3d8-2"

        Returns:
            DiceExpression instance

        Raises:
            ValueError: If expression is invalid
        """
        expression = expression.strip().lower()

        # Handle simple expressions first
        match = cls._PATTERN.match(expression)
        if match:
            num_dice = int(match.group(1))
            die_size = int(match.group(2))
            modifier = 0

            if match.group(3) and match.group(4):
                sign = match.group(3)
                mod_value = int(match.group(4))
                modifier = mod_value if sign == "+" else -mod_value

            return cls(num_dice=num_dice, die_size=die_size, modifier=modifier)

        raise ValueError(f"Invalid dice expression: {expression}")

    @classmethod
    def from_components(
        cls, num_dice: int, die_size: int, modifier: int = 0
    ) -> "DiceExpression":
        """Create a dice expression from components."""
        return cls(num_dice=num_dice, die_size=die_size, modifier=modifier)

    def __str__(self) -> str:
        """Return string representation like '2d6+3'."""
        base = f"{self.num_dice}d{self.die_size}"
        if self.modifier > 0:
            return f"{base}+{self.modifier}"
        elif self.modifier < 0:
            return f"{base}{self.modifier}"
        return base


class DiceRoller:
    """
    Deterministic dice roller for SRD 5.2 mechanics.

    Supports seeded random number generation for reproducible tests.
    """

    def __init__(self, seed: int | None = None):
        """
        Initialize the dice roller.

        Args:
            seed: Optional seed for deterministic rolling. If None, uses
                  system random for each roll.
        """
        self._seed = seed
        self._rng = random.Random(seed) if seed is not None else None
        self._roll_count = 0

    def _get_random(self) -> int:
        """Get a random number using the appropriate generator."""
        if self._rng is not None:
            return self._rng.randint(1, 2**31 - 1)
        return random.randint(1, 2**31 - 1)

    def _roll_single(self, die_size: int) -> DieRoll:
        """Roll a single die."""
        self._roll_count += 1
        result = (self._get_random() % die_size) + 1
        return DieRoll(die_size=die_size, result=result)

    def roll_d20(
        self,
        advantage: AdvantageState = AdvantageState.NONE,
        modifier: int = 0,
    ) -> RollResult:
        """
        Roll a d20 with optional advantage/disadvantage.

        Args:
            advantage: Advantage state
            modifier: Modifier to add to the roll

        Returns:
            RollResult with total, rolls, and advantage info
        """
        if advantage == AdvantageState.NONE:
            roll = self._roll_single(20)
            natural = roll.result
            total = natural + modifier
            return RollResult(
                total=total,
                rolls=[roll],
                modifier=modifier,
                natural_roll=natural,
                advantage_state=advantage,
                is_critical=(natural == 20),
                is_fumble=(natural == 1),
            )

        # Roll twice for advantage/disadvantage
        roll1 = self._roll_single(20)
        roll2 = self._roll_single(20)

        if advantage == AdvantageState.ADVANTAGE:
            natural = max(roll1.result, roll2.result)
            used_roll = roll1 if roll1.result >= roll2.result else roll2
            discarded_roll = roll2 if roll1.result >= roll2.result else roll1
        else:  # DISADVANTAGE
            natural = min(roll1.result, roll2.result)
            used_roll = roll1 if roll1.result <= roll2.result else roll2
            discarded_roll = roll2 if roll1.result <= roll2.result else roll1

        total = natural + modifier

        return RollResult(
            total=total,
            rolls=[used_roll],
            modifier=modifier,
            natural_roll=natural,
            advantage_state=advantage,
            discarded_rolls=[discarded_roll],
            is_critical=(natural == 20),
            is_fumble=(natural == 1),
        )

    def roll(
        self,
        expression: str | DiceExpression,
        extra_modifier: int = 0,
    ) -> RollResult:
        """
        Roll dice from an expression.

        Args:
            expression: Dice expression string (e.g., "2d6+3") or DiceExpression
            extra_modifier: Additional modifier to add

        Returns:
            RollResult with total and individual rolls
        """
        if isinstance(expression, str):
            expr = DiceExpression.parse(expression)
        else:
            expr = expression

        rolls: list[DieRoll] = []
        for _ in range(expr.num_dice):
            rolls.append(self._roll_single(expr.die_size))

        roll_total = sum(r.result for r in rolls)
        total_modifier = expr.modifier + extra_modifier
        total = roll_total + total_modifier

        return RollResult(
            total=total,
            rolls=rolls,
            modifier=total_modifier,
        )

    def roll_damage(
        self,
        expression: str | DiceExpression,
        modifier: int = 0,
        critical: bool = False,
    ) -> RollResult:
        """
        Roll damage dice.

        Args:
            expression: Damage dice expression (e.g., "2d6")
            modifier: Damage modifier (e.g., strength or dex mod)
            critical: If True, double the dice rolled

        Returns:
            RollResult with damage total
        """
        if isinstance(expression, str):
            expr = DiceExpression.parse(expression)
        else:
            expr = expression

        num_dice = expr.num_dice * 2 if critical else expr.num_dice

        rolls: list[DieRoll] = []
        for _ in range(num_dice):
            rolls.append(self._roll_single(expr.die_size))

        roll_total = sum(r.result for r in rolls)
        total = roll_total + expr.modifier + modifier

        # Minimum damage is 1 (per SRD)
        total = max(1, total)

        return RollResult(
            total=total,
            rolls=rolls,
            modifier=expr.modifier + modifier,
        )

    def roll_with_reroll(
        self,
        expression: str | DiceExpression,
        reroll_threshold: int = 1,
        reroll_once: bool = True,
    ) -> RollResult:
        """
        Roll dice with reroll mechanic (like Great Weapon Fighting).

        Args:
            expression: Dice expression
            reroll_threshold: Reroll results at or below this value
            reroll_once: If True, only reroll once per die

        Returns:
            RollResult with rerolled dice
        """
        if isinstance(expression, str):
            expr = DiceExpression.parse(expression)
        else:
            expr = expression

        rolls: list[DieRoll] = []
        discarded: list[DieRoll] = []

        for _ in range(expr.num_dice):
            roll = self._roll_single(expr.die_size)

            if roll.result <= reroll_threshold:
                discarded.append(roll)
                roll = self._roll_single(expr.die_size)

                # If reroll_once is False and still below threshold, keep rerolling
                while not reroll_once and roll.result <= reroll_threshold:
                    discarded.append(roll)
                    roll = self._roll_single(expr.die_size)

            rolls.append(roll)

        roll_total = sum(r.result for r in rolls)
        total = roll_total + expr.modifier

        return RollResult(
            total=total,
            rolls=rolls,
            modifier=expr.modifier,
            discarded_rolls=discarded,
        )

    def reset_seed(self, seed: int | None = None) -> None:
        """Reset the random state with a new seed."""
        self._seed = seed
        self._rng = random.Random(seed) if seed is not None else None
        self._roll_count = 0

    @property
    def roll_count(self) -> int:
        """Number of individual dice rolled since creation/reset."""
        return self._roll_count
