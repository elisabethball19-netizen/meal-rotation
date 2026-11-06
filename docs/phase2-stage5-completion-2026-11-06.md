# Phase 2 — Stage 5 completion: optional recipe photos

Date: 2026-11-06. Repository: `elisabethball19-netizen/meal-rotation`. Branch: `codex/phase2-meal-rotation`.

Stage 5 implementation is complete for independent acceptance review. No merge or deployment was performed. The accepted Stage 4 source was the starting point; no older scheduling issues were included in this implementation.

## Features

- Attach, replace and remove a recipe photo from the internal recipe viewer. Successful changes retain the active recipe tab, viewer state and focus. The controls use the existing modal/focus mechanisms, with Cancel and Escape and scrollable controls at narrow sizes.
- Small 32px thumbnails, or subdued placeholders, appear in Meal Groups, Change Meal, global meal search and the viewer's Open Recipes selector. A larger image appears in the viewer content. My Rotation and Weekly Overview remain free of photos.
- Shared group memberships of one recipe share a photo. Serving-linked recipes retain independent photos. Existing recipe editing, exclusions, linked tabs, schedules, groceries and cooking state remain usable with absent or unavailable photos.
- Photo-only Undo/Redo restores only the affected photo reference fields. It preserves later recipe edits, grocery checkbox changes, occurrence scales and cooking completion.

## Storage, backup and recovery design

