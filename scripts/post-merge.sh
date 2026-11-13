#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# This is a static vanilla app. No dependencies, migrations, or build are needed.
# Check the app shell without modifying files or browser storage.
for file in index.html styles.css state.js import-export.js recipes.js \
  rotation.js grocery.js ui.js pwa.js service-worker.js manifest.webmanifest; do
  if [[ ! -f "$file" ]]; then
    printf 'Missing required app file: %s\n' "$file" >&2
    exit 1
  fi
done

printf 'Static app files are ready. No installation or build required.\n'
