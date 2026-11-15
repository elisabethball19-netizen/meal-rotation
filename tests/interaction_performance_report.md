# Original-app interaction profile

Baseline: main `8513380c97babf4aa2bfe50de5dcabb3c8954986`.

Disposable, generated fixture: 200 recipe membership records representing 180 logical recipes, 2,400 recipe ingredient lines, three meal plans, 63 current-week and 63 next-week occurrences, 1,516 grocery sources, approximately 264 KB of saved app data. Includes Rotation/Ideas, shared memberships, built-in Sides/preferences, linked and simple sides, preparation tasks, manual groceries and a shopping-text edit. No private backup or existing site data was used.

Chromium, 390 × 800 viewport, fixed planning date, 4× CPU throttle; three repetitions of each action on the same fixture and conditions. Detailed call counters were disabled during latency comparisons. Each action uses the existing event handler; dialog opening excludes the intentional long-press recognition interval. Setup, editor entry and view preparation are outside the measured interval. Values below are medians in milliseconds.

| Action | Synchronous blocking before → after | Handler/save completion before → after | Frame opportunity before → after |
| --- | ---: | ---: | ---: |
| Ideas pin toggle | 10,838 → 260 | 10,838 → 261 | 10,912 → 318 |
| Grocery checkbox | 18,487 → 1,124 | 18,491 → 1,127 | 18,749 → 1,345 |
| Preparation checkbox | 19,477 → 697 | 19,477 → 697 | 19,520 → 727 |
| Main-view switch | 2,462 → 131 | 2,462 → 132 | 2,504 → 158 |
| Meal-options dialog | 392 → 23 | 393 → 23 | 423 → 45 |
| Small recipe save | 23,665 → 1,734 | 23,666 → 1,735 | 23,710 → 1,774 |
| Named-only occurrence side save | 22,412 → 1,568 | 22,414 → 1,570 | 22,458 → 1,600 |
| Select all groceries | 29,102 → 1,297 | 29,104 → 1,297 | 29,532 → 1,516 |

“Frame opportunity” measures two requestAnimationFrame callbacks after dispatch, separately from handler completion. It estimates when the browser can display feedback; it is not a screen-recorded Android first-paint measurement. Mutation-observer delivery is also collected by the opt-in harness. These substantial fixture delays reproduce the reported class of lag; actual device timings remain unmeasured. Larger saves and grocery interactions still have noticeable blocking under this throttle.

## Measured shared work and fixes

Separate diagnostic runs with call counters found approximately 2.33 million group-identity reads and 547,000 native storage reads during one pin action, with 136 week allocations. The group-rotation invariant was checked inside every recipe filter, repeatedly parsing the same group identities. Moving that invariant outside the filter and reusing the already eligible pool eliminates the multiplying work. Allocation-local candidate and side-type matching maps reuse pure derived results only for one allocation; no cache survives edits or navigation.

Calendar reconciliation calculated the same schedule twice while toggling tab-strip visibility, although visibility does not alter scheduling. It now calculates/deduplicates it once. Grocery contribution reads also saved/reconciled the plan unnecessarily; they now read an active-plan snapshot. A grocery-check operation reuses its completed next/both-period schedule snapshot only within that synchronous operation (never the temporary current/rotation queries inside preview simulation).

A pin previously ran the full structural recipe/schedule transaction. Its narrow metadata transaction now uses the existing backup validation, staged storage, atomic restore/recovery, shared identities, ordering and Undo. It avoids schedule/grocery reconciliation for a flag that cannot alter those schedules. The diagnostic pin count fell to three allocations and zero calendar reconciliations, versus 136 allocations and 12 reconciliations before. Task completion likewise retains occurrence validation, saves completion metadata without calendar reconciliation, and reuses its validated task list. Local pin/task/bulk-grocery renders skip structural persistence/reconciliation; other render callers retain existing behavior.

Saving remains synchronous. There is no delayed write queue, spinner, timer-based work deferral, schema migration or data reduction. Actual recipe/side structural saves still use existing full domain operations. Production contains no timing logs or enabled profiling hooks.

## Reproduction and focused verification

```sh
python tests/interaction_performance_browser.py --ref 8513380 --trials 3 --cpu 4 --timing-only --output /tmp/before.json
python tests/interaction_performance_browser.py --trials 3 --cpu 4 --timing-only --output /tmp/after.json
python tests/interaction_performance_checks.py
python tests/builtin_sides_browser.py
```

The baseline option serves Git source through disposable browser routes on the existing app URL; it does not create another app version. Omit `--timing-only` for diagnostic call counts (instrumentation overhead makes those latencies unsuitable for the comparison table). The functional checks exercise both existing app pages, isolated test storage, rapid shared pin/grocery/task changes, injected write failures/recovery, reload, Undo/Redo, dialog/side cancellation, recipe/side saves, current/next-week isolation, bulk selection, unaffected manual groceries and shopping edits. The Sides suite checks migration, preferences/manual protection, linked/simple sides, groceries/scaling/progress, backups and Undo/Redo. All these checks passed for both existing app pages. Syntax and changed helper parity also passed. A separate baseline/current comparison produced identical current- and next-week occurrence identities, dates and side content for the 200-record fixture. At native CPU speed, three Select/Deselect pairs took 270–370 ms for Select and 259–328 ms for Deselect in the regular app (functional run; not the throttled comparison).

Remaining phone verification: Android tap-to-painted-feedback timing, rapid physical touches/scrolling, app background/exit and reopen, and recipe/side save responsiveness with the user's actual collection. If substantial lag remains, the smallest useful additional evidence is a Chrome Performance trace of one slow checkbox or pin interaction, the deployed build version and approximate collection size; a private backup is not required to begin.
