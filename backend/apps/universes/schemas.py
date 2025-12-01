"""
Step schemas for AI-assisted universe building.

Defines the structure, required fields, and validation for each step
in the universe creation process.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StepName(str, Enum):
    """Names of universe creation steps."""

    BASICS = "basics"
    TONE = "tone"
    RULES = "rules"
    CALENDAR = "calendar"
    LORE = "lore"
    HOMEBREW = "homebrew"


@dataclass
class FieldSpec:
    """Specification for a single field."""

    name: str
    field_type: str  # "string", "number", "boolean", "array", "object"
    required: bool = False
    min_value: float | None = None
    max_value: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    default: Any = None
    description: str = ""


@dataclass
class StepSpec:
    """Specification for a universe creation step."""

    name: StepName
    display_name: str
    description: str
    fields: list[FieldSpec]
    prompt_context: str  # Context to give the AI about this step

    def get_required_fields(self) -> list[str]:
        """Get list of required field names."""
        return [f.name for f in self.fields if f.required]

    def get_field(self, name: str) -> FieldSpec | None:
        """Get a field spec by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None


# Step definitions
STEP_SPECS: dict[StepName, StepSpec] = {
    StepName.BASICS: StepSpec(
        name=StepName.BASICS,
        display_name="Basics",
        description="Universe name and description",
        prompt_context=(
            "Help the user choose a name and write a description for their universe. "
            "Ask about the general concept, setting type (fantasy, sci-fi, etc.), "
            "and any inspirations they have."
        ),
        fields=[
            FieldSpec(
                name="name",
                field_type="string",
                required=True,
                min_length=1,
                max_length=200,
                description="The name of the universe",
            ),
            FieldSpec(
                name="description",
                field_type="string",
                required=False,
                max_length=2000,
                default="",
                description="A description of the universe",
            ),
        ],
    ),
    StepName.TONE: StepSpec(
        name=StepName.TONE,
        display_name="Tone",
        description="Mood and atmosphere settings",
        prompt_context=(
            "Help the user define the tone and atmosphere of their universe using sliders "
            "from 0-100. Discuss whether they want dark/gritty or light/cozy, "
            "comedic or serious, low or high magic, sandbox or guided stories, "
            "and combat-heavy or roleplay-focused."
        ),
        fields=[
            FieldSpec(
                name="darkness",
                field_type="number",
                required=True,
                min_value=0,
                max_value=100,
                default=50,
                description="0=grimdark, 100=cozy",
            ),
            FieldSpec(
                name="humor",
                field_type="number",
                required=True,
                min_value=0,
                max_value=100,
                default=50,
                description="0=comedic, 100=serious",
            ),
            FieldSpec(
                name="realism",
                field_type="number",
                required=True,
                min_value=0,
                max_value=100,
                default=50,
                description="0=realistic, 100=fantastical",
            ),
            FieldSpec(
                name="magic_level",
                field_type="number",
                required=True,
                min_value=0,
                max_value=100,
                default=50,
                description="0=low magic, 100=high magic",
            ),
            FieldSpec(
                name="themes",
                field_type="array",
                required=False,
                default=[],
                description="Theme tags like 'exploration', 'intrigue', 'war'",
            ),
        ],
    ),
    StepName.RULES: StepSpec(
        name=StepName.RULES,
        display_name="Rules",
        description="Game mechanics preferences",
        prompt_context=(
            "Help the user decide on house rules and mechanics. Discuss permadeath, "
            "critical fumbles, encumbrance tracking, and how strict vs. loose "
            "they want the rules interpreted."
        ),
        fields=[
            FieldSpec(
                name="permadeath",
                field_type="boolean",
                required=True,
                default=None,
                description="Characters can permanently die",
            ),
            FieldSpec(
                name="critical_fumbles",
                field_type="boolean",
                required=True,
                default=None,
                description="Natural 1s have additional penalties",
            ),
            FieldSpec(
                name="encumbrance",
                field_type="boolean",
                required=True,
                default=None,
                description="Track carrying capacity",
            ),
            FieldSpec(
                name="rules_strictness",
                field_type="number",
                required=False,
                default=50,
                min_value=0,
                max_value=100,
                description="0=Loose (rule of cool), 50=Standard, 100=Strict (RAW)",
            ),
        ],
    ),
    StepName.CALENDAR: StepSpec(
        name=StepName.CALENDAR,
        display_name="Calendar",
        description="In-world time system",
        prompt_context=(
            "Help the user customize the calendar for their world. "
            "Uses standard 12-month, 365-day calendar with optional custom names "
            "for months and weekdays to add flavor."
        ),
        fields=[
            FieldSpec(
                name="use_custom_names",
                field_type="boolean",
                required=False,
                default=False,
                description="Use custom names for months and weekdays",
            ),
            FieldSpec(
                name="month_names",
                field_type="string",
                required=False,
                default="",
                description="Comma-separated custom month names (12 names)",
            ),
            FieldSpec(
                name="weekday_names",
                field_type="string",
                required=False,
                default="",
                description="Comma-separated custom weekday names (7 names)",
            ),
        ],
    ),
    StepName.LORE: StepSpec(
        name=StepName.LORE,
        display_name="Lore",
        description="World history, geography, cultures, and politics",
        prompt_context=(
            "Help the user create detailed lore for their world across three areas:\n"
            "1. HISTORY: World timeline, regional histories, legendary figures & myths, political history\n"
            "2. GEOGRAPHY & CULTURES: Continents, regions, settlements, cultures, factions, religions\n"
            "3. POLITICS: Leaders, agendas, tensions, conflicts\n"
            "These documents become immutable truths about the world."
        ),
        fields=[
            # History section
            FieldSpec(
                name="world_timeline",
                field_type="string",
                required=False,
                default="",
                description="Structured world timeline - major eras and events",
            ),
            FieldSpec(
                name="regional_histories",
                field_type="string",
                required=False,
                default="",
                description="History of specific regions and how they developed",
            ),
            FieldSpec(
                name="legendary_figures",
                field_type="string",
                required=False,
                default="",
                description="Legendary figures, heroes, villains, and myths",
            ),
            FieldSpec(
                name="political_history",
                field_type="string",
                required=False,
                default="",
                description="Wars, treaties, rise and fall of empires",
            ),
            # Geography & Cultures section
            FieldSpec(
                name="geography",
                field_type="string",
                required=False,
                default="",
                description="Continents, seas, trade routes, distances",
            ),
            FieldSpec(
                name="regions_settlements",
                field_type="string",
                required=False,
                default="",
                description="Detailed regions with major settlements",
            ),
            FieldSpec(
                name="cultures_peoples",
                field_type="string",
                required=False,
                default="",
                description="Cultures, peoples, customs, and traditions",
            ),
            FieldSpec(
                name="factions_religions",
                field_type="string",
                required=False,
                default="",
                description="Factions, religions, guilds, and organizations",
            ),
            FieldSpec(
                name="mysterious_lands",
                field_type="string",
                required=False,
                default="",
                description="Mysterious distant lands and unexplored regions",
            ),
            # Politics section
            FieldSpec(
                name="political_leaders",
                field_type="string",
                required=False,
                default="",
                description="Major political leaders and their positions",
            ),
            FieldSpec(
                name="leader_agendas",
                field_type="string",
                required=False,
                default="",
                description="Leader goals, motivations, and agendas",
            ),
            FieldSpec(
                name="regional_tensions",
                field_type="string",
                required=False,
                default="",
                description="Regional tensions and brewing conflicts",
            ),
            FieldSpec(
                name="faction_conflicts",
                field_type="string",
                required=False,
                default="",
                description="Faction conflicts, alliances, and goals",
            ),
            # Legacy fields for backward compatibility
            FieldSpec(
                name="canon_docs",
                field_type="array",
                required=False,
                default=[],
                description="Array of {title, content} for hard canon documents",
            ),
            FieldSpec(
                name="world_overview",
                field_type="string",
                required=False,
                default="",
                description="Generated world overview text",
            ),
        ],
    ),
    StepName.HOMEBREW: StepSpec(
        name=StepName.HOMEBREW,
        display_name="Homebrew",
        description="Custom game content",
        prompt_context=(
            "Help the user create homebrew content for their universe. "
            "This can include custom species, spells, items, monsters, feats, "
            "backgrounds, and classes. All content should be balanced for SRD 5.2."
        ),
        fields=[
            FieldSpec(
                name="species",
                field_type="string",
                required=False,
                default="",
                description="Custom playable species/races",
            ),
            FieldSpec(
                name="classes",
                field_type="string",
                required=False,
                default="",
                description="Custom character classes",
            ),
            FieldSpec(
                name="spells",
                field_type="string",
                required=False,
                default="",
                description="Custom spells",
            ),
            FieldSpec(
                name="items",
                field_type="string",
                required=False,
                default="",
                description="Custom items and equipment",
            ),
            FieldSpec(
                name="monsters",
                field_type="string",
                required=False,
                default="",
                description="Custom creatures and monsters",
            ),
            FieldSpec(
                name="feats",
                field_type="string",
                required=False,
                default="",
                description="Custom feats",
            ),
            FieldSpec(
                name="backgrounds",
                field_type="string",
                required=False,
                default="",
                description="Custom character backgrounds",
            ),
        ],
    ),
}

