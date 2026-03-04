# 🏛️ Navigium — Latin Dictionary

<div align="center">

<img src="release/icons/navigium_icon.png" alt="Navigium Icon" width="120" style="border-radius:20px;" />

**A sleek desktop Latin dictionary for Windows**  
Instant word lookup · Grammar info · Offline cache · Search history

[![Release](https://img.shields.io/github/v/release/Johni12M/Latin-Dictionary?color=00d4ff&label=Download&logo=windows)](https://github.com/Johni12M/Latin-Dictionary/releases/latest)
[![License](https://img.shields.io/github/license/Johni12M/Latin-Dictionary?color=f0c060)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)](https://github.com/Johni12M/Latin-Dictionary/releases/latest)
[![Built with Flet](https://img.shields.io/badge/built%20with-Flet-7c4dff)](https://flet.dev)

[🌐 Website](https://johni12m.github.io/Latin-Dictionary/) · [⬇ Download](https://github.com/Johni12M/Latin-Dictionary/releases/latest) · [📋 Releases](https://github.com/Johni12M/Latin-Dictionary/releases)

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| ⚡ **Instant lookup** | Search any Latin word and get full grammatical info in under a second |
| 📖 **Grammar details** | Head form, declension/conjugation class, individual form analysis |
| 📜 **Search history** | Last 50 searches stored locally for quick revisits |
| ⚙️ **Offline cache** | Results cached after the first lookup — no internet needed for repeat searches |
| 🎨 **Dark UI** | Clean deep-indigo interface with animated search indicator |
| 📦 **No dependencies** | Single `.exe` — no Python or any other runtime required |

---

## ⬇ Download

Head to the [**Releases page**](https://github.com/Johni12M/Latin-Dictionary/releases/latest) or download directly:

| File | Description |
|---|---|
| [`Navigium_Setup_v1.0.0.exe`](https://github.com/Johni12M/Latin-Dictionary/releases/download/v1.0.0/Navigium_Setup_v1.0.0.exe) | Windows installer (recommended) |
| [`Navigium.exe`](https://github.com/Johni12M/Latin-Dictionary/releases/download/v1.0.0/Navigium.exe) | Portable — no installation needed |

**Requirements:** Windows 10 or 11 (64-bit)

---

## 🚀 Getting Started

### Option A — Installer (recommended)
1. Download `Navigium_Setup_v1.0.0.exe`
2. Run the installer and follow the prompts
3. Launch **Navigium** from the Start menu

### Option B — Portable
1. Download `Navigium.exe`
2. Run it directly — no installation needed

---

## 🛠 Building from Source

**Prerequisites:** Python 3.10+, pip

```bash
# Clone the repo
git clone https://github.com/Johni12M/Latin-Dictionary.git
cd Latin-Dictionary

# Create virtual environment and install dependencies
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run the app
python main.py
```

### Building the standalone .exe

```bash
# Install build tool
pip install flet-cli

# Build
flet pack main.py --icon release\icons\navigium_icon.ico --name Navigium ^
  --add-data "navigium.db:." --add-data "navigium_cache.json:." --distpath dist
```

The compiled executable will be at `dist\Navigium.exe`.

---

## 📁 Project Structure

```
Latin-Dictionary/
├── main.py                     # App entry point (Flet UI)
├── backend.py                  # DB, cache, and word lookup logic
├── requirements.txt            # Python dependencies
├── navigium.bat                # Helper script to run without venv activation
├── build_windows.bat           # One-click build script
└── release/
    ├── icons/
    │   ├── navigium_icon.png   # App icon (512×512)
    │   └── navigium_icon.ico   # App icon (multi-size ICO)
    └── installer/
        └── navigium_installer.iss  # Inno Setup installer script
```

---

## 🏗 Tech Stack

- **[Flet](https://flet.dev)** — Flutter-powered Python UI framework
- **SQLite** — local database for history, cache, and saved words
- **[PyInstaller](https://pyinstaller.org)** — packages the app into a single `.exe`
- **[Inno Setup](https://jrsoftware.org/isinfo.php)** — Windows installer compiler

---

## 📜 License

MIT — see [LICENSE](LICENSE) for details.
