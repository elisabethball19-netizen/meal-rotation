# Phase 2 — Stage 4 final corrections

Date: 2026-11-06  
Repository: `elisabethball19-netizen/meal-rotation`  
Branch: `codex/phase2-meal-rotation`  
Starting remote head: `7c515f3074644b16ecc4c10d4151d71f72e0a4df`  
Findings addressed: [Stage 4 corrections independent verification](phase2-stage4-corrections-independent-verification-2026-11-06.md).

Implemented only S4C-IV-1 and S4C-IV-2 and their regression coverage. Stage 5 has not begun. No merge or deployment was performed. Independent verification remains the next step.

## Reproduction evidence before application edits

Archived unchanged current application files and used the existing archived pre-Stage-4 files. Verified their Git blob hashes:

| Source | Production HTML | Test HTML |
| --- | --- | --- |
| Pre-Stage-4, commit `6bbcee63b2a377d3471a4b7266f16526997dfeed` | `f7f33ac6f64bd9f526a39eff70fd61fdcb64ea54` | `8f37b89b16f78809a9e6dd0a334bc9483dfb9daa` |
| Current unchanged baseline at the starting head | `6ea5bb042b677917b345acf02a6bd4f68251429c` | `a808d5b74c930bc14e6b520a744d2d62d88327c4` |

Ran synthetic fixtures against actual HTML and UI handlers before modifying application code:

- **S4C-IV-1:** both current baseline apps at 280px, 320px and 360px. Open Tuesday's picker, open Side for Sides, choose Dependent side for Rice, and confirm. All six cases left the active element at `BODY`; immediate Escape left the parent picker open.
- **S4C-IV-2:** both apps on both sources above. Rice recipe ID 1 shares its identity with an existing destination membership. Keep/move Rice into Destination and press the real Undo button. Exact recipe records returned, but saved scales fell **5→2**, cooking-session records fell **5→2**, and grocery contributions differed. All four cases reproduced the data loss, including main, linked and side occurrences while another tab retained its separate occurrences.

The new regression script's optional `--reproduce` mode supplies these historical runs using `/tmp/stage4-before` for pre-Stage-4 HTML and `/tmp/stage4-final-before` for the unchanged current baseline. Normal regression execution uses repository HTML and does not depend on those archives.

## Exact implementation changes

### S4C-IV-1: focus after nested confirmation

Added an optional return-focus resolver to the existing bulk dialog/value chooser. Side-pair controls supply a resolver for the current Side for group button in their parent holder. After the child closes and background inert states are restored, the dialog focuses the original opener if it still exists, or resolves its replacement if rendering removed it.

This fixes confirmation without adding a delayed Tab or synthetic key event. Immediate Escape reaches the parent picker, and its existing focus containment remains active. Cancel still returns to its unchanged opener. Side-pair assignment callbacks, allocation, queue and Favorites algorithms are unchanged. The optional resolver leaves other callers' behavior intact.

### S4C-IV-2: complete group-operation Undo

- Kept the existing category-removal/move engine and destination identity-merging rules. Wrapped its execution in the existing storage draft bridge and validated backup replacement transaction used by dependency-aware recipe changes.
- Work on cloned mutable group, plan, recipe, grocery and cooking state. Validate the proposed complete storage before committing. A failed commit restores the prior memory state, retains the existing durable rollback/recovery protections, and registers the operation and its complete proposal for recovery export and explicit Retry Save. An Undo entry is added only after a successful commit.
- Capture deep copies of cooking sessions and occurrence scales before removal. Record the exact occurrence keys removed, changed or created by the operation. Undo uses the existing dependency-aware restoration helper to restore those contexts or remove newly created ones. This includes main recipes, linked attachments, sides, completion tokens, automatic ingredient completion and ingredient overrides.
- Preserve changed grocery-selection keys and their prior absence, so Undo also reverses any selection materialized by destination merging without rewriting unrelated selections.
- Preserve the same occurrence/selection metadata when capturing Undo/Redo counterparts. Redo followed by another Undo retains the complete state rather than losing the new preservation information.
- Restore only the operation's affected cooking contexts. Cooking/scaling edits made afterward to an unaffected occurrence remain intact; a dedicated full-state comparison verifies this behavior.
- A successful Retry dismisses the stale group-delete dialog, and the resulting operation has a complete usable Undo entry.

