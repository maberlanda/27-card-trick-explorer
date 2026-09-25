"""Compartimento J — sessione, cronologia, undo/redo e L90 nell'interfaccia.

App reale sotto xvfb. La cattura passa dalle viste esistenti; undo/redo e
caricamento devono riportare lo stato nelle viste senza creare eventi.
"""
import json
import tkinter as tk
from tkinter import ttk

import pytest

from gioco27 import i18n as catalogo
from gioco27.services import esperimento as E
from gioco27.services.procedure import ProceduraGioco

TARGET = ("1280x720", "1366x768", "1920x1080")


@pytest.fixture(scope="module")
def app():
    try:
        radice = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    radice.destroy()
    from gioco27.gui import app as app_module
    a = app_module.App()
    a._imposta_livello("laboratorio")
    a.update_idletasks()
    try:
        yield a
    finally:
        d = getattr(a, "_sessione_dialog", None)
        if d is not None and d.winfo_exists():
            d.destroy()
        a.destroy()


@pytest.fixture
def pulita(app):
    app._sessione_nuova()
    app._explorer_clear()
    d = app._open_sessione()
    app.update()
    return d


def _explorer(app, testo):
    app._explorer_entry.delete("1.0", "end")
    app._explorer_entry.insert("1.0", testo)
    app._explorer_calc()


A = "(SCD_U x SDC_U x SDC_U) o MSC"
B = "(CDS_U x SCD_U x SCD_U) o MSC"


def test_cattura_dalle_viste(app, pulita):
    _explorer(app, A)
    sim = app._simulator_frame
    sim._card_var.set(3)
    sim._target_var.set(20)
    sim._find_sequence()
    sim._p_modo_var.set("conseguenze")
    sim._su_modo()
    app._tavola_frame._on_usa_T(list(range(27)))
    ric = app._riconoscimento
    ric._modo_var.set("perm")
    ric._su_modo()
    ric._imposta(ric._campo1, " ".join(map(str, list(range(9, 27)) + list(range(9)))))
    ric.analizza()
    app._laboratorio.verifica()
    stato = app._sessione.stato_scientifico
    assert set(stato) == {"explorer", "simulatore", "tavola", "riconoscimento", "laboratorio"}
    assert stato["simulatore"] == {"carta": 3, "bersaglio": 20, "disposizione_fissata": None,
                                   "modalita_pratica": "conseguenze"}
    assert stato["tavola"] == {"mescolamenti": ["SCD", "SCD", "SCD"], "rovesciamenti": [0, 0, 0]}
    d = app._sessione.documento()
    assert E.verifica_testo(E.json_canonico(d)).verificato


def test_presentazione_non_crea_eventi(app, pulita):
    _explorer(app, A)
    n = app._sessione.cronologia.numero_eventi
    for livello in ("base", "avanzato", "laboratorio"):
        app._imposta_livello(livello)
    app._seleziona_scheda("guida")
    app.geometry("1366x768")
    app.update()
    assert app._sessione.cronologia.numero_eventi == n


def test_undo_redo_riportano_le_viste(app, pulita):
    _explorer(app, A)
    _explorer(app, B)
    assert app._explorer_entry.get("1.0", "end-1c") == B
    pulita.annulla()
    assert app._explorer_entry.get("1.0", "end-1c") == A
    assert app._explorer_last_result["ok"]
    n = app._sessione.cronologia.numero_eventi
    pulita.ripristina()
    assert app._explorer_entry.get("1.0", "end-1c") == B
    assert app._sessione.cronologia.numero_eventi == n            # nessun evento fantasma
    pulita.annulla()
    pulita.annulla()
    assert app._explorer_entry.get("1.0", "end-1c") == ""
    _explorer(app, B)                                              # nuovo ramo
    assert not app._sessione.cronologia.puo_ripristinare()
    assert pulita._pulsanti["redo"].instate(["disabled"])


def test_salva_modifica_undo_pulito_e_carica(app, pulita, tmp_path):
    _explorer(app, A)
    pulita._titolo_var.set("prova")
    pulita.applica_annotazioni()
    f = tmp_path / "sessione.json"
    assert pulita.salva_come(f) == f
    assert not app._sessione.modificata and "✔" in pulita._stato_lbl.cget("text")
    _explorer(app, B)
    assert app._sessione.modificata and "●" in pulita._stato_lbl.cget("text")
    pulita.annulla()
    assert not app._sessione.modificata
    app._imposta_livello("avanzato")
    _explorer(app, B)
    app._sessione.segna = None
    app._sessione.cronologia.segna_salvato()                       # evita la conferma
    r = pulita.apri(f)
    assert r.verificato
    assert app._explorer_entry.get("1.0", "end-1c") == A
    assert app._sessione.annotazioni["titolo"] == "prova"
    doc = json.loads(f.read_text(encoding="utf-8"))
    assert doc["presentazione"]["livello"] == "laboratorio"
    assert app._livello == "laboratorio"


def test_caricamento_fallito_non_tocca_la_sessione(app, pulita, tmp_path):
    _explorer(app, A)
    app._sessione.cronologia.segna_salvato()
    prima = (app._sessione.id, app._sessione.stato_scientifico)
    rotto = tmp_path / "rotto.json"
    rotto.write_text('{"schema": "gioco27.esperimento", "schema_version": 9}', encoding="utf-8")
    r = pulita.apri(rotto)
    assert r.stato is E.Stato.UNSUPPORTED_SCHEMA
    assert (app._sessione.id, app._sessione.stato_scientifico) == prima
    assert "UNSUPPORTED_SCHEMA" in pulita._esito.get("1.0", "end")


