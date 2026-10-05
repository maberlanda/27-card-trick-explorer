"""Targeted operational contracts for UX-4, without mathematical re-audit."""
import tkinter as tk
from tkinter import ttk
import pytest

from gioco27 import i18n
from gioco27.core import config
from gioco27.core.constants import ANY
from gioco27.gui.app import App
from gioco27.gui import context_help, guidance
from gioco27.gui.help_banner import HelpBanner
from gioco27.gui.decomposition import DecompositionDialog


def walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from walk(child)
from gioco27.gui.tooltip import attach, posizione_tooltip


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    directory = tmp_path_factory.mktemp("ux4")
    patch = pytest.MonkeyPatch()
    patch.setattr(config, "_CONFIG_DIR", directory)
    patch.setattr(config, "_CONFIG_FILE", directory / "config.json")
    cfg = config.Config()
    cfg._data.update(language="it", livello="base", ui_intro_done=True, use_parallel=False)
    patch.setattr(config, "_instance", cfg)
    root = App()
    root.geometry("1280x800+0+0")
    root.withdraw()
    root.update()
    yield root
    root.destroy()
    patch.undo()


@pytest.mark.parametrize("x,y,w,h", [(1270, 790, 320, 80), (600, 300, 200, 90),
                                     (-3, -4, 350, 250)])
def test_t01_geometry(x, y, w, h):
    left, top = posizione_tooltip(x, y, w, h, 1280, 800, 770)
    assert 0 <= left and left + w <= 1280
    assert 0 <= top and top + h <= 800


def test_t01_keyboard_escape_cleanup(app):
    button = ttk.Button(app)
    tip = attach(button, "Keyboard help", delay=0)
    tip._schedule_dal_focus()
    app.update()
    assert tip._tip is not None and tip._dal_focus
    assert button.bind("<Escape>") and button.bind("<FocusIn>")
    tip._hide()
    assert tip._tip is None
    tip._show()
    button.destroy()
    assert tip._tip is None


def test_t02_toolbar_long_count_and_status(app):
    app._imposta_livello("laboratorio")
    app.count_var.set("5 159 780 352")
    app.status_var.set("A very long status message " * 20)
    app.deiconify()
    app.update()
    bar = app._barra_azioni
    bar._su_configure()
    app.update()
    protocol = app._azioni_livello["protocollo"]
    assert protocol.winfo_ismapped()
    for widget, _, _ in bar._visibili():
        assert widget.winfo_ismapped()
        assert widget.winfo_rootx() + widget.winfo_width() <= app.winfo_rootx() + app.winfo_width()
    assert protocol.winfo_rootx() + protocol.winfo_width() <= app.winfo_rootx() + app.winfo_width()
    assert app._status_lbl.winfo_width() >= bar.MINIMO_ELASTICO
    assert len(app._status_display.get()) <= 48
    assert app._status_lbl._tooltip.text() == app.status_var.get()
    app.withdraw()


@pytest.mark.parametrize("level", ["base", "intermedio", "avanzato", "laboratorio"])
def test_toolbar_controls_are_not_covered(app, level):
    app._imposta_livello(level)
    app.count_var.set("5 159 780 352")
    app.status_var.set("Long status " * 30)
    app.deiconify()
    try:
        # Verify resize both ways, not only the initial mapped geometry.
        for width in (1280, 1600, 1280):
            app.geometry(f"{width}x800+0+0")
            app.update()
            bar = app._barra_azioni
            buttons = [w for w, _, _ in bar._visibili()
                       if isinstance(w, (ttk.Button, ttk.Menubutton, tk.Menubutton))]
            assert any(w.cget("text").endswith(i18n.tr("button.settings")) for w in buttons)
            if level == "laboratorio":
                assert app._azioni_livello["protocollo"] in buttons
            for button in buttons:
                assert button.winfo_ismapped()
                assert button.winfo_rootx() + button.winfo_width() <= app.winfo_rootx() + width
                x = button.winfo_rootx() + button.winfo_width() // 2
                y = button.winfo_rooty() + button.winfo_height() // 2
                hit = app.winfo_containing(x, y)
                assert hit not in getattr(bar, "_contenitori_riga", ())
                assert hit is button or (hit is not None and
                                         str(hit).startswith(str(button) + ".")), (
                    level, width, button.cget("text"), str(hit))
    finally:
        app.withdraw()


