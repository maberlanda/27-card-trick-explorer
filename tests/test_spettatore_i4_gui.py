"""Compartimento I4 — vista «Spettatore (carta ignota)» del Simulatore.

Lo spettatore simulato legge le facce nella tabella dei mazzetti, come farebbe
una persona; la vista non riceve mai la carta pensata.
"""
import ast
import pathlib
import random
import re
import tkinter as tk

import pytest

from gioco27 import i18n as catalogo
from gioco27.core import gioco_reale as gr
from gioco27.services import spettatore as sp

MODULO = pathlib.Path(__file__).resolve().parents[1] / "gioco27" / "gui" / "spettatore_tab.py"


@pytest.fixture
def lingua():
    precedente = catalogo.get_language()
    yield catalogo.set_language
    catalogo.set_language(precedente)


def _vista(lingua, codice="it", seme=1):
    lingua(codice)
    from gioco27.gui.spettatore_tab import SpettatoreFrame
    try:
        radice = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    radice.geometry("1280x720")
    v = SpettatoreFrame(radice, casuale=random.Random(seme))
    v.pack(fill="both", expand=True)
    radice.update()
    return radice, v


@pytest.fixture
def vista(lingua):
    radice, v = _vista(lingua)
    try:
        yield v
    finally:
        radice.destroy()


def _pile(v):
    return [[v._pile.set(i, c) for i in v._pile.get_children()] for c in "SCD"]


def _risposta(v, faccia):
    return next(g for g, p in enumerate(_pile(v)) if faccia in p)


def _gioca(v, faccia):
    risposte = []
    for _ in range(3):
        a = _risposta(v, faccia)
        risposte.append(a)
        v.rispondi(a)
        v.esegui_raccolta()
        v.update()
    return risposte


def _info(v):
    return v._info_txt.get("1.0", "end")


def _fisico(v):
    return v._fisico_txt.get("1.0", "end")


# ═══════════════════════ modalita' A: ordine noto ═══════════════════════════

def test_prima_dell_avvio_non_si_risponde(vista):
    assert all(str(b.cget("state")) == "disabled" for b in vista._risposta_btn)
    assert str(vista._raccolta_btn.cget("state")) == "disabled"
    assert "▶[27]" in vista._conteggio_lbl.cget("text")


def test_sessione_completa_carta_19_bersaglio_13(vista):
    vista._bersaglio_var.set(13)
    vista.avvia()
    vista.update()
    assert len(vista._pile.get_children()) == 9
    risposte = _gioca(vista, "C19")
    assert risposte == [1, 0, 2]                     # C, S, D = rev(DSC)
    testo = _info(vista)
    assert "1 + 3·0 + 9·2 = 19" in testo
    assert "DSC" in testo and "C19" in testo
    assert "posizione bersaglio 13" in testo         # controllo della destinazione
    e = sp.esito(vista._sessione)
    assert e.posizione_iniziale == 19 and e.posizione_finale == 13
    assert "▶[1]" in vista._conteggio_lbl.cget("text")


def test_si_vedono_i_candidati_non_solo_il_numero(vista):
    vista.avvia()
    vista.rispondi(_risposta(vista, "C07"))
    vista.update()
    testo = _info(vista)
    attesi = " ".join(str(x) for x in range(27) if x % 3 == 1)
    assert attesi in testo                           # i nove candidati per nome
    assert "(9)" in testo and "n0 = 1" in testo
    assert "??C" in testo                            # la cifra fine, via ω di I2
    assert "▶[9]" in vista._conteggio_lbl.cget("text")


def test_la_raccolta_si_vede_prima_di_eseguirla(vista):
    vista._bersaglio_var.set(5)                      # 5 = (0, 1, 2): sede 2 prima
    vista.avvia()
    vista.rispondi(0)
    vista.update()
    scelta = sp.scelta_raccolta(5, 1, 0)
    testo = vista._raccolta_lbl.cget("text")
    assert scelta in testo and gr.IMPILAMENTO_DI[scelta] in testo
    assert "18–26" in testo                          # sede 2 = posizioni 18–26
    assert str(vista._raccolta_btn.cget("state")) == "normal"
    assert all(str(b.cget("state")) == "disabled" for b in vista._risposta_btn)


def test_fisico_e_informativo_sono_due_riquadri_distinti(vista):
    vista.avvia()
    vista.rispondi(_risposta(vista, "C00"))
    vista.esegui_raccolta()
    vista.update()
    fisico, info = _fisico(vista), _info(vista)
    assert "Posizioni attuali occupate dalle carte candidate" in fisico
    assert "posizione iniziale" in info
    assert "Posizioni attuali" not in info
    titoli = {w.cget("text").strip() for w in _labelframe(vista)}
    assert titoli == {catalogo.tr("spectator.physical.title"),
                      catalogo.tr("spectator.info.title")}


def _labelframe(v):
    from tkinter import ttk
    return [w for w in v.winfo_children() if isinstance(w, ttk.LabelFrame)]


def test_mazzo_mescolato_carta_diversa_dalla_posizione(lingua):
    radice, v = _vista(lingua, seme=7)
    try:
        v._mescolato_var.set(True)
        v._bersaglio_var.set(20)
        v.avvia()
        v.update()
        n = next(i for i, c in enumerate(v._facce) if c != i)
        faccia = f"C{v._facce[n]:02d}"
        _gioca(v, faccia)
        e = sp.esito(v._sessione)
        assert e.posizione_iniziale == n != v._facce[n]
        assert e.carta == v._facce[n] and e.posizione_finale == 20
        assert f"Carta pensata: {faccia}" in _info(v)
    finally:
        radice.destroy()


