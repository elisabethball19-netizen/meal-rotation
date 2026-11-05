# Meal-action last-cooked caption verification

Test: `python tests/meal_action_cooked_date_browser.py` using isolated fixtures in both regular and test apps. Eight reported test groups passed, with no browser JavaScript errors.

## Verified

- Existing Oct 29, 2026 date and Never appear beneath the recipe title, in muted 12px text with the existing pencil icon and a comfortable tappable area.
- The old large Edit last cooked date action is absent; all other scheduled/group menu actions retain their order.
- Saved date prepopulates the existing picker. Save updates the caption without closing the action popup. Clear confirmation cancel retains the date; confirmed Clear updates to Never. Picker Cancel leaves saved data unchanged.
- Correct recipe updates, reopening and reload persistence, unchanged schedule and unrelated recipe properties.
- Show Last Cooked Date enabled/disabled: popup always displays the caption; Meal Groups card visibility still follows the preference. Change Meal retains its existing date text and behavior.
- 320px and 360px portrait layouts, long headings, and 740×360 landscape scroll reachability. Final screenshot inspected for title/date positioning and old-button removal.
- Existing shared date synchronization and persistence reused; no changes to sorting, date eligibility or rotation calculations.

The timer, grocery, shared-editing, scheduled-date and editor-origin regression suites also passed alongside this update (see dependent-side report). Inline JavaScript syntax and regular/test changed-block parity passed.

Physical Android testing remains advisable for actual device touch/viewport behavior. No working-app saved data was accessed or modified.
