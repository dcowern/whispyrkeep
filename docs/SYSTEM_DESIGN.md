# System Design Document

**Project name (working):** *WhispyrKeep* (placeholder)
**Tech stack:** Angular 18 SPA + Django 5 / DRF + Postgres 16 + Celery + Redis + ChromaDB
**LLM interface:** OpenAI-compatible Chat Completions endpoint (BYO key)
**Rules baseline:** SRD 5.2 (2024) CC-BY-4.0

---

## 0. Executive Summary

You are building a web-based, single-player, text-only roleplaying game where an LLM functions as the Dungeon Master. The player and LLM can co-create "Universes" (world bibles + rules variants + content + lore), then run scenarios/campaigns inside those universes. The game enforces SRD 5.2 mechanics by having the LLM *request* rolls and mechanics while the backend performs deterministic computations (dice, DC checks, HP changes, conditions, time passage). Each turn produces:

1. Narrative DM response (text for player)
2. Mechanics/roll spec (structured)
3. JSON "state patch" applied to the canonical backend state
4. Lore deltas to be embedded into a per-universe ChromaDB vector store

Gameplay is event-sourced per turn with rewind (no branching). Universes preserve monotonic time across scenarios (no time travel, no causality loops). Lore is partitioned into **Hard Canon** (never contradicted; minimally compacted) and **Soft Lore** (rumors, legends, emergent play; aggressively compactable).

The UI/UX is elegant, responsive, and beautiful. It looks as good and functions as well on a mobile device as it does in a desktop browser.

---

## 1. Goals & Non-Goals

### 1.1 Goals

* **LLM-powered Dungeon Master:** fully conversational, turn-based chat play.
* **SRD 5.2 mechanics compliance:** enforced by backend validation + deterministic compute. SRD 5.2 is CC-BY-4.0 licensed, requiring specific attribution. ([D&D Beyond][1])
* **Universe Builder:** co-creation of reusable worlds with tone sliders and rules toggles.
* **Scenario/Campaign Runner:** user configurable length (one-shot ↔ campaign), failure style (fail-forward ↔ strict RAW).
* **Stateful + rewindable:** event-sourced turn deltas, rewind rewrites history; no branches.
* **Lore consistency:** per-universe lore curated and stored in ChromaDB; retrieved into prompts.
* **Time system:** SRD-ish calendar; immediate clock + multi-year timeline; scenarios positioned relative to known events.
* **Homebrew extension:** SRD by default; user+LLM can create substitutions/adapters for other genres (sci-fi etc.).
* **ND-friendly UX:** dark mode default, low-stim mode, concise recap toggle, decision menu option, freeform option.
* **Beautiful, responsive design:** looks amazing and is intuitive on any device or browser.

### 1.2 Non-Goals (initially)

* Multiplayer / co-op.
* Tactical grid/maps or VTT style movement.
* Hosted LLM inference (BYO endpoint only).
* Marketplace / sharing universes publicly (can be later).
* Non-SRD D&D IP (explicitly excluded).

---

## 2. User Roles & Primary Use Cases

### 2.1 Roles

* **Player (authenticated user):** creates characters, universes, campaigns; uploads lore docs; plays turns; rewinds.
* **System (backend services):** validates rules, maintains canonical state, runs dice, manages lore/time.
* **LLM DM (external model):** generates narrative + roll requests + state patches + lore deltas.

### 2.2 Primary Use Cases

1. **Create Character**
2. **Create Universe with LLM**
3. **Upload Seed Lore/Docs**
4. **Start Scenario/Campaign**
5. **Play Turn**
6. **Rewind to Prior Turn**
7. **Start Another Scenario in Same Universe**
8. **Export Universe/Campaign**

---

## 3. Licensing & Legal Requirements

### 3.1 SRD 5.2 Attribution

SRD 5.2 is under **Creative Commons Attribution 4.0**; you must include the exact SRD attribution statement in your product. ([D&D Beyond][1])

**Required attribution statement (must be included verbatim):**

