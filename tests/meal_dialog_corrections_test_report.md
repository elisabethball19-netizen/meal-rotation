# Original-app meal-dialog corrections — 2026-11-14

Base: main `a4936a2e8ea0b4139ac2fa64bd057a393a5eb092`. Changes are to the original modular app and its existing isolated test HTML, not a separate rebuild.

## Duplicate-confirmation failure

A clean single native tap worked in the disposable baseline fixture. The confirmed failure path was Save-handler re-entry while awaiting the confirmation: there was no handler-level pending guard, and each dispatch created an independent, unguarded confirmation promise/overlay.

Replaying the original main-branch chooser and confirmation functions produced **two identical confirmations**. Responding to the top one scheduled the meal and closed the meal picker, but **one identical stale prompt remained**, with no runtime error. This reproduces the apparent unresponsive/stuck-prompt symptom under re-entry. The exact physical-phone event sequence still needs device confirmation; a layering failure on a clean single tap was not observed.

The chooser now permits one pending dispatch, verifies plan/week and target/source occurrence identities, and recovers from cancellation/errors. Confirmation uses the existing standard dialog lifecycle for foreground placement, inert background, focus return and cancellation. A single settlement guard handles Replace, Keep both, X, Escape and outside close. The existing meal-action tap shield protects the handoff and ignores temporary shields when setting background inertness.

Replace still calls the existing `applyManualWeekdayMeal` replacement path: the selected recipe goes to the target, and the original slot is resolved by the existing rotation operation. No queue policy was invented. Keep both preserves the original occurrence. X returns to a usable picker with no schedule change.

## Menu and sides

Saved populated-meal options use consistent unboxed rows: Change meal, Add or edit sides, Edit recipe, Edit groceries, Skip this meal. Recipe/Favorite/X remain in the header, with the compact cooked-date caption/pencil immediately below. Scheduled menus omit Open recipe; short taps still open it. Unscheduled/group menus retain recipe access. Automatic replacement remains reachable as Choose another rotation meal in Change meal. Applicable Resume/hidden-linked restore controls remain available.

Skip masks the selected scheduled occurrence rather than all meals in its day/group; additional dishes survive, including an occasional meal sharing the same group. Occasional and one-time variants reuse their existing scheduling/editor operations. The optional mask is compatible with older full-slot empties. Calendar/grocery state and scoped cooking-state Undo use existing capture/restore paths; reload/Resume preserves tested completion and scale state.

Add or edit sides opens one direct editor with existing side edit/remove controls and an immediately available name field. Optional ingredients are collapsed. Adding shows a live inline Always question with Always / This time only; either commits atomically and closes to My Rotation. Blank names disable saving. X discards the draft. Existing edits/removals use a standard check and stay occurrence-only; removal is staged inline until that check. Failures retain the draft and allow retry. Duplicate names reuse existing identities/defaults.

The previous occurrence manager/prompt/final-check chain is removed. Recipe-default controls still use the recipe editor's existing final Save/Cancel flow. Linked recipes, stable side/ingredient IDs, defaults, scaling and grocery operations are retained. Generated next-week previews gain no editing.

## Focused checks performed

`python tests/meal_dialog_corrections_browser.py` fixture groups passed for both existing apps:

- Replace / Keep both / X, repeated handler dispatch, rapid coordinate touch retaps, one confirmation/action, background inertness and picker usability. Injected choice-dispatch failure recovers for retry.
- Existing replacement outcomes, unaffected days/plans, native session Undo/Redo, and Keep both's original side/progress state.
- Five compact rows, caption ordering, original recipe/linked-recipe and grocery-edit routes, automatic-replacement access, and short-tap recipe access retained by existing handlers.
- One-editor named-only Always/This time saves, blank disable, live question, optional ingredients, X, existing-side check/edit/remove, cancel removal, duplicate reuse, atomic failed-save rollback/retry, multiple sides and single-save re-entry protection.
- Side default separation, groceries/scaling, unchanged/new ingredient checks, reload/backup, parent removal Undo, saved-future occurrence isolation and generated-preview read-only behavior.
- Selected Skip with multiple dishes in one day/group; untouched other dishes/days; cooking completion/scale Undo. Additional Skip/reload/Resume checks passed in both apps with a checked ingredient-bearing side.
- 320px and reduced-height 420px editor layout, foreground scrolling and reachable actions. Menu/editor screenshots reviewed.

`python tests/simple_sides_browser.py` passed the retained recipe-editor defaults Save/Cancel/shared-membership/new-occurrence checks and pin-layout checks for both apps. Superseded manager-flow UI checks were replaced by the direct-editor checks; older menu test labels were updated.

Changed JavaScript/service worker and all inline test-app scripts passed syntax checks. Changed-function parity passed with only the pre-existing isolated storage alias normalized. `git diff --check` passed. Offline shell version is v138.

No site data was cleared, additional test-app page created, dependency added, or broad audit performed. Deferred grocery navigation, pin delays, timers and unrelated styling were untouched.

Remaining physical-phone verification: the original freeze sequence, fast nested-dialog retaps, native keyboard resizing/foreground scrolling and final menu/editor appearance in the installed app.
