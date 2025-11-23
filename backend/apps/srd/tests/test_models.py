"""Tests for SRD models."""

import pytest
from django.db import IntegrityError

from apps.srd.models import (
    AbilityScore,
    Armor,
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
    Weapon,
)


@pytest.mark.django_db
class TestAbilityScore:
    """Tests for AbilityScore model."""

    def test_create_ability_score(self):
        """Test creating an ability score."""
        ability = AbilityScore.objects.create(
            abbreviation="STR",
            name="Strength",
            description="Physical power",
        )
        assert ability.abbreviation == "STR"
        assert ability.name == "Strength"
        assert str(ability) == "Strength (STR)"

    def test_abbreviation_unique(self):
        """Test that abbreviation must be unique."""
        AbilityScore.objects.create(abbreviation="DEX", name="Dexterity")
        with pytest.raises(IntegrityError):
            AbilityScore.objects.create(abbreviation="DEX", name="Dexterity2")

    def test_name_unique(self):
        """Test that name must be unique."""
        AbilityScore.objects.create(abbreviation="CON", name="Constitution")
        with pytest.raises(IntegrityError):
            AbilityScore.objects.create(abbreviation="CON2", name="Constitution")


@pytest.mark.django_db
class TestSkill:
    """Tests for Skill model."""

    def test_create_skill(self):
        """Test creating a skill."""
        dex = AbilityScore.objects.create(abbreviation="DEX", name="Dexterity")
        skill = Skill.objects.create(
            name="Acrobatics",
            ability_score=dex,
            description="Maintaining balance and performing acrobatic stunts.",
        )
        assert skill.name == "Acrobatics"
        assert skill.ability_score == dex
        assert str(skill) == "Acrobatics"

    def test_skill_ability_score_relationship(self):
        """Test the relationship between skill and ability score."""
        dex = AbilityScore.objects.create(abbreviation="DEX", name="Dexterity")
        Skill.objects.create(name="Acrobatics", ability_score=dex)
        Skill.objects.create(name="Stealth", ability_score=dex)

        assert dex.skills.count() == 2
        assert set(dex.skills.values_list("name", flat=True)) == {"Acrobatics", "Stealth"}


@pytest.mark.django_db
class TestCondition:
    """Tests for Condition model."""

    def test_create_condition(self):
        """Test creating a condition."""
        condition = Condition.objects.create(
            name="Blinded",
            description="Cannot see",
            effects=["auto_fail_sight_checks", "attacks_have_disadvantage"],
        )
        assert condition.name == "Blinded"
        assert len(condition.effects) == 2
        assert str(condition) == "Blinded"

    def test_condition_name_unique(self):
        """Test that condition name must be unique."""
        Condition.objects.create(name="Prone", description="Lying down")
        with pytest.raises(IntegrityError):
            Condition.objects.create(name="Prone", description="Also lying down")


@pytest.mark.django_db
class TestDamageType:
    """Tests for DamageType model."""

    def test_create_damage_type(self):
        """Test creating a damage type."""
        dt = DamageType.objects.create(
            name="Fire",
            description="Burns and flames",
        )
        assert dt.name == "Fire"
        assert str(dt) == "Fire"


@pytest.mark.django_db
class TestSpecies:
    """Tests for Species model."""

    def test_create_species(self):
        """Test creating a species."""
        species = Species.objects.create(
            name="Human",
            description="Versatile people",
            size="medium",
            speed=30,
            ability_bonuses={"str": 1, "dex": 1, "con": 1, "int": 1, "wis": 1, "cha": 1},
            traits=[{"name": "Versatile", "description": "Extra skill"}],
            languages=["Common", "One extra"],
            darkvision=0,
        )
        assert species.name == "Human"
        assert species.size == "medium"
        assert species.speed == 30
        assert species.ability_bonuses["str"] == 1
        assert len(species.traits) == 1
        assert str(species) == "Human"

    def test_species_darkvision(self):
        """Test species with darkvision."""
        elf = Species.objects.create(
            name="Elf",
            size="medium",
            speed=30,
            ability_bonuses={"dex": 2},
            darkvision=60,
        )
        assert elf.darkvision == 60


