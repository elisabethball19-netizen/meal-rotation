# Issue #120 verification

Implemented/code-checked; awaiting physical phone testing. Only #120 is implemented; #121–#124 remain queued.

The original modular app and existing embedded test app retain their storage adapters and saved identities. No data reset or scheduling-algorithm migration was introduced. The week-start UI dispatches the existing rotation operation once, keeps its active-plan eligible scope and manual protections, and adds affected cooking-state/manual-grocery data to existing Undo/Redo. An entirely unchecked checklist is a no-op; an empty eligible list explains the situation and disables confirmation.

## Checks run

- `python3 tests/meal_plan_batch120_browser.py` — PASS in disposable Chromium touch contexts for **both** existing apps. Covers storage-exact week preview/return, fixed-date weekday captions, six direct card actions, ordinary and linked-side pickers, staged editor cancellation, skip/empty/resume and linked protection, selective carry-forward, cooked dates, checked manual cleanup, prep checks, cooking progress/scaling and whole-operation Undo/Redo. Also covers all-selected single dispatch/reentry, no eligible occurrences, hidden/restored slots, reachable horizontal overflow, fixed navigation and keyboard/dialog/selection hiding, narrow/short viewports, old global wake preference/reload, supported and denied wake requests, background/foreground, disable, close and a pending request resolving after close. The test-app working-storage sentinel and unrelated storage survive.
- `python3 tests/quota_backup_static.py` — PASS: modular/embedded syntax, its existing changed-block parity checks, JSON chooser checks, centralized journal writers and whitespace.
- `node --check grocery.js`, `recipes.js`, `rotation.js`, `service-worker.js` — PASS. The preceding static check also covers `ui.js` and all inline test-app scripts.
- `bash scripts/post-merge.sh` — PASS; static app files ready, no build or installation required.
- `git diff --check` — PASS.
- Inspected 360px screenshots of the collapsed/expanded meal plan and week-start dialog. Fixed a disclosure placement issue found in that inspection. Browser checks also exercise a 320×420 dialog.

An attempted reuse of `skipped_empty_rotation_browser.exact(..., 'skip-empty')` could not reach its scenarios: its older setup failed with `ReferenceError: slotTest is not defined` in `promotion_schedule_browser.setup`. No pass is claimed for that older fixture. The new focused suite exercises the relevant current UI and operations in both storage namespaces instead. Other batch tests/source were left unchanged.

Additional focused viewer geometry checks passed for both apps at 320px and 360px: all six toolbar controls share one row, retain 44px targets and stay within the viewport. This corrects the new wake icon wrapping Open recipes into a second row.

The offline shell version is v145. Push and actual GitHub Pages deployment evidence must be checked separately; passing local checks alone does not establish deployment.

## Pending phone checklist

- Check both week tabs/dates without advancing; scroll long custom slots and reach +. Toggle multiple slots off/on and confirm saved plans and grocery scope.
- Expand ordinary/linked meals, exercise all six actions and empty/resume access; check that no tap passes through a closing dialog.
- Start next week with a meal unchecked; verify carry-forward and groceries, cooked preference, X cancellation, Undo and Redo.
- Scroll every page; confirm the bottom bar clears content, hides for the keyboard/popups/group selection, and returns.
- Check wake preference across recipes/relaunch, lock release on background/close and return when enabled; confirm prep rows have no olive stripe.

No Android, installed-PWA or physical wake-lock verification is claimed. Close all regular/test app windows and reopen online to finish a pending service-worker update; never clear site data.
