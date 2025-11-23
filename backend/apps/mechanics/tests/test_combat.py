"""
Tests for combat resolution (attack rolls and damage).

Ticket: 9.0.3

Based on SYSTEM_DESIGN.md section 7.3 and CLAUDE.md testing requirements.
"""


from apps.mechanics.services.checks import CharacterStats
from apps.mechanics.services.combat import (
    WEAPONS,
    AttackResult,
    AttackType,
    CombatResolver,
    DamageType,
    TargetStats,
    WeaponProfile,
    resolve_attack,
)
from apps.mechanics.services.dice import AdvantageState, DiceRoller


class TestWeaponProfile:
    """Tests for WeaponProfile dataclass."""

    def test_basic_weapon(self):
        """Test creating a basic weapon profile."""
        weapon = WeaponProfile(
            name="Longsword",
            attack_type=AttackType.MELEE_WEAPON,
            damage_dice="1d8",
            damage_type=DamageType.SLASHING,
        )
        assert weapon.name == "Longsword"
        assert weapon.damage_dice == "1d8"
        assert weapon.magic_bonus == 0
        assert weapon.finesse is False

    def test_magic_weapon(self):
        """Test magic weapon with bonus."""
        weapon = WeaponProfile(
            name="+2 Longsword",
            attack_type=AttackType.MELEE_WEAPON,
            damage_dice="1d8",
            damage_type=DamageType.SLASHING,
            magic_bonus=2,
        )
        assert weapon.magic_bonus == 2

    def test_finesse_weapon(self):
        """Test finesse weapon."""
        weapon = WeaponProfile(
            name="Rapier",
            attack_type=AttackType.MELEE_WEAPON,
            damage_dice="1d8",
            damage_type=DamageType.PIERCING,
            finesse=True,
        )
        assert weapon.finesse is True

    def test_versatile_weapon(self):
        """Test versatile weapon with two-handed damage."""
        weapon = WeaponProfile(
            name="Longsword",
            attack_type=AttackType.MELEE_WEAPON,
            damage_dice="1d8",
            damage_type=DamageType.SLASHING,
            two_handed_damage="1d10",
        )
        assert weapon.two_handed_damage == "1d10"

    def test_from_dict(self):
        """Test creating weapon from dictionary."""
        data = {
            "name": "Greatsword",
            "attack_type": "melee_weapon",
            "damage_dice": "2d6",
            "damage_type": "slashing",
            "magic_bonus": 1,
        }
        weapon = WeaponProfile.from_dict(data)
        assert weapon.name == "Greatsword"
        assert weapon.attack_type == AttackType.MELEE_WEAPON
        assert weapon.damage_dice == "2d6"
        assert weapon.magic_bonus == 1


class TestTargetStats:
    """Tests for TargetStats dataclass."""

    def test_default_target(self):
        """Test default target stats."""
        target = TargetStats()
        assert target.armor_class == 10
        assert len(target.resistances) == 0
        assert len(target.immunities) == 0

    def test_armored_target(self):
        """Test target with high AC."""
        target = TargetStats(armor_class=18)
        assert target.armor_class == 18

    def test_resistant_target(self):
        """Test target with resistances."""
        target = TargetStats(
            armor_class=15,
            resistances={"fire", "cold"},
        )
        assert "fire" in target.resistances
        assert "cold" in target.resistances

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "ac": 16,
            "resistances": ["fire"],
            "immunities": ["poison"],
            "vulnerabilities": ["radiant"],
        }
        target = TargetStats.from_dict(data)
        assert target.armor_class == 16
        assert "fire" in target.resistances
        assert "poison" in target.immunities
        assert "radiant" in target.vulnerabilities


