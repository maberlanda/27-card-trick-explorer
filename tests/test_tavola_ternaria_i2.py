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


# ═══════════════════════ I2c — scheda «Una carta» ═══════════════════════════

def _carta(tavola, numero, carta):
    _seleziona(tavola, numero)
    tavola.pannello.imposta_carta(carta)
    tavola.update()
    return tavola.pannello


def test_f1_indirizzo_qualificato(tavola):
    p = _carta(tavola, 100, 19)
    assert p._indirizzo.cget("text") == catalogo.tr(
        "ternary.card.address", position=19, d2=2, d1=0, d0=1, word="DSC")
    # «DSC» qui e' un indirizzo: la parola compare con il suo ruolo
    assert catalogo.tr("ternary.card.address", position=19, d2=2, d1=0, d0=1,
                       word="DSC").count("DSC") == 1


def test_f8_passo_passo(tavola):
    p = _carta(tavola, 100, 19)
    assert p.passo == 0
    assert p._btn_indietro.instate(["disabled"])
    registri = [p._registro.cget("text")]
    for _ in range(3):
        p._btn_avanti.invoke()
        registri.append(p._registro.cget("text"))
    assert p.passo == 3 and p._btn_avanti.instate(["disabled"])
    attesi = [((2, 0, 1), 19, "DSC"), ((2, 2, 0), 24, "DDS"),
              ((1, 2, 2), 17, "CDD"), ((2, 1, 2), 23, "DCD")]
    assert registri == [catalogo.tr("ternary.card.register", d2=a, d1=b, d0=c,
                                    position=pos, word=w)
                        for (a, b, c), pos, w in attesi]
    p._btn_indietro.invoke()
    assert p.passo == 2
    p._btn_inizio.invoke()
    assert p.passo == 0


def test_f8_dettaglio_e_storie(tavola):
    p = _carta(tavola, 100, 19)
    p._btn_avanti.invoke()
    atteso = catalogo.tr("ternary.card.phase_step", phase=1, position=19,
                         column=1, letter="C", height=6, shuffle="CDS", block=2,
                         after=24, a2=2, a1=2, a0=0, word="DDS", out=1, into=2)
    assert p._dettaglio_passo.cget("text") == atteso
    assert p._storia_distribuzioni.cget("text").startswith(catalogo.tr(
        "ternary.card.distributions", columns="1 (C), 0 (S), 2 (D)"))
    assert catalogo.tr("ternary.card.distributions_rev", position=19, n0=1,
                       n1=0, n2=2) in p._storia_distribuzioni.cget("text")
    assert p._storia_raccolte.cget("text") == catalogo.tr(
        "ternary.card.collections", s0=2, s1=1, s2=2, position=23)


def test_log_testuale_completo_e_raggiungibile(tavola):
    p = _carta(tavola, 100, 19)
    area = p._testo_carta
    assert area.cget("takefocus") and area.cget("state") == "disabled"
    testo = _testo(area)
    for fase in (1, 2, 3):          # tutti i passi, qualunque sia il passo corrente
        assert catalogo.tr("ternary.card.phase_step", **_parametri_passo(100, 19, fase)) in testo
    assert catalogo.tr("ternary.card.law") in testo


def _parametri_passo(numero, carta, fase):
    from gioco27.services import tabellone as tb
    from gioco27.services.procedure import ProceduraGioco
    ps = tb.flusso_carta(ProceduraGioco.da_identificatore(numero, 0), carta).passi[fase - 1]
    a2, a1, a0 = ps.cifre_dopo
    return dict(phase=fase, position=ps.posizione_distribuita, column=ps.colonna,
                letter=ps.lettera_colonna, height=ps.altezza,
                shuffle=ps.mescolamento, block=ps.destinazione_blocco,
                after=ps.posizione_dopo, a2=a2, a1=a1, a0=a0,
                word=ps.parola_dopo, out=ps.cifra_uscente,
                into=ps.cifra_entrante)


