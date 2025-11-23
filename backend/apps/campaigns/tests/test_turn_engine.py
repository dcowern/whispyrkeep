"""
Tests for the turn engine.

Tickets: 8.2.1, 8.2.2, 8.2.3
"""

import pytest

from apps.campaigns.services.turn_engine import (
    LLMResponseParser,
    MechanicsExecutor,
    RollResult,
    TurnPhase,
)


class TestLLMResponseParser:
    """Tests for LLMResponseParser."""

    def test_parse_valid_response(self):
        """Test parsing a valid LLM response."""
        parser = LLMResponseParser()
        response = """DM_TEXT:
You attempt to sneak past the guards. The shadows seem to welcome you.

DM_JSON:
{
  "roll_requests": [
    {
      "id": "r1",
      "type": "ability_check",
      "ability": "dex",
      "skill": "stealth",
      "dc": 15
    }
  ],
  "patches": [],
  "lore_deltas": []
}"""

        dm_text, dm_json, errors = parser.parse(response)

        assert len(errors) == 0
        assert "sneak past the guards" in dm_text
        assert len(dm_json["roll_requests"]) == 1
        assert dm_json["roll_requests"][0]["id"] == "r1"

    def test_parse_missing_dm_text(self):
        """Test parsing response without DM_TEXT."""
        parser = LLMResponseParser()
        response = """DM_JSON:
{"roll_requests": []}"""

        dm_text, dm_json, errors = parser.parse(response)

        assert len(errors) > 0
        assert any("DM_TEXT" in e for e in errors)

    def test_parse_invalid_json(self):
        """Test parsing response with invalid JSON."""
        parser = LLMResponseParser()
        response = """DM_TEXT:
Some narrative text.

DM_JSON:
{invalid json}"""

        dm_text, dm_json, errors = parser.parse(response)

        assert len(errors) > 0
        assert "narrative text" in dm_text

    def test_parse_fallback_json_detection(self):
        """Test parsing with fallback JSON detection."""
        parser = LLMResponseParser()
        response = """Some text before
{"roll_requests": [], "patches": []}
Some text after"""

        dm_text, dm_json, errors = parser.parse(response)

        # Should find the JSON even without DM_JSON prefix
        assert dm_json.get("roll_requests") == []


