"""
Unit tests for homebrew models.

Tests the universe-scoped homebrew content models:
- HomebrewSpecies
- HomebrewSpell
- HomebrewItem
- HomebrewMonster
- HomebrewFeat
- HomebrewBackground
- HomebrewClass
- HomebrewSubclass
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.srd.models import (
    Condition,
    DamageType,
    ItemCategory,
    MonsterType,
    SpellSchool,
)
from apps.universes.models import (
    HomebrewBackground,
    HomebrewClass,
    HomebrewFeat,
    HomebrewItem,
    HomebrewMonster,
    HomebrewSpecies,
    HomebrewSpell,
    HomebrewSubclass,
    Universe,
)

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        username="testuser",
    )


@pytest.fixture
def universe(user):
    """Create a test universe."""
    return Universe.objects.create(
        user=user,
        name="Test Universe",
        description="A universe for testing homebrew content",
    )


@pytest.fixture
def spell_school(db):
    """Create a test spell school."""
    return SpellSchool.objects.create(
        name="Evocation",
        description="Spells that manipulate energy",
    )


@pytest.fixture
def damage_type(db):
    """Create a test damage type."""
    return DamageType.objects.create(
        name="Fire",
        description="Fire damage",
    )


@pytest.fixture
def item_category(db):
    """Create a test item category."""
    return ItemCategory.objects.create(
        name="Weapon",
        description="Weapons for combat",
    )


@pytest.fixture
def monster_type(db):
    """Create a test monster type."""
    return MonsterType.objects.create(
        name="Dragon",
        description="Legendary creatures with immense power",
    )


@pytest.fixture
def condition(db):
    """Create a test condition."""
    return Condition.objects.create(
        name="Frightened",
        description="The creature is frightened",
        effects=["Disadvantage on ability checks and attack rolls"],
    )


# ==================== HomebrewSpecies Tests ====================


@pytest.mark.django_db
class TestHomebrewSpecies:
    """Tests for HomebrewSpecies model."""

    def test_create_homebrew_species(self, universe):
        """Test creating a basic homebrew species."""
        species = HomebrewSpecies.objects.create(
            universe=universe,
            name="Starborn",
            description="A species from the celestial planes",
            source_type="homebrew",
            power_tier="standard",
            size="medium",
            speed=30,
            ability_bonuses={"wis": 2, "cha": 1},
            traits=[{"name": "Celestial Legacy", "description": "You can cast light at will"}],
            languages=["Common", "Celestial"],
            darkvision=60,
        )
        assert species.name == "Starborn"
        assert species.universe == universe
        assert species.source_type == "homebrew"
        assert species.darkvision == 60
        assert str(species) == "Starborn (Test Universe)"

    def test_unique_species_per_universe(self, universe):
        """Test that species names must be unique within a universe."""
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Starborn",
            size="medium",
        )
        with pytest.raises(IntegrityError):
            HomebrewSpecies.objects.create(
                universe=universe,
                name="Starborn",
                size="small",
            )

    def test_same_name_different_universes(self, user, universe):
        """Test that same name can exist in different universes."""
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Starborn",
            size="medium",
        )
        universe2 = Universe.objects.create(
            user=user,
            name="Second Universe",
        )
        species2 = HomebrewSpecies.objects.create(
            universe=universe2,
            name="Starborn",
            size="small",
        )
        assert species2.name == "Starborn"

    def test_species_level_band(self, universe):
        """Test species with suggested level band."""
        species = HomebrewSpecies.objects.create(
            universe=universe,
            name="Epic Starborn",
            size="medium",
            power_tier="very_strong",
            suggested_level_min=10,
            suggested_level_max=20,
        )
        assert species.suggested_level_min == 10
        assert species.suggested_level_max == 20


# ==================== HomebrewSpell Tests ====================


@pytest.mark.django_db
class TestHomebrewSpell:
    """Tests for HomebrewSpell model."""

    def test_create_homebrew_spell(self, universe, spell_school, damage_type):
        """Test creating a homebrew spell."""
        spell = HomebrewSpell.objects.create(
            universe=universe,
            name="Celestial Burst",
            description="A burst of celestial energy",
            source_type="homebrew",
            power_tier="strong",
            level=3,
            school=spell_school,
            casting_time="1 action",
            range="60 feet",
            components={"verbal": True, "somatic": True, "material": "a holy symbol"},
            duration="Instantaneous",
            concentration=False,
            ritual=False,
            damage_type=damage_type,
            dice_expression="6d8",
            suggested_level_min=5,
            suggested_level_max=10,
        )
        assert spell.name == "Celestial Burst"
        assert spell.level == 3
        assert spell.school == spell_school
        assert spell.dice_expression == "6d8"
        assert "Level 3" in str(spell)

    def test_create_cantrip(self, universe, spell_school):
        """Test creating a cantrip (level 0 spell)."""
        spell = HomebrewSpell.objects.create(
            universe=universe,
            name="Minor Blessing",
            level=0,
            school=spell_school,
            casting_time="1 action",
            range="Touch",
            duration="1 minute",
        )
        assert spell.level == 0
        assert "Cantrip" in str(spell)

    def test_unique_spell_per_universe(self, universe, spell_school):
        """Test spell name uniqueness within universe."""
        HomebrewSpell.objects.create(
            universe=universe,
            name="Unique Spell",
            level=1,
            school=spell_school,
            casting_time="1 action",
            range="Self",
            duration="1 hour",
        )
        with pytest.raises(IntegrityError):
            HomebrewSpell.objects.create(
                universe=universe,
                name="Unique Spell",
                level=2,
                school=spell_school,
                casting_time="1 action",
                range="Self",
                duration="1 hour",
            )

    def test_spell_class_restrictions(self, universe, spell_school):
        """Test spell with class restrictions."""
        spell = HomebrewSpell.objects.create(
            universe=universe,
            name="Wizard Only Spell",
            level=1,
            school=spell_school,
            casting_time="1 action",
            range="Self",
            duration="1 hour",
            class_restrictions=["Wizard", "Sorcerer"],
        )
        assert "Wizard" in spell.class_restrictions
        assert len(spell.class_restrictions) == 2


# ==================== HomebrewItem Tests ====================


@pytest.mark.django_db
class TestHomebrewItem:
    """Tests for HomebrewItem model."""

    def test_create_basic_item(self, universe, item_category):
        """Test creating a basic homebrew item."""
        item = HomebrewItem.objects.create(
            universe=universe,
            name="Star Compass",
            description="A compass that points to celestial bodies",
            source_type="homebrew",
            category=item_category,
            cost_gp=Decimal("50.00"),
            weight_lb=Decimal("0.5"),
            rarity="uncommon",
            magical=True,
        )
        assert item.name == "Star Compass"
        assert item.cost_gp == Decimal("50.00")
        assert item.magical is True

    def test_create_weapon_item(self, universe, item_category, damage_type):
        """Test creating a homebrew weapon."""
        weapon = HomebrewItem.objects.create(
            universe=universe,
            name="Celestial Blade",
            category=item_category,
            rarity="rare",
            magical=True,
            is_weapon=True,
            weapon_type="martial_melee",
            damage_dice="1d10",
            damage_type=damage_type,
            weapon_properties=["versatile", "finesse"],
        )
        assert weapon.is_weapon is True
        assert weapon.damage_dice == "1d10"
        assert "versatile" in weapon.weapon_properties

    def test_create_armor_item(self, universe, item_category):
        """Test creating homebrew armor."""
        armor = HomebrewItem.objects.create(
            universe=universe,
            name="Starweave Armor",
            category=item_category,
            rarity="rare",
            magical=True,
            is_armor=True,
            armor_type="light",
            base_ac=13,
            dex_bonus="full",
            stealth_disadvantage=False,
        )
        assert armor.is_armor is True
        assert armor.base_ac == 13
        assert armor.armor_type == "light"

    def test_item_requires_attunement(self, universe, item_category):
        """Test item with attunement requirements."""
        item = HomebrewItem.objects.create(
            universe=universe,
            name="Attuned Item",
            category=item_category,
            requires_attunement=True,
            attunement_requirements="requires attunement by a spellcaster",
            rarity="very_rare",
            magical=True,
        )
        assert item.requires_attunement is True
        assert "spellcaster" in item.attunement_requirements


# ==================== HomebrewMonster Tests ====================


@pytest.mark.django_db
class TestHomebrewMonster:
    """Tests for HomebrewMonster model."""

    def test_create_homebrew_monster(self, universe, monster_type, damage_type, condition):
        """Test creating a homebrew monster."""
        monster = HomebrewMonster.objects.create(
            universe=universe,
            name="Star Drake",
            description="A dragon infused with celestial energy",
            source_type="homebrew",
            power_tier="legendary",
            monster_type=monster_type,
            size="huge",
            alignment="lawful good",
            armor_class=18,
            armor_description="natural armor",
            hit_points=200,
            hit_dice="17d12+85",
            speed={"walk": 40, "fly": 80},
            ability_scores={"str": 22, "dex": 14, "con": 20, "int": 16, "wis": 18, "cha": 20},
            challenge_rating=Decimal("12.00"),
            experience_points=8400,
            traits=[{"name": "Legendary Resistance", "description": "3/day"}],
            actions=[{"name": "Multiattack", "description": "Three attacks"}],
            suggested_level_min=10,
            suggested_level_max=15,
        )
        monster.damage_resistances.add(damage_type)
        monster.condition_immunities.add(condition)

        assert monster.name == "Star Drake"
        assert monster.challenge_rating == Decimal("12.00")
        assert monster.hit_points == 200
        assert damage_type in monster.damage_resistances.all()
        assert condition in monster.condition_immunities.all()
        assert "CR 12" in str(monster)

    def test_monster_with_legendary_actions(self, universe, monster_type):
        """Test monster with legendary actions."""
        monster = HomebrewMonster.objects.create(
            universe=universe,
            name="Ancient Star Drake",
            monster_type=monster_type,
            size="gargantuan",
            armor_class=22,
            hit_points=400,
            hit_dice="28d20+140",
            speed={"walk": 40, "fly": 100},
            ability_scores={"str": 28, "dex": 12, "con": 24, "int": 18, "wis": 20, "cha": 24},
            challenge_rating=Decimal("20.00"),
            experience_points=25000,
            legendary_actions=[
                {"name": "Detect", "description": "Wisdom check"},
                {"name": "Tail Attack", "description": "Makes a tail attack"},
                {"name": "Wing Attack (2 actions)", "description": "Beats wings"},
            ],
            lair_actions=[{"name": "Blinding Light", "description": "The lair fills with light"}],
        )
        assert len(monster.legendary_actions) == 3
        assert len(monster.lair_actions) == 1


# ==================== HomebrewFeat Tests ====================


@pytest.mark.django_db
class TestHomebrewFeat:
    """Tests for HomebrewFeat model."""

    def test_create_homebrew_feat(self, universe):
        """Test creating a homebrew feat."""
        feat = HomebrewFeat.objects.create(
            universe=universe,
            name="Celestial Blessing",
            description="You have been blessed by celestial forces",
            source_type="homebrew",
            power_tier="standard",
            prerequisites={"level": 4},
            benefits=[
                "You gain darkvision 60 feet",
                "You learn the light cantrip",
                "You have resistance to radiant damage",
            ],
            ability_score_increase={"choice": ["wis", "cha"], "amount": 1},
        )
        assert feat.name == "Celestial Blessing"
        assert len(feat.benefits) == 3
        assert feat.ability_score_increase["amount"] == 1

    def test_feat_with_ability_prerequisites(self, universe):
        """Test feat with ability score prerequisites."""
        feat = HomebrewFeat.objects.create(
            universe=universe,
            name="Heavy Armor Master",
            prerequisites={"ability": {"str": 15}},
            benefits=["Reduce non-magical damage by 3"],
        )
        assert feat.prerequisites["ability"]["str"] == 15


# ==================== HomebrewBackground Tests ====================


@pytest.mark.django_db
class TestHomebrewBackground:
    """Tests for HomebrewBackground model."""

    def test_create_homebrew_background(self, universe):
        """Test creating a homebrew background."""
        background = HomebrewBackground.objects.create(
            universe=universe,
            name="Star Navigator",
            description="You learned to navigate by the stars",
            source_type="homebrew",
            skill_proficiencies=["Perception", "Survival"],
            tool_proficiencies=["Navigator's tools"],
            languages=["Celestial"],
            equipment=["Navigator's tools", "Star chart", "Traveler's clothes", "10 gp"],
            feature_name="Star Reader",
            feature_description="You can always determine north and predict weather",
            suggested_characteristics={
                "personality_traits": ["I always look up at the stars", "I speak in metaphors"],
                "ideals": ["Knowledge. The stars hold ancient wisdom."],
                "bonds": ["My mentor taught me to read the stars."],
                "flaws": ["I get lost indoors."],
            },
        )
        assert background.name == "Star Navigator"
        assert len(background.skill_proficiencies) == 2
        assert background.feature_name == "Star Reader"


# ==================== HomebrewClass Tests ====================


@pytest.mark.django_db
class TestHomebrewClass:
    """Tests for HomebrewClass model."""

    def test_create_homebrew_class(self, universe):
        """Test creating a homebrew class."""
        char_class = HomebrewClass.objects.create(
            universe=universe,
            name="Star Knight",
            description="Warriors blessed by celestial forces",
            source_type="homebrew",
            power_tier="standard",
            hit_die=10,
            primary_ability=["str", "cha"],
            saving_throw_proficiencies=["str", "cha"],
            armor_proficiencies=["light", "medium", "heavy", "shields"],
            weapon_proficiencies=["simple", "martial"],
            skill_choices={"count": 2, "from": ["Athletics", "Insight", "Persuasion", "Religion"]},
            starting_equipment=[
                {"choice": [{"item": "longsword"}, {"item": "any martial weapon"}]},
                {"item": "chain mail"},
            ],
            spellcasting_ability="cha",
            features=[
                {"level": 1, "name": "Divine Sense", "description": "Detect celestial, fiend, undead"},
                {"level": 2, "name": "Celestial Smite", "description": "Add radiant damage"},
            ],
            subclass_level=3,
            spell_slots={"1": {"1": 0, "2": 2}, "2": {"1": 0, "2": 2}},
        )
        assert char_class.name == "Star Knight"
        assert char_class.hit_die == 10
        assert char_class.spellcasting_ability == "cha"
        assert char_class.subclass_level == 3


# ==================== HomebrewSubclass Tests ====================


@pytest.mark.django_db
class TestHomebrewSubclass:
    """Tests for HomebrewSubclass model."""

    def test_create_subclass_for_homebrew_class(self, universe):
        """Test creating a subclass for a homebrew class."""
        parent_class = HomebrewClass.objects.create(
            universe=universe,
            name="Star Knight",
            hit_die=10,
            primary_ability=["str"],
            saving_throw_proficiencies=["str", "cha"],
        )
        subclass = HomebrewSubclass.objects.create(
            universe=universe,
            name="Order of the Radiant Star",
            description="Knights dedicated to pure light",
            parent_class=parent_class,
            subclass_level=3,
            features=[
                {"level": 3, "name": "Radiant Aura", "description": "Emanate light"},
                {"level": 7, "name": "Blinding Strike", "description": "Blind enemies"},
            ],
        )
        assert subclass.parent_class == parent_class
        assert len(subclass.features) == 2
        assert "Star Knight" in str(subclass)

    def test_create_subclass_for_srd_class(self, universe):
        """Test creating a subclass for an SRD class."""
        subclass = HomebrewSubclass.objects.create(
            universe=universe,
            name="Circle of Stars",
            description="Druids who draw power from the stars",
            srd_parent_class_name="Druid",
            subclass_level=2,
            features=[
                {"level": 2, "name": "Star Map", "description": "Create a star map"},
                {"level": 6, "name": "Cosmic Omen", "description": "Read omens"},
            ],
        )
        assert subclass.srd_parent_class_name == "Druid"
        assert subclass.parent_class is None
        assert "Druid" in str(subclass)


# ==================== Lock Functionality Tests ====================


@pytest.mark.django_db
class TestHomebrewLocking:
    """Tests for homebrew content locking functionality."""

    def test_homebrew_locked_by_default_false(self, universe):
        """Test that homebrew content is not locked by default."""
        species = HomebrewSpecies.objects.create(
            universe=universe,
            name="Test Species",
            size="medium",
        )
        assert species.is_locked is False

    def test_lock_homebrew_content(self, universe):
        """Test locking homebrew content."""
        species = HomebrewSpecies.objects.create(
            universe=universe,
            name="Test Species",
            size="medium",
        )
        species.is_locked = True
        species.save()
        species.refresh_from_db()
        assert species.is_locked is True


# ==================== Cascade Delete Tests ====================


@pytest.mark.django_db
class TestCascadeDelete:
    """Tests for cascade delete behavior."""

    def test_delete_universe_deletes_homebrew(self, user, spell_school):
        """Test that deleting a universe deletes all homebrew content."""
        universe = Universe.objects.create(user=user, name="Temp Universe")
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Test Species",
            size="medium",
        )
        HomebrewSpell.objects.create(
            universe=universe,
            name="Test Spell",
            level=1,
            school=spell_school,
            casting_time="1 action",
            range="Self",
            duration="1 hour",
        )

        species_count = HomebrewSpecies.objects.filter(universe=universe).count()
        spell_count = HomebrewSpell.objects.filter(universe=universe).count()
        assert species_count == 1
        assert spell_count == 1

        universe.delete()

        species_count = HomebrewSpecies.objects.filter(universe=universe).count()
        spell_count = HomebrewSpell.objects.filter(universe=universe).count()
        assert species_count == 0
        assert spell_count == 0
