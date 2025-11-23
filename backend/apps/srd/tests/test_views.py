"""Tests for SRD catalog API endpoints."""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.srd.models import (
    AbilityScore,
    Background,
    CharacterClass,
    Condition,
    DamageType,
    Feat,
    Item,
    ItemCategory,
    Monster,
    MonsterType,
    Skill,
    Species,
    Spell,
    SpellSchool,
    Subclass,
)


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def ability_scores(db):
    """Create test ability scores."""
    scores = []
    for abbr, name in [
        ("STR", "Strength"),
        ("DEX", "Dexterity"),
        ("CON", "Constitution"),
        ("INT", "Intelligence"),
        ("WIS", "Wisdom"),
        ("CHA", "Charisma"),
    ]:
        scores.append(AbilityScore.objects.create(abbreviation=abbr, name=name))
    return scores


@pytest.fixture
def skills(db, ability_scores):
    """Create test skills."""
    dex = ability_scores[1]  # DEX
    return [
        Skill.objects.create(name="Acrobatics", ability_score=dex),
        Skill.objects.create(name="Stealth", ability_score=dex),
    ]


@pytest.fixture
def conditions(db):
    """Create test conditions."""
    return [
        Condition.objects.create(name="Blinded", description="Cannot see", effects=["blind"]),
        Condition.objects.create(name="Prone", description="Lying down", effects=["prone"]),
    ]


@pytest.fixture
def damage_types(db):
    """Create test damage types."""
    return [
        DamageType.objects.create(name="Fire", description="Fire damage"),
        DamageType.objects.create(name="Cold", description="Cold damage"),
    ]


@pytest.fixture
def species_list(db):
    """Create test species."""
    return [
        Species.objects.create(name="Human", size="medium", speed=30),
        Species.objects.create(name="Elf", size="medium", speed=30, darkvision=60),
        Species.objects.create(name="Halfling", size="small", speed=25),
    ]


@pytest.fixture
def character_classes(db, ability_scores):
    """Create test character classes."""
    str_ability = ability_scores[0]
    cha = ability_scores[5]
    fighter = CharacterClass.objects.create(
        name="Fighter", hit_die=10, primary_ability=str_ability
    )
    sorcerer = CharacterClass.objects.create(
        name="Sorcerer", hit_die=6, primary_ability=cha, spellcasting_ability=cha
    )
    return [fighter, sorcerer]


@pytest.fixture
def subclasses(db, character_classes):
    """Create test subclasses."""
    fighter = character_classes[0]
    return [
        Subclass.objects.create(name="Champion", character_class=fighter, subclass_level=3),
        Subclass.objects.create(name="Battle Master", character_class=fighter, subclass_level=3),
    ]


@pytest.fixture
def spell_schools(db):
    """Create test spell schools."""
    return [
        SpellSchool.objects.create(name="Evocation"),
        SpellSchool.objects.create(name="Abjuration"),
    ]


@pytest.fixture
def spells(db, spell_schools, character_classes, damage_types):
    """Create test spells."""
    evocation = spell_schools[0]
    fire = damage_types[0]
    sorcerer = character_classes[1]

    firebolt = Spell.objects.create(
        name="Fire Bolt",
        level=0,
        school=evocation,
        casting_time="1 action",
        range="120 feet",
        duration="Instantaneous",
        description="Hurl fire",
        damage_type=fire,
    )
    firebolt.classes.add(sorcerer)

    fireball = Spell.objects.create(
        name="Fireball",
        level=3,
        school=evocation,
        casting_time="1 action",
        range="150 feet",
        duration="Instantaneous",
        concentration=False,
        description="Big boom",
        damage_type=fire,
    )
    fireball.classes.add(sorcerer)

    return [firebolt, fireball]


@pytest.fixture
def item_categories(db):
    """Create test item categories."""
    return [
        ItemCategory.objects.create(name="Weapon"),
        ItemCategory.objects.create(name="Armor"),
    ]