def test_lettura_cifra_per_cifra_evidenzia_la_griglia(tavola):
    p = _carta(tavola, 100, 10)
    assert p._lettura.cget("text").startswith(catalogo.tr(
        "ternary.card.reading", number=100, d2=1, d1=0, d0=1, b2=0, b1=1, b0=2,
        position=5, word="SCD"))
    marcate = [(r, c) for r in range(3) for c in range(3)
               if p._celle[r][c].cget("text").startswith("▶")]
    assert marcate == [(0, 1), (1, 0), (2, 1)]
    assert catalogo.tr("ternary.card.action", phase=3, weight=9, digit=2,
                       before=1, after=0, shuffle="CSD") in p._lettura.cget("text")


def test_f10_rovesciamento_canonico_di_una_procedura(tavola):
    p = _carta(tavola, 30, 0)                   # (SCD, DCS, SCD)
    assert gr.riga_tavola(30)["mescolamenti"] == ("SCD", "DCS", "SCD")
    p._eps_vars[2].set(True)
    p._su_rovesciamenti()
    tavola.update()
    testo = _testo(p._testo_carta)
    assert catalogo.tr("ternary.card.flip_step", phase=3, before=18, b2=2,
                       b1=0, b0=0, after=8, a2=0, a1=2, a0=2) in testo
    assert p._realizzata.cget("text") == catalogo.tr("ternary.card.realized",
                                                     number=185)
    assert catalogo.tr("ternary.card.distributions_flip", phases="3") in \
        p._storia_distribuzioni.cget("text")
    assert catalogo.tr("ternary.card.distributions_rev", position=0, n0=0,
                       n1=0, n2=0) not in p._storia_distribuzioni.cget("text")
    p._vai_realizzata.invoke()
    tavola.update()
    assert tavola._tv.selection() == ("185",)


def test_nessun_elenco_di_procedure_equivalenti_nella_vista():
    sorgente = (RADICE / "gioco27" / "gui" / "pannello_ternario.py").read_text(
        encoding="utf-8")
    assert "classe_trasformazione" not in sorgente
    assert "fibra" not in sorgente


# ═══════════════════════ I2c — scheda «27 posizioni» ════════════════════════

def test_f5_tabella_27_posizioni(tavola):
    _seleziona(tavola, 193)
    tab = tavola.pannello._tabella
    gruppi = tab.get_children("")
    assert len(gruppi) == 3
    assert [tab.item(g, "text") for g in gruppi] == [
        catalogo.tr("ternary.pos.group", digit=d, letter=l, first=9 * d,
                    last=9 * d + 8) for d, l in enumerate("SCD")]
    righe = [r for g in gruppi for r in tab.get_children(g)]
    assert len(righe) == 27
    valori = [tab.item(r, "values") for r in righe]
    assert [int(v[0]) for v in valori] == list(range(27))
    assert tuple(str(x) for x in valori[1]) == ("1", "(0,0,1)", "SSC", "(2,1,2)",
                                                "DCD", "23")


def test_selezionare_una_posizione_sincronizza_carta_e_griglia(tavola):
    _seleziona(tavola, 100)
    p = tavola.pannello
    p._tabella.selection_set("pos10")
    tavola.update()
    assert p.carta == 10
    assert [(r, c) for r in range(3) for c in range(3)
            if p._celle[r][c].cget("text").startswith("▶")] == \
        [(0, 1), (1, 0), (2, 1)]
    dettaglio = p._dettaglio_posizione.cget("text")
    assert catalogo.tr("ternary.card.action", phase=1, weight=1, digit=0,
                       before=1, after=2, shuffle="CDS") in dettaglio


def test_i_blocchi_non_sono_segnati_solo_dal_colore(tavola):
    _seleziona(tavola, 0)
    tab = tavola.pannello._tabella
    assert all(tab.item(g, "text") for g in tab.get_children(""))
