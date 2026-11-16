# Issue #121 — single-group editing and supported handles

Implemented/code-checked; awaiting phone testing. Started from clean current main `edb28a0`, including the explicit deferral of the latest #120 phone feedback. No #120 follow-up or #122–#124 implementation is included.

## Changes

- Group heading/chevron expands recipes; pencil opens that group's selection bar with zero selected. Long press selects the exact pressed recipe. A settings gear in the organizing header retains the existing group rename, order, rotation-use and deletion menu. Renaming keeps the selection attached to its source; deleting the source exits cleanly.
- Bottom bar shows group/count and Groups / Status / Delete / Done. Navigation is hidden; dialogs and keyboard retain foreground priority. Groups and Status open existing controls directly, without an intermediate Edit recipes dialog.
- Above-list Select all/Deselect all explicitly tracks the initial auto-selected long-press exception. Manual selection ends that exception; partial selections can clear immediately, including 11 of 12. Empty selection and filtered scope work without allowing cross-group selection.
- Groups keeps independent Remove from source / Add to groups, unrelated memberships and Unassigned behavior. Destinations/new groups remain drafts until the final check; X cancels them. Status keeps mixed Keep existing / In Rotation / Ideas. Existing transaction validation, atomic backup writer, failure rollback, deletion names and linked-recipe protection are reused; no saved-data migration or clearing occurs.
- Visible handles only appear while organizing: source-group Ideas and existing group display ordering. They use the existing shared persistent Ideas order, pinned/unpinned boundaries and group-order writer. Handles accept touch/mouse dragging and Alt+Up/Down. In Rotation has no new handle or manual-order operation. Normal long-press shortcuts remain available outside organizing.
- Existing isolated test HTML mirrors these changes, retaining its sandbox adapter, banner and test-only features. Offline shell is `v148`.

## Focused checks

`python3 tests/group_editing_batch121_browser.py` reuses the existing disposable mobile/storage fixture and checks both `index.html` and `meal-rotation-test.html`:

- Heading expansion, pencil with zero selected, empty-action disabled states, main navigation visibility, exact real-touch long press and initial Select all exception.
- Manual second/one selection, 11/12 immediate clearing, source-group isolation, filtered Select all and clean Done.
- Direct membership picker, staged destination/new-group cancellation, copy/removal preserving other memberships, Unassigned, injected storage failure retaining the dialog/selections/data, and successful retry.
- Direct mixed status Keep existing/cancel/apply, existing deletion confirmation/names, unselected linked-recipe protection and Undo.
- Ideas handle touch drag/cancel, pin boundaries, shared membership order, unchanged selection/scheduling, Undo/Redo, group touch/keyboard reorder/cancel and persistent reload.
- Group settings/rename retaining source selection, pending new groups committed only by the final check, source-group deletion removing the toolbar/handles cleanly, and exact Undo/Redo.
- 320×800 and 740×360 toolbar/picker bounds and targets; regular/test storage sentinels and saved memberships survive reload.

Additional checks: `python3 tests/quota_backup_static.py` (modular/embedded syntax and relevant mirror checks), `bash scripts/post-merge.sh`, `node --check rotation.js`, `node --check service-worker.js`, and `git diff --check`.

Captured and visually inspected mobile screenshots for the selection header, Ideas-only handles, four-action toolbar, preserved test banner and portrait/landscape membership dialogs. Selected counts, labels and final check/X fit; the destination list scrolls independently in landscape. These are Chromium browser checks/screenshots, not physical-phone verification. Unrelated batches and viewer checks were not rerun.

## Phone checklist

1. Reopen online without clearing site data. Expand a group; tap its pencil. Check zero selected and Groups / Status / Delete / Done. Open the gear to confirm existing group controls are accessible.
2. Long-press one recipe: Select all should remain. Manually select another: Deselect all should clear immediately, including a nearly complete selection. Confirm another source group cannot join the selection.
3. Try Groups copy/remove/new-group drafts and X; preserve other memberships and Unassigned. Try mixed Status Keep existing, cancel, apply, Delete cancellation and Done. Check Undo/Redo.
4. Drag Ideas handles within each pinned/unpinned portion; verify shared order and reload. Confirm no In Rotation handle. Try group ordering and cancellation.
5. Check narrow/landscape layouts, dialog scrolling and keyboard visibility.

Phone-testing link: https://elisabethball19-netizen.github.io/meal-rotation/index.html

Actual commit/push and Pages deployment evidence are reported after publishing. Awaiting physical-phone acceptance; no physical Android/PWA verification is claimed. Never clear site data.
