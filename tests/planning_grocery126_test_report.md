# Issue 126 — code checked, awaiting phone test

Implemented on current modular main using the existing occurrence/check store, plan snapshots, transactional recipe scheduling, preview operation, recipe viewer tabs and isolated test app. No user site data was cleared. No other backlog item was implemented. Tuesday's reported date issue remains unresolved without the phone diagnostic; this batch makes no Tuesday repair claim.

## Behavior

- Combined groceries remains default. Saved Group by meal uses dated occurrence sections and the same source checks/quantities/manual section. Expanded aggregate content shows names only, multiple-source checkboxes, and one first-source pencil. Aggregate wording is stored with each represented contribution's quantity/scale provenance; dated edits do not bleed into another week's occurrence. Week/meal filter checkbox columns align, including wrapped names.
- Existing weekday assignment editor distinguishes served-together groups from ordered weekly sequences. Sequence positions are plan-owned stable group IDs; preview/edit/reload does not consume a turn. Explicit advance, carry-forward and Undo/Redo retain the existing plan operation. Unavailable groups are flagged and block advance.
- Future cards and the existing picker save pending choices owned by plan/group/week. Their groceries and generated prep update immediately; explicit future choices survive current changes/reload and become active on advance. Manual carry conflicts require the existing overwrite confirmation. Preview scales/checks/prep retain dated provenance as they become active.
- This-week selection replaces an automatic next-week duplicate using that future slot's group/filter rules inside the scheduling transaction. Manual/unknown future choices use weekday/next-week prompts, including the Groups scheduling entry point. No replacement rejects the operation without partial state changes.
- Scale popup retains its presets/custom Apply and adds two independent switches, both initially off. Defaults live optionally in existing scale storage; explicit 1x retains precedence. Other scheduled copies keep their prior amounts. Direct linked IDs are applied once, without recursive multiplication. Unscheduled temporary viewer scaling writes no scheduled scale/default. Legacy backups remain readable.
- Today eligibility explicitly normalizes the local due date before filtering; future tasks remain available to date/next-week views. Completed tasks cannot keep Today alive. The replaced held-name action editors are detached from plan/overview names; ordinary recipe tap, drag and distinct group/tab/task/link gestures retain their existing paths.

## Actual commands and outcomes

All passed for **index.html and meal-rotation-test.html** in disposable Chromium contexts:

- `python3 tests/planning_grocery126_browser.py` — grouped/combined partial checks and reload; names-only expansion/one pencil; future picker Save, Cancel and browser Back; saved choices/reload/advance/Undo/Redo; direct linked/default scaling; repeating assignment preview/current/advance; due-only Today; held plan name no obsolete popup, normal name tap still opens viewer.
- `python3 tests/planning_grocery126_edges_browser.py` — aggregate wording through 1x → 2x → half → 1x with original recipes/manual items preserved; automatic/protected duplicates and atomic no-replacement rejection; carried meal with sequence advance; toggle combinations/default reset/direct-only fanout; backup validation; future-only/all-complete Today hidden; 320px larger-text layouts, checkbox-column coordinate assertion, keyboard-sized edit viewport, at least 12 dated meal sections across both weeks.
- `python3 tests/planning_grocery126_flows_browser.py` — exact current-plan metadata preservation during future edits; actual picker and Groups protected-choice prompts, Cancel/Keep; pending grocery check/scale/generated prep handoff into current week; storage restore/reload plus legacy missing-scale backup; temporary linked viewer scaling without storage writes; no-link popup/custom Apply in reduced viewport; carry conflict Cancel; unavailable group rejection. Due filtering checked at Sunday/Monday and next local midnight around 23:59/00:01 in **America/Los_Angeles**.
- `python3 tests/grocery_batch122_browser.py` — existing source checks, quantity/custom wording, reload, manual/legacy source preservation and narrow/large/landscape checks.
- `python3 tests/preparation_batch125_browser.py` — existing prep amounts/dependencies/completion/editor/cancel/Undo/reload/suppression and viewer sync checks.

`bash scripts/post-merge.sh`, `node --check` on all modified JS modules/service worker and `git diff --check` passed. New fixture loads allow a 30-second navigation deadline for the large inline isolated app after one environment-load timeout; interaction assertions retain the existing short deadline.

## Screenshots inspected

Synthetic fixtures only. Inspected the entire phone viewport and scrolled bottom, not just controls in isolation. Regular and test-app future/scaling views were both inspected. Captured reduced viewport represents keyboard space; it is not an actual Android keyboard. Browser Back tests are desktop Chromium history simulation, not physical-device acceptance.

| View | Evidence |
| --- | --- |
| Combined, partial, larger text, long names | [combined-partial](evidence/issue126/combined-partial.png) |
| Many dated sections / end of list and manual items | [grouped-many](evidence/issue126/grouped-many.png), [grouped-bottom](evidence/issue126/grouped-bottom.png) |
| Alternating assignment editor | [assignment](evidence/issue126/alternating-assignment.png) |
| Editable future card and To-Do | [next week](evidence/issue126/next-week-actions.png) |
| Scaling with direct link / without links and keyboard space | [linked](evidence/issue126/scale-linked.png), [custom Apply](evidence/issue126/scale-no-links-keyboard.png) |
| Explicit protected future duplicate | [duplicate](evidence/issue126/protected-duplicate.png) |
| Aligned filter / grocery edit Save-Cancel in keyboard space | [filter](evidence/issue126/grocery-filter.png), [editor](evidence/issue126/grocery-edit-keyboard.png) |

Screenshot review caught and corrected the obsolete source-grid layout and the fieldset's two-pixel checkbox offset. Test assertions confirm final alignment.

## Phone acceptance still needed

Open https://elisabethball19-netizen.github.io/meal-rotation/index.html after closing existing app windows and reopening online to activate the normal waiting PWA update (shell v159). Never clear site data.

Check partial rice contributions across both grocery views; save/cancel a next-week choice and advance/Undo; alternate an assignment with a carried meal; try remembered/direct linked scale switches; verify only due prep appears in Today. Physical Android Back/keyboard/scroll and saved-data acceptance remain awaiting the user's phone test. Deployment evidence is reported separately after the push; a pushed commit alone is not phone verification.