class TestAttackResult:
    """Tests for AttackResult dataclass."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        result = AttackResult(
            hit=True,
            critical=False,
            attack_total=18,
            natural_roll=14,
            attack_modifier=4,
            target_ac=15,
            damage_total=12,
            damage_type="slashing",
        )
        d = result.to_dict()
        assert d["hit"] is True
        assert d["critical"] is False
        assert d["attack_total"] == 18
        assert d["damage_total"] == 12


class TestCombatResolver:
    """Tests for CombatResolver service."""

    # ==================== Basic Attack Tests ====================

    def test_basic_melee_attack_hit(self):
        """Test basic melee attack that hits."""
        roller = DiceRoller(seed=42)  # Produces 8
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=16, level=1)  # +3 STR, +2 prof
        target = TargetStats(armor_class=12)
        weapon = WEAPONS["longsword"]

        result = resolver.resolve_attack(attacker, target, weapon)

        # Attack: 8 + 3 + 2 = 13 vs AC 12
        assert result.hit is True
        assert result.attack_total == 13
        assert result.natural_roll == 8
        assert result.attack_modifier == 5  # +3 STR + 2 prof
        assert result.target_ac == 12
        assert result.damage_total > 0

    def test_basic_melee_attack_miss(self):
        """Test basic melee attack that misses."""
        roller = DiceRoller(seed=4)  # Produces 1 (fumble)
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=16, level=1)
        target = TargetStats(armor_class=12)
        weapon = WEAPONS["longsword"]

        result = resolver.resolve_attack(attacker, target, weapon)

        assert result.hit is False
        assert result.natural_roll == 1
        assert result.damage_total == 0  # No damage on miss

    def test_ranged_attack(self):
        """Test ranged attack uses DEX."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        attacker = CharacterStats(dexterity=16, level=1)
        target = TargetStats(armor_class=12)
        weapon = WEAPONS["shortbow"]

        result = resolver.resolve_attack(attacker, target, weapon)

        # Should use DEX for ranged
        assert result.attack_modifier == 5  # +3 DEX + 2 prof

    def test_finesse_weapon_uses_better_stat(self):
        """Test finesse weapon uses higher of STR/DEX."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        # DEX is higher than STR
        attacker = CharacterStats(strength=10, dexterity=18, level=1)
        target = TargetStats(armor_class=12)
        weapon = WEAPONS["dagger"]

        result = resolver.resolve_attack(attacker, target, weapon)

        # Should use DEX (+4) not STR (+0)
        assert result.attack_modifier == 6  # +4 DEX + 2 prof

    def test_finesse_weapon_uses_str_if_higher(self):
        """Test finesse weapon uses STR if higher than DEX."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        # STR is higher than DEX
        attacker = CharacterStats(strength=18, dexterity=10, level=1)
        target = TargetStats(armor_class=12)
        weapon = WEAPONS["dagger"]

        result = resolver.resolve_attack(attacker, target, weapon)

        # Should use STR (+4) not DEX (+0)
        assert result.attack_modifier == 6  # +4 STR + 2 prof

    # ==================== Critical Hit Tests ====================

    def test_critical_hit_auto_hits(self):
        """Test natural 20 always hits regardless of AC."""
        roller = DiceRoller(seed=0)  # Produces 20
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=10, level=1)  # +0 modifier
        target = TargetStats(armor_class=30)  # Very high AC
        weapon = WEAPONS["longsword"]

        result = resolver.resolve_attack(attacker, target, weapon)

        assert result.hit is True
        assert result.critical is True
        assert result.natural_roll == 20

    def test_critical_hit_doubles_damage_dice(self):
        """Test critical hit doubles damage dice."""
        roller = DiceRoller(seed=0)  # Produces 20 (critical)
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=10, level=1)  # +0 modifier
        target = TargetStats(armor_class=10)
        weapon = WeaponProfile(
            name="Test",
            attack_type=AttackType.MELEE_WEAPON,
            damage_dice="1d6",
            damage_type=DamageType.SLASHING,
        )

        result = resolver.resolve_attack(attacker, target, weapon)

        # Should roll 2d6 instead of 1d6
        assert result.critical is True
        assert len(result.damage_rolls) > 0
        # Damage roll should have 2 dice (doubled from critical)
        assert len(result.damage_rolls[0].rolls) == 2

    def test_critical_miss_auto_misses(self):
        """Test natural 1 always misses regardless of modifiers."""
        roller = DiceRoller(seed=4)  # Produces 1
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=20, level=20)  # Huge modifiers
        target = TargetStats(armor_class=5)  # Very low AC
        weapon = WEAPONS["longsword"]

        result = resolver.resolve_attack(attacker, target, weapon)

        assert result.hit is False
        assert result.natural_roll == 1

    # ==================== Damage Resistance Tests ====================

    def test_damage_resistance_halves_damage(self):
        """Test damage resistance halves damage."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=16)
        target = TargetStats(armor_class=10, resistances={"slashing"})
        weapon = WEAPONS["longsword"]

        result = resolver.resolve_attack(attacker, target, weapon)

        assert result.hit is True
        assert result.damage_modified is True
        assert "resistant" in result.damage_modifier_reason

    def test_damage_immunity_negates_damage(self):
        """Test damage immunity negates all damage."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=16)
        target = TargetStats(armor_class=10, immunities={"slashing"})
        weapon = WEAPONS["longsword"]

        result = resolver.resolve_attack(attacker, target, weapon)

        assert result.hit is True
        assert result.damage_total == 0
        assert result.damage_modified is True
        assert "immune" in result.damage_modifier_reason

    def test_damage_vulnerability_doubles_damage(self):
        """Test damage vulnerability doubles damage."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=16)
        target = TargetStats(armor_class=10, vulnerabilities={"slashing"})
        weapon = WEAPONS["longsword"]

        result = resolver.resolve_attack(attacker, target, weapon)

        assert result.hit is True
        assert result.damage_modified is True
        assert "vulnerable" in result.damage_modifier_reason

    # ==================== Magic Weapon Tests ====================

    def test_magic_weapon_bonus(self):
        """Test magic weapon adds bonus to attack and damage."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=16, level=1)
        target = TargetStats(armor_class=15)
        weapon = WeaponProfile(
            name="+2 Longsword",
            attack_type=AttackType.MELEE_WEAPON,
            damage_dice="1d8",
            damage_type=DamageType.SLASHING,
            magic_bonus=2,
        )

        result = resolver.resolve_attack(attacker, target, weapon)

        # Attack: +3 STR + 2 prof + 2 magic = +7
        assert result.attack_modifier == 7

    # ==================== Advantage/Disadvantage Tests ====================

    def test_attack_with_advantage(self):
        """Test attack with advantage."""
        roller = DiceRoller(seed=42)  # 8, 5 - takes 8
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=16)
        target = TargetStats(armor_class=15)
        weapon = WEAPONS["longsword"]

        result = resolver.resolve_attack(
            attacker, target, weapon, advantage=AdvantageState.ADVANTAGE
        )

        assert result.natural_roll == 8
        assert result.advantage_state == AdvantageState.ADVANTAGE

    def test_attack_with_disadvantage(self):
        """Test attack with disadvantage."""
        roller = DiceRoller(seed=42)  # 8, 5 - takes 5
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=16)
        target = TargetStats(armor_class=15)
        weapon = WEAPONS["longsword"]

        result = resolver.resolve_attack(
            attacker, target, weapon, advantage=AdvantageState.DISADVANTAGE
        )

        assert result.natural_roll == 5
        assert result.advantage_state == AdvantageState.DISADVANTAGE

    # ==================== Versatile Weapon Tests ====================

    def test_versatile_weapon_one_handed(self):
        """Test versatile weapon one-handed damage."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=16)
        target = TargetStats(armor_class=10)
        weapon = WEAPONS["longsword"]  # 1d8 one-handed, 1d10 two-handed

        result = resolver.resolve_attack(attacker, target, weapon, two_handed=False)

        assert result.hit is True
        # Should use 1d8 (die size 8)
        assert result.damage_rolls[0].rolls[0].die_size == 8

    def test_versatile_weapon_two_handed(self):
        """Test versatile weapon two-handed damage."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=16)
        target = TargetStats(armor_class=10)
        weapon = WEAPONS["longsword"]

        result = resolver.resolve_attack(attacker, target, weapon, two_handed=True)

        assert result.hit is True
        # Should use 1d10 (die size 10)
        assert result.damage_rolls[0].rolls[0].die_size == 10

    # ==================== Proficiency Tests ====================

    def test_not_proficient(self):
        """Test attack without proficiency."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        attacker = CharacterStats(strength=16, level=1)  # +2 prof normally
        target = TargetStats(armor_class=10)
        weapon = WEAPONS["longsword"]

        result = resolver.resolve_attack(
            attacker, target, weapon, proficient=False
        )

        # Should only have STR modifier, not proficiency
        assert result.attack_modifier == 3  # Just +3 STR

    # ==================== Deterministic Golden Tests ====================

    def test_deterministic_attack_seed_42(self):
        """Golden test: Attack with seed 42."""
        result = resolve_attack(
            attacker=CharacterStats(strength=16, level=1),
            target=TargetStats(armor_class=15),
            weapon=WEAPONS["longsword"],
            seed=42,
        )

        # Seed 42: attack roll 8, +3 STR, +2 prof = 13 vs AC 15 = miss
        assert result.natural_roll == 8
        assert result.attack_total == 13
        assert result.hit is False

    def test_deterministic_attack_with_hit_seed_12345(self):
        """Golden test: Attack with seed 12345."""
        result = resolve_attack(
            attacker=CharacterStats(strength=16, level=1),
            target=TargetStats(armor_class=15),
            weapon=WEAPONS["longsword"],
            seed=12345,
        )

        # Seed 12345: attack roll 17, +3 STR, +2 prof = 22 vs AC 15 = hit
        assert result.natural_roll == 17
        assert result.attack_total == 22
        assert result.hit is True
        assert result.damage_total > 0

    # ==================== Standalone Functions ====================

    def test_attack_roll_only(self):
        """Test resolving just the attack roll."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        attacker = CharacterStats(intelligence=18, level=5)

        result = resolver.resolve_attack_roll_only(
            attacker, target_ac=15, ability="int"
        )

        # 8 + 4 INT + 3 prof = 15 vs AC 15 = hit
        assert result.hit is True
        assert result.attack_total == 15
        assert result.damage_total == 0  # No damage in this call

    def test_damage_only(self):
        """Test resolving just damage."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        result = resolver.resolve_damage_only(
            damage_dice="2d6",
            modifier=3,
            damage_type=DamageType.FIRE,
        )

        assert result["total"] > 0
        assert result["damage_type"] == "fire"

    def test_damage_only_with_resistance(self):
        """Test damage with target resistance."""
        roller = DiceRoller(seed=42)
        resolver = CombatResolver(roller)

        target = TargetStats(resistances={"fire"})

        result = resolver.resolve_damage_only(
            damage_dice="2d6",
            modifier=3,
            damage_type=DamageType.FIRE,
            target=target,
        )

        assert result["modified"] is True
        assert result["total"] < result["base_damage"]


class TestPrebuiltWeapons:
    """Tests for the WEAPONS dictionary."""

    def test_dagger_is_finesse(self):
        """Test dagger has finesse property."""
        assert WEAPONS["dagger"].finesse is True

    def test_longsword_is_versatile(self):
        """Test longsword is versatile."""
        assert WEAPONS["longsword"].two_handed_damage == "1d10"

    def test_greatsword_damage(self):
        """Test greatsword does 2d6."""
        assert WEAPONS["greatsword"].damage_dice == "2d6"

    def test_shortbow_is_ranged(self):
        """Test shortbow is ranged weapon."""
        assert WEAPONS["shortbow"].attack_type == AttackType.RANGED_WEAPON
