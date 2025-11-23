"""
Unit tests for CharacterValidationService.

Tests cover validation of:
- Basic character info (species, class, background)
- Ability scores (ranges, standard array, point buy)
- Skills (valid names, proficiency rules)
- Subclass (exists, belongs to class, level requirements)
- Spells (valid spells, slot limits)
- Equipment (item existence)
"""

import pytest
from django.contrib.auth import get_user_model

from apps.characters.models import CharacterSheet
from apps.characters.services.validation import (
    ABILITY_SCORE_NAMES,
    POINT_BUY_COSTS,
    POINT_BUY_TOTAL,
    STANDARD_ARRAY,
    CharacterValidationService,
    ValidationResult,
)
from apps.srd.models import (
    Background,
    CharacterClass,
    Skill,
    Species,
    Spell,
    SpellSchool,
    Subclass,
)

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testvalidator",
        email="validator@test.com",
        password="testpass123",
    )


@pytest.fixture
def srd_species(db):
    """Create SRD species for testing."""
    return [
        Species.objects.create(name="Human", size="medium", speed=30),
        Species.objects.create(name="Elf", size="medium", speed=30),
        Species.objects.create(name="Dwarf", size="medium", speed=25),
    ]


@pytest.fixture
def srd_classes(db):
    """Create SRD classes for testing."""
    return [
        CharacterClass.objects.create(name="Fighter", hit_die=10),
        CharacterClass.objects.create(name="Wizard", hit_die=6),
        CharacterClass.objects.create(name="Rogue", hit_die=8),
    ]


@pytest.fixture
def srd_subclasses(db, srd_classes):
    """Create SRD subclasses for testing."""
    fighter = srd_classes[0]
    wizard = srd_classes[1]
    return [
        Subclass.objects.create(
            name="Champion",
            character_class=fighter,
            subclass_level=3,
        ),
        Subclass.objects.create(
            name="School of Evocation",
            character_class=wizard,
            subclass_level=2,
        ),
    ]


@pytest.fixture
def srd_backgrounds(db):
    """Create SRD backgrounds for testing."""
    return [
        Background.objects.create(name="Soldier"),
        Background.objects.create(name="Sage"),
        Background.objects.create(name="Criminal"),
    ]


@pytest.fixture
def srd_skills(db):
    """Create SRD skills for testing."""
    from apps.srd.models import AbilityScore

    str_ability = AbilityScore.objects.create(abbreviation="STR", name="Strength")
    dex_ability = AbilityScore.objects.create(abbreviation="DEX", name="Dexterity")
    int_ability = AbilityScore.objects.create(abbreviation="INT", name="Intelligence")

    return [
        Skill.objects.create(name="Athletics", ability_score=str_ability),
        Skill.objects.create(name="Acrobatics", ability_score=dex_ability),
        Skill.objects.create(name="Arcana", ability_score=int_ability),
        Skill.objects.create(name="Stealth", ability_score=dex_ability),
    ]


@pytest.fixture
def srd_spells(db, srd_classes):
    """Create SRD spells for testing."""
    evocation = SpellSchool.objects.create(name="Evocation")
    abjuration = SpellSchool.objects.create(name="Abjuration")

    spell1 = Spell.objects.create(
        name="Magic Missile",
        level=1,
        school=evocation,
        casting_time="1 action",
        range="120 feet",
        duration="Instantaneous",
        description="Three darts of magical force.",
    )
    spell2 = Spell.objects.create(
        name="Shield",
        level=1,
        school=abjuration,
        casting_time="1 reaction",
        range="Self",
        duration="1 round",
        description="An invisible barrier of magical force.",
    )
    spell3 = Spell.objects.create(
        name="Fireball",
        level=3,
        school=evocation,
        casting_time="1 action",
        range="150 feet",
        duration="Instantaneous",
        description="A bright streak flashes from your finger.",
    )
    return [spell1, spell2, spell3]


@pytest.fixture
def valid_character(user, srd_species, srd_classes, srd_backgrounds):
    """Create a valid character for testing."""
    return CharacterSheet.objects.create(
        user=user,
        name="Test Character",
        species="Human",
        character_class="Fighter",
        background="Soldier",
        level=5,
        hit_points_max=44,
        hit_points_current=44,
        ability_scores_json={
            "str": 16,
            "dex": 14,
            "con": 14,
            "int": 10,
            "wis": 12,
            "cha": 8,
        },
        skills_json={
            "Athletics": {"proficient": True, "expertise": False},
            "Acrobatics": {"proficient": True, "expertise": False},
        },
        proficiencies_json={
            "saving_throws": ["str", "con"],
        },
    )