# ═════════════════════════════ modalita' B12 ════════════════════════════════

def test_b12_riavvolge_interroga_e_non_nomina_la_carta(vista):
    vista._modo_var.set("b12")
    vista._aggiorna_controlli()
    assert str(vista._bersaglio_spin.cget("state")) == "disabled"
    assert vista._bersaglio_var.get() == 13
    assert [v.get() for v in vista._osservati_var] == ["DSC", "DSC", "CSD"]
    vista.avvia()
    vista.update()
    fisico = _fisico(vista)
    assert "#100" in fisico and "CDS, CDS, CSD" in fisico
    faccia = f"C{vista._facce[4]:02d}"               # lo spettatore conosce la sua
    _gioca(vista, faccia)
    e = sp.esito(vista._sessione)
    assert e.carta is None and e.posizione_iniziale == 4
    assert e.posizione_finale == 13
    info = _info(vista)
    assert "non determinata" in info and faccia not in info


def test_b12_con_altre_raccolte_osservate(vista):
    vista._modo_var.set("b12")
    vista._aggiorna_controlli()
    for var, sigla in zip(vista._osservati_var, ("SCD", "CDS", "DCS")):
        var.set(sigla)
    vista.avvia()
    rv = vista._riavvolgimento
    assert rv.impilamenti_osservati == ("SCD", "CDS", "DCS")
    assert f"#{rv.numero_ritorno}" in _fisico(vista)


# ════════════════════════ errori e casi limite ══════════════════════════════

def test_una_risposta_fuori_turno_e_segnalata(vista):
    vista.avvia()
    vista.rispondi(0)
    vista.rispondi(1)                                # raccolta in sospeso
    vista.update()
    assert catalogo.tr("spectator.error.raccolta_in_sospeso") in _fisico(vista)
    assert vista._sessione.risposte == (0,)


def test_bersaglio_non_valido(vista):
    vista._bersaglio_spin.set("99")
    vista.avvia()
    assert vista._sessione is None
    assert catalogo.tr("spectator.error.target") in _fisico(vista)


def test_ogni_codice_d_errore_ha_un_testo():
    codici = re.findall(r"``(\w+)``", sp.RispostaNonAccettata.__doc__)
    assert len(codici) == 6
    for lingua_ in ("it", "en"):
        catalogo.set_language(lingua_)
        try:
            for c in codici:
                assert catalogo.tr(f"spectator.error.{c}") != f"spectator.error.{c}"
        finally:
            catalogo.set_language("it")


# ═════════════════ contratti: nessuna carta, nessuna perdita ════════════════

def test_la_vista_non_conosce_ne_passa_la_carta_pensata():
    albero = ast.parse(MODULO.read_text(encoding="utf-8"))
    nomi = {n.attr for n in ast.walk(albero) if isinstance(n, ast.Attribute)}
    assert "risolvi_trucco" not in nomi
    for n in ast.walk(albero):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "esegui_raccolta"
                and getattr(n.func.value, "id", "") == "sp"):
            assert len(n.args) == 1 and not n.keywords  # sempre la scelta adattiva


def test_nessun_testo_parla_di_perdita_fisica_di_informazione():
    vietati = ("perde", "collass", "loses", "lost", "collapse", "Gaia",
               "Cronaca", "Giullare", "Γ", "G_ext")
    for diz in (catalogo._ITALIAN, catalogo._ENGLISH):
        for k, v in diz.items():
            if k.startswith("spectator."):
                assert not any(p in v for p in vietati), (k, v)


def test_chiavi_simmetriche():
    it = {k for k in catalogo._ITALIAN if k.startswith("spectator.")}
    en = {k for k in catalogo._ENGLISH if k.startswith("spectator.")}
    assert it == en and len(it) == 46


def test_in_inglese_davvero(lingua):
    radice, v = _vista(lingua, "en")
    try:
        assert v._risposta_btn[0].cget("text") == "S — Left"
        titoli = {w.cget("text").strip() for w in _labelframe(v)}
        assert titoli == {"Physical state — the deck",
                          "Information state — what the performer knows"}
        v.avvia()
        _gioca(v, "C13")
        assert "Reconstruction" in _info(v)
        assert "1 + 3·1 + 9·1 = 13" in _info(v)
    finally:
        radice.destroy()


# ═══════════════════════ integrazione nel Simulatore ════════════════════════

@pytest.fixture(scope="module")
def app():
    try:
        tk.Tk().destroy()
    except tk.TclError:
        pytest.skip("display non disponibile")
    from gioco27.gui import app as app_module
    a = app_module.App()
    a.update_idletasks()
    try:
        yield a
    finally:
        a.destroy()


def test_la_vista_e_una_sotto_scheda_esplicita(app):
    sim = app._simulator_frame
    schede = sim._notebook.tabs()
    assert len(schede) == 4
    assert schede[-1] == str(sim._spettatore)
    assert catalogo.tr("spectator.tab") in sim._notebook.tab(schede[-1], "text")


def test_la_pratica_resta_com_era(app):
    sim = app._simulator_frame
    assert sim._p_modo_var.get() == "valutazione"
    assert sim._notebook.index(sim._practice_tab) == 2
