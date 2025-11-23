"""
Unit tests for LevelingService.

Tests cover XP thresholds, level up mechanics, HP calculations,
and multiclass requirements following SRD 5.2 rules.
"""

import pytest
from django.contrib.auth import get_user_model

from apps.characters.models import CharacterSheet
from apps.characters.services.leveling import (
    CLASS_HIT_DICE,
    MULTICLASS_REQUIREMENTS,
    XP_THRESHOLDS,
    LevelingService,
)

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testleveling",
        email="leveling@test.com",
        password="testpass123",
    )


@pytest.fixture
def level_1_fighter(user):
    """Create a level 1 fighter character."""
    return CharacterSheet.objects.create(
        user=user,
        name="Test Fighter",
        species="Human",
        character_class="Fighter",
        background="Soldier",
        level=1,
        experience_points=0,
        hit_points_max=12,
        hit_points_current=12,
        ability_scores_json={
            "str": 16,
            "dex": 14,
            "con": 14,
            "int": 10,
            "wis": 12,
            "cha": 8,
        },
        hit_dice_json={"d10": {"max": 1, "spent": 0}},
    )


@pytest.fixture
def level_4_wizard(user):
    """Create a level 4 wizard character."""
    return CharacterSheet.objects.create(
        user=user,
        name="Test Wizard",
        species="Elf",
        character_class="Wizard",
        background="Sage",
        level=4,
        experience_points=2700,  # Exactly at level 4
        hit_points_max=18,
        hit_points_current=18,
        ability_scores_json={
            "str": 8,
            "dex": 14,
            "con": 12,
            "int": 17,
            "wis": 13,
            "cha": 10,
        },
        hit_dice_json={"d6": {"max": 4, "spent": 0}},
    )


@pytest.fixture
def leveling_service():
    """Create a leveling service instance."""
    return LevelingService()


class TestXPThresholds:
    """Tests for XP threshold calculations."""

    def test_xp_thresholds_defined_for_all_levels(self):
        """XP thresholds should be defined for levels 1-20."""
        for level in range(1, 21):
            assert level in XP_THRESHOLDS

    def test_xp_thresholds_increase(self):
        """XP thresholds should increase with each level."""
        for level in range(2, 21):
            assert XP_THRESHOLDS[level] > XP_THRESHOLDS[level - 1]

    def test_level_1_requires_0_xp(self, leveling_service):
        """Level 1 requires 0 XP."""
        assert leveling_service.get_xp_for_level(1) == 0

    def test_level_2_requires_300_xp(self, leveling_service):
        """Level 2 requires 300 XP."""
        assert leveling_service.get_xp_for_level(2) == 300

    def test_level_20_requires_355000_xp(self, leveling_service):
        """Level 20 requires 355,000 XP."""
        assert leveling_service.get_xp_for_level(20) == 355000


class TestGetLevelForXP:
    """Tests for determining level from XP."""

    def test_0_xp_is_level_1(self, leveling_service):
        """0 XP should be level 1."""
        assert leveling_service.get_level_for_xp(0) == 1

    def test_299_xp_is_level_1(self, leveling_service):
        """299 XP should still be level 1."""
        assert leveling_service.get_level_for_xp(299) == 1

    def test_300_xp_is_level_2(self, leveling_service):
        """300 XP should be level 2."""
        assert leveling_service.get_level_for_xp(300) == 2

    def test_899_xp_is_level_2(self, leveling_service):
        """899 XP should be level 2."""
        assert leveling_service.get_level_for_xp(899) == 2

    def test_900_xp_is_level_3(self, leveling_service):
        """900 XP should be level 3."""
        assert leveling_service.get_level_for_xp(900) == 3

    def test_huge_xp_is_level_20(self, leveling_service):
        """Very high XP should cap at level 20."""
        assert leveling_service.get_level_for_xp(1000000) == 20