def test_t03_fixed_any_and_uniform(app):
    frame = app.filter_frames[0]
    frame.reset()
    frame._vars["P0"][0].set("SCD_U")
    assert all(w.instate(["disabled"]) for w in frame._caselle["P0"])
    frame._vars["P0"][0].set(ANY)
    assert all(w.instate(["!disabled"]) for w in frame._caselle["P0"])
    frame.set_j_uniform(True)
    assert frame._combo["J1"].instate(["disabled"])
    frame.set_j_uniform(False)
    assert str(frame._combo["J1"].cget("state")) == "readonly"


def test_t04_factor_convention_and_numeric_effect(app):
    app._explorer_example()
    assert [w.cget("text").split(" =")[0] for w in app._mat_flbls_t] == ["P2", "P1", "P0"]
    assert len(app._explorer_last_result["perm"]) == 27
    assert "P2 ⊗ P1 ⊗ P0" in context_help.text(("A04",))


def test_t05_shuffle_empty_loaded_and_clear(app):
    viewer = app._shuffle_viewer
    viewer.clear_all()
    assert viewer._steps == []
    assert all(w.cget("text") == "—" for row in viewer._cell_labels for w in row)
    assert all(w.instate(["disabled"]) for w in viewer._transport)
    app._explorer_example()
    viewer.load_formula()
    assert viewer._steps and all(w.instate(["!disabled"]) for w in viewer._transport)
    viewer.clear_all()
    assert not viewer._steps


def test_t06_decomposition_complete_node_and_target(app, monkeypatch):
    monkeypatch.setattr(DecompositionDialog, "_start_search", lambda self: None)
    dialog = DecompositionDialog(app, list(range(27)), list(reversed(range(27))))
    try:
        tree = dialog._tree
        tree.insert("", "end", iid="group", text="A0")
        tree.insert("group", "end", iid="leaf", values=("A0", "A1", "A2"))
        dialog._node_expr["leaf"] = "I"
        tree.focus("group")
        dialog._on_select(None)
        assert dialog._open_btn.instate(["disabled"])
        tree.focus("leaf")
        dialog._on_select(None)
        assert dialog._open_btn.instate(["!disabled"])
        assert dialog._current_target() == list(reversed(range(27)))
        dialog._target_inv.set(False)
        assert dialog._current_target() == list(range(27))
        assert dialog._tree._guidance_body == i18n.tr("ux4.decomp.blocks")
        guidance.install(tree, "decomposition")
        assert tree._guidance_body == i18n.tr("ux4.decomp.blocks")
        assert len(tree._guidance_bindings) == 2
        tree.event_generate("<FocusIn>")
        assert tree._tooltip.text() == i18n.tr("ux4.decomp.blocks")
        assert any(isinstance(w, HelpBanner) and "TARGET" in w._long for w in walk(dialog))
    finally:
        dialog.destroy()


def test_t07_lab_unavailable_domain_and_object(app):
    frame = app._laboratorio
    assert "proprietà" in frame._verifica_btn.cget("text")
    assert "automaticamente" in i18n.tr("ux4.lab.prompt")
    for index in range(frame._elenco.size()):
        frame._elenco.selection_clear(0, "end")
        frame._elenco.selection_set(index)
        frame._su_proprieta()
        for button in frame._domini_rb.values():
            if button.instate(["disabled"]):
                assert "dichiarata" in button._tooltip.text


def test_t08_analysis_headers(app):
    headers = [app._analisi_tv.heading(c, "text") for c in app._analisi_tv["columns"]]
    assert "Molteplicità" in headers and "Destinazioni T (0–26)" in headers
    assert "configurazioni" in i18n.tr("ux4.analysis.scope")


def test_t09_sequence_states_and_return(app):
    dialog = app._open_successione()
    try:
        assert dialog._schede.select() == str(dialog._sequence_page)
        for key in ("remove", "up", "down", "back", "forward", "return"):
            assert dialog._btn[key].instate(["disabled"])
        dialog.aggiungi()
        assert dialog._btn["forward"].instate(["!disabled"])
        dialog._albero.selection_set("0")
        dialog._stati_successione()
        assert dialog._btn["remove"].instate(["!disabled"])
        assert dialog._btn["up"].instate(["disabled"])
        assert dialog._btn["down"].instate(["disabled"])
        dialog.replay(1)
        assert dialog._btn["forward"].instate(["disabled"])
        dialog.ritorno_compresso()
        assert dialog._passo == 0
    finally:
        dialog.destroy()


