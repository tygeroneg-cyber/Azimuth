# Azimuth

Daily world and markets briefing in English and Romanian, published with GitHub Pages at https://tygeroneg-cyber.github.io/Azimuth/ and installed on phones as an app (APK made with PWABuilder, or "Add to Home Screen" on iPhone).

Developed by Sergiu-Pompei Pavel and Dragoș Petrișor Verzia. First edition: 12 November 2026.

## Layout

- `src/template.html` is the source of the whole app: HTML, CSS and JavaScript in one file. **Edit this file, not `index.html`.**
- `src/flags.json` holds the country flag images that are inserted in place of `__FLAGS__`.
- `scripts/build.py` builds `index.html` from the template, adds the install tags and the OneSignal push setup, and checks the script with `node --check`. Run it from the repository root: `python3 scripts/build.py`.
- `index.html` is the built file. It is generated; never edit it by hand.
- `data/` holds the editions: `days.js` (list of editions with date, impact, headlines and the Fear & Greed readings) plus `YYYY-MM-DD.js` (Romanian) and `YYYY-MM-DD.en.js` (English) for each day. Only the last 7 days are kept.
- `manifest.json`, `icons/` and `sw.js` make the page installable and let it work offline. `sw.js` also loads the OneSignal service worker.
- `.github/workflows/notify.yml` sends a push notification through OneSignal. It needs the `ONESIGNAL_API_KEY` repository secret.

## Who changes what

The daily editions are written by a scheduled Claude run every morning at 08:45 Romania time, in the Claude conversation that manages the project. It writes `data/`, publishes the same files to the claude.ai copy of the app, deletes days older than 7 days and pushes here with a commit message starting with `Edition`.

When working on the app from Claude Code:

- Change only `src/`, `scripts/`, `manifest.json`, `icons/`, `sw.js` and `.github/`. Leave `data/` to the daily run.
- After editing the template, run `python3 scripts/build.py` and commit both `src/template.html` and `index.html`.
- **Commit messages that start with `Edition` or `Test notification` send a push notification to every subscriber.** Do not use those prefixes for code changes.
- The claude.ai copy of the app is not built from this repository. Changes made here only reach it when they are also published there from the Claude conversation.

## Rules for the app

- Two languages, English (default) and Romanian. Every visible text goes through the `I18N` tables in the template, with a key in both languages.
- No emoji anywhere in the interface or the content.
- Themes: Auto (follows the phone), Light and Dark, chosen in the side menu. The theme is set before first paint by the small script in `<head>`; keep the `only light` / `only dark` color-scheme switch, which stops browsers from forcing their own dark mode and washing out the colors.
- Test on narrow phones (320 to 430 px wide) and on desktop. Nothing may overflow the screen horizontally.
- Logo: a faceted compass needle (north half blue #6FB1FF/#2F6FEB, south half #F4F5F8/#B9BCC7) over a globe with meridian and parallels, on a navy tile (gradient #1E2A4A to #0A0F1F) with a graduated bezel. The same drawing is used in the header (`#brandBtn`, needle spins on tap), in the credits (`.cr-logo`) and in `icons/` (maskable icons keep the drawing at 78% inside the safe zone). Changing the APK icon needs a new PWABuilder package.
- The impact colors come from `impactColor()`; they are tuned separately for light and dark backgrounds to stay readable.

## Data format (summary)

Each edition is `window.DM_DATA["YYYY-MM-DD"] = {...}` (Romanian) or `window.DM_DATA_EN[...]` (English) with: `date`, `updated`, `impact` (1 to 10), `summary` (3 sentences), `stories` (15 items: `title`, `cat`, `region`, `overnight`, `impact`, `countries`, `essential`, `what`, `context`, `why`, `sources`), `markets` (`rows`, `note`, `sources`), `effects` (market impact entries), `watch`, `secondary`. Both language files carry the same stories in the same order with the same scores.
