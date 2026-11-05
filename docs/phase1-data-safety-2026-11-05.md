# Phase 1 — Data safety and reliability

Based on upstream `aae78bce7ac8048f692956ed1df5cd0a9b12733f` (November 5, 2026). Safety corrections below are based on branch head `19dc5ff6af82d67f65729d150c4a0337bb4a33cb` and the independent review of `ecd53176cf3899004be2997daaaf1119669286df`.

Status: implemented for independent verification on `codex/phase1-data-safety`; **not approval to merge**. No merge, deployment, or Phase 2 work was performed.

## Changes

- Full and selected Cycle Back restore scheduling choices against the current library. Current recipe content, additions, deletions, memberships and ingredient selections are retained. Historical links cannot recreate a removed relationship. Existing grocery-check and legitimate cooking-date restoration remain compatible.
- Swipe Delete uses `applyRecipeBulk`, including dependency cleanup, rotation-history pruning, occurrence cleanup, and Undo. It retains the existing scope of deleting the swiped record; it does not silently expand deletion to other shared memberships.
- A startup guard checks saved data before migrations or autosave. Unreadable records are retained and automatic writes are blocked. Recovery offers Restore Backup, Export Data for Recovery, and explicitly confirmed Start Fresh. Recovery operations stay within the current app's storage namespace.
- Ordinary storage failures show a persistent Retry Save / Export Data for Recovery warning. Pending writes stay in memory and are readable by the app. Further writes are queued until retry succeeds. Transactional bulk/backup writes retain rollback behavior; their failed proposal can be explicitly retried. A later change prevents replaying a stale proposal. The warning's controls bypass editor outside-click handling so retry cannot accidentally discard a draft.
- Existing backup validation helpers are available outside the settings renderer so startup and recovery can use the same validation. No storage keys or defaults were migrated.
- Both HTML apps share the same applicable code. The test banner, reset feature, and isolated storage wrapper remain. The offline shell version advances from v94 through v95 to v96 so an installed app can cache the corrected HTML when the update activates.

Recipe importing, grocery defaults, Favorites, plan tabs, rotation terminology, existing CSS, and normal navigation were not redesigned. Import/refresh notices only distinguish unsaved in-memory results when persistence fails.

## Independent safety review corrections

1. **Backup recovery validation.** `validateSavedRecords()` is shared by startup and backup validation. Recovery validates before touching storage, writes and reads back a namespace-local `mealRotationRecoveryJournalV1` containing the original raw records, verifies the replacement, and retains that journal across reload until application startup and viewer restoration succeed. Write, readback, startup, or rollback failures retain the original journal for recovery export; insufficient space for the journal aborts replacement before changing any other key. The journal is excluded from normal backups and ordinary key iteration.
2. **Current editor retries.** Failed operations have explicit identities, proposals, and editor owners. Retry invokes the live editor's current save handler rather than replaying an earlier snapshot. Editor retries do not reload. Open nested dialogs must be finished or cancelled first. Save also checks whether the raw draft changed while an asynchronous confirmation was open. Bulk retries re-execute against current in-memory data; conflicting or missing-owner operations remain available for export instead of replaying stale data.
3. **Complete, labelled recovery exports.** Recovery format v2 distinguishes readable persisted `storage`, `originalStorage`, pending `unsaved` writes/removals, serializable `failedTransactions` (including proposed records and original bases), current raw `editorDrafts`, unreadable key names, and any recovery journal. Draft providers include recipe fields, raw ingredient/instruction text and step links, memberships, Serve with/make-ahead settings, pending ingredient imports, nested dialog controls, and viewer link selections. Files are described by metadata rather than embedded. Capturing a draft does not validate or save it. Runtime recovery blocks replacement over dirty drafts and provides explicitly confirmed draft cancellation.
4. **Unresolved warnings.** Ordinary/background persistence and unrelated successful transactions no longer dismiss failed-operation warnings. Each failure resolves only after that operation succeeds, its editor explicitly discards it, or the same operation is safely superseded. Pending write repairs and journal-cleanup failures also retain warnings and close protection.
5. **Structured startup records.** An explicit registry validates known structured records and their expected types, including weekday/category colors, preferences, grocery exclusions, group state, legacy filters, and dynamic rotation-ID lists. Legitimate optional null preferences, scalar settings, numeric/string legacy IDs, and opaque extension records remain compatible. Invalid records enter recovery before migrations/default persistence.
6. **Test timing.** The invalid-backup assertion in `tests/phase1_data_safety_browser.py` now waits for the asynchronous rejection before comparing storage. Recovery rollback assertions additionally require the durable journal while verifying original records. The group-order suite now expects malformed structured JSON to enter recovery without rewriting its bytes, then repairs only its disposable fixture to continue legacy restore checks.

