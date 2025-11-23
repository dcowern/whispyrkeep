"""
Tests for character leveling service.

Tests the LevelingService for SRD 5.2 leveling mechanics.
"""

import pytest
from django.contrib.auth import get_user_model

from apps.characters.leveling import (
    ASI_LEVELS,
    FIGHTER_ASI_LEVELS,
    PROFICIENCY_BONUS,
    ROGUE_ASI_LEVELS,
    XP_THRESHOLDS,
    LevelingService,
)
from apps.characters.models import CharacterSheet

User = get_user_model()


@pytest.fixture
def leveling_service():
    """Create leveling service."""
    return LevelingService()


@pytest.fixture
def user():
    """Create test user."""
    return User.objects.create_user(
        username="testplayer",
        email="player@example.com",
        password="testpass123",
    )


@pytest.fixture
def character(user):
    """Create test character at level 3."""
    return CharacterSheet.objects.create(
        user=user,
        name="Test Character",
        species="Human",
        character_class="Fighter",
        background="Soldier",
        level=3,
        ability_scores_json={
            "str": 16,
            "dex": 14,
            "con": 14,  # +2 modifier
            "int": 10,
            "wis": 12,
            "cha": 8,
        },
    )


class TestXPThresholds:
    """Tests for XP-to-level calculations."""

    def test_xp_thresholds_has_all_levels(self):
        """Test that XP thresholds has entries for levels 1-20."""
        for level in range(1, 21):
            assert level in XP_THRESHOLDS

    def test_xp_thresholds_monotonic(self):
        """Test that XP thresholds are monotonically increasing."""
        prev_xp = 0
        for level in range(1, 21):
            assert XP_THRESHOLDS[level] >= prev_xp
            prev_xp = XP_THRESHOLDS[level]

    def test_get_level_for_xp(self, leveling_service):
        """Test getting level from XP."""
        assert leveling_service.get_level_for_xp(0) == 1
        assert leveling_service.get_level_for_xp(299) == 1
        assert leveling_service.get_level_for_xp(300) == 2
        assert leveling_service.get_level_for_xp(899) == 2
        assert leveling_service.get_level_for_xp(900) == 3

    def test_get_level_for_xp_max_level(self, leveling_service):
        """Test that XP cannot exceed level 20."""
        assert leveling_service.get_level_for_xp(355000) == 20
        assert leveling_service.get_level_for_xp(1000000) == 20

    def test_get_xp_for_level(self, leveling_service):
        """Test getting XP threshold for level."""
        assert leveling_service.get_xp_for_level(1) == 0
        assert leveling_service.get_xp_for_level(2) == 300
        assert leveling_service.get_xp_for_level(5) == 6500
        assert leveling_service.get_xp_for_level(20) == 355000

    def test_get_xp_to_next_level(self, leveling_service):
        """Test getting XP needed for next level."""
        assert leveling_service.get_xp_to_next_level(1, 0) == 300
        assert leveling_service.get_xp_to_next_level(1, 150) == 150
        assert leveling_service.get_xp_to_next_level(1, 300) == 0

    def test_get_xp_to_next_level_at_max(self, leveling_service):
        """Test that max level returns None for next level XP."""
        assert leveling_service.get_xp_to_next_level(20, 400000) is None


class TestProficiencyBonus:
    """Tests for proficiency bonus calculations."""

    def test_proficiency_bonus_has_all_levels(self):
        """Test proficiency bonus has entries for all levels."""
        for level in range(1, 21):
            assert level in PROFICIENCY_BONUS

    def test_proficiency_bonus_values(self, leveling_service):
        """Test proficiency bonus increases at correct levels."""
        # Levels 1-4: +2
        for level in [1, 2, 3, 4]:
            assert leveling_service.get_proficiency_bonus(level) == 2

        # Levels 5-8: +3
        for level in [5, 6, 7, 8]:
            assert leveling_service.get_proficiency_bonus(level) == 3

        # Levels 9-12: +4
        for level in [9, 10, 11, 12]:
            assert leveling_service.get_proficiency_bonus(level) == 4

        # Levels 13-16: +5
        for level in [13, 14, 15, 16]:
            assert leveling_service.get_proficiency_bonus(level) == 5

        # Levels 17-20: +6
        for level in [17, 18, 19, 20]:
            assert leveling_service.get_proficiency_bonus(level) == 6


