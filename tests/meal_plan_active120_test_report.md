# #120 NEXT ACTIVE BATCH — implemented/code-checked; awaiting phone acceptance

Inspected current main `e3295e6`, AGENTS.md, live handoff guidance and the latest active section of issue #120. Changes reuse existing calendar repair, atomic writer, occurrence identities, card actions, task navigation and viewer operations. All browser checks used disposable intercepted origins. No site data was cleared. Remaining imports, prep automation, editor/grocery/group-reorder polish and #124 remain queued.

## Tuesday date: demonstrated gap and limits

The user's saved backup was not supplied. This is a reproducible legacy mixed-date fixture, not a claim to have reproduced their saved plan.

The existing calendar renderer reads stored occurrence dates. The existing repair detects local replacement rollover from the plan's intended Tuesday to the following Tuesday, but excluded all `assignedOn <= target` records. Consequently it missed a replacement made on Tuesday itself, even with explicit skip-replacement provenance and a matching assignment timestamp.

The repair now admits that same-day boundary only when `skipReplacement` is true and the recorded assignment timestamp is on that target local date. It retains the previous guards for week anchor, exact one-week displacement, non-temporary/non-occasional occurrence, replacement provenance, assignment window and cooked progress. A prior-day future assignment, an uncertain same-day choice without the replacement flag, and unrelated later future dates remain unchanged.

The repair changes the real stored occurrence/slot date using `copyOccurrenceDate`, carries linked-only dates and dated prep/check aliases, and rekeys grocery checks with the existing stable-source operation. Recipe choices, memberships, scale/cooking contexts and history dates remain intact. The complete storage proposal uses the existing validated atomic writer; the successful repair has one normal Undo snapshot.

Test fixture: Tue Nov17 assigned on Tue Nov10 with matching timestamp → actual Tue Nov10; Wed Nov18 with previously supported late replacement evidence → Wed Nov11; unrelated Sat Nov28 remains Nov28. Tuesday prep moves from scheduled Nov17/due Nov16 to scheduled Nov10/due Nov9 with its completed state retained. Grocery check amounts/scales remain identical by stable source. Undo/Redo and reload verify actual dates, not display substitutions.

Remaining limitation: a mixed plan without sufficient replacement/assignment evidence is intentionally left unchanged. The user's exact Tuesday cause and result still require their saved-plan evidence/phone check; no blanket rebase or guessed occurrence dates were introduced.

## Other changes

- At most one My Meal Plan occurrence is expanded. Opening another clears the previous stable identity and anchors the opened card while respecting the sticky controls. Rendering and edit/planning lifecycle still use the existing identities/actions.
- Touch week-radio selection no longer leaves a large label outline; keyboard `:focus-visible` retains an accessible outline on Meals and Overview.
- The selected tab's baseline mask now overrides an older `display:none!important` rule; the baseline remains beneath inactive tabs/gaps and breaks under the selected tab. A compact gap separates the intended sticky divider from the first rounded card, removing the edge-line artifact without deleting the intended divider.
- Collapsed date columns center the weekday/date pair together; expanded cards keep that block near the top rather than centering it over the actions. Existing minimum card heights remain.
- To-Do no longer appends Due-date subtitles. Due dates, eligibility, sorting, task keys and completion remain in the model. Its section anchor now finds the actual sticky header instead of the retired direct header selector.
- Task text locates the exact current or preview source, switches plan/week and scrolls the owning card with sticky offset plus temporary soft shadow. Linked accompaniment links expose their stable occurrence identity. Preview provenance is transient task data, not a new saved format. Completion remains checkbox-only. Reduced-motion users get instant navigation and static brief feedback.
- Sync Ingredients and Auto-complete Ingredients default on when no saved boolean choice exists. Explicit false is read independently of legacy mode/ratio validation and survives recipe/link changes and reload.
- First-unfinished-step return uses one compact reserved footer row while the active target is out of view. It remains reachable during ingredients and normal/split instruction scrolling, consumes no horizontal text gutter, and hides for an in-view target, link editing, all done or no steps. It uses the active recipe/context/token. Return hides the row before aligning and aligns again on the next layout frame, avoiding the split-pane resize moving the target above the pane. It does not reset progress or introduce a timer/spinner.
- Both existing apps retain equivalent changes and separate storage. Offline shell: v155.

## Focused verification

- `python3 tests/meal_plan_active120_browser.py` — PASS, both apps: same-day repair with negative future/provenance guards; real prep/check association and grocery amounts/scales; repair Undo/Redo/reload; one expanded card; rerender identity; touch/keyboard header states and Overview; actual To-Do checkbox/text interaction; current and preview task navigation/feedback; preview no scheduling mutation; normal/split portrait/landscape step return, including linked-recipe target and long ingredients; all-done hiding; defaults and explicit OFF across legacy preference object/reload/link changes; narrow/large-text layouts; sandbox sentinel; no page JavaScript errors.
- Existing `meal_plan_batch120_browser.renewed_expansion` — PASS, both apps: Sunday versus Saturday identity/scroll, favorite/date actions, recipe/grocery/side edit Save and cancellation, completed planning collapse, empty/resume lifecycle.
- Additional reduced-motion fixture — PASS, both apps: task feedback has no CSS animation and uses the existing target card.
- `node --test tests/vanilla_storage_backup.test.js`, touched JavaScript syntax checks, isolated inline-script syntax check and `git diff --check` — PASS. Storage unit tests use in-memory fake storage.

## Screenshots inspected

`/workspace/work/screenshots120-active`: regular and isolated app headers, selected/inactive tabs, keyboard versus touch radio focus, collapsed/expanded long-name cards, current and preview task destinations, normal/split viewers at 360×800 and 740×360, linked-step return, long ingredients with reachable control, and app Extra Large text at 320×640. Also inspected the existing expansion-flow screenshots under `/workspace/work/renew120`. These are emulated Chromium/history interactions, not physical Android acceptance.

## Phone checklist

1. Open online for v155; never clear site data. Check Tuesday's actual date and prep/grocery associations. If still wrong, preserve/export the saved plan for diagnosis rather than resetting data.
2. Open two occurrence cards in sequence; test Sunday favorite/date and edit Save/Cancel, then planning completion. Confirm one card, correct identity and return position.
3. Check Meals/Overview touch radios, keyboard focus, tab baseline and date-column alignment with long names/large text.
4. Tap To-Do text versus checkbox; confirm exact plan/week/card, brief shadow and unchanged task dates/completions.
5. In normal/split portrait/landscape, scroll away from the first unfinished step and use its contextual return, including a linked recipe. Confirm saved OFF preferences remain off.

Actual deployment is verified after push and reported in the delivery response. Awaiting physical-phone acceptance.
