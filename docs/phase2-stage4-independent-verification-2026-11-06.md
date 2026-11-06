# Phase 2 — Stage 4 independent verification

Date: 2026-11-06. Branch: `codex/phase2-meal-rotation`.

**CORRECTIONS REQUIRED**

The new setup workflow fails the requested keyboard/Escape acceptance criterion. Its underlying weekday-picker accessibility defect also exists before Stage 4; this is an inherited component defect exposed through the new onboarding workflow, not a newly introduced rotation regression. No new scheduling, grocery, recipe-content, or durable-storage regression was confirmed in this review.

## Reviewed source and method

- Reviewed head: [`deb29f875026e6ce8bd2603e76dbc2cf237638cd`](https://github.com/elisabethball19-netizen/meal-rotation/commit/deb29f875026e6ce8bd2603e76dbc2cf237638cd).
- Inspected the completion report, application implementation commit `c8bcd4635c86646f4345192e20c7e90ed15fa259`, and test/selector commit `45a0ba89188a0c62f38a602236fce3c8d9058a1e`.
- Compared against the unchanged pre-Stage-4 application at `6bbcee63b2a377d3471a4b7266f16526997dfeed`.
- Ran actual production and test HTML in Chromium/Playwright, using synthetic fixtures, isolated browser contexts, and intercepted external requests. Supplemental checks exercised real buttons, dialogs, keyboard events, and stored records. Fixture hooks supplied synthetic state and read internal scheduling/grocery state; they did not replace the application handlers under review.
- Verified exact Git blob hashes of the tested application: production `284a06e944401a857fbfd29f5f2fd95e7b351acb`, test `6932c9b488487e18b05f65f6fd5d196244735499`, service worker `aebd090ba5bf4c8bed10aad69575ddad94aaf711`.
- Application code was not edited. This report is the only published change. No merge, deployment, or Stage 5 work occurred.

## Blocking acceptance finding

### S4-IV-1 — Setup loses keyboard focus when opening weekday selection

**Confirmed on both applications at 280px, 320px, and 360px. Medium severity; blocks the requested Stage 4 keyboard/Escape acceptance criterion.**

Reproduction:

1. Start with recipes and no configured weekday keys in any meal tab.
2. Open Meal Groups. Focus **Set Up Your Rotation** and press Enter.
3. Focus **Monday** in the setup dialog and press Enter.
4. Observe the new **Choose Monday's meal groups** dialog.
5. Press Tab, then Escape.

Actual: `document.activeElement` becomes `BODY` during the handoff. The next Tab focuses the background **Dinner** control, outside the dialog. Escape does not dismiss weekday selection. The picker has `aria-modal="true"`, but neither receives initial focus nor contains keyboard traversal. The new launcher itself has keyboard handling; that handling is lost when it closes and opens the existing picker.

Expected: focus enters the weekday dialog, Tab/Shift+Tab stay within it, and Escape dismisses it without changing assignments. Closing should return focus to a meaningful control in the initiating workflow.

Relevant code: `openRotationSetup` near `index.html:6917` and `openDayCategoryPicker` near `index.html:5270`; equivalent code exists in the test HTML.

**Baseline attribution:** opening the same weekday picker directly against unchanged pre-Stage-4 HTML also leaves focus outside and ignores Escape. Consequently, this report does not claim Stage 4 introduced that underlying defect. The new Stage 4 setup route nevertheless fails an explicitly requested acceptance check. Correct the modal handoff/picker keyboard behavior and add a regression test that continues past the setup launcher into weekday selection.

## Other cancellation boundary

Opening the setup launcher, changing its meal-tab selector, and closing the launcher leave the captured application storage exactly unchanged. After selecting another tab's weekday and closing the weekday picker without editing an assignment, storage is not byte-for-byte unchanged:

- `mealRotationPlansV1.activeId` changes to the navigated tab.
- Empty per-tab last-top-meal, recipe-filter, override, and weekday-category cache values can be written.
- The plans' actual assignments, recipe definitions, temporary schedules, and grocery progress remain unchanged.

This is view navigation/default-cache persistence, not a demonstrated scheduling or data-loss defect. The current tests' “no writes on Cancel” claim applies to the launcher, not the complete day-picker route. If the requirement intends literally zero storage writes after canceling that longer route, that boundary also needs adjustment and an explicit test.

## Functional verification

| Area | Result and evidence |
| --- | --- |
| Empty collections and fresh installation | Both clear actions appear; empty group cards/order controls are suppressed. Fresh installs retain Breakfast/Lunch/Dinner through reload. Both no-group and existing-empty-group fixtures pass. |
| Add Recipe onboarding | Uses the full editor and Stage 3 rotation/grocery defaults. Cancel/Escape before Continue create no recipe or group. Explicitly creating a group with Continue, then canceling recipe creation, retains exactly that empty group through reload. |
| Import onboarding | Actual file-chooser upload reaches the existing parser and group-selection workflow. Synthetic JSON recipe ingredients/instructions import correctly with new-recipe defaults. Import-source Escape cancellation changes no recipes. Existing import/refresh suites also pass. |
| Setup prompt | Absent without recipes and when any tab has a configured weekday key. An intentionally empty weekday counts as configured. Explicit assignments target the selected tab/day. Unrelated plans, temporary meal identity/quantities/checks, labels, recipe definitions, and settings survive reload and backup restoration. |
| Setup failure handling | Injected plan-write failure preserves durable data and recipe definitions, exposes the existing warning/recovery export, and saves the requested assignment after Retry Save. |
| Terminology | User-facing Rotate Meals/Rotate Back labels replace the former exact button/dialog terminology. Internal cycle identifiers remain unchanged. Selection, history, linked-side, and grocery regressions were checked independently; known baseline failures are separated below. |
| Needs Adjusting | Controls remain functional; compact 16px symbols retain 44px targets. Removal confirmation explicitly says recipes are not deleted. Existing status/removal/rotation tests pass. |
| Membership and assignment controls | Saved secondary memberships/assignments use trash icons; pending unsaved rows retain Cancel. Existing scoped handlers are unchanged. Shared-member removal preserves the other recipe record/content; scheduled-day removal preserves permanent records and assignments. |
| Group deletion | Safe Keep recipes action receives initial focus. Escape and Cancel preserve records; Tab wrapping works in this dialog. Keep/move into a new destination retains exact recipe IDs and every field except the intended category; Undo restores the exact prior records. Unaffected grocery checks survive. Shared-destination merging, reload, and backup cases pass. Permanent deletion remains an explicit separately labeled destructive action. |
| Narrow layouts | Independent 280/320/360px checks find no page overflow in the new empty/setup flows; Rotate labels fit their buttons and wrap as whole controls. Group-delete dialog stays within the viewport. At 280px the longer rotation controls add a row: header height changes from 77px to 124px. No clipping or inaccessible button was observed. The older 14px heading-gap assertion remains failing as described below. |
| Synchronization/isolation | Shared application JavaScript matches after the expected storage-provider substitution and test-banner sticky-offset additions. CSS matches after removing test-banner CSS and normalizing blank lines. Test storage adapter/reset code is unchanged. Production sentinel storage survives test-app workflows. Inline JavaScript syntax check passes. |

## Reported failures: independent baseline comparison

| Suite | Independently reproduced result | Attribution |
| --- | --- | --- |
| `occasional_meals_browser.py` | Legacy Side restoration assertion at line 87 fails in both applications before and after Stage 4. | Previously confirmed legacy Side issue; retained separately, not a new Stage 4 regression. |
| `rotation_no_duplicates_browser.py` | Weekend case fails line 83, `duplicate Lentils regression`, with identical actual scheduled rows before/after: Saturday Weekend ID 4, Sunday Weekend ID 2, Lunch Tuesday Weekend ID 3. | Pre-existing scheduling failure. |
| `cycle_linked_occurrences_browser.py` | Line 73 fails `legacy-pin / independent occurrence moved`, with the same Thursday occurrence changing from ID 1 to ID 2 before/after. Compared actual rows, including linked children. | Pre-existing legacy pinned-occurrence failure. |
| `page_heading_spacing_browser.py` | The first rotation-content gap is 14px rather than the asserted 8px at 280px in both applications before/after. Unmodified pre-Stage-4 labels reproduce the same gap. | Pre-existing spacing mismatch; Stage 4 separately increases header height because of longer labels, without observed overflow. |
| `weekday_setup_browser.py` | Full suite passes, including historical height comparison, 280/320/360/390px/desktop and larger-text layout, assignment changes, Cancel, reload, and preservation checks. Historical height is 847px versus current 541px at 320px and 360px in both applications. | The earlier inability to execute the historical comparison was environmental, not an application failure. |

For rotation tests requiring the new button names, the comparison fixture used a separate copy of baseline HTML with **only** Cycle Meals/Cycle Back display strings replaced; scheduling code and data were unchanged. This adaptation allowed the current test to exercise the old engine. The legacy Side comparison and natural-label heading comparison used unchanged baseline HTML directly. Failure comparisons exercised the identified failing paths; they do not imply that the rest of those failing suites completed successfully.

The previously unavailable historical object `309866412d9b7778128c5dc8ea58f4a54b0e4f59` was fetched through GitHub. The original weekday suite's `git show` read was supplied those historical HTML bytes without changing its assertions. Its comparison completed successfully, so that missing local Git object leaves no material comparison gap in this review.

## Regression execution

The Stage 4 suite completes all **30 scenario groups**, covering both HTML variants. Together with the following 27 existing suites, **28 complete suites pass** (exit status 0); names omit `_browser.py`:

- Stage 3: `phase2_stage3_corrections`, `phase2_stage3`.
- Stage 2: `phase2_stage2_corrections`, `phase2_stage2`.
- Stage 1: `phase2_stage1_corrections`, `phase2_stage1`, `phase2_stage1_workflows`.
- Phase 1: `phase1_final_recovery_safety`, `phase1_safety_corrections`, `phase1_data_safety`.
- Groceries/rotation: `grocery_rotation_checks`, `favorites_weighted`, `scheduled_linked_slots`, `dependent_side_groups`, `shared_week_scheduling`, `outgoing_cooked_dates`.
- Recipes/groups/viewer: `needs_tweaking`, `meal_groups_bulk_safety`, `shared_recipe_management`, `add_recipe_ideas`, `recipe_tabs`, `recipe_tab_reorder`, `recipe_touch`, `group_order`, `rotation_dialog_layout`, `recipesage_refresh`.
- Weekday setup: `weekday_setup`, including the recovered historical comparison described above.

These checks cover stored ingredient exclusions and checked quantities; shared groceries and linked-side ownership; manual/temporary/empty scheduling; rotation reset/Resume/Undo/Rotate Back; queue and Favorites ledgers; Stage 2 duplicate rejection and paired-side preservation; Stage 3 content/source clearing; editor draft failure/Retry/recovery export; journals, malformed saved data, backup compatibility, and isolated test storage. Passing regression suites are evidence for the exercised fixtures, not proof against every possible saved-data combination.

Supplemental independent checks additionally verified explicit empty-group retention after recipe cancellation, exact record identity/content during Keep/move and Undo, preserved unaffected grocery checks, narrow layouts, natural-label baseline spacing, setup navigation storage differences, and the keyboard defect above. An actual destructive group-delete button test confirmed that only the target group's memberships disappear, while shared peers and unrelated records retain their IDs/content through reload and backup restoration.

## Regression-test review and missing boundaries

The new suite contains meaningful assertions against actual records, saved plan assignments, grocery progress, temporary slot identity, failed-write durable values, recovery export, reload/backup state, and production-storage sentinels. It does not merely assert button visibility.

All nine adapted existing test files were compared structurally using Python ASTs after normalizing the intended UI-label/confirmation-text substitutions. Assertions and control flow remain equivalent; no correctness check was removed or weakened by those adaptations.

Important gaps:

1. The setup test activates the launcher with the keyboard, then uses pointer clicks for weekday selection. It never checks initial focus, background traversal, or Escape after the modal handoff; this misses S4-IV-1.
2. The no-write assertion ends at launcher cancellation. It misses storage changes after navigating into another tab's day picker and closing without edits.
3. The new suite covers 320px and 360px, not 280px. Supplemental checks cover the principal new controls at 280px, but are not a replacement for committed regression coverage.
4. The Keep/move test asserts matching name/ingredients while calling it identity preservation. That could miss an unintended replacement ID or changes to other recipe fields. Supplemental non-duplicate-destination checks compared exact IDs and all fields except the intended category and verified Undo. The committed test should be strengthened accordingly.
5. Native iOS/Safari focus behavior, assistive-technology announcements, real-device touch ergonomics, and service-worker upgrade behavior were not verified. Chromium viewport/CDP touch tests cannot certify those device behaviors. These are verification limitations, not confirmed defects.

## Required follow-up

Fix the weekday-picker keyboard handoff, focus containment, and Escape dismissal used by Set Up Your Rotation, then rerun the Stage 4 suite with a real keyboard-only test through that second dialog. Keep the legacy Side and other reproduced baseline failures tracked separately. Resolve whether setup cancellation promises domain-data preservation or literally no storage writes beyond launcher cancellation, and test the chosen behavior explicitly.

**CORRECTIONS REQUIRED**
