"""
Resting Service.

Handles short and long rest mechanics per SRD 5.2 rules.

Ticket: 9.1.1

Based on SYSTEM_DESIGN.md sections 7.3 and 11.4.
"""

from dataclasses import dataclass, field

from .conditions import Condition, ConditionManager, ConditionState
from .dice import DiceRoller


@dataclass
class ResourceState:
    """
    Character resource state for resting.

    Tracks HP, hit dice, spell slots, and other resources.
    """

    # Hit Points
    current_hp: int = 0
    max_hp: int = 0
    temp_hp: int = 0

    # Hit Dice (keyed by die size, e.g., "d8": {"max": 4, "spent": 1})
    hit_dice: dict[str, dict[str, int]] = field(default_factory=dict)

    # Spell Slots (keyed by level, e.g., "1": {"max": 4, "used": 2})
    spell_slots: dict[str, dict[str, int]] = field(default_factory=dict)

    # Class-specific resources (e.g., ki points, rage uses)
    class_resources: dict[str, dict[str, int]] = field(default_factory=dict)

    # Death saves (reset on any healing)
    death_save_successes: int = 0
    death_save_failures: int = 0

    # Level (needed for exhaustion calculations)
    level: int = 1

    # Constitution modifier (for hit dice healing)
    constitution_modifier: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            "temp_hp": self.temp_hp,
            "hit_dice": self.hit_dice,
            "spell_slots": self.spell_slots,
            "class_resources": self.class_resources,
            "death_save_successes": self.death_save_successes,
            "death_save_failures": self.death_save_failures,
            "level": self.level,
            "constitution_modifier": self.constitution_modifier,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResourceState":
        """Create from dictionary."""
        return cls(
            current_hp=data.get("current_hp", 0),
            max_hp=data.get("max_hp", 0),
            temp_hp=data.get("temp_hp", 0),
            hit_dice=data.get("hit_dice", {}),
            spell_slots=data.get("spell_slots", {}),
            class_resources=data.get("class_resources", {}),
            death_save_successes=data.get("death_save_successes", 0),
            death_save_failures=data.get("death_save_failures", 0),
            level=data.get("level", 1),
            constitution_modifier=data.get("constitution_modifier", 0),
        )


@dataclass
class RestResult:
    """Result of a rest action."""

    rest_type: str  # "short" or "long"
    hp_healed: int = 0
    hit_dice_spent: list[dict] = field(default_factory=list)
    hit_dice_recovered: int = 0
    spell_slots_recovered: dict[str, int] = field(default_factory=dict)
    resources_recovered: dict[str, int] = field(default_factory=dict)
    conditions_removed: list[str] = field(default_factory=list)
    exhaustion_reduced: int = 0
    interrupted: bool = False
    interruption_reason: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "rest_type": self.rest_type,
            "hp_healed": self.hp_healed,
            "hit_dice_spent": self.hit_dice_spent,
            "hit_dice_recovered": self.hit_dice_recovered,
            "spell_slots_recovered": self.spell_slots_recovered,
            "resources_recovered": self.resources_recovered,
            "conditions_removed": self.conditions_removed,
            "exhaustion_reduced": self.exhaustion_reduced,
            "interrupted": self.interrupted,
            "interruption_reason": self.interruption_reason,
        }


