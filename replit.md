# Meal Rotation

## Run on Replit

Use **Run** to start the **Start application** workflow. It serves the existing
static app using Python's standard-library web server:

```sh
python3 -m http.server 5000 --bind 0.0.0.0
```

Open `/` (or `/index.html`) for Meal Rotation. The separate test app is at
`/meal-rotation-test.html`.

No package installation, database, or secrets are required to run the app.
Keep the existing HTML/JavaScript structure; there is no build step.

## Data and browser features

Recipes, plans, and settings are stored in the browser for the current site
address. Data saved on GitHub Pages does not automatically transfer to Replit.
Export a backup from the old app and restore it here to move existing data.
Keep regular backups because clearing browser data can remove saved meals.

Website imports and photo OCR require internet access; browser restrictions may
block some recipe websites. Service-worker/offline installation and screen wake
lock behavior depend on browser support and may differ inside the preview
iframe. Use the app in its own browser tab when checking installation behavior.
