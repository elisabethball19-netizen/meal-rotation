# Phase 2 pull request preparation

Date: 2026-11-06. Proposed merge: `codex/phase2-meal-rotation` → `main`. All five stages are independently accepted. This prepares the pull request only; merge and deployment still require the owner's separate approval.

## Summary

1. **Scheduling and rotation safety:** Skip This Meal, individual/whole-day intentional empty slots, temporary one-time meals with groceries, and schedule-only drag ordering. Same-cycle grocery progress is preserved; rotated occurrences reset appropriately. Undo and history retain temporary scheduling without rewinding unrelated recipe edits.
2. **Direct scheduling and tabs:** Schedule Meal from Meal Groups, reusable recipe creation from Change Meal with safe Cancel/Undo/Retry, and explicit restoration/addition of default or custom meal tabs. Temporary scheduling preserves normal queues and paired-side Favorites credits; unsupported same-day duplicates are rejected before mutation.
3. **Recipe and grocery workflows:** Lightweight viewer editing, grocery-to-recipe navigation with shopping/view restoration, and In Rotation/default-all grocery choices for genuinely new/imported recipes. Existing Ideas, explicit ingredient exclusions (including empty selections), shared memberships and import provenance remain preserved.
4. **Onboarding and interface:** Empty-collection Import/Add actions, temporary Set Up Your Rotation using existing weekday assignments, Rotate Meals terminology, compact Needs Adjusting controls, clearer removal/deletion wording and trash icons. Accepted corrections cover nested-dialog focus and occurrence-aware group Undo, preserving later unrelated shopping/cooking/scaling edits.
5. **Optional photos:** Attach/replace/remove, small thumbnails/placeholders in Meal Groups and recipe selection/search, and a larger viewer image. My Rotation and Weekly Overview stay compact. Shared recipe memberships share photos; serving-linked recipes remain independent.

## Independent acceptance

