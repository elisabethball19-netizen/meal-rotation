# Meal Rotation bug-fix handoff

Date: November 6, 2026

## Review links and status

- Repository: https://github.com/elisabethball19-netizen/meal-rotation
- Pull request: https://github.com/elisabethball19-netizen/meal-rotation/pull/79
- Branch: `fix/deferred-meals-touch-reordering`
- Main base commit: `fd1f014b3265f833bf187bca08dc21d70515ac22`
- Implementation commit: `1145c4b095bbc38e1d0e93ca481b812d4af2397c`
- The pull request is open. Nothing has been merged or deployed.

## Requested changes

1. Preserve rotation positions when Saturday's Korean Beef Bowls is manually replaced with Pernil, Sunday's Pot Roast is skipped, and Rotate Meals generates the following week. Korean Beef Bowls and Pot Roast should remain due.
2. Remove visible six-dot drag handles in My Rotation while preserving tap behavior, long-press recipe opening, long-press dragging to reorder, ordinary vertical scrolling, and meal-card appearance and spacing.

Scope requirements: preserve saved data and existing features; keep `index.html` and `meal-rotation-test.html` synchronized except for test-only functionality; include mobile regression coverage; use a separate bug-fix branch and PR; do not merge or deploy automatically.

## Rotation investigation and fix

Manual replacements already leave the recipe queue unchanged. However, after a manual replacement, Skip could choose the displaced original meal as its alternative. The following rotation then treated that original as an outgoing meal and consumed its turn. Skip also advanced the Favorites selection credits even though it was a schedule adjustment.

The fix records displaced automatic meal IDs in the existing slot-choice metadata (`deferredMealIds`) and excludes them from subsequent Skip alternatives for that week. Skip no longer advances Favorites credits. Explicit rotation replaces the slot-choice metadata through the existing rotation path, and existing history snapshots preserve it for Rotate Back. No migration or new storage namespace was introduced.

## Gesture implementation

The visible My Rotation reorder handles are replaced with a shared meal-row gesture recognizer:

- Tap: existing meal actions.
- Hold for 550 ms, then release without meaningful movement: existing saved-recipe opening behavior.
- Hold, then move more than 10 px: reorder within the day.
- Move more than 8 px before the hold completes: leave the gesture to scrolling.
- Small jitter during a hold does not initiate a drag.
- Cancellation prevents recipe opening.
- Drag completion suppresses unintended swipe and menu activation.
- An invisible spacer preserves the former handle's card spacing.
- Alt+ArrowUp/Down on the meal name supports keyboard reordering.

Both HTML files contain the same application changes. Existing test-only UI and isolated storage remain intact.

## Regression tests and results

New test file: `tests/deferred_rotation_gestures_browser.py`.

Passed in mobile Chromium against both HTML files:

- Requested Korean Beef Bowls / Pot Roast / Pernil sequence, with and without Favorites.
- Recipe data remains unchanged during schedule adjustments.
- Skip does not consume Favorites credits.
- Resulting selection survives reload.
- Rotate Back restores the adjusted prior schedule.
- Touch and mouse tap behavior.
- Hold, small jitter, and release; recipe opens only on release.
- Touch cancellation without recipe opening.
- Long-press drag reorder and persisted order after reload.
- Actual native vertical scrolling through Chromium CDP touch events without reordering or opening a menu.

Existing tests that passed:

- `skip_this_week_browser.py`: all 22 cases.
- `grocery_rotation_checks_browser.py`: all 16 cases, including linked meals, retained grocery checks, partial/full rotation, Undo, Rotate Back, backups, and reload.
- Bounded Favorites check: 10 ordinary weighted rotations per app, all recipes selected and no adjacent repeats. Sequence in both apps: `1, 2, 3, 4, 1, 2, 1, 3, 4, 1`.

## Existing test failures and limitations

The following failures also reproduced against unchanged main at the base commit using the same fixtures. They were left outside this targeted change:

- `rotation_no_duplicates_browser.py`: weekend expected-ID assertion.
- `weekly_manual_cycle_browser.py`: mark-cooked-disabled all-rotation expected-ID assertion.
- `cycle_linked_occurrences_browser.py`: legacy-pin independent-occurrence assertion.

The full 200-cycle Favorites suite was stopped during its long synchronous run. It is not reported as passing; the bounded 10-cycle check above passed instead.

Testing used Chromium mobile emulation, including real CDP touch dispatch. Physical-device and other-browser testing were not performed.

## Instructions for the next reviewer or ChatGPT

