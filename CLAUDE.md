# Meal Rotation — Claude Entry Point

This repository is the ORIGINAL app, not a separate fresh rebuild. Use current modular code; do not reconstruct a historical monolithic `index.html`. Keep the core web app in 100% pure vanilla HTML, CSS, and JavaScript with zero build tools or frontend frameworks.

## Read Selectively
- [Vision](docs/handoff/01-app-vision.txt): product goals and simplicity.
- [Development preferences](docs/handoff/02-development-preferences.txt): workflow/data rules; read for implementation.
- [App experience](docs/handoff/03-app-experience.txt): relevant accepted behavior.
- [Remaining work](docs/handoff/04-remaining-work.txt): state, evidence, and deferred scope.

The latest explicit user instruction and approved task take precedence. These documents describe product intent and reported evidence, not a fresh audit. Historical docs may describe superseded stages.

## Implementation Essentials
- Reuse existing components; make targeted edits and run focused checks. No unrelated refactoring, broad audits, or rewrites.
- Preserve all saved data and `localStorage` compatibility (`version: 2` JSON import/export). NEVER clear site data.
- Keep existing `meal-rotation-test.html` equivalent where applicable, retaining isolated storage/test features; do not create extra versions.
- Respect occurrence/plan/week isolation, cancellation, atomic updates, and Undo/Redo.
- For authorized implementation tasks, commit and push changes cleanly directly to `main` (standing user instruction, 2026-11-17: always push to `main` so the installed PWA updates, including in Claude web/mobile cloud sessions; no pull request unless the user asks for one). Documentation-only updates do not authorize app changes.
- Use `README` and relevant existing test scripts to establish actual commands; report checks run, commit/PR status, and real deployment status. Do not invent phone verification.
- After every batch, run the phone test as a simplified checklist, ONE item at a time, in plain text (no answer buttons): send only the next item (short: what to do, what should happen), then wait. The user may reply pass/fail or discuss the item freely; resolve any discussion before sending the next item. Never send the whole list at once (standing user instruction, updated 2026-11-19).
- Opinion or discussion questions get discussion only; build only on an explicit go-ahead. When the user says they have several things, collect them all before building.
- UI conventions: toggles on the right side use a down chevron (flips up when open); left-side nested toggles use a small right arrow (turns down when open). Switches sit to the left of their label.
- Read the assigned issue or prompt for scope. Do not implement the whole backlog. Mark code-complete work as awaiting phone testing until confirmed.
- Update only affected lasting decisions/backlog statuses; do not append conflicting corrections or rewrite every document.
- 
## Execution Scope Rules (Default to Minimal Blast Radius)
- **Implicitly Scoped Edits:** When asked for a visual or style tweak (e.g., "fix button padding", "change font color"), automatically inspect and edit *only* `styles.css` unless another file is explicitly named.
- **Single-File Isolation:** Never touch or refactor surrounding markup or logic scripts unless the requested feature explicitly requires it. If a tweak can be resolved in a single CSS rule or HTML element, keep the diff strictly restricted to that one file.
- 
## Brainstorming & Issue Planning Workflow (Claude Chat / Projects)
- Do not implement app changes from brainstorming or discussion alone—wait for explicit approval.
- When the user approves a batch of changes, follow the scoped workflow in `docs/handoff/02-development-preferences.txt`: update only relevant reference facts, outline or create one scoped GitHub issue, and provide:
  1. The issue link or scoped summary,
  2. A short, token-efficient Claude Code prompt referencing that issue and `CLAUDE.md`, and
  3. A concise phone testing checklist.
- Note model selection when helpful (e.g., use **Sonnet** for routine CSS/UI tweaks and **Opus** for complex multi-file logic). Keep follow-up corrections in the existing feature issue/thread where appropriate.
