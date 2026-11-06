# Meal Rotation bug-fix handoff

Latest status: [PR #82](https://github.com/elisabethball19-netizen/meal-rotation/pull/82) now has 14 additional passing tests for the supplied Dinner Sunday record and exact IDs 537/535/22, including retention provenance and repeated Back/Forward. The full backup was not attached; unreported context is synthetic. The PR remains draft, unmerged, and undeployed. See the final section; earlier statuses are historical.

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

The follow-up branch is ready for review of this narrow correction. Do not merge or deploy automatically.

- Follow-up PR: https://github.com/elisabethball19-netizen/meal-rotation/pull/80
- Implementation commit: `a561051b50164c7961a2894a5941e6cb8e92e84f`
- Branch: `fix/skipped-empty-slot-turns`
- Share this handoff: https://github.com/elisabethball19-netizen/meal-rotation/blob/fix/skipped-empty-slot-turns/docs/meal-rotation-fix-handoff.md

The PR is open and unmerged. Mergeability is checked through the live pull-request API after the documentation update; the initial creation response may precede GitHub's mergeability calculation.

## PR #80 live follow-up: persisted-state investigation — unresolved

Latest investigated main: `cd6d070a464121154022b9a8baa2733702ee0845`, including merged PR #80. The user reports successful GitHub Pages deployment #447 and the same failure in both installed and Chrome views. Do not dismiss this as caching or conclude the prior fix works merely because fresh tests pass.

### Confirmed report and missing evidence

The user still gets Beef Bowls on Saturday and Spaghetti on Sunday, instead of Pot Roast, after Saturday was manually replaced with Pernil and Sunday skipped/left empty. Repeated Rotate Back / Rotate Meals does not correct it. The user confirmed that **Sunday shows “Empty this week” after Rotate Back**.

The actual live root cause is **not established** from source and synthetic state alone. That Sunday label indicates restoration of a temporary empty presentation, but does not reveal the hidden choice or original recipe ID behind it. No actual user backup or browser storage has been inspected.

### What the earlier tests missed

The earlier fresh scenario created both days' choices through the then-current code. Its “legacy” variation removed Sunday's `deferredMealIds` but left Saturday's newer deferral metadata and the newer temporary empty marker. This did not test a complete upgrade from older persisted state or old snapshots lacking both deferrals.

This investigation generated storage with verified pre-#79 and pre-#80 source, then loaded that committed storage before current app startup. Reloads do not reseed it. The replay performs three rounds of Rotate Meals, reload, Rotate Back, reload. It checks the original saved history before any action and preserves recipe data. The fixture files contain only synthetic data; they are not evidence of which state the user actually has.

| Persisted state loaded into current main | Results across three forward rotations | Meaning |
| --- | --- | --- |
| Ordinary pre-#80 after-cycle state, with its old saved rotation snapshot | Beef Bowls / Pot Roast each time | This common old snapshot is already handled by #80. |
| Pre-#79 after-cycle state, without either day’s newer deferral metadata | Pot Roast / Pernil each time | Proven algorithm compatibility failure: Sunday’s one recoverable deferred ID is pooled into the first day while Saturday’s older original is not known. Does not match the user’s correct Saturday. |
| Constructed legacy `cycleSlotChoices.empty: true` representation | Beef Bowls / Spaghetti first, then Beef Bowls / Pot Roast | Proven legacy-representation gap: the slot lacks a schedule-only placeholder. This does not fully match repeated live behavior or the confirmed restored empty label. It is a schema probe, not an asserted user action. |

The first two fixtures were produced by the actual old app operations, including an old rotation and reload. The third deliberately represents an empty slot with the legacy flag and is labeled as constructed. Producer Git blob hashes are checked by the committed generator. No speculative algorithm patch was made: choosing an original when its identity was lost could repeat a consumed meal or override a legitimate filter/reservation.

### Current changes and test evidence

The investigation branch adds:

- `tests/fixtures/rotation-upgrades/` with three synthetic persisted snapshots and provenance.
- `tests/generate_rotation_upgrade_fixtures.py` for reproducible generation using verified historical source.
- `tests/persisted_rotation_upgrade_browser.py`: six upgrade tests on production/test HTML, with two passes and four explicit expected failures covering the two known compatibility gaps. **Expected failure means unfixed**, not passing rotation behavior.
- `docs/rotation-diagnostics.html`, an offline, read-only backup redactor.
- `tests/rotation_diagnostics_browser.py`: passes at 360 px and 760 px; checks input/UI/download, private-content sentinels, stable aliases through old history, malformed input, no storage writes, and no network requests after the intercepted document load.
- `docs/rotation-diagnostics.md` with private collection instructions.

As a control, the existing fresh exact-sequence case still passes on both HTML files. This is recorded as a comparison, not proof of a live fix. The three older baseline suite failures previously documented remain separate; those suites were not rerun here.

`index.html` and `meal-rotation-test.html` are unchanged from latest main (Git blob SHAs `931d187647764bfe36b55a3b3980302b58b5151d` and `1818111b5f9d7b4f6aec8b70a3cf2df48d324e86`). There is no app styling, rotation, localStorage, recipe, Favorites, linked-meal, grocery, or history migration in this draft. This preserves both HTML files and their existing test-only differences without claiming the live bug resolved.

### Required next evidence

Request only an anonymized diagnostic report from the actual app state, following `docs/rotation-diagnostics.md`. It needs the affected role aliases, raw-library order, both global and per-plan overrides, Saturday/Sunday slot choices, empty-marker kind/key, deferred/avoid/exclusion fields, filters, cross-plan reservations, Favorites scores, linked/dependent relationships, and corresponding saved prior-rotation metadata. The tool retains these relationships while omitting private recipe content and using aliases/date ranks.

Prefer an export while the wrong schedule is already showing and before another Rotate Back, so its saved snapshot is present. Exporting the current empty-after-Back state is also useful; do not ask the user to manipulate their data just to generate a report. Never ask the user to clear site data, reinstall, reset history, or restore a backup.

Do not ask for the full backup or commit a user report publicly. The tool runs independently from a downloaded HTML file, does not access the app origin, and does not require merging/deploying this draft. A controlled browser test verified its UI; physical-device opening is not claimed tested, and the managed test browser's policy blocks local `file:` navigation.

### Delivery status

Draft investigation PR, awaiting actual-state evidence. **Not a resolved live bug and not ready for approval as an application fix.** Do not merge or deploy automatically. The next step is to compare the anonymized current/previous slots and identify a correction supported by that evidence, then add that persisted state to regression coverage and recheck Favorites, links, groceries, normal order, reload, and repeated Rotate Back/Rotate Meals.

Investigation PR: https://github.com/elisabethball19-netizen/meal-rotation/pull/81

Private collection instructions: https://github.com/elisabethball19-netizen/meal-rotation/blob/investigate/persisted-rotation-state/docs/rotation-diagnostics.md

Standalone offline tool (download the raw HTML and open locally; no merge/deployment required): https://github.com/elisabethball19-netizen/meal-rotation/blob/investigate/persisted-rotation-state/docs/rotation-diagnostics.html

Share this handoff with ChatGPT: https://github.com/elisabethball19-netizen/meal-rotation/blob/investigate/persisted-rotation-state/docs/meal-rotation-fix-handoff.md

## PR #82 verification and correction

PR: https://github.com/elisabethball19-netizen/meal-rotation/pull/82

Branch: `fix/hidden-weekend-rotation-state`. The PR currently targets the investigation branch (`investigate/persisted-rotation-state`); that existing stacked relationship is preserved. Nothing is merged or deployed.

### Root cause verified in the stored-state reproduction

A temporary Sunday empty/one-time slot hides the underlying automatic selection. Three persisted maps can still identify the old meal: `weekdayMealOverrides`, `cycleRetainedSlots`, and `cycleSlotChoices`. Removing the temporary marker can revive that automatic pin.

The initial PR #82 cleanup block passed its three isolated tests, but a full browser replay still returned Beef Bowls/Spaghetti. The subsequent deferred-turn logic promoted the hidden alternative into the due set, effectively undoing the cleanup. Conversely, unconditionally avoiding the hidden meal incorrectly changed a normal empty week: a legitimate Sunday Pot Roast was replaced by Pernil, even though the hidden meal had not been consumed.

The correction distinguishes an unfinished hidden manual choice from a stale automatic pin, and treats an unconsumed hidden recipe as eligible rather than consumed. It rebuilds preferences for affected temporary-slot groups using explicit deferred originals plus the existing automatic candidate order, while reserving selections belonging to other visible or hidden slots/tabs. The old metadata-poor pre-#79 case also works now: when Saturday's original identity is absent, earlier eligible queue entries are considered before assigning Sunday's one known deferred original to Saturday.

The origin of the particular retained flag in private backups (20)/(21) has not been established here. Those files were not accessible in the workspace or linked from PR #82. The new retained-pin case is built from a copy of the repository's synthetic persisted fixture and models the shape shown by the PR, not the user's actual backup. Do not claim exact live-backup verification.

### Changes

- Release hidden automatic override/pin state when its temporary slot rotates. Preserve blocked linked parents and explicit manual choices.
- Do not create an `avoidMealId` merely because a meal was hidden; it was not consumed.
- Do not promote a hidden alternative ahead of earlier eligible recipes. Prefer known deferred originals, use normal date/Favorites candidate ranking for metadata-poor fallback, and suppress already outgoing or reserved meals when distinct eligible choices exist.
- Respect reservations in other tabs even when their meals are themselves temporarily hidden.
- Preserve existing rotation handling for groups without temporary slots. The final allocator still resolves linked priorities, filters, and unavoidable-repeat fallback.
- Apply identical application edits to `index.html` and `meal-rotation-test.html`. No styling, navigation, recipe fields, storage keys, or schema versions were changed. No migration/reset or history deletion workaround was introduced.
- Expand the three pin-cleanup tests to 14 checks across both HTML files and add full persisted browser replay coverage. Remove the pre-#79 expected-failure annotations now that those historical upgrades pass.

### Tests and results

- `node --test tests/hidden-rotation-pins.test.cjs`: 14 passing checks for both HTML files, including other-plan/unassigned-group isolation, manual/self-deferred choices, and blocked linked parents.
- `hidden_rotation_replay_browser.py`: 22 passing cold-storage scenarios (11 per app), each with three forward/reload/back/reload rounds followed by three consecutive forward rotations. Covers stale retained pins, ordinary empty weeks, manual/self-deferred/deferred-manual choices, whole-day empties, Favorites, linked recipes, visible and hidden cross-tab reservations, and legacy candidate ranking. Verifies recipe data, grocery checks, permanent ingredient selections, opaque saved settings, backup validation, sandbox isolation, and no JavaScript errors. The stale-pin scenario fails on the initial PR #82 implementation with Sunday Spaghetti, and passes after the correction with Sunday Pot Roast.
- `skipped_empty_rotation_browser.py`: all 30 fixture scenarios pass on production/test HTML (24 PASS summaries).
- `skip_this_week_browser.py`: all 22 cases pass.
- `grocery_rotation_checks_browser.py`: all 16 cases pass, including fractions, repeated ingredients, linked recipes, partial/full rotation, other tabs, Undo/Rotate Back, backups, and reload.
- `deferred_rotation_gestures_browser.py`: all 6 reported cases pass, including touch tap, hold/release, cancellation, dragging, and actual native vertical scrolling.
- Relevant Stage 1 empty, one-time, and manual/linked-Idea checks pass on both HTML files. Existing weekly all-rotation with Mark Cooked enabled passes on both. Ten normal weighted Favorites cycles preserve the established sequence on both apps.
- `persisted_rotation_upgrade_browser.py`: four historical upgrade cases pass (pre-#79 and pre-#80 on both HTML files). Two constructed legacy `cycleSlotChoices.empty` probes remain explicitly expected failures, unchanged from the base; they lack the temporary `weekSchedule` marker confirmed in the user's report and are not represented as fixed.
- A source-diff comparison confirms identical application edits with only the pre-existing test-only differences preserved.

No unexpected failures or JavaScript errors occurred in the targeted passing checks. The full older Stage 1 runner also reaches an obsolete assertion requiring visible `.week-reorder-handle` controls; this fails on unchanged base too, because those controls were intentionally removed earlier. Its relevant empty/one-time/manual cases were run separately, and the current mobile gesture suite passes. The three previously documented unrelated baseline suite failures were not broadened into this fix or claimed resolved.

### Scope of verification

Testing used disposable browser contexts and copies of synthetic saved-state/history fixtures. No actual saved meal data was accessed, reset, or edited. All generated changes stay on PR #82. Its draft status remains appropriate until copies or private anonymized reports for backups (20)/(21) are available for exact-state replay; the existing collection guide remains available without requiring a merge/deployment.

Current handoff: https://github.com/elisabethball19-netizen/meal-rotation/blob/fix/hidden-weekend-rotation-state/docs/meal-rotation-fix-handoff.md

## Confirmed Sunday retention pattern: IDs 537 / 535 / 22

The user subsequently supplied these facts from a fresh live-backup analysis:

- Dinner, `Sunday::Weekend`: override `"22"`, retained pin `"22"`, choice exactly `{"mealId":"22","parentId":"","retain":true}`.
- The saved `mealRotationLastRotationBeforeV1` snapshot also retains Sunday Spaghetti (22).
- Current Saturday is Korean Slow-Cooker Beef Bowls (537); Mississippi-Style Pot Roast is 535.

The full backup file was not attached. The new regression uses these exact reported fields/IDs; unreported dates, the test Pernil ID, and Saturday snapshot details are explicitly synthetic. It is not presented as replaying the user's entire backup.

### What `retain` means and how it is written

This exact Sunday record is **automatic**, not an explicit manual choice. `manualWeekdayMealChoice` checks matching overrides/choice metadata and `substitution: true` (or the supported older manual-override rules). `retain: true` alone does not establish manual intent.

Two source paths demonstrably produce the exact reported record:

1. `applyManualWeekdayMeal` calls `preserveOtherMealPlanChoices(day, category)`. When Saturday is edited, that helper marks the other day's already displayed selection as retained. If Sunday was displaying Spaghetti, the resulting Sunday choice is exactly the supplied object. This prevents an unrelated Saturday edit from changing Sunday midweek; it does not itself explain why Spaghetti was initially selected.
2. `rotateSelectedBack` sets `retain: true` on a restored visible choice, including an automatic one, to keep the restored week stable. When restoring a temporary hidden slot, it copies that slot's prior overrides, pin, and choice metadata from the snapshot, including an existing `retain: true`.

Other existing paths preserve unselected days/other tabs or carry an existing retained flag forward. The backup contains states, not an audit log of callers, so it cannot uniquely identify which earlier action first wrote this particular flag. Do not claim a specific historical writer without more evidence.

### Intended lifetime

- Unrelated same-week edits: keep the retained selection stable.
- Rotate Back: restore the prior week faithfully, including its empty presentation and hidden pin. Back is not a global stale-data cleanup.
- Explicit forward rotation of that Sunday: expire its **automatic** current-week pin and recompute the new choice. A hidden meal was not consumed, so it must not be automatically avoided or promoted over an earlier due recipe.
- Legitimate hidden manual choices remain protected. They are not identified by `retain` alone, and no global removal of retained choices is appropriate.

It is therefore normal for the archived snapshot to continue containing Spaghetti after a correct forward rotation. The current Sunday maps should then hold Pot Roast (535), while the old snapshot remains available for a faithful Back operation.

### Added regression and results

`python tests/retained_sunday_evidence_browser.py`: **14 passing tests**, covering both production and test HTML, with no JavaScript errors.

The cold-start fixture begins with current Saturday 537 and Sunday 22. Its current and prior Sunday maps contain the exact reported retained record. Tests check:

- Back restores `Empty this week` and the prior Sunday override/pin/choice for 22.
- Forward writes 535 to the current Sunday override, retained-slot pin, and choice; the automatic `retain` flag does not carry into that new choice.
- The old snapshot still contains 22, unchanged. No history reset or destructive repair is used.
- Three repeated Back/reload/Forward/reload rounds behave consistently.
- Saturday returns to 537 when the archived Saturday represents the earlier manual Pernil substitution. A separate automatic-Saturday snapshot case follows normal rotation rather than forcing Saturday to remain frozen.
- Both individual-slot and whole-day empty markers work; the older Saturday representation without `deferredMealIds` is also covered.
- A negative control with `substitution: true` preserves the legitimate manual Sunday 22 instead of removing all retained choices.
- Actual Saturday-edit and visible-Rotate-Back actions produce the exact automatic retained object; classification remains non-manual.
- Recipe records, permanent ingredient selections, opaque saved settings, and test/production storage isolation remain intact.

`node --test tests/hidden-rotation-pins.test.cjs`: all **14 checks pass** again.

No additional runtime change was necessary: PR #82's existing correction passes this newly supplied pattern. This follow-up changes tests and documentation only. Production/test application blobs remain `d691301232f79b4267e2a20817c429ebfc508b53` / `b6d9236c25f50546b12b2635ba153bc9a208feb3`, matching the previously verified PR revision `04fe145aadfbd3515fd3e5f8c5f722a5d530c7c2`.

PR #82 remains draft and unmerged; no deployment or actual user-data edits were performed. The reported mapping is now covered, while conclusions about unreported backup contents or the precise original flag-writing event remain limited to the evidence above.
