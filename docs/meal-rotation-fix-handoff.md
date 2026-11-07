# Meal Rotation bug-fix handoff

Latest status: Batch 4 editor cleanup is on `ui/meal-editor-cleanup-batch4`, awaiting review; not merged or deployed. Main includes merged PR #94. Earlier sections below are historical.

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


## Weekday group display and picker follow-up — November 6, 2026

Pull request: https://github.com/elisabethball19-netizen/meal-rotation/pull/83

Base: latest main `4759af3b7441cac414dab6c138607707049123a7`, including merged PR #82. Branch: `fix/weekday-group-picker-display`.

### Cause and correction

Assignments were saved correctly and the planner could schedule multiple groups. My Rotation only created an empty fallback when the entire weekday had no meals, so an assigned group without an eligible meal disappeared whenever a sibling group had a meal. Rendering now adds an existing-style empty row for each missing assigned group, keeps assigned ordering and explicit display ordering, and preserves sibling rows when one group is temporarily empty. Empty rows do not become persisted recipes or queue entries.

The weekday picker now uses the existing new-group prompt and `createMealGroup` system, appends the new group in existing category order, selects it for the edited day, and refreshes the list immediately. Nested prompt focus and cancellation are handled without duplicate controls. Only the picker's “Leave Entire Day Empty This Week” control was removed; individual-meal/empty-meal options retain their existing empty-day behavior.

No rotation allocation, retention provenance, storage schema, migration, recipe data, global CSS, or navigation redesign was introduced. Production and test HTML have identical shared edits; isolated test storage and test-only UI remain intact. No actual user browser storage was accessed or reset.

### Focused verification

- `python tests/weekday_group_selection_browser.py`: four passing browser cases, covering both HTML files at 320px and 390px mobile widths. Verified multiple selections, mixed populated/empty groups, ordering, reload persistence, independent category rotation, create/cancel, automatic selection, sibling empty states, existing meal-level whole-day empty action, preserved grocery checks, no duplicate controls, no horizontal overflow, and no JavaScript page errors.
- `python tests/retained_sunday_evidence_browser.py`: 14 passing regression tests, including the persisted Sunday IDs 537/535/22, retention provenance, legitimate manual selections, and repeated Rotate Back/forward. No JavaScript page errors.
- Shared application edits were compared against main and are identical between production and test HTML after normalizing their existing storage adapter names.

These are focused checks rather than a full application-suite rerun. The previously documented unrelated main-suite failures were not reclassified or changed by this batch. GitHub Pages deployment follows the authorized merge; the user will verify the live app.



## Empty group formatting and one-time meals — November 6, 2026

Pull request: https://github.com/elisabethball19-netizen/meal-rotation/pull/84

Base: latest main `5a9363d2b4e0608debb00488d6aa310022be627e`, including PR #82 and PR #83. Branch: `fix/empty-group-one-time-meals`.

### Implementation

Empty assigned-group rows previously combined the group name and placeholder in one text string. They now use the same title-line and category-label classes as scheduled meals: message on the left, group label on the right. This also applies to “Empty this week” rows. Existing day colors and row spacing are retained; no global CSS was changed. Group labels retain the existing Meal Groups navigation action. Paired-side placeholders retain their existing chooser behavior.

Tapping an ordinary empty-group message opens “Empty group options” with Move Meal Into Rotation and Add One-Time Meal. The former preserves navigation to Meal Groups; the latter opens the existing one-time meal editor. The existing `weekSchedule` temporary slot stores the meal without creating a recipe or consuming a rotation turn. Existing temporary-meal options support changing, editing, leaving empty, or resuming the planned meal. Existing weekly overview, grocery, reload, and Rotate Back/forward behavior are reused rather than reimplemented.

No recipe records, queue algorithms, retention rules, storage keys, or backup schema were changed. Actual user browser storage was never accessed, reset, or overwritten. Production/test shared edits match exactly after normalizing their existing storage adapter names; test-only isolation remains intact.

### Focused checks

- `python tests/empty_group_once_browser.py`: four passing browser cases (production and test HTML, 320px and 390px touch viewports). Covers right-edge alignment, popup options, add/edit/remove controls, reload persistence, weekly overview inclusion, existing backup validation, no permanent recipe creation, unchanged group queue through rotation, expiration on forward rotation, restoration on Rotate Back, repeated forward rotation, preserved grocery selections, existing Meal Groups navigation, and no horizontal overflow or JavaScript page errors.
- `python tests/retained_sunday_evidence_browser.py`: all 14 existing persisted Sunday/retention/manual-selection and Back/forward regression tests passed. No JavaScript page errors.
- Both pages parsed and executed in Chromium without JavaScript errors. Only two shared application blocks changed; existing test-only storage/UI differences were preserved.

Focused testing was used as requested, without an exhaustive application-suite rerun. Previously documented unrelated main-suite failures were not changed or reclassified. Automatic merge is authorized after checks; GitHub Pages deploys from main, and the user will verify the live app.



## Compact meal options and stable group alignment — November 6, 2026

Pull request: https://github.com/elisabethball19-netizen/meal-rotation/pull/85

Base: latest main `ceeabba658f29468302e21cc318bf359d404aeaa`, including PR #82–84. Branch: `fix/compact-slot-meal-options`.

### Changes and cause

The gesture recognizer appended an invisible 44px spacer after the meal body when multiple displayed meals became reorderable. That reduced the body's width and pulled its group label inward. The spacer was removed; row-based touch reorder/hold behavior remains. Scheduled recipes, one-time meals and empty messages now share a full-width name/group grid with wrapping names and right-aligned labels. Existing weekday colors, card design and vertical spacing remain.

Empty assigned-group messages open a compact modal with Choose Meal, Auto-Populate Meal when eligible candidates exist, and a contextual Leave day/group empty action. Choose Meal delegates to the existing chooser with search, all eligible group lists, Create New Recipe and Add One-Time Meal. It does not move a recipe's permanent group. The initial menu has no separate one-time action. Paired-side placeholders use the same compact entry menu and existing eligibility rules.

Auto-Populate uses existing automatic/Favorites ranking and paired-side candidate rules, respects slot exclusions, prefers recipes not used by other scheduled slots, and retains the existing bounded duplicate fallback when all candidates are used. It uses the existing slot scheduling/grocery/Undo path, marking its choice automatic rather than a manual substitution. It does not advance queues, mark recipes cooked, or rotate another slot. Explicit empty-slot state is cleared for the selected slot only. Existing deferred/exclusion metadata is preserved.

