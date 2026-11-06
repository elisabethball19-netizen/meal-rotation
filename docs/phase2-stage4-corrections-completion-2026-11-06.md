# Phase 2 — Stage 4 corrections completion

Date: 2026-11-06  
Branch: `codex/phase2-meal-rotation`  
Starting remote commit: `d05c036afe336b9e10862301fda57de7dd86808c`  
Review addressed: [Stage 4 independent verification](phase2-stage4-independent-verification-2026-11-06.md).

## Scope and exact corrections

**S4-IV-1:** corrected the existing shared weekday-group picker used by Set Up Your Rotation and the existing weekday heading/planner entry points.

- Opening the picker moves focus to its Close button.
- Tab and Shift+Tab wrap among currently visible, enabled controls. Background body children are made inert while the picker is active, with their previous inert states restored on dismissal. A focus guard also contains focus if background elements are added during rendering.
- The guard yields when a child side-pair dialog makes the picker inert, preserving nested dialog interaction.
- Escape prevents further handling and dismisses the picker. Close and backdrop dismissal use the same cleanup, removing the focus listener and restoring background interaction.
- Dismissal restores the initiating control when it remains usable. When the setup launcher or weekday rendering has removed that control, focus returns to the corresponding current weekday heading.
- The existing Leave Entire Day Empty and Resume actions run before focus restoration, so their rendering does not discard the restored focus.
- Pointer/touch handlers, checkbox assignment handlers, side-pair logic, rotation logic and saved-data formats remain unchanged.

Both HTML versions contain the same functional correction with the existing test storage-provider substitution. The service-worker asset cache version is v105. No deployment was performed.

## Cancellation contract

Canceling the setup launcher or entering a weekday picker and dismissing it **without explicitly editing assignments** preserves domain data: recipe records/order, weekday assignments, scheduled and temporary meals, intentional empty slots, grocery selections/checks/quantities, rotation history, Favorites scores, cooking progress and scales. Ordinary navigation to another meal tab and harmless empty caches may persist. There is no navigation rollback or new saved-data migration.

The weekday picker retains its existing immediate-save behavior: explicitly toggling a group is an assignment edit; closing afterward does not undo that intentional edit. Escape/Close themselves make no assignment changes. The setup launcher still does not create assignments automatically.

## Reproduction before application edits

Archived the exact unchanged Stage 4 application files, then exercised real UI controls in synthetic Chromium contexts. In **both apps at 280px, 320px and 360px**:

1. Open unconfigured Meal Groups, focus Set Up Your Rotation, press Enter.
2. Tab to Monday and press Enter.
3. The weekday dialog opens with active element `BODY`.
4. Tab focuses a background control; Escape leaves the picker open.

All six unchanged-source reproductions confirmed the review's defect before application code was modified. The inherited component attribution remains as documented in the independent review.

## Permanent regressions

Added `tests/phase2_stage4_corrections_browser.py` with real keyboard interactions through the full setup handoff at **280/320/360px in both apps**. Fixture hooks only seed/read synthetic state; user actions operate actual UI handlers.

Coverage includes launcher and cross-tab picker cancellation; initial focus; repeated Tab/Shift+Tab traversal beyond both boundaries; blocked background focus; keyboard selection and completion; Escape and Close; meaningful weekday focus restoration after rendering; existing weekday heading and empty-day planner routes; nested side-pair cancellation; pointer/touch dismissal; keyboard Leave Empty/Resume; reload and backup/restore; production storage sentinels. Cancellation fixtures contain actual rotation history, Favorites weighting, checked groceries, one-time meals and intentional empty slots. Domain snapshots permit only ordinary active-tab navigation and absent-versus-empty cache normalization.

Strengthened `tests/phase2_stage4_browser.py`:

