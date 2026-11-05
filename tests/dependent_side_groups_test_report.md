# Dependent side groups verification

Verified using isolated Chromium browser fixtures against both index.html and meal-rotation-test.html. No working-app data was loaded or changed.

## Implementation

Dependent weekday slots explicitly designate their main assignment using stable group IDs. They select directly from preferred source-group memberships, retain independent source queues/favorite credits, and coordinate on actual main changes. Existing independent slots remain unchanged. Optional dependency anchors initialize old schedules without replacing them. Roles commit through staged backup/validation/atomic persistence with rollback. Linked recipe placement retains priority where a destination is unambiguous. Manual side overrides last until an applicable cycle or designated main change. Full/partial Cycle Back restore external-source choices.

## Tests performed

The focused dependent suite passed 28 reported test groups across both apps, including:

- Direct sources not assigned to the day, with no duplicate placeholder membership; designated main last in assignments.
- Independent defaults, role enable/cancel/disable, external side retention on disabling, multiple preferred groups and independent sequences.
- Main rotation, manual main chooser including duplicate Keep Both, promotions, Skip, same-ID one-recipe main cycling, side-only cycling, manual outside-pool overrides and unrelated-main preservation.
- No preferences, no eligible side, tappable empty-slot chooser, recovery after an eligible recipe becomes available.
- Explicit linked source placement and suppression; repeat prevention against linked attachments and retained later weekdays.
- Repeated recipe occurrences on separate days with independent progress/scaling and retained grocery checks.
- Full and partial Cycle Back; dated outgoing main/side versus unmarked incoming meals.
- Source/placeholder renaming, old configured schedules without anchors, reload, backup compatibility and test-storage isolation.
- Atomic failures injected at plan and primary data writes: complete memory/storage equality after rollback.
- 200 favorite-weighted source selections per app: favorite 80, each regular 40, no immediate repeats/starvation; unrelated source history unchanged.
- Narrow 320px/360px portrait role selectors without horizontal overflow.

Additional regression suites passed: shared scheduling 64 groups (including 300 allocation graphs per app), grocery preservation 16, bulk safety 10, scheduled dates 46, shared editing 16, weighted rotation 12, linked slots 4, bulk workflow 8, favorite display 4, editor origin 20, and timer regressions 22. The popup-date suite separately passed 8 groups. Total: 258 reported passing groups across 13 suites. Inline JavaScript syntax and changed-block parity between regular/test apps passed.

Development fixture/assertion failures were corrected before final runs: missing fixture URL normalization, existing linked queue normalization, unchanged-key failure injection, native storage mock binding, empty fixture rerender, and card-date assertion location. Final logs contained no tracebacks.

## Limits

Mobile testing used Chromium emulation, not a physical Android device. Ambiguous explicit links retain established placement rather than guessing. Changing preferences on an unchanged main takes effect on its next applicable rotation/main change. No historical cooked dates were rewritten and no production saved data was repaired or reset.
