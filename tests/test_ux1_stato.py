"""UX-1: contratti di stato, file e preferenze con widget Tk reali."""
import copy
import json
import tkinter as tk
from tkinter import ttk

import pytest

from gioco27 import i18n
from gioco27.core import config
from gioco27.core.constants import ANY
from gioco27.gui import app as app_module, sessione_tab
from gioco27.services.sessione import SessioneLavoro


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "_CONFIG_FILE", tmp_path / "config.json")
    cfg = config.Config()
    cfg._data.update(n_workers=1, use_parallel=False, ui_intro_done=True,
                     livello="laboratorio", language="it")
    cfg.save()
    monkeypatch.setattr(config, "_instance", cfg)
    from gioco27.core import cache
    monkeypatch.setattr(cache, "_CACHE_DIR", tmp_path / "cache")
    try:
        prova = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    prova.destroy()
    a = app_module.App()
    a.update()
    yield a
    if a.winfo_exists():
        a.destroy()
    i18n.set_language("it")


def prepara(app):
    app._explorer_entry.insert("1.0", "(SCD_U x SCD_U x SCD_U) o MSC")
    app._explorer_calc()
    app._simulator_frame._card_var.set(3)
    app._simulator_frame._find_sequence()
    app._preset_gioco_reale()
    app.update()


def bozza(app):
    d = app._open_sessione()
    d._titolo_var.set("Titolo in bozza à")
    d._nota.insert("1.0", "Nota non applicata\nseconda riga")
    app.update()
    return d


def test_t01_reset_filtri_locale(app):
    prepara(app)
    prima = (app._explorer_last_result, app._simulator_frame._sessione,
             list(app._last_T_perm), app._sessione.documento())
    app._reset_filtri()
    assert all(f.get_filter() == dict(p0=ANY, p1=ANY, p2=ANY, j0=ANY,
                                    j1=ANY, j2=ANY, j_uniform=False)
               for f in app.filter_frames)
    from gioco27.core.combinations import count_combinations_ex
    from gioco27.gui.i18n import format_integer
    assert app.count_var.get() == format_integer(count_combinations_ex(app._get_filters()))
    assert app._explorer_last_result is prima[0]
    assert app._simulator_frame._sessione is prima[1]
    assert app._last_T_perm == prima[2]
    assert app._sessione.stato_scientifico == {
        v["strumento"]: v["input"] for v in prima[3]["voci"]}


def test_t02_reset_workspace_scope_e_annulla(app, monkeypatch, tmp_path):
    prepara(app)
    d = bozza(app)
    d.aggiungi()
    app._tavola_frame.vai_alla_riga(100)
    app._tavola_frame._usa_come_T()
    app._simulator_frame._spettatore.avvia()
    dist = app._distrib_frame
    dist._result = dict(histogram={1: 216}, total_T=216, total_decomp=216)
    dist._show_results()
    app.update()
    ann = app._sessione.annotazioni_visibili
    ident = app._sessione.id
    seq = app._sessione.input_di("successione")
    d.salva_come(tmp_path / "salvato.json")
    assert not app._sessione.modificata
    eventi = app._sessione.cronologia.numero_eventi
    cfg = copy.deepcopy(app._cfg._data)
    esterno = tmp_path / "esportato.txt"
    esterno.write_text("non toccare")
    cache_file = tmp_path / "cache" / "sentinella.txt"
    cache_file.parent.mkdir(exist_ok=True)
    cache_file.write_text("cache intatta")
    monkeypatch.setattr(app_module, "conferma_reset", lambda _: False)
    app._reset()
    assert app._tavola_frame.pannello.numero == 100 and dist._result is not None
    assert app._sessione.cronologia.numero_eventi == eventi
    monkeypatch.setattr(app_module, "conferma_reset", lambda _: True)
    app._reset()
    app.update()
    assert app._last_T_perm is None and app._explorer_last_result is None
    assert not app._tavola_frame._tv.selection()
    assert app._tavola_frame.pannello.numero is None
    assert app._tavola_frame._btn_usa_T.instate(["disabled"])
    assert dist._result is None
    assert app._simulator_frame._sessione is None
    assert app._simulator_frame._spettatore._sessione is None
    assert app._sessione.id == ident and app._sessione.annotazioni_visibili == ann
    assert app._sessione.input_di("successione") == seq
    assert app._sessione.cronologia.numero_eventi > eventi and app._sessione.modificata
    assert app._cfg._data == cfg and esterno.read_text() == "non toccare"
    assert cache_file.read_text() == "cache intatta"


