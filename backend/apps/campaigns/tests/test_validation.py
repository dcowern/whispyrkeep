"""
Tests for the validation service.

Ticket: 8.3.1
"""


from apps.campaigns.services.validation import (
    LLMOutputValidator,
    LoreDeltaValidator,
    PatchValidator,
    RollValidator,
    ValidationResult,
)


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_valid_result(self):
        """Test creating a valid result."""
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert result.success is True

    def test_add_error(self):
        """Test adding an error invalidates result."""
        result = ValidationResult(valid=True)
        result.add_error("Test error")
        assert result.valid is False
        assert "Test error" in result.errors

    def test_merge(self):
        """Test merging results."""
        result1 = ValidationResult(valid=True)
        result1.add_warning("Warning 1")

        result2 = ValidationResult(valid=True)
        result2.add_error("Error 1")

        result1.merge(result2)
        assert result1.valid is False
        assert "Warning 1" in result1.warnings
        assert "Error 1" in result1.errors


class TestRollValidator:
    """Tests for RollValidator."""

    def test_valid_ability_check(self):
        """Test validating a valid ability check."""
        validator = RollValidator()
        roll = {
            "id": "r1",
            "type": "ability_check",
            "ability": "dex",
            "skill": "stealth",
            "dc": 15,
            "advantage": "none",
        }

        result = validator.validate_roll_request(roll)
        assert result.valid is True

    def test_invalid_roll_type(self):
        """Test that invalid roll type fails."""
        validator = RollValidator()
        roll = {
            "id": "r1",
            "type": "invalid_type",
        }

        result = validator.validate_roll_request(roll)
        assert result.valid is False
        assert any("Invalid roll type" in e for e in result.errors)

    def test_invalid_ability(self):
        """Test that invalid ability fails."""
        validator = RollValidator()
        roll = {
            "id": "r1",
            "type": "ability_check",
            "ability": "invalid",
            "dc": 15,
        }

        result = validator.validate_roll_request(roll)
        assert result.valid is False
        assert any("Invalid ability" in e for e in result.errors)

    def test_invalid_skill(self):
        """Test that invalid skill fails."""
        validator = RollValidator()
        roll = {
            "id": "r1",
            "type": "ability_check",
            "ability": "dex",
            "skill": "invalid_skill",
            "dc": 15,
        }

        result = validator.validate_roll_request(roll)
        assert result.valid is False
        assert any("Invalid skill" in e for e in result.errors)

    def test_invalid_dc(self):
        """Test that invalid DC fails."""
        validator = RollValidator()
        roll = {
            "id": "r1",
            "type": "ability_check",
            "ability": "dex",
            "dc": 50,  # Too high
        }

        result = validator.validate_roll_request(roll)
        assert result.valid is False

    def test_invalid_advantage(self):
        """Test that invalid advantage fails."""
        validator = RollValidator()
        roll = {
            "id": "r1",
            "type": "ability_check",
            "ability": "dex",
            "advantage": "super_advantage",
        }

        result = validator.validate_roll_request(roll)
        assert result.valid is False

    def test_valid_attack_roll(self):
        """Test validating a valid attack roll."""
        validator = RollValidator()
        roll = {
            "id": "r1",
            "type": "attack_roll",
            "attacker": "player",
            "target": "goblin_1",
        }

        result = validator.validate_roll_request(roll)
        assert result.valid is True

    def test_valid_damage_roll(self):
        """Test validating a valid damage roll."""
        validator = RollValidator()
        roll = {
            "id": "r1",
            "type": "damage_roll",
            "dice": "2d6+3",
        }

        result = validator.validate_roll_request(roll)
        assert result.valid is True

    def test_invalid_dice_expression(self):
        """Test that invalid dice expression fails."""
        validator = RollValidator()
        roll = {
            "id": "r1",
            "type": "damage_roll",
            "dice": "invalid",
        }

        result = validator.validate_roll_request(roll)
        assert result.valid is False

    def test_duplicate_roll_ids(self):
        """Test that duplicate roll IDs fail."""
        validator = RollValidator()
        rolls = [
            {"id": "r1", "type": "ability_check", "ability": "dex", "dc": 15},
            {"id": "r1", "type": "ability_check", "ability": "str", "dc": 10},
        ]

        result = validator.validate_roll_requests(rolls)
        assert result.valid is False
        assert any("Duplicate" in e for e in result.errors)


