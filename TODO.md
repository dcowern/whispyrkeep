# WhispyrKeep Development TODO

**Last Updated**: 2025-11-23
**Current Epic**: 7 - Campaigns

## Status Legend

| Status | Meaning |
|--------|---------|
| `NOT_STARTED` | Work not begun |
| `IN_PROGRESS` | Currently being worked on |
| `BLOCKED` | Waiting on dependency |
| `TESTING` | Implementation complete, testing in progress |
| `DONE` | Fully complete with tests passing |

---

## Build Order

1. Epic 0 → Epic 1 (DevOps + Auth + LLM config)
2. Epic 2 (SRD catalog) + Epic 3 (Characters)
3. Epic 4 (Universes) + Epic 5 (Lore baseline)
4. Epic 7 (Campaigns + state)
5. Epic 9 (Mechanics engine)
6. Epic 8 (Turn engine)
7. Epic 10 (Rewind)
8. Epic 12 (Play UI + builders)
9. Epic 11 (Exports)
10. Epic 13 + Epic 14 (Safety + hardening)

---

## EPIC 0 — Repo, Tooling, DevOps Foundations

### FEAT 0.1 — Monorepo Bootstrap

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 0.1.1 | Create monorepo skeleton | `DONE` | N/A |
| 0.1.2 | Docker Compose baseline | `DONE` | N/A |
| 0.1.3 | CI pipeline (GitHub Actions) | `DONE` | N/A |

---

## EPIC 1 — Backend Core (Django/DRF)

### FEAT 1.0 — Django Project Setup

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 1.0.1 | Create Django project | `DONE` | N/A |
| 1.0.2 | Postgres connection + migrations | `DONE` | N/A |

### FEAT 1.1 — Auth & User Settings

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 1.1.1 | User model & profile | `DONE` | `DONE` |
| 1.1.2 | Auth endpoints | `DONE` | `DONE` |
| 1.1.3 | User settings endpoints | `DONE` | `DONE` |

### FEAT 1.2 — LLM Endpoint Config

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 1.2.1 | LlmEndpointConfig model | `DONE` | `DONE` |
| 1.2.2 | LLM config API | `DONE` | `DONE` |
| 1.2.3 | Encryption utilities | `DONE` | `DONE` |

---

## EPIC 2 — SRD Rules + Homebrew Catalog

### FEAT 2.0 — SRD Baseline Data

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 2.0.1 | Import SRD 5.2 reference tables | `DONE` | `DONE` |
| 2.0.2 | SRD catalog API | `DONE` | `DONE` |

### FEAT 2.1 — Universe Homebrew Overlays

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 2.1.1 | UniverseHomebrew tables | `DONE` | `DONE` |
| 2.1.2 | Homebrew CRUD API | `DONE` | `DONE` |
| 2.1.3 | Catalog merge logic | `DONE` | `DONE` |

---

## EPIC 3 — Characters

### FEAT 3.0 — CharacterSheet Model + Schema

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 3.0.1 | CharacterSheet model | `DONE` | `DONE` |
| 3.0.2 | Character validation service | `DONE` | `DONE` |

### FEAT 3.1 — Character APIs

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 3.1.1 | Character CRUD endpoints | `DONE` | `DONE` |
| 3.1.2 | Leveling service | `DONE` | `DONE` |

---

## EPIC 4 — Universes

### FEAT 4.0 — Universe Model + CRUD

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 4.0.1 | Universe model | `DONE` | `DONE` |
| 4.0.2 | Universe CRUD API | `DONE` | `DONE` |

### FEAT 4.1 — Universe Builder LLM Co-write

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 4.1.1 | Worldgen orchestration endpoint | `DONE` | `DONE` |
| 4.1.2 | Bulk catalog pre-generation task | `DONE` | `DONE` |
| 4.1.3 | Tone & rules sliders persistence | `DONE` | `DONE` |

---

## EPIC 5 — Lore System + ChromaDB

### FEAT 5.0 — Hard Canon Ingestion

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 5.0.1 | Upload docs endpoint | `DONE` | `DONE` |
| 5.0.2 | Hard canon chunking + embedding | `DONE` | `DONE` |