- Added 280px execution for empty states, onboarding creation, setup and group deletion, retaining 320px/360px coverage.
- Keep/move expectations compare the complete ordered recipe records and exact IDs. For a fixture whose destination already contains the shared recipe, the destination's existing ID survives and only the redundant source membership disappears; no inferred replacement by matching names is accepted. Expected field changes are limited to the requested category move and existing singleton `linkGroup` normalization; all other fields must match exactly.
- Assert exact prior records after Undo, then repeat the move and assert exact records after reload and backup restoration.
- Check unaffected grocery occurrences' checked states and quantities. Undo preserves all occurrence checkmarks and unrelated quantities; non-merge Undo also retains the complete source quantity map. The existing duplicate-destination scaling limitation is explicitly separated below.

No previously committed scheduling/data correctness assertion was removed or relaxed. The prior name/ingredient-only identity check was replaced by stricter complete-record equality. No unrelated existing test was edited.

## Actual test results

### New and strengthened suites

- `python tests/phase2_stage4_corrections_browser.py`: **18 PASS scenario groups**, exit 0, both apps at 280/320/360px.
- `python tests/phase2_stage4_browser.py`: **38 PASS scenario groups**, exit 0, including the new 280px and exact-record/Undo coverage.
- Full `weekday_setup_browser.py`: **passed**, exit 0 (six PASS groups plus historical comparison output). Its missing historical `git show` input was supplied by a temporary runner using exact GitHub HTML blobs from commit `309866412d9b7778128c5dc8ea58f4a54b0e4f59`, verified as production `2c9795601af060916028eab46a275cd660a14554` and test `37e8a4a58076c6b171733075b55f556f507f1b56`. The original suite and all assertions were unchanged.

### Existing regression suites

**29 existing suites completed with successful final executions** (exit 0, with the Phase 1 retry described below):

- `python tests/phase2_stage2_corrections_browser.py`
- `python tests/phase2_stage3_browser.py`
- `python tests/phase2_stage3_corrections_browser.py`
- `python tests/phase2_stage2_browser.py`
- `python tests/phase2_stage1_browser.py`
- `python tests/phase2_stage1_corrections_browser.py`
- `python tests/phase2_stage1_workflows_browser.py`
- `python tests/phase1_final_recovery_safety_browser.py`
- `python tests/phase1_safety_corrections_browser.py`
- `python tests/grocery_rotation_checks_browser.py`
- `python tests/phase1_data_safety_browser.py`
- `python tests/favorites_weighted_browser.py`
- `python tests/scheduled_linked_slots_browser.py`
- `python tests/dependent_side_groups_browser.py`
- `python tests/manual_duplicate_meal_browser.py`
- `python tests/scheduled_date_integrity_browser.py`
- `python tests/recipesage_refresh_browser.py`
- `python tests/meal_groups_bulk_safety_browser.py`
- `python tests/skip_this_week_browser.py`
- `python tests/shared_week_scheduling_browser.py`
- `python tests/add_recipe_ideas_browser.py`
- `python tests/recipe_tabs_browser.py`
- `python tests/recipe_touch_browser.py`
- `python tests/shared_recipe_management_browser.py`
- `python tests/needs_tweaking_browser.py`
- `python tests/rotation_dialog_layout_browser.py`
- `python tests/recipe_tab_reorder_browser.py`
- `python tests/outgoing_cooked_dates_browser.py`
- `python tests/group_order_browser.py`

Together with the two Stage 4 suites and the full weekday suite above, **32 complete suites have passing final executions**. The separately rerun historical failure paths below remain failures and are not included in this pass count.

The initial parallel execution of `phase1_safety_corrections_browser.py` timed out waiting five seconds for the native file-chooser event in `recovery_journal`. A separate complete rerun of that unchanged suite **passed**, exit 0, with **26 PASS groups**, including recovery journals, interrupted retry/rollback, exports, cancellation and live recovery. The first timeout is disclosed rather than counted as a pass.

### Static checks and tested source

- `node --check` on all inline scripts in both HTML files and the service worker: passed.
- Normalized shared application JavaScript equality and shared CSS equality: passed.
- Test-only shell, storage wrapper, reset controls and banner compared with archived source: unchanged.
- Python compilation of the two Stage 4 regression files: passed.
- `git diff --check`: passed.
- Synthetic fixtures, intercepted requests and disposable Chromium contexts only; test-app production-storage sentinels survived.

