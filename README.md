# meal-rotation
personal meal rotation app

## Read and cook recipes

The existing **Open recipe** action opens an internal full-page recipe view. Tap ingredients and instruction steps to fade/unfade them. Scheduled meals keep separate progress for each plan, weekday, recipe, and linked parent; **Reset Progress** affects only the displayed occurrence. Cycling a meal out clears its progress. Meal Groups previews allow temporary taps without changing a scheduled meal's saved progress.

Use the optional **Cooking instructions** and **Recipe notes** fields in the existing meal editor. Put one step on each line and use `## Heading` for instruction sections. Existing ingredients, times, and recipe URLs remain in the same editor. The viewer links to the original recipe near the bottom. Keep Screen Awake, in Recipe settings, defaults on and requests a screen wake lock where supported.

Supported structured website/RecipeSage responses and file imports retain available instructions, sections, notes, and times. Bulk file data is imported together; missing source details are checked in the background, with unfinished work retained across refreshes. Browser access restrictions can prevent extraction. Existing nonempty recipe content is preserved when enrichment fails or returns blank fields; manual editing and the original link remain available.

Photo imports also retain recognized Instructions and Notes sections when present. Review OCR text in the editor before saving; image quality can affect recognition.

Recipe content stays on existing meal records, and cooking progress is saved separately and included in version-2 backups. Older backups remain supported. Export backups regularly. Very large libraries can exceed browser storage limits; failed saves/imports preserve prior data rather than truncating recipes. Physical-device wake-lock behavior depends on browser permissions and power settings.

## Import cleanup and related recipes

Structured imports share a conservative instruction cleanup pass: recognizable image-only entries, account prompts, website metadata, and related-recipe lists are removed from cooking instructions. Temperatures, timings, quantities, cooking headings, and uncertain text are retained. Related recipe references are kept for optional review, separately from active relationships.

After a file import, choose **Review related recipes**, or use the reference review link inside the recipe viewer. New links start unchecked; an already saved relationship remains checked. Exact source identifiers, URLs, or unique normalized titles can reuse an existing meal. Ambiguous matches require the existing Linked Meals picker. A missing recipe can be imported and linked only when a usable source provides recipe content; a failed import saves no partial changes or empty placeholders. Mentioned recipes do not enter the schedule unless you explicitly select a link, which then uses the app's existing linked-meal behavior.

To clean an existing recipe, open **Recipe settings → Review instruction cleanup / related recipes**. Compare the original, editable proposal, and removed content, then Save or Cancel. Opening recipes and restoring backups do not run this cleanup on saved instructions. Original URLs and other recipe details remain intact; import references and ordinary linked-meal IDs are included in existing backups. Sources that require login or block browser readers may need manual import.

## Install on your phone

Open https://elisabethball19-netizen.github.io/meal-rotation/index.html online once.

- Android / Chrome: open the browser menu and choose **Add to Home screen** or **Install app**.
- iPhone / Safari: choose **Share → Add to Home Screen**, then **Add**. If offered, keep **Open as Web App** enabled.

Export a backup before installing and check your meals in the installed app. Some browsers, especially on iPhone, may use separate storage for the installed app; restore the backup there if needed. Keep the same site address to retain access to existing browser data.

The app can start and use saved recipes, plans, and grocery lists offline after its first successful online setup. Website imports and loading the photo OCR reader require Internet access. Do not rely on browser storage as your only backup: uninstalling, clearing site data, or browser storage eviction can remove it.

The separate `meal-rotation-test.html` can also be installed alongside the regular app. It is named **Meal Rotation Test**, has an amber icon, and retains its isolated storage and reset control. Their installation scopes are restricted to their respective HTML pages so that opening one does not match the other installed app.

To install both, open each address directly in Chrome/Safari rather than navigating inside the other installed app:

- Regular: https://elisabethball19-netizen.github.io/meal-rotation/index.html
- Test: https://elisabethball19-netizen.github.io/meal-rotation/meal-rotation-test.html

If an older installation replaced the other app, export backups before removing the old installation and reinstalling from these two addresses. Do not clear the site's browser data. Existing installations may retain the previous broad scope until updated or reinstalled; this change preserves the app IDs, URLs, and recipe storage keys.

## Updates and deployment

Publish the HTML files together with `pwa.js`, `service-worker.js`, both `.webmanifest` files, and `icons/`. Online launches check for current app files and fall back to the cached app when offline. A service-worker update waits for existing app windows to close; it does not force an editing session to reload. Close all regular/test app windows and reopen online to finish a pending update. Updates do not clear recipe storage.