| Stage | Final accepted verification |
| --- | --- |
| 1 | [Corrections verification — READY FOR STAGE 2](https://github.com/elisabethball19-netizen/meal-rotation/blob/ba89b4646b8d28fe084869cdc051b8bb19bc47b3/docs/phase2-stage1-corrections-independent-verification-2026-11-06.md) |
| 2 | [Corrections verification — READY FOR STAGE 3](https://github.com/elisabethball19-netizen/meal-rotation/blob/ba89b4646b8d28fe084869cdc051b8bb19bc47b3/docs/phase2-stage2-corrections-independent-verification-2026-11-06.md) |
| 3 | [Corrections verification — READY FOR STAGE 4](https://github.com/elisabethball19-netizen/meal-rotation/blob/ba89b4646b8d28fe084869cdc051b8bb19bc47b3/docs/phase2-stage3-corrections-independent-verification-2026-11-06.md) |
| 4 | [ACCEPT STAGE 4](https://github.com/elisabethball19-netizen/meal-rotation/blob/ba89b4646b8d28fe084869cdc051b8bb19bc47b3/docs/phase2-stage4-acceptance-2026-11-06.md) |
| 5 | [ACCEPT STAGE 5](https://github.com/elisabethball19-netizen/meal-rotation/blob/ba89b4646b8d28fe084869cdc051b8bb19bc47b3/docs/phase2-stage5-acceptance-2026-11-06.md) |

## Branch and scope checks

- Current `main` is `b362c19bcd57ec8259729f43c7ef552b7dd74089`, the merged Phase 1 PR [#77](https://github.com/elisabethball19-netizen/meal-rotation/pull/77). GitHub confirms that PR was merged on 2026-11-05.
- Accepted Phase 2 head is `ba89b4646b8d28fe084869cdc051b8bb19bc47b3`: **50 commits ahead, 0 behind**. The merge base equals current `main`, so the accepted branch incorporates all of `main` and has no merge conflicts.
- The accepted diff contains 58 paths: 24 Phase 2 documents, 31 regression-test files, and only three application files (`index.html`, `meal-rotation-test.html`, `service-worker.js`). Existing test adaptations follow the approved UI/default changes and accepted fixtures. No unrelated assets, infrastructure, deployment configuration or application modules changed.
- Since Stage 5 completion `bf2284a`, the only remote change was the Stage 5 acceptance document. The application still matches the independently accepted blobs: production `cd4395c13861e1722160b0bb2bdbd41d7a3f4fd9`, test `40c287b03180ff4a30bb11077d9fe7488b800b6c`, worker `667b14fd6e4c2b56f358648356120c1d45c49fe7`.
- PR preparation adds only this Markdown document. No application or test implementation was changed during preparation. Shared application JavaScript/CSS remain synchronized after the intentional storage adapter/banner differences. Test localStorage, photo IndexedDB, banner and reset remain isolated.

## Automated validation

| Evidence | Actual result |
| --- | --- |
| Fresh PR-preparation `python tests/phase2_stage5_static.py` | PASS: both inline scripts, worker syntax, normalized shared JS/CSS, preserved test shell/storage adapter and whitespace checks |
| Fresh PR-preparation `python tests/phase1_final_recovery_safety_browser.py` | Exit 0; **16 PASS groups**, both apps: unreadable originals, incomplete/repeated recovery and unrelated-operation protection |
| Fresh PR-preparation `python tests/phase2_stage5_photos_browser.py` | Exit 0; **6 PASS groups**, both apps at 280/360px: real uploads, scoped history, persistence, placeholders/thumbnails and actual photo-bearing backup round trips |
| Recorded final Stage 5 implementation run | **38 browser scripts passed**, plus static checks; includes 28 scheduling/recipe/grocery/Phase 1–3 scripts, four Stage 4 suites, Phase 1 safety corrections, weekday setup and four photo suites |
| Independent Stage 5 acceptance | All six selected scripts exited 0: **23 photo groups + 42 Phase 1 recovery/safety groups**, plus two fresh-context photo backup/restore probes |

The [Stage 5 completion report](https://github.com/elisabethball19-netizen/meal-rotation/blob/ba89b4646b8d28fe084869cdc051b8bb19bc47b3/docs/phase2-stage5-completion-2026-11-06.md) lists the 38-script coverage and limitations. The broader recorded run was checked against its saved exit results; it was not repeated wholesale for documentation-only PR preparation. Earlier stage acceptance reports supply the independent scheduling, grocery, Favorites, shared-recipe, completion, Undo/Back and data-safety evidence. Results are local/disposable Chromium script executions, not a deployed smoke test or a claim that every historical suite passes.

Existing recipes, localStorage compatibility, ingredient selections, queues, Favorites, occurrence scales/completion and grocery progress are covered by the accepted regressions. Phase 1 failed-save rollback, pending drafts, recovery journals/export, Retry Save and safe backup replacement remain active; the fresh recovery suite passes on the exact accepted source.

## Photo storage and backups

[Finalized design](https://github.com/elisabethball19-netizen/meal-rotation/blob/ba89b4646b8d28fe084869cdc051b8bb19bc47b3/docs/phase2-stage5-photo-storage-design-2026-11-06.md): photos are resized/re-encoded to JPEG, at most 1024px on the longest edge and 256 KiB each. Recipe/localStorage records contain only a lightweight SHA-256 `recipePhotoId`; blobs use separate production/test IndexedDB databases. No image payload or object URL enters localStorage.

Immutable blobs finish writing and pass verification before recipe references are saved. Missing/unavailable storage, quota errors and interrupted writes leave recipes usable. Reference-save failures retain the prior recipe/photo and the existing recovery proposal/Retry path. Removal detaches a reference without needing IndexedDB. Old blobs are retained for Undo/history/recovery; unused blobs can consume quota because no destructive garbage collection was added.

Ordinary downloadable backups remain **version 2**, with an optional deduplicated `photos` extension (4096 images / 40 MiB decoded bytes maximum; omissions explicit). Older version-1/version-2 backups remain supported. Core validation precedes image staging and the existing protected core replacement. Optional image damage/failure gives warnings/placeholders without rejecting valid recipes. Core backups/recovery exports remain available if photos fail; internal safety snapshots retain references, while ordinary downloads supply portable images. Browser/origin storage is local, so portable photo backups matter when changing browsers/devices.

## Four separate pre-existing issues

These remain documented and outside this PR's correction scope:

- **Legacy Side assignment restoration:** a scheduled side can restore incorrectly after full rotation, Rotation Back and reload.
- **Historical duplicate allocation:** selected rotation can allocate a recipe already retained in another occurrence; distinct from the new direct-scheduling duplicate guard.
- **Linked-occurrence rotation:** an independently scheduled/linked occurrence can move or lose state during selected rotation.
- **Heading spacing:** existing sticky heading/content gaps fail the historical narrow-screen spacing expectations.

The Stage 5 completion run retained these assertions and reproduced the four targeted failures in both apps (8 expected baseline failures). They are not counted as passing suites. No unrelated allocator/layout redesign or fixes are included. See the [separate known-issue record](https://github.com/elisabethball19-netizen/meal-rotation/blob/ba89b4646b8d28fe084869cdc051b8bb19bc47b3/docs/phase2-stage4-final-independent-verification-2026-11-06.md) and Stage 5 completion limitations.

## Deployment and service worker

No merge or deployment is authorized or performed here. The shell version advances **v97 → v108**; worker behavior and shell-file list are otherwise unchanged. A future approved release must deliver both HTML apps and the worker together. The existing worker waits rather than forcing `skipWaiting`, allowing open editing sessions to finish before takeover; activation clears older shell caches within its scope, not recipe localStorage or photo IndexedDB. The worker caches static shell files, not recipe backups/imports or photos.

Installed-PWA update behavior, physical-device Safari/Firefox and very large collections were not acceptance-tested. Verify the installed/offline update path during a separately approved release. Hosting settings were not changed; any hosting automation tied to `main` must be considered before approving a later merge. No GitHub Actions workflow files are present in the inspected branch.

[Shareable Markdown preparation document](https://github.com/elisabethball19-netizen/meal-rotation/blob/codex/phase2-meal-rotation/docs/phase2-pull-request-preparation-2026-11-06.md).
