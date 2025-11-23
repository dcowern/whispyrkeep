"""
Campaign State Service.

Manages campaign state snapshots and replay functionality.

Based on SYSTEM_DESIGN.md:
- Snapshot-based state storage for fast loads
- Event-sourced replay for state reconstruction
- Hash verification for integrity
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from django.db import transaction

from apps.campaigns.models import Campaign, CanonicalCampaignState, TurnEvent
from apps.characters.models import CharacterSheet

logger = logging.getLogger(__name__)


@dataclass
class CampaignState:
    """Represents the full state of a campaign at a point in time."""

    campaign_id: str
    turn_index: int
    character_state: dict = field(default_factory=dict)
    world_state: dict = field(default_factory=dict)
    universe_time: dict = field(default_factory=dict)
    rules_context: dict = field(default_factory=dict)
    global_flags: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "campaign_id": self.campaign_id,
            "turn_index": self.turn_index,
            "character_state": self.character_state,
            "world_state": self.world_state,
            "universe_time": self.universe_time,
            "rules_context": self.rules_context,
            "global_flags": self.global_flags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CampaignState":
        """Create from dictionary."""
        return cls(
            campaign_id=data.get("campaign_id", ""),
            turn_index=data.get("turn_index", 0),
            character_state=data.get("character_state", {}),
            world_state=data.get("world_state", {}),
            universe_time=data.get("universe_time", {}),
            rules_context=data.get("rules_context", {}),
            global_flags=data.get("global_flags", {}),
        )

    def compute_hash(self) -> str:
        """Compute deterministic hash of state."""
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass
class StateReplayResult:
    """Result of state replay operation."""

    success: bool
    state: Optional[CampaignState] = None
    turn_index: int = 0
    from_snapshot: bool = False
    turns_replayed: int = 0
    errors: list[str] = field(default_factory=list)


class StateService:
    """
    Service for managing campaign state.

    Provides:
    - Initial state generation
    - State snapshot storage
    - State replay from turns
    - State hash verification

    Usage:
        service = StateService()
        state = service.get_current_state(campaign)
        service.save_snapshot(campaign, state)
    """

    # Snapshot every N turns for fast recovery
    SNAPSHOT_INTERVAL = 10

    def get_initial_state(self, campaign: Campaign) -> CampaignState:
        """
        Generate initial state for a new campaign.

        Args:
            campaign: The campaign to generate state for

        Returns:
            Initial CampaignState
        """
        character = campaign.character_sheet
        universe = campaign.universe

        # Build character state from sheet
        character_state = self._build_character_state(character)

        # Build rules context
        rules_context = {
            "srd_version": "5.2",
            "homebrew_allowed": True,
            "failure_style": campaign.failure_style,
            "content_rating": campaign.content_rating,
        }

        # Merge with universe rules profile
        if universe.rules_profile_json:
            rules_context.update(universe.rules_profile_json)

        # Initial universe time
        universe_time = campaign.start_universe_time or universe.current_universe_time

        return CampaignState(
            campaign_id=str(campaign.id),
            turn_index=0,
            character_state=character_state,
            world_state={
                "locations": {},
                "npcs": {},
                "factions": {},
            },
            universe_time=universe_time,
            rules_context=rules_context,
            global_flags={},
        )

    def _build_character_state(self, character: CharacterSheet) -> dict:
        """Build character state from sheet."""
        # Calculate HP if not stored
        con_mod = (character.ability_scores_json.get("con", 10) - 10) // 2
        base_hp = 10 + (character.level * (5 + con_mod))  # Simplified calculation

        return {
            "id": str(character.id),
            "name": character.name,
            "level": character.level,
            "class": character.character_class,
            "subclass": character.subclass,
            "species": character.species,
            "background": character.background,
            "ability_scores": character.ability_scores_json,
            "hp": {
                "current": base_hp,
                "max": base_hp,
                "temp": 0,
            },
            "conditions": [],
            "inventory": character.inventory_json,
            "features": character.features_json,
            "spell_slots": {},
            "resources": {},
        }

    def get_current_state(self, campaign: Campaign) -> CampaignState:
        """
        Get the current state of a campaign.

        First tries to load from latest snapshot, then replays any
        turns after the snapshot.

        Args:
            campaign: The campaign

        Returns:
            Current CampaignState
        """
        result = self.replay_to_turn(campaign, turn_index=None)

        if result.success and result.state:
            return result.state

        # If replay fails, return initial state
        return self.get_initial_state(campaign)

    def replay_to_turn(
        self,
        campaign: Campaign,
        turn_index: Optional[int] = None,
    ) -> StateReplayResult:
        """
        Replay campaign state to a specific turn.

        Args:
            campaign: The campaign
            turn_index: Target turn index (None = latest)

        Returns:
            StateReplayResult with reconstructed state
        """
        # Find target turn index
        if turn_index is None:
            latest_turn = campaign.turns.order_by("-turn_index").first()
            turn_index = latest_turn.turn_index if latest_turn else 0

        # Find nearest snapshot
        snapshot = CanonicalCampaignState.objects.filter(
            campaign=campaign,
            turn_index__lte=turn_index,
        ).order_by("-turn_index").first()

        if snapshot:
            # Start from snapshot
            state = CampaignState.from_dict(snapshot.state_json)
            from_snapshot = True
            start_turn = snapshot.turn_index + 1
        else:
            # Start from initial state
            state = self.get_initial_state(campaign)
            from_snapshot = False
            start_turn = 1

        # Replay turns from start to target
        turns = campaign.turns.filter(
            turn_index__gte=start_turn,
            turn_index__lte=turn_index,
        ).order_by("turn_index")

        turns_replayed = 0
        errors = []

        for turn in turns:
            try:
                state = self._apply_turn_patch(state, turn)
                turns_replayed += 1
            except Exception as e:
                logger.error(f"Failed to apply turn {turn.turn_index}: {e}")
                errors.append(f"Turn {turn.turn_index}: {str(e)}")

        state.turn_index = turn_index

        return StateReplayResult(
            success=len(errors) == 0,
            state=state,
            turn_index=turn_index,
            from_snapshot=from_snapshot,
            turns_replayed=turns_replayed,
            errors=errors,
        )

    def _apply_turn_patch(
        self,
        state: CampaignState,
        turn: TurnEvent,
    ) -> CampaignState:
        """
        Apply a turn's state patch to the state.

        Args:
            state: Current state
            turn: Turn event with patch

        Returns:
            Updated state
        """
        patch = turn.state_patch_json

        if not patch:
            return state

        # Apply character state patches
        if "character" in patch:
            state.character_state = self._deep_merge(
                state.character_state,
                patch["character"],
            )

        # Apply world state patches
        if "world" in patch:
            state.world_state = self._deep_merge(
                state.world_state,
                patch["world"],
            )

        # Apply global flags
        if "global_flags" in patch:
            state.global_flags = self._deep_merge(
                state.global_flags,
                patch["global_flags"],
            )

        # Update universe time
        if turn.universe_time_after_turn:
            state.universe_time = turn.universe_time_after_turn

        return state

    def _deep_merge(self, base: dict, update: dict) -> dict:
        """Deep merge update into base."""
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def save_snapshot(
        self,
        campaign: Campaign,
        state: CampaignState,
        force: bool = False,
    ) -> Optional[CanonicalCampaignState]:
        """
        Save a state snapshot.

        Args:
            campaign: The campaign
            state: State to save
            force: If True, save regardless of interval

        Returns:
            Created snapshot or None if not due for snapshot
        """
        # Only save at intervals unless forced
        if not force and state.turn_index % self.SNAPSHOT_INTERVAL != 0:
            return None

        # Check if snapshot already exists
        existing = CanonicalCampaignState.objects.filter(
            campaign=campaign,
            turn_index=state.turn_index,
        ).exists()

        if existing and not force:
            return None

        # Create snapshot
        snapshot = CanonicalCampaignState.objects.create(
            campaign=campaign,
            turn_index=state.turn_index,
            state_json=state.to_dict(),
        )

        logger.info(f"Saved state snapshot for campaign {campaign.id} at turn {state.turn_index}")
        return snapshot

    def verify_state_hash(
        self,
        campaign: Campaign,
        turn_index: int,
        expected_hash: str,
    ) -> bool:
        """
        Verify state hash matches expected value.

        Args:
            campaign: The campaign
            turn_index: Turn to verify
            expected_hash: Expected state hash

        Returns:
            True if hash matches
        """
        result = self.replay_to_turn(campaign, turn_index)

        if not result.success or not result.state:
            return False

        actual_hash = result.state.compute_hash()
        return actual_hash == expected_hash

    def delete_snapshots_after_turn(
        self,
        campaign: Campaign,
        turn_index: int,
    ) -> int:
        """
        Delete snapshots after a turn index (for rewind).

        Args:
            campaign: The campaign
            turn_index: Delete snapshots after this turn

        Returns:
            Number of snapshots deleted
        """
        deleted, _ = CanonicalCampaignState.objects.filter(
            campaign=campaign,
            turn_index__gt=turn_index,
        ).delete()

        return deleted

    def get_state_for_response(self, campaign: Campaign) -> dict:
        """
        Get state formatted for API response.

        Args:
            campaign: The campaign

        Returns:
            Dict formatted for API response
        """
        state = self.get_current_state(campaign)
        snapshot = CanonicalCampaignState.objects.filter(
            campaign=campaign,
            turn_index=state.turn_index,
        ).exists()

        return {
            "campaign_id": str(campaign.id),
            "turn_index": state.turn_index,
            "state": state.to_dict(),
            "character_state": state.character_state,
            "universe_time": state.universe_time,
            "is_snapshot": snapshot,
        }