When changing the offline shell, increment `SHELL_VERSION` in `service-worker.js`. Only this app's static files are cached; imports, backup files, and unrelated site resources are excluded. Old shell caches for this app's exact scope are cleaned up after the new worker activates.

For local development, serve the checkout with an HTTP server, such as `python3 -m http.server 8000`, and open it on localhost. Installation and service workers require HTTPS in production; opening an HTML file directly still runs the app without offline installation support.

## Official app artwork

`icons/meal-rotation-original.png` preserves the supplied PNG byte for byte. The regular PNG icons are uniform, uncropped resizes with transparency retained: 16, 32, 48, 180 (Apple), 192, and 512 pixels. The ICO favicon contains 16, 32, and 48 pixel images. The test icon places the unchanged artwork inside an amber surround so the two installations are distinguishable. Manifest icons use `purpose: any`; this artwork is not declared safe for maskable cropping. Launcher presentation is controlled by the device, and existing installed icons may take time to refresh.

## Recipe viewing modes

Inside a recipe, **Split View** puts ingredients above instructions with independent scrolling. Drag the center handle (or focus it and use arrow keys) to resize the sections; **Full View** returns to the single scrolling layout. The mode and divider position are saved locally and included in backups. Changing modes does not change occurrence-specific cooking progress. Imported instruction formatting is cleaned for display without rewriting older recipe records or their progress identifiers.

In **Recipe settings** (the viewer’s gear icon), **Sync Ingredients** is a checkbox that optionally follows the instruction near the upper-middle reading position after scrolling pauses. It starts off and remembers your preference. Relevant ingredients receive a blue-tinted background without changing cooking progress. Manually browsing ingredients pauses following; scrolling instructions again or switching sync off and on resumes it. Divider dragging and ingredient taps do not request synchronization, and reduced-motion preferences are respected.

Automatic matching is conservative and local: it recognizes explicit English ingredient names, plurals and preparation words, and clearly labeled ingredient sections such as Sauce or Marinade. It does not infer missing group membership or choose between ambiguous duplicate names. Unmatched instructions leave the ingredient position unchanged. In **Edit meal → Ingredient links for steps (optional)**, select a step and choose ingredients to override automatic matching; selecting Automatic clears the correction. An empty manual selection intentionally links no ingredients. Corrections save with the meal and its backups, independently of occurrence-specific cooking progress. Exact content matching preserves links across reordering; changed, removed, or identical duplicate items invalidate links rather than redirecting them.

With Sync Ingredients enabled in Split View, completing a step fades it immediately and advances to the next step after 350 ms. Manual scrolling, another interaction, closing the recipe, and changing modes cancel pending advancement. Undoing a step and completing the final step do not advance. Reduced-motion preferences are respected.

**Auto-complete Ingredients**, beneath Sync Ingredients in the same settings panel, is optional and starts off. Sync Ingredients is disabled outside Split View; automatic ingredient completion is disabled when synchronized Split View is off. Saved preferences are retained while unavailable. When enabled, subsequent instruction completions can fade confidently associated ingredients only after every associated step is complete. Explicit ingredient taps always win, including manually restoring an automatically completed ingredient. Turning the setting on or off does not retroactively change progress. Undoing a step reevaluates its automatic ingredient marks while preserving manual choices. Session metadata is optional and backward compatible with older backups; resets and rotation remove it for the affected occurrence. Meal Groups previews keep temporary progress separate from scheduled meals.

## Linked-recipe viewer tabs

The strip beneath the four viewer toolbar icons shows recipe names without a Main prefix. The initially opened recipe is the fixed anchor and has no individual close control, even after it moves. The entire strip is hidden when only that recipe is open. Linked recipes open or select another tab. Closing an active linked tab returns to the initial recipe; closing an inactive tab leaves the current recipe selected. The toolbar X closes the whole viewer. Recipe tabs match the rounded borders and selected styling of the Breakfast/Lunch/Dinner tabs. Full names display whenever they fit; when their combined widths overflow, labels abbreviate to the first word plus the next initial (for example, Crying T… and Puerto V…). Single-word labels use ordinary ellipsis when needed. Full names remain available as accessible labels and tooltips, and recipe headings stay unchanged. The strip scrolls horizontally, with keyboard arrow/Home/End navigation and 44-pixel touch targets. Long-press a tab name for 550 ms, then drag to reorder any tab; dragging near either edge scrolls through offscreen tabs. A short swipe scrolls the strip without reordering or selecting. Close buttons retain their separate tap targets. Drag cancellation restores the previous order. Reordering preserves active selection and each tab’s occurrence, progress, scaling, mode, divider and scroll positions. The order lasts for the current viewer session (including Edit Recipe return), and opening a tab appends it without rearranging the others. No linked-meal order or relationship is saved by this gesture.

