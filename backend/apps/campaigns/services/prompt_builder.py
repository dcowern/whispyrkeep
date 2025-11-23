"""
Prompt Builder Service.

Constructs prompts for the LLM DM including:
- System prompt (static)
- Universe prompt (dynamic)
- Campaign prompt (dynamic)
- Lore injection

Tickets: 8.1.1, 8.1.2, 8.1.3, 8.1.4

Based on SYSTEM_DESIGN.md section 8.1 Prompt Layers.
"""

from dataclasses import dataclass, field
from typing import Any

from apps.campaigns.models import Campaign, TurnEvent
from apps.lore.services.chroma_client import ChromaClientService, LoreQueryResult
from apps.timeline.services import CalendarConfig, CalendarService, UniverseTime
from apps.universes.models import Universe


# System prompt template - static core instructions
SYSTEM_PROMPT_TEMPLATE = """You are a skilled and creative Dungeon Master for a single-player tabletop RPG using SRD 5.2 rules.

## Core Responsibilities
1. Narrate the world, NPCs, and events engagingly
2. Request dice rolls when mechanics are needed - NEVER roll dice yourself
3. Respect the player's agency and choices
4. Maintain consistency with established lore
5. Enforce the content rating guidelines

## Output Format
You MUST respond in exactly this format:

DM_TEXT:
<Your narrative response for the player. Describe what happens, what NPCs say, what the player sees/hears. End with options or a prompt for the player's next action.>

DM_JSON:
{
  "roll_requests": [
    {
      "id": "r1",
      "type": "<ability_check|saving_throw|attack_roll|damage_roll>",
      "ability": "<str|dex|con|int|wis|cha>",
      "skill": "<skill_name or null>",
      "dc": <number or null for attacks>,
      "advantage": "<none|advantage|disadvantage>",
      "reason": "<brief explanation>"
    }
  ],
  "patches": [
    {
      "op": "<replace|add|remove|advance_time>",
      "path": "<JSON path like /party/player/hp/current>",
      "value": <new value>
    }
  ],
  "lore_deltas": [
    {
      "type": "<hard_canon|soft_lore>",
      "text": "<new lore fact>",
      "tags": ["tag1", "tag2"],
      "time_ref": {"year": Y, "month": M, "day": D}
    }
  ]
}

## Rules
- If no rolls are needed, leave roll_requests empty: []
- If no state changes, leave patches empty: []
- If no new lore, leave lore_deltas empty: []
- ALWAYS include both DM_TEXT and DM_JSON sections
- Keep narrative engaging but concise
- For soft_lore: rumors, legends, NPC opinions (can be contradicted later)
- For hard_canon: only use when establishing verified facts (rare)

## Roll Types
- ability_check: skill checks, ability checks
- saving_throw: saving throws against effects
- attack_roll: melee or ranged attacks
- damage_roll: damage after a hit

## State Patches
Valid paths include:
- /party/player/hp/current - Current HP
- /party/player/conditions - Active conditions array
- /party/player/resources/spell_slots/{level}/used - Spell slots used
- /world/npcs/{npc_id}/status - NPC status
- /world/npcs/{npc_id}/attitude - NPC attitude toward player
- /world/quests/{quest_id}/stage - Quest progress
- /world/global_flags/{flag} - World state flags

## Time Advancement
Use advance_time patch when time passes:
{"op": "advance_time", "value": {"minutes": 10}}
{"op": "advance_time", "value": {"hours": 1}}
{"op": "advance_time", "value": {"days": 1}}

## SRD Compliance
- Only reference SRD 5.2 content unless homebrew is explicitly allowed
- No Wizards of the Coast Product Identity (named settings, unique monsters not in SRD)
- All mechanics must follow SRD rules
"""

