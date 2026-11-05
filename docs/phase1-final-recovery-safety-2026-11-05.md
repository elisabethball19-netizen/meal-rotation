# Meal Rotation — Final Phase 1 Recovery Safety Corrections

Date: November 5, 2026.

Repository: https://github.com/elisabethball19-netizen/meal-rotation
Branch: `codex/phase1-data-safety`
PR: https://github.com/elisabethball19-netizen/meal-rotation/pull/77
Implementation base: `9b271acec18a37a8743ab87114356ef03bd96fe9`

## Scope and status

This change addresses the four findings in [the independent verification report](phase1-safety-corrections-independent-verification-2026-11-05.md). That report and the earlier independent review are preserved unchanged as records of the implementations they reviewed.

The corrections require independent verification before merge approval. No merge, deployment, or Phase 2 work was performed. Tests used synthetic data and disposable Chromium contexts; no real user data was accessed or cleared.

No normal interface or recovery interface redesign was introduced. Grocery defaults, importing behavior, Favorites behavior, plan tabs, rotation terminology, and other unrelated functionality were not changed. The applicable inline code remains synchronized between the production and test HTML apps, with sandbox storage, banner, and reset functionality preserved.

## Corrections and safety invariants

### 1. Replacement requires a complete original snapshot

`createMealPersistence().replace()` now uses the strict `readRaw()` path and reads the existing recovery journal before any replacement or journal write. Any owned-record read, enumeration, or journal-read failure aborts replacement with “No replacement was attempted.” This applies to Restore Backup and explicitly confirmed Start Fresh.

Best-effort partial snapshots remain available for diagnostic exports, but are never used as replacement/rollback snapshots. A failed read is not treated as an absent key. Startup reads the journal independently from app-record reads so accessible earlier journal data remains exportable even when another record is denied.

### 2. Whole-replacement completion is established before initialization

Before migrations, normalization, or automatic app writes, `inspect()` validates the saved records and checks every key/value against the journal's intended replacement. Exact equality includes the absence of obsolete keys; individually valid mixed records are insufficient.

Once exact completion has been established, the app writes and reads back `replacementCommitted: true` in the existing journal before allowing initialization. This durable proof distinguishes a completed replacement from partial writes, while allowing a subsequent startup after normalization or journal-cleanup failure. Every new recovery attempt starts with `replacementCommitted: false`.

Marker write/readback failure pauses initialization in recovery. Partial replacements retain the journal and raw saved records. Journal deletion requires a verified completed replacement and successful startup validation. Existing version-1 journals without the new marker are verified by comparing their intended replacement; journals with insufficient metadata remain accessible in recovery rather than being discarded.

### 3. Repeated attempts retain earlier recovery payloads

Each new journal preserves earlier attempts in a flat `previousAttempts` array. It retains the earliest `originalStorage`, earlier before-replacement snapshots, pending writes, failed proposals, and editor drafts without replacing them with empty collections after reload.

Unparseable or unsupported old journal bytes are retained as `previousJournalRaw`. A journal write failure occurs before app-record replacement; later failed attempts leave earlier information available through Export Data for Recovery. Flat history avoids recursively embedding the entire previous encoded journal at every attempt.

As before, a successfully completed replacement followed by successful startup ends the journal lifecycle. Export recovery data before deliberately completing a restore or Start Fresh if earlier snapshots/drafts are needed afterward. These corrections protect history across unresolved and failed attempts; they are not permanent backup retention.

### 4. Unrelated operations retain separate failures

`recipeBulkOperationId()` identifies a bulk operation by its type, sorted target IDs, requested patch, and dependent-role data. Object keys are ordered consistently. A label change cannot resolve a failed Favorite change on the same recipe.

The successful corresponding mutation resolves its failure. Current-editor saves retain their existing owner identity because a successful live save safely supersedes that editor's failed draft; explicit editor cancellation remains supported. Conservative conflict guards retain older proposals for export when changed saved data prevents safe automatic replay. No generic stale snapshot replay was introduced.

## Files changed

- `index.html`
- `meal-rotation-test.html`
- `service-worker.js` — offline shell v96 → v97.
- `tests/phase1_final_recovery_safety_browser.py` — permanent regressions and boundary cases.
- `docs/phase1-final-recovery-safety-2026-11-05.md` — this completion report.

Primary functions: `createMealPersistence`, `parseJournal`, `matchesRecords`, `inspect`, `replace`, `finishStartup`, `recipeBulkOperationId`, and the operation descriptor in `applyRecipeBulk`.

## Verification

### Before/after reproductions

