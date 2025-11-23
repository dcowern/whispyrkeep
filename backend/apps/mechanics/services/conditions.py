"""
Condition System Service.

Manages SRD 5.2 conditions and their effects on characters.

Ticket: 9.0.4

Based on SYSTEM_DESIGN.md section 7.3 Deterministic Functions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from .dice import AdvantageState


class Condition(str, Enum):
    """SRD 5.2 conditions."""

    BLINDED = "blinded"
    CHARMED = "charmed"
    DEAFENED = "deafened"
    FRIGHTENED = "frightened"
    GRAPPLED = "grappled"
    INCAPACITATED = "incapacitated"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    POISONED = "poisoned"
    PRONE = "prone"
    RESTRAINED = "restrained"
    STUNNED = "stunned"
    UNCONSCIOUS = "unconscious"
    EXHAUSTION = "exhaustion"  # Has levels 1-6


@dataclass
class ConditionEffect:
    """
    Effects of a condition on a character.

    Each condition modifies various aspects of gameplay.
    """

    # Attack modifiers
    attack_advantage: AdvantageState = AdvantageState.NONE
    attack_disadvantage: AdvantageState = AdvantageState.NONE
    attacks_against_advantage: AdvantageState = AdvantageState.NONE

    # Check/Save modifiers
    ability_check_disadvantage: set[str] = field(default_factory=set)
    saving_throw_advantage: set[str] = field(default_factory=set)
    saving_throw_disadvantage: set[str] = field(default_factory=set)
    auto_fail_saves: set[str] = field(default_factory=set)

    # Speed modifiers
    speed_modifier: float = 1.0  # Multiplier (0.5 = half, 0 = can't move)

    # Special flags
    can_attack: bool = True
    can_move: bool = True
    can_take_actions: bool = True
    can_take_reactions: bool = True
    can_speak: bool = True
    can_see: bool = True
    can_hear: bool = True

    # Combat effects
    is_incapacitated: bool = False
    attacks_auto_crit_in_melee: bool = False  # Attacks auto-crit if within 5 feet

    # Other effects
    grants_advantage_on_stealth: bool = False
    description: str = ""


# SRD 5.2 condition effects
CONDITION_EFFECTS: dict[Condition, ConditionEffect] = {
    Condition.BLINDED: ConditionEffect(
        attack_disadvantage=AdvantageState.DISADVANTAGE,
        attacks_against_advantage=AdvantageState.ADVANTAGE,
        auto_fail_saves=set(),  # Auto-fail sight-based checks (handled separately)
        can_see=False,
        description="Can't see; auto-fails checks requiring sight; attacks have disadvantage; "
                   "attacks against have advantage.",
    ),
    Condition.CHARMED: ConditionEffect(
        description="Can't attack the charmer; charmer has advantage on social checks.",
    ),
    Condition.DEAFENED: ConditionEffect(
        can_hear=False,
        description="Can't hear; auto-fails checks requiring hearing.",
    ),
    Condition.FRIGHTENED: ConditionEffect(
        ability_check_disadvantage={"str", "dex", "con", "int", "wis", "cha"},
        attack_disadvantage=AdvantageState.DISADVANTAGE,
        description="Disadvantage on ability checks and attacks while source is in sight; "
                   "can't willingly move closer to source.",
    ),
    Condition.GRAPPLED: ConditionEffect(
        speed_modifier=0.0,
        can_move=False,
        description="Speed becomes 0; can't benefit from bonuses to speed.",
    ),
    Condition.INCAPACITATED: ConditionEffect(
        can_take_actions=False,
        can_take_reactions=False,
        is_incapacitated=True,
        description="Can't take actions or reactions.",
    ),
    Condition.INVISIBLE: ConditionEffect(
        attack_advantage=AdvantageState.ADVANTAGE,
        attacks_against_advantage=AdvantageState.DISADVANTAGE,
        grants_advantage_on_stealth=True,
        description="Impossible to see without special sense; heavily obscured; "
                   "attacks have advantage; attacks against have disadvantage.",
    ),
    Condition.PARALYZED: ConditionEffect(
        can_take_actions=False,
        can_take_reactions=False,
        can_move=False,
        speed_modifier=0.0,
        is_incapacitated=True,
        auto_fail_saves={"str", "dex"},
        attacks_against_advantage=AdvantageState.ADVANTAGE,
        attacks_auto_crit_in_melee=True,
        description="Incapacitated; can't move or speak; auto-fails STR/DEX saves; "
                   "attacks have advantage; hits within 5ft are critical.",
    ),
    Condition.PETRIFIED: ConditionEffect(
        can_take_actions=False,
        can_take_reactions=False,
        can_move=False,
        can_speak=False,
        speed_modifier=0.0,
        is_incapacitated=True,
        auto_fail_saves={"str", "dex"},
        attacks_against_advantage=AdvantageState.ADVANTAGE,
        description="Transformed to inanimate substance; incapacitated; can't move/speak; "
                   "unaware of surroundings; auto-fails STR/DEX saves; "
                   "resistance to all damage; immune to poison/disease.",
    ),
    Condition.POISONED: ConditionEffect(
        ability_check_disadvantage={"str", "dex", "con", "int", "wis", "cha"},
        attack_disadvantage=AdvantageState.DISADVANTAGE,
        description="Disadvantage on attack rolls and ability checks.",
    ),
    Condition.PRONE: ConditionEffect(
        attack_disadvantage=AdvantageState.DISADVANTAGE,
        description="Disadvantage on attacks; attacks within 5ft have advantage, "
                   "beyond 5ft have disadvantage; can only crawl; "
                   "standing costs half movement.",
    ),
    Condition.RESTRAINED: ConditionEffect(
        speed_modifier=0.0,
        can_move=False,
        attack_disadvantage=AdvantageState.DISADVANTAGE,
        saving_throw_disadvantage={"dex"},
        attacks_against_advantage=AdvantageState.ADVANTAGE,
        description="Speed becomes 0; attacks have disadvantage; "
                   "attacks against have advantage; disadvantage on DEX saves.",
    ),
    Condition.STUNNED: ConditionEffect(
        can_take_actions=False,
        can_take_reactions=False,
        can_move=False,
        is_incapacitated=True,
        auto_fail_saves={"str", "dex"},
        attacks_against_advantage=AdvantageState.ADVANTAGE,
        description="Incapacitated; can't move; can speak only falteringly; "
                   "auto-fails STR/DEX saves; attacks have advantage.",
    ),
    Condition.UNCONSCIOUS: ConditionEffect(
        can_take_actions=False,
        can_take_reactions=False,
        can_move=False,
        can_speak=False,
        speed_modifier=0.0,
        is_incapacitated=True,
        auto_fail_saves={"str", "dex"},
        attacks_against_advantage=AdvantageState.ADVANTAGE,
        attacks_auto_crit_in_melee=True,
        description="Incapacitated; can't move or speak; unaware of surroundings; "
                   "drops held items; falls prone; auto-fails STR/DEX saves; "
                   "attacks have advantage; hits within 5ft are critical.",
    ),
    Condition.EXHAUSTION: ConditionEffect(
        # Exhaustion effects depend on level - handled separately
        description="Cumulative effects based on exhaustion level (1-6).",
    ),
}


@dataclass
class ExhaustionLevel:
    """Effects at a specific exhaustion level."""

    level: int
    effects: ConditionEffect
    description: str


EXHAUSTION_LEVELS: dict[int, ExhaustionLevel] = {
    1: ExhaustionLevel(
        level=1,
        effects=ConditionEffect(
            ability_check_disadvantage={"str", "dex", "con", "int", "wis", "cha"},
        ),
        description="Disadvantage on ability checks",
    ),
    2: ExhaustionLevel(
        level=2,
        effects=ConditionEffect(
            ability_check_disadvantage={"str", "dex", "con", "int", "wis", "cha"},
            speed_modifier=0.5,
        ),
        description="Disadvantage on ability checks; speed halved",
    ),
    3: ExhaustionLevel(
        level=3,
        effects=ConditionEffect(
            ability_check_disadvantage={"str", "dex", "con", "int", "wis", "cha"},
            attack_disadvantage=AdvantageState.DISADVANTAGE,
            saving_throw_disadvantage={"str", "dex", "con", "int", "wis", "cha"},
            speed_modifier=0.5,
        ),
        description="Disadvantage on ability checks, attacks, and saves; speed halved",
    ),
    4: ExhaustionLevel(
        level=4,
        effects=ConditionEffect(
            ability_check_disadvantage={"str", "dex", "con", "int", "wis", "cha"},
            attack_disadvantage=AdvantageState.DISADVANTAGE,
            saving_throw_disadvantage={"str", "dex", "con", "int", "wis", "cha"},
            speed_modifier=0.5,
            # HP max halved - handled separately
        ),
        description="Disadvantage on ability checks, attacks, and saves; speed halved; "
                   "HP maximum halved",
    ),
    5: ExhaustionLevel(
        level=5,
        effects=ConditionEffect(
            ability_check_disadvantage={"str", "dex", "con", "int", "wis", "cha"},
            attack_disadvantage=AdvantageState.DISADVANTAGE,
            saving_throw_disadvantage={"str", "dex", "con", "int", "wis", "cha"},
            speed_modifier=0.0,
            can_move=False,
            # HP max halved - handled separately
        ),
        description="Disadvantage on ability checks, attacks, and saves; speed 0; "
                   "HP maximum halved",
    ),
    6: ExhaustionLevel(
        level=6,
        effects=ConditionEffect(
            # Death - handled separately
        ),
        description="Death",
    ),
}


@dataclass
class AppliedCondition:
    """A condition applied to a character with duration tracking."""

    condition: Condition
    source: str = ""  # What caused the condition
    duration_rounds: int | None = None  # None = permanent until removed
    duration_minutes: int | None = None  # For out-of-combat durations
    save_dc: int | None = None  # DC to save against at end of turn
    save_ability: str | None = None  # Ability to use for save
    exhaustion_level: int = 0  # Only for exhaustion condition

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "condition": self.condition.value,
            "source": self.source,
            "duration_rounds": self.duration_rounds,
            "duration_minutes": self.duration_minutes,
            "save_dc": self.save_dc,
            "save_ability": self.save_ability,
            "exhaustion_level": self.exhaustion_level,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppliedCondition":
        """Create from dictionary."""
        condition_str = data.get("condition", "")
        try:
            condition = Condition(condition_str)
        except ValueError:
            condition = Condition.POISONED  # Default fallback

        return cls(
            condition=condition,
            source=data.get("source", ""),
            duration_rounds=data.get("duration_rounds"),
            duration_minutes=data.get("duration_minutes"),
            save_dc=data.get("save_dc"),
            save_ability=data.get("save_ability"),
            exhaustion_level=data.get("exhaustion_level", 0),
        )


@dataclass
class ConditionState:
    """Current condition state for a character."""

    active_conditions: list[AppliedCondition] = field(default_factory=list)

    def has_condition(self, condition: Condition | str) -> bool:
        """Check if character has a condition."""
        if isinstance(condition, str):
            condition = Condition(condition)
        return any(ac.condition == condition for ac in self.active_conditions)

    def get_condition(self, condition: Condition | str) -> AppliedCondition | None:
        """Get the applied condition if present."""
        if isinstance(condition, str):
            condition = Condition(condition)
        for ac in self.active_conditions:
            if ac.condition == condition:
                return ac
        return None

    def get_exhaustion_level(self) -> int:
        """Get current exhaustion level."""
        exhaustion = self.get_condition(Condition.EXHAUSTION)
        return exhaustion.exhaustion_level if exhaustion else 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "active_conditions": [ac.to_dict() for ac in self.active_conditions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConditionState":
        """Create from dictionary."""
        conditions = [
            AppliedCondition.from_dict(ac)
            for ac in data.get("active_conditions", [])
        ]
        return cls(active_conditions=conditions)


class ConditionManager:
    """
    Manages conditions for characters.

    Handles:
    - Applying/removing conditions
    - Tracking durations
    - Computing combined effects
    - Exhaustion level management
    """

    def apply_condition(
        self,
        state: ConditionState,
        condition: Condition | str,
        source: str = "",
        duration_rounds: int | None = None,
        duration_minutes: int | None = None,
        save_dc: int | None = None,
        save_ability: str | None = None,
        exhaustion_level: int = 1,
    ) -> AppliedCondition:
        """
        Apply a condition to a character.

        Args:
            state: Character's current condition state
            condition: Condition to apply
            source: What caused the condition
            duration_rounds: Duration in combat rounds
            duration_minutes: Duration in minutes (out of combat)
            save_dc: DC to save against
            save_ability: Ability to use for save
            exhaustion_level: Level of exhaustion (only for exhaustion condition)

        Returns:
            The applied condition
        """
        if isinstance(condition, str):
            condition = Condition(condition)

        # Handle exhaustion specially - it stacks
        if condition == Condition.EXHAUSTION:
            return self._apply_exhaustion(state, source, exhaustion_level)

        # Check if already has condition - don't duplicate
        existing = state.get_condition(condition)
        if existing:
            # Update duration if new one is longer
            if duration_rounds and (
                existing.duration_rounds is None
                or duration_rounds > existing.duration_rounds
            ):
                existing.duration_rounds = duration_rounds
            if duration_minutes and (
                existing.duration_minutes is None
                or duration_minutes > existing.duration_minutes
            ):
                existing.duration_minutes = duration_minutes
            return existing

        # Create and add new condition
        applied = AppliedCondition(
            condition=condition,
            source=source,
            duration_rounds=duration_rounds,
            duration_minutes=duration_minutes,
            save_dc=save_dc,
            save_ability=save_ability,
        )
        state.active_conditions.append(applied)
        return applied

    def _apply_exhaustion(
        self,
        state: ConditionState,
        source: str,
        levels: int = 1,
    ) -> AppliedCondition:
        """Apply exhaustion levels (stacks up to 6)."""
        existing = state.get_condition(Condition.EXHAUSTION)

        if existing:
            # Increase exhaustion level
            existing.exhaustion_level = min(6, existing.exhaustion_level + levels)
            return existing

        # Create new exhaustion condition
        applied = AppliedCondition(
            condition=Condition.EXHAUSTION,
            source=source,
            exhaustion_level=min(6, levels),
        )
        state.active_conditions.append(applied)
        return applied

    def remove_condition(
        self,
        state: ConditionState,
        condition: Condition | str,
    ) -> bool:
        """
        Remove a condition from a character.

        Returns:
            True if condition was removed, False if not present
        """
        if isinstance(condition, str):
            condition = Condition(condition)

        for i, ac in enumerate(state.active_conditions):
            if ac.condition == condition:
                state.active_conditions.pop(i)
                return True
        return False

    def reduce_exhaustion(
        self,
        state: ConditionState,
        levels: int = 1,
    ) -> int:
        """
        Reduce exhaustion by specified levels.

        Returns:
            New exhaustion level
        """
        existing = state.get_condition(Condition.EXHAUSTION)
        if not existing:
            return 0

        existing.exhaustion_level = max(0, existing.exhaustion_level - levels)

        if existing.exhaustion_level == 0:
            self.remove_condition(state, Condition.EXHAUSTION)
            return 0

        return existing.exhaustion_level

    def tick_durations(
        self,
        state: ConditionState,
        rounds: int = 1,
    ) -> list[Condition]:
        """
        Reduce duration of conditions by specified rounds.

        Returns:
            List of conditions that expired
        """
        expired = []
        remaining = []

        for ac in state.active_conditions:
            if ac.duration_rounds is not None:
                ac.duration_rounds -= rounds
                if ac.duration_rounds <= 0:
                    expired.append(ac.condition)
                    continue
            remaining.append(ac)

        state.active_conditions = remaining
        return expired

    def get_combined_effects(self, state: ConditionState) -> ConditionEffect:
        """
        Compute the combined effects of all active conditions.

        Returns:
            Combined ConditionEffect
        """
        combined = ConditionEffect()

        for ac in state.active_conditions:
            effect = CONDITION_EFFECTS.get(ac.condition)
            if not effect:
                continue

            # Handle exhaustion specially
            if ac.condition == Condition.EXHAUSTION:
                effect = EXHAUSTION_LEVELS.get(
                    ac.exhaustion_level, EXHAUSTION_LEVELS[1]
                ).effects

            # Merge effects - most restrictive wins
            if effect.attack_disadvantage == AdvantageState.DISADVANTAGE:
                combined.attack_disadvantage = AdvantageState.DISADVANTAGE
            if effect.attack_advantage == AdvantageState.ADVANTAGE:
                combined.attack_advantage = AdvantageState.ADVANTAGE
            if effect.attacks_against_advantage == AdvantageState.ADVANTAGE:
                combined.attacks_against_advantage = AdvantageState.ADVANTAGE

            combined.ability_check_disadvantage.update(effect.ability_check_disadvantage)
            combined.saving_throw_advantage.update(effect.saving_throw_advantage)
            combined.saving_throw_disadvantage.update(effect.saving_throw_disadvantage)
            combined.auto_fail_saves.update(effect.auto_fail_saves)

            combined.speed_modifier = min(combined.speed_modifier, effect.speed_modifier)
            combined.can_attack = combined.can_attack and effect.can_attack
            combined.can_move = combined.can_move and effect.can_move
            combined.can_take_actions = combined.can_take_actions and effect.can_take_actions
            combined.can_take_reactions = combined.can_take_reactions and effect.can_take_reactions
            combined.can_speak = combined.can_speak and effect.can_speak
            combined.can_see = combined.can_see and effect.can_see
            combined.can_hear = combined.can_hear and effect.can_hear
            combined.is_incapacitated = combined.is_incapacitated or effect.is_incapacitated
            combined.attacks_auto_crit_in_melee = (
                combined.attacks_auto_crit_in_melee or effect.attacks_auto_crit_in_melee
            )

        return combined

    def get_attack_advantage_state(
        self,
        state: ConditionState,
        is_attacker: bool = True,
        melee_range: bool = False,
    ) -> AdvantageState:
        """
        Get the advantage state for attacks.

        Args:
            state: Condition state
            is_attacker: True if checking for character's attacks
            melee_range: True if attack is within 5 feet

        Returns:
            AdvantageState for the attack
        """
        effects = self.get_combined_effects(state)

        if is_attacker:
            # Check attacker's conditions
            if effects.attack_disadvantage == AdvantageState.DISADVANTAGE:
                if effects.attack_advantage == AdvantageState.ADVANTAGE:
                    return AdvantageState.NONE  # Cancel out
                return AdvantageState.DISADVANTAGE
            if effects.attack_advantage == AdvantageState.ADVANTAGE:
                return AdvantageState.ADVANTAGE
        else:
            # Check target's conditions (for attacks against)
            if effects.attacks_against_advantage == AdvantageState.ADVANTAGE:
                return AdvantageState.ADVANTAGE

        return AdvantageState.NONE

    def get_save_advantage_state(
        self,
        state: ConditionState,
        ability: str,
    ) -> AdvantageState | None:
        """
        Get advantage state for a saving throw.

        Args:
            state: Condition state
            ability: Ability being used for save

        Returns:
            AdvantageState or None if auto-fail
        """
        effects = self.get_combined_effects(state)

        # Check for auto-fail
        if ability in effects.auto_fail_saves:
            return None  # Auto-fail

        # Check for advantage/disadvantage
        has_advantage = ability in effects.saving_throw_advantage
        has_disadvantage = ability in effects.saving_throw_disadvantage

        if has_advantage and has_disadvantage:
            return AdvantageState.NONE
        if has_advantage:
            return AdvantageState.ADVANTAGE
        if has_disadvantage:
            return AdvantageState.DISADVANTAGE

        return AdvantageState.NONE

    def check_ability_check_disadvantage(
        self,
        state: ConditionState,
        ability: str,
    ) -> bool:
        """Check if ability checks have disadvantage."""
        effects = self.get_combined_effects(state)
        return ability in effects.ability_check_disadvantage


# Convenience functions
def apply_condition(
    state: ConditionState | dict,
    condition: Condition | str,
    **kwargs,
) -> AppliedCondition:
    """Apply a condition to a character state."""
    if isinstance(state, dict):
        state = ConditionState.from_dict(state)

    manager = ConditionManager()
    return manager.apply_condition(state, condition, **kwargs)


def remove_condition(
    state: ConditionState | dict,
    condition: Condition | str,
) -> bool:
    """Remove a condition from a character state."""
    if isinstance(state, dict):
        state = ConditionState.from_dict(state)

    manager = ConditionManager()
    return manager.remove_condition(state, condition)


def get_condition_effects(condition: Condition | str) -> ConditionEffect:
    """Get the effects of a specific condition."""
    if isinstance(condition, str):
        condition = Condition(condition)
    return CONDITION_EFFECTS.get(condition, ConditionEffect())