class TestAbilityModifier:
    """Tests for ability modifier calculations."""

    def test_ability_modifier_calculation(self, leveling_service):
        """Test ability modifier formula."""
        # Score 10-11 = +0
        assert leveling_service.calculate_ability_modifier(10) == 0
        assert leveling_service.calculate_ability_modifier(11) == 0

        # Score 12-13 = +1
        assert leveling_service.calculate_ability_modifier(12) == 1
        assert leveling_service.calculate_ability_modifier(13) == 1

        # Score 14-15 = +2
        assert leveling_service.calculate_ability_modifier(14) == 2
        assert leveling_service.calculate_ability_modifier(15) == 2

        # Score 8-9 = -1
        assert leveling_service.calculate_ability_modifier(8) == -1
        assert leveling_service.calculate_ability_modifier(9) == -1

        # Score 6-7 = -2
        assert leveling_service.calculate_ability_modifier(6) == -2
        assert leveling_service.calculate_ability_modifier(7) == -2

    def test_ability_modifier_extremes(self, leveling_service):
        """Test ability modifier at extreme values."""
        assert leveling_service.calculate_ability_modifier(1) == -5
        assert leveling_service.calculate_ability_modifier(20) == 5
        assert leveling_service.calculate_ability_modifier(30) == 10


class TestHPCalculation:
    """Tests for hit point calculations."""

    def test_hp_average_d10_positive_con(self, leveling_service):
        """Test average HP calculation with d10 and positive CON."""
        result = leveling_service.calculate_hp_increase(
            hit_die=10, constitution_modifier=2, use_average=True
        )

        assert result.used_average is True
        assert result.roll_result is None
        assert result.hit_die == 10
        assert result.constitution_modifier == 2
        # Average of d10 is 6, plus 2 CON = 8
        assert result.total == 8

    def test_hp_average_d8_negative_con(self, leveling_service):
        """Test average HP with negative CON modifier."""
        result = leveling_service.calculate_hp_increase(
            hit_die=8, constitution_modifier=-2, use_average=True
        )

        # Average of d8 is 5, minus 2 CON = 3
        assert result.total == 3

    def test_hp_minimum_is_one(self, leveling_service):
        """Test that HP increase is at least 1."""
        result = leveling_service.calculate_hp_increase(
            hit_die=6, constitution_modifier=-10, use_average=True
        )

        # Even with -10 CON, minimum is 1
        assert result.total == 1

    def test_hp_roll_deterministic(self, leveling_service):
        """Test that HP roll is deterministic with seed."""
        result1 = leveling_service.calculate_hp_increase(
            hit_die=10, constitution_modifier=2, use_average=False, seed=42
        )
        result2 = leveling_service.calculate_hp_increase(
            hit_die=10, constitution_modifier=2, use_average=False, seed=42
        )

        assert result1.roll_result == result2.roll_result
        assert result1.total == result2.total
        assert result1.used_average is False

    def test_hp_roll_in_range(self, leveling_service):
        """Test that HP roll is within die range."""
        for _ in range(20):
            result = leveling_service.calculate_hp_increase(
                hit_die=8, constitution_modifier=0, use_average=False
            )
            assert 1 <= result.roll_result <= 8


class TestASILevels:
    """Tests for Ability Score Improvement levels."""

    def test_standard_asi_levels(self, leveling_service):
        """Test standard class ASI levels."""
        assert ASI_LEVELS == {4, 8, 12, 16, 19}

    def test_fighter_asi_levels(self, leveling_service):
        """Test Fighter gets extra ASIs."""
        asi_levels = leveling_service.get_asi_levels_for_class("Fighter")
        assert 6 in asi_levels  # Fighter extra
        assert 14 in asi_levels  # Fighter extra
        assert asi_levels == FIGHTER_ASI_LEVELS

    def test_rogue_asi_levels(self, leveling_service):
        """Test Rogue gets extra ASI."""
        asi_levels = leveling_service.get_asi_levels_for_class("Rogue")
        assert 10 in asi_levels  # Rogue extra
        assert asi_levels == ROGUE_ASI_LEVELS

    def test_wizard_standard_asi_levels(self, leveling_service):
        """Test Wizard has standard ASI levels."""
        asi_levels = leveling_service.get_asi_levels_for_class("Wizard")
        assert asi_levels == ASI_LEVELS


