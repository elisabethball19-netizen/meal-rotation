# Quota recovery and version-2 backup verification

## Verification after merging main-branch changes

Repeated the static checks, all eight quota/backup scenario groups, all 16 final
recovery-safety checks, and the focused legacy recovery/parser compatibility
checks against the resolved code; all passed. Also ran
`python3 tests/modular_browser_smoke.py --flows` against the running app: forced
quota reset made zero writes, full backup restore retained all tested data after
reload, and no JavaScript errors were observed. The smoke test now opens the
explicit Restore backup control rather than treating Import recipes as restore.
The normal first-use screen was confirmed in a fresh preview screenshot.

All data was synthetic, in disposable Chromium contexts on intercepted test
origins. Real user storage was never cleared or imported into.

## Passing checks

- `python3 tests/quota_backup_static.py`
  - JavaScript syntax in changed modules, embedded app and diagnostics.
  - Changed recovery/normalization/import/settings behavior matches the
    embedded test app after accounting for its isolated storage adapter.
  - Every JSON chooser, including diagnostics and multi-format pickers, has
    the wildcard accept option; journal writes are centralized.
  - `git diff --check`.
- `PLAYWRIGHT_NODEJS_PATH=$(command -v node) python3 tests/quota_backup_browser.py`
  - Eight scenario groups passed across modular and embedded apps.
  - Start Fresh at injected quota with huge valid and malformed legacy journals:
    no writes before deletion; all owned keys/journal removed, unrelated and
    other-app namespaces retained, clean app initialized.
  - Cancelled reset does nothing. Throwing and silently ignored deletion fail
    honestly without resuming saving.
  - Journal count/size bounds, newest-attempt retention, retry once with oldest
    history removed, persistent quota, essential snapshot too large to fit,
    startup completion/cleanup/restart without a recovery loop. Sample bounded
    journal: 42,247 UTF-8 bytes, six previous attempts.
  - Actual recipe picker imports V2 `meals` with string/array `cat` plus direct
    tags without restoring plan data. Existing wrappers and Trello still parse.
  - Full restore/reload imports two plans, weekday categories/overrides, cooking
    progress tokens, checked ingredients, grocery selections, colors/settings.
    Top-level values override conflicting storage; storage-only and top-level-only
    V2 backups work. Actual export downloads restore/reload successfully.
  - Invalid backup rejected without storage changes. Optional journal quota does
    not block valid restore; failed restore retains complete in-memory recovery
    export and can retry successfully without stale journal metadata.
- `PLAYWRIGHT_NODEJS_PATH=$(command -v node) python3 tests/run_browser_regressions.py tests/phase1_final_recovery_safety_browser.py`
  - All 16 checks passed (eight per app). Expectations were updated only where
    the requested deletion-only reset and optional journaling change the contract.
- `PLAYWRIGHT_NODEJS_PATH=$(command -v node) python3 tests/run_browser_regressions.py --backup-compatibility`
  - Existing `phase1_data_safety_browser.recovery` and `recovery_actions` passed
    for both apps: frozen invalid records, exact raw recovery exports, denied
    reads, malformed non-destructive rejection, legacy V1 and V2 recovery.
  - Existing `recipe_import_audit_browser.parse_tests` passed at 320 and 360
    pixels for both apps: JSON, HTML, CSV, ZIP, Paprika, Mela, Trello, JSON-LD
    graphs, instruction references, structured precedence, ambiguity handling,
    metadata cleanup, and legitimate instruction wording.
- Restarted the existing static-server workflow. Preview screenshot showed the
  normal first-use recipe dialog and meal plans, not a recovery error.
  App assets returned HTTP 200; no browser-console errors were reported.

## Broader legacy-suite limitations

Attempted the full `phase1_safety_corrections_browser.py` suite: `unsafe_backup`
passed, then `latest_editor_retry` stopped because its fixture fills `#name`,
which is now a hidden editor field. This is an outdated editor test assumption,
not a quota/backup failure. The complete suite was not verified.

Attempted the full `recipe_import_audit_browser.py` suite: parser checks passed,
then `repair_tests` stopped because its fixture calls the no-longer-defined
`openRecipeInstructionRepair`. The complete repair suite was not verified.
The focused parser checks above were run independently for both apps and widths.

## Startup dependency correction

Real modular execution exposed two pre-existing load-order hazards that blocked
reliable fresh initialization: the ingredient-fraction migration was called
before its UI-file definition, and the import MutationObserver could resume
before saved meals were initialized. Existing migration helpers were moved into
the earlier state module without changing their behavior, and import resumption
now waits until document parsing completes. No styling, framework, application
dependencies, build step, or storage schema was introduced.
