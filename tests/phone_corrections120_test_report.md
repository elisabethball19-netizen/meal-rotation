# Issue 120 — authorized November 16 phone correction pass

Status: implemented/code-checked; awaiting phone acceptance. No following backlog batch started.

## Tuesday: proven facts and remaining evidence

Phone reports Tue17 alongside Wed11–Sun15. No exact backup/occurrence provenance was supplied. Inspection confirms cards render stored occurrence dates; the existing migration requires a specific one-week local-replacement rollover, assignment provenance and no cooked history. A screenshot cannot establish which guard excludes the real occurrence, whether an earlier repair ran, or whether the stored future date was deliberate. No guard was relaxed and no display-only substitution or blind rebase was added.

The synthetic fixture explicitly supplies Tuesday's Nov10 assignment timestamp, skip-replacement evidence and Nov17 stored date. Its repair to Nov10, prep due-date carry, grocery checks/scales/progress preservation and Undo/Redo pass. Prior-day/uncertain assignments and a legitimate Nov28 occurrence remain protected. This establishes that guarded path's behavior, **not reproduction or diagnosis of the user's saved state**.

On the phone: select the affected meal plan in Meals, open Settings → Backups → **Export meal-date diagnostic**. The downloaded `meal-date-diagnostic.json` contains the local date/timezone, displayed context, explicit/derived/calendar anchors, occurrence/slot dates, assignment timestamps, choice/protection flags, repair eligibility and previous repair records. It excludes recipe/group/plan names, recipe contents, identifiers and unrelated plans. Uses the existing backup downloader; focused checks verify the actual download and unchanged storage. This report is needed before deciding whether any further stored-date correction is justified. Do not reset either app or restore this diagnostic as a backup.

## Changes and focused checks

`python3 tests/phone_corrections120_browser.py` exercises regular and isolated apps in disposable intercepted origins:

- Monday Nov16 prep for generated Tuesday Nov17 appears in today's Meals To-Do and Monday Overview. Exact source navigation, delayed whole-card shadow, completion across both representations/reload, and completion Undo/Redo. Preview navigation does not change recipes, schedules, groceries or progress.
- Current/next context and tabs on/off wording; custom Wednesday-first context preserves provenance rather than inferring suffix from calendar dates. Authored descriptions remain unchanged. Next-view task membership uses displayed preview occurrences, preserving retained meals/custom weekday ordering; current task scope remains the active plan.
- Source-link Add/Edit labels and chain icon; reference editor hides radios/spacing and preserves all recipe statuses/promotion metadata when saving. Rotation editor still exposes controls. Source-link Save/Cancel and browser-history Back (Android Back equivalent, not a physical Android claim).
- Group drafts validate/save before reordering; assigned-group disable guard remains. Done and Back return directly to Meal Groups with no reopened editor or handles. Reorder cancellation cancels order changes; already saved group edits remain saved. Organizing bar gets surface/top edge contrast without changing control order or height.
- Centered directional viewer arrow in the existing reserved bottom bar, normal/split at 360×800, 740×360 and 320×640 with extra-large text. Reachable target, all-done hiding, linked recipe target/pane retained. Accessible name: “Go to first unfinished step”; no visible caption.
- Long editor names/headers, grocery Both weeks summary at 320px/landscape with extra-large text, and unchanged production-storage sentinel in the isolated app.

Shared viewer source editor: `python3 tests/phone_corrections120_source_browser.py` verifies Save/Cancel and the existing Back guard (Back retains the viewer draft; explicit Cancel returns to the same viewer). Its phone popup screenshot was inspected.

Also: `node --test tests/vanilla_storage_backup.test.js`; `node --check ui.js`; `node --check recipes.js`; extracted isolated inline JavaScript syntax; `git diff --check`.

## Visual inspection

Inspected touch Chromium screenshots in `/workspace/work/screenshots120-phone`: Monday To-Do and due-day Overview, scrolled preview shadow, source editor, long/wrapped editor headers, reorder/Done, organizing toolbar, full/split viewer portrait/landscape/extra-large text, linked return target, and narrow grocery heading. Inspected representative regular and isolated screenshots. Corrected a narrow source-link flex basis and long linked-name truncation found during review. These are browser viewport checks, not physical-phone acceptance.

No site data cleared. Existing modular app/test sandbox retained. Deployment evidence is reported after push; a commit alone is not deployment evidence. Unrelated import, grocery redesign, prep automation and #124 remain queued.
