"""
Combat Resolution Service.

Resolves attack rolls and damage per SRD 5.2 rules.

Ticket: 9.0.3

Based on SYSTEM_DESIGN.md section 7.3 Deterministic Functions.
"""

from dataclasses import dataclass, field
from enum import Enum

from .checks import Ability, CharacterStats
from .dice import AdvantageState, DiceExpression, DiceRoller, RollResult


class AttackType(str, Enum):
    """Types of attacks."""

    MELEE_WEAPON = "melee_weapon"
    RANGED_WEAPON = "ranged_weapon"
    MELEE_SPELL = "melee_spell"
    RANGED_SPELL = "ranged_spell"


class DamageType(str, Enum):
    """SRD 5.2 damage types."""

    ACID = "acid"
    BLUDGEONING = "bludgeoning"
    COLD = "cold"
    FIRE = "fire"
    FORCE = "force"
    LIGHTNING = "lightning"
    NECROTIC = "necrotic"
    PIERCING = "piercing"
    POISON = "poison"
    PSYCHIC = "psychic"
    RADIANT = "radiant"
    SLASHING = "slashing"
    THUNDER = "thunder"


@dataclass
class WeaponProfile:
    """Weapon or spell attack profile."""

    name: str
    attack_type: AttackType
    damage_dice: str  # e.g., "1d8", "2d6"
    damage_type: DamageType | str
    ability_override: Ability | str | None = None  # Override default ability
    magic_bonus: int = 0  # +1, +2, +3 weapons
    finesse: bool = False  # Can use STR or DEX
    two_handed_damage: str | None = None  # Versatile weapons
    properties: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "WeaponProfile":
        """Create from dictionary."""
        attack_type_str = data.get("attack_type", "melee_weapon")
        if isinstance(attack_type_str, str):
            attack_type = AttackType(attack_type_str)
        else:
            attack_type = attack_type_str

        damage_type_str = data.get("damage_type", "slashing")
        if isinstance(damage_type_str, str):
            try:
                damage_type = DamageType(damage_type_str)
            except ValueError:
                damage_type = damage_type_str  # Custom damage type
        else:
            damage_type = damage_type_str

        return cls(
            name=data.get("name", "Unknown"),
            attack_type=attack_type,
            damage_dice=data.get("damage_dice", "1d4"),
            damage_type=damage_type,
            ability_override=data.get("ability_override"),
            magic_bonus=data.get("magic_bonus", 0),
            finesse=data.get("finesse", False),
            two_handed_damage=data.get("two_handed_damage"),
            properties=data.get("properties", []),
        )


@dataclass
class TargetStats:
    """Target statistics for attack resolution."""

    armor_class: int = 10
    resistances: set[str] = field(default_factory=set)
    immunities: set[str] = field(default_factory=set)
    vulnerabilities: set[str] = field(default_factory=set)

    @classmethod
    def from_dict(cls, data: dict) -> "TargetStats":
        """Create from dictionary."""
        return cls(
            armor_class=data.get("armor_class", data.get("ac", 10)),
            resistances=set(data.get("resistances", [])),
            immunities=set(data.get("immunities", [])),
            vulnerabilities=set(data.get("vulnerabilities", [])),
        )


@dataclass
class AttackResult:
    """Result of an attack roll."""

    hit: bool
    critical: bool
    attack_total: int
    natural_roll: int
    attack_modifier: int
    target_ac: int
    damage_total: int = 0
    damage_rolls: list[RollResult] = field(default_factory=list)
    damage_type: str = ""
    damage_modified: bool = False  # Was damage resisted/immune/vulnerable?
    damage_modifier_reason: str = ""
    advantage_state: AdvantageState = AdvantageState.NONE
    attack_roll: RollResult | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "hit": self.hit,
            "critical": self.critical,
            "attack_total": self.attack_total,
            "natural_roll": self.natural_roll,
            "attack_modifier": self.attack_modifier,
            "target_ac": self.target_ac,
            "damage_total": self.damage_total,
            "damage_type": self.damage_type,
            "damage_modified": self.damage_modified,
            "damage_modifier_reason": self.damage_modifier_reason,
            "advantage_state": self.advantage_state.value,
        }


