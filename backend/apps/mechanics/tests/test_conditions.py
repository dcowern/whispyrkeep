"""
Tests for the condition system.

Ticket: 9.0.4

Based on SYSTEM_DESIGN.md section 7.3 and CLAUDE.md testing requirements.
"""


from apps.mechanics.services.conditions import (
    CONDITION_EFFECTS,
    EXHAUSTION_LEVELS,
    AppliedCondition,
    Condition,
    ConditionEffect,
    ConditionManager,
    ConditionState,
    apply_condition,
    get_condition_effects,
    remove_condition,
)
from apps.mechanics.services.dice import AdvantageState


class TestConditionEnum:
    """Tests for Condition enum."""

    def test_all_srd_conditions_present(self):
        """Test that all SRD 5.2 conditions are defined."""
        expected = [
            "blinded", "charmed", "deafened", "frightened", "grappled",
            "incapacitated", "invisible", "paralyzed", "petrified",
            "poisoned", "prone", "restrained", "stunned", "unconscious",
            "exhaustion",
        ]
        for cond in expected:
            assert Condition(cond), f"Missing condition: {cond}"

    def test_condition_from_string(self):
        """Test creating condition from string."""
        assert Condition("blinded") == Condition.BLINDED
        assert Condition("prone") == Condition.PRONE


class TestConditionEffect:
    """Tests for ConditionEffect dataclass."""

    def test_default_effect(self):
        """Test default condition effect values."""
        effect = ConditionEffect()
        assert effect.attack_advantage == AdvantageState.NONE
        assert effect.speed_modifier == 1.0
        assert effect.can_attack is True
        assert effect.can_move is True

    def test_blinded_effect(self):
        """Test blinded condition effects."""
        effect = CONDITION_EFFECTS[Condition.BLINDED]
        assert effect.attack_disadvantage == AdvantageState.DISADVANTAGE
        assert effect.attacks_against_advantage == AdvantageState.ADVANTAGE
        assert effect.can_see is False

    def test_paralyzed_effect(self):
        """Test paralyzed condition effects."""
        effect = CONDITION_EFFECTS[Condition.PARALYZED]
        assert effect.is_incapacitated is True
        assert effect.can_move is False
        assert effect.attacks_auto_crit_in_melee is True
        assert "str" in effect.auto_fail_saves
        assert "dex" in effect.auto_fail_saves

    def test_grappled_effect(self):
        """Test grappled condition effects."""
        effect = CONDITION_EFFECTS[Condition.GRAPPLED]
        assert effect.speed_modifier == 0.0
        assert effect.can_move is False

    def test_invisible_effect(self):
        """Test invisible condition effects."""
        effect = CONDITION_EFFECTS[Condition.INVISIBLE]
        assert effect.attack_advantage == AdvantageState.ADVANTAGE
        assert effect.attacks_against_advantage == AdvantageState.DISADVANTAGE


class TestExhaustionLevels:
    """Tests for exhaustion levels."""

    def test_level_1_disadvantage_on_checks(self):
        """Test level 1 exhaustion gives disadvantage on ability checks."""
        effect = EXHAUSTION_LEVELS[1].effects
        assert len(effect.ability_check_disadvantage) == 6

    def test_level_2_halves_speed(self):
        """Test level 2 exhaustion halves speed."""
        effect = EXHAUSTION_LEVELS[2].effects
        assert effect.speed_modifier == 0.5

    def test_level_3_disadvantage_on_attacks(self):
        """Test level 3 exhaustion gives disadvantage on attacks."""
        effect = EXHAUSTION_LEVELS[3].effects
        assert effect.attack_disadvantage == AdvantageState.DISADVANTAGE

    def test_level_5_speed_zero(self):
        """Test level 5 exhaustion sets speed to 0."""
        effect = EXHAUSTION_LEVELS[5].effects
        assert effect.speed_modifier == 0.0
        assert effect.can_move is False

    def test_level_6_is_death(self):
        """Test level 6 exhaustion is death."""
        level = EXHAUSTION_LEVELS[6]
        assert "Death" in level.description