@pytest.mark.django_db
class TestCharacterClass:
    """Tests for CharacterClass model."""

    def test_create_class(self):
        """Test creating a character class."""
        str_ability = AbilityScore.objects.create(abbreviation="STR", name="Strength")
        fighter = CharacterClass.objects.create(
            name="Fighter",
            description="A master of martial combat",
            hit_die=10,
            primary_ability=str_ability,
            armor_proficiencies=["All armor", "Shields"],
            weapon_proficiencies=["Simple weapons", "Martial weapons"],
            skill_choices={"count": 2, "from": ["Athletics", "Intimidation"]},
            features=[
                {"level": 1, "name": "Fighting Style"},
                {"level": 2, "name": "Action Surge"},
            ],
        )
        assert fighter.name == "Fighter"
        assert fighter.hit_die == 10
        assert fighter.primary_ability == str_ability
        assert len(fighter.features) == 2
        assert str(fighter) == "Fighter"

    def test_spellcasting_class(self):
        """Test creating a spellcasting class."""
        cha = AbilityScore.objects.create(abbreviation="CHA", name="Charisma")
        sorcerer = CharacterClass.objects.create(
            name="Sorcerer",
            hit_die=6,
            primary_ability=cha,
            spellcasting_ability=cha,
        )
        assert sorcerer.spellcasting_ability == cha


@pytest.mark.django_db
class TestSubclass:
    """Tests for Subclass model."""

    def test_create_subclass(self):
        """Test creating a subclass."""
        fighter = CharacterClass.objects.create(name="Fighter", hit_die=10)
        champion = Subclass.objects.create(
            name="Champion",
            character_class=fighter,
            description="Focuses on physical prowess",
            subclass_level=3,
            features=[{"level": 3, "name": "Improved Critical"}],
        )
        assert champion.name == "Champion"
        assert champion.character_class == fighter
        assert champion.subclass_level == 3
        assert str(champion) == "Champion (Fighter)"

    def test_subclass_relationship(self):
        """Test the relationship between class and subclass."""
        fighter = CharacterClass.objects.create(name="Fighter", hit_die=10)
        Subclass.objects.create(name="Champion", character_class=fighter)
        Subclass.objects.create(name="Battle Master", character_class=fighter)

        assert fighter.subclasses.count() == 2


@pytest.mark.django_db
class TestBackground:
    """Tests for Background model."""

    def test_create_background(self):
        """Test creating a background."""
        background = Background.objects.create(
            name="Acolyte",
            description="Served in a temple",
            tool_proficiencies=[],
            languages=["Two of your choice"],
            equipment=["Holy symbol", "Prayer book"],
            feature_name="Shelter of the Faithful",
            feature_description="Can receive help from those who share your faith",
            suggested_characteristics={
                "personality_traits": ["I idolize a hero"],
                "ideals": ["Tradition"],
            },
        )
        assert background.name == "Acolyte"
        assert background.feature_name == "Shelter of the Faithful"
        assert str(background) == "Acolyte"


@pytest.mark.django_db
class TestSpellSchool:
    """Tests for SpellSchool model."""

    def test_create_spell_school(self):
        """Test creating a spell school."""
        school = SpellSchool.objects.create(
            name="Evocation",
            description="Manipulating energy",
        )
        assert school.name == "Evocation"
        assert str(school) == "Evocation"


