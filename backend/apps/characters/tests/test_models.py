"""
Unit tests for CharacterSheet model.

Tests cover model creation, validation, property calculations,
and helper methods following SRD 5.2 mechanics.
"""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.characters.models import CharacterSheet

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testplayer",
        email="player@test.com",
        password="testpass123",
    )


@pytest.fixture
def basic_character(user):
    """Create a basic level 1 fighter character."""
    return CharacterSheet.objects.create(
        user=user,
        name="Thorin Ironforge",
        species="Dwarf",
        character_class="Fighter",
        background="Soldier",
        level=1,
        hit_points_max=12,
        hit_points_current=12,
        ability_scores_json={
            "str": 16,
            "dex": 12,
            "con": 14,
            "int": 10,
            "wis": 8,
            "cha": 10,
        },
        skills_json={
            "athletics": {"proficient": True, "expertise": False},
            "intimidation": {"proficient": True, "expertise": False},
        },
        proficiencies_json={
            "armor": ["light", "medium", "heavy", "shields"],
            "weapons": ["simple", "martial"],
            "tools": [],
            "languages": ["Common", "Dwarvish"],
            "saving_throws": ["str", "con"],
        },
        features_json=[
            {"name": "Fighting Style", "source": "Fighter 1", "description": "Defense"},
            {"name": "Second Wind", "source": "Fighter 1", "description": "Heal 1d10 + level"},
        ],
        equipment_json={
            "inventory": [
                {"name": "Chain Mail", "qty": 1, "equipped": True},
                {"name": "Longsword", "qty": 1, "equipped": True},
                {"name": "Shield", "qty": 1, "equipped": True},
            ],
            "money": {"gp": 10, "sp": 0, "cp": 0, "ep": 0, "pp": 0},
        },
        hit_dice_json={"d10": {"max": 1, "spent": 0}},
    )


@pytest.fixture
def multiclass_character(user):
    """Create a multiclass Fighter 3/Wizard 2 character."""
    return CharacterSheet.objects.create(
        user=user,
        name="Elara Stormwind",
        species="Human",
        character_class="Fighter",
        subclass="Eldritch Knight",
        background="Sage",
        level=5,
        multiclass_json={"Fighter": 3, "Wizard": 2},
        hit_points_max=38,
        hit_points_current=38,
        ability_scores_json={
            "str": 14,
            "dex": 10,
            "con": 14,
            "int": 16,
            "wis": 12,
            "cha": 8,
        },
        skills_json={
            "athletics": {"proficient": True, "expertise": False},
            "arcana": {"proficient": True, "expertise": True},
        },
        proficiencies_json={
            "saving_throws": ["str", "con", "int"],
        },
        spellbook_json={
            "spellcasting_ability": "int",
            "spell_save_dc": 14,
            "spell_attack_bonus": 6,
            "cantrips_known": ["Fire Bolt", "Light"],
            "spells_known": ["Shield", "Magic Missile", "Find Familiar"],
            "spells_prepared": ["Shield", "Magic Missile"],
            "spell_slots": {
                "1": {"max": 4, "used": 1},
                "2": {"max": 2, "used": 0},
            },
        },
        hit_dice_json={
            "d10": {"max": 3, "spent": 1},
            "d6": {"max": 2, "spent": 0},
        },
    )


@pytest.fixture
def spellcaster_character(user):
    """Create a level 5 wizard character."""
    return CharacterSheet.objects.create(
        user=user,
        name="Gandalf the Grey",
        species="Human",
        character_class="Wizard",
        subclass="School of Evocation",
        background="Hermit",
        level=5,
        hit_points_max=22,
        hit_points_current=18,
        hit_points_temp=5,
        ability_scores_json={
            "str": 8,
            "dex": 14,
            "con": 12,
            "int": 18,
            "wis": 14,
            "cha": 10,
        },
        skills_json={
            "arcana": {"proficient": True, "expertise": True},
            "investigation": {"proficient": True, "expertise": False},
            "history": {"proficient": True, "expertise": False},
        },
        proficiencies_json={
            "armor": [],
            "weapons": ["daggers", "darts", "slings", "quarterstaffs", "light crossbows"],
            "tools": [],
            "languages": ["Common", "Elvish", "Draconic"],
            "saving_throws": ["int", "wis"],
        },
        spellbook_json={
            "spellcasting_ability": "int",
            "spell_save_dc": 15,
            "spell_attack_bonus": 7,
            "cantrips_known": ["Fire Bolt", "Light", "Prestidigitation", "Minor Illusion"],
            "spells_known": [
                "Magic Missile", "Shield", "Detect Magic", "Fireball",
                "Counterspell", "Fly", "Misty Step"
            ],
            "spells_prepared": ["Fireball", "Shield", "Counterspell", "Fly"],
            "spell_slots": {
                "1": {"max": 4, "used": 2},
                "2": {"max": 3, "used": 1},
                "3": {"max": 2, "used": 0},
            },
        },
        hit_dice_json={"d6": {"max": 5, "spent": 2}},
    )