Recipe popups show title, underlined Select/Skip/Edit actions (Skip only for an independently scheduled recipe), Last Cooked/date editor, then centered Open recipe, contextual Leave empty, and Edit grocery list buttons. Select opens the existing chooser without changing a meal. Library-only popups retain their Schedule Meal and Favorite controls. One-time popups show Select/Edit, contextual Leave empty, and Resume planned meal only if an underlying scheduled recipe exists; they omit recipe-only controls. Existing one-time editor/expiration/Rotate Back logic is reused.

Shared compact modal controls provide the existing close X and scroll-limited panel, 44px touch targets, centered wrapping full-width labels, and consistent spacing. Existing empty-week menus retain their whole-day action so the earlier preserved empty-day feature remains available.

### Focused verification

- `tests/compact_meal_options_browser.py`: four passing cases, production/test HTML at 320px and 390px touch widths. Includes right-edge alignment before/after choosing meals and with long recipe/one-time names; exact compact action lists; centered labels/touch size; chooser search and cross-group selection affecting only its target; recipe library unchanged; conditional Resume; one-time edit/reload; automatic Favorites choice; exclusions; duplicate avoidance; linked recipe activation; unchanged queues/unrelated slots; contextual single/multiple-group empty wording; real Skip action; backup validation; no JavaScript page errors or horizontal overflow.
- `tests/retained_sunday_evidence_browser.py`: all 14 persisted Sunday/manual-retention and repeated Back/forward regression tests passed.
- `tests/deferred_rotation_gestures_browser.py`: six passing scenarios across both pages, covering deferred turns with/without Favorites and tap, hold/jitter/release, drag/reload, cancellation, and native scroll.
- `tests/weekday_group_selection_browser.py`: four passing mobile cases for multiple groups, ordering, reload, group creation, independent rotation, and empty-day behavior. Existing selectors were updated for the approved labels/layout.
- `tests/empty_group_once_browser.py`: four passing mobile cases for one-time add/edit/remove, overview, persistence, expiration, repeated Back/forward, queue preservation, grocery selections, and navigation. Updated to reach one-time creation through Choose Meal and to omit Resume when no underlying planned meal exists.
- Both HTML pages parsed/executed without JavaScript errors; shared application edits were compared and match after normalizing the existing production/test storage adapter names.

Only focused checks were run, as requested. Prior unrelated full-suite failures were not reclassified. No saved user browser data was accessed or reset; no new storage keys, migration or backup schema changes were added. Automatic merge is authorized once checks pass, followed by GitHub Pages deployment and live verification by the user.



## Combined weekday and popup refinements — November 6, 2026

Pull request: https://github.com/elisabethball19-netizen/meal-rotation/pull/86