@pytest.mark.parametrize("salva_come", [False, True])
def test_t03_salva_bozze_e_riapre(app, tmp_path, salva_come):
    d = bozza(app)
    f = tmp_path / "esperimento.json"
    app._sessione.percorso = str(f)
    assert (d.salva_come(f) if salva_come else d.salva())
    nuova, rapporto = SessioneLavoro.carica(f)
    assert rapporto.verificato
    assert nuova.annotazioni == {"titolo": "Titolo in bozza à",
                                 "nota": "Nota non applicata\nseconda riga"}
    assert not app._sessione.modificata
    assert d.apri(f).verificato
    assert d._titolo_var.get() == nuova.annotazioni["titolo"]


def test_t04_applica_poi_salva_senza_evento_duplicato(app, tmp_path):
    d = bozza(app)
    d.applica_annotazioni()
    n = app._sessione.cronologia.numero_eventi
    d.salva_come(tmp_path / "e.json")
    assert app._sessione.cronologia.numero_eventi == n


def test_t05_bozze_dirty_e_refresh_non_distruttivo(app):
    d = bozza(app)
    assert app._sessione.modificata
    assert "●" in d._stato_lbl.cget("text")
    app._sessione_aggiorna_dialog()
    assert d._titolo_var.get() == "Titolo in bozza à"
    d._chiudi()
    d = app._open_sessione()
    assert "seconda riga" in d._nota.get("1.0", "end")
    assert app._sessione.modificata


def test_apri_stesso_file_scarta_la_bozza(app, monkeypatch, tmp_path):
    d = bozza(app)
    f = tmp_path / "e.json"
    d.salva_come(f)
    d._titolo_var.set("Da scartare")
    monkeypatch.setattr(sessione_tab, "conferma_abbandono", lambda _: "discard")
    assert d.apri(f).verificato
    assert d._titolo_var.get() == "Titolo in bozza à"
    assert not app._sessione.modificata


@pytest.mark.parametrize("scelta", [None, "discard", "save"])
@pytest.mark.parametrize("esistente", [False, True])
def test_t06_t08_chiusura(app, monkeypatch, tmp_path, scelta, esistente):
    bozza(app)
    f = tmp_path / "e.json"
    app._sessione.percorso = str(f)
    if esistente:
        SessioneLavoro().salva(f)
    precedente = f.read_bytes() if esistente else None
    stato = app._sessione.stato_scientifico
    eventi = app._sessione.cronologia.numero_eventi
    monkeypatch.setattr(sessione_tab, "conferma_abbandono", lambda _: scelta)
    distrutte = []
    monkeypatch.setattr(app, "destroy", lambda: distrutte.append(True))
    if scelta is None:
        app._on_close()
        assert not distrutte and not app._closing and app._sessione.modificata
        assert app._sessione.stato_scientifico == stato
        assert app._sessione.cronologia.numero_eventi == eventi
    else:
        with pytest.raises(SystemExit):
            app._on_close()
        assert distrutte == [True]
    assert f.exists() == (esistente or scelta == "save")
    if scelta == "save":
        assert json.loads(f.read_text(encoding="utf-8"))["annotazioni"]["titolo"] == "Titolo in bozza à"
    elif esistente:
        assert f.read_bytes() == precedente
    # Ripristina destroy prima del teardown della fixture.
    monkeypatch.undo()


def test_t08_salva_come_annullato_o_fallito_blocca_abbandono(app, monkeypatch):
    bozza(app)
    monkeypatch.setattr(sessione_tab, "conferma_abbandono", lambda _: "save")
    monkeypatch.setattr(sessione_tab.filedialog, "asksaveasfilename", lambda **_: "")
    assert not app._sessione_conferma_sostituzione()
    assert app._sessione.modificata and not app._closing
    app._sessione.percorso = "destinazione.json"
    monkeypatch.setattr(app._sessione, "salva", lambda *_: (_ for _ in ()).throw(OSError("guasto")))
    errori = []
    monkeypatch.setattr(sessione_tab.messagebox, "showerror", lambda *a, **k: errori.append(a))
    assert not app._sessione_conferma_sostituzione()
    assert errori and app._sessione.modificata


