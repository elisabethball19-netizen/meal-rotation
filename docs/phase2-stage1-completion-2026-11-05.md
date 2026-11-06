# Meal Rotation — Phase 2, Stage 1 Completion Report

Date: November 5, 2026  
Repository: https://github.com/elisabethball19-netizen/meal-rotation  
Branch: `codex/phase2-meal-rotation`  
Approved plan: [Phase 2 architecture review and implementation plan](phase2-implementation-plan-2026-11-05.md)

## Status

**Stage 1 is implemented and committed for owner review. Stage 2 has not begun. No merge or deployment was performed.**

Phase 1 [PR #77](https://github.com/elisabethball19-netizen/meal-rotation/pull/77) was verified merged before work began. The development branch starts from main merge commit `b362c19bcd57ec8259729f43c7ef552b7dd74089`, followed by the approved-plan document at `9b84eae5b29351a24163f21007bf92a1beaaa52b`. Main was rechecked after publishing the implementation and still points to `b362c19bcd57ec8259729f43c7ef552b7dd74089`.

Implementation commits:

1. [`2ad6cbe83bb6bd8085d047a1c644302add48dfea`](https://github.com/elisabethball19-netizen/meal-rotation/commit/2ad6cbe83bb6bd8085d047a1c644302add48dfea) — safe current-week empty and one-time meal scheduling, queue safeguards, display reordering, and initial regressions.
2. [`549bfa0e9ae8aa691a87dbd5c9a6ae6398299432`](https://github.com/elisabethball19-netizen/meal-rotation/commit/549bfa0e9ae8aa691a87dbd5c9a6ae6398299432) — individual empty-slot display/position corrections, full rotation-back display order, workflow coverage and fixture corrections, and offline shell v98 preparation.

This report is a documentation-only follow-up. Implementation testing is reported below, including existing failing suites; this is not an independent review or authorization to merge.

## Approved clarifications applied

- Empty one selected meal/group without clearing other meals that day. Also provide a whole-day action. Neither empty action advances recipe queues or Favorites turns.
- Temporary scheduling and manual substitutions must not permanently consume normal recipe rotation turns. Verify reload, backup/restore, selected rotation, and history.
- Photos remain optional and deferred. Missing photos or photo-storage failures must never block ordinary recipe saves or data backups. Define their backup/restore behavior before Stage 5 implementation.

## Completed behavior

### Skip This Meal

Renamed the scheduled-meal action from **Skip This Week** to **Skip This Meal**. Its replacement/postponement behavior remains in the existing skip implementation. The existing skip suite passes in both apps, including linked slots, no-alternative handling, grocery checks, and Undo that preserves later progress on retained meals.

### Leave Empty This Week

Added **Leave Empty This Week** immediately below Skip This Meal. It suppresses the selected current-week meal/group without selecting a replacement or advancing its queue. Assigned groups remain intact. Other assigned meals that day and other tabs remain scheduled.

Each cleared group has its own **Empty this week** placeholder in its display position. Its options allow changing the meal or resuming the planned meal. The weekday's existing planning/group dialog also offers **Leave Entire Day Empty This Week**. With temporary state present, the group dialog offers **Resume planned meals**.

Empty slots remain selectable in the rotation chooser. Rotating an empty slot ends its temporary suppression and resumes the underlying plan without consuming the held recipe's turn. A full rotation expires the scoped week's temporary slots; selected rotation expires only selected slots. Rotation Back and general Undo can restore the temporary schedule.

Hiding a parent removes its unscheduled linked attachments from the active schedule, while independently assigned other groups stay present. Queue maintenance and dependent-side coordination continue to see the underlying plan, so presentation-only absences do not trigger queue changes.

### Add One-Time Meal

Added **Add One-Time Meal** inside Change Meal. It also works on an unconfigured weekday through the existing Choose a meal flow, including when the chooser has no reusable recipes to list.

Users enter a meal name and optional grocery lines with quantities. These entries:

- Live in the current meal tab's temporary schedule, outside the reusable recipe collection.
- Never enter permanent group membership, rotation queues, or normal recipe overrides.
- Contribute their entered grocery quantities only while actively scheduled. Existing quantity aggregation and occurrence-specific checks remain in use.
- Have a lightweight one-time editor rather than the permanent meal editor.
- Expire when their applicable slot/week is rotated. An unselected entry remains when a different group is rotated.
- Survive reload and backup/restore, and can be recovered through explicit Rotation Back/Undo. Their removal from the active schedule does not erase unrelated data.

Prior one-time names/items can therefore remain in a rotation-history snapshot or backup for recovery; they do not remain active grocery contributions after expiration.

Existing legacy `occasionalMeals` records refer to reusable recipes and retain their prior behavior. They were not silently converted into the new temporary-entry format.

### Temporary/manual scheduling and rotation safety

Manual recipe substitutions and their linked children do not consume permanent queue positions or Favorites credits when the substitution expires. Manually displaying a linked recipe saved as an Idea does not promote it into rotation.

The underlying planner is used for permanent recipe mutations, schedule-consistency validation, dependent-side coordination, and linked activation. The temporary schedule is used for current display and groceries. This separation prevents temporary IDs from leaking into permanent planner overrides and allows editing/deleting a recipe that is currently hidden by a temporary slot.

History restoration continues to restore scheduling choices, not old recipe definitions. Tests cover preserving recipe edits made after rotation and preventing deleted recipes from reappearing.

### Weekday display ordering

Added a dedicated **hold-and-drag handle** beside independently displayed meals when more than one is shown that day. This preserves existing name long-press and swipe gestures. Drag metadata uses its own DOM attribute so existing weekday-heading selectors remain compatible.

The handle has a 44px minimum touch target and keyboard Arrow Up/Down support. Inline linked attachments remain with their parent. Ordering uses current-schedule slot identities, independently of permanent Meal Groups order or recipe queue order.

Display order survives reload and backup/restore. A full rotation clears the prior current-week display order; full Rotation Back restores the previous order. Selected-group rotation retains display ordering for the remaining current schedule.

## Storage, backups, and Phase 1 protections

The implementation adds an optional `weekSchedule` field to existing meal-plan records:

```text
weekSchedule = {
  version: 1,
  slots: { weekday/group key: empty-or-one-time descriptor },
  order: { weekday: ordered display-slot keys }
}
```

One-time descriptors contain a stable `once-...` ID, name, and ingredient lines. They are not placed in the primary `meals` collection or `mealRotationSelectedIngredientsV1`.

- Existing data without this field remains valid. There is no bulk migration of saved recipes, ingredient selections, statuses, or queue positions.
- Existing plan snapshots, Undo, rotation history, current backups, and legacy plan loading carry the optional state through their existing structures.
- New optional state is validated during startup and backup validation, including one-time ingredient types, duplicate temporary IDs, and display-order structure.
- Malformed temporary records pause startup in Phase 1 recovery rather than being replaced with defaults. Invalid backups are rejected before replacement.
- Failed writes retain the persistent warning and pending data. Tests verify original durable plans remain available, recovery exports contain pending one-time data/live drafts, and Retry Save persists the intended result after writes recover.
- One-time editor drafts participate in the existing Phase 1 recovery-draft collection.
- Group renaming/removal updates the corresponding temporary-slot/display keys. Recipe deletion continues through Phase 1 dependency/history cleanup.
- Shared application code is synchronized between `index.html` and `meal-rotation-test.html`. Test-only storage isolation, production sentinels, banner, and reset controls remain intact.

The Phase 1 replacement journal and its completion/history protections were not redesigned. Their original regression suites pass.

The service-worker shell version is prepared as **v98** on this development branch. No installed-PWA update or deployment was performed.

## Testing results

All browser testing used synthetic records, intercepted fixture requests, and disposable Chromium contexts. No real user storage was accessed or cleared.

### New Stage 1 suites

| Command | Result |
| --- | --- |
| `python tests/phase2_stage1_browser.py` | PASS: 14 reported case groups across both HTML apps. Rerun after the final empty-slot display and drag-metadata corrections. |
| `python tests/phase2_stage1_workflows_browser.py` | PASS: 28 reported checks across both apps, including existing manual duplicate decisions, Undo/partial Back, Favorites/history integration, reminders, groceries, and import parsing at 320px/360px. |

The Stage 1 suite covers individual/day empty actions; separate placeholders and their positions; linked/dependent groups; multiple tabs; one-time quantities/checks; unconfigured weekdays; manual linked Ideas; reload; backup/restore; selected/full expiration; Rotation Back; general Undo; recovery after failed writes; malformed startup/backup records; recipe deletion and non-resurrection; explicit group rename; grocery/overview rendering; and escaped text.

Real UI interaction checks run at **320px and 360px**, including pointer long-press dragging, Chromium touch-event dragging, keyboard reordering, and full rotation/back display-order restoration. Touch dragging is also checked against accidental activation of the existing swipe-to-edit gesture.

### Existing full suites that passed during Stage 1 verification

```sh
python tests/phase1_final_recovery_safety_browser.py
python tests/phase1_safety_corrections_browser.py
python tests/phase1_data_safety_browser.py
python tests/grocery_rotation_checks_browser.py
python tests/scheduled_linked_slots_browser.py
python tests/meal_groups_bulk_safety_browser.py
python tests/favorites_weighted_browser.py
python tests/dependent_side_groups_browser.py
python tests/shared_week_scheduling_browser.py
python tests/skip_this_week_browser.py
python tests/recipesage_refresh_browser.py
python tests/scheduled_date_integrity_browser.py
python tests/manual_duplicate_meal_browser.py
```

The final recovery suite reports 16 case groups; the earlier safety-corrections suite reports 26. The manual-duplicate suite reports **60 passing checks**, including explicit multiple-occurrence decisions. Favorites testing includes 200 ordinary cycles, weighted skips, and starvation/repetition checks.

The broad regression sweep covered the scheduling/mutation safeguards. The final presentation corrections were additionally checked by rerunning the complete Stage 1 suite and focused mobile/order-history cases.

Inline JavaScript, service-worker JavaScript, and changed Python syntax checks pass. Shared-code parity and `git diff --check` pass. Published implementation blob hashes were checked against the local tested files.

### Test-only corrections

- Updated the skip test to use the requested **Skip This Meal** name.
- Updated legacy occasional-meal menu expectations for the new day/meal actions and the existing cooked-date header layout.
- Corrected stale manual-duplicate assertions: the unchanged baseline already chooses recipe 1 in the vacated source slot, rather than the old assertion's recipe 3. Corresponding linked-dish expectations now follow that actual source choice.
- Marked intentional duplicate occurrences as explicit manual choices in their fixture, rather than expecting automatic allocation to create duplicates.
- Updated the legacy-filter fixture assertion to reflect preserved but inactive filter data. No filtering controls or production filtering behavior were added.

These changes retain assertions for scheduling, quantities/checks, progress, history, and definitions; they do not turn the incomplete full suites below into claimed passes.

## Existing failures and verification limits

The repository's entire test collection is **not fully green**. The following were attempted and are not counted as passing full suites:

| Suite/probe | Finding and baseline comparison |
| --- | --- |
| `recipe_import_audit_browser.py` | Full repair scenarios call the missing `openRecipeInstructionRepair` hook. Reproduced before Stage 1 and documented in Phase 1. Parsing/extraction cases pass separately in both apps at 320px/360px. |
| `import_cleanup_browser.py:146` | The reviewed-save assertion expects immediate memory rollback, conflicting with Phase 1's queued-save policy. Reproduced before Stage 1. Existing durable-data/recovery/retry safeguards remain covered by the passing Phase 1 suites. |
| `editor_return_browser.py` | Its validation probe attempts to fill the collapsed `#prep` field without opening its section. Same timeout reproduced on untouched baseline source. Earlier ordinary save/cancel/return cases run, but the full suite is not a pass. |
| `compact_meal_editor_browser.py` | The long-layout probe waits for absent `#preferredSideGroups`. Same failure reproduced on untouched baseline source. Its initial group/validation/save-cancel checks pass, but the full suite is not a pass. |
| `occasional_meals_browser.py` | After updating stale menu expectations, the full suite reaches a legacy reusable-recipe Side assignment restoration assertion that fails after full rotation/back and reload. Directly reproduced on untouched baseline with `assignment(browser, 'index.html', 320, 'Sides')`. This pre-existing legacy case remains unresolved; the new temporary-entry cases pass. |
| `prep_skip_favorites_integration_browser.py` historical comparison | The full entry point asks local Git for historical object `8177685`, unavailable in this connector-materialized workspace. That historical equality probe was not completed. Its current history, multi-slot, reminders/skip, and backup checks pass through the new workflow runner. |

The workspace Git proxy could not be reached. Repository source was obtained through the GitHub connector; implementation commits were published through GitHub Git-data APIs with branch-head checks. Unrelated remote files were retained through the existing base tree.

Physical iOS/Android gesture behavior, real device quota/process termination, screen-reader behavior, cross-tab conflicts, and installed-PWA upgrades remain manual verification limits. Chromium touch tests and injected storage failures do not establish those device-level guarantees. No independent review has been performed as part of this implementation turn.

## Deferred work and approval boundary

Stage 2 direct scheduling from Meal Groups, Create New Recipe from Change Meal, and meal-tab restoration have **not** begun. Stages 3–5 also remain deferred: recipe-view editing, grocery navigation, new-recipe defaults, onboarding, Rotate Meals terminology, interface polish, and photos.

Stage 5 must first define optional photo backup/restore behavior that allows ordinary recipe saves and data backups to succeed when images are missing or photo storage fails. No photo fields, IndexedDB database, or photo backup format were introduced here.

**Stop here for owner review. Obtain approval before beginning Stage 2. Obtain separate approval before any merge or deployment.** Future plans and completion reports should continue to be published as repository Markdown with a shareable GitHub link, as requested by the owner.
