# Our Table — personal recipe app

A small offline-first recipe book for Android, with a matching responsive web interface. The Android version bundles the web interface inside a native Java WebView shell; it is not a shortcut to a remotely hosted website.

## First-release acceptance criteria

Save a recipe, edit it without losing its earlier version, adjust ingredient quantities for a different yield, combine ingredients into a shopping list, use one-step-at-a-time cooking mode, and export/import a recipe backup without replacing existing data.

## Implemented

- Recipe creation, editing, deletion, ingredient search, categories, and favorites.
- Fraction parsing and yield scaling, including unmeasured ingredients.
- Ten earlier recipe versions, reversible restoration, and kitchen notes.
- Local photo selection and compression.
- Combined shopping list with per-recipe yields, checkboxes, manual items, and copy.
- Cooking mode, native keep-screen-on request, and an in-app timer.
- Recipe-only JSON exports and non-destructive imports; conflicts become copies.
- Native atomic-file storage and storage-failure feedback. Browser mode uses localStorage.
- Bundled assets, blocked network loads, no Android INTERNET permission, no trackers or accounts.

The two starter recipes are editable drafts, not verified final family recipes. The app does not provide dietary or allergy guarantees. Ingredient quantities scale mathematically; cooking time, temperatures, pan size, and instructions do not automatically scale.

## Run the website locally

From this folder, run `python -m http.server 8000 --directory web` and open the local server in a current browser. Serve `web/` over HTTPS to enable the included offline service worker. The website is not deployed by this change.

## Tests and Android build

Run `node --test tests/core.test.cjs` and `node --check web/app.js`.

Install Android SDK platform 35 and build-tools 35.0.0; set `ANDROID_HOME`, then run `bash scripts/build-android.sh`. Java 17 or newer, Node 18 or newer, and the SDK command-line tools are expected. This build does not require Gradle, Expo, a paid backend, or an app-store account.

The pull-request workflow produces `Our-Table-0.1.0.apk`, an APK signature verification report, package metadata, and a SHA-256 checksum. Successful compilation/signature verification is not a substitute for testing installation and behavior on a physical Android device.

## Important preview limitations

This is a personal preview, not a Play Store release. There is no live family sync, meal planner, AI recipe generator, website-recipe scraper, or iPhone build. The timer only alerts while the app is open; use the phone Clock app for reliable background alarms.

Recipes, photos and the ten earlier versions are exported; shopping lists are not. Export before uninstalling or clearing app data. Backup files are ordinary unencrypted JSON, so share and store them accordingly.

CI uses a disposable preview signing key and never uploads or commits that key. A later build may have a different certificate and require export, uninstall, reinstall, and import. Establish a user-controlled persistent release-signing key before treating this as a long-term install or publishing it. Local builds can reuse the ignored `.local-signing/preview.jks` file. The preview password is not suitable for a production keystore.

## Architecture and privacy

`web/core.js` contains pure calculations/validation; `web/app.js` owns the interface; `web/seed.js` contains sanitized starter drafts. `android/` owns the local-content allowlist, atomic storage, file picker, clipboard, and screen-awake bridge. No private family, medical, employment, financial, or account data is included in the source. No secrets or signing keys are committed.

Native APIs are only exposed to bundled content under the private appassets origin. External navigation and requests are blocked; imported text is escaped and imported photos must be embedded JPEG, PNG, or WebP. Document access is limited to files explicitly selected through Android's picker.

Food-safety reference for the ground-beef starter: USDA FSIS Safe Minimum Internal Temperature Chart, https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/safe-temperature-chart .
