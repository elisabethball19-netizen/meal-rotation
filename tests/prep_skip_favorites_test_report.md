# Make ahead / Skip This Week / favorites validation

Tested with Chromium touch emulation on isolated origins and synthetic saved app records, for both `index.html` and `meal-rotation-test.html`. Working-app browser data was never opened, reset, or changed. Test-app checks also verify the regular storage sentinel remains untouched.

## Focused suites — passed

- `make_ahead_reminders_browser.py`: multiple tasks, same-day/custom offsets, pre-week placement, Tuesday/Sunday/Monday week starts, month/year boundaries, editor Save/Cancel, preserved marinade field, independent completion, later rotations, reload, complete backup/restore and Cycle Back.
- `skip_this_week_browser.py`: 22 cases covering individual-slot replacement, protected selections, multiple assigned groups, linked slots, exhausted alternatives, unchanged recipe definitions/queue/cooked dates, retained quantities/check states, new unchecked contributions, existing Cycle Back history, and Undo including scaling. Scoped Undo also preserves later cooking progress/scaling on retained meals, including protected sides on the same day.
- `favorites_weighted_browser.py`: heart actions in all requested main lists and viewer, chooser filter, stable schedules/groceries, reload/backup, linked duplicate Yes/No/Cancel, single/two-recipe fallback, no-favorite selector parity. Each app produced exactly **80 favorite / 40 / 40 / 40 regular** appearances over 200 normal cycles, without immediate repeats; 30 skips produced **12 / 6 / 6 / 6**. No cooked dates were changed by selection.
- `prep_skip_favorites_integration_browser.py`: reminder/linked-side updates after Skip, independent duplicate occurrences, unchanged other days/tabs, Undo, complete backup comparisons, weighted partial/full Cycle Back, later favorite edits, cross-tab duplicate prevention/manual protection. Fifteen no-favorite weekly rotations match pre-weighting commit `8177685` exactly in each app.
- `personal_recipe_icons_browser.py`: 320px portrait / 740px landscape, long recipe names, linked descriptions and time metadata, timer/favorite/preparation/Needs Adjusting icons coexisting without horizontal overflow. Timer deletion retains favorite/preparation controls; icon taps do not open unrelated meal actions. Screenshots inspected.

## Existing regression suites — passed

`shared_week_scheduling_browser.py`, `promotion_schedule_browser.py`, `scheduled_linked_slots_browser.py`, `grocery_rotation_checks_browser.py`, `scheduled_date_integrity_browser.py`, `recipe_section_moves_browser.py`, `recipe_ordering_browser.py`, `compact_recipe_timer_browser.py`, and `inline_links_browser.py`.

Applicable feature source parity and `git diff --check` passed. No JavaScript page errors were observed in the passing browser suites.

## Existing test expectation failures

Two older suites fail their first specific replacement-ID assertion: `rotation_no_duplicates_browser.py` and `manual_duplicate_meal_browser.py`. Both failures were reproduced against unchanged main `8fc4ed3` using the same fixtures. Their expected replacement ignores a recipe already allocated to another tab under the current whole-week allocator. No application change was made to satisfy the obsolete expectations. The newer shared-week suite, targeted weighted cross-tab checks, and linked duplicate decision checks pass.

## Device checks and constraints

Physical Android testing remains necessary for touch comfort and installed-PWA update pickup; browser emulation is not a physical-device test. Favorite weighting is bounded by existing eligible slots, retained meals, linked priority and duplicate avoidance. Two eligible recipes alternate instead of achieving 2:1, because 2:1 would require immediate repeats. A linked-only attachment or occasional meal with no independent assigned group is left unchanged by Skip, with an explanation. These are intentional constraints, not storage migrations.
