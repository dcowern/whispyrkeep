"""SRD 5.2 reference table models.

This module contains Django models for storing SRD 5.2 baseline data.
All SRD data is licensed under Creative Commons Attribution 4.0.
"""

from django.db import models


class AbilityScore(models.Model):
    """Core ability scores (STR, DEX, CON, INT, WIS, CHA)."""

    abbreviation = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Ability Score"
        verbose_name_plural = "Ability Scores"

    def __str__(self) -> str:
        return f"{self.name} ({self.abbreviation})"


class Skill(models.Model):
    """Skills linked to ability scores."""

    name = models.CharField(max_length=50, unique=True)
    ability_score = models.ForeignKey(
        AbilityScore,
        on_delete=models.PROTECT,
        related_name="skills",
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Condition(models.Model):
    """Status conditions (Blinded, Charmed, etc.)."""

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    effects = models.JSONField(
        default=list,
        help_text="List of mechanical effects this condition applies",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class DamageType(models.Model):
    """Damage types (Slashing, Fire, etc.)."""

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Damage Type"
        verbose_name_plural = "Damage Types"

    def __str__(self) -> str:
        return self.name


class Species(models.Model):
    """Playable species/races from SRD 5.2."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    size = models.CharField(
        max_length=20,
        choices=[
            ("tiny", "Tiny"),
            ("small", "Small"),
            ("medium", "Medium"),
            ("large", "Large"),
        ],
        default="medium",
    )
    speed = models.PositiveIntegerField(default=30, help_text="Base walking speed in feet")
    ability_bonuses = models.JSONField(
        default=dict,
        help_text="Ability score bonuses, e.g., {'str': 2, 'con': 1}",
    )
    traits = models.JSONField(
        default=list,
        help_text="List of racial trait objects",
    )
    languages = models.JSONField(
        default=list,
        help_text="List of languages known",
    )
    darkvision = models.PositiveIntegerField(
        default=0,
        help_text="Darkvision range in feet (0 if none)",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Species"
        verbose_name_plural = "Species"

    def __str__(self) -> str:
        return self.name


class CharacterClass(models.Model):
    """Character classes from SRD 5.2."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    hit_die = models.PositiveIntegerField(
        help_text="Hit die size (e.g., 8 for d8)",
    )
    primary_ability = models.ForeignKey(
        AbilityScore,
        on_delete=models.PROTECT,
        related_name="primary_for_classes",
        null=True,
        blank=True,
    )
    saving_throw_proficiencies = models.ManyToManyField(
        AbilityScore,
        related_name="saving_throw_classes",
        blank=True,
    )
    armor_proficiencies = models.JSONField(
        default=list,
        help_text="List of armor proficiencies",
    )
    weapon_proficiencies = models.JSONField(
        default=list,
        help_text="List of weapon proficiencies",
    )
    tool_proficiencies = models.JSONField(
        default=list,
        help_text="List of tool proficiency options",
    )
    skill_choices = models.JSONField(
        default=dict,
        help_text="Skill selection options, e.g., {'count': 2, 'from': ['Acrobatics', 'Athletics']}",
    )
    starting_equipment = models.JSONField(
        default=list,
        help_text="Starting equipment options",
    )
    spellcasting_ability = models.ForeignKey(
        AbilityScore,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spellcasting_classes",
    )
    features = models.JSONField(
        default=list,
        help_text="Class features by level",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Character Class"
        verbose_name_plural = "Character Classes"

    def __str__(self) -> str:
        return self.name


class Subclass(models.Model):
    """Subclasses for character classes."""

    name = models.CharField(max_length=100)
    character_class = models.ForeignKey(
        CharacterClass,
        on_delete=models.CASCADE,
        related_name="subclasses",
    )
    description = models.TextField(blank=True)
    subclass_level = models.PositiveIntegerField(
        default=3,
        help_text="Level at which this subclass is chosen",
    )
    features = models.JSONField(
        default=list,
        help_text="Subclass features by level",
    )

    class Meta:
        ordering = ["character_class__name", "name"]
        unique_together = ["name", "character_class"]

    def __str__(self) -> str:
        return f"{self.name} ({self.character_class.name})"


class Background(models.Model):
    """Character backgrounds from SRD 5.2."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    skill_proficiencies = models.ManyToManyField(
        Skill,
        related_name="backgrounds",
        blank=True,
    )
    tool_proficiencies = models.JSONField(
        default=list,
        help_text="List of tool proficiencies granted",
    )
    languages = models.JSONField(
        default=list,
        help_text="Language options",
    )
    equipment = models.JSONField(
        default=list,
        help_text="Starting equipment",
    )
    feature_name = models.CharField(max_length=100, blank=True)
    feature_description = models.TextField(blank=True)
    suggested_characteristics = models.JSONField(
        default=dict,
        help_text="Personality traits, ideals, bonds, flaws tables",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class SpellSchool(models.Model):
    """Schools of magic."""

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Spell School"
        verbose_name_plural = "Spell Schools"

    def __str__(self) -> str:
        return self.name


class Spell(models.Model):
    """Spells from SRD 5.2."""

    name = models.CharField(max_length=100, unique=True)
    level = models.PositiveIntegerField(
        help_text="Spell level (0 for cantrips)",
    )
    school = models.ForeignKey(
        SpellSchool,
        on_delete=models.PROTECT,
        related_name="spells",
    )
    casting_time = models.CharField(max_length=100)
    range = models.CharField(max_length=100)
    components = models.JSONField(
        default=dict,
        help_text="Components dict, e.g., {'verbal': true, 'somatic': true, 'material': 'a bit of fur'}",
    )
    duration = models.CharField(max_length=100)
    concentration = models.BooleanField(default=False)
    ritual = models.BooleanField(default=False)
    description = models.TextField()
    higher_levels = models.TextField(
        blank=True,
        help_text="At Higher Levels description",
    )
    classes = models.ManyToManyField(
        CharacterClass,
        related_name="spells",
        blank=True,
    )
    damage_type = models.ForeignKey(
        DamageType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spells",
    )
    dice_expression = models.CharField(
        max_length=50,
        blank=True,
        help_text="Damage/healing dice, e.g., '8d6'",
    )

    class Meta:
        ordering = ["level", "name"]

    def __str__(self) -> str:
        level_str = "Cantrip" if self.level == 0 else f"Level {self.level}"
        return f"{self.name} ({level_str})"


class ItemCategory(models.Model):
    """Categories for items (Weapon, Armor, Adventuring Gear, etc.)."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Item Category"
        verbose_name_plural = "Item Categories"

    def __str__(self) -> str:
        return self.name


class Item(models.Model):
    """Items from SRD 5.2 (equipment, weapons, armor, etc.)."""

    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        related_name="items",
    )
    description = models.TextField(blank=True)
    cost_gp = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost in gold pieces",
    )
    weight_lb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight in pounds",
    )
    rarity = models.CharField(
        max_length=20,
        choices=[
            ("common", "Common"),
            ("uncommon", "Uncommon"),
            ("rare", "Rare"),
            ("very_rare", "Very Rare"),
            ("legendary", "Legendary"),
            ("artifact", "Artifact"),
        ],
        default="common",
    )
    magical = models.BooleanField(default=False)
    requires_attunement = models.BooleanField(default=False)
    attunement_requirements = models.CharField(
        max_length=200,
        blank=True,
        help_text="Attunement requirements if any",
    )
    properties = models.JSONField(
        default=dict,
        help_text="Item-specific properties",
    )

    class Meta:
        ordering = ["category__name", "name"]

    def __str__(self) -> str:
        return self.name


