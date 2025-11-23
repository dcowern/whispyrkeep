"""
Tests for character validation service.

Tests the CharacterValidationService against SRD 5.2 rules.
"""

import pytest

from apps.characters.services import (
    ABILITY_ABBREVIATIONS,
    MAX_LEVEL,
    MIN_LEVEL,
    CharacterValidationService,
    ValidationResult,
)


@pytest.fixture
def validation_service():
    """Create a validation service without universe."""
    return CharacterValidationService()


@pytest.fixture
def valid_character_data():
    """Valid character data for testing."""
    return {
        "name": "Aragorn",
        "species": "Human",
        "character_class": "Fighter",
        "background": "Soldier",
        "level": 5,
        "ability_scores": {
            "str": 16,
            "dex": 14,
            "con": 12,
            "int": 10,
            "wis": 8,
            "cha": 15,
        },
    }


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_default_is_valid(self):
        """Test that result is valid by default."""
        result = ValidationResult()
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_add_error_sets_invalid(self):
        """Test that adding an error marks result as invalid."""
        result = ValidationResult()
        result.add_error("field", "message", "code")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "field"
        assert result.errors[0].message == "message"
        assert result.errors[0].code == "code"

    def test_add_warning_keeps_valid(self):
        """Test that warnings don't invalidate result."""
        result = ValidationResult()
        result.add_warning("warning message")

        assert result.is_valid is True
        assert len(result.warnings) == 1
        assert result.warnings[0] == "warning message"


@pytest.mark.django_db
class TestCharacterValidationService:
    """Tests for CharacterValidationService."""

    def test_valid_character(self, validation_service, valid_character_data, srd_data):
        """Test validation of a valid character."""
        result = validation_service.validate(**valid_character_data)
        assert result.is_valid is True

    def test_empty_name_invalid(self, validation_service, valid_character_data):
        """Test that empty name is invalid."""
        valid_character_data["name"] = ""
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(e.field == "name" and e.code == "required" for e in result.errors)

    def test_long_name_invalid(self, validation_service, valid_character_data):
        """Test that name over 100 chars is invalid."""
        valid_character_data["name"] = "A" * 101
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(e.field == "name" and e.code == "max_length" for e in result.errors)

    def test_level_below_min(self, validation_service, valid_character_data):
        """Test that level below minimum is invalid."""
        valid_character_data["level"] = 0
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(e.field == "level" and e.code == "min_value" for e in result.errors)

    def test_level_above_max(self, validation_service, valid_character_data):
        """Test that level above maximum is invalid."""
        valid_character_data["level"] = 21
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(e.field == "level" and e.code == "max_value" for e in result.errors)

    def test_valid_level_range(self, validation_service, valid_character_data, srd_data):
        """Test that all valid levels work."""
        for level in [MIN_LEVEL, 10, MAX_LEVEL]:
            valid_character_data["level"] = level
            result = validation_service.validate(**valid_character_data)
            assert result.is_valid is True, f"Level {level} should be valid"


@pytest.mark.django_db
class TestSpeciesValidation:
    """Tests for species validation."""

    def test_empty_species_invalid(self, validation_service, valid_character_data):
        """Test that empty species is invalid."""
        valid_character_data["species"] = ""
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(e.field == "species" and e.code == "required" for e in result.errors)

    def test_invalid_species(self, validation_service, valid_character_data):
        """Test that non-existent species is invalid."""
        valid_character_data["species"] = "InvalidSpecies123"
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(
            e.field == "species" and e.code == "invalid_choice" for e in result.errors
        )


@pytest.mark.django_db
class TestClassValidation:
    """Tests for character class validation."""

    def test_empty_class_invalid(self, validation_service, valid_character_data):
        """Test that empty class is invalid."""
        valid_character_data["character_class"] = ""
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(
            e.field == "character_class" and e.code == "required" for e in result.errors
        )

    def test_invalid_class(self, validation_service, valid_character_data):
        """Test that non-existent class is invalid."""
        valid_character_data["character_class"] = "InvalidClass123"
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(
            e.field == "character_class" and e.code == "invalid_choice"
            for e in result.errors
        )


@pytest.mark.django_db
class TestBackgroundValidation:
    """Tests for background validation."""

    def test_empty_background_invalid(self, validation_service, valid_character_data):
        """Test that empty background is invalid."""
        valid_character_data["background"] = ""
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(
            e.field == "background" and e.code == "required" for e in result.errors
        )

    def test_invalid_background(self, validation_service, valid_character_data):
        """Test that non-existent background is invalid."""
        valid_character_data["background"] = "InvalidBackground123"
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(
            e.field == "background" and e.code == "invalid_choice"
            for e in result.errors
        )


