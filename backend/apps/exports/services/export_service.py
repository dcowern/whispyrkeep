"""
Export Service - Handles universe and campaign exports.

Based on SYSTEM_DESIGN.md section 13.7:
- Universe export (JSON/Markdown)
- Campaign export (JSON/Markdown)
- SRD attribution in all exports

Epic 11 implementation.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from django.utils import timezone

from apps.campaigns.models import Campaign, TurnEvent
from apps.exports.models import ExportJob
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
    UniverseHardCanonDoc,
)

logger = logging.getLogger(__name__)

# SRD 5.2 Attribution (required by CC-BY-4.0 license)
SRD_ATTRIBUTION = """This work includes material from the System Reference Document 5.2 ("SRD 5.2") by Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2 is licensed under the Creative Commons Attribution 4.0 International License, available at https://creativecommons.org/licenses/by/4.0/legalcode."""


@dataclass
class ExportResult:
    """Result of an export operation."""

    success: bool
    content: str = ""
    filename: str = ""
    content_type: str = ""
    errors: list[str] = field(default_factory=list)


class UniverseExporter:
    """
    Exports universe data to various formats.

    Includes:
    - Universe metadata and tone profile
    - Hard canon documents
    - All homebrew content (species, classes, spells, items, monsters, etc.)
    - SRD attribution
    """

    def __init__(self, universe: Universe):
        """Initialize with universe to export."""
        self.universe = universe

    def to_json(self) -> ExportResult:
        """Export universe to JSON format."""
        try:
            data = self._build_export_data()
            content = json.dumps(data, indent=2, default=str)

            return ExportResult(
                success=True,
                content=content,
                filename=f"{self._safe_filename(self.universe.name)}_export.json",
                content_type="application/json",
            )
        except Exception as e:
            logger.error(f"Universe JSON export failed: {e}")
            return ExportResult(
                success=False,
                errors=[f"Export failed: {str(e)}"],
            )

    def to_markdown(self) -> ExportResult:
        """Export universe to Markdown format."""
        try:
            content = self._build_markdown()

            return ExportResult(
                success=True,
                content=content,
                filename=f"{self._safe_filename(self.universe.name)}_export.md",
                content_type="text/markdown",
            )
        except Exception as e:
            logger.error(f"Universe Markdown export failed: {e}")
            return ExportResult(
                success=False,
                errors=[f"Export failed: {str(e)}"],
            )

    def _build_export_data(self) -> dict[str, Any]:
        """Build the full export data structure."""
        return {
            "export_metadata": {
                "format_version": "1.0",
                "export_type": "universe",
                "exported_at": timezone.now().isoformat(),
                "srd_attribution": SRD_ATTRIBUTION,
            },
            "universe": {
                "id": str(self.universe.id),
                "name": self.universe.name,
                "description": self.universe.description,
                "tone_profile": self.universe.tone_profile_json,
                "rules_profile": self.universe.rules_profile_json,
                "calendar_profile": self.universe.calendar_profile_json,
                "current_universe_time": self.universe.current_universe_time,
                "canonical_lore_version": self.universe.canonical_lore_version,
                "created_at": self.universe.created_at.isoformat(),
            },
            "hard_canon": self._export_hard_canon(),
            "homebrew": {
                "species": self._export_homebrew_species(),
                "classes": self._export_homebrew_classes(),
                "subclasses": self._export_homebrew_subclasses(),
                "backgrounds": self._export_homebrew_backgrounds(),
                "feats": self._export_homebrew_feats(),
                "spells": self._export_homebrew_spells(),
                "items": self._export_homebrew_items(),
                "monsters": self._export_homebrew_monsters(),
            },
        }

    def _export_hard_canon(self) -> list[dict]:
        """Export hard canon documents."""
        docs = UniverseHardCanonDoc.objects.filter(universe=self.universe)
        return [
            {
                "id": str(doc.id),
                "title": doc.title,
                "source_type": doc.source_type,
                "raw_text": doc.raw_text,
                "never_compact": doc.never_compact,
                "created_at": doc.created_at.isoformat(),
            }
            for doc in docs
        ]

    def _export_homebrew_species(self) -> list[dict]:
        """Export homebrew species."""
        species = HomebrewSpecies.objects.filter(universe=self.universe)
        return [
            {
                "name": s.name,
                "description": s.description,
                "size": s.size,
                "speed": s.speed,
                "ability_bonuses": s.ability_bonuses_json,
                "traits": s.traits_json,
                "source_type": s.source_type,
                "power_tier": s.power_tier,
            }
            for s in species
        ]

    def _export_homebrew_classes(self) -> list[dict]:
        """Export homebrew classes."""
        classes = HomebrewClass.objects.filter(universe=self.universe)
        return [
            {
                "name": c.name,
                "description": c.description,
                "hit_die": c.hit_die,
                "primary_ability": c.primary_ability,
                "saving_throws": c.saving_throws_json,
                "proficiencies": c.proficiencies_json,
                "features": c.features_json,
                "source_type": c.source_type,
                "power_tier": c.power_tier,
            }
            for c in classes
        ]

    def _export_homebrew_subclasses(self) -> list[dict]:
        """Export homebrew subclasses."""
        subclasses = HomebrewSubclass.objects.filter(universe=self.universe)
        return [
            {
                "name": s.name,
                "description": s.description,
                "parent_class_name": s.parent_class.name if s.parent_class else s.srd_parent_class_name,
                "features": s.features_json,
                "source_type": s.source_type,
                "power_tier": s.power_tier,
            }
            for s in subclasses
        ]

    def _export_homebrew_backgrounds(self) -> list[dict]:
        """Export homebrew backgrounds."""
        backgrounds = HomebrewBackground.objects.filter(universe=self.universe)
        return [
            {
                "name": b.name,
                "description": b.description,
                "skill_proficiencies": b.skill_proficiencies_json,
                "tool_proficiencies": b.tool_proficiencies_json,
                "languages": b.languages_json,
                "equipment": b.equipment_json,
                "feature_name": b.feature_name,
                "feature_description": b.feature_description,
                "source_type": b.source_type,
                "power_tier": b.power_tier,
            }
            for b in backgrounds
        ]

    def _export_homebrew_feats(self) -> list[dict]:
        """Export homebrew feats."""
        feats = HomebrewFeat.objects.filter(universe=self.universe)
        return [
            {
                "name": f.name,
                "description": f.description,
                "prerequisites": f.prerequisites_json,
                "benefits": f.benefits_json,
                "source_type": f.source_type,
                "power_tier": f.power_tier,
            }
            for f in feats
        ]

    def _export_homebrew_spells(self) -> list[dict]:
        """Export homebrew spells."""
        spells = HomebrewSpell.objects.filter(universe=self.universe)
        return [
            {
                "name": s.name,
                "description": s.description,
                "level": s.level,
                "school": s.school.name if s.school else None,
                "casting_time": s.casting_time,
                "range": s.spell_range,
                "components": s.components,
                "duration": s.duration,
                "concentration": s.concentration,
                "ritual": s.ritual,
                "classes": s.classes_json,
                "source_type": s.source_type,
                "power_tier": s.power_tier,
            }
            for s in spells
        ]

    def _export_homebrew_items(self) -> list[dict]:
        """Export homebrew items."""
        items = HomebrewItem.objects.filter(universe=self.universe)
        return [
            {
                "name": i.name,
                "description": i.description,
                "category": i.category.name if i.category else None,
                "rarity": i.rarity,
                "magical": i.magical,
                "cost": i.cost,
                "weight": str(i.weight) if i.weight else None,
                "properties": i.properties_json,
                "source_type": i.source_type,
                "power_tier": i.power_tier,
            }
            for i in items
        ]

    def _export_homebrew_monsters(self) -> list[dict]:
        """Export homebrew monsters."""
        monsters = HomebrewMonster.objects.filter(universe=self.universe)
        return [
            {
                "name": m.name,
                "description": m.description,
                "size": m.size,
                "monster_type": m.monster_type.name if m.monster_type else None,
                "alignment": m.alignment,
                "armor_class": m.armor_class,
                "hit_points": m.hit_points,
                "hit_dice": m.hit_dice,
                "speed": m.speed_json,
                "ability_scores": m.ability_scores_json,
                "saving_throws": m.saving_throws_json,
                "skills": m.skills_json,
                "senses": m.senses_json,
                "languages": m.languages,
                "challenge_rating": str(m.challenge_rating) if m.challenge_rating else None,
                "traits": m.traits_json,
                "actions": m.actions_json,
                "legendary_actions": m.legendary_actions_json,
                "source_type": m.source_type,
                "power_tier": m.power_tier,
            }
            for m in monsters
        ]

    def _build_markdown(self) -> str:
        """Build Markdown export content."""
        lines = [
            f"# {self.universe.name}",
            "",
            f"*Exported on {timezone.now().strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
            "---",
            "",
            "## Universe Overview",
            "",
            self.universe.description or "*No description provided.*",
            "",
        ]

        # Tone Profile
        if self.universe.tone_profile_json:
            lines.extend([
                "### Tone Profile",
                "",
            ])
            for key, value in self.universe.tone_profile_json.items():
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
            lines.append("")

        # Hard Canon
        canon_docs = UniverseHardCanonDoc.objects.filter(universe=self.universe)
        if canon_docs.exists():
            lines.extend([
                "---",
                "",
                "## Hard Canon Documents",
                "",
            ])
            for doc in canon_docs:
                lines.extend([
                    f"### {doc.title}",
                    "",
                    doc.raw_text,
                    "",
                ])

        # Homebrew Sections
        lines.extend(self._markdown_homebrew_section("Species", HomebrewSpecies))
        lines.extend(self._markdown_homebrew_section("Classes", HomebrewClass))
        lines.extend(self._markdown_homebrew_section("Subclasses", HomebrewSubclass))
        lines.extend(self._markdown_homebrew_section("Backgrounds", HomebrewBackground))
        lines.extend(self._markdown_homebrew_section("Feats", HomebrewFeat))
        lines.extend(self._markdown_homebrew_section("Spells", HomebrewSpell))
        lines.extend(self._markdown_homebrew_section("Items", HomebrewItem))
        lines.extend(self._markdown_homebrew_section("Monsters", HomebrewMonster))

        # Attribution
        lines.extend([
            "---",
            "",
            "## Legal",
            "",
            SRD_ATTRIBUTION,
            "",
        ])

        return "\n".join(lines)

    def _markdown_homebrew_section(self, title: str, model_class) -> list[str]:
        """Generate markdown for a homebrew section."""
        items = model_class.objects.filter(universe=self.universe)
        if not items.exists():
            return []

        lines = [
            "---",
            "",
            f"## Homebrew {title}",
            "",
        ]

        for item in items:
            lines.extend([
                f"### {item.name}",
                "",
                f"*{item.source_type} - {item.power_tier}*",
                "",
                item.description or "*No description.*",
                "",
            ])

        return lines

    def _safe_filename(self, name: str) -> str:
        """Create a safe filename from a string."""
        return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)[:50]


