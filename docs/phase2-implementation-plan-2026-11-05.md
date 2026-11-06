# Meal Rotation — Phase 2 Architecture Review and Proposed Plan

Date: November 5, 2026  
Repository: https://github.com/elisabethball19-netizen/meal-rotation  
Development branch: `codex/phase2-meal-rotation`

## Status and approval boundary

Phase 1 [PR #77](https://github.com/elisabethball19-netizen/meal-rotation/pull/77) was verified merged into `main` on November 5, 2026 at 22:58:40 UTC. The merge commit is `b362c19bcd57ec8259729f43c7ef552b7dd74089`.

The separate Phase 2 development branch was created from that latest main commit. This document records inspection findings and a proposed plan. **Implementation has not been approved or begun.** Publishing this document does not authorize implementation. No merge or deployment has occurred; both require separate owner approval.

The owner requests that plans and progress reports be published as Markdown documents in this repository and that a shareable GitHub link be supplied each time.

## Architecture findings

- Application logic and styling live primarily in `index.html` and `meal-rotation-test.html`.
- Scheduling combines shared recipe order, per-tab weekday assignments and overrides, linked meals, Favorites weighting, and rotation history. Relevant paths include `allocateScheduledWeek`, `getDisplayedWeekdayMealsForPlan`, `skipScheduledMeal`, and rotation-back helpers.
- Meal tabs already have plan creation and persistence primitives, including `createMealPlan`, `saveActiveMealPlan`, and `loadMealPlan`. New installations receive Breakfast, Lunch, and Dinner; saved installations retain their own plans.
- Groceries track ingredient selections and checked states by scheduled occurrence. `getGroceryContributions` combines displayed schedules with saved selections, quantities, and occurrence multipliers.
- Recipe view already preserves navigation origin, active viewer tabs, focus, and scroll, providing a foundation for lightweight editing and grocery-to-recipe navigation.
- Backups contain versioned recipe/plan data and a storage snapshot. Existing legacy and current backups must remain readable.
- Phase 1 protects storage through validation, queued failed saves, recovery drafts, and replacement journals. New state must participate in those protections.

## Development constraints

Preserve existing features, styling, saved recipes, settings, navigation, localStorage compatibility, and rotation positions unless a requested feature explicitly changes them. Avoid unrelated refactoring or redesign.

Keep shared functionality synchronized between both HTML apps. Preserve test-only storage isolation, banner, and reset controls, along with Phase 1 backups and recovery mechanisms.

Use small, reviewable commits. Document completed changes, outstanding issues, and actual testing results. Do not merge or deploy without owner approval.

## Proposed stages

### 1. Scheduling and rotation safety

- Rename Skip This Week to **Skip This Meal**, preserving postponement and replacement behavior.
- Add **Leave Empty This Week** immediately below it. Leave the selected slot empty without choosing a replacement, advancing that meal's rotation position, or removing assigned groups. Resume normal rotation in the following week.
- Add **Add One-Time Meal** from Change Meal, with an optional name and grocery items with quantities. Keep temporary meals outside the permanent recipe collection and rotation queue; expire their active schedule and grocery contributions when the applicable week is rotated.
- Add long-press drag-and-drop ordering within a weekday, affecting only current schedule display order.

Safety focus: explicit current-week state must survive reload and backup without changing recipe queues, assigned groups, or unrelated slots. Empty slots must remain distinguishable from unconfigured slots. Cover multiple groups, tabs, linked meals, selected rotation, and rotation history.

### 2. Scheduling entry points and meal tabs

- Add **Schedule Meal** to Meal Groups actions, with weekday and meal-tab selection, without changing permanent group assignments or normal rotation rules.
- Add **Create New Recipe** to Change Meal; save a reusable recipe and schedule it in the selected slot.
- Restore **Add Tab**, including user-selected Breakfast, Lunch, or custom names.
- Preserve rename, reorder, delete, scheduling, grocery, and backup behavior.

Safety focus: reuse scheduling rules without changing permanent assignments. Do not automatically recreate deleted tabs or alter initial Breakfast/Lunch/Dinner defaults. A cancelled recipe draft must not leave unintended schedule changes.

### 3. Recipe and grocery workflows and defaults

- Open a lightweight editor inside recipe view for ingredients, instructions, source link, and notes.
- Keep linked relationships, group assignments, labels, and rotation organization in the full meal editor.
- Preserve the active recipe tab and scroll position after saving.
- Make associated meal names in groceries selectable, opening the existing viewer and returning to the grocery list at its prior scroll position with checks and selections preserved.
- Include ingredients for newly created/imported recipes in groceries when scheduled, retaining individual deselection.
- Default newly created/imported recipes to **In Rotation**, with an **Ideas** option.

Safety focus: register editor drafts with Phase 1 recovery. Apply defaults only at recipe creation/import; preserve all existing selections and statuses, including deliberate exclusions. Preserve Favorites weighting. Distinguish new imported records from updates to existing recipes.

### 4. Onboarding, terminology, and interface polish

- In empty Meal Groups, offer **Import Recipes** and **Add Recipe**.
- When recipes exist but rotation is unconfigured, show a temporary **Set Up Your Rotation** prompt.
- Once recipes exist, keep importing accessible through existing settings without a permanent import button.
- Rename user-facing Cycle Meals terminology to **Rotate Meals**, preserving all options and behavior.
- Make Needs Adjusting visually smaller while preserving its mobile touch target.
- Clarify delete confirmations to distinguish label removal from assignment removal and state when recipes are not deleted.
- Replace the delete-group X in the meal editor with a matching small trash icon; retain confirmation.

Safety focus: preserve legacy storage identifiers, labels and filter data, existing navigation, and mobile touch targets. Do not reintroduce inactive filtering controls.

### 5. Optional recipe photos

- Support user-attached photos.
- Show small optional thumbnails in Meal Groups and relevant selection/search views, with a larger image in recipe view.
- Provide a placeholder where no photo exists.
- Keep My Rotation and Weekly Overview compact by default.

Proposed storage design: resize images and store image blobs in IndexedDB, with references in recipe data rather than large image data in localStorage. Photo storage failures must leave recipes usable. Extend backup/restore to include photos while continuing to accept existing backups. Isolate test photo storage too.

Safety focus: photo writes and restore need careful ordering across IndexedDB and localStorage. Handle missing images, unavailable storage, failed writes, and recovery without risking recipes. Finalize the photo backup format and validation before implementing it.

## Testing strategy

Establish the unchanged-main baseline before implementation. Use synthetic data and disposable browser/storage contexts for both apps.

After each relevant stage, test:

- Scheduling, skip/replacement, full and selected rotation, rotation back/history, multiple groups/tabs, linked meals, and Favorites weighting.
- Grocery aggregation, quantities, checked items, ingredient selections, and occurrence identity.
- Recipe editing, cancelled drafts, import parsing and saves, reload persistence, and backup/restore.
- Empty-slot resumption, one-time expiration, temporary groceries, and display-only ordering.
- Storage failure, retry, recovery drafts, interrupted replacement, and Phase 1 recovery-journal invariants.
- Shared-code parity, JavaScript syntax, and preservation of test storage isolation, banner, and reset.
- For photos: unavailable storage, missing blobs, failed writes, and backups with and without images.

Reuse existing relevant browser suites, add focused regression cases for new behavior, and report actual results rather than treating documented Phase 1 results as new runs. Mobile touch interactions, file handling, accessibility/focus, and installed-PWA behavior also require appropriate browser/manual verification.

## Known baseline test issues

The Phase 1 final recovery report and independent verification document two existing import-suite problems:

1. `tests/recipe_import_audit_browser.py` calls the absent `openRecipeInstructionRepair` hook in repair scenarios. Parsing/extraction was independently reported passing.
2. `tests/import_cleanup_browser.py:146` expects rollback and an open review dialog after a failed save. Phase 1 queues the change in memory, retains it for recovery, and displays the persistent save warning. Independent verification found native saved recipes remained unchanged until a successful retry, followed by persistence on reload.

Establish these baselines and report them separately from Phase 2 regressions. Do not count the full suites as passing or change expectations merely to obtain a green result.

References:

- [Phase 1 final recovery safety report](phase1-final-recovery-safety-2026-11-05.md)
- [Phase 1 final independent verification](phase1-final-independent-verification-2026-11-05.md)

## Inspection limitations and next step

No tests were run during this planning inspection. Workspace Git cloning failed because the configured proxy could not be reached; repository files and metadata were inspected through the GitHub connector.

Await owner approval of this plan before writing implementation code. Keep implementation on the separate Phase 2 branch and obtain separate approval before any merge or deployment.