class CombatResolver:
    """
    Resolves attack rolls and damage.

    SRD 5.2 attack resolution:
    1. Roll d20 + ability modifier + proficiency bonus (if proficient)
    2. Compare to target AC
    3. Natural 20 = critical hit (auto-hit, double damage dice)
    4. Natural 1 = critical miss (auto-miss)
    5. On hit, roll damage dice + ability modifier
    6. Apply resistances/vulnerabilities/immunities
    """

    def __init__(self, dice_roller: DiceRoller | None = None):
        """Initialize the resolver."""
        self.dice = dice_roller or DiceRoller()

    def _get_attack_ability(
        self,
        attacker: CharacterStats,
        weapon: WeaponProfile,
    ) -> Ability:
        """Determine the ability used for an attack."""
        if weapon.ability_override:
            if isinstance(weapon.ability_override, Ability):
                return weapon.ability_override
            return Ability(weapon.ability_override)

        # Default abilities by attack type
        if weapon.attack_type in (AttackType.MELEE_WEAPON, AttackType.MELEE_SPELL):
            default_ability = Ability.STR
        else:
            default_ability = Ability.DEX

        # Finesse weapons can use STR or DEX (use higher)
        if weapon.finesse:
            str_mod = attacker.get_ability_modifier(Ability.STR)
            dex_mod = attacker.get_ability_modifier(Ability.DEX)
            return Ability.DEX if dex_mod > str_mod else Ability.STR

        # Spell attacks use spellcasting ability (default to INT for simplicity)
        if weapon.attack_type in (AttackType.MELEE_SPELL, AttackType.RANGED_SPELL):
            return Ability.INT  # Could be overridden via ability_override

        return default_ability

    def resolve_attack(
        self,
        attacker: CharacterStats | dict,
        target: TargetStats | dict,
        weapon: WeaponProfile | dict,
        advantage: AdvantageState = AdvantageState.NONE,
        bonus: int = 0,
        proficient: bool = True,
        two_handed: bool = False,
    ) -> AttackResult:
        """
        Resolve a complete attack (attack roll + damage if hit).

        Args:
            attacker: Attacker's stats
            target: Target's stats
            weapon: Weapon/spell profile
            advantage: Advantage state for attack roll
            bonus: Additional attack bonus
            proficient: Whether attacker is proficient with weapon
            two_handed: Use two-handed damage for versatile weapons

        Returns:
            AttackResult with hit/miss and damage
        """
        # Normalize inputs
        if isinstance(attacker, dict):
            attacker = CharacterStats.from_dict(attacker)
        if isinstance(target, dict):
            target = TargetStats.from_dict(target)
        if isinstance(weapon, dict):
            weapon = WeaponProfile.from_dict(weapon)

        # Determine ability for attack
        attack_ability = self._get_attack_ability(attacker, weapon)
        ability_mod = attacker.get_ability_modifier(attack_ability)

        # Calculate attack modifier
        attack_modifier = ability_mod + weapon.magic_bonus + bonus
        if proficient:
            attack_modifier += attacker.proficiency_bonus

        # Roll attack
        attack_roll = self.dice.roll_d20(advantage=advantage, modifier=attack_modifier)

        # Determine hit
        natural = attack_roll.natural_roll
        critical = natural == 20
        fumble = natural == 1

        if fumble:
            hit = False
        elif critical:
            hit = True
        else:
            hit = attack_roll.total >= target.armor_class

        # Create base result
        result = AttackResult(
            hit=hit,
            critical=critical,
            attack_total=attack_roll.total,
            natural_roll=natural,
            attack_modifier=attack_modifier,
            target_ac=target.armor_class,
            advantage_state=advantage,
            attack_roll=attack_roll,
        )

        # Roll damage if hit
        if hit:
            damage_result = self._resolve_damage(
                attacker=attacker,
                target=target,
                weapon=weapon,
                ability=attack_ability,
                critical=critical,
                two_handed=two_handed,
            )
            result.damage_total = damage_result["total"]
            result.damage_rolls = damage_result["rolls"]
            result.damage_type = damage_result["damage_type"]
            result.damage_modified = damage_result["modified"]
            result.damage_modifier_reason = damage_result["reason"]

        return result

    def _resolve_damage(
        self,
        attacker: CharacterStats,
        target: TargetStats,
        weapon: WeaponProfile,
        ability: Ability,
        critical: bool,
        two_handed: bool,
    ) -> dict:
        """Resolve damage for a hit."""
        # Determine damage dice
        if two_handed and weapon.two_handed_damage:
            damage_dice = weapon.two_handed_damage
        else:
            damage_dice = weapon.damage_dice

        # Get ability modifier for damage
        ability_mod = attacker.get_ability_modifier(ability)

        # Roll damage
        damage_roll = self.dice.roll_damage(
            damage_dice,
            modifier=ability_mod + weapon.magic_bonus,
            critical=critical,
        )

        base_damage = damage_roll.total
        damage_type = weapon.damage_type
        if isinstance(damage_type, DamageType):
            damage_type_str = damage_type.value
        else:
            damage_type_str = damage_type

        # Apply resistance/immunity/vulnerability
        final_damage = base_damage
        modified = False
        reason = ""

        if damage_type_str in target.immunities:
            final_damage = 0
            modified = True
            reason = f"immune to {damage_type_str}"
        elif damage_type_str in target.resistances:
            final_damage = base_damage // 2
            modified = True
            reason = f"resistant to {damage_type_str}"
        elif damage_type_str in target.vulnerabilities:
            final_damage = base_damage * 2
            modified = True
            reason = f"vulnerable to {damage_type_str}"

        return {
            "total": final_damage,
            "rolls": [damage_roll],
            "damage_type": damage_type_str,
            "modified": modified,
            "reason": reason,
        }

    def resolve_attack_roll_only(
        self,
        attacker: CharacterStats | dict,
        target_ac: int,
        ability: Ability | str,
        advantage: AdvantageState = AdvantageState.NONE,
        bonus: int = 0,
        proficient: bool = True,
    ) -> AttackResult:
        """
        Resolve just an attack roll (no damage).

        Useful for spells where damage is separate.
        """
        if isinstance(attacker, dict):
            attacker = CharacterStats.from_dict(attacker)

        ability_mod = attacker.get_ability_modifier(ability)
        attack_modifier = ability_mod + bonus
        if proficient:
            attack_modifier += attacker.proficiency_bonus

        attack_roll = self.dice.roll_d20(advantage=advantage, modifier=attack_modifier)

        natural = attack_roll.natural_roll
        critical = natural == 20
        fumble = natural == 1

        if fumble:
            hit = False
        elif critical:
            hit = True
        else:
            hit = attack_roll.total >= target_ac

        ability_str = ability.value if isinstance(ability, Ability) else ability

        return AttackResult(
            hit=hit,
            critical=critical,
            attack_total=attack_roll.total,
            natural_roll=natural,
            attack_modifier=attack_modifier,
            target_ac=target_ac,
            advantage_state=advantage,
            attack_roll=attack_roll,
            damage_type="",  # No damage in this call
        )

    def resolve_damage_only(
        self,
        damage_dice: str,
        modifier: int = 0,
        damage_type: DamageType | str = DamageType.BLUDGEONING,
        critical: bool = False,
        target: TargetStats | dict | None = None,
    ) -> dict:
        """
        Resolve damage without an attack roll.

        Useful for spell damage, environmental damage, etc.
        """
        if target is not None and isinstance(target, dict):
            target = TargetStats.from_dict(target)

        damage_roll = self.dice.roll_damage(damage_dice, modifier=modifier, critical=critical)
        base_damage = damage_roll.total

        damage_type_str = damage_type.value if isinstance(damage_type, DamageType) else damage_type

        final_damage = base_damage
        modified = False
        reason = ""

        if target:
            if damage_type_str in target.immunities:
                final_damage = 0
                modified = True
                reason = f"immune to {damage_type_str}"
            elif damage_type_str in target.resistances:
                final_damage = base_damage // 2
                modified = True
                reason = f"resistant to {damage_type_str}"
            elif damage_type_str in target.vulnerabilities:
                final_damage = base_damage * 2
                modified = True
                reason = f"vulnerable to {damage_type_str}"

        return {
            "total": final_damage,
            "base_damage": base_damage,
            "rolls": [damage_roll],
            "damage_type": damage_type_str,
            "modified": modified,
            "reason": reason,
            "critical": critical,
        }


