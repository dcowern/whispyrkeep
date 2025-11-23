# Mechanics services - Dice, checks, saves, combat resolution
from .checks import (
    Ability,
    CharacterStats,
    CheckResolver,
    CheckResult,
    resolve_ability_check,
    resolve_saving_throw,
)
from .combat import (
    AttackResult,
    AttackType,
    CombatResolver,
    DamageType,
    TargetStats,
    WeaponProfile,
    WEAPONS,
    resolve_attack,
)
from .conditions import (
    AppliedCondition,
    Condition,
    ConditionEffect,
    ConditionManager,
    ConditionState,
    CONDITION_EFFECTS,
    EXHAUSTION_LEVELS,
    apply_condition,
    get_condition_effects,
    remove_condition,
)
from .dice import (
    AdvantageState,
    DiceExpression,
    DiceRoller,
    DieRoll,
    RollResult,
)
from .resting import (
    ResourceState,
    RestingService,
    RestResult,
    long_rest,
    short_rest,
)

__all__ = [
    # Dice
    "AdvantageState",
    "DiceExpression",
    "DiceRoller",
    "DieRoll",
    "RollResult",
    # Checks
    "Ability",
    "CharacterStats",
    "CheckResolver",
    "CheckResult",
    "resolve_ability_check",
    "resolve_saving_throw",
    # Combat
    "AttackResult",
    "AttackType",
    "CombatResolver",
    "DamageType",
    "TargetStats",
    "WeaponProfile",
    "WEAPONS",
    "resolve_attack",
    # Conditions
    "AppliedCondition",
    "Condition",
    "ConditionEffect",
    "ConditionManager",
    "ConditionState",
    "CONDITION_EFFECTS",
    "EXHAUSTION_LEVELS",
    "apply_condition",
    "get_condition_effects",
    "remove_condition",
    # Resting
    "ResourceState",
    "RestingService",
    "RestResult",
    "long_rest",
    "short_rest",
]