@pytest.mark.django_db
class TestAbilityScoreValidation:
    """Tests for ability score validation."""

    def test_valid_ability_scores(self, validation_service, valid_character_data, srd_data):
        """Test valid ability scores."""
        result = validation_service.validate(**valid_character_data)
        assert result.is_valid is True

    def test_invalid_ability_name(self, validation_service, valid_character_data):
        """Test invalid ability score name."""
        valid_character_data["ability_scores"]["invalid"] = 10
        result = validation_service.validate(**valid_character_data)

        assert any(
            e.field == "ability_scores" and e.code == "invalid_ability"
            for e in result.errors
        )

    def test_ability_below_min(self, validation_service, valid_character_data):
        """Test ability score below minimum."""
        valid_character_data["ability_scores"]["str"] = 0
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(
            e.field == "ability_scores" and e.code == "min_value" for e in result.errors
        )

    def test_ability_above_max(self, validation_service, valid_character_data):
        """Test ability score above maximum."""
        valid_character_data["ability_scores"]["str"] = 31
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(
            e.field == "ability_scores" and e.code == "max_value" for e in result.errors
        )

    def test_ability_above_standard_max_warning(
        self, validation_service, valid_character_data, srd_data
    ):
        """Test that ability above 20 generates warning but is valid."""
        valid_character_data["ability_scores"]["str"] = 22
        result = validation_service.validate(**valid_character_data)

        # Should be valid (22 is under 30)
        assert result.is_valid is True
        # Should have warning about exceeding typical max
        assert any("22" in w and "20" in w for w in result.warnings)

    def test_non_numeric_ability_invalid(self, validation_service, valid_character_data):
        """Test that non-numeric ability score is invalid."""
        valid_character_data["ability_scores"]["str"] = "high"
        result = validation_service.validate(**valid_character_data)

        assert result.is_valid is False
        assert any(
            e.field == "ability_scores" and e.code == "invalid_type"
            for e in result.errors
        )

    def test_missing_abilities_warning(self, validation_service, valid_character_data, srd_data):
        """Test that missing abilities generate warning."""
        valid_character_data["ability_scores"] = {"str": 16}  # Only one ability
        result = validation_service.validate(**valid_character_data)

        # Valid but with warning
        assert result.is_valid is True
        assert any("Missing ability scores" in w for w in result.warnings)

    def test_all_abilities_present(self, validation_service, valid_character_data):
        """Test all ability abbreviations are valid."""
        for ability in ABILITY_ABBREVIATIONS:
            data = valid_character_data.copy()
            data["ability_scores"] = {ability: 10}
            result = validation_service.validate(**data)
            # Should not have invalid_ability error
            assert not any(
                e.code == "invalid_ability" for e in result.errors
            ), f"Ability {ability} should be valid"


@pytest.mark.django_db
class TestSkillValidation:
    """Tests for skill validation."""

    def test_expertise_without_proficiency_warning(
        self, validation_service, valid_character_data, srd_data
    ):
        """Test that expertise without proficiency generates warning."""
        valid_character_data["skills"] = {
            "Stealth": {"proficient": False, "expertise": True}
        }
        result = validation_service.validate(**valid_character_data)

        assert any("expertise" in w.lower() for w in result.warnings)


@pytest.mark.django_db
class TestSpellbookValidation:
    """Tests for spellbook validation."""

    def test_invalid_spellcasting_ability(
        self, validation_service, valid_character_data
    ):
        """Test invalid spellcasting ability."""
        valid_character_data["spellbook"] = {"spellcasting_ability": "invalid"}
        result = validation_service.validate(**valid_character_data)

        assert any(
            e.field == "spellbook" and e.code == "invalid_ability"
            for e in result.errors
        )

    def test_valid_spellcasting_abilities(
        self, validation_service, valid_character_data
    ):
        """Test all valid spellcasting abilities."""
        for ability in ABILITY_ABBREVIATIONS:
            data = valid_character_data.copy()
            data["spellbook"] = {"spellcasting_ability": ability}
            result = validation_service.validate(**data)
            assert not any(
                e.field == "spellbook" and e.code == "invalid_ability"
                for e in result.errors
            ), f"Ability {ability} should be valid for spellcasting"

    def test_prepared_not_in_known(self, validation_service, valid_character_data):
        """Test that prepared spell not in known spells is invalid."""
        valid_character_data["spellbook"] = {
            "known_spells": ["Magic Missile"],
            "prepared_spells": ["Fireball"],  # Not in known
        }
        result = validation_service.validate(**valid_character_data)

        assert any(
            e.field == "spellbook" and e.code == "not_known" for e in result.errors
        )

    def test_invalid_spell_slot_level(self, validation_service, valid_character_data):
        """Test invalid spell slot level."""
        valid_character_data["spellbook"] = {"spell_slots": {"10": {"max": 1}}}
        result = validation_service.validate(**valid_character_data)

        assert any(
            e.field == "spellbook" and e.code == "invalid_slot_level"
            for e in result.errors
        )

    def test_non_numeric_spell_slot_level(
        self, validation_service, valid_character_data
    ):
        """Test non-numeric spell slot level."""
        valid_character_data["spellbook"] = {"spell_slots": {"first": {"max": 1}}}
        result = validation_service.validate(**valid_character_data)

        assert any(
            e.field == "spellbook" and e.code == "invalid_type" for e in result.errors
        )

    def test_used_exceeds_max_warning(self, validation_service, valid_character_data):
        """Test that used slots exceeding max generates warning."""
        valid_character_data["spellbook"] = {
            "spell_slots": {"1": {"max": 2, "used": 5}}
        }
        result = validation_service.validate(**valid_character_data)

        assert any("used" in w.lower() and "max" in w.lower() for w in result.warnings)


@pytest.mark.django_db
class TestCampaignValidation:
    """Tests for stricter campaign validation."""

    def test_campaign_requires_all_abilities(
        self, validation_service, valid_character_data
    ):
        """Test that campaign validation requires all ability scores."""
        valid_character_data["ability_scores"] = {"str": 16}  # Missing others
        result = validation_service.validate_for_campaign(**valid_character_data)

        assert result.is_valid is False
        assert any(
            e.field == "ability_scores" and e.code == "required" for e in result.errors
        )

    def test_campaign_valid_with_all_abilities(
        self, validation_service, valid_character_data
    ):
        """Test that campaign validation passes with all abilities."""
        result = validation_service.validate_for_campaign(**valid_character_data)
        # May still have other validation issues (SRD data not present)
        # but ability scores should be fine
        assert not any(
            e.field == "ability_scores" and e.code == "required" for e in result.errors
        )
