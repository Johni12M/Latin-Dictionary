import json
import sqlite3
import time
from pathlib import Path

# Translation cache: (word, lang) -> translated meanings list
_translation_cache: dict[tuple, list[str]] = {}

LANGUAGES = {
    "de": ("🇩🇪", "Deutsch"),
    "en": ("🇬🇧", "English"),
    "fr": ("🇫🇷", "Français"),
    "es": ("🇪🇸", "Español"),
    "it": ("🇮🇹", "Italiano"),
}

def translate_meanings(meanings: list[str], target_lang: str, word_key: str = "") -> list[str]:
    """Translate a list of German meanings to target_lang. Returns originals on failure."""
    if target_lang == "de" or not meanings:
        return meanings
    cache_key = (word_key, target_lang)
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source="de", target=target_lang)
        translated = [translator.translate(m) or m for m in meanings]
        _translation_cache[cache_key] = translated
        return translated
    except Exception as e:
        print(f"[translate] error: {e}")
        return meanings

DB_FILE = Path(__file__).parent / "navigium.db"

def _conn():
    c = sqlite3.connect(str(DB_FILE))
    c.row_factory = sqlite3.Row
    return c

def init_db():
    # If the file exists but isn't a valid SQLite DB (e.g. old empty file), recreate it
    if DB_FILE.exists():
        try:
            c = sqlite3.connect(str(DB_FILE))
            c.execute("SELECT name FROM sqlite_master LIMIT 1")
            c.close()
        except sqlite3.DatabaseError:
            import os
            os.remove(str(DB_FILE))
            print(f"[DB] old/corrupt file removed, recreating")

    c = _conn()
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            word TEXT PRIMARY KEY,
            searched_at REAL NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            word TEXT PRIMARY KEY,
            results_json TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS saved (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_json TEXT NOT NULL UNIQUE
        )
    """)
    c.commit()
    c.close()
    print(f"[DB] ready → {DB_FILE}")

# --- History ---

def load_history():
    try:
        c = _conn()
        rows = c.execute("SELECT word FROM history ORDER BY searched_at DESC LIMIT 50").fetchall()
        c.close()
        result = [r["word"] for r in rows]
        print(f"[DB] load_history → {result}")
        return result
    except Exception as e:
        print(f"[DB] load_history error: {e}")
        return []

def save_history_entry(word):
    try:
        c = _conn()
        c.execute(
            "INSERT INTO history (word, searched_at) VALUES (?, ?) "
            "ON CONFLICT(word) DO UPDATE SET searched_at = excluded.searched_at",
            (word, time.time())
        )
        c.commit()
        c.close()
        print(f"[DB] saved history: {word}")
    except Exception as e:
        print(f"[DB] save_history_entry error: {e}")

def clear_history():
    try:
        c = _conn()
        c.execute("DELETE FROM history")
        c.commit()
        c.close()
    except Exception as e:
        print(f"[DB] clear_history error: {e}")

# --- Cache ---

def load_cache():
    try:
        c = _conn()
        rows = c.execute("SELECT word, results_json FROM cache").fetchall()
        c.close()
        return {r["word"]: json.loads(r["results_json"]) for r in rows}
    except Exception as e:
        print(f"[DB] load_cache error: {e}")
        return {}

def save_cache_entry(word, results):
    try:
        c = _conn()
        c.execute(
            "INSERT OR REPLACE INTO cache (word, results_json) VALUES (?, ?)",
            (word, json.dumps(results, ensure_ascii=False))
        )
        c.commit()
        c.close()
    except Exception as e:
        print(f"[DB] save_cache_entry error: {e}")

# --- Saved vocabs ---

def load_saved_vocabs():
    try:
        c = _conn()
        rows = c.execute("SELECT data_json FROM saved ORDER BY id").fetchall()
        c.close()
        return [json.loads(r["data_json"]) for r in rows]
    except Exception as e:
        print(f"[DB] load_saved_vocabs error: {e}")
        return []

def save_vocabs(vocabs):
    try:
        c = _conn()
        c.execute("DELETE FROM saved")
        for v in vocabs:
            c.execute("INSERT OR IGNORE INTO saved (data_json) VALUES (?)",
                      (json.dumps(v, ensure_ascii=False, sort_keys=True),))
        c.commit()
        c.close()
    except Exception as e:
        print(f"[DB] save_vocabs error: {e}")


def lookup_vocab_bs(vocab):
    import requests
    from bs4 import BeautifulSoup
    url = f'https://www.navigium.de/latein-woerterbuch/{vocab}?wb=gross'
    parsed_results = []

    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return [{"error": f"Fehler: HTTP {resp.status_code}"}]

        soup = BeautifulSoup(resp.text, 'html.parser')
        section = soup.find('h3', class_='ergebnis')
        if section and 'Ergebnis der Suche nach lat. Formen' not in section.get_text():
            section = None

        if not section:
            return [{"error": f"Keine Treffer für '{vocab}' gefunden."}]

        umgebend_divs = []
        next_sibling = section
        while True:
            next_sibling = next_sibling.find_next_sibling('div', class_='umgebend')
            if next_sibling: umgebend_divs.append(next_sibling)
            else: break

        for umgebend in umgebend_divs:
            for entry in umgebend.find_all('div', class_='innen'):
                res_dict = {'head': '', 'art': '', 'formen': '', 'bedeutungen': []}
                try:
                    res_dict['head'] = entry.select_one('div.lemma > span').get_text(strip=True)
                    res_dict['art'] = entry.select_one('div.lemma i.wortart > span').get_text(strip=True)

                    inflected = entry.find_all('div', recursive=False)
                    if len(inflected) > 1:
                        res_dict['formen'] = inflected[1].get_text(strip=True)

                    meanings = entry.select('ol[type="I"] > li')
                    for m in meanings:
                        for b in m.select('div.bedeutung'):
                            res_dict['bedeutungen'].append(b.get_text(strip=True))

                    parsed_results.append(res_dict)
                except Exception: pass
    except Exception as e:
        return [{"error": f"Verbindungsfehler: {e}"}]

    return parsed_results