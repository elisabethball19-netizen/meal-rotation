# Phase 2 — Stage 3 Independent Verification

Date: November 6, 2026 (UTC)

**Decision: CORRECTIONS REQUIRED**

**Confirmed blocking Stage 3 regression:** explicit grocery exclusions can be overridden by a later group-membership addition through the full Edit Meal editor. This includes an explicitly empty selection, persists through reload and backup/restore, and does not occur on verified Stage 2 source.

A separate confirmed source-link editing gap is documented below: clearing the new editor's source field can leave an effective fallback link visible. Ordinary viewer editing/navigation/defaults and the supplied Stage 3 suite pass, but those tests miss these boundaries.

## Scope and source

- Repository/branch: `elisabethball19-netizen/meal-rotation`, `codex/phase2-meal-rotation`.
- Reviewed head: [`02f82de6f4e9415769668490f2f4b67d2b0c81f1`](https://github.com/elisabethball19-netizen/meal-rotation/commit/02f82de6f4e9415769668490f2f4b67d2b0c81f1).
- Started with the [Stage 3 completion report](phase2-stage3-completion-2026-11-06.md). Inspected the implementation changes in `b7b4e2931a2356ecd3be8cf53bce5bafb3fdf659`, the test adaptations in `6f1192c3c26db01e591aa657d4d7df067220a6ad`, and the Ideas/exclusion follow-ups `a1ee04886628c5b238dc5f1fc88d5e22f16133bd` and `080ed1e4cde6472f864ad2cf4a6d60b3dd018d8f`.
- Compared with preserved verified Stage 2 correction source from `f511e8e003afacba85d00ab25fd4ed9e9ffe3d8b`.
- Retrieved files through GitHub because the workspace Git proxy was unavailable. Local Git blob hashes match published source: production `c63638ddbec886b192f6d5d6dea5dfc15506b222`, test `bbbcae580677ea84098013180ca5efa0a708fcff`, service worker `b66704b2f6b66309b6985d7e6590d4f9581e2d72`.
- Used synthetic recipes/storage, intercepted fixture requests, disposable Chromium contexts, and independent probe scripts outside repository source. No real user data was accessed. No application/test fixes, Stage 4 work, merge, or deployment occurred. Only this report is published.

## Confirmed findings

### S3-1 — High, blocking: adding a membership from a copied member resurrects excluded groceries

**Reproduction through the existing creation, ingredient chooser, group picker, and full-editor controls, in both apps:**

1. Create and schedule a reusable recipe in Sauces with `2 cups rice` and `3 apples`, explicitly including its ingredients in groceries.
2. In the ingredient chooser, exclude `2 cups rice`. Only `3 apples` contributes to groceries.
3. Use the existing group picker to **Copy** that recipe into Rice. The exclusion correctly survives this first copy. The Rice member shares the recipe identity but has no separate saved ingredient-selection array.
4. Open that Rice member's full **Edit meal** editor. Under Organization, add a further membership in Sides, then Save.

**Expected:** the shared recipe still contributes only `3 apples`; adding a group does not undo a shopping exclusion. **Actual:** `2 cups rice` returns. A variant excluding **both** ingredients likewise changes from no grocery contribution to both ingredients included.

Observed source lines after the second membership addition, backup/restore, and reload:

| Explicit selection before the addition | Effective grocery contribution afterward |
| --- | --- |
| `['3 apples']` | `['2 cups rice', '3 apples']` |
| `[]` | `['2 cups rice', '3 apples']` |

The original member's selection is not deleted; it is overridden by a new full-selection array written for the newly added member. For example, original member 22 retains `['3 apples']`, while member 24 gains both lines, and the shared-identity union includes rice again. No browser error or explanatory prompt occurs.

**Cause:** [the full editor's membership-addition branch](https://github.com/elisabethball19-netizen/meal-rotation/blob/02f82de6f4e9415769668490f2f4b67d2b0c81f1/index.html#L6744) checks only `selections[source.id]`. When the edited copy lacks its own array, the new `groceryDefaultAll` fallback selects every source ingredient, even though another member holds the explicit exclusions. The [shared selection reader](https://github.com/elisabethball19-netizen/meal-rotation/blob/02f82de6f4e9415769668490f2f4b67d2b0c81f1/index.html#L7438) correctly prioritizes explicit selections over defaults, but cannot distinguish this incorrectly materialized full array from a deliberate choice.

**Baseline confirmation:** ran the same explicit creation/exclusion/copy/full-editor sequence on both verified Stage 2 HTML files and both Stage 3 files. Stage 2 keeps only apples; Stage 3 reintroduces rice. Thus this is a new Stage 3 regression, not the known legacy Side issue or merely an old missing-selection record.

**Correction criteria:** derive a new member's selection from the shared recipe's effective explicit choices before applying defaults. Preserve partial and empty selections even when the edited member itself has no array. Add regressions combining group-picker copies with subsequent full-editor additions, editing each possible member, and reload/backup. Do not erase existing selections or disable the new defaults globally.

### S3-2 — Medium: clearing the lightweight editor's source field leaves a fallback link active

**Reproduction in both apps:** use a valid recipe record with `originalRecipeUrl`, `url`, and a fallback `sourceUrl`. Open the internal viewer → Edit Recipe, empty **Recipe source link**, and Save.

The editor clears `url` and `originalRecipeUrl`, but **View Original Recipe** remains and now points to `sourceUrl`. Reopening Edit Recipe shows a blank source field while the viewer still exposes that link. This is a mismatch between the editable field and the effective displayed source.

**Cause:** the [new editor](https://github.com/elisabethball19-netizen/meal-rotation/blob/02f82de6f4e9415769668490f2f4b67d2b0c81f1/index.html#L8249) initializes/updates only `originalRecipeUrl` and `url`; [the existing source resolver](https://github.com/elisabethball19-netizen/meal-rotation/blob/02f82de6f4e9415769668490f2f4b67d2b0c81f1/index.html#L2134) also falls back to `sourceUrl` and `ingredientImportUrl`.

**Classification:** confirmed handling gap in the new editor for existing source fields. The fallback resolver predates Stage 3; this is not a claim that Stage 3 introduced a new URL parser or storage regression. Saving a nonempty replacement URL works in the tested cases.

**Correction criteria:** make the field reflect the effective source and define/honor an explicit clearing action. Preserve import provenance separately if needed; do not silently delete unrelated import identity data. Test fallback-only records, clearing/replacement, shared members, reload, and backup/restore.

## Results by requested area

### Lightweight recipe editor

Ordinary Save, Cancel, Escape, and backdrop dismissal pass. The viewer remains open and the full Edit Meal editor remains available outside this lightweight content workflow. Linked-tab identity/order, active tab, pane scroll positions, split ratio, scaling, and unchanged completion tokens pass the Stage 3 and adapted viewer suites.

The content allowlist limits edits to ingredients, instructions, source fields, notes, and valid step links; ordinary saves preserve membership, labels, serving links, Favorites, and rotation status. Shared notes/content propagation passes the shared-recipe suite. Independent ambiguous-duplicate ingredient/instruction edits in an unscheduled preview correctly clear the formerly completed duplicate tokens; the suspected stale-preview boundary did **not** reproduce a defect.

Primary-record and ingredient-selection failed saves pass the supplied rollback/recovery cases. An additional independent selection-write failure probe verifies unchanged recipe/selection state, recovery export containing the latest ingredient/instruction/source/Unicode-note drafts, Retry Save using all those latest fields, unambiguous quantity-selection remapping, and backup/reload afterward. Other recipe selections remain unchanged. An initial independent injection against an unchanged plan key did not cause a write failure; the probe was corrected to target a changed selection record before drawing conclusions.

**Exceptions:** S3-1 affects the full editor's new default-selection fallback during membership changes. S3-2 affects clearing fallback source links in the lightweight editor. Passing ordinary edit tests do not resolve those defects.

### Grocery List recipe navigation

**Pass for tested cases.** The implementation identifies associations by recipe ID and exact contribution context, rather than display name. The Stage 3 suite verifies shared ingredients, same-name recipes, tab/weekday context, filtered contributions, long actual scroll positions, checked quantities, and unchanged captured storage after opening/closing recipes.

Independent probes additionally use the same recipe on Tuesday and Sunday, activate the precise links with the keyboard, check the viewer's recipe ID and occurrence context, and return to the prior grocery position within three pixels. Grocery sources/checks, selections, exclusions, active tab, and plans stay unchanged. One-time associations display the no-saved-recipe explanation, open no permanent viewer record, and leave the library and grocery data unchanged.

### New-recipe defaults

The ordinary defaults and explicit opt-outs pass across full creation, Create New Recipe from Change Meal, file imports, and newly fetched related recipes. New records default to In Rotation/all ingredients; explicit Ideas and grocery opt-outs remain effective in the tested paths. Related-recipe Ideas remain Ideas even with an automatically scheduled parent and after backup/reload.

Existing records receive no startup default migration. Inspected import matching/enrichment keeps status/selections separate from new-record defaults, and tested existing selections/statuses remain intact. Existing queue/Favorites suites pass their covered behavior.

**S3-1 prevents acceptance of the requested exclusion-preservation invariant across membership changes.** The new suite's first-copy regression is meaningful but stops before adding another member through a copy that lacks an explicit selection array.

## Existing-test adaptation audit

Compared all four adapted existing test files with their verified Stage 2 versions:

| File | Adaptation and independent assessment |
| --- | --- |
| `recipe_tabs_browser.py` | Replaces full-editor Save/Cancel/instruction selectors with the lightweight dialog's semantic controls. Existing tab count, active tab, scroll, new-step completion, and occurrence assertions remain. |
| `recipe_tab_reorder_browser.py` | Updates Save/Cancel selectors; retains deck order, anchor, active occurrence, scroll, keyboard, and later assertions. |
| `add_recipe_ideas_browser.py` | Adds an assertion that the new default is checked, then explicitly unchecks it before the existing Ideas-save assertions. This correctly adapts the intentional default change without removing Ideas/Cancel/draft-safety checks. |
| `phase1_safety_corrections_browser.py` | Adds `bring_to_front()` before the existing native file chooser interaction. The chooser, upload, journal, export, replacement, and recovery assertions remain required. No application picker behavior is bypassed. |

No existing correctness assertion was removed or weakened in these adaptations. They all pass independently. The defects above come from missing combination/fallback cases, not from weakening an old assertion.

## Independent regression record

Every suite below was independently executed on the reviewed source and exited successfully:

| Suite | Result |
| --- | --- |
| `phase2_stage3_browser.py` | PASS — 28 reported groups, both apps; core UI at 320/360px |
| `phase2_stage2_corrections_browser.py` | PASS — duplicate rejection and protected weighted-side history |
| `phase2_stage2_browser.py` | PASS — scheduling, creation/Undo/rollback/Retry, tabs |
| `phase2_stage1_corrections_browser.py` | PASS |
| `phase2_stage1_browser.py` | PASS |
| `phase2_stage1_workflows_browser.py` | PASS |
| `phase1_final_recovery_safety_browser.py` | PASS |
| `phase1_safety_corrections_browser.py` | PASS |
| `phase1_data_safety_browser.py` | PASS |
| `grocery_rotation_checks_browser.py` | PASS |
| `favorites_weighted_browser.py` | PASS |
| `scheduled_linked_slots_browser.py` | PASS |
| `dependent_side_groups_browser.py` | PASS |
| `shared_week_scheduling_browser.py` | PASS |
| `recipe_tabs_browser.py` | PASS |
| `recipe_tab_reorder_browser.py` | PASS |
| `recipe_touch_browser.py` | PASS |
| `add_recipe_ideas_browser.py` | PASS |
| `shared_recipe_management_browser.py` | PASS |

These passes cover Stage 1 temporary/empty state, grocery hold/reset, Undo/ordering; Stage 2 guarded scheduling, paired-side/Favorites protection, creation/tabs; and Phase 1 journals, compatibility, durable rollback, exports, pending drafts, and retry. They do not negate the independent S3-1/S3-2 reproductions.

Normalized production/test shared-script equality passes. The test-only shell outside that block is byte-for-byte unchanged, including storage prefix, banner, and reset controls. Synthetic production sentinels survive test-app cases. All inline scripts and the service worker pass `node --check`. Shell v102 was inspected, not deployed.

## Existing issue and verification limits

The known **legacy Side restoration bug remains separate**. Independently ran `occasional_meals_browser.assignment(browser, filename, 320, 'Sides')` against both verified pre-Stage 3 HTML files and both Stage 3 files. All four fail the same post-full-rotation/Back/reload assertion at line 87. No distinct new legacy Side regression was demonstrated.

Historical obsolete import/editor probes are not claimed fixed or counted as passing full suites. This review does not claim the entire repository test collection is green.

Physical-device keyboards/gestures, screen readers, real quota exhaustion/process termination, cross-tab concurrency, and installed-PWA upgrades remain unverified. Chromium emulation and injected write failures do not establish those device guarantees.

## Exit criteria

Correct S3-1's shared-selection inheritance and add the multi-step membership regressions, including empty selections and persistence. Resolve S3-2's source-field/effective-link mismatch with explicit clearing semantics and fallback-field coverage. Retain the passing viewer, navigation, defaults/Ideas, Stage 1/2, and Phase 1 checks. Re-run independent verification before requesting Stage 4 authorization.

**CORRECTIONS REQUIRED**
