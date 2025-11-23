"""
Tests for characters models.

Tests the CharacterSheet model with all SRD 5.2 character attributes.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.characters.models import CharacterSheet
from apps.universes.models import Universe

User = get_user_model()


@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username="testplayer",
        email="player@example.com",
        password="testpass123",
        display_name="Test Player",
    )


@pytest.fixture
def universe(user):
    """Create a test universe."""
    return Universe.objects.create(
        user=user,
        name="Test Universe",
        description="A test universe for character testing",
    )


@pytest.fixture
def sample_ability_scores():
    """Sample ability scores for testing."""
    return {
        "str": 16,
        "dex": 14,
        "con": 12,
        "int": 10,
        "wis": 8,
        "cha": 15,
    }


@pytest.fixture
def sample_skills():
    """Sample skills for testing."""
    return {
        "acrobatics": {"proficient": False, "expertise": False},
        "athletics": {"proficient": True, "expertise": False},
        "perception": {"proficient": True, "expertise": True},
        "stealth": {"proficient": True, "expertise": False},
    }


@pytest.fixture
def sample_proficiencies():
    """Sample proficiencies for testing."""
    return {
        "armor": ["light", "medium", "shields"],
        "weapons": ["simple", "martial"],
        "tools": ["thieves_tools"],
        "languages": ["common", "elvish"],
        "saving_throws": ["str", "con"],
    }


@pytest.fixture
def sample_features():
    """Sample class features for testing."""
    return {
        "second_wind": {
            "name": "Second Wind",
            "description": "Regain 1d10 + level HP as bonus action",
            "uses_max": 1,
            "uses_remaining": 1,
            "recharge": "short_rest",
        },
        "action_surge": {
            "name": "Action Surge",
            "description": "Take an additional action",
            "uses_max": 1,
            "uses_remaining": 0,
            "recharge": "short_rest",
        },
    }


@pytest.fixture
def sample_spellbook():
    """Sample spellbook for testing."""
    return {
        "spellcasting_ability": "int",
        "spell_slots": {
            "1": {"max": 4, "used": 2},
            "2": {"max": 3, "used": 0},
        },
        "known_spells": ["magic_missile", "shield", "fireball"],
        "prepared_spells": ["magic_missile", "shield"],
        "cantrips": ["fire_bolt", "prestidigitation"],
    }


@pytest.fixture
def sample_equipment():
    """Sample equipment for testing."""
    return {
        "weapons": [
            {"item_id": "longsword", "equipped": True, "charges": None},
            {"item_id": "shortbow", "equipped": False, "charges": None},
        ],
        "armor": {"item_id": "chain_mail", "equipped": True},
        "items": [
            {"item_id": "potion_of_healing", "qty": 3},
            {"item_id": "rope_50ft", "qty": 1},
        ],
        "money": {"gp": 50, "sp": 20, "cp": 100},
    }


@pytest.mark.django_db
class TestCharacterSheetModel:
    """Tests for the CharacterSheet model."""

    def test_create_basic_character(self, user):
        """Test creating a basic character with required fields."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Aragorn",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=5,
        )

        assert character.name == "Aragorn"
        assert character.species == "Human"
        assert character.character_class == "Fighter"
        assert character.background == "Soldier"
        assert character.level == 5
        assert character.subclass == ""
        assert character.universe is None

    def test_character_uuid_pk(self, user):
        """Test that character has UUID primary key."""
        character = CharacterSheet.objects.create(
            user=user,
            name="UUID Test",
            species="Elf",
            character_class="Wizard",
            background="Sage",
        )

        # UUID should be a valid UUID string (36 chars with hyphens)
        assert len(str(character.id)) == 36
        assert "-" in str(character.id)

    def test_character_with_universe(self, user, universe):
        """Test creating a character tied to a universe."""
        character = CharacterSheet.objects.create(
            user=user,
            universe=universe,
            name="Universe Character",
            species="Dwarf",
            character_class="Cleric",
            background="Acolyte",
        )

        assert character.universe == universe
        assert character in universe.characters.all()

    def test_character_with_ability_scores(self, user, sample_ability_scores):
        """Test character with full ability scores."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Strong Fighter",
            species="Half-Orc",
            character_class="Barbarian",
            background="Outlander",
            ability_scores_json=sample_ability_scores,
        )

        assert character.ability_scores_json["str"] == 16
        assert character.ability_scores_json["dex"] == 14
        assert character.ability_scores_json["con"] == 12
        assert character.ability_scores_json["int"] == 10
        assert character.ability_scores_json["wis"] == 8
        assert character.ability_scores_json["cha"] == 15

    def test_character_with_skills(self, user, sample_skills):
        """Test character with skill proficiencies."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Skilled Rogue",
            species="Halfling",
            character_class="Rogue",
            background="Criminal",
            skills_json=sample_skills,
        )

        assert character.skills_json["athletics"]["proficient"] is True
        assert character.skills_json["perception"]["expertise"] is True

    def test_character_with_proficiencies(self, user, sample_proficiencies):
        """Test character with various proficiencies."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Proficient Fighter",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            proficiencies_json=sample_proficiencies,
        )

        assert "martial" in character.proficiencies_json["weapons"]
        assert "thieves_tools" in character.proficiencies_json["tools"]
        assert "str" in character.proficiencies_json["saving_throws"]

    def test_character_with_features(self, user, sample_features):
        """Test character with class features."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Feature Fighter",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            level=2,
            features_json=sample_features,
        )

        assert "second_wind" in character.features_json
        assert character.features_json["action_surge"]["uses_remaining"] == 0

    def test_character_with_spellbook(self, user, sample_spellbook):
        """Test character with spellcasting abilities."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Wizard Test",
            species="Elf",
            character_class="Wizard",
            background="Sage",
            level=5,
            spellbook_json=sample_spellbook,
        )

        assert character.spellbook_json["spellcasting_ability"] == "int"
        assert "fireball" in character.spellbook_json["known_spells"]
        assert character.spellbook_json["spell_slots"]["1"]["used"] == 2

    def test_character_with_equipment(self, user, sample_equipment):
        """Test character with equipment and inventory."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Equipped Fighter",
            species="Human",
            character_class="Fighter",
            background="Soldier",
            equipment_json=sample_equipment,
        )

        assert len(character.equipment_json["weapons"]) == 2
        assert character.equipment_json["armor"]["equipped"] is True
        assert character.equipment_json["money"]["gp"] == 50

    def test_character_with_subclass(self, user):
        """Test character with subclass selection."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Champion",
            species="Human",
            character_class="Fighter",
            subclass="Champion",
            background="Soldier",
            level=3,
        )

        assert character.subclass == "Champion"

    def test_character_with_homebrew_overrides(self, user):
        """Test character with homebrew content overrides."""
        homebrew = {
            "species_override": {
                "name": "Custom Elf",
                "ability_bonus": {"dex": 2, "int": 1},
            },
            "class_features_override": {
                "custom_feature": {
                    "name": "Custom Feature",
                    "description": "A custom homebrew feature",
                }
            },
        }

        character = CharacterSheet.objects.create(
            user=user,
            name="Homebrew Character",
            species="Custom Elf",
            character_class="Wizard",
            background="Sage",
            homebrew_overrides_json=homebrew,
        )

        assert "species_override" in character.homebrew_overrides_json
        assert character.homebrew_overrides_json["species_override"]["name"] == "Custom Elf"

    def test_character_str_representation(self, user):
        """Test character string representation."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Gandalf",
            species="Human",
            character_class="Wizard",
            background="Sage",
            level=20,
        )

        assert str(character) == "Gandalf (Level 20 Wizard)"

    def test_character_default_level(self, user):
        """Test character defaults to level 1."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Newbie",
            species="Human",
            character_class="Fighter",
            background="Folk Hero",
        )

        assert character.level == 1

    def test_character_json_fields_default_empty(self, user):
        """Test that JSON fields default to empty dicts."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Empty JSON",
            species="Human",
            character_class="Fighter",
            background="Soldier",
        )

        assert character.ability_scores_json == {}
        assert character.skills_json == {}
        assert character.proficiencies_json == {}
        assert character.features_json == {}
        assert character.spellbook_json == {}
        assert character.equipment_json == {}
        assert character.homebrew_overrides_json == {}

    def test_character_timestamps(self, user):
        """Test character has created_at and updated_at timestamps."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Timestamped",
            species="Human",
            character_class="Fighter",
            background="Soldier",
        )

        assert character.created_at is not None
        assert character.updated_at is not None

        original_updated = character.updated_at
        character.level = 2
        character.save()

        character.refresh_from_db()
        assert character.updated_at > original_updated

    def test_character_user_cascade_delete(self, user):
        """Test that deleting user cascades to characters."""
        character = CharacterSheet.objects.create(
            user=user,
            name="Doomed",
            species="Human",
            character_class="Fighter",
            background="Soldier",
        )
        character_id = character.id

        user.delete()

        assert not CharacterSheet.objects.filter(id=character_id).exists()

    def test_character_universe_set_null_on_delete(self, user, universe):
        """Test that deleting universe sets character.universe to NULL."""
        character = CharacterSheet.objects.create(
            user=user,
            universe=universe,
            name="Orphaned",
            species="Human",
            character_class="Fighter",
            background="Soldier",
        )
        character_id = character.id

        universe.delete()

        character.refresh_from_db()
        assert character.universe is None
        assert CharacterSheet.objects.filter(id=character_id).exists()

    def test_multiple_characters_per_user(self, user):
        """Test user can have multiple characters."""
        char1 = CharacterSheet.objects.create(
            user=user,
            name="Character 1",
            species="Human",
            character_class="Fighter",
            background="Soldier",
        )
        char2 = CharacterSheet.objects.create(
            user=user,
            name="Character 2",
            species="Elf",
            character_class="Wizard",
            background="Sage",
        )

        assert user.characters.count() == 2
        assert char1 in user.characters.all()
        assert char2 in user.characters.all()

    def test_full_character_creation(
        self,
        user,
        universe,
        sample_ability_scores,
        sample_skills,
        sample_proficiencies,
        sample_features,
        sample_spellbook,
        sample_equipment,
    ):
        """Test creating a fully-loaded character with all fields."""
        character = CharacterSheet.objects.create(
            user=user,
            universe=universe,
            name="Complete Character",
            species="Half-Elf",
            character_class="Eldritch Knight",
            subclass="Eldritch Knight",
            background="Noble",
            level=7,
            ability_scores_json=sample_ability_scores,
            skills_json=sample_skills,
            proficiencies_json=sample_proficiencies,
            features_json=sample_features,
            spellbook_json=sample_spellbook,
            equipment_json=sample_equipment,
            homebrew_overrides_json={"custom": "data"},
        )

        assert character.user == user
        assert character.universe == universe
        assert character.name == "Complete Character"
        assert character.species == "Half-Elf"
        assert character.character_class == "Eldritch Knight"
        assert character.subclass == "Eldritch Knight"
        assert character.background == "Noble"
        assert character.level == 7
        assert character.ability_scores_json == sample_ability_scores
        assert character.skills_json == sample_skills
        assert character.proficiencies_json == sample_proficiencies
        assert character.features_json == sample_features
        assert character.spellbook_json == sample_spellbook
        assert character.equipment_json == sample_equipment
        assert character.homebrew_overrides_json == {"custom": "data"}
