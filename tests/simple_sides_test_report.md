# Simple sides — 2026-11-14

Base: main `0cca87dad4430b76f0e0cf8e04c120221f7668d7`.

## Changes

Simple sides are optional `simpleSides` recipe defaults and dated `simpleSideOccurrences` plan snapshots. Sides and their ingredient lines have stable IDs. They are not recipe records, legacy Serve with keywords or linked recipes. Existing records without side data continue to mean no occurrence sides; there is no defaults-on-read fallback or migration.

The existing recipe editor's Serve with area adds/edits/removes multiple simple-side defaults using its final Save/Cancel transaction. Shared logical recipe memberships receive the same defaults. New manual and regular-rotation occurrences snapshot defaults; already scheduled occurrences, including saved future occurrences, retain their own sides or absence of sides. Explicitly removing all sides persists an empty occurrence snapshot.

A scheduled meal's existing options menu has Serve with. Adding a side stages an Always / This time only choice; X returns to the intact side editor. Always stages both that occurrence and a matching/reused recipe default. The outer Save commits them together using the existing atomic recipe transaction; Cancel commits neither. Editing/removing an existing occurrence side remains local. Removing a newly staged Always side before outer Save also removes that pending default intent. Stale occurrence/default edits are rejected without selecting another occurrence.

My Rotation and Weekly Overview display compact, noninteractive simple-side names alongside existing linked names. Long names wrap with space for the existing floating controls. Generated next-week previews display sides but retain their existing read-only scheduling behavior.

Ingredient-bearing sides enter the existing grocery pipeline under the dated parent occurrence and stable side/ingredient source IDs. They use the parent's multiplier and existing week selection, combining, shopping-text and check machinery. New/changed ingredient identities start unchecked; unchanged sources retain checks. Names alone add no groceries, and side ingredients have no invented recipe instruction target. Attribution identifies the parent and side. Parent rotation/removal controls source visibility; existing Undo/Redo and Cycle Back restore occurrence snapshots and shopping state. Scaling follows the parent's existing scale state and never rewrites saved default ingredient text.

Ideas pins are centered in their existing cells alongside the text blocks. The icon, row heights, compact spacing, touch footprint, priority flags and dragging remain unchanged.

The existing isolated test HTML contains equivalent changes. Existing backup/export/restore includes the optional recipe/plan fields with validation. Offline shell version is v137. No data clearing, additional test app, dependencies or unrelated rewrites were introduced. Deferred task spacing/shadow, pin-toggle delay, grocery split-view positioning, timers and import onboarding were untouched.

## Checks actually performed

`python tests/simple_sides_browser.py` passed all six focused fixture groups for both `index.html` and `meal-rotation-test.html`:

- Blank-name rejection and trimming; multiple sides; named-only side with no groceries; existing Serve with keywords and linked recipes preserved; no extra recipe records.
- My Rotation menu access, Always / This time only, prompt X preserving the draft, outer Cancel, duplicate-default ID reuse and confirmed content, occurrence edits/removals and remove-all after reload.
- Recipe-editor defaults Save/Cancel; shared memberships; defaults inherited by new manual, rotation and preview occurrences; current and already scheduled future occurrences unchanged by default edits. Later default edits leave existing side checks intact.
- Optional ingredients scaled by the existing parent scale component; defaults unchanged; stable source IDs; unaffected checked ingredients, edited/new lines unchecked; source attribution and no instruction token; shopping-text override preserved.
- Current/next/both source selection, saved future side isolation and scaling, both-week deduplication; generated next-week menus remain read-only for occurrence-side editing.
- Side removal and parent rotation/removal with Undo/Redo, Cycle Back, restored side IDs and checks; backup round-trip; older backup without side fields; injected primary-storage failure rolls back both defaults/occurrence state and a subsequent retry succeeds.
- Narrow 320px name wrapping clear of floating controls, Weekly Overview names, pin/text center geometry, row-height comparison with the previous pin alignment, and CDP touch dragging. Screenshots reviewed.

`python tests/grocery_bulk_performance_browser.py --trials 1` completed for both apps using the existing disposable 55-recipe/1,100-ingredient fixture (840 total sources, 560 visible sources, 456 displayed recipe rows). Each select/deselect operation recorded one ledger write, one render and six contribution-generation calls, rather than row-by-row regeneration. No general performance audit was performed.

Changed modular JavaScript and service worker passed `node --check`; all inline test-app scripts passed syntax checks. Changed-function parity passed allowing only the existing isolated storage alias. `git diff --check` passed.

Physical-phone verification remains: side-editor keyboard/scrolling, nested X/confirmation taps, long-name appearance, shopping interactions and pin centering/dragging in the installed app. Browser fixtures use disposable storage; no working site data was cleared.