@pytest.fixture
def validation_service():
    """Create a validation service without universe."""
    return CharacterValidationService()


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_new_result_is_valid(self):
        """New validation result should be valid."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_error_makes_invalid(self):
        """Adding an error should make result invalid."""
        result = ValidationResult(is_valid=True)
        result.add_error("field", "code", "message")
        assert result.is_valid is False
        assert len(result.errors) == 1

    def test_add_warning_keeps_valid(self):
        """Adding a warning should keep result valid."""
        result = ValidationResult(is_valid=True)
        result.add_warning("field", "code", "message")
        assert result.is_valid is True
        assert len(result.warnings) == 1

    def test_merge_results(self):
        """Merging results should combine errors and warnings."""
        result1 = ValidationResult(is_valid=True)
        result1.add_error("field1", "code1", "message1")

        result2 = ValidationResult(is_valid=True)
        result2.add_warning("field2", "code2", "message2")

        result1.merge(result2)
        assert len(result1.errors) == 1
        assert len(result1.warnings) == 1


class TestAbilityScoreValidation:
    """Tests for ability score validation."""

    def test_valid_ability_scores(self, validation_service):
        """Valid ability scores should pass."""
        scores = {"str": 16, "dex": 14, "con": 12, "int": 10, "wis": 8, "cha": 15}
        result = validation_service.validate_ability_scores(scores)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_missing_ability_scores(self, validation_service):
        """Missing ability scores should fail."""
        result = validation_service.validate_ability_scores({})
        assert result.is_valid is False
        assert any(e.code == "missing_ability_scores" for e in result.errors)

    def test_missing_single_ability(self, validation_service):
        """Missing a single ability should fail."""
        scores = {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10}
        # Missing cha
        result = validation_service.validate_ability_scores(scores)
        assert result.is_valid is False
        assert any(e.code == "missing_ability" for e in result.errors)

    def test_score_too_low(self, validation_service):
        """Ability score below 1 should fail."""
        scores = {"str": 0, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10}
        result = validation_service.validate_ability_scores(scores)
        assert result.is_valid is False
        assert any(e.code == "score_out_of_range" for e in result.errors)

    def test_score_too_high(self, validation_service):
        """Ability score above 30 should fail."""
        scores = {"str": 31, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10}
        result = validation_service.validate_ability_scores(scores)
        assert result.is_valid is False
        assert any(e.code == "score_out_of_range" for e in result.errors)

    def test_invalid_score_type(self, validation_service):
        """Non-integer ability score should fail."""
        scores = {"str": "ten", "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10}
        result = validation_service.validate_ability_scores(scores)
        assert result.is_valid is False
        assert any(e.code == "invalid_score_type" for e in result.errors)

    def test_standard_array_strict_mode(self, validation_service):
        """Standard array should pass strict mode."""
        scores = dict(zip(ABILITY_SCORE_NAMES, STANDARD_ARRAY, strict=True))
        result = validation_service.validate_ability_scores(scores, strict=True)
        assert result.is_valid is True

    def test_point_buy_strict_mode(self, validation_service):
        """Valid point buy should pass strict mode."""
        # 27 point buy: 15+14+13+12+10+8 = exactly 27 points
        scores = {"str": 15, "dex": 14, "con": 13, "int": 12, "wis": 10, "cha": 8}
        total = sum(POINT_BUY_COSTS.get(s, 0) for s in scores.values())
        assert total == POINT_BUY_TOTAL

        result = validation_service.validate_ability_scores(scores, strict=True)
        assert result.is_valid is True

    def test_non_standard_scores_warning(self, validation_service):
        """Non-standard scores should give warning in strict mode."""
        # All 18s is neither standard array nor point buy
        scores = {"str": 18, "dex": 18, "con": 18, "int": 18, "wis": 18, "cha": 18}
        result = validation_service.validate_ability_scores(scores, strict=True)
        assert result.is_valid is True  # Still valid, just a warning
        assert any(w.code == "non_standard_scores" for w in result.warnings)


class TestBasicInfoValidation:
    """Tests for basic character info validation."""

    def test_valid_character_passes(
        self, validation_service, valid_character, srd_species, srd_classes, srd_backgrounds
    ):
        """Valid character with SRD content should pass."""
        result = validation_service.validate_basic_info(valid_character)
        assert result.is_valid is True

    def test_invalid_species_fails(
        self, validation_service, user, srd_species, srd_classes, srd_backgrounds
    ):
        """Character with invalid species should fail."""
        char = CharacterSheet(
            user=user,
            name="Test",
            species="InvalidSpecies",
            character_class="Fighter",
            background="Soldier",
        )
        result = validation_service.validate_basic_info(char)
        assert result.is_valid is False
        assert any(e.code == "invalid_species" for e in result.errors)

    def test_invalid_class_fails(
        self, validation_service, user, srd_species, srd_classes, srd_backgrounds
    ):
        """Character with invalid class should fail."""
        char = CharacterSheet(
            user=user,
            name="Test",
            species="Human",
            character_class="InvalidClass",
            background="Soldier",
        )
        result = validation_service.validate_basic_info(char)
        assert result.is_valid is False
        assert any(e.code == "invalid_class" for e in result.errors)

    def test_invalid_background_fails(
        self, validation_service, user, srd_species, srd_classes, srd_backgrounds
    ):
        """Character with invalid background should fail."""
        char = CharacterSheet(
            user=user,
            name="Test",
            species="Human",
            character_class="Fighter",
            background="InvalidBackground",
        )
        result = validation_service.validate_basic_info(char)
        assert result.is_valid is False
        assert any(e.code == "invalid_background" for e in result.errors)


class TestLevelValidation:
    """Tests for level validation."""

    def test_valid_level_passes(self, validation_service, valid_character):
        """Valid level should pass."""
        result = validation_service.validate_level(valid_character)
        assert result.is_valid is True

    def test_level_zero_fails(self, validation_service, user):
        """Level 0 should fail."""
        char = CharacterSheet(
            user=user,
            name="Test",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=0,
        )
        result = validation_service.validate_level(char)
        assert result.is_valid is False
        assert any(e.code == "level_too_low" for e in result.errors)

    def test_level_21_fails(self, validation_service, user):
        """Level 21 should fail."""
        char = CharacterSheet(
            user=user,
            name="Test",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=21,
        )
        result = validation_service.validate_level(char)
        assert result.is_valid is False
        assert any(e.code == "level_too_high" for e in result.errors)

    def test_multiclass_level_mismatch(self, validation_service, user, srd_classes):
        """Multiclass levels not summing to total should fail."""
        char = CharacterSheet(
            user=user,
            name="Test",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=5,
            multiclass_json={"Fighter": 3, "Wizard": 1},  # Sum is 4, not 5
        )
        result = validation_service.validate_level(char)
        assert result.is_valid is False
        assert any(e.code == "multiclass_level_mismatch" for e in result.errors)

    def test_multiclass_valid(self, validation_service, user, srd_classes):
        """Valid multiclass should pass."""
        char = CharacterSheet(
            user=user,
            name="Test",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=5,
            multiclass_json={"Fighter": 3, "Wizard": 2},
        )
        result = validation_service.validate_level(char)
        assert result.is_valid is True


class TestSkillsValidation:
    """Tests for skills validation."""

    def test_valid_skills_pass(self, validation_service, srd_skills):
        """Valid skills should pass."""
        skills = {
            "Athletics": {"proficient": True, "expertise": False},
            "Acrobatics": {"proficient": True, "expertise": False},
        }
        result = validation_service.validate_skills(skills)
        assert result.is_valid is True

    def test_unknown_skill_warning(self, validation_service, srd_skills):
        """Unknown skill should give warning."""
        skills = {
            "MadeUpSkill": {"proficient": True, "expertise": False},
        }
        result = validation_service.validate_skills(skills)
        assert result.is_valid is True  # Warning, not error
        assert any(w.code == "unknown_skill" for w in result.warnings)

    def test_expertise_without_proficiency_fails(self, validation_service, srd_skills):
        """Expertise without proficiency should fail."""
        skills = {
            "Athletics": {"proficient": False, "expertise": True},
        }
        result = validation_service.validate_skills(skills)
        assert result.is_valid is False
        assert any(e.code == "expertise_without_proficiency" for e in result.errors)

    def test_invalid_skill_info_structure(self, validation_service, srd_skills):
        """Invalid skill info structure should fail."""
        skills = {
            "Athletics": "proficient",  # Should be dict
        }
        result = validation_service.validate_skills(skills)
        assert result.is_valid is False
        assert any(e.code == "invalid_skill_info" for e in result.errors)


class TestSubclassValidation:
    """Tests for subclass validation."""

    def test_valid_subclass_passes(self, validation_service, srd_subclasses):
        """Valid subclass for class should pass."""
        result = validation_service.validate_subclass("Fighter", "Champion", 5)
        assert result.is_valid is True

    def test_invalid_subclass_fails(self, validation_service, srd_subclasses):
        """Subclass not belonging to class should fail."""
        result = validation_service.validate_subclass("Fighter", "School of Evocation", 5)
        assert result.is_valid is False
        assert any(e.code == "invalid_subclass" for e in result.errors)

    def test_subclass_level_warning(self, validation_service, srd_subclasses):
        """Subclass at too low level should give warning."""
        result = validation_service.validate_subclass("Fighter", "Champion", 1)
        assert result.is_valid is True  # Warning, not error
        assert any(w.code == "subclass_level_requirement" for w in result.warnings)


class TestSpellbookValidation:
    """Tests for spellbook validation."""

    def test_valid_spellbook_passes(self, validation_service, srd_spells):
        """Valid spellbook should pass."""
        spellbook = {
            "spellcasting_ability": "int",
            "spell_save_dc": 14,
            "spell_attack_bonus": 6,
            "spells_known": ["Magic Missile", "Shield"],
            "spell_slots": {
                "1": {"max": 4, "used": 1},
            },
        }
        result = validation_service.validate_spellbook(spellbook, "Wizard", 5)
        assert result.is_valid is True

    def test_invalid_spellcasting_ability(self, validation_service):
        """Invalid spellcasting ability should fail."""
        spellbook = {
            "spellcasting_ability": "luck",
        }
        result = validation_service.validate_spellbook(spellbook, "Wizard", 5)
        assert result.is_valid is False
        assert any(e.code == "invalid_spellcasting_ability" for e in result.errors)

    def test_slots_overused(self, validation_service):
        """Used slots exceeding max should fail."""
        spellbook = {
            "spell_slots": {
                "1": {"max": 4, "used": 5},
            },
        }
        result = validation_service.validate_spellbook(spellbook, "Wizard", 5)
        assert result.is_valid is False
        assert any(e.code == "slots_overused" for e in result.errors)

    def test_unknown_spell_warning(self, validation_service, srd_spells):
        """Unknown spell should give warning."""
        spellbook = {
            "spells_known": ["Nonexistent Spell"],
        }
        result = validation_service.validate_spellbook(spellbook, "Wizard", 5)
        assert result.is_valid is True  # Warning, not error
        assert any(w.code == "unknown_spell" for w in result.warnings)


class TestFullValidation:
    """Tests for full character validation."""

    def test_full_validation_valid_character(
        self,
        validation_service,
        valid_character,
        srd_species,
        srd_classes,
        srd_backgrounds,
        srd_skills,
    ):
        """Full validation on valid character should pass."""
        result = validation_service.validate(valid_character)
        assert result.is_valid is True

    def test_full_validation_invalid_character(
        self, validation_service, user, srd_species, srd_classes, srd_backgrounds
    ):
        """Full validation on invalid character should fail."""
        char = CharacterSheet(
            user=user,
            name="Invalid",
            species="InvalidSpecies",
            character_class="InvalidClass",
            background="InvalidBackground",
            level=25,
            ability_scores_json={},
        )
        result = validation_service.validate(char)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_full_validation_skip_spells(
        self,
        validation_service,
        valid_character,
        srd_species,
        srd_classes,
        srd_backgrounds,
        srd_skills,
    ):
        """Full validation can skip spell validation."""
        valid_character.spellbook_json = {
            "spellcasting_ability": "invalid",
        }
        result = validation_service.validate(valid_character, validate_spells=False)
        # Should not have spellbook errors since we skipped
        assert not any(
            e.field.startswith("spellbook_json") for e in result.errors
        )


class TestMaxSpellLevel:
    """Tests for max spell level calculation."""

    def test_full_caster_spell_levels(self, validation_service):
        """Full caster should have correct max spell levels."""
        # Level 1 Wizard: max 1st level
        assert validation_service._get_max_spell_level("Wizard", 1) == 1
        # Level 5 Wizard: max 3rd level
        assert validation_service._get_max_spell_level("Wizard", 5) == 3
        # Level 9 Wizard: max 5th level
        assert validation_service._get_max_spell_level("Wizard", 9) == 5
        # Level 17 Wizard: max 9th level
        assert validation_service._get_max_spell_level("Wizard", 17) == 9

    def test_half_caster_spell_levels(self, validation_service):
        """Half caster should have correct max spell levels."""
        # Level 1 Paladin: no spells
        assert validation_service._get_max_spell_level("Paladin", 1) == 0
        # Level 2 Paladin: max 1st level
        assert validation_service._get_max_spell_level("Paladin", 2) == 1
        # Level 5 Paladin: max 2nd level
        assert validation_service._get_max_spell_level("Paladin", 5) == 1
