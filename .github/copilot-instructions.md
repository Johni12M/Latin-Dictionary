# Copilot Instructions — Navigium Latin Dictionary

## Project Overview
Navigium is a Windows desktop app for looking up Latin words. It scrapes
**navigium.de** for German definitions, then optionally translates them
into English, French, Spanish, or Italian via `deep-translator`.

Built with **Python + Flet** (Flutter-powered UI), packaged into a single
`.exe` with PyInstaller via `flet pack`, and distributed with an
**Inno Setup** installer.

---

## Tech Stack
| Layer | Tool |
|---|---|
| UI | [Flet 0.81](https://flet.dev) (Flutter widgets in Python) |
| Data source | Scrapes `navigium.de` with `requests` + `beautifulsoup4` |
| Translation | `deep-translator` (Google Translate, source: `de`) |
| Local storage | SQLite via `sqlite3` — history, cache, saved vocabs |
| Packaging | `flet pack` → PyInstaller → single `Navigium.exe` |
| Installer | Inno Setup 6 (`release/installer/navigium_installer.iss`) |
| Hosting | GitHub Pages from `docs/` on `master` branch |

---

## Project Structure
```
navigium/new/
├── main.py                          # All UI logic (Flet)
├── backend.py                       # DB, scraping, translation
├── requirements.txt                 # pip dependencies
├── navigium.bat                     # Run app without venv activation
├── build_windows.bat                # Helper build script
├── .github/
│   └── copilot-instructions.md      # This file
├── docs/
│   ├── index.html                   # GitHub Pages site
│   └── icon.png                     # App icon for website
└── release/
    ├── Navigium.exe                 # Latest portable exe (gitignored)
    ├── Navigium_Setup_vX.X.X.exe   # Latest installer (gitignored)
    ├── icons/
    │   ├── navigium_icon.png        # 512×512 source PNG
    │   └── navigium_icon.ico        # Multi-size ICO (16–256px)
    └── installer/
        └── navigium_installer.iss   # Inno Setup script
```

**Gitignored:** `venv/`, `__pycache__/`, `.vscode/`, `navigium.db`
(contains personal search history), `navigium_cache.json`, `release/*.exe`
(too large for git — distributed via GitHub Releases).

---

## Key File Details

### `main.py`
- Window: 1050×720, dark theme, CYAN colour seed
- Sidebar: collapsible (60px ↔ 220px), shows last 50 searches
- Two tabs: **Latein → Deutsch** (search) and **Vokabelheft** (saved)
- Language selector: flag buttons 🇩🇪 🇬🇧 🇫🇷 🇪🇸 🇮🇹 below tabs
- Search uses `threading.Thread` + `ft.ProgressBar(value=None)` for animation
- Result cards: CYAN head, italic word type, Consolas forms, ➔ meanings

### `backend.py`
- `init_db()` — creates tables if missing; call on startup
- `lookup_vocab_bs(word)` — scrapes navigium.de, returns list of dicts:
  `[{head, art, formen, bedeutungen: [str]}]`
- `translate_meanings(meanings, target_lang, word_key)` — translates German
  meanings; uses in-memory `_translation_cache`; returns originals on error
- `LANGUAGES` dict: `{"de": ("🇩🇪","Deutsch"), "en": ..., ...}`
- DB tables: `history(word, searched_at)`, `cache(word, results_json)`,
  `saved(id, data_json)`

---

## After Every Code Change

### 1 — Commit & Push
```powershell
git add -A
git commit -m "Short description of change"
git push
```

### 2 — Build new exe (when main.py or backend.py changed)
Run from the project root (venv must be active or use full path):
```powershell
venv\Scripts\flet.exe pack main.py `
  --icon release\icons\navigium_icon.ico `
  --name Navigium `
  --product-name "Navigium Latin Dictionary" `
  --product-version "X.X.X" `
  --file-version "X.X.X.0" `
  --add-data "navigium.db:." `
  --add-data "navigium_cache.json:." `
  --distpath dist -y
```
Output: `dist\Navigium.exe`

### 3 — Build installer (after building exe)
1. Update version in `release\installer\navigium_installer.iss` (line 2):
   `#define MyAppVersion "X.X.X"`
2. Compile:
```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "release\installer\navigium_installer.iss"
```
Output: `release\installer\installer\Navigium_Setup_vX.X.X.exe`

### 4 — Move outputs to release\
```powershell
Copy-Item dist\Navigium.exe release\Navigium.exe -Force
Copy-Item release\installer\installer\Navigium_Setup_vX.X.X.exe release\Navigium_Setup_vX.X.X.exe -Force
Remove-Item -Recurse -Force build, dist, Navigium.spec
Remove-Item -Recurse -Force release\installer\installer
```

### 5 — Create GitHub Release
```powershell
gh release create vX.X.X `
  "release\Navigium_Setup_vX.X.X.exe#Navigium Setup vX.X.X (Windows)" `
  "release\Navigium.exe#Navigium.exe (Portable)" `
  --title "Navigium vX.X.X — Short description" `
  --notes "## What's new..."
```

### 6 — Update GitHub Pages download links (if version bumped)
Edit `docs/index.html` — search for `/releases/download/` and update the
two download URLs to point to the new version tag.

---

## Version Convention
- **Patch** (x.x.**X**): bug fix, small UI tweak
- **Minor** (x.**X**.0): new feature (e.g. new language, new tab)
- **Major** (**X**.0.0): architectural change or major redesign

Current version: **1.1.0**

---

## Venv & Dependencies
```powershell
# Activate
venv\Scripts\Activate.ps1

# Install all deps
pip install -r requirements.txt

# Current key packages
# flet==0.81.0, flet-desktop==0.81.0, flet-cli==0.81.0
# requests, beautifulsoup4, deep-translator, Pillow
```

> **Note:** `flet-desktop` must be installed for `flet pack` to work
> without a Flutter SDK. Do not upgrade flet past 0.81 without testing.

---

## GitHub Pages
- URL: https://johni12m.github.io/Latin-Dictionary/
- Source: `docs/index.html` on `master` branch (`/docs` folder)
- Re-deploys automatically on every push to `master`
- The interactive mockup uses hardcoded demo words; no backend needed

---

## Common Pitfalls
- `navigium.db` must exist at runtime (created by `backend.init_db()` on first run)
- `navigium_cache.json` is not required; app works without it
- `flet pack` copies `navigium.db` and `navigium_cache.json` into the exe — make sure they exist (even empty) before building, or remove the `--add-data` flags
- ICO format max size is 256×256 — Pillow silently ignores larger sizes
- `deep-translator` uses Google Translate under the hood; needs internet on first translation per word (subsequent calls use `_translation_cache`)
- Windows console can't print flag emojis — use `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` first
