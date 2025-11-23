"""
Catalog merge service for combining SRD baseline with universe homebrew.

This service provides a unified interface for retrieving game content that:
1. Returns SRD baseline content
2. Overlays universe-specific homebrew content
3. Handles filtering and search across both sources
4. Supports the game engine's content needs

Usage:
    catalog = CatalogService(universe)
    spells = catalog.get_spells(level=3)
    monsters = catalog.get_monsters(challenge_rating_max=5)
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db.models import QuerySet

from apps.srd.models import (
    Background,
    CharacterClass,
    Feat,
    Item,
    Monster,
    Species,
    Spell,
    Subclass,
)
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


@dataclass
class CatalogEntry:
    """
    A unified catalog entry that can represent either SRD or homebrew content.

    Attributes:
        id: The database ID (int for SRD, UUID for homebrew)
        name: The entry name
        source: Either 'srd' or 'homebrew'
        source_type: More specific source ('srd', 'srd_derived', 'homebrew')
        power_tier: Power tier (only for homebrew, None for SRD)
        level_band: Tuple of (min_level, max_level) for suggested use
        data: The full model instance
    """

    id: Any
    name: str
    source: str  # 'srd' or 'homebrew'
    source_type: str  # 'srd', 'srd_derived', 'homebrew'
    power_tier: str | None
    level_band: tuple[int, int] | None
    data: Any  # The actual model instance


class CatalogService:
    """
    Service for retrieving merged SRD + homebrew content for a universe.

    The catalog service provides a unified interface for accessing game content,
    automatically combining baseline SRD content with any universe-specific
    homebrew additions.

    Example:
        >>> universe = Universe.objects.get(id=...)
        >>> catalog = CatalogService(universe)
        >>> all_spells = catalog.get_spells()
        >>> fire_spells = catalog.get_spells(damage_type='Fire')
        >>> low_cr_monsters = catalog.get_monsters(challenge_rating_max=5)
    """

    def __init__(self, universe: Universe):
        """
        Initialize the catalog service for a specific universe.

        Args:
            universe: The Universe to provide content for
        """
        self.universe = universe

    def _to_catalog_entry(self, item: Any, source: str = "srd") -> CatalogEntry:
        """Convert a model instance to a CatalogEntry."""
        if source == "srd":
            return CatalogEntry(
                id=item.id,
                name=item.name,
                source="srd",
                source_type="srd",
                power_tier=None,
                level_band=None,
                data=item,
            )
        else:
            return CatalogEntry(
                id=item.id,
                name=item.name,
                source="homebrew",
                source_type=item.source_type,
                power_tier=item.power_tier,
                level_band=(item.suggested_level_min, item.suggested_level_max),
                data=item,
            )

    def _merge_querysets(
        self,
        srd_qs: QuerySet,
        homebrew_qs: QuerySet,
        include_srd: bool = True,
        include_homebrew: bool = True,
    ) -> list[CatalogEntry]:
        """
        Merge SRD and homebrew querysets into a unified list.

        Args:
            srd_qs: QuerySet of SRD content
            homebrew_qs: QuerySet of homebrew content
            include_srd: Whether to include SRD content
            include_homebrew: Whether to include homebrew content

        Returns:
            List of CatalogEntry objects, sorted by name
        """
        entries = []

        if include_srd:
            for item in srd_qs:
                entries.append(self._to_catalog_entry(item, "srd"))

        if include_homebrew:
            for item in homebrew_qs:
                entries.append(self._to_catalog_entry(item, "homebrew"))

        # Sort by name
        entries.sort(key=lambda x: x.name.lower())
        return entries

    # ==================== Species ====================

    def get_species(
        self,
        *,
        name: str | None = None,
        size: str | None = None,
        include_srd: bool = True,
        include_homebrew: bool = True,
    ) -> list[CatalogEntry]:
        """
        Get all available species (SRD + homebrew).

        Args:
            name: Filter by name (case-insensitive contains)
            size: Filter by size ('tiny', 'small', 'medium', 'large')
            include_srd: Include SRD species
            include_homebrew: Include homebrew species

        Returns:
            List of CatalogEntry objects for species
        """
        srd_qs = Species.objects.all()
        homebrew_qs = HomebrewSpecies.objects.filter(universe=self.universe)

        if name:
            srd_qs = srd_qs.filter(name__icontains=name)
            homebrew_qs = homebrew_qs.filter(name__icontains=name)

        if size:
            srd_qs = srd_qs.filter(size=size)
            homebrew_qs = homebrew_qs.filter(size=size)

        return self._merge_querysets(srd_qs, homebrew_qs, include_srd, include_homebrew)

    def get_species_by_name(self, name: str) -> CatalogEntry | None:
        """
        Get a specific species by exact name.

        Homebrew takes precedence over SRD if names match.
        """
        # Check homebrew first (takes precedence)
        homebrew = HomebrewSpecies.objects.filter(
            universe=self.universe,
            name__iexact=name,
        ).first()
        if homebrew:
            return self._to_catalog_entry(homebrew, "homebrew")

        # Fall back to SRD
        srd = Species.objects.filter(name__iexact=name).first()
        if srd:
            return self._to_catalog_entry(srd, "srd")

        return None

    # ==================== Spells ====================

    def get_spells(
        self,
        *,
        name: str | None = None,
        level: int | None = None,
        level_max: int | None = None,
        school_name: str | None = None,
        concentration: bool | None = None,
        ritual: bool | None = None,
        class_name: str | None = None,
        include_srd: bool = True,
        include_homebrew: bool = True,
    ) -> list[CatalogEntry]:
        """
        Get all available spells (SRD + homebrew).

        Args:
            name: Filter by name (case-insensitive contains)
            level: Filter by exact spell level (0 for cantrips)
            level_max: Filter by maximum spell level
            school_name: Filter by spell school name
            concentration: Filter by concentration requirement
            ritual: Filter by ritual casting
            class_name: Filter by class that can cast the spell (SRD only)
            include_srd: Include SRD spells
            include_homebrew: Include homebrew spells

        Returns:
            List of CatalogEntry objects for spells
        """
        srd_qs = Spell.objects.select_related("school", "damage_type")
        homebrew_qs = HomebrewSpell.objects.filter(
            universe=self.universe
        ).select_related("school", "damage_type")

        if name:
            srd_qs = srd_qs.filter(name__icontains=name)
            homebrew_qs = homebrew_qs.filter(name__icontains=name)

        if level is not None:
            srd_qs = srd_qs.filter(level=level)
            homebrew_qs = homebrew_qs.filter(level=level)

        if level_max is not None:
            srd_qs = srd_qs.filter(level__lte=level_max)
            homebrew_qs = homebrew_qs.filter(level__lte=level_max)

        if school_name:
            srd_qs = srd_qs.filter(school__name__iexact=school_name)
            homebrew_qs = homebrew_qs.filter(school__name__iexact=school_name)

        if concentration is not None:
            srd_qs = srd_qs.filter(concentration=concentration)
            homebrew_qs = homebrew_qs.filter(concentration=concentration)

        if ritual is not None:
            srd_qs = srd_qs.filter(ritual=ritual)
            homebrew_qs = homebrew_qs.filter(ritual=ritual)

        if class_name:
            srd_qs = srd_qs.filter(classes__name__iexact=class_name)
            # For homebrew, check class_restrictions list
            # Note: This is less efficient but homebrew content is typically smaller
            homebrew_list = [
                h for h in homebrew_qs
                if not h.class_restrictions or class_name in h.class_restrictions
            ]
            entries = []
            if include_srd:
                for item in srd_qs:
                    entries.append(self._to_catalog_entry(item, "srd"))
            if include_homebrew:
                for item in homebrew_list:
                    entries.append(self._to_catalog_entry(item, "homebrew"))
            entries.sort(key=lambda x: (x.data.level, x.name.lower()))
            return entries

        result = self._merge_querysets(srd_qs, homebrew_qs, include_srd, include_homebrew)
        # Sort spells by level, then name
        result.sort(key=lambda x: (x.data.level, x.name.lower()))
        return result

    def get_spell_by_name(self, name: str) -> CatalogEntry | None:
        """Get a specific spell by exact name. Homebrew takes precedence."""
        homebrew = HomebrewSpell.objects.filter(
            universe=self.universe,
            name__iexact=name,
        ).select_related("school", "damage_type").first()
        if homebrew:
            return self._to_catalog_entry(homebrew, "homebrew")

        srd = Spell.objects.filter(name__iexact=name).select_related(
            "school", "damage_type"
        ).first()
        if srd:
            return self._to_catalog_entry(srd, "srd")

        return None

    # ==================== Items ====================

    def get_items(
        self,
        *,
        name: str | None = None,
        category_name: str | None = None,
        rarity: str | None = None,
        magical: bool | None = None,
        is_weapon: bool | None = None,
        is_armor: bool | None = None,
        include_srd: bool = True,
        include_homebrew: bool = True,
    ) -> list[CatalogEntry]:
        """
        Get all available items (SRD + homebrew).

        Args:
            name: Filter by name (case-insensitive contains)
            category_name: Filter by category name
            rarity: Filter by rarity
            magical: Filter by magical status
            is_weapon: Filter for weapons only (homebrew)
            is_armor: Filter for armor only (homebrew)
            include_srd: Include SRD items
            include_homebrew: Include homebrew items

        Returns:
            List of CatalogEntry objects for items
        """
        srd_qs = Item.objects.select_related("category")
        homebrew_qs = HomebrewItem.objects.filter(
            universe=self.universe
        ).select_related("category", "damage_type")

        if name:
            srd_qs = srd_qs.filter(name__icontains=name)
            homebrew_qs = homebrew_qs.filter(name__icontains=name)

        if category_name:
            srd_qs = srd_qs.filter(category__name__iexact=category_name)
            homebrew_qs = homebrew_qs.filter(category__name__iexact=category_name)

        if rarity:
            srd_qs = srd_qs.filter(rarity=rarity)
            homebrew_qs = homebrew_qs.filter(rarity=rarity)

        if magical is not None:
            srd_qs = srd_qs.filter(magical=magical)
            homebrew_qs = homebrew_qs.filter(magical=magical)

        if is_weapon is not None:
            # SRD: check if weapon_stats exists
            if is_weapon:
                srd_qs = srd_qs.filter(weapon_stats__isnull=False)
            else:
                srd_qs = srd_qs.filter(weapon_stats__isnull=True)
            homebrew_qs = homebrew_qs.filter(is_weapon=is_weapon)

        if is_armor is not None:
            # SRD: check if armor_stats exists
            if is_armor:
                srd_qs = srd_qs.filter(armor_stats__isnull=False)
            else:
                srd_qs = srd_qs.filter(armor_stats__isnull=True)
            homebrew_qs = homebrew_qs.filter(is_armor=is_armor)

        return self._merge_querysets(srd_qs, homebrew_qs, include_srd, include_homebrew)

    def get_item_by_name(self, name: str) -> CatalogEntry | None:
        """Get a specific item by exact name. Homebrew takes precedence."""
        homebrew = HomebrewItem.objects.filter(
            universe=self.universe,
            name__iexact=name,
        ).select_related("category", "damage_type").first()
        if homebrew:
            return self._to_catalog_entry(homebrew, "homebrew")

        srd = Item.objects.filter(name__iexact=name).select_related("category").first()
        if srd:
            return self._to_catalog_entry(srd, "srd")

        return None

    # ==================== Monsters ====================

    def get_monsters(
        self,
        *,
        name: str | None = None,
        monster_type_name: str | None = None,
        size: str | None = None,
        challenge_rating: Decimal | None = None,
        challenge_rating_min: Decimal | None = None,
        challenge_rating_max: Decimal | None = None,
        include_srd: bool = True,
        include_homebrew: bool = True,
    ) -> list[CatalogEntry]:
        """
        Get all available monsters (SRD + homebrew).

        Args:
            name: Filter by name (case-insensitive contains)
            monster_type_name: Filter by monster type name
            size: Filter by size
            challenge_rating: Filter by exact CR
            challenge_rating_min: Filter by minimum CR
            challenge_rating_max: Filter by maximum CR
            include_srd: Include SRD monsters
            include_homebrew: Include homebrew monsters

        Returns:
            List of CatalogEntry objects for monsters, sorted by CR then name
        """
        srd_qs = Monster.objects.select_related("monster_type")
        homebrew_qs = HomebrewMonster.objects.filter(
            universe=self.universe
        ).select_related("monster_type")

        if name:
            srd_qs = srd_qs.filter(name__icontains=name)
            homebrew_qs = homebrew_qs.filter(name__icontains=name)

        if monster_type_name:
            srd_qs = srd_qs.filter(monster_type__name__iexact=monster_type_name)
            homebrew_qs = homebrew_qs.filter(monster_type__name__iexact=monster_type_name)

        if size:
            srd_qs = srd_qs.filter(size=size)
            homebrew_qs = homebrew_qs.filter(size=size)

        if challenge_rating is not None:
            srd_qs = srd_qs.filter(challenge_rating=challenge_rating)
            homebrew_qs = homebrew_qs.filter(challenge_rating=challenge_rating)

        if challenge_rating_min is not None:
            srd_qs = srd_qs.filter(challenge_rating__gte=challenge_rating_min)
            homebrew_qs = homebrew_qs.filter(challenge_rating__gte=challenge_rating_min)

        if challenge_rating_max is not None:
            srd_qs = srd_qs.filter(challenge_rating__lte=challenge_rating_max)
            homebrew_qs = homebrew_qs.filter(challenge_rating__lte=challenge_rating_max)

        result = self._merge_querysets(srd_qs, homebrew_qs, include_srd, include_homebrew)
        # Sort monsters by CR, then name
        result.sort(key=lambda x: (x.data.challenge_rating, x.name.lower()))
        return result

    def get_monster_by_name(self, name: str) -> CatalogEntry | None:
        """Get a specific monster by exact name. Homebrew takes precedence."""
        homebrew = HomebrewMonster.objects.filter(
            universe=self.universe,
            name__iexact=name,
        ).select_related("monster_type").first()
        if homebrew:
            return self._to_catalog_entry(homebrew, "homebrew")

        srd = Monster.objects.filter(name__iexact=name).select_related(
            "monster_type"
        ).first()
        if srd:
            return self._to_catalog_entry(srd, "srd")

        return None

    # ==================== Feats ====================

    def get_feats(
        self,
        *,
        name: str | None = None,
        include_srd: bool = True,
        include_homebrew: bool = True,
    ) -> list[CatalogEntry]:
        """Get all available feats (SRD + homebrew)."""
        srd_qs = Feat.objects.all()
        homebrew_qs = HomebrewFeat.objects.filter(universe=self.universe)

        if name:
            srd_qs = srd_qs.filter(name__icontains=name)
            homebrew_qs = homebrew_qs.filter(name__icontains=name)

        return self._merge_querysets(srd_qs, homebrew_qs, include_srd, include_homebrew)

    def get_feat_by_name(self, name: str) -> CatalogEntry | None:
        """Get a specific feat by exact name. Homebrew takes precedence."""
        homebrew = HomebrewFeat.objects.filter(
            universe=self.universe,
            name__iexact=name,
        ).first()
        if homebrew:
            return self._to_catalog_entry(homebrew, "homebrew")

        srd = Feat.objects.filter(name__iexact=name).first()
        if srd:
            return self._to_catalog_entry(srd, "srd")

        return None

    # ==================== Backgrounds ====================

    def get_backgrounds(
        self,
        *,
        name: str | None = None,
        include_srd: bool = True,
        include_homebrew: bool = True,
    ) -> list[CatalogEntry]:
        """Get all available backgrounds (SRD + homebrew)."""
        srd_qs = Background.objects.all()
        homebrew_qs = HomebrewBackground.objects.filter(universe=self.universe)

        if name:
            srd_qs = srd_qs.filter(name__icontains=name)
            homebrew_qs = homebrew_qs.filter(name__icontains=name)

        return self._merge_querysets(srd_qs, homebrew_qs, include_srd, include_homebrew)

    def get_background_by_name(self, name: str) -> CatalogEntry | None:
        """Get a specific background by exact name. Homebrew takes precedence."""
        homebrew = HomebrewBackground.objects.filter(
            universe=self.universe,
            name__iexact=name,
        ).first()
        if homebrew:
            return self._to_catalog_entry(homebrew, "homebrew")

        srd = Background.objects.filter(name__iexact=name).first()
        if srd:
            return self._to_catalog_entry(srd, "srd")

        return None

    # ==================== Classes ====================

    def get_classes(
        self,
        *,
        name: str | None = None,
        include_srd: bool = True,
        include_homebrew: bool = True,
    ) -> list[CatalogEntry]:
        """Get all available character classes (SRD + homebrew)."""
        srd_qs = CharacterClass.objects.all()
        homebrew_qs = HomebrewClass.objects.filter(universe=self.universe)

        if name:
            srd_qs = srd_qs.filter(name__icontains=name)
            homebrew_qs = homebrew_qs.filter(name__icontains=name)

        return self._merge_querysets(srd_qs, homebrew_qs, include_srd, include_homebrew)

    def get_class_by_name(self, name: str) -> CatalogEntry | None:
        """Get a specific class by exact name. Homebrew takes precedence."""
        homebrew = HomebrewClass.objects.filter(
            universe=self.universe,
            name__iexact=name,
        ).first()
        if homebrew:
            return self._to_catalog_entry(homebrew, "homebrew")

        srd = CharacterClass.objects.filter(name__iexact=name).first()
        if srd:
            return self._to_catalog_entry(srd, "srd")

        return None

    # ==================== Subclasses ====================

    def get_subclasses(
        self,
        *,
        name: str | None = None,
        parent_class_name: str | None = None,
        include_srd: bool = True,
        include_homebrew: bool = True,
    ) -> list[CatalogEntry]:
        """
        Get all available subclasses (SRD + homebrew).

        Args:
            name: Filter by subclass name
            parent_class_name: Filter by parent class name
            include_srd: Include SRD subclasses
            include_homebrew: Include homebrew subclasses
        """
        srd_qs = Subclass.objects.select_related("character_class")
        homebrew_qs = HomebrewSubclass.objects.filter(
            universe=self.universe
        ).select_related("parent_class")

        if name:
            srd_qs = srd_qs.filter(name__icontains=name)
            homebrew_qs = homebrew_qs.filter(name__icontains=name)

        if parent_class_name:
            srd_qs = srd_qs.filter(character_class__name__iexact=parent_class_name)
            # For homebrew, check both parent_class and srd_parent_class_name
            homebrew_qs = homebrew_qs.filter(
                parent_class__name__iexact=parent_class_name
            ) | homebrew_qs.filter(
                srd_parent_class_name__iexact=parent_class_name
            )

        return self._merge_querysets(srd_qs, homebrew_qs, include_srd, include_homebrew)

    def get_subclass_by_name(
        self,
        name: str,
        parent_class_name: str | None = None,
    ) -> CatalogEntry | None:
        """Get a specific subclass by exact name. Homebrew takes precedence."""
        homebrew_qs = HomebrewSubclass.objects.filter(
            universe=self.universe,
            name__iexact=name,
        ).select_related("parent_class")
        if parent_class_name:
            homebrew_qs = homebrew_qs.filter(
                parent_class__name__iexact=parent_class_name
            ) | homebrew_qs.filter(
                srd_parent_class_name__iexact=parent_class_name
            )
        homebrew = homebrew_qs.first()
        if homebrew:
            return self._to_catalog_entry(homebrew, "homebrew")

        srd_qs = Subclass.objects.filter(name__iexact=name).select_related(
            "character_class"
        )
        if parent_class_name:
            srd_qs = srd_qs.filter(character_class__name__iexact=parent_class_name)
        srd = srd_qs.first()
        if srd:
            return self._to_catalog_entry(srd, "srd")

        return None

    # ==================== Utility Methods ====================

    def get_catalog_stats(self) -> dict[str, dict[str, int]]:
        """
        Get statistics about the catalog content.

        Returns:
            Dictionary with counts for each content type from both sources.
        """
        return {
            "species": {
                "srd": Species.objects.count(),
                "homebrew": HomebrewSpecies.objects.filter(universe=self.universe).count(),
            },
            "spells": {
                "srd": Spell.objects.count(),
                "homebrew": HomebrewSpell.objects.filter(universe=self.universe).count(),
            },
            "items": {
                "srd": Item.objects.count(),
                "homebrew": HomebrewItem.objects.filter(universe=self.universe).count(),
            },
            "monsters": {
                "srd": Monster.objects.count(),
                "homebrew": HomebrewMonster.objects.filter(universe=self.universe).count(),
            },
            "feats": {
                "srd": Feat.objects.count(),
                "homebrew": HomebrewFeat.objects.filter(universe=self.universe).count(),
            },
            "backgrounds": {
                "srd": Background.objects.count(),
                "homebrew": HomebrewBackground.objects.filter(universe=self.universe).count(),
            },
            "classes": {
                "srd": CharacterClass.objects.count(),
                "homebrew": HomebrewClass.objects.filter(universe=self.universe).count(),
            },
            "subclasses": {
                "srd": Subclass.objects.count(),
                "homebrew": HomebrewSubclass.objects.filter(universe=self.universe).count(),
            },
        }
