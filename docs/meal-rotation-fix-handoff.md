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
