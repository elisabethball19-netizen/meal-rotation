# Phase 2 — Stage 4 completion

Date: 2026-11-06  
Repository: elisabethball19-netizen/meal-rotation  
Branch: `codex/phase2-meal-rotation`  
Starting commit: `6bbcee63b2a377d3471a4b7266f16526997dfeed`

Stage 4 is implemented and committed for independent verification. Stage 5 has not begun. Nothing was merged or deployed.

## Changes

- Empty Meal Groups now presents **Import Recipes** and **Add Recipe**, without empty group cards or collection ordering controls. Import uses the existing source picker/parser; Add uses the existing full editor and Stage 3 defaults. Users can select an existing group or explicitly create a new one. Canceling the initial dialog makes no changes. Continuing explicitly creates a requested group; canceling the subsequent recipe editor discards the blank recipe but retains that group.
- **Set Up Your Rotation** appears in Meal Groups and My Rotation when recipes exist and no meal tab has a saved weekday assignment. It launches the existing weekday group picker for the chosen tab/day. Opening, changing the launcher's tab selection, and closing do not save anything. Only explicit edits in the existing weekday controls change assignments. A saved weekday key, including an intentionally empty assignment, counts as configured. Once any tab is configured, the prompt disappears; normal weekday controls remain accessible in settings. No new onboarding completion key or second scheduling system was introduced.
- User-facing **Cycle Meals / Cycle Back** buttons are now **Rotate Meals / Rotate Back**. Internal functions, history keys, rotation options and algorithms are unchanged.
- Needs Adjusting uses a smaller 16px indication and more compact viewer button, with at least 44px touch targets. Removal confirmation explicitly describes removing the status/note while preserving recipes and rotation positions.
- Saved additional group memberships in Edit Meal and saved secondary weekday assignments use small trash icons. Pending unsaved rows retain Cancel controls. Existing Save-time membership confirmation and assignment handlers remain in place.
- Group deletion explains the difference between keeping/moving recipes and explicitly deleting recipes unique to that group. The existing Keep recipes choice is first and initially focused. The explicit destructive choice remains available with a trash icon. The existing deletion/move engine is unchanged; other group memberships and unrelated groups are preserved.
- Recipe swipe actions distinguish **Remove from this group** for shared recipes from **Delete recipe** for a sole membership. The scheduled-day removal action says **Remove scheduled meal**, with confirmation that saved recipes and permanent assignments are retained. Existing removal behavior is unchanged.
- Import and group deletion dialogs support keyboard focus, Escape and Tab wrapping.
- Shared application JavaScript and CSS are synchronized between production and test HTML. Test-only storage wrapper, banner and reset controls are unchanged. Service-worker cache version is v104 for the changed assets; no deployment was performed.

## Permanent regression coverage

Added `tests/phase2_stage4_browser.py`: **30 passing scenario groups**, running production and isolated test versions at 320px/360px where relevant. Coverage includes:

- Empty collections with and without groups; genuine fresh installs; default meal tabs; uncluttered actions; native file import and new recipe defaults.
- Keyboard activation/cancellation, recipe creation and canceled drafts, mobile overflow and touch targets.
- Setup with multiple tabs, explicit day selection, canceled setup without writes, configured and intentionally empty days, legacy labels/filters, and preservation of unrelated temporary scheduling.
- Group removal/move with and without an existing shared member at the destination, safe initial focus, Escape cancellation, recipe identity/content preservation, reload and backup/restore.
- Compact Needs Adjusting controls and scoped confirmation; membership trash icons; actual shared-membership removal without deleting its surviving recipe membership.
- Scheduled-day removal with Cancel/confirm, preserved definitions/assignments and unaffected grocery checks.
- One-time meal identity, quantities and checked groceries surviving unrelated weekday setup, reload and backup/restore.
- Failed settings persistence using existing warnings, recovery export and Retry Save.

Existing test edits update user-facing selectors/confirmation text only. Existing scheduling/data correctness assertions were retained; none were removed or weakened.

## Actual validation results

Synthetic data only; browser requests were intercepted. Browser: installed Chromium via Playwright. Both HTML versions were exercised with test-storage sentinel checks.

### Passing suites

The following **28 complete browser suites passed** (exit 0; together 519 printed PASS groups):

```
phase2_stage3_corrections  phase2_stage3
phase2_stage2_corrections  phase2_stage2
phase2_stage1_corrections  phase2_stage1  phase2_stage1_workflows
phase1_final_recovery_safety  phase1_safety_corrections  phase1_data_safety
grocery_rotation_checks  scheduled_linked_slots  favorites_weighted
dependent_side_groups  manual_duplicate_meal  shared_week_scheduling
scheduled_date_integrity  meal_groups_bulk_safety  recipesage_refresh
skip_this_week  add_recipe_ideas  recipe_tabs  recipe_tab_reorder
recipe_touch  shared_recipe_management  needs_tweaking
group_order  rotation_dialog_layout
```

