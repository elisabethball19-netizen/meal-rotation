# Issue #121 — latest approved completion pass

Implemented/code-checked; **awaiting phone acceptance**. Started from current main `82dce44`. Latest completion instructions supersede older #121 presentation. Deferred To-Do/date/settings/grocery work and #122–#124 remain queued.

Changes reuse existing status moves, shared recipe identities, Ideas/pinned ordering, group-order persistence/history, favorite and multi-day scheduling operations. Organize entry exposes the same Ideas handles before selection; individual status moves remove selected logical recipes without changing the subgroup lock. Group handles are absent during recipe organizing.

Edit group offers an icon-only Reorder groups action. Dedicated compact group reorder stages order in memory until Done; Cancel/Android Back restores the original order. Both exits restore expansion/position and reopen the untouched name/rotation draft for explicit Save/Cancel. Done uses the original group-order writer and one Undo entry.

Expanded Groups recipes have five separate 44px bottom actions: pencil, groceries, calendar, favorite, status. Collapsed favorite hearts stay beside the name. Weekdays share the reserved right area immediately before the name-aligned chevron. Current-plan action placement is unchanged. Scheduling has one wrapping Schedule [name] heading; multi-day transaction behavior is unchanged.

Meals and Overview use labeled week radios, retaining keyboard focus through rerender. Meals tabs/week controls and Overview week controls alone stick; titles/icons/To-Do scroll away. Dialogs/keyboard/editor release sticky positioning. Existing test banner inset is retained. Tab baseline spans inactive tabs/gaps and is interrupted only under the selected tab. Setting reads Use multiple meal tabs, with unchanged storage/helper. Shell **v151**.

## Focused evidence

`python3 tests/completion121_browser.py` uses disposable browser contexts/storage and the existing fixture for both modular and isolated apps:

- Header/long-press entry, zero-selection Ideas handles, subgroup lock/count after individual moves, no checkbox toggling or group handles, status Undo/Redo.
- Keyboard and real CDP touch Ideas/group handle reorder, pin-partition preservation, touch cancellation, Undo/Redo and reload.
- Group reorder draft restoration, Cancel/Back, explicit group Save/Cancel, no recipe controls, original expansion restoration, order commit/Undo/Redo/reload.
- Five 44px targets on one row at 320px, one favorite, weekday/chevron name placement with long name and linked side, single Schedule heading, Back cancellation/collapse.
- Meals/Overview radio switching and keyboard arrows, sticky geometry (including isolated banner inset), keyboard release, portrait/landscape and Extra Large app text without horizontal overflow; second selected/overflow-end tab screenshots and hidden-tab spacing.

Focused existing regression functions `remaining_closing`, `remaining_multi`, `remaining_scope_duplicates`, `remaining_plan_changes` in `tests/group_editing_batch121_browser.py` passed for both apps: recipe/grocery save/cancel/Back/return behavior; 0/1/multiple schedule destinations; distinct day choices; atomic storage-failure rollback/retry; manual side, other meals/plans/memberships, cooking/scaling/grocery checks retained; hidden active plan; plan change clears stale destinations; duplicate cancel/keep/replace; whole-operation Undo/Redo/reload.

Also passed: `python3 tests/quota_backup_static.py`, `bash scripts/post-merge.sh`, Node syntax checks for changed scripts and `git diff --check`. No site data was cleared.

## Screenshot review

Actual Chromium touch-browser screenshots inspected in `/workspace/work/complete121/screenshots/`, both apps: collapsed/expanded long-name Groups at 320×800; Extra Large text; 740×360 expanded Groups; dedicated reorder; long Schedule title; sticky Meals portrait/landscape and Overview landscape. Corrected inherited off-screen chevron positioning, sticky release selector, and legacy status-arrow margin/offset after visual inspection. These are emulated browser checks, not physical-phone verification.

## Phone acceptance pending

At https://elisabethball19-netizen.github.io/meal-rotation/index.html test header/long-press Organize parity, per-row arrows/counts, pin-safe dragging, Edit group draft → reorder → Done/Back/Cancel → Save/Cancel, Undo/Redo, long names/weekdays/linked sides and all five expanded actions. Check week radios, scrolling tab baseline, sticky controls with keyboard/dialogs in portrait/landscape, and scheduling save/cancel/Back with existing saved meals and grocery checks. **Never clear site data.** Deployment status is reported separately after push; code checks do not establish phone acceptance.
