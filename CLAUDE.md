# CLAUDE.md - AI Development Guide for WhispyrKeep

## Project Overview

WhispyrKeep is an LLM-powered single-player RPG with SRD 5.2 mechanics. The system design is in [docs/SYSTEM_DESIGN.md](./docs/SYSTEM_DESIGN.md).

## Quick Reference

### Tech Stack
- **Frontend**: Angular 18 (standalone components, signals)
- **Backend**: Django 5.x, DRF 3.15+, Python 3.12+
- **Database**: PostgreSQL 16
- **Async**: Celery 5.x + Redis 7.x
- **Vector DB**: ChromaDB
- **Testing**: pytest (backend), Jest/Karma (frontend)

### Key Directories
```
frontend/src/app/           # Angular components, services, routes
backend/whispyrkeep/        # Django project
backend/apps/               # Django apps (auth, characters, universes, campaigns, etc.)
backend/mechanics/          # SRD mechanics engine (deterministic)
docs/prompts/               # LLM prompt templates
ops/                        # Docker, CI/CD
```

## Build Commands

```bash
# Start dev environment
docker compose up -d

# Backend
cd backend && python manage.py runserver
cd backend && pytest                        # Run tests
cd backend && pytest --cov                  # With coverage
cd backend && python manage.py makemigrations
cd backend && python manage.py migrate

# Frontend
cd frontend && npm start                    # Dev server
cd frontend && npm test                     # Run tests
cd frontend && npm run build                # Production build
cd frontend && npm run lint                 # Lint check

# Full test suite
./scripts/test.sh
```

## Architecture Principles

### Backend Architecture

1. **Event-Sourced Turns**: Every turn is a TurnEvent with deterministic replay
2. **Deterministic Mechanics**: All dice rolls happen server-side with seeded RNG
3. **State Patches**: LLM outputs JSON patches, backend validates and applies
4. **Lore Separation**: Hard Canon (immutable) vs Soft Lore (compactable)

### Django App Structure
```
apps/
├── auth/           # User authentication, profiles, settings
├── llm_config/     # BYO-key management, encrypted storage
├── characters/     # CharacterSheet CRUD, SRD validation
├── universes/      # Universe, HardCanonDoc, homebrew catalog
├── campaigns/      # Campaign, TurnEvent, CanonicalState
├── mechanics/      # Dice, checks, saves, combat resolution
├── lore/           # ChromaDB integration, embeddings, compaction
├── timeline/       # Calendar, time system, scenario placement
└── exports/        # JSON/MD/PDF export jobs
```

### Frontend Architecture

1. **Standalone Components**: Use Angular 18 standalone components
2. **Signals**: Prefer signals over RxJS where appropriate
3. **State Management**: NgRx for complex state, signals for local
4. **Accessibility First**: All components must support ND-friendly modes

## Development Workflow

### Using /build Command

The `/build` command reads TODO.md and intelligently resumes work:

```bash
/build                      # Continue from last incomplete task
/build epic:1               # Build specific epic
/build test                 # Run tests and update TODO status
```

### TODO.md Status Values
- `NOT_STARTED` - Work not begun
- `IN_PROGRESS` - Currently being worked on
- `BLOCKED` - Waiting on dependency
- `TESTING` - Implementation complete, testing in progress
- `DONE` - Fully complete with tests passing

### Commit Conventions
```
feat(scope): description    # New feature
fix(scope): description     # Bug fix
test(scope): description    # Tests only
refactor(scope): description
docs(scope): description
chore(scope): description
```

Scopes: `auth`, `characters`, `universes`, `campaigns`, `mechanics`, `lore`, `frontend`, `ops`, `ci`

## Testing Requirements

### Backend Tests (pytest)

Every module needs:
1. **Unit tests** for business logic (>80% coverage)
2. **API tests** for endpoints
3. **Integration tests** for service interactions

```python
# Naming convention
test_<module>_<function>_<scenario>.py

# Example structure
backend/apps/mechanics/tests/
├── test_dice_roller.py
├── test_ability_checks.py
├── test_attack_resolution.py
└── test_condition_effects.py
```

### Mechanics Engine Tests (Critical)

