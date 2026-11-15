# Built-in Sides and preferred-side behavior

Original modular app and the existing storage-isolated test app only. No rebuild, new dependencies, additional app page, site-data reset, import classification, timer or performance work.

## Implementation and migration

A new optional `mealRotationBuiltinSidesGroupV1` storage value points to the existing unique ID in `mealRotationGroupIdentitiesV1`. Membership names, recipe IDs and weekday assignments keep their existing structures. A unique case-insensitive Sides group is adopted with its current ID; otherwise an empty, unassigned Sides group is added. Repeated initialization/reload is idempotent. Multiple case-insensitive Sides names are preserved without merging, with a message asking the user to disambiguate by renaming. An orphaned saved role is reported rather than rebound to an unrelated group.

Runtime matching resolves this ID, including after rename. Existing group controls and In Rotation/Ideas sections remain. Rename/reorder work; UI and domain deletion paths reject deleting the built-in group with a short explanation. Existing rename metadata handling includes the built-in group's automatic/manual choice keys and favorite-order metadata. Full backup/restore preserves the role and identity.

Assigned Sides uses existing title vocabulary, synonym matching and eligible rotation ordering. No preferences means ordinary eligible Sides rotation; an unassigned group generates no side from preferences. Ideas and existing skip exclusions remain excluded from automatic choices. Explicit links and simple sides remain separate. Conflicting parent preferences receive no invented precedence; existing sides are kept and an explanation is shown.

Recipe Save prepares current-week occurrence changes before mutating data. A still-valid automatic side stays. Invalid automatic sides are replaced through the existing manual-scheduling operation inside the existing recipe transaction, preserving the occurrence date. Explicit manual and legacy-unknown choices use standard check/X confirmation. X saves the preferences while keeping the selected side. No eligible match keeps the old side and explains the conflict. Recipe-editor Cancel changes neither preferences nor schedules. Next/cycling operations and explicit choices record automatic/manual provenance, which survives reload.

Preference and side changes share one Undo entry. Existing affected-source grocery Undo helpers preserve later unrelated checks. Replaced-side cooking/scale snapshots are captured for Undo/Redo, including progress added to the replacement after Save. No cooked date is recorded by a preference change.

## Checks actually run

`python tests/builtin_sides_browser.py` passed all case groups in both `index.html` and `meal-rotation-test.html`, with focused reruns for additional provenance checks:

- Fresh installation: one empty, unassigned Sides group; reload retains its ID.
- Existing installation: reuse existing ID; preserve memberships, recipe order/content/custom fields, group order, pins and weekday assignments; no duplicate on reload.
- Repeated initialization, actual rename control, reorder operation, deletion explanation, full-backup round-trip, and ambiguous names left unchanged.
- Assigned + Rice chooses an eligible rice recipe; assigned + no preference chooses normal rotation; unassigned preferences generate no side. Ideas excluded.
- Current-week automatic replacement, valid-side retention, repeated Save, clearing preferences, unsaved editor Cancel, other days/tabs unchanged and a saved future-week side unchanged.
- Manual and older unknown provenance: accept/X, no mutation before confirmation, preferences retained on X, and correct provenance after reload.
- No eligible match and conflicting parent preferences: no silent substitution; side retained with explanation. Linked recipes/simple sides remain and no linked/automatic duplicate appears.
- Ingredient-bearing disposable fixtures: unaffected checks retained, new ingredients unchecked, side tasks reconciled, completed unaffected tasks retained, manual groceries and shopping text unchanged.
- Injected storage failure: recipe and plan records roll back, draft remains, retry succeeds, one Undo entry. No new cooked dates.
- Undo/Redo restores recipe preferences, side occurrence, cooking progress and scales. A later unrelated grocery uncheck survives both directions; replacement progress/scale added after Save survives Redo.
- Use next and side cycling retain automatic provenance across reload and subsequent preference saves; manual explicit choices stay protected.
- No browser page runtime errors; existing test storage remains isolated.

Changed JavaScript/service worker and all inline test-app scripts passed syntax checks. Changed-function and editor-save parity passed with only the existing isolated storage alias normalized. `git diff --check` passed. At 320px width / 420px height, the standard manual-side confirmation has reachable check/X controls without horizontal overflow. Offline shell is v142.

## Pending / deferred

Physical-phone verification remains for native long-press/taps, confirmation/history behavior, group reorder/rename and keyboard/short-screen layout after the installed app updates. Ambiguous group names or conflicting parent preferences require a user decision; they are explicitly preserved rather than merged or assigned a guessed priority.

README records the future import batch: suggest likely side recipes for Sides only after user confirmation, preserving other memberships and leaving uncertain classifications alone. No import behavior was implemented.
