"""Compartimento I2 — il pannello ternario della Tavola (viste).

Specifica: V4_PRE_I2_VIEW_DECISIONS.md, decisioni D-I2-2, D-I2-3, D-I2-5,
D-I2-6, D-I2-8. I dati vengono dal presenter `services.tabellone`, gia'
provato contro la fisica in `test_tabellone_ternario_i2.py`: qui si controlla
che la vista li mostri tutti, nell'ordine giusto, con un'alternativa
testuale e senza affidare nulla al solo colore.

I test usano una TavolaFrame vera sotto un display e si saltano senza.
"""
import ast
import pathlib
import tkinter as tk

import pytest

from gioco27 import i18n as catalogo
from gioco27.core import gioco_reale as gr

RADICE = pathlib.Path(__file__).resolve().parents[1]


def _radice():
    try:
        radice = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    radice.geometry("1280x720")
    return radice


@pytest.fixture
def tavola():
    from gioco27.gui.tavola_tab import TavolaFrame
    radice = _radice()
    frame = TavolaFrame(radice)
    frame.pack(fill="both", expand=True)
    radice.update()
    try:
        yield frame
    finally:
        radice.destroy()


@pytest.fixture
def lingua():
    precedente = catalogo.get_language()
    yield catalogo.set_language
    catalogo.set_language(precedente)


def _seleziona(tavola, numero):
    tavola._tv.selection_set(str(numero))
    tavola._tv.see(str(numero))
    tavola.update()


def _testo(widget):
    return widget.get("1.0", "end")


# ═══════════════════════════════ struttura ══════════════════════════════════

def test_la_tavola_ha_un_pannello_ridimensionabile_con_tre_schede(tavola):
    from tkinter import ttk
    pannello = tavola.pannello
    assert isinstance(tavola._divisore, ttk.Panedwindow)
    assert len(tavola._divisore.panes()) == 2
    schede = [pannello._schede.tab(t, "text") for t in pannello._schede.tabs()]
    assert schede == [catalogo.tr("ternary.tab.board"),
                      catalogo.tr("ternary.tab.card"),
                      catalogo.tr("ternary.tab.positions")]


def test_prima_della_selezione_il_pannello_lo_dice(tavola):
    assert tavola.pannello.numero is None
    assert catalogo.tr("ternary.none") in _testo(tavola.pannello._testo_tabellone)


def test_la_selezione_aggiorna_il_pannello(tavola):
    _seleziona(tavola, 100)
    assert tavola.pannello.numero == 100
    _seleziona(tavola, 56)
    assert tavola.pannello.numero == 56


# ═══════════════════════ cronologia e griglia (D-I2-3) ══════════════════════

def test_striscia_cronologica_e_griglia_con_la_fase_3_in_alto(tavola):
    _seleziona(tavola, 100)                        # (CDS, CDS, CSD)
    p = tavola.pannello
    fasi = [lbl.cget("text") for lbl in p._fasi]
    for i, (m, s) in enumerate([("CDS", "DSC"), ("CDS", "DSC"), ("CSD", "CSD")]):
        assert catalogo.tr("ternary.board.phase_cell", phase=i + 1,
                           shuffle=m, stacking=s) in fasi[i]
    righe = [lbl.cget("text") for lbl in p._etichette_righe]
    assert righe == [catalogo.tr("ternary.board.row_label", phase=f, weight=w,
                                 digit=d)
                     for f, w, d in [(3, 9, 2), (2, 3, 1), (1, 1, 0)]]
    lettere = [[c.cget("text").strip("▶ ") for c in riga] for riga in p._celle]
    assert lettere == [list("CSD"), list("CDS"), list("CDS")]
    inverse = [[c.cget("text").strip("▶ ") for c in riga] for riga in p._celle_inverse]
    assert inverse == [list("CSD"), list("DSC"), list("DSC")]


