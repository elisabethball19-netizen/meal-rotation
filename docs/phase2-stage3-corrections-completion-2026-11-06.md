# Phase 2 — Stage 3 corrections completion report

Date: 2026-11-06 (UTC)  
Repository: [elisabethball19-netizen/meal-rotation](https://github.com/elisabethball19-netizen/meal-rotation)  
Branch: `codex/phase2-meal-rotation`  
Status: S3-1 and S3-2 corrected and tested; ready for another independent verification. No Stage 4 work, merge, or deployment performed.

## Starting point and commits

Corrections address [the independent Stage 3 verification](phase2-stage3-independent-verification-2026-11-06.md). Starting remote head: `c671bb46140ceed4b86ea00209debc861f081ff9`. Its application blobs match the reviewed Stage 3 source; the added independent report was preserved unchanged.

Published commits:

- [`904bcae44d6a8650b08f80ba4060777c90380a6a`](https://github.com/elisabethball19-netizen/meal-rotation/commit/904bcae44d6a8650b08f80ba4060777c90380a6a) — permanent reproduction and correction regressions.
- [`0b600acdf79f5ae5a00c9c676ea53dbee5bbf3ca`](https://github.com/elisabethball19-netizen/meal-rotation/commit/0b600acdf79f5ae5a00c9c676ea53dbee5bbf3ca) — targeted selection inheritance and explicit display-link clearing in both apps; shell v103.

This report is published in a subsequent documentation commit. The test commit intentionally exposes the old defects; the following implementation commit corrects them.

## Reproduction before application changes

Both confirmed findings were reproduced in both unchanged Stage 3 HTML apps before application edits:

- **S3-1:** create/schedule a recipe, exclude rice (or exclude both ingredients), copy to Rice through the existing picker, then use that copy's full Edit Meal editor to add Sides. The new membership materializes all ingredients instead of inheriting the shared identity's partial/empty selection.
- **S3-2:** clearing a record with multiple source fields leaves the fallback View Original Recipe link active. A fallback-only record also opens the lightweight editor with an empty field despite its visible source link.

The final permanent tests were additionally run against the preserved unchanged checkout and reproduced all **eight specific expected failures** (partial/empty membership inheritance and mixed/fallback source handling in each app). Reproduction mode checks the expected assertion message and does not accept arbitrary setup errors:

```sh
MEAL_STAGE3_EXPECT_FAILURES=1 MEAL_STAGE3_CORRECTION_SOURCE_ROOT=/path/to/unchanged-stage3-checkout python tests/phase2_stage3_corrections_browser.py
```

Run the tests/fixtures from the corrected checkout, pointing the environment variable to HTML from starting head `c671bb46140ceed4b86ea00209debc861f081ff9`.

## Exact corrections

### S3-1 — Full-editor additions inherit effective shared selections

The full Edit Meal membership-addition branch now initializes the new member's ingredient-selection array with the existing canonical `grocerySelectionsForMeal(source, selections)` reader. It no longer checks only the edited member's own array and falls back independently to all ingredients.

That reader already gives effective explicit selections priority across shared members, including an explicitly empty array. Thus additions from an original member, a picker-created copy with no own array, or a later full-editor-created member inherit the same effective choices. The genuine-new-recipe default-all behavior remains enabled when there is no explicit choice.

No recipe definitions, existing membership selections, rotation/Favorites records, or grocery progress are rewritten by this correction. Only the new membership receives the inherited array. The pre-existing identity/selection-union rules remain in use.

### S3-2 — Explicit display-link clearing without deleting provenance

The lightweight field and viewer action now use the same display-source helper. For legacy records without an explicit clear, it delegates to the existing URL resolver and retains its precedence and URL validation, including `sourceUrl` and `ingredientImportUrl` fallbacks.

An explicit clear stores optional boolean `recipeSourceHidden:true` on the shared recipe members. It suppresses the visible View Original Recipe action and makes the editor's display-link field empty. **Clearing leaves all four underlying URL fields intact**, along with import identifiers, references, recipe content, and other metadata. The original resolver remains available to import matching/enrichment; the new flag affects display only. Import enrichment cannot silently bring the visible link back.

A nonempty replacement updates the existing editable `url`/`originalRecipeUrl` fields and resets the flag, preserving unrelated fallback/provenance fields. Explicit URL edits through the full Edit Meal editor also reset the display state appropriately, so a cleared source can be deliberately re-enabled. Shared content propagation keeps the display decision consistent across `linkGroup` members.

This is an optional field in the existing recipe JSON, not a new localStorage key or backup schema. Absent/false uses legacy display behavior. Backup/restore retains the flag and provenance; no existing record receives a startup migration.

## Regression coverage

`tests/phase2_stage3_corrections_browser.py` adds 20 scenario groups across both app versions:

- Partial and complete exclusions, initial additions from originals and copies, three repeated full-editor additions using different shared members, reload after each addition, and backup/restore.
- Exact preservation of existing recipe records, ingredient selections, displayed schedules, grocery lines/checks, and Favorites ledgers during membership additions.
- Original/multiple-source, fallback-only `sourceUrl`, fallback-only `ingredientImportUrl`, and URL-only records; effective initial values, Cancel, replacement, explicit clearing, peer-member viewing, reopen, reload, backup/restore, and deliberate re-enabling.
- Exact preservation of stored source/import fields and recipe content on a display-only clear, including after import enrichment; full-editor URL editing can restore the visible action.
- Source-clear failed-save rollback, recovery export, Retry Save of the latest source edit, failed-clear cancellation, and unchanged durable records after cancellation.

The source fixtures use stable opaque import identifiers so unrelated legacy RecipeSage URL-repair normalization does not alter their captured baseline. The normal RecipeSage refresh/import workflows are separately exercised by the existing suites. Fixture initialization is allowed to settle before order/progress snapshots; existing correctness assertions were not weakened to accommodate those fixture details.

## Tests and actual results

All data was synthetic, in disposable Chromium contexts with intercepted fixture requests. No user recipes or live application storage were accessed. Every completed command below exited **0**. Commands are `python tests/<filename>`.

| Suite | Actual result |
| --- | --- |
| `phase2_stage3_corrections_browser.py` | PASS, exit 0 — 20 groups |
| `phase2_stage3_browser.py` | PASS, exit 0 — 28 printed groups |
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

Printed groups summarize scenarios, not individual assertions. RecipeSage refresh reports success by exit status without printed PASS groups. The correction suite also passes its eight-case unchanged-source reproduction mode.

All existing regression files remain unchanged in this correction pass. No existing correctness assertion was removed or weakened. The full relevant suites cover viewer completion, split/scale/tab/scroll behavior, grocery navigation and aggregation, explicit defaults/Ideas/exclusions, scheduling/rotation/history, weighted Favorites, temporary/empty slots, imports, pending drafts, journals, rollback/retry, and backup/storage compatibility.

Additional checks passed: all inline JavaScript in both apps and the service worker with `node --check`; Python test syntax; normalized production/test application equality; byte-for-byte preservation of the test-only shell/storage adapter/banner/reset controls; `git diff --check`; and published source/test blob hashes matching the tested local files.

## Separate existing issue and limits

The **legacy Side restoration issue remains separate and unchanged**. The focused `occasional_meals_browser.assignment(browser, filename, 320, 'Sides')` case failed the same post-full-rotation/Back/reload assertion at line 87 in both unchanged apps and both corrected apps. It was not necessary to fix that existing issue to correct S3-1/S3-2, and its scope was not expanded.

The historical scheduling allocator was not redesigned. Previously documented obsolete import/editor probes are not claimed fixed, and this report does not claim every historical repository test passes. Physical-device keyboards/gestures, screen readers, real quota exhaustion/process termination, cross-tab concurrency, and installed-PWA upgrades remain unverified. Source shell version `v103` prepares a future approved release; no deployment occurred.

Only these Stage 3 corrections, their permanent tests, and this report were included. Stop here for another independent verification; no Stage 4 work, merge, or deployment was performed.
