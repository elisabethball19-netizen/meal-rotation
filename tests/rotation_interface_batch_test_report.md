# Rotation/interface batch — 2026-11-14

Base: main `e44750976fa6370a589110223e5300b3f9f915e5`.

Changes are mirrored in the existing isolated `meal-rotation-test.html`; its storage shim and test-only features are retained. Offline shell version is v134.

## Passed

- `python tests/rotation_interface_batch_browser.py`: both existing app pages, disposable touch-browser contexts. Empty Tuesday retains its position with Monday and Saturday week starts via the displayed-day source. Task wording uses task/day/recipe, natural meal-tab context, and preserves occurrence keys and due/scheduled dates through completion/uncompletion. Plus/Settings add-tab access works with tabs shown/hidden, including toggling the actual Settings checkbox.
- Same focused suite: outlined/filled pin SVG and labels; bulk selector chevrons, Remove/Add order, independent checkboxes, destination-required validation, pending group staging, outer Cancel and final Apply, Unassigned omission. At 320×800, 360×420 and 740×360 only destination groups scroll while heading, action rows and confirmation remain in bounds. Screenshots reviewed for bulk layout and pin presentation.
- `python tests/batch1_ideas_browser.py`: both pages. Pin toggles and ordering/reload/backup, manual ordering in both portions, shared memberships, demotion first placement, promotion arrows, unchanged Favorites and scheduled associated data. CDP touch dragging/cancellation, ordinary scrolling, edge scrolling, and no accidental actions; import defaults and failed-write rollback.
- `node --check ui.js`, `recipes.js`, and `service-worker.js`; all inline test-app scripts syntax checked. Changed picker/pin/task functions match the test-app copies. `git diff --check` passed.

## Existing check blocked

`python tests/today_todo_browser.py` stops before its assertions: `promotion_schedule_browser.setup` calls `slotTest.seed()` but `slotTest` is undefined. This older fixture was left unchanged. The new focused suite independently checks task text, completion and date/key preservation.

## Unconfirmed requests left pending

- `ui.js`, `renderList`: `showTop && showMealPlanTabs` renders meal tabs before aggregate-page branches, so Weekly Overview and Groceries currently retain them when enabled. Which aggregate pages should hide them remains unspecified.
- `ui.js`, `renderRotationWeekPreview` / `rotationWeekControls`: title is “My [tab name] Rotation · Next week”; the return control reads “This week.” `styles.css` rotation-week-controls rules already provide a bordered pale button, dark text, and a 40px height. Desired replacement wording/style remains unspecified.

Physical-phone keyboard, touch and installed-PWA appearance still need device confirmation. Browser checks use isolated contexts; no existing site data was cleared and no extra app version was created. Grocery split-view instruction placement and other deferred work were untouched.
