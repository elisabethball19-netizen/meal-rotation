# Issue #121 — approved combined phone-review follow-up

Implemented/code-checked; awaiting phone acceptance. This report supersedes the initial pencil/Status popup/changing Select-all design. Started from clean current main `cb79eb0`. Other deferred changes and #122–#124 remain queued; the expanded name-row heart is the only meal-plan presentation change in this pass.

## Targeted implementation

- Normal group headers expose three separate 44px targets: Organize meals checklist, Edit group pencil and Add meal +. Hold labels are available. Group settings directly edits name and the existing rotation preference as a switch, with protected Delete and Save/Cancel. No gear, nested rename popup, Add meals duplication or popup ordering arrows/explanation. Existing group drag/handle keyboard ordering remains. Built-in Sides keeps its identity/nondeletability; assigned groups cannot silently disable rotation.
- Selection locks to one source and one subgroup. Organize starts empty; first selection establishes In Rotation/Ideas (plain-list reference groups retain their scope). Long press selects the exact recipe/subgroup without opening its viewer. Other subgroups have no selectable checkboxes. The bar is Groups / Delete / Done; individual promotion/demotion arrows remain direct operations. There is no bulk Status action.
- Fixed Select all/Deselect all controls reuse the exact Groceries SVG assets, with appropriate disabled states, subgroup/filter scope and accessible/hold labels. No entry exception or changing-text control remains.
- The immediate membership list puts the named source first and shows original checked/mixed states. Only explicit per-group changes feed the existing per-recipe membership/atomic-save operation, preserving untouched mixed memberships. Copy, move, remove, derived Unassigned, existing record aliases and pending new groups retain their semantics. X/Back cancels; an unchecked pending group is not created. Injected save failure retains data and selections for retry.
- Browser history now records selection and child layers. Back cancels a child first, then exits selection locally at the same position/expansion. Existing editor pending-save handling remains authoritative. Dirty grocery close retains its existing save/discard prompt. Settings-to-delete transitions wait for the old history layer to settle, preventing a stale frame from sending Back to the prior page.
- Group recipe names open the internal viewer. Separate status arrow/chevron targets reveal one compact inline Edit recipe / Edit groceries / Schedule meal panel, keyed by stable group/recipe IDs. Last cooked/pencil has its own line. One expanded Favorite heart sits on the name row, remains open on toggle, and is hidden collapsed. Current meal-plan hearts use the same name-row placement without changing their existing actions/lifecycle.
- Group setting name/preference changes reuse the existing rename operation and atomic backup writer; Undo snapshots include the optional existing rotation-preference record compatibly. The isolated test HTML mirrors all applicable changes with its original adapter/banner/features. No site data is cleared or schema replaced. Offline shell: **v149**.

## Focused evidence

Extended `tests/group_editing_batch121_browser.py`, reusing its existing disposable mobile/storage fixture. The focused suite and additional checks exercised both `index.html` and `meal-rotation-test.html`:

- Direct controls, actual hold label, long group names, settings Back/cancel/save, assigned guard, Sides protection, injected settings-save rollback and Undo/Redo.
- First-selection subgroup lock, fixed check/minus/filter scope, long-press dispatch, child membership/search/Delete Back, pending-group cancellation and top-level selection Back with preserved position.
- Source-first and mixed membership states; copy/move/remove; explicit mixed check/uncheck; untouched memberships; Unassigned; pending/unchecked new groups; injected storage failure/retry; reload and Undo/Redo.
- Existing scheduled source copied into an extra membership and that extra membership removed: exact scheduling, checked cooking progress, multipliers and effective grocery checks/amounts remain unchanged, including Undo/Redo.
- Inline singleton expansion, name-to-viewer, saved/cancelled recipe/grocery/schedule actions, dirty grocery Back/discard, direct status arrows/pin ordering and current-plan heart placement.
- Ideas touch/keyboard handles, cancellation, pin portions/shared order, selected IDs, group ordering, Delete cancellation, persistence and Undo/Redo. In Rotation has no manual handle.
- Search subgroup transfer and viewer routes; existing working-data/test-storage sentinels remain intact.

Captured and visually inspected 320×800 and 740×360 screenshots for normal/long group headers, subgroup selection, collapsed/expanded/long recipe rows, arrows/chevrons, membership popup, and current-plan name-row heart. Inspection corrected chevron alignment beside multiline names and prevented the meal count from squeezing a long group name into an unreadable column. These are Chromium mobile/touch/browser-history checks, not physical Android verification. Unrelated #120 investigations/viewer audits were not repeated.

Additional checks: `python3 tests/quota_backup_static.py` (modular/embedded syntax and relevant parity), `bash scripts/post-merge.sh`, JavaScript syntax checks on changed modules/service worker, and `git diff --check`.

## Pending phone checklist

1. Check Organize checklist / Edit pencil / + targets and hold labels, including a long group name. Edit name/rotation directly; test cancel/save, assigned-group guard and Sides protection.
2. Organize empty, select one subgroup, check fixed Select/Deselect scope and filters. Long press a recipe; confirm no accidental viewer or cross-subgroup selection. Test individual status arrows separately.
3. Copy/move/remove memberships with different existing groups; leave mixed boxes untouched, then explicitly check/uncheck mixed. Test pending new group, X/Back, failure/cancellation, Undo/Redo and reload.
4. Back from a child popup should cancel it first. Back from selection should act like Done without moving to the meal plan or jumping scroll. Try dirty grocery/editor close prompts.
5. Tap a recipe name, expand its separate chevron, edit/save/cancel/schedule, and switch expanded recipes. Check separate name-row heart and Last cooked below, including current meal-plan cards. No collapsed heart should appear.
6. Drag Ideas within pinned/unpinned portions and group order; verify selected IDs, shared order and reload. Check narrow/landscape layout.

Phone-testing link: https://elisabethball19-netizen.github.io/meal-rotation/index.html

Actual commit/push and Pages deployment evidence are reported after publishing. Awaiting physical-phone acceptance; no physical Android/PWA verification is claimed. Never clear site data.
