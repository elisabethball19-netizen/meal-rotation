---
name: Classic-script initialization
description: Non-obvious startup constraints after splitting the original single app closure.
---

Helpers formerly declared later inside a single closure were available to early initialization through function hoisting. That availability does not carry across separate classic script files.

**Why:** Moving the code without relocating startup dependencies interrupted state initialization and made later failures look like corrupted user data. DOM observers can also run between parser-blocking scripts, before all shared state exists.

**How to apply:** Keep validators and migration/storage helpers available before their first startup call. Defer background-import observers until document initialization is complete, and test both fresh startup and an existing saved library.