# Content rating guidelines
RATING_GUIDELINES = {
    "G": """Content Rating: G (General Audiences)
- No violence beyond mild cartoon-style conflict
- No romance beyond friendship
- No substance use
- Family-friendly language only
- Focus on adventure, puzzles, and exploration""",
    "PG": """Content Rating: PG (Parental Guidance)
- Mild fantasy violence (combat without graphic description)
- Light romantic themes (hand-holding, implied affection)
- No substance abuse
- Mild language acceptable
- Themes of danger and mild peril""",
    "PG13": """Content Rating: PG-13
- Moderate fantasy violence (combat with consequences)
- Romantic subplots allowed (kissing, dating)
- Alcohol/tavern culture acceptable
- Moderate language
- Themes of death, loss, and moral complexity""",
    "R": """Content Rating: R (Restricted)
- Intense violence and combat
- Adult romantic themes (fade-to-black for intimate scenes)
- Substance use portrayed realistically
- Strong language
- Dark themes, horror elements, mature subject matter""",
    "NC17": """Content Rating: NC-17 (Adults Only)
- Graphic violence
- Explicit romantic content allowed
- All substance use
- Unrestricted language
- Extremely dark or disturbing themes
Note: Still prohibited: CSAM, graphic torture, real-world hate speech""",
}

# Failure style instructions
FAILURE_STYLE_INSTRUCTIONS = {
    "fail_forward": """Failure Style: Fail Forward
When the player fails a roll:
- The failure should still advance the story
- Introduce complications rather than dead ends
- "Yes, but..." or "No, and..." outcomes
- Keep the narrative momentum going
- Failure reveals information or opens new paths""",
    "strict_raw": """Failure Style: Strict RAW (Rules As Written)
When the player fails a roll:
- Apply the mechanical consequences as written
- Failed stealth means being detected
- Failed persuasion means the NPC refuses
- Death saves and conditions apply strictly
- Player must find alternative solutions""",
}


@dataclass
class SystemPrompt:
    """The static system prompt."""

    content: str = SYSTEM_PROMPT_TEMPLATE


@dataclass
class UniversePrompt:
    """Dynamic universe context prompt."""

    universe_name: str
    description: str
    tone_profile: dict = field(default_factory=dict)
    rules_profile: dict = field(default_factory=dict)
    current_time: UniverseTime | None = None
    key_events: list[dict] = field(default_factory=list)
    homebrew_allowed: bool = False

    def build(self) -> str:
        """Build the universe prompt string."""
        parts = [
            f"## Universe: {self.universe_name}",
            "",
            self.description,
            "",
        ]

        # Tone sliders
        if self.tone_profile:
            parts.append("### Tone")
            for key, value in self.tone_profile.items():
                parts.append(f"- {key}: {value}")
            parts.append("")

        # Rules
        if self.rules_profile:
            parts.append("### Rules Modifications")
            for key, value in self.rules_profile.items():
                parts.append(f"- {key}: {value}")
            parts.append("")

        # Current time
        if self.current_time:
            calendar_service = CalendarService()
            formatted = calendar_service.format_time(self.current_time)
            parts.append(f"### Current Universe Time")
            parts.append(formatted)
            parts.append("")

        # Key events
        if self.key_events:
            parts.append("### Timeline - Key Events")
            for event in self.key_events:
                name = event.get("name", "Unknown")
                year = event.get("time", {}).get("year", "?")
                parts.append(f"- Year {year}: {name}")
            parts.append("")

        # Homebrew
        if self.homebrew_allowed:
            parts.append("### Homebrew")
            parts.append("Homebrew content is ALLOWED in this universe.")
            parts.append("You may reference universe-specific items, monsters, and mechanics.")
        else:
            parts.append("### Homebrew")
            parts.append("Homebrew is NOT allowed. Use only SRD 5.2 content.")

        return "\n".join(parts)

    @classmethod
    def from_universe(cls, universe: Universe) -> "UniversePrompt":
        """Create from a Universe model instance."""
        current_time = None
        if universe.current_universe_time:
            current_time = UniverseTime.from_dict(universe.current_universe_time)

        # Extract key events from calendar profile
        key_events = (universe.calendar_profile_json or {}).get("timeline_anchors", [])

        # Check if homebrew is allowed
        rules = universe.rules_profile_json or {}
        homebrew_allowed = rules.get("homebrew_allowed", False)

        return cls(
            universe_name=universe.name,
            description=universe.description or "",
            tone_profile=universe.tone_profile_json or {},
            rules_profile=rules,
            current_time=current_time,
            key_events=key_events[:10],  # Limit to 10 most recent
            homebrew_allowed=homebrew_allowed,
        )


