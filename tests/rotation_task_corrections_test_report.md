# Rotation/task corrections — 2026-11-14

Base: main `1eda790fb1dd3a807a7fdd14108166809f8ec875`.

## Changes

- The existing week-row gesture recognizer opens the existing Empty meal options for explicitly skipped dashes. Unassigned/ordinary empty slots are not auto-populated. Restore, Select Meal and Auto-Populate remain explicit existing actions.
- Empty-slot actions and their existing picker retain plan/day/group/date context and reject stale targets. A temporary empty slot now keeps its existing occurrence-calendar values as optional metadata. Resume restores those values before the existing task/grocery reconciliation, retaining dates and task completion identities. Existing records without that metadata remain supported, with no migration.
- A saved future-dated empty remains in the correct next-week preview; its actions target the saved occurrence. Generated next-week preview meals retain their existing read-only schedule behavior. Adding editing for generated preview meals was asked as a clarification and is not included in this batch.
- Task rows preserve entered description text exactly and generate only a short planned-day/plan-name suffix, with concise week context. Recipe titles and “meal tab” are omitted. The separate make-ahead popup date line no longer repeats the plan name.
- Task text is a button navigating to the matching plan/week and exact occurrence anchor, including occasional and inline linked recipes. It scrolls, focuses and briefly outlines that recipe. Missing occurrences show an app message rather than substituting another meal. Checkboxes only change completion. Held task editing suppresses the subsequent touch click; releasing a hold no longer dismisses the editor immediately.
- Settings now says “Show meal tabs” and has no Add Meal Tab button. Existing plus rendering already supports one plan. Existing initialization, saved-plan loading and deletion guards enforce at least one plan, so no zero-plan popup was added. Settings draft Save/Cancel behavior is retained.
- All changes are mirrored into the existing isolated test app. Offline shell version is v135. No data was cleared or extra test-app page created.

## Checks actually performed

`python tests/rotation_task_corrections_browser.py` passed for both existing pages using the existing batch1 disposable-browser fixture infrastructure:

- Skip/leave empty, long-press dash, restore/replacement/cancel; multiple groups and an additional meal in the same slot; unassigned dash distinction; stale picker rejection.
- Saved next-week empty survives reload, opens options, restores or selects a replacement on its original date. Unrelated days/plans and saved recipes remain unchanged.
- Hide/resume of an unchanged meal preserves task dates, occurrence keys, completed task, checked groceries, cooking sessions and scaling.
- Entered punctuation/whitespace retained; preparation due before the associated planned weekday; short standard-plan wording.
- Task text navigates across plans/weeks and to the correct occasional/linked recipe. Schedule/progress snapshots remain unchanged. Checkbox taps do not navigate. Mouse and CDP touch holds edit without navigation or follow-up dismissal; a subsequent checkbox tap still completes the task. Missing occurrence is handled without navigation.
- Populated-card recipe tap and CDP touch-held options remain functional. Ordinary touch movement on an empty slot does not invoke scheduling commands.
- One-plan strip/plus, actual Settings Save/Cancel buttons, hidden/shown reload, unchanged plan IDs/data and cancellation of the existing plus dialog.
- 320px and 360px/reduced-height layouts; no horizontal overflow, task buttons remain in bounds. Screenshots reviewed.

`python tests/rotation_interface_batch_browser.py` passed for both pages after updating only the approved task/Settings expectations. Existing weekday order and bulk presentation checks remain passing.

`node --check ui.js`, `recipes.js`, `service-worker.js`, all inline scripts in `meal-rotation-test.html`, changed-function parity and `git diff --check` passed.

No broad regression audit was run. Physical-phone touch/scroll, keyboard layout and installed-PWA update behavior still require device confirmation. Generated-preview schedule editing remains outside the implemented saved-slot correction pending clarification.
