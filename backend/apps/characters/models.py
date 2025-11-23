"""
Character model - Player character sheets.

Based on SYSTEM_DESIGN.md section 5.1 CharacterSheet entity.
Stores full character data including abilities, skills, equipment,
and spell information following SRD 5.2 rules.
"""

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class CharacterSheet(models.Model):
    """
    Player character sheet with SRD 5.2 attributes.

    JSON Field Schemas:

    ability_scores_json:
        {
            "str": 16, "dex": 14, "con": 12,
            "int": 10, "wis": 8, "cha": 15
        }

    skills_json:
        {
            "acrobatics": {"proficient": true, "expertise": false},
            "athletics": {"proficient": true, "expertise": true},
            ...
        }

    proficiencies_json:
        {
            "armor": ["light", "medium", "shields"],
            "weapons": ["simple", "martial"],
            "tools": ["thieves' tools"],
            "languages": ["Common", "Elvish"],
            "saving_throws": ["str", "con"]
        }

    features_json:
        [
            {"name": "Second Wind", "source": "Fighter 1", "description": "..."},
            {"name": "Action Surge", "source": "Fighter 2", "description": "..."}
        ]

    spellbook_json:
        {
            "spellcasting_ability": "int",
            "spell_save_dc": 14,
            "spell_attack_bonus": 6,
            "cantrips_known": ["Fire Bolt", "Prestidigitation"],
            "spells_known": ["Magic Missile", "Shield"],
            "spells_prepared": ["Magic Missile"],
            "spell_slots": {
                "1": {"max": 4, "used": 2},
                "2": {"max": 2, "used": 0}
            }
        }

    equipment_json:
        {
            "inventory": [
                {"name": "Longsword", "qty": 1, "equipped": true},
                {"name": "Torch", "qty": 5, "equipped": false}
            ],
            "armor_equipped": "Chain Mail",
            "weapons_equipped": ["Longsword", "Shield"],
            "money": {"gp": 15, "sp": 4, "cp": 10, "ep": 0, "pp": 0},
            "encumbrance": {"current": 120, "max": 240}
        }

    hit_dice_json:
        {
            "d10": {"max": 5, "spent": 1},
            "d6": {"max": 2, "spent": 0}
        }

    homebrew_overrides_json:
        {
            "species": "starborn_uuid",  # UUID of homebrew species
            "class": "star_knight_uuid",  # UUID of homebrew class
            "items": ["celestial_blade_uuid"]  # UUIDs of homebrew items
        }

    personality_json:
        {
            "traits": ["I always have a plan.", "I never back down."],
            "ideals": ["Freedom. Chains are meant to be broken."],
            "bonds": ["I protect those who cannot protect themselves."],
            "flaws": ["I'm overconfident in my abilities."]
        }
    """

    # Size choices for species
    SIZE_CHOICES = [
        ("tiny", "Tiny"),
        ("small", "Small"),
        ("medium", "Medium"),
        ("large", "Large"),
    ]

    # Core identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="characters",
    )
    universe = models.ForeignKey(
        "universes.Universe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="characters",
        help_text="Universe this character belongs to (for homebrew content)",
    )

    # Basic info
    name = models.CharField(max_length=100)
    species = models.CharField(
        max_length=100,
        help_text="Species name (from SRD or homebrew)",
    )
    character_class = models.CharField(
        max_length=100,
        help_text="Primary class name",
    )
    subclass = models.CharField(
        max_length=100,
        blank=True,
        help_text="Subclass name (if chosen)",
    )
    background = models.CharField(
        max_length=100,
        help_text="Character background",
    )
    alignment = models.CharField(
        max_length=50,
        blank=True,
        help_text="Character alignment (e.g., 'Lawful Good')",
    )
    size = models.CharField(
        max_length=20,
        choices=SIZE_CHOICES,
        default="medium",
        help_text="Character size from species",
    )

    # Level and XP
    level = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
    )
    experience_points = models.PositiveIntegerField(
        default=0,
        help_text="Total XP earned",
    )

    # Multiclass support
    multiclass_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Multiclass levels, e.g., {'Fighter': 3, 'Wizard': 2}",
    )

    # Hit Points
    hit_points_max = models.PositiveIntegerField(
        default=0,
        help_text="Maximum HP",
    )
    hit_points_current = models.PositiveIntegerField(
        default=0,
        help_text="Current HP",
    )
    hit_points_temp = models.PositiveIntegerField(
        default=0,
        help_text="Temporary HP",
    )
    hit_dice_json = models.JSONField(
        default=dict,
        help_text="Hit dice by type with max/spent tracking",
    )

    # Core stats
    ability_scores_json = models.JSONField(
        default=dict,
        help_text="Ability scores: str, dex, con, int, wis, cha",
    )
    skills_json = models.JSONField(
        default=dict,
        help_text="Skill proficiencies and expertise",
    )
    proficiencies_json = models.JSONField(
        default=dict,
        help_text="Armor, weapon, tool, language, and saving throw proficiencies",
    )

    # Speed and movement
    speed = models.PositiveIntegerField(
        default=30,
        help_text="Base walking speed in feet",
    )
    speed_modifiers_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional speeds: fly, swim, climb, burrow",
    )

    # Defense
    armor_class = models.PositiveIntegerField(
        default=10,
        help_text="Current AC including armor and modifiers",
    )
    armor_class_base = models.PositiveIntegerField(
        default=10,
        help_text="Base AC without equipment",
    )

    # Initiative
    initiative_bonus = models.IntegerField(
        default=0,
        help_text="Total initiative modifier",
    )

    # Features and abilities
    features_json = models.JSONField(
        default=list,
        help_text="Class, species, and background features",
    )

    # Magic
    spellbook_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Spellcasting info, known spells, prepared spells, spell slots",
    )

    # Equipment
    equipment_json = models.JSONField(
        default=dict,
        help_text="Inventory, equipped items, money, encumbrance",
    )

    # Personality from background
    personality_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Personality traits, ideals, bonds, flaws",
    )

    # Homebrew overrides
    homebrew_overrides_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="References to homebrew content (species, class, items, etc.)",
    )

    # Conditions and status
    conditions_json = models.JSONField(
        default=list,
        blank=True,
        help_text="Active conditions (blinded, charmed, etc.)",
    )
    death_saves_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Death save successes and failures: {'successes': 0, 'failures': 0}",
    )

    # Character notes
    backstory = models.TextField(
        blank=True,
        help_text="Character backstory and history",
    )
    notes = models.TextField(
        blank=True,
        help_text="Player notes about the character",
    )

    # Portrait/appearance
    appearance = models.TextField(
        blank=True,
        help_text="Physical appearance description",
    )

    # Inspiration
    has_inspiration = models.BooleanField(
        default=False,
        help_text="Whether character currently has inspiration",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Character Sheet"
        verbose_name_plural = "Character Sheets"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} (Level {self.level} {self.character_class})"

    @property
    def proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on total level."""
        return (self.level - 1) // 4 + 2

    @property
    def is_multiclass(self) -> bool:
        """Check if character has multiple classes."""
        return bool(self.multiclass_json)

    def get_ability_modifier(self, ability: str) -> int:
        """Get the modifier for an ability score."""
        score = self.ability_scores_json.get(ability.lower(), 10)
        return (score - 10) // 2

    def get_skill_bonus(self, skill_name: str, ability: str) -> int:
        """
        Calculate total skill bonus.

        Args:
            skill_name: Name of the skill
            ability: The associated ability score

        Returns:
            Total skill bonus including ability mod and proficiency
        """
        base = self.get_ability_modifier(ability)
        skill_info = self.skills_json.get(skill_name, {})

        if skill_info.get("expertise"):
            return base + (self.proficiency_bonus * 2)
        elif skill_info.get("proficient"):
            return base + self.proficiency_bonus
        return base

    def get_saving_throw_bonus(self, ability: str) -> int:
        """Get saving throw bonus for an ability."""
        base = self.get_ability_modifier(ability)
        proficiencies = self.proficiencies_json.get("saving_throws", [])

        if ability.lower() in [p.lower() for p in proficiencies]:
            return base + self.proficiency_bonus
        return base

    def is_proficient_with(self, item_type: str, item_name: str) -> bool:
        """
        Check if character is proficient with a specific item.

        Args:
            item_type: 'armor', 'weapons', or 'tools'
            item_name: Specific item name or category

        Returns:
            True if proficient
        """
        proficiencies = self.proficiencies_json.get(item_type, [])
        return item_name.lower() in [p.lower() for p in proficiencies]

    def get_spell_slots_remaining(self, level: int) -> int:
        """Get remaining spell slots for a given level."""
        slots = self.spellbook_json.get("spell_slots", {}).get(str(level), {})
        return slots.get("max", 0) - slots.get("used", 0)

    def get_hit_dice_remaining(self) -> dict:
        """Get remaining hit dice by die type."""
        remaining = {}
        for die_type, data in self.hit_dice_json.items():
            remaining[die_type] = data.get("max", 0) - data.get("spent", 0)
        return remaining