class TestAppliedCondition:
    """Tests for AppliedCondition dataclass."""

    def test_basic_condition(self):
        """Test creating a basic applied condition."""
        applied = AppliedCondition(
            condition=Condition.POISONED,
            source="poison dart",
            duration_rounds=10,
        )
        assert applied.condition == Condition.POISONED
        assert applied.source == "poison dart"
        assert applied.duration_rounds == 10

    def test_condition_with_save(self):
        """Test condition with save DC."""
        applied = AppliedCondition(
            condition=Condition.FRIGHTENED,
            source="dragon",
            save_dc=15,
            save_ability="wis",
        )
        assert applied.save_dc == 15
        assert applied.save_ability == "wis"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        applied = AppliedCondition(
            condition=Condition.PRONE,
            source="trip attack",
        )
        d = applied.to_dict()
        assert d["condition"] == "prone"
        assert d["source"] == "trip attack"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "condition": "stunned",
            "source": "stunning strike",
            "duration_rounds": 1,
        }
        applied = AppliedCondition.from_dict(data)
        assert applied.condition == Condition.STUNNED
        assert applied.source == "stunning strike"
        assert applied.duration_rounds == 1


class TestConditionState:
    """Tests for ConditionState dataclass."""

    def test_empty_state(self):
        """Test empty condition state."""
        state = ConditionState()
        assert len(state.active_conditions) == 0
        assert state.has_condition(Condition.BLINDED) is False

    def test_has_condition(self):
        """Test checking for condition presence."""
        state = ConditionState(
            active_conditions=[AppliedCondition(condition=Condition.PRONE)]
        )
        assert state.has_condition(Condition.PRONE) is True
        assert state.has_condition("prone") is True
        assert state.has_condition(Condition.BLINDED) is False

    def test_get_condition(self):
        """Test getting applied condition."""
        applied = AppliedCondition(condition=Condition.RESTRAINED, source="web")
        state = ConditionState(active_conditions=[applied])

        result = state.get_condition(Condition.RESTRAINED)
        assert result is applied
        assert state.get_condition(Condition.BLINDED) is None

    def test_get_exhaustion_level(self):
        """Test getting exhaustion level."""
        state = ConditionState(
            active_conditions=[
                AppliedCondition(condition=Condition.EXHAUSTION, exhaustion_level=3)
            ]
        )
        assert state.get_exhaustion_level() == 3

    def test_to_dict_from_dict_roundtrip(self):
        """Test serialization roundtrip."""
        state = ConditionState(
            active_conditions=[
                AppliedCondition(condition=Condition.POISONED),
                AppliedCondition(condition=Condition.PRONE),
            ]
        )
        d = state.to_dict()
        restored = ConditionState.from_dict(d)
        assert len(restored.active_conditions) == 2
        assert restored.has_condition(Condition.POISONED)
        assert restored.has_condition(Condition.PRONE)