The mechanics engine MUST have deterministic golden tests:
```python
# Example: Golden test for ability check
def test_ability_check_dc15_with_modifier():
    """Deterministic test with seeded RNG"""
    result = resolve_ability_check(
        character=mock_character(dex=14, stealth_proficiency=True),
        ability="dex",
        skill="stealth",
        dc=15,
        seed=42  # Deterministic
    )
    assert result.roll == 13  # Known output for seed=42
    assert result.modifier == 4  # +2 DEX, +2 proficiency
    assert result.total == 17
    assert result.success == True
```

### Frontend Tests (Jest)

1. **Component tests** for UI logic
2. **Service tests** for API integration
3. **E2E tests** for critical flows (Playwright)

## Key Implementation Notes

### LLM Integration

The LLM outputs structured responses:
```
DM_TEXT:
<narrative for player>

DM_JSON:
{
  "roll_requests": [...],
  "patches": [...],
  "lore_deltas": [...]
}
```

Backend parses, validates, and executes. Never trust LLM output directly.

### State Patch Validation

All patches must pass:
1. Schema validation (JSON Schema)
2. Path legality check
3. Value type/range validation
4. Monotonic time enforcement
5. Hard canon contradiction check

### Security Considerations

1. **API Keys**: AES-GCM encrypted at rest, never logged
2. **Content Safety**: Movie rating enforcement in prompts
3. **Injection Prevention**: Validate all LLM outputs server-side

## CI/CD Pipeline

### On PR
1. Lint (backend + frontend)
2. Unit tests
3. Integration tests
4. Build verification

### On Merge to Main
1. All PR checks
2. E2E tests
3. Docker image build
4. Deploy to staging

### Release
1. Tag-based deployment
2. Database migrations
3. Deploy to production

## Common Tasks

### Adding a New API Endpoint

1. Create serializer in `apps/<app>/serializers.py`
2. Create view in `apps/<app>/views.py`
3. Add URL in `apps/<app>/urls.py`
4. Write tests in `apps/<app>/tests/`
5. Update OpenAPI spec in `docs/api/`

### Adding a New Mechanic

1. Implement in `backend/mechanics/`
2. Add deterministic unit tests with golden outputs
3. Update roll spec schema if needed
4. Update validation rules
5. Document in `docs/prompts/` for LLM awareness

### Adding a Frontend Feature

1. Generate component: `ng generate component features/<name>`
2. Use standalone component pattern
3. Implement accessibility (keyboard nav, ARIA, ND modes)
4. Write component tests
5. Add route if needed

## Commands Available

Use `/build` command for orchestrated development:

```bash
/build                      # Continue from last incomplete task
/build epic:1               # Build specific epic
/build ticket:1.1.1         # Work on specific ticket
/build test                 # Run tests and update TODO status
/build status               # Show current progress
```

## Agents Available (`.claude/agents/`)

Specialized agents for different roles and skillsets:

### Architecture & Design
- **architect** - System architecture, component integration, technical standards
- **db-architect** - Database schema design, data modeling, index strategies
- **game-designer** - SRD mechanics, game balance, LLM DM behavior design

### Development
- **backend-dev** - Django/DRF development, API endpoints, services
- **frontend-dev** - Angular components, state management, routing
- **db-engineer** - Migrations, query optimization, database maintenance
- **devops** - CI/CD pipelines, Docker, deployment automation

### Design & UX
- **hcd** - Human-centered design, ND accessibility, user research
- **uiux** - Visual design, component library, responsive design

### Quality & Security
- **qa-engineer** - Test strategy, test plans, quality gates
- **tester** - Unit tests, integration tests, edge cases
- **security-engineer** - Security controls, encryption, input validation
- **security-auditor** - Code review, vulnerability assessment, compliance
- **red-team** - Penetration testing, attack simulation

### Documentation
- **technical-writer** - API docs, developer guides, prompt documentation

## Resources

- [System Design](./docs/SYSTEM_DESIGN.md) - Full architecture spec
- [TODO.md](./TODO.md) - Current status and roadmap
- [SRD 5.2](https://www.dndbeyond.com/srd) - Rules reference
