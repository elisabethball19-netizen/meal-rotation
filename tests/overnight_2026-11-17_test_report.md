# Overnight batches 2026-11-17 — test report

Browser checks only (Chromium, 360×800 phone emulation unless noted). **No physical-phone verification**; every batch below is awaiting the user's one-item-at-a-time phone test.

Run any suite with: `python3 tests/<name>.py` (each runs `index.html` and the isolated `meal-rotation-test.html`).

## Commits on `main`

| Commit | Scope |
|---|---|
| 535b68d | Batch 6 revised: editor Sort by steps (preview/Apply, split amounts), "For this step" box removed |
| b880f36 | Batch 5: first open on a new day starts on Meals |
| 393f9a5 | Batch 4: Meal Groups sections, Unassigned checklist + Move/Delete, bulk bar Move |
| a355785 | Batch 3: source link row, collapsed viewer edit, step picker |
| f613837 | Batch 2 part 1: shopping names, skipped serve-with lines, item pencil, per-recipe amounts |
| 2aa7ddf | Batch 2 part 2: Edit groceries include dialog (switches, footer order, no import/trash) |
| 6b7b26a | Batch 7: Week/To-Do/card typography polish |
| d8f0b8d | Batch 8: card group label "Rice · Soup" |
| 8a2cdaf | Weekday Setup wording without implied order |
| 01ead17 | Batch 9: shared modal scroll lock |
| a4bf947 | Text Size respected on new text |
| d7706ca | Fix: Edit groceries Cancel save prompt caused by hidden serve-with lines |
| e546fb1 | Sort by steps button styling; whole Link Steps list visible |
| e6f7512 | Fix: two different lines sharing a name not auto-highlighted |

## Final run (all pass in both apps)

batch2_groceries, batch3_recipe_editor, batch4_groups_page, batch5_start_view, batch7_week_todo, batch8_group_label, batch9_modal_scroll, recipe_sync_matching, sides_batch127, followup126, preparation_batch125, grocery_batch122.

Extra checks: Extra Large text sweep (Meals, Week, Meal Groups, Groceries, Edit groceries, step picker, Sort preview) and 740×360 landscape Groceries; recipe viewer touch scrolling (split and full) with the modal lock; batch9 confirmed to FAIL with the lock removed.

## Known pre-existing failures

About 15 older suites (e.g. inline_links, recipe_tabs, group_order, occasional_meals, phase2_*) fail identically on the pre-batch commits (their hooks such as `slotTest`/`linkTest` are not defined, or the page closes). They give no regression signal either way. `preparation_batch125` failed twice under heavy load right before a workspace restart, then passed 4/4 runs.

## Held for user decisions (not built)

- Edit groceries per-row pencil that edits/removes only the shopping contribution (long-press edit / swipe-delete still change the recipe on Save, as before).
- Regular grocery items; renames; Plan Ahead; balanced rotation; "Use next recipe" shifting next week.
- Inline Settings Weekday Setup layout (needs screenshot 11674; older layout not in repo history).
- Next-week To-Do still disappears without the fade (re-rendered via the full list).
