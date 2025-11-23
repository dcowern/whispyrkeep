"""
Worldgen Service - LLM co-write for universe creation.

Orchestrates the universe generation process:
1. Takes user's worldgen parameters (tone, themes, rules)
2. Generates world content via LLM
3. Creates homebrew content (species, spells, items, monsters)
4. Creates hard canon documents

Based on SYSTEM_DESIGN.md section 9.
"""

import hashlib
from dataclasses import dataclass, field
from typing import Optional

from django.db import transaction

from apps.llm_config.models import LlmEndpointConfig
from apps.universes.models import (
    HomebrewBackground,
    HomebrewClass,
    HomebrewFeat,
    HomebrewItem,
    HomebrewMonster,
    HomebrewSpecies,
    HomebrewSpell,
    Universe,
    UniverseHardCanonDoc,
)


@dataclass
class WorldgenRequest:
    """Request parameters for worldgen."""

    # Universe basic info
    name: str
    description: str = ""

    # Tone sliders (0.0 to 1.0)
    grimdark_cozy: float = 0.5
    comedy_serious: float = 0.5
    low_high_magic: float = 0.5
    sandbox_railroad: float = 0.5
    combat_roleplay: float = 0.5

    # Theme tags
    themes: list[str] = field(default_factory=list)

    # Rules preferences
    rules_strictness: str = "standard"  # strict, standard, loose
    homebrew_amount: str = "moderate"  # none, minimal, moderate, extensive

    # Generation options
    generate_species: bool = True
    generate_classes: bool = False
    generate_backgrounds: bool = True
    generate_spells: bool = True
    generate_items: bool = True
    generate_monsters: bool = True
    generate_feats: bool = True

    # Content limits
    max_species: int = 3
    max_classes: int = 0
    max_backgrounds: int = 2
    max_spells: int = 5
    max_items: int = 5
    max_monsters: int = 5
    max_feats: int = 3

    # Seed for deterministic generation (optional)
    seed: Optional[int] = None


@dataclass
class WorldgenResult:
    """Result of worldgen operation."""

    success: bool
    universe_id: Optional[str] = None
    created_content: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    llm_prompt: Optional[str] = None  # For debugging


