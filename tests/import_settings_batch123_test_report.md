# Issue #123 — implemented/code-checked; awaiting physical-phone acceptance

Started from current main `72e59c8`, after inspecting root AGENTS.md, updated handoff scope, and issue #123. Changes reuse the original modular app and existing parsers, cleanup, editor, membership operations, backup writer, OCR, website readers and RecipeSage matching/safety code. No site data was cleared. Deferred grocery/card/calendar/tab/group-reorder corrections and #124 remain queued.

## Delivered behavior

- Settings has Recipes (Import recipes / Export recipes / Refresh from RecipeSage) and Backups (Save backup / Restore backup), with concise explanations distinguishing recipe-only sharing from complete data/settings backups.
- One import popup reveals fields for Website link, Photo or camera, Paste text, Recipe file, or Trello board link. File-format information appears only under Recipe file. Existing file/Trello entry points use this popup. Existing partial ingredient/step import controls in editors remain intact.
- Single imports open the ordinary editable recipe draft; imported drafts use the existing transient-record mechanism, stay out of persisted recipe data, and commit with the main Save. Cancel/Back does not add recipes. Bulk imports retain the existing group/duplicate/enrichment workflow. Unstructured text without recognized recipe sections is retained in Notes for review instead of being discarded.
- Optional Sides suggestions are unchecked until confirmed. Explicit side metadata is stronger evidence than a recipe name; contrary/uncertain metadata prevents name-based suggestions. The conservative name fallback covers clear vegetable-side preparations. Single review stages Sides membership with other memberships; bulk review adds only selected candidates. The stable built-in Sides identity is reused. Existing duplicate imports retain their prior duplicate/enrichment behavior rather than silently acquiring memberships.
- RecipeSage refresh has its own popup. Existing matching, uncertain-match skips, personal-note/customization protection, validated IndexedDB safety backup/download and atomic recipe write remain. Closing while a safety backup is pending prevents the refresh write. Successful refresh also has a normal Undo snapshot.
- Display switches use shared control/text columns and consistent spacing, with helper text aligned under the label. Inline In Rotation / Ideas radios sit directly beneath the editable time controls, with an accessible group label and no visible status heading or nested selector. The hidden existing status control remains synchronized; main Save/Cancel and existing status/schedule operations are retained.
- Import popups reuse existing focus/viewport/history handling. Back consumes the popup, asynchronous reads are invalidated on close/method changes, and cancellation restores the opened popup's source scroll position. Short-screen popup content scrolls without footer overlap; the close heading remains reachable.
- Both existing apps have equivalent changes; the test app retains isolated storage, banner and test features. Offline shell is v153.

## Verification

`python3 tests/import_settings_batch123_browser.py` — PASS on both `index.html` and `meal-rotation-test.html`, disposable intercepted origins only:

- Recipes/Backups actions and separation; Display control/label columns, on/off states and wrapped helper text.
- All five import choices; website response and OCR recognition mocked to exercise the existing downstream parser/editor paths. Actual remote-site availability, OCR accuracy, native camera/file picker and Android keyboard are not claimed verified.
- JSON, JSON-LD/RecipeSage shape, CSV, HTML, Mela single recipe, gzip Paprika single recipe, and ZIP/Paprika/Mela archive wrappers. No new formats/services were added. ZIP fixture uses stored entries; decompression code was reused unchanged.
- Single source content/notes/URL retained; no persisted imported recipe before Save; editable review, Cancel, raw-text fallback, optional Sides plus another group, shared membership, stable Sides ID, Save/Undo/Redo.
- Bulk group workflow, metadata-based side review opt-in, and uncertain main-dish metadata left unclassified. Trello board parsing reaches bulk review; Back cancels.
- Inline status pending until Save; Cancel and Back/No discard pending changes; Save/Undo/Redo use the existing operations. Unassigned status controls disabled until a membership is selected.
- RecipeSage refresh downloads a pre-write safety backup, preserves personal notes, updates matched instructions, supports Undo, and does not write recipes when closed during the awaited backup.
- Recipe export omits full storage; full backup includes it. Existing Restore backup UI reloads the complete backup into disposable storage with the same recipes after existing legacy-status normalization. The production-key sentinel survives in the isolated test app.
- Import popup Back and source return position; X, main editor Cancel, save and reload paths; no page JavaScript errors.

`node --test tests/vanilla_storage_backup.test.js` — PASS (in-memory fake storage only).
`node --check ui.js`, `node --check import-export.js`, syntax check of the isolated inline script, and `git diff --check` — PASS.

The older standalone RecipeSage refresh harness was attempted with the new popup entry; its obsolete `refreshTest` injection did not initialize, so no result is claimed for that harness. The focused fixture above covers the changed refresh entry, safety/cancellation and Undo paths without weakening old assertions.

## Visual inspection and limits

Inspected screenshots generated under `/workspace/work/screenshots123`: both apps at normal mobile width, 320×640 with app extra text size, 740×360 landscape and a 360×360 keyboard-like viewport. Included Display, inline status, Trello/text import fields, bulk Sides review, long/wrapped source text, and popup scrolling. Fixed the observed footer/content overlap and short-screen header bleed. No horizontal document overflow in narrow fixtures. These are emulated Chromium screenshots and browser-history Back tests, not physical Android/PWA acceptance.

## Phone checklist

1. Open online for v153; never clear site data. Check Recipes versus Backups and wrapped Display rows.
2. Try each import source; review a single recipe, accept/reject Sides, edit memberships and Save. Cancel/Android Back must leave recipes unchanged; confirm source return position.
3. Import a bulk file/Trello export; confirm side suggestions are optional and original quantities, instructions, notes and sources survive.
4. Change inline recipe status, Cancel/Back, then Save and Undo/Redo. Confirm other recipes and schedules remain intact.
5. Refresh from RecipeSage with an export, confirm safety backup and retained customizations; close without refreshing as a separate check. Save a full backup and verify restore only in the isolated test app.

Deployment is checked after push and reported in the delivery response. Physical-phone acceptance remains pending.
