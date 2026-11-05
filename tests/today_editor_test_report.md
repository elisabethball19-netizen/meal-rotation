# Today's To-Do and compact meal editor verification

Both regular and isolated test apps were tested in Chromium mobile contexts with synthetic saved recipes/plans. Working-app browser data was not accessed or changed. No recipe IDs, content structures, scheduling algorithms, cooking timers or backup formats were replaced.

## Implementation

- Today's To-Do reuses `scheduledMakeAheadTasks`, the existing local-date helpers, and each plan's existing dated occurrence/task key. The shared completion handler updates the same `makeAheadChecks` map used by Weekly Overview. The enumerator reads current active-plan assignments, uses each plan's calendar, and deduplicates identical occurrence/task keys.
- Today uses all plans regardless of visible/active tabs, filters strictly by the device's current local date, orders incomplete before complete, and hides its entire section when no tasks are due. The eye preference defaults to hiding completed tasks; all-complete/hidden shows "All done!" with the eye retained. My Rotation recipe-card preparation icons are removed.
- The default-enabled global Display setting hides planning reminders without changing tasks/checks. Its optional preference and Today's completed visibility use `mealRotationMakeAheadDisplayV1`, included by the existing complete-backup mechanism. Settings Save/Cancel includes the global visibility field; older backups use enabled/hidden-completed defaults.
- One local-midnight UI timeout plus focus/pageshow/visibility handling refreshes Today independently. It does not rerender meal cards or reset an open recipe/editor. This is not an additional cooking timer.
- The editor moves its existing DOM controls into four default-closed sections using the existing chevrons/styles. Names/IDs/event handlers and overall Save/Delete/Cancel remain intact. Primary Group stays visible; additional shared-group membership controls move into Organization. All saved group keys and structures are unchanged. Validation opens the section containing an invalid field.

## Focused suites — passed

`today_todo_browser.py` passed 14 case groups across both apps, including:

- 320px/360px, tabs visible and hidden; due tasks from Dinner, Lunch and a renamed additional plan; linked recipe occurrence deduplication.
- Local dates differing from UTC in Los Angeles and Auckland; past/future exclusion; an upcoming meal from a different plan week.
- Checking/unchecking synchronized with Weekly Overview, completed-last order, eye visibility persistence, All done, no-task disappearance, reload, and unchanged recipe/schedule/grocery/progress/scaling data.
- Global setting Save/Cancel, hiding/restoring both views, editing tasks while disabled, complete backup/restore and older backups without the preference.
- Skip, cycle, delete and Undo/Cycle Back update the checklist and preserve independent-plan tasks and occurrence completion. Last-cooked fields are unchanged by these non-cooking tests.
- Live midnight, background/foreground refresh, the 25-hour daylight-saving day, and midnight during an unsaved editor draft. Meal-card DOM is retained during date-only refresh.

`compact_meal_editor_browser.py` passed eight case groups across both apps:

- Four collapsed sections, visible name/Group/In rotation, three unchanged bottom action icons, unique control placement and independent expansion.
- Three-column timing on narrow screens; labels, instructions/ingredients, Step links, URL, Needs Adjusting, make-ahead tasks and notes remain accessible. Photo inputs retain gallery/camera types and capture attributes.
- Collapse with unsaved values, save while sections are closed, cancel all drafts, reload, and preservation of IDs, linked meals, ingredient associations, favorites, last-cooked fields, current schedule, grocery checks, progress and scaling.
- Primary Group reflects the edited shared copy; additional groups and removing/reselecting all memberships retain existing behavior.
- Invalid time in a closed Timing section is revealed/focused; Needs Adjusting removal still uses its existing confirmation and Cancel preserves the note.
- Long names and unbroken labels, all sections expanded, accessible bottom icons and no horizontal overflow at 320px portrait and 740×360 landscape.

## Existing regression suites — passed

- `make_ahead_reminders_browser.py`
- `inline_links_browser.py`
- `timer_completion_updates_browser.py`
- `open_recipes_viewer_browser.py`
- `editor_origin_adjusting_browser.py`
- `shared_week_scheduling_browser.py`
- `grocery_rotation_checks_browser.py`
- `prep_skip_favorites_integration_browser.py`
- `personal_recipe_icons_browser.py`
- `meal_groups_bulk_safety_browser.py`
- `favorites_weighted_browser.py`
- `add_recipe_ideas_browser.py`
- `group_order_browser.py`

Existing tests now explicitly expand the relevant editor section before using nested controls. Former card-icon reminder checks use Weekly Overview, and category-wording selectors use the requested Group terminology. No production test hooks are shipped.

`git diff --check` passes. Regular/test changed logic and CSS match after normalizing their existing storage adapter names. Browser tests reported no unexpected JavaScript errors or duplicate controls. Screenshots of Today, collapsed/expanded editor and narrow layouts were inspected. Offline shell version is v90.

## Limits and device checks

Physical Android keyboard behavior, camera/OCR capture and touch comfort still require the user's phone. New tests verify the preserved photo controls; they do not take a physical photo. Browser suspension can delay work until the app becomes visible; foreground refresh then uses the current local date. Existing legacy planning-week fallbacks remain for undated schedules; no historical cooked dates are inferred or rewritten by this update.
