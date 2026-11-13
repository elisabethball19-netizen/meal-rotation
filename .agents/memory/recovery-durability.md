---
name: Recovery durability
description: Why destructive reset and non-destructive restore need different storage guarantees
---

Explicitly confirmed Start Fresh is deletion-only. Restore retains validation,
rollback, and recovery export, but durable recovery journaling is optional;
complete in-memory rollback data is preferable to a truncated durable snapshot.

**Why:** The user's blocking recovery failure happened because saving a recovery
journal required additional space in an already-full browser store.

**How to apply:** Never route destructive reset through snapshot-first restore.
When optional journaling cannot fit, retain complete exportable in-memory data
and retire stale journal metadata before changing the records it describes.