Base: latest main `a7b42b1863dae61ef171463e66192136964d40a0` (merged PR #85). Branch: `fix/weekday-touch-empty-popup-refinements`.

### Root causes and corrections

**Weekday dragging:** the recognizer counted/selectively targeted only actual recipe wrappers and ignored group-label buttons. Empty/unfilled rows never participated, so a mixed Weekend/Breakfast/Lunch card could not be reordered as a whole. All displayed weekday rows now share a drag target/key, including intentionally empty rows and one-time meals. Group labels accept the same hold/drag recognition as names; normal taps, held recipe actions, cancellation, movement thresholds, native scrolling and group management elsewhere remain intact. Display-order saving writes only existing `weekSchedule.order`, without the previous temporary-week stabilizer rewriting recipe choices. Touch tests confirm assignments, overrides, choice metadata and recipe queues remain exact and order survives reload.

**Phantom linked groups on emptying:** reproduced the whole-day helper copying a linked-only Bread entry into an independent `Sunday::Bread` empty slot. Assignments themselves were not changed, but rendering made that derived membership look like an added group. The helper now materializes only assigned/independent slots. Rendering ignores orphan linked-group empty markers left by older saves while retaining those records and rotation history. Ordinary slot emptying preserves assignments, other days and queues. Every whole-day-empty popup action has been removed; the internal compatible helper and existing saved states remain available to history/restore paths. Users can still empty all assigned slots individually.

**Corners and empty rows:** every slot now counts toward the card's final segment, rather than only populated recipes. The actual final row receives the existing bottom corner radius, with existing heading top corners, colors and styling preserved. All My Rotation empty presentations use one muted em dash; their semantic state remains available in state/accessible labels. The full row is tappable and keyboard accessible, with right-aligned group labels and the appropriate existing slot/no-group popup.

### Approved UI refinements

- Compact recipe and one-time quick actions are muted, non-underlined text with existing touch targets. Spacing below title/actions/Last Cooked and between centered full-width buttons is tightened consistently. Existing recipe, Skip, editor, Last Cooked, grocery and conditional Resume behavior is retained.
- Relevant meal-selection action buttons read **Select Meal**. Chooser headings, meal-group headings and unrelated grocery selection wording remain intact.
- Unassigned weekday popup has exactly **Select Meal** and **Choose Meal Groups**, both centered.
- Weekday meal-group picker removes Resume planned meals and its full-width creation button. An existing-style plus icon with a 44px target sits immediately before the close X. It uses the existing creation prompt, automatically selects the group and refreshes the checkbox list without closing the picker. Focus handling, ordering and scrollable list remain.
- Add/Edit One-Time Meal fits the visual viewport during keyboard resize/scroll, limits its inner scrolling panel to the available height, and restores positioning when the keyboard closes. Active fields scroll into view; Save/Cancel remain reachable. Listeners are cleaned up when the popup closes, including recovery/removal paths.

No storage schema, migration, queue allocator, rotation provenance, scaling or ingredient mapping was changed. No actual user browser data was accessed, reset or overwritten. Shared production/test application changes were compared and match after normalizing the existing isolated storage adapter names; test-only functionality remains confined to test HTML.

### Focused results

All 36 focused cases/scenarios passed, with no JavaScript page errors:

- `python tests/combined_weekday_ui_browser.py`: 4 cases (both HTML pages at 320px/390px touch widths). Actual Chromium touch dispatch covers dragging empty/regular group labels, display-only state, reload, dash/whole-row taps, mixed-card corners, icon creation/persistence, linked Bread conversion and legacy marker retention, contextual menus/centering, and simulated visual-viewport keyboard shrink/restore with reachable Save/Cancel for add/edit.
- `python tests/retained_sunday_evidence_browser.py`: all 14 persisted Sunday/retention/Rotate Back/forward regressions passed. The old visible “Empty this week” assertion now uses its preserved accessible state label; rotation expectations are unchanged.
- `python tests/deferred_rotation_gestures_browser.py`: 6 scenarios passed, preserving deferred turns/Favorites, taps, held release/jitter, drag/reload, cancellation and native page scrolling on both pages.
- `python tests/weekday_group_selection_browser.py`: 4 cases passed for group assignments/order, reload, icon create/cancel, independent rotation, sibling empties, and emptying all slots individually. Updated obsolete labels/control expectations.
- `python tests/empty_group_once_browser.py`: 4 cases passed for add/edit/remove, reload, overview, backup validation, expiration, repeated Back/forward, unchanged queues and grocery selections. Updated to Select Meal and the dash display.
- `python tests/compact_meal_options_browser.py`: 4 cases passed for long-title alignment, compact actions, chooser/search/cross-group slot selection, Auto-Populate/Favorites/exclusions/duplicates/linked recipes, reload, Skip and backup validation.

The keyboard check emulates visual-viewport geometry; it is not an on-device Android keyboard test. Touch drag uses Chromium's mobile touch event dispatch. Focused testing was used instead of a broad suite rerun; prior unrelated main-suite failures were not changed or reclassified. Automatic merge is authorized after checks; GitHub Pages deploys from main, and the user will verify the live app.



## Same-day group assignments and stable ordering — November 6, 2026

Pull request: https://github.com/elisabethball19-netizen/meal-rotation/pull/87

Base: latest main `003aecfc68b8ec75cdb3c46c8fa08563ef958ea2`, including merged PR #86. Branch: `fix/same-day-slot-assignments-order`.

### Baseline evidence and root causes

A browser replay using Weekend/Breakfast/Lunch, Beef Bowls ID 537, one-time Sandwiches, and intentionally empty Lunch reproduced bugs 2 and 3 on unchanged main:

- Selecting Beef Bowls for Lunch produced zero duplicate confirmation dialogs.
- Lunch's override was nevertheless saved as `537` while visible rows still showed only Weekend and Breakfast.
- Changing Weekend to Spaghetti ID 22 then revealed Beef Bowls in Lunch.

The duplicate filter explicitly excluded every same-day occurrence. The schedule display then deduplicated all meals by recipe ID per day, hiding an independently assigned second group. This was already committed slot state, not an uncommitted chooser variable. Those two defects explain the no-response behavior and later surprise meal.

Ordering had related slot/recipe confusion: display ranking fell back to the currently emitted meal list (which changes with temporary, hidden, linked and empty presentations), rather than assigned group identities. Full rotation also explicitly deleted saved weekday order, and Rotate Back could overwrite the current display order from its snapshot. The fresh complete-order Soup sequence did not itself reproduce the reported order jump; persisted partial/legacy orders and rotation are covered explicitly rather than assuming fresh fixtures explain every saved-state variant.

### Targeted correction

- Rank assigned groups by their stable group slot names in saved display order, with missing legacy keys filled in assignment order. Recipe IDs and one-time/occasional token differences do not move a group. Full rotation preserves display order; Rotate Back retains the current explicit order, filling a historical order only if none exists. No order schema migration is required.
- Include recipes already assigned to another same-day group in the existing duplicate confirmation. The same dialog retains No — Keep both meals; a same-day move shows the source group and Yes — Move meal. Cross-day wording and workflow remain intact.
- Preserve each independently assigned slot in display output even when another slot deliberately uses the same recipe. Existing linked-addition deduplication remains.
- A confirmed same-day move leaves its source slot explicitly empty using existing temporary-week state, preserves the original planned meal beneath it, and does not rotate a source recipe or other queues. Selecting a replacement later changes only that slot. Existing Undo/grocery reconciliation paths are reused.
- Capture the selected recipe before awaiting the confirmation. Cancel/close leaves persistent assignments unchanged and resets the chooser preview; no hidden write is made. Existing saved explicit duplicate selections are displayed rather than silently deleted, because legacy intentional and previously hidden selections cannot safely be distinguished.

No recipe, category, ingredient mapping, scaling, localStorage key, or backup schema was changed. No user browser data was accessed, reset or overwritten. Shared production/test changes match after normalizing their existing storage adapter names; isolated test features remain intact. Existing cross-day approved moves retain their previous behavior.

### Focused results

All 33 focused cases/scenarios passed, without JavaScript page errors:

- `python tests/same_day_group_assignment_browser.py`: 4 mobile cases across both HTML files at 320px/390px. Replays the requested Soup → clear → Beef duplicate → cancel → Spaghetti sequence; verifies no writes while confirmation is open/canceled and no later Lunch assignment; tests both keep-both and same-day move with one-time and regular Breakfast; unchanged recipe content/order/rotation flags; stable complete/partial display orders; reload, forward/back and backup-storage restore; linked recipe control case; isolated production-storage sentinel and backup validation.
- `python tests/retained_sunday_evidence_browser.py`: all 14 persisted Sunday/retention/manual-choice and repeated Back/forward regressions passed.
- `python tests/deferred_rotation_gestures_browser.py`: 6 scenarios passed on both pages, preserving deferred turns, Favorites, tap/hold/jitter/release, drag/reload, cancellation and native scrolling.
- Focused existing `manual_duplicate_meal_browser` subset: 9 passing scenarios. Standard cross-day yes/no/cancel on both pages, linked approved move, Undo, and partial Rotate Back. Includes grocery source checks, quantity handling, preserved unrelated progress/settings/assignments, linked recipes and rotation history.

The initial new-fixture whole-record comparison after reload was adjusted to compare recipe IDs/content/order/rotation fields, since existing startup normalization adds default fields to minimal synthetic recipes. No production normalization logic was changed. The existing unrelated full-suite failures were not reclassified; no broad suite rerun was performed. Automatic merge is authorized once basic checks pass; GitHub Pages follows main and the user will personally verify live behavior.



## Unified meal creation and consistent empty rows — November 6, 2026

Pull request: https://github.com/elisabethball19-netizen/meal-rotation/pull/88

Base: latest main `6828cfe4fef5426c12ea18e1222bfe306b4282ba` (merged PR #87). Branch: `fix/unified-meal-creation-layout`.

### Changes

- Empty group labels used spans that did not inherit the existing button-only small uppercase style. Both now receive the same explicit 12px, normal-weight, muted uppercase styling, letter spacing and right alignment. Empty rows use flex centering within their existing 40px minimum; the dash stays in the normal name column, with matching right inset and existing corner treatment. No dividers, colors, group-order or gesture changes were introduced.
- All weekday/group/change-meal selection paths use the same chooser. Its two large creation buttons and heart/Favorites filter were removed. A single existing-style plus icon beside search opens creation. Existing group lists, search, highlights, last-cooked labels, selection/save/cancel and duplicate confirmation remain intact; contextual chooser headings remain unchanged.
- The initial Create New Recipe form now contains only Meal name, an unchecked One-time meal checkbox, Recipe Group, optional Ingredients, and Save/Cancel. Checking the checkbox changes the heading to Add One-Time Meal and hides/disables the group dropdown. Each opening resets the checkbox to unchecked. No instructions, source, notes, rotation or grocery toggles are shown initially.
- Permanent creation reuses the existing atomic create-and-schedule transaction, its existing rotation default, group membership and ingredient grocery selection. Only the originating slot is scheduled; the full recipe editor remains available later for instructions and other details. One-time creation reuses the existing temporary-week save, expiration, grocery and restoration behavior and never adds a permanent recipe.
- Shared viewport fitting now scrolls only the modal's inner scrolling regions to reveal focused fields. It locks background overflow and guards page scroll while open, fits to visual-viewport keyboard resize/offsets, restores original overflow/scroll and cleans listeners on close. The same behavior applies to existing one-time add/edit and recipe-viewer Edit Recipe dialogs. Save/Cancel remain reachable; unrelated dialogs were not redesigned.

No queue allocation, manual/duplicate/linked rules, group order, recipe scaling, storage schema or backup migration changed. Actual user browser storage was not accessed, reset or replaced. Production/test shared edits were compared and match after normalizing their existing storage adapter names; test-only UI/storage remain isolated.

### Focused evidence

26 cases/scenarios passed with no JavaScript page errors:

- `python tests/unified_meal_creation_browser.py`: 4 mobile cases (production/test HTML at 320px/390px). Covers consistent label typography, vertically centered dash/corners, all chooser entry contexts, toolbar without heart/large buttons, unchecked reset and cancel without writes, permanent scheduling to another recipe group without changing sibling slots, ingredient/grocery integration, later full editor, one-time add/edit/reload/expiration/Back, backup validation, keyboard geometry with reachable controls and unchanged background scroll, and production-storage isolation.
- `python tests/retained_sunday_evidence_browser.py`: all 14 persisted Sunday/retention/Back-forward regressions passed.
- `python tests/deferred_rotation_gestures_browser.py`: all 6 deferred-turn/Favorites and tap/hold/drag/reload/native-scroll scenarios passed on both pages.
- `same_day_group_assignment_browser.run` at 390px on each page: 2 cases passed for the exact Saturday cancel/keep-both/move sequence, unchanged queues, one-time/linked controls, stable order, reload, rotation/back and backup-storage restore.

The keyboard check simulates visual-viewport geometry in mobile Chromium; actual Android browser/PWA behavior will be verified live by the user. An early assertion incorrectly treated a legitimate Breakfast Sandwiches as the expired Lunch one-time meal; it now checks the target slot. The final four-case creation run passed. Older focused tests were updated where they expected the removed chooser buttons; the historical broad initial-creation scripts with now-removed fields were not rerun. No extensive full-suite rerun was performed.

Merge and GitHub Pages deployment are authorized. Suggested live checks: confirm label/dash alignment, use plus to save a permanent meal and a one-time meal with groceries, toggle/cancel/reopen the form, and verify keyboard access to both fields and Save/Cancel in Chrome and the installed app.



## Creation guard, chooser return context and linked tabs — November 6, 2026

Pull request: https://github.com/elisabethball19-netizen/meal-rotation/pull/89

Base: latest main `479791e269d526c3fa48831b752cf9df45b43303`, including merged PR #88. Branch: `fix/creation-guard-linked-tabs`.

### Cause and changes

Creation used `editId`/`newRecipeDraftId` alone to decide whether an editor was open. A disconnected draft marker could therefore block creation without a visible form. The actual history restoration function reset `editId` but left the new-draft identity and category baseline behind. A controlled replay of group recipe creation followed by state restoration covers this lifecycle; no user backup was inspected or changed.

History restoration now clears only the transient editor identity/baseline/positioning state associated with the restored editor. A shared creation guard checks connected inline, scheduled, viewer and one-time recipe editor roots and active unsaved link editing. It keeps the warning for real open editors, including a typed unsaved title verified in the browser test. Orphaned scalar IDs without an editor are cleaned without deleting recipes or touching assignments. Group recipe creation uses the same ownership check.

The chooser retains one header plus icon beside Search, without a full-width recipe-creation button or heart filter. The centered full-width Add One-Time Meal button is restored below the header/search. The simplified plus form remains available for permanent or checkbox-selected temporary creation. Cancel/escape/outside dismissal returns to the original hidden chooser instance with its search, expansion, pending highlight and scroll state intact. Saving closes both dialogs and uses the existing atomic originating-slot scheduling path. Standalone creation entry points still work without a chooser callback.

The Display checkbox for automatically opening linked recipes is removed. Initial viewer decks and existing linked-add paths now open direct linked recipes by default while preserving explicitly confirmed checklist decks and closed-tab/saved-viewer behavior. Old saved false values remain valid/importable but cannot disable the behavior; runtime preferences read the flag as true and ordinary future preference saves normalize it. There is no startup preference migration or deletion. Settings capture/cancel no longer controls this obsolete option. Other Display controls and preference fields remain unchanged.

No rotation, group-order, duplicate confirmation, scaling, ingredient parsing, linked relationships or backup schema was changed. No actual user storage was reset or overwritten. Shared production/test application edits match after normalizing their existing storage adapter names; test-only features/storage remain isolated.

### Basic focused results

20 cases/scenarios passed without JavaScript page errors:

- `python tests/creation_guard_linked_tabs_browser.py`: 4 cases, both pages at 320px/390px. Actual draft-create/state-restore lifecycle, defensive orphan IDs, protection of a real unsaved inline edit, plus icon and centered one-time button, cancel restoring search/selection without writes, permanent originating-slot assignment, direct one-time creation, group creation/cancel, old saved false preference, automatic linked tabs, per-tab scroll restoration, tab closing without unlink/delete, single-tab bar hiding, settings control removal, other preference preservation, backup validation, and isolated production storage sentinel.
- `python tests/retained_sunday_evidence_browser.py`: all 14 persisted Sunday/retention/Back-forward regressions passed.
- `same_day_group_assignment_browser.run` at 390px on each page: 2 cases passed for Saturday cancel/keep-both/move, one-time/linked controls, unchanged queues, stable order, reload, rotation/back and backup-storage restore.

The first new test needed to return from the group-editor test context to My Rotation after history replay; no production view/navigation behavior was changed for that test setup. Existing chooser/tabs test expectations were updated for the approved restored button, cancel return context and always-on tabs; the broad historical tabs suite was not rerun. This was focused mobile Chromium testing rather than an extensive full-suite or physical-device session.

Merge and Pages deployment are authorized. Suggested live checks: create and cancel from an empty Friday/Saturday slot, confirm the same chooser returns on cancel, and open/close linked tabs after previously disabling the old setting.



## Linked-side restoration, full editor, occurrence groceries and popup heart — November 6, 2026

Pull request: https://github.com/elisabethball19-netizen/meal-rotation/pull/90 (open, awaiting approval; not merged or deployed).

Base: latest main `664d1eb935a768fc831973e135ea7437bd9741d6`, including merged PR #89. Branch: `fix/linked-restoration-full-editor-groceries`. Status: review branch only; main and GitHub Pages are unchanged.

### Implementation

**Restore hidden linked sides.** A scheduled parent's action menu lists a separate Restore [side name] action for each side actually suppressed by weekly empty-slot, exclusion or blocked-parent state. Duplicate relationship IDs do not create duplicate buttons. Restoration changes only that plan/day's relevant side placement and suppression, retains permanent links, and leaves other occurrences alone. It supports inline sides and independently assigned side groups. Restoring one of several sides does not restore the others or move an already rotating side to the front of its queue.

Weekly held grocery checks are retained in existing temporary-slot checks and an optional validated `weekSchedule.linkedGroceryChecks` map. Restoration preserves available checks and leaves newly required source lines unchecked. Old four-component held checks remain readable. A matching side-only rotation snapshot can supply older checks only when the same parent occurrence is still present and that parent was not cycled. Data that was never retained in a legacy save is not reconstructed; absent historical check evidence remains unchecked.

**One full editor for scheduled creation.** The chooser plus icon now reads Create New Meal and launches the actual Meal Groups `renderEditor`, rather than a second simplified form. The existing name/group/rotation controls, Timing, Organization, Recipe, ingredients/instructions/URL/import/link controls, Notes & Reminders and validation are reused. Creation's group label is Meal Group. The One-time meal checkbox is unchecked for every new draft; rich one-time edits reopen checked. All fields remain available for temporary meals, and their details survive save/edit/reload/expiry/Back.

The full editor runs in a keyboard-aware modal host; nested linked controls retain their normal stacking and behavior. Its private draft is filtered from persisted recipe data and captured state. Cancel removes only the draft and returns to the original chooser; a regular save reuses atomic create-and-schedule, while a one-time save uses temporary-week state with rotation forced off. Permanent multi-group memberships and the In rotation setting are honored. The originating day, group and plan tab are retained. Rich temporary linked meals use the existing placement/suppression rules and do not consume linked recipe queue turns. No full-width Create New Recipe or Add One-Time Meal button is reintroduced in the chooser.

Creation validation now tolerates newly eligible automatic candidates that remain behind an already-saved explicit empty slot, only when no prior underlying meal occupied that slot. This is a read-only validation distinction: it does not create empty flags in other meal plans or change their saved weekly empty records. It prevents a false rejection when creating a rotating meal in another tab while preserving the visible empty selections. A broader proposed mutation of unfilled slots was rejected by automatic review and was not implemented.

**Independent grocery occurrences.** The former source identity was plan/day/recipe/role and grocery collection also deduplicated by cooking context. Same-recipe, same-day groups therefore collapsed. Sources now include the scheduled group's stable identity as a fifth identity component, and collection deduplicates by that occurrence. Each duplicate contributes its own quantities and checked state; removing one leaves the others intact. Existing aggregation, fractions, unmeasured ingredients, ingredient selections, scaling context and shopping splits remain.

Compatibility: the V1 grocery ledger accepts both legacy four-component and new five-component identities. The existing group-identity registry supplies stable slot IDs lazily, so renaming a group does not change its grocery source IDs. Older unscoped checks are applied once to the stable original assignment order, not copied onto every duplicate or reassigned by display dragging. New quantities reconcile as unchecked. No global ingredient checks or selections are cleared. Existing backups without the optional metadata still import; new checks and weekly held checks are validated and round-trip with the registry.

**Scheduled-meal heart.** Saved-recipe action popups now use the existing favorite button between title and close X, including scheduled meals. It toggles immediately through existing favorite persistence, stays open, retains selected/outline appearance and leaves schedule IDs, recipe queue order and display order unchanged. Long titles wrap without overlapping the heart/X. No favorite heart is added to the meal chooser.

### Focused verification

34 distinct cases/scenarios passed across production and isolated test HTML, with no JavaScript page errors:

- `tests/remaining_meal_features_browser.py`: 4 mobile cases at 320px/390px. Legacy/scoped same-day duplicate groceries, other days/tabs, checked/unchecked quantity totals and removing one occurrence; display-order-safe legacy checks; inline and assigned-group side restoration, multiple individually hidden sides, newly added ingredient lines, old held checks and matching old snapshot checks; popup favorite persistence/long-title alignment; full-editor cancel, permanent/rich temporary creation, time/ingredients/instructions/URL/notes, temporary edit/reload/expiry/Back, backup validation, private-draft exclusion and simulated keyboard access without page scrolling.
- `tests/full_editor_occurrence_boundaries_browser.py`: 2 cases at 390px. Correct originating plan tab, permanent memberships and unchecked rotation, normal rotating creation behind another tab's explicit empty state, queue-preserving side restore, nested linked picker, temporary linked recipes/memberships, editing/restoring/expiring/Back, and no permanent draft leakage.
- `tests/retained_sunday_evidence_browser.py`: all 14 persisted Sunday/manual-retention and Back/forward regressions passed.
- `tests/deferred_rotation_gestures_browser.py`: 6 deferred-turn/Favorites and tap/hold/drag/reload/native-scroll scenarios passed.
- Focused `grocery_rotation_checks_browser` subset (`run`, `full_and_repeat`, `mixed_legacy_and_rename`, both pages at 360px): 6 passed, including mixed checked quantities, shared/fraction/unmeasured ingredients, cross-plan retention, full/partial rotations and Back, Undo, reload/backups/progress/settings, stable group rename IDs, and invalid-backup rejection without writes.
- `same_day_group_assignment_browser.run`, both pages at 390px: 2 passed for cancel/keep-both/move, independent slots, one-time/linked controls, queue/order/history, reload and backup-storage restore.
- JavaScript syntax and new Python test compilation passed. Shared application edits match after normalizing the existing production/test storage adapter names; test-only features remain isolated.

The tests use copies of synthetic and legacy-format fixtures, not the user's actual saved app data. Historical simplified-form tests are superseded by the requested full-editor workflow; no exhaustive application-suite rerun was performed and earlier unrelated main-suite failures were not reclassified.

### Phone verification and delivery

Still requires physical-phone verification: Android keyboard/scroll/focus with the full editor in Chrome and the installed app; camera/photo/OCR and live URL imports with device permissions/network; visual/touch comfort of long titles and nested editor controls; and the user's actual previously hidden-side state/check history. Simulated mobile Chromium checks do not establish those physical-device results.

No actual user data was accessed, reset, cleared or reconstructed. No recipes, settings, links or rotation history were replaced as a migration. All changes remain isolated in this PR. **Do not merge or deploy until the user approves.**

## November 7, 2026 — Multiple weekday-group removal follow-up

Status: added to PR #90; not merged or deployed. Approval remains required before merging.

### Root cause and correction

Unchecking groups cleared assigned groups and manual/retained choices but left temporary `weekSchedule.slots` records behind. The schedule renderer still appended those one-time meals, so an occupied Breakfast could remain visible after Lunch disappeared. A second path could carry a formerly day-only meal into a remaining group when its owning group was removed.

Group updates now clear removed groups' scheduled selections, manual/retained choices, and dependent-side state only for the selected day and active meal-plan tab. The chooser also reconciles old already-unchecked orphan selections when closed. Group-bound occasional meals are removed with their owning slot instead of being transferred into another group. Genuine day-only meals and intentional hidden-linked-side masks remain intact. Display-order preferences, permanent recipes, rotation membership, other days/tabs, settings, grocery selections, and rotation history are preserved. No user data was accessed or reset.

### Verification

- Reproduced the pre-fix failure against the previous PR #90 source: unchecked Breakfast retained its saved one-time Sandwiches slot.
- `tests/weekday_group_removal_browser.py`: 26 browser cases passed across both HTML files, Saturday/Sunday, one occupied plus one empty, both occupied, both empty, adopted meals, legacy orphan records, and day-only/hidden-side boundaries. Checks include actual checkbox interaction, raw saved state, reopening, reload, reassignment, scoped rotation, backup compatibility, unchanged recipes/settings/history/other day/tab, and isolated test storage.
- Two enhanced reassignment cases passed, explicitly choosing a meal after reassigning Breakfast, then checking scoped rotation.
- `tests/retained_sunday_evidence_browser.py`: 14 tests passed, preserving the weekend rotation correction and repeated Rotate Back behavior.
- `tests/remaining_meal_features_browser.py`: all 4 production/test mobile-width cases passed (320/390 px), including linked-side restoration, full editor, duplicate grocery contributions, and favorites.
- Inline JavaScript syntax checks, Python compilation, and identical shared-change checks passed. No JavaScript errors were observed in these browser runs.

The new removal matrix uses synthetic persisted fixtures at mobile width; actual saved meal data was not modified. Physical Android interaction remains for live-device verification after approval and deployment.

## November 7, 2026 — Approved merge and deployment

The user explicitly requested “Merge and deploy PR 90.” GitHub reported the PR mergeable with a clean merge state; no remote check runs or commit statuses were configured for its head. Previously recorded focused tests passed. PR #90 was merged with its exact reviewed head `43a14eda60e033625f21d765e426d7412da2b45b`. Pages deployment for the merge commit is tracked at https://github.com/elisabethball19-netizen/meal-rotation/actions/runs/42316231287. No saved app data was accessed, reset, or replaced.

## November 7, 2026 — Scheduled-occurrence recipe scaling

Status: implemented on `feature/scheduled-occurrence-scaling` from latest confirmed main `edbafbef26c9fe8048fe75b95fe96b37590f35e2`. No merge, deployment, user-data reset, or original ingredient rewrite.

### Implementation and storage

The existing presets, ingredient parser/formatter, recipe viewer and grocery aggregation are reused. The scale menu now includes a labeled decimal numeric field and Apply multiplier control. Both presets and custom entry call `setViewedRecipeScale`; zero, negative, blank, nonnumeric and nonfinite values are rejected. The custom field shows the saved multiplier; matching presets remain highlighted. Mobile viewport handling keeps the field available when the keyboard reduces the viewport.

Scales continue using `mealRotationOccurrenceScalesV1` with its version-1 envelope. New records are keyed by plan, day, recipe, linked-parent and stable group identity; their context includes `scaleGroupId`. Missing entries mean 1×. Existing four-component preset entries are accepted and apply only to their recorded group; editing that occurrence replaces its legacy entry lazily. No collection-wide migration is performed. The existing cooking-progress identity is unchanged.

`currentRecipeContext` and `definiteRecipeContext` now resolve the actual group rather than rejecting same-day recipe duplicates as ambiguous. Viewer tab identities distinguish scale occurrences. Library previews remain unscheduled and never write an occurrence multiplier. Linked recipes have their own scales, defaulting to 1×. Existing linked scheduling and grocery contribution deduplication are retained.

`reconcileCookingSchedule` and `clearCycledCookingContexts` prune scales by group-specific occurrence. Removing/replacing/rotating an occurrence cannot transfer its scale to an unrelated future selection or clear an independent duplicate's scale. Group rename and existing parent-deletion context transfers retain compatible scale records. Rotate Back retains its existing progress-reset semantics: restored meals start at 1× after their occurrence was rotated out.

### Checked grocery quantities

The existing `mealRotationGroceryOccurrenceChecksV1` boolean ledger accepts an optional `quantities` map keyed by the existing stable grocery source ID. Each entry records already checked lower/upper quantities. Old booleans and legacy ingredient checks remain readable. Scaling materializes prior checked amounts, clamps them when a requirement decreases, and leaves increases unchecked. Existing split grocery rows show checked and unchecked portions without introducing a new grocery interface. Checking/unchecking those rows updates only their represented amount.

Quantity records travel through the existing rotation reconciliation, source rename, scoped undo, temporary-slot resume and hidden-side restoration paths. Temporary masks use optional `groceryQuantities` / `linkedGroceryQuantities` alongside their existing boolean records. Backup capture already includes these app-owned records; validation accepts the compatible extensions and legacy backups without them. Ingredient normalization, unit boundaries, unmeasured text and existing quantity precision are preserved; incompatible units are not converted or summed together. Unparseable ingredient quantities remain text.

### Focused verification

- `tests/occurrence_scaling_browser.py`: four mobile production/test runs at 320px and 390px. Covers 1×/½×/1½×/2×/3×, 0.75×/2.25×, rejected inputs, exact ingredient display, same-day duplicate scales via the existing meal action workflow, different days/tabs, included tab filtering, independent linked sides, no duplicate linked grocery sources, checked increases/decreases/toggles, partial-check backup/restore, temporary empty/resume, hidden-side restoration, one-time groceries, group rename, removal/replacement, rotation/Rotate Back, reload, old scale data and standalone preview isolation. No JavaScript errors.
- `tests/remaining_meal_features_browser.py`: all four existing 320/390px production/test feature runs passed, covering linked-side restoration, full editors, duplicate groceries and favorites.
- `tests/retained_sunday_evidence_browser.py`: all 14 persisted weekend rotation tests passed.
- `tests/grocery_rotation_checks_browser.py`: all 16 existing grouped scenarios passed across both HTML files and 320/360px widths, including rotation, checked portions, linked removal, ingredient/group rename, exclusions, undo, reload and backup validation.
- Inline JavaScript syntax, Python compilation and identical shared HTML edit checks passed. Test-only storage isolation remains intact.

### Pre-existing failure and manual verification

`tests/recipe_touch_browser.py` fails because its exact-name selector finds two “Cilantro Sauce” tabs (scheduled and preview). The same strict-selector failure was reproduced against unchanged main source. This test is not reported as passing and the unrelated tab workflow was not redesigned.

Physical Android numeric keyboard behavior, installed-PWA/offline interaction and visual touch comfort require phone verification after approval. Browser coverage uses synthetic persisted fixtures, never the user's actual localStorage. Existing parsing precision and conservative handling of ambiguous ingredient text remain limitations; scaling does not infer quantities from prose. No new build system, settings page or linked-side rotation feature was introduced.

## November 7, 2026 — Batch 1 meal-editor layout

- Based on main `197edc2b3aeb5dc631f932afe7add7d2a1991d73`, including PR #91. No merge or deployment authorized.
- Shared `organizeMealEditor` now keeps meal name, memberships, rotation and timing accessible above Serve with, Linked Meals, Recipe and Notes & Reminders. Existing selection dialogs and all nested recipe/notes controls remain intact. Scoped CSS replaces nested section borders with subtle dividers.
- Top-level section preferences extend the existing `mealRotationEditorSectionsV1` record separately from recipe data. New meals begin collapsed; saved content does not auto-expand sections. Muted headings show saved Serve with, linked count, or conservative Added indicators.
- `installMealEditorLayout` bounds each inline/modal editor, gives fields their own scroll area, and keeps the unchanged Save/Delete/Cancel icons in its bottom toolbar. Visual-viewport resizing keeps fields and toolbar separate; listeners clean up when the editor is removed.
- Focused `tests/editor_batch1_browser.py`: four production/test mobile cases at 320/390px passed for creation/editing/one-time meals, membership controls, existing timing storage, all four sections/preferences/summaries, Serve with/Linked Meals dialogs, save/delete confirmation/cancel, inline/modal reduced keyboard viewport, scrolling, reload and backup validation. Existing `remaining_meal_features_browser.py`: four cases passed. No JavaScript errors. Inline JS syntax, Python compilation and shared HTML synchronization passed.
- Real Android keyboard, native dropdowns and installed-PWA touch/scroll comfort still require phone verification. No later-batch interactions, rotation/scaling/grocery algorithms, recipe data or user storage were changed.

## November 7, 2026 — Batch 2: Notes & Reminders and live indicators

- Base: latest confirmed main `3af9537e487126be60f2cd5fd3c4e5d7984b7809`. Dedicated branch `ui/meal-editor-notes-batch2`; do not merge/deploy automatically.
- Text-only indicator refresh reads current editor drafts for Serve with, Linked Meals, Recipe and Notes & Reminders. Existing selection handlers and delegated input/change events update labels without rebuilding fields, resetting expansion, or replacing the editor. Linked-dialog Cancel restores its prior indicator.
- Notes & Reminders now contains Needs Adjusting, Make Ahead and Notes subsections, using the Batch 1 chevrons/dividers and existing editor-preference record's compatible `subsections` extension. Saved content does not force expansion.
- Adjustment text controls the status; trash clears the draft text/status without a new modal. The obsolete visible checkbox is removed; an internal hidden state retains existing save/recovery handlers. Legacy marked-without-note records remain visibly identified and stay marked until explicitly cleared. Cancel discards drafts.
- Preparation tasks use direct editable rows, a plus icon, trash icons and inline number/Hours/Days controls. Existing IDs, day offsets and extra task fields are retained. Fractional days remain exact; new hour tasks add optional `hoursBefore` alongside `daysBefore:0`. Unrepresentable legacy values are shown as retained timing and kept unchanged unless edited. No destructive migration occurs.
- Necessary scheduling support subtracts hour offsets from the app's existing scheduled-date anchor; whole-day offsets retain their calendar-day behavior. Reminders remain date-based: no meal clock time, timed alarm or new scheduling system is introduced. Existing task completion identities remain unchanged.
- Passed: four focused 320/390px production/test runs for live indicators, subsection preferences, legacy statuses, adding/editing/clearing notes/tasks, exact/legacy timing, invalid timing rejection, Cancel/Save/reload/backup, one-time creation and reduced keyboard viewport; two additional final-source linked-checkbox/Cancel checks; all eight existing Make Ahead boundary/editor/rotation/backup scenarios; all four existing full-editor/linked/grocery/favorite feature runs. No JavaScript errors observed. Inline JS syntax, Python compilation and identical shared HTML edits checked.
- Real Android numeric keyboard, native unit dropdowns and installed-PWA touch/scroll comfort still need phone verification. No Batch 3, photo removal, app-wide cleanup or linked-side rotation changes were implemented.

Batch 1's separate HTTPS test preview (exact branch head `6567b39665f8f50030ba9bd303ce0fd5d2d28c2a`): https://raw.githack.com/elisabethball19-netizen/meal-rotation/6567b39665f8f50030ba9bd303ce0fd5d2d28c2a/meal-rotation-test.html . Served HTML matched the branch blob byte-for-byte. It uses the isolated test-storage namespace on a different origin from the live GitHub Pages app; it does not contain Batch 2.

## November 7, 2026 — Batch 3: editor refinements, recipe linking and meal selection

- Base: latest confirmed main `09d60e4352061bed379c48b49b6a6342eca056c8` (PR #93). Dedicated branch `ui/meal-editor-refinements-batch3`; no automatic merge or deployment.
- Every full meal-editor section and subsection now starts collapsed. Editor expansion preferences are ignored and no longer written; old settings and Meal Groups expansion remain intact.
- Make Ahead's compact plus sits immediately before its heading chevron and expands the section when adding. Hours/Days uses inline segmented buttons; stored task IDs, day/hour values and scheduling logic are unchanged. Redundant note labels are removed with accessible field names retained. Nested headings use lighter typography, indentation and subtle dividers.
- Recipe has Ingredients, Instructions and Link Steps subsections. All ingredient/instruction photo, camera and link import controls remain available. Link Steps uses one step selector and ingredient checkboxes initialized from the existing automatic matcher; edits use the existing per-step manual override tokens. Reset to automatic appears only for manual overrides. Switching steps preserves other draft overrides; the matching algorithm and viewer completion behavior are unchanged.
- Serve with uses removable chips, available suggestions and a custom-entry plus, with existing normalization preventing duplicates. Linked Meals uses the existing grouped picker inline, selected rows, compact scrolling and left chevrons. This picker alone always uses AND word matching and has no Match word order checkbox; general search preferences are untouched.
- Live draft indicators remain text-only updates. Linked draft changes participate in unsaved-change detection; editor Cancel restores saved data. No recipe data, photos, rotation algorithm, grocery calculation or occurrence-scale storage was migrated.
- Passed: four focused production/test mobile runs (320/390px), covering collapsed reopening, independent sections, header task addition, segmented timing, inline Serve with/link selection, AND search, automatic/manual step links/reset, saved overrides driving viewer ingredient completion, live indicators, Save/Cancel/reload/backups and one-time/keyboard-sized toolbar. Eight existing Make Ahead calendar/editor/rotation/backup scenarios and four existing shared-editor/linked/grocery/favorite cases passed. No JavaScript errors in these runs. Inline JavaScript syntax, Python compilation and identical shared HTML edits passed; uploaded source hashes checked.
- Existing `inline_links_browser.py` still times out when it expects `#editor [data-editor-section="recipe"]` after the recipe viewer's quick Edit Recipe action. The same missing-full-editor timeout was reproduced on unchanged main. Its obsolete Ingredient matching assertion was updated for Reset to automatic, but this suite is not reported as passing.
- Physical Android keyboard, camera/gallery/OCR imports, native file/URL flows and installed-PWA touch/scroll comfort remain phone checks. Photo/import controls were inspected and retained; real camera/OCR was not exercised. Existing matching ambiguity rules are preserved. No smarter linked-side rotation, per-occurrence side overrides or photo removal was implemented.

## November 7, 2026 — Batch 4: editor cleanup and visual consistency

- Base: latest confirmed main `7f4094156d6e76f90c4ec685a2581607021a24e1`, including PR #94. Dedicated branch `ui/meal-editor-cleanup-batch4`; do not merge/deploy automatically. No Batch 5 meal-card work or photo removal.
- Reproduced actual width overflow on unchanged main at 320px: the 240px editor scroller had 254px of content because nested sections combined 100% width with a 10px margin. Link Steps also retained legacy 10px container padding. Removed those offsets, flattened content padding and constrained flex/grid minimum widths. No overflow-x hiding was added as a workaround.
- Main headers use restrained Harvest Kitchen highlighting; aligned nested headers remain plain with subtle dividers. Editor headings respect the existing text-size factor while maintaining a smaller nested base size. Instructions is visibly Steps in the editor/viewer; property names, parsers and storage remain unchanged. Add to rotation is the editor checkbox label.
- Linked Meals search now uses the editor's rounded field/focus styling. This picker's left chevrons are standard down/up SVGs with expanded-state semantics; other picker styling remains unchanged. Blank/whitespace and unfinished draft meals are excluded from selectable options without deleting their recipe records or existing saved link IDs. Selected/available rows retain AND search and normalized alignment/wrapping.
- Editor keyboard handling uses VirtualKeyboard geometry when available and a substantial visual/layout viewport reduction fallback, with a 120px/20% threshold and zoom/orientation handling. Input focus alone or a small browser-chrome height change does not hide actions. Only this editor's Save/Delete/Cancel toolbar hides and restores; field nodes and focus are retained. Physical Android behavior remains to be checked.
- Each task has text/trash on row one and numeric lead time/Hours-Days/plus on row two. Plus inserts immediately after its own row; trash removes only its task. IDs, order and exact values remain intact. Selected unit uses a contrasting accent with aria-pressed. Permanent same-day helper text is removed; opaque legacy-timing explanations remain where needed.
- Needs Adjusting now has an independent checkbox and optional note, without trash or note-driven marking. Unchecking retains notes, including unchanged legacy whitespace; notes can be edited/cleared while unmarked. Save/dirty checks retain independent notes and legacy marked-without-note records. The editor no longer invokes the old status-and-note removal confirmation when unchecking. Viewer removal actions elsewhere are unchanged.
- Passed: four focused production/test runs at 320/390px for horizontal bounds, header alignment/hierarchy, linked field/chevrons/no blank options, hardware-focus and software-keyboard geometry, local task insertion/removal/timing, independent adjustment states/notes, live indicators, rotation label, Cancel/Save/reload/backup/one-time behavior. Eight existing Make Ahead boundary/editor/rotation/backup scenarios and four existing shared-editor/one-time/linked/grocery/favorite cases passed. No JavaScript errors observed in those runs. JS syntax, Python compilation, shared HTML equivalence and uploaded hashes checked.
- No outstanding failures in the selected final suites. Earlier batches' documented inline viewer-editor test timeout was not rerun or claimed passing here. Real Android keyboard detection, hardware-keyboard interaction, native search-clear affordance, camera/OCR and installed-PWA scrolling still need phone verification. No matching, rotation, grocery, scaling, data migration or backup-format redesign was introduced.
