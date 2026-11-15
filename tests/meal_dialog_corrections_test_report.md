# Meal selection and sides-dialog checks

Scope: original modular app (`index.html`) and existing isolated `meal-rotation-test.html`. No rebuild, extra app page, dependency, storage reset, settings switch or unrelated backlog change.

## Reproduced scheduling cause

Replayed the original `applyManualWeekdayMeal` from main in disposable fixtures. A group-specific empty destination filled successfully. With a legacy/day-wide `Monday::@day` empty override and a group-specific destination, the original handler cleared only `Monday::Meals`. Tuesday received its replacement, but the surviving day-wide mask hid Chicken Curry on Monday. The source update had no joint commit/rollback or destination-visibility check.

The destination now releases its relevant exact masks. A day-wide mask becomes masks for the other dishes, so another intentionally empty group or independent dish stays empty. Duplicate selection uses the existing cloned-memory/staged-storage transaction and original scheduling/rotation operations. Source/destination are committed together, validated before commit, and represented by one Undo entry. Source identity includes its plan and dated occurrence key. Independent occasional meals retain the other dish in the same group. No cooking date or recipe-status update is introduced.

## Dialog changes

- Duplicate confirmation has the requested weekday heading, two stacked radios with no initial selection, and bottom check/X. Radios do not mutate schedules. No explanatory paragraph or source-day selector. X returns to the usable outer picker. Busy/settle guards and closing tap shields remain.
- Saved populated-meal options use standard rounded outlined buttons: Change meal, Add or edit sides, Edit recipe, Edit groceries. Favorite, X and Last cooked controls remain. Leave empty moves into Change meal.
- Change meal shows Use next recipe, the tab-aware Leave empty label, and the existing searchable/grouped chooser together. Quick actions/heading stay above the scrolling list. Use next reuses the existing replacement/automatic-fill operations; unavailable independent rotation actions remain disabled. Generated previews gain no editing.
- The occurrence-side editor has plain rows with pencil/trash, the same name/ingredient fields for editing, an outlined collapsed ingredients chevron, inline question and Always/This time only radios (default This time only). One bottom check commits the complete pending draft; X cancels it. Trash is pending with no extra confirmation. Existing edits/removals remain occurrence-only. Existing linked recipes and recipe-editor defaults retain their original paths.
- Offline shell version advances to v139.

## Checks actually performed

`tests/meal_dialog_corrections_browser.py` suite and focused case-group reruns passed against both app pages:

- Group-specific, exact skipped, day-wide and unassigned empty destinations: Replace, Keep both, explicit-radio requirement, radio-only no mutation, X and outer cancel. Other empty groups and separately skipped dishes stay empty.
- Populated destinations; source/destination identity; unavailable replacement leaves both days unchanged; injected storage-write failure rolls back memory/storage and permits retry. Reload and session Undo/Redo.
- Rapid Save re-entry, native retaps and detached old controls; single confirmation/action, parent inert/focus recovery, no stuck overlay, picker retry after error.
- Three-option picker order, searchable list already present, shown/hidden tab labels, Use next/Undo, automatic empty fill, exact independent occasional source/destination and unchanged cooked dates/status.
- Four outlined main actions; existing recipe, linked-recipe, grocery and replacement routes. Leave empty with multiple dishes in one day/group, retained scale/cooking/task checks through Undo and Skip/reload/Resume.
- Side Always/This time, valid/blank states, default scope, pending edit/trash/new draft combinations, cancel, removal-only save, ingredient-only invalid draft, duplicate reuse, multiple sides, failed-save rollback/retry and single save. Defaults, occurrence isolation, groceries/scaling, retained/new grocery checks, reload, backup and Undo/Redo. Read-only generated preview remains read-only.

`python tests/simple_sides_browser.py` passed the retained recipe-editor default Save/Cancel, shared-membership and new-occurrence checks in both apps (plus its existing pin-layout checks; pin code was untouched).

At 320px, reviewed menu, picker and side-editor screenshots. At 420px viewport height, checked foreground scrolling, reachable bottom controls/radios and no horizontal overflow. Changed JavaScript/service worker and every test-app inline script passed `node --check`; changed-function parity passed after normalizing only the isolated storage alias; `git diff --check` passed.

Remaining phone verification: installed-app update, the original empty-Monday sequence, fast physical retaps, native keyboard resize/foreground scroll, and final visual appearance. Desktop Chromium touch emulation does not replace that verification.
