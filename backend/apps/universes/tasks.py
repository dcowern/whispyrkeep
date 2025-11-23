"""
Celery tasks for universe operations.

Includes async tasks for worldgen and catalog pre-generation.
"""

from celery import shared_task


@shared_task(bind=True)
def generate_universe_content_task(
    self,
    user_id: str,
    universe_id: str,
    content_types: list[str],
    max_items_per_type: int = 5,
):
    """
    Async task to generate homebrew content for a universe.

    This task is used for bulk content generation after initial universe creation.

    Args:
        user_id: UUID of the user
        universe_id: UUID of the universe
        content_types: List of content types to generate (species, spells, etc.)
        max_items_per_type: Maximum items to generate per type

    Returns:
        Dict with generated content counts
    """
    from django.contrib.auth import get_user_model

    from apps.universes.models import Universe
    from apps.universes.services.worldgen import WorldgenRequest, WorldgenService

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
        # Verify universe exists and belongs to user
        Universe.objects.get(id=universe_id, user=user)
    except (User.DoesNotExist, Universe.DoesNotExist) as e:
        return {"success": False, "error": str(e)}

    # Build request based on content types
    # Note: This is a stub - actual LLM generation would use WorldgenService
    # For now, WorldgenRequest and WorldgenService are imported but unused
    # pending LLM integration
    _ = WorldgenRequest  # Silence unused import warning
    _ = WorldgenService  # Silence unused import warning
    return {
        "success": True,
        "universe_id": str(universe_id),
        "content_types": content_types,
        "max_items_per_type": max_items_per_type,
        "message": "Bulk generation task completed (LLM integration pending)",
    }


@shared_task(bind=True)
def pregenerate_catalog_task(
    self,
    user_id: str,
    universe_id: str,
):
    """
    Pre-generate the full homebrew catalog for a universe.

    This task runs in the background to populate the universe with
    a full set of homebrew content based on its tone profile.

    Args:
        user_id: UUID of the user
        universe_id: UUID of the universe

    Returns:
        Dict with generation results
    """
    # Run full content generation
    all_content_types = [
        "species",
        "backgrounds",
        "spells",
        "items",
        "monsters",
        "feats",
    ]

    return generate_universe_content_task.apply(
        args=[user_id, universe_id, all_content_types, 5]
    ).get()


@shared_task(bind=True)
def lock_universe_homebrew_task(self, universe_id: str):
    """
    Lock all homebrew content for a universe.

    This is typically called after worldgen/catalog generation is complete.

    Args:
        universe_id: UUID of the universe

    Returns:
        Dict with locked counts
    """
    from apps.universes.models import (
        HomebrewBackground,
        HomebrewClass,
        HomebrewFeat,
        HomebrewItem,
        HomebrewMonster,
        HomebrewSpecies,
        HomebrewSpell,
        HomebrewSubclass,
        Universe,
    )

    try:
        universe = Universe.objects.get(id=universe_id)
    except Universe.DoesNotExist:
        return {"success": False, "error": "Universe not found"}

    homebrew_models = [
        ("species", HomebrewSpecies),
        ("spells", HomebrewSpell),
        ("items", HomebrewItem),
        ("monsters", HomebrewMonster),
        ("feats", HomebrewFeat),
        ("backgrounds", HomebrewBackground),
        ("classes", HomebrewClass),
        ("subclasses", HomebrewSubclass),
    ]

    locked_counts = {}
    for name, model in homebrew_models:
        count = model.objects.filter(universe=universe, is_locked=False).update(
            is_locked=True
        )
        locked_counts[name] = count

    return {
        "success": True,
        "universe_id": str(universe_id),
        "locked_counts": locked_counts,
    }