def test_colonne_assi_e_le_due_letture_nominate(tavola):
    _seleziona(tavola, 56)
    p = tavola.pannello
    diretto, inverso = p._piede_diretto.cget("text"), p._piede_inverso.cget("text")
    assert catalogo.tr("ternary.board.aces_direct", spades=7, clubs=18,
                       hearts=14) == diretto
    assert catalogo.tr("ternary.board.aces_inverse", first=4, middle=24,
                       last=11) == inverso
    assert p._titolo_diretto.cget("text").endswith(
        catalogo.tr("ternary.board.direct_reading"))
    assert p._titolo_inverso.cget("text").endswith(
        catalogo.tr("ternary.board.inverse_reading"))
    testo = _testo(p._testo_tabellone)
    riga = gr.riga_tavola(56)
    assert ", ".join(map(str, riga["T"])) in testo
    assert ", ".join(map(str, riga["T_inv"])) in testo
    assert catalogo.tr("ternary.board.not_self_inverse") in testo


def test_auto_inversa_dichiarata(tavola):
    _seleziona(tavola, 78)
    assert catalogo.tr("ternary.board.self_inverse") in \
        _testo(tavola.pannello._testo_tabellone)


# ═══════════════════════════════ (R) e ritorno ══════════════════════════════

def test_realizza_e_ritorno(tavola):
    _seleziona(tavola, 100)
    p = tavola.pannello
    assert p._realizza.cget("text") == catalogo.tr(
        "ternary.board.realize", shuffles="CDS CDS CSD", stackings="DSC DSC CSD")
    assert p._ritorno.cget("text") == catalogo.tr(
        "ternary.board.return", number=93, shuffles="DSC DSC CSD")
    assert p._vai_ritorno.cget("text") == catalogo.tr("ternary.board.goto",
                                                        number=93)
    p._vai_ritorno.invoke()
    tavola.update()
    assert tavola._tv.selection() == ("93",)
    assert p.numero == 93


def test_vai_alla_riga_toglie_il_filtro(tavola):
    tavola._filtro_var.set("CDS CDS CSD")
    tavola.update()
    _seleziona(tavola, 100)
    tavola.pannello._vai_ritorno.invoke()
    tavola.update()
    assert tavola._filtro_var.get() == ""
    assert tavola._tv.selection() == ("93",)


# ═══════════════════════════════ H2 ═════════════════════════════════════════

def test_l_alternativa_testuale_del_tabellone(tavola):
    _seleziona(tavola, 100)
    area = tavola.pannello._testo_tabellone
    assert area.cget("takefocus") and area.cget("state") == "disabled"
    testo = _testo(area)
    for sigla in ("CDS", "DSC", "CSD"):
        assert sigla in testo
    for f, w, d in [(3, 9, 2), (2, 3, 1), (1, 1, 0)]:
        assert catalogo.tr("ternary.board.row_label", phase=f, weight=w,
                           digit=d) in testo
    assert catalogo.tr("ternary.board.aces_direct", spades=13, clubs=8,
                       hearts=18) in testo


def test_in_inglese_il_pannello_parla_inglese(lingua):
    lingua("en")
    from gioco27.gui.tavola_tab import TavolaFrame
    radice = _radice()
    try:
        frame = TavolaFrame(radice)
        frame.pack(fill="both", expand=True)
        radice.update()
        _seleziona(frame, 100)
        testo = _testo(frame.pannello._testo_tabellone)
        assert "Board" in frame.pannello._schede.tab(0, "text")
        assert "fase" not in testo and "phase" in testo
    finally:
        radice.destroy()


def test_nessun_canvas_nel_pannello():
    for nome in ("pannello_ternario.py", "tavola_tab.py"):
        albero = ast.parse((RADICE / "gioco27" / "gui" / nome).read_text(encoding="utf-8"))
        assert not [n for n in ast.walk(albero) if isinstance(n, ast.Attribute)
                    and n.attr == "Canvas"], nome


def test_il_pannello_non_calcola_matematica_propria():
    """La vista legge il presenter: niente MESCOLAMENTO, digits3, T_da_…"""
    sorgente = (RADICE / "gioco27" / "gui" / "pannello_ternario.py").read_text(
        encoding="utf-8")
    for vietato in ("MESCOLAMENTO", "digits3", "T_da_", "esegui_partita",
                    "risolvi_trucco", "procedura_sicura", "// 3"):
        assert vietato not in sorgente, vietato
