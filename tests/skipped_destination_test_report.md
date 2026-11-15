# Persisted skipped Monday/Rice correction

Scope: original app and existing isolated test app. No cosmetic changes, recipe-status changes, data resets or new app pages.

## Reproduction and cause

The regular assigned-group Monday/Rice path worked. A persisted skipped **one-time** Rice occurrence reproduced both phone symptoms through the rendered dash → Select Meal → recipe picker:

- Use next recipe was disabled despite eligible Rice recipes.
- Explicit selection produced “The destination could not be filled. No meals were changed.”

The empty-slot opener classified every named-group dash as a regular assigned slot. For a one-time occurrence without that regular assignment, the scheduling handler switched to one-time scheduling and changed its category to `null`. This lost the original `Monday::Rice` empty-override identity. The transaction's destination check also retained the old regular-slot classification. The validation correctly rejected the inconsistent result and rolled it back.

## Targeted fix

- Classify the destination consistently before selection and keep the named skipped-slot key when scheduling a one-time replacement.
- Keep the original persisted empty context for validation even if a day-wide empty slot resolves to its sole assigned group.
- Use the existing eligible-candidate operation for a skipped one-time occurrence. Use next is available when a candidate exists; empty pools and reference-only groups stay disabled.
- Preserve the existing destination validation, atomic transaction, source replacement operations, recipe status, recurring assignments, cancellation and Undo/Redo.
- Mirror the changes in the existing test app. Offline shell advances to v140.

## Checks performed

`tests/skipped_destination_browser.py` was run with disposable browser contexts; focused reruns added visible-card assertions and disabled-state coverage. All case groups passed for `index.html` and `meal-rotation-test.html`:

- Persist the skipped Monday/Rice fixture, reload, long-press its actual rendered dash, open Select Meal, search/select recipes, and confirm using the real controls. No direct picker invocation.
- Unscheduled In Rotation recipe, Ideas recipe in Rice, Ideas recipe from another group, duplicate Replace, duplicate Keep both, and Use next recipe.
- Matching persisted weekday/date, relevant mask removed, Monday recipe card visible immediately and after reload, unrelated Thursday empty override and other days/groups/tabs retained.
- Recipe rotation status and last-cooked values unchanged. Session Undo restores the skipped destination and source; Redo and reload preserve the successful selection.
- Outer cancel and duplicate-dialog X leave data unchanged. No eligible source replacement and an injected storage-write failure leave source/destination unchanged; retry succeeds after restoring writes.
- Candidate-free and reference-only groups keep Use next disabled while manual Ideas selection remains available. A skipped one-time Rice occurrence also works with a separate Other group assigned to Monday.
- Control fixtures for a normally assigned skipped Rice slot and a day-wide empty slot with one assigned Rice group passed all selection cases.
- Test-app working-storage sentinel retained; no page runtime errors.

Changed functions match between regular/test apps after normalizing only the existing storage alias. JavaScript/service-worker and all inline test-app scripts passed syntax checks; `git diff --check` passed.

Remaining: physical-phone verification of the installed app after deployment/update, including the reported Monday slot and native long-press/tap behavior.