@pytest.mark.parametrize("invalid", ["abc", "0", "99999"])
def test_t10_worker_validation_atomic(app, invalid):
    dialog = app._open_settings()
    try:
        spin = next(w for w in walk(dialog) if isinstance(w, ttk.Spinbox))
        previous = dict(app._cfg._data)
        spin.set(invalid)
        app._salva_impostazioni.invoke()
        assert dialog.winfo_exists()
        assert app._cfg._data == previous
        assert app._avviso_impostazioni.cget("text")
    finally:
        dialog.destroy()


def test_t11_guide_contents_search_return(app):
    app._imposta_livello("avanzato")
    app._seleziona_scheda("explorer")
    app._open_guide("s04")
    assert app._guide_origin == str(app._schede["explorer"])
    assert app._guide_text.tag_ranges("toc_1")
    app._guide_query.set("Kronecker")
    app._guide_search()
    assert app._guide_text.tag_ranges("search_hit")
    app._guide_back()
    assert app._nb.select() == str(app._schede["explorer"])


def test_t12_presentation_escape_label():
    for lang, word in (("it", "schermo intero"), ("en", "full screen")):
        assert word in i18n.CATALOGS[lang]["presentation.navigation_hint"].split("Esc:")[1]


def test_t13_localised_catalog():
    assert set(i18n.CATALOGS["it"]) == set(i18n.CATALOGS["en"])
    for scope, label in i18n._UX4_TIPS:
        assert label.startswith("@") or label in i18n.CATALOGS["it"], (scope, label)


def test_selective_unbind_clears_last_callback(app):
    from gioco27.gui.common import rimuovi_binding
    widget = ttk.Frame(app)
    try:
        binding = widget.bind("<<OnlyCallback>>", lambda e: None, add="+")
        rimuovi_binding(widget, "<<OnlyCallback>>", binding)
        assert widget.bind("<<OnlyCallback>>") == ""
        assert not widget.tk.call("info", "commands", binding)
    finally:
        widget.destroy()


def test_guidance_reinstall_preserves_notebook_behavior(app):
    app._imposta_livello("avanzato")
    app._seleziona_scheda("explorer")
    notebook = app._explorer_nb
    calls = []
    binding = notebook.bind("<<NotebookTabChanged>>", lambda e: calls.append(e.widget), add="+")
    try:
        for _ in range(2):
            guidance.install(notebook, "explorer")
        notebook.select(app._mat_scheda)
        notebook.event_generate("<<NotebookTabChanged>>")
        app.update()
        assert calls and all(w is notebook for w in calls)
        assert int(notebook.cget("height")) == app._mat_scheda.winfo_reqheight()
        assert notebook.master.grid_rowconfigure(2)["weight"] == 0
    finally:
        from gioco27.gui.common import rimuovi_binding
        rimuovi_binding(notebook, "<<NotebookTabChanged>>", binding)


@pytest.mark.parametrize("topic", context_help.TOPICS)
def test_t14_topics(app, topic):
    banner = context_help.banner(app, topic, app._open_guide)
    banner._toggle_long()
    assert banner._open and banner._longlbl.cget("text") == context_help.text((topic,))
    banner.destroy()


def test_t15_catalog_attached(app):
    for widget in (app._decomp_btn, app._exp_export_btn, app._analisi_exp_mb,
                   app._laboratorio._verifica_btn, app._shuffle_viewer._play_btn):
        assert getattr(widget, "_tooltip", None) is not None
    assert app._tavola_frame._tv._guidance_regions
    assert app._tavola_frame.pannello._tabella._guidance_regions
    for topic in ("A01", "A02", "A03", "A04", "A05", "A06", "A06b", "A07", "A08", "A09", "A10", "A10b"):
        assert any(isinstance(w, HelpBanner) and context_help.text((topic,)) in (w._long or "")
                   for w in walk(app)), topic


@pytest.mark.parametrize("scope,label", [("lab", "lab.domain.short.h"),
    ("recognition", "recognition.sums.forward"), ("simulator", "simulator.tab.practice"),
    ("*", "ternary.pos.col.dest"), ("settings", "settings.workers")])
def test_t15_semantic_catalog(scope, label):
    assert len(guidance.tip(scope, label)) > len(i18n.tr(label))