@pytest.fixture
def items(db, item_categories):
    """Create test items."""
    weapon = item_categories[0]
    return [
        Item.objects.create(name="Dagger", category=weapon, cost_gp=2.00, rarity="common"),
        Item.objects.create(
            name="Flame Tongue", category=weapon, rarity="rare", magical=True
        ),
    ]


@pytest.fixture
def monster_types(db):
    """Create test monster types."""
    return [
        MonsterType.objects.create(name="Dragon"),
        MonsterType.objects.create(name="Undead"),
    ]


@pytest.fixture
def monsters(db, monster_types):
    """Create test monsters."""
    dragon = monster_types[0]
    undead = monster_types[1]
    return [
        Monster.objects.create(
            name="Adult Red Dragon",
            monster_type=dragon,
            size="huge",
            armor_class=19,
            hit_points=256,
            hit_dice="17d12+136",
            challenge_rating=17.00,
            experience_points=18000,
        ),
        Monster.objects.create(
            name="Zombie",
            monster_type=undead,
            size="medium",
            armor_class=8,
            hit_points=22,
            hit_dice="3d8+9",
            challenge_rating=0.25,
            experience_points=50,
        ),
    ]


@pytest.fixture
def backgrounds(db, skills):
    """Create test backgrounds."""
    bg = Background.objects.create(
        name="Acolyte",
        description="Temple service",
        feature_name="Shelter",
        feature_description="Help from faithful",
    )
    bg.skill_proficiencies.set(skills)
    return [bg]


@pytest.fixture
def feats(db):
    """Create test feats."""
    return [
        Feat.objects.create(
            name="Alert",
            description="Always alert",
            prerequisites={},
            benefits=["+5 initiative"],
        ),
    ]