@pytest.mark.django_db
class TestSpell:
    """Tests for Spell model."""

    def test_create_cantrip(self):
        """Test creating a cantrip (level 0 spell)."""
        evocation = SpellSchool.objects.create(name="Evocation")
        fire = DamageType.objects.create(name="Fire")
        firebolt = Spell.objects.create(
            name="Fire Bolt",
            level=0,
            school=evocation,
            casting_time="1 action",
            range="120 feet",
            components={"verbal": True, "somatic": True},
            duration="Instantaneous",
            description="Hurl a mote of fire",
            damage_type=fire,
            dice_expression="1d10",
        )
        assert firebolt.name == "Fire Bolt"
        assert firebolt.level == 0
        assert str(firebolt) == "Fire Bolt (Cantrip)"

    def test_create_leveled_spell(self):
        """Test creating a leveled spell."""
        evocation = SpellSchool.objects.create(name="Evocation")
        fire = DamageType.objects.create(name="Fire")
        fireball = Spell.objects.create(
            name="Fireball",
            level=3,
            school=evocation,
            casting_time="1 action",
            range="150 feet",
            components={"verbal": True, "somatic": True, "material": "bat guano"},
            duration="Instantaneous",
            description="An explosion of flame",
            damage_type=fire,
            dice_expression="8d6",
        )
        assert fireball.level == 3
        assert str(fireball) == "Fireball (Level 3)"

    def test_concentration_spell(self):
        """Test creating a concentration spell."""
        divination = SpellSchool.objects.create(name="Divination")
        detect = Spell.objects.create(
            name="Detect Magic",
            level=1,
            school=divination,
            casting_time="1 action",
            range="Self",
            components={"verbal": True, "somatic": True},
            duration="Concentration, up to 10 minutes",
            concentration=True,
            ritual=True,
            description="Sense the presence of magic",
        )
        assert detect.concentration is True
        assert detect.ritual is True


@pytest.mark.django_db
class TestItemAndWeapon:
    """Tests for Item and Weapon models."""

    def test_create_weapon(self):
        """Test creating a weapon with item."""
        weapon_cat = ItemCategory.objects.create(name="Weapon")
        piercing = DamageType.objects.create(name="Piercing")

        dagger_item = Item.objects.create(
            name="Dagger",
            category=weapon_cat,
            cost_gp=2.00,
            weight_lb=1.00,
            rarity="common",
        )
        dagger_stats = Weapon.objects.create(
            item=dagger_item,
            weapon_type="simple_melee",
            damage_dice="1d4",
            damage_type=piercing,
            properties=["finesse", "light", "thrown"],
            range_normal=20,
            range_long=60,
        )
        assert dagger_item.name == "Dagger"
        assert dagger_stats.damage_dice == "1d4"
        assert "finesse" in dagger_stats.properties
        assert str(dagger_stats) == "Dagger (1d4 Piercing)"

    def test_magical_item(self):
        """Test creating a magical item."""
        weapon_cat = ItemCategory.objects.create(name="Weapon")

        flame_tongue = Item.objects.create(
            name="Flame Tongue",
            category=weapon_cat,
            rarity="rare",
            magical=True,
            requires_attunement=True,
            description="A sword that can burst into flames",
        )
        assert flame_tongue.magical is True
        assert flame_tongue.requires_attunement is True
        assert flame_tongue.rarity == "rare"


@pytest.mark.django_db
class TestArmor:
    """Tests for Armor model."""

    def test_create_armor(self):
        """Test creating armor."""
        armor_cat = ItemCategory.objects.create(name="Armor")
        chain_mail_item = Item.objects.create(
            name="Chain Mail",
            category=armor_cat,
            cost_gp=75.00,
            weight_lb=55.00,
        )
        chain_mail = Armor.objects.create(
            item=chain_mail_item,
            armor_type="heavy",
            base_ac=16,
            dex_bonus="none",
            strength_requirement=13,
            stealth_disadvantage=True,
        )
        assert chain_mail.base_ac == 16
        assert chain_mail.strength_requirement == 13
        assert chain_mail.stealth_disadvantage is True
        assert str(chain_mail) == "Chain Mail (AC 16)"


