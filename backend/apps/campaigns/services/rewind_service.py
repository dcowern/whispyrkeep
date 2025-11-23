"""
Rewind Service - Handles campaign rewind operations.

Based on SYSTEM_DESIGN.md section 11.2:
- Rewind rewrites history
- All later TurnEvents are deleted (soft-deleted)
- Soft lore from those turns is invalidated
- Universe time resets to snapshot time

Epic 10.0.1 implementation.
"""

import logging
from dataclasses import dataclass, field

from django.db import transaction

from apps.campaigns.models import Campaign, TurnEvent
from apps.campaigns.services.state_service import CampaignState, StateService
from apps.lore.services.lore_service import LoreService

logger = logging.getLogger(__name__)


@dataclass
class RewindResult:
    """Result of a rewind operation."""

    success: bool
    target_turn_index: int = 0
    turns_deleted: int = 0
    snapshots_deleted: int = 0
    lore_chunks_invalidated: int = 0
    new_state: CampaignState | None = None
    errors: list[str] = field(default_factory=list)


class RewindService:
    """
    Service for rewinding campaigns to a previous turn.

    Rewind operations:
    1. Validate target turn exists
    2. Delete all turns after target
    3. Delete state snapshots after target
    4. Invalidate soft lore from deleted turns
    5. Update campaign state

    Usage:
        service = RewindService()
        result = service.rewind_to_turn(campaign, target_turn_index=5)
    """

    def __init__(self):
        """Initialize rewind service."""
        self.state_service = StateService()
        self.lore_service = LoreService()

    def rewind_to_turn(
        self,
        campaign: Campaign,
        target_turn_index: int,
    ) -> RewindResult:
        """
        Rewind a campaign to a specific turn.

        This operation is destructive - all turns after the target
        are permanently deleted, along with their associated lore.

        Args:
            campaign: The campaign to rewind
            target_turn_index: The turn index to rewind to (inclusive).
                               Use 0 to reset to initial state.

        Returns:
            RewindResult with operation details
        """
        errors = []

        # Validate target turn index
        validation_error = self._validate_rewind(campaign, target_turn_index)
        if validation_error:
            return RewindResult(
                success=False,
                target_turn_index=target_turn_index,
                errors=[validation_error],
            )

        try:
            with transaction.atomic():
                # Get turns to delete (after target)
                turns_to_delete = TurnEvent.objects.filter(
                    campaign=campaign,
                    turn_index__gt=target_turn_index,
                ).order_by("turn_index")

                # Collect turn IDs for lore invalidation
                turn_ids_to_invalidate = list(
                    turns_to_delete.values_list("id", flat=True)
                )
                turns_deleted = turns_to_delete.count()

                # Delete turns
                turns_to_delete.delete()

                # Delete state snapshots after target turn
                snapshots_deleted = self.state_service.delete_snapshots_after_turn(
                    campaign, target_turn_index
                )

                # Invalidate lore from deleted turns
                lore_chunks_invalidated = 0
                for turn_id in turn_ids_to_invalidate:
                    chunks = self.lore_service.invalidate_turn_lore(
                        campaign.universe,
                        str(turn_id),
                    )
                    lore_chunks_invalidated += chunks

                # Rebuild state at target turn
                if target_turn_index == 0:
                    new_state = self.state_service.get_initial_state(campaign)
                else:
                    replay_result = self.state_service.replay_to_turn(
                        campaign, target_turn_index
                    )
                    if replay_result.success and replay_result.state:
                        new_state = replay_result.state
                    else:
                        new_state = self.state_service.get_initial_state(campaign)
                        errors.extend(replay_result.errors)

                logger.info(
                    f"Rewound campaign {campaign.id} to turn {target_turn_index}. "
                    f"Deleted {turns_deleted} turns, {snapshots_deleted} snapshots, "
                    f"invalidated {lore_chunks_invalidated} lore chunks."
                )

                return RewindResult(
                    success=True,
                    target_turn_index=target_turn_index,
                    turns_deleted=turns_deleted,
                    snapshots_deleted=snapshots_deleted,
                    lore_chunks_invalidated=lore_chunks_invalidated,
                    new_state=new_state,
                    errors=errors,
                )

        except Exception as e:
            logger.error(f"Rewind failed for campaign {campaign.id}: {e}")
            return RewindResult(
                success=False,
                target_turn_index=target_turn_index,
                errors=[f"Rewind operation failed: {str(e)}"],
            )

    def _validate_rewind(
        self,
        campaign: Campaign,
        target_turn_index: int,
    ) -> str | None:
        """
        Validate a rewind operation.

        Args:
            campaign: The campaign
            target_turn_index: Target turn index

        Returns:
            Error message if invalid, None if valid
        """
        # Check campaign is active or paused (not ended)
        if campaign.status == "ended":
            return "Cannot rewind an ended campaign"

        # Target must be non-negative
        if target_turn_index < 0:
            return "Target turn index must be non-negative"

        # Get current turn index
        latest_turn = campaign.turns.order_by("-turn_index").first()
        current_turn_index = latest_turn.turn_index if latest_turn else 0

        # Can't rewind to the future
        if target_turn_index > current_turn_index:
            return f"Target turn {target_turn_index} is greater than current turn {current_turn_index}"

        # If target is non-zero, verify that turn exists
        if target_turn_index > 0:
            turn_exists = TurnEvent.objects.filter(
                campaign=campaign,
                turn_index=target_turn_index,
            ).exists()

            if not turn_exists:
                return f"Turn {target_turn_index} does not exist"

        return None

    def get_rewindable_turns(
        self,
        campaign: Campaign,
        limit: int = 50,
    ) -> list[dict]:
        """
        Get a list of turns that can be rewound to.

        Args:
            campaign: The campaign
            limit: Maximum number of turns to return

        Returns:
            List of turn summaries for the rewind UI
        """
        turns = TurnEvent.objects.filter(
            campaign=campaign,
        ).order_by("-turn_index")[:limit]

        return [
            {
                "turn_index": turn.turn_index,
                "user_input_preview": turn.user_input_text[:100] if turn.user_input_text else "",
                "llm_response_preview": turn.llm_response_text[:100] if turn.llm_response_text else "",
                "universe_time": turn.universe_time_after_turn,
                "created_at": turn.created_at.isoformat(),
            }
            for turn in turns
        ]
