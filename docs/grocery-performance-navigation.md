# Grocery bulk performance and source navigation

Measurements use disposable headless Chromium contexts at a 360 × 800 touch viewport, without CPU throttling. These are desktop browser handler timings, **not physical Android measurements**. `performance.now()` surrounds the actual Select All/Deselect All toolbar handler, including its synchronous state changes and final render. It does not measure screen paint. Baseline has one trial per action/app; each after column has two trials.

## Representative fixture

- 55 recipes, 20 ingredients each (1,100 stored recipe ingredient lines).
- Three meal tabs, with one excluded from the grocery view.
- Both weeks enabled: 840 source contributions across all tabs/weeks, of which 560 are in the displayed scope.
- 456 initially generated recipe grocery rows, including mixed checked/unchecked shared ingredients, plus 24 manual items (480 initial rows total).
- Checked and unchecked occurrence-specific quantities and manual items are represented. Existing mixed-state rows merge to 452 recipe rows after the bulk action.

## Timings (milliseconds)

| App | Action | Before | After batching, before navigation | After navigation |
| --- | --- | ---: | ---: | ---: |
| Regular | Select All | 44150 | 428–467 | 460–483 |
| Regular | Deselect All | 42389 | 316–333 | 331–414 |
| Test | Select All | 48456 | 388–529 | 462–512 |
| Test | Deselect All | 51260 | 361–392 | 381–390 |

## Identified cause and fix

The toolbar loop called `setGroceryItemChecked` separately for every generated row. Each call captured grocery checks across both weeks, previewed the next-week schedule through that dependency, materialized legacy checks, scanned the entire source collection for its base ingredient, and serialized/saved the whole occurrence ledger. The top-level DOM render was already once per action; repeated source/check generation and persistence inside the loop caused the freeze.

On regular-app Select All, the original handler made 914 check-capture calls, 916 contribution-generation calls, 458 next-week previews, 917 calendar reconciliations and 456 occurrence-ledger save calls. Deselect All made 906 captures, 908 contribution calls, 454 previews and 452 ledger saves.

The batch now shares one captured source universe, applies the same per-row check/partial-quantity semantics together, updates affected legacy base states once, and saves the occurrence ledger once. Whole-handler counts are fixed: 4 captures, 6 contribution generations, 3 previews, 7 calendar reconciliations, 1 ledger save and 1 final render. Those fixed calls include existing preview/render dependencies. There is no timer, spinner or deferred copy of the former blocking loop. Manual-item checks participate in the existing history mechanism so Undo/Redo cover the complete bulk action.

The improvement was measured and scope/history checks passed **before** source navigation was added. The same performance fixture was rechecked after navigation, as shown above.

## Source navigation

Each generated contribution carries its recipe's existing ingredient token and scale as ephemeral metadata; persisted source IDs and grocery keys are unchanged. Clicking a recipe source verifies its occurrence/date, opens the existing internal viewer and targets that token in the displayed ingredient order. Explicit saved ingredient-step links alone select a step, choosing the earliest instruction when multiple steps link the ingredient. Split panes scroll independently; full view remains at the ingredient and uses the existing selected-step highlight. The viewer's layout coordinator applies the target after restoration, rather than starting a competing delayed scroll. Future-only occurrences stay preview contexts so they cannot borrow current-week progress or scaling. Unresolvable ingredients/occurrences fall back to normal recipe opening.

No separate star optimization was made: the demonstrated cause was the per-grocery-row check-update loop, which priority-star handlers do not use. The reported star delay remains pending.

## Focused checks performed

- `python3 tests/grocery_bulk_performance_browser.py`: actual toolbar timings/call counts for both existing apps; repeated after navigation.
- `python3 tests/grocery_bulk_checks_browser.py`: This week / Next week / both / neither, excluded plans/recipes, hide-checked presentation, comparison with existing single-row check semantics (including split quantities and row order), manual items, exact outside-scope checks, shopping wording, recipes/schedules/tasks/scaling/progress, Undo/Redo, reload and whole-week cleanup.
- `python3 tests/grocery_source_navigation_browser.py`: linked/unlinked and inferred-only ingredients, multiple explicit steps, edited grocery text, current scaling, future preview contexts, ingredient display reordering, split/full modes, linked tabs, stable scroll after opening, invalid source fallback, unchanged normal recipe opening/manual groceries and exact saved-state preservation.
- JavaScript syntax and existing storage/backup checks.

All browser fixtures use isolated disposable data. The existing test HTML retains its sandbox namespace and test-only controls. Physical Android responsiveness, opening targets with the installed app/keyboard, and offline update behavior still require a phone check. No deferred combining, manually edited quantity scaling or Group by meal changes are included.