### FEAT 5.1 — Soft Lore Ingestion

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 5.1.1 | Lore delta persistence | `DONE` | `DONE` |
| 5.1.2 | Soft lore embedding task | `DONE` | `DONE` |

### FEAT 5.2 — Lore Retrieval Service

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 5.2.1 | Chroma query wrapper | `DONE` | `DONE` |
| 5.2.2 | Lore injection assembler | `DONE` | `DONE` |

### FEAT 5.3 — Compaction

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 5.3.1 | Soft lore compaction job | `DONE` | `DONE` |
| 5.3.2 | Hard canon compaction escape hatch | `DONE` | `DONE` |

---

## EPIC 6 — Time System

### FEAT 6.0 — Calendar + Time Utils

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 6.0.1 | SRD-ish calendar module | `NOT_STARTED` | `NOT_STARTED` |
| 6.0.2 | Monotonic time validator | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 6.1 — Scenario Placement

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 6.1.1 | Relative time resolver | `NOT_STARTED` | `NOT_STARTED` |
| 6.1.2 | Universe timeline rebuild task | `NOT_STARTED` | `NOT_STARTED` |

---

## EPIC 7 — Campaigns

### FEAT 7.0 — Campaign Model + CRUD

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 7.0.1 | Campaign model | `NOT_STARTED` | `NOT_STARTED` |
| 7.0.2 | Campaign CRUD API | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 7.1 — Canonical State & Snapshots

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 7.1.1 | CanonicalCampaignState snapshot table | `NOT_STARTED` | `NOT_STARTED` |
| 7.1.2 | State replay engine | `NOT_STARTED` | `NOT_STARTED` |

---

## EPIC 8 — Turn Engine + LLM DM

### FEAT 8.0 — LLM Client

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 8.0.1 | OpenAI-compatible chat client | `NOT_STARTED` | `NOT_STARTED` |
| 8.0.2 | Retry + backoff | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 8.1 — Prompt System

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 8.1.1 | System prompt template | `NOT_STARTED` | N/A |
| 8.1.2 | Universe prompt builder | `NOT_STARTED` | `NOT_STARTED` |
| 8.1.3 | Campaign prompt builder | `NOT_STARTED` | `NOT_STARTED` |
| 8.1.4 | Lore injection | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 8.2 — Two-Stage Turn Flow

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 8.2.1 | Turn proposal call | `NOT_STARTED` | `NOT_STARTED` |
| 8.2.2 | Mechanics execution + second call | `NOT_STARTED` | `NOT_STARTED` |
| 8.2.3 | Turn persistence | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 8.3 — Repair Loop

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 8.3.1 | Patch/roll validation | `NOT_STARTED` | `NOT_STARTED` |
| 8.3.2 | Auto-repair prompt | `NOT_STARTED` | `NOT_STARTED` |

---

## EPIC 9 — Mechanics Engine

### FEAT 9.0 — Dice + Core Resolution

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 9.0.1 | Dice roller | `NOT_STARTED` | `NOT_STARTED` |
| 9.0.2 | Ability checks / saves | `NOT_STARTED` | `NOT_STARTED` |
| 9.0.3 | Attack + damage resolution | `NOT_STARTED` | `NOT_STARTED` |
| 9.0.4 | Conditions | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 9.1 — Resting & Resources

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 9.1.1 | Short/long rest | `NOT_STARTED` | `NOT_STARTED` |

---

## EPIC 10 — Rewind (No Branching)

### FEAT 10.0 — Backend Rewind

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 10.0.1 | Rewind endpoint | `NOT_STARTED` | `NOT_STARTED` |
| 10.0.2 | Lore invalidation | `NOT_STARTED` | `NOT_STARTED` |

---

## EPIC 11 — Exports

### FEAT 11.0 — Export Jobs

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 11.0.1 | Export job model | `NOT_STARTED` | `NOT_STARTED` |
| 11.0.2 | Universe export | `NOT_STARTED` | `NOT_STARTED` |
| 11.0.3 | Campaign export | `NOT_STARTED` | `NOT_STARTED` |

---

## EPIC 12 — Frontend App (Angular)

