# Phase 2 — Stage 1 Corrections: Independent Verification

Date: November 6, 2026 (UTC)

**Decision: READY FOR STAGE 2**

No confirmed blocking defect was found in this correction review. The previous R1–R3 defects are corrected, and the previously unresolved grocery Resume behavior now preserves same-cycle progress while rotation resets affected occurrences. The existing legacy Side restoration defect remains reproducible and separate. This decision is a verification result, not authorization to start Stage 2, merge, or deploy.

## Scope and source

- Branch: `codex/phase2-meal-rotation` in `elisabethball19-netizen/meal-rotation`.
- Reviewed head: [`8b6ed26ca88debbfe98bf38dda8be8d4d016311a`](https://github.com/elisabethball19-netizen/meal-rotation/commit/8b6ed26ca88debbfe98bf38dda8be8d4d016311a). Correction implementation: `9b51edbc5b671ca64a4a270ff07f52d5ea20cdae`.
- Started with the [corrections completion report](phase2-stage1-corrections-completion-2026-11-06.md) and [previous independent review](phase2-stage1-independent-verification-2026-11-05.md). Inspected the actual HTML changes, history restoration, grocery-source reconciliation/cache ownership, occurrence pruning/reset, backup validation, deletion cleanup, and new tests.
- Compared with preserved pre-correction Stage 1 HTML. The new test suite reproduces **12 expected failures** on that source, then passes **24 reported case groups** on corrected source. These are assertion failures, not browser exceptions accepted as successful reproductions.
- Retrieved source through GitHub because the workspace Git proxy was unavailable. Local HTML Git blob hashes match published source: production `1950fd46e1033a6488ded1220ce9125a8e0d3074`, test `85438fbfae2927b521ca0180ee74476b5a7075b6`. Service worker: `ac9cf142593d05f1a54423497b5e6e968ac929bf`.
- Used synthetic recipes/storage, intercepted fixture requests, disposable Chromium contexts, and additional probe scripts outside repository source. No real user storage was accessed. Only this report is published; no application/test fixes, merge, deployment, or Stage 2 work were performed.

## Findings against the requested checks

### 1. Undo and live data preservation — PASS

The Change Meal mutation now snapshots the intact state before clearing a temporary slot. Scheduling-only restoration keeps current recipe records and permanent ingredient selections, rather than restoring an old recipe library. Its source-ID set limits grocery restoration to quantities entering/leaving the affected schedule; retained occurrences keep later shopping progress.

Verified both one-time-to-recipe and empty-to-recipe Undo in both apps. Assertions compare the complete temporary descriptor, stable one-time ID, displayed schedule, grocery lines/checks/quantities, and unrelated occurrences. Tests also preserve later changes to notes, ingredients, instructions, source URL, selections, unrelated checks, and scaling. Duplicate-source replacement includes the one-recipe/same-ID case.

Independent additional probes exercised real Undo/Redo controls for one-time, individual-empty, and whole-day-empty transitions with scaled main/linked quantities and later live recipe edits/shopping progress. The original descriptors and the expected grocery state survived the round trip. Repeated Empty → One-Time → Empty → One-Time → Resume preserved the underlying meal's held shopping state.

Relevant implementation: [`restoreScheduleUndoState` and snapshot metadata](https://github.com/elisabethball19-netizen/meal-rotation/blob/8b6ed26ca88debbfe98bf38dda8be8d4d016311a/index.html#L3958), and [`applyManualWeekdayMeal`](https://github.com/elisabethball19-netizen/meal-rotation/blob/8b6ed26ca88debbfe98bf38dda8be8d4d016311a/index.html#L7184).

### 2. Unconfigured weekdays — PASS

The temporary meal's Change Meal action normalizes `@day` and uses the existing occasional-meal path. The mutation routine also normalizes this case defensively. Actual UI selection on unconfigured Sunday now displays the chosen reusable recipe and its grocery contributions without adding Sunday group assignments or `Sunday::@day` entries to permanent override/pin/choice maps. Choosing an otherwise unscheduled recipe preserves normal queue order.

Verified reusable recipes, Ideas and linked groceries, reload, backup/restore, Undo, duplicate Cancel/Keep both/Replace decisions, and the one-recipe duplicate-source edge. These assertions check actual scheduled rows and grocery sources, not merely successful dialog closure.

### 3. Legacy occasional ordering and gestures — PASS

Rendered row metadata and handles now use the complete planner entry. The legacy `occasional` flag and recipe ID therefore participate consistently in ranking, pointer drag, keyboard lookup, and saved order. Keyboard focus restoration is scoped to the weekday.

Verified the legacy meal's own handle using pointer drag and keyboard at **320px and 360px**, with reload and backup/restore. Also verified weekday-specific keyboard focus when the same legacy recipe appears on another day. Independent UI probes reordered the legacy meal, then confirmed name long-press still opens its recipe viewer and ordinary left swipe opens its editor in both apps. The original Stage 1 gesture suite also passes, including touch drag without accidental swipe activation.

### 4. Grocery preservation versus cycle reset — PASS

The optional per-slot `groceryChecks` cache holds only occurrence-specific checks. Hidden quantities retain their existing occurrence multipliers. Resume merges available same-cycle checks back into active sources. Rotation discards the selected temporary descriptor and includes its hidden underlying occurrences in shopping/cooking reset, without treating those hidden recipes as consumed queue turns.

Verified:

- Empty → Resume restores main and linked checks and scaled quantities, including reload and full backup/restore while hidden.
- Whole-day holds and multiple hidden groups resumed individually preserve the expected source states.
- Selected rotation expires/reset only selected/affected occurrences; an unrotated hidden group retains its cache and quantities.
- Rotating another group leaves a hidden main and attachment's progress intact when resumed.
- Full rotation and selected rotation reset newly scheduled sources, including the exact same recipe ID returning in a one-recipe pool.
- A recipe returning after intervening rotations has unchecked groceries; unaffected side and other-tab sources retain checks.
- Shared ingredient totals and mixed checked/unchecked contribution states agree with their individual source quantities. Permanent ingredient selections/exclusions remain unchanged.

Relevant implementation: [`temporaryGroceryOwner`, held checks, and temporary mutation](https://github.com/elisabethball19-netizen/meal-rotation/blob/8b6ed26ca88debbfe98bf38dda8be8d4d016311a/index.html#L5688), and [rotation reset of hidden occurrences](https://github.com/elisabethball19-netizen/meal-rotation/blob/8b6ed26ca88debbfe98bf38dda8be8d4d016311a/index.html#L6256).

### 5. Data safety and compatibility — PASS for tested scenarios

The new cache stays inside optional `weekSchedule` slot state. It does not replace recipe ingredients or permanent ingredient-selection storage. The cache validator delegates to the existing occurrence-source validation; old records without it remain valid. Dependency-aware deletion prunes cached references to deleted recipes/parents.

Verified backup/restore and reload with hidden checks/scales, malformed-cache backup rejection without replacement, original durable plans retained after injected write failure, persistent warning, recovery export containing pending cache data, Retry Save, and successful subsequent reload/Resume. Existing recipe-deletion and history protections remain covered by regression suites.

All three Phase 1 safety/recovery suites pass independently. No change to the core recovery journal/replacement machinery was found in the correction diff. These checks establish the tested browser/storage behavior; they do not simulate real device termination or every quota failure timing.

### 6. Regression quality, synchronization, and isolation — PASS

The new correction suite makes meaningful comparisons of descriptors, source checks/lines, queue order, definitions, ingredient selections, actual UI choices, reload/backup persistence, aggregation, and failure recovery. Its historical failure mode distinguishes AssertionError from unexpected browser errors. The correction implementation commit changes only the two HTML apps, service worker, and new correction suite; existing regression assertions were not weakened in that commit.

Independent probes supplemented the suite with whole-day Undo/Redo, repeated temporary replacement, multi-group Resume, post-reorder legacy long-press/swipe, and real test-app reset. These passed. An additional grocery probe covered range quantities (both lower and upper aggregate totals), duplicate ingredient occurrences, unmeasured lines, and mixed checks through hidden reload/backup/Resume and selected rotation in both apps; selections and unaffected checks remained intact. Some fixture operations use direct hooks to create precise later edits/checks/scales; the critical selection, reorder, Undo/Redo, and reset interactions also use real controls.

The shared inline persistence/application script is identical after normalizing only the intentional storage-adapter differences. Production/test manifests, banner, reset, and storage namespace remain distinct. A real test-app reset preserved the synthetic production sentinel. Inline JavaScript and service-worker syntax checks pass. Shell v99 was inspected but not deployed.

## Independent execution record

Repository suites rerun on the corrected HTML:

| Suite | Result |
| --- | --- |
| `phase2_stage1_corrections_browser.py` | PASS — 24 reported groups across both apps |
| Same suite against preserved pre-correction HTML with reproduction flags | PASS — all 12 expected failures reproduced |
| `phase2_stage1_browser.py` | PASS |
| `phase2_stage1_workflows_browser.py` | PASS |
| `phase1_final_recovery_safety_browser.py` | PASS |
| `phase1_safety_corrections_browser.py` | PASS |
| `phase1_data_safety_browser.py` | PASS |
| `grocery_rotation_checks_browser.py` | PASS |
| `skip_this_week_browser.py` | PASS |
| `favorites_weighted_browser.py` | PASS |
| `scheduled_linked_slots_browser.py` | PASS |
| `dependent_side_groups_browser.py` | PASS |

The additional independent probes described above passed. The report does not inherit unexecuted suite results from the implementation completion report or claim that the entire repository test collection is green.

## Existing issue and verification limits

**Legacy Side restoration remains an existing issue.** Independently reran `occasional_meals_browser.assignment(browser, filename, 320, 'Sides')` on both corrected HTML apps. Both still fail the known post-full-rotation/Back/reload assertion at line 87. The previous independent review reproduced this same failure on unchanged Phase 1 source. No distinct new Side restoration regression was demonstrated here. Its full legacy suite is not claimed to pass.

The previously documented obsolete import-repair hook, reviewed-import rollback assertion, and hidden/obsolete editor-control probes were not fixed by this patch and are not counted as passing full suites. This review does not reclassify them as new correction regressions.

Unverified: physical iOS/Android gestures, screen readers, real quota exhaustion/process termination, cross-tab conflict handling, and installed-PWA upgrades. Previously discarded hidden shopping checks cannot be reconstructed from old records that never saved them. Undo remains an in-memory feature; persisted schedule/shopping state was verified across reload and backup/restore.

No confirmed blocking defect remains from the reviewed correction areas. Retain the existing-issue/device limitations in follow-up tracking and obtain owner authorization before Stage 2.

**READY FOR STAGE 2**
