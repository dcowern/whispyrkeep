# System Prompt Template

This document describes the system prompt used by the LLM Dungeon Master.

## Overview

The system prompt establishes the LLM's role as a Dungeon Master and defines:
- Output format requirements (DM_TEXT and DM_JSON)
- Roll request schema
- State patch operations
- Lore delta structure
- SRD compliance rules

## Prompt Location

The system prompt is defined in:
`backend/apps/campaigns/services/prompt_builder.py` as `SYSTEM_PROMPT_TEMPLATE`

## Output Format

The LLM must respond with two sections:

```
DM_TEXT:
<narrative for the player>

DM_JSON:
{
  "roll_requests": [...],
  "patches": [...],
  "lore_deltas": [...]
}
```

### Roll Requests

```json
{
  "id": "r1",
  "type": "ability_check|saving_throw|attack_roll|damage_roll",
  "ability": "str|dex|con|int|wis|cha",
  "skill": "skill_name or null",
  "dc": 15,
  "advantage": "none|advantage|disadvantage",
  "reason": "brief explanation"
}
```

### State Patches

```json
{
  "op": "replace|add|remove|advance_time",
  "path": "/party/player/hp/current",
  "value": 18
}
```

### Lore Deltas

```json
{
  "type": "hard_canon|soft_lore",
  "text": "New lore fact",
  "tags": ["tag1", "tag2"],
  "time_ref": {"year": 1023, "month": 7, "day": 14}
}
```

## Content Rating Guidelines

See `RATING_GUIDELINES` in prompt_builder.py for per-rating instructions.

## Failure Style Instructions

- **fail_forward**: Failures advance the story with complications
- **strict_raw**: Rules as written, consequences apply strictly