class TestSubclassLevels:
    """Tests for subclass selection levels."""

    def test_standard_subclass_level_3(self, leveling_service):
        """Test most classes get subclass at level 3."""
        for class_name in ["Fighter", "Barbarian", "Ranger", "Monk", "Paladin"]:
            assert leveling_service.get_subclass_level_for_class(class_name) == 3

    def test_cleric_subclass_level_1(self, leveling_service):
        """Test Cleric gets subclass at level 1."""
        assert leveling_service.get_subclass_level_for_class("Cleric") == 1

    def test_sorcerer_subclass_level_1(self, leveling_service):
        """Test Sorcerer gets subclass at level 1."""
        assert leveling_service.get_subclass_level_for_class("Sorcerer") == 1

    def test_warlock_subclass_level_1(self, leveling_service):
        """Test Warlock gets subclass at level 1."""
        assert leveling_service.get_subclass_level_for_class("Warlock") == 1

    def test_wizard_subclass_level_2(self, leveling_service):
        """Test Wizard gets subclass at level 2."""
        assert leveling_service.get_subclass_level_for_class("Wizard") == 2


@pytest.mark.django_db
class TestLevelUp:
    """Tests for level-up operations."""

    def test_level_up_success(self, leveling_service, character):
        """Test successful level up."""
        result = leveling_service.level_up(character, use_average_hp=True)

        assert result.success is True
        assert result.new_level == 4
        assert result.hp_increase > 0
        assert result.proficiency_bonus == 2  # Still +2 at level 4

    def test_level_up_asi_at_4(self, leveling_service, character):
        """Test ASI available at level 4."""
        result = leveling_service.level_up(character, use_average_hp=True)

        assert result.can_select_asi is True
        assert any("ability score" in msg.lower() for msg in result.messages)

    def test_level_up_proficiency_increase_at_5(self, leveling_service, character):
        """Test proficiency bonus increases at level 5."""
        # Level up to 4 first
        character.level = 4
        character.save()

        result = leveling_service.level_up(character, use_average_hp=True)

        assert result.proficiency_bonus == 3
        assert any("proficiency" in msg.lower() for msg in result.messages)

    def test_level_up_max_level(self, leveling_service, character):
        """Test cannot level up at max level."""
        character.level = 20
        character.save()

        result = leveling_service.level_up(character)

        assert result.success is False
        assert "maximum level" in result.errors[0].lower()

    def test_level_up_deterministic_hp(self, leveling_service, character):
        """Test level up with deterministic HP roll."""
        result1 = leveling_service.level_up(
            character, use_average_hp=False, hp_roll_seed=42
        )
        # Reset character
        character.level = 3
        result2 = leveling_service.level_up(
            character, use_average_hp=False, hp_roll_seed=42
        )

        assert result1.hp_increase == result2.hp_increase

    def test_apply_level_up_saves(self, leveling_service, character):
        """Test that apply_level_up saves changes."""
        original_level = character.level
        result = leveling_service.apply_level_up(character, use_average_hp=True)

        character.refresh_from_db()
        assert character.level == original_level + 1
        assert result.success is True


@pytest.mark.django_db
class TestLevelSummary:
    """Tests for level summary generation."""

    def test_level_summary(self, leveling_service):
        """Test level summary generation."""
        summary = leveling_service.get_level_summary(5, "Fighter")

        assert summary["level"] == 5
        assert summary["proficiency_bonus"] == 3
        assert summary["xp_required"] == 6500
        assert summary["hit_die"] == "d10"
        assert 6 in summary["asi_levels_remaining"]  # Fighter extra ASI

    def test_level_summary_max_level(self, leveling_service):
        """Test level summary at max level."""
        summary = leveling_service.get_level_summary(20, "Wizard")

        assert summary["level"] == 20
        assert summary["xp_to_next"] is None
        assert summary["next_asi_level"] is None
        assert summary["asi_levels_remaining"] == []


class TestHitDie:
    """Tests for hit die retrieval."""

    def test_barbarian_d12(self, leveling_service):
        """Test Barbarian has d12 hit die."""
        assert leveling_service._get_hit_die_for_class("Barbarian") == 12

    def test_fighter_d10(self, leveling_service):
        """Test Fighter has d10 hit die."""
        assert leveling_service._get_hit_die_for_class("Fighter") == 10

    def test_rogue_d8(self, leveling_service):
        """Test Rogue has d8 hit die."""
        assert leveling_service._get_hit_die_for_class("Rogue") == 8

    def test_wizard_d6(self, leveling_service):
        """Test Wizard has d6 hit die."""
        assert leveling_service._get_hit_die_for_class("Wizard") == 6

    def test_unknown_class_defaults_d8(self, leveling_service):
        """Test unknown class defaults to d8."""
        assert leveling_service._get_hit_die_for_class("UnknownClass") == 8
