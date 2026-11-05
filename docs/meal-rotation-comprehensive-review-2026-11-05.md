# Meal Rotation — Original Review Instructions and Review Report

Review date: November 5, 2026.

This document preserves the user's original review request and the resulting report from a ChatGPT conversation. It is provided as context for another conversation; recommendations are proposals, not authorization to implement changes. Findings refer to the reviewed commit linked in the report and should be rechecked against newer code.

The report's statement that no repository files were modified describes the analysis phase. The user subsequently explicitly authorized publishing this documentation file, containing the original instructions plus the report. No application changes were authorized or made as part of publishing it.

## Original user instructions

Meal Rotation — Comprehensive Simplicity and Usability Review

Please conduct a thorough product, usability, and technical review of my Meal Rotation web app.

Repository: https://github.com/elisabethball19-netizen/meal-rotation

IMPORTANT: This is an analysis-only assignment. Do not modify any files, commit changes, remove features, or implement improvements yet.

1. Understand the app's primary purpose

Meal Rotation is fundamentally a meal-planning app, not a cooking app.

Its main purpose is to eliminate repetitive meal-planning decisions by automatically cycling through recipes and generating grocery lists.

I want someone to find substantial value in the app even if they never use any advanced features.

A new user should ideally be able to:

1. Import a collection of recipes.
2. Organize those recipes into Meal Groups.
3. Assign Meal Groups to weekdays.
4. Automatically rotate meals into a weekly plan.
5. Have the grocery list automatically populate from those meals.

This should be straightforward, intuitive, and reliable without extensive configuration.

2. Evaluate the bare-bones experience

Review the app as though you are a first-time user with no prior knowledge of its features.

Consider a hypothetical user importing 20 recipes and wanting to begin rotating meals immediately.

Investigate:

- What must they configure before the app becomes useful?
- Are the default settings appropriate?
- Are any required steps unnecessarily complicated?
- Can imported recipes immediately participate in rotation?
- Are ingredients automatically included in the grocery list?
- Can users understand Meal Groups without explanation?
- Is assigning groups to weekdays intuitive?
- Is generating the next week's meals obvious?
- Are there confusing empty states?
- Are there unnecessary confirmations, popups, or settings?
- Does the interface make the next logical action apparent?

Distinguish verified code behavior from assumptions requiring live testing.

3. Evaluate every major feature

Inspect the entire app, including the main views, dialogs, settings, and supporting systems.

For each major feature, evaluate whether it:

- Directly simplifies meal planning.
- Supports meal planning indirectly.
- Primarily assists with cooking.
- Adds useful optional flexibility.
- Creates unnecessary complexity or maintenance.

Consider features such as:

- Recipe importing and editing
- Meal Groups
- Weekday assignments
- Automatic rotation
- Manual meal changes
- Multiple meal-plan tabs
- Weekly Overview
- Grocery lists
- Favorites
- Last cooked dates
- Linked recipes
- Serve with preferences and side matching
- Make-ahead reminders
- Recipe scaling
- Internal recipe viewer
- Cooking timers
- Ingredient/instruction synchronization
- Recipe completion tracking
- Search and filtering
- Backup and restore
- Customization settings

Also identify any major features I haven't listed.

Do not assume a feature should be removed simply because it is advanced.

4. Determine whether the app is still primarily a meal planner

This is an important part of the review.

Assess whether the app's functionality, interface, and development complexity remain centered on meal planning.

Identify areas where cooking-related functionality may be competing with the primary purpose.

Distinguish between:

- Features that improve the planning experience.
- Cooking conveniences that remain unobtrusive.
- Features that may distract from or complicate planning.

I enjoy cooking conveniences, and I do not want to remove useful features unnecessarily. However, I don't want the app to gradually become a comprehensive cooking application at the expense of simple meal planning.

5. Examine progressive complexity

Advanced functionality should remain available without being required.

Verify whether the app works properly when users never configure:

- Favorites
- Linked recipes
- Serve with
- Make-ahead reminders
- Last cooked dates
- Timers
- Ingredient-step synchronization
- Advanced rotation settings

