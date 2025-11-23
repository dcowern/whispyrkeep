"""
Turn Engine Service.

Orchestrates the two-stage turn flow:
1. LLM generates turn proposal with roll requests
2. Backend executes mechanics
3. LLM generates final narration with resolved rolls
4. Turn is persisted

Tickets: 8.2.1, 8.2.2, 8.2.3, 8.3.2

Based on SYSTEM_DESIGN.md section 8.2 Turn Flow.
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum

from apps.campaigns.models import Campaign, TurnEvent
from apps.lore.services.chroma_client import ChromaClientService
from apps.timeline.services import CalendarService, TimeDelta, UniverseTime

from .llm_client import LLMClient, LLMClientConfig, LLMError, Message
from .prompt_builder import PromptBuilder
from .state_service import CampaignState, StateService
from .validation import LLMOutputValidator, ValidationResult

logger = logging.getLogger(__name__)


class TurnPhase(str, Enum):
    """Phases of turn processing."""

    INITIALIZED = "initialized"
    CONTEXT_BUILT = "context_built"
    PROPOSAL_RECEIVED = "proposal_received"
    MECHANICS_EXECUTED = "mechanics_executed"
    FINAL_RESPONSE = "final_response"
    VALIDATED = "validated"
    PERSISTED = "persisted"
    FAILED = "failed"


@dataclass
class RollResult:
    """Result of a dice roll."""

    roll_id: str
    roll_type: str
    roll_value: int
    modifier: int
    total: int
    success: bool | None = None  # For checks/saves with DC
    dc: int | None = None
    advantage_state: str = "none"
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "roll_id": self.roll_id,
            "roll_type": self.roll_type,
            "roll_value": self.roll_value,
            "modifier": self.modifier,
            "total": self.total,
            "success": self.success,
            "dc": self.dc,
            "advantage_state": self.advantage_state,
            "details": self.details,
        }


@dataclass
class TurnRequest:
    """Request to process a turn."""

    campaign: Campaign
    user_input: str
    llm_config: LLMClientConfig

    @property
    def campaign_id(self) -> str:
        return str(self.campaign.id)


@dataclass
class TurnResult:
    """Result of processing a turn."""

    success: bool
    phase: TurnPhase
    dm_text: str = ""
    roll_results: list[RollResult] = field(default_factory=list)
    state_patches: list[dict] = field(default_factory=list)
    lore_deltas: list[dict] = field(default_factory=list)
    turn_event: TurnEvent | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "phase": self.phase.value,
            "dm_text": self.dm_text,
            "roll_results": [r.to_dict() for r in self.roll_results],
            "turn_event_id": str(self.turn_event.id) if self.turn_event else None,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class LLMResponseParser:
    """Parses LLM responses into structured data."""

    DM_TEXT_PATTERN = re.compile(r"DM_TEXT:\s*(.*?)(?=DM_JSON:|$)", re.DOTALL)
    DM_JSON_PATTERN = re.compile(r"DM_JSON:\s*(\{.*\})", re.DOTALL)

    def parse(self, response: str) -> tuple[str, dict, list[str]]:
        """
        Parse LLM response into text and JSON components.

        Args:
            response: Raw LLM response

        Returns:
            Tuple of (dm_text, dm_json, errors)
        """
        errors = []
        dm_text = ""
        dm_json = {}

        # Extract DM_TEXT
        text_match = self.DM_TEXT_PATTERN.search(response)
        if text_match:
            dm_text = text_match.group(1).strip()
        else:
            errors.append("Could not find DM_TEXT section in response")

        # Extract DM_JSON
        json_match = self.DM_JSON_PATTERN.search(response)
        if json_match:
            json_str = json_match.group(1)
            try:
                dm_json = json.loads(json_str)
            except json.JSONDecodeError as e:
                errors.append(f"Failed to parse DM_JSON: {e}")
        else:
            # Try to find any JSON object in the response
            try:
                # Look for JSON-like content
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    dm_json = json.loads(json_str)
                else:
                    errors.append("Could not find DM_JSON section in response")
            except json.JSONDecodeError:
                errors.append("Could not find valid JSON in response")

        return dm_text, dm_json, errors


class MechanicsExecutor:
    """Executes game mechanics (dice rolls, etc.)."""

    def __init__(self, seed: int | None = None):
        """
        Initialize the executor.

        Args:
            seed: Optional seed for deterministic rolls (for testing)
        """
        self._seed = seed
        self._rng_state = seed

    def _roll_d20(self, advantage: str = "none") -> tuple[int, dict]:
        """
        Roll a d20 with optional advantage/disadvantage.

        Returns:
            Tuple of (result, details)
        """
        import random

        if self._rng_state is not None:
            random.seed(self._rng_state)
            self._rng_state += 1

        roll1 = random.randint(1, 20)

        if advantage == "none":
            return roll1, {"rolls": [roll1]}

        roll2 = random.randint(1, 20)

        result = max(roll1, roll2) if advantage == "advantage" else min(roll1, roll2)

        return result, {"rolls": [roll1, roll2], "used": result}

    def _roll_dice(self, expression: str) -> tuple[int, dict]:
        """
        Roll dice from an expression like "2d6+3".

        Returns:
            Tuple of (total, details)
        """
        import random

        if self._rng_state is not None:
            random.seed(self._rng_state)
            self._rng_state += 1

        # Parse expression
        match = re.match(r"(\d+)d(\d+)(?:\+(\d+))?", expression)
        if not match:
            return 0, {"error": f"Invalid dice expression: {expression}"}

        num_dice = int(match.group(1))
        die_size = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

        rolls = [random.randint(1, die_size) for _ in range(num_dice)]
        total = sum(rolls) + modifier

        return total, {"rolls": rolls, "modifier": modifier}

    def execute_roll(
        self,
        roll_spec: dict,
        character_state: dict,
    ) -> RollResult:
        """
        Execute a single roll request.

        Args:
            roll_spec: Roll specification from LLM
            character_state: Current character state for modifiers

        Returns:
            RollResult
        """
        roll_id = roll_spec.get("id", "unknown")
        roll_type = roll_spec.get("type", "ability_check")
        advantage = roll_spec.get("advantage", "none")

        # Get ability modifier
        ability = roll_spec.get("ability", "str")
        abilities = character_state.get("abilities", {})
        ability_score = abilities.get(ability, 10)
        ability_mod = (ability_score - 10) // 2

        # Get proficiency bonus (simplified)
        level = character_state.get("level", 1)
        prof_bonus = 2 + (level - 1) // 4

        # Calculate modifier based on roll type
        if roll_type in ("ability_check", "saving_throw"):
            # Check for skill proficiency
            skill = roll_spec.get("skill")
            skills = character_state.get("skills", {})

            modifier = ability_mod + prof_bonus if skill and skill in skills else ability_mod

            # Roll
            roll_value, details = self._roll_d20(advantage)
            total = roll_value + modifier

            # Check against DC
            dc = roll_spec.get("dc")
            success = None
            if dc is not None:
                success = total >= dc

            return RollResult(
                roll_id=roll_id,
                roll_type=roll_type,
                roll_value=roll_value,
                modifier=modifier,
                total=total,
                success=success,
                dc=dc,
                advantage_state=advantage,
                details=details,
            )

        elif roll_type == "attack_roll":
            # Attack roll
            modifier = ability_mod + prof_bonus
            roll_value, details = self._roll_d20(advantage)
            total = roll_value + modifier

            return RollResult(
                roll_id=roll_id,
                roll_type=roll_type,
                roll_value=roll_value,
                modifier=modifier,
                total=total,
                advantage_state=advantage,
                details=details,
            )

        elif roll_type == "damage_roll":
            # Damage roll
            dice_expr = roll_spec.get("dice", "1d6")
            total, details = self._roll_dice(dice_expr)

            return RollResult(
                roll_id=roll_id,
                roll_type=roll_type,
                roll_value=total,
                modifier=0,
                total=total,
                details=details,
            )

        else:
            return RollResult(
                roll_id=roll_id,
                roll_type=roll_type,
                roll_value=0,
                modifier=0,
                total=0,
                details={"error": f"Unknown roll type: {roll_type}"},
            )

    def execute_rolls(
        self,
        roll_specs: list[dict],
        character_state: dict,
    ) -> list[RollResult]:
        """Execute multiple rolls."""
        return [self.execute_roll(spec, character_state) for spec in roll_specs]


class TurnEngine:
    """
    Orchestrates the complete turn flow.

    Two-stage turn processing:
    1. Build context and send to LLM for turn proposal
    2. Execute mechanics on roll requests
    3. Send results back to LLM for final narration
    4. Validate and persist the turn
    """

    MAX_REPAIR_ATTEMPTS = 2

    def __init__(
        self,
        state_service: StateService | None = None,
        prompt_builder: PromptBuilder | None = None,
        chroma_service: ChromaClientService | None = None,
        mechanics_seed: int | None = None,
    ):
        """Initialize the turn engine."""
        self.state_service = state_service or StateService()
        self.prompt_builder = prompt_builder or PromptBuilder(chroma_service)
        self.parser = LLMResponseParser()
        self.mechanics = MechanicsExecutor(seed=mechanics_seed)
        self.calendar_service = CalendarService()

    def process_turn(self, request: TurnRequest) -> TurnResult:
        """
        Process a complete turn.

        Args:
            request: TurnRequest with campaign, user input, and LLM config

        Returns:
            TurnResult with outcome
        """
        result = TurnResult(success=False, phase=TurnPhase.INITIALIZED)

        try:
            # Get current state
            current_state = self.state_service.get_current_state(request.campaign)
            character_state = current_state.character_state

            # Get recent turns for context
            recent_turns = list(
                request.campaign.turns.order_by("-turn_index")[:10]
            )
            recent_turns.reverse()

            # Build context
            result.phase = TurnPhase.CONTEXT_BUILT

            # Phase 1: Get turn proposal from LLM
            proposal_result = self._get_turn_proposal(
                request, current_state.to_dict(), recent_turns
            )
            if not proposal_result["success"]:
                result.errors.extend(proposal_result.get("errors", []))
                result.phase = TurnPhase.FAILED
                return result

            result.phase = TurnPhase.PROPOSAL_RECEIVED
            dm_text = proposal_result["dm_text"]
            dm_json = proposal_result["dm_json"]

            # Phase 2: Execute mechanics
            roll_requests = dm_json.get("roll_requests", [])
            roll_results = self.mechanics.execute_rolls(roll_requests, character_state)
            result.roll_results = roll_results
            result.phase = TurnPhase.MECHANICS_EXECUTED

            # Phase 3: Get final narration if there were rolls
            if roll_results:
                final_result = self._get_final_narration(
                    request, dm_text, roll_results, current_state.to_dict()
                )
                if final_result["success"]:
                    dm_text = final_result["dm_text"]
                    # Merge any additional patches
                    final_json = final_result.get("dm_json", {})
                    dm_json["patches"] = dm_json.get("patches", []) + final_json.get(
                        "patches", []
                    )

            result.dm_text = dm_text
            result.state_patches = dm_json.get("patches", [])
            result.lore_deltas = dm_json.get("lore_deltas", [])
            result.phase = TurnPhase.FINAL_RESPONSE

            # Phase 4: Validate output
            validator = LLMOutputValidator(current_state.to_dict())
            validation = validator.validate_json_output(dm_json)

            if not validation.valid:
                # Attempt repair
                repair_result = self._attempt_repair(
                    request, dm_text, dm_json, validation, current_state.to_dict()
                )
                if repair_result["success"]:
                    dm_text = repair_result["dm_text"]
                    dm_json = repair_result["dm_json"]
                    result.dm_text = dm_text
                    result.state_patches = dm_json.get("patches", [])
                    result.lore_deltas = dm_json.get("lore_deltas", [])
                else:
                    result.errors.extend(validation.errors)
                    result.phase = TurnPhase.FAILED
                    return result

            result.warnings.extend(validation.warnings)
            result.phase = TurnPhase.VALIDATED

            # Phase 5: Persist the turn
            turn_event = self._persist_turn(
                request,
                current_state,
                dm_text,
                dm_json,
                roll_results,
            )
            result.turn_event = turn_event
            result.phase = TurnPhase.PERSISTED
            result.success = True

        except LLMError as e:
            logger.error(f"LLM error during turn: {e}")
            result.errors.append(f"LLM error: {e.message}")
            result.phase = TurnPhase.FAILED

        except Exception as e:
            logger.exception(f"Unexpected error during turn: {e}")
            result.errors.append(f"Unexpected error: {str(e)}")
            result.phase = TurnPhase.FAILED

        return result

    def _get_turn_proposal(
        self,
        request: TurnRequest,
        current_state: dict,
        recent_turns: list[TurnEvent],
    ) -> dict:
        """Get the initial turn proposal from LLM."""
        # Build messages
        system_prompt = self.prompt_builder.build_system_prompt()
        context = self.prompt_builder.build_full_context(
            campaign=request.campaign,
            current_state=current_state,
            user_input=request.user_input,
            recent_turns=recent_turns,
        )

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="assistant", content=f"[Context]\n{context}"),
            Message(role="user", content=request.user_input),
        ]

        # Call LLM
        with LLMClient(request.llm_config) as client:
            response = client.chat(messages, temperature=0.7)

        # Parse response
        dm_text, dm_json, errors = self.parser.parse(response.content)

        if errors:
            return {"success": False, "errors": errors}

        return {
            "success": True,
            "dm_text": dm_text,
            "dm_json": dm_json,
        }

    def _get_final_narration(
        self,
        request: TurnRequest,
        proposal_text: str,
        roll_results: list[RollResult],
        current_state: dict,
    ) -> dict:
        """Get final narration after mechanics are resolved."""
        # Format roll results for LLM
        roll_summary = "\n".join(
            f"- {r.roll_id}: Rolled {r.roll_value} + {r.modifier} = {r.total}"
            + (f" vs DC {r.dc}: {'SUCCESS' if r.success else 'FAILURE'}" if r.dc else "")
            for r in roll_results
        )

        system_prompt = self.prompt_builder.build_system_prompt()

        messages = [
            Message(role="system", content=system_prompt),
            Message(
                role="assistant",
                content=f"[Previous proposal]\n{proposal_text}\n\n[Roll Results]\n{roll_summary}",
            ),
            Message(
                role="user",
                content="Based on these roll results, provide the final narrative. "
                "Update any patches based on the actual outcomes.",
            ),
        ]

        with LLMClient(request.llm_config) as client:
            response = client.chat(messages, temperature=0.7)

        dm_text, dm_json, errors = self.parser.parse(response.content)

        if errors:
            # Fall back to proposal text if parsing fails
            return {"success": True, "dm_text": proposal_text, "dm_json": {}}

        return {"success": True, "dm_text": dm_text, "dm_json": dm_json}

    def _attempt_repair(
        self,
        request: TurnRequest,
        dm_text: str,
        dm_json: dict,
        validation: ValidationResult,
        current_state: dict,
    ) -> dict:
        """Attempt to repair invalid LLM output."""
        for attempt in range(self.MAX_REPAIR_ATTEMPTS):
            logger.info(f"Repair attempt {attempt + 1}/{self.MAX_REPAIR_ATTEMPTS}")

            # Build repair prompt
            error_summary = "\n".join(f"- {e}" for e in validation.errors)
            original_response = f"DM_TEXT:\n{dm_text}\n\nDM_JSON:\n{json.dumps(dm_json, indent=2)}"
            repair_prompt = self.prompt_builder.build_repair_prompt(
                error_summary, original_response
            )

            messages = [
                Message(role="system", content=self.prompt_builder.build_system_prompt()),
                Message(role="user", content=repair_prompt),
            ]

            try:
                with LLMClient(request.llm_config) as client:
                    response = client.chat(messages, temperature=0.5)

                new_dm_text, new_dm_json, errors = self.parser.parse(response.content)

                if errors:
                    continue

                # Validate repaired output
                validator = LLMOutputValidator(current_state)
                new_validation = validator.validate_json_output(new_dm_json)

                if new_validation.valid:
                    return {
                        "success": True,
                        "dm_text": new_dm_text,
                        "dm_json": new_dm_json,
                    }

            except LLMError as e:
                logger.warning(f"Repair attempt failed: {e}")
                continue

        return {"success": False}

    def _persist_turn(
        self,
        request: TurnRequest,
        current_state: CampaignState,
        dm_text: str,
        dm_json: dict,
        roll_results: list[RollResult],
    ) -> TurnEvent:
        """Persist the turn to the database."""
        from django.db import transaction

        # Calculate new turn index
        last_turn = request.campaign.turns.order_by("-turn_index").first()
        turn_index = (last_turn.turn_index + 1) if last_turn else 0

        # Apply time advancement if present
        new_time = current_state.to_dict().get("universe_time", {})
        for patch in dm_json.get("patches", []):
            if patch.get("op") == "advance_time":
                delta = TimeDelta.from_dict(patch.get("value", {}))
                current_time = UniverseTime.from_dict(new_time)
                new_time = self.calendar_service.advance_time(current_time, delta).to_dict()

        # Compute state hash
        state_hash = self._compute_state_hash(current_state.to_dict(), dm_json)

        with transaction.atomic():
            # Create turn event
            turn_event = TurnEvent.objects.create(
                campaign=request.campaign,
                turn_index=turn_index,
                user_input_text=request.user_input,
                llm_response_text=dm_text,
                roll_spec_json={"roll_requests": dm_json.get("roll_requests", [])},
                roll_results_json={"results": [r.to_dict() for r in roll_results]},
                state_patch_json={"patches": dm_json.get("patches", [])},
                canonical_state_hash=state_hash,
                lore_deltas_json=dm_json.get("lore_deltas", []),
                universe_time_after_turn=new_time,
            )

            # Update universe time
            universe = request.campaign.universe
            universe.current_universe_time = new_time
            universe.save(update_fields=["current_universe_time", "updated_at"])

            # Maybe save state snapshot
            new_state = self._apply_patches(current_state, dm_json.get("patches", []))
            self.state_service.save_snapshot(request.campaign, new_state)

            # Queue lore deltas for embedding (would use Celery in production)
            self._queue_lore_deltas(
                str(request.campaign.universe.id),
                str(turn_event.id),
                dm_json.get("lore_deltas", []),
            )

        return turn_event

    def _compute_state_hash(self, state: dict, patches: dict) -> str:
        """Compute a hash of the state for integrity verification."""
        combined = json.dumps(
            {"state": state, "patches": patches}, sort_keys=True
        )
        return hashlib.sha256(combined.encode()).hexdigest()

    def _apply_patches(
        self, state: CampaignState, patches: list[dict]
    ) -> CampaignState:
        """Apply patches to create new state (simplified)."""
        # In production, this would properly apply JSON patches
        # For now, return the state with updated turn index
        return CampaignState(
            campaign_id=state.campaign_id,
            turn_index=state.turn_index + 1,
            character_state=state.character_state,
            world_state=state.world_state,
        )

    def _queue_lore_deltas(
        self,
        universe_id: str,
        turn_id: str,
        lore_deltas: list[dict],
    ) -> None:
        """Queue lore deltas for embedding."""
        if not lore_deltas:
            return

        # In production, this would use Celery:
        # from apps.lore.tasks import embed_lore_chunks
        # embed_lore_chunks.delay(universe_id, turn_id, lore_deltas)

        logger.info(f"Queued {len(lore_deltas)} lore deltas for embedding")