def test_conferma_prima_di_sostituire_una_sessione_modificata(app, pulita, monkeypatch, tmp_path):
    _explorer(app, B)
    assert app._sessione.modificata
    from gioco27.gui import sessione_tab
    monkeypatch.setattr(sessione_tab.messagebox, "askyesno", lambda *a, **k: False)
    id_prima = app._sessione.id
    assert pulita.apri(tmp_path / "x.json") is None
    pulita.nuova()
    assert app._sessione.id == id_prima


def test_export_non_cancellato_da_undo(app, pulita, tmp_path):
    pulita.aggiungi(ProceduraGioco(("CDS", "CDS", "CSD")))
    out = tmp_path / "successione.csv"
    m = pulita.esporta_successione(out)
    assert out.exists() and (tmp_path / "successione.csv.manifest.json").exists()
    while app._sessione.cronologia.puo_annullare():
        pulita.annulla()
    assert out.exists() and E.sha256(out.read_bytes()) == m["sha256"]
    assert any("⤓" in pulita._eventi.get(i) for i in range(pulita._eventi.size()))


def test_vista_successione_l90(app, pulita):
    pulita.aggiungi(ProceduraGioco.da_identificatore(100, 0))
    pulita.aggiungi(ProceduraGioco(("SCD", "SDC", "CSD"), (1, 0, 1)))
    pulita.aggiungi(ProceduraGioco.da_identificatore(56, 0))
    albero = pulita._albero
    assert len(albero.get_children()) == 3
    assert albero.item("0")["values"][2] == "#100"
    assert "ε=101" in albero.item("1")["values"][1]
    albero.selection_set("2")
    pulita.sposta(-1)
    assert "#56" in albero.item("1")["values"][2]
    albero.selection_set("0")
    pulita.rimuovi()
    assert len(albero.get_children()) == 2
    pulita.replay(1)
    pulita.replay(1)
    pulita.replay(1)
    assert pulita._tappa_lbl.cget("text").startswith(catalogo.tr("sequence.stage", k=2, n=2)[:5])
    r = pulita.ritorno_compresso()
    testo = pulita._replay.get("1.0", "end")
    assert f"#{r.numero_tavola}" in testo and "0 1 2 3" in testo
    pulita.annulla()                                               # la rimozione torna indietro
    assert len(albero.get_children()) == 3


def test_nessun_canvas_e_testo_alternativo():
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "gioco27" / "gui" / "sessione_tab.py"
           ).read_text(encoding="utf-8")
    assert "Canvas" not in src.replace("nessun\nCanvas", "").replace("Nessun Canvas", "")


# ═══════════════════════════════ H2 ══════════════════════════════════════════

def _discendenti(w):
    out = []
    for c in w.winfo_children():
        out.append(c)
        out.extend(_discendenti(c))
    return out


@pytest.mark.parametrize("geometria", TARGET)
def test_h2_finestra_sessione(app, pulita, geometria):
    app.geometry(geometria)
    app.update()
    d = pulita
    larghezza, altezza = (int(x) for x in geometria.split("x"))
    d.geometry(f"{min(980, larghezza - 40)}x{min(600, altezza - 80)}")
    for indice in range(3):
        d._schede.select(indice)
        d.update()
        pagina = d._schede.nametowidget(d._schede.select())
        for w in _discendenti(pagina):
            if isinstance(w, (ttk.Button, ttk.Entry, ttk.Combobox, ttk.Checkbutton,
                              tk.Listbox, ttk.Treeview)) and w.winfo_manager():
                assert w.winfo_ismapped(), (geometria, indice, w)
                assert w.winfo_rootx() + w.winfo_width() <= d.winfo_rootx() + d.winfo_width() + 1
                assert w.winfo_rooty() + w.winfo_height() <= d.winfo_rooty() + d.winfo_height() + 1
    assert app._btn_sessione.winfo_ismapped()


def test_h2_tastiera_e_livelli(app, pulita):
    d = pulita
    d._schede.select(2)
    d.update()
    attesi = [*d._sigle, d._btn["add"], d._btn["remove"], d._btn["up"], d._btn["down"]]
    attesi[0].focus_set()
    d.update()
    visti, w = [], attesi[0]
    for _ in range(30):
        if w in attesi and w not in visti:
            visti.append(w)
        w = w.tk_focusNext()
    assert visti == attesi
    for livello in ("base", "intermedio", "avanzato", "laboratorio"):
        app._imposta_livello(livello)
        app.update()
        assert app._btn_sessione.winfo_ismapped()
    stato = d._stato_lbl.cget("text")
    assert ("✔" in stato) or ("●" in stato)                       # non solo colore


def test_h2_finestra_in_inglese(app, monkeypatch):
    precedente = catalogo.get_language()
    catalogo.set_language("en")
    try:
        from gioco27.gui.sessione_tab import SessioneDialog
        d = SessioneDialog(app)
        d.update()
        assert d.title() == "Experiment and history"
        assert "Experiment:" in d._stato_lbl.cget("text")
        d.destroy()
    finally:
        catalogo.set_language(precedente)