class RestingService:
    """
    Service for handling short and long rests.

    SRD 5.2 Rest Rules:
    - Short Rest: 1 hour, can spend hit dice to heal
    - Long Rest: 8 hours, regain all HP, half hit dice, all spell slots
    """

    # Rest durations in hours
    SHORT_REST_HOURS = 1
    LONG_REST_HOURS = 8

    def __init__(
        self,
        dice_roller: DiceRoller | None = None,
        condition_manager: ConditionManager | None = None,
    ):
        """Initialize the service."""
        self.dice = dice_roller or DiceRoller()
        self.conditions = condition_manager or ConditionManager()

    def short_rest(
        self,
        resources: ResourceState | dict,
        conditions: ConditionState | dict | None = None,
        hit_dice_to_spend: list[str] | None = None,
    ) -> RestResult:
        """
        Process a short rest.

        Short rest benefits:
        - Can spend hit dice to heal
        - Some class features recharge

        Args:
            resources: Character's current resource state
            conditions: Character's condition state (optional)
            hit_dice_to_spend: List of hit dice to spend (e.g., ["d8", "d8"])

        Returns:
            RestResult with changes
        """
        if isinstance(resources, dict):
            resources = ResourceState.from_dict(resources)
        if conditions and isinstance(conditions, dict):
            conditions = ConditionState.from_dict(conditions)

        result = RestResult(rest_type="short")

        # Process hit dice spending
        if hit_dice_to_spend:
            hp_healed, dice_spent = self._spend_hit_dice(
                resources, hit_dice_to_spend
            )
            result.hp_healed = hp_healed
            result.hit_dice_spent = dice_spent

        # Recover certain class resources (class-specific, marked as "short_rest")
        for resource_name, resource_data in resources.class_resources.items():
            if resource_data.get("recharges_on") == "short_rest":
                used = resource_data.get("used", 0)
                if used > 0:
                    resource_data["used"] = 0
                    result.resources_recovered[resource_name] = used

        return result

    def long_rest(
        self,
        resources: ResourceState | dict,
        conditions: ConditionState | dict | None = None,
    ) -> RestResult:
        """
        Process a long rest.

        Long rest benefits:
        - Regain all HP
        - Regain half hit dice (minimum 1)
        - Regain all spell slots
        - All class features recharge
        - Reduce exhaustion by 1 level (if any)

        Args:
            resources: Character's current resource state
            conditions: Character's condition state (optional)

        Returns:
            RestResult with changes
        """
        if isinstance(resources, dict):
            resources = ResourceState.from_dict(resources)
        if conditions and isinstance(conditions, dict):
            conditions = ConditionState.from_dict(conditions)

        result = RestResult(rest_type="long")

        # Regain all HP
        hp_healed = resources.max_hp - resources.current_hp
        if hp_healed > 0:
            resources.current_hp = resources.max_hp
            result.hp_healed = hp_healed

        # Reset death saves
        resources.death_save_successes = 0
        resources.death_save_failures = 0

        # Regain half hit dice (minimum 1)
        total_hit_dice_recovered = 0
        for die_type, die_data in resources.hit_dice.items():
            max_dice = die_data.get("max", 0)
            spent = die_data.get("spent", 0)

            # Recover half of total (minimum 1)
            to_recover = max(1, max_dice // 2)
            actual_recovered = min(to_recover, spent)

            if actual_recovered > 0:
                die_data["spent"] = spent - actual_recovered
                total_hit_dice_recovered += actual_recovered

        result.hit_dice_recovered = total_hit_dice_recovered

        # Regain all spell slots
        for slot_level, slot_data in resources.spell_slots.items():
            used = slot_data.get("used", 0)
            if used > 0:
                slot_data["used"] = 0
                result.spell_slots_recovered[slot_level] = used

        # Recover all class resources
        for resource_name, resource_data in resources.class_resources.items():
            used = resource_data.get("used", 0)
            if used > 0:
                resource_data["used"] = 0
                result.resources_recovered[resource_name] = used

        # Reduce exhaustion by 1 level (if conditions provided)
        if conditions and conditions.has_condition(Condition.EXHAUSTION):
            old_level = conditions.get_exhaustion_level()
            new_level = self.conditions.reduce_exhaustion(conditions, levels=1)
            if new_level < old_level:
                result.exhaustion_reduced = 1

        return result

    def _spend_hit_dice(
        self,
        resources: ResourceState,
        dice_to_spend: list[str],
    ) -> tuple[int, list[dict]]:
        """
        Spend hit dice to heal.

        Args:
            resources: Character's resource state
            dice_to_spend: List of dice to spend (e.g., ["d8", "d8"])

        Returns:
            Tuple of (total HP healed, list of dice spent with results)
        """
        total_healed = 0
        dice_spent = []

        for die_type in dice_to_spend:
            # Normalize die type
            die_key = die_type.lower()
            if not die_key.startswith("d"):
                die_key = f"d{die_key}"

            # Check if have available dice
            die_data = resources.hit_dice.get(die_key)
            if not die_data:
                continue

            available = die_data.get("max", 0) - die_data.get("spent", 0)
            if available <= 0:
                continue

            # Roll the hit die
            die_size = int(die_key[1:])
            roll_result = self.dice.roll(f"1{die_key}")
            roll_value = roll_result.rolls[0].result

            # Add Constitution modifier (minimum 1 HP healed per die)
            hp_healed = max(1, roll_value + resources.constitution_modifier)

            # Cap healing at max HP
            actual_healed = min(hp_healed, resources.max_hp - resources.current_hp)
            resources.current_hp += actual_healed
            total_healed += actual_healed

            # Mark die as spent
            die_data["spent"] = die_data.get("spent", 0) + 1

            dice_spent.append({
                "die_type": die_key,
                "roll": roll_value,
                "modifier": resources.constitution_modifier,
                "hp_healed": actual_healed,
            })

        return total_healed, dice_spent

    def can_short_rest(
        self,
        conditions: ConditionState | dict | None = None,
    ) -> tuple[bool, str]:
        """
        Check if character can take a short rest.

        Returns:
            Tuple of (can_rest, reason_if_not)
        """
        if conditions:
            if isinstance(conditions, dict):
                conditions = ConditionState.from_dict(conditions)

            # Check for conditions that prevent resting
            if conditions.has_condition(Condition.UNCONSCIOUS):
                return False, "Cannot rest while unconscious"
            if conditions.has_condition(Condition.PETRIFIED):
                return False, "Cannot rest while petrified"

            # Check exhaustion level 6 (death)
            if conditions.get_exhaustion_level() >= 6:
                return False, "Cannot rest - exhaustion level 6 (death)"

        return True, ""

    def can_long_rest(
        self,
        conditions: ConditionState | dict | None = None,
    ) -> tuple[bool, str]:
        """
        Check if character can take a long rest.

        Returns:
            Tuple of (can_rest, reason_if_not)
        """
        # Same restrictions as short rest
        return self.can_short_rest(conditions)

    def get_available_hit_dice(
        self,
        resources: ResourceState | dict,
    ) -> dict[str, int]:
        """
        Get available (unspent) hit dice.

        Returns:
            Dict of die type to available count
        """
        if isinstance(resources, dict):
            resources = ResourceState.from_dict(resources)

        available = {}
        for die_type, die_data in resources.hit_dice.items():
            max_dice = die_data.get("max", 0)
            spent = die_data.get("spent", 0)
            remaining = max_dice - spent
            if remaining > 0:
                available[die_type] = remaining

        return available


# Convenience functions
def short_rest(
    resources: ResourceState | dict,
    conditions: ConditionState | dict | None = None,
    hit_dice_to_spend: list[str] | None = None,
    seed: int | None = None,
) -> RestResult:
    """
    Process a short rest.

    Args:
        resources: Character's resource state
        conditions: Character's condition state
        hit_dice_to_spend: Hit dice to spend for healing
        seed: Optional seed for deterministic dice rolls

    Returns:
        RestResult
    """
    roller = DiceRoller(seed=seed)
    service = RestingService(dice_roller=roller)
    return service.short_rest(resources, conditions, hit_dice_to_spend)


def long_rest(
    resources: ResourceState | dict,
    conditions: ConditionState | dict | None = None,
) -> RestResult:
    """
    Process a long rest.

    Args:
        resources: Character's resource state
        conditions: Character's condition state

    Returns:
        RestResult
    """
    service = RestingService()
    return service.long_rest(resources, conditions)
