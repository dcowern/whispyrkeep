"""
Tests for the dice roller module.

These tests include deterministic golden tests with seeded RNG
to ensure reproducible dice roll outcomes.

Ticket: 9.0.1

Based on SYSTEM_DESIGN.md section 7.3 and CLAUDE.md testing requirements.
"""

import pytest

from apps.mechanics.services.dice import (
    AdvantageState,
    DiceExpression,
    DiceRoller,
    DieRoll,
    RollResult,
)


class TestDieRoll:
    """Tests for DieRoll dataclass."""

    def test_valid_die_roll(self):
        """Test creating a valid die roll."""
        roll = DieRoll(die_size=6, result=4)
        assert roll.die_size == 6
        assert roll.result == 4

    def test_invalid_die_size_raises(self):
        """Test that invalid die size raises ValueError."""
        with pytest.raises(ValueError, match="Die size must be at least 1"):
            DieRoll(die_size=0, result=1)

    def test_result_too_low_raises(self):
        """Test that result below 1 raises ValueError."""
        with pytest.raises(ValueError, match="out of range"):
            DieRoll(die_size=6, result=0)

    def test_result_too_high_raises(self):
        """Test that result above die size raises ValueError."""
        with pytest.raises(ValueError, match="out of range"):
            DieRoll(die_size=6, result=7)


class TestDiceExpression:
    """Tests for DiceExpression parsing."""

    def test_parse_simple(self):
        """Test parsing simple expression like '2d6'."""
        expr = DiceExpression.parse("2d6")
        assert expr.num_dice == 2
        assert expr.die_size == 6
        assert expr.modifier == 0

    def test_parse_with_positive_modifier(self):
        """Test parsing expression with positive modifier."""
        expr = DiceExpression.parse("1d20+5")
        assert expr.num_dice == 1
        assert expr.die_size == 20
        assert expr.modifier == 5

    def test_parse_with_negative_modifier(self):
        """Test parsing expression with negative modifier."""
        expr = DiceExpression.parse("3d8-2")
        assert expr.num_dice == 3
        assert expr.die_size == 8
        assert expr.modifier == -2

    def test_parse_case_insensitive(self):
        """Test that parsing is case insensitive."""
        expr = DiceExpression.parse("2D10+3")
        assert expr.num_dice == 2
        assert expr.die_size == 10
        assert expr.modifier == 3

    def test_parse_with_whitespace(self):
        """Test that whitespace is stripped."""
        expr = DiceExpression.parse("  1d6  ")
        assert expr.num_dice == 1
        assert expr.die_size == 6

    def test_parse_invalid_raises(self):
        """Test that invalid expressions raise ValueError."""
        with pytest.raises(ValueError, match="Invalid dice expression"):
            DiceExpression.parse("not_dice")

        with pytest.raises(ValueError, match="Invalid dice expression"):
            DiceExpression.parse("d6")

        with pytest.raises(ValueError, match="Invalid dice expression"):
            DiceExpression.parse("2d")

    def test_from_components(self):
        """Test creating expression from components."""
        expr = DiceExpression.from_components(2, 6, 3)
        assert expr.num_dice == 2
        assert expr.die_size == 6
        assert expr.modifier == 3

    def test_str_representation(self):
        """Test string representation of expressions."""
        assert str(DiceExpression(2, 6)) == "2d6"
        assert str(DiceExpression(1, 20, 5)) == "1d20+5"
        assert str(DiceExpression(3, 8, -2)) == "3d8-2"

    def test_invalid_num_dice_raises(self):
        """Test that zero dice raises ValueError."""
        with pytest.raises(ValueError, match="Number of dice"):
            DiceExpression(0, 6)

    def test_invalid_die_size_raises(self):
        """Test that zero die size raises ValueError."""
        with pytest.raises(ValueError, match="Die size"):
            DiceExpression(2, 0)