Review PR #79 and the implementation against the original two requests. Distinguish the passing targeted regressions from the documented pre-existing suite failures. Keep production and test HTML synchronized except for test-only functionality. Preserve existing data and keep changes targeted. Do not merge or deploy unless the user explicitly asks.

## User handoff preference

The user requests a Markdown handoff document published in this GitHub repository, followed by a link they can give to ChatGPT, for future repository work. Continue this practice when this instruction is available in the conversation or repository context. Keep documents on the relevant work branch unless the user requests another location.

## PR #79 mergeability investigation — November 6, 2026

### Actual GitHub status

The live GitHub REST pull-request response reported `mergeable: true` and `mergeable_state: "clean"` before any changes during this investigation. PR head was `022aee1baa41d8ebb8100f5221f7b930a582c6b8`; latest main remained `fd1f014b3265f833bf187bca08dc21d70515ac22`, the original branch base.

The main branch response reported `protected: false`, protection disabled, and no required status checks. The PR head had zero check runs and zero commit status entries. GitHub's combined-status endpoint returned `pending` with `total_count: 0`; that empty status response does not represent a failing check or a required check blocking this PR.

There is no current merge conflict, outdated-main divergence, branch-protection requirement, or failing GitHub check to fix. The earlier PR-creation tool returned `mergeable: false` immediately after creation. The subsequent live response is clean; a transient initial mergeability calculation is plausible, but the historical reason cannot be established from the current response. No conflict resolution, rebase, merge commit, or application-code correction was necessary.

### Scope and preservation

Only this handoff document was updated in this investigation. Both application HTML files and the targeted regression test match their published PR blob hashes exactly. Comparing the application edits against the original main snapshots confirms the same changes in both HTML files, with only the pre-existing test-only differences preserved. No styling, recipe data, storage keys, localStorage compatibility, or saved data was changed.

### Verification rerun

All requested targeted reruns passed against the unchanged PR application code:

- `deferred_rotation_gestures_browser.py`: 6 reported passing cases across both HTML files. Covers the requested meal sequence with and without Favorites, untouched recipe data/Skip credits, reload, Rotate Back, touch and mouse tap, hold/release with jitter, cancellation, long-press drag/reload, and native vertical scrolling.
- `skip_this_week_browser.py`: all 22 cases passed.
- `grocery_rotation_checks_browser.py`: all 16 cases passed, including retained grocery checks, linked behavior, partial/full rotation, Undo, Rotate Back, backups, and reload.
- Bounded normal Favorites check: 10 rotations per app passed, all four recipes selected with no adjacent repeats; both sequences were `1, 2, 3, 4, 1, 2, 1, 3, 4, 1`.
- Synchronization check: application edit blocks match between production and test HTML after normalizing the test storage name.

No new failures occurred in these reruns. The three previously documented failures (duplicate expected-ID, weekly mark-cooked-disabled expected-ID, and linked legacy-pin occurrence) remain separate baseline findings from the earlier comparison against the same unchanged main commit; they were not reclassified as passing or expanded into this investigation. The full 200-cycle Favorites suite was not rerun.

### Approval status

PR #79 is mergeable and ready for human approval of these targeted changes, with the existing baseline test limitations disclosed above. No automatic merge or deployment was performed. This document update does not change either application fix.


## Follow-up: skipped empty slot still bypasses its original — November 6, 2026

This section supersedes the earlier PR #79 delivery status: PR #79 has been merged. This correction starts from latest main `ba6f3b7d802338541ecc640cbfe001599e38a453` on a separate branch, `fix/skipped-empty-slot-turns`. No merge or deployment is authorized.

### Reproduction and root cause

The new fixture uses the reported seven-recipe order exactly: Pernil, Korean Slow-Cooker Beef Bowls, Mississippi-Style Pot Roast, Spaghetti, Tortilla Soup, Apple Braised Pork, French Dip. Saturday starts with Beef Bowls and Sunday with Pot Roast. Unlike the earlier test, Pernil precedes both originals and the recipes have distinct cooking dates.

The current main has two separate UI actions: **Skip This Meal** chooses a replacement, and **Leave Empty This Week** hides the slot. The reported empty-Sunday result is reproducible after Skip's state is hidden by an empty slot. The regression covers that combination, Skip without the empty marker, and leaving the original slot empty directly. The actions themselves were not redesigned or renamed.

On main, the empty-Sunday state contains:

