# WhispyrKeep Prompt Reference

This document provides comprehensive documentation for the LLM prompt system used in WhispyrKeep.

## Table of Contents

1. [Overview](#overview)
2. [System Prompt Structure](#system-prompt-structure)
3. [Universe Context](#universe-context)
4. [Campaign Context](#campaign-context)
5. [Lore Injection](#lore-injection)
6. [Content Rating Guidelines](#content-rating-guidelines)
7. [Output Schema](#output-schema)
8. [Best Practices](#best-practices)

## Overview

WhispyrKeep uses a multi-component prompt system to enable the LLM to function as a Dungeon Master. The prompt is assembled dynamically based on:

- Base system prompt (role, rules, output format)
- Universe context (tone, rules, homebrew)
- Campaign context (current state, character)
- Retrieved lore (RAG from ChromaDB)
- Content rating guidelines
- Previous turn history

## System Prompt Structure

The system prompt is built in `backend/apps/campaigns/services/prompt_builder.py`.

### Base Prompt Components

```python
prompt = (
    SYSTEM_PROMPT_TEMPLATE           # Core DM instructions
    + universe_context               # Universe details
    + campaign_context               # Campaign state
    + lore_context                   # Retrieved lore
    + rating_guidelines              # Content restrictions
)
```

### Core Role Definition

The LLM is instructed to:
1. Act as a Dungeon Master following SRD 5.2 rules
2. Create engaging narrative responses
3. Request dice rolls when mechanics are needed
4. Apply state patches for game state changes
5. Record new lore discoveries

## Universe Context

Universe context includes:

### Tone Settings

Sliders from 0-100 that influence narrative style:

| Setting | Low (0) | High (100) |
|---------|---------|------------|
| Darkness | Light, hopeful | Grim, bleak |
| Humor | Serious, dramatic | Comedic, lighthearted |
| Realism | Fantastical, mythic | Grounded, realistic |
| Magic Level | Low magic, rare | High magic, common |

### Optional Rules

Boolean flags for variant rules:

- `permadeath` - Character death is permanent
- `critical_fumbles` - Natural 1 has mechanical consequences
- `encumbrance` - Track carrying capacity strictly

## Campaign Context

Campaign context includes:

### Character State

```json
{
  "name": "Aria Brightwood",
  "class": "Fighter",
  "level": 5,
  "hp": { "current": 45, "max": 52 },
  "conditions": ["exhaustion_1"],
  "spell_slots": { "1": 2, "2": 1 },
  "equipment": [...]
}
```

### World State

```json
{
  "location": "Thornwood Village",
  "time": { "year": 1023, "month": "Mirtul", "day": 14, "hour": 14 },
  "active_quests": [...],
  "npcs_present": [...]
}
```

## Lore Injection

### Hard Canon (Immutable)

Retrieved from ChromaDB, hard canon represents established facts that cannot be contradicted:

```
[HARD CANON]
- The Dragon Queen Tiamat was banished in the Age of Binding
- Thornwood Village was founded by refugees from the Sundering
[END HARD CANON]
```

### Soft Lore (Compactable)

Soft lore represents accumulated narrative that may be compacted or pruned:

```
[CAMPAIGN LORE]
- Aria heard rumors of goblins in the eastern woods
- The innkeeper mentioned a haunted tower
[END CAMPAIGN LORE]
```

## Content Rating Guidelines

### G (General Audiences)

- Combat described abstractly ("you defeat the goblin")
- No blood, gore, or graphic violence
- No profanity
- No mature themes
- No horror elements

### PG (Parental Guidance)

- Mild combat descriptions ("your sword strikes true")
- Mild profanity allowed (damn, hell)
- Mild peril and suspense
- No graphic violence or gore

### PG-13 (Parents Strongly Cautioned)

- Moderate combat descriptions
- Some blood/injury descriptions
- Moderate language
- Suspense and mild horror
- Romantic tension allowed

### R (Restricted)

- Graphic combat descriptions
- Strong language allowed
- Intense horror and violence
- Adult themes
- No explicit sexual content

### NC-17 (Adults Only)

- No content restrictions
- All themes allowed
- Full creative freedom

## Output Schema

### DM_TEXT Section

Free-form narrative text for the player:

```
DM_TEXT:
The tavern falls silent as you enter, all eyes turning to regard the
stranger. The barkeep, a grizzled dwarf with a scarred face, sets down
his rag and nods toward an empty stool at the bar.

"What'll it be, traveler?"
```

### DM_JSON Section

Structured game data:

```json
{
  "roll_requests": [
    {
      "id": "r1",
      "type": "ability_check",
      "ability": "cha",
      "skill": "persuasion",
      "dc": 12,
      "advantage": "none",
      "reason": "Convincing the barkeep to share information"
    }
  ],
  "patches": [
    {
      "op": "replace",
      "path": "/location/current",
      "value": "The Rusty Tankard"
    }
  ],
  "lore_deltas": [
    {
      "type": "soft_lore",
      "text": "The barkeep at the Rusty Tankard is named Grimnak",
      "tags": ["npc", "thornwood"]
    }
  ]
}
```

### Roll Request Types

| Type | Description |
|------|-------------|
| `ability_check` | Skill or ability check vs DC |
| `saving_throw` | Saving throw vs effect |
| `attack_roll` | Attack vs AC |
| `damage_roll` | Damage after hit |

### Patch Operations

| Operation | Description |
|-----------|-------------|
| `replace` | Replace value at path |
| `add` | Add new value (arrays, objects) |
| `remove` | Remove value at path |
| `advance_time` | Special: advance game time |

## Best Practices

### For Prompt Authors

1. **Be Specific**: Include concrete examples in prompts
2. **Set Boundaries**: Clearly define what content is allowed
3. **Provide Context**: Include relevant lore and state
4. **Limit History**: Only include recent turns (3-5)

### For LLM Responses

1. **Always use both sections**: DM_TEXT and DM_JSON are required
2. **Request rolls appropriately**: Don't assume outcomes
3. **Respect hard canon**: Never contradict established facts
4. **Apply rating guidelines**: Follow content restrictions

### Token Optimization

- Compress lore context when approaching token limits
- Prioritize recent and relevant lore
- Summarize older turn history
- Use compact state representations