### FEAT 12.0 — Angular Bootstrap

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 12.0.1 | Angular 18 project | `NOT_STARTED` | N/A |
| 12.0.2 | API client layer | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 12.1 — Auth UI

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 12.1.1 | Login/register screens | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 12.2 — Home / Library

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 12.2.1 | Dashboard | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 12.3 — Character Builder UI

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 12.3.1 | SRD picker UI | `NOT_STARTED` | `NOT_STARTED` |
| 12.3.2 | Homebrew editor | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 12.4 — Universe Builder UI

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 12.4.1 | Wizard flow | `NOT_STARTED` | `NOT_STARTED` |
| 12.4.2 | Co-write chat mode | `NOT_STARTED` | `NOT_STARTED` |
| 12.4.3 | Lore upload UI | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 12.5 — Campaign Setup UI

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 12.5.1 | Setup screen | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 12.6 — Play Screen

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 12.6.1 | Chat stream | `NOT_STARTED` | `NOT_STARTED` |
| 12.6.2 | Decision menu mode | `NOT_STARTED` | `NOT_STARTED` |
| 12.6.3 | Sidebar | `NOT_STARTED` | `NOT_STARTED` |
| 12.6.4 | Dice log panel | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 12.7 — Accessibility & ND Features

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 12.7.1 | Low-stim toggle | `NOT_STARTED` | `NOT_STARTED` |
| 12.7.2 | Concise recap toggle | `NOT_STARTED` | `NOT_STARTED` |
| 12.7.3 | Readability controls | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 12.8 — Rewind UI

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 12.8.1 | Timeline slider/turn picker | `NOT_STARTED` | `NOT_STARTED` |
| 12.8.2 | Rewind confirmation modal | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 12.9 — Lore Browser UI

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 12.9.1 | Canon vs rumor tabs | `NOT_STARTED` | `NOT_STARTED` |
| 12.9.2 | Lore search | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 12.10 — Timeline Viewer UI

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 12.10.1 | Era + event visual | `NOT_STARTED` | `NOT_STARTED` |

### FEAT 12.11 — Export UI

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 12.11.1 | Export buttons | `NOT_STARTED` | `NOT_STARTED` |

---

## EPIC 13 — Safety + Moderation

### FEAT 13.0 — Campaign Rating Enforcement

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 13.0.1 | Rating profiles | `NOT_STARTED` | `NOT_STARTED` |
| 13.0.2 | Output filter | `NOT_STARTED` | `NOT_STARTED` |

---

## EPIC 14 — QA, Docs, Hardening

### FEAT 14.0 — Testing

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 14.0.1 | Mechanics unit tests | `NOT_STARTED` | N/A |
| 14.0.2 | Turn-flow integration tests | `NOT_STARTED` | N/A |
| 14.0.3 | Rewind tests | `NOT_STARTED` | N/A |

### FEAT 14.1 — Documentation

| Ticket | Description | Status | Tests |
|--------|-------------|--------|-------|
| 14.1.1 | Prompt docs | `NOT_STARTED` | N/A |
| 14.1.2 | OpenAPI spec | `NOT_STARTED` | N/A |
| 14.1.3 | SRD licensing doc | `NOT_STARTED` | N/A |

---

## Progress Summary

| Epic | Total | Done | In Progress | Not Started |
|------|-------|------|-------------|-------------|
| 0 | 3 | 3 | 0 | 0 |
| 1 | 8 | 8 | 0 | 0 |
| 2 | 5 | 5 | 0 | 0 |
| 3 | 4 | 4 | 0 | 0 |
| 4 | 5 | 5 | 0 | 0 |
| 5 | 8 | 8 | 0 | 0 |
| 6 | 4 | 0 | 0 | 4 |
| 7 | 4 | 0 | 0 | 4 |
| 8 | 10 | 0 | 0 | 10 |
| 9 | 5 | 0 | 0 | 5 |
| 10 | 2 | 0 | 0 | 2 |
| 11 | 3 | 0 | 0 | 3 |
| 12 | 23 | 0 | 0 | 23 |
| 13 | 2 | 0 | 0 | 2 |
| 14 | 6 | 0 | 0 | 6 |
| **TOTAL** | **92** | **33** | **0** | **59** |