class TestCharacterSheetCreation:
    """Tests for character sheet creation and basic functionality."""

    def test_create_basic_character(self, basic_character):
        """Test that a basic character can be created."""
        assert basic_character.name == "Thorin Ironforge"
        assert basic_character.species == "Dwarf"
        assert basic_character.character_class == "Fighter"
        assert basic_character.level == 1
        assert isinstance(basic_character.id, uuid.UUID)

    def test_character_str_representation(self, basic_character):
        """Test string representation of character."""
        expected = "Thorin Ironforge (Level 1 Fighter)"
        assert str(basic_character) == expected

    def test_character_with_subclass(self, multiclass_character):
        """Test character with subclass."""
        assert multiclass_character.subclass == "Eldritch Knight"

    def test_character_auto_timestamps(self, basic_character):
        """Test that timestamps are auto-generated."""
        assert basic_character.created_at is not None
        assert basic_character.updated_at is not None

    def test_character_uuid_auto_generated(self, user):
        """Test that UUID is auto-generated."""
        char = CharacterSheet.objects.create(
            user=user,
            name="Test Character",
            species="Human",
            character_class="Rogue",
            background="Criminal",
        )
        assert isinstance(char.id, uuid.UUID)
        assert char.id != uuid.UUID(int=0)

    def test_default_values(self, user):
        """Test that default values are set correctly."""
        char = CharacterSheet.objects.create(
            user=user,
            name="Minimal Character",
            species="Human",
            character_class="Fighter",
            background="Soldier",
        )
        assert char.level == 1
        assert char.hit_points_max == 0
        assert char.hit_points_current == 0
        assert char.hit_points_temp == 0
        assert char.speed == 30
        assert char.armor_class == 10
        assert char.armor_class_base == 10
        assert char.initiative_bonus == 0
        assert char.has_inspiration is False
        assert char.size == "medium"

    def test_character_size_choices(self, user):
        """Test valid size choices."""
        for size_value, _ in CharacterSheet.SIZE_CHOICES:
            char = CharacterSheet.objects.create(
                user=user,
                name=f"Test {size_value}",
                species="Creature",
                character_class="Fighter",
                background="Soldier",
                size=size_value,
            )
            assert char.size == size_value


class TestProficiencyBonus:
    """Tests for proficiency bonus calculation."""

    def test_level_1_proficiency(self, user):
        """Level 1 should have +2 proficiency."""
        char = CharacterSheet.objects.create(
            user=user, name="Test", species="Human",
            character_class="Fighter", background="Soldier", level=1
        )
        assert char.proficiency_bonus == 2

    def test_level_4_proficiency(self, user):
        """Level 4 should have +2 proficiency."""
        char = CharacterSheet.objects.create(
            user=user, name="Test", species="Human",
            character_class="Fighter", background="Soldier", level=4
        )
        assert char.proficiency_bonus == 2

    def test_level_5_proficiency(self, user):
        """Level 5 should have +3 proficiency."""
        char = CharacterSheet.objects.create(
            user=user, name="Test", species="Human",
            character_class="Fighter", background="Soldier", level=5
        )
        assert char.proficiency_bonus == 3

    def test_level_9_proficiency(self, user):
        """Level 9 should have +4 proficiency."""
        char = CharacterSheet.objects.create(
            user=user, name="Test", species="Human",
            character_class="Fighter", background="Soldier", level=9
        )
        assert char.proficiency_bonus == 4

    def test_level_13_proficiency(self, user):
        """Level 13 should have +5 proficiency."""
        char = CharacterSheet.objects.create(
            user=user, name="Test", species="Human",
            character_class="Fighter", background="Soldier", level=13
        )
        assert char.proficiency_bonus == 5

    def test_level_17_proficiency(self, user):
        """Level 17 should have +6 proficiency."""
        char = CharacterSheet.objects.create(
            user=user, name="Test", species="Human",
            character_class="Fighter", background="Soldier", level=17
        )
        assert char.proficiency_bonus == 6

    def test_level_20_proficiency(self, user):
        """Level 20 should have +6 proficiency."""
        char = CharacterSheet.objects.create(
            user=user, name="Test", species="Human",
            character_class="Fighter", background="Soldier", level=20
        )
        assert char.proficiency_bonus == 6


