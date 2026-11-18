# Issue 127 — Meal card + sides phone-review batch (Batch 1)

2026-11-17. Batch 1 only, from `docs/handoff/04-remaining-work.txt` "APPROVED 2026-11-18 PHONE-REVIEW DECISIONS". Code-checked; **awaiting physical-phone testing**. Batches 2–5, renames, Plan Ahead and the rotation algorithm were not touched.

## What changed

- **Undo after a saved side removal.** The reported failure did not reproduce in synthetic fixtures with the old flow. Current/next week, simple/recipe/legacy-linked sides and reload were all tried in both apps, and toolbar Undo restored the side each time. The user's exact data was not available. The old save step is now replaced: each side change saves on its own as one Undo/Redo step through the existing `servingTransaction`. An open side editor resyncs from saved data after Undo/Redo. Removal shows a "Side removed · Undo" toast for 5 s; its Undo runs the toolbar Undo, but only if nothing else was saved since.
- **Auto-save.** The ✓/✗ row under Sides is gone. Each of these saves the side and never discards it: collapsing the card, opening another card, closing the open side (which also closes side editing), the Sides close chevron, Android Back, changing week and leaving the page. A blank new simple side is not saved. Typed names and ingredients save when the field is left, or on close.
- **No sides / one side.** "Add or edit sides" opens Add side directly. Its X leaves the expanded card unchanged. A single side opens auto-expanded. The Sides area is a lighter rounded panel with no divider under "Sides".
- **Add side pop-up.** It has two options:
  - **Choose a side:** one search box. The first row is `+ Add "text"` as a simple side. When the text exactly matches a recipe name (case-insensitive), that recipe is first and the simple-side row second. Other matches follow with their group. With no text, it browses groups using the shared picker's cards and outline chevrons, and highlights the selection.
  - **Mix it up:** a group checklist with recipe counts. Checked groups float to the top. It has ✓/✗.
  - Wording: there is no "rotating" wording in the side or weekday dialogs. The weekday dialog is titled "Choose Tuesday's meal groups".
- **Details.** The main meal shows prep/total and marinate on one line, directly under its name and before the sides. Recipe sides show their own time line and Last cooked only when the card is expanded. Side prep to-dos are generated whether or not the card is expanded.
- **Favorites.** Recipe sides get the existing recipe-wide heart in the expanded card and in the expanded side editor row. Simple sides get no heart.
- **Date column.** It is top-aligned in every card state, so the weekday/date sits at the same offset collapsed or expanded, and for empty vs filled cards, in both weeks.
- **Styling.** Text boxes have rounded corners. "Ingredients (optional)" uses the app chevron. The edit area is lighter than its card; this was checked on all 7 weekday colors.
- **Recipe editor.** The editor's Serve with section still keeps sides as part of its own Save/Cancel draft, since the recipe editor is excluded from this batch. It now uses the new Add side pop-up because that pop-up is the shared component.

**Behavior note:** with save-as-you-go, adding a side (default "Always serve" ON) and then switching it off saves twice. The recipe can be left with empty `serveWithEntriesV1`/`linkedMealIds`/`simpleSides` arrays. These mean the same as absent arrays. As with any rule change, other already-scheduled copies of that recipe keep a frozen snapshot of their sides.

No data migration was added, and `version: 2` import/export is unchanged. The service-worker shell was bumped to `v162`. `meal-rotation-test.html` mirrors the same `serving.js`, `ui.js` line edits and CSS.

## Follow-up after first phone check (2026-11-17)

Item 1 passed on phone; the user then asked for a simpler side editor. Changed: the "Choose a different side" / "Use next recipe" text buttons are gone (remove + add replaces them); each expanded side shows three icon-only actions (pencil, trash, cart), with the plus (add side) in the bottom row beside the ✓ (moved there after the first phone check); a simple side's cart opens its ingredient list so plain items such as white rice can still be shopped for; the Sides header is only a title; a side's chevron only expands/collapses that side; one ✓ at the bottom closes the editor (changes are already saved, so there is no X); one side opens expanded, several start collapsed, a just-added side opens expanded. This replaces the earlier rule that closing a side also closed the editor. Screenshots: [icon row](evidence/issue127/side-icon-row.png), [collapsed list](evidence/issue127/sides-edit-mode.png). Re-run: `sides_batch127_browser.py` and the five #126 suites pass in both apps (their picker steps now use remove + add).

