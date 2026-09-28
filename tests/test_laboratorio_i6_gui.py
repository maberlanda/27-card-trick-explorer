"""Compartimento I6 — vista Explorer → «Laboratorio».

La vista legge i campi del service e scrive testo localizzato; marcatori ✔/✘
con parole, niente Canvas. Gli oracoli numerici vengono dal service.
"""
import ast
import re
import tkinter as tk
from pathlib import Path

import pytest

from gioco27 import i18n as catalogo
from gioco27.services import laboratorio as lab
from gioco27.services.laboratorio import Dominio

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def lingua():
    precedente = catalogo.get_language()
    yield catalogo.set_language
    catalogo.set_language(precedente)


def _vista(lingua, codice="it"):
    lingua(codice)
    from gioco27.gui.laboratorio_tab import LaboratorioFrame
    try:
        radice = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    radice.geometry("1280x720")
    v = LaboratorioFrame(radice)
    v.pack(fill="both", expand=True)
    radice.update()
    return radice, v


@pytest.fixture(params=["it", "en"])
def vista(request, lingua):
    radice, v = _vista(lingua, request.param)
    try:
        yield v
    finally:
        radice.destroy()


def _testo(t):
    return t.get("1.0", "end")


def _scegli(v, pid, dominio):
    v._elenco.selection_clear(0, "end")
    v._elenco.selection_set([p.id for p in lab.CATALOGO].index(pid))
    v._su_proprieta()
    v._dominio_var.set(dominio.value)
    v.verifica()
    return _testo(v._dettaglio_txt)


def test_ogni_proprieta_e_dominio_si_mostra_nelle_due_lingue(vista):
    campi = [catalogo.tr(f"lab.field.{k}") for k in
             ("statement", "domain", "outcome", "verification", "counterexample", "source")]
    for p in lab.CATALOGO:
        for d in p.domini:
            testo = _scegli(vista, p.id, d)
            for c in campi:
                assert c + ":" in testo, (p.id, d, c)
            v = p.verifica(d)
            assert ("✔" in testo) == v.vera and ("✘" in testo) == (not v.vera)
            assert catalogo.tr(f"lab.domain.{d.value}") in testo


def test_i_domini_non_previsti_sono_disattivati(vista):
    _scegli(vista, "parita_prodotto_locale", Dominio.H)
    stati = {d: str(rb.cget("state")) for d, rb in vista._domini_rb.items()}
    assert stati[Dominio.H] == "normal"
    assert all(stati[d] == "disabled" for d in Dominio if d is not Dominio.H)
    vista._dominio_var.set(Dominio.S27.value)        # forzato: si torna al dichiarato
    vista.verifica()
    assert vista._verifica.dominio is Dominio.H


def test_controesempio_s27_con_posizione_e_metodo(vista, lingua):
    testo = _scegli(vista, "punti_fissi_potenze_di_3", Dominio.S27)
    assert "0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 26 25" in testo
    assert catalogo.tr("lab.where.s27") in testo
    assert catalogo.tr("lab.method.controesempio") in testo
    testo = _scegli(vista, "ordini_1_2_3_6", Dominio.GAMMA)
    assert "9" in testo and catalogo.tr("lab.note.nota_ordine_9") in testo
    testo = _scegli(vista, "centro_banale", Dominio.S27)
    assert catalogo.tr("lab.theorem.teorema_centro_sn") in testo


def test_a4_mostra_il_minimo(vista):
    testo = _scegli(vista, "due_carte_forzabili", Dominio.H)
    assert catalogo.tr("lab.cex.due_carte", c1=0, c2=1, t1=0, t2=3) in testo
    assert catalogo.tr("lab.note.nota_audit_0_9") in testo


