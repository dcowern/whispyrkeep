"""
Tests for the resting service.

Ticket: 9.1.1

Based on SYSTEM_DESIGN.md section 7.3 and 11.4.
"""

import pytest

from apps.mechanics.services.conditions import (
    AppliedCondition,
    Condition,
    ConditionState,
)
from apps.mechanics.services.dice import DiceRoller
from apps.mechanics.services.resting import (
    ResourceState,
    RestingService,
    RestResult,
    long_rest,
    short_rest,
)


class TestResourceState:
    """Tests for ResourceState dataclass."""

    def test_default_state(self):
        """Test default resource state."""
        state = ResourceState()
        assert state.current_hp == 0
        assert state.max_hp == 0
        assert state.temp_hp == 0
        assert len(state.hit_dice) == 0
        assert len(state.spell_slots) == 0

    def test_custom_state(self):
        """Test custom resource state."""
        state = ResourceState(
            current_hp=20,
            max_hp=30,
            hit_dice={"d8": {"max": 4, "spent": 1}},
            spell_slots={"1": {"max": 4, "used": 2}},
            constitution_modifier=2,
        )
        assert state.current_hp == 20
        assert state.max_hp == 30
        assert state.hit_dice["d8"]["spent"] == 1
        assert state.spell_slots["1"]["used"] == 2
        assert state.constitution_modifier == 2

    def test_to_dict(self):
        """Test serialization to dictionary."""
        state = ResourceState(
            current_hp=15,
            max_hp=25,
            hit_dice={"d10": {"max": 3, "spent": 0}},
        )
        d = state.to_dict()
        assert d["current_hp"] == 15
        assert d["max_hp"] == 25
        assert "d10" in d["hit_dice"]

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "current_hp": 10,
            "max_hp": 20,
            "spell_slots": {"1": {"max": 3, "used": 1}},
            "constitution_modifier": -1,
        }
        state = ResourceState.from_dict(data)
        assert state.current_hp == 10
        assert state.max_hp == 20
        assert state.constitution_modifier == -1


class TestRestResult:
    """Tests for RestResult dataclass."""

    def test_short_rest_result(self):
        """Test short rest result."""
        result = RestResult(rest_type="short", hp_healed=10)
        assert result.rest_type == "short"
        assert result.hp_healed == 10

    def test_long_rest_result(self):
        """Test long rest result."""
        result = RestResult(
            rest_type="long",
            hp_healed=20,
            hit_dice_recovered=2,
            spell_slots_recovered={"1": 3, "2": 2},
        )
        assert result.rest_type == "long"
        assert result.hp_healed == 20
        assert result.hit_dice_recovered == 2

    def test_to_dict(self):
        """Test serialization."""
        result = RestResult(
            rest_type="short",
            hp_healed=5,
            hit_dice_spent=[{"die_type": "d8", "roll": 6, "modifier": 2, "hp_healed": 5}],
        )
        d = result.to_dict()
        assert d["rest_type"] == "short"
        assert d["hp_healed"] == 5
        assert len(d["hit_dice_spent"]) == 1