@pytest.mark.django_db
class TestAbilityScoreAPI:
    """Tests for ability score endpoints."""

    def test_list_ability_scores(self, api_client, ability_scores):
        """Test listing all ability scores."""
        url = reverse("abilityscore-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 6

    def test_retrieve_ability_score(self, api_client, ability_scores):
        """Test retrieving a single ability score."""
        strength = ability_scores[0]
        url = reverse("abilityscore-detail", kwargs={"pk": strength.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Strength"
        assert response.data["abbreviation"] == "STR"


@pytest.mark.django_db
class TestSkillAPI:
    """Tests for skill endpoints."""

    def test_list_skills(self, api_client, skills):
        """Test listing all skills."""
        url = reverse("skill-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_filter_skills_by_ability(self, api_client, skills, ability_scores):
        """Test filtering skills by ability score."""
        dex = ability_scores[1]
        url = reverse("skill-list")
        response = api_client.get(url, {"ability_score": dex.pk})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2


@pytest.mark.django_db
class TestConditionAPI:
    """Tests for condition endpoints."""

    def test_list_conditions(self, api_client, conditions):
        """Test listing all conditions."""
        url = reverse("condition-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2


@pytest.mark.django_db
class TestSpeciesAPI:
    """Tests for species endpoints."""

    def test_list_species(self, api_client, species_list):
        """Test listing all species."""
        url = reverse("species-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_filter_species_by_size(self, api_client, species_list):
        """Test filtering species by size."""
        url = reverse("species-list")
        response = api_client.get(url, {"size": "small"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Halfling"

    def test_search_species(self, api_client, species_list):
        """Test searching species by name."""
        url = reverse("species-list")
        response = api_client.get(url, {"search": "elf"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


@pytest.mark.django_db
class TestCharacterClassAPI:
    """Tests for character class endpoints."""

    def test_list_classes(self, api_client, character_classes):
        """Test listing all classes."""
        url = reverse("characterclass-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_class_with_subclasses(self, api_client, character_classes, subclasses):
        """Test retrieving a class includes subclasses."""
        fighter = character_classes[0]
        url = reverse("characterclass-detail", kwargs={"pk": fighter.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Fighter"
        assert len(response.data["subclasses"]) == 2

    def test_class_subclasses_action(self, api_client, character_classes, subclasses):
        """Test getting subclasses via action endpoint."""
        fighter = character_classes[0]
        url = reverse("characterclass-subclasses", kwargs={"pk": fighter.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2


@pytest.mark.django_db
class TestSubclassAPI:
    """Tests for subclass endpoints."""

    def test_list_subclasses(self, api_client, subclasses):
        """Test listing all subclasses."""
        url = reverse("subclass-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_filter_subclasses_by_class(self, api_client, subclasses, character_classes):
        """Test filtering subclasses by character class."""
        fighter = character_classes[0]
        url = reverse("subclass-list")
        response = api_client.get(url, {"character_class": fighter.pk})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2


@pytest.mark.django_db
class TestSpellAPI:
    """Tests for spell endpoints."""

    def test_list_spells(self, api_client, spells):
        """Test listing all spells (uses summary serializer)."""
        url = reverse("spell-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        # Summary serializer should have limited fields
        assert "school_name" in response.data["results"][0]

    def test_retrieve_spell_full_details(self, api_client, spells):
        """Test retrieving a spell has full details."""
        fireball = spells[1]
        url = reverse("spell-detail", kwargs={"pk": fireball.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Fireball"
        assert "school" in response.data
        assert "damage_type" in response.data

    def test_filter_spells_by_level(self, api_client, spells):
        """Test filtering spells by level."""
        url = reverse("spell-list")
        response = api_client.get(url, {"level": 0})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Fire Bolt"


@pytest.mark.django_db
class TestItemAPI:
    """Tests for item endpoints."""

    def test_list_items(self, api_client, items):
        """Test listing all items (uses summary serializer)."""
        url = reverse("item-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_filter_items_by_rarity(self, api_client, items):
        """Test filtering items by rarity."""
        url = reverse("item-list")
        response = api_client.get(url, {"rarity": "rare"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Flame Tongue"

    def test_filter_items_magical(self, api_client, items):
        """Test filtering magical items."""
        url = reverse("item-list")
        response = api_client.get(url, {"magical": "true"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


@pytest.mark.django_db
class TestMonsterAPI:
    """Tests for monster endpoints."""

    def test_list_monsters(self, api_client, monsters):
        """Test listing all monsters (uses summary serializer)."""
        url = reverse("monster-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_monster_full_details(self, api_client, monsters):
        """Test retrieving a monster has full details."""
        dragon = monsters[0]
        url = reverse("monster-detail", kwargs={"pk": dragon.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Adult Red Dragon"
        assert "monster_type" in response.data
        assert "actions" in response.data

    def test_filter_monsters_by_cr(self, api_client, monsters):
        """Test filtering monsters by challenge rating."""
        url = reverse("monster-list")
        response = api_client.get(url, {"challenge_rating__lte": 1})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Zombie"


@pytest.mark.django_db
class TestBackgroundAPI:
    """Tests for background endpoints."""

    def test_list_backgrounds(self, api_client, backgrounds):
        """Test listing all backgrounds."""
        url = reverse("background-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_background_includes_skills(self, api_client, backgrounds):
        """Test background includes skill proficiencies."""
        url = reverse("background-detail", kwargs={"pk": backgrounds[0].pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["skill_proficiencies"]) == 2


@pytest.mark.django_db
class TestFeatAPI:
    """Tests for feat endpoints."""

    def test_list_feats(self, api_client, feats):
        """Test listing all feats."""
        url = reverse("feat-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_search_feats(self, api_client, feats):
        """Test searching feats by name."""
        url = reverse("feat-list")
        response = api_client.get(url, {"search": "alert"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


@pytest.mark.django_db
class TestAPIPublicAccess:
    """Tests to verify SRD API is publicly accessible."""

    def test_ability_scores_no_auth_required(self, api_client, ability_scores):
        """Test ability scores endpoint works without authentication."""
        url = reverse("abilityscore-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_spells_no_auth_required(self, api_client, spells):
        """Test spells endpoint works without authentication."""
        url = reverse("spell-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_monsters_no_auth_required(self, api_client, monsters):
        """Test monsters endpoint works without authentication."""
        url = reverse("monster-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
