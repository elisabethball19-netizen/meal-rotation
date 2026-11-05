# Phase 2 — Stage 1 Independent Verification

Review date: November 5–6, 2026 (UTC). Requested report date: November 5, 2026.

**Decision: CORRECTIONS REQUIRED**

Three confirmed Stage 1 defects remain: Undo loses temporary scheduling when changing to a reusable recipe; changing a one-time meal on an unconfigured day silently leaves that day unscheduled; and a legacy occasional meal's own reorder handle does not work. The reported legacy Side restoration failure is real but predates Stage 1. No regression in the Phase 1 persistence/recovery machinery was found in the inspected code and synthetic checks.

## Scope and provenance

- Repository: `elisabethball19-netizen/meal-rotation`; reviewed branch: `codex/phase2-meal-rotation`.
- Reviewed head: [`d91533bde22c0fb3c94f41bf6baad8af7eee08c4`](https://github.com/elisabethball19-netizen/meal-rotation/commit/d91533bde22c0fb3c94f41bf6baad8af7eee08c4). Implementation ends at `549bfa0e9ae8aa691a87dbd5c9a6ae6398299432`; the reviewed head adds the completion report.
- Phase 1 comparison: [`b362c19bcd57ec8259729f43c7ef552b7dd74089`](https://github.com/elisabethball19-netizen/meal-rotation/commit/b362c19bcd57ec8259729f43c7ef552b7dd74089).
- Started with [the completion report](phase2-stage1-completion-2026-11-05.md), then inspected the production/test HTML diff against Phase 1, scheduling and history routines, grocery reconciliation, validators, recovery code, gesture handlers, and the tests themselves.
- The Git proxy was unavailable. Files were obtained through the GitHub connector and materialized locally. Production/test HTML Git blob hashes match GitHub: `eb9a328d131d05481083ec2cf7e9c259f6c62274` / `fea9fb91c4163bd532b016edc81d44a57a79da5c`.
- All browser storage and recipes were synthetic, in disposable Chromium contexts with intercepted fixture requests. Independent probe scripts were kept outside repository source. No real user data was accessed. No application/test code, merge, deployment, or Stage 2 work was performed. The owner explicitly allowed a report-only commit to resolve the original no-commit/publication conflict.

Source links below are pinned to the reviewed head. Line references use production HTML; the same defects reproduce in `meal-rotation-test.html`.

## Confirmed Stage 1 defects

### R1 — High: Change Meal takes its Undo snapshot after deleting temporary state

**Reproduction, in both apps:**

1. On an assigned group, add a one-time meal named `Potluck` with `2 cups rice` and `3 apples`.
2. Change it to a reusable recipe that is not already scheduled elsewhere.
3. Undo the change.

**Expected:** recover the exact one-time meal, stable ID, entered grocery lines, and applicable checks. **Actual:** the underlying planned recipe returns. The one-time descriptor is absent from the Undo state, so its name and groceries cannot be recovered by undoing this change. The same sequence starting with **Leave Empty This Week** fails to restore the empty slot and resumes the underlying plan instead.

**Cause:** [`applyManualWeekdayMeal`](https://github.com/elisabethball19-netizen/meal-rotation/blob/d91533bde22c0fb3c94f41bf6baad8af7eee08c4/index.html#L7126) captures `beforeState`, calls `clearTemporarySlot`, and only then calls `snapshot()` on the ordinary non-replacement path. The earlier intact `beforeState` is used for the duplicate-source rotation path, but not this ordinary path. Thus the snapshot already lacks the temporary slot.

Independent reproduction used the existing Stage 1 fixture and its existing `manual()`/`undo()` hooks: `weekTest.once(); weekTest.manual(); weekTest.undo()`. Before Undo, the original temporary entry has a `once-...` ID. After Undo, `weekSchedule.slots` is `{}`, and recipe 1 is scheduled instead. `weekTest.empty(); weekTest.manual(); weekTest.undo()` likewise leaves no empty descriptor. This is new Stage 1 state and a newly added clear operation, not a baseline failure.

**Correction criterion:** capture/use the intact pre-change state for every Change Meal path. Add regressions for one-time-to-recipe and empty-to-recipe Undo, including grocery quantities/checks and unrelated slots. Do not fix this by restoring old recipe definitions from rotation history.

### R2 — High: Change Meal on an unconfigured one-time day silently removes the schedule

**Reproduction through real UI, in both apps:**

1. Leave Sunday without assigned groups. Add a one-time `Potluck` there.
2. Tap its name, choose **Change meal**, search for an otherwise unscheduled reusable recipe (`Third Main` in the fixture), select it, and Save.

**Expected:** the selected reusable recipe is scheduled for Sunday through the supported unconfigured-day/occasional scheduling path; its groceries appear. **Actual:** Sunday has no displayed meal. `Potluck` and its groceries disappear; the selected recipe and its groceries do not replace them. No JavaScript error or explanatory rejection occurs.

The saved plan contains `weekdayMealOverrides['Sunday::@day']='3'` and matching `cycleRetainedSlots`/`cycleSlotChoices` entries, but neither a Sunday assignment nor an `occasionalMeals` entry. `weekSchedule.slots` is empty. These records do not produce a scheduled Sunday meal; this is a persisted scheduling error, not merely a rendering delay. R1 also prevents ordinary Undo from recovering the cleared temporary meal.

**Cause:** the [temporary meal options](https://github.com/elisabethball19-netizen/meal-rotation/blob/d91533bde22c0fb3c94f41bf6baad8af7eee08c4/index.html#L7074) pass `category='@day'` to `openWeekdayMealChooser` without the unconfigured-day `occasional` flag. Save consequently takes the ordinary group-override branch of `applyManualWeekdayMeal`, then clears the valid temporary slot. The [empty-slot options](https://github.com/elisabethball19-netizen/meal-rotation/blob/d91533bde22c0fb3c94f41bf6baad8af7eee08c4/index.html#L5695) already normalize this sentinel and set the appropriate flag, demonstrating the inconsistent routing.

**Correction criterion:** normalize the synthetic day slot at the temporary meal's Change Meal boundary and preserve normal duplicate-choice behavior. Cover reusable recipes, Ideas, linked groceries, reload, backup/restore, and Undo on an unconfigured day. Do not create permanent `@day` group overrides.

### R3 — Medium: Legacy occasional meals cannot be reordered with their own handle

**Reproduction, in both apps at 320px:**

1. Use the existing occasional-meal fixture: schedule legacy `Occasional curry` (recipe 2) on Monday, with linked side recipe 12, then assign Monday to the `Sides` group. Two independent rows are displayed: `Replacement Linked Side`, then `Occasional curry`.
2. Focus the curry's reorder handle and press Arrow Up. The rows do not move.
3. Hold its handle for more than 450 ms and pointer-drag it above the side. The rows still do not move.

The drag saves Monday order as `['["Rice"]','["Sides"]']`, but the displayed order remains side then curry. This was tested separately from the known legacy Rotation Back failure and does not require performing Rotation Back.

**Cause:** [`scheduleDisplayKey`](https://github.com/elisabethball19-netizen/meal-rotation/blob/d91533bde22c0fb3c94f41bf6baad8af7eee08c4/index.html#L5626) includes the `occasional` flag and recipe ID for legacy occasional entries, producing `["Rice","occasional","2"]`. [Row metadata and handle creation](https://github.com/elisabethball19-netizen/meal-rotation/blob/d91533bde22c0fb3c94f41bf6baad8af7eee08c4/index.html#L7027) reconstruct `{cat,meal,linkedTo}` and omit `occasional`. The handle searches/stores `["Rice"]` instead. Keyboard lookup returns `-1`; drag stores a key the ranker does not recognize for that meal.

**Correction criterion:** use the same complete slot identity for planner entries, rendered rows, pointer drag, and keyboard ordering. Add a legacy occasional-plus-assigned-group reorder regression. Ordinary new one-time and normal group ordering tests already pass.

## Results against the seven requested checks

| Check | Independent result |
| --- | --- |
| 1. Skip This Meal preserves replacement behavior | **Pass for reviewed scenarios.** Skip implementation remains intact apart from the label and adjacent new action. Full skip suite passes: replacement/no-alternative, linked slots, checks, retained progress, and Undo. |
| 2. Empty individual groups/whole days without queue advancement | **Pass for direct empty/resume-via-rotation flows.** Tests confirm assigned groups remain, unrelated groups/tabs survive, hidden attachments disappear, queue order/Favorites credits do not advance, selected/full expiry and Back work. **R1** breaks Undo when subsequently changing an empty slot to a reusable recipe. |
| 3. One-time meals and groceries across lifecycle operations | **Pass for tested direct lifecycle flows:** reload; selected/full rotation; unselected temporary slots retained; expired groceries removed; partial/full Back; ordinary temporary-action Undo; backup/restore; quantities and occurrence checks; no recipe resurrection after deletion. **Fails at Change Meal boundaries: R1 and R2.** Existing passing tests do not cover these transitions. |
| 4. Manual/temporary scheduling preserves queues and Favorites | **Pass for inspected/tested queue invariants.** Manual substitutions and linked Ideas do not consume ordinary queue positions on expiry. Full Favorites suite and Stage 1 workflows pass. The temporary layer does not enter reusable recipe definitions or ingredient-selection storage. This does not imply the Change Meal/Undo state itself is correct; see R1/R2. |
| 5. Drag ordering coexists with swipe/long press | **Pass for ordinary/new temporary entries in Chromium at 320/360px:** pointer long-press, touch drag, keyboard, reload/backup, full Back ordering. Handles are excluded from swipe initiation; recipe name long-press remains separate. **R3** fails the legacy occasional-entry case. Physical-device behavior remains unverified. |
| 6. Phase 1 safety, journals, saved-data compatibility | **No new persistence/recovery regression found.** All three Phase 1 safety suites pass, including original-data export, incomplete replacement, journal history, retries, pending drafts, malformed startup/backup rejection, strict bulk rollback, recipe-definition preservation and deletion cleanup. New temporary records use existing plan serialization and optional validation. R1 is a scheduling snapshot defect, not a failure of the durable replacement journal. |
| 7. Production/test synchronization and isolation | **Pass.** Shared inline persistence/application scripts are byte-identical after normalizing the intentional `testStorage`/`localStorage` adapter differences. Test prefix, banner, reset controls, manifests/icons remain separate. Synthetic production sentinels survive test-app scenarios. Both HTML files reproduce the same confirmed defects. |

## Baseline failures investigated

These are classified separately from R1–R3. A passing focused case is not presented as a passing full legacy suite.

| Reported failure | Independent investigation | Classification |
| --- | --- | --- |
| Legacy Side assignment restoration in `occasional_meals_browser.py` | Ran `assignment(browser, filename, 320, 'Sides')` against both unchanged Phase 1 HTML files and both Stage 1 HTML files using the same synthetic fixture. All four fail the same post-full-rotation/Back/reload assertion at line 87, expecting side recipe 12. | **Confirmed existing scheduling defect, not introduced by Stage 1.** Keep tracked; do not attribute it to new `weekSchedule` entries or claim the full occasional suite passes. |
| `editor_return_browser.py` validation case | Ran `invalid_and_navigation` on Phase 1 and Stage 1 production HTML. Both time out filling hidden `#prep` without opening Timing. | **Existing test interaction problem.** Does not independently demonstrate a new validation defect. |
| `compact_meal_editor_browser.py` long layout | Ran `long_layout` on both versions. Both wait for absent `#preferredSideGroups`. | **Existing stale-selector coverage gap.** Long layout is not verified by this failed probe. |
| Import audit repair hook | Ran `recipe_import_audit_browser.repair_tests` on both versions. Both raise `ReferenceError: openRecipeInstructionRepair is not defined`. Parser/extraction cases pass separately through the Stage 1 workflow suite. | **Existing repair/test-hook failure, not a Stage 1 regression.** Repair scenarios remain unverified. |
| Import cleanup reviewed-save failure | Full `import_cleanup_browser.run` reaches line 146 on both versions and fails `assert state()==before` after injected save failure. | **Confirmed existing assertion/queued-save-policy mismatch.** The failure is not new; passing Phase 1 durability/recovery checks are the evidence for durable storage safety. This review does not claim the entire import workflow is green. |
| Historical no-Favorites parity (`8177685`) | Retrieved both historical HTML files through GitHub. Substituted only the fixture's `git show` source lookup with those fetched bytes; ran its existing `no_favorites_parity` comparisons. Both apps pass 15 whole-week rotations against pre-weighting source. | **Original infrastructure limitation resolved for this comparison; no sequence regression found.** Other current integration cases pass through the workflow suite. |

## Additional grocery-state observation

A synthetic check confirmed that **Leave Empty This Week → Resume planned meal** clears previously checked grocery quantities for the temporarily hidden meal and its hidden attachment, while retaining the independently displayed side's checks. Example before/after: recipe IDs `1,20,10` have checks `true,true,true` then `false,false,true`.

This follows `changeTemporaryWeek` calling `reconcileRotatedGroceryChecks(before,[])`, which rebuilds checks from only active contributions; hidden sources are removed and return as new unchecked sources. No recipe or grocery quantity is deleted. The completion report does not define whether explicit Resume should recover purchases already checked before hiding. **Confirmed behavior requiring an explicit acceptance decision, not counted as a separately established blocking defect.** If Resume is intended to restore the same occurrence's progress, add preservation/restore coverage before accepting that behavior.

## Validation record

The following repository suites were independently executed with synthetic records and exited successfully:

| Suite | Result |
| --- | --- |
| `phase2_stage1_browser.py` | PASS — 14 reported case groups, both HTML apps, 320/360px UI cases |
| `phase2_stage1_workflows_browser.py` | PASS — 28 reported checks, both apps |
| `phase1_final_recovery_safety_browser.py` | PASS — 16 reported groups |
| `phase1_data_safety_browser.py` | PASS |
| `phase1_safety_corrections_browser.py` | PASS — 26 reported groups |
| `skip_this_week_browser.py` | PASS — 22 reported groups |
| `favorites_weighted_browser.py` | PASS — weighted rotation, duplicate decisions, mobile UI/isolation |
| `grocery_rotation_checks_browser.py` | PASS |
| `dependent_side_groups_browser.py` | PASS — coordination, queues/credits, history, backup/restore, mobile controls |
| `scheduled_linked_slots_browser.py` | PASS — both apps at 320/360px; selected/full/legacy Back, checks/scales, linked attachments |

Additional focused probes reproduced R1–R3 in both apps and the baseline failures listed above. Inline JavaScript in both apps and `service-worker.js` pass `node --check`. No source fixes or weakening of repository assertions were made. Independent harness selector/module mistakes were corrected outside repository source before drawing conclusions.

## Verification limits and exit criteria

Physical iOS/Android gestures, screen readers, real quota exhaustion/process termination, cross-tab conflicts, and installed-PWA upgrades were not verified. Chromium touch emulation and injected storage failures are useful evidence but do not establish those device guarantees. The service-worker version change was inspected, not deployed. This was a focused review, not a claim that every repository suite passes.

Correct R1/R2 and add transition/grocery/Undo regressions; correct R3 and cover legacy occasional slot identities. Preserve the passing recovery, queue, Favorites, and shared-script/isolation checks. Resolve or explicitly accept the separate Resume/check-state observation, and retain the pre-existing Side issue in the existing-issue record. Then rerun independent verification before advancing.

**CORRECTIONS REQUIRED**
