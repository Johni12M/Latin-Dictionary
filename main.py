import flet as ft
import sys
import time
import math
import threading
import backend

def main(page: ft.Page):
    page.title = "Navigium Latin Dictionary"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO)
    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.CYAN)
    page.window.width = 1050
    page.window.height = 720
    page.window.min_width = 900
    page.window.min_height = 600
    page.padding = 0


    # --- STATE ---
    app_state = {
        "history": [],
        "saved": [],
        "cache": {},
        "sidebar_open": False,
        "showing_placeholder": True,
        "search_controls": [],
        "last_word": None,
    }

    # --- UI COMPONENTS ---
    
    # 1. Sidebar Elements
    history_list = ft.ListView(expand=True, spacing=5)
    
    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        page.update()

    def clear_all(e):
        app_state["history"].clear()
        app_state["showing_placeholder"] = True
        app_state["search_controls"] = []
        backend.clear_history()
        history_list.controls.clear()
        results_view.controls.clear()
        show_placeholder()
        page.update()

    sidebar_content = ft.Column(
        controls=[
            ft.Row([ft.Text("🏛️", size=24), ft.Text("NAVIGIUM", size=18, weight=ft.FontWeight.BOLD)]),
            ft.Divider(),
            ft.Text("LETZTE SUCHEN", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.OUTLINE),
            history_list,
            ft.Divider(),
            ft.Button("Theme wechseln", icon=ft.Icons.DARK_MODE, on_click=toggle_theme, width=180),
            ft.Button("🗑️ Alles leeren", color=ft.Colors.ERROR, on_click=clear_all, width=180),
        ],
        expand=True,
        opacity=0, # Hidden initially
        animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN),
    )

    # Store reference to menu icon container for easy access
    menu_icon_container = ft.Container(
        content=ft.Icon(ft.Icons.MENU, size=30),
        rotate=0, 
        animate_rotation=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK),
        on_click=lambda e: toggle_sidebar()
    )

    sidebar = ft.Container(
        width=60, # Start collapsed
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        padding=10,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT_CUBIC),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        menu_icon_container
                    ],
                    alignment=ft.MainAxisAlignment.END
                ),
                sidebar_content
            ],
            expand=True
        )
    )

    def toggle_sidebar():
        app_state["sidebar_open"] = not app_state["sidebar_open"]
        if app_state["sidebar_open"]:
            sidebar.width = 220
            sidebar_content.opacity = 1
            menu_icon_container.rotate = math.pi / 2 # Rotate 90 degrees
        else:
            sidebar.width = 60
            sidebar_content.opacity = 0
            menu_icon_container.rotate = 0
        page.update()

    # 2. Main Area Elements
    search_input = ft.TextField(
        hint_text="Lateinisches Wort oder Form eingeben...",
        expand=True,
        border_radius=8,
        on_submit=lambda e: perform_search(),
    )

    search_btn = ft.Button("Übersetzen", on_click=lambda e: perform_search(), height=45)

    # Search animation
    _anim_stop = {"v": False}
    _braille = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    anim_spinner = ft.Text("⠋", size=40, color=ft.Colors.CYAN_ACCENT, font_family="Consolas")
    anim_word    = ft.Text("", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_ACCENT)
    anim_label   = ft.Text("wird übersetzt…", size=13, color=ft.Colors.OUTLINE, italic=True)

    search_anim_container = ft.Container(
        visible=False,
        expand=True,
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            [anim_spinner, ft.Container(height=4), anim_word, anim_label],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
    )

    results_view = ft.ListView(expand=True, spacing=15, auto_scroll=False)

    search_row = ft.Row([ft.Text("🔍", size=24), search_input, search_btn], visible=True)

    # Native Flutter indeterminate bouncing bar
    search_progress_bar = ft.ProgressBar(
        value=None,
        bar_height=6,
        color=ft.Colors.BLUE_ACCENT_400,
        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLUE_ACCENT_400),
        border_radius=3,
        visible=False,
    )

    # Language selector
    current_lang = {"code": "de"}

    lang_buttons = {}
    def make_lang_btn(code, flag, label):
        def on_click(e, c=code):
            current_lang["code"] = c
            for lc, lb in lang_buttons.items():
                lb.style = ft.ButtonStyle(
                    bgcolor=ft.Colors.PRIMARY if lc == c else ft.Colors.TRANSPARENT,
                    color=ft.Colors.ON_PRIMARY if lc == c else ft.Colors.OUTLINE,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                )
            # Re-translate existing results if there are cached ones
            last_word = app_state.get("last_word")
            if last_word and last_word.lower() in app_state["cache"]:
                results = app_state["cache"][last_word.lower()]
                display_results(results, last_word, skip_history=True)
            else:
                page.update()
        btn = ft.ElevatedButton(
            f"{flag} {code.upper()}",
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY if code == "de" else ft.Colors.TRANSPARENT,
                color=ft.Colors.ON_PRIMARY if code == "de" else ft.Colors.OUTLINE,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
            ),
            height=34,
        )
        lang_buttons[code] = btn
        return btn

    lang_row = ft.Row(
        [make_lang_btn(code, flag, label) for code, (flag, label) in backend.LANGUAGES.items()],
        spacing=4,
    )

    # Simple tab buttons for navigation
    current_tab = {"index": 0}  
    
    def tab_changed(e):
        if e and hasattr(e.control, 'data'):
            current_tab["index"] = e.control.data
        
        # --- FIXED: Direct color properties, using TRANSPARENT instead of None ---
        tab_btn_search.bgcolor = ft.Colors.PRIMARY if current_tab["index"] == 0 else ft.Colors.TRANSPARENT
        tab_btn_search.color = ft.Colors.ON_PRIMARY if current_tab["index"] == 0 else ft.Colors.OUTLINE
        
        tab_btn_saved.bgcolor = ft.Colors.PRIMARY if current_tab["index"] == 1 else ft.Colors.TRANSPARENT
        tab_btn_saved.color = ft.Colors.ON_PRIMARY if current_tab["index"] == 1 else ft.Colors.OUTLINE
        # ------------------------------------------------------------------------
        
        if current_tab["index"] == 0:
            results_view.controls.clear()
            search_row.visible = True
            if app_state["search_controls"]:
                results_view.controls.extend(app_state["search_controls"])
                app_state["showing_placeholder"] = False
            else:
                show_placeholder()
        else:
            app_state["search_controls"] = list(results_view.controls)
            results_view.controls.clear()
            search_row.visible = False
            if not app_state["saved"]:
                results_view.controls.append(ft.Text("\n\nNoch keine Vokabeln gespeichert.\nKlicke auf ⭐ bei einem Ergebnis!", color=ft.Colors.OUTLINE, text_align=ft.TextAlign.CENTER))
            else:
                for item in app_state["saved"]:
                    results_view.controls.append(create_result_card(item, is_saved=True))
        page.update()
    
    # --- FIXED: Use Flet 0.80+ Button directly with initial colors ---
    tab_btn_search = ft.Button("Latein ➔ Deutsch", data=0, on_click=tab_changed, bgcolor=ft.Colors.PRIMARY, color=ft.Colors.ON_PRIMARY)
    tab_btn_saved = ft.Button("Vokabelheft (Gespeichert)", data=1, on_click=tab_changed, bgcolor=ft.Colors.TRANSPARENT, color=ft.Colors.OUTLINE)
    
    tab_row = ft.Row([tab_btn_search, tab_btn_saved], spacing=5)

    # --- LOGIC & HELPERS ---
    tip_text = ("Warte auf Eingabe...\n\nTipp: Du kannst auch konjugierte oder deklinierte\n"
                "Formen wie 'amabant' eingeben.")
    tip_control = ft.Text("", color=ft.Colors.OUTLINE, size=14, text_align=ft.TextAlign.CENTER)

    def show_placeholder():
        results_view.controls.clear()
        app_state["showing_placeholder"] = True
        tip_control.value = tip_text
        results_view.controls.append(
            ft.Container(
                content=tip_control,
                alignment=ft.Alignment.CENTER,
                padding=100,
            )
        )
        page.update()

    def _rebuild_history_list():
        history_list.controls.clear()
        for w in app_state["history"]:
            history_list.controls.append(
                ft.Button(
                    content=f"🕒  {w}",
                    bgcolor=ft.Colors.TRANSPARENT,
                    color=ft.Colors.OUTLINE,
                    on_click=lambda e, term=w: quick_search(term),
                )
            )

    def update_history_ui(word):
        if word in app_state["history"]:
            app_state["history"].remove(word)
        app_state["history"].insert(0, word)
        # keep max 50 entries in memory and DB
        while len(app_state["history"]) > 50:
            app_state["history"].pop()
        backend.save_history_entry(word)
        _rebuild_history_list()

    def quick_search(word):
        search_input.value = word
        perform_search()

    def _start_search_anim(word):
        pass  # ProgressBar(value=None) animates itself natively

    def perform_search():
        word = search_input.value.strip()
        if not word: return

        page.title = f"🔍 {word} – Navigium"
        search_btn.disabled = True
        if app_state["showing_placeholder"]:
            results_view.controls.clear()
            app_state["showing_placeholder"] = False
        search_progress_bar.visible = True
        page.update()

        threading.Thread(target=_start_search_anim, args=(word,), daemon=True).start()

        def do_lookup():
            key = word.lower()
            if key in app_state["cache"]:
                results = app_state["cache"][key]
            else:
                results = backend.lookup_vocab_bs(word)
                if results and "error" not in results[0]:
                    app_state["cache"][key] = results
                    backend.save_cache_entry(key, results)
            display_results(results, word)

        threading.Thread(target=do_lookup, daemon=True).start()

    def display_results(results, word, skip_history=False):
        _anim_stop["v"] = True
        search_progress_bar.visible = False
        search_btn.disabled = False
        page.title = "Navigium Latin Dictionary"
        app_state["last_word"] = word
        if not skip_history:
            update_history_ui(word)

        results_view.controls.clear()
        if not results or "error" in results[0]:
            msg = results[0]["error"] if results else "Unbekannter Fehler."
            results_view.controls.append(ft.Text(f"⚠️ {msg}", color=ft.Colors.ERROR, size=14))
        else:
            lang_code = current_lang["code"]
            flag, lang_label = backend.LANGUAGES[lang_code]
            results_view.controls.append(
                ft.Text(f"Ergebnisse für »{word}« ({flag} {lang_label})",
                        size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.OUTLINE)
            )
            for item in results:
                # Translate meanings if not German
                translated_item = dict(item)
                translated_item['bedeutungen'] = backend.translate_meanings(
                    item.get('bedeutungen', []), lang_code, word_key=f"{word}_{list(backend.LANGUAGES.keys()).index(lang_code)}"
                )
                results_view.controls.append(create_result_card(translated_item))

        app_state["search_controls"] = list(results_view.controls)
        page.update()

    def create_result_card(data, is_saved=False):
        meanings_column = ft.Column(spacing=5)
        if data.get('bedeutungen'):
            for b in data['bedeutungen']:
                meanings_column.controls.append(ft.Text(f"➔  {b}", size=14))

        def copy_text(e):
            copy_str = f"{data.get('head', '')} - {', '.join(data.get('bedeutungen', []))}"
            page.set_clipboard(copy_str)
            page.open(ft.SnackBar(ft.Text("Kopiert! ✓"), duration=2000))

        def save_item(e):
            if data not in app_state["saved"]:
                app_state["saved"].append(data)
                backend.save_vocabs(app_state["saved"])
                e.control.icon = ft.Icons.CHECK
                e.control.icon_color = ft.Colors.GREEN
                e.control.disabled = True
                page.update()

        def delete_item(e):
            if data in app_state["saved"]:
                app_state["saved"].remove(data)
                backend.save_vocabs(app_state["saved"])
            tab_changed(None) 

        actions = [ft.IconButton(ft.Icons.COPY, on_click=copy_text)]
        
        if not is_saved:
            is_already_saved = data in app_state["saved"]
            actions.append(
                ft.IconButton(
                    ft.Icons.STAR if not is_already_saved else ft.Icons.CHECK,
                    icon_color=ft.Colors.AMBER if not is_already_saved else ft.Colors.GREEN,
                    disabled=is_already_saved,
                    on_click=save_item
                )
            )
        else:
            actions.append(ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.ERROR, on_click=delete_item))

        return ft.Card(
            elevation=4,
            content=ft.Container(
                padding=20,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(data.get('head', '').upper(), size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_ACCENT),
                                        ft.Text(f" ({data.get('art', '')})", size=13, italic=True, color=ft.Colors.OUTLINE)
                                    ]
                                ),
                                ft.Row(controls=actions)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Text(data.get('formen', ''), size=12, color=ft.Colors.OUTLINE, font_family="Consolas"),
                        meanings_column
                    ]
                )
            )
        )

    # --- LAYOUT CONSTRUCTION ---
    main_content = ft.Container(
        expand=True,
        padding=30,
        content=ft.Column([
            tab_row,
            ft.Container(height=6),
            lang_row,
            ft.Container(height=6),
            search_row,
            search_progress_bar,
            results_view
        ])
    )

    page.add(
        ft.Row([sidebar, main_content], expand=True)
    )

    # Load persisted data synchronously — SQLite reads are fast and
    # page.update() is unreliable from a background thread on startup.
    backend.init_db()
    app_state["history"] = backend.load_history()
    app_state["saved"] = backend.load_saved_vocabs()
    app_state["cache"] = backend.load_cache()

    _rebuild_history_list()

    if app_state["history"] and app_state["cache"]:
        app_state["showing_placeholder"] = False
        results_view.controls.clear()
        for word in reversed(app_state["history"]):
            key = word.lower()
            if key not in app_state["cache"]:
                continue
            results = app_state["cache"][key]
            if results_view.controls:
                results_view.controls.insert(0, ft.Divider())
            results_view.controls.insert(
                0,
                ft.Text(f"Ergebnisse für »{word}«", size=16,
                        weight=ft.FontWeight.BOLD, color=ft.Colors.OUTLINE)
            )
            for item in reversed(results):
                results_view.controls.insert(1, create_result_card(item))
        app_state["search_controls"] = list(results_view.controls)
        page.update()
    else:
        show_placeholder()

    if len(sys.argv) > 1:
        def typewriter(word):
            for i in range(len(word) + 1):
                search_input.value = word[:i]
                page.update()
                time.sleep(0.08)
            time.sleep(0.2)
            perform_search()
            
        threading.Thread(target=typewriter, args=(sys.argv[1],), daemon=True).start()

if __name__ == "__main__":
    ft.run(main)