class CampaignExporter:
    """
    Exports campaign data to various formats.

    Includes:
    - Campaign metadata
    - Character sheet summary
    - All turns (narrative and mechanics)
    - Current state
    - SRD attribution
    """

    def __init__(self, campaign: Campaign):
        """Initialize with campaign to export."""
        self.campaign = campaign

    def to_json(self) -> ExportResult:
        """Export campaign to JSON format."""
        try:
            data = self._build_export_data()
            content = json.dumps(data, indent=2, default=str)

            return ExportResult(
                success=True,
                content=content,
                filename=f"{self._safe_filename(self.campaign.title)}_export.json",
                content_type="application/json",
            )
        except Exception as e:
            logger.error(f"Campaign JSON export failed: {e}")
            return ExportResult(
                success=False,
                errors=[f"Export failed: {str(e)}"],
            )

    def to_markdown(self) -> ExportResult:
        """Export campaign to Markdown format."""
        try:
            content = self._build_markdown()

            return ExportResult(
                success=True,
                content=content,
                filename=f"{self._safe_filename(self.campaign.title)}_export.md",
                content_type="text/markdown",
            )
        except Exception as e:
            logger.error(f"Campaign Markdown export failed: {e}")
            return ExportResult(
                success=False,
                errors=[f"Export failed: {str(e)}"],
            )

    def _build_export_data(self) -> dict[str, Any]:
        """Build the full export data structure."""
        character = self.campaign.character_sheet
        turns = TurnEvent.objects.filter(campaign=self.campaign).order_by("turn_index")

        return {
            "export_metadata": {
                "format_version": "1.0",
                "export_type": "campaign",
                "exported_at": timezone.now().isoformat(),
                "srd_attribution": SRD_ATTRIBUTION,
            },
            "campaign": {
                "id": str(self.campaign.id),
                "title": self.campaign.title,
                "universe_id": str(self.campaign.universe_id),
                "universe_name": self.campaign.universe.name,
                "mode": self.campaign.mode,
                "target_length": self.campaign.target_length,
                "failure_style": self.campaign.failure_style,
                "content_rating": self.campaign.content_rating,
                "status": self.campaign.status,
                "start_universe_time": self.campaign.start_universe_time,
                "created_at": self.campaign.created_at.isoformat(),
            },
            "character": {
                "id": str(character.id),
                "name": character.name,
                "species": character.species,
                "class": character.character_class,
                "subclass": character.subclass,
                "background": character.background,
                "level": character.level,
                "ability_scores": character.ability_scores_json,
            },
            "turns": [
                {
                    "turn_index": turn.turn_index,
                    "user_input": turn.user_input_text,
                    "dm_response": turn.llm_response_text,
                    "roll_spec": turn.roll_spec_json,
                    "roll_results": turn.roll_results_json,
                    "state_patch": turn.state_patch_json,
                    "lore_deltas": turn.lore_deltas_json,
                    "universe_time": turn.universe_time_after_turn,
                    "created_at": turn.created_at.isoformat(),
                }
                for turn in turns
            ],
            "total_turns": turns.count(),
        }

    def _build_markdown(self) -> str:
        """Build Markdown export content."""
        character = self.campaign.character_sheet
        turns = TurnEvent.objects.filter(campaign=self.campaign).order_by("turn_index")

        lines = [
            f"# {self.campaign.title}",
            "",
            f"*Campaign in {self.campaign.universe.name}*",
            "",
            f"*Exported on {timezone.now().strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
            "---",
            "",
            "## Campaign Details",
            "",
            f"- **Mode**: {self.campaign.get_mode_display()}",
            f"- **Status**: {self.campaign.get_status_display()}",
            f"- **Content Rating**: {self.campaign.content_rating}",
            f"- **Failure Style**: {self.campaign.get_failure_style_display()}",
            f"- **Total Turns**: {turns.count()}",
            "",
            "---",
            "",
            "## Character",
            "",
            f"**{character.name}** - Level {character.level} {character.species} {character.character_class}",
            "",
            f"*Background: {character.background}*",
            "",
        ]

        if character.subclass:
            lines.append(f"*Subclass: {character.subclass}*")
            lines.append("")

        # Ability Scores
        if character.ability_scores_json:
            lines.append("### Ability Scores")
            lines.append("")
            scores = character.ability_scores_json
            lines.append(f"| STR | DEX | CON | INT | WIS | CHA |")
            lines.append(f"|-----|-----|-----|-----|-----|-----|")
            lines.append(
                f"| {scores.get('str', '-')} | {scores.get('dex', '-')} | "
                f"{scores.get('con', '-')} | {scores.get('int', '-')} | "
                f"{scores.get('wis', '-')} | {scores.get('cha', '-')} |"
            )
            lines.append("")

        # Turns
        lines.extend([
            "---",
            "",
            "## Adventure Log",
            "",
        ])

        for turn in turns:
            lines.extend([
                f"### Turn {turn.turn_index}",
                "",
                f"**Player:** {turn.user_input_text}",
                "",
                f"**DM:** {turn.llm_response_text}",
                "",
            ])

            # Roll results
            if turn.roll_results_json:
                lines.append("*Rolls:*")
                for roll in turn.roll_results_json if isinstance(turn.roll_results_json, list) else []:
                    if isinstance(roll, dict):
                        lines.append(f"- {roll.get('description', 'Roll')}: {roll.get('total', '?')}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Attribution
        lines.extend([
            "## Legal",
            "",
            SRD_ATTRIBUTION,
            "",
        ])

        return "\n".join(lines)

    def _safe_filename(self, name: str) -> str:
        """Create a safe filename from a string."""
        return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)[:50]


