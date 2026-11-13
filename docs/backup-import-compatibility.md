# Backup and recipe-import compatibility

- **Import recipes** reads recipes only. Version-2 `meals` arrays and unversioned
  `meals` arrays are recognized. `cat` strings/arrays and direct `tags` join
  existing category/label sources in the group chooser. Importing recipes does
  not restore plans, cooking progress, or settings.
- **Restore backup** restores the entire validated backup. Version-2 documents
  may provide top-level fields, `storage`, or both. Explicit top-level recipe
  collections, plans, weekday assignments/overrides, colors, pins, cooking
  sessions (`cookSessions`), checked ingredients, and supported preferences
  override the corresponding storage records. Missing top-level fields leave
  the storage records unchanged. Unknown app-owned storage extensions remain
  opaque; unrelated origin data and test namespaces are not imported.
- Full-restore recipes retain the existing saved-meal schema (`cat` is one
  group per meal); multiple source tags belong to the recipe-only importer.
- Confirmed **Start Fresh** deletes app-owned keys and the recovery journal
  without writing a snapshot first. A deletion or verification failure leaves
  saving paused and reports that the reset did not finish.
- Recovery journals are optional. They retain at most six previous attempts
  (seven including the current attempt), within 50 KiB of UTF-8 JSON. Old
  attempts are removed first. A quota failure permits one smaller retry.
  Essential current rollback data is never truncated: if it cannot fit,
  recovery export uses the complete in-memory snapshot. Keep the page open
  until recovery succeeds or that data has been exported.

## Regression commands

The app still has no dependencies or build step. Browser checks use the existing
Python Playwright test setup and an installed Chromium. On Nix, use the system
Node for the Playwright driver:

```
python3 tests/quota_backup_static.py
PLAYWRIGHT_NODEJS_PATH=$(command -v node) python3 tests/quota_backup_browser.py
PLAYWRIGHT_NODEJS_PATH=$(command -v node) python3 tests/run_browser_regressions.py tests/phase1_final_recovery_safety_browser.py
PLAYWRIGHT_NODEJS_PATH=$(command -v node) python3 tests/run_browser_regressions.py --backup-compatibility
```

The runner adapts older inline-app fixtures in memory only; the new quota/backup
suite keeps the modular app's separate script execution. All browser contexts
use synthetic data on intercepted test origins, never real user storage.
