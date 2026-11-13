---
name: Vanilla compatibility
description: Standing constraints for changes to this recipe app.
---

Keep this app 100% pure vanilla HTML/CSS/JS: no npm packages, Vite, Webpack, ES modules, or build steps. Preserve existing features, styling, element IDs, localStorage keys and compatibility. Do not change the existing data structure.

**Why:** The user explicitly required these constraints repeatedly for both the refactor and recovery/import fixes.

**How to apply:** Keep app scripts as ordered classic scripts with globally accessible handlers. Fix storage and import behavior without migrating or redesigning saved records.