class TestXPInfo:
    """Tests for XP info retrieval."""

    def test_xp_info_level_1(self, leveling_service, level_1_fighter):
        """XP info for level 1 character."""
        info = leveling_service.get_xp_info(level_1_fighter)
        assert info.current_level == 1
        assert info.current_xp == 0
        assert info.xp_for_next_level == 300
        assert info.xp_needed == 300
        assert info.can_level_up is False

    def test_xp_info_ready_to_level(self, leveling_service, level_1_fighter):
        """XP info when character has enough XP to level."""
        level_1_fighter.experience_points = 300
        level_1_fighter.save()

        info = leveling_service.get_xp_info(level_1_fighter)
        assert info.can_level_up is True
        assert info.xp_needed == 0

    def test_xp_info_level_20(self, leveling_service, user):
        """XP info for max level character."""
        char = CharacterSheet.objects.create(
            user=user,
            name="Epic Hero",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=20,
            experience_points=400000,
            ability_scores_json={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        )
        info = leveling_service.get_xp_info(char)
        assert info.current_level == 20
        assert info.can_level_up is False
        assert info.xp_needed == 0


class TestAddXP:
    """Tests for XP addition."""

    def test_add_xp(self, leveling_service, level_1_fighter):
        """Can add XP to character."""
        info = leveling_service.add_xp(level_1_fighter, 150)
        assert info.current_xp == 150
        assert level_1_fighter.experience_points == 150

    def test_add_xp_enables_level_up(self, leveling_service, level_1_fighter):
        """Adding enough XP enables level up."""
        info = leveling_service.add_xp(level_1_fighter, 300)
        assert info.can_level_up is True


class TestHitDie:
    """Tests for hit die calculations."""

    def test_fighter_hit_die(self, leveling_service):
        """Fighter should have d10 hit die."""
        assert leveling_service.get_hit_die_for_class("Fighter") == 10

    def test_wizard_hit_die(self, leveling_service):
        """Wizard should have d6 hit die."""
        assert leveling_service.get_hit_die_for_class("Wizard") == 6

    def test_barbarian_hit_die(self, leveling_service):
        """Barbarian should have d12 hit die."""
        assert leveling_service.get_hit_die_for_class("Barbarian") == 12

    def test_cleric_hit_die(self, leveling_service):
        """Cleric should have d8 hit die."""
        assert leveling_service.get_hit_die_for_class("Cleric") == 8

    def test_unknown_class_defaults_to_d8(self, leveling_service):
        """Unknown class defaults to d8."""
        assert leveling_service.get_hit_die_for_class("UnknownClass") == 8


class TestHPCalculation:
    """Tests for HP gain calculations."""

    def test_average_hp_fighter_con_14(self, leveling_service):
        """Fighter with CON 14 should gain 8 HP (6 + 2)."""
        # d10 average = 6, CON mod = +2
        hp = leveling_service.calculate_hp_gain("Fighter", 2, use_average=True)
        assert hp == 8

    def test_average_hp_wizard_con_12(self, leveling_service):
        """Wizard with CON 12 should gain 5 HP (4 + 1)."""
        # d6 average = 4, CON mod = +1
        hp = leveling_service.calculate_hp_gain("Wizard", 1, use_average=True)
        assert hp == 5

    def test_rolled_hp(self, leveling_service):
        """Can use actual roll instead of average."""
        # d10, rolled 8, CON mod +2 = 10
        hp = leveling_service.calculate_hp_gain(
            "Fighter", 2, roll_result=8, use_average=False
        )
        assert hp == 10

    def test_minimum_hp_gain_is_1(self, leveling_service):
        """HP gain minimum is 1 even with negative CON."""
        # d6, rolled 1, CON mod -3 = would be -2, but minimum is 1
        hp = leveling_service.calculate_hp_gain(
            "Wizard", -3, roll_result=1, use_average=False
        )
        assert hp == 1

    def test_first_level_hp(self, leveling_service):
        """First level HP is max hit die + CON mod."""
        # Fighter d10 = 10, CON mod +2 = 12
        hp = leveling_service.calculate_first_level_hp("Fighter", 2)
        assert hp == 12


class TestLevelUp:
    """Tests for level up operation."""

    def test_level_up_success(self, leveling_service, level_1_fighter):
        """Can successfully level up."""
        result = leveling_service.level_up(level_1_fighter)
        assert result.success is True
        assert result.new_level == 2
        assert result.hp_gained == 8  # d10 avg (6) + CON mod (2)
        assert result.hit_die_added == "d10"
        assert level_1_fighter.level == 2

    def test_level_up_increases_hp(self, leveling_service, level_1_fighter):
        """Level up increases HP correctly."""
        initial_hp = level_1_fighter.hit_points_max
        result = leveling_service.level_up(level_1_fighter)
        assert level_1_fighter.hit_points_max == initial_hp + result.hp_gained

    def test_level_up_adds_hit_die(self, leveling_service, level_1_fighter):
        """Level up adds a hit die."""
        leveling_service.level_up(level_1_fighter)
        assert level_1_fighter.hit_dice_json["d10"]["max"] == 2

    def test_cannot_level_past_20(self, leveling_service, user):
        """Cannot level past 20."""
        char = CharacterSheet.objects.create(
            user=user,
            name="Max Level",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=20,
            ability_scores_json={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        )
        result = leveling_service.level_up(char)
        assert result.success is False
        assert "max_level" in result.errors[0]


class TestMulticlassRequirements:
    """Tests for multiclass requirement validation."""

    def test_multiclass_requirements_defined(self):
        """Multiclass requirements defined for all SRD classes."""
        for class_name in CLASS_HIT_DICE:
            assert class_name in MULTICLASS_REQUIREMENTS

    def test_can_multiclass_with_requirements(self, leveling_service, level_1_fighter):
        """Can multiclass when requirements are met."""
        # Fighter has STR 16, can multiclass to Barbarian (STR 13)
        errors = leveling_service.check_multiclass_requirements(
            level_1_fighter, "Barbarian"
        )
        assert errors == []

    def test_cannot_multiclass_without_requirements(self, leveling_service, level_1_fighter):
        """Cannot multiclass when requirements not met."""
        # Fighter has CHA 8, cannot multiclass to Bard (CHA 13)
        errors = leveling_service.check_multiclass_requirements(
            level_1_fighter, "Bard"
        )
        assert len(errors) > 0
        assert "CHA" in errors[0]

    def test_fighter_multiclass_str_or_dex(self, leveling_service, user):
        """Fighter can multiclass with either STR or DEX."""
        # Character with DEX 13 but STR 8
        char = CharacterSheet.objects.create(
            user=user,
            name="Dex Fighter",
            species="Human",
            character_class="Rogue",
            background="Criminal",
            level=1,
            ability_scores_json={
                "str": 8,
                "dex": 14,
                "con": 10,
                "int": 10,
                "wis": 10,
                "cha": 10,
            },
        )
        errors = leveling_service.check_multiclass_requirements(char, "Fighter")
        assert errors == []

    def test_multiclass_checks_both_classes(self, leveling_service, user):
        """Multiclass checks requirements for both classes."""
        # Character with low WIS trying to multiclass from Cleric
        char = CharacterSheet.objects.create(
            user=user,
            name="Low Wis Cleric",
            species="Human",
            character_class="Cleric",
            background="Acolyte",
            level=1,
            ability_scores_json={
                "str": 10,
                "dex": 10,
                "con": 10,
                "int": 14,
                "wis": 10,  # Below 13 requirement
                "cha": 10,
            },
        )
        errors = leveling_service.check_multiclass_requirements(char, "Wizard")
        # Should fail both leaving Cleric (WIS 13) and entering Wizard
        assert len(errors) >= 1


class TestMulticlassLevelUp:
    """Tests for multiclass level up."""

    def test_multiclass_level_up(self, leveling_service, level_4_wizard):
        """Can level up in a different class."""
        # Wizard has INT 17, WIS 13 - can multiclass to Cleric
        result = leveling_service.level_up(level_4_wizard, "Cleric")
        assert result.success is True
        assert result.new_level == 5
        assert result.hit_die_added == "d8"  # Cleric hit die
        assert level_4_wizard.multiclass_json == {"Wizard": 4, "Cleric": 1}

    def test_multiclass_level_up_fails_without_requirements(
        self, leveling_service, level_4_wizard
    ):
        """Multiclass level up fails when requirements not met."""
        # Wizard has STR 8 - cannot multiclass to Fighter
        result = leveling_service.level_up(level_4_wizard, "Fighter")
        assert result.success is False
        assert len(result.errors) > 0

    def test_multiclass_adds_different_hit_die(self, leveling_service, level_4_wizard):
        """Multiclass adds hit die of new class."""
        leveling_service.level_up(level_4_wizard, "Cleric")
        assert "d8" in level_4_wizard.hit_dice_json
        assert level_4_wizard.hit_dice_json["d8"]["max"] == 1


class TestProficiencyBonus:
    """Tests for proficiency bonus calculation."""

    def test_level_1_to_4_proficiency(self, leveling_service):
        """Levels 1-4 have +2 proficiency."""
        for level in range(1, 5):
            assert leveling_service.get_proficiency_bonus(level) == 2

    def test_level_5_to_8_proficiency(self, leveling_service):
        """Levels 5-8 have +3 proficiency."""
        for level in range(5, 9):
            assert leveling_service.get_proficiency_bonus(level) == 3

    def test_level_9_to_12_proficiency(self, leveling_service):
        """Levels 9-12 have +4 proficiency."""
        for level in range(9, 13):
            assert leveling_service.get_proficiency_bonus(level) == 4

    def test_level_13_to_16_proficiency(self, leveling_service):
        """Levels 13-16 have +5 proficiency."""
        for level in range(13, 17):
            assert leveling_service.get_proficiency_bonus(level) == 5

    def test_level_17_to_20_proficiency(self, leveling_service):
        """Levels 17-20 have +6 proficiency."""
        for level in range(17, 21):
            assert leveling_service.get_proficiency_bonus(level) == 6


class TestSyncLevelWithXP:
    """Tests for syncing level with XP."""

    def test_sync_gains_multiple_levels(self, leveling_service, level_1_fighter):
        """Sync can gain multiple levels at once."""
        # Give enough XP for level 5 (6500)
        level_1_fighter.experience_points = 6500
        level_1_fighter.save()

        levels_gained = leveling_service.sync_level_with_xp(level_1_fighter)
        assert levels_gained == 4  # Level 1 -> 5
        assert level_1_fighter.level == 5

    def test_sync_no_levels_needed(self, leveling_service, level_4_wizard):
        """Sync does nothing when already at correct level."""
        levels_gained = leveling_service.sync_level_with_xp(level_4_wizard)
        assert levels_gained == 0
        assert level_4_wizard.level == 4