Each name corresponds to `python tests/<name>_browser.py`.

Additional results:

- `python tests/phase2_stage4_browser.py`: **30 PASS groups**, exit 0.
- `python tests/outgoing_cooked_dates_browser.py`: **passed**, exit 0.
- Targeted `needs_tweaking_refinements_browser.viewer`: **8 cases passed**, both apps, 320/360px, Full/Split modes. This was viewer coverage only, not that older suite's full-editor paths.
- Targeted `occasional_meals_browser.remove`: **4 cases passed**, both apps, 320/360px.
- Targeted `weekday_setup_browser.run`: **4 cases passed**, both apps, 320/360px, retaining original assertions for add/change/remove, save/cancel, start-day prompts, recipes, selections, progress and other-tab preservation.
- Manual screenshot inspection of empty onboarding and setup dialog at 320px: passed; setup's weekday list scrolls within the modal.
- `node --check`: all inline scripts in both apps and service worker passed.
- Normalized shared application JavaScript equality and shared CSS equality: passed. Test-only shell/storage/reset and banner compared with pre-Stage-4 source: unchanged.
- `git diff --check`: passed.

### Existing failures and validation limitations

These were not silently counted as passes and were not fixed or relaxed in Stage 4:

1. **Known legacy Side restoration issue:** `occasional_meals_browser.assignment(browser, app, 320, 'Sides')` fails its post-Rotation-Back/reload expected Side ID assertion (line 87). Reproduced on both unchanged starting apps and both Stage 4 apps. This is the previously documented legacy issue, separate from the corrected Stage 2 paired-side queue protection.
2. **Older duplicate-allocation assertion:** full `rotation_no_duplicates_browser.py` exits 1 at line 83 in its initial weekend case, expecting a different Saturday recipe (actual ID 4, Sunday ID 2). The same assertion and identical rows were reproduced against unchanged starting source in both apps. All new Stage 2 duplicate-rejection tests and relevant scheduling suites above pass.
3. **Older linked-occurrence assertion:** full `cycle_linked_occurrences_browser.py` exits 1 at line 73 for `legacy-pin` (Thursday's independent occurrence moves). Reproduced with identical scheduling rows against unchanged starting source in both apps.
4. **Older heading-spacing assertion:** full `page_heading_spacing_browser.py` exits 1 at line 37 at 280px: existing content gap is 14px rather than expected 8px. Reproduced against unchanged starting source in both apps. Longer Rotate labels can wrap on very narrow screens; Stage 4 320/360px functional/mobile checks pass.
5. **Unavailable historical comparison:** full `weekday_setup_browser.py` cannot finish its historical-height comparison because Git object `309866412d9b7778128c5dc8ea58f4a54b0e4f59` is absent from this workspace. Its original interaction tests were invoked separately and passed all four cases above. The historical comparison assertion was not removed.

Baseline comparisons used archived source from the exact starting commit. Where current UI selectors required it, only Cycle/Rotate button text was adapted in the in-memory baseline test page; scheduling code and assertions were unchanged. No newly introduced correctness failure was identified in the completed checks. The baseline failures and historical comparison limitation remain for independent review.

## Compatibility and remaining scope

No saved-data migration, recipe status rewrite, ingredient-selection rewrite, queue change or rotation-position adjustment is introduced. Existing data fields and Phase 1 persistence/recovery mechanisms are reused. Explicit empty days and saved preferences are not overwritten by onboarding. Current import access in settings remains available after recipes exist; no permanent collection import action is added to populated Meal Groups.

The legacy Side issue and other baseline test discrepancies above remain outside this Stage 4 scope. Optional recipe photos and their storage/backup design remain Stage 5 work and have not begun.

## Commit references

- Implementation: [`c8bcd4635c86646f4345192e20c7e90ed15fa259`](https://github.com/elisabethball19-netizen/meal-rotation/commit/c8bcd4635c86646f4345192e20c7e90ed15fa259)
- Permanent regressions and selector updates: [`45a0ba89188a0c62f38a602236fce3c8d9058a1e`](https://github.com/elisabethball19-netizen/meal-rotation/commit/45a0ba89188a0c62f38a602236fce3c8d9058a1e)
- This report is published in the subsequent documentation commit on the same development branch.

Shareable report: https://github.com/elisabethball19-netizen/meal-rotation/blob/codex/phase2-meal-rotation/docs/phase2-stage4-completion-2026-11-06.md

Stopped after Stage 4 for independent verification. No Stage 5, merge or deployment is authorized or performed.
