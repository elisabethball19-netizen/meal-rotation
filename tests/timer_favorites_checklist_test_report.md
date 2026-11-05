# Timer, favorites and Open Recipes verification

Both regular and isolated test HTML versions were tested with synthetic app records in fresh Chromium contexts. The actual working app's saved data was not accessed or changed. Regular/test implementations were compared after normalizing their existing storage adapter names; all changed behavior matches, with separate storage retained.

## Timer

- The existing alarm window is now a shared `6000` millisecond constant used by both the completion deadline and Web Audio playback cap. The sound, global volume, three-second test preview, one-active-timer replacement, completed popup, handled-alert persistence, visibility/freeze/suspension stops and notification behavior are unchanged.
- `timer_completion_updates_browser.py` passed its 14 case groups across both apps. The alarm remains active after five seconds and stops by six; acknowledgment/deletion stops it immediately. Tests also cover compact controls, pause/resume/hide/reopen, replacement confirmation, all three list surfaces, automatic completion over pages/tabs/editor drafts, preserved scroll/progress, notification once, background/suspended/blocked audio simulation, quiet expired reload, complete backup restore, volume and stoppable bounded preview.
- `timer_native_audio_browser.py` passed both apps using native Chromium AudioContext. The audio source ended within the six-second deadline window; the completed timer remained until acknowledgment. This verifies source lifecycle, not physical speaker audibility.

## Favorites

- Meal Groups no longer creates outlined-heart controls for regular recipes or hearts for linked entries (including their standalone incoming-link rows). Favorite main entries retain a filled heart. No hidden heart placeholders reserve space. Stored favorite flags and the shared viewer control are unchanged.
- `favorite_display_browser.py` passed both apps at 320px and 360px: correct visibility/fill, favorite toggles in the existing action popup without dismissal, linked recipe's own popup, immediate list refresh, viewer toggles, unchanged recipe content/schedules/groceries, reload, full backup/restore and test namespace isolation. Long headings flow below the right-side heart/X controls, with no text overlap; the popup scrolls if taller than the viewport.
- `favorites_weighted_browser.py` passed. Across 200 normal cycles, one favorite appeared 80 times and each of three regular recipes 40 times. Thirty weighted skips gave 12/6/6/6 appearances. Tests verify no immediate repeats/starvation, one/two-recipe fallbacks, no-favorite parity, existing linked duplicate decisions, chooser filtering, persistence and backup compatibility.

## Open Recipes

- `open_recipes_viewer_browser.py` passed 22 case groups in both apps, with 320px/360px portrait and 740×360 landscape, Full/Split View and automatic links on/off.
- Scheduled recipes and existing tabs are checked initially. Search uses the existing multi-word matcher across the collection, selections survive query changes/clearing, and the dialog stays open while selecting. Select All/Deselect All affect visible results only, preserving hidden choices; controls hide for one row. Tests include a 120-result scrolling list with header/search/actions visible.
- Top X and bottom X discard all draft changes exactly. Confirm adds selected tabs together, removes unchecked existing tabs, avoids duplicates, keeps the selected tab if retained, and selects the primary tab when the active tab is removed. The primary checkbox is disabled and labeled "Primary recipe · stays open."
- Retained/closed-and-reopened tabs preserve the existing order, scroll cache, preview or occurrence progress, scale and divider behavior. Tests include a retained non-primary active tab, untrusted legacy parent context, editor return, different global meal-tab selection, a verified Dinner/Lunch origin, and a collection viewer with no guessed scheduled day. Recipe definitions, last-cooked fields, schedule, groceries and active paused timer remain unchanged by tab management.
- The existing automatic linked setting is reflected in draft selections. Explicit child unchecks win at confirmation. A filtered Select All never silently adds hidden linked recipes. Individual parent checks can auto-select direct links, which are visible in the cleared checklist and can be unchecked. Confirm uses the existing tab/context helpers without auto-opening additional unchecked links afterward.

## Regression and layout checks

The following additional suites passed:

- `meal_groups_bulk_browser.py`
- `meal_groups_bulk_safety_browser.py`
- `timer_list_indicators_browser.py`
- `recipe_ordering_browser.py`
- `editor_origin_adjusting_browser.py`
- `personal_recipe_icons_browser.py`

Mobile screenshots of the checklist in both orientations and a long-name favorite popup were inspected. `git diff --check` passes. Tests reported no unexpected JavaScript errors, duplicate controls or horizontal page overflow. No persistent fields, storage keys, timer-record format, settings, manifest configuration or backup schema were added; offline shell version is v89.

## Device verification

Physical Android sound audibility, media-volume interaction, lock-screen notification delivery and touch comfort still require the user's phone. Chromium mobile/CDP and native Web Audio tests cannot establish those hardware behaviors. Hidden/frozen/suspended pages stop sound; reopening expired timers remains quiet. The app still cannot guarantee an alarm while Android or the browser suspends/closes it.
