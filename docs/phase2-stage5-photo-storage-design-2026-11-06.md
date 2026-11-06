# Stage 5 — Optional recipe photo storage, backup and recovery design

Date: 2026-11-06. Branch: `codex/phase2-meal-rotation`.

Finalized before implementing storage changes, under the owner's Stage 5 authorization. This is an implementation design, not a merge/deployment approval.

## Reference and ownership

A saved recipe may have `recipePhotoId: "rp1-<64 lowercase SHA-256 hex characters>"`. This is the digest of the processed JPEG bytes. No image data or object URL goes into localStorage. Invalid/missing references are treated as unavailable images rather than invalidating recipes or backups.

Shared memberships of the same recipe use the same reference using the existing shared-recipe membership rule and validated persistence transaction. Serving-linked recipes remain separate recipes and keep their own photos. Existing recipe fields and memberships are not migrated.

## Blob storage and image handling

Use IndexedDB version 1 with a `photos` object store keyed by the reference. Production database: `mealRotationRecipePhotosV1`; test database: `mealRotationTestRecipePhotosV1`. The test reset clears only test photos in addition to its existing test-storage reset. Ordinary backup reload/recovery events do not erase photos.

Accept user-selected JPEG, PNG, WebP and GIF files; GIF uses a still frame. Limit the input to 20 MiB and reject decoded images over 40 megapixels. Draw to a canvas with a longest edge at most 1024px, white transparency background, and JPEG encoding with progressively reduced quality/dimensions until at most 256 KiB. Canvas re-encoding removes source metadata. Unsupported formats and failed decodes report a photo-specific error without altering the recipe.

Photo operations are bounded by deadlines and IndexedDB transaction completion. Upload writes and verifies the immutable blob before saving the reference using the existing validated recipe mutation/rollback/retry path. Cancel, navigation interruption, or a stale recipe/photo selection prevents the asynchronous upload from committing a reference.

A crash before the reference save can leave an unreferenced blob, but cannot replace a valid recipe/photo reference with an incomplete write. Failed reference saves preserve the original recipe and photo and retain the existing recovery proposal/Retry Save behavior.

Photo Undo/Redo records restore only the photo reference fields on the affected recipe memberships, preserving later recipe, shopping, scheduling and cooking edits.

Replacing/removing a photo does not delete old immutable blobs. Removal detaches the reference, works without IndexedDB, and is subject to the existing recipe-save safety protections. Retention protects Undo/Redo, rotation history, failed proposals and interrupted restore. No automatic destructive garbage collection is introduced in this stage; retained unused blobs can consume quota, and subsequent failed uploads remain harmless to recipes.

## Rendering and controls

Provide attach/replace/remove controls within the internal recipe-view experience. Use optional 32px thumbnails or a subtle placeholder in Meal Groups and recipe selection/search lists. Show a larger image in the recipe viewer's content, preserving its existing tab/scroll behavior. My Rotation and Weekly Overview receive no photos. Missing blobs or database access failures show placeholders; they do not prevent reading/editing recipes, cooking, groceries or scheduling.

Release temporary object URLs when their image elements leave the DOM or the document is discarded. Preserve URLs during back/forward-cache retention.

## Optional backup extension

Keep ordinary backups at `version: 2` with the existing storage snapshot and recipe/plan fields. Add an optional root field:

```
photos: {
  version: 1,
  items: [{ id: "rp1-...", type: "image/jpeg", data: "<base64 JPEG>" }],
  missing: ["rp1-..."],
  warnings: ["..."]
}
```

Base64 is permitted only in the downloaded file, never in localStorage. Include deduplicated references used by current recipes and supported rotation-history snapshots. Recovery exports additionally collect references in readable original storage, pending writes and failed-transaction storage proposals.

Each image must meet the 256 KiB JPEG limit and digest/reference match. Limit processing to 4096 entries and 40 MiB decoded photo bytes per bundle. If export exceeds this optional budget, record omitted references explicitly in `missing` and warnings. A photo read/error/quota/unavailability failure must still produce the ordinary recipe backup or recovery download, with an explicit warning about missing photos.

## Restore ordering and safety

1. Validate the ordinary recipe/storage replacement first using the existing validation path. Invalid core data must not start photo writes.
2. Validate optional photo entries (shape, bounded base64, JPEG decoding/dimensions, digest). Ignore malformed or unreferenced image entries with warnings; do not reject otherwise valid recipes because optional photo data is damaged.
3. Stage valid images in an atomic IndexedDB transaction before the existing localStorage replacement. Content-addressed IDs cannot overwrite a different valid image: equal IDs represent the same verified bytes. Existing valid blobs remain usable if staging fails.
4. Perform the existing Phase 1 validated localStorage replacement/journal/retry flow unchanged. If it fails, older blobs remain and staged extras are harmless. If photos fail but core restore succeeds, keep recipe references and display placeholders for unavailable images, with a restore notice.

Old version-1 and version-2 backups without photos remain accepted. A backup containing references but no available image data restores fully usable recipes. Restore never clears an entire photo database or deletes existing photos as a side effect.

Recovery exports remain recipes-first. Their ordinary storage/base/proposal information is retained even if optional image collection fails. A reconstructed recipe backup may carry the same optional `photos` field when restoring a chosen recovery proposal. No new Phase 1 journal schema is required.

## Verification scope

Test real uploads and attach/replace/remove, immutable references, shared memberships, missing blobs, unavailable/failed/aborted IndexedDB, failed recipe-reference writes/Retry, interrupted uploads, backup/recovery export, malformed/missing photo data, core restore failure, legacy backups, production/test isolation and test reset. Assert recipe/scheduling/grocery/cooking state is unchanged except explicitly requested photo references. Verify mobile layout, keyboard controls, image resizing and URL cleanup. Rerun relevant existing Phase 1 and Phase 2 suites. Document browser/device limits and retained-blob quota behavior in the completion report.
