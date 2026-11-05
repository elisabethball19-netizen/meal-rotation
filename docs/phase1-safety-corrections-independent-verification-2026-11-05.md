# Meal Rotation — Independent Verification of Phase 1 Safety Corrections

Review date: November 5, 2026.

## Verdict: DO NOT MERGE YET

Repository: https://github.com/elisabethball19-netizen/meal-rotation  
Draft PR: https://github.com/elisabethball19-netizen/meal-rotation/pull/77  
Branch: `codex/phase1-data-safety`  
Reviewed head: [0efe5d4a6fb41b51763033914f3c0c42c8152e75](https://github.com/elisabethball19-netizen/meal-rotation/tree/0efe5d4a6fb41b51763033914f3c0c42c8152e75)  
Correction implementation commit: `95490c46097e15f71b056939fd6c785b46865411`

The actual implementation and regression tests were reviewed against the six findings in [the original independent safety review](phase1-independent-safety-review-2026-11-05.md). The source used for testing was checked against GitHub. Both HTML apps were tested using synthetic data and disposable Chromium profiles.

The original defect reproductions pass, but additional tests found four remaining significant defects. The earlier completion report's readiness statement should not be treated as merge approval; these findings supersede that readiness assessment.

Repository files were not modified, committed, or merged during verification. This report is a subsequent documentation-only publication requested by the owner. No Phase 2 work was performed and no real user data was accessed or cleared.

## 1. Critical — Recovery can delete a record it cannot read

### Locations

- [index.html:1135](https://github.com/elisabethball19-netizen/meal-rotation/blob/0efe5d4a6fb41b51763033914f3c0c42c8152e75/index.html#L1135): `capture()`.
- [index.html:1197](https://github.com/elisabethball19-netizen/meal-rotation/blob/0efe5d4a6fb41b51763033914f3c0c42c8152e75/index.html#L1197): `replace()`, particularly lines 1200–1208.
- [meal-rotation-test.html:1152](https://github.com/elisabethball19-netizen/meal-rotation/blob/0efe5d4a6fb41b51763033914f3c0c42c8152e75/meal-rotation-test.html#L1152) and lines 1217–1225.

### Reproduction

1. Seed an existing recipe collection.
2. Inject a persistent `getItem` failure for `mealRotationDataV1`, while allowing writes.
3. Choose Restore Backup with a valid replacement.
4. Inspect the underlying native storage and recovery journal.

### Verified result

In both apps, the recipe record becomes absent. The journal also lacks its original contents, yet the interface says:

> Original records were restored; the recovery journal is retained. Please retry.

`capture()` returns an incomplete snapshot after a read failure. Recovery continues, overwrites the unreadable record, then rollback removes it because it was absent from that snapshot.

This is additional data loss caused by the recovery action, rather than merely the unavoidable inability to export bytes a browser refuses to return.

### Required correction

Abort replacement when the original snapshot is incomplete. Never interpret an unreadable record as nonexistent, and do not claim rollback restored records that were never captured.

**Evidence level:** Reproduced with injected persistent read failure in both apps.

## 2. High — Startup discards the journal for an incomplete replacement

### Locations

- [index.html:1211](https://github.com/elisabethball19-netizen/meal-rotation/blob/0efe5d4a6fb41b51763033914f3c0c42c8152e75/index.html#L1211): `finishStartup()`.
- [meal-rotation-test.html:1228](https://github.com/elisabethball19-netizen/meal-rotation/blob/0efe5d4a6fb41b51763033914f3c0c42c8152e75/meal-rotation-test.html#L1228).

### Reproduction

1. Seed the on-disk state of an interrupted restore:
   - Original recipe records remain.
   - Replacement grocery selections and colors have been written.
   - A valid recovery journal records the original snapshot and intended replacement.
2. Reload the app.
3. Inspect recipes, grocery selections, recovery visibility, and the journal.

### Verified result

In both apps, the old recipe remains with replacement grocery selections, recovery does not appear, and the journal is deleted.

The fixture retained the recipe name `Preserved legacy meal` while its saved selection became `backup ingredient`. The intended replacement recipe name had not been committed.

Startup checks individual record validity but never establishes that the journaled replacement completed. The protected original snapshot disappears despite mixed data remaining.

### Required correction

Detect incomplete journaled replacement before initialization can normalize records. Retain recovery information until completion is established, or provide a verified rollback/recovery path.

**Evidence level:** Reproduced in both apps using a synthetic interrupted-storage fixture representing partial multi-key replacement. A physical process-kill or real-device crash at this exact point was not established. This finding should not be described as a demonstrated physical crash reproduction.

## 3. High — Another failed recovery erases previously journaled unsaved work

### Locations

- [index.html:1202](https://github.com/elisabethball19-netizen/meal-rotation/blob/0efe5d4a6fb41b51763033914f3c0c42c8152e75/index.html#L1202): construction of `nextJournal`.
- [meal-rotation-test.html:1219](https://github.com/elisabethball19-netizen/meal-rotation/blob/0efe5d4a6fb41b51763033914f3c0c42c8152e75/meal-rotation-test.html#L1219).

### Reproduction

1. Queue an unsaved setting using an injected write failure.
2. Enter recovery and fail a restore after journal creation.
3. Verify that the journal contains the pending value.
4. Reload into recovery.
5. Fail another restore.
6. Export Data for Recovery and inspect its contents.

### Verified result

In both apps, the pending value present in the first real journal disappears from the later recovery export. The probe used a distinct pending setting value, `UNIQUE_PENDING_REAL`, to verify its presence before reload and absence after the second failed restore.

Separate seeded-journal tests also demonstrated loss of archived failed proposals and editor drafts.

The new journal preserves the previous `originalStorage`, but replaces its pending writes, failed proposals, and drafts with the current page's empty collections. For a parsed existing journal, `previousJournalRaw` is omitted, so those payloads are not retained there either.

### Required correction

Retain earlier recovery payloads across attempts, including unsuccessful attempts. Protect archived pending writes, failed proposals, and drafts independently from the original persisted-record snapshot.

**Evidence level:** Repeated failed recovery with real journal creation and a pending setting reproduced in both apps. Archived failed-proposal/draft loss was additionally verified using seeded journals.

## 4. Medium — An unrelated bulk success clears an unresolved failure

### Locations

- [index.html:6481](https://github.com/elisabethball19-netizen/meal-rotation/blob/0efe5d4a6fb41b51763033914f3c0c42c8152e75/index.html#L6481): operation identity in `applyRecipeBulk()`.
- [index.html:1332](https://github.com/elisabethball19-netizen/meal-rotation/blob/0efe5d4a6fb41b51763033914f3c0c42c8152e75/index.html#L1332): `restoreBackupStorage()`.
- [index.html:1179](https://github.com/elisabethball19-netizen/meal-rotation/blob/0efe5d4a6fb41b51763033914f3c0c42c8152e75/index.html#L1179): `resolve()`.
- Test-app equivalents: [meal-rotation-test.html:6498](https://github.com/elisabethball19-netizen/meal-rotation/blob/0efe5d4a6fb41b51763033914f3c0c42c8152e75/meal-rotation-test.html#L6498), lines 1349 and 1196.

### Reproduction

1. Fail a bulk Favorite change for recipe 1.
2. Restore storage availability.
3. Successfully add a label to recipe 1.
4. Inspect the Favorite value, save warning, and persistence unresolved state.

### Verified result

In both apps:

- Favorite remains false.
- The unrelated label is saved.
- The failure warning disappears.
- `mealPersistence.unsaved` becomes false.

Different operations share an identity derived only from selected recipe IDs. The successful label operation therefore resolves the failed Favorite operation without saving or explicitly cancelling it.

### Required correction

Distinguish operations and clear failures only after corresponding success, explicit cancellation, or demonstrated safe supersession. A successful change to another field is not sufficient.

**Evidence level:** Reproduced in both apps using the actual bulk-operation functions and injected storage failure.

## Comparison against the six original findings

| Original finding | Assessment |
| --- | --- |
| Recovery validation mismatch | Original invalid-backup case fixed; recovery remains unsafe under the additional read-failure and journal scenarios above. |
| Stale editor retry | Current-draft reproduction passes without reload. |
| Incomplete exports | Current drafts/proposals are included; repeated recovery loses archived work. |
| Premature warning dismissal | Background-save case fixed; unrelated bulk success still clears unresolved failures. |
| Structured startup validation | Weekday-color reproduction and supplied structured/legacy cases pass. |
| Asynchronous assertion race | Corrected retrying assertion passes. |

## Tests independently rerun

The following five browser suites passed across both HTML apps:

```sh
python tests/phase1_data_safety_browser.py
python tests/phase1_safety_corrections_browser.py
python tests/meal_groups_bulk_safety_browser.py
python tests/grocery_rotation_checks_browser.py
python tests/recipesage_refresh_browser.py
```

The corrections suite passed all **26 case groups**. The original Phase 1 suite also passed, including scheduling-only Cycle Back, deletion/history cleanup, recovery actions, storage failures, and editor retry scenarios.

Passing these tests does not cover the additional defects above. In particular, the supplied `recovery_journal()` test at [tests/phase1_safety_corrections_browser.py:118](https://github.com/elisabethball19-netizen/meal-rotation/blob/0efe5d4a6fb41b51763033914f3c0c42c8152e75/tests/phase1_safety_corrections_browser.py#L118) interrupts after replacement writes complete and before reload. It does not test a partial-write dataset that is individually valid, repeated recovery preserving archived pending work, or restore while original reads continue to fail.

The additional probes were temporary verification scripts outside the repository. No application or regression-test edits were made during this review.

## Limits

- Physical-device storage failures, Safari/iOS behavior, and installed-PWA updates remain unverified.
- Browser/process termination can lose in-memory changes; inaccessible bytes cannot be exported.
- These inherent limits do not justify overwriting unreadable originals, erasing already-journaled data, or clearing unresolved failures.
- The interrupted-storage finding is explicitly based on a synthetic persisted-state fixture.

## Final recommendation

**DO NOT MERGE YET.**

Correct the recovery read-failure behavior, journal retention across incomplete/repeated replacement, and failed-operation identity handling. Add regression coverage for these cases and independently verify the resulting implementation before merging.

No merge or Phase 2 work is authorized by this report.