**Automatically open linked recipes in tabs**, in main **Settings → Display**, defaults off and is included in the existing view preferences and backups. When enabled, only the main recipe's direct links open initially. Opening tabs does not change rotation membership. Each tab retains Full/Split mode, divider ratio, ingredient/instruction/full-view scroll positions, progress and scaling. Switching cancels pending guided advancement and pauses synchronization until an instruction interaction resumes it. Save or Cancel an ingredient-link draft before switching. Edit Recipe returns to the same tab deck; Reset Progress affects only the active occurrence and retains its scale.

Scheduled progress and scaling continue using the existing V1 keys and `[planId, day, mealId, parentId]` identity, never a title or recipe ID alone. Linked tabs resolve only within their source occurrence's plan and day: an exact linked-parent occurrence takes precedence, followed by a unique independently scheduled instance. Another parent's occurrence, an ambiguous match, or an unscheduled source is never borrowed. Unresolved links show a temporary-progress notice and retain their progress, manual overrides and scaling in the current viewer's cache, scoped to their source occurrence. Closing and reopening a linked tab restores that state; closing the whole viewer ends temporary sessions. Different main-meal viewer sessions cannot share temporary progress. No scheduled-state migration or replacement storage is introduced, and existing backups remain compatible.

Recipe content and ingredient-to-step associations remain on the shared recipe record. Existing reconciliation retains compatible occurrence progress when content changes, without marking newly added items complete. Cycling an occurrence clears only that occurrence and its associated linked progress/scaling; other days remain independent. Grocery totals still read each scheduled occurrence's multiplier.

## Android touch handling and split divider

The entire recipe-tab strip (including tab padding, gaps and close buttons) uses one non-passive touch stream. Touch starts prevent browser takeover; a short stationary touch performs exactly one selection/close, a swipe scrolls without clicking, and a 550 ms hold starts reordering with edge scrolling. Mouse/pen use separate pointer handlers. Android pointer cancellation/capture-loss events do not cancel an ongoing touch stream; actual touch cancellation or a second finger cancels the reorder. Sorting uses CSS order while a finger is down, and commits DOM order after release, so the held element is never detached during a drag. The fixed main anchor, session-only order and independent cooking progress remain unchanged.

The split divider draws a 10px band and 3px grip inside a transparent 44px target. The target occupies its own layout space, so it does not overlay ingredient or instruction controls. Touch, mouse/pen and existing keyboard resizing preserve the per-tab split ratio using the same preference storage; vertical scrolling in each pane remains independent. Full View hides the divider. Physical-device behavior still depends on browser/OS versions; regression tests use Android-sized Chromium touch simulation, including capture-loss/pointer-cancellation event variants.

## Recipe editing and amounts

**Edit Recipe**, beside the internal recipe title, opens the existing editor and returns to the viewer after Save or Cancel. Ingredients appear above Cooking Instructions; each section remembers whether it is expanded. Both sections support photo selection and camera capture where supported. Instruction OCR uses the same text reader as ingredients, offers review and correction, and asks before replacing existing instructions. Nothing is saved until the meal's Save action. Image text recognition needs an Internet connection to load its reader.

**Scale Recipe** offers ½×, 1×, 1½×, 2×, and 3×. Scheduled occurrences save their own amount separately from cooking progress. Outside the schedule, scaling is temporary. Original ingredient text, instructions, temperatures and cooking times remain unchanged. Leading numeric amounts, common fractions, decimals and ranges scale; uncertain compound amounts and nonnumeric descriptions stay unchanged. Container sizes inside descriptions are retained. Reset Progress leaves the chosen amount intact; removing or cycling out the occurrence clears its saved multiplier.

Groceries now count scheduled occurrences individually. Quantities with matching names and units are added together; incompatible units and distinct container sizes remain separate. Base ingredient selections are retained, and compatible grocery checkmarks survive amount changes. Older backups remain supported, and current backups include multipliers and editor preferences.

The viewer’s gear opens a compact settings panel without moving the split divider or recipe scroll positions. **Keep Screen Awake** defaults on, can be turned off without closing the recipe, and remembers the choice. Disabled means no new wake-lock requests; existing locks are released. Unsupported browsers show an availability message. The preference is included in backups alongside the other viewer settings.

In the recipe editor, **Ingredient links for steps** and **Recipe notes** start collapsed. Show/Hide Recipe Notes only changes visibility; saved text (including existing whitespace) and associations remain intact while hidden. Ingredients and Cooking Instructions keep their independent remembered expansion settings.
