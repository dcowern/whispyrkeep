# WhispyrKeep

A web-based, single-player, text-only roleplaying game where an LLM functions as the Dungeon Master.

## Overview

WhispyrKeep allows players to co-create "Universes" (world bibles + rules variants + content + lore) with an AI, then run scenarios and campaigns inside those universes. The game enforces SRD 5.2 mechanics deterministically while the LLM provides narrative and requests rolls.

### Key Features

- **LLM-powered Dungeon Master**: Fully conversational, turn-based chat play
- **SRD 5.2 Mechanics**: Backend-enforced rules with deterministic dice rolls
- **Universe Builder**: Co-create reusable worlds with tone sliders and rules toggles
- **Event-sourced Gameplay**: Full rewind capability (no branching)
- **Lore Management**: ChromaDB-powered lore with Hard Canon and Soft Lore separation
- **ND-Friendly UX**: Dark mode, low-stim mode, decision menus, accessibility controls

## Tech Stack

- **Frontend**: Angular 18 SPA
- **Backend**: Django 5 / Django REST Framework
- **Database**: PostgreSQL 16
- **Task Queue**: Celery + Redis
- **Vector Store**: ChromaDB
- **LLM**: OpenAI-compatible endpoint (BYO key)

## Project Structure

```
whispyrkeep/
├── frontend/          # Angular 18 SPA
├── backend/           # Django 5 + DRF API
├── ops/               # Docker, CI/CD configs
├── infra/             # Infrastructure as code
├── scripts/           # Development scripts
├── docs/              # Documentation
│   ├── SYSTEM_DESIGN.md
│   ├── prompts/       # LLM prompt templates
│   └── api/           # OpenAPI specs
└── .claude/           # Claude Code agent commands
    └── commands/
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.12+ (for backend development)

### Development Setup

```bash
# Clone the repository
git clone <repo-url>
cd whispyrkeep

# Start all services
docker compose up -d

# Access the application
# Frontend: http://localhost:4200
# Backend API: http://localhost:8000
# ChromaDB: http://localhost:8001
```

### Running Tests

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test

# All tests with coverage
./scripts/test.sh
```

## Development

See [CLAUDE.md](./CLAUDE.md) for AI-assisted development guidelines.

See [docs/SYSTEM_DESIGN.md](./docs/SYSTEM_DESIGN.md) for full system architecture.

See [TODO.md](./TODO.md) for current development status and roadmap.

## Legal

This work includes material from the System Reference Document 5.2 ("SRD 5.2") by Wizards of the Coast LLC, available at [https://www.dndbeyond.com/srd](https://www.dndbeyond.com/srd). The SRD 5.2 is licensed under the Creative Commons Attribution 4.0 International License, available at [https://creativecommons.org/licenses/by/4.0/legalcode](https://creativecommons.org/licenses/by/4.0/legalcode).

## License

[TBD]