def test_classi_fusione_centro_j(vista):
    for valore in ("classi", "fusione", "centro", "j"):
        vista._vista_classi.set(valore)
        vista.mostra_classi()
        t = _testo(vista._classi_txt)
        if valore == "classi":
            righe = [r for r in t.splitlines() if re.match(r"\s*\d+\s+\(", r)]
            assert len(righe) == 27 and "⋆" in righe[0]
            assert "216 = 1 + 2 + 2 + 2 + 3" in t
        elif valore == "fusione":
            righe = [r for r in t.splitlines() if re.match(r"\s*[1-7]\s+\d+\^", r)]
            assert len(righe) == 7
            assert "27" in t and "7" in t
        elif valore == "centro":
            assert "#0" in t and "46656" in t and "✔" in t
        else:
            assert "#215" in t and "DCS DCS DCS" in t and "13" in t and "#27" in t


def test_coset_stadi_locale(vista):
    t = _testo(vista._coset_txt)
    assert "1728" in t and "648" in t and "216" in t and "H∘MSC^0" in t
    assert t.count("H∘MSC^") == 3
    vista._risultato_cb.set("SCD")
    vista._da_cb.set("SDC")
    vista._a_cb.set("CDS")
    vista.mostra_locale()
    t = _testo(vista._locale_txt)
    assert "36" in t and "CDS∘DSC" in t and "= CSD" in t
    righe = [r for r in t.splitlines() if re.match(r"\s+(SCD|SDC|CSD|CDS|DSC|DCS) \([ITC]\)", r)]
    assert [r.split()[2:] for r in righe] == [list(x) for x in lab.TAVOLA_LOCALE_FONTE]


def test_grafi_solo_testo_con_alternativa_completa(vista):
    for g in lab.grafi():
        vista._grafo_var.set(g.id)
        vista.mostra_grafo()
        t = _testo(vista._grafi_txt)
        assert f"{len(g.archi)}" in t and f"{g.diametro}" in t
        adiacenze = [r for r in t.splitlines() if re.match(r"  (#\d+|[SCD]{3}): ", r)]
        assert len(adiacenze) == len(g.vertici)
        stato = str(vista._cammino_btn.cget("state"))
        assert stato == ("normal" if g.dominio is Dominio.H else "disabled")
    vista._grafo_var.set("raccolte")
    vista._da_var.set(0)
    vista._a_var.set(215)
    vista.mostra_grafo()
    assert "#0 SCD·SCD·SCD → " in _testo(vista._grafi_txt)
    vista._a_var.set(999)
    vista.mostra_grafo()
    assert catalogo.tr("lab.graph.path.invalid") in _testo(vista._grafi_txt)


def test_nessun_canvas_e_nessuna_matematica_nella_vista():
    src = (ROOT / "gioco27" / "gui" / "laboratorio_tab.py").read_text(encoding="utf-8")
    assert "Canvas" not in src.replace("nessun Canvas", "")
    tree = ast.parse(src)
    importati = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert "services" in importati or "..services" in importati or any(
        m and m.endswith("services") for m in importati)
    assert "def _comp" not in src and "permutations(" not in src


def test_dp2_nomi_dei_gruppi(lingua):
    for codice in ("it", "en"):
        lingua(codice)
        h = catalogo.tr("lab.header")
        gruppo_ambiente = "S₂₇"
        assert "H — 216" in h and "Γ — 648" in h and gruppo_ambiente in h
        nota = catalogo.tr("lab.legacy_note")
        assert "H = 216" in nota and "Γ" in nota and "648" in nota
    it, en = catalogo.CATALOGS["it"], catalogo.CATALOGS["en"]
    chiavi = [k for k in it if k.startswith("lab.")]
    assert chiavi and all(k in en for k in chiavi)
    for k in chiavi:                       # H non indica mai 648 nei testi I6
        for testo in (it[k], en[k]):
            assert not re.search(r"\bH\s*[—=-]\s*648", testo), k
            assert "G_ext" not in testo
    # una sola nota tecnica sui nomi legacy
    assert sum("legacy" in it[k] or "legacy" in en[k] for k in chiavi) <= 2
