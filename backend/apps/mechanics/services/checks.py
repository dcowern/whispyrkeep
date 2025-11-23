"""
Ability Check and Saving Throw Resolution.

Resolves ability checks and saving throws per SRD 5.2 rules.
Uses the dice roller for deterministic resolution.

Ticket: 9.0.2

Based on SYSTEM_DESIGN.md section 7.3 Deterministic Functions.
"""

from dataclasses import dataclass, field
from enum import Enum

from .dice import AdvantageState, DiceRoller, RollResult


class Ability(str, Enum):
    """SRD 5.2 ability scores."""

    STR = "str"
    DEX = "dex"
    CON = "con"
    INT = "int"
    WIS = "wis"
    CHA = "cha"


# Mapping of skills to their associated ability
SKILL_ABILITY_MAP: dict[str, Ability] = {
    "acrobatics": Ability.DEX,
    "animal_handling": Ability.WIS,
    "arcana": Ability.INT,
    "athletics": Ability.STR,
    "deception": Ability.CHA,
    "history": Ability.INT,
    "insight": Ability.WIS,
    "intimidation": Ability.CHA,
    "investigation": Ability.INT,
    "medicine": Ability.WIS,
    "nature": Ability.INT,
    "perception": Ability.WIS,
    "performance": Ability.CHA,
    "persuasion": Ability.CHA,
    "religion": Ability.INT,
    "sleight_of_hand": Ability.DEX,
    "stealth": Ability.DEX,
    "survival": Ability.WIS,
}

# Alternate skill names mapping for compatibility
SKILL_ALIASES: dict[str, str] = {
    "animal handling": "animal_handling",
    "sleight of hand": "sleight_of_hand",
}


