# Phase 2 — Stage 3 Corrections: Independent Verification

Date: November 6, 2026 (UTC)

**Decision: READY FOR STAGE 4**

No confirmed blocking defect was found. S3-1 preserves effective explicit grocery choices across repeated membership additions, including empty selections. S3-2 makes source-link clearing persistent and consistent with the viewer while retaining import provenance. The older legacy Side restoration issue remains reproducible and separate.

This is a verification result, not authorization to begin Stage 4, merge, or deploy. Owner review remains required.

## Scope and provenance

- Repository/branch: `elisabethball19-netizen/meal-rotation`, `codex/phase2-meal-rotation`.
- Reviewed head: [`be2b644eb7b02ccee5912dd516e776f586803a9b`](https://github.com/elisabethball19-netizen/meal-rotation/commit/be2b644eb7b02ccee5912dd516e776f586803a9b). Correction implementation: `0b600acdf79f5ae5a00c9c676ea53dbee5bbf3ca`; new tests: `904bcae44d6a8650b08f80ba4060777c90380a6a`.
- Started with the [corrections completion report](phase2-stage3-corrections-completion-2026-11-06.md) and [previous independent findings](phase2-stage3-independent-verification-2026-11-06.md), then inspected actual code changes and regression assertions.
- Compared with preserved unchanged Stage 3 HTML from starting head `c671bb46140ceed4b86ea00209debc861f081ff9`. The new suite reproduces **all eight specific expected failures** there: partial/empty inheritance and mixed/fallback source handling in both apps. The corrected source passes **20 reported scenario groups**. Reproduction mode checks the expected assertion text, not arbitrary browser exceptions.
- GitHub supplied source because the workspace Git proxy was unavailable. Materialized Git blob hashes match published files: production `f7f33ac6f64bd9f526a39eff70fd61fdcb64ea54`, test `8f37b89b16f78809a9e6dd0a334bc9483dfb9daa`, service worker `3fe93897856ed8ab33d264d75a51309b00b4ac6f`.
- All data was synthetic, in disposable Chromium contexts with intercepted fixture requests. Supplemental probe scripts stayed outside repository source. No real user storage was accessed, application/test fixes made, Stage 4 work begun, or merge/deployment performed. Only this report is published.

## S3-1 — Grocery exclusion preservation: PASS

The [full-editor membership-addition branch](https://github.com/elisabethball19-netizen/meal-rotation/blob/be2b644eb7b02ccee5912dd516e776f586803a9b/index.html#L6746) now initializes the new member's selection using `grocerySelectionsForMeal(source, selections)`. It therefore inherits effective shared choices instead of defaulting from the edited member's missing local array. No existing selection-reader semantics or ingredient defaults were globally replaced.

Verified in both HTML apps through real creation, ingredient chooser, copy picker, and full Edit Meal controls:

- Excluding rice while retaining apples stays `['3 apples']` after copying and further membership additions.
- Excluding every ingredient stays `[]`; neither ingredient returns.
- Additions initiated from the original member, a picker-created copy without its own saved array, and a later full-editor-created member all inherit the effective choice.
- Three successive full-editor additions using different shared members preserve actual scheduled grocery contributions and the new members' stored arrays.
- Existing selection arrays and existing recipe records remain exact during the subsequent additions; intended new membership records are added normally.
- Scheduled rows, grocery checkmarks and line quantities, and Favorites state remain unchanged. Reload after individual additions and full backup/restore retain the result.

An independent supplemental probe strengthens the suite's empty-ledger cases: it creates a real Favorite and **nonzero Favorites ledger**, checks groceries, scales the scheduled recipe, and repeats additions from original/copied members. Complete source/check/quantity/scale and credit state remains equal before/after each addition and persistence boundary. Both partial and empty selections pass in both apps.

A separate genuine-new-recipe case starts in the full editor with `groceryDefaultAll:true` and **no explicit source selection array**. Its ingredients are included when scheduled and remain included after a full-editor membership addition. Thus the fix preserves exclusions without disabling the intended default-all behavior.

## S3-2 — Source-link clearing: PASS

The [display-source helper](https://github.com/elisabethball19-netizen/meal-rotation/blob/be2b644eb7b02ccee5912dd516e776f586803a9b/index.html#L2139) returns no visible source when `recipeSourceHidden===true`; otherwise it uses the existing source resolver. Both the lightweight editor and View Original Recipe use that display decision. The original resolver remains available to matching/enrichment.

The [lightweight mutation](https://github.com/elisabethball19-netizen/meal-rotation/blob/be2b644eb7b02ccee5912dd516e776f586803a9b/index.html#L8264) records a clear as a display flag, rather than deleting provenance. A nonempty replacement updates the editable URL fields and clears the flag. Shared-field propagation applies the display decision across recipe members. The [full editor's explicit URL-change path](https://github.com/elisabethball19-netizen/meal-rotation/blob/be2b644eb7b02ccee5912dd516e776f586803a9b/index.html#L8672) also updates that flag appropriately.

Verified the following record shapes in both apps:

| Source fields | Result |
| --- | --- |
| `originalRecipeUrl` plus `url` | Effective initial field, clear, persistence, and replacement pass |
| Fallback-only `sourceUrl` | Pass |
| Fallback-only `ingredientImportUrl` | Pass |
| All four source fields populated | Pass |
| `url` only | Pass |
| Shared recipe members with different stored source fields | Shared clear/reopen and deliberate re-enable pass |

Supplemental direct-first-clear probes check each shape **before** inserting a replacement URL. Clearing hides View Original Recipe, reopening shows an empty field, and full recipe records remain equal except for the expected display flag. All four stored URL fields and matching/import metadata remain intact. Exact records survive backup/restore and reload. A replacement entered from another shared member restores the visible link. The repository suite also verifies deliberate full-editor URL re-enabling.

### Enrichment and import provenance

The suite checks that helper-driven enrichment does not restore a hidden link. An additional independent workflow uses actual **file-import matching/enrichment UI** with real-format RecipeSage identifiers and canonical reference records. Existing source records receive a missing note from the import, demonstrating that enrichment occurred; record count, URL provenance, identifiers, explicit Ideas status, and ingredient selections remain intact. The hidden decision survives enrichment, reload, and backup/restore, and the editor stays intentionally empty.

The supplemental fixture initially used noncanonical reference objects; import normalized them by adding an empty `sourceId`. That was not provenance loss. The fixture was initialized canonically before final exact-record comparisons; URL/identifier preservation assertions were retained.

### Failure handling, recovery, and latest draft

The new suite passes failed-clear rollback, recovery export, Retry Save of a later nonempty replacement, and cancellation after another failed clear. Durable records and visible source state remain unchanged after cancellation.

An independent reverse case also passes: start hidden, attempt a replacement that fails, then return the latest draft to an empty field. Recovery export contains that latest empty draft. Retry resolves the operation with the original hidden records intact, rather than applying the abandoned replacement proposal. This verifies both directions of the display decision and live-draft retry behavior.

## Regression and data safety

Independently rerun suites cover lightweight content editing, unchanged/ambiguous completion tokens, linked tab order/identity, split geometry, scaling/scrolling, grocery recipe navigation and shopping progress, new defaults/explicit Ideas, shared quantities, and existing full-editor/shared-content behavior.

Stage 2 tests cover Schedule Meal, unsupported duplicate rejection, paired-side queue/Favorites protection through Back, guarded creation/Undo/rollback/Retry, and meal tabs. Stage 1 tests cover temporary meals, empty holds, grocery preservation/reset, Undo, Rotation Back, and drag ordering. Phase 1 tests cover durable originals, journals, interrupted replacement, pending drafts, strict rollback, exports/retry, and backup compatibility.

The new display flag is optional recipe JSON. No new storage key or startup migration was introduced. The selection fix writes the inherited array only for the new member. Core recovery/replacement code was not modified in this correction diff.

Normalized shared application-script equality passes. The test-only shell outside that block is byte-for-byte unchanged, including its storage prefix, banner, and reset controls. Synthetic production sentinels survive test-app workflows. All inline scripts and the service worker pass `node --check`. Shell v103 was inspected, not deployed.

## Independent execution record

| Suite/probe | Result |
| --- | --- |
| `phase2_stage3_corrections_browser.py` | PASS — 20 reported groups, both apps |
| Same suite against unchanged Stage 3 source with reproduction flags | PASS — eight specific failures reproduced |
| `phase2_stage3_browser.py` | PASS — existing 28-group Stage 3 suite |
| `phase2_stage2_corrections_browser.py` | PASS |
| `phase2_stage2_browser.py` | PASS |
| `phase2_stage1_corrections_browser.py` | PASS |
| `phase2_stage1_browser.py` | PASS |
| `phase2_stage1_workflows_browser.py` | PASS |
| `phase1_final_recovery_safety_browser.py` | PASS |
| `phase1_safety_corrections_browser.py` | PASS |
| `phase1_data_safety_browser.py` | PASS |
| `grocery_rotation_checks_browser.py` | PASS |
| `favorites_weighted_browser.py` | PASS |
| `scheduled_linked_slots_browser.py` | PASS |
| `dependent_side_groups_browser.py` | PASS |
| `shared_week_scheduling_browser.py` | PASS |
| `recipe_tabs_browser.py` | PASS |
| `recipe_tab_reorder_browser.py` | PASS |
| `recipe_touch_browser.py` | PASS |
| `add_recipe_ideas_browser.py` | PASS |
| `shared_recipe_management_browser.py` | PASS |
| `recipesage_refresh_browser.py` | PASS |
| Supplemental selection/Favorites/scale/default-all probes | PASS — both apps |
| Supplemental direct-clear source-field matrix/shared persistence | PASS — both apps |
| Supplemental matching import and reverse latest-draft Retry | PASS — both apps |

These are results from this verification, not inherited completion-report claims. The known failing legacy case below is separate and is not counted as a passing suite.

## Test quality and remaining boundaries

The new assertions compare effective grocery contributions and stored selections, old records, shopping progress, queue/Favorites state, displayed schedules, provenance fields, and persistent state. They exercise original/copied members, repeated additions, both exclusion extremes, shared sources, rollback, and specific old-failure messages. This is meaningful regression coverage rather than merely checking successful function returns.

Confirmed from commit file lists that the test commit adds only `phase2_stage3_corrections_browser.py`; the implementation commit changes only the two apps and service worker. **No existing regression file or correctness assertion was changed or weakened in this correction pass.**

The independent additions address important gaps in the supplied cases: a nonzero Favorites ledger and scaled shopping state; a genuinely new recipe without any explicit array; direct clearing of every source shape before replacement; real matching file-import enrichment instead of only the helper; and Retry from a failed replacement back to an empty latest draft. These probes found no confirmed blocking defect.

Physical-device keyboards/gestures, screen readers, real quota exhaustion/process termination, cross-tab concurrency, and installed-PWA upgrades remain unverified. Chromium emulation and injected write failures do not establish those device guarantees. This review does not claim every historical repository probe passes.

## Separate pre-existing issue

The **legacy Side restoration bug remains unchanged**. Independently executed `occasional_meals_browser.assignment(browser, filename, 320, 'Sides')` on both pre-correction and corrected HTML apps. All four fail the same post-full-rotation/Back/reload assertion at line 87. Previous reviews also reproduced it on earlier source. No new legacy Side regression was demonstrated by these corrections. Historical obsolete import/editor probes are not claimed fixed.

No confirmed blocking defect remains in the reviewed correction areas. Retain the existing issue/device limits in follow-up tracking and obtain owner authorization before Stage 4.

**READY FOR STAGE 4**
