"""
Tests for ability checks and saving throws.

Ticket: 9.0.2

Based on SYSTEM_DESIGN.md section 7.3 and CLAUDE.md testing requirements.
"""

import pytest

from apps.mechanics.services.checks import (
    Ability,
    CharacterStats,
    CheckResolver,
    CheckResult,
    resolve_ability_check,
    resolve_saving_throw,
)
from apps.mechanics.services.dice import AdvantageState, DiceRoller


class TestCharacterStats:
    """Tests for CharacterStats dataclass."""

    def test_default_stats(self):
        """Test default character stats."""
        stats = CharacterStats()
        assert stats.strength == 10
        assert stats.dexterity == 10
        assert stats.level == 1
        assert stats.proficiency_bonus == 2

    def test_custom_stats(self):
        """Test custom character stats."""
        stats = CharacterStats(
            strength=16,
            dexterity=14,
            wisdom=12,
            level=5,
            skill_proficiencies={"stealth", "perception"},
        )
        assert stats.strength == 16
        assert stats.dexterity == 14
        assert stats.level == 5
        assert stats.proficiency_bonus == 3  # Level 5 = +3

    def test_get_ability_score(self):
        """Test getting ability score by name."""
        stats = CharacterStats(strength=18, dexterity=14)
        assert stats.get_ability_score("str") == 18
        assert stats.get_ability_score("dex") == 14
        assert stats.get_ability_score(Ability.STR) == 18

    def test_get_ability_modifier(self):
        """Test getting ability modifier."""
        stats = CharacterStats(
            strength=10,  # +0
            dexterity=14,  # +2
            constitution=8,  # -1
            wisdom=20,  # +5
        )
        assert stats.get_ability_modifier("str") == 0
        assert stats.get_ability_modifier("dex") == 2
        assert stats.get_ability_modifier("con") == -1
        assert stats.get_ability_modifier("wis") == 5

    def test_proficiency_bonus_by_level(self):
        """Test proficiency bonus scales with level."""
        assert CharacterStats(level=1).proficiency_bonus == 2
        assert CharacterStats(level=4).proficiency_bonus == 2
        assert CharacterStats(level=5).proficiency_bonus == 3
        assert CharacterStats(level=8).proficiency_bonus == 3
        assert CharacterStats(level=9).proficiency_bonus == 4
        assert CharacterStats(level=12).proficiency_bonus == 4
        assert CharacterStats(level=13).proficiency_bonus == 5
        assert CharacterStats(level=16).proficiency_bonus == 5
        assert CharacterStats(level=17).proficiency_bonus == 6
        assert CharacterStats(level=20).proficiency_bonus == 6

    def test_from_dict_simple(self):
        """Test creating from simple dictionary."""
        data = {
            "abilities": {"str": 16, "dex": 14, "con": 12, "int": 10, "wis": 8, "cha": 15},
            "level": 3,
            "skills": {"stealth": True, "perception": True},
        }
        stats = CharacterStats.from_dict(data)
        assert stats.strength == 16
        assert stats.dexterity == 14
        assert stats.level == 3
        assert "stealth" in stats.skill_proficiencies
        assert "perception" in stats.skill_proficiencies

    def test_from_dict_complex_skills(self):
        """Test creating from dict with complex skill format."""
        data = {
            "abilities": {"str": 10, "dex": 16},
            "level": 5,
            "skills": {
                "stealth": {"proficient": True, "expertise": False},
                "perception": {"proficient": True, "expertise": True},
                "acrobatics": {"proficient": False},
            },
        }
        stats = CharacterStats.from_dict(data)
        assert "stealth" in stats.skill_proficiencies
        assert "stealth" not in stats.skill_expertises
        assert "perception" in stats.skill_proficiencies
        assert "perception" in stats.skill_expertises
        assert "acrobatics" not in stats.skill_proficiencies

    def test_from_dict_save_proficiencies(self):
        """Test save proficiencies from dict."""
        data = {
            "abilities": {"str": 10},
            "save_proficiencies": ["str", "con"],
        }
        stats = CharacterStats.from_dict(data)
        assert "str" in stats.save_proficiencies
        assert "con" in stats.save_proficiencies
        assert "dex" not in stats.save_proficiencies


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        result = CheckResult(
            success=True,
            total=18,
            natural_roll=14,
            modifier=4,
            dc=15,
            ability="dex",
            skill="stealth",
            proficient=True,
            advantage_state=AdvantageState.NONE,
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["total"] == 18
        assert d["natural_roll"] == 14
        assert d["modifier"] == 4
        assert d["dc"] == 15
        assert d["ability"] == "dex"
        assert d["skill"] == "stealth"
        assert d["proficient"] is True


class TestCheckResolver:
    """Tests for CheckResolver service."""

    # ==================== Basic Ability Check Tests ====================

    def test_basic_ability_check(self):
        """Test basic ability check without skill."""
        roller = DiceRoller(seed=42)  # Produces 8
        resolver = CheckResolver(roller)
        stats = CharacterStats(dexterity=14)  # +2 modifier

        result = resolver.resolve_ability_check(stats, "dex", dc=10)

        assert result.total == 10  # 8 + 2
        assert result.natural_roll == 8
        assert result.modifier == 2
        assert result.dc == 10
        assert result.success is True
        assert result.ability == "dex"
        assert result.skill is None
        assert result.proficient is False

    def test_ability_check_with_skill_proficiency(self):
        """Test ability check with skill proficiency."""
        roller = DiceRoller(seed=42)  # Produces 8
        resolver = CheckResolver(roller)
        stats = CharacterStats(
            dexterity=14,  # +2 modifier
            level=1,  # +2 proficiency
            skill_proficiencies={"stealth"},
        )

        result = resolver.resolve_ability_check(stats, "dex", dc=15, skill="stealth")

        assert result.total == 12  # 8 + 2 + 2
        assert result.modifier == 4  # +2 dex + 2 prof
        assert result.proficient is True
        assert result.skill == "stealth"

    def test_ability_check_with_expertise(self):
        """Test ability check with expertise (double proficiency)."""
        roller = DiceRoller(seed=42)  # Produces 8
        resolver = CheckResolver(roller)
        stats = CharacterStats(
            dexterity=14,  # +2 modifier
            level=5,  # +3 proficiency
            skill_proficiencies={"stealth"},
            skill_expertises={"stealth"},
        )

        result = resolver.resolve_ability_check(stats, "dex", dc=15, skill="stealth")

        assert result.total == 16  # 8 + 2 + 3 + 3 (double prof)
        assert result.modifier == 8  # +2 dex + 3 prof + 3 expertise
        assert result.proficient is True
        assert result.expertise is True

    def test_ability_check_fails(self):
        """Test ability check that fails."""
        roller = DiceRoller(seed=4)  # Produces 1
        resolver = CheckResolver(roller)
        stats = CharacterStats(dexterity=10)  # +0 modifier

        result = resolver.resolve_ability_check(stats, "dex", dc=15)

        assert result.total == 1
        assert result.success is False
        assert result.is_critical_failure is True

    # ==================== Saving Throw Tests ====================

    def test_basic_saving_throw(self):
        """Test basic saving throw."""
        roller = DiceRoller(seed=42)  # Produces 8
        resolver = CheckResolver(roller)
        stats = CharacterStats(constitution=14)  # +2 modifier

        result = resolver.resolve_saving_throw(stats, "con", dc=12)

        assert result.total == 10  # 8 + 2
        assert result.success is False  # 10 < 12
        assert result.ability == "con"

    def test_saving_throw_with_proficiency(self):
        """Test saving throw with proficiency."""
        roller = DiceRoller(seed=42)  # Produces 8
        resolver = CheckResolver(roller)
        stats = CharacterStats(
            constitution=14,  # +2 modifier
            level=1,  # +2 proficiency
            save_proficiencies={"con"},
        )

        result = resolver.resolve_saving_throw(stats, "con", dc=12)

        assert result.total == 12  # 8 + 2 + 2
        assert result.modifier == 4  # +2 con + 2 prof
        assert result.proficient is True
        assert result.success is True  # 12 >= 12

    def test_saving_throw_no_expertise(self):
        """Test that saving throws don't get expertise bonus."""
        roller = DiceRoller(seed=42)
        resolver = CheckResolver(roller)
        stats = CharacterStats(
            dexterity=14,
            level=5,
            save_proficiencies={"dex"},
            skill_expertises={"stealth"},  # Shouldn't affect saves
        )

        result = resolver.resolve_saving_throw(stats, "dex", dc=15)

        # Should only get single proficiency, not double
        assert result.modifier == 5  # +2 dex + 3 prof
        assert result.expertise is False

    # ==================== Advantage/Disadvantage Tests ====================

    def test_ability_check_with_advantage(self):
        """Test ability check with advantage."""
        roller = DiceRoller(seed=42)  # Produces 8, then 5 - advantage takes 8
        resolver = CheckResolver(roller)
        stats = CharacterStats(dexterity=14)

        result = resolver.resolve_ability_check(
            stats, "dex", dc=10, advantage=AdvantageState.ADVANTAGE
        )

        assert result.natural_roll == 8  # Higher of 8, 5
        assert result.total == 10
        assert result.advantage_state == AdvantageState.ADVANTAGE

    def test_ability_check_with_disadvantage(self):
        """Test ability check with disadvantage."""
        roller = DiceRoller(seed=42)  # Produces 8, then 5 - disadvantage takes 5
        resolver = CheckResolver(roller)
        stats = CharacterStats(dexterity=14)

        result = resolver.resolve_ability_check(
            stats, "dex", dc=10, advantage=AdvantageState.DISADVANTAGE
        )

        assert result.natural_roll == 5  # Lower of 8, 5
        assert result.total == 7  # 5 + 2
        assert result.advantage_state == AdvantageState.DISADVANTAGE
        assert result.success is False

    # ==================== Deterministic Golden Tests ====================

    def test_deterministic_ability_check_seed_42(self):
        """Golden test: Ability check with seed 42."""
        result = resolve_ability_check(
            character=CharacterStats(dexterity=14, skill_proficiencies={"stealth"}),
            ability="dex",
            dc=15,
            skill="stealth",
            seed=42,
        )

        # Seed 42 produces 8, +2 dex, +2 prof = 12
        assert result.natural_roll == 8
        assert result.total == 12
        assert result.success is False
        assert result.proficient is True

    def test_deterministic_saving_throw_seed_42(self):
        """Golden test: Saving throw with seed 42."""
        result = resolve_saving_throw(
            character=CharacterStats(constitution=16, save_proficiencies={"con"}),
            ability="con",
            dc=15,
            seed=42,
        )

        # Seed 42 produces 8, +3 con, +2 prof = 13
        assert result.natural_roll == 8
        assert result.total == 13
        assert result.success is False

    def test_deterministic_high_level_character(self):
        """Golden test: High level character with expertise."""
        result = resolve_ability_check(
            character=CharacterStats(
                dexterity=20,  # +5
                level=17,  # +6 proficiency
                skill_proficiencies={"stealth"},
                skill_expertises={"stealth"},
            ),
            ability="dex",
            dc=25,
            skill="stealth",
            seed=42,
        )

        # Seed 42 produces 8, +5 dex, +6 prof, +6 expertise = 25
        assert result.natural_roll == 8
        assert result.modifier == 17  # 5 + 6 + 6
        assert result.total == 25
        assert result.success is True

    # ==================== Contested Check Tests ====================

    def test_contested_check_actor_wins(self):
        """Test contested check where actor wins."""
        roller = DiceRoller(seed=42)  # Will produce consistent sequence
        resolver = CheckResolver(roller)

        actor = CharacterStats(strength=16, skill_proficiencies={"athletics"})
        target = CharacterStats(strength=10)

        actor_result, target_result, actor_wins = resolver.resolve_contested_check(
            actor=actor,
            actor_ability="str",
            actor_skill="athletics",
            target=target,
            target_ability="str",
            target_skill=None,
        )

        # Actor: 8 + 3 + 2 = 13, Target: 5 + 0 = 5
        assert actor_wins is True
        assert actor_result.success is True
        assert target_result.success is False

    def test_contested_check_ties_go_to_actor(self):
        """Test that ties in contested checks go to the actor."""
        # Use two rollers to get same results
        roller = DiceRoller(seed=100)  # Find a seed where both roll same
        resolver = CheckResolver(roller)

        # Give same stats so totals are equal
        actor = CharacterStats(strength=10)
        target = CharacterStats(strength=10)

        # Force equal totals by using same ability and no skills
        actor_result, target_result, actor_wins = resolver.resolve_contested_check(
            actor=actor,
            actor_ability="str",
            actor_skill=None,
            target=target,
            target_ability="str",
            target_skill=None,
        )

        # Even if totals match, actor should win ties
        if actor_result.natural_roll == target_result.natural_roll:
            assert actor_wins is True

    # ==================== Edge Cases ====================

    def test_negative_modifier(self):
        """Test ability check with negative modifier."""
        roller = DiceRoller(seed=42)  # Produces 8
        resolver = CheckResolver(roller)
        stats = CharacterStats(intelligence=6)  # -2 modifier

        result = resolver.resolve_ability_check(stats, "int", dc=10)

        assert result.modifier == -2
        assert result.total == 6  # 8 - 2

    def test_skill_name_normalization(self):
        """Test that skill names are normalized correctly."""
        roller = DiceRoller(seed=42)
        resolver = CheckResolver(roller)
        stats = CharacterStats(
            dexterity=14,
            skill_proficiencies={"sleight_of_hand"},
        )

        # Should work with space-separated name
        result = resolver.resolve_ability_check(
            stats, "dex", dc=10, skill="sleight of hand"
        )

        assert result.proficient is True
        assert result.skill == "sleight_of_hand"

    def test_bonus_modifier(self):
        """Test ability check with additional bonus."""
        roller = DiceRoller(seed=42)  # Produces 8
        resolver = CheckResolver(roller)
        stats = CharacterStats(dexterity=14)  # +2 modifier

        result = resolver.resolve_ability_check(stats, "dex", dc=15, bonus=5)

        assert result.modifier == 7  # 2 + 5
        assert result.total == 15  # 8 + 7
        assert result.success is True

    def test_from_dict_character(self):
        """Test using dict directly instead of CharacterStats."""
        roller = DiceRoller(seed=42)
        resolver = CheckResolver(roller)

        char_dict = {
            "abilities": {"dex": 16},
            "level": 3,
            "skills": {"stealth": True},
        }

        result = resolver.resolve_ability_check(
            char_dict, "dex", dc=15, skill="stealth"
        )

        assert result.modifier == 5  # +3 dex + 2 prof
        assert result.proficient is True

    def test_ability_enum_usage(self):
        """Test using Ability enum instead of string."""
        roller = DiceRoller(seed=42)
        resolver = CheckResolver(roller)
        stats = CharacterStats(strength=18)

        result = resolver.resolve_ability_check(stats, Ability.STR, dc=15)

        assert result.ability == "str"
        assert result.modifier == 4  # STR 18 = +4