Successful group Undo restores recipe IDs, all record fields and ordering, memberships, group display metadata, plans, Favorites scores, grocery selections, complete grocery contributions/quantities/checks, sessions and scales. There is **no changed-day exclusion** in the Undo preservation assertions.

No saved-data migration, new recipe field, rotation algorithm change or backup schema change was introduced. New Undo metadata is held in the existing in-memory history. Existing backups remain compatible. The previous report's group merge/scaling limitation is superseded by this correction; the four separate baseline issues below remain outside scope.

Production and test functionality remain synchronized. Test-only storage isolation, banner and reset controls are unchanged. Service-worker asset cache version is v106; no deployed upgrade was performed.

## Permanent regressions and actual results

### Focused and Stage 4 suites

| Execution | Actual result |
| --- | --- |
| `python tests/phase2_stage4_final_browser.py` | **30 PASS groups**, exit 0. Full-state comparisons include the changed day and all cooking/scaling metadata. |
| `python tests/phase2_stage4_browser.py` | **38 PASS groups**, exit 0, with the changed-day Undo quantity exception removed. |
| `python tests/phase2_stage4_corrections_browser.py` | **18 PASS groups**, exit 0. |
| Full `weekday_setup_browser.py` | **Passed**, exit 0; six PASS groups plus historical-height comparisons. A temporary runner supplied the exact historical HTML for the missing local Git object `309866412d9b7778128c5dc8ea58f4a54b0e4f59` without changing assertions. |

### Existing regression suites

**All 29 existing suites below passed**, exit 0. The 28-suite parallel batch completed without failures. `phase1_safety_corrections` was run separately after the batch to avoid the previously observed native file-chooser focus timeout; it passed all 26 printed scenario groups on this execution.

- `python tests/phase2_stage2_corrections_browser.py`
- `python tests/phase2_stage3_browser.py`
- `python tests/phase2_stage3_corrections_browser.py`
- `python tests/phase2_stage2_browser.py`
- `python tests/phase2_stage1_browser.py`
- `python tests/phase2_stage1_corrections_browser.py`
- `python tests/phase2_stage1_workflows_browser.py`
- `python tests/phase1_final_recovery_safety_browser.py`
- `python tests/grocery_rotation_checks_browser.py`
- `python tests/phase1_data_safety_browser.py`
- `python tests/favorites_weighted_browser.py`
- `python tests/scheduled_linked_slots_browser.py`
- `python tests/dependent_side_groups_browser.py`
- `python tests/scheduled_date_integrity_browser.py`
- `python tests/manual_duplicate_meal_browser.py`
- `python tests/recipesage_refresh_browser.py`
- `python tests/meal_groups_bulk_safety_browser.py`
- `python tests/skip_this_week_browser.py`
- `python tests/shared_week_scheduling_browser.py`
- `python tests/add_recipe_ideas_browser.py`
- `python tests/recipe_tabs_browser.py`
- `python tests/recipe_touch_browser.py`
- `python tests/shared_recipe_management_browser.py`
- `python tests/needs_tweaking_browser.py`
- `python tests/recipe_tab_reorder_browser.py`
- `python tests/rotation_dialog_layout_browser.py`
- `python tests/outgoing_cooked_dates_browser.py`
- `python tests/group_order_browser.py`
- `python tests/phase1_safety_corrections_browser.py`

Together with the four focused/Stage 4/weekday suites above, **33 complete suites passed**. The eight separately reproduced historical failure paths below are not included in that count. The full weekday historical-height comparison used verified HTML blobs `2c9795601af060916028eab46a275cd660a14554` (production) and `37e8a4a58076c6b171733075b55f556f507f1b56` (test).

No correctness assertion was relaxed to obtain these results.

### Static and storage checks

All inline scripts in both apps and the service worker passed `node --check`. Shared application JavaScript matches after the expected storage-provider substitution; shared CSS matches with the preserved test banner. Test-only shell/storage adapter/reset controls and banner were compared with archived source and remain unchanged. Python compilation and `git diff --check` passed. Test-app production-storage sentinels survived the exercised workflows.

Final tested application blob hashes:

