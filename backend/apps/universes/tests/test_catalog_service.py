"""
Unit tests for the CatalogService.

Tests the catalog merge logic that combines SRD baseline with universe homebrew:
- Merging SRD and homebrew content
- Homebrew precedence over SRD
- Filtering across both sources
- Catalog statistics
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.srd.models import (
    CharacterClass,
    DamageType,
    Feat,
    Item,
    ItemCategory,
    Monster,
    MonsterType,
    Species,
    Spell,
    SpellSchool,
    Subclass,
)
from apps.universes.models import (
    HomebrewClass,
    HomebrewFeat,
    HomebrewItem,
    HomebrewMonster,
    HomebrewSpecies,
    HomebrewSpell,
    HomebrewSubclass,
    Universe,
)
from apps.universes.services import CatalogService

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
        description="A universe for testing",
    )


@pytest.fixture
def spell_school(db):
    """Create a test spell school."""
    return SpellSchool.objects.create(name="Evocation")


@pytest.fixture
def damage_type(db):
    """Create a test damage type."""
    return DamageType.objects.create(name="Fire")


@pytest.fixture
def item_category(db):
    """Create a test item category."""
    return ItemCategory.objects.create(name="Weapon")


@pytest.fixture
def monster_type(db):
    """Create a test monster type."""
    return MonsterType.objects.create(name="Dragon")


@pytest.fixture
def catalog(universe):
    """Create a catalog service for the test universe."""
    return CatalogService(universe)


# ==================== Species Tests ====================


@pytest.mark.django_db
class TestCatalogSpecies:
    """Tests for species catalog merging."""

    def test_get_species_empty(self, catalog):
        """Test getting species when none exist."""
        species = catalog.get_species()
        assert species == []

    def test_get_srd_species(self, catalog):
        """Test getting SRD species."""
        Species.objects.create(name="Human", size="medium", speed=30)
        Species.objects.create(name="Elf", size="medium", speed=30)

        species = catalog.get_species()
        assert len(species) == 2
        assert all(s.source == "srd" for s in species)

    def test_get_homebrew_species(self, catalog, universe):
        """Test getting homebrew species."""
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Starborn",
            size="medium",
        )

        species = catalog.get_species()
        assert len(species) == 1
        assert species[0].source == "homebrew"
        assert species[0].name == "Starborn"

    def test_merge_srd_and_homebrew_species(self, catalog, universe):
        """Test merging SRD and homebrew species."""
        Species.objects.create(name="Human", size="medium", speed=30)
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Starborn",
            size="medium",
        )

        species = catalog.get_species()
        assert len(species) == 2
        # Should be sorted by name
        assert species[0].name == "Human"
        assert species[1].name == "Starborn"

    def test_filter_species_by_size(self, catalog, universe):
        """Test filtering species by size."""
        Species.objects.create(name="Human", size="medium", speed=30)
        Species.objects.create(name="Halfling", size="small", speed=25)
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Starborn",
            size="medium",
        )

        species = catalog.get_species(size="small")
        assert len(species) == 1
        assert species[0].name == "Halfling"

    def test_homebrew_precedence(self, catalog, universe):
        """Test that homebrew takes precedence for same name."""
        Species.objects.create(name="Human", size="medium", speed=30)
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Human",  # Same name as SRD
            size="medium",
            source_type="srd_derived",
            speed=35,  # Modified
        )

        result = catalog.get_species_by_name("Human")
        assert result is not None
        assert result.source == "homebrew"
        assert result.data.speed == 35

    def test_exclude_srd_species(self, catalog, universe):
        """Test excluding SRD species."""
        Species.objects.create(name="Human", size="medium", speed=30)
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Starborn",
            size="medium",
        )

        species = catalog.get_species(include_srd=False)
        assert len(species) == 1
        assert species[0].source == "homebrew"


# ==================== Spells Tests ====================


@pytest.mark.django_db
class TestCatalogSpells:
    """Tests for spell catalog merging."""

    def test_get_spells_with_level_filter(self, catalog, universe, spell_school):
        """Test filtering spells by level."""
        Spell.objects.create(
            name="Fireball",
            level=3,
            school=spell_school,
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
            description="A ball of fire",
        )
        Spell.objects.create(
            name="Fire Bolt",
            level=0,
            school=spell_school,
            casting_time="1 action",
            range="120 feet",
            duration="Instantaneous",
            description="A bolt of fire",
        )
        HomebrewSpell.objects.create(
            universe=universe,
            name="Celestial Burst",
            level=3,
            school=spell_school,
            casting_time="1 action",
            range="60 feet",
            duration="Instantaneous",
        )

        cantrips = catalog.get_spells(level=0)
        assert len(cantrips) == 1
        assert cantrips[0].name == "Fire Bolt"

        level_3_spells = catalog.get_spells(level=3)
        assert len(level_3_spells) == 2

    def test_get_spells_sorted_by_level(self, catalog, universe, spell_school):
        """Test that spells are sorted by level then name."""
        Spell.objects.create(
            name="Fireball",
            level=3,
            school=spell_school,
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
            description="Fire",
        )
        Spell.objects.create(
            name="Fire Bolt",
            level=0,
            school=spell_school,
            casting_time="1 action",
            range="120 feet",
            duration="Instantaneous",
            description="Fire",
        )
        HomebrewSpell.objects.create(
            universe=universe,
            name="Arcane Bolt",
            level=0,
            school=spell_school,
            casting_time="1 action",
            range="60 feet",
            duration="Instantaneous",
        )

        spells = catalog.get_spells()
        assert len(spells) == 3
        # Level 0 first, sorted by name
        assert spells[0].name == "Arcane Bolt"
        assert spells[1].name == "Fire Bolt"
        # Then level 3
        assert spells[2].name == "Fireball"

    def test_filter_spells_by_school(self, catalog, spell_school):
        """Test filtering spells by school."""
        other_school = SpellSchool.objects.create(name="Necromancy")
        Spell.objects.create(
            name="Fireball",
            level=3,
            school=spell_school,
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
            description="Fire",
        )
        Spell.objects.create(
            name="Animate Dead",
            level=3,
            school=other_school,
            casting_time="1 minute",
            range="10 feet",
            duration="Instantaneous",
            description="Undead",
        )

        evocation_spells = catalog.get_spells(school_name="Evocation")
        assert len(evocation_spells) == 1
        assert evocation_spells[0].name == "Fireball"


# ==================== Items Tests ====================


@pytest.mark.django_db
class TestCatalogItems:
    """Tests for item catalog merging."""

    def test_filter_items_by_rarity(self, catalog, universe, item_category):
        """Test filtering items by rarity."""
        Item.objects.create(
            name="Longsword",
            category=item_category,
            rarity="common",
        )
        Item.objects.create(
            name="Flametongue",
            category=item_category,
            rarity="rare",
            magical=True,
        )
        HomebrewItem.objects.create(
            universe=universe,
            name="Star Blade",
            category=item_category,
            rarity="legendary",
            magical=True,
        )

        rare_items = catalog.get_items(rarity="rare")
        assert len(rare_items) == 1
        assert rare_items[0].name == "Flametongue"

    def test_filter_items_by_magical(self, catalog, universe, item_category):
        """Test filtering items by magical status."""
        Item.objects.create(
            name="Longsword",
            category=item_category,
            magical=False,
        )
        Item.objects.create(
            name="Flametongue",
            category=item_category,
            magical=True,
        )
        HomebrewItem.objects.create(
            universe=universe,
            name="Star Blade",
            category=item_category,
            magical=True,
        )

        magical_items = catalog.get_items(magical=True)
        assert len(magical_items) == 2


# ==================== Monsters Tests ====================


@pytest.mark.django_db
class TestCatalogMonsters:
    """Tests for monster catalog merging."""

    def test_filter_monsters_by_cr_range(self, catalog, universe, monster_type):
        """Test filtering monsters by challenge rating range."""
        Monster.objects.create(
            name="Young Dragon",
            monster_type=monster_type,
            size="large",
            armor_class=18,
            hit_points=178,
            hit_dice="17d10",
            challenge_rating=Decimal("10.00"),
            experience_points=5900,
        )
        Monster.objects.create(
            name="Adult Dragon",
            monster_type=monster_type,
            size="huge",
            armor_class=19,
            hit_points=256,
            hit_dice="19d12",
            challenge_rating=Decimal("17.00"),
            experience_points=18000,
        )
        HomebrewMonster.objects.create(
            universe=universe,
            name="Baby Dragon",
            monster_type=monster_type,
            size="small",
            armor_class=14,
            hit_points=45,
            hit_dice="6d6",
            challenge_rating=Decimal("2.00"),
            experience_points=450,
        )

        low_cr_monsters = catalog.get_monsters(challenge_rating_max=Decimal("5.00"))
        assert len(low_cr_monsters) == 1
        assert low_cr_monsters[0].name == "Baby Dragon"

        mid_cr_monsters = catalog.get_monsters(
            challenge_rating_min=Decimal("5.00"),
            challenge_rating_max=Decimal("15.00"),
        )
        assert len(mid_cr_monsters) == 1
        assert mid_cr_monsters[0].name == "Young Dragon"

    def test_monsters_sorted_by_cr(self, catalog, universe, monster_type):
        """Test that monsters are sorted by CR then name."""
        Monster.objects.create(
            name="Adult Dragon",
            monster_type=monster_type,
            size="huge",
            armor_class=19,
            hit_points=256,
            hit_dice="19d12",
            challenge_rating=Decimal("17.00"),
            experience_points=18000,
        )
        Monster.objects.create(
            name="Young Dragon",
            monster_type=monster_type,
            size="large",
            armor_class=18,
            hit_points=178,
            hit_dice="17d10",
            challenge_rating=Decimal("10.00"),
            experience_points=5900,
        )
        HomebrewMonster.objects.create(
            universe=universe,
            name="Ancient Dragon",
            monster_type=monster_type,
            size="gargantuan",
            armor_class=22,
            hit_points=500,
            hit_dice="25d20",
            challenge_rating=Decimal("24.00"),
            experience_points=62000,
        )

        monsters = catalog.get_monsters()
        assert len(monsters) == 3
        assert monsters[0].name == "Young Dragon"  # CR 10
        assert monsters[1].name == "Adult Dragon"  # CR 17
        assert monsters[2].name == "Ancient Dragon"  # CR 24


# ==================== Feats Tests ====================


@pytest.mark.django_db
class TestCatalogFeats:
    """Tests for feat catalog merging."""

    def test_merge_feats(self, catalog, universe):
        """Test merging SRD and homebrew feats."""
        Feat.objects.create(
            name="Alert",
            description="You gain a +5 bonus to initiative.",
        )
        HomebrewFeat.objects.create(
            universe=universe,
            name="Celestial Blessing",
            description="You gain divine powers.",
        )

        feats = catalog.get_feats()
        assert len(feats) == 2

    def test_feat_by_name_homebrew_precedence(self, catalog, universe):
        """Test homebrew precedence for feats."""
        Feat.objects.create(
            name="Alert",
            description="SRD version",
        )
        HomebrewFeat.objects.create(
            universe=universe,
            name="Alert",
            description="Homebrew version with changes",
            source_type="srd_derived",
        )

        result = catalog.get_feat_by_name("Alert")
        assert result.source == "homebrew"
        assert "Homebrew" in result.data.description


# ==================== Classes Tests ====================


@pytest.mark.django_db
class TestCatalogClasses:
    """Tests for class catalog merging."""

    def test_merge_classes(self, catalog, universe):
        """Test merging SRD and homebrew classes."""
        CharacterClass.objects.create(
            name="Fighter",
            hit_die=10,
        )
        HomebrewClass.objects.create(
            universe=universe,
            name="Star Knight",
            hit_die=10,
            primary_ability=["str"],
            saving_throw_proficiencies=["str", "con"],
        )

        classes = catalog.get_classes()
        assert len(classes) == 2


# ==================== Subclasses Tests ====================


@pytest.mark.django_db
class TestCatalogSubclasses:
    """Tests for subclass catalog merging."""

    def test_get_subclasses_by_parent_class(self, catalog, universe):
        """Test filtering subclasses by parent class name."""
        fighter = CharacterClass.objects.create(name="Fighter", hit_die=10)
        wizard = CharacterClass.objects.create(name="Wizard", hit_die=6)

        Subclass.objects.create(
            name="Champion",
            character_class=fighter,
        )
        Subclass.objects.create(
            name="Evocation School",
            character_class=wizard,
        )
        HomebrewSubclass.objects.create(
            universe=universe,
            name="Star Knight Order",
            srd_parent_class_name="Fighter",
        )

        fighter_subclasses = catalog.get_subclasses(parent_class_name="Fighter")
        assert len(fighter_subclasses) == 2

        wizard_subclasses = catalog.get_subclasses(parent_class_name="Wizard")
        assert len(wizard_subclasses) == 1


# ==================== Catalog Stats Tests ====================


@pytest.mark.django_db
class TestCatalogStats:
    """Tests for catalog statistics."""

    def test_get_catalog_stats(self, catalog, universe, spell_school, monster_type, item_category):
        """Test getting catalog statistics."""
        # Create some SRD content
        Species.objects.create(name="Human", size="medium", speed=30)
        Species.objects.create(name="Elf", size="medium", speed=30)
        Spell.objects.create(
            name="Fireball",
            level=3,
            school=spell_school,
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
            description="Fire",
        )
        Monster.objects.create(
            name="Dragon",
            monster_type=monster_type,
            size="huge",
            armor_class=19,
            hit_points=256,
            hit_dice="19d12",
            challenge_rating=Decimal("17.00"),
            experience_points=18000,
        )

        # Create homebrew content
        HomebrewSpecies.objects.create(
            universe=universe,
            name="Starborn",
            size="medium",
        )
        HomebrewMonster.objects.create(
            universe=universe,
            name="Star Drake",
            monster_type=monster_type,
            size="huge",
            armor_class=18,
            hit_points=200,
            hit_dice="17d12",
            challenge_rating=Decimal("12.00"),
            experience_points=8400,
        )
        HomebrewMonster.objects.create(
            universe=universe,
            name="Void Wyrm",
            monster_type=monster_type,
            size="gargantuan",
            armor_class=22,
            hit_points=400,
            hit_dice="25d20",
            challenge_rating=Decimal("20.00"),
            experience_points=25000,
        )

        stats = catalog.get_catalog_stats()

        assert stats["species"]["srd"] == 2
        assert stats["species"]["homebrew"] == 1
        assert stats["spells"]["srd"] == 1
        assert stats["spells"]["homebrew"] == 0
        assert stats["monsters"]["srd"] == 1
        assert stats["monsters"]["homebrew"] == 2


# ==================== CatalogEntry Tests ====================


@pytest.mark.django_db
class TestCatalogEntry:
    """Tests for CatalogEntry dataclass."""

    def test_srd_catalog_entry(self, catalog):
        """Test CatalogEntry for SRD content."""
        srd_species = Species.objects.create(name="Human", size="medium", speed=30)

        entry = catalog.get_species_by_name("Human")
        assert entry is not None
        assert entry.source == "srd"
        assert entry.source_type == "srd"
        assert entry.power_tier is None
        assert entry.level_band is None
        assert entry.data == srd_species

    def test_homebrew_catalog_entry(self, catalog, universe):
        """Test CatalogEntry for homebrew content."""
        homebrew = HomebrewSpecies.objects.create(
            universe=universe,
            name="Starborn",
            size="medium",
            source_type="homebrew",
            power_tier="strong",
            suggested_level_min=5,
            suggested_level_max=15,
        )

        entry = catalog.get_species_by_name("Starborn")
        assert entry is not None
        assert entry.source == "homebrew"
        assert entry.source_type == "homebrew"
        assert entry.power_tier == "strong"
        assert entry.level_band == (5, 15)
        assert entry.data == homebrew
