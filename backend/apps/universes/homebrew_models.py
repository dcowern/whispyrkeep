"""
Universe Homebrew models - Custom content per universe.

Based on SYSTEM_DESIGN.md section 9.2-9.3:
- During universe creation, LLM can invent monsters/items/feats/spells as homebrew
- Must label as SRD-derived or Homebrew
- Must assign rarity/power tier and suggested level band
- Post-creation, backend locks these into the homebrew catalog for that universe
"""

import uuid

from django.db import models

from apps.srd.models import (
    Condition,
    DamageType,
    ItemCategory,
    MonsterType,
    SpellSchool,
)

from .models import Universe


class HomebrewBase(models.Model):
    """Abstract base model for all homebrew content."""

    SOURCE_TYPE_CHOICES = [
        ("srd_derived", "SRD Derived"),
        ("homebrew", "Homebrew"),
    ]

    POWER_TIER_CHOICES = [
        ("weak", "Weak"),
        ("standard", "Standard"),
        ("strong", "Strong"),
        ("very_strong", "Very Strong"),
        ("legendary", "Legendary"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    universe = models.ForeignKey(
        Universe,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        default="homebrew",
        help_text="Whether this is derived from SRD or purely homebrew",
    )
    power_tier = models.CharField(
        max_length=20,
        choices=POWER_TIER_CHOICES,
        default="standard",
        help_text="Relative power level of this content",
    )
    suggested_level_min = models.PositiveIntegerField(
        default=1,
        help_text="Minimum suggested character level for this content",
    )
    suggested_level_max = models.PositiveIntegerField(
        default=20,
        help_text="Maximum suggested character level for this content",
    )
    is_locked = models.BooleanField(
        default=False,
        help_text="Locked after universe creation is complete",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class HomebrewSpecies(HomebrewBase):
    """Custom playable species for a universe."""

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
        ordering = ["universe", "name"]
        verbose_name = "Homebrew Species"
        verbose_name_plural = "Homebrew Species"
        constraints = [
            models.UniqueConstraint(
                fields=["universe", "name"],
                name="unique_homebrew_species_per_universe",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.universe.name})"


class HomebrewSpell(HomebrewBase):
    """Custom spells for a universe."""

    level = models.PositiveIntegerField(
        help_text="Spell level (0 for cantrips)",
    )
    school = models.ForeignKey(
        SpellSchool,
        on_delete=models.PROTECT,
        related_name="homebrew_spells",
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
    higher_levels = models.TextField(
        blank=True,
        help_text="At Higher Levels description",
    )
    damage_type = models.ForeignKey(
        DamageType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="homebrew_spells",
    )
    dice_expression = models.CharField(
        max_length=50,
        blank=True,
        help_text="Damage/healing dice, e.g., '8d6'",
    )
    class_restrictions = models.JSONField(
        default=list,
        help_text="List of class names that can use this spell (empty = all)",
    )

    class Meta:
        ordering = ["universe", "level", "name"]
        verbose_name = "Homebrew Spell"
        verbose_name_plural = "Homebrew Spells"
        constraints = [
            models.UniqueConstraint(
                fields=["universe", "name"],
                name="unique_homebrew_spell_per_universe",
            )
        ]

    def __str__(self) -> str:
        level_str = "Cantrip" if self.level == 0 else f"Level {self.level}"
        return f"{self.name} ({level_str}) - {self.universe.name}"


class HomebrewItem(HomebrewBase):
    """Custom items for a universe (equipment, weapons, armor, etc.)."""

    RARITY_CHOICES = [
        ("common", "Common"),
        ("uncommon", "Uncommon"),
        ("rare", "Rare"),
        ("very_rare", "Very Rare"),
        ("legendary", "Legendary"),
        ("artifact", "Artifact"),
    ]

    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        related_name="homebrew_items",
    )
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
        choices=RARITY_CHOICES,
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
    # Weapon stats (if applicable)
    is_weapon = models.BooleanField(default=False)
    weapon_type = models.CharField(
        max_length=20,
        choices=[
            ("simple_melee", "Simple Melee"),
            ("simple_ranged", "Simple Ranged"),
            ("martial_melee", "Martial Melee"),
            ("martial_ranged", "Martial Ranged"),
        ],
        blank=True,
    )
    damage_dice = models.CharField(
        max_length=20,
        blank=True,
        help_text="Damage dice, e.g., '1d8'",
    )
    damage_type = models.ForeignKey(
        DamageType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="homebrew_items",
    )
    weapon_properties = models.JSONField(
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
    # Armor stats (if applicable)
    is_armor = models.BooleanField(default=False)
    armor_type = models.CharField(
        max_length=20,
        choices=[
            ("light", "Light"),
            ("medium", "Medium"),
            ("heavy", "Heavy"),
            ("shield", "Shield"),
        ],
        blank=True,
    )
    base_ac = models.PositiveIntegerField(
        null=True,
        blank=True,
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

    class Meta:
        ordering = ["universe", "category", "name"]
        verbose_name = "Homebrew Item"
        verbose_name_plural = "Homebrew Items"
        constraints = [
            models.UniqueConstraint(
                fields=["universe", "name"],
                name="unique_homebrew_item_per_universe",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.universe.name})"


class HomebrewMonster(HomebrewBase):
    """Custom monsters/creatures for a universe."""

    monster_type = models.ForeignKey(
        MonsterType,
        on_delete=models.PROTECT,
        related_name="homebrew_monsters",
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
        help_text="Ability scores dict, e.g., {'str': 16, 'dex': 12, ...}",
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
        related_name="vulnerable_homebrew_monsters",
        blank=True,
    )
    damage_resistances = models.ManyToManyField(
        DamageType,
        related_name="resistant_homebrew_monsters",
        blank=True,
    )
    damage_immunities = models.ManyToManyField(
        DamageType,
        related_name="immune_homebrew_monsters",
        blank=True,
    )
    condition_immunities = models.ManyToManyField(
        Condition,
        related_name="immune_homebrew_monsters",
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
    lair_actions = models.JSONField(
        default=list,
        help_text="Lair actions if any",
    )
    regional_effects = models.JSONField(
        default=list,
        help_text="Regional effects if any",
    )

    class Meta:
        ordering = ["universe", "challenge_rating", "name"]
        verbose_name = "Homebrew Monster"
        verbose_name_plural = "Homebrew Monsters"
        constraints = [
            models.UniqueConstraint(
                fields=["universe", "name"],
                name="unique_homebrew_monster_per_universe",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} (CR {self.challenge_rating}) - {self.universe.name}"


class HomebrewFeat(HomebrewBase):
    """Custom feats for a universe."""

    prerequisites = models.JSONField(
        default=dict,
        help_text="Prerequisites for taking this feat, e.g., {'level': 4, 'ability': {'str': 13}}",
    )
    benefits = models.JSONField(
        default=list,
        help_text="List of benefits granted by this feat",
    )
    ability_score_increase = models.JSONField(
        default=dict,
        help_text="Ability score increases, e.g., {'choice': ['str', 'dex'], 'amount': 1}",
    )

    class Meta:
        ordering = ["universe", "name"]
        verbose_name = "Homebrew Feat"
        verbose_name_plural = "Homebrew Feats"
        constraints = [
            models.UniqueConstraint(
                fields=["universe", "name"],
                name="unique_homebrew_feat_per_universe",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.universe.name})"


class HomebrewBackground(HomebrewBase):
    """Custom character backgrounds for a universe."""

    skill_proficiencies = models.JSONField(
        default=list,
        help_text="List of skill proficiency names",
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
        ordering = ["universe", "name"]
        verbose_name = "Homebrew Background"
        verbose_name_plural = "Homebrew Backgrounds"
        constraints = [
            models.UniqueConstraint(
                fields=["universe", "name"],
                name="unique_homebrew_background_per_universe",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.universe.name})"


class HomebrewClass(HomebrewBase):
    """Custom character classes for a universe."""

    hit_die = models.PositiveIntegerField(
        help_text="Hit die size (e.g., 8 for d8)",
    )
    primary_ability = models.JSONField(
        default=list,
        help_text="Primary ability scores, e.g., ['str'] or ['str', 'dex']",
    )
    saving_throw_proficiencies = models.JSONField(
        default=list,
        help_text="Saving throw proficiency ability abbreviations",
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
    spellcasting_ability = models.CharField(
        max_length=3,
        blank=True,
        help_text="Spellcasting ability abbreviation (str, dex, etc.)",
    )
    features = models.JSONField(
        default=list,
        help_text="Class features by level",
    )
    subclass_level = models.PositiveIntegerField(
        default=3,
        help_text="Level at which subclass is chosen",
    )
    spell_slots = models.JSONField(
        default=dict,
        help_text="Spell slots by level, e.g., {'1': {'1': 2, '2': 3}, ...}",
    )

    class Meta:
        ordering = ["universe", "name"]
        verbose_name = "Homebrew Class"
        verbose_name_plural = "Homebrew Classes"
        constraints = [
            models.UniqueConstraint(
                fields=["universe", "name"],
                name="unique_homebrew_class_per_universe",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.universe.name})"


class HomebrewSubclass(HomebrewBase):
    """Custom subclasses for homebrew classes."""

    parent_class = models.ForeignKey(
        HomebrewClass,
        on_delete=models.CASCADE,
        related_name="subclasses",
        null=True,
        blank=True,
        help_text="Link to homebrew parent class (if homebrew)",
    )
    srd_parent_class_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of SRD parent class (if extending SRD class)",
    )
    subclass_level = models.PositiveIntegerField(
        default=3,
        help_text="Level at which this subclass is chosen",
    )
    features = models.JSONField(
        default=list,
        help_text="Subclass features by level",
    )

    class Meta:
        ordering = ["universe", "name"]
        verbose_name = "Homebrew Subclass"
        verbose_name_plural = "Homebrew Subclasses"
        constraints = [
            models.UniqueConstraint(
                fields=["universe", "name"],
                name="unique_homebrew_subclass_per_universe",
            )
        ]

    def __str__(self) -> str:
        parent = self.parent_class.name if self.parent_class else self.srd_parent_class_name
        return f"{self.name} ({parent}) - {self.universe.name}"
