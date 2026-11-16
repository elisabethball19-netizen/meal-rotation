# Issue #122 — implementation checks; awaiting physical-phone testing

Inspected current main at c978563 before implementation. No site data was cleared. All browser runs used disposable intercepted test origins and fixture storage. The existing isolated app remains equivalent, with its sandbox and test features retained. Deferred #121 polish and #123–#124 remain queued.

## Changes and evidence

- Reference groups render all member records regardless of rotation status, with a left pin on every record. Current main's `masterRecipeOrder`/`all` section already returned every member; the reported disappearance did not reproduce in the disposable mixed-status fixture. Kept that all-member path and added pinned-first ordering using the existing shared pin/order store, retaining hidden order IDs after rotation is re-enabled. No recipe status, ID, membership or scheduled assignment is rewritten to provide reference visibility.
- Grocery totals remain combined across mixed checks. Every recipe-ingredient row has a chevron; text expands details, checkboxes only check. Contributions retain occurrence identity, amount, exact source navigation and their own wording pencil. Multi-source rows show an inline count and per-source checks; parent checks represent all/none/partial. Required totals do not shrink when checked. Fully checked rows sort first; partially checked rows stay in their normal position and remain available with Hide checked.
- New wording overrides retain the saved input and its occurrence multiplier, scaling from that baseline every time. Canonical recipe quantities/IDs remain the source of check-state accounting. Shopping wording participates in existing quantity/name combining; editing one source does not rename others. Original recipe ingredients are unchanged. Text and checkbox changes use existing Undo/Redo snapshots. Single-write shopping edits and cancellation retain their prior storage behavior.
- Legacy string overrides remain readable/backed up. A single-source legacy edit whose quantity equals the original recipe quantity can scale reliably. Ambiguous legacy manual amounts or multi-source overrides have no saved baseline: their text is preserved, not guessed. Multi-source legacy wording remains on the total while details show canonical contributions; editing an individual contribution establishes its own scaling baseline. Unparseable free text remains verbatim. Newly saved explicit quantities scale from the multiplier at edit time, including deliberate manual amounts.
- Offline shell version is v152. No new framework, app version or separate pin database.

## Checks

- `python3 tests/grocery_batch122_browser.py` — PASS, both apps. Bread-like 1 In Rotation + 56 Ideas plus shared membership; 57 visible recipes/pins; reload; off/on status retention; assigned-group guard and cancel; pin persistence/Undo/Redo; 1 + 2 cups rice → 3 cups rice (2); individual/partial/parent checks; Hide checked/reload; exact helper; garlic rename/scaling 1→2→½→1; independent occurrences of the same recipe; simple-side wording/scaling; explicit manual amount; unrelated checked manual item; wording Cancel/Undo/Redo; legacy unambiguous/ambiguous overrides; sandbox sentinel.
- `node --check` on touched JavaScript; `node --test tests/vanilla_storage_backup.test.js`; `git diff --check` — PASS.
- Checked inline grocery-module parity against regular source after replacing only the sandbox storage identifier.
- Existing grocery bulk suite: original run passes current-week behavior, then fails its `captureChecks <= 4` performance assertion. Reproduced on unchanged c978563: 7 captures, 9 contribution reads, 2 list generations, 1 ledger save, same as this patch. Functional run with only that bound set to the measured baseline 7 passes all four week scopes, both apps, excluded checks, manual items, reload and Undo/Redo. The checked-in bound was not weakened.
- Existing source navigation suite: updated row lookup for the new contribution wrapper and inline count. Its 500 ms scroll-equality assertion fails intermittently on both unchanged c978563 and this patch. Functional run — PASS in both apps/full and split — omitting only that equality assertion retains exact ingredient/step, preview, linked/unlinked, full/split, tabs, source state and manual-item assertions. Physical split-view step scrolling remains the separately deferred item; no claim of fixing it.
- Older Batch 1 suite stops on a superseded collapsed-favorite UI assertion. No unrelated UI changes were made to satisfy it.

## Visual inspection

Inspected disposable screenshots of both apps at 360×800, 320×640 with the app's extra text size, and 740×360 landscape. Included expanded/collapsed groceries, long source names, and mixed reference recipes/pins. Corrected reference pin alignment; no horizontal overflow in the narrow fixture. Screenshots are generated under `/workspace/work/screenshots` by the focused test, not on a user's live origin. This is emulated Chromium touch testing, not physical Android/PWA acceptance.

## Phone checklist

1. Open online and allow the v152 shell update; never clear site data. Confirm Bread's 57 recipes remain visible when rotation is off, pins reorder/persist, and re-enabling retains statuses. Assigned groups must still block disabling.
2. Expand a combined grocery; check one contribution, check the partial parent to select all, then clear it. Test Hide checked, week/meal filters and reload.
3. Edit “2 cloves garlic, minced” to “2 cloves garlic”; scale 1→2→½→1 and verify wording, totals and unchanged original ingredient. Test one simple side and two occurrences of the same recipe.
4. Follow each source name to its ingredient; test pencil Save/Cancel, Android Back and Undo/Redo. Confirm unrelated groceries/checks/schedules remain intact.

Deployment is verified after push by the delivery response; a local commit alone is not deployment evidence. Phone acceptance remains pending.