class TestAbilityModifiers:
    """Tests for ability score modifier calculation."""

    def test_ability_modifier_standard(self, basic_character):
        """Test standard ability modifiers."""
        # STR 16 = +3
        assert basic_character.get_ability_modifier("str") == 3
        # DEX 12 = +1
        assert basic_character.get_ability_modifier("dex") == 1
        # CON 14 = +2
        assert basic_character.get_ability_modifier("con") == 2
        # INT 10 = +0
        assert basic_character.get_ability_modifier("int") == 0
        # WIS 8 = -1
        assert basic_character.get_ability_modifier("wis") == -1
        # CHA 10 = +0
        assert basic_character.get_ability_modifier("cha") == 0

    def test_ability_modifier_high_score(self, spellcaster_character):
        """Test high ability score modifier."""
        # INT 18 = +4
        assert spellcaster_character.get_ability_modifier("int") == 4

    def test_ability_modifier_low_score(self, spellcaster_character):
        """Test low ability score modifier."""
        # STR 8 = -1
        assert spellcaster_character.get_ability_modifier("str") == -1

    def test_ability_modifier_case_insensitive(self, basic_character):
        """Test that ability lookup is case insensitive."""
        assert basic_character.get_ability_modifier("STR") == 3
        assert basic_character.get_ability_modifier("Str") == 3
        assert basic_character.get_ability_modifier("str") == 3

    def test_ability_modifier_missing_defaults_to_10(self, basic_character):
        """Test that missing abilities default to 10 (modifier 0)."""
        assert basic_character.get_ability_modifier("nonexistent") == 0


class TestSkillBonuses:
    """Tests for skill bonus calculation."""

    def test_skill_with_proficiency(self, basic_character):
        """Test skill bonus with proficiency."""
        # Athletics: STR (+3) + proficiency (+2) = +5
        assert basic_character.get_skill_bonus("athletics", "str") == 5

    def test_skill_with_expertise(self, spellcaster_character):
        """Test skill bonus with expertise."""
        # Arcana: INT (+4) + expertise (+6) = +10 at level 5
        assert spellcaster_character.get_skill_bonus("arcana", "int") == 10

    def test_skill_without_proficiency(self, basic_character):
        """Test skill bonus without proficiency."""
        # Stealth (not proficient): DEX (+1) only
        assert basic_character.get_skill_bonus("stealth", "dex") == 1

    def test_skill_nonexistent_defaults_to_ability_only(self, basic_character):
        """Test that nonexistent skills default to ability modifier only."""
        # Made-up skill with STR
        assert basic_character.get_skill_bonus("made_up_skill", "str") == 3


class TestSavingThrows:
    """Tests for saving throw bonus calculation."""

    def test_saving_throw_with_proficiency(self, basic_character):
        """Test saving throw with proficiency."""
        # STR save: modifier (+3) + proficiency (+2) = +5
        assert basic_character.get_saving_throw_bonus("str") == 5
        # CON save: modifier (+2) + proficiency (+2) = +4
        assert basic_character.get_saving_throw_bonus("con") == 4

    def test_saving_throw_without_proficiency(self, basic_character):
        """Test saving throw without proficiency."""
        # DEX save: modifier (+1) only
        assert basic_character.get_saving_throw_bonus("dex") == 1
        # WIS save: modifier (-1) only
        assert basic_character.get_saving_throw_bonus("wis") == -1

    def test_saving_throw_case_insensitive(self, basic_character):
        """Test that proficiency lookup is case insensitive."""
        assert basic_character.get_saving_throw_bonus("STR") == 5
        assert basic_character.get_saving_throw_bonus("Str") == 5


