# Preferred side groups, retired Labels, membership controls and favorite display

Both regular and isolated test apps were tested in Chromium with synthetic/legacy-shaped data in isolated storage. Working-app saved data was not accessed. Test-app scenarios verify that the regular namespace remains untouched. Narrow touch viewports were 320px and 360px; existing editor, bulk and timer layout tests also exercise 740×360 landscape. Screenshots of the new editor and pairing popup were inspected.

## Architecture and behavior

- Existing groups are names in `cats`; recipe records are stable group-membership IDs joined by `linkGroup`. Existing records do not identify main versus side slots.
- Optional `mealRotationGroupIdentitiesV1` maps group names to stable IDs. It is created on configuration, included in complete backups, follows renames and removes the deleted group's mapping. Recipes/memberships are not migrated or merged. Deleted preference IDs remain visibly unavailable until explicitly removed; recreating the same name does not resurrect the old identity.
- `preferredSideGroupIds` is intrinsic recipe data and uses the existing shared-property Save mechanism. `sideGroupPairs` is per-plan/per-weekday configuration keyed by stable IDs. The existing weekday popup exposes `Side for`; no groups or weekday assignments are created automatically. Cyclic/side-as-main pairings are rejected.
- A compatible recipe belongs to the assigned side group and at least one preferred group through its existing shared memberships. Its assigned side-group membership must be In Rotation. An additional type membership can remain in Ideas without changing the assigned membership's status.
- Existing established/manual/retained selections remain exact. Unpinned paired side openings wait for the main allocation, then use the same date/variety/duplicate selection logic over compatible candidates. Skip and duplicate repair use that pool too. Explicit recipe links retain their existing priority. There is no incompatible fallback: a missing side stays empty with a compact explanation in My Rotation and can be retried by normal subsequent cycling or manually chosen.
- Queue subsequences remain independent; weighted credits are keyed by compatibility pool. Cycle Back keeps later preference edits and reconciles stable identities with restored group names.
- Labels management, editor/bulk label controls, and weekday label filters are removed. Saved labels/catalog/filter keys remain compatible and preserved; retired filters are ignored. External import source tags remain usable to choose groups.
- Group selectors remain above the editor sections: first selector has one plus, extra selectors have X, duplicate options are disabled, stable IDs/status/order remain intact on Save. Organization contains Preferred side groups and Linked meals.
- Planning lists show only filled favorite-main hearts; linked rows and regular recipes have none. Viewer/menu toggles, saved favorites and weighted rotation are unchanged. A scheduled linked target can lack `linkedTo` when it already occupied its group slot, so display suppression also checks that day's explicit recipe links.

## Browser suites — passed

| Suite | Reported test groups | Coverage |
| --- | ---: | --- |
| `preferred_side_groups_browser.py` | 20 | Main-first and side-only rotation; retained main; multiple/no preferences and unrestricted parity; independent cereal/root sequences; 100 weighted compatible cycles per app (40 favorite, 20 each regular, no immediate repeats); pool-credit preservation; Skip/Undo; manual incompatible selection; linked priority and retained side; missing/deleted groups and empty valid pools; stable ID rename and actual side-slot rename; Cycle Back across rename; cyclic-pair rejection; +/X memberships, duplicate prevention, shared preference Save/Cancel; pairing selector Cancel; old/new backups, reload and isolation. |
| `favorite_display_browser.py` | 4 | Filled main hearts only in My Rotation, Weekly Overview and Meal Groups; no regular/linked hearts or loss of linked favorite status; immediate menu toggle without closing; viewer toggle, long names, groceries/schedules/content, persistence/backups. |
| `shared_week_scheduling_browser.py` | 64 | 300 deterministic allocation graphs per app, cross-tab maximum distinct allocation, inert legacy label filters, manual protection, promotion/date ordering, repeat fallback, displayed/manual order, cycling and persistence. |
| `promotion_schedule_browser.py` | 70 | Existing ordinary/linked promotions, manual protection, no-day and already-scheduled cases, active-plan isolation, week starts, retired filter eligibility, grocery/progress preservation and reload. |
| `grocery_rotation_checks_browser.py` | 16 | Partial/full rotations, shared/moved/repeated quantities, linked priority, retained checks, tabs, editing, Undo/Cycle Back and backups. |
| `scheduled_date_integrity_browser.py` | 46 | Actual outgoing dates, week starts/boundaries, early cycling, missing dates, manual/shared/linked occurrences, disabled marking, newer history, Undo/Redo/Cycle Back, old data and backups. |
| `editor_origin_adjusting_browser.py` | 20 | Save/Cancel origins, tab/scroll/expansion, viewer and search return, adjustment note controls. |
| `compact_meal_editor_browser.py` | 8 | Four collapsed sections, timing/nested instructions/ingredients/photos/links/tasks/notes, preferred-group draft, retained legacy labels, group changes, hidden-field validation, mobile/landscape overflow and Save/Cancel. |
| `shared_recipe_management_browser.py` | 16 | Shared content/metadata and stable memberships, local status/order, untouched legacy labels/content, additions/removals, timer transfer, inline links/grocery editor, last-cooked updates, global delete, rollback and backups. |
| `favorites_weighted_browser.py` | 12 | 200 ordinary weighted cycles per app with unchanged 80:40:40:40 distribution, no repeats/starvation, Skip, one/two-recipe pools, duplicate decisions, toggles and persistence. |
| `meal_groups_bulk_browser.py` | 24 | Touch selection, scopes, success exits, legacy-label preservation with no label controls, move/promote/demote/delete, references/history/Undo and atomic failure/collision handling. |
| `meal_groups_bulk_safety_browser.py` | 10 | CDP touch/scroll cancellation, mixed Move, dependent/main-key failures, linked side progress/scales/reminders/groceries/timer, Undo/Cycle Back and reload. |
| `bulk_workflow_browser.py` | 8 | App selectors/new group, Cancel/failure retention, success exits, 120-group lists and landscape toolbar geometry. |
| `compact_recipe_timer_browser.py` | 22 | Existing single timer, live controls/indicators, hide/reopen, pause/resume, completion, Full/Split and portrait/landscape. |
| `add_recipe_ideas_browser.py` | 8 | Immediate editor, tap guard, blank-draft discard, bottom-group scrolling/focus, Save/reload and unchanged existing data. |

Total: **15 suites, 348 reported passing test groups**, including page-error assertions. Both HTML script bodies pass `node --check`; regular/test feature implementations match after accounting for their storage adapters; `git diff --check` passes. No multiple timers were implemented.

## Development findings and remaining device checks

Removing the old label-manager block initially also removed its neighboring display-order collator; that unchanged declaration was restored before final tests. Early obsolete label-control expectations and an isolated test hook were updated to the requested interface. All final suites pass; the removed controls were not reintroduced.

Compatibility requires the side recipe's additional membership in a preferred type group; preferences do not pull unrelated recipes into a slot. Pairing is explicit and does not immediately replace an existing side. Existing manual or retained choices may intentionally remain incompatible until explicitly changed/cycled. An empty compatible pool intentionally leaves that side opening empty rather than selecting an incompatible meal. Specific linked-recipe placement remains the established behavior.

Physical Android touch/keyboard rendering and installed-PWA update receipt require device verification. Browser emulation and screenshots are not a physical-device test. No working-app data was reset, repaired or reimported.