Before implementation, all four findings were reproduced against the unchanged branch source in both apps: **eight expected failures**.

```sh
MEAL_FINAL_SOURCE_ROOT=/tmp/phase1-final-before MEAL_FINAL_EXPECT_FAILURES=1 \
  PYTHONDONTWRITEBYTECODE=1 python tests/phase1_final_recovery_safety_browser.py
```

The source-root override selects pre-correction HTML copies; the test and fixture modules remain the current regression implementation. Each case has disposable storage.

After correction, the final recovery suite passed **16 case groups** across both apps. Beyond the four reproductions it covers denied dependent/journal reads, enumeration failure in each storage adapter, confirmed Start Fresh aborting safely, restoration after access returns, exports with another record denied, multiple archived proposals/drafts, old malformed journal bytes, journal-write failure, incomplete removals, complete empty replacements, completion-marker write/readback failures, startup normalization followed by reload, and cleanup failure/retry.

The earlier corrections suite passed all **26 case groups**, including the original six findings: rejected unsafe backups, latest-draft retry without reload, pending proposal/current-draft exports, background warning retention, structured/legacy startup validation, and asynchronous rejection timing. Its startup-interruption/journal test also passed with the durable completion marker.

### Full passing suites

```sh
python tests/phase1_final_recovery_safety_browser.py
python tests/phase1_safety_corrections_browser.py
python tests/phase1_data_safety_browser.py
python tests/grocery_rotation_checks_browser.py
python tests/scheduled_linked_slots_browser.py
python tests/meal_groups_bulk_safety_browser.py
python tests/recipesage_refresh_browser.py
```

These cover both apps, scheduling-only Cycle Back, full/selected/legacy rotation history, dependency-aware swipe and bulk deletion, Undo, deleted-recipe non-resurrection, grocery checks/quantities, rollback, current editor saves, storage failures, legacy backups, and namespace isolation.

Existing `recipe_import_audit_browser.parse_tests()` cases were additionally run separately and passed for both apps at 320px and 360px. They exercise RecipeSage and structured extraction, JSON/HTML/CSV/ZIP/Paprika/Mela/Trello inputs, ambiguity, cleanup, and legitimate wording preservation.

Inline JavaScript and service-worker syntax checks, Python syntax checks, shared-code parity, and whitespace checks passed.

### Confirmed pre-existing import-suite failures

Two full import suites were attempted and do **not** pass. Each failure was reproduced against the unchanged pre-correction branch source as well as the corrected source:

- `tests/recipe_import_audit_browser.py`: its repair scenarios call the missing `openRecipeInstructionRepair` function. The extraction/parsing portion passes separately; the full suite stops in the obsolete repair hook.
- `tests/import_cleanup_browser.py:146`: its failed reviewed-save scenario fails `state() == before`. This is an existing failure under the preceding Phase 1 persistence implementation.

These failures are not counted as passing suites. No importing implementation or unrelated test expectations were changed to make them pass. They remain issues for independent assessment and were not fixed within this recovery-only scope.

## Remaining limitations and manual checks

- Physical Safari/iOS and Android file handling, accessibility/focus, actual device storage exhaustion, abrupt process termination, and installed-PWA updates from v96 to v97 still require manual verification. Injected failures and seeded interrupted-storage fixtures do not establish physical-device behavior.
- The recovery journal/history consumes additional localStorage capacity. If it cannot be written or verified, replacement aborts before app records change. The app does not prune history from an unresolved recovery to make space.
- Completely denied reads cannot export inaccessible bytes. Restore and Start Fresh remain blocked while the required original snapshot or journal cannot be read; partial exports identify readable data rather than authorizing destructive replacement.
- localStorage does not provide atomic multi-key transactions or a filesystem durability guarantee. The journal preserves captured originals/history through tested partial-write and rollback-failure scenarios, but this phase does not guarantee survival of every browser/device storage failure.
- Successful replacement and successful startup clean up the journal; it is a recovery safeguard, not an indefinite archive. Diagnostic recovery exports are not normal automatically restorable backups and omit file binaries.
- Cross-tab conflict resolution is outside Phase 1. The durable marker records a verified commit by this app; it is not a general tamper-proof or multi-writer transaction log.
- Unrelated successful changes may cause an older failed bulk proposal to require repeating the original action rather than automatic replay. Its warning and exported proposal remain instead of being silently discarded.
- The two baseline import-suite failures above remain unresolved.

## Handoff

The four requested corrections are implemented with permanent regression coverage. This report describes implementation verification, not an independent merge approval. Review the actual code and tests independently, including the remaining limitations and baseline test failures, before deciding whether to merge PR #77.
