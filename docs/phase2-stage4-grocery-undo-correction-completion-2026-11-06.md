# Phase 2 — Stage 4 grocery Undo correction

Date: 2026-11-06  
Repository: `elisabethball19-netizen/meal-rotation`  
Branch: `codex/phase2-meal-rotation`  
Starting remote head: `a47cb32939c2a9274ebaad64f6374d13994b6467`  
Finding addressed: **S4F-IV-1** in [the independent review](phase2-stage4-final-independent-verification-2026-11-06.md).

Implemented only the authorized group-operation grocery Undo correction and its tests. No Stage 5 work, merge or deployment occurred. Independent verification is the next step.

## Before/after evidence

Before editing application code, archived the unchanged HTML and verified these baseline blobs:

- Production: `244782bf8a2cbddaa2e355c083fc9e3b4a5dba8b`.
- Test: `ace9ddbf83e69c084837ab0fa4e400cd37f82d56`.

Used real group-delete/Keep recipes controls and actual Grocery List checkbox interactions. In both apps, with both an empty destination and an existing shared destination membership, checking the unrelated Lunch/Thursday **7 apples** item after the group move changed it to checked. Undo changed it back to unchecked; reload retained the lost progress. **All four unchanged-source cases reproduced the defect.** Grocery checkbox actions were verified not to add Undo entries.

On corrected source, all **20 focused regression cases pass**. Later unrelated checked and unchecked states survive Undo, Redo, second Undo, reload and backup restoration; affected occurrences return to their intended previous states. The same shared-rice checkbox changes affected and unaffected contributions, and Undo separates their states correctly rather than clearing an unrelated contribution.

The permanent test supports historical reproduction with `--reproduce --source-root /tmp/stage4-grocery-before`, where the archive contains the unchanged HTML above. Ordinary test execution uses the repository HTML without that archive dependency.

## Exact implementation changes

- At a successful group operation, compare grocery contributions before and after the operation and record the affected **occurrence identities**, source keys, effective prior checks and relevant legacy aliases. Changed inactive ledger entries are included; unchanged active legacy materialization does not claim an unrelated occurrence.
- Group Undo starts with a copy of the **current live grocery ledger**. It restores/removes entries only within that operation's affected scope, retaining later checks and unchecks on unaffected occurrences. This is not an old whole-ledger replacement or a day-wide reset.
- Preserve current legacy check flags used by unaffected/shared contributions. Restore exclusive affected aliases as appropriate, and materialize an occurrence-specific value when needed so a shared legacy flag cannot incorrectly check a restored occurrence.
- Capture the same scoped metadata in Undo/Redo counterparts. Each transition reads current unrelated shopping progress, so later checkbox edits between Undo, Redo and second Undo remain intact.
- Retain the preceding corrections for recipe identities, group memberships/order, complete cooking-session metadata, occurrence scales, selected ingredients, and later unrelated cooking/scaling edits. Existing group-save transaction/rollback and generic warned-pending-write recovery behavior are reused.

The generic Undo behavior for other operation types and rotation allocation are unchanged. No new localStorage key, saved-data migration or backup schema was introduced. The additional group-history metadata remains in the existing in-memory history. Shared code is synchronized between both HTML apps, and the service-worker asset cache version is v107. Test-only storage isolation, banner and reset controls are unchanged.

## Permanent regression coverage

Added `tests/phase2_stage4_grocery_undo_browser.py`. All shopping changes use actual rendered checkbox handlers; hooks only seed synthetic data, read state and perform the separately tested unrelated cooking/scaling edit.

Coverage in both apps and both destination variants includes:

- An initially checked unrelated pears item; unchecked apples changed to checked; checked plums changed to unchecked and later checked again.
- A shared rice checkbox spanning affected and unaffected occurrences, plus an affected main meal's garlic checkbox. Restored affected checks and retained unrelated checks are asserted separately.
- Actual rendered checkbox states, complete visible contribution identity sets and aggregate quantities, and exact full-domain comparisons of every grocery contribution/key, scaled line, check ledger, legacy flags and exclusions.
- Exact recipes/IDs, memberships/order, group display metadata, plans/Favorites ledgers, selected ingredients, sessions, ingredient/instruction completion, overrides and scales. No changed-day quantity or cooking-state exception is used.
- Later unrelated cooking/scaling changes retained along with the shopping edits.
- Undo → another unrelated checkbox edit → Redo → another unrelated checkbox edit → second Undo. Complete resulting state is compared after reload and backup/restore.
- Legacy-only fallback checks, including an explicit unchecked affected occurrence when an unrelated shared legacy ingredient flag is checked.
- Failed group-save rollback and Retry Save, and failed Undo writes to both occurrence-check and legacy-check storage. Actual recovery exports contain the complete intended grocery data; Retry, repeated history transitions, reload and backup remain correct.