Identify any unnecessary dependencies between advanced features and the basic rotation/grocery workflow.

Consider whether optional controls are visible too prominently or make the interface harder to understand.

6. Review interface complexity

Inspect the code that generates the actual screens and dialogs.

Look for:

- Redundant controls
- Duplicated functionality
- Excessive settings
- Unnecessary nested dialogs
- Too many steps for common actions
- Inconsistent icons or interactions
- Important features hidden behind unintuitive gestures
- Overcrowded screens
- Confusing terminology
- Inconsistent navigation
- Features that could be simplified without losing functionality

Pay particular attention to mobile usability.

Do not recommend hiding essential actions merely to make screens look cleaner.

7. Review technical reliability

Inspect the core workflows for potential problems involving:

- Recipe import and data preservation
- Meal rotation and rotation history
- Group-specific rotation state
- Weekday assignments
- Linked/dependent side rotation
- Grocery-list generation
- Ingredient quantities and scaling
- Saved grocery selections
- localStorage compatibility
- Backup and restore
- Interactions between optional and core features

Identify duplicated, obsolete, or unnecessarily complicated code where it creates meaningful maintenance or regression risks.

Do not refactor anything yet.

8. Testing

Use available testing tools to verify actual behavior where possible.

Prioritize a fresh-install scenario using isolated test data, followed by existing-data compatibility checks.

Do not clear or overwrite real user data.

If browser-based interaction is available, test the complete first-time planning workflow, preferably at mobile viewport sizes.

If browser testing is unavailable, explain what you could verify through code inspection and what requires manual testing.

Do not claim that a workflow works unless you have actually verified it.

9. Categorize recommendations

Organize your findings into:

KEEP
Features that provide clear value and work well.

SIMPLIFY
Useful features or workflows that could become easier to understand or operate.

MAKE OPTIONAL OR LESS PROMINENT
Advanced features that should remain available without complicating the basic experience.

CONSIDER REMOVING
Features that duplicate functionality, add little value, or undermine the primary purpose.

Preserve useful capabilities wherever practical.

10. Prioritize findings

Rank recommendations by:

1. Impact on basic meal-planning usability.
2. Reliability and data safety.
3. Reduction in user effort.
4. Reduction in interface complexity.
5. Implementation difficulty and regression risk.

Identify the five highest-value improvements.

For each, explain the current problem, proposed solution, expected benefit, implementation risk, and whether it requires a design decision from me.

11. Deliver a written report

Please provide:

1. Executive summary.
2. Assessment of whether Meal Rotation is still primarily a meal-planning app.
3. First-time-user workflow analysis.
4. Feature-by-feature assessment.
5. Interface and navigation findings.
6. Technical reliability findings.
7. Five highest-priority improvements.
8. Lower-priority opportunities.
9. Features you recommend leaving alone.
10. Questions requiring my input before implementation.

Reference relevant files and functions when possible.

Clearly distinguish verified findings, inferred concerns, and untested scenarios.

Do not implement any changes. I want to review your findings and decide which recommendations to pursue before making modifications.

The guiding principle is:

The simplest version of Meal Rotation should be a complete, valuable meal-planning app. Advanced features should enhance that experience, never be required for it.

---

## Review report

**Meal Rotation is still primarily a meal planner, but its simplest experience does not yet deliver the complete workflow you described.** The main obstacles are defaults and setup transitions—not the mere presence of cooking features.

I also reproduced two important data-safety problems involving Cycle Back and unreadable saved data.

No repository files were modified, committed, or deployed. All testing used downloaded review copies and disposable browser profiles with synthetic data.

**1. Executive summary**

The core product is valuable: reusable Meal Groups, weekday assignments, automatic selection, manual exceptions, and consolidated groceries directly reduce repetitive planning decisions. The scheduling and grocery systems also have substantial regression coverage.

However, a first-time user importing 20 recipes encounters two additional requirements:

- Imported recipes enter **Ideas**, so they cannot automatically rotate until promoted.
- Saved ingredients do **not** automatically enter groceries. Users must select ingredients separately.