## Checks run (both `index.html` and isolated `meal-rotation-test.html`)

- `tests/sides_batch127_browser.py` (new) covers:
  - Undo/Redo after a saved removal via toolbar and toast, and after reload.
  - Collapse saving a pending name; side close saving and closing side editing.
  - Add side with no sides, one side and many sides; exact-match ordering; group labels; simple-side creation.
  - Draft cancel via the pop-up's X (state unchanged); Mix it up checked-first ordering with no "rotating" wording; weekday dialog title.
  - Hearts on recipe sides only, with the recipe-wide favorite; side details only when expanded; side prep to-do present while collapsed.
  - Main time line placement; date offsets equal across cards and collapsed/expanded in both weeks; next-week isolation; edit-area background on 7 card colors.
- Existing `followup126_browser.py`, `followup126_servings_browser.py`, `followup126_edges_browser.py`, `followup126_phone_browser.py`, `followup126_visual_browser.py` pass. Their steps for the removed type chooser and check/X row were adapted to the new flow. Former "cancel restores state" steps now close the editor and use toolbar Undo.
- `preparation_batch125_browser.py` passes.
- `meal_plan_batch120_browser.py` (`renewed_controls`, line 280) and `favorites_weighted_browser.py` (missing `slotTest` fixture) fail identically on the unmodified base commit. Both failures are pre-existing and unrelated.
- `node --check` on modified JS and on the test app's extracted inline scripts; `git diff --check`; `bash scripts/post-merge.sh`.

Run locally with Playwright and Chromium: `python3 tests/sides_batch127_browser.py`. Screenshots go to `$BATCH127_OUT`, default `/tmp/batch127`.

## Inspected screenshots (synthetic 360×800 browser captures, not a phone)

[collapsed](evidence/issue127/collapsed-with-sides.png) · [expanded with side details/hearts](evidence/issue127/expanded-side-details.png) · [sides editing](evidence/issue127/sides-edit-mode.png) · [removed toast](evidence/issue127/removed-toast.png) · [simple side editor](evidence/issue127/simple-edit.png) · [Add side browse](evidence/issue127/add-side-browse.png) · [exact match](evidence/issue127/add-side-exact.png) · [new name](evidence/issue127/add-side-new-name.png) · [Mix it up](evidence/issue127/mix-it-up.png) · [next week dates](evidence/issue127/dates-week1.png) · [edit area on 7 colors](evidence/issue127/edit-area-colors.png) · test app: [editing](evidence/issue127/test-sides-edit-mode.png), [exact match](evidence/issue127/test-add-side-exact.png)

## Follow-up redesign (2026-11-17)

All 21 Batch 1 phone-checklist items passed. Follow-up covered by `redesign()` in `tests/sides_batch127_browser.py`: Sides box/plus/chevron, plain new simple side, empty-day Choose meal groups and no dash, meal-groups dialog without chevrons and new sentence, Use next recipe inside Choose a different meal (both weeks), gray side hearts, date centered on the header block. All #126/#127 suites pass in both apps; other suites fail identically on the base commit. Awaiting phone test of the follow-up.

## Follow-up 3 (2026-11-17)

Single-view Sides box (no editing mode, nothing expanded by default, no check), shorter card actions, groups option only when no group, new dialog sentence, one card when a group is assigned after a one-time meal (single Undo). Covered by `redesign()`; adapted all #126 suites. Same unrelated failures as the base commit. Awaiting phone test.

## Original phone checklist (passed)

Remove side → Undo (toolbar and toast). Add side on an empty day. Type a new name vs an existing recipe name. Collapse an editing card. Favorite a side. Compare date position collapsed/expanded. Check a few card colors. Keyboard and large-text behavior on a real Android device.
