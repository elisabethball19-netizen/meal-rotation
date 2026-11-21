# Meal Rotation — agent entry point

This repository is the ORIGINAL app, not a separate fresh rebuild. Use current modular code; do not reconstruct a historical monolithic index.html.

## Read selectively
Read only what the assigned issue or prompt names. Do NOT load the docs/ folder by default; for a normal implementation task the issue is the scope and the code is the source of truth. Open a handoff file only when the issue points to it or the task needs that specific rule, and then read just the relevant section.
- [Vision](docs/handoff/01-app-vision.txt): product goals (planning/discussion only).
- [Development preferences](docs/handoff/02-development-preferences.txt): workflow/data rules (planning, handoff, or when the issue asks).
- [App experience](docs/handoff/03-app-experience.txt): accepted behavior; search it for the feature you touch.
- [Remaining work](docs/handoff/04-remaining-work.txt): short active list (open, held and awaiting-phone-test items).
- `docs/archive/` is history only: never read it unless an issue names it.

The latest explicit user instruction and approved task take precedence. These documents describe product intent and reported evidence, not a fresh audit. Historical docs may describe superseded stages.

## Implementation essentials
Reuse existing components; targeted edits and focused checks. No unrelated refactoring, broad audits or rewrites.
Preserve all saved data/localStorage compatibility. NEVER clear site data.
Keep existing meal-rotation-test.html equivalent where applicable, retaining isolated storage/test features; no extra versions.
Respect occurrence/plan/week isolation, cancellation, atomic updates, and Undo/Redo.
Work directly on main; commit/push for authorized implementation tasks. Documentation-only updates do not authorize app changes.
Use README and relevant existing test scripts to establish actual commands; report checks run, commit/push and real deployment status. Do not invent phone verification.
Read the assigned issue for scope. Do not implement the whole backlog. Mark code-complete work awaiting phone testing until confirmed.
Update only affected lasting decisions/backlog statuses; do not append conflicting corrections or rewrite every document.

## Workflow
Implementation is done directly by Claude; Codex is no longer used (2026-11-21). When the user approves a batch, implement only that batch, run focused checks on both apps, push to main, and give a phone checklist one item at a time. For sizeable batches use one scoped GitHub issue (REST API if GraphQL is blocked). Do not implement app changes from discussion alone. See CLAUDE.md and docs/handoff/02-development-preferences.txt.
