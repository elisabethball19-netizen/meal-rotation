---
name: Browser fixture lifecycle
description: Safely switching synthetic saved-data fixtures in this autosaving app.
---

Use disposable browser profiles for saved-data tests. Clearing localStorage alone does not reset the running app's memory; include the autosave lifecycle when switching fixtures.

**Why:** Unload autosave repopulated cleared test storage from the previous document's memory, producing misleading onboarding failures. The user explicitly forbids wiping existing user data during testing.

**How to apply:** Isolate synthetic data from the creator's browser, suspend the old document's autosave before fixture navigation, and wait for a new document rather than accepting the old document's ready state.