> "This work includes material from the System Reference Document 5.2 ("SRD 5.2") by Wizards of the Coast LLC, available at [https://www.dndbeyond.com/srd](https://www.dndbeyond.com/srd). The SRD 5.2 is licensed under the Creative Commons Attribution 4.0 International License, available at [https://creativecommons.org/licenses/by/4.0/legalcode."](https://creativecommons.org/licenses/by/4.0/legalcode.")

### 3.2 Placement

* **In-app:** Footer "Legal / Credits" modal + About page.
* **Exports:** All JSON/Markdown/PDF exports include the attribution line.
* **Universe sharing (future):** attribution persists with any derivative content.

### 3.3 Product Identity Guardrail

System must prevent LLM from introducing non-SRD Wizards Product Identity (e.g., named monsters/settings). SRD legal text explicitly warns not to include other Wizard IP branding beyond attribution.
Implementation: "SRD-only" constraint + validation blocklists + user-homebrew allowance.

---

## 4. High-Level Architecture

### 4.1 Component Diagram (logical)

**Frontend**

* Angular SPA
  * Auth UI
  * Character Builder
  * Universe Builder (chat + sliders)
  * Campaign Runner (chat)
  * Lore Browser
  * Timeline Viewer
  * Settings/Accessibility

**Backend**

* Django + DRF API
  * Auth + profiles
  * Character Service
  * Universe Service
  * Campaign Service
  * Turn Engine (LLM orchestration)
  * Mechanics Engine (SRD rules compute)
  * World Clock Service
  * Lore Service (ChromaDB bridge)
  * Export Service

**Async**

* Celery workers
  * Lore ingestion + embedding
  * Lore compaction & summarization
  * Universe "pre-generation" (bulk monsters/items)
  * Export rendering jobs

**Stores**

* Postgres (canonical)
* Redis (celery broker + cache + ephemeral turn retries)
* ChromaDB (lore vectors per universe)

---

## 5. Data Model (Postgres)

### 5.1 Core Entities

#### User

* `id (uuid pk)`
* `email (unique)`
* `password_hash`
* `display_name`
* `created_at`
* `settings_json`
  * ui mode, ND options, safety defaults, endpoint prefs

#### LlmEndpointConfig

* `id`
* `user_id fk`
* `provider_name` (openai, azure-openai, local, etc.)
* `base_url`
* `api_key_encrypted` (AES-GCM with server KMS)
* `default_model`
* `created_at`, `updated_at`
* `is_active`

#### Universe

* `id`
* `user_id fk`
* `name`
* `description`
* `tone_profile_json`
  * sliders: grimdark/cozy, comedy/serious, low/high magic, optimism, cruelty, etc.
* `rules_profile_json`
  * SRD baseline + homebrew overrides
* `calendar_profile_json` (SRD-ish default)
* `current_universe_time` (datetime or custom struct)
* `canonical_lore_version` (int)
* `created_at`, `updated_at`
* `is_archived`

#### UniverseHardCanonDoc

* `id`
* `universe_id fk`
* `source_type` (upload, worldgen, user_edit)
* `title`
* `raw_text`
* `checksum`
* `created_at`
* `never_compact (bool)` default true

#### LoreChunk

* `id`
* `universe_id fk`
* `chunk_type` (hard_canon, soft_lore)
* `source_ref` (doc id / turn id)
* `text`
* `tags_json`
* `time_range_json`
  * start_year, end_year, in_universe_date
* `is_compacted (bool)`
* `supersedes_chunk_id (nullable fk)`
* `created_at`

#### CharacterSheet

* `id`
* `user_id fk`
* `universe_id fk nullable` (if universe-specific homebrew ties)
* `name`
* `species`
* `class`
* `subclass`
* `background`
* `level`
* `ability_scores_json`
* `skills_json`
* `proficiencies_json`
* `features_json`
* `spellbook_json`
* `equipment_json`
* `homebrew_overrides_json`
* `created_at`, `updated_at`

#### Campaign

* `id`
* `universe_id fk`
* `user_id fk`
* `character_sheet_id fk`
* `title`
* `mode` (scenario | campaign)
* `target_length` (short | medium | long | custom turns estimate)
* `failure_style` (fail_forward | strict_raw)
* `content_rating` (G | PG | PG13 | R | NC17)
* `start_universe_time`
* `status` (active | paused | ended)
* `created_at`, `updated_at`

#### TurnEvent

Event-sourced turn delta

* `id`
* `campaign_id fk`
* `turn_index` (int, monotonic)
* `user_input_text`
* `llm_response_text`
* `roll_spec_json` (what rolls were requested)
* `roll_results_json` (deterministic backend results)
* `state_patch_json` (validated patch from LLM)
* `canonical_state_hash` (hash after patch)
* `lore_deltas_json`
* `universe_time_after_turn`
* `created_at`

#### CanonicalCampaignState

Snapshot for fast loads

* `id`
* `campaign_id fk`
* `turn_index` (snapshot at)
* `state_json` (full)
* `created_at`

---

## 6. Canonical State Schema (JSON)

### 6.1 Campaign State (authoritative)

Top-level JSON stored in snapshots + derived by replaying TurnEvents.

```json
{
  "campaign_id": "...",
  "universe_id": "...",
  "turn_index": 42,
  "universe_time": {
    "year": 1023,
    "month": 7,
    "day": 14,
    "hour": 19,
    "minute": 20
  },
  "party": {
    "player": {
      "character_id": "...",
      "hp": { "current": 21, "max": 31, "temp": 0 },
      "conditions": ["prone"],
      "abilities": { "str": 16, "dex": 14, "con": 12, "int": 10, "wis": 8, "cha": 15 },
      "skills": { "perception": 3, "stealth": 5 },
      "resources": {
        "hit_dice": { "d8": { "max": 4, "spent": 1 } },
        "spell_slots": { "1": { "max": 4, "used": 2 }, "2": { "max": 2, "used": 0 } }
      },
      "inventory": [
        { "item_id": "i_sword_001", "qty": 1, "equipped": true, "charges": null }
      ],
      "money": { "gp": 12, "sp": 4, "cp": 0 }
    }
  },
  "world": {
    "location_id": "loc_tavern_12",
    "zones": { "...": { "flags": {}, "npcs_present": [] } },
    "quests": [
      { "quest_id": "q_bandits", "stage": 2, "flags": { "met_leader": true } }
    ],
    "npcs": {
      "npc_aldra": {
        "status": "alive",
        "attitude": "friendly",
        "location_id": "loc_tavern_12",
        "knowledge_flags": ["knows_player_name"]
      }
    },
    "factions": {},
    "global_flags": { "dragon_war_started": false }
  },
  "rules_context": {
    "srd_version": "5.2",
    "homebrew_allowed": true,
    "in_world_invention_allowed": false,
    "failure_style": "fail_forward"
  }
}
```

### 6.2 State Patch Contract (LLM → backend)

**LLM must output JSON Patch-like deltas** with strict schema. Example:

```json
{
  "patches": [
    { "op": "replace", "path": "/party/player/hp/current", "value": 18 },
    { "op": "add", "path": "/world/global_flags/orc_warlord_defeated", "value": true },
    { "op": "advance_time", "value": { "minutes": 10 } }
  ],
  "lore_deltas": [
    {
      "type": "soft_lore",
      "text": "The Black Pike Tavern is rumored to be haunted by sailors lost on the sea.",
      "tags": ["location", "rumor", "tavern"],
      "time_ref": { "year": 1023, "month": 7, "day": 14 }
    }
  ]
}
```

Backend validates:

* op types allowed
* path legality
* value types/ranges
* time ops monotonic
* no contradictions to hard canon

---

## 7. Mechanics Engine (Backend)

### 7.1 Responsibilities

* Parse LLM roll specs
* Resolve dice
* Apply SRD 5.2 rules deterministically
* Return results to LLM
* Reject illegal specs

### 7.2 Roll Spec Schema (LLM → backend)

```json
{
  "roll_requests": [
    {
      "id": "r1",
      "type": "ability_check",
      "ability": "dex",
      "skill": "stealth",
      "dc": 15,
      "advantage": "none",
      "reason": "Sneaking past guards"
    },
    {
      "id": "r2",
      "type": "attack_roll",
      "attacker": "player",
      "target": "npc_guard_2",
      "weapon_or_spell_id": "i_dagger_01",
      "advantage": "disadvantage"
    }
  ]
}
```

### 7.3 Deterministic Functions

* `roll_d20(advantage_state)`
* `roll_damage(dice_expr, modifiers)`
* `resolve_ability_check(character, ability, skill, dc)`
* `resolve_saving_throw(character, stat, dc)`
* `resolve_attack(attacker, target, attack_profile)`
* `apply_condition(target, condition, duration)`
* `long_rest(character)` / `short_rest(character)`
* `advance_time(state, delta)`

### 7.4 Validation

Reject if:

* roll type not in SRD baseline
* dc missing where required
* spell/item not in SRD or active homebrew list
* advantage flag invalid
* target unknown
* would violate monotonic time

On rejection:

1. Create a **TurnError** response to LLM describing schema/rule mismatch.
2. Auto-retry with LLM using "repair" prompt (max 2 retries).
3. If still invalid → return friendly error to user.

---

## 8. LLM Orchestration

### 8.1 Prompt Layers

1. **System Prompt (static)**
   * You are DM, SRD-only unless told otherwise.
   * During gameplay you may *not invent* new items/monsters unless explicitly enabled.
   * Must request rolls instead of rolling.
   * Must output **two blocks**: `DM_TEXT` and `DM_JSON`.
   * No non-SRD Wizards IP.

2. **Universe Prompt (dynamic)**
   * Hard canon summary
   * Tone slider values
   * Rules/homebrew allowed list
   * Content rating guardrails
   * Universe timeline & key events
   * Current universe time

3. **Campaign Prompt (dynamic)**
   * Scenario goals, length, failure style
   * Player character summary
   * Active quests, flags
   * Last N turns recap

4. **Lore Retrieval Injection (dynamic)**
   * Top K relevant hard canon chunks (K=3–5)
   * Top K soft lore chunks (K=3–5)
   * Filtered by era/time proximity

### 8.2 Turn Flow

1. User message arrives.
2. Backend builds context.
3. Backend calls LLM for **turn proposal**.
4. LLM outputs:
   * DM narrative
   * Roll spec
   * State patch (tentative)
   * Lore deltas
5. Backend runs mechanics on roll spec.
6. Backend calls LLM again with roll results for **final narration + patch reconciliation**.
7. Backend validates final patch and applies to canonical state.
8. TurnEvent persisted; lore deltas queued for embedding.

### 8.3 Output Format Required

LLM response MUST be:

```
DM_TEXT:
<player-visible narrative + options>

DM_JSON:
{
  "roll_requests": [...],
  "patches": [...],
  "lore_deltas": [...]
}
```

Backend parses by delimiter.

---

## 9. Universe Builder

### 9.1 Modes

1. **Guided Wizard**
   * Step-by-step forms + LLM chat helper.
2. **Freeform Co-write**
   * Pure chat to define world; UI extracts structure afterward.

### 9.2 Outputs

Universe creation must produce:

* **World Bible (hard canon doc)**
* **Bulk content lists**
  * monsters (SRD + new homebrew)
  * items (SRD + homebrew)
  * factions, locations, NPC seeds
* **Timeline anchors**
  * named events with year offsets
* **Tone profile**
* **Rules profile (genre adapters)**

### 9.3 World-Creation LLM Permission

During universe creation:

* LLM *may* invent monsters/items/feats/spells as homebrew.
* Must label each as:
  * SRD-derived
  * Homebrew
* Must assign **rarity/power tier** and suggested level band.

Post-creation:

* backend locks these into the homebrew catalog for that universe.

---

## 10. Lore System

### 10.1 Lore Types

* **Hard Canon**
  * User uploads
  * World-creation output
  * Explicit user edits marked canon
  * *Never contradicted*
* **Soft Lore**
  * Rumors, legends, emergent play
  * NPC hearsay
  * LLM flavor additions
  * *Can be retconned or disproven*

### 10.2 ChromaDB Collections

* One collection per universe:
  * `universe_{id}_hard`
  * `universe_{id}_soft`

Metadata for each chunk:

```json
{
  "chunk_id": "...",
  "universe_id": "...",
  "type": "hard_canon",
  "tags": ["npc","war","ancient"],
  "year_start": 1000,
  "year_end": 1023,
  "source_ref": "turn:42",
  "compacted": false
}
```

### 10.3 Retrieval Policy

Given current turn:

1. Determine current universe year Y.
2. Query hard canon top-K by semantic similarity with filter:
   * `year_start <= Y <= year_end` OR open range
3. Query soft lore top-K similarly, but allow "nearby era" (±200 years).
4. Return merged list to prompt assembler.

### 10.4 Compaction Policy

Celery job runs nightly or on threshold:

* **Hard canon**
  * compact **only if** collection size exceeds cap (configurable, e.g., 10k chunks)
  * compact by *grouping within same topic+era*; preserve all named entities
  * mark summarized chunk as hard canon; link superseded chunks
* **Soft lore**
  * compact aggressively:
    * by quest arc completion
    * by era windows
    * by "low retrieval frequency"
  * allow contradiction cleanup

Compaction produces:

* summary chunk
* list of superseded chunk ids
* preservation of citations to source turns

---

## 11. Time System

### 11.1 Calendar

* SRD-ish 365-day calendar, 12 months, 7-day weeks.
* Stored in universe `calendar_profile_json`.

### 11.2 Monotonic Rule

* **Universe time never decreases** in canonical state.
* Rewind rewrites history:
  * when rewound, all later TurnEvents are deleted (soft-deleted) and their soft lore is invalidated.
  * universe current time resets to snapshot time.

### 11.3 Scenario Placement

When starting scenario:

* User chooses relative placement:
  * "after X"
  * "before X"
  * "N years after/before"
* Backend resolves to fixed start date and locks it.
* If conflicts with existing canonical events, user must pick another anchor (no branching reality).

### 11.4 Rest & Downtime

* RAW short rest = 1 hour
* RAW long rest = 8 hours
* Backend validates any rest request against time and environment.

---

## 12. Frontend (Angular)

### 12.1 Global UX

* Dark mode default; light optional.
* Accessibility toggles in top bar.

### 12.2 ND-Friendly Features

* **Low-stim mode**
  * reduced animation
  * muted palette
  * simplified layout
* **Concise recap toggle**
  * show "last turn summary"
  * show "current objective"
* **Decision menu mode**
  * LLM outputs 3–6 concrete choices labeled A–F
  * user can click or type freeform anyway
* **Freeform mode**
  * no UI constraints; pure text entry
* **Readability controls**
  * font size, line spacing, dyslexia-friendly font option
* **Scroll anchoring**
  * keep input visible when history grows
* **Dice log panel**
  * collapsible mechanical view

### 12.3 Core Screens

1. **Login/Register**
2. **Home / Library**
   * Universes
   * Characters
   * Campaigns (active, paused, ended)
3. **Character Builder**
   * SRD tabs w/ search
   * Homebrew add/edit
4. **Universe Builder**
   * Wizard (steps)
   * Co-write chat
   * Tone sliders
   * Rules toggles
   * Upload lore
5. **Campaign Setup**
   * pick universe, character
   * length + failure style
   * content rating
   * scenario seed prompt
6. **Play Screen**
   * chat stream
   * options panel
   * inventory/character sidebar
   * world clock indicator
   * rewind button + timeline slider
7. **Lore Browser**
   * search + filters
   * canon vs rumor tabs
8. **Timeline Viewer**
   * eras, events, scenario anchors
9. **Settings**
   * endpoint config
   * accessibility defaults
   * export

---

## 13. Backend API (DRF)

### 13.1 Auth

* `POST /api/auth/register`
* `POST /api/auth/login`
* `POST /api/auth/logout`
* `GET /api/auth/me`

### 13.2 Endpoint Config

* `POST /api/llm/config` (create/update)
* `GET /api/llm/config`
* `DELETE /api/llm/config/{id}`

### 13.3 Characters

* `POST /api/characters`
* `GET /api/characters`
* `GET /api/characters/{id}`
* `PUT /api/characters/{id}`
* `DELETE /api/characters/{id}`

### 13.4 Universes

* `POST /api/universes`
* `GET /api/universes`
* `GET /api/universes/{id}`
* `PUT /api/universes/{id}`
* `POST /api/universes/{id}/worldgen` (LLM co-write)
* `POST /api/universes/{id}/lore/upload`
* `GET /api/universes/{id}/lore`
* `POST /api/universes/{id}/lore/edit`
* `GET /api/universes/{id}/timeline`

### 13.5 Campaigns

* `POST /api/campaigns`
* `GET /api/campaigns`
* `GET /api/campaigns/{id}`
* `PUT /api/campaigns/{id}` (pause/resume/end)
* `POST /api/campaigns/{id}/rewind` (turn_index)

### 13.6 Turns

* `POST /api/campaigns/{id}/turn`
  * body: user_input
  * response: DM_TEXT + updated sidebar state
* `GET /api/campaigns/{id}/turns?after=n`
* `GET /api/campaigns/{id}/state`
* `GET /api/campaigns/{id}/dice-log`

### 13.7 Exports

* `POST /api/universes/{id}/export?format=json|md|pdf`
* `POST /api/campaigns/{id}/export?format=json|md|pdf`
* `GET /api/exports/{job_id}`

---

## 14. Celery Tasks

1. `embed_lore_chunks(universe_id, chunk_ids)`
2. `compact_soft_lore(universe_id)`
3. `compact_hard_canon_if_needed(universe_id)`
4. `pre_generate_universe_catalog(universe_id)`
   * bulk monsters/items
5. `render_export(job_id, format)`
6. `rebuild_universe_timeline(universe_id)`

Redis queues:

* `lore_embed_queue`
* `lore_compaction_queue`
* `export_queue`

---

## 15. Security / Privacy

### 15.1 BYO-Key

* API keys encrypted at rest.
* Never logged.
* Only decrypted in memory for outbound call.

### 15.2 Content Safety

* Backend enforces per-campaign "movie rating":
  * prompt injection includes allowed bounds.
* Hard bans:
  * CSAM
  * graphic torture / sexual assault
  * harm to children/animals in graphic detail
* If LLM violates:
  * backend truncates/blocks response
  * re-asks LLM with "safe rewrite" instruction
  * user gets gentle warning

### 15.3 Prompt Injection / Jailbreaks

* System prompt explicitly ignores user attempts to override SRD/IP constraints.
* Backend validates roll specs and patches regardless of narrative.

---

## 16. Testing Strategy

### 16.1 Unit Tests

* mechanics engine determinism
* schema validators
* time monotonicity
* lore contradiction checks

### 16.2 Contract Tests

* LLM output parser robustness
* repair retry logic
* roll spec round-trip

### 16.3 Integration Tests

* full turn flow with mocked LLM
* universe creation to campaign play
* rewind correctness (state replay)

### 16.4 Golden Scenario Suites

* scripted adventures with fixed RNG seeds.
* verify state progression vs expected.

---

## 17. Deployment Notes

* Docker compose services:
  * `frontend`
  * `backend`
  * `postgres`
  * `redis`
  * `celery_worker`
  * `chromadb`
* Environment:
  * `LLM_DEFAULT_MODEL`
  * `CHROMA_URL`
  * `POSTGRES_URL`
  * `REDIS_URL`
  * `KMS_SECRET`

---

## 18. Rollout Plan (MVP → v1)

### MVP (playable)

* auth
* SRD character builder
* universe builder (wizard + co-write)
* campaign setup
* turn loop with deterministic dice
* lore embedding (no compaction yet)
* rewind
* exports JSON/MD

### v1

* soft lore compaction
* timeline viewer
* canon/rumor browser
* genre adapters
* robust safety tuning

---

[1]: https://media.dndbeyond.com/compendium-images/srd/5.2/SRD_CC_v5.2.pdf "SRD_CC_v5.2.pdf"