class TestMulticlassCharacters:
    """Tests for multiclass character features."""

    def test_is_multiclass_true(self, multiclass_character):
        """Test is_multiclass returns True for multiclass character."""
        assert multiclass_character.is_multiclass is True

    def test_is_multiclass_false(self, basic_character):
        """Test is_multiclass returns False for single-class character."""
        assert basic_character.is_multiclass is False

    def test_multiclass_json_content(self, multiclass_character):
        """Test multiclass JSON contains correct class levels."""
        assert multiclass_character.multiclass_json == {"Fighter": 3, "Wizard": 2}


class TestProficiencyChecks:
    """Tests for proficiency checking functionality."""

    def test_armor_proficiency(self, basic_character):
        """Test checking armor proficiency."""
        assert basic_character.is_proficient_with("armor", "heavy") is True
        assert basic_character.is_proficient_with("armor", "shields") is True

    def test_weapon_proficiency(self, basic_character):
        """Test checking weapon proficiency."""
        assert basic_character.is_proficient_with("weapons", "martial") is True
        assert basic_character.is_proficient_with("weapons", "simple") is True

    def test_proficiency_case_insensitive(self, basic_character):
        """Test that proficiency check is case insensitive."""
        assert basic_character.is_proficient_with("armor", "Heavy") is True
        assert basic_character.is_proficient_with("armor", "HEAVY") is True

    def test_no_proficiency(self, spellcaster_character):
        """Test checking lack of proficiency."""
        assert spellcaster_character.is_proficient_with("armor", "heavy") is False
        assert spellcaster_character.is_proficient_with("armor", "medium") is False


class TestSpellSlots:
    """Tests for spell slot tracking."""

    def test_get_spell_slots_remaining(self, spellcaster_character):
        """Test getting remaining spell slots."""
        # Level 1: max 4, used 2 = 2 remaining
        assert spellcaster_character.get_spell_slots_remaining(1) == 2
        # Level 2: max 3, used 1 = 2 remaining
        assert spellcaster_character.get_spell_slots_remaining(2) == 2
        # Level 3: max 2, used 0 = 2 remaining
        assert spellcaster_character.get_spell_slots_remaining(3) == 2

    def test_spell_slots_for_level_without_slots(self, spellcaster_character):
        """Test getting spell slots for level without slots."""
        # Level 9 spell slots don't exist for level 5 wizard
        assert spellcaster_character.get_spell_slots_remaining(9) == 0

    def test_spell_slots_non_caster(self, basic_character):
        """Test getting spell slots for non-caster."""
        assert basic_character.get_spell_slots_remaining(1) == 0


class TestHitDice:
    """Tests for hit dice tracking."""

    def test_get_hit_dice_remaining_single_type(self, basic_character):
        """Test getting remaining hit dice for single-class character."""
        remaining = basic_character.get_hit_dice_remaining()
        assert remaining == {"d10": 1}

    def test_get_hit_dice_remaining_multiclass(self, multiclass_character):
        """Test getting remaining hit dice for multiclass character."""
        remaining = multiclass_character.get_hit_dice_remaining()
        # d10: max 3, spent 1 = 2 remaining
        # d6: max 2, spent 0 = 2 remaining
        assert remaining == {"d10": 2, "d6": 2}

    def test_get_hit_dice_remaining_partial_spent(self, spellcaster_character):
        """Test getting remaining hit dice with some spent."""
        remaining = spellcaster_character.get_hit_dice_remaining()
        # d6: max 5, spent 2 = 3 remaining
        assert remaining == {"d6": 3}


