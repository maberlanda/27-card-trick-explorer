"""Compartimento I5 — vista Explorer → «Riconoscimento».

La vista legge i campi e scrive testo localizzato con marcatori ✔/✘; la
matematica e' tutta in `services.riconoscimento` (qui usato come oracolo solo
per i numeri di riga attesi).
"""
import tkinter as tk

import pytest

from gioco27 import i18n as catalogo
from gioco27.core import gioco_reale as gr
from gioco27.core.algebra import CanonicalForm
from gioco27.services import riconoscimento as rc


@pytest.fixture
def lingua():
    precedente = catalogo.get_language()
    yield catalogo.set_language
    catalogo.set_language(precedente)


def _vista(lingua, codice="it", fornisci_T=None):
    lingua(codice)
    from gioco27.gui.riconoscimento_tab import RiconoscimentoFrame
    try:
        radice = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    radice.geometry("1280x720")
    v = RiconoscimentoFrame(radice, fornisci_T)
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


def _testo(t):
    return t.get("1.0", "end")


def _esempio(v, chiave):
    i = [k for k, *_ in v._esempi].index(chiave)
    v._esempio_cb.current(i)
    v.carica_esempio()
    v.update()


def _perm(v, valori, modo="perm"):
    v._modo_var.set(modo)
    v._su_modo()
    v._imposta(v._campo1, " ".join(map(str, valori)))
    v.analizza()
    v.update()


# ════════════════════════════ esempi fissi ══════════════════════════════════

def test_esempio_7_1_diretto_e_somme(vista):
    _esempio(vista, "recognition.example.es71")
    assert vista._esito_lbl.cget("text").count("✔") == 3
    d = _testo(vista._diretto_txt)
    assert d.count("✔ Livello") == 3 and "CDS" in d and "DCS" in d
    s = _testo(vista._somme_txt)
    assert "Σ = (117, 126, 108)" in s and "Σ = (144, 117, 90)" in s
    assert "Σ = (117, 36, 198)" in s and "C₀ = 108, C₁ = 90, C₂ = 36" in s


def test_c1_diagnostica_per_livello(vista):
    _esempio(vista, "recognition.example.c1")
    assert vista._esito_lbl.cget("text").count("✘") == 3
    d = _testo(vista._diretto_txt)
    assert "✔ Livello 0" in d and "✘ Livello 1" in d and "✘ Livello 2" in d
    assert "stessa cifra" in d
    s = _testo(vista._somme_txt)
    assert "1/3" in s and "interi ✘" in s


@pytest.mark.parametrize("chiave,riga", [("recognition.example.c9", 144),
                                         ("recognition.example.c18", 108)])
def test_c9_c18_sono_righe_della_tavola(vista, chiave, riga):
    _esempio(vista, chiave)
    assert f"#{riga}" in vista._esito_lbl.cget("text")
    assert f"riga #{riga}" in _testo(vista._diretto_txt)
    assert "k = 0" in _testo(vista._estesa_txt)


def test_somme_equilibrate_intero_non_basta(vista):
    _esempio(vista, "recognition.example.balanced")
    s = _testo(vista._somme_txt)
    assert s.count("interi ✔ · in {0,1,2} ✔ · distinti ✘ → permutazione ✘") == 3
    assert "«Intero» non basta" in s


def test_2_4_8_avanti_e_indietro(vista):
    _esempio(vista, "recognition.example.final248")
    assert "#195" in vista._esito_lbl.cget("text")
    vista._verso_var.set(rc.INDIETRO)
    vista._mostra_somme()
    s = _testo(vista._somme_txt)
    assert "Indietro" in s and "Σ = (198, 117, 36)" in s
    assert "(1, 2, 0) = CDS" in s and "(2, 1, 0) = DCS" in s
    vista._verso_var.set(rc.AVANTI)
    vista._mostra_somme()
    assert "(2, 0, 1) = DSC" in _testo(vista._somme_txt)          # M0 della #195


def test_classe_estesa_con_k_1(vista):
    f = [list(gr.MESCOLAMENTO[s]) for s in gr.mescolamenti_da_numero(77)]
    p = CanonicalForm(kron_factors=[f[2], f[1], f[0]], msc_exp=1).to_perm()
    _perm(vista, p)
    e = _testo(vista._estesa_txt)
    assert "k = 1" in e and "#77" in e
    assert "✘" in _testo(vista._diretto_txt)


# ═════════════════════════════ strumenti ════════════════════════════════════

def test_due_guide_esempio_10_2_1(vista):
    vista._q0_var.set(2)
    vista._q2_var.set(22)
    vista.guide_da_posizioni()
    g = _testo(vista._guide_txt)
    for atteso in ("τ2 = (0, 1, 2) = SCD", "τ1 = (0, 2, 1) = SDC",
                   "τ0 = (1, 2, 0) = CDS", "riga di ritorno #10", "DSC SDC SCD", "= 15"):
        assert atteso in g
    vista._q2_var.set(1)
    vista.guide_da_posizioni()
    assert "✘ Le cifre coincidono" in _testo(vista._guide_txt)


