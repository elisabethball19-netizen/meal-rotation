# Phase 1 — Data safety and reliability

Based on upstream `aae78bce7ac8048f692956ed1df5cd0a9b12733f` (November 5, 2026).

## Changes

- Full and selected Cycle Back restore scheduling choices against the current library. Current recipe content, additions, deletions, memberships and ingredient selections are retained. Historical links cannot recreate a removed relationship. Existing grocery-check and legitimate cooking-date restoration remain compatible.
- Swipe Delete uses `applyRecipeBulk`, including dependency cleanup, rotation-history pruning, occurrence cleanup, and Undo. It retains the existing scope of deleting the swiped record; it does not silently expand deletion to other shared memberships.
- A startup guard checks saved data before migrations or autosave. Unreadable records are retained and automatic writes are blocked. Recovery offers Restore Backup, Export Data for Recovery, and explicitly confirmed Start Fresh. Recovery operations stay within the current app's storage namespace.
- Ordinary storage failures show a persistent Retry Save / Export Data for Recovery warning. Pending writes stay in memory and are readable by the app. Further writes are queued until retry succeeds. Transactional bulk/backup writes retain rollback behavior; their failed proposal can be explicitly retried. A later change prevents replaying a stale proposal. The warning's controls bypass editor outside-click handling so retry cannot accidentally discard a draft.
- Existing backup validation helpers are available outside the settings renderer so startup and recovery can use the same validation. No storage keys or defaults were migrated.
- Both HTML apps share the same applicable code. The test banner, reset feature, and isolated storage wrapper remain. The offline shell version advances from v94 to v95 so an installed app can cache the corrected HTML when the update activates.

Recipe importing, grocery defaults, Favorites, plan tabs, rotation terminology, existing CSS, and normal navigation were not redesigned. Import/refresh notices only distinguish unsaved in-memory results when persistence fails.

## Verification

All tests use synthetic data and disposable Chromium contexts. No real browser profile or user data was cleared.

The following browser suites passed for both HTML apps:

```sh
python tests/phase1_data_safety_browser.py
python tests/scheduled_linked_slots_browser.py
python tests/scheduled_date_integrity_browser.py
python tests/grocery_rotation_checks_browser.py
python tests/meal_groups_bulk_safety_browser.py
python tests/shared_recipe_management_browser.py
python tests/serve_with_browser.py
python tests/recipesage_refresh_browser.py
```

The new suite covers all/selected Back after current recipe and linked-recipe edits, additions and deletions; changed link definitions; swipe deletion, history pruning and Undo; malformed primary/dependent records; denied storage reads; raw recovery downloads; rejected and valid V1/V2 backup restore; confirmed/cancelled reset; legacy/empty-library compatibility; test/production namespace isolation; injected quota and removal failures; retained pending recipes/preferences/scales/grocery checks/timers; repeated failed retries followed by successful retry/reload; transactional rollback/retry; actual editor Save failure without loss of the draft; and failed recovery writes followed by retry. A static assertion checks shared application code synchronization.

Existing suites additionally cover linked-slot allocations, retained occurrences, partial/full/legacy history, grocery quantities/checks, manual choices, shared memberships, date boundaries/DST/timezones, and IndexedDB safety-backup write/readback failures.

JavaScript syntax checks, Python compilation, and `git diff --check` passed. Recovery and warning layouts were visually inspected at 320px and had no horizontal overflow.

## Remaining risks and manual checks

- Test actual Safari/iOS and Android browsers, file selection/download, accessibility announcements/focus, browser-close warnings, and an installed PWA updating from v94. Headless Chromium cannot establish physical-device behavior.
- Pending changes remain in memory until retry succeeds or the user downloads an export. Browser/process termination can still lose in-memory changes; a close warning is best effort.
- If the browser refuses both a write and rollback, no JavaScript implementation can guarantee an atomic multi-key localStorage transaction. The app reports the failure and retains the original snapshot and pending recovery data for export/retry. Recovery exports include both current readable raw records and the original snapshot.
- Completely denied storage reads cannot export bytes the browser refuses to expose; recovery exports include the read error and any readable records.
- Cross-tab conflict resolution and recovery from actual device/browser storage corruption were not added. This phase does not change the storage format or attempt automatic repairs.
