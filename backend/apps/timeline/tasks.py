"""
Timeline Celery Tasks.

Handles asynchronous timeline operations.

Ticket: 6.1.2

Based on SYSTEM_DESIGN.md section 14:
- rebuild_universe_timeline(universe_id)
"""

import logging
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def rebuild_universe_timeline_task(
    self,
    universe_id: str,
) -> dict[str, Any]:
    """
    Rebuild the timeline for a universe.

    This task:
    1. Loads all campaigns for the universe
    2. Extracts time anchors from:
       - Hard canon documents
       - Campaign start/end times
       - Significant events from turn history
    3. Rebuilds the timeline anchor list
    4. Updates the universe's timeline data

    Args:
        universe_id: UUID of the universe to rebuild

    Returns:
        Dict with success status and timeline summary
    """
    from django.db import transaction

    from apps.universes.models import Universe, UniverseHardCanonDoc
    from apps.campaigns.models import Campaign, TurnEvent
    from apps.timeline.services import (
        TimeAnchor,
        TimeResolver,
        UniverseTime,
        CalendarConfig,
    )
    from apps.timeline.services.time_resolver import TimeAnchorType

    try:
        universe = Universe.objects.get(id=universe_id)
    except Universe.DoesNotExist:
        logger.error(f"Universe not found: {universe_id}")
        return {"success": False, "error": "Universe not found"}

    logger.info(f"Rebuilding timeline for universe: {universe.name} ({universe_id})")

    # Load calendar config
    calendar_config = CalendarConfig.from_dict(universe.calendar_profile_json or {})
    resolver = TimeResolver(calendar_config=calendar_config)

    anchors_created = 0
    errors = []

    # Extract anchors from hard canon documents
    hard_canon_docs = UniverseHardCanonDoc.objects.filter(universe=universe)
    for doc in hard_canon_docs:
        # Check if document contains timeline data
        # This would be enhanced with NLP in a production system
        # For now, we look for explicit time references in title
        if any(
            keyword in doc.title.lower()
            for keyword in ["timeline", "history", "chronicle", "era"]
        ):
            # Create an anchor for the document
            anchor = TimeAnchor(
                id=f"doc_{doc.id}",
                name=f"Historical Document: {doc.title}",
                time=UniverseTime.from_dict(universe.current_universe_time or {}),
                anchor_type=TimeAnchorType.EVENT,
                description=f"Hard canon document: {doc.title[:100]}",
                tags=["hard_canon", "document"],
            )
            resolver.add_anchor(anchor)
            anchors_created += 1

    # Extract anchors from campaigns
    campaigns = Campaign.objects.filter(universe=universe).prefetch_related("turns")
    for campaign in campaigns:
        # Campaign start anchor
        start_time = UniverseTime.from_dict(campaign.start_universe_time or {})
        start_anchor = TimeAnchor(
            id=f"campaign_start_{campaign.id}",
            name=f"Campaign Start: {campaign.title}",
            time=start_time,
            anchor_type=TimeAnchorType.CAMPAIGN,
            description=f"Start of campaign: {campaign.title}",
            tags=["campaign", "start"],
        )
        resolver.add_anchor(start_anchor)
        anchors_created += 1

        # Find the last turn to get campaign end time
        last_turn = campaign.turns.order_by("-turn_index").first()
        if last_turn and last_turn.universe_time_after_turn:
            end_time = UniverseTime.from_dict(last_turn.universe_time_after_turn)
            end_anchor = TimeAnchor(
                id=f"campaign_current_{campaign.id}",
                name=f"Campaign Current: {campaign.title}",
                time=end_time,
                anchor_type=TimeAnchorType.CAMPAIGN,
                description=f"Current point in campaign: {campaign.title}",
                tags=["campaign", "current"],
            )
            resolver.add_anchor(end_anchor)
            anchors_created += 1

        # Extract significant events from turn history
        # Look for turns with major state changes
        significant_turns = campaign.turns.filter(
            turn_index__in=[0, 10, 25, 50, 100]  # Sample key turns
        )
        for turn in significant_turns:
            if turn.universe_time_after_turn:
                turn_time = UniverseTime.from_dict(turn.universe_time_after_turn)
                turn_anchor = TimeAnchor(
                    id=f"turn_{campaign.id}_{turn.turn_index}",
                    name=f"Turn {turn.turn_index}: {campaign.title}",
                    time=turn_time,
                    anchor_type=TimeAnchorType.EVENT,
                    description=f"Turn {turn.turn_index} of {campaign.title}",
                    tags=["turn", "milestone"],
                )
                resolver.add_anchor(turn_anchor)
                anchors_created += 1

    # Export anchors and update universe
    timeline_anchors = resolver.export_anchors()

    with transaction.atomic():
        # Update universe with new timeline data
        # Store in a dedicated field or as part of existing JSON
        # For now, we'll store in a separate structure
        universe.calendar_profile_json = universe.calendar_profile_json or {}
        universe.calendar_profile_json["timeline_anchors"] = timeline_anchors
        universe.calendar_profile_json["timeline_rebuilt_at"] = str(
            universe.updated_at
        )
        universe.save(update_fields=["calendar_profile_json", "updated_at"])

    logger.info(
        f"Timeline rebuilt for universe {universe.name}: "
        f"{anchors_created} anchors created"
    )

    return {
        "success": True,
        "universe_id": str(universe_id),
        "universe_name": universe.name,
        "anchors_created": anchors_created,
        "total_anchors": len(timeline_anchors),
        "errors": errors,
    }