class Weapon(models.Model):
    """Weapons with combat statistics."""

    item = models.OneToOneField(
        Item,
        on_delete=models.CASCADE,
        related_name="weapon_stats",
    )
    weapon_type = models.CharField(
        max_length=20,
        choices=[
            ("simple_melee", "Simple Melee"),
            ("simple_ranged", "Simple Ranged"),
            ("martial_melee", "Martial Melee"),
            ("martial_ranged", "Martial Ranged"),
        ],
    )
    damage_dice = models.CharField(
        max_length=20,
        help_text="Damage dice, e.g., '1d8'",
    )
    damage_type = models.ForeignKey(
        DamageType,
        on_delete=models.PROTECT,
        related_name="weapons",
    )
    properties = models.JSONField(
        default=list,
        help_text="Weapon properties (finesse, versatile, etc.)",
    )
    range_normal = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Normal range in feet",
    )
    range_long = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Long range in feet",
    )
    versatile_dice = models.CharField(
        max_length=20,
        blank=True,
        help_text="Two-handed damage dice if versatile",
    )

    class Meta:
        ordering = ["weapon_type", "item__name"]

    def __str__(self) -> str:
        return f"{self.item.name} ({self.damage_dice} {self.damage_type.name})"


class Armor(models.Model):
    """Armor with defense statistics."""

    item = models.OneToOneField(
        Item,
        on_delete=models.CASCADE,
        related_name="armor_stats",
    )
    armor_type = models.CharField(
        max_length=20,
        choices=[
            ("light", "Light"),
            ("medium", "Medium"),
            ("heavy", "Heavy"),
            ("shield", "Shield"),
        ],
    )
    base_ac = models.PositiveIntegerField(
        help_text="Base armor class",
    )
    dex_bonus = models.CharField(
        max_length=20,
        default="full",
        help_text="DEX bonus: 'full', 'max2', or 'none'",
    )
    strength_requirement = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum STR to avoid speed penalty",
    )
    stealth_disadvantage = models.BooleanField(default=False)
    don_time = models.CharField(
        max_length=50,
        blank=True,
        help_text="Time to don armor",
    )
    doff_time = models.CharField(
        max_length=50,
        blank=True,
        help_text="Time to doff armor",
    )

    class Meta:
        ordering = ["armor_type", "item__name"]

    def __str__(self) -> str:
        return f"{self.item.name} (AC {self.base_ac})"


