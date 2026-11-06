# Phase 2 — Stage 4 corrections: independent verification

Date: 2026-11-06. Repository: `elisabethball19-netizen/meal-rotation`. Branch: `codex/phase2-meal-rotation`.

**CORRECTIONS REQUIRED**

The original setup-to-weekday focus handoff is corrected. Two unresolved acceptance/data-integrity defects remain: confirming a nested side-pair change loses focus and disables immediate Escape dismissal; group merge/Undo loses occurrence scales **and saved cooking completion**, not just displayed grocery quantities. Both defects reproduce in unchanged source. Neither is attributed to a newly introduced correction regression.

## Source and independence

Reviewed head: [`eecfd5f06278b6bcf79f52b7bdd040117c303116`](https://github.com/elisabethball19-netizen/meal-rotation/commit/eecfd5f06278b6bcf79f52b7bdd040117c303116).

Read the corrections completion report and prior independent review, then inspected the actual changes in `c616a00f181807025569fe25c8ed05846c8f74ca`, `ebd9a0266b690832bc0aa41c0a4c65722ea51da4`, and `81d238199d1b555627da99bbdc4c99cf97ef2b7c`. The application diff changes the shared weekday picker's focus/dismissal behavior and bumps the service-worker cache to v105. It does not change group merge/Undo, storage formats, rotation allocation, or Favorites algorithms.

Tested exact fetched application blobs:

| File | Git blob |
| --- | --- |
| `index.html` | `6ea5bb042b677917b345acf02a6bd4f68251429c` |
| `meal-rotation-test.html` | `a808d5b74c930bc14e6b520a744d2d62d88327c4` |
| `service-worker.js` | `86bde24be5cb8697f7f9d0c69f106e960d428e03` |

Archived unchanged Stage 4 HTML before loading corrected files. Its application blobs are production `284a06e944401a857fbfd29f5f2fd95e7b351acb` and test `6932c9b488487e18b05f65f6fd5d196244735499`, as reviewed at `deb29f875026e6ce8bd2603e76dbc2cf237638cd` / report-only `d05c036afe336b9e10862301fda57de7dd86808c`. Also tested the earlier pre-Stage-4 source at `6bbcee63b2a377d3471a4b7266f16526997dfeed` for the merge/Undo issue.

Used actual HTML in Chromium/Playwright with synthetic data, disposable contexts, intercepted external requests, and real keyboard/pointer/touch events. Hooks seed fixtures and read actual application state; they do not replace the handlers under review. No application code, group engine, or committed test was edited. Only this report is published. No Stage 5 work, merge, or deployment occurred.

## 1. Keyboard correction verification

### Original S4-IV-1: reproduced, then corrected

In both unchanged Stage 4 apps at **280px, 320px, and 360px**, keyboard activation of Set Up Your Rotation followed by a weekday leaves the active element at `BODY`; Tab reaches background controls and Escape leaves the picker open. All six baseline reproductions match the original independent finding.

In the corrected apps at all six app/width combinations:

- Keyboard-only setup navigation reaches another meal tab's weekday, places focus inside the weekday picker, traverses controls with Tab/Shift+Tab beyond both boundaries, toggles a group with Space, and activates Close with Enter.
- Initial weekday-picker focus is its Close button. Background programmatic focus requests cannot steal focus.
- Escape, Close, pointer backdrop, and touch backdrop dismissal restore usable focus. When rendering removes the opener, focus returns to the current corresponding weekday heading.
- Existing assigned-weekday headings and the empty-day planner's Choose meal groups route reach the same corrected picker.
- Leave Entire Day Empty and Resume render before focus restoration; keyboard reopening works and same-cycle grocery quantities/checkmarks return intact.
- Previously inert body content remains inert after dismissal; ordinary background content becomes usable again.
- Nested side-pair **cancellation** returns focus to the parent picker and permits Escape dismissal of the parent.
- Closing without an assignment edit preserves captured domain data, including recipes, plans/assignments, temporary meals, intentional empties, rotation history, Favorites scores, selected ingredients, grocery contributions/checks, cooking progress, and scales. Ordinary active-tab navigation and empty view caches are allowed, as authorized in this request.

The legacy empty-day planner itself still does not move initial focus into its own dialog. Its controls can be reached with Tab from the initiating heading, and the corrected weekday picker receives focus when launched from it. That planner-shell behavior is separate from the corrected shared picker and was already present before these changes.

### S4C-IV-1 — Nested side-pair confirmation still loses focus

**Confirmed residual keyboard defect; medium severity; correction required for the requested nested-dialog acceptance. Pre-existing in unchanged Stage 4.**

Reproduced in **both apps at 280/320/360px**, against both unchanged Stage 4 and corrected source:

1. Open a configured weekday containing Rice and Sides using its heading and Enter.
2. Open **Side for Sides** with Enter.
3. Use the radio controls and ArrowDown to change Independent to Dependent side for Rice (or the opposite).
4. Tab to **Confirm side for sides** and press Enter.
5. Immediately press Escape.

Actual: the child dialog closes, but `document.activeElement` is `BODY`, outside the still-open weekday picker. Immediate Escape does not close that picker. In the corrected app, pressing Tab first recovers focus inside via the guard; Escape then works. This recovery does not satisfy focus restoration immediately after confirmation.

Cause visible in source: `chooseBulkValue` calls the selection callback before closing. `buildSidePairControls` replaces the original side-button opener while the parent is inert. `recipeBulkDialog.close` restores focus only if that old opener is still connected. No fallback focus event occurs, and the parent's focus guard only responds to later `focusin` events. The parent's Escape handler consequently does not receive a key event targeted at `BODY`.

Relevant functions: `buildSidePairControls` near `index.html:3459`, `openDayCategoryPicker` near `5270`, `recipeBulkDialog` near `6685`, and `chooseBulkValue` near `6799`; corresponding test-app code is synchronized.

The new regression suite tests nested Escape cancellation, but does not confirm an actual nested selection. Add a keyboard confirmation case asserting immediate focus inside the parent, successful immediate Escape, and focus restoration to the weekday heading. This is an incomplete correction of an inherited boundary, not evidence of a new scheduling regression.

## 2. Merge/Undo scaling investigation

### S4C-IV-2 — Merge/Undo loses durable scales and cooking completion

**Confirmed pre-existing data-integrity defect. Recommend a separately scoped fix before Stage 5 authorization.**

Reproduced through the group Keep/move dialog and the actual Undo button in both HTML apps against **pre-Stage-4**, **unchanged Stage 4**, and **corrected Stage 4** source. The behavior genuinely predates Stage 4 and the keyboard correction.

Synthetic reproduction:

1. Rice contains source recipe ID 1; Destination already contains its shared membership ID 22.
2. Tuesday's source meal and linked recipes IDs 20 and 10 have saved 2× occurrence scales, ingredient/step completion, and checked groceries. Another tab has independent scaled occurrences.
3. Delete Rice using **Delete group, but keep recipes**, choose Destination, and confirm the move. The destination's existing identity appropriately absorbs the redundant source membership.
4. Press Undo.

The exact original recipe IDs, ordered records, and recipe fields return. Grocery source keys and checkmarks also return. However, three restored Tuesday occurrences lose their saved scale entries and cooking-session records:

| Occurrence | Grocery line before | After Undo |
| --- | --- | --- |
| Tuesday source ID 1 | 2 cups rice | 1 cups rice |
| Tuesday linked ID 20 | 40 cups rice | 20 cups rice |
| Tuesday side ID 10 | 20 cups rice | 10 cups rice |

Saved scale entries fall from five to two. Saved cooking-session records likewise fall from five to two; the lost records contain completed ingredient tokens, completed instruction tokens, and ingredient overrides. The independent occurrences in the other tab remain intact.

**Durability:** reload retains the reduced quantities and missing cooking completion. Restoring a complete backup captured **before** the operation restores the original scales, completion state, and grocery contributions exactly. A later backup cannot reconstruct values already removed by Undo.

Existing grocery-selection keys/values survive in this fixture. The merge materializes one additional explicit selection for the destination member (`22: ["1 cups rice"]`); this alone is not evidence of an exclusion regression. No recipe-content loss or grocery-checkmark loss was demonstrated in this reproduction.

Source inspection supports the observed failure: category removal uses a plain `snapshot()`. `captureState` excludes occurrence scales and cooking sessions. Persistence reconciles/prunes occurrences invalidated by the merge, but this group-operation snapshot does not carry the extra saved cooking state used by other, dependency-aware operations. Undo therefore restores recipes without restoring the removed occurrence metadata. These engine paths are unchanged by the corrections.

**Assessment:** this is more than a visual quantity mismatch. It silently loses saved user choices and cooking progress through an action labeled Undo, and can halve needed grocery quantities. Successful writes persist this incomplete restored state; Phase 1 write-failure protections cannot reconstruct metadata omitted from Undo. Its pre-existing attribution prevents treating it as a correction regression; it does not make it safe to count as preserved data. I recommend authorizing a focused merge/Undo preservation fix and a regression that checks scales, cooking completion, and resulting quantities before proceeding to Stage 5. The engine was not changed during this verification.

## 3. Strengthened-test review

Both new/strengthened Stage 4 suites completed successfully:

- `phase2_stage4_corrections_browser.py`: **18 PASS scenario groups**.
- `phase2_stage4_browser.py`: **38 PASS scenario groups**, including 280px execution alongside 320px and 360px.

The corrections suite genuinely uses keyboard events through the complete setup handoff and assignment completion. Its domain comparisons include seeded rotation history, Favorites weighting, one-time and empty slots, checked groceries, scales, and cooking completion. It does not merely click controls or assert modal visibility.

The modified Keep/move test compares the complete ordered recipe records, exact IDs, and all fields, allowing only the intended category move and singleton `linkGroup` normalization. The duplicate destination retains its existing ID; a name/ingredients match cannot disguise an identity replacement. Undo restores exact prior records; repeating the move, reloading, and restoring a backup preserve the expected records. Checkmarks and unrelated quantities are asserted, with complete quantity equality for non-merge Undo.

Inspected the test commit and compared the previous Stage 4 file structurally. Only `group_delete` changes among existing test functions, plus the added 280px main-loop width. Its previous name/ingredients/ID-presence assertions are replaced by stronger complete-record equality. No earlier correctness assertion was weakened or removed, and unrelated existing regression files were not changed by this correction.

Important gaps remain:

1. Nested side-pair confirmation is missing; cancellation alone misses S4C-IV-1.
2. The merge test deliberately excludes changed-day quantities from its Undo quantity assertion. This is a newly added exception for a documented baseline issue, not a weakened old quantity assertion, but it means a passing suite does **not** establish complete Undo preservation.
3. Cooking completion is not asserted across the group merge/Undo path, missing the broader impact of S4C-IV-2.
4. The after-move grocery comparison uses the intersection of old/new source keys. An exact expected set for unaffected occurrences would also detect accidentally missing contributions. The final group reload/backup checks compare records; explicit grocery-state equality there would strengthen coverage.
5. The permanent correction tests omit backdrop dismissal and restoration of previously inert content. Supplemental independent pointer/touch and inert-state checks passed at all six app/width combinations.

## 4. Regression and compatibility results

The two Stage 4 suites above and the complete historical weekday suite pass. The following 29 existing suites were also rerun (names omit `_browser.py`):

- Stage 3: `phase2_stage3_corrections`, `phase2_stage3`.
- Stage 2: `phase2_stage2_corrections`, `phase2_stage2`.
- Stage 1: `phase2_stage1_corrections`, `phase2_stage1`, `phase2_stage1_workflows`.
- Phase 1: `phase1_final_recovery_safety`, `phase1_safety_corrections`, `phase1_data_safety`.
- Groceries/scheduling: `grocery_rotation_checks`, `favorites_weighted`, `scheduled_linked_slots`, `dependent_side_groups`, `manual_duplicate_meal`, `scheduled_date_integrity`, `skip_this_week`, `shared_week_scheduling`, `outgoing_cooked_dates`.
- Recipes/groups/viewer: `recipesage_refresh`, `meal_groups_bulk_safety`, `add_recipe_ideas`, `recipe_tabs`, `recipe_touch`, `shared_recipe_management`, `needs_tweaking`, `rotation_dialog_layout`, `recipe_tab_reorder`, `group_order`.

**32 complete suites have passing final executions**: the two Stage 4 suites, full weekday suite, and 29 existing suites listed above. The initial parallel `phase1_safety_corrections` execution failed on its five-second native file-chooser event timeout in `recovery_journal`, at `upload_backup` line 116. After the entire batch finished, a complete isolated rerun of that unchanged suite passed, exit 0, with **26 PASS groups**, including recovery journals and interrupted retry/rollback. The initial timeout is disclosed, not counted as a successful run. The isolated pass and narrow application diff do not demonstrate a persistent recovery regression.

Checks exercised rotation queues/Favorites ledgers, linked-side ownership and scheduling, duplicate rejection, temporary/empty slots, same-cycle grocery Resume, rotation resets, Undo/Rotate Back, selected ingredients and quantities, editor creation/content/source clearing, imports, failed-save rollback/latest-draft Retry Save, recovery exports/journals, and backup compatibility. Passing fixtures do not negate the independently reproduced merge/Undo defect.

Static verification passed: shared JavaScript matches after the expected test-storage provider substitution and test-banner offset additions; shared CSS matches after removing banner CSS and normalizing blank lines. The test storage adapter/reset wrapper remains unchanged. Synthetic production-storage sentinels survive test-app workflows. All inline scripts and the service worker pass `node --check`; tested files match their fetched Git blob hashes.

## 5. Other known failures remain separate

Targeted reproductions against unchanged and corrected Stage 4 in both apps retain the same boundaries:

| Known issue | Reproduced failure |
| --- | --- |
| Legacy Side restoration | `occasional_meals_browser.py:87`, Side assignment after Rotate Back/reload. |
| Duplicate allocation | `rotation_no_duplicates_browser.py:83`, Weekend case; same Saturday ID 4 / Sunday ID 2 / Lunch Tuesday ID 3 rows. |
| Legacy linked occurrence | `cycle_linked_occurrences_browser.py:73`, `legacy-pin` Thursday occurrence changes ID 1 → ID 2. |
| Heading spacing | `page_heading_spacing_browser.py:37`, 14px content gap versus asserted 8px at 280px. |

These are not newly introduced correction defects and are not counted among passing complete suites. Targeted failure-path execution does not imply completion of the remaining cases in those failing suites. Stage 4 already uses the new labels, so the comparison copy's old-to-new label substitution makes no functional change to its source.

The complete weekday setup suite passes with the historical comparison supplied exact HTML from `309866412d9b7778128c5dc8ea58f4a54b0e4f59`, without changing its assertions. It covers 280/320/360/390px/desktop and larger text. Historical weekday-panel height is 847px versus current 541px at 320/360px in both apps. The formerly unavailable local Git object therefore leaves no unresolved historical-comparison limitation here.

## Limitations and decision

Validation uses Chromium, responsive viewports, synthetic fixtures, and simulated touch. Native iOS/Safari, real assistive-technology announcements, and an actual deployed service-worker upgrade were not verified. Those are device/environment limitations, not confirmed defects.

No newly introduced correction regression was confirmed. The original setup handoff, ordinary dismissal, Leave Empty/Resume restoration, and strengthened identity checks work. Before Stage 5, address residual nested-confirmation focus restoration and the separately scoped, pre-existing merge/Undo loss of scales and cooking completion. Keep the four older baseline failures tracked separately.

**CORRECTIONS REQUIRED**
