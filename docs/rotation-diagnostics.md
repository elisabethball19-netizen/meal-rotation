# Collect a private rotation diagnostic

This investigation needs the actual hidden Saturday/Sunday slot metadata. The current code and synthetic historical replay do not establish why your particular saved schedule repeatedly returns Beef Bowls / Spaghetti.

Do not clear site data, reinstall, reset rotation, import a backup, or change recipes to collect this information.

## What to send

Send only the generated **anonymized diagnostic JSON**, privately in the ChatGPT conversation. Do not send or commit your original backup, photos, recipe text, or a screenshot of unrelated recipes.

The report contains:

- The affected group's saved recipe order and the aliases for the three meals you identify.
- Current per-plan assignments, automatic/manual pins, slot choices, deferred/excluded/avoided IDs, filters, temporary empty markers, Favorites scores, and linked/dependent meal relationships.
- Any saved previous-rotation snapshots, their corresponding slot metadata, and records of outgoing/cooked occurrences.
- Relative date ordering, not actual cooking dates; recipe, group, label, and plan aliases, not their names.

Those relationships distinguish a lost original ID from a filter, duplicate reservation, stale override, or incomplete Rotate Back restoration. They also show whether the group-level or whole-day empty marker is involved.

## Steps

1. In the app, export a backup through **Settings and backups → Export backup**. Export the state it is currently in; there is no need to rotate or edit anything solely for this report. Tell ChatGPT whether you exported before or after Rotate Back. If the wrong schedule is already showing, export before choosing Rotate Back again so its saved snapshot is still available.
2. Download [rotation-diagnostics.html](rotation-diagnostics.html) from this branch using GitHub's **Download raw file** action. Open the downloaded HTML file in a browser that supports local HTML files. A desktop/laptop Chrome browser is an option if a phone does not open downloaded HTML. This tool is independent of your app and does not require merging this PR or updating GitHub Pages.
3. You can disconnect from the internet now. In the tool, choose the backup file locally. Choose Weekend and identify Saturday's original Beef Bowls, Sunday's skipped Pot Roast, and the replacement Pernil in the local selectors.
4. Select **Generate anonymized report**. Review the text, then use **Download report** or **Copy report**. Share that report in the existing ChatGPT conversation.
5. Keep the original backup private. The report is not a backup and must not be imported into the app.

If a local HTML file cannot be opened on your device, tell ChatGPT the device/browser and the error. Do not upload the full backup as a workaround.

## Privacy and limits

The standalone tool has no external scripts, images, fonts, forms, or upload endpoint. Its content security policy forbids network connections. It reads the file you choose and uses explicit field allowlists; it never reads or writes the live app's browser storage. Downloading/copying a report happens only when selected by you.

Recipe names, ingredients, instructions, notes, URLs, photos, file names, unrelated storage values, raw IDs, actual cooking dates, and timestamp-based promotion priorities are omitted or replaced with aliases/ranks. Only structural rotation information is retained. Review it before sharing; do not post it publicly.

The report's `expectedAppMain` is the investigated source reference, not proof of the version running on your device. Its aliases are consistent across snapshots within one report, not guaranteed to be the same across separate reports. It captures up to three nested saved rotation snapshots and records when older data was truncated or a storage value could not be parsed.

Tests exercised backup selection, generation, download, privacy sentinels, invalid input, and absence of network/storage writes at 360 px and 760 px using an intercepted browser test origin. This managed test browser blocks `file:` navigation, so physical-device/local-file opening is not claimed as tested.
