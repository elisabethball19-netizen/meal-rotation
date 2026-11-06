# Phase 2 — Stage 2 corrections completion report

Date: 2026-11-06 (UTC)  
Repository: [elisabethball19-netizen/meal-rotation](https://github.com/elisabethball19-netizen/meal-rotation)  
Branch: `codex/phase2-meal-rotation`  
Status: S2-1 and S2-2 corrected; ready for another independent verification. No Stage 3 work, merge, or deployment performed.

## Starting point and commits

Corrections address [the independent Stage 2 verification](phase2-stage2-independent-verification-2026-11-06.md). Starting remote head: `fc7c8da3238567502c1f142a73a245814dbb61c2`. The independently reviewed source was unchanged at that head; only its verification report had been added after the Stage 2 completion.

Published commits:

- [`8bcd112c96be4fcc3feea23bbdf6ea4e384b8411`](https://github.com/elisabethball19-netizen/meal-rotation/commit/8bcd112c96be4fcc3feea23bbdf6ea4e384b8411) — permanent regressions for both defects and normal automatic rotation controls.
- [`e647fd35f4d922befba6cebf71c3399e74835543`](https://github.com/elisabethball19-netizen/meal-rotation/commit/e647fd35f4d922befba6cebf71c3399e74835543) — targeted history metadata restoration and duplicate scheduling guard in both apps; offline shell source version `v101`.

This report is published in a subsequent documentation commit. The preceding test commit deliberately exposes the defects in the original application source; the fix commit follows it.

## Reproduction before application changes

Before application edits, the history defect and main-to-side duplicate were reproduced in both apps using disposable synthetic data. Additional displayed-side and final expected-failure probes used a preserved copy of those unchanged Stage 2 HTML files.

**S2-1:** Five eligible side records had queue `[10,11,12,13,14]`; side 13 was a Favorite. The manually scheduled main had two compatible sides, 13 and 14. Its first expiration left the side queue and credit ledger intact. After either full or selected Rotation Back, reload, and another expiration, the queue became `[10,11,12,14,13]`. An originally absent weighted ledger gained scores `{10:1,11:1,12:1,13:-4,14:1}`. The restored main choice had lost `preserveSideQueue`.

**S2-2:** Real Meal Groups → Schedule Meal controls were used with Tuesday assigned Rice and Sides. Scheduling the displayed main into Sides, or the actually displayed linked side into Rice, closed the dialog without representing the requested independent occurrence. The side test derives its recipe ID from the displayed schedule rather than assuming which side the allocator selected.

The baseline run recorded eight expected reproductions: full/selected history and main/side duplicate cases in each HTML app. The regression file supports running against an unchanged checkout:

```sh
MEAL_STAGE2_EXPECT_FAILURES=1 MEAL_STAGE2_SOURCE_ROOT=/path/to/unchanged-checkout python tests/phase2_stage2_corrections_browser.py
```

The unchanged checkout must contain the HTML source from `fc7c8da3238567502c1f142a73a245814dbb61c2`. The test runner and fixtures run from the corrected checkout. Expected-failure mode checks the specific queue/credit corruption or silent-dialog-close assertion; ordinary mode requires corrected behavior.

## Corrections

### S2-1 — Restore complete valid scheduling choice metadata

Full and selected Rotation Back share the same restoration path. That path now copies the saved slot choice metadata when its recipe ID matches the restored occurrence, then applies the existing current-recipe/parent validation and retention rules. This retains `preserveSideQueue` instead of rebuilding only a subset of choice fields.

Existing dependent-side coordination consequently recognizes the restored manual parent and records its side as protected. Reload and backup/restore retain the same choice. Expiring it again leaves both side order and Favorites scores unchanged. Recipe records are not copied back from history; current recipe edits remain intact.

The regression suite covers existing-recipe scheduling and Create New Recipe as both an Idea and In Rotation, full and selected Back, selected-main and full active-plan rotations, backup/restore with pending history and after Back, reload, complete saved choice metadata, dependent-side state, and a subsequent rotation. Every protected case has multiple eligible sides and a real Favorite. A separate control confirms normal automatic side changes still move their source queue and charge weighted turns.

### S2-2 — Reject unsupported same-day duplicates before mutation

The shared Schedule Meal action now checks the target tab's actual displayed weekday entries before taking an Undo snapshot or writing any changes. If the selected recipe already occupies another group that day, it reports why a second occurrence cannot be represented and leaves the scheduling dialog open.

The message identifies the conflicting group and weekday, explains the once-per-weekday/per-tab limitation, and offers another group/day or Cancel to select another recipe. The existing target and source meals, other occurrences, permanent assignments, recipe selections, queues, Favorites scores, and grocery progress remain unchanged. Actual browser tests compare the complete captured storage and displayed/grocery state after rejection.

Scheduling the same recipe on another weekday or in another meal tab remains supported and is tested through real UI controls, including reload. All Schedule Meal UI calls use this guarded action. Create New Recipe allocates a distinct new record and retains its existing guarded save path. The historical allocator and older Change Meal duplicate workflow were not redesigned.

## Test results

All tests used synthetic, isolated Chromium contexts and intercepted fixture network requests. No user recipes or live application storage were accessed. The correction suite and all 18 relevant existing suites below exited **0**. Each command is `python tests/<filename>`.

| Suite | Actual result |
| --- | --- |
| `phase2_stage2_corrections_browser.py` | PASS, exit 0 — 22 scenario groups |
| `phase2_stage2_browser.py` | PASS, exit 0 — 18 printed PASS groups |
| `phase2_stage1_browser.py` | PASS, exit 0 — 14 printed PASS groups |
| `phase2_stage1_corrections_browser.py` | PASS, exit 0 — 24 printed PASS groups |
| `phase2_stage1_workflows_browser.py` | PASS, exit 0 — 28 printed PASS groups |
| `phase1_final_recovery_safety_browser.py` | PASS, exit 0 — 16 printed PASS groups |
| `phase1_safety_corrections_browser.py` | PASS, exit 0 — 26 printed PASS groups |
| `phase1_data_safety_browser.py` | PASS, exit 0 — 17 printed PASS groups |
| `grocery_rotation_checks_browser.py` | PASS, exit 0 — 16 printed PASS groups |
| `favorites_weighted_browser.py` | PASS, exit 0 — 12 printed PASS groups |
| `scheduled_linked_slots_browser.py` | PASS, exit 0 — 4 printed PASS groups |
| `dependent_side_groups_browser.py` | PASS, exit 0 — 12 printed PASS groups |
| `manual_duplicate_meal_browser.py` | PASS, exit 0 — 60 printed PASS groups |
| `shared_week_scheduling_browser.py` | PASS, exit 0 — 64 printed PASS groups |
| `scheduled_date_integrity_browser.py` | PASS, exit 0 — 46 printed PASS groups |
| `meal_groups_bulk_safety_browser.py` | PASS, exit 0 — 10 printed PASS groups |
| `recipesage_refresh_browser.py` | PASS, exit 0 — 0 printed PASS groups |
| `skip_this_week_browser.py` | PASS, exit 0 — 22 printed PASS groups |
| `add_recipe_ideas_browser.py` | PASS, exit 0 — 8 printed PASS groups |

Printed PASS groups summarize scenarios, not individual assertion counts. RecipeSage refresh reports success by its exit status without printed PASS groups. Existing test assertions were not weakened or edited.

The passing suites cover Stage 2 creation/Cancel/Undo/failed-save rollback/latest-draft Retry Save and default/custom tabs; Stage 1 temporary meals, empty holds, grocery checks and rotation resets, linked contributions, ordering, and Undo; rotation history and weighted Favorites; recipe imports; guarded backups and compatibility; pending drafts, journals, strict rollback, and recovery export/retry.

Additional checks passed:

- `node --check` on every inline script in both HTML apps and on `service-worker.js`.
- Normalized equality of the shared application block between production and test HTML.
- Byte-for-byte preservation of the test-only shell outside that block, including storage isolation, banner, and reset controls.
- Python regression syntax and `git diff --check`.
- Published application/test blobs matched the tested local Git blob hashes.

Offline shell source was incremented to `v101` for a future approved release; no deployment or installed-PWA update was performed.

## Remaining issues and limits

The **older legacy Side assignment restoration issue remains separate and unchanged**. The targeted call `occasional_meals_browser.assignment(browser, filename, 320, 'Sides')` fails its post-full-rotation/Back/reload assertion at line 87 in both apps before these corrections and in both corrected apps. It was not necessary to fix that baseline issue to correct S2-1, and its scope was not expanded. S2-1 concerns a lost Stage 2 protection flag for ordinary paired automatic sides.

The allocator still does not support independent copies of the same recipe in multiple groups on the same weekday within a tab; Schedule Meal now rejects that unsupported request explicitly. Different weekdays and tabs remain supported. Previously documented historical import/editor probe limitations are not claimed fixed, and this report does not claim the entire historical test collection is green.

Physical-device gestures, screen readers, real quota exhaustion/process termination, cross-tab concurrency, and installed-PWA upgrades were not independently verified in this correction pass. Chromium emulation and injected storage failures do not establish those device guarantees.

Only these Stage 2 corrections and their tests/report were included. No Stage 3 defaults, later features, unrelated redesign, merge, or deployment were performed. Another independent verification is required before requesting authorization for further work.