class TestConditionsAndDeathSaves:
    """Tests for condition and death save tracking."""

    def test_conditions_default_empty(self, basic_character):
        """Test that conditions default to empty list."""
        assert basic_character.conditions_json == []

    def test_death_saves_default_empty(self, basic_character):
        """Test that death saves default to empty dict."""
        assert basic_character.death_saves_json == {}

    def test_add_conditions(self, user):
        """Test adding conditions to character."""
        char = CharacterSheet.objects.create(
            user=user,
            name="Poisoned Fighter",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            conditions_json=["poisoned", "frightened"],
        )
        assert "poisoned" in char.conditions_json
        assert "frightened" in char.conditions_json

    def test_death_saves_tracking(self, user):
        """Test death save tracking."""
        char = CharacterSheet.objects.create(
            user=user,
            name="Dying Fighter",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            hit_points_current=0,
            death_saves_json={"successes": 2, "failures": 1},
        )
        assert char.death_saves_json["successes"] == 2
        assert char.death_saves_json["failures"] == 1


class TestPersonalityAndBackstory:
    """Tests for personality and backstory fields."""

    def test_personality_json(self, user):
        """Test storing personality traits."""
        personality = {
            "traits": ["I speak very slowly."],
            "ideals": ["Honor above all."],
            "bonds": ["My weapon is my best friend."],
            "flaws": ["I trust no one."],
        }
        char = CharacterSheet.objects.create(
            user=user,
            name="Deep Character",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            personality_json=personality,
        )
        assert char.personality_json["traits"] == ["I speak very slowly."]
        assert char.personality_json["ideals"] == ["Honor above all."]

    def test_backstory_field(self, user):
        """Test storing character backstory."""
        backstory = "Born in a small village, trained by a legendary swordmaster."
        char = CharacterSheet.objects.create(
            user=user,
            name="Story Character",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            backstory=backstory,
        )
        assert char.backstory == backstory


class TestHomebrewOverrides:
    """Tests for homebrew override tracking."""

    def test_homebrew_overrides_json(self, user):
        """Test storing homebrew override references."""
        overrides = {
            "species": "550e8400-e29b-41d4-a716-446655440001",
            "class": "550e8400-e29b-41d4-a716-446655440002",
            "items": ["550e8400-e29b-41d4-a716-446655440003"],
        }
        char = CharacterSheet.objects.create(
            user=user,
            name="Homebrew Character",
            species="Starborn",
            character_class="Star Knight",
            background="Dimensional Traveler",
            homebrew_overrides_json=overrides,
        )
        assert char.homebrew_overrides_json["species"] == "550e8400-e29b-41d4-a716-446655440001"


class TestCharacterRelationships:
    """Tests for character model relationships."""

    def test_user_relationship(self, basic_character, user):
        """Test that character is linked to user."""
        assert basic_character.user == user
        assert basic_character in user.characters.all()

    def test_cascade_delete_on_user(self, basic_character, user):
        """Test that character is deleted when user is deleted."""
        char_id = basic_character.id
        user.delete()
        assert not CharacterSheet.objects.filter(id=char_id).exists()

    def test_universe_relationship_optional(self, basic_character):
        """Test that universe relationship is optional."""
        assert basic_character.universe is None


class TestLevelValidation:
    """Tests for level validation."""

    def test_level_minimum_valid(self, user):
        """Test that level 1 is valid minimum."""
        char = CharacterSheet.objects.create(
            user=user,
            name="Level 1",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=1,
        )
        char.full_clean()  # Should not raise

    def test_level_maximum_valid(self, user):
        """Test that level 20 is valid maximum."""
        char = CharacterSheet.objects.create(
            user=user,
            name="Level 20",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=20,
        )
        char.full_clean()  # Should not raise

    def test_level_zero_invalid(self, user):
        """Test that level 0 is invalid."""
        char = CharacterSheet(
            user=user,
            name="Level 0",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=0,
        )
        with pytest.raises(ValidationError):
            char.full_clean()

    def test_level_above_20_invalid(self, user):
        """Test that level above 20 is invalid."""
        char = CharacterSheet(
            user=user,
            name="Level 21",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=21,
        )
        with pytest.raises(ValidationError):
            char.full_clean()


class TestInspiration:
    """Tests for inspiration tracking."""

    def test_inspiration_default_false(self, basic_character):
        """Test that inspiration defaults to False."""
        assert basic_character.has_inspiration is False

    def test_inspiration_can_be_set(self, user):
        """Test that inspiration can be set to True."""
        char = CharacterSheet.objects.create(
            user=user,
            name="Inspired",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            has_inspiration=True,
        )
        assert char.has_inspiration is True
