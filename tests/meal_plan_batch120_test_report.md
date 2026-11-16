# Issue #120 — renewed phone-review follow-up

Implemented/code-checked, awaiting physical-phone acceptance. This report supersedes the previous mixed-date fixture's acceptance claim. Current main was pulled to `908b20e` before changes; batches #121–#124 remain queued.

## Targeted corrections and causes

- Android switches now retain semantic inputs with real DOM tracks/thumbs, distinct positions, focus and disabled styles. Manual recipe ordering uses the same switch. Reminder visibility is separate from collapsed-card details; task/multi-select checkboxes remain checkboxes.
- Touch slot gestures no longer depend on implicit pointer-capture transfer surviving Android cancellation. Native touch events distinguish tap, hold/release and hold/drag, prevent held scrolling, suppress the synthetic click, cancel cleanly and reuse existing ordering/management operations. Mouse/keyboard alternatives and stable IDs remain. Tabs restore outlined rounded tops, shaded inactive/white selected states and baseline shadows. Both pages' week buttons share Hours/Days styling.
- Meal cards contain no task checklist. The separate collapsible Today's To-Do uses eligible due/overdue tasks and disappears entirely when no eligible incomplete tasks remain, including Show completed. Future tasks remain in their separate scope. Turning reminders off preserves authored tasks/checks without exposing them on expansion.
- Collapsed content is centered vertically and left aligned; chevron/adjustment icon align to the name block. Expanded metadata/action gaps are reduced, retaining six actions in two columns and comfortable targets.
- Favorite previously restored the first category-matching card, so Sunday could reopen Saturday. Expansion now uses plan/week/day/group/recipe/parent/date identity. Favorite/date/edit/cancel preserve expansion and return scroll; completed planning changes collapse the affected occurrence only.

## Date and grocery diagnosis / repair limits

Creating an unknown replacement occurrence previously called the next-matching-weekday allocator. Replacing Tuesday/Wednesday on Sunday could assign Nov 17/18 while the plan still held Nov 12–15. Local replacements now inherit their existing slot date, falling back to the plan's week anchor. Explicit Start next week wraps the existing selection operation with a plan-week anchor; retained meals carry their checks/sides forward, and legitimate later retained dates stay later. No replacement selection algorithm was rewritten.

A one-time guarded repair recognizes only independent, non-temporary local replacement choices with an occurrence exactly one week after its anchored weekday and assignment after that weekday but before that week's end, without occurrence cooked history. It preserves original-date provenance in the plan, copies side/prep/grocery check aliases without deleting old records, validates the staged backup and commits through the existing atomic writer. Other mixed/future dates are ambiguous and remain unchanged. The phone's stored backup was unavailable; exact physical-phone data recovery is not claimed. The focused fixture reproduces Tue17/Wed18 beside Thu12–Sun15 and verifies the evidenced repair to Tue10/Wed11, with unrelated future Saturday preserved.

Groceries previously used an older calendar-boundary forecast while My Meal Plan simulated confirmation. Both now use the same isolated existing advance simulation per plan, including retained/manual meals. Grocery inclusion and lines use those chosen sources; retained scales/check amounts and custom wording follow stable identities. Viewing/filtering does not alter live scheduling. This does not implement #122's breakdown/scaling redesign.

## Focused evidence

`python3 tests/meal_plan_batch120_browser.py` runs disposable Chromium mobile/touch contexts for both existing apps:

- Real thumb movement/manual-order semantics, separate reminder preference, tabs and both pages' week controls at 320px.
- Real touch input hold/release, drag/edge scroll/cancellation, tap selection, rename/order cancellation, keyboard/mouse alternatives, stable selected IDs and reload.
- Separate collapsible To-Do, completion removing its header/eye/spacing, future isolation and reminders off.
- Sunday versus adjacent Saturday expansion/scroll after favorite, saved recipe/grocery/side/date edits, edit/picker cancellation and completed Use next/empty/resume actions.
- Evidenced mixed-date repair, unrelated future-date guard, cooking/prep history, custom wording, canonical grocery/preview sources, current/next/both/none, cancellation, confirmation and complete Undo/Redo. Selective carry-over additionally checks retained scales/check amounts, genuine future dates and reload.

Browser mobile screenshots were visually inspected for visible switch knobs, restored tabs, compact expanded/collapsed cards and alignment, separate To-Do, both pages' week controls, next plan and grocery chooser. Inspection caught wrapping settings labels; each collapsed-detail switch now occupies its own aligned row. These are browser screenshots, not physical-device verification. Unrelated passing viewer work was not rerun.

Additional checks: `python3 tests/quota_backup_static.py`, `bash scripts/post-merge.sh`, JavaScript syntax checks and `git diff --check`. The static check parses embedded test-app scripts; the original isolated storage adapter/test features and working-data sentinel are retained.

Offline shell: **v147**. Commit/push and actual Pages deployment evidence are reported after publishing; local checks alone do not establish deployment.

## Pending phone checklist

- Reopen online without clearing site data. Check visible on/off switch knobs, settings save/cancel, tabs and both pages' week buttons.
- Tap slots; hold/release to rename/delete; hold/drag at edges; cancel and reload. Confirm selection/data survive without accidental actions.
- Check centered long names, icon alignment and compact actions. Favorite Sunday next to Saturday, edit/save/cancel each action, and verify the same card/scroll returns. Completed planning actions should collapse only that card.
- Check separate To-Do collapse/completion/Show completed and reminders off; future tasks must not keep Today's section visible.
- Check current/next dates with actual saved data, next-plan/grocery recipe agreement, retained/manual meals/scales/wording/checks, all week filters, cancellation, confirmation, Undo/Redo and reload. Ambiguous legacy dates intentionally require further evidence rather than a blind reset.

Phone testing: https://elisabethball19-netizen.github.io/meal-rotation/index.html

No physical Android or installed-PWA verification is claimed. Never clear site data.
