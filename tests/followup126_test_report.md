# Issue 126 — authorized phone follow-up

2026-11-16. Only the issue's top “CURRENT AUTHORIZED FOLLOW-UP — phone corrections and unified meal/sides design” section. Reused main `0736298` and the previous implemented `8ec1318` batch. Code-checked; awaiting physical-phone acceptance.

The evidenced Overview failure had two causes: its grid used the clock's week while meals used a saved plan anchor, and occurrence inclusion still compared against the clock week. It now lists actual dated occurrences using the selected saved plan anchor, including tabs-off active-plan context. Empty future cards had the same clock fallback and now use the saved plan week. No stored date was blindly rebased and existing repair guards remain intact.

The Rice fixture exposed an unprotected automatic cached choice overriding the eligible queue; scheduled-first list ordering also obscured the last-cooked queue. The group, picker and automatic choice now use the eligible queue while retaining explicit manual, favorite, retained and replacement protections. The named Rice dates produce Chili-Garlic Broth Bowls current, Thai Garlic Pork next, Chicken Curry last. Explicit date edits refresh only eligible automatic choices.

New optional serving records support fixed recipes, one-from-ordered-group rotations and simple sides. Shared inline/current/next/editor controls use the existing transactions, recipe links, progress and dated grocery identities. Other scheduled copies freeze before default changes; legacy multi-main transition requires an explicit review and retains the original source identities. Side and weekday sequence turns advance on explicit scheduling, not render. Child recipe/grocery edits are explicitly separate saves. No site data was cleared.

## Actual focused checks

All commands below passed for both `index.html` and isolated `meal-rotation-test.html`, using disposable intercepted browser origins, Chromium touch contexts, Los Angeles local time and synthetic data:

- `python tests/followup126_browser.py`: saved Tuesday anchor versus clock anchor; current/next Overview inclusion with tabs on/off and exact viewer ownership; Rice queue/group/picker/manual safeguard; actual due date versus stale due cache; scale draft cancel/reset/thumbs; current/next shared actions, inline cancellation and grouped source controls.
- `python tests/followup126_servings_browser.py`: simple current-only save/reload, fixed real links/default removal, Undo/Redo, actual future-side picker/save/current isolation, side-group and within-group rotation, preview without advancement, explicit legacy review and identical grocery source IDs, weekday Back cancellation, Last cooked changes and favorite/manual guards.
- `python tests/followup126_phone_browser.py`: unified recipe editor unchanged Save, protected other copies, both weekday-selector entry points, real advance checklist with unchecked carry retaining scale/check/custom wording/manual groceries, grouped/Combined partial checks, source-only wording, exact future viewer and reload; scale Back and two thumb controls; short landscape custom multiplier/check; narrow/large-text inline Back/cancel; due spacing and read-only diagnostic/complete backup restore.
- `python tests/followup126_edges_browser.py`: recipe-editor current-only/Always and next-week ownership, actual linked-scaling targets on frozen other copies, two main servings rotating side recipes within a group, nested viewer Back to pending sides, both-week empty/resume and saved dates, local Sunday 23:59/Monday 00:01 due/overdue/future filtering despite the Tuesday plan anchor.
- `python tests/followup126_visual_browser.py`: collapsed/expanded current and next cards, equal Overview dishes, long sides, inline recipe actions and complete check/X footer, searchable child picker/cancel, normal scale popup fitting without scroll with two real switch thumbs, large-text actions, next-side footer and group Last cooked collapsed/expanded. Both apps captured.
- `node --check` on modified JavaScript and the extracted test-app inline script; `git diff --check`; `bash scripts/post-merge.sh` including the new `serving.js` shell file. Service-worker shell is `v160` and includes `serving.js`.

No unrelated legacy test campaigns or backlog work were added. During focused visual testing, inherited two-column panel layout, button display overrides, missing up icon, action-word breaking, sticky-toolbar orientation measurement, scale-footer/navigation overlap and a hidden-panel CSS override were found and corrected. Earlier failed test attempts were also corrected where fixture carry wording or expanded UI state leaked between synthetic scenarios; final tests identify actual source rows and reset only the disposable fixture's state.

## Inspected screenshots

The following are synthetic browser captures, inspected directly, not physical-device screenshots. Normal phone is 360×800; narrow/large text uses 320×640 and reduced 320×400 viewport; short landscape is 640×360. Reduced viewports simulate keyboard space; they do not prove Android's actual keyboard behavior.

| Flow | Inspected evidence |
| --- | --- |
| Actual saved week / equal main and side rows | [Overview](evidence/issue126-followup/overview-current.png), [with sides](evidence/issue126-followup/overview-with-sides.png) |
| Current/next cards, long names and full action layout | [collapsed](evidence/issue126-followup/current-collapsed.png), [expanded](evidence/issue126-followup/current-expanded.png), [large text](evidence/issue126-followup/current-large-actions.png), [next](evidence/issue126-followup/next-parity.png) |
| Pending sides through final controls | [side actions/footer](evidence/issue126-followup/side-actions-footer.png), [simple fields](evidence/issue126-followup/simple-current-keyboard.png), [child picker](evidence/issue126-followup/side-picker.png), [next footer](evidence/issue126-followup/next-side-footer.png), [reduced viewport](evidence/issue126-followup/sides-narrow-keyboard.png) |
| Unified recipe editor, settings, legacy review | [editor](evidence/issue126-followup/unified-recipe-editor.png), [same weekday sequence](evidence/issue126-followup/settings-sequence.png), [required legacy review](evidence/issue126-followup/legacy-review.png) |
| Scale switches and reachable check/X | [normal two thumbs](evidence/issue126-followup/scale-normal-two-switches.png), [short landscape/custom](evidence/issue126-followup/scale-short-large-keyboard.png) |
| Tasks, dates and groceries | [Today](evidence/issue126-followup/todo-spacing.png), [Next Week tasks](evidence/issue126-followup/next-todo-spacing.png), [group dates](evidence/issue126-followup/groups-last-cooked.png), [expanded date](evidence/issue126-followup/groups-expanded-last-cooked.png), [grouped groceries](evidence/issue126-followup/groceries-grouped.png) |
| Isolated test app parity | [editor](evidence/issue126-followup/test-unified-recipe-editor.png), [Today](evidence/issue126-followup/test-todo-spacing.png), [short scale](evidence/issue126-followup/test-scale-short-large-keyboard.png), [reduced side footer](evidence/issue126-followup/test-sides-narrow-keyboard.png), [group dates](evidence/issue126-followup/test-groups-last-cooked.png) |

## Limits and phone acceptance

The user's exact saved Tuesday backup/date diagnostic was not supplied. These fixtures reproduce the observed clock/saved-anchor mismatch and missing-inclusion paths, but cannot establish that every date in the user's saved case is correct. Settings → Backups → meal-date diagnostic is read-only and now includes all plan anchors, actual current/next dates, nameless queue IDs/dates/provenance and actual versus stored task due dates.

Browser Back was exercised as the Android history path, including popup cancellation, return to pending sides with the same scroll position, and cancellation of a child recipe editor. Actual Android Back, keyboard, installed-PWA update and comfortable touch/return-position behavior still need physical-phone acceptance. No physical-phone test is claimed. Per-page display preferences and other backlog items remain deferred.

Deployment SHA, actual Pages build result and served-file byte verification are reported in the delivery message after push. Phone URL: https://elisabethball19-netizen.github.io/meal-rotation/index.html . Close all app windows and reopen online to activate a waiting shell update; do not clear site data.
