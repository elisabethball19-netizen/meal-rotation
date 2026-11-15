# Issue #120 — approved phone-review corrections

Implemented/code-checked, awaiting renewed physical-phone acceptance. This pass follows the updated issue body and supersedes the initial presentation. Batches #121–#124 remain untouched.

## Targeted corrections

- Shared active/preview cards use the existing colors and saved dates, with a narrow date column, group above recipe, compact linked names and a right disclosure. Parent actions use two columns; there is one expanded Favorite heart/Last cooked caption. Display switches control collapsed details without removing expanded access or changing task scheduling/To-Do visibility rules. Empty/skipped cards choose/resume inline; independently scheduled sides retain full actions.
- Title, true slot tabs and compact week controls appear in the approved order. Hold/release opens compact rename/delete management; hold/drag reorders stable IDs with edge scrolling. Cancellation and F2/Alt+Arrow alternatives are included. Real touch checks exposed synthetic-click dismissal on hold/release; opening after that click now preserves the manager.
- The advance checklist retains weekday colors, reserves a right weekday column and uses the existing cooked preference as a switch. Cancellation and the existing confirmation/Undo/Redo operation remain intact.
- The recipe viewer has an enabled-highlighted lightbulb, a reserved toolbar row for the unfinished-step jump, per-stable-ID Needs Adjusting collapse in the existing viewer-preferences record, and compact linked/source/adjusting footer actions. Existing wake lifecycle and recipe content are preserved.
- Aggregate pages omit slot tabs/+; Overview week controls and task spacing are compact. Grocery Weeks checkboxes moved inside the existing filter; scope, none/both choices, saved meal inclusion and grocery checks remain supported. As before, week preferences apply immediately; meal inclusion uses Save/Cancel.

## Date and preview diagnosis

Saved occurrences can legitimately belong to different weeks after individual advancement. The focused fixture retains **Tue Nov 17 / Wed Nov 18 / Thu Nov 12**, alongside other stored dates. The renderer reads each occurrence; it does not rewrite dates to make a uniform week.

The previous meal-plan preview filtered replacements to dates before next week's boundary and simulated all tabs. Start next week instead uses the current plan's explicit confirmation scope, including eligible meals already dated next week. In the mixed-date fixture, the previous preview retained recipe IDs 1/71 while confirmation chose 70/72 (and different Saturday choices). The corrected meal-plan preview runs the same existing operation in cloned memory and draft storage, with the same selected/retained slots. Default and selective results match confirmation. No selection, Favorite, group, manual-choice or calendar algorithm was rewritten. Existing aggregate/grocery calendar-period inclusion remains unchanged.

## Focused evidence

`python3 tests/meal_plan_batch120_browser.py` exercises both `index.html` and the existing isolated test app in disposable Chromium mobile/touch contexts:

- 320px header/card geometry, long Saturday recipe wrapping, date/group alignment, one expanded heart, display on/off, six direct actions, staged editor cancellation, skip/empty/resume and direct empty-day picker.
- Stored mixed dates, preview storage equality, default and selective preview/confirmation parity, cooked switch cancellation, single confirmation dispatch, checked manual cleanup, cooking progress/scales, prep checks, groceries and complete Undo/Redo.
- Tap switching, held-release rename/delete access, rename/order cancellation, keyboard and mouse/touch drag ordering, horizontal edge scrolling, cancelled gestures, stable IDs/selection and reload.
- Linked accompaniment versus independent-side controls and preservation of occurrence data; compact viewer footer/source actions.
- Aggregate selectors removed, compact Overview task-row height/bottom spacing, Grocery weeks current/next/both/none, immediate week preference versus staged meals, persistence and grocery-check preservation.
- Per-ID note collapse across viewer close/reopen/reload and independent linked recipes. The jump occupies toolbar space in Full/Split at 320×800 and 740×360 with normal/extra-large text and actual scrolling. Supported, denied, background/foreground, off, close and late-resolving wake requests retain their lifecycle behavior.

Mobile screenshots were captured and visually inspected for collapsed/expanded/empty cards, preview, colored checklist/switch, Overview tasks, Grocery filter, footer, and portrait/landscape Full/Split recipe views. Inspection caught and corrected the legacy sibling-card display rule, compact warning-icon spacing, and slot-manager action clipping at 320px. All five manager targets remain at least 44px and inside the dialog. These are browser screenshots, not physical-device verification.

Additional checks: `python3 tests/quota_backup_static.py`, `bash scripts/post-merge.sh`, `node --check` on changed JavaScript modules/service worker, and `git diff --check`. The static check also parses all embedded test-app JavaScript. The original test storage adapter/banner/features are retained; disposable tests preserve the working-data sentinel.

Offline shell: **v146**. Commit/push and actual GitHub Pages deployment evidence are reported separately after publishing; local checks alone do not establish deployment.

## Pending phone checklist

- Check title → slot tabs → week controls → cards, including a long Saturday recipe, linked accompaniments, independent sides, and empty/skipped cards. Toggle collapsed details; confirm only one expanded heart/date caption.
- Tap slots, hold/release to rename/delete, hold/drag near edges, cancel, and verify selected IDs/data after reload.
- Compare Next week with confirmation using default and unchecked replacements. Confirm mixed saved dates are preserved; test cooked switch, X, Undo and Redo.
- Check the lightbulb/wake behavior, unfinished-step jump in Full/Split and landscape, note collapse after reopen/reload, and footer actions.
- Check Overview task spacing and Grocery filter weeks/meals, including both/none and reload. Confirm navigation clears content and yields to dialogs/keyboard.

No physical Android, installed-PWA, or actual-device wake-lock acceptance is claimed. Close all regular/test app windows and reopen online to finish a pending update. Never clear site data.