- Saturday: manual Pernil, with `deferredMealIds: ["2"]` for Beef Bowls.
- Sunday: hidden Spaghetti, with `skipReplacement: true`, `deferredMealIds: ["3"]`, and `avoidMealId: "3"` for Pot Roast.
- A temporary `weekSchedule` empty marker over Sunday.

`rotationWeekEntries` represents Sunday as a schedule-only empty placeholder. Rotation's normal slot-reset loop skips schedule-only entries. Clearing the empty marker therefore revives the pinned Spaghetti choice, along with the old avoidance of Pot Roast. `deferredMealIds` was used to protect originals from Skip alternatives but was never handed back to next-week selection. Pot Roast was not physically moved to the queue tail or credited as consumed; the retained choice caused it to be bypassed.

The new regression fails against untouched main with exactly Saturday Beef Bowls / Sunday Spaghetti. Saturday's working retention is preserved by the correction.

### Correction

- Collect unconsumed deferred turns only from the slots being rotated, including underlying choices hidden by empty or one-time slots.
- Pool those IDs across the same group's rotating days and sort by their saved recipe-queue positions. Repeated skips can otherwise interleave IDs in edit order and bypass an earlier due recipe.
- Clear the expired replacement/avoidance state and return eligible deferred recipes as ordinary automatic preferences to the existing allocator. Its filters, linked priority, reservations, and duplicate prevention remain in charge.
- Exclude recipes actually advanced elsewhere in the same rotation. Ignore unavailable/Idea or filtered-out recipes rather than resurrecting them.
- Leave unselected slots and ordinary empty-week allocation without deferred edits on their existing paths.
- Recognize legacy skipped-choice metadata using `skipReplacement` / `avoidMealId` when `deferredMealIds` is absent.
- Restore the hidden slot's underlying overrides, pins, and choice metadata during Rotate Back, as well as its empty/one-time presentation. This keeps a second forward rotation consistent.

The application edits are synchronized in `index.html` and `meal-rotation-test.html`. The drag gesture implementation, styling, recipe records, storage keys, schema versions, and test-only storage differences were not changed. There is no migration and no new persistent field.

### Regression evidence

New test: `tests/skipped_empty_rotation_browser.py`.

Passed on both HTML files:

- Exact seven-meal sequence at 320 px and 360 px, including Skip plus empty, Skip alone, and direct empty.
- Saturday Beef Bowls and Sunday Pot Roast in order after rotation; unchanged unconsumed recipe data/cooked dates.
- Reload before rotation, reload after rotation, Rotate Back, hidden-choice restoration, and a second forward rotation.
- Favorites plus Mark Cooked enabled; neither schedule edits nor hidden skipped originals consume Favorites credit turns.
- Three consecutive days sharing a group, repeated manual replacements, repeated skips, whole-day empties, and distinct selections in saved queue order.
- Partial rotations preserve unselected deferrals.
- Unavailable deferred recipes, slot filters, cross-tab manual reservations, duplicate prevention, and ordinary empty-week order.
- Incoming grocery quantities reset, unrelated tab checks and ingredient selections are preserved, and Rotate Back restores the prior visible grocery state.

The new suite reports 24 PASS summaries covering 30 fixture scenarios. Its optional `--source-dir /path/to/clean-main` argument runs the same test against baseline HTML files. Running against main `ba6f3b7` reproduces the reported Sunday-Spaghetti assertion failure.

Existing checks rerun successfully:

- `deferred_rotation_gestures_browser.py`: all 6 reported cases, including mobile tap, hold/release with jitter, cancellation, drag/reload, and native vertical scrolling.
- `skip_this_week_browser.py`: all 22 cases.
- `grocery_rotation_checks_browser.py`: all 16 cases, including linked meals, retained checks, partial/full rotation, Undo, Rotate Back, backups, and reload.
- Existing Stage 1 empty and one-time meal checks: both checks pass on both files, including linked/dependent sides and history.
- Existing weekly all-rotation check with Mark Cooked enabled: passes on both files.
- Ten normal weighted Favorites rotations per app preserve the prior sequence `1, 2, 3, 4, 1, 2, 1, 3, 4, 1`.
- Final synchronization check confirms identical application edit blocks with pre-existing test-only differences preserved.

No new failures occurred in these targeted passing checks. The three older baseline failures documented above are separate findings; their full suites were not rerun or claimed fixed as part of this narrow correction. The newly reproduced failure is specifically the hidden skipped-slot regression, now passing with the correction. Testing used mobile Chromium emulation, not physical devices or every browser.

### Review status

The follow-up branch is ready for review of this narrow correction. Do not merge or deploy automatically. The pull-request link is recorded below after creation.