class TestRestingService:
    """Tests for RestingService."""

    # ==================== Short Rest Tests ====================

    def test_short_rest_no_hit_dice_spent(self):
        """Test short rest without spending hit dice."""
        service = RestingService()
        resources = ResourceState(
            current_hp=10,
            max_hp=20,
            hit_dice={"d8": {"max": 4, "spent": 0}},
        )

        result = service.short_rest(resources)

        assert result.rest_type == "short"
        assert result.hp_healed == 0
        assert len(result.hit_dice_spent) == 0

    def test_short_rest_spend_hit_dice(self):
        """Test short rest spending hit dice."""
        roller = DiceRoller(seed=42)  # d8 roll = 8
        service = RestingService(dice_roller=roller)
        resources = ResourceState(
            current_hp=10,
            max_hp=30,
            hit_dice={"d8": {"max": 4, "spent": 0}},
            constitution_modifier=2,
        )

        result = service.short_rest(resources, hit_dice_to_spend=["d8"])

        assert result.hp_healed > 0
        assert len(result.hit_dice_spent) == 1
        # Check die was marked as spent
        assert resources.hit_dice["d8"]["spent"] == 1

    def test_short_rest_multiple_hit_dice(self):
        """Test spending multiple hit dice."""
        roller = DiceRoller(seed=42)
        service = RestingService(dice_roller=roller)
        resources = ResourceState(
            current_hp=5,
            max_hp=30,
            hit_dice={"d8": {"max": 4, "spent": 0}},
            constitution_modifier=2,
        )

        result = service.short_rest(resources, hit_dice_to_spend=["d8", "d8"])

        assert len(result.hit_dice_spent) == 2
        assert resources.hit_dice["d8"]["spent"] == 2

    def test_short_rest_hit_die_healing_minimum_one(self):
        """Test that hit die healing is at least 1 HP."""
        roller = DiceRoller(seed=4)  # d8 roll = 1
        service = RestingService(dice_roller=roller)
        resources = ResourceState(
            current_hp=10,
            max_hp=30,
            hit_dice={"d8": {"max": 4, "spent": 0}},
            constitution_modifier=-5,  # Negative CON modifier
        )

        result = service.short_rest(resources, hit_dice_to_spend=["d8"])

        # Even with -5 CON and roll of 1, minimum healing is 1
        assert result.hp_healed >= 1
        for dice in result.hit_dice_spent:
            assert dice["hp_healed"] >= 1

    def test_short_rest_cant_overheal(self):
        """Test that healing can't exceed max HP."""
        roller = DiceRoller(seed=42)  # High roll
        service = RestingService(dice_roller=roller)
        resources = ResourceState(
            current_hp=28,
            max_hp=30,
            hit_dice={"d8": {"max": 4, "spent": 0}},
            constitution_modifier=5,
        )

        result = service.short_rest(resources, hit_dice_to_spend=["d8"])

        # Should only heal up to max HP
        assert resources.current_hp <= resources.max_hp
        assert resources.current_hp == 30

    def test_short_rest_no_available_dice(self):
        """Test short rest with no available hit dice."""
        service = RestingService()
        resources = ResourceState(
            current_hp=10,
            max_hp=30,
            hit_dice={"d8": {"max": 4, "spent": 4}},  # All spent
        )

        result = service.short_rest(resources, hit_dice_to_spend=["d8"])

        assert result.hp_healed == 0
        assert len(result.hit_dice_spent) == 0

    def test_short_rest_class_resource_recovery(self):
        """Test short rest resource recovery."""
        service = RestingService()
        resources = ResourceState(
            current_hp=20,
            max_hp=20,
            class_resources={
                "action_surge": {
                    "max": 1,
                    "used": 1,
                    "recharges_on": "short_rest",
                },
                "second_wind": {
                    "max": 1,
                    "used": 1,
                    "recharges_on": "short_rest",
                },
                "rage": {
                    "max": 3,
                    "used": 2,
                    "recharges_on": "long_rest",  # Shouldn't recover
                },
            },
        )

        result = service.short_rest(resources)

        assert "action_surge" in result.resources_recovered
        assert "second_wind" in result.resources_recovered
        assert "rage" not in result.resources_recovered

    # ==================== Long Rest Tests ====================

    def test_long_rest_full_hp_recovery(self):
        """Test long rest recovers all HP."""
        service = RestingService()
        resources = ResourceState(
            current_hp=5,
            max_hp=30,
        )

        result = service.long_rest(resources)

        assert result.rest_type == "long"
        assert result.hp_healed == 25  # 30 - 5
        assert resources.current_hp == 30

    def test_long_rest_half_hit_dice_recovery(self):
        """Test long rest recovers half hit dice."""
        service = RestingService()
        resources = ResourceState(
            current_hp=30,
            max_hp=30,
            hit_dice={"d10": {"max": 6, "spent": 4}},  # 6 total, 4 spent
        )

        result = service.long_rest(resources)

        # Should recover 3 (half of 6)
        assert result.hit_dice_recovered == 3
        assert resources.hit_dice["d10"]["spent"] == 1  # 4 - 3 = 1

    def test_long_rest_minimum_one_hit_die_recovery(self):
        """Test long rest recovers at least 1 hit die."""
        service = RestingService()
        resources = ResourceState(
            current_hp=8,
            max_hp=8,
            hit_dice={"d8": {"max": 1, "spent": 1}},  # Level 1 character
        )

        result = service.long_rest(resources)

        # Should recover 1 (minimum 1)
        assert result.hit_dice_recovered == 1
        assert resources.hit_dice["d8"]["spent"] == 0

    def test_long_rest_spell_slot_recovery(self):
        """Test long rest recovers all spell slots."""
        service = RestingService()
        resources = ResourceState(
            current_hp=20,
            max_hp=20,
            spell_slots={
                "1": {"max": 4, "used": 3},
                "2": {"max": 3, "used": 2},
                "3": {"max": 2, "used": 2},
            },
        )

        result = service.long_rest(resources)

        assert result.spell_slots_recovered == {"1": 3, "2": 2, "3": 2}
        assert resources.spell_slots["1"]["used"] == 0
        assert resources.spell_slots["2"]["used"] == 0
        assert resources.spell_slots["3"]["used"] == 0

    def test_long_rest_all_resources_recovery(self):
        """Test long rest recovers all class resources."""
        service = RestingService()
        resources = ResourceState(
            current_hp=20,
            max_hp=20,
            class_resources={
                "rage": {"max": 3, "used": 3, "recharges_on": "long_rest"},
                "wild_shape": {"max": 2, "used": 2, "recharges_on": "long_rest"},
            },
        )

        result = service.long_rest(resources)

        assert "rage" in result.resources_recovered
        assert "wild_shape" in result.resources_recovered

    def test_long_rest_exhaustion_reduction(self):
        """Test long rest reduces exhaustion by 1."""
        service = RestingService()
        resources = ResourceState(current_hp=20, max_hp=20)
        conditions = ConditionState(
            active_conditions=[
                AppliedCondition(condition=Condition.EXHAUSTION, exhaustion_level=3)
            ]
        )

        result = service.long_rest(resources, conditions)

        assert result.exhaustion_reduced == 1
        assert conditions.get_exhaustion_level() == 2

    def test_long_rest_resets_death_saves(self):
        """Test long rest resets death saving throws."""
        service = RestingService()
        resources = ResourceState(
            current_hp=0,
            max_hp=20,
            death_save_successes=2,
            death_save_failures=1,
        )

        service.long_rest(resources)

        assert resources.death_save_successes == 0
        assert resources.death_save_failures == 0

    # ==================== Rest Eligibility Tests ====================

    def test_can_short_rest_normal(self):
        """Test normal character can short rest."""
        service = RestingService()
        conditions = ConditionState()

        can_rest, reason = service.can_short_rest(conditions)
        assert can_rest is True

    def test_cannot_rest_while_unconscious(self):
        """Test cannot rest while unconscious."""
        service = RestingService()
        conditions = ConditionState(
            active_conditions=[AppliedCondition(condition=Condition.UNCONSCIOUS)]
        )

        can_rest, reason = service.can_short_rest(conditions)
        assert can_rest is False
        assert "unconscious" in reason.lower()

    def test_cannot_rest_while_petrified(self):
        """Test cannot rest while petrified."""
        service = RestingService()
        conditions = ConditionState(
            active_conditions=[AppliedCondition(condition=Condition.PETRIFIED)]
        )

        can_rest, reason = service.can_short_rest(conditions)
        assert can_rest is False
        assert "petrified" in reason.lower()

    def test_cannot_rest_at_exhaustion_6(self):
        """Test cannot rest at exhaustion level 6 (death)."""
        service = RestingService()
        conditions = ConditionState(
            active_conditions=[
                AppliedCondition(condition=Condition.EXHAUSTION, exhaustion_level=6)
            ]
        )

        can_rest, reason = service.can_short_rest(conditions)
        assert can_rest is False
        assert "death" in reason.lower()

    def test_get_available_hit_dice(self):
        """Test getting available hit dice."""
        service = RestingService()
        resources = ResourceState(
            hit_dice={
                "d8": {"max": 4, "spent": 1},  # 3 available
                "d6": {"max": 2, "spent": 2},  # 0 available
                "d10": {"max": 3, "spent": 0},  # 3 available
            }
        )

        available = service.get_available_hit_dice(resources)

        assert available["d8"] == 3
        assert "d6" not in available  # 0 available, not included
        assert available["d10"] == 3

    # ==================== Deterministic Golden Tests ====================

    def test_deterministic_short_rest_seed_42(self):
        """Golden test: Short rest with seed 42."""
        result = short_rest(
            resources=ResourceState(
                current_hp=10,
                max_hp=30,
                hit_dice={"d8": {"max": 4, "spent": 0}},
                constitution_modifier=2,
            ),
            hit_dice_to_spend=["d8"],
            seed=42,
        )

        # Seed 42 on d8 produces 8, +2 CON = 10 HP
        assert result.hp_healed == 10
        assert result.hit_dice_spent[0]["roll"] == 8
        assert result.hit_dice_spent[0]["hp_healed"] == 10


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_short_rest_function(self):
        """Test short_rest convenience function."""
        resources = ResourceState(
            current_hp=15,
            max_hp=20,
            hit_dice={"d8": {"max": 2, "spent": 0}},
            constitution_modifier=1,
        )

        result = short_rest(resources, hit_dice_to_spend=["d8"], seed=42)

        assert result.rest_type == "short"
        assert result.hp_healed > 0

    def test_long_rest_function(self):
        """Test long_rest convenience function."""
        resources = ResourceState(
            current_hp=5,
            max_hp=30,
            hit_dice={"d10": {"max": 4, "spent": 3}},
            spell_slots={"1": {"max": 4, "used": 4}},
        )

        result = long_rest(resources)

        assert result.rest_type == "long"
        assert resources.current_hp == 30
        assert resources.spell_slots["1"]["used"] == 0