def test_due_guide_dai_mazzi_con_controllo(vista):
    _esempio(vista, "recognition.example.final248")
    vista.guide_da_mazzi()
    assert "✔ Controllo sulle 27 carte" in _testo(vista._guide_txt)
    vista._modo_var.set("perm")
    vista._su_modo()
    vista.guide_da_mazzi()
    assert "⚠" in _testo(vista._guide_txt)


def test_mazzi_gemelli_v_w(vista):
    _esempio(vista, "recognition.example.twins")
    m100, _ = gr.esegui_partita(gr.mescolamenti_da_numero(100))
    m91, _ = gr.esegui_partita(gr.mescolamenti_da_numero(91))
    atteso = rc.separabile(rc.trasformazione_relativa(m100, m91)).numero_tavola
    t = _testo(vista._vw_txt)
    assert "✔ Raggiungibile" in t and f"#{atteso}" in t
    vista._pos_var.set(13)
    vista.mostra_effetto()
    assert "La carta che parte da 13" in _testo(vista._vw_txt)


def test_a1(vista):
    ini = " ".join(f"c{i}" for i in range(27))
    vista._a1_campi[0].insert(0, ini)
    vista._a1_campi[2].insert(0, " ".join(map(str, gr.riga_tavola(100)["T"])))
    vista.a1()
    t = _testo(vista._a1_txt)
    assert "finale = P · iniziale" in t and "Calcolato: il mazzo finale" in t
    assert "finale[T[i]] = iniziale[i]" in t
    vista._a1_campi[2].delete(0, "end")
    vista.a1()
    assert "⚠ Servono almeno due" in _testo(vista._a1_txt)


# ═════════════════════════════ errori ═══════════════════════════════════════

def test_errori_di_ingresso(vista):
    _perm(vista, list(range(26)))
    assert "⚠ Servono esattamente 27 valori" in vista._errore_lbl.cget("text")
    vista._imposta(vista._campo1, "a b c")
    vista.analizza()
    assert "⚠ Servono numeri interi" in vista._errore_lbl.cget("text")
    vista._modo_var.set("mazzi")
    vista._su_modo()
    vista._imposta(vista._campo1, " ".join(map(str, range(27))))
    vista._imposta(vista._campo2, " ".join(map(str, range(1, 28))))
    vista.analizza()
    assert "⚠ I due mazzi non contengono" in vista._errore_lbl.cget("text")


def test_codice_senza_frase_usa_il_generico(vista):
    class Finto(ValueError):
        codice = "codice_nuovo"
    assert vista._testo_errore(Finto()) == "Ingresso non valido (codice_nuovo)."


def test_usa_la_T_dell_explorer(lingua):
    T = gr.riga_tavola(144)["T"]
    radice, v = _vista(lingua, fornisci_T=lambda: T)
    try:
        v.usa_T_explorer()
        assert "#144" in v._esito_lbl.cget("text")
    finally:
        radice.destroy()
    radice, v = _vista(lingua)
    try:
        v.usa_T_explorer()
        assert "⚠" in v._errore_lbl.cget("text")
    finally:
        radice.destroy()


def test_in_inglese_davvero(lingua):
    radice, v = _vista(lingua, "en")
    try:
        _esempio(v, "recognition.example.c1")
        assert v._schede.tab(0, "text").strip() == "Direct separability"
        d = _testo(v._diretto_txt)
        assert "✘ Level 1" in d and "share digit" in d
        assert "Direct separability ✘" in v._esito_lbl.cget("text")
    finally:
        radice.destroy()


def test_chiavi_simmetriche_e_termini_neutri():
    it = {k: v for k, v in catalogo._ITALIAN.items() if k.startswith("recognition.")}
    en = {k: v for k, v in catalogo._ENGLISH.items() if k.startswith("recognition.")}
    assert set(it) == set(en) and len(it) == 102
    import re
    vietati = re.compile(r"\b(Gaia|Cronaca|Giullare|G_ext|Γ|H_\{)|\bG\b|\bH\b")
    for testo in list(it.values()) + list(en.values()):
        assert not vietati.search(testo), testo


# ═════════════════════════════ integrazione ═════════════════════════════════

@pytest.fixture(scope="module")
def app():
    try:
        tk.Tk().destroy()
    except tk.TclError:
        pytest.skip("display non disponibile")
    from gioco27.gui import app as app_module
    a = app_module.App()
    a._livello = "esperto"
    a._apply_livello()
    a.update_idletasks()
    try:
        yield a
    finally:
        a.destroy()


def test_sotto_scheda_dell_explorer_e_matrice_intatta(app):
    nb = app._explorer_nb
    assert nb.tabs()[7] == str(app._riconoscimento)       # I6 aggiunge il Laboratorio dopo
    assert catalogo.tr("recognition.tab") in nb.tab(nb.tabs()[7], "text")
    assert nb.index(app._mat_scheda) == 5


def test_dall_explorer_al_riconoscimento(app):
    app._seleziona_scheda("explorer")
    app._explorer_entry.delete("1.0", "end")
    app._explorer_entry.insert("1.0", "(SCD_U x SDC_U x SDC_U) o MSC")
    app._explorer_calc()
    app._explorer_nb.select(app._riconoscimento)
    app.update()
    app._riconoscimento.usa_T_explorer()
    e = _testo(app._riconoscimento._estesa_txt)
    assert "k = 1" in e                      # T = K ∘ MSC: classe estesa, non separabile
    app._explorer_clear()