Consequently, “import → organize → assign weekdays” can still produce an empty plan, and a populated plan can still produce an empty grocery list.

My overall recommendation is to preserve the capabilities while improving the default path:

- Make imported collections immediately usable for rotation.
- Make groceries populate automatically unless users explicitly exclude ingredients.
- Make cycling easier to understand as advancing the plan.
- Preserve current recipe content when restoring scheduling history.
- Protect unreadable saved data from automatic replacement.

Evidence labels throughout this report:

- **Tested:** reproduced in isolated Chromium browser tests.
- **Code:** verified by inspecting implementation; not necessarily exercised interactively.
- **Untested:** requires additional testing.

Reviewed version: [`8c955e9`](https://github.com/elisabethball19-netizen/meal-rotation/commit/8c955e9215ac0db5bc6cbe666814fa4299c2dca7). I verified that the downloaded production HTML matched GitHub’s reported blob.

**2. Is it still primarily a meal-planning app?**

**Yes, in its main interface and core behavior.** Home emphasizes weekday meals and cycling; Meal Groups organizes the reusable library; Weekly Overview combines plans; Grocery List supports shopping.

The cooking viewer remains a separate destination reached through meal actions. The compact editor also keeps Timing, Organization, Recipe, and Notes & Reminders collapsed initially. Those are good examples of progressive complexity.

The greater concern is **technical coupling**. Cooking progress, occurrence scaling, linked recipes, grocery checks, reminders, and rotation calendars all interact with scheduling mutations. For example, `persist()` reconciles cooking data and dependent sides as part of saving recipe state. This increases the regression surface of otherwise simple planning changes.

A useful product boundary would be:

| Relationship to planning | Features |
|---|---|
| Directly simplifies planning | Groups, assignments, rotation, substitutions, skipping, groceries |
| Supports planning | Importing, search, bulk management, backups, favorites, last-cooked history |
| Cooking convenience with planning benefit | Scaling that updates groceries, make-ahead reminders, recipe notes |
| Primarily cooking convenience | Timers, split viewer, ingredient-step synchronization, completion tracking |

I would retain the cooking conveniences. Their presence does not undermine the product as long as they remain optional and failures in those systems do not prevent basic planning.

**3. First-time-user workflow analysis**

I tested a fresh installation at **390 × 844**, importing 20 synthetic recipes into Chicken and Pasta groups.

| Stage | Actual behavior | Assessment |
|---|---|---|
| First launch | Breakfast, Lunch, and Dinner tabs; Dinner selected; Chicken/Pasta/Soup starter groups; no assignments | Usable starting structure, but more concepts than a single-plan user needs |
| Find import | Settings → Data & Backups → Import recipes → choose export file | Essential acquisition action is buried among maintenance tools |
| Organize import | Select source tags to become groups; all tags initially unchecked; unmatched recipes go to Misc | Useful control, but requires understanding the group model immediately |
| Finish import | All 20 recipes entered Ideas; group cards were collapsed | Import succeeds without making the rotation ready |
| Assign Monday | Choose meal groups → Chicken | Straightforward once found |
| View Monday | “Move a meal into rotation to display it here.” | Helpful explanation, but another required task |
| Promote recipes | Open group, expand Ideas, move recipes into rotation | Works, but adds effort after importing an intended rotation collection |
| View populated plan | Meal appeared automatically | Core selection worked without advanced configuration |
| Open groceries | “No selected groceries.” | Main promise remains incomplete |
| Select ingredients | Meal → Edit grocery list → check ingredients → Save | Required per-recipe setup |
| Cycle | Cycle Meals → Rotate out all recipes | Worked; replacement survived reload |
| Cycle Back | Opens another all/select menu | Available after reload, but has data-safety problems described below |

Sources: [`showRecipeImportSelection()`](https://github.com/elisabethball19-netizen/meal-rotation/blob/8c955e9215ac0db5bc6cbe666814fa4299c2dca7/index.html#L4159), [`openWeekdayCard()`](https://github.com/elisabethball19-netizen/meal-rotation/blob/8c955e9215ac0db5bc6cbe666814fa4299c2dca7/index.html#L4861), [`grocerySelectionsForMeal()`](https://github.com/elisabethball19-netizen/meal-rotation/blob/8c955e9215ac0db5bc6cbe666814fa4299c2dca7/index.html#L6973).

**What is actually required before substantial value appears?**

Recipes need group membership, rotation eligibility, and weekday assignments. Automatic groceries additionally need ingredients and saved ingredient selections. Source tags can supply the groups, reducing organizational work when imports are well structured.

Favorites, links, Serve with, reminders, last-cooked dates, timers, synchronization, and advanced rotation configuration were **not required** for the tested basic selection and cycling workflow.

**Default assessment**

- **Appropriate:** no forced favorite setup; manual ordering off; advanced editor sections collapsed; marking cycled recipes cooked initially off.
- **Questionable:** three visible starter plans, unchecked import-group choices, all imports entering Ideas.
- **Misaligned with your stated goal:** no default ingredient inclusion.
- **Needs clearer guidance:** after import, the next action should be “Set up your rotation,” with a clear route to assignments and activation.

A user can understand the value of Meal Groups with one concrete sentence: **“A Meal Group is a collection of recipes the app takes turns choosing from.”** The interface currently expects users to infer much of that relationship.

**4. Feature-by-feature assessment**

“Keep” below means preserve the capability; it does not imply every edge case was tested.

| Feature | Product role | Recommendation and evidence |
|---|---|---|
| File recipe import | Core acquisition | **SIMPLIFY.** Twenty-recipe import worked; activation and grocery readiness remained separate. Tested |
| Website/photo import | Supports library creation | **KEEP.** Useful alternatives; external extraction and OCR reliability need live-source/device testing. Code |
| Recipe editing | Essential maintenance | **KEEP.** Compact collapsed sections are a strong improvement; reconsider burying grocery-critical ingredients inside Recipe. Tested/Code |
| Meal Groups | Core planning | **KEEP.** Explain the rotation-pool concept and improve post-import activation. Tested |
| Weekday assignments | Core planning | **KEEP.** Direct weekday interaction works; retain both direct access and central setup. Tested |
| Automatic rotation | Core planning | **KEEP.** Basic cycling worked; allocation regression tests passed. Tested |
| Manual changes | Essential flexibility | **KEEP.** Protecting deliberate choices is valuable; clarify their duration and reset behavior. Code/regression tests |
| Skip This Week | Planning exception | **KEEP.** Appropriate for real weekly variation; preserve distinction from removing a recipe from rotation. Code |
| One-time meals | Planning flexibility | **KEEP.** Supports occasional choices without changing the reusable system. Code |
| Multiple plan tabs | Optional flexibility | **MAKE LESS PROMINENT initially.** Valuable for breakfast/lunch/dinner or other plans; three empty plans need not be mandatory. Tested |
| Weekly Overview | Cross-plan planning | **KEEP.** Valuable when multiple plans are used; unnecessary as an equal destination for a single-plan beginner. Code |
| Grocery aggregation | Core output | **SIMPLIFY default inclusion.** Existing aggregation and retained-check behavior passed substantial tests. Tested |
| Grocery meal/plan exclusions | Optional shopping control | **KEEP.** Clarify that meal inclusion and ingredient inclusion are separate layers. Tested/Code |
| Favorites | Optional rotation preference | **KEEP, explain effect.** Favorites affect selection weighting; they are more than bookmarks. Code |
| Last-cooked dates | Supports variety/history | **KEEP.** Dates affect automatic ordering, but undated recipes remain eligible. Code |
| Shared recipes across groups | Library flexibility | **KEEP.** Useful, but distinguish shared membership from recipes served together. Code/regression tests |
| Linked recipes | Meal composition | **KEEP as optional.** Useful for explicit accompaniments; terminology overlaps with shared recipes. Code/regression tests |
| Serve with / side matching | Planning automation | **MAKE OPTIONAL.** Current matching and integration tests passed; empty matching pools need clear recovery. Tested |
| Make-ahead reminders / Today’s To-Do | Planning and preparation | **KEEP as optional.** Explicit tasks are useful; no tasks means no required setup. Code |
| Scaling | Planning and cooking | **KEEP.** Updating grocery quantities makes this relevant to the primary purpose. Code/regression tests |
| Internal recipe viewer | Cooking convenience | **KEEP.** Separate destination; original-recipe access remains useful. Code |
| Timers | Cooking convenience | **KEEP inside viewer.** No reason to remove merely because they are advanced. Code |
| Ingredient-step synchronization | Advanced cooking | **MAKE LESS PROMINENT.** Keep within recipe settings and contextual editing. Code |
| Cooking completion tracking | Cooking convenience | **KEEP optional.** Separate occurrence records are appropriate; avoid treating completion as mandatory planning input. Code |
| Search | Library management | **KEEP.** Increasingly important as collections grow; name it consistently as recipe search. Code |
| Labels / legacy weekday filters | Compatibility metadata | **CLARIFY.** Labels persist, but `recipeMatchesFilters()` currently always returns true. Do not imply saved filters still constrain selection. Code |
| Bulk recipe management | Reduces repetitive work | **KEEP, expose an obvious entry.** Long-press discovery is insufficient for a valuable setup tool. Code |
| Needs Adjusting and notes | Recipe quality/selection support | **KEEP optional.** Useful lightweight feedback without requiring a full cooking system. Code |
| Backup/restore | Data safety | **KEEP.** Version-2 validation and rollback are valuable; distinguish protection here from weaker ordinary-save paths. Code/regression tests |
| Undo/Redo and Cycle Back | Recovery | **KEEP, repair semantics.** These recover different kinds of actions and should not unexpectedly restore old recipe content. Tested |
| Display customization | Accessibility/preferences | **KEEP restrained.** Text size is valuable; legacy pin/opening settings should not dominate. Code |
| PWA/offline support | Everyday accessibility | **KEEP.** Shell caching is useful; real offline installation/update behavior remains untested. Code |

**5. Interface and navigation findings**

**The compact editor is already doing progressive disclosure well.** At 320px, the tested editor fit without horizontal overflow. Name, Group, and In rotation remained immediately accessible, while advanced sections were collapsed. Preserve that structure.

The main opportunities are:

- **Make import a first-class action.** Put “Import recipes” in the empty library and Meal Groups view. Keep the existing backup location as a secondary route.
- **Explain empty grocery lists precisely.** “No selected groceries” does not distinguish missing ingredients, no saved ingredient selections, excluded meals, and checked items being hidden.
- **Use consistent cycling language.** “Cycle Meals” leads to “Rotate out recipes,” then “Rotate out all recipes,” while partial cycling uses “Move selected.” These describe one operation with several vocabularies.
- **Show the planning period.** Weekday-only cards and “Cycle Meals” do not clearly communicate which dated week is being advanced. The underlying rotation calendar is more sophisticated than the visible explanation.
- **Label essential navigation visibly.** Four floating icon buttons are always visible in the multi-plan experience, but their names depend on familiarity or accessibility labels. “Menu” is also used for Meal Groups in tutorial/help copy.
- **Address floating-button overlap.** In the 320px screenshot, the vertical navigation stack occupies the right edge of several day cards. It visibly overlaps card space; obstruction of long meal names still needs a targeted test.
- **Keep normal actions discoverable without gestures.** Meal editing has a tap-accessible menu, which is good. Bulk selection and plan management rely more heavily on long-press.
- **Clarify shared membership versus linked accompaniments.** Both use linking concepts, but one shares recipe content across groups and the other adds recipes to a meal.

There is also **verified help drift**. `openHelpModal()` describes a long-press action that does not match the current Home handler, mentions an all-tabs rotation control without a corresponding visible invocation in the inspected UI, and describes Overview navigation differently from `navigateToOverviewMeal()`.

Sources: [`openHelpModal()`](https://github.com/elisabethball19-netizen/meal-rotation/blob/8c955e9215ac0db5bc6cbe666814fa4299c2dca7/index.html#L3800), [`addFloatingViewButtons()`](https://github.com/elisabethball19-netizen/meal-rotation/blob/8c955e9215ac0db5bc6cbe666814fa4299c2dca7/index.html#L4680), [`organizeMealEditor()`](https://github.com/elisabethball19-netizen/meal-rotation/blob/8c955e9215ac0db5bc6cbe666814fa4299c2dca7/index.html#L7794).

Settings also combine immediate persistence with Save/Cancel restoration and sometimes a closing confirmation. That is implemented deliberately, but it makes simple preferences feel transactional. Consider one consistent model, preserving protection for genuinely unsaved recipe edits.

**6. Technical reliability findings**

**A. High severity: Cycle Back can overwrite newer recipe changes — Tested**

Reproduction:

1. Cycle meals.
2. Edit a recipe’s name and save it.
3. Choose Cycle Back → Rotate back all recipes.
4. The saved name reverts.

My test changed `Meal 00` to `Renamed after cycling`; Cycle Back restored `Meal 00`.

`rotateAllBack()` restores an earlier state containing the full recipe collection. It preserves a whitelist of later fields such as favorites and Serve with, but does not generally preserve current recipe content.

**Expected correction:** restore scheduling state against the current library. Recipe names, ingredients, instructions, additions, and explicit deletions should survive unless the user explicitly requests a broader undo.

Source: [`rotateAllBack()` and `restoreState()`](https://github.com/elisabethball19-netizen/meal-rotation/blob/8c955e9215ac0db5bc6cbe666814fa4299c2dca7/index.html#L5646).

**B. High severity: unreadable main saved data is replaced with an empty collection — Tested**

I seeded only a disposable profile with an invalid main record. Startup silently replaced it with default groups and `meals: []`.

The initial loader catches parsing errors and continues with empty state; rendering then calls `persist()`.

**Expected correction:** preserve the original raw record, stop automatic writes, and show a recovery/export path. Unreadable data must not be treated as a new installation.

Sources: [initial loading](https://github.com/elisabethball19-netizen/meal-rotation/blob/8c955e9215ac0db5bc6cbe666814fa4299c2dca7/index.html#L3315), [`persist()`](https://github.com/elisabethball19-netizen/meal-rotation/blob/8c955e9215ac0db5bc6cbe666814fa4299c2dca7/index.html#L3672).

**C. High severity: swipe deletion bypasses the safer deletion system — Tested/Code**

The swipe-menu Delete handler directly removes a recipe and clears category overrides. The editor/bulk path instead uses dependency-aware operations and rotation-history pruning.

I reproduced this sequence:

1. Cycle.
2. Swipe-delete a recipe.
3. Cycle Back.
4. The deleted recipe reappears.

Route all deletion entry points through the same safe operation. Preserve Undo rather than adding unnecessary confirmations everywhere.

Sources: [`openMealSwipeMenu()`](https://github.com/elisabethball19-netizen/meal-rotation/blob/8c955e9215ac0db5bc6cbe666814fa4299c2dca7/index.html#L6091), `applyRecipeBulk()`, `pruneBulkRotationHistory()`.

**D. Ordinary persistence has weaker failure handling than import/bulk operations — Code**

Import checks that the primary write succeeds before adopting the imported collection. Bulk changes stage and validate writes. Those are good safeguards.

However, `persist()`, plan saves, and rotation-history writes often catch storage errors silently. A visible change can therefore appear successful without equivalent durable persistence. Some operations span multiple keys without the bulk system’s transaction-like protection.

Quota failure and concurrent-tab scenarios were **not tested**. They warrant targeted fault-injection tests before changing persistence.

**E. Grocery generation is reliable after setup, but setup is an unnecessary dependency — Tested**

The browser probe confirmed that both imported ingredient checkboxes initially remained unchecked. Selecting one ingredient produced the grocery entry.

The existing regression tests passed for:

- Partial and full cycling.
- Repeated recipes and cross-plan retention.
- Mixed checked/unchecked quantities.
- Fractions and unmeasured ingredients.
- Linked recipes, ingredient edits, reloads, and backups.

This is a reason to **preserve the aggregation/check-state system** while changing its default inclusion policy.

Sources: [`getGroceryContributions()`](https://github.com/elisabethball19-netizen/meal-rotation/blob/8c955e9215ac0db5bc6cbe666814fa4299c2dca7/index.html#L4623), `getMasterGroceryItems()`.

**F. Rotation and group-specific state are sophisticated and tested**

The allocator coordinates the whole week and multiple plans, protects manual choices, and tries distinct eligible recipes before allowing fallback repeats. Rotation queues live in recipe ordering, while plans retain additional choices, credits, overrides, and calendars.

That complexity serves real requirements. It should not be casually replaced with a simpler-looking selector.

I ran the repository’s **300 deterministic allocation graphs**, plus compatibility/filter and grocery scenarios. These passed.

Source: [`allocateScheduledWeek()`](https://github.com/elisabethball19-netizen/meal-rotation/blob/8c955e9215ac0db5bc6cbe666814fa4299c2dca7/index.html#L5353).

**G. Side matching is optional and currently well covered**

The current Serve with tests passed for offline matching, synonyms, manual overrides, empty pools, explicit links, cycling, Cycle Back, backup/restore, and the 320px editor.

Keep its fallback explanations. A failed side match should never look like a failed main-meal rotation.

**H. Quantity handling is conservative, not universal — Code**

Scaling handles recognizable leading quantities and ranges. Ambiguous lines can remain unchanged; aggregation uses recognized units and normalized ingredient names.

Do not promise universal scaling or conversion. Examples such as package sizes, alternatives, and mixed units need explicit expectations. Leaving uncertain text intact is preferable to silently producing incorrect quantities.

**I. Compatibility and backup strengths**

A legacy-shaped synthetic recipe without newer fields loaded while retaining an unknown custom field. Version-2 backup handling validates before writes and attempts rollback, with the main recipe record committed last.

The test app has a separate storage namespace. Its grocery regression scenario passed with production sentinel records intact.

However, invalid optional grocery-check metadata can deliberately block rotation/promotion. That protects data, but needs a recovery route that does not leave the primary workflow indefinitely blocked.

**J. Meaningful maintenance risks**

The production file is approximately **859 KB and 8,284 lines**, combining layout, dialogs, persistence, import parsers, scheduling, shopping, and cooking systems.

Specific risks include:

- Separate near-complete production and test HTML applications.
- Legacy view code remaining alongside replacement views.
- No-op compatibility functions and retired controls.
- Multiple implementations of similar operations, especially deletion.
- Rendering and read-oriented helpers that also save/reconcile state.
- Extensive gesture-specific handlers and document-wide interaction interception.

These justify gradual consolidation behind regression coverage—not a broad rewrite.

**Testing limits**

I tested local Chromium at mobile viewport sizes and ran selected existing suites. Existing regression suites instrument the downloaded source in memory.

I did **not** validate physical iOS/Android behavior, screen readers, real website/OCR imports, installed-PWA updates, storage exhaustion, concurrent browser tabs, or every historical backup format. No real user data was accessed or cleared.

**7. Five highest-priority improvements**

Ordered by basic usability impact, data safety, effort reduction, and implementation risk:

| Priority | Current problem | Proposed solution | Benefit | Risk | Your decision needed? |
|---|---|---|---|---|---|
| **1. Automatic grocery inclusion** | A populated plan can produce no groceries until users configure selections | Include saved ingredients by default when no explicit selection exists; retain explicit exclusions and checked states | Completes the fundamental planning-to-shopping promise | **Medium–high:** absent selections must be distinguished from intentionally empty selections; preserve existing behavior during migration | **Yes:** default inclusion and pantry-item policy |
| **2. Import-to-first-plan setup** | Imports enter collapsed Ideas and remain ineligible for rotation | Offer a clear import destination/status choice, defaulting toward rotation for a new user; follow with weekday setup | Removes substantial activation work for a 20-recipe collection | **Medium:** bulk activation affects scheduling; reuse existing protected operations | **Yes:** default status and single-plan versus three-plan onboarding |
| **3. Scheduling-only Cycle Back and unified deletion** | Cycle Back reverts saved content and can resurrect swipe-deleted recipes | Restore schedule/history against current recipes; use one dependency-aware deletion operation | Prevents loss of edits and unexpected resurrection | **High:** history, identities, linked recipes, groceries, and calendars interact | **Yes:** confirm that Cycle Back should undo scheduling only |
| **4. Safe loading and visible save failures** | Invalid main data is overwritten; some save errors are silent | Preserve unreadable records, enter recovery mode, report failed saves, and strengthen coordinated writes | Protects the user’s entire library and trust | **Medium–high:** touches startup and persistence; stage carefully | Only recovery wording and presentation |
| **5. Clear weekly advancement and navigation** | “Cycle,” “rotate out,” and “move” compete; planning period is unclear; essential routes use icons | Use consistent language, show week/date context, provide a clear advance-all action with selective options, and visibly label navigation | Reduces interpretation and repeat effort | **Low–medium** for presentation; higher if date semantics change | **Yes:** preferred terminology and week-advancement behavior |

I would address the reproduced data-safety defects before releasing changes to defaults, even though groceries and onboarding have the largest everyday usability impact.

**8. Lower-priority opportunities and recommendation categories**

**KEEP**

Preserve the allocator, grocery aggregation/check preservation, direct weekday assignment, manual exceptions, compact editor, source-recipe access, backup validation, shared memberships, and test isolation.

**SIMPLIFY**

Improve import placement, post-import guidance, empty states, cycling terminology, grocery inclusion explanations, settings save behavior, and help accuracy. Make bulk editing discoverable through a normal labeled action.

**MAKE OPTIONAL OR LESS PROMINENT**

Use a quieter initial presentation for multiple plans, weighted favorites, side relationships, reminders, manual queue ordering, synchronization, and viewer customization. Their existing capabilities should remain available.

**CONSIDER REMOVING**

I do not recommend removing a major user-facing feature on this evidence.

Candidates for later removal are implementation duplication: the unsafe legacy deletion path, obsolete view branches, unused navigation builders, and retired-control scaffolding after confirming callers and compatibility requirements. Preserve saved metadata until a deliberate migration exists.

Additional opportunities:

- Explain that favorites change rotation frequency.
- Identify grocery scope explicitly when plan tabs are hidden.
- Use clear names for “same recipe in several groups” versus “recipes served together.”
- Add targeted regression cases for the reproduced Cycle Back and corrupt-load failures.
- Keep instructions and cooking enrichment failures from dominating successful planning-import messages.
- Generate production/test variants from shared implementation while preserving separate storage.

**9. Features I recommend leaving alone**

The strongest reason to retain advanced features is that many already stay out of the basic path.

I would leave these capabilities intact:

- Full and split recipe viewing.
- Optional timers and completion tracking.
- Explicit make-ahead tasks and Today’s To-Do.
- Serve with and linked accompaniments.
- Scaling that feeds grocery quantities.
- Manual meal changes, skipping, and one-time meals.
- Shared recipes across groups.
- Text-size customization.
- Original recipe links.
- Existing backup safety checks.
- The tested allocation and grocery-check algorithms.

The needed simplification is primarily about **defaults, visibility, explanations, and safe boundaries between systems**.

**10. Questions requiring your input before implementation**

1. **Imported recipes:** should new imports default to In Rotation, with “Save as Ideas” as an alternative?
2. **Groceries:** should all ingredients be included automatically unless explicitly excluded? Should pantry exclusions be recipe-specific or global?
3. **Initial plans:** should beginners start with one Dinner plan, adding Breakfast/Lunch when needed?
4. **Cycle Back:** should it restore only scheduling decisions while preserving all later recipe edits, additions, and deletions?
5. **Weekly advancement:** should the main action mean “Plan next week,” or should cycling remain useful for advancing individual meals independently?
6. **Favorites:** do you intend a favorite to mean “cook more often,” or also want bookmarking without changing frequency?
7. **Legacy behavior:** should old label filters remain inactive, or is filter-based scheduling still an intended capability?

The app already contains a substantial meal-planning product. The highest-value direction is to make its basic promise work with fewer decisions, while retaining advanced features behind clear, reliable boundaries.
