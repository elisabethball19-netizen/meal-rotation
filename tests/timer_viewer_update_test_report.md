# Timer completion and recipe-opening validation

This report records the preceding timer/viewer release. See [the latest checklist/favorites/six-second verification](timer_favorites_checklist_test_report.md) for the current interface and alarm limit.

Implemented against main `e8ad49fa27b9c85e931b84147aab208e478bef2b`, in both regular and isolated apps. Browser tests use separate synthetic origins and test storage; no working-app data was opened or changed.

## Implementation

The shared compact timer surface already existed and remains the single renderer for viewer and list-popup controls. Only replacement confirmation uses the new icon-only confirmation mode; multiple-duration selection retains its existing choices. One timer record, deadline calculation, paused remainder, global volume preference, indicators and backup keys remain unchanged.

Previously every synchronization of a completed timer could start/resume its looping sound. Completion now consumes a persisted handled-alert marker once, bounds native source duration and a wall-clock timeout to the original five-second completion window, and stops audio on hidden/frozen pages or suspended contexts. Reloading or returning to an expired timer never replays the alarm. A global completion popup shows the recipe and acknowledgment without switching tabs/pages or losing editor drafts. No new worker/background scheduler is introduced.

Open Recipes uses the existing recipe-tab cache, constructors, linked-tab handling and tab rendering. It adds scheduled day/plan entries or collection search results without activating/reordering existing tabs. A verified schedule origin is kept separately from definite cooking-occurrence identity, including editor round trips; invalid legacy parent contexts do not borrow cooking progress. No schedule, group, rotation, grocery or recipe-definition changes are made by opening tabs.

## Focused tests — passed

- `timer_completion_updates_browser.py`: 14 case groups across both apps at 320/360px. Shared compact controls; pause/resume/hide/reopen/delete; two-icon replacement; completion over all three meal-list pages, another recipe tab and an unsaved editor; retained scroll/progress; interruption of transient dialogs; five-second audio bounds; immediate acknowledgment; one-shot notifications; hidden/suspended/blocked audio simulation; no late/reload replay; global volume and bounded preview; completed-timer backup restoration and separate test storage.
- `open_recipes_viewer_browser.py`: 22 case groups. Open All/individual/collection search, exact Dinner/Lunch and day origin, direct collection entries with no guessed day, linked preference on/off, stable-ID duplicate avoidance, existing order/active tab/nonclosable anchor, cached previews, independent Full/Split scroll positions, saved progress/scaling/timer, unchanged meals/plans/groceries, legacy parent context and preview editor round trip. 320/360px portrait and 740×360 landscape; long collection list scrolling and screenshots inspected.
- `timer_native_audio_browser.py`: both apps passed with native Chromium AudioContext (no audio mock). The source ended within the five-second window while the completed timer remained until acknowledged. This does not verify physical audibility.

## Existing regression suites — passed

`recipe_cooking_timer_browser.py`, `compact_recipe_timer_browser.py`, `timer_list_indicators_browser.py`, `timer_alarm_adjusting_browser.py`, `recipe_tabs_browser.py`, `recipe_tab_layout_browser.py`, `recipe_tab_reorder_browser.py`, `recipe_touch_browser.py`, `recipe_orientation_browser.py`, `inline_links_browser.py`, `timer_duration_units_browser.py`, and `editor_origin_adjusting_browser.py`.

Expectations changed only for requested behavior: the fifth toolbar icon, bounded alarm/completion acknowledgment, and compact replacement. A linked-recipe test locator was scoped to the viewer after confirming the background list remained inert. Final reruns passed; no outstanding JavaScript page errors were observed. Feature-source parity between storage-isolated apps and `git diff --check` passed.

## Android verification still needed

Test physical touch comfort, sound audibility at device media volume, granted notifications, and visibility/lock transitions in the installed Android app. Hidden/suspended-state tests are simulations and notification APIs are mocked. Fully closed/suspended web apps cannot guarantee alarm execution or notifications. The implementation starts no background audio intentionally and never resumes an expired alarm. Close all app windows and reopen online to pick up shell v87; do not clear app data.
