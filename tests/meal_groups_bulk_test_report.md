# Meal Groups bulk-operation verification

Tested both `index.html` and `meal-rotation-test.html` using Chromium with isolated fixture storage. Working-app storage was never loaded or modified. Test-app cases keep a sentinel in the regular-app namespace and verify isolation.

## New browser suites — passed

- `meal_groups_bulk_browser.py`: 24 test groups covering 320px and 360px mobile selection gestures, initial long-press selection, row/checkbox taps, deselection, cross-group selections, parent/section expansion, scoped selection, visible count, zero-selection disabled actions, fixed toolbar/navigation geometry, Exit and restored normal taps. A 100-recipe fixture checks scrolling without a jump.
- The same suite checks one shared edit dialog, unchanged/mixed defaults, additive and subtractive labels, favorites, Needs Adjusting marking with individual notes preserved, confirmed removal of status/notes, exact Cancel, group moves, ordered bulk promotion without auto-scheduling, batch demotion, confirmed deletion, shared-copy collisions, linked references, grocery source checks, rotation history, Undo, reload and complete backup restore.
- `meal_groups_bulk_safety_browser.py`: Android-style CDP touch long-press/release and scroll cancellation; section/group scopes preserve cross-group selections; landscape toolbar geometry at 740×360; independently scheduled linked side survives parent deletion with its cooking progress, scale, completed make-ahead reminder, grocery checks and paused timer. Undo restores the original occurrence; Cycle Back cannot resurrect the deleted parent.
- Safety cases also cover mixed group/status Move with exact Cancel, dependent-key and main-data-key write failures, complete storage/memory rollback and preserved active timer, promotion into a previously empty group slot without changing the schedule, exact preservation of individual label spelling/duplicates, rejected conflicting label operations, and reload/complete-backup restoration after moves, demotion and deletion. Deleting a timer's owner deletes that timer; deleting its linked parent keeps the child's timer.

During development, touch release could hit a neighboring row after checkboxes changed wrapping. The original release click is now suppressed regardless of its retargeted row. Batch demotion initially allowed a replacement to take a retained short-pool recipe from another tab; replacements now use the existing deferred replacement priority, retaining unrelated slots first. Both regressions have passing assertions.

## Existing regression suites — passed

- `recipe_section_moves_browser.py`
- `shared_week_scheduling_browser.py`
- `grocery_rotation_checks_browser.py`
- `recipesage_refresh_browser.py`
- `scheduled_date_integrity_browser.py`
- `group_order_browser.py`
- `collapsible_recipe_sections_browser.py`
- `recipe_ordering_browser.py`
- `favorites_weighted_browser.py`
- `editor_origin_adjusting_browser.py`
- `timer_completion_updates_browser.py`
- `open_recipes_viewer_browser.py`

The group-drag suite now expects the requested recipe long-press selection behavior, expands In Rotation explicitly after Add Recipe collapses it, and drags group-body padding rather than a section button. The section geometry comparison now uses the actual latest pre-change main commit (`1e50448`), avoiding a stale baseline from before cooking-time metadata was added. All recipe-row geometry outside selection remains unchanged.

`git diff --check` passes. Browser suites report no unexpected JavaScript errors. Additional portrait/landscape scroll-to-bottom probes confirm the bottommost visible recipe clears the fixed toolbar. Portrait 320px selection/editor and landscape selection screenshots were inspected for overflow, readability and overlapping bottom controls.

## Deliberate safeguards and physical-device checks

- Bulk promotion does not automatically replace scheduled meals. Group-only moves retain existing scheduled occurrences as temporary substitutions. Explicit movement into Ideas and deletion replace affected scheduled occurrences with existing scheduling logic.
- Moving shared copies into the same destination group is rejected to preserve both IDs. A linked arrangement that would silently change unrelated scheduled meals is rejected atomically with an explanation rather than partially applied.
- Selection state is temporary, cleared on Exit/navigation, and not added to backups. Completed recipe changes use existing saved fields, storage keys, full backups and the isolated test adapter.
- Physical Android long-press feel, scrolling and toolbar usability still need confirmation on the user's phone. These are Chromium mobile/CDP tests, not hardware tests.
