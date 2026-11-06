# Phase 2 — Stage 4 final corrections: independent verification

Date: 2026-11-06. Repository: `elisabethball19-netizen/meal-rotation`. Branch: `codex/phase2-meal-rotation`.

**CORRECTIONS REQUIRED**

The two reported corrections work: nested confirmation restores focus immediately, and group merge/Undo restores the previously lost scales and cooking sessions. However, a later grocery checkmark for an unrelated weekday and meal tab is still silently reverted by group Undo. This fails the requested preservation of later edits to unaffected occurrences. It reproduces on unchanged source, so it is an unresolved pre-existing acceptance defect, not a newly introduced final-correction regression.

## Reviewed source and exact files

Reviewed head: [`bb98e0a2264b254fae8c7fc82a4f771f6f1a5a50`](https://github.com/elisabethball19-netizen/meal-rotation/commit/bb98e0a2264b254fae8c7fc82a4f771f6f1a5a50).

Read the final completion report and previous independent review, inspected application commit `71f8c23aa9eadde90e09dc0524dbe88bc8db5552`, test commit `108898e074a8216166761a11e2b47d6bc8c05b7c`, and ordering-test addition `d495340678b9ee65278860078ea2155b18308523`, then executed the actual applications and tests.

| Tested file | Git blob SHA |
| --- | --- |
| `index.html` | `244782bf8a2cbddaa2e355c083fc9e3b4a5dba8b` |
| `meal-rotation-test.html` | `ace9ddbf83e69c084837ab0fa4e400cd37f82d56` |
| `service-worker.js` | `a0327e692a7e3ab7df32c63844ed4166d539a3e4` |
| `tests/phase2_stage4_final_browser.py` | `f9d84eb15357caf5d360ab166c5f6641b0a16dbc` |
| `tests/phase2_stage4_browser.py` | `6ebb438b91aebe121db2a5d149f482306aae0202` |
| `tests/phase2_stage4_corrections_browser.py` | `c81a1c897b0a341ff29fe64909a28143c7d3da6a` |

The unchanged comparison source is the application reviewed at report-only commit `7c515f3074644b16ecc4c10d4151d71f72e0a4df`: production blob `6ea5bb042b677917b345acf02a6bd4f68251429c`, test blob `a808d5b74c930bc14e6b520a744d2d62d88327c4`. Also reproduced the old merge loss against archived pre-Stage-4 source at `6bbcee63b2a377d3471a4b7266f16526997dfeed`.

All application files were tested exactly as fetched. Tests used installed Chromium/Playwright, synthetic fixtures, disposable contexts, intercepted external requests, actual UI handlers, and real keyboard/pointer/touch events. Hooks seeded synthetic records or read state. Supplemental checks were temporary scripts outside the repository. No application code or committed test was authored or modified during verification; this report is the only published change. No Stage 5 work, merge, or deployment occurred.

## Confirmed remaining defect

### S4F-IV-1 — Group Undo reverts later shopping progress on an unrelated occurrence

**Medium severity; blocking the requested complete preservation of later unaffected-occurrence edits. Pre-existing, independently reproduced on unchanged and final source.**

Reproduced in both HTML apps, with both an empty Destination and a Destination already containing a shared recipe. All eight source/app/destination combinations fail identically.

Reproduction using actual UI actions:

1. Before the group operation, prepare an unrelated one-time Lunch/Thursday meal containing **7 apples**, initially unchecked. It does not belong to the Rice group being moved. Keep the existing Dinner/Tuesday meals and linked sides in the fixture.
2. Keep/move Rice into Destination through the group-delete dialog.
3. Open **Grocery List** and check the apples checkbox. Verify its source is Lunch/Thursday and its checkmark is now true.
4. Press the application's **Undo** button once.

Actual: the group operation is undone, but the unrelated apples checkmark changes **true → false**. Reload retains the lost shopping progress. The grocery checkbox handler creates no Undo entry: independent history capture confirmed the Undo/Redo stacks did not change when the checkbox was checked, so that Undo really targets the preceding group move, not a separate shopping action.

Expected: restore the group operation and its affected data while retaining the later checkmark for the unrelated occurrence. The quantity and temporary meal remain present; the defect is loss of the later shopping state.

Source evidence: `restoreState` still replaces the entire `checkedIngredients` set and `groceryOccurrenceChecks` object from the old snapshot. The new group metadata selectively restores cooking/scaling keys and changed ingredient-selection keys, but does not apply equivalent selective preservation to later shopping checks. Relevant code is `restoreState` near `index.html:4065` and the grocery checkbox handler near `5111`.

This finding is separate from the four older baseline failures below, and separate from the now-fixed merge scale/session loss. No new regression is inferred merely from its discovery: the actual unchanged-source comparison confirms its pre-existing attribution.

**Required follow-up:** add the real Grocery List checkbox workflow above to both merge variants, preserve later shopping changes on unaffected occurrences, and assert the result through reload/backup. Keep complete comparisons for the changed day and all cooking/scaling state; do not reinstate the former changed-day exception.

## S4C-IV-1 — Nested confirmation: verified fixed

Against unchanged source, both apps at **280px, 320px, and 360px** reproduce the original finding: confirming the nested side-pair selection leaves focus at `BODY`, and immediate Escape fails to close the parent weekday picker.

Against corrected source:

- Confirmed **Independent → Dependent side for Rice** and **Dependent → Independent** separately at all six app/width combinations. Each immediately focuses the replacement Side for Sides button inside the parent. Immediate Escape closes the parent **without any intervening Tab**, and focus returns to the weekday heading.
- Tab and Shift+Tab remain contained; background focus attempts fail to steal focus.
- Supplemental pointer and touch confirmations and explicit child Cancel buttons pass at 280/320/360px in both apps. Cancel preserves complete captured records/plans/queues/cooking/grocery state and returns focus inside the parent.
- Existing heading/planner entry, setup cancellation, Leave Empty/Resume, and parent Escape/Close behavior pass their correction suites. Side selections persist correctly; dependent-side, Favorites, queue, and linked-slot regression checks also pass for their fixtures.

The optional return-focus resolver is narrowly integrated: the side-pair caller resolves its replacement button after rendering; other value-chooser callers retain their previous behavior. No delayed Tab or synthetic focus-repair key is needed.

## S4C-IV-2 — Complete merge restoration: verified fixed for operation state

Reproduced the original scale/session loss on both unchanged apps and both archived pre-Stage-4 apps. After Keep/move into an already-shared destination and actual Undo, recipe records return but saved scales and cooking sessions each fall **5 → 2**, and grocery quantities differ.

The corrected applications pass complete-state equality after Keep/move and Undo, with both an empty destination and an existing shared membership. Comparisons include:

- Exact ordered recipe IDs, every recipe field, memberships, group order/display metadata and identities.
- All plans, rotation queue ordering, nonempty Favorites ledgers, and rotation history.
- Main, attachment, side, repeated-weekday, and other-tab occurrence scales.
- Complete cooking-session records, ingredient/instruction tokens, automatic ingredient completion, and true/false ingredient overrides.
- Explicit ingredient exclusions, an explicitly empty selection, complete grocery contribution records, actual scaled lines/quantities, checkmarks, and legacy check state.
- Undo → Redo → Undo, moved-state persistence, restored-state reload, and backup/restore.
- Later unrelated cooking/scaling changes, preserved through Undo and persistence while the operation's affected occurrences return exactly.

**No changed-day quantities, cooking sessions, or scales are excluded.** Supplemental tests also seed actual meal-level and tab-level grocery exclusions and compare filtered visible contributions exactly through Undo/Redo/Undo, reload, and backup restoration in both destination variants.

The preservation gap in S4F-IV-1 concerns later shopping changes. The successful initial-state and cooking/scaling comparisons do not establish that those later checkmarks are preserved.

## Storage failures, recovery, and history

In addition to the committed tests, independently exercised both apps with injected write failures at:

- Group Keep/move: group display order, cooking sessions, occurrence scales, selected ingredients, and primary recipe data.
- Undo: cooking sessions, occurrence scales, and group display order.

For the ten supplemental failed-move cases, memory and durable records remain at the prior state, and the **entire Undo and Redo stacks remain exactly unchanged**. This was tested with an existing Redo entry as well as existing Undo history. Failed attempts therefore do not silently insert unusable history entries. Retry commits exactly one usable entry; subsequent Undo → Redo → Undo restores the complete expected states.

Recovery validation went beyond testing whether proposal keys exist:

1. Downloaded the actual recovery export.
2. For a failed move, extracted the complete `group-removal` proposal.
3. For failed Undo, overlaid `unsaved` writes/removals onto the export's readable `storage`, following the documented recovery format.
4. Restored that complete storage into a fresh context, reloaded, and compared **every captured domain field** against the intended successful state.

All sixteen supplemental failure/recovery cases pass. A fixed synthetic clock was used when comparing separate successful/failed attempts, so legitimate assignment timestamps remain comparable; timestamp fields were not dropped from the comparisons.

Failed Undo keeps the complete intended result in memory with an explicit unsaved warning. Successful writes may already be durable while a failed key retains its old value: generic Undo is not one atomic multi-key replacement. The export retains the complete recoverable intent, and Retry, Redo/Undo, reload, and backup checks pass after resolving the failure. This is the existing warned-pending-write contract, not a claim that failed Undo is already fully saved.

The group wrapper's successful-history entry is added only after commit. It reuses the storage draft/validated replacement bridge; cloned mutable state is rolled back on failed group commits. Undo metadata is in-memory only, preserving existing localStorage and backup schemas.

## Regression quality and missing boundary

The new focused test performs actual group-dialog confirmation, Undo/Redo buttons, nested chooser controls, recovery downloads, and Retry Save. It asserts complete structured state, rather than matching names or intersecting grocery keys. Fixture guards require real scales, nonempty Favorites scores, completion tokens and overrides, so those comparisons are meaningful.

The modified older Stage 4 test now requires exact grocery equality **unconditionally**, including the formerly excluded merge day. It also asserts that all unaffected contributions remain present. Structural comparison confirms only `group_delete` changed among existing functions in that file. No earlier correctness assertion was weakened; the change strengthens them. Unrelated earlier regression files were not changed by these final corrections.

Important coverage gap: `retained_progress` edits only cooking/scaling metadata. It never checks an unrelated Grocery List item between move and Undo, so the successful test misses S4F-IV-1. The final state helper includes grocery checks, but its expected state does not contain a later shopping edit. Add that edit, not an exemption from the state comparison.

Supplemental checks also closed boundaries absent or incomplete in the new committed test: immediate Escape after the **reverse** confirmation without intervening traversal, pointer/touch confirmation and explicit Cancel at every width, full recovery proposal reconstruction, exact failed-operation history stacks, and filtered meal/tab grocery exclusions.

## Complete regression executions

The 31-suite batch completed with no failures. The separately run complete historical weekday suite also passed. Phase 1 safety corrections are run alone afterward to avoid the previously observed native file-chooser focus interference.

| Focused suite | Result |
| --- | --- |
| `phase2_stage4_final_browser.py` | 30 PASS groups, exit 0 |
| `phase2_stage4_browser.py` | 38 PASS groups, exit 0 |
| `phase2_stage4_corrections_browser.py` | 18 PASS groups, exit 0 |
| Full `weekday_setup_browser.py` | Passed, including original historical comparison |

The following 29 existing suites were rerun; names omit `_browser.py`:

- Stage 3: `phase2_stage3_corrections`, `phase2_stage3`.
- Stage 2: `phase2_stage2_corrections`, `phase2_stage2`.
- Stage 1: `phase2_stage1_corrections`, `phase2_stage1`, `phase2_stage1_workflows`.
- Phase 1: `phase1_final_recovery_safety`, `phase1_data_safety`, `phase1_safety_corrections`.
- Groceries/scheduling: `grocery_rotation_checks`, `favorites_weighted`, `scheduled_linked_slots`, `dependent_side_groups`, `manual_duplicate_meal`, `scheduled_date_integrity`, `skip_this_week`, `shared_week_scheduling`, `outgoing_cooked_dates`.
- Recipes/groups/viewer: `recipesage_refresh`, `meal_groups_bulk_safety`, `add_recipe_ideas`, `recipe_tabs`, `recipe_touch`, `shared_recipe_management`, `needs_tweaking`, `rotation_dialog_layout`, `recipe_tab_reorder`, `group_order`.

**All 33 complete suites passed, exit 0**, comprising the three Stage 4 suites, full weekday suite, and 29 existing suites above. The isolated `phase1_safety_corrections` execution passed all **26 printed scenario groups** on this run, with no file-chooser retry needed.

The passing suites do not include the supplemental negative reproduction of S4F-IV-1 or the separately reproduced older baseline failures. Those failing behaviors remain defects despite the successful complete-suite executions.

Static verification passes: normalized shared JavaScript and CSS match between apps; only the established storage-provider and test-banner differences remain. The test storage adapter/reset controls are unchanged, production-storage sentinels survive, and all inline scripts plus the v106 service worker pass `node --check`. Tested source matches the Git blobs listed above. No new migration or backup schema is introduced.

## Four older baseline failures — separate

The original targeted failure paths still fail at the same boundary in both unchanged and final apps: sixteen expected comparison failures across four paths, two apps, and two sources. No new attribution is inferred from their continued failure.

| Existing issue | Reproduced boundary |
| --- | --- |
| Legacy Side restoration | `occasional_meals_browser.py:87`, Side assignment after Rotate Back/reload. |
| Duplicate allocation | `rotation_no_duplicates_browser.py:83`, Weekend allocation; same Saturday ID 4 / Sunday ID 2 / Lunch Tuesday ID 3 rows. |
| Legacy linked occurrence | `cycle_linked_occurrences_browser.py:73`, `legacy-pin` Thursday occurrence changes ID 1 → ID 2. |
| Heading spacing | `page_heading_spacing_browser.py:37`, 14px content gap versus asserted 8px at 280px. |

These targeted failures are not counted as passing complete suites and do not imply execution of the rest of those failing suites. S4F-IV-1 is documented separately rather than being folded into this older list.

The full weekday setup suite passes, including its original historical-height comparison supplied exact GitHub HTML from `309866412d9b7778128c5dc8ea58f4a54b0e4f59` without modifying assertions. Historical/current heights remain **847px → 541px** at 320/360px in both apps. That formerly unavailable local object leaves no unresolved comparison gap here.

## Limitations and conclusion

Chromium viewport and simulated touch tests do not certify native iOS/Safari behavior, real assistive-technology announcements, or a deployed service-worker upgrade. Existing Undo/Redo history remains in memory; reload/backup checks verify the resulting saved state, not persistence of the Undo stack itself. These are limitations, not newly confirmed defects.

Both reported final corrections are verified. No newly introduced final-correction regression was confirmed in the completed comparisons. Nevertheless, the requested complete preservation of later unrelated occurrence edits still fails for actual shopping checkmarks. Correct S4F-IV-1 before Stage 5 authorization, retaining the complete cooking/scaling and changed-day regression assertions. Keep the four older baseline failures tracked separately.

**CORRECTIONS REQUIRED**
