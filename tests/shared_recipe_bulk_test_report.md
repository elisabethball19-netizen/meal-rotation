# Shared recipes and bulk-edit refinement verification

Both apps were tested in Chromium using isolated synthetic/legacy-shaped fixture storage. No working-app saved data was loaded or modified. Test-app fixtures verify the regular namespace remains untouched. Portrait widths were 320px and 360px; selector/toolbar/editor landscape checks used 740×360. Custom-selector screenshots were inspected.

## Implementation and compatibility

Existing records represent individual group memberships, with stable record IDs. Only the existing `linkGroup` connects shared recipe content. `linkedMealIds` remains the separate serving/side relationship; matching names, source URLs and import IDs do not establish shared identity for ordinary edits.

Explicit intrinsic changes propagate to shared memberships on Save. Untouched fields are excluded, preserving legacy divergent content instead of copying defaults or normalizing it during an unrelated edit. Group, rotation status, ordering and promotion priority remain membership-specific. Existing membership IDs are retained when their group changes or another membership is removed. No storage migration or new recipe identity scheme is introduced. Existing complete-backup formats and test-storage isolation remain intact.

Individual editor Save/Delete reuse the existing staged bulk transaction and complete-backup atomic writer. Dependent storage keys are committed before primary recipe data; simulated write errors restore memory and storage. Group creation is a separate explicit operation and can survive canceling Move. Successful bulk operations exit selection only after commit; Cancel/rejection/failure retain selections.

## Focused suites — passed

- `bulk_workflow_browser.py` (8 groups): custom group/status radios and checkmark/X, no native Move selects, remembered selector drafts, selector Cancel, valid group creation without moving recipes, preserved selections/status, overall Cancel retaining the group, empty/case-insensitive duplicate-name rejection, group creation/storage failures, failed Move rollback with accessible error, successful Move/Edit/Delete exit, reload, 120-group scrolling and footer reachability in portrait/landscape.
- `shared_recipe_management_browser.py` (16 groups): title/ingredients/instructions/URL/times/notes/labels/tasks/adjustment notes shared by identity on one editor Save; unrelated identically named recipe untouched; shared favorite and adjusting actions; additive bulk labels preserve each member's existing labels; local ordering/status/group changes; stable membership IDs, addition/removal and Undo; timer association transfers to a surviving shared membership without resetting the timer; grocery-editor draft Cancel and shared saved ingredients; inline step-link synchronization; manual last-cooked edits and retained import-review Save synchronize; global editor/bulk Delete confirms all memberships and preserves unselected serving-linked recipes; failed writes retain the editor draft and all prior data; reload and complete backup/restore; unchanged schedule, progress, scales, groceries and membership order assertions.

## Existing regression suites rerun — passed

- `meal_groups_bulk_browser.py` — 24 groups, updated for app selectors, exit-after-success and global shared-recipe deletion.
- `meal_groups_bulk_safety_browser.py` — 10 groups: Android-style CDP gestures, selection scopes, mixed Move, dependent/main-key rollback, surviving independent linked-side progress/scales/reminders/groceries/timer, history pruning, Undo and Cycle Back.
- `compact_meal_editor_browser.py` — 8 groups; updated blank-primary expectation so removing a membership does not silently reassign another membership's ID.
- `promotion_schedule_browser.py` — 70 groups: normal/linked promotions, manual protection, active-plan isolation, weekday order, cycling and reload.
- `grocery_rotation_checks_browser.py` — 16 groups: retained/new/moved/shared quantities, tabs, manual editing, Undo/Cycle Back and backups.
- `editor_origin_adjusting_browser.py` — 20 groups: Save/Cancel origins, tabs, scroll/expansion, viewer/search return and adjustment controls.
- `inline_links_browser.py` — 4 groups: Full/Split, touch long press, links, occurrence progress, highlighting, scroll positions and toolbar reachability.
- `favorites_weighted_browser.py` — 12 groups, including 200 cycles per app (80 favorite appearances and 40 each for three regular recipes), skips, duplicate choices, persistence and backups.
- `compact_recipe_timer_browser.py` — 22 groups: existing single timer, controls/indicators, live state, completion, Full/Split and both orientations.
- `today_todo_browser.py` — 14 groups: local-day/all-plan reminders, completion, preferences, reload and backup compatibility.
- `add_recipe_ideas_browser.py` — 8 groups: immediate editor, rapid-tap guard, blank-draft discard, mobile scrolling, Save and reload.
- `import_cleanup_browser.py` — 2 groups: retained import-review code, cleanup/matching/linking, save failures and backups. The old test entry through the previously removed Recipe Settings cleanup button was replaced with its existing test hook; that button remains removed.

These 14 suites passed 234 reported test groups, with page-error assertions. Shared regular/test implementation parity and `git diff --check` also passed. No multiple-timer support was added.

## Findings and limits

- Testing exposed an error message layered behind the Move dialog; its stacking is corrected so failure feedback can be acknowledged while selections remain available.
- A progress test initially used two indistinguishable ingredient lines. Existing conservative reconciliation intentionally clears ambiguous marks after content edits; it was left unchanged. The shared-content test uses distinguishable ingredients to verify unchanged tokens/progress are retained. Content edits still use the established reconciliation rules when steps/ingredients actually change.
- Moves that would place separate membership records of the same shared recipe into the same group are rejected atomically with a clear error. Records are not silently merged, avoiding loss of their IDs or occurrence/grocery state. Existing safeguards also reject linked arrangements that would unexpectedly alter unrelated scheduled meals.
- Removing a referenced/scheduled membership uses existing replacement/reference cleanup and may require the specific destructive confirmation. Other memberships and unselected serving-linked recipes are retained. Global Delete explicitly names all groups.
- Physical Android rendering, keyboard behavior and installed-PWA update delivery still require device verification. Tests used Chromium mobile emulation and CDP touch input, not a physical phone.
