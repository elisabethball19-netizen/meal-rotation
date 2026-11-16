# #123 phone-review corrections — code-checked; awaiting phone acceptance

Inspected current main `0de4e1b`, root AGENTS.md, updated handoff documents and the current issue #123 before editing. Reused the completed import interface and existing parsers/editor/membership/backup operations. No site data was cleared; all browser fixtures use disposable intercepted origins. No #124, grocery/card/date/group-reorder or editing-bar changes were included.

## Link-import findings and corrections

The exact phone-tested URL was not supplied. These are demonstrated path defects and synthetic-source checks, not a reproduction of screenshot 11463 or the user's source.

- `extractCompleteRecipe` produces normalized `prep`, `cook`, `total` fields. Single-review hydration calls `completeRecipeFields` again; it previously read only external time aliases and dropped normalized times. It now accepts both forms.
- The website reader can recover ingredient lines from markup while `recipeDetails.ingredients` remains empty. The review entry previously chose `recipeDetails` wholesale and ignored those recovered lines. It now carries the actual recovered lines into the editor.
- The existing corroborated HTML-card merge previously filled only instructions. It now also fills missing ingredients and valid explicit time fields for the same unambiguous recipe identity. It retains populated structured data and leaves unrelated/ambiguous recipe cards separate.
- An instructions-only direct response no longer counts as a fully populated ingredient import before existing fallback readers are considered. Review identifies unreadable/missing ingredients or cooking times rather than silently appearing complete. No exact cooking time is inferred from prose.

Remaining limitation: blocked fetches, authentication, unsupported page structures, or genuinely absent source metadata can still leave fields unavailable. The retrieved-payload warning distinguishes that condition from a complete import. The user's actual URL is needed to determine which source-specific condition caused the phone report.

## Large collection review and other corrections

- Helper is exactly “457 recipes found. Choose which groups to import.” for the 457-record fixture, without filename/hash/extension clutter. Accurate selected-group/Unassigned counts and source-tag counts remain.
- Group selection uses the existing Groceries boxed check/minus artwork with accessible Select all groups / Deselect all groups labels/tooltips and existing icon touch targets.
- Header and final actions remain outside one internal content scroller. Source groups and every optional Sides choice are reachable; the Sides review has no independent fixed-height clipping. Background scrolling is locked by the shared viewport fitter.
- Fixed an actual click-path defect found in testing: bulk construction overwrote the shared viewport height limit; focusing a checkbox could make the fitter grow/recenter the dialog between pointer down/up. Construction now retains the shared limit, keeping controls stationary.
- Removed Settings’ obsolete RecipeSage refresh action, popup and feature-only refresh/matching/safety-backup handlers. Normal RecipeSage file imports, shared import/cleanup and all backup/export/restore paths remain. No old IndexedDB safety backups or other stored recovery data are deleted. Updated reachable missing-instruction text so it does not point at the removed feature.
- Inline status keeps native draft radio events. Removed its duplicate synthetic change event and excluded status-only events from unrelated recipe-summary scans. Status stays pending until main Save, with existing Cancel/Back/Undo behavior.
- Empty-app primary action has compact spacing above/below, natural wrapping and a comfortable target. Both tab modes and the isolated test banner remain supported; no sample seeding/onboarding redesign.
- Both existing apps are equivalent in touched behavior and retain isolated storage/test features. Offline shell: v154.

## Focused checks

- `python3 tests/import_review_corrections123_browser.py` — PASS, both apps. Structured nested HowToSection/HowToStep Recipe; markup-recovered ingredients; microdata ingredients/times; mixed structured/card data; explicit prep/cook/total through review, save and reopen; cancel without additions; incomplete-source warning without invented times; absent refresh UI/handlers. Sources are explicitly mocked synthetic URLs.
- Same suite — PASS on a reproducible synthetic 457-record collection, 153 likely-side candidates, many source tags and long recipe names. Exercises select/deselect group icons, complete top-to-bottom scrolling, final Sides choice, Back cancellation with no data, final confirm importing exactly 457 sources, exactly one opted-in Sides membership, Undo and Redo. Header/footer bounds checked at 360×800, 320×640, 740×360 and 360×360, including app extra text size.
- Same suite — PASS for empty regular/test apps, tabs hidden and shown (two actual meal tabs), portrait/narrow/landscape, clear first-card spacing and no horizontal overflow.
- `python3 tests/import_settings_batch123_browser.py` — PASS, both apps. Updated only for refresh removal; retains normal source/file-format/editor/Sides/export/restore/cancel/Back/Undo/Redo/sandbox checks. No obsolete refresh reimplementation/testing in this pass.
- `node --test tests/vanilla_storage_backup.test.js`, JavaScript syntax checks, isolated inline-script syntax check and `git diff --check` — PASS. Storage unit tests use in-memory fake storage.

## Radio work/timing evidence

`tests/status_radio_performance123_browser.py` profiles 40 alternating native `.click()` toggles on a 457-record disposable collection. It counts bubbled change events and full-library filter calls during synchronous click handling; it does not measure Android touch-to-paint latency.

| Check | Unchanged main | Correction |
| --- | ---: | ---: |
| Change events | 80 | 40 |
| Full-library summary scans | 120 | 0 |
| Median synchronous click | ~0.1 ms | ~0.1 ms |
| Maximum in observed runs | ~1.3 ms | ~0.8–1.0 ms |

This establishes redundant work removal, not a measured reproduction or guaranteed resolution of the phone's perceived delay. No timer, spinner or delayed commit masks it. Phone response still needs confirmation.

## Screenshots inspected

Generated under `/workspace/work/screenshots123-correction` on disposable fixtures: source-review times, expanded ingredient/step fields, full large-review top, Sides heading and bottom, final confirmed collection, and empty-app layouts. Inspected regular and isolated apps with long names, large text, landscape and short viewport; verified foreground scrolling and reachable confirmation/cancel controls. These are Chromium emulation screenshots/history Back tests, not physical Android acceptance.

## Phone checklist

1. Open online for v154; never clear site data. Retry the original link and supply its exact URL if ingredients/times still fail. Check review, Save and reopen.
2. Import the large export through Recipe file. Scroll groups and all Sides choices, check/uncheck near the bottom, then separately test final confirm and X/Android Back cancellation.
3. Confirm obsolete refresh is gone while RecipeSage files and backups still work.
4. Try inline status response, main Save/Cancel/Back and Undo; confirm unrelated recipes/schedules remain intact.
5. Check the empty-app primary action in the isolated test app, with tabs on/off and narrow/landscape screens. Do not erase the regular app to create an empty state.

Deployment is verified after push and reported in the delivery response. Physical-phone acceptance remains pending.