class TestMechanicsExecutor:
    """Tests for MechanicsExecutor (deterministic with seed)."""

    def test_roll_d20_seeded(self):
        """Test d20 rolling with seed produces consistent results."""
        executor = MechanicsExecutor(seed=42)
        result1, details1 = executor._roll_d20()

        executor = MechanicsExecutor(seed=42)
        result2, details2 = executor._roll_d20()

        assert result1 == result2

    def test_roll_d20_advantage(self):
        """Test d20 with advantage."""
        executor = MechanicsExecutor(seed=42)
        result, details = executor._roll_d20("advantage")

        assert "rolls" in details
        assert len(details["rolls"]) == 2
        assert result == max(details["rolls"])

    def test_roll_d20_disadvantage(self):
        """Test d20 with disadvantage."""
        executor = MechanicsExecutor(seed=42)
        result, details = executor._roll_d20("disadvantage")

        assert "rolls" in details
        assert len(details["rolls"]) == 2
        assert result == min(details["rolls"])

    def test_roll_dice_expression(self):
        """Test rolling dice expression."""
        executor = MechanicsExecutor(seed=42)
        total, details = executor._roll_dice("2d6+3")

        assert "rolls" in details
        assert len(details["rolls"]) == 2
        assert details["modifier"] == 3
        assert total == sum(details["rolls"]) + 3

    def test_roll_dice_invalid_expression(self):
        """Test invalid dice expression."""
        executor = MechanicsExecutor(seed=42)
        total, details = executor._roll_dice("invalid")

        assert "error" in details

    def test_execute_ability_check(self):
        """Test executing an ability check."""
        executor = MechanicsExecutor(seed=42)
        character_state = {
            "abilities": {"dex": 16},  # +3 modifier
            "skills": {"stealth": True},
            "level": 5,  # +3 proficiency
        }
        roll_spec = {
            "id": "r1",
            "type": "ability_check",
            "ability": "dex",
            "skill": "stealth",
            "dc": 15,
        }

        result = executor.execute_roll(roll_spec, character_state)

        assert result.roll_id == "r1"
        assert result.roll_type == "ability_check"
        assert result.modifier == 6  # +3 DEX, +3 proficiency
        assert result.dc == 15
        assert result.success is not None

    def test_execute_saving_throw(self):
        """Test executing a saving throw."""
        executor = MechanicsExecutor(seed=42)
        character_state = {
            "abilities": {"con": 14},  # +2 modifier
            "level": 1,
        }
        roll_spec = {
            "id": "r1",
            "type": "saving_throw",
            "ability": "con",
            "dc": 12,
        }

        result = executor.execute_roll(roll_spec, character_state)

        assert result.roll_type == "saving_throw"
        assert result.dc == 12

    def test_execute_attack_roll(self):
        """Test executing an attack roll."""
        executor = MechanicsExecutor(seed=42)
        character_state = {
            "abilities": {"str": 18},  # +4 modifier
            "level": 3,
        }
        roll_spec = {
            "id": "r1",
            "type": "attack_roll",
            "attacker": "player",
            "target": "goblin",
        }

        result = executor.execute_roll(roll_spec, character_state)

        assert result.roll_type == "attack_roll"
        assert result.modifier == 6  # +4 STR, +2 proficiency

    def test_execute_damage_roll(self):
        """Test executing a damage roll."""
        executor = MechanicsExecutor(seed=42)
        roll_spec = {
            "id": "r1",
            "type": "damage_roll",
            "dice": "1d8+3",
        }

        result = executor.execute_roll(roll_spec, {})

        assert result.roll_type == "damage_roll"
        assert 4 <= result.total <= 11  # 1d8+3 range

    def test_execute_multiple_rolls(self):
        """Test executing multiple rolls."""
        executor = MechanicsExecutor(seed=42)
        character_state = {"abilities": {"dex": 14}, "level": 1}
        roll_specs = [
            {"id": "r1", "type": "ability_check", "ability": "dex", "dc": 10},
            {"id": "r2", "type": "ability_check", "ability": "dex", "dc": 15},
        ]

        results = executor.execute_rolls(roll_specs, character_state)

        assert len(results) == 2
        assert results[0].roll_id == "r1"
        assert results[1].roll_id == "r2"


class TestTurnPhase:
    """Tests for TurnPhase enum."""

    def test_phase_values(self):
        """Test phase value strings."""
        assert TurnPhase.INITIALIZED.value == "initialized"
        assert TurnPhase.PERSISTED.value == "persisted"
        assert TurnPhase.FAILED.value == "failed"

    def test_phase_progression(self):
        """Test expected phase progression."""
        phases = [
            TurnPhase.INITIALIZED,
            TurnPhase.CONTEXT_BUILT,
            TurnPhase.PROPOSAL_RECEIVED,
            TurnPhase.MECHANICS_EXECUTED,
            TurnPhase.FINAL_RESPONSE,
            TurnPhase.VALIDATED,
            TurnPhase.PERSISTED,
        ]

        # Just verify all phases exist
        for phase in phases:
            assert phase in TurnPhase


class TestRollResult:
    """Tests for RollResult dataclass."""

    def test_roll_result_creation(self):
        """Test creating a roll result."""
        result = RollResult(
            roll_id="r1",
            roll_type="ability_check",
            roll_value=15,
            modifier=5,
            total=20,
            success=True,
            dc=15,
        )

        assert result.roll_id == "r1"
        assert result.total == 20
        assert result.success is True

    def test_roll_result_to_dict(self):
        """Test serializing roll result."""
        result = RollResult(
            roll_id="r1",
            roll_type="ability_check",
            roll_value=10,
            modifier=3,
            total=13,
            success=False,
            dc=15,
        )

        d = result.to_dict()

        assert d["roll_id"] == "r1"
        assert d["total"] == 13
        assert d["success"] is False
        assert d["dc"] == 15