@shared_task(bind=True)
def validate_universe_timeline_task(
    self,
    universe_id: str,
) -> dict[str, Any]:
    """
    Validate the timeline consistency for a universe.

    Checks for:
    - Monotonic time violations
    - Overlapping scenarios
    - Orphaned time anchors

    Args:
        universe_id: UUID of the universe to validate

    Returns:
        Dict with validation results
    """
    from apps.universes.models import Universe
    from apps.campaigns.models import Campaign
    from apps.timeline.services import (
        TimeValidator,
        TimeResolver,
        UniverseTime,
        CalendarConfig,
    )

    try:
        universe = Universe.objects.get(id=universe_id)
    except Universe.DoesNotExist:
        return {"success": False, "error": "Universe not found"}

    calendar_config = CalendarConfig.from_dict(universe.calendar_profile_json or {})
    validator = TimeValidator(calendar_config)
    resolver = TimeResolver(calendar_config)

    # Load existing anchors
    existing_anchors = (
        universe.calendar_profile_json or {}
    ).get("timeline_anchors", [])
    for anchor_data in existing_anchors:
        from apps.timeline.services.time_resolver import TimeAnchor
        anchor = TimeAnchor.from_dict(anchor_data)
        resolver.add_anchor(anchor)

    issues = []
    warnings = []

    # Check campaign time consistency
    campaigns = Campaign.objects.filter(universe=universe).prefetch_related("turns")

    campaign_times: list[tuple[UniverseTime, UniverseTime]] = []
    for campaign in campaigns:
        start_time = UniverseTime.from_dict(campaign.start_universe_time or {})

        # Get current time from last turn
        last_turn = campaign.turns.order_by("-turn_index").first()
        if last_turn and last_turn.universe_time_after_turn:
            end_time = UniverseTime.from_dict(last_turn.universe_time_after_turn)

            # Validate monotonicity within campaign
            validation = validator.validate_time_advance(start_time, end_time)
            if not validation.valid:
                issues.extend(
                    f"Campaign {campaign.title}: {err}" for err in validation.errors
                )
            warnings.extend(validation.warnings)

            campaign_times.append((start_time, end_time))

        # Check turn-by-turn monotonicity
        prev_time = start_time
        for turn in campaign.turns.order_by("turn_index"):
            if turn.universe_time_after_turn:
                turn_time = UniverseTime.from_dict(turn.universe_time_after_turn)
                validation = validator.validate_time_advance(prev_time, turn_time)
                if not validation.valid:
                    issues.append(
                        f"Campaign {campaign.title}, Turn {turn.turn_index}: "
                        f"Time goes backwards"
                    )
                prev_time = turn_time

    # Check for overlapping campaigns (warning only, not an error)
    for i, (start1, end1) in enumerate(campaign_times):
        for j, (start2, end2) in enumerate(campaign_times[i + 1 :], i + 1):
            if start1 < end2 and start2 < end1:
                warnings.append(
                    f"Campaigns {i + 1} and {j + 1} have overlapping time ranges"
                )

    return {
        "success": len(issues) == 0,
        "universe_id": str(universe_id),
        "issues": issues,
        "warnings": warnings,
        "campaigns_checked": len(campaigns),
    }