# Order of steps for UI
STEP_ORDER = [
    StepName.BASICS,
    StepName.TONE,
    StepName.RULES,
    StepName.CALENDAR,
    StepName.LORE,
    StepName.HOMEBREW,
]

# Required steps that must be complete to create a universe
REQUIRED_STEPS = [StepName.BASICS, StepName.TONE, StepName.RULES]


def validate_step_data(step_name: StepName, data: dict) -> tuple[bool, list[str]]:
    """
    Validate data for a specific step.

    Args:
        step_name: The step to validate
        data: The data to validate

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    spec = STEP_SPECS.get(step_name)
    if not spec:
        return False, [f"Unknown step: {step_name}"]

    errors = []

    for field_spec in spec.fields:
        value = data.get(field_spec.name)

        # Check required fields
        if field_spec.required and value is None:
            errors.append(f"{field_spec.name} is required")
            continue

        if value is None:
            continue

        # Type-specific validation
        if field_spec.field_type == "string":
            if not isinstance(value, str):
                errors.append(f"{field_spec.name} must be a string")
            else:
                if field_spec.min_length and len(value) < field_spec.min_length:
                    errors.append(
                        f"{field_spec.name} must be at least {field_spec.min_length} characters"
                    )
                if field_spec.max_length and len(value) > field_spec.max_length:
                    errors.append(
                        f"{field_spec.name} must be at most {field_spec.max_length} characters"
                    )

        elif field_spec.field_type == "number":
            if not isinstance(value, (int, float)):
                errors.append(f"{field_spec.name} must be a number")
            else:
                if field_spec.min_value is not None and value < field_spec.min_value:
                    errors.append(
                        f"{field_spec.name} must be at least {field_spec.min_value}"
                    )
                if field_spec.max_value is not None and value > field_spec.max_value:
                    errors.append(
                        f"{field_spec.name} must be at most {field_spec.max_value}"
                    )

        elif field_spec.field_type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"{field_spec.name} must be a boolean")

        elif field_spec.field_type == "array":
            if not isinstance(value, list):
                errors.append(f"{field_spec.name} must be an array")

        elif field_spec.field_type == "object":
            if not isinstance(value, dict):
                errors.append(f"{field_spec.name} must be an object")

    return len(errors) == 0, errors


def check_step_completion(
    step_name: StepName, data: dict, touched: bool = False
) -> tuple[bool, dict]:
    """
    Check if a step has all required fields filled with meaningful values.

    A step is complete when:
    1. It has been touched (user/AI explicitly provided data for it)
    2. All required fields have non-default, meaningful values

    Args:
        step_name: The step to check
        data: The current data for the step
        touched: Whether the step has been explicitly touched by user/AI

    Returns:
        Tuple of (is_complete, {field_name: is_filled})
    """
    spec = STEP_SPECS.get(step_name)
    if not spec:
        return False, {}

    field_status = {}
    all_required_filled = True

    for field_spec in spec.fields:
        value = data.get(field_spec.name)

        # Check if value is meaningfully filled (not empty/default)
        is_filled = _is_field_meaningfully_filled(field_spec, value)

        field_status[field_spec.name] = is_filled

        if field_spec.required and not is_filled:
            all_required_filled = False

    # Step is only complete if touched AND all required fields are filled
    is_complete = touched and all_required_filled

    return is_complete, field_status


def _is_field_meaningfully_filled(field_spec: FieldSpec, value) -> bool:
    """
    Check if a field has a meaningful (non-empty) value.

    For strings: must have actual content (not empty)
    For numbers: any value is valid if present
    For booleans: any value is valid if present
    For arrays: must have at least one item
    For objects: must have at least one key

    Args:
        field_spec: The field specification
        value: The current value

    Returns:
        True if the field has meaningful content
    """
    if value is None:
        return False

    if field_spec.field_type == "string":
        return isinstance(value, str) and len(value.strip()) > 0

    if field_spec.field_type == "number":
        return isinstance(value, (int, float))

    if field_spec.field_type == "boolean":
        return isinstance(value, bool)

    if field_spec.field_type == "array":
        return isinstance(value, list) and len(value) > 0

    if field_spec.field_type == "object":
        return isinstance(value, dict) and len(value) > 0

    return value is not None


def get_step_defaults() -> dict:
    """Get default values for all steps."""
    defaults = {}
    for step_name, spec in STEP_SPECS.items():
        step_defaults = {}
        for field_spec in spec.fields:
            if field_spec.default is not None:
                step_defaults[field_spec.name] = field_spec.default
        defaults[step_name.value] = step_defaults
    return defaults


def get_ai_context_for_step(step_name: StepName, current_data: dict) -> str:
    """
    Get AI context for a specific step.

    Args:
        step_name: The step the AI should focus on
        current_data: All current draft data

    Returns:
        Context string to include in AI prompt
    """
    spec = STEP_SPECS.get(step_name)
    if not spec:
        return ""

    context_parts = [
        f"## Current Step: {spec.display_name}",
        f"\n{spec.description}\n",
        f"\n### Your Task\n{spec.prompt_context}\n",
        "\n### Fields to Fill",
    ]

    for field_spec in spec.fields:
        required_marker = " (required)" if field_spec.required else " (optional)"
        current_value = current_data.get(step_name.value, {}).get(field_spec.name)
        if current_value:
            context_parts.append(
                f"- **{field_spec.name}**{required_marker}: Currently set to {current_value}"
            )
        else:
            context_parts.append(
                f"- **{field_spec.name}**{required_marker}: {field_spec.description}"
            )

    return "\n".join(context_parts)