class TestPatchValidator:
    """Tests for PatchValidator."""

    def test_valid_replace_patch(self):
        """Test validating a valid replace patch."""
        validator = PatchValidator()
        patch = {
            "op": "replace",
            "path": "/party/player/hp/current",
            "value": 25,
        }

        result = validator.validate_patch(patch)
        assert result.valid is True

    def test_invalid_operation(self):
        """Test that invalid operation fails."""
        validator = PatchValidator()
        patch = {
            "op": "invalid_op",
            "path": "/party/player/hp/current",
            "value": 25,
        }

        result = validator.validate_patch(patch)
        assert result.valid is False

    def test_invalid_path(self):
        """Test that invalid path fails."""
        validator = PatchValidator()
        patch = {
            "op": "replace",
            "path": "/invalid/path",
            "value": 25,
        }

        result = validator.validate_patch(patch)
        assert result.valid is False

    def test_missing_value_for_replace(self):
        """Test that missing value for replace fails."""
        validator = PatchValidator()
        patch = {
            "op": "replace",
            "path": "/party/player/hp/current",
        }

        result = validator.validate_patch(patch)
        assert result.valid is False

    def test_valid_advance_time(self):
        """Test validating a valid advance_time patch."""
        validator = PatchValidator()
        patch = {
            "op": "advance_time",
            "value": {"hours": 1, "minutes": 30},
        }

        result = validator.validate_patch(patch)
        assert result.valid is True

    def test_invalid_time_delta(self):
        """Test that negative time delta fails."""
        validator = PatchValidator()
        patch = {
            "op": "advance_time",
            "value": {"hours": -1},
        }

        result = validator.validate_patch(patch)
        assert result.valid is False

    def test_hp_validation(self):
        """Test HP value validation."""
        validator = PatchValidator()
        patch = {
            "op": "replace",
            "path": "/party/player/hp/current",
            "value": -5,  # Negative HP
        }

        result = validator.validate_patch(patch)
        assert result.valid is False

    def test_conditions_validation(self):
        """Test conditions value validation."""
        validator = PatchValidator()
        patch = {
            "op": "replace",
            "path": "/party/player/conditions",
            "value": "not_a_list",  # Should be list
        }

        result = validator.validate_patch(patch)
        assert result.valid is False


class TestLoreDeltaValidator:
    """Tests for LoreDeltaValidator."""

    def test_valid_soft_lore(self):
        """Test validating valid soft lore."""
        validator = LoreDeltaValidator()
        delta = {
            "type": "soft_lore",
            "text": "The tavern is said to be haunted.",
            "tags": ["rumor", "tavern"],
        }

        result = validator.validate_lore_delta(delta)
        assert result.valid is True

    def test_hard_canon_warning(self):
        """Test that hard_canon produces warning."""
        validator = LoreDeltaValidator()
        delta = {
            "type": "hard_canon",
            "text": "The king is dead.",
            "tags": ["fact"],
        }

        result = validator.validate_lore_delta(delta)
        assert result.valid is True
        assert len(result.warnings) > 0

    def test_invalid_type(self):
        """Test that invalid type fails."""
        validator = LoreDeltaValidator()
        delta = {
            "type": "invalid_type",
            "text": "Some text",
        }

        result = validator.validate_lore_delta(delta)
        assert result.valid is False

    def test_missing_text(self):
        """Test that missing text fails."""
        validator = LoreDeltaValidator()
        delta = {
            "type": "soft_lore",
        }

        result = validator.validate_lore_delta(delta)
        assert result.valid is False

    def test_text_too_long(self):
        """Test that too long text fails."""
        validator = LoreDeltaValidator()
        delta = {
            "type": "soft_lore",
            "text": "x" * 3000,  # Too long
        }

        result = validator.validate_lore_delta(delta)
        assert result.valid is False

    def test_invalid_tags(self):
        """Test that invalid tags fails."""
        validator = LoreDeltaValidator()
        delta = {
            "type": "soft_lore",
            "text": "Some text",
            "tags": "not_a_list",
        }

        result = validator.validate_lore_delta(delta)
        assert result.valid is False


class TestLLMOutputValidator:
    """Tests for LLMOutputValidator."""

    def test_valid_complete_output(self):
        """Test validating a complete valid output."""
        validator = LLMOutputValidator()
        output = {
            "roll_requests": [
                {
                    "id": "r1",
                    "type": "ability_check",
                    "ability": "dex",
                    "skill": "stealth",
                    "dc": 15,
                    "advantage": "none",
                }
            ],
            "patches": [
                {
                    "op": "advance_time",
                    "value": {"minutes": 10},
                }
            ],
            "lore_deltas": [
                {
                    "type": "soft_lore",
                    "text": "A rumor heard in the tavern.",
                    "tags": ["rumor"],
                }
            ],
        }

        result = validator.validate_json_output(output)
        assert result.valid is True

    def test_empty_output_valid(self):
        """Test that empty arrays are valid."""
        validator = LLMOutputValidator()
        output = {
            "roll_requests": [],
            "patches": [],
            "lore_deltas": [],
        }

        result = validator.validate_json_output(output)
        assert result.valid is True

    def test_invalid_nested_data(self):
        """Test that invalid nested data fails."""
        validator = LLMOutputValidator()
        output = {
            "roll_requests": [
                {
                    "id": "r1",
                    "type": "invalid_type",
                }
            ],
        }

        result = validator.validate_json_output(output)
        assert result.valid is False