# Convenience function
def resolve_attack(
    attacker: CharacterStats | dict,
    target: TargetStats | dict,
    weapon: WeaponProfile | dict,
    advantage: AdvantageState = AdvantageState.NONE,
    seed: int | None = None,
    **kwargs,
) -> AttackResult:
    """
    Convenience function to resolve an attack.

    Args:
        attacker: Attacker stats
        target: Target stats
        weapon: Weapon profile
        advantage: Advantage state
        seed: Optional seed for deterministic roll
        **kwargs: Additional arguments passed to resolve_attack

    Returns:
        AttackResult
    """
    roller = DiceRoller(seed=seed)
    resolver = CombatResolver(roller)
    return resolver.resolve_attack(attacker, target, weapon, advantage, **kwargs)


# Common weapon profiles
WEAPONS = {
    "dagger": WeaponProfile(
        name="Dagger",
        attack_type=AttackType.MELEE_WEAPON,
        damage_dice="1d4",
        damage_type=DamageType.PIERCING,
        finesse=True,
        properties=["finesse", "light", "thrown"],
    ),
    "shortsword": WeaponProfile(
        name="Shortsword",
        attack_type=AttackType.MELEE_WEAPON,
        damage_dice="1d6",
        damage_type=DamageType.PIERCING,
        finesse=True,
        properties=["finesse", "light"],
    ),
    "longsword": WeaponProfile(
        name="Longsword",
        attack_type=AttackType.MELEE_WEAPON,
        damage_dice="1d8",
        damage_type=DamageType.SLASHING,
        two_handed_damage="1d10",
        properties=["versatile"],
    ),
    "greatsword": WeaponProfile(
        name="Greatsword",
        attack_type=AttackType.MELEE_WEAPON,
        damage_dice="2d6",
        damage_type=DamageType.SLASHING,
        properties=["heavy", "two-handed"],
    ),
    "shortbow": WeaponProfile(
        name="Shortbow",
        attack_type=AttackType.RANGED_WEAPON,
        damage_dice="1d6",
        damage_type=DamageType.PIERCING,
        properties=["ammunition", "two-handed"],
    ),
    "longbow": WeaponProfile(
        name="Longbow",
        attack_type=AttackType.RANGED_WEAPON,
        damage_dice="1d8",
        damage_type=DamageType.PIERCING,
        properties=["ammunition", "heavy", "two-handed"],
    ),
}
