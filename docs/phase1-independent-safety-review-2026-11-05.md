# Meal Rotation — Independent Phase 1 Safety Review

Review date: November 5, 2026.

**DO NOT MERGE YET.** The Cycle Back and swipe-deletion changes substantially improve safety, and eight existing regression suites passed. However, I reproduced defects in both apps involving destructive recovery, stale editor retries, and incomplete recovery exports.

Reviewed:

- Repository: https://github.com/elisabethball19-netizen/meal-rotation
- Base: `main` at `aae78bce7ac8048f692956ed1df5cd0a9b12733f`
- Review branch: `codex/phase1-data-safety` at `ecd53176cf3899004be2997daaaf1119669286df`
- Both HTML apps, the actual branch differences, implementation report (`docs/phase1-data-safety-2026-11-05.md`), original review (`docs/meal-rotation-comprehensive-review-2026-11-05.md`), persistence callers, and relevant tests.

Repository source was not modified during the review. Tests used downloaded source copies, synthetic records, and disposable Chromium contexts. No real user data was accessed. This report was subsequently added to GitHub at the owner's request; application code remains unchanged.

## Findings

### 1. Critical — Recovery can overwrite the original records with a backup that immediately fails startup validation

Locations:

- [index.html, lines 1175–1181 and 1189](https://github.com/elisabethball19-netizen/meal-rotation/blob/ecd53176cf3899004be2997daaaf1119669286df/index.html#L1175)
- `index.html`, lines 1247–1264: incomplete backup validation.
- `meal-rotation-test.html`, corresponding lines 1192–1198, 1206, and 1264–1281.

Recovery validates replacements with `validateBackupStorage()`, but that validator accepts some records that `validateStartupStorage()` rejects. For example, it accepts:

```json
"mealRotationSelectedIngredientsV1": "[]"
```

Startup requires that record to be an object.

Reproduction:

1. Seed malformed primary data and another recoverable record in an isolated profile.
2. Open Restore Backup from the recovery screen.
3. Supply a V2 backup with valid top-level groups and recipes, but the selections record above.
4. Recovery writes the backup, removes obsolete original records, and reloads.
5. Startup rejects the replacement and displays recovery again.

I reproduced this in both apps. The original raw records had been replaced. Because the page reloaded, its original in-memory snapshot was also gone; a subsequent export could no longer recover those original bytes.

**Consequence:** A recovery attempt that does not produce a usable application can destroy the information the recovery screen was protecting.

**Recommended correction:** Validate the complete normalized replacement against the same rules required for successful startup before writing anything. Preserve the pre-recovery snapshot across the replacement and successful startup, or provide an equivalent durable recovery safeguard.

**Status:** Reproduced in both apps.

### 2. High — Retry Save commits an earlier editor draft and reloads over newer typing

Locations:

- [index.html, line 1167](https://github.com/elisabethball19-netizen/meal-rotation/blob/ecd53176cf3899004be2997daaaf1119669286df/index.html#L1167): retry revision check.
- `index.html`, lines 1284–1286: captured proposal and unconditional reload.
- `meal-rotation-test.html`, lines 1184 and 1301–1303.

The retry closure retains the failed proposal. Its revision check observes storage writes, but typing in an open editor does not increment that revision.

Reproduction:

1. Open an existing recipe.
2. Change its name to `First failed draft`.
3. Inject a one-time primary-storage write failure and press Save.
4. Dismiss the error; the editor remains open.
5. Change the name to `LATEST unsaved draft`.
6. Restore storage availability and press the warning’s Retry Save.

Observed in both apps:

- The saved name became `First failed draft`.
- The page reloaded and the editor closed.
- `LATEST unsaved draft` was lost.

**Consequence:** Retry Save can discard the latest changes despite presenting itself as the recovery action for unsaved work.

**Recommended correction:** Make editor retry use the current validated draft, or track draft revisions and prevent a stale proposal from reloading over a changed editor. Successful retry should preserve any remaining unsaved editor state.

**Status:** Reproduced in both apps.

### 3. High — Export Data for Recovery omits failed transactional recipe changes

Locations:

- [index.html, line 1129](https://github.com/elisabethball19-netizen/meal-rotation/blob/ecd53176cf3899004be2997daaaf1119669286df/index.html#L1129)
- `index.html`, lines 1159–1167 and 1284–1286.
- `meal-rotation-test.html`, corresponding lines 1146, 1176–1184, and 1301–1303.

Recovery export serializes saved records, the original snapshot, and `pending`. A failed transactional proposal is held separately in a retry closure. After successful rollback, `pending` can be empty even though the failed proposal contains unsaved recipe changes.

Reproduction:

1. Edit a recipe name.
2. Fail its transactional save.
3. Dismiss the error.
4. Choose Export Data for Recovery.
5. Inspect the downloaded JSON.

The export contained neither the failed recipe name nor subsequent editor typing. I checked both names explicitly in both apps.

**Consequence:** A user can follow the warning’s export advice, close the app believing their changes are recoverable, and discover the downloaded file contains only the older state.

**Recommended correction:** Retain failed proposals as explicit serializable data and include them in the recovery export. Clearly distinguish saved state, pending ordinary writes, failed transactional proposals, and any editor draft the export promises to protect.

**Status:** Reproduced in both apps.

### 4. Medium — A background save silently dismisses the warning for a failed transactional save

Locations:

- [index.html, lines 1135–1145](https://github.com/elisabethball19-netizen/meal-rotation/blob/ecd53176cf3899004be2997daaaf1119669286df/index.html#L1135)
- `index.html`, line 3878: `pagehide` and visibility-triggered persistence.
- `meal-rotation-test.html`, lines 1152–1162 and 3895.

When `pending` is empty, an ordinary write clears `retryAction` and removes the warning. This includes background persistence of the rolled-back application state.

Reproduction:

1. Fail an editor save and dismiss the error.
2. Restore storage availability.
3. Trigger the registered `pagehide` persistence path.

The warning disappeared in both apps while the unsaved editor draft remained open. The failed proposal had not been saved.

**Consequence:** Background persistence can remove Retry Save and the persistence-related close warning without resolving the failed action. This is a misleading indication that the failure has cleared.

**Recommended correction:** Separate background writes from explicit cancellation or supersession of a failed proposal. Keep its warning until that proposal is saved, deliberately discarded, or explicitly replaced.

**Status:** Reproduced through the actual registered lifecycle handler in both apps.

### 5. Medium — Startup protection does not cover every unreadable structured record

Locations:

- [index.html, lines 1207–1218](https://github.com/elisabethball19-netizen/meal-rotation/blob/ecd53176cf3899004be2997daaaf1119669286df/index.html#L1207)
- `index.html`, lines 3471 and 3523: automatic weekday-color write.
- `meal-rotation-test.html`, lines 1224–1235, 3488, and 3540.

The generic startup parser only parses values beginning with `{` or `[`. Some structured keys lack explicit validation, so malformed values with another leading character escape the guard.

Reproduction:

1. Seed valid primary recipe data.
2. Set `mealRotationWeekdayColorsV1` to `not-json`.
3. Load the app.

Both apps opened normally and replaced the malformed value with default weekday colors. Recovery was not displayed.

**Consequence:** The stated guarantee that unreadable saved data is preserved before initialization is incomplete. The reproduced loss concerns presentation metadata, not the recipe library, which limits its severity.

**Recommended correction:** Validate known structured keys according to their expected formats, independently of their first character. Audit startup writers against that registry. Keep legitimate scalar preferences compatible.

**Status:** Reproduced in both apps. The automatic color writer predates this branch; the new guard fails to protect this path.

### 6. Low — The new recovery test contains an asynchronous assertion race

Location:

- [tests/phase1_data_safety_browser.py, lines 93–95](https://github.com/elisabethball19-netizen/meal-rotation/blob/ecd53176cf3899004be2997daaaf1119669286df/tests/phase1_data_safety_browser.py#L93)

The test reads the rejection message immediately after selecting a file. The application first awaits `file.text()`, so rejection need not have completed.

The unmodified suite stopped at line 95 in this environment. Running the recovery scenarios with an explicit wait for the rejection message passed for both apps.

**Consequence:** Flaky failure can prevent later safety scenarios from running and obscure genuine regressions.

**Recommended correction:** Wait for the expected status text using a retrying assertion before checking unchanged storage.

**Status:** Reproduced. The timing failure itself does not establish an application recovery defect.

## Cycle Back assessment

The central correction is sound: full Cycle Back now uses restoration against the current library rather than restoring an entire historical library snapshot.

Code inspection and executed tests support these improvements:

- Recipe names, ingredients, instructions, notes, custom fields, additions, and deletions survive the tested full and partial restoration paths.
- Current linked-recipe definitions survive; tested removed relationships were not recreated.
- Deleted main recipes, scheduled sides, and attachments were not resurrected.
- Ingredient selections remain intact.
- Current groups and weekday assignments are not wholesale replaced with historical copies.
- Existing suites passed for manual choices, repeated occurrences, multiple plans, legacy history, grocery checks, and partial restoration.
- Last-cooked restoration checks whether the current date still matches the cycle-generated update, protecting later manual changes in the tested cases.

Cooking progress and scaling have occurrence-specific semantics: cycling or restoring affected occurrences can reset their progress/scales. Retained occurrences are protected by the existing regression coverage. That deliberate behavior should not be described as preserving every progress or scale value indiscriminately.

I found no additional reproduced Cycle Back defect in the reviewed scenarios. More direct coverage of membership and weekday changes between cycle and restoration would still strengthen confidence.

## Swipe-deletion assessment

Swipe Delete now calls `applyRecipeBulk()`, gaining dependency cleanup, history pruning, occurrence cleanup, rollback behavior, and Undo.

The swipe and existing bulk-safety tests passed, including deletion followed by Cycle Back. This addresses the original resurrection defect.

One intentional difference remains:

- Swipe deletion removes the swiped membership record.
- Editor/global bulk deletion can expand to every shared membership after confirmation.

That distinction is documented in the implementation report and preserves the prior swipe scope. I consider it a reasonable limitation, rather than an accidental cleanup inconsistency. Its failed-save retry path still inherits findings 2–4 where applicable.

## Persistence and recovery assessment

Ordinary write failures are substantially better handled:

- Failed writes and removals generate a visible warning.
- Pending values remain readable in memory.
- Subsequent writes are deferred.
- Repeated retries can fail without clearing pending ordinary changes.
- A later successful retry persists those queued changes.
- Existing bulk rollback and RecipeSage safety-backup tests passed.

The defects are concentrated in the separate transactional-proposal lifecycle and inconsistent validation. Passing ordinary-write tests does not establish that failed editor/bulk proposals are equally recoverable.

For valid backups, I verified V1/V2 recovery restore, rejection of plainly invalid backups, confirmed/cancelled Start Fresh, and namespace preservation. Recovery write failure followed by retry also passed.

Production and test localStorage namespaces remained isolated in the executed scenarios. The test banner and dedicated Reset Test App control remain exclusive to the test app.

## Regression and caching assessment

The branch comparison shows no broad redesign or intentional changes to grocery defaults, import defaults, Favorites weighting, plan tabs, or rotation terminology. The shared application-code synchronization assertion passed.

All eight existing suites below passed:

| Suite | Result |
|---|---|
| `scheduled_linked_slots_browser.py` | Passed |
| `scheduled_date_integrity_browser.py` | Passed |
| `grocery_rotation_checks_browser.py` | Passed |
| `meal_groups_bulk_safety_browser.py` | Passed |
| `shared_recipe_management_browser.py` | Passed |
| `serve_with_browser.py` | Passed |
| `recipesage_refresh_browser.py` | Passed |
| `favorites_weighted_browser.py` | Passed |

Both apps’ inline JavaScript syntax checks passed.

The service-worker change is only the shell-version bump from `v94` to `v95`, at `service-worker.js:2`. That is appropriate. Existing behavior deliberately waits for older controlled sessions to finish before activation, so an installed app is not guaranteed to switch immediately while old windows remain open. Network-first loading and offline fallback remain unchanged.

Physical Android installation, offline update activation, and device storage exhaustion were not established by these headless tests.

## Test quality and missing coverage

The new tests meaningfully exercise behavior: native storage contents, downloads, reloads, real editor Save, swipe deletion, and Undo. They are more than implementation-name checks. The scheduling fixtures also expose internal functions, so they do not replace complete interaction testing.

I ran the remaining Phase 1 scenarios separately after the assertion race; they passed for both apps. Recovery-action scenarios also passed with an in-memory synchronization adjustment. Repository test files were unchanged.

Important missing cases include:

- Editing a draft again after its save fails, then pressing Retry Save.
- Inspecting recovery-export contents after transactional failures.
- Backgrounding the app between failed Save and retry.
- Backups accepted by restore validation but rejected by startup validation.
- Multiple different pending changes, including repeated writes to the same key.
- Interrupted multi-key retries where some writes succeed before another fails.
- Rollback itself failing, followed by additional edits and export/retry.
- Existing-data fixtures covering all known structured storage keys.
- Membership, weekday, and relationship changes between cycling and partial restoration.
- Failure handling for the test-only reset’s direct storage removals.
- Installed-PWA updates and physical Android file picker/download behavior.

Some limits are reasonable: localStorage cannot guarantee atomic multi-key commits during process termination; unreadable bytes cannot be exported if the browser denies access; in-memory changes cannot survive every Android process kill; cross-tab conflict resolution remains outside this phase. Those limits do not explain the reproduced defects above.

## Manual Android checklist

Use a disposable test installation with synthetic recipes:

- Cycle, edit recipe content, add/delete recipes, change memberships and links, then test full and selected Cycle Back.
- Swipe-delete a shared membership; test Undo, reload, and Cycle Back.
- Check mixed grocery quantities, ingredient selections, scaling, retained cooking progress, and manual last-cooked dates.
- Inject save failures; edit again, background/resume, export recovery data, retry, and reload. Verify exact saved values.
- Test malformed backups, valid V1/V2 restore, failed restore, and cancelled/confirmed Start Fresh.
- Confirm test reset and recovery never alter production sentinel records.
- Update an installed `v94` PWA, close all old app windows, reopen online, then test offline.
- Verify recovery controls, file selection, downloads, dialogs, and the Android Back button on a narrow screen.

## Final recommendation

**DO NOT MERGE YET.** Correct the destructive recovery-validation mismatch and the transactional retry/export defects before merging. The scheduling and deletion changes have encouraging regression evidence, but the new safety interface currently offers recovery actions that can lose newer work or replace recoverable originals.