class WorldgenService:
    """
    Service for orchestrating universe worldgen via LLM.

    Usage:
        service = WorldgenService(user)
        result = service.generate(request)
    """

    def __init__(self, user):
        """
        Initialize worldgen service.

        Args:
            user: The authenticated user
        """
        self.user = user
        self.llm_config = self._get_llm_config()

    def _get_llm_config(self) -> Optional[LlmEndpointConfig]:
        """Get user's active LLM configuration."""
        return LlmEndpointConfig.objects.filter(
            user=self.user,
            is_active=True,
        ).first()

    def generate(self, request: WorldgenRequest) -> WorldgenResult:
        """
        Generate a universe with homebrew content.

        Args:
            request: WorldgenRequest with generation parameters

        Returns:
            WorldgenResult with created universe and content
        """
        errors = []
        warnings = []

        # Validate request
        validation_errors = self._validate_request(request)
        if validation_errors:
            return WorldgenResult(
                success=False,
                errors=validation_errors,
            )

        # Check LLM config
        if not self.llm_config:
            warnings.append(
                "No LLM configuration found. Universe will be created with default settings only. "
                "Configure an LLM endpoint to enable AI-powered worldgen."
            )

        # Build tone profile from sliders
        tone_profile = self._build_tone_profile(request)

        # Build rules profile
        rules_profile = self._build_rules_profile(request)

        try:
            with transaction.atomic():
                # Create the universe
                universe = Universe.objects.create(
                    user=self.user,
                    name=request.name,
                    description=request.description,
                    tone_profile_json=tone_profile,
                    rules_profile_json=rules_profile,
                    calendar_profile_json=self._default_calendar(),
                    current_universe_time={"year": 1, "month": 1, "day": 1},
                )

                created_content = {
                    "species": [],
                    "classes": [],
                    "backgrounds": [],
                    "spells": [],
                    "items": [],
                    "monsters": [],
                    "feats": [],
                    "canon_docs": [],
                }

                # Generate LLM prompt (for future LLM integration)
                llm_prompt = self._build_worldgen_prompt(request)

                # If LLM is configured, call it for content generation
                if self.llm_config:
                    llm_content = self._call_llm_for_content(llm_prompt, request)
                    if llm_content:
                        created_content = self._create_content_from_llm(
                            universe, llm_content, request
                        )
                else:
                    # Create placeholder content without LLM
                    created_content = self._create_placeholder_content(
                        universe, request
                    )

                # Create initial hard canon doc
                world_doc = self._create_world_overview_doc(universe, request)
                created_content["canon_docs"].append({
                    "id": str(world_doc.id),
                    "title": world_doc.title,
                })

                return WorldgenResult(
                    success=True,
                    universe_id=str(universe.id),
                    created_content=created_content,
                    warnings=warnings,
                    llm_prompt=llm_prompt,
                )

        except Exception as e:
            return WorldgenResult(
                success=False,
                errors=[f"Universe creation failed: {str(e)}"],
            )

    def _validate_request(self, request: WorldgenRequest) -> list[str]:
        """Validate worldgen request."""
        errors = []

        if not request.name or not request.name.strip():
            errors.append("Universe name is required")

        if len(request.name) > 200:
            errors.append("Universe name must be 200 characters or less")

        # Validate slider values
        sliders = [
            ("grimdark_cozy", request.grimdark_cozy),
            ("comedy_serious", request.comedy_serious),
            ("low_high_magic", request.low_high_magic),
            ("sandbox_railroad", request.sandbox_railroad),
            ("combat_roleplay", request.combat_roleplay),
        ]
        for name, value in sliders:
            if not 0.0 <= value <= 1.0:
                errors.append(f"{name} must be between 0.0 and 1.0")

        # Validate content limits
        if request.max_species < 0 or request.max_species > 10:
            errors.append("max_species must be between 0 and 10")
        if request.max_spells < 0 or request.max_spells > 20:
            errors.append("max_spells must be between 0 and 20")

        return errors

    def _build_tone_profile(self, request: WorldgenRequest) -> dict:
        """Build tone profile JSON from request."""
        return {
            "grimdark_cozy": request.grimdark_cozy,
            "comedy_serious": request.comedy_serious,
            "low_high_magic": request.low_high_magic,
            "sandbox_railroad": request.sandbox_railroad,
            "combat_roleplay": request.combat_roleplay,
            "themes": request.themes,
        }

    def _build_rules_profile(self, request: WorldgenRequest) -> dict:
        """Build rules profile JSON from request."""
        strictness_configs = {
            "strict": {
                "encumbrance": "standard",
                "rest_variant": "gritty",
                "flanking": False,
                "multiclassing": False,
                "feats": False,
            },
            "standard": {
                "encumbrance": "variant",
                "rest_variant": "standard",
                "flanking": True,
                "multiclassing": True,
                "feats": True,
            },
            "loose": {
                "encumbrance": "ignored",
                "rest_variant": "epic",
                "flanking": True,
                "multiclassing": True,
                "feats": True,
            },
        }

        profile = strictness_configs.get(request.rules_strictness, strictness_configs["standard"])
        profile["homebrew_amount"] = request.homebrew_amount
        return profile

    def _default_calendar(self) -> dict:
        """Return default calendar configuration."""
        return {
            "calendar_type": "standard",
            "months_per_year": 12,
            "days_per_month": [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
            "month_names": [
                "Hammer", "Alturiak", "Ches", "Tarsakh", "Mirtul", "Kythorn",
                "Flamerule", "Eleasis", "Eleint", "Marpenoth", "Uktar", "Nightal"
            ],
            "weekday_names": ["Moonday", "Towerday", "Wingsday", "Earthday", "Freeday", "Starday", "Sunday"],
        }

    def _build_worldgen_prompt(self, request: WorldgenRequest) -> str:
        """Build the LLM prompt for worldgen."""
        tone_descriptions = []
        if request.grimdark_cozy < 0.3:
            tone_descriptions.append("dark and grim")
        elif request.grimdark_cozy > 0.7:
            tone_descriptions.append("cozy and comforting")

        if request.comedy_serious < 0.3:
            tone_descriptions.append("comedic and lighthearted")
        elif request.comedy_serious > 0.7:
            tone_descriptions.append("serious and dramatic")

        if request.low_high_magic < 0.3:
            tone_descriptions.append("low magic")
        elif request.low_high_magic > 0.7:
            tone_descriptions.append("high magic")

        tone_str = ", ".join(tone_descriptions) if tone_descriptions else "balanced"
        themes_str = ", ".join(request.themes) if request.themes else "classic fantasy"

        prompt = f"""You are a world-building assistant for a tabletop RPG universe.

Create content for a universe called "{request.name}".

Description: {request.description or "A new fantasy world"}

Tone: {tone_str}
Themes: {themes_str}

Generate the following content in JSON format:
"""

        if request.generate_species and request.max_species > 0:
            prompt += f"\n- {request.max_species} unique playable species"
        if request.generate_backgrounds and request.max_backgrounds > 0:
            prompt += f"\n- {request.max_backgrounds} character backgrounds"
        if request.generate_spells and request.max_spells > 0:
            prompt += f"\n- {request.max_spells} thematic spells"
        if request.generate_items and request.max_items > 0:
            prompt += f"\n- {request.max_items} unique items"
        if request.generate_monsters and request.max_monsters > 0:
            prompt += f"\n- {request.max_monsters} creatures/monsters"
        if request.generate_feats and request.max_feats > 0:
            prompt += f"\n- {request.max_feats} feats"

        prompt += """

All content should be balanced for D&D 5e SRD rules.
Mark each piece of content as "srd_derived" if based on existing SRD content, or "homebrew" if entirely new.
Assign appropriate power tiers (weak, standard, strong, very_strong, legendary) and level bands."""

        return prompt

    def _call_llm_for_content(self, prompt: str, request: WorldgenRequest) -> Optional[dict]:
        """
        Call LLM to generate content.

        This is a placeholder for actual LLM integration.
        In a full implementation, this would:
        1. Decrypt the API key
        2. Call the LLM API
        3. Parse the response
        4. Return structured content

        For now, returns None to use placeholder content.
        """
        # TODO: Implement actual LLM call when LLM integration is complete
        # from apps.llm_config.encryption import decrypt_api_key
        # api_key = decrypt_api_key(self.llm_config.api_key_encrypted)
        # response = call_llm(api_key, prompt)
        # return parse_llm_response(response)
        return None

    def _create_content_from_llm(
        self, universe: Universe, llm_content: dict, request: WorldgenRequest
    ) -> dict:
        """Create homebrew content from LLM response."""
        # TODO: Implement when LLM integration is complete
        return self._create_placeholder_content(universe, request)

    def _create_placeholder_content(
        self, universe: Universe, request: WorldgenRequest
    ) -> dict:
        """Create placeholder content when LLM is not available."""
        created = {
            "species": [],
            "classes": [],
            "backgrounds": [],
            "spells": [],
            "items": [],
            "monsters": [],
            "feats": [],
            "canon_docs": [],
        }

        # Only create minimal placeholder content
        # Real content should come from LLM

        return created

    def _create_world_overview_doc(
        self, universe: Universe, request: WorldgenRequest
    ) -> UniverseHardCanonDoc:
        """Create the initial world overview document."""
        overview_text = f"""# {request.name}

## Overview
{request.description or "A new fantasy world awaits exploration."}

## Tone & Themes
This world has been crafted with the following characteristics:
- Atmosphere: {"Dark and grim" if request.grimdark_cozy < 0.5 else "Warm and inviting"}
- Magic Level: {"Low magic" if request.low_high_magic < 0.5 else "High magic"}
- Themes: {", ".join(request.themes) if request.themes else "Classic fantasy adventure"}

## Rules Framework
- Rules Strictness: {request.rules_strictness.title()}
- Homebrew Content: {request.homebrew_amount.title()}

---
*This document was generated during universe creation and serves as the foundational canon for this world.*
"""

        checksum = hashlib.sha256(overview_text.encode()).hexdigest()

        return UniverseHardCanonDoc.objects.create(
            universe=universe,
            source_type="worldgen",
            title=f"{request.name} - World Overview",
            raw_text=overview_text,
            checksum=checksum,
            never_compact=True,
        )

    def preview(self, request: WorldgenRequest) -> dict:
        """
        Preview what would be generated without creating anything.

        Args:
            request: WorldgenRequest with generation parameters

        Returns:
            Preview of what would be created
        """
        validation_errors = self._validate_request(request)
        if validation_errors:
            return {"valid": False, "errors": validation_errors}

        return {
            "valid": True,
            "universe_name": request.name,
            "tone_profile": self._build_tone_profile(request),
            "rules_profile": self._build_rules_profile(request),
            "content_to_generate": {
                "species": request.max_species if request.generate_species else 0,
                "classes": request.max_classes if request.generate_classes else 0,
                "backgrounds": request.max_backgrounds if request.generate_backgrounds else 0,
                "spells": request.max_spells if request.generate_spells else 0,
                "items": request.max_items if request.generate_items else 0,
                "monsters": request.max_monsters if request.generate_monsters else 0,
                "feats": request.max_feats if request.generate_feats else 0,
            },
            "llm_available": self.llm_config is not None,
            "prompt_preview": self._build_worldgen_prompt(request)[:500] + "...",
        }
