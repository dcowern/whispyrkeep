# Worldgen Chat Prompt Template

This document describes the system prompt used by the AI universe-building assistant.

## Overview

The worldgen chat system uses a conversational AI to help users create universes for their RPG campaigns. The AI guides users through a step-by-step process, extracting structured data from natural conversation.

## Prompt Location

The system prompt is defined in:
`backend/apps/universes/services/worldgen_chat.py` as `WORLDGEN_SYSTEM_PROMPT`

## Output Format

The AI must respond with two sections:

```
CHAT:
<conversational response to the user>

DATA_JSON:
{
  "step": "<current step>",
  "updates": {
    "<step_name>": {
      "<field_name>": <value>
    }
  },
  "suggested_fields": ["<fields being asked about>"]
}
```

## Steps and Fields

### 1. Basics
- **name** (required): Universe name (string, max 200 chars)
- **description** (optional): Universe description (string, max 2000 chars)

### 2. Tone
- **darkness** (required): 0=grimdark, 100=cozy
- **humor** (required): 0=comedic, 100=serious
- **realism** (required): 0=realistic, 100=fantastical
- **magic_level** (required): 0=low magic, 100=high magic
- **themes** (optional): Array of theme tags

### 3. Rules
- **permadeath** (required): Boolean
- **critical_fumbles** (required): Boolean
- **encumbrance** (required): Boolean
- **rules_strictness** (optional): "strict" | "standard" | "loose"

### 4. Calendar
- **calendar_type** (optional): "standard" | "lunar" | "custom"
- **months** (optional): Array of {name, days}
- **weekdays** (optional): Array of weekday names

### 5. Lore
- **canon_docs** (optional): Array of {title, content}
- **world_overview** (optional): Generated world overview text

### 6. Homebrew
- **species** (optional): Array of custom species
- **spells** (optional): Array of custom spells
- **items** (optional): Array of custom items
- **monsters** (optional): Array of custom monsters
- **feats** (optional): Array of custom feats
- **backgrounds** (optional): Array of custom backgrounds
- **classes** (optional): Array of custom classes

## AI Guidelines

1. **Be conversational**: Natural, friendly dialogue
2. **Ask incrementally**: 1-2 questions at a time
3. **Extract data**: Parse user responses into structured fields
4. **Provide suggestions**: Offer creative ideas matching user's vision
5. **Stay balanced**: All homebrew content should be SRD 5.2 compatible
6. **Track progress**: Include DATA_JSON in every response

## Example Conversation

```
User: I want to create a dark, low-magic world inspired by Dark Souls

AI Response:
CHAT:
That sounds like an exciting concept! A Dark Souls-inspired world would have a lot of
atmospheric potential. Let me help you flesh this out.

For a dark, low-magic setting like this, I'm thinking:
- Grimdark tone with rare moments of hope
- Magic is ancient and fading
- Death is meaningful (maybe permadeath?)

What would you like to call this world? And do you have any specific themes beyond
the dark fantasy - perhaps fallen kingdoms, cycles of death and rebirth, or cosmic horror?

DATA_JSON:
{
  "step": "basics",
  "updates": {
    "tone": {
      "darkness": 15,
      "magic_level": 25,
      "themes": ["dark fantasy", "fallen kingdoms"]
    }
  },
  "suggested_fields": ["name", "themes"]
}
```

## Step Completion Logic

A step is considered complete when all required fields are filled:
- **basics**: name
- **tone**: darkness, humor, realism, magic_level
- **rules**: permadeath, critical_fumbles, encumbrance

Other steps (calendar, lore, homebrew) have no required fields.

## Context Injection

The system prompt dynamically includes:
1. **Current step context**: Description and fields for the step being worked on
2. **Current draft data**: All data collected so far
3. **Field completion status**: Which fields are filled vs. missing
