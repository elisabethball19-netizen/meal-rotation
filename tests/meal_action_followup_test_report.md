# Small meal-action/presentation follow-up — 2026-11-14

Base: main `4303ff17b68d3fdfa735c91caf60d9f729d1cab1`.

## Changes

- The existing compact meal dialog now owns a single-use action dispatcher. It disables/removes its controls before calling the existing handler synchronously. Detached handlers and repeated taps cannot dispatch a second action from that instance.
- The dismissed surface briefly becomes a transparent input shield. Its 350ms quiet period starts after synchronous dispatch returns and extends when it absorbs a retap, protecting underlying controls and new dialogs. Action work is not postponed to a timeout. Synchronous and asynchronous failures use the existing app-message dialog and leave the page usable.
- Current meal-menu cooked-date and favorite controls use the same dispatcher. Their existing return flow uses a fresh menu after completion/cancellation; resumption checks the original plan/week. The date dialog exposes its existing overlay lifecycle to that handoff.
- Skip reuses its already calculated eligible candidate list instead of calculating it a second time. No general performance investigation was performed.
- Empty/skipped and empty-group menus no longer show Auto-Populate Meal. Existing helpers, Select Meal, Resume planned meal, long-press access and X remain.
- Task navigation places its feedback on the containing meal card, using a subtle one-second drop-shadow fade. Original card color, dimensions and normal shadow are retained. Reduced-motion mode uses a static brief shadow. Navigation, scrolling and focus stay unchanged, and normal focus-visible outlines are retained.
- Task text starts at the top of its existing button; reminder checkboxes align with the first text line in wrapped and single-line descriptions. Ideas text blocks use center alignment in their existing grid cell, with unchanged row heights, wrapping, metadata, pin/action columns and touch targets.
- Pin artwork is a straightforward SVG swap to a broader-head pushpin with a clear shoulder and stem. Existing fill, colors, footprint, flags, ordering and gestures are unchanged.
- Equivalent changes are present in the existing isolated test app. Offline shell version is v136. No migration, site-data clearing or extra test-app page was introduced.

## Checks actually run

`python tests/meal_action_followup_browser.py` passed on both existing pages using disposable browser fixtures:

- Rapid coordinate mouse/touch taps, repeated detached handlers and multiple actions on the same popup: exactly one dispatch; no underlying click; nested action becomes usable after the shield expires.
- Injected synchronous and asynchronous failures: one existing error dialog, acknowledgement and subsequent actions remain usable. No schedule/progress changes in these dispatch probes.
- Actual meal Select/cancel, Leave Empty, Resume, Undo/Redo; repeated old menu handlers do not add another change. Empty options have no Auto-Populate action.
- Cooked-date nested cancellation returns to a usable fresh meal menu; rapid favorite taps toggle once.
- Whole-card one-second shadow and removal; reduced-motion behavior; keyboard focus-visible retained. First-line checkbox/text geometry for single and multiple lines; no horizontal overflow at 320px.
- Ideas text/metadata centering and exact row-height comparison against top alignment; multiline titles stay left-aligned. Outline/fill SVG, pin toggles, CDP touch dragging and reload persistence.
- Screenshots reviewed for task alignment, card feedback and Ideas rows/pushpins.

The existing `rotation_task_corrections_browser.empty_cases` checks also passed for both pages: Skip/empty long-press, restore/replacement/cancel, saved future slots/reload, stale-target protection, unaffected slots/recipes and associated task/grocery state. Its intentional gesture helper now waits for the short tap shield; navigation assertions identify the focused recipe rather than the presentation-only card highlight.

`node --check` passed for changed JavaScript and service worker; inline test-app scripts and changed-function parity checked; `git diff --check` passed.

Physical-phone rapid retaps, native dialog transitions, scrolling and the appearance of the shadow/pushpins still need device confirmation. The separate priority-toggle delay and grocery split-view instruction positioning remain deferred. No broad regression audit was run.