class TestConditionManager:
    """Tests for ConditionManager service."""

    # ==================== Apply Condition Tests ====================

    def test_apply_condition_basic(self):
        """Test applying a basic condition."""
        manager = ConditionManager()
        state = ConditionState()

        applied = manager.apply_condition(state, Condition.BLINDED)

        assert state.has_condition(Condition.BLINDED)
        assert applied.condition == Condition.BLINDED

    def test_apply_condition_with_duration(self):
        """Test applying condition with duration."""
        manager = ConditionManager()
        state = ConditionState()

        applied = manager.apply_condition(
            state, "poisoned", duration_rounds=5, source="poison"
        )

        assert applied.duration_rounds == 5
        assert applied.source == "poison"

    def test_apply_duplicate_condition_updates_duration(self):
        """Test that applying same condition updates duration."""
        manager = ConditionManager()
        state = ConditionState()

        manager.apply_condition(state, Condition.FRIGHTENED, duration_rounds=3)
        manager.apply_condition(state, Condition.FRIGHTENED, duration_rounds=5)

        # Should still only have one condition
        assert len(state.active_conditions) == 1
        # Duration should be the longer one
        assert state.get_condition(Condition.FRIGHTENED).duration_rounds == 5

    def test_apply_exhaustion_stacks(self):
        """Test that exhaustion levels stack."""
        manager = ConditionManager()
        state = ConditionState()

        manager.apply_condition(state, Condition.EXHAUSTION, exhaustion_level=2)
        assert state.get_exhaustion_level() == 2

        manager.apply_condition(state, Condition.EXHAUSTION, exhaustion_level=1)
        assert state.get_exhaustion_level() == 3

    def test_exhaustion_caps_at_6(self):
        """Test exhaustion caps at level 6."""
        manager = ConditionManager()
        state = ConditionState()

        manager.apply_condition(state, Condition.EXHAUSTION, exhaustion_level=10)
        assert state.get_exhaustion_level() == 6

    # ==================== Remove Condition Tests ====================

    def test_remove_condition(self):
        """Test removing a condition."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[AppliedCondition(condition=Condition.PRONE)]
        )

        result = manager.remove_condition(state, Condition.PRONE)

        assert result is True
        assert state.has_condition(Condition.PRONE) is False

    def test_remove_nonexistent_condition(self):
        """Test removing condition that doesn't exist."""
        manager = ConditionManager()
        state = ConditionState()

        result = manager.remove_condition(state, Condition.BLINDED)
        assert result is False

    def test_reduce_exhaustion(self):
        """Test reducing exhaustion levels."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[
                AppliedCondition(condition=Condition.EXHAUSTION, exhaustion_level=3)
            ]
        )

        new_level = manager.reduce_exhaustion(state, levels=1)

        assert new_level == 2
        assert state.get_exhaustion_level() == 2

    def test_reduce_exhaustion_to_zero_removes_condition(self):
        """Test reducing exhaustion to 0 removes condition."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[
                AppliedCondition(condition=Condition.EXHAUSTION, exhaustion_level=1)
            ]
        )

        new_level = manager.reduce_exhaustion(state, levels=1)

        assert new_level == 0
        assert state.has_condition(Condition.EXHAUSTION) is False

    # ==================== Duration Tests ====================

    def test_tick_durations(self):
        """Test ticking duration of conditions."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[
                AppliedCondition(condition=Condition.POISONED, duration_rounds=3),
                AppliedCondition(condition=Condition.PRONE, duration_rounds=1),
            ]
        )

        expired = manager.tick_durations(state, rounds=1)

        assert Condition.PRONE in expired
        assert Condition.POISONED not in expired
        assert state.has_condition(Condition.PRONE) is False
        assert state.has_condition(Condition.POISONED) is True
        assert state.get_condition(Condition.POISONED).duration_rounds == 2

    def test_tick_permanent_conditions(self):
        """Test that permanent conditions don't expire."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[
                AppliedCondition(condition=Condition.PETRIFIED),  # No duration
            ]
        )

        expired = manager.tick_durations(state, rounds=100)

        assert len(expired) == 0
        assert state.has_condition(Condition.PETRIFIED)

    # ==================== Combined Effects Tests ====================

    def test_combined_effects_single_condition(self):
        """Test combined effects with single condition."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[AppliedCondition(condition=Condition.BLINDED)]
        )

        effects = manager.get_combined_effects(state)

        assert effects.attack_disadvantage == AdvantageState.DISADVANTAGE
        assert effects.can_see is False

    def test_combined_effects_multiple_conditions(self):
        """Test combined effects with multiple conditions."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[
                AppliedCondition(condition=Condition.BLINDED),
                AppliedCondition(condition=Condition.PRONE),
            ]
        )

        effects = manager.get_combined_effects(state)

        # Both give disadvantage on attacks
        assert effects.attack_disadvantage == AdvantageState.DISADVANTAGE
        assert effects.can_see is False

    def test_combined_effects_with_exhaustion(self):
        """Test combined effects include exhaustion."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[
                AppliedCondition(condition=Condition.EXHAUSTION, exhaustion_level=2)
            ]
        )

        effects = manager.get_combined_effects(state)

        assert effects.speed_modifier == 0.5

    # ==================== Advantage State Tests ====================

    def test_get_attack_advantage_state_disadvantage(self):
        """Test getting attack advantage state with disadvantage."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[AppliedCondition(condition=Condition.POISONED)]
        )

        result = manager.get_attack_advantage_state(state, is_attacker=True)
        assert result == AdvantageState.DISADVANTAGE

    def test_get_attack_advantage_state_advantage(self):
        """Test getting attack advantage state with advantage."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[AppliedCondition(condition=Condition.INVISIBLE)]
        )

        result = manager.get_attack_advantage_state(state, is_attacker=True)
        assert result == AdvantageState.ADVANTAGE

    def test_get_attack_advantage_state_cancel_out(self):
        """Test advantage and disadvantage cancel out."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[
                AppliedCondition(condition=Condition.INVISIBLE),  # Advantage
                AppliedCondition(condition=Condition.POISONED),  # Disadvantage
            ]
        )

        result = manager.get_attack_advantage_state(state, is_attacker=True)
        assert result == AdvantageState.NONE

    def test_attacks_against_advantage(self):
        """Test attacks against have advantage."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[AppliedCondition(condition=Condition.PARALYZED)]
        )

        result = manager.get_attack_advantage_state(state, is_attacker=False)
        assert result == AdvantageState.ADVANTAGE

    # ==================== Saving Throw Tests ====================

    def test_get_save_advantage_state_auto_fail(self):
        """Test auto-fail saves return None."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[AppliedCondition(condition=Condition.PARALYZED)]
        )

        result = manager.get_save_advantage_state(state, "dex")
        assert result is None  # Auto-fail

    def test_get_save_disadvantage(self):
        """Test save disadvantage."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[AppliedCondition(condition=Condition.RESTRAINED)]
        )

        result = manager.get_save_advantage_state(state, "dex")
        assert result == AdvantageState.DISADVANTAGE

    def test_ability_check_disadvantage(self):
        """Test checking ability check disadvantage."""
        manager = ConditionManager()
        state = ConditionState(
            active_conditions=[AppliedCondition(condition=Condition.POISONED)]
        )

        assert manager.check_ability_check_disadvantage(state, "str") is True
        assert manager.check_ability_check_disadvantage(state, "dex") is True


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_apply_condition_function(self):
        """Test apply_condition convenience function."""
        state = ConditionState()
        applied = apply_condition(state, Condition.PRONE)

        assert state.has_condition(Condition.PRONE)
        assert applied.condition == Condition.PRONE

    def test_remove_condition_function(self):
        """Test remove_condition convenience function."""
        state = ConditionState(
            active_conditions=[AppliedCondition(condition=Condition.BLINDED)]
        )

        result = remove_condition(state, "blinded")
        assert result is True
        assert not state.has_condition(Condition.BLINDED)

    def test_get_condition_effects_function(self):
        """Test get_condition_effects convenience function."""
        effect = get_condition_effects(Condition.GRAPPLED)
        assert effect.speed_modifier == 0.0

    def test_apply_condition_with_dict(self):
        """Test applying condition to dict state."""
        state_dict = {"active_conditions": []}
        # This would convert from dict internally
        state = ConditionState.from_dict(state_dict)
        apply_condition(state, Condition.STUNNED)
        assert state.has_condition(Condition.STUNNED)
