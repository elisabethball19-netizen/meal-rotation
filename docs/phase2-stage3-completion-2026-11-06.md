# Phase 2 — Stage 3 completion report

Date: 2026-11-06 (UTC)  
Repository: [elisabethball19-netizen/meal-rotation](https://github.com/elisabethball19-netizen/meal-rotation)  
Branch: `codex/phase2-meal-rotation`  
Status: Stage 3 implemented and tested; ready for independent verification. No Stage 4 work, merge, or deployment performed.

## Starting point and commits

Work began from remote head `f511e8e003afacba85d00ab25fd4ed9e9ffe3d8b`, after the [independent Stage 2 corrections verification](phase2-stage2-corrections-independent-verification-2026-11-06.md) concluded **READY FOR STAGE 3** and the owner authorized this stage.

Published commits:

- [`b7b4e2931a2356ecd3be8cf53bce5bafb3fdf659`](https://github.com/elisabethball19-netizen/meal-rotation/commit/b7b4e2931a2356ecd3be8cf53bce5bafb3fdf659) — viewer editor, grocery navigation, new-recipe defaults, shell v102.
- [`6f1192c3c26db01e591aa657d4d7df067220a6ad`](https://github.com/elisabethball19-netizen/meal-rotation/commit/6f1192c3c26db01e591aa657d4d7df067220a6ad) — permanent Stage 3 regressions and existing-test adaptations.
- [`a1ee04886628c5b238dc5f1fc88d5e22f16133bd`](https://github.com/elisabethball19-netizen/meal-rotation/commit/a1ee04886628c5b238dc5f1fc88d5e22f16133bd) — honor explicit new Ideas choices when automatically linked.
- [`080ed1e4cde6472f864ad2cf4a6d60b3dd018d8f`](https://github.com/elisabethball19-netizen/meal-rotation/commit/080ed1e4cde6472f864ad2cf4a6d60b3dd018d8f) — preserve explicit ingredient exclusions when copying group memberships.

This report is published in a subsequent documentation commit. Application changes are limited to `index.html`, synchronized `meal-rotation-test.html`, and the offline shell version in `service-worker.js`.

## Implemented features

### Lightweight recipe editor

The internal viewer's **Edit Recipe** icon now opens a compact content editor over the existing viewer. It edits ingredient lines/quantities, cooking instructions, original/source URL, and notes. Cancel, Escape, or backdrop dismissal discards its draft. Browser Back retains an open draft until it is saved or canceled.

The viewer stays open. Save preserves its active linked-recipe tab, deck order, viewing mode, split ratio, scale, and captured scroll positions. Unchanged ingredient/instruction completion tokens remain intact. Edited, removed, or ambiguous tokens follow the existing reconciliation rules rather than inheriting stale completion. Shared recipe content still follows `linkGroup`; group memberships, serving links, labels, Favorites, and rotation settings remain in the full **Edit meal** editor.

Saving uses the guarded bulk/backup transaction with a content-field allowlist and a live draft recovery owner. A failed save rolls back persisted/application data and keeps the draft open. Recovery export includes current text; Retry Save reads the latest edits. Cancellation removes the abandoned proposal. Unambiguous quantity-only changes retain the ingredient's permanent grocery selection; unrelated selections remain intact.

### Open recipes from Grocery List

Expanded associated-meal names are now keyboard-accessible buttons. Each uses the contributing recipe ID and exact tab/weekday/occurrence context. Labels include tab, weekday, and group, so shared ingredients and repeated occurrences can be distinguished. No recipe is looked up by its display name.

Opening the viewer leaves the grocery DOM and filter state in place. Closing restores the page's prior scroll position and focus without changing checked groceries, quantities, ingredient selections, selected plans/meals, or the active app tab. Tests exercise a long, actually scrolled grocery list, filtered contributions, inactive-tab occurrences, and identical recipe display names.

One-time entries have no saved recipe to view; selecting their association explains that fact without converting them into permanent recipes or changing groceries.

### New-recipe defaults

New recipes default to **In Rotation** and include their ingredients in groceries when scheduled. Users can choose **Ideas** and use the existing ingredient chooser to exclude individual ingredients. Create New Recipe from Change Meal also starts with both default checkboxes checked and retains its explicit opt-outs.

The full meal editor defaults its new-draft rotation checkbox to checked while keeping the blank draft out of the rotation until Save. File imports and newly fetched related-recipe imports expose an In Rotation/Ideas choice. Existing imported matches/enrichment records retain their status and selections. Existing recipe records receive no startup migration or default rewrite.

Two optional fields are written only for newly created/imported recipes:

- `groceryDefaultAll` supplies initial ingredient inclusion when the recipe identity has no explicit saved selection. Any saved selection, including an empty array, takes precedence across its group memberships. A newly copied membership cannot resurrect excluded ingredients.
- `keepAsIdea` records an explicit initial Ideas choice. Automatic linked-meal activation respects that choice; legacy recipes retain their existing activation behavior. Explicitly placing the recipe In Rotation later continues to use the existing rotation controls.

These fields use the existing recipe JSON and backup format; no new localStorage key or schema migration was added. Favorites weighting and existing automatic rotation behavior remain covered by regression tests.

## Interaction fixes caught during implementation

A targeted test reproduced an explicit new related-recipe Ideas choice being overridden by automatic linked activation. The new-record-only Ideas guard fixes that interaction; the final test covers an automatically scheduled parent and backup/reload.

A real group-membership copy test reproduced default ingredient inclusion overriding an already saved exclusion on the source recipe. Explicit selections now take priority for the shared identity. The regression creates and schedules a recipe, excludes an ingredient through the existing chooser, copies it through the existing group picker, and checks backup/reload.

Both fixes are part of the approved defaults work. They do not redesign the historical scheduling allocator or change existing recipes' statuses/selections.

## Tests and actual results

All browser data was synthetic and disposable, with intercepted fixture requests; no user storage or live recipes were accessed. Tests use Chromium at `/usr/bin/chromium`. Commands below are `python tests/<filename>`.

| Suite | Completed result |
| --- | --- |
| `phase2_stage3_browser.py` | PASS, exit 0 — 28 groups |
| `phase2_stage2_corrections_browser.py` | PASS, exit 0 — 22 printed groups |
| `phase2_stage2_browser.py` | PASS, exit 0 — 18 printed groups |
| `phase2_stage1_corrections_browser.py` | PASS, exit 0 — 24 printed groups |
| `phase2_stage1_browser.py` | PASS, exit 0 — 14 printed groups |
| `phase2_stage1_workflows_browser.py` | PASS, exit 0 — 28 printed groups |
| `phase1_final_recovery_safety_browser.py` | PASS, exit 0 — 16 printed groups |
| `phase1_safety_corrections_browser.py` | PASS, exit 0 — 26 printed groups |
| `phase1_data_safety_browser.py` | PASS, exit 0 — 17 printed groups |
| `grocery_rotation_checks_browser.py` | PASS, exit 0 — 16 printed groups |
| `favorites_weighted_browser.py` | PASS, exit 0 — 12 printed groups |
| `dependent_side_groups_browser.py` | PASS, exit 0 — 12 printed groups |
| `scheduled_linked_slots_browser.py` | PASS, exit 0 — 4 printed groups |
| `shared_week_scheduling_browser.py` | PASS, exit 0 — 64 printed groups |
| `manual_duplicate_meal_browser.py` | PASS, exit 0 — 60 printed groups |
| `scheduled_date_integrity_browser.py` | PASS, exit 0 — 46 printed groups |
| `meal_groups_bulk_safety_browser.py` | PASS, exit 0 — 10 printed groups |
| `recipesage_refresh_browser.py` | PASS, exit 0 — 0 printed groups |
| `skip_this_week_browser.py` | PASS, exit 0 — 22 printed groups |
| `add_recipe_ideas_browser.py` | PASS, exit 0 — 8 printed groups |
| `recipe_tabs_browser.py` | PASS, exit 0 — 4 printed groups |
| `recipe_tab_reorder_browser.py` | PASS, exit 0 — 6 printed groups |
| `recipe_touch_browser.py` | PASS, exit 0 — 4 printed groups |
| `shared_recipe_management_browser.py` | PASS, exit 0 — 16 printed groups |

Printed groups are scenario summaries, not individual assertion counts. RecipeSage refresh signals success by its exit status without printed PASS groups.

The final Stage 3 suite passed 28 groups in both HTML apps, with core UI cases at 320px and 360px. Coverage includes content editing and Cancel; split scroll/active linked tabs; preview completion and scaling; keyboard progression/Escape/Back; grocery navigation with real scrolling, same-name meals and exact occurrence IDs; defaults/Ideas/exclusions across full creation, Change Meal, file import, and related imports; shared content; primary and ingredient-selection write failures; latest-draft retry, recovery export, cancellation, reload, and backup/restore.

All 22 previously relevant suites completed passing runs during Stage 3 verification, and `shared_recipe_management_browser.py` additionally passed 16 groups. After the final Ideas safeguard, eight affected suites were rerun and passed: Stage 2 corrections, Stage 2, Stage 1 corrections, Favorites, dependent sides, scheduled linked slots, shared-week scheduling, and Add Recipe/Ideas. After the membership-exclusion safeguard, the grocery suite passed again and the shared-recipe suite passed. The final 28-group Stage 3 run includes both safeguards.

### Existing-test adaptations and recovery run history

No existing correctness assertion was removed or weakened:

- Viewer tab/reorder tests now use the lightweight dialog's semantic Save/Cancel/instructions controls and retain their prior tab, scroll, progress, and scale assertions.
- The existing Add Recipe/Ideas workflow asserts the new checked default, explicitly chooses Ideas, and keeps its previous Ideas/Cancel/draft-safety assertions.
- Initial full and isolated safety runs intermittently timed out waiting for a native file chooser in `recovery_journal`; focused recovery runs passed. The recovery upload test helper now explicitly foregrounds the page before the native picker gesture. The final complete Phase 1 safety corrections run passed all 26 groups with the native chooser and every recovery assertion still required. This changes test synchronization, not the application's file-picker or recovery algorithm.

Additional checks passed: every inline script in both apps and the service worker with `node --check`; normalized shared-application equality; byte-for-byte preservation of the test-only shell/storage adapter/banner/reset controls; Python test syntax; `git diff --check`; and published blob hashes matching the tested local source.

## Compatibility, remaining issues, and limits

Phase 1 recovery journals, pending drafts, failed-save warnings, guarded backups/restoration, and storage isolation remain in place. Stage 1 temporary meals/empty slots, grocery holds/resets, ordering, Undo, and Rotation Back pass their suites. Stage 2 direct scheduling, duplicate rejection, paired-side protection, creation rollback/retry, and tab management remain covered. The production/test application blocks are synchronized.

The **known legacy Side restoration bug remains separate**. The focused `occasional_meals_browser.assignment(browser, filename, 320, 'Sides')` case fails its existing post-full-rotation/Back/reload assertion at line 87 in both the pre-Stage 3 HTML and Stage 3 HTML. It was not expanded or fixed here. The historical allocator and linked-group placement rules were preserved.

This is not a claim that every historical repository probe is green. Previously documented obsolete import/editor probes remain outside the passing full-suite claims above. Physical-device keyboards/gestures, screen readers, real quota exhaustion/process termination, cross-tab concurrency, and installed-PWA upgrades remain unverified. The mobile screenshot and Chromium tests do not establish those device guarantees.

Shell version `v102` is a source change for a future approved release; no deployment was performed. No Stage 4 onboarding/terminology/polish, recipe photos, unrelated redesign, merge, or deployment was included. Stop here for independent verification before further authorization.
