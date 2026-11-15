# Meal Rotation — agent entry point

This repository is the ORIGINAL app, not a separate fresh rebuild. Use current modular code; do not reconstruct a historical monolithic index.html.

## Read selectively
- [Vision](docs/handoff/01-app-vision.txt): product goals and simplicity.
- [Development preferences](docs/handoff/02-development-preferences.txt): workflow/data rules; read for implementation.
- [App experience](docs/handoff/03-app-experience.txt): relevant accepted behavior.
- [Remaining work](docs/handoff/04-remaining-work.txt): state, evidence and deferred scope.

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

## Automatic ChatGPT-to-Codex handoff
When the user approves a batch, follow the issue-based handoff workflow in Development preferences without requiring the user to repeat it: update only relevant reference facts, create or update one scoped issue, then supply its link, a short Codex instruction referencing that issue and AGENTS.md, and a phone checklist. Tell the user to select Sol Light outside the Codex prompt. Keep follow-up corrections in the existing feature issue/thread where appropriate. Do not implement app changes from discussion alone.
