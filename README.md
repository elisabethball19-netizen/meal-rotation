# meal-rotation
personal meal rotation app

## Install on your phone

Open https://elisabethball19-netizen.github.io/meal-rotation/ online once.

- Android / Chrome: open the browser menu and choose **Add to Home screen** or **Install app**.
- iPhone / Safari: choose **Share → Add to Home Screen**, then **Add**. If offered, keep **Open as Web App** enabled.

Export a backup before installing and check your meals in the installed app. Some browsers, especially on iPhone, may use separate storage for the installed app; restore the backup there if needed. Keep the same site address to retain access to existing browser data.

The app can start and use saved recipes, plans, and grocery lists offline after its first successful online setup. Website imports and loading the photo OCR reader require Internet access. Do not rely on browser storage as your only backup: uninstalling, clearing site data, or browser storage eviction can remove it.

The separate `meal-rotation-test.html` can also be installed. It is named **Meal Rotation Test**, has an amber icon, and retains its isolated storage and reset control.

## Updates and deployment

Publish the HTML files together with `pwa.js`, `service-worker.js`, both `.webmanifest` files, and `icons/`. Online launches check for current app files and fall back to the cached app when offline. A service-worker update waits for existing app windows to close; it does not force an editing session to reload. Close all regular/test app windows and reopen online to finish a pending update. Updates do not clear recipe storage.

When changing the offline shell, increment `SHELL_VERSION` in `service-worker.js`. Only this app's static files are cached; imports, backup files, and unrelated site resources are excluded. Old shell caches for this app's exact scope are cleaned up after the new worker activates.

For local development, serve the checkout with an HTTP server, such as `python3 -m http.server 8000`, and open it on localhost. Installation and service workers require HTTPS in production; opening an HTML file directly still runs the app without offline installation support.