@dataclass
class CampaignPrompt:
    """Dynamic campaign context prompt."""

    campaign_title: str
    mode: str  # "scenario" or "campaign"
    target_length: str
    failure_style: str
    content_rating: str
    character_summary: str
    current_state: dict = field(default_factory=dict)
    recent_turns: list[dict] = field(default_factory=list)
    active_quests: list[dict] = field(default_factory=list)

    def build(self) -> str:
        """Build the campaign prompt string."""
        parts = [
            f"## Campaign: {self.campaign_title}",
            f"Mode: {self.mode.title()} | Target Length: {self.target_length}",
            "",
        ]

        # Content rating
        rating_text = RATING_GUIDELINES.get(self.content_rating, RATING_GUIDELINES["PG13"])
        parts.append(rating_text)
        parts.append("")

        # Failure style
        failure_text = FAILURE_STYLE_INSTRUCTIONS.get(
            self.failure_style, FAILURE_STYLE_INSTRUCTIONS["fail_forward"]
        )
        parts.append(failure_text)
        parts.append("")

        # Character
        parts.append("### Player Character")
        parts.append(self.character_summary)
        parts.append("")

        # Current state summary
        if self.current_state:
            parts.append("### Current State")
            hp = self.current_state.get("party", {}).get("player", {}).get("hp", {})
            if hp:
                parts.append(f"- HP: {hp.get('current', '?')}/{hp.get('max', '?')}")

            conditions = (
                self.current_state.get("party", {}).get("player", {}).get("conditions", [])
            )
            if conditions:
                parts.append(f"- Conditions: {', '.join(conditions)}")
            else:
                parts.append("- Conditions: None")

            location = self.current_state.get("world", {}).get("location_id", "unknown")
            parts.append(f"- Location: {location}")
            parts.append("")

        # Active quests
        if self.active_quests:
            parts.append("### Active Quests")
            for quest in self.active_quests:
                quest_id = quest.get("quest_id", "unknown")
                stage = quest.get("stage", 0)
                parts.append(f"- {quest_id}: Stage {stage}")
            parts.append("")

        # Recent turns recap
        if self.recent_turns:
            parts.append("### Recent Events (Last Few Turns)")
            for turn in self.recent_turns[-5:]:  # Last 5 turns
                turn_idx = turn.get("turn_index", "?")
                user_input = turn.get("user_input", "")[:100]
                parts.append(f"Turn {turn_idx}: Player said: \"{user_input}...\"")
            parts.append("")

        return "\n".join(parts)

    @classmethod
    def from_campaign(
        cls,
        campaign: Campaign,
        current_state: dict,
        recent_turns: list[TurnEvent] | None = None,
    ) -> "CampaignPrompt":
        """Create from a Campaign model instance."""
        # Build character summary
        character = campaign.character_sheet
        char_summary = (
            f"{character.name}, Level {character.level} "
            f"{character.species} {character.character_class}"
        )

        # Extract active quests from state
        active_quests = current_state.get("world", {}).get("quests", [])

        # Convert turns to dicts
        turn_dicts = []
        if recent_turns:
            for turn in recent_turns:
                turn_dicts.append({
                    "turn_index": turn.turn_index,
                    "user_input": turn.user_input_text,
                })

        return cls(
            campaign_title=campaign.title,
            mode=campaign.mode,
            target_length=campaign.target_length,
            failure_style=campaign.failure_style,
            content_rating=campaign.content_rating,
            character_summary=char_summary,
            current_state=current_state,
            recent_turns=turn_dicts,
            active_quests=active_quests,
        )