@pytest.mark.parametrize("operazione", ["nuova", "apri"])
@pytest.mark.parametrize("scelta", [None, "discard", "save"])
def test_t09_nuovo_apri_stesso_guard(app, monkeypatch, tmp_path, operazione, scelta):
    target = tmp_path / "target.json"
    SessioneLavoro().salva(target)
    d = bozza(app)
    ident = app._sessione.id
    salvato = tmp_path / "corrente.json"
    app._sessione.percorso = str(salvato)
    monkeypatch.setattr(sessione_tab, "conferma_abbandono", lambda _: scelta)
    d.nuova() if operazione == "nuova" else d.apri(target)
    assert (app._sessione.id == ident) == (scelta is None)
    assert salvato.exists() == (scelta == "save")


def controlli_settings(app):
    dlg = app._open_settings()
    app.update()

    def figli(w):
        for c in w.winfo_children():
            yield c
            yield from figli(c)

    widgets = list(figli(dlg))
    combos = [w for w in widgets if isinstance(w, ttk.Combobox)]
    spin = next(w for w in widgets if isinstance(w, ttk.Spinbox))
    cancel = next(w for w in widgets if isinstance(w, ttk.Button) and w.cget("text") == "Annulla")
    return dlg, combos[-1], combos[0], spin, cancel


def test_t10_lingua_annulla(app):
    prima = config._CONFIG_FILE.read_bytes()
    dlg, lingua, _, _, cancel = controlli_settings(app)
    lingua.set("English")
    lingua.event_generate("<<ComboboxSelected>>")
    cancel.invoke()
    assert app._cfg["language"] == "it" and config._CONFIG_FILE.read_bytes() == prima
    dlg, lingua, *_ = controlli_settings(app)
    assert lingua.get() == "Italiano"
    dlg.destroy()


def test_t11_lingua_salva_tutti_i_campi(app):
    dlg, lingua, scala, spin, _ = controlli_settings(app)
    lingua.set("English")
    scala.current(1)
    spin.set(2)
    app._salva_impostazioni.invoke()
    assert not dlg.winfo_exists()
    scritto = json.loads(config._CONFIG_FILE.read_text(encoding="utf-8"))
    assert scritto["language"] == "en" and scritto["help_font_scale"] == 1.3
    assert scritto["n_workers"] == 2 and i18n.get_language() == "it"
    assert config.Config()["language"] == "en"


@pytest.mark.parametrize("valore,guasto", [("non intero", False), ("2.5", False),
                                          ("0", False), ("257", False), ("2", True)])
def test_t12_impostazioni_atomiche_anche_su_guasto(app, monkeypatch, valore, guasto):
    prima = config._CONFIG_FILE.read_bytes()
    memoria = copy.deepcopy(app._cfg._data)
    dlg, lingua, _, spin, _ = controlli_settings(app)
    lingua.set("English")
    spin.set(valore)
    if guasto:
        monkeypatch.setattr(config, "atomic_write", lambda *a, **k: (_ for _ in ()).throw(OSError("disco pieno")))
    app._salva_impostazioni.invoke()
    assert dlg.winfo_exists() and app._avviso_impostazioni.cget("text")
    assert app._cfg._data == memoria and config._CONFIG_FILE.read_bytes() == prima
    dlg.destroy()


def test_clean_non_chiede_conferma(app, monkeypatch):
    monkeypatch.setattr(sessione_tab, "conferma_abbandono", lambda _: pytest.fail("sessione clean"))
    assert app._sessione_conferma_sostituzione()


def test_reset_distribuzione_scarto_del_risultato_tardivo(app):
    d = app._distrib_frame
    d._computing = True
    d.reset()
    d._q.put(("DONE", {"histogram": {1: 216}}))
    d._poll_queue()
    assert d._result is None and not d._computing
    assert d._btn.instate(["!disabled"])
