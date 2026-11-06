# Phase 2 — Stage 2 Independent Verification

Date: November 6, 2026 (UTC)

**Decision: CORRECTIONS REQUIRED**

**Confirmed blocking Stage 2 defect:** Rotation Back discards the new paired-side queue-protection flag. Rotating the restored manual schedule again permanently changes the side queue and Favorites credits. This reproduces in both HTML apps with full and selected Rotation Back. Ordinary Stage 2 workflows and the supplied Stage 2 suite pass, but do not exercise this sequence with a meaningful weighted side pool.

A second confirmed scheduling gap involves an existing allocator restriction: the new Schedule Meal action silently accepts an already-scheduled same-day recipe in another group, then fails to populate the requested slot. This is distinguished below from both the new history defect and the previously documented legacy Side restoration bug.

## Scope and provenance

- Repository/branch: `elisabethball19-netizen/meal-rotation`, `codex/phase2-meal-rotation`.
- Reviewed head: [`2bbcd5c898756354f2b7fdbec7e780b07f619790`](https://github.com/elisabethball19-netizen/meal-rotation/commit/2bbcd5c898756354f2b7fdbec7e780b07f619790). Implementation commits: `b96fdad460e4b40e0eb5d923826825221b115a1b` and `e811150204edb1e761d37b3b7c726692665cf27c`.
- Started with the [Stage 2 completion report](phase2-stage2-completion-2026-11-06.md), then compared implementation against the independently verified Stage 1 correction source (`2b809c72ccf57b4f3fbc9d806441a4ab91bd1392`). Read application code and test assertions independently.
- Source was retrieved through GitHub because the workspace Git proxy was unavailable. Materialized application Git blob hashes match published files: production `f65c65649a05a157bc815303fcf7782def38d96a`, test `d43cb6c620a8bdbeb34ce3965b6678641b937642`, service worker `6b94ef53913885e4eb15b60da266dfd4dfd7a491`.
- All browser data was synthetic, in disposable Chromium contexts with intercepted fixture requests. Additional probe scripts stayed outside repository source. No user storage was accessed, application/test fixes made, merge/deployment performed, or Stage 3 work begun. Only this report is published.

## Confirmed findings

### S2-1 — High, blocking: Rotation Back loses paired-side queue and Favorites protection

**Reproduction in both apps:**

1. Configure Tuesday with a main group and paired automatic side group. Provide multiple eligible side recipes, including a Favorite. In the synthetic fixture, side IDs are `10,11,12,13,14`; recipe 13 is a Favorite, and recipes 13/14 can match the manually scheduled main's side preference.
2. Use Schedule Meal to put recipe 3 in Tuesday's main slot. Its automatic side becomes recipe 13. The new main choice correctly contains `preserveSideQueue:true`.
3. Rotate the main out. The side queue and Favorites scores remain unchanged: this is the passing control.
4. Restore the schedule with Rotation Back, reload, and rotate the main out again. Repeat separately using selected Rotation Back for the main.

**Expected:** the restored scheduling choice retains the same protection; expiration of that manual schedule does not consume a normal side queue/Favorites turn. **Actual:** both full and selected Back omit the protection. The dependent side is reclassified as automatic. The next rotation moves side 13 to the end and charges a Favorites turn.

Observed side queue:

```text
Before: [10, 11, 12, 13, 14]
After Back + another rotation: [10, 11, 12, 14, 13]
```

The previously absent Favorites ledger gains a weighted pool with scores `{10:1, 11:1, 12:1, 13:-4, 14:1}`. This is a permanent scheduling/weighting change, not a presentation-only difference. Reload does not prevent it.

**Cause:** [Rotation Back reconstructs `cycleSlotChoices`](https://github.com/elisabethball19-netizen/meal-rotation/blob/2bbcd5c898756354f2b7fdbec7e780b07f619790/index.html#L6131) with substitution, ID, parent, and retention fields but drops the new `preserveSideQueue` field. Stage 2's [dependent-side state/queue guards](https://github.com/elisabethball19-netizen/meal-rotation/blob/2bbcd5c898756354f2b7fdbec7e780b07f619790/index.html#L3397) and [rotation turn guard](https://github.com/elisabethball19-netizen/meal-rotation/blob/2bbcd5c898756354f2b7fdbec7e780b07f619790/index.html#L5753) therefore no longer recognize the restored choice as protected.

**Classification:** confirmed Stage 2 protection/history defect. The field and its new semantics were introduced in Stage 2. It is unrelated to the older legacy occasional Side restoration issue.

**Correction criteria:** preserve applicable scheduling metadata during full and selected history restoration, and keep dependent-side state consistent with that restored metadata. Add a Schedule → Rotate → Back → reload → Rotate regression with at least two eligible sides and an actual Favorite; assert both queue order and score ledger. Cover creation/scheduling paths that use the same flag. Do not repair this by restoring old recipe definitions.

### S2-2 — Medium: Schedule Meal accepts a same-day slot choice the allocator cannot represent

**Real UI reproduction in both apps:** Tuesday has assigned Rice and Sides groups. Recipe 1 is already the Rice meal. Open its Meal Groups actions → Schedule Meal → Tuesday → Sides → Schedule meal.

The dialog closes successfully with no error. Tuesday retains recipe 1 under Rice, but has **no Sides row**; the requested Sides occurrence was not scheduled. The failed target persists after reload. A related probe scheduling an already-displayed side into the main slot removes its other same-day displayed occurrence rather than adding an independent occurrence.

**Cause:** the [new scheduling action](https://github.com/elisabethball19-netizen/meal-rotation/blob/2bbcd5c898756354f2b7fdbec7e780b07f619790/index.html#L3689) writes a manual override without guarding the existing planner's per-day recipe deduplication. The planner emits a recipe ID once per day, so two slot overrides do not produce two independent displayed occurrences.

**Classification:** confirmed new-workflow validation/acceptance gap around an **existing allocator limitation**. Calling the older Change Meal mutation on the preserved Stage 1 HTML reproduces the same deduplication in both apps. This review does not claim Stage 2 introduced that allocator behavior. The new action nevertheless reports success for a target it cannot schedule.

**Correction criteria:** either support the requested independent occurrence consistently, or reject/explain this unsupported same-day choice without replacing the target's existing schedule. Add an actual multiple-assigned-group UI case where the chosen recipe already appears in another group that day. Fixing the entire historical allocator is not required to provide a safe guard in this new entry point.

## Verification results by requested feature

### Schedule Meal from Meal Groups

Ordinary scheduling passes. Independently scheduled recipe 3 to **all seven weekdays in both existing meal tabs**, verifying actual scheduled rows, unchanged recipe definitions/Ideas/rotation state, unchanged weekday assignments, and reload. The repository suite also exercises real UI selection into another tab, unconfigured weekdays, linked groceries, unchanged ingredient selections, other occurrences, Undo, backup/restore, paired automatic sides, and first rotation/history restoration.

The originating active tab remains unchanged. Unconfigured days do not acquire permanent group assignments. For ordinary distinct recipes, selecting a target among assigned groups produces the requested slot. Scheduling-only Undo restores prior temporary/empty state without discarding live recipe definitions.

**Exceptions:** S2-1 fails the queue/Favorites invariant after history restoration and another rotation. S2-2 fails a same-day duplicate choice in the multiple-group UI. These cases prevent an unconditional pass for this feature.

### Create New Recipe from Change Meal

**Pass for tested scenarios.** Actual Change Meal entry, Save, and Cancel pass in the new suite. Independent Escape and backdrop-dismissal probes compare the entire captured application storage and confirm no change. New records preserve the selected permanent group, explicit rotation status, ingredient lines/quantities, instructions, source URL, and multiline notes. Additional field-fidelity/reload probes used Unicode names, range quantities, multiple instructions, a source URL with query parameters, and multiline notes.

Save schedules the record in the intended assigned or unconfigured slot. Scheduling Undo preserves the newly created reusable recipe while restoring prior one-time/empty descriptors and grocery state. Existing recipe records/selections remain intact in the covered scenarios.

Failure checks cover rollback of library and schedule, original durable storage preservation, recovery export containing the latest edited draft, Retry Save, reload after retry, and cancellation after failure. Independent injections on **plan storage and ingredient-selection storage**, in addition to the suite's primary recipe-record failure, also pass rollback and Retry with latest edits to name, ingredients, instructions, and notes.

The unchecked defaults in this dialog are **not treated as defects**: the requested global default-checkbox changes belong to Stage 3. Checkbox states were set explicitly in these tests. S2-1 also requires coverage for any newly created recipe that uses the same scheduling/history protection, but no separate creation/atomic-save defect was demonstrated.

### Add Meal Tabs

**Pass for tested scenarios.** The suite covers default/custom additions, rename, reorder, delete, hidden-tab Settings access, reload, backup/restore, and namespace sentinels. Independent probes additionally reject blank/whitespace names and case/whitespace variants of an existing name; exercise custom-tab scheduling and groceries; and compare persisted state.

An independent probe deleted Breakfast, Lunch, and Dinner while retaining a custom tab. All three stayed absent through reload and backup/restore, then were recreated only by explicit Add actions. Their restored plans were empty; the recipe library and synthetic production sentinel were preserved in both apps.

The dialog does not change initial defaults automatically. Added tabs have no weekday assignments. Keyboard progression through recipe textareas is covered, and empty/duplicate tab validation leaves the dialog open rather than creating an invalid tab. Mobile suite cases run at 320px and 360px with control sizing/overflow assertions.

## Regression and data-safety record

The following were independently rerun on the reviewed implementation:

| Suite | Result |
| --- | --- |
| `phase2_stage2_browser.py` | PASS — 18 reported scenario groups, both HTML apps |
| `phase2_stage1_corrections_browser.py` | PASS — temporary Undo, grocery preservation/reset, legacy ordering, failure recovery |
| `phase2_stage1_browser.py` | PASS — temporary scheduling, groceries, pointer/touch/keyboard ordering |
| `phase2_stage1_workflows_browser.py` | PASS — duplicate choices, Undo/history, imports and current workflows |
| `phase1_final_recovery_safety_browser.py` | PASS |
| `phase1_safety_corrections_browser.py` | PASS |
| `phase1_data_safety_browser.py` | PASS |
| `grocery_rotation_checks_browser.py` | PASS |
| `favorites_weighted_browser.py` | PASS for its covered ordinary weighting cases; does not cover S2-1 |
| `scheduled_linked_slots_browser.py` | PASS |
| `dependent_side_groups_browser.py` | PASS for its covered cases; does not cover S2-1 |
| `shared_week_scheduling_browser.py` | PASS |

The broad passing suites do not negate the independent reproductions above. Stage 1 temporary meals, empty slots, grocery-check holds, selected/full resets, and drag ordering pass their suites. Phase 1 journal/replacement, recovery export, pending edits, strict rollback, and retry protections pass. S2-1 is a history-metadata/queue defect rather than evidence that the durable recovery journal is broken.

Normalized shared application-script equality passes. The test-only shell outside that block is byte-for-byte unchanged from the verified Stage 1 version. Test prefix/banner/reset and production sentinels remain separate. All inline scripts and the service worker pass `node --check`. Shell v100 was inspected, not deployed.

## Test quality and missing boundaries

The new suite has meaningful assertions for definitions, assignments, selections, actual scheduled rows/grocery sources, rollback bytes, draft retry, temporary restoration, and persistence. It exercises real controls for critical entry points rather than checking only that functions return success. Some fixture setup and precise mutation operations use direct hooks. Existing regression assertions were not changed in the Stage 2 implementation files inspected here.

The most consequential omissions are:

- **History followed by another rotation with a weighted multi-side pool.** The supplied paired-side test has one matching side, no Favorite in that pool, and stops after Back. A queue move can therefore be invisible and the missing flag remains undetected.
- **Same recipe in another group on the same day.** The ordinary scheduling UI cases use another tab's single assigned group or an unconfigured day. They do not assert the duplicate same-day target remains representable.
- **Complete field assertions and non-primary write failures.** The initial creation test does not assert every source/instruction field, and its storage-failure injection targets the final recipe record. Independent fidelity and plan/selection-write probes passed, closing those review gaps without changing repository tests.
- **All deleted defaults together.** The suite restores Dinner after deletion and adds Breakfast/Lunch, but does not itself delete all three default names and verify they stay absent. The additional independent tab probe passed, as recorded above.

## Existing issues and verification limits

The **legacy Side assignment restoration bug remains separate**: independently reran `occasional_meals_browser.assignment(browser, filename, 320, 'Sides')` in both Stage 2 HTML apps. Both fail the existing post-full-rotation/Back/reload assertion at line 87. Earlier independent reviews reproduced the same assertion against Phase 1 and verified Stage 1 source. S2-1 uses ordinary paired automatic sides and a lost Stage 2 flag; it is a distinct defect. S2-2's allocator restriction is also separately baseline-confirmed.

Previously documented obsolete import-repair/editor probes and the reviewed-import rollback assertion are not claimed fixed or counted as passing full suites. This is a focused review, not a claim that the entire historical repository test collection is green.

Unverified: physical iOS/Android gestures, screen readers, real quota exhaustion/process termination, cross-tab conflicts, and installed-PWA upgrades. Chromium mobile emulation, keyboard checks, and injected write failures do not establish those device guarantees. No Stage 3 defaults or later-stage features were evaluated as Stage 2 defects.

## Exit criteria

Correct S2-1 and prove full/selected Back retains queue/Favorites protection through a subsequent rotation and reload. Safely handle S2-2's unsupported same-day target rather than silently accepting it. Retain passing atomic creation, draft recovery, tab, Stage 1, and Phase 1 checks. Keep the existing legacy Side issue tracked separately. Obtain another independent verification and owner authorization before Stage 3.

**CORRECTIONS REQUIRED**
