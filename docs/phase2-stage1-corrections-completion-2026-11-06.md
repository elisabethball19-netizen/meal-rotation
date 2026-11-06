# Phase 2 — Stage 1 Corrections Completion Report

Date: November 6, 2026 (UTC)  
Repository: https://github.com/elisabethball19-netizen/meal-rotation  
Branch: `codex/phase2-meal-rotation`  
Review addressed: [Stage 1 independent verification](phase2-stage1-independent-verification-2026-11-05.md)

## Status and commits

**The requested Stage 1 corrections are implemented and committed for another independent verification. Stage 2 has not begun. No merge or deployment was performed.**

Work continued from branch head `a8633c05172031dc4985878a2e5fda28aa08b8a1`, which adds the independent report. The starting HTML blob hashes matched the reviewed implementation. The independent report and earlier completion report remain preserved.

1. [`4920dff235268fb437214108635cbc81f1d1ef0e`](https://github.com/elisabethball19-netizen/meal-rotation/commit/4920dff235268fb437214108635cbc81f1d1ef0e) — permanent reproductions for temporary Undo, unconfigured-day Change Meal, legacy occasional reordering, and same-cycle grocery Resume.
2. [`9b51edbc5b671ca64a4a270ff07f52d5ea20cdae`](https://github.com/elisabethball19-netizen/meal-rotation/commit/9b51edbc5b671ca64a4a270ff07f52d5ea20cdae) — corrections, expanded regressions, and offline shell v99 preparation.

This report is a documentation-only follow-up. Publishing it does not approve Stage 2, merging, or deployment.

## Reproduced before implementation

The three confirmed defects were reproduced in both HTML apps using synthetic records before application code was edited. The grocery Resume observation was reproduced too:

| Before-fix case | Production and test app |
| --- | --- |
| One-time meal → reusable recipe → Undo loses the original descriptor | Expected failure reproduced |
| Empty slot → reusable recipe → Undo loses the empty descriptor | Expected failure reproduced |
| Unconfigured Sunday's one-time meal → reusable recipe leaves Sunday unscheduled | Expected failure reproduced through the actual UI |
| Legacy occasional meal's own keyboard reorder control does not move it | Expected failure reproduced |
| Legacy occasional meal's own pointer-drag control does not move it | Expected failure reproduced |
| Leave Empty → Resume loses hidden main/linked grocery checks | Expected failure reproduced |

That is **12 expected failing reproductions across both apps**. After implementation, the permanent reproduction mode was rerun against preserved unchanged HTML and again reproduced all 12 failures. Unexpected browser errors are not treated as successful reproductions.

The source-root option makes the comparison reproducible without replacing current application files:

```sh
MEAL_CORRECTION_SOURCE_ROOT=/path/to/unchanged-stage1-checkout \
MEAL_STAGE1_EXPECT_FAILURES=1 \
python tests/phase2_stage1_corrections_browser.py
```

## Corrections

### R1 — Complete, recipe-safe Undo for temporary changes

Change Meal now uses the intact scheduling snapshot captured **before** clearing a temporary slot on ordinary and duplicate-source paths. Undo restores the original one-time name, stable ID, entered grocery lines, checked states and quantities, or the original empty-slot descriptor.

Temporary scheduling Undo is explicitly marked as scheduling-only. Its restoration retains current recipe definitions, ingredient selections and unrelated settings. It restores the affected scheduling fields and shopping sources while keeping later shopping progress on retained occurrences. The real Undo/Redo controls preserve current recipe content rather than replaying old recipe definitions.

When a duplicate decision also moves a recipe from another weekday, both days' removed cooking/quantity contexts are captured. Source checks are restored even when a one-recipe pool produces the same recipe/occurrence identity after the operation. Where an explicit move requires order restoration, current recipe records are reordered by ID; old recipe records are not resurrected.

Tests cover one-time and empty transitions, stable descriptors, quantities/checks, later changes to notes/ingredients/instructions/source links, permanent ingredient selections, later unrelated shopping progress and scaling, and real Undo/Redo.

### R2 — Change Meal on an unconfigured weekday

The temporary meal's Change Meal action now normalizes the synthetic day slot and selects the existing occasional-meal route. The mutation function also defensively normalizes `@day` and weekdays without assigned groups.

The selected reusable recipe and its groceries appear on Sunday without assigning a permanent weekday group or creating a `Sunday::@day` permanent override. Choosing an otherwise unscheduled recipe does not consume its normal queue turn.

Tests cover actual UI selection, Ideas with linked recipes, reload, backup/restore, Undo, duplicate-choice Cancel/Keep both/Replace decisions, and a one-recipe duplicate-source edge case. Existing explicit duplicate-source replacement behavior is retained.

### R3 — Complete legacy occasional entry identity

Rendered rows and reorder handles now receive the complete planner entry, including the legacy `occasional` flag and recipe ID. They no longer reconstruct a partial entry that produces a different display key.

Planner ranking, row metadata, pointer drag, keyboard lookup and saved order therefore use the same identity. Keyboard focus restoration is also scoped to the correct weekday when the same legacy recipe appears on more than one day.

Tests use a legacy occasional meal and another assigned group on the same day, at 320px and 360px, and check pointer/keyboard ordering, reload, backup/restore and weekday-specific focus. Existing swipe and recipe-name long-press handlers were preserved; the original Stage 1 touch/gesture suite passes.

### R4 — Preserve hidden shopping progress within a cycle; reset it on rotation

Each temporary slot can now hold optional `groceryChecks`: booleans keyed by the existing occurrence-specific grocery source identities. Hidden main and linked contributions are preserved when the slot is temporarily suppressed. Their recipe multipliers remain in the existing occurrence-scale storage, with hidden current-cycle contexts recognized as valid across reload.

Resume during the same cycle restores those checks and quantities. The active grocery list continues to exclude hidden contributions. Unrelated checked contributions remain intact, including other meals sharing the same grocery ingredient.

Rotating an applicable temporary slot removes its temporary preservation descriptor. Its hidden underlying occurrences are included in shopping/cooking reset handling, **without** advancing those hidden recipes' queue positions, Favorites turns or cooked dates. Unrotated temporary slots retain their preservation data.

Consequently, newly rotated contributions start unchecked even if the same recipe ID remains scheduled in a one-recipe pool, or a previously checked recipe returns after later rotations. Permanent ingredient selections/exclusions are not changed. Existing quantity aggregation and mixed checked/unchecked contribution splitting remain in use.

## Storage and Phase 1 safeguards

- The new check map is an optional property of an existing temporary-slot descriptor under `weekSchedule`. Existing localStorage keys and format versions remain unchanged; no recipe/status/selection migration was added.
- Existing records and backups without the optional map remain accepted. No large image data or photo storage was introduced.
- The optional map is validated using the existing grocery-source validator. Malformed hidden-check backup records are rejected before replacement.
- The preservation data travels through existing plan snapshots and backups. Tests restore a full storage backup while a slot is hidden, reload, then Resume with the original checks and quantities.
- Existing dependency-aware recipe deletion also prunes cached checks for deleted recipes and linked parents. Recipe records are not restored from the cache.
- Injected write failures retain the durable original plan, persistent warning and recovery export. Retry saves the intended hidden progress after writes recover.
- Recovery journals, replacement verification, pending drafts and failed-save machinery were not redesigned. All three Phase 1 safety/recovery suites pass.
- Production/test shared code remains synchronized. Test-only storage isolation, banner and reset controls remain intact. No interface redesign was made.
- The service-worker shell is prepared as **v99** on this development branch. It has not been deployed or tested as an installed-PWA upgrade.

## Tests and actual results

All testing used synthetic data and disposable Chromium profiles with fixture requests intercepted. No real user recipes or browser storage were accessed.

### New correction coverage

`python tests/phase2_stage1_corrections_browser.py` passes **24 reported case groups across both apps**. Additional focused runs also passed the one-recipe duplicate-source Undo edge case after that case was added to the permanent suite.

Coverage includes:

- One-time-to-recipe and empty-to-recipe Undo, exact stable IDs and grocery lines/checks/quantities.
- Preservation of later recipe content and permanent ingredient selections, unrelated shopping progress/scaling, and Undo/Redo behavior.
- Unconfigured-day selection, linked Ideas, duplicate decisions, reload, backup/restore and Undo, with no permanent `@day` overrides.
- Legacy occasional pointer/keyboard reordering at both mobile widths, saved order and weekday-specific focus.
- Same-cycle Leave Empty → Resume; hidden linked multipliers/checks through reload and backup/restore.
- Two hidden groups with only one rotated; rotation of another group while a main remains hidden; shared ingredient quantities/checks.
- Full rotation, selected-group rotation, a same-ID one-recipe pool and a recipe returning after intervening rotations.
- Failed writes, recovery export, Retry, malformed hidden-check backups and deletion cleanup.

### Requested regression suites

Every command below was run and exited **0** during the correction pass. Existing test assertions were not weakened or changed in this pass.

```sh
python tests/phase2_stage1_browser.py
python tests/phase2_stage1_workflows_browser.py
python tests/phase1_final_recovery_safety_browser.py
python tests/phase1_safety_corrections_browser.py
python tests/phase1_data_safety_browser.py
python tests/skip_this_week_browser.py
python tests/favorites_weighted_browser.py
python tests/grocery_rotation_checks_browser.py
python tests/dependent_side_groups_browser.py
python tests/scheduled_linked_slots_browser.py
python tests/manual_duplicate_meal_browser.py
python tests/shared_week_scheduling_browser.py
python tests/scheduled_date_integrity_browser.py
python tests/meal_groups_bulk_safety_browser.py
python tests/recipesage_refresh_browser.py
```

These are **15 passing regression suites**, in addition to the new correction suite. Notable reported counts are 14 Stage 1 groups, 28 workflow checks, 16 final-recovery groups, 26 safety-correction groups, 60 manual-duplicate checks and 46 scheduled-date checks. The workflow suite also exercises import parsing separately from the known obsolete repair hook.

Inline JavaScript in both apps, service-worker JavaScript, and changed Python syntax pass their syntax checks. Shared-script parity and `git diff --check` pass. Published implementation blob hashes match the tested local files.

The broad sweep covered the scheduling and grocery changes. Final focused checks additionally verified duplicate-source quantities, same-ID source checks, richer unrelated recipe edits and weekday-specific reorder focus.

## Separate existing issues and limitations

**The older Side restoration issue remains unresolved and separate.** `occasional_meals_browser.assignment(browser, filename, 320, 'Sides')` was rechecked in both apps. Both still fail the existing post-rotation/Back/reload assertion at **line 87**, as independently confirmed against Phase 1. This correction pass did not expand scope to fix it, and the full legacy occasional suite is not claimed as passing.

The other known baseline failures remain documented in the [independent review](phase2-stage1-independent-verification-2026-11-05.md): the missing import repair hook, the reviewed-import rollback assertion conflicting with queued saves, and the two editor probes expecting hidden/obsolete controls. Those full failing suites were not counted as passes or presented as fixed here. Relevant import parsing/refresh, real editor-save safety, backup compatibility and recovery tests are included in the passing suites above.

Previously discarded hidden shopping progress cannot be reconstructed from an older record that never saved it. The new preservation applies to available progress captured by the corrected implementation; it does not invent past checks or silently rewrite old recipe selections. Undo remains an in-memory interaction, as before; reload/backup coverage applies to persisted scheduling and shopping state.

Physical iOS/Android gestures, screen readers, real device quota exhaustion/process termination, cross-tab conflict handling and installed-PWA upgrades remain manual verification limits. Injected failures and Chromium gesture tests do not establish those device guarantees.

## Stop point

All four approved correction areas are implemented and tested for review. Stage 2, photos and unrelated work have not begun. **Obtain another independent verification before approving Stage 2. Do not merge or deploy without separate owner approval.**
