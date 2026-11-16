# Issue #121 — latest renewed corrections

Implemented/code-checked; awaiting phone acceptance. Started from clean current main `6c19e8a`. This report supersedes earlier #121 presentation and keep-expanded Groups editor-return wording. Only remaining approved #121 work was implemented; unrelated deferred items and #122–#124 remain queued.

## Targeted changes

- Lighter two-checkbox outline Organize icon, tighter header action cluster, Organize visible only while expanded. Header Organize entry scrolls once to the existing visible top inset; later selections retain position and long-press entry keeps the recipe reachable. Ideas handles use the far-right column without unused trailing space. The test app's existing banner inset is respected.
- Status arrows are expanded-only. Inline editing/scheduling controls are icons only, with existing pencil/cart artwork and the same calendar artwork as Week navigation, accessible names and hold labels. Favorites retain one filled name-row heart collapsed; nonfavorites show outline only expanded. Favorite algorithm/storage and current-plan expanded-only heart policy are unchanged.
- Expanded Groups rows show saved prep/cook/total/marinade independent of collapsed switches. Time/date text aligns with the name, without duplicate rows or trailing dot separators. Last cooked underlines its value/Never; its whole button opens the existing date editor. The same date treatment applies to current meal-plan cards, retaining their previous editing lifecycle.
- Closing Groups Edit recipe, Edit groceries or Schedule meal collapses only its originating row on Save, Cancel or Back. Favorite/date changes stay expanded; list position and stable identity remain. Current-plan editor returns stay expanded.
- Compact scheduling shows all seven weekdays immediately, initially unchecked. One destination auto-resolves; multiple destinations show per-day Meal group radios; none uses existing day-only scheduling. There are no native selects or redundant Meal slot fields. Styled meal-tab radios are available when enabled; hidden tabs use the exact active stored plan. Plan/day changes discard stale destination choices.

## Atomic scheduling / reuse

The single-destination scheduling validation and operation are reused for every selected day inside the existing complete-backup atomic transaction. Existing duplicate confirmation/replacement logic was extracted for shared use, without a new allocator. Decisions complete before scheduling writes begin; cancelling a duplicate child or the parent leaves no partial schedule. One final check creates one Undo entry.

Pure scheduling preserves original untouched-plan provenance rather than adding generic bulk-edit retain flags to hidden plans. Explicit duplicate replacement continues using the existing replacement and queue-protection operation. Whole-operation Undo/Redo includes affected cooking/scaling contexts, grocery source checks/amounts and make-ahead pending/check metadata. This fixed a focused failure where Undo restored the schedule but left a pending task created by duplicate replacement.

No memberships/statuses are changed by scheduling. Existing same-day duplicate rejection, manual-side protections, dates and lead-time rules remain. No date rebasing, data reset, new schema or unrelated calendar/selection algorithm was introduced. Existing test-app storage adapter/banner/features remain; shell version is **v150**.

## Focused evidence

Extended the existing `tests/group_editing_batch121_browser.py` fixture/checks only for these remaining failures. The focused suite passed for both `index.html` and `meal-rotation-test.html`; additional manual-side and inset checks passed after screenshot inspection:

- Header visibility/icon artwork, one-time scroll, no selection scroll reset, far-right handle bounds, expanded-only status arrows, collapsed filled/expanded outline favorite behavior.
- Saved time fields with switches off, no duplicate/separator row, underlined date save retaining expansion, icon-only pencil/cart/calendar actions; 320×800 and 740×360 layouts.
- Groups recipe/grocery Save and Cancel collapse; scheduling Back cancels/collapses; current meal-plan editor cancellation retains expansion.
- Multi-day 0/1/multiple destinations and different per-day choices; no preselection/native selects; one final Undo entry. Injected plan-storage failure rolls back all days, then retries successfully.
- Manual side retained despite a different linked side on the incoming recipe. Its checked cooking progress, multiplier and partial grocery amount survive, along with other days/plans, memberships and statuses. Whole Undo/Redo and reload preserve the result.
- Hidden slots schedule only in the active Lunch plan, keeping hidden Dinner data intact. Visible plan change clears stale destinations and preserves the active plan; same-day conflict rejects the entire request before writes.
- Existing duplicate Back/cancel, Keep and Use a different meal decisions remain atomic across multiple destinations and Undo.

Captured and visually inspected mobile screenshots for the compact scheduling popup, inline group details, icons/date alignment and handle placement in both apps, portrait and landscape. Inspection also corrected the isolated banner/header inset. These are Chromium browser/touch/history checks, not physical Android verification. Earlier passing membership/Back/viewer investigations were not broadly rerun.

Additional checks: `python3 tests/quota_backup_static.py` (modular/embedded syntax/parity), `bash scripts/post-merge.sh`, syntax checks on changed JavaScript modules/service worker, and `git diff --check`.

## Phone checklist

1. Expand/collapse groups; check the two-box Organize icon, action spacing, one-time entry scroll and right-edge Ideas handles. Long-press selection must keep the recipe reachable.
2. Check collapsed favorites, expanded nonfavorite outline, status arrow visibility and icon-only pencil/cart/calendar actions. Turn collapsed time switches off, expand a saved-time recipe, and edit the underlined date.
3. Save/cancel each Groups editing/scheduling action: only that row should collapse and position should remain. Favorite/date should remain open; current-plan editor returns should keep their existing behavior.
4. Select several scheduling days with zero/one/multiple groups and different per-day destinations. Switch plan, cancel/X/Back, confirm, Undo/Redo and reload. Hidden tabs must use the active plan, not Breakfast or merged hidden plans.
5. Test duplicate cancellation/Keep/Replace, protected manual sides, checked groceries/progress/scales and lead-time tasks. Confirm no partial days or unrelated meals change.

Phone-testing link: https://elisabethball19-netizen.github.io/meal-rotation/index.html

Actual commit/push and Pages deployment evidence are reported after publishing. Awaiting physical-phone acceptance; no physical Android/PWA verification is claimed. Never clear site data.