class ExportService:
    """
    Main export service for managing export jobs.

    Provides:
    - Job creation and tracking
    - Async export execution
    - Status checking
    """

    def create_universe_export_job(
        self,
        universe: Universe,
        format: str,
    ) -> ExportJob:
        """
        Create an export job for a universe.

        Args:
            universe: Universe to export
            format: Export format (json, md)

        Returns:
            Created ExportJob
        """
        return ExportJob.objects.create(
            user=universe.user,
            export_type="universe",
            target_id=universe.id,
            format=format,
            status="pending",
        )

    def create_campaign_export_job(
        self,
        campaign: Campaign,
        format: str,
    ) -> ExportJob:
        """
        Create an export job for a campaign.

        Args:
            campaign: Campaign to export
            format: Export format (json, md)

        Returns:
            Created ExportJob
        """
        return ExportJob.objects.create(
            user=campaign.user,
            export_type="campaign",
            target_id=campaign.id,
            format=format,
            status="pending",
        )

    def execute_export(self, job: ExportJob) -> ExportResult:
        """
        Execute an export job synchronously.

        Args:
            job: The export job to execute

        Returns:
            ExportResult with content or errors
        """
        job.status = "processing"
        job.save(update_fields=["status"])

        try:
            if job.export_type == "universe":
                result = self._execute_universe_export(job)
            elif job.export_type == "campaign":
                result = self._execute_campaign_export(job)
            else:
                result = ExportResult(
                    success=False,
                    errors=[f"Unknown export type: {job.export_type}"],
                )

            if result.success:
                job.status = "completed"
                job.completed_at = timezone.now()
                # In a real implementation, you'd upload to storage and set file_url
                # For now, we store the content directly (for small exports)
            else:
                job.status = "failed"
                job.error_message = "; ".join(result.errors)

            job.save()
            return result

        except Exception as e:
            logger.error(f"Export job {job.id} failed: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.save()
            return ExportResult(success=False, errors=[str(e)])

    def _execute_universe_export(self, job: ExportJob) -> ExportResult:
        """Execute universe export."""
        try:
            universe = Universe.objects.get(id=job.target_id, user=job.user)
        except Universe.DoesNotExist:
            return ExportResult(success=False, errors=["Universe not found"])

        exporter = UniverseExporter(universe)

        if job.format == "json":
            return exporter.to_json()
        elif job.format == "md":
            return exporter.to_markdown()
        else:
            return ExportResult(success=False, errors=[f"Unsupported format: {job.format}"])

    def _execute_campaign_export(self, job: ExportJob) -> ExportResult:
        """Execute campaign export."""
        try:
            campaign = Campaign.objects.select_related(
                "universe", "character_sheet"
            ).get(id=job.target_id, user=job.user)
        except Campaign.DoesNotExist:
            return ExportResult(success=False, errors=["Campaign not found"])

        exporter = CampaignExporter(campaign)

        if job.format == "json":
            return exporter.to_json()
        elif job.format == "md":
            return exporter.to_markdown()
        else:
            return ExportResult(success=False, errors=[f"Unsupported format: {job.format}"])