Applicable code is synchronized in `index.html` and `meal-rotation-test.html`; sandbox-only controls and storage isolation remain intact. Service-worker shell version is v96. The independent review document is preserved unchanged.

## Verification

All tests use synthetic data and disposable Chromium contexts. No real browser profile or user data was cleared.

The following browser suites passed for both HTML apps after the corrections:

```sh
python tests/phase1_data_safety_browser.py
python tests/phase1_safety_corrections_browser.py
python tests/group_order_browser.py
python tests/favorite_display_browser.py
python tests/recipe_cooking_timer_browser.py
python tests/scheduled_linked_slots_browser.py
python tests/scheduled_date_integrity_browser.py
python tests/grocery_rotation_checks_browser.py
python tests/meal_groups_bulk_safety_browser.py
python tests/shared_recipe_management_browser.py
python tests/serve_with_browser.py
python tests/recipesage_refresh_browser.py
```

The original Phase 1 suite covers all/selected Back after current recipe and linked-recipe edits, additions and deletions; changed link definitions; swipe deletion, history pruning and Undo; malformed primary/dependent records; denied storage reads; raw recovery downloads; rejected and valid V1/V2 backup restore; confirmed/cancelled reset; legacy/empty-library compatibility; test/production namespace isolation; injected quota and removal failures; retained pending recipes/preferences/scales/grocery checks/timers; repeated failed retries followed by successful retry/reload; transactional rollback/retry; actual editor Save failure without loss of the draft; and failed recovery writes followed by retry. A static assertion checks shared application code synchronization.

The independent-review suite has 13 case groups per app (26 passes), including the five original defect reproductions. Those five tests were also run against the previous implementation with `MEAL_SAFETY_SOURCE_ROOT=/tmp/phase1-safety-before MEAL_SAFETY_EXPECT_BASELINE_FAILURES=1`: all ten app/defect combinations failed as expected. Expanded cases cover malformed structured types, legitimate legacy/scalar/null data, recovery journal creation/readback/reload/startup failure/cleanup, current-draft retries and asynchronous confirmation, background pagehide, cancellation/supersession, bulk conflicts, multiple failed proposals, nested raw drafts and Set serialization, interrupted retries/rollback, denied reads, and runtime recovery over unsaved work.

Existing suites additionally cover linked-slot allocations, retained occurrences, partial/full/legacy history, grocery quantities/checks, manual choices, shared memberships, date boundaries/DST/timezones, and IndexedDB safety-backup write/readback failures.

JavaScript syntax checks, Python compilation, and `git diff --check` passed. Recovery and warning layouts were visually inspected at 320px and had no horizontal overflow.

## Remaining risks and manual checks

- Test actual Safari/iOS and Android browsers, file selection/download, accessibility announcements/focus, browser-close warnings, and an installed PWA updating from v94 or v95. Headless Chromium cannot establish physical-device behavior.
- Recovery exports are diagnostic JSON, not a normal backup that the Restore Backup control can import automatically. Pending proposals and raw drafts require recovery/re-entry; file contents are not embedded.
- Pending changes remain in memory until retry succeeds or the user downloads an export. Browser/process termination can still lose in-memory changes; a close warning is best effort.
- If the browser refuses both a write and rollback, no JavaScript implementation can guarantee an atomic multi-key localStorage transaction. The app reports the failure and retains the original snapshot and pending recovery data for export/retry. Recovery exports include both current readable raw records and the original snapshot.
- Completely denied storage reads cannot export bytes the browser refuses to expose; recovery exports include the read error and any readable records.
- Cross-tab conflict resolution and recovery from actual device/browser storage corruption were not added. This phase does not change the storage format or attempt automatic repairs.
