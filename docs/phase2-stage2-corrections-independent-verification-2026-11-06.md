# Phase 2 — Stage 2 Corrections: Independent Verification

Date: November 6, 2026 (UTC)

**Decision: READY FOR STAGE 3**

No confirmed blocking defect was found in this correction review. S2-1 now preserves paired-side queue/Favorites protection through history restoration, persistence, and another rotation. S2-2 now rejects unsupported same-day conflicts before mutation and explains the limitation without closing the dialog. The known legacy Side restoration issue remains reproducible and separate.

This is a verification result, not authorization to begin Stage 3, merge, or deploy. Owner review remains required.

## Scope and source

- Repository/branch: `elisabethball19-netizen/meal-rotation`, `codex/phase2-meal-rotation`.
- Reviewed head: [`e5a3043f72d436c745ac339574a7e341ffa464f1`](https://github.com/elisabethball19-netizen/meal-rotation/commit/e5a3043f72d436c745ac339574a7e341ffa464f1). Correction implementation: `e647fd35f4d922befba6cebf71c3399e74835543`; new regression commit: `8bcd112c96be4fcc3feea23bbdf6ea4e384b8411`.
- Started with the [correction completion report](phase2-stage2-corrections-completion-2026-11-06.md) and [previous independent findings](phase2-stage2-independent-verification-2026-11-06.md), then inspected the actual implementation diff and test assertions.
- Compared against preserved, unchanged pre-correction Stage 2 source from `fc7c8da3238567502c1f142a73a245814dbb61c2`. The new tests reproduce **all eight expected defects** on that source and pass **22 reported scenario groups** on corrected source. Reproduction mode checks specific assertion messages rather than accepting arbitrary browser failures.
- GitHub supplied the files because the workspace Git proxy was unavailable. Materialized Git blob hashes match published source: production `4101e1cc5a9a60da3783b4091a5c4336d3f77b68`, test `818f4fa4f55d23826dc38f2214092d705f16f3f7`, service worker `876d5284d7c1be401c187c95358d2395513a482b`.
- All recipes/storage were synthetic, in disposable Chromium contexts with intercepted fixture requests. Additional independent probe scripts stayed outside repository source. No application/test fixes, real user-data access, Stage 3 work, merge, or deployment occurred. Only this verification report is published.

## S2-1: Rotation Back and paired-side protection — PASS

The [shared Back restoration path](https://github.com/elisabethball19-netizen/meal-rotation/blob/e5a3043f72d436c745ac339574a7e341ffa464f1/index.html#L6129) now copies saved choice metadata only when its recipe ID matches the restored occurrence. It then applies the existing current-recipe, parent-link, substitution, and retention rules. This retains `preserveSideQueue` without replacing current recipe definitions with historical records.

Executed checks in both HTML apps use a real weighted side pool with multiple eligible sides, including Favorite recipe 13. Main scheduling uses the real Meal Groups → Schedule Meal controls. Creation cases use Create New Recipe through Change Meal, as both an Idea and explicitly In Rotation.

Verified:

- The first expiration of a manually scheduled main preserves the actual side queue and complete Favorites ledgers.
- Both full and selected Back retain the matching saved choice metadata, including `preserveSideQueue:true`.
- Dependent-side state remains protected (`automatic:false`) after restoring the manual parent.
- Reload and backup/restore preserve the flag, including backups with pending history and backups taken after Back.
- A subsequent rotation preserves the same queue and credit ledger. Cases include selected-main and full active-plan rotations.
- Current recipe edits made after rotation remain intact through Back.
- Create New Recipe scheduling receives the same protection in the covered Idea/In Rotation and full/selected Back cases.

The suite compares queue arrays, ledger objects, saved choices, and live definitions; these are not visual-only checks. The previously failing `[10,11,12,13,14] → [10,11,12,14,13]` corruption no longer occurs in the protected cases.

An additional independent probe initialized a **nonzero existing Favorites ledger** before scheduling. Through real UI scheduling, both Back modes, two backup/restore/reload boundaries, and another rotation, the entire queue/ledger state stayed exactly equal to its starting state in both apps. This supplements the repository suite's initially absent ledger cases.

### Ordinary automatic rotation control — PASS

The fix does not suppress normal automatic side consumption. Beyond the suite's change-versus-no-change control, an independent probe asserted the exact outcome of one ordinary automatic turn:

```text
Initial side queue: [10, 11, 12, 13, 14]
Outgoing side: 11
Resulting queue: [10, 12, 13, 14, 11]
Favorite: 13 (weight 2; other weights 1)
Resulting scores: {10:1, 11:-5, 12:1, 13:2, 14:1}
```

Both apps produce exactly this queue and one weighted turn. Protection is therefore retained for the manual schedule without globally disabling automatic queue/Favorites advancement.

## S2-2: Same-day duplicate scheduling — PASS

The [shared Schedule Meal action](https://github.com/elisabethball19-netizen/meal-rotation/blob/e5a3043f72d436c745ac339574a7e341ffa464f1/index.html#L3692) checks the target tab's displayed entries before taking a scheduling snapshot or writing state. A conflicting occurrence in another group raises an explanation identifying the group/day and the once-per-weekday/per-tab restriction. The UI catches the error and retains the open dialog.

Using actual Meal Groups → Schedule Meal controls in both apps, verified:

- A displayed main cannot silently be scheduled into the other assigned group that day.
- A displayed side, including the linked-side fixture, cannot silently be scheduled into the main slot that day.
- The dialog stays open and its status explains the conflict.
- Rejection leaves captured application storage, displayed rows, grocery lines/checks, queues, Favorites state, ingredient selections, and permanent assignments unchanged.
- The same recipe can still be scheduled on another weekday and in another tab; existing source occurrences remain, and supported results survive reload.

Independent supplemental cases target a **different, inactive meal tab** containing both assigned groups. They use an existing Favorites ledger and checked/scaled grocery sources. Repeated rejected UI requests, Cancel, and direct calls of the shared action preserve the complete captured storage and live state, including **Undo history length** and active tab. Both main and side conflicts pass. Thus the guard is not restricted to the visible tab or to one button handler.

The historical allocator restriction remains: independent copies of the same recipe ID in multiple groups on one weekday within one tab are unsupported. This review accepts explicit rejection as the scoped S2-2 correction; it does not claim the allocator was redesigned or that the older Change Meal workflow changed.

## Existing functionality and safety

### Stage 2 creation and tabs

The Stage 2 suite passes independently: Create New Recipe entry, Save, Cancel, scheduling Undo that retains the created recipe, restoration of one-time/empty state and groceries, failed-save rollback of both library and schedule, recovery export of the latest edited draft, Retry Save, and reload/backup persistence.

Additional independent failure injections on **plan storage and ingredient-selection storage** pass exact durable rollback and Retry with latest edits to name, ingredients, instructions, and notes. This supplements the suite's primary recipe-record write failure. The custom-tab scheduling/grocery and backup probe also passes. Stage 3 default-checkbox changes are not treated as correction requirements.

The existing Stage 2 tab suite passes default/custom additions, validation, rename, reorder, delete, Settings access while hidden, reload, backup, and isolation. An additional probe deletes Breakfast, Lunch, and Dinner while retaining a custom tab. All three remain absent through reload/backup and return only after explicit Add actions, with empty assignments. Recipe definitions and production sentinels remain intact. Blank/whitespace and case/whitespace duplicate names are rejected.

### Stage 1 and Phase 1

Stage 1 suites cover temporary entries, intentional empty slots, scheduling-only Undo, same-cycle grocery-check/quantity preservation, selected/full rotation resets, linked quantities, and keyboard/pointer/touch ordering. Phase 1 suites cover recovery journals, original-data preservation/export, interrupted replacement, malformed backup/startup data, pending drafts, strict rollback, retry, and saved-data compatibility.

No new storage key or migration was introduced by these corrections. The implementation diff is limited to the early duplicate guard and matching saved-choice metadata restoration in both apps, plus the shell version. The core persistence/recovery machinery was not changed.

### Synchronization, isolation, and syntax

Normalized shared application-script equality passes. The test-only shell outside the shared block is byte-for-byte unchanged from pre-correction source, including its prefixed storage adapter, banner, and reset controls. Synthetic production sentinels survive test-app cases. All inline scripts and the service worker pass `node --check`. Shell v101 was inspected, not deployed or tested as an installed-PWA upgrade.

## Independent execution record

| Suite/probe | Result |
| --- | --- |
| `phase2_stage2_corrections_browser.py` | PASS — 22 reported groups, both apps |
| Same suite against preserved pre-correction HTML with reproduction flags | PASS — all eight specific defects reproduced |
| `phase2_stage2_browser.py` | PASS — existing creation/tab/scheduling cases |
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
| Independent nonzero-ledger/history and exact automatic control | PASS — both apps |
| Independent inactive-tab UI/direct conflict rejection and no-history-mutation | PASS — both apps |
| Independent partial-write/latest-draft Retry and custom-tab checks | PASS — both apps |
| Independent deletion/explicit restoration of all default tab names | PASS — both apps |

Results are from this verification, not inherited pass claims from the completion report. The focused known failing legacy case below is not counted as a passing suite. This is not a claim that the entire historical repository test collection is green.

## Test quality and remaining coverage limits

The new tests directly address the previous coverage failures: multiple compatible sides, a real Favorite, queue and ledger equality before/after another rotation, retained choice metadata, persistence boundaries, both Back modes, creation paths, and real duplicate UI interactions. Expected-failure mode verifies the exact old corruption or silent close, reducing the chance of treating an unrelated setup error as a successful reproduction. No existing regression assertions were weakened in the inspected correction diff.

The suite's normal automatic control checks that queue/ledger change; the independent exact-turn probe strengthens that to a precise expected result. The repository history cases begin with no ledger; independent nonzero-ledger cases close that gap. Inactive-tab rejection, repeated submissions, and Undo-history preservation also received supplemental assertions. These additions found no confirmed blocking defect.

Physical-device gestures, screen readers, real quota exhaustion/process termination, cross-tab concurrency, and installed-PWA upgrades remain unverified. Chromium mobile/keyboard checks and injected failures do not establish those device guarantees. Historical import/editor probe limitations documented in previous reviews are not claimed fixed.

## Separate existing issue

The **legacy Side assignment restoration bug is unchanged**. Independently executed `occasional_meals_browser.assignment(browser, filename, 320, 'Sides')` on both pre-correction and corrected HTML apps. All four fail the same post-full-rotation/Back/reload assertion at line 87. Its earlier reproduction on Phase 1 is documented in the previous reviews. This is distinct from S2-1's now-corrected lost protection flag for ordinary paired automatic sides. No new legacy Side regression was demonstrated here.

No confirmed blocking defect remains in the reviewed correction areas. Keep the existing issue and device limits tracked separately and obtain owner authorization before any Stage 3 work.

**READY FOR STAGE 3**