@dataclass
class LoreInjection:
    """Lore context to inject into prompts."""

    hard_canon_chunks: list[str] = field(default_factory=list)
    soft_lore_chunks: list[str] = field(default_factory=list)

    def build(self) -> str:
        """Build the lore injection string."""
        if not self.hard_canon_chunks and not self.soft_lore_chunks:
            return ""

        parts = ["## Relevant Lore", ""]

        if self.hard_canon_chunks:
            parts.append("### Established Facts (Hard Canon)")
            parts.append("These facts are TRUE and must not be contradicted:")
            for chunk in self.hard_canon_chunks:
                parts.append(f"- {chunk}")
            parts.append("")

        if self.soft_lore_chunks:
            parts.append("### Rumors & Legends (Soft Lore)")
            parts.append("These may be true, partially true, or false rumors:")
            for chunk in self.soft_lore_chunks:
                parts.append(f"- {chunk}")
            parts.append("")

        return "\n".join(parts)

    @classmethod
    def from_query_result(
        cls,
        hard_canon_result: LoreQueryResult | None,
        soft_lore_result: LoreQueryResult | None,
    ) -> "LoreInjection":
        """Create from ChromaDB query results."""
        hard_canon = []
        soft_lore = []

        if hard_canon_result:
            for result in hard_canon_result.results:
                hard_canon.append(result.text[:500])  # Truncate long chunks

        if soft_lore_result:
            for result in soft_lore_result.results:
                soft_lore.append(result.text[:500])

        return cls(
            hard_canon_chunks=hard_canon,
            soft_lore_chunks=soft_lore,
        )


class PromptBuilder:
    """
    Builds complete prompts for the LLM DM.

    Combines system prompt, universe context, campaign context,
    and relevant lore into a coherent prompt.
    """

    def __init__(self, chroma_service: ChromaClientService | None = None):
        """Initialize the prompt builder."""
        self.chroma_service = chroma_service or ChromaClientService()

    def build_system_prompt(self) -> str:
        """Get the system prompt."""
        return SYSTEM_PROMPT_TEMPLATE

    def build_universe_prompt(self, universe: Universe) -> str:
        """Build universe context prompt."""
        return UniversePrompt.from_universe(universe).build()

    def build_campaign_prompt(
        self,
        campaign: Campaign,
        current_state: dict,
        recent_turns: list[TurnEvent] | None = None,
    ) -> str:
        """Build campaign context prompt."""
        return CampaignPrompt.from_campaign(
            campaign, current_state, recent_turns
        ).build()

    def build_lore_injection(
        self,
        universe_id: str,
        user_input: str,
        current_context: str = "",
        top_k: int = 5,
    ) -> str:
        """
        Build lore injection based on user input and context.

        Args:
            universe_id: UUID of the universe
            user_input: The user's current input
            current_context: Additional context for the query
            top_k: Number of lore chunks to retrieve

        Returns:
            Lore injection string
        """
        # Combine user input and context for semantic search
        query = f"{user_input} {current_context}".strip()

        # Query hard canon
        hard_canon_result = self.chroma_service.query(
            universe_id=universe_id,
            query_text=query,
            top_k=top_k,
            chunk_type="hard_canon",
        )

        # Query soft lore
        soft_lore_result = self.chroma_service.query(
            universe_id=universe_id,
            query_text=query,
            top_k=top_k,
            chunk_type="soft_lore",
        )

        injection = LoreInjection.from_query_result(hard_canon_result, soft_lore_result)
        return injection.build()

    def build_full_context(
        self,
        campaign: Campaign,
        current_state: dict,
        user_input: str,
        recent_turns: list[TurnEvent] | None = None,
    ) -> str:
        """
        Build the complete context for an LLM call.

        Args:
            campaign: The campaign
            current_state: Current canonical state
            user_input: User's input for this turn
            recent_turns: Recent turn history

        Returns:
            Complete context string (for assistant message)
        """
        parts = []

        # Universe context
        universe = campaign.universe
        parts.append(self.build_universe_prompt(universe))
        parts.append("")

        # Campaign context
        parts.append(self.build_campaign_prompt(campaign, current_state, recent_turns))
        parts.append("")

        # Lore injection
        lore = self.build_lore_injection(
            universe_id=str(universe.id),
            user_input=user_input,
            current_context=current_state.get("world", {}).get("location_id", ""),
        )
        if lore:
            parts.append(lore)

        return "\n".join(parts)

    def build_repair_prompt(self, error_message: str, original_response: str) -> str:
        """
        Build a repair prompt for when LLM output validation fails.

        Args:
            error_message: Description of the validation error
            original_response: The original LLM response that failed

        Returns:
            Repair prompt string
        """
        return f"""Your previous response had validation errors that need to be fixed.

## Error
{error_message}

## Your Previous Response
{original_response}

## Instructions
Please provide a corrected response that:
1. Fixes the validation errors
2. Maintains the same narrative intent
3. Uses the correct output format (DM_TEXT and DM_JSON)

Respond with the corrected output only."""
