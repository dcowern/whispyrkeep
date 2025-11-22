# /build - Intelligent Build Orchestrator

You are the build orchestrator for WhispyrKeep. Your job is to read TODO.md, understand current progress, and intelligently continue implementation.

## Instructions

1. **Read TODO.md** to understand current project status
2. **Identify the next task** to work on based on:
   - Build order (Epic 0 → 1 → 2+3 → 4+5 → 7 → 9 → 8 → 10 → 12 → 11 → 13+14)
   - Dependencies between tickets
   - Any `IN_PROGRESS` tasks should be completed first
   - Then find the first `NOT_STARTED` task in the current epic
3. **Update TODO.md** status as you work:
   - Mark task `IN_PROGRESS` when starting
   - Mark task `TESTING` when implementation complete
   - Mark task `DONE` when tests pass
4. **Run tests** after each implementation
5. **Commit changes** with conventional commit messages

## Command Arguments

Parse the user's input for optional arguments:
- `epic:N` - Focus on specific epic (e.g., `/build epic:1`)
- `ticket:X.Y.Z` - Work on specific ticket (e.g., `/build ticket:1.1.1`)
- `test` - Run tests and update TODO status only
- `status` - Show current progress summary
- (no args) - Continue from last incomplete task

## Workflow

### Starting a New Task
```
1. Read TODO.md
2. Find next task per build order
3. Update status to IN_PROGRESS
4. Read relevant docs (SYSTEM_DESIGN.md, CLAUDE.md)
5. Implement with tests
6. Run tests
7. Update status to TESTING or DONE
8. Commit with descriptive message
9. Repeat or pause for user feedback
```

### Resume After Interruption
```
1. Read TODO.md
2. Find any IN_PROGRESS tasks
3. Read the code/tests for that task
4. Continue where left off
5. Complete and update status
```

## Quality Gates

Before marking any task DONE:
- [ ] Implementation matches SYSTEM_DESIGN.md spec
- [ ] Unit tests written and passing (>80% coverage for the module)
- [ ] Code follows project conventions (see CLAUDE.md)
- [ ] No linting errors
- [ ] Integration points tested if applicable

## Epic Milestones

After completing each epic, pause and:
1. Summarize what was built
2. List any deviations from spec
3. Note any technical debt
4. Suggest user testing/feedback areas
5. Update Progress Summary in TODO.md

## Example Session

```
User: /build

Claude: Reading TODO.md...

Current Status:
- Epic 0: 1/3 complete
- Next task: 0.1.2 - Docker Compose baseline

Starting ticket 0.1.2...
[Updates TODO.md status to IN_PROGRESS]
[Creates docker-compose.yml]
[Creates service configurations]
[Verifies services start]
[Updates TODO.md status to DONE]

Ticket 0.1.2 complete. Continuing to 0.1.3...
```

Now read TODO.md and begin work based on the user's input (if any) or the next available task.
