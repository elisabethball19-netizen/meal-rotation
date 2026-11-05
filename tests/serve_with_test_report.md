# Serve with verification

Both app versions use the same offline matcher and existing dependent-slot coordinator. Testing used isolated synthetic legacy/current records in Chromium with 320px and 360px Android-sized touch viewports. No working-app saved data was accessed or changed.

## Implementation and compatibility

- `serveWith` is an optional shared recipe array. The Organization selector uses existing checkbox/dialog/action styles, supports five common choices plus custom words/phrases, and saves only through the normal editor Save action.
- Candidate selection first uses the assigned side group's existing In Rotation pool and ranking, then filters titles. No new groups, memberships or side classifications are created. The offline bidirectional vocabulary is centralized in `SERVE_WITH_SYNONYMS`; whole words/phrases, punctuation, case and basic plurals are normalized. Exact matches and synonym matches have equal rotation eligibility.
- Existing dependent main-change coordination, manual-side protection, linked priority, grocery reconciliation, repeat avoidance and Cycle Back remain in use. Unmatched sides remain empty with a tappable chooser indication. Empty preferences are unrestricted.
- Legacy `preferredSideGroupIds` remain stored and valid in complete backups but no longer filter recipes. No group-name-to-keyword migration is guessed. Existing schedules are not silently rewritten when the feature changes or preferences are saved; the new filter applies on the next applicable selection/main change.
- Preferences are retained through Cycle Back just like other current shared recipe metadata. No date, membership, queue or cooking-progress migration was introduced. Shell cache version advanced to v94.

## Tests performed

`tests/serve_with_browser.py`: 12 reported passing test groups across both app versions:

1. Potatoes -> Garlic Mashed Potatoes, Creamy Garlic Mash, Roasted Baby Potatoes; equal queue eligibility and successive selection; Ideas excluded.
2. Rice/pilaf, Pasta/noodles in both directions, vegetables/green beans, bread/rolls, custom quinoa/couscous/beans, multiple preferences, punctuation/plurals (including tomato/tomatoes and berry/berries), and false substring exclusions.
3. Manual main changes update the side; unrelated main stays; retained grocery checks and last-cooked dates unchanged.
4. Manual incompatible side survives unrelated changes and reload, expires on applicable side rotation.
5. No matches -> unselected side/message/existing manual chooser; no preferences -> unrestricted group.
6. Explicit incompatible linked side in assigned group keeps priority once; external matching linked source also occupies the dependent slot once.
7. Main cycle, multiple dependent weekdays/full rotation and exact Cycle Back; complete backup/restore of recipe records/schedules; old preference data retained; test namespace leaves regular-storage sentinel unchanged.
8. Shared identity editor Save synchronizes Serve with without changing sibling group or local Ideas status.
9. Single eligible side repeats safely; saving preferences leaves source queue and favorite credits unchanged.
10. Real 320/360px selector: multiple choices, custom add, deselection, Cancel, normal editor Save, reload, no unwanted schedule changes, no horizontal overflow, old control absent. Selector and editor screenshots captured and inspected.

Additional browser regressions passed: shared-week scheduling 64 groups (including 300 allocation graphs per app), grocery occurrence preservation 16, scheduled linked slots 4, favorite-weighted rotation 12, shared recipe editing/memberships 16, scheduled calendar/last-cooked integrity 46. Total: 170 reported passing groups across seven suites. Inline JavaScript syntax and changed-block parity between apps passed; git diff whitespace checks passed. No browser JavaScript errors were captured.

An initial new test failed because it accessed closure-scoped app variables directly. That fixture was corrected to use injected hooks; no application failure was concealed. Final runs passed.

## Limitations / phone checks

Title matching is deliberately limited to the built-in vocabulary and explicitly entered custom phrases. It does not infer meaning from ingredients or instructions, so unusually named sides may need another keyword or manual selection. Basic plural normalization is not a full natural-language stemmer. Ambiguous external linked destinations retain established placement rather than guessing. Physical Android testing remains advisable; no real phone was available. No multiple-timer work was included.
