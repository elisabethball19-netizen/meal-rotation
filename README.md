# meal-rotation
personal meal rotation app

## Read and cook recipes

The existing **Open recipe** action opens an internal full-page recipe view. Tap ingredients and instruction steps to fade/unfade them. Scheduled meals keep separate progress for each plan, weekday, recipe, and linked parent; **Reset Progress** affects only the displayed occurrence. Cycling a meal out clears its progress. Meal Groups previews allow temporary taps without changing a scheduled meal's saved progress.

Use the optional **Cooking instructions** and **Recipe notes** fields in the existing meal editor. Put one step on each line and use `## Heading` for instruction sections. Existing ingredients, times, and recipe URLs remain in the same editor. The viewer links to the original recipe near the bottom and automatically requests a screen wake lock where supported.

Supported structured website/RecipeSage responses and file imports retain available instructions, sections, notes, and times. Bulk file data is imported together; missing source details are checked in the background, with unfinished work retained across refreshes. Browser access restrictions can prevent extraction. Existing nonempty recipe content is preserved when enrichment fails or returns blank fields; manual editing and the original link remain available.

Photo imports also retain recognized Instructions and Notes sections when present. Review OCR text in the editor before saving; image quality can affect recognition.

Recipe content stays on existing meal records, and cooking progress is saved separately and included in version-2 backups. Older backups remain supported. Export backups regularly. Very large libraries can exceed browser storage limits; failed saves/imports preserve prior data rather than truncating recipes. Physical-device wake-lock behavior depends on browser permissions and power settings.

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
