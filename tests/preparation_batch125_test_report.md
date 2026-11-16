# Issue 125 — combined prep automation and remaining corrections

Status: implemented/code-checked; **awaiting phone acceptance**. Tuesday's exact saved-state diagnosis remains blocked; no further batch started.

## Tuesday: findings, evidence and limits

`cookingPlanningWeekStart` uses the configured first weekday, not a hardcoded Monday. `mealPlanWeekStart` separately preserves an explicit saved plan anchor or its calendar anchor. Week advancement derives from that saved anchor and the configured current boundary. Changing display order does not silently rebase saved occurrences. These are code facts, not proof of the phone's root cause.

Focused fixtures verify Tuesday-first order on Monday Nov16: the configured week begins Tue10, current Tue10/Monday16 advance in preview to Tue17/Monday23 without writes. Existing evidenced local-rollover repairs and negative prior-day/uncertain/future guards still pass. The synthetic rollover fixture supplies assignment timestamps/choice evidence deliberately; it is **not the user's missing backup**. No repair guard or occurrence/prep/grocery date was speculatively changed.

Still needed: in the affected plan on the phone, Settings → Backups → **Export meal-date diagnostic**. Inspect `firstWeekday`, new `configuredWeekdayOrder` / `planningWeekStartToday`, explicit/calendar/derived plan anchors, Tuesday's stored/slot dates, assignment date/timestamp, choice flags, cooked protection and previous repair record. Those distinguish a saved older anchor/window from a replacement or intentional future occurrence. The screenshot alone does not supply this provenance. Export is read-only and excludes recipe contents/names and unrelated plans. No site reset/restore is needed.

## Implementation

- Parent preference retains existing Save/Cancel semantics. New automatic marinating/defrost child switches default OFF, hide under parent OFF, and keep their choices. Existing manual tasks retain their semantics.
- Cached recipe-source extraction plus read-only occurrence projection covers existing, future and linked owners. No render-time whole-library migration/write or stored scaled text. IDs `automatic-prep:marinating:v1` and `automatic-prep:defrost:v1` remain stable across quantities/timing changes. Existing equivalent authored defrost/marinade tasks keep their wording, IDs and checks.
- One combined defrost task uses canonical meat lines and the established scaling formatter (fractions/ranges included). Broth/stock, cooked/canned, seasoning/flavoring, substitutes and ambiguous alternatives are excluded conservatively. Enabling defrost expresses the user's choice to receive these suggestions; detection is not proof that meat is frozen.
- Explicit marinade fields/clear instruction durations and overnight are supported; unrelated cook/rest times are not used. Existing marinade parser now accepts overnight/day units and common duration words so such recipes remain saveable. Defrost defaults to the prior local date and moves before marinade start; no dinner hour or cut/size timing is invented. Existing hour/day due-date semantics are reused.
- Generated rows use direct pencil/trash/+ controls and wrapping task textareas. Edited whole text stays verbatim; timing-only overrides keep amount scaling. Optional source overrides/suppression records stay within recipe `makeAheadTasks`, sharing existing atomic edits/backups/Undo/Redo. Deleted generated reminders stay suppressed through recipe edits, preference changes, future projections and reload. No authored task/check is deleted by turning preferences off.
- Today's labels use local tomorrow only in Today's context and omit redundant next-week wording. Future views retain weekday wording; hidden tabs omit slot names, and an unambiguous Soup/meal-slot context supplies the single suffix. Existing due-day Overview and exact owner navigation remain.
- The return jump releases its geometry hold after split layout restoration settles, then uses the existing ingredient-sync operation for the active recipe. The existing reserved arrow-only bar is unchanged. OFF remains OFF; the jump does not complete anything or change auto-complete preferences.
- A focused reload fixture exposed startup scale validation depending on a later-loaded helper/live group map. Validation now resolves group identities from the snapshot being validated, preserving strict identity checks and older saved scale contexts. No reset, data deletion or guard removal.

## Focused checks actually run

`python3 tests/preparation_batch125_browser.py` passes for `index.html` and the existing isolated test app, in disposable intercepted browser origins with **America/Los_Angeles** local time:

- Tuesday-first Monday-boundary/current/preview dates, read-only preview and existing repair/future-date guards.
- Already-scheduled and generated future owners; no duplicate tasks or writes from repeated projection. Canonical 1×/2×/½× amounts, fractions/ranges, multiple meats and stock/cooked/canned/flavoring negatives; ambiguous quantities stay unchanged. Explicit numeric/word duration, overnight, two days, unrelated cook/rest negatives and legacy equivalent-task suppression.
- Defrost-before-overnight-marination dependency; manual tasks preserved. Full-text override, deletion, source updates, timing-only override with changing scale/ingredients, stable completion, task-date carry/rescheduling, Undo/Redo and reload. Independent fixture reset is used only after proving persisted suppression to exercise a separate timing-edit branch.
- Settings enable/Save/Cancel/parent hiding/retained child values/individual child OFF. Direct recipe task edits/Cancel/Save; task popup Cancel/Save/browser Back; unmodified inline-editor Back. History Back is browser emulation, not a physical Android claim.
- Generated task completion via due-day Overview, exact future task text navigation and completion surviving reload, Today/next-week/tabs/Soup wording, local midnight boundary. Preview navigation preserves model/grocery/progress state.
- Manual-scroll versus arrow ingredient synchronization in portrait/landscape split, actual linked-tab activation, normal view and Sync OFF. Auto-complete ON and OFF remain unchanged; progress is unchanged by jumping. Viewports: 360×800, 740×360 and 320×640 with extra text.
- Isolated app keeps its production-storage sentinel unchanged.

Also passed: `node --test tests/vanilla_storage_backup.test.js`; JavaScript syntax for `state.js`, `rotation.js`, `recipes.js`, `ui.js` and extracted isolated inline scripts; `git diff --check`. Storage unit checks use fake memory, never the user's live app.

## Screenshots inspected

Touch Chromium screenshots under `/workspace/work/screenshots125`, including regular and isolated representatives:

- `*-settings-on.png`: parent/child preference alignment and retained choices.
- `*-today-generated.png`, `*-future-source.png`: actual Today quantities/wording and future source navigation.
- `*-editor-generated.png`: complete scrolled lower editor flow, long combined description and pencil/trash/+ targets at 320px/extra text.
- `*-task-popup.png`: wrapping description, Hours/Days, reachable Save/Cancel.
- `*-viewer-before-*`, `*-viewer-after-*`, `*-linked-sync.png`: normal/split, portrait/landscape/large text, preserved OFF position and active linked recipe.

Review caught narrow text wrapping and a split-layout restoration race; both were corrected before delivery. These screenshots and interaction checks do not constitute physical-phone acceptance. Commit/deployment evidence is reported with delivery after push.