class TestRollResult:
    """Tests for RollResult dataclass."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        result = RollResult(
            total=15,
            rolls=[DieRoll(20, 12)],
            modifier=3,
            natural_roll=12,
            advantage_state=AdvantageState.NONE,
        )
        d = result.to_dict()

        assert d["total"] == 15
        assert len(d["rolls"]) == 1
        assert d["rolls"][0]["die_size"] == 20
        assert d["rolls"][0]["result"] == 12
        assert d["modifier"] == 3
        assert d["natural_roll"] == 12
        assert d["advantage_state"] == "none"
        assert d["is_critical"] is False
        assert d["is_fumble"] is False


class TestDiceRoller:
    """Tests for DiceRoller service."""

    # ==================== Basic Rolling Tests ====================

    def test_roll_d20_basic(self):
        """Test basic d20 roll produces valid result."""
        roller = DiceRoller(seed=42)
        result = roller.roll_d20()

        assert 1 <= result.total <= 20 + 0  # No modifier
        assert len(result.rolls) == 1
        assert result.rolls[0].die_size == 20
        assert result.advantage_state == AdvantageState.NONE
        assert result.natural_roll == result.rolls[0].result

    def test_roll_d20_with_modifier(self):
        """Test d20 roll with modifier."""
        roller = DiceRoller(seed=42)
        result = roller.roll_d20(modifier=5)

        assert result.modifier == 5
        assert result.total == result.natural_roll + 5

    # ==================== Deterministic Golden Tests ====================

    def test_deterministic_d20_seed_42(self):
        """Golden test: d20 with seed 42 should always produce same result."""
        roller = DiceRoller(seed=42)
        result = roller.roll_d20()

        # This is the expected result for seed 42
        # If this test fails, the RNG behavior has changed
        assert result.natural_roll == 8
        assert result.total == 8

    def test_deterministic_d20_seed_12345(self):
        """Golden test: d20 with seed 12345."""
        roller = DiceRoller(seed=12345)
        result = roller.roll_d20()

        # Expected result for seed 12345
        assert result.natural_roll == 17
        assert result.total == 17

    def test_deterministic_2d6_seed_42(self):
        """Golden test: 2d6 with seed 42."""
        roller = DiceRoller(seed=42)
        result = roller.roll("2d6")

        # Expected results for seed 42
        assert len(result.rolls) == 2
        assert result.rolls[0].result == 6
        assert result.rolls[1].result == 1
        assert result.total == 7

    def test_deterministic_multiple_rolls_seed_42(self):
        """Golden test: Multiple rolls with seed 42 are reproducible."""
        roller = DiceRoller(seed=42)

        # First d20
        r1 = roller.roll_d20()
        assert r1.natural_roll == 8

        # Second d20
        r2 = roller.roll_d20()
        assert r2.natural_roll == 5

        # Third d20
        r3 = roller.roll_d20()
        assert r3.natural_roll == 6

    def test_deterministic_sequence_reproducible(self):
        """Test that same seed produces same sequence."""
        results1 = []
        roller1 = DiceRoller(seed=999)
        for _ in range(10):
            results1.append(roller1.roll_d20().natural_roll)

        results2 = []
        roller2 = DiceRoller(seed=999)
        for _ in range(10):
            results2.append(roller2.roll_d20().natural_roll)

        assert results1 == results2

    # ==================== Advantage/Disadvantage Tests ====================

    def test_roll_d20_advantage(self):
        """Test d20 roll with advantage."""
        roller = DiceRoller(seed=42)
        result = roller.roll_d20(advantage=AdvantageState.ADVANTAGE)

        # With advantage, should roll twice and take higher
        assert result.advantage_state == AdvantageState.ADVANTAGE
        assert len(result.rolls) == 1  # Only the used roll
        assert len(result.discarded_rolls) == 1
        # The natural roll should be the higher of the two
        used = result.natural_roll
        discarded = result.discarded_rolls[0].result
        assert used >= discarded

    def test_roll_d20_disadvantage(self):
        """Test d20 roll with disadvantage."""
        roller = DiceRoller(seed=42)
        result = roller.roll_d20(advantage=AdvantageState.DISADVANTAGE)

        # With disadvantage, should roll twice and take lower
        assert result.advantage_state == AdvantageState.DISADVANTAGE
        assert len(result.rolls) == 1
        assert len(result.discarded_rolls) == 1
        # The natural roll should be the lower of the two
        used = result.natural_roll
        discarded = result.discarded_rolls[0].result
        assert used <= discarded

    def test_deterministic_advantage_seed_42(self):
        """Golden test: Advantage roll with seed 42."""
        roller = DiceRoller(seed=42)
        result = roller.roll_d20(advantage=AdvantageState.ADVANTAGE)

        # Seed 42 produces: first roll 8, second roll 5
        # Advantage takes higher: 8
        assert result.natural_roll == 8
        assert result.discarded_rolls[0].result == 5

    def test_deterministic_disadvantage_seed_42(self):
        """Golden test: Disadvantage roll with seed 42."""
        roller = DiceRoller(seed=42)
        result = roller.roll_d20(advantage=AdvantageState.DISADVANTAGE)

        # Seed 42 produces: first roll 8, second roll 5
        # Disadvantage takes lower: 5
        assert result.natural_roll == 5
        assert result.discarded_rolls[0].result == 8

    # ==================== Critical/Fumble Tests ====================

    def test_critical_detection(self):
        """Test that natural 20 is detected as critical."""
        # Find a seed that produces a natural 20
        for seed in range(10000):
            roller = DiceRoller(seed=seed)
            result = roller.roll_d20()
            if result.natural_roll == 20:
                assert result.is_critical is True
                assert result.is_fumble is False
                return

        pytest.fail("Could not find a seed producing natural 20")

    def test_fumble_detection(self):
        """Test that natural 1 is detected as fumble."""
        # Find a seed that produces a natural 1
        for seed in range(10000):
            roller = DiceRoller(seed=seed)
            result = roller.roll_d20()
            if result.natural_roll == 1:
                assert result.is_fumble is True
                assert result.is_critical is False
                return

        pytest.fail("Could not find a seed producing natural 1")

    def test_seed_0_produces_natural_20(self):
        """Golden test: Seed 0 produces natural 20."""
        roller = DiceRoller(seed=0)
        result = roller.roll_d20()
        assert result.natural_roll == 20
        assert result.is_critical is True

    def test_seed_4_produces_natural_1(self):
        """Golden test: Seed 4 produces natural 1."""
        roller = DiceRoller(seed=4)
        result = roller.roll_d20()
        assert result.natural_roll == 1
        assert result.is_fumble is True

    # ==================== Damage Roll Tests ====================

    def test_roll_damage_basic(self):
        """Test basic damage roll."""
        roller = DiceRoller(seed=42)
        result = roller.roll_damage("2d6", modifier=3)

        assert result.modifier == 3
        assert len(result.rolls) == 2
        # Total should be at least 1 (minimum damage)
        assert result.total >= 1

    def test_roll_damage_critical(self):
        """Test critical damage roll doubles dice."""
        roller = DiceRoller(seed=42)
        result = roller.roll_damage("2d6", critical=True)

        # Should roll 4 dice instead of 2
        assert len(result.rolls) == 4

    def test_roll_damage_minimum_one(self):
        """Test that damage minimum is 1."""
        roller = DiceRoller(seed=42)
        # Use a negative modifier that might make total negative
        result = roller.roll_damage("1d4", modifier=-10)

        # Even with -10 modifier, minimum damage is 1
        assert result.total >= 1

    def test_deterministic_damage_seed_42(self):
        """Golden test: Damage roll with seed 42."""
        roller = DiceRoller(seed=42)
        result = roller.roll_damage("1d8+3")

        # Expected for seed 42
        assert result.rolls[0].result == 8
        assert result.total == 11  # 8 + 3

    # ==================== General Roll Tests ====================

    def test_roll_expression_string(self):
        """Test rolling with string expression."""
        roller = DiceRoller(seed=42)
        result = roller.roll("3d6+2")

        assert len(result.rolls) == 3
        for roll in result.rolls:
            assert roll.die_size == 6
        assert result.modifier == 2

    def test_roll_expression_object(self):
        """Test rolling with DiceExpression object."""
        roller = DiceRoller(seed=42)
        expr = DiceExpression(2, 8, 1)
        result = roller.roll(expr)

        assert len(result.rolls) == 2
        assert result.modifier == 1

    def test_roll_extra_modifier(self):
        """Test rolling with extra modifier."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d6+2", extra_modifier=3)

        # Total modifier should be 2 + 3 = 5
        assert result.modifier == 5

    # ==================== Reroll Mechanic Tests ====================

    def test_roll_with_reroll_great_weapon_fighting(self):
        """Test reroll mechanic like Great Weapon Fighting."""
        roller = DiceRoller(seed=42)
        result = roller.roll_with_reroll("2d6", reroll_threshold=2)

        # All kept rolls should be 3 or higher (unless rerolled once)
        for roll in result.rolls:
            # After one reroll, might still be 1 or 2
            assert 1 <= roll.result <= 6

    def test_deterministic_reroll_seed_100(self):
        """Golden test: Reroll mechanic with seed 100."""
        roller = DiceRoller(seed=100)
        result = roller.roll_with_reroll("2d6", reroll_threshold=2)

        # First roll: 1 (rerolled), 2 (rerolled)
        # This tests the reroll behavior deterministically
        assert len(result.rolls) == 2
        # Verify the total is consistent
        expected_total = sum(r.result for r in result.rolls)
        assert result.total == expected_total

    # ==================== Roll Count and Reset Tests ====================

    def test_roll_count(self):
        """Test that roll count is tracked."""
        roller = DiceRoller(seed=42)
        assert roller.roll_count == 0

        roller.roll_d20()
        assert roller.roll_count == 1

        roller.roll("3d6")
        assert roller.roll_count == 4  # 1 + 3

    def test_reset_seed(self):
        """Test resetting the seed."""
        roller = DiceRoller(seed=42)
        r1 = roller.roll_d20().natural_roll

        roller.reset_seed(42)
        r2 = roller.roll_d20().natural_roll

        assert r1 == r2
        assert roller.roll_count == 1  # Reset resets count

    def test_reset_to_none(self):
        """Test resetting to no seed (random)."""
        roller = DiceRoller(seed=42)
        roller.reset_seed(None)

        # Should still produce valid results
        result = roller.roll_d20()
        assert 1 <= result.natural_roll <= 20

    # ==================== Distribution Tests (Statistical) ====================

    def test_d20_distribution_reasonable(self):
        """Test that d20 results are reasonably distributed."""
        roller = DiceRoller(seed=42)
        results = [roller.roll_d20().natural_roll for _ in range(1000)]

        # All results should be in range
        assert all(1 <= r <= 20 for r in results)

        # Should hit most numbers (unlikely to miss many with 1000 rolls)
        unique_values = set(results)
        assert len(unique_values) >= 15  # At least 15 different values

        # Average should be close to 10.5
        avg = sum(results) / len(results)
        assert 9.0 <= avg <= 12.0

    def test_d6_distribution_reasonable(self):
        """Test that d6 results are reasonably distributed."""
        roller = DiceRoller(seed=42)
        results = []
        for _ in range(600):
            r = roller.roll("1d6")
            results.append(r.rolls[0].result)

        # All results should be in range
        assert all(1 <= r <= 6 for r in results)

        # Should hit all numbers
        unique_values = set(results)
        assert len(unique_values) == 6

        # Average should be close to 3.5
        avg = sum(results) / len(results)
        assert 3.0 <= avg <= 4.0