@pytest.mark.django_db
class TestMonster:
    """Tests for Monster model."""

    def test_create_monster(self):
        """Test creating a monster."""
        dragon_type = MonsterType.objects.create(name="Dragon")
        fire = DamageType.objects.create(name="Fire")

        dragon = Monster.objects.create(
            name="Adult Red Dragon",
            monster_type=dragon_type,
            size="huge",
            alignment="Chaotic Evil",
            armor_class=19,
            armor_description="natural armor",
            hit_points=256,
            hit_dice="17d12+136",
            speed={"walk": 40, "climb": 40, "fly": 80},
            ability_scores={"str": 27, "dex": 10, "con": 25, "int": 16, "wis": 13, "cha": 21},
            saving_throws={"dex": 6, "con": 13, "wis": 7, "cha": 11},
            skills={"perception": 13, "stealth": 6},
            senses={"blindsight": 60, "darkvision": 120, "passive_perception": 23},
            languages=["Common", "Draconic"],
            challenge_rating=17.00,
            experience_points=18000,
            actions=[{"name": "Multiattack", "description": "The dragon makes three attacks"}],
        )
        dragon.damage_immunities.add(fire)

        assert dragon.name == "Adult Red Dragon"
        assert dragon.challenge_rating == 17.00
        assert dragon.speed["fly"] == 80
        assert fire in dragon.damage_immunities.all()
        assert str(dragon) == f"Adult Red Dragon (CR {dragon.challenge_rating})"


@pytest.mark.django_db
class TestFeat:
    """Tests for Feat model."""

    def test_create_feat(self):
        """Test creating a feat."""
        feat = Feat.objects.create(
            name="Alert",
            description="Always on the lookout for danger",
            prerequisites={},
            benefits=[
                "+5 to initiative",
                "Can't be surprised while conscious",
                "No advantage for hidden attackers",
            ],
        )
        assert feat.name == "Alert"
        assert len(feat.benefits) == 3
        assert str(feat) == "Alert"

    def test_feat_with_prerequisites(self):
        """Test creating a feat with prerequisites."""
        feat = Feat.objects.create(
            name="Heavy Armor Master",
            description="Reduce damage from nonmagical attacks",
            prerequisites={"strength": 13, "proficiency": "heavy armor"},
            benefits=["Reduce bludgeoning, piercing, slashing by 3"],
        )
        assert feat.prerequisites["strength"] == 13


@pytest.mark.django_db
class TestModelRelationships:
    """Tests for model relationships."""

    def test_spell_class_relationship(self):
        """Test the many-to-many relationship between spells and classes."""
        evocation = SpellSchool.objects.create(name="Evocation")
        wizard = CharacterClass.objects.create(name="Wizard", hit_die=6)
        sorcerer = CharacterClass.objects.create(name="Sorcerer", hit_die=6)

        fireball = Spell.objects.create(
            name="Fireball",
            level=3,
            school=evocation,
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
            description="Boom",
        )
        fireball.classes.add(wizard, sorcerer)

        assert wizard in fireball.classes.all()
        assert sorcerer in fireball.classes.all()
        assert fireball in wizard.spells.all()

    def test_background_skill_relationship(self):
        """Test the many-to-many relationship between backgrounds and skills."""
        wis = AbilityScore.objects.create(abbreviation="WIS", name="Wisdom")
        int_ability = AbilityScore.objects.create(abbreviation="INT", name="Intelligence")
        insight = Skill.objects.create(name="Insight", ability_score=wis)
        religion = Skill.objects.create(name="Religion", ability_score=int_ability)

        acolyte = Background.objects.create(
            name="Acolyte",
            description="Temple service",
            feature_name="Shelter",
            feature_description="Help from faithful",
        )
        acolyte.skill_proficiencies.add(insight, religion)

        assert insight in acolyte.skill_proficiencies.all()
        assert acolyte in insight.backgrounds.all()