class MonsterType(models.Model):
    """Monster types (Beast, Dragon, Undead, etc.)."""

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Monster Type"
        verbose_name_plural = "Monster Types"

    def __str__(self) -> str:
        return self.name


class Monster(models.Model):
    """Monsters/creatures from SRD 5.2."""

    name = models.CharField(max_length=100, unique=True)
    monster_type = models.ForeignKey(
        MonsterType,
        on_delete=models.PROTECT,
        related_name="monsters",
    )
    size = models.CharField(
        max_length=20,
        choices=[
            ("tiny", "Tiny"),
            ("small", "Small"),
            ("medium", "Medium"),
            ("large", "Large"),
            ("huge", "Huge"),
            ("gargantuan", "Gargantuan"),
        ],
    )
    alignment = models.CharField(max_length=50, blank=True)
    armor_class = models.PositiveIntegerField()
    armor_description = models.CharField(
        max_length=100,
        blank=True,
        help_text="Source of AC (natural armor, etc.)",
    )
    hit_points = models.PositiveIntegerField()
    hit_dice = models.CharField(
        max_length=20,
        help_text="Hit dice expression, e.g., '4d8+4'",
    )
    speed = models.JSONField(
        default=dict,
        help_text="Speed types and values, e.g., {'walk': 30, 'fly': 60}",
    )
    ability_scores = models.JSONField(
        default=dict,
        help_text="Ability scores dict",
    )
    saving_throws = models.JSONField(
        default=dict,
        help_text="Saving throw bonuses",
    )
    skills = models.JSONField(
        default=dict,
        help_text="Skill bonuses",
    )
    damage_vulnerabilities = models.ManyToManyField(
        DamageType,
        related_name="vulnerable_monsters",
        blank=True,
    )
    damage_resistances = models.ManyToManyField(
        DamageType,
        related_name="resistant_monsters",
        blank=True,
    )
    damage_immunities = models.ManyToManyField(
        DamageType,
        related_name="immune_monsters",
        blank=True,
    )
    condition_immunities = models.ManyToManyField(
        Condition,
        related_name="immune_monsters",
        blank=True,
    )
    senses = models.JSONField(
        default=dict,
        help_text="Senses and passive perception",
    )
    languages = models.JSONField(
        default=list,
        help_text="Languages known",
    )
    challenge_rating = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Challenge rating (0.125 for 1/8, etc.)",
    )
    experience_points = models.PositiveIntegerField()
    traits = models.JSONField(
        default=list,
        help_text="Special traits",
    )
    actions = models.JSONField(
        default=list,
        help_text="Actions available",
    )
    reactions = models.JSONField(
        default=list,
        help_text="Reactions available",
    )
    legendary_actions = models.JSONField(
        default=list,
        help_text="Legendary actions if any",
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["challenge_rating", "name"]

    def __str__(self) -> str:
        return f"{self.name} (CR {self.challenge_rating})"


class Feat(models.Model):
    """Optional feats from SRD 5.2."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    prerequisites = models.JSONField(
        default=dict,
        help_text="Prerequisites for taking this feat",
    )
    benefits = models.JSONField(
        default=list,
        help_text="List of benefits granted by this feat",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