The [storage design](phase2-stage5-photo-storage-design-2026-11-06.md) was finalized and published in [abbaf12e40996ad5107f347367a0165b8b645964](https://github.com/elisabethball19-netizen/meal-rotation/commit/abbaf12e40996ad5107f347367a0165b8b645964) **before storage implementation**. The final document also records the narrowly scoped photo Undo behavior.

Recipe records contain only an optional `recipePhotoId` (`rp1-` plus a SHA-256 digest). Processed JPEG blobs live in IndexedDB: `mealRotationRecipePhotosV1` for production and `mealRotationTestRecipePhotosV1` for the isolated test app. No image bytes or object URLs are written into localStorage, and existing records are not migrated.

Uploads accept JPEG, PNG, WebP and GIF (still image). Inputs are limited to 20 MiB and 40 megapixels. Canvas re-encoding flattens transparency onto white, removes source metadata and reduces the longest edge to at most 1024px and the result to at most 256 KiB. Unsupported formats, decoding errors and quota failures leave the recipe unchanged.

An immutable blob must finish writing and pass a read/checksum verification **before** the existing validated recipe-storage transaction saves its reference. Cancel, stale references and interrupted uploads prevent a late reference commit. Failed core saves retain the prior recipe/photo and use existing recovery export and Retry Save. Removing a reference works without IndexedDB. Object URLs are released when their elements are removed or the document is discarded.

Ordinary downloadable backups retain `version: 2` and their existing recipe/storage fields. An optional `photos` extension contains deduplicated JPEG files, missing-reference IDs and warnings. Base64 exists only inside the downloaded file. The extension is bounded to 4096 images and 40 MiB decoded bytes. Recovery exports also collect photos referenced by original storage and failed/pending proposals.

Restore validates ordinary recipe/storage data first, validates and stages optional images second, and then uses the existing Phase 1 core replacement/rollback/journal protection. Missing, malformed or unavailable photos produce a warning and usable recipes/placeholders. Old backups without photos remain accepted. A failed core restore never deletes earlier blobs. Existing internal safety snapshots keep their existing format and references; the ordinary downloaded backup is the portable photo-inclusive export.

The test banner and isolated storage adapter are preserved. Reset Test App additionally clears only the test photo database; a photo-reset failure does not prevent resetting test recipe data. The service-worker cache version advances to v108 for a future approved deployment; nothing was deployed in this stage.

## Permanent regression coverage and results

| Command / suite | Actual result |
| --- | --- |
| `python tests/phase2_stage5_photos_browser.py` | PASS: 6 groups, both apps, 280px/360px and real photo backup round trip |
| `python tests/phase2_stage5_photo_safety_browser.py` | PASS: 8 groups, including failed Redo/Retry and interrupted writes |
| `python tests/phase2_stage5_photo_isolation_browser.py` | PASS: 3 groups, same-origin isolation/reset and both apps' image/mobile/keyboard handling |
| `python tests/phase2_stage5_photo_recovery_browser.py` | PASS: 6 groups, startup recovery, selection/search UI and nonresponding storage |
| `python tests/phase2_stage5_static.py` | PASS: both HTML syntax, service worker syntax, shared JS/CSS parity, preserved test shell/adapter and whitespace checks |
| Stage 4 original / corrections / final / grocery Undo browser suites | PASS: 38 / 18 / 30 / 20 groups (106 total) |
| `phase1_safety_corrections_browser.py` | PASS: 26 groups, including recovery journals, nested drafts, rollback, interrupted Retry and supersession |
| Existing weekday setup suite | PASS: 6 groups, including 280/320/360/390px/desktop and large text |
| Existing Phase 1–3 / scheduling / grocery / viewer / import regression batch (28 scripts, listed below) | PASS: all 28 exited 0 on the final run |

In total, 38 browser scripts passed (the 4 new photo suites plus 34 existing scripts), alongside the static suite. The four new photo suites contain 23 grouped checks. The 28-script batch covers `phase2_stage3`, `phase2_stage3_corrections`, `phase2_stage2`, `phase2_stage2_corrections`, `phase2_stage1`, `phase2_stage1_corrections`, `phase2_stage1_workflows`, `phase1_final_recovery_safety`, `phase1_data_safety`, `grocery_rotation_checks`, `scheduled_linked_slots`, `favorites_weighted`, `dependent_side_groups`, `manual_duplicate_meal`, `shared_week_scheduling`, `scheduled_date_integrity`, `meal_groups_bulk_safety`, `recipesage_refresh`, `skip_this_week`, `add_recipe_ideas`, `recipe_tabs`, `recipe_tab_reorder`, `recipe_touch`, `shared_recipe_management`, `needs_tweaking`, `group_order`, `rotation_dialog_layout` and `outgoing_cooked_dates` (each `tests/<name>_browser.py`).

The existing weekday test's historical `git show` fixture was supplied from an unchanged archived HTML copy because the managed workspace has mirrored Git history; its assertions were unchanged. New photo tests accommodate the bounded asynchronous image/storage deadlines with a 20-second UI wait. This does not change any existing correctness assertion.

The new tests use real file inputs, actual export downloads and restore file choosers, real IndexedDB transactions, actual Grocery List checkbox changes, isolated synthetic recipes and injected failure boundaries. They compare recipe/scheduling/grocery/cooking state, not just image visibility.

Covered cases include attachment/replacement/removal; compressed JPEG dimensions/digests; shared memberships and independent serving-linked photos; thumbnails and placeholders; reload; photo Undo/Redo after later edits; failed photo Redo and Retry; quota and aborted transactions; cancellation and reload after a real write starts; failed reference saves; recovery exports containing original and proposed photos; ordinary saves without photo storage; nonresponding IndexedDB; missing images; malformed/oversized optional manifests; invalid core rejection before image staging; old version-1/version-2 backups; photo-bearing startup recovery with working and unavailable IndexedDB; failed backup core restore and Retry; same-origin production/test isolation and Reset Test App; unsupported/corrupt/oversized files; JPEG/PNG/WebP/GIF; noisy-image compression; narrow portrait/short-height controls; keyboard trapping/Escape; and object URL cleanup.

Existing test files and correctness assertions were not weakened or edited. Production/test shared JavaScript and CSS parity, inline JavaScript/service-worker syntax, preserved test shell/storage adapter and `git diff --check` are checked by the new static suite.

## Known limitations and separate existing issues

- Replaced, removed or interrupted-upload blobs are retained deliberately for Undo, history and recovery. There is no automatic garbage collection. These unused blobs can consume quota; later failed photo uploads remain optional and do not prevent recipe saves or core backups.
- Browser storage remains local to that browser/origin. Missing or evicted images display placeholders. Export a photo-inclusive backup to carry images to another browser. HEIC/SVG are not supported; animated GIFs become a still image.
- Photo bundles exceeding the optional export budget omit excess images explicitly and retain all ordinary recipe data. Damaged/unavailable image files can be omitted with warnings.
- Browser verification used Chromium with emulated mobile sizes, including 280px and a short 280×360 viewport. Physical-device Safari/Firefox behavior, very large real-world collections and an installed service-worker upgrade were not verified. No deployment was used for testing.
- The separately documented older Side-restoration, duplicate-allocation, linked-occurrence and heading-spacing failures remain outside Stage 5. The targeted baseline checks still reproduce each in both HTML apps (8 expected failures); their assertions were retained. No unrelated scheduling redesign was attempted.

## Commits and handoff

- Design before implementation: [abbaf12e40996ad5107f347367a0165b8b645964](https://github.com/elisabethball19-netizen/meal-rotation/commit/abbaf12e40996ad5107f347367a0165b8b645964).
- Implementation: [afd0019c89bc89a89da79ff14edc05913628ebd5](https://github.com/elisabethball19-netizen/meal-rotation/commit/afd0019c89bc89a89da79ff14edc05913628ebd5).
- Permanent regressions: [1e5b358e99724f06be598b9380c6a136a638911b](https://github.com/elisabethball19-netizen/meal-rotation/commit/1e5b358e99724f06be598b9380c6a136a638911b).

[Shareable completion report](https://github.com/elisabethball19-netizen/meal-rotation/blob/codex/phase2-meal-rotation/docs/phase2-stage5-completion-2026-11-06.md).

Stop point: Stage 5 implementation and testing only. Await the owner's focused independent acceptance review before any merge or deployment.