No existing regression file or correctness assertion was weakened or removed.

## Actual test results

**34 complete suites passed on their final executions**, comprising the new focused suite, the three prior Stage 4 suites, the full weekday suite and 29 existing regression suites.

| Suite | Actual result |
| --- | --- |
| `phase2_stage4_grocery_undo_browser.py` | 20 PASS groups; exit 0 |
| `phase2_stage4_final_browser.py` | 30 PASS groups; exit 0 |
| `phase2_stage4_browser.py` | 38 PASS groups; exit 0 |
| `phase2_stage4_corrections_browser.py` | 18 PASS groups; exit 0 |
| Full `weekday_setup_browser.py` | Passed, including six PASS groups and original historical-height comparisons |

The following **29 existing suites passed**, exit 0:

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
- `python tests/manual_duplicate_meal_browser.py`
- `python tests/scheduled_date_integrity_browser.py`
- `python tests/recipesage_refresh_browser.py`
- `python tests/meal_groups_bulk_safety_browser.py`
- `python tests/skip_this_week_browser.py`
- `python tests/shared_week_scheduling_browser.py`
- `python tests/add_recipe_ideas_browser.py`
- `python tests/recipe_tabs_browser.py`
- `python tests/recipe_touch_browser.py`
- `python tests/shared_recipe_management_browser.py`
- `python tests/needs_tweaking_browser.py`
- `python tests/rotation_dialog_layout_browser.py`
- `python tests/recipe_tab_reorder_browser.py`
- `python tests/outgoing_cooked_dates_browser.py`
- `python tests/group_order_browser.py`
- `python tests/phase1_safety_corrections_browser.py`

The 28-suite parallel batch completed without failures. `phase1_safety_corrections` ran separately afterward to avoid previously observed native file-chooser interference; it passed all 26 printed scenario groups on this execution. The weekday historical comparison used verified original HTML from commit `309866412d9b7778128c5dc8ea58f4a54b0e4f59` through the temporary runner, without changing its assertions.

Static validation passed: all inline scripts and the service worker pass `node --check`; Python compilation passes; normalized shared JavaScript and CSS match; the test-only shell/storage adapter/reset and banner match the archive; production-storage sentinels survive the test-app workflows; `git diff --check` passes.

Final tested application blobs:

| File | Git blob SHA |
| --- | --- |
| `index.html` | `3afa5e4364c7f4cc5713d9db278a68f3fb3dd7ba` |
| `meal-rotation-test.html` | `9e0e4395c521736e71e6cca6e1caf4efcbf7f5ac` |
| `service-worker.js` | `afc033f8cf7463caa0086113b2f4b91ea493b0ed` |

## Four older failures remain separate

The original targeted paths still reproduce in both apps. These eight expected failures are not counted among complete passing suites, and do not imply completion of the rest of those failing suites:

| Existing issue | Boundary |
| --- | --- |
| Legacy Side restoration | `occasional_meals_browser.py:87`, Side assignment after Rotation Back/reload |
| Duplicate allocation | `rotation_no_duplicates_browser.py:83`, Weekend case; same Saturday ID 4 / Sunday ID 2 / Lunch Tuesday ID 3 rows |
| Legacy linked occurrence | `cycle_linked_occurrences_browser.py:73`, `legacy-pin` Thursday occurrence changes ID 1 → ID 2 |
| Heading spacing | `page_heading_spacing_browser.py:37`, 14px versus asserted 8px content gap at 280px |

None was changed by this focused correction.

## Limitations

Tests use Chromium/Playwright, synthetic fixtures, disposable contexts and intercepted requests. Native iOS/Safari, real assistive-technology announcements and an actual deployed service-worker upgrade were not verified. Undo history remains in memory; reload/backup checks verify the saved result after Undo, not persistence of the history stack.

A failed generic Undo retains its intended state with the existing unsaved warning and recoverable pending writes. It is not claimed fully durable until Retry succeeds. The new focused tests explicitly verify that contract for grocery checks. No general Undo/storage redesign was made.

No unresolved S4F-IV-1 failure was observed in the completed checks. This report does not authorize Stage 5.

## Commit references

- Scoped correction: [`67a7750f5ff4cafdda7ce7986e512e32e0546e2b`](https://github.com/elisabethball19-netizen/meal-rotation/commit/67a7750f5ff4cafdda7ce7986e512e32e0546e2b).
- Real-checkbox regressions: [`0607c0238efac7c21858158909b5760ad4d51149`](https://github.com/elisabethball19-netizen/meal-rotation/commit/0607c0238efac7c21858158909b5760ad4d51149).
- This report is published in the subsequent documentation commit on the same development branch.

Shareable report: https://github.com/elisabethball19-netizen/meal-rotation/blob/codex/phase2-meal-rotation/docs/phase2-stage4-grocery-undo-correction-completion-2026-11-06.md