Final tested Git blob hashes:

| File | Blob SHA |
| --- | --- |
| `index.html` | `6ea5bb042b677917b345acf02a6bd4f68251429c` |
| `meal-rotation-test.html` | `a808d5b74c930bc14e6b520a744d2d62d88327c4` |
| `service-worker.js` | `86bde24be5cb8697f7f9d0c69f106e960d428e03` |

## Existing issues kept separate

The four independently confirmed baseline failure paths were rerun against the corrected apps, with their original assertions unchanged. Each still fails at the same identified boundary in both apps; these targeted executions do not imply completion of the rest of those failing suites.

| Existing issue | Actual failing path | Attribution / scope |
| --- | --- | --- |
| Legacy Side restoration | `occasional_meals_browser.assignment(..., 320, 'Sides')`, line 87 after Rotation Back/reload | Predates Stage 4 and remains distinct from Stage 2 paired-side queue protection. |
| Duplicate allocation | `rotation_no_duplicates_browser.run(..., 320, 'weekend')`, line 83; Saturday ID 4 / Sunday ID 2 / Lunch Tuesday ID 3 | Same previously verified baseline allocation assertion. No allocator redesign. |
| Legacy linked occurrence | `cycle_linked_occurrences_browser.run(..., 320)`, line 73, `legacy-pin` Thursday occurrence ID 1 becomes ID 2 | Same previously verified baseline behavior. |
| Heading spacing | `page_heading_spacing_browser.run(..., 280, 'normal', False)`, line 37; actual gap 14px versus asserted 8px | Same previously verified baseline spacing mismatch. New controls retain narrow-screen coverage. |

### Additional baseline limitation exposed by stronger move/Undo checks

Moving Rice into a destination that already contains its shared recipe, then Undo, restores the exact prior recipe IDs/fields and checkmarks, but can lose cooking-scale multipliers for restored occurrences in the changed day. In the synthetic fixture, some original Tuesday quantities change from 2→1, 20→10 and 40→20 cups; unrelated occurrences remain intact. This is a **quantity-scaling difference**, not a demonstrated loss of recipe definitions or checkmarks.

Reproduced this extra full-quantity expectation against both archived unchanged Stage 4 apps and both corrected apps. The existing group deletion/merge and Undo engines were not changed. The permanent move regression requires exact recipe restoration, all original checkmarks and unrelated quantities, and exact complete quantities for non-merge moves. The duplicate-destination scale restoration issue remains documented for a separately scoped correction, rather than silently counted as fixed.

## Limitations and next step

Validation uses Chromium with synthetic fixtures and intercepted network requests. Native iOS/Safari, assistive-technology announcements on real devices and an actual deployed service-worker upgrade were not verified. No Stage 5 work, merge or deployment occurred. Independent verification is the next step.

## Commit references

- Shared picker focus containment and dismissal: [`c616a00f181807025569fe25c8ed05846c8f74ca`](https://github.com/elisabethball19-netizen/meal-rotation/commit/c616a00f181807025569fe25c8ed05846c8f74ca).
- Focus restoration after Empty/Resume rendering: [`ebd9a0266b690832bc0aa41c0a4c65722ea51da4`](https://github.com/elisabethball19-netizen/meal-rotation/commit/ebd9a0266b690832bc0aa41c0a4c65722ea51da4).
- Permanent keyboard, 280px and exact-record regression coverage: [`81d238199d1b555627da99bbdc4c99cf97ef2b7c`](https://github.com/elisabethball19-netizen/meal-rotation/commit/81d238199d1b555627da99bbdc4c99cf97ef2b7c).
- This report is published in the following documentation commit on the same branch.

Shareable report: https://github.com/elisabethball19-netizen/meal-rotation/blob/codex/phase2-meal-rotation/docs/phase2-stage4-corrections-completion-2026-11-06.md