@dataclass
class CharacterStats:
    """
    Character statistics needed for ability checks and saves.

    This can be constructed from campaign state or CharacterSheet data.
    """

    # Ability scores (1-30, typically 3-20)
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    # Character level (1-20)
    level: int = 1

    # Skill proficiencies (set of skill names)
    skill_proficiencies: set[str] = field(default_factory=set)

    # Skill expertises (double proficiency bonus)
    skill_expertises: set[str] = field(default_factory=set)

    # Saving throw proficiencies (set of ability names)
    save_proficiencies: set[str] = field(default_factory=set)

    @classmethod
    def from_dict(cls, data: dict) -> "CharacterStats":
        """
        Create CharacterStats from a dictionary.

        Supports multiple formats for compatibility.
        """
        # Handle ability scores
        abilities = data.get("abilities", data.get("ability_scores", {}))

        # Normalize skill proficiencies
        skills = data.get("skills", {})
        skill_profs = set()
        skill_exps = set()

        for skill_name, skill_data in skills.items():
            normalized = _normalize_skill_name(skill_name)
            if isinstance(skill_data, dict):
                if skill_data.get("proficient", False):
                    skill_profs.add(normalized)
                if skill_data.get("expertise", False):
                    skill_exps.add(normalized)
            elif skill_data:  # Simple truthy value means proficient
                skill_profs.add(normalized)

        # Handle save proficiencies
        save_profs = set(
            s.lower() for s in data.get("save_proficiencies", [])
        )

        return cls(
            strength=abilities.get("str", abilities.get("strength", 10)),
            dexterity=abilities.get("dex", abilities.get("dexterity", 10)),
            constitution=abilities.get("con", abilities.get("constitution", 10)),
            intelligence=abilities.get("int", abilities.get("intelligence", 10)),
            wisdom=abilities.get("wis", abilities.get("wisdom", 10)),
            charisma=abilities.get("cha", abilities.get("charisma", 10)),
            level=data.get("level", 1),
            skill_proficiencies=skill_profs,
            skill_expertises=skill_exps,
            save_proficiencies=save_profs,
        )

    def get_ability_score(self, ability: Ability | str) -> int:
        """Get the score for an ability."""
        ability_str = ability.value if isinstance(ability, Ability) else ability.lower()
        return {
            "str": self.strength,
            "dex": self.dexterity,
            "con": self.constitution,
            "int": self.intelligence,
            "wis": self.wisdom,
            "cha": self.charisma,
        }.get(ability_str, 10)

    def get_ability_modifier(self, ability: Ability | str) -> int:
        """Get the modifier for an ability score."""
        score = self.get_ability_score(ability)
        return (score - 10) // 2

    @property
    def proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on level."""
        return 2 + (self.level - 1) // 4


def _normalize_skill_name(skill: str) -> str:
    """Normalize a skill name to the standard format."""
    skill_lower = skill.lower().strip()
    return SKILL_ALIASES.get(skill_lower, skill_lower.replace(" ", "_"))


@dataclass
class CheckResult:
    """Result of an ability check or saving throw."""

    success: bool
    total: int
    natural_roll: int
    modifier: int
    dc: int
    ability: str
    skill: str | None = None
    proficient: bool = False
    expertise: bool = False
    advantage_state: AdvantageState = AdvantageState.NONE
    is_critical_success: bool = False  # Natural 20
    is_critical_failure: bool = False  # Natural 1
    roll_result: RollResult | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "total": self.total,
            "natural_roll": self.natural_roll,
            "modifier": self.modifier,
            "dc": self.dc,
            "ability": self.ability,
            "skill": self.skill,
            "proficient": self.proficient,
            "expertise": self.expertise,
            "advantage_state": self.advantage_state.value,
            "is_critical_success": self.is_critical_success,
            "is_critical_failure": self.is_critical_failure,
        }


class CheckResolver:
    """
    Resolves ability checks and saving throws.

    Uses SRD 5.2 rules for check resolution:
    - Roll d20
    - Add ability modifier
    - Add proficiency bonus if proficient
    - Double proficiency bonus if expertise (checks only)
    - Compare to DC
    """

    def __init__(self, dice_roller: DiceRoller | None = None):
        """
        Initialize the resolver.

        Args:
            dice_roller: Optional dice roller (creates new one if not provided)
        """
        self.dice = dice_roller or DiceRoller()

    def resolve_ability_check(
        self,
        character: CharacterStats | dict,
        ability: Ability | str,
        dc: int,
        skill: str | None = None,
        advantage: AdvantageState = AdvantageState.NONE,
        bonus: int = 0,
    ) -> CheckResult:
        """
        Resolve an ability check.

        Args:
            character: Character stats (CharacterStats or dict)
            ability: The ability to check (str, dex, etc.)
            dc: Difficulty class
            skill: Optional skill for the check (adds proficiency if proficient)
            advantage: Advantage state for the roll
            bonus: Additional bonus to the check

        Returns:
            CheckResult with outcome
        """
        if isinstance(character, dict):
            character = CharacterStats.from_dict(character)

        ability_str = ability.value if isinstance(ability, Ability) else ability.lower()

        # Get ability modifier
        ability_mod = character.get_ability_modifier(ability_str)

        # Calculate skill bonus
        proficient = False
        expertise = False
        skill_normalized = None

        if skill:
            skill_normalized = _normalize_skill_name(skill)
            proficient = skill_normalized in character.skill_proficiencies
            expertise = skill_normalized in character.skill_expertises

        # Calculate total modifier
        prof_bonus = character.proficiency_bonus
        total_modifier = ability_mod + bonus

        if proficient:
            total_modifier += prof_bonus
        if expertise:
            total_modifier += prof_bonus  # Double proficiency

        # Roll the dice
        roll = self.dice.roll_d20(advantage=advantage, modifier=total_modifier)

        # Determine success
        # Note: Natural 1/20 don't auto-fail/succeed ability checks in SRD 5.2
        success = roll.total >= dc

        return CheckResult(
            success=success,
            total=roll.total,
            natural_roll=roll.natural_roll,
            modifier=total_modifier,
            dc=dc,
            ability=ability_str,
            skill=skill_normalized,
            proficient=proficient,
            expertise=expertise,
            advantage_state=advantage,
            is_critical_success=roll.is_critical,
            is_critical_failure=roll.is_fumble,
            roll_result=roll,
        )

    def resolve_saving_throw(
        self,
        character: CharacterStats | dict,
        ability: Ability | str,
        dc: int,
        advantage: AdvantageState = AdvantageState.NONE,
        bonus: int = 0,
    ) -> CheckResult:
        """
        Resolve a saving throw.

        Args:
            character: Character stats (CharacterStats or dict)
            ability: The ability for the save (str, dex, etc.)
            dc: Difficulty class
            advantage: Advantage state for the roll
            bonus: Additional bonus to the save

        Returns:
            CheckResult with outcome
        """
        if isinstance(character, dict):
            character = CharacterStats.from_dict(character)

        ability_str = ability.value if isinstance(ability, Ability) else ability.lower()

        # Get ability modifier
        ability_mod = character.get_ability_modifier(ability_str)

        # Check for save proficiency
        proficient = ability_str in character.save_proficiencies

        # Calculate total modifier
        total_modifier = ability_mod + bonus
        if proficient:
            total_modifier += character.proficiency_bonus

        # Roll the dice
        roll = self.dice.roll_d20(advantage=advantage, modifier=total_modifier)

        # Determine success
        # Note: Natural 1/20 don't auto-fail/succeed saves in SRD 5.2
        # (unlike attack rolls)
        success = roll.total >= dc

        return CheckResult(
            success=success,
            total=roll.total,
            natural_roll=roll.natural_roll,
            modifier=total_modifier,
            dc=dc,
            ability=ability_str,
            skill=None,
            proficient=proficient,
            expertise=False,  # No expertise on saves
            advantage_state=advantage,
            is_critical_success=roll.is_critical,
            is_critical_failure=roll.is_fumble,
            roll_result=roll,
        )

    def resolve_contested_check(
        self,
        actor: CharacterStats | dict,
        actor_ability: Ability | str,
        actor_skill: str | None,
        target: CharacterStats | dict,
        target_ability: Ability | str,
        target_skill: str | None,
        actor_advantage: AdvantageState = AdvantageState.NONE,
        target_advantage: AdvantageState = AdvantageState.NONE,
    ) -> tuple[CheckResult, CheckResult, bool]:
        """
        Resolve a contested check (e.g., grapple, hide vs perception).

        Args:
            actor: The initiating character's stats
            actor_ability: Actor's ability for the check
            actor_skill: Actor's skill for the check
            target: The opposing character's stats
            target_ability: Target's ability for the check
            target_skill: Target's skill for the check
            actor_advantage: Actor's advantage state
            target_advantage: Target's advantage state

        Returns:
            Tuple of (actor_result, target_result, actor_wins)
        """
        # Both roll against DC 0 (we compare totals)
        actor_result = self.resolve_ability_check(
            actor, actor_ability, dc=0, skill=actor_skill, advantage=actor_advantage
        )
        target_result = self.resolve_ability_check(
            target, target_ability, dc=0, skill=target_skill, advantage=target_advantage
        )

        # Actor wins ties per SRD
        actor_wins = actor_result.total >= target_result.total

        # Update success flags based on contest outcome
        actor_result.success = actor_wins
        target_result.success = not actor_wins

        return actor_result, target_result, actor_wins


# Convenience functions for common checks
def resolve_ability_check(
    character: CharacterStats | dict,
    ability: Ability | str,
    dc: int,
    skill: str | None = None,
    advantage: AdvantageState = AdvantageState.NONE,
    seed: int | None = None,
) -> CheckResult:
    """
    Convenience function to resolve an ability check.

    Args:
        character: Character stats
        ability: Ability to check
        dc: Difficulty class
        skill: Optional skill
        advantage: Advantage state
        seed: Optional seed for deterministic roll

    Returns:
        CheckResult
    """
    roller = DiceRoller(seed=seed)
    resolver = CheckResolver(roller)
    return resolver.resolve_ability_check(character, ability, dc, skill, advantage)


def resolve_saving_throw(
    character: CharacterStats | dict,
    ability: Ability | str,
    dc: int,
    advantage: AdvantageState = AdvantageState.NONE,
    seed: int | None = None,
) -> CheckResult:
    """
    Convenience function to resolve a saving throw.

    Args:
        character: Character stats
        ability: Ability for the save
        dc: Difficulty class
        advantage: Advantage state
        seed: Optional seed for deterministic roll

    Returns:
        CheckResult
    """
    roller = DiceRoller(seed=seed)
    resolver = CheckResolver(roller)
    return resolver.resolve_saving_throw(character, ability, dc, advantage)