| File | Git blob SHA |
| --- | --- |
| `index.html` | `244782bf8a2cbddaa2e355c083fc9e3b4a5dba8b` |
| `meal-rotation-test.html` | `ace9ddbf83e69c084837ab0fa4e400cd37f82d56` |
| `service-worker.js` | `a0327e692a7e3ab7df32c63844ed4166d539a3e4` |

The new focused fixtures compare complete domain records, rather than names or intersected grocery keys. They include:

- Main and linked/side cooking contexts across multiple weekdays and meal tabs.
- Nonempty Favorites weighting ledgers and unchanged recipe queue ordering after Undo.
- Explicit ingredient exclusions and an explicitly empty selection.
- Ingredient and instruction completion, automatic completion, true/false overrides, occurrence scales, mixed checked/unchecked groceries and actual scaled contribution lines.
- A destination with an existing shared membership and an empty destination without a duplicate.
- Exact Undo, Redo, second Undo, reload, and full backup/restore comparisons; persistence of the moved state is checked separately as well.
- Later unrelated cooking/scaling edits retained through Undo and persistence.
- Failed group saves at session, scale and primary recipe writes: unchanged memory/durable records, complete recovery proposal/export, Retry, and exact subsequent Undo/reload/backup.
- Failed Undo writes for sessions, scales and explicit group display ordering: complete desired state retained in memory and recovery export, successful Retry, reload and backup restoration. Pending failed Undo is explicitly warned and is not claimed durably saved until Retry succeeds.
- Actual child confirmation in both directions, immediate parent focus/Escape, Tab/Shift+Tab containment, child cancellation, pointer and touch confirmation, at 280/320/360px in both apps.

The older Stage 4 group test now unconditionally requires exact grocery quantity equality after Undo, including the changed day. Its previous baseline exception was removed. It also checks the presence of every unaffected contribution, so accidentally missing keys cannot pass through an intersection-only comparison. No existing correctness assertion was weakened.

## Separate known baseline issues

Targeted original failure paths were rerun in both corrected apps, retaining their original assertions. All eight expected failures reproduced. These are not counted as complete passing suites and were not fixed or redesigned here:

| Existing issue | Boundary |
| --- | --- |
| Legacy Side restoration | `occasional_meals_browser.assignment(..., 320, 'Sides')`, line 87 after Rotation Back/reload. Separate from the Stage 2 paired-side queue fix. |
| Duplicate allocation | `rotation_no_duplicates_browser.run(..., 320, 'weekend')`, line 83; same Saturday ID 4 / Sunday ID 2 / Lunch Tuesday ID 3 rows. |
| Legacy linked occurrence | `cycle_linked_occurrences_browser.run(..., 320)`, line 73, `legacy-pin` Thursday ID 1 changes to ID 2. |
| Heading spacing | `page_heading_spacing_browser.run(..., 280, 'normal', False)`, line 37; 14px versus asserted 8px content gap. |

## Limitations

Validation uses installed Chromium/Playwright with synthetic fixtures, disposable contexts and intercepted external requests. Native iOS/Safari, real assistive-technology announcements and an actual deployed service-worker upgrade were not verified. Existing in-memory Undo history does not become persistent across a browser reload; the tests verify Undo followed by durable reload/backup restoration, consistent with the existing application model.

No new limitation in the two corrected paths was identified in the completed checks. This is an implementation/testing report, not independent approval to begin Stage 5.

## Commit references

- Application corrections: [`71f8c23aa9eadde90e09dc0524dbe88bc8db5552`](https://github.com/elisabethball19-netizen/meal-rotation/commit/71f8c23aa9eadde90e09dc0524dbe88bc8db5552).
- Permanent complete-state and nested-confirmation regressions: [`108898e074a8216166761a11e2b47d6bc8c05b7c`](https://github.com/elisabethball19-netizen/meal-rotation/commit/108898e074a8216166761a11e2b47d6bc8c05b7c).
- Explicit ordering and failed Undo order-save coverage: [`d495340678b9ee65278860078ea2155b18308523`](https://github.com/elisabethball19-netizen/meal-rotation/commit/d495340678b9ee65278860078ea2155b18308523).
- This report is published in the subsequent documentation commit on the same branch.

Shareable report: https://github.com/elisabethball19-netizen/meal-rotation/blob/codex/phase2-meal-rotation/docs/phase2-stage4-final-corrections-completion-2026-11-06.md
