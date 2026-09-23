"""Compartimento H2 — layout adattivo, tastiera e accessibilità.

Come in C, E, F, G e H1, questo file nasce **prima** delle correzioni: misura
il comportamento attuale e marca con `xfail(strict=True)` i contratti che H2
deve introdurre.

M04 non è un'opinione di stile: si misura. Con la finestra a 1280×720 e a
1366×768, sull'applicazione vera sotto un display, oggi accade questo:

* la finestra **non può essere alta 720**: `minsize(1200, 750)` lo impedisce;
* cinque pulsanti della barra azioni — Verifica, Presentazione, Protocollo,
  Cayley, Coniugio — **spariscono del tutto**. Sono impacchettati a destra, e
  `pack` li lascia fuori quando lo spazio finisce: non sono tagliati a metà,
  non si raggiungono scorrendo, semplicemente non ci sono;
* nel Simulatore spariscono «Conferma impilamento» e «Ricomincia», cioè le
  azioni primarie del flusso di pratica;
* nell'Explorer oltre venti controlli finiscono sotto il bordo, senza che
  nulla permetta di arrivarci.

A questo si aggiungono tre cose che non dipendono dalla dimensione: il banner
d'aiuto presente su ogni scheda si usa **solo con il mouse**, i dialoghi non
danno il focus a nulla quando si aprono, e i Canvas che portano informazione
non hanno un'alternativa testuale nella loro vista.

Nessun test usa screenshot pixel-perfect: si misurano proprietà —
`winfo_ismapped`, geometria, `scrollregion`, focus, ordine di Tab — e i test
si saltano da soli quando manca un display.
"""
import pathlib
import tkinter as tk
from tkinter import ttk

import pytest

from gioco27 import i18n as catalogo

RADICE = pathlib.Path(__file__).resolve().parents[1]
PACCHETTO = RADICE / "gioco27"

#: Le tre dimensioni di collaudo richieste dal compartimento.
TARGET = ("1280x720", "1366x768", "1920x1080")

#: Widget con cui si interagisce davvero.
INTERATTIVI = (ttk.Button, ttk.Checkbutton, ttk.Radiobutton, ttk.Menubutton,
               ttk.Combobox, ttk.Entry, ttk.Scrollbar, tk.Menubutton,
               tk.Button, tk.Checkbutton, tk.Radiobutton, tk.Entry,
               tk.Scrollbar, tk.Listbox)


# ════════════════════════════ armamentario ══════════════════════════════════

def _display_o_salta():
    try:
        radice = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    radice.withdraw()
    return radice


@pytest.fixture(scope="module")
def applicazione():
    """L'applicazione vera, costruita una volta sola: aprirla costa secondi."""
    radice = _display_o_salta()
    radice.destroy()
    from gioco27.gui import app as app_module

    app = app_module.App()
    app._livello = "esperto"            # tutte le schede visibili
    app._apply_livello()
    app.update_idletasks()
    try:
        yield app
    finally:
        try:
            app.destroy()
        except tk.TclError:
            pass


@pytest.fixture
def lingua():
    precedente = catalogo.get_language()
    yield catalogo.set_language
    catalogo.set_language(precedente)


def _dimensiona(app, geometria):
    app.geometry(geometria)
    app.update()
    app.update_idletasks()
    return app.winfo_width(), app.winfo_height()


def _discendenti(widget, classi=INTERATTIVI, dentro=None):
    trovati = []
    for figlio in widget.winfo_children():
        if isinstance(figlio, classi):
            trovati.append(figlio)
        trovati.extend(_discendenti(figlio, classi))
    return trovati if dentro is None else [w for w in trovati if dentro(w)]


def _etichetta(widget):
    try:
        testo = widget.cget("text")
    except tk.TclError:
        testo = ""
    return str(testo).strip() or widget.winfo_class()


def _cornice(app):
    """I controlli sempre presenti: barre, progresso, legenda — non le schede."""
    prefisso = str(app._nb)
    return [w for w in _discendenti(app) if not str(w).startswith(prefisso)]


def _perduti(controlli):
    """Quelli che non sono proprio sullo schermo: non tagliati, assenti."""
    return [w for w in controlli if not w.winfo_ismapped()]


def _oltre_il_bordo(app, controlli):
    larghezza, altezza = app.winfo_width(), app.winfo_height()
    x0, y0 = app.winfo_rootx(), app.winfo_rooty()
    fuori = []
    for w in controlli:
        if not w.winfo_ismapped():
            continue
        x, y = w.winfo_rootx() - x0, w.winfo_rooty() - y0
        if (y + w.winfo_height() > altezza + 1
                or x + w.winfo_width() > larghezza + 1 or x < -1 or y < -1):
            fuori.append(w)
    return fuori


#: Le azioni che devono restare raggiungibili: aprono uno strumento o
#: eseguono un comando che non ha altra strada nella finestra principale.
AZIONI_ESSENZIALI = ("button.count", "button.generate", "button.reset_all",
                     "button.settings", "button.verify", "button.presentation",
                     "button.protocol", "button.cayley", "button.conjugacy",
                     "button.exit", "button.real_game", "button.uniform_j")


def _azioni_essenziali_presenti(app):
    """Quante delle azioni essenziali sono davvero sullo schermo."""
    attese = {catalogo.tr(k) for k in AZIONI_ESSENZIALI}
    presenti = set()
    for w in _cornice(app):
        if not w.winfo_ismapped():
            continue
        testo = _etichetta(w)
        for attesa in attese:
            if attesa and attesa in testo:
                presenti.add(attesa)
    return presenti, attese


# ═════════════════ M04 — quello che oggi non si raggiunge ═══════════════════

def test_m04_a_1920x1080_tutto_c_e(applicazione):
    """Con spazio abbondante non manca niente: il problema è la riduzione."""
    _dimensiona(applicazione, "1920x1080")
    presenti, attese = _azioni_essenziali_presenti(applicazione)
    assert presenti == attese, sorted(attese - presenti)


@pytest.mark.parametrize("geometria", list(TARGET))
def test_m04_le_azioni_essenziali_restano_raggiungibili(applicazione,
                                                        geometria):
    _dimensiona(applicazione, geometria)
    presenti, attese = _azioni_essenziali_presenti(applicazione)
    assert presenti == attese, sorted(attese - presenti)


@pytest.mark.parametrize("geometria", list(TARGET))
def test_le_barre_vanno_a_capo_invece_di_perdere_pulsanti(applicazione,
                                                          geometria):
    """Nessun pulsante scompare: la barra occupa una riga in più."""
    _dimensiona(applicazione, geometria)
    for barra in (applicazione._barra_azioni, applicazione._barra_preset):
        assert barra.numero_di_righe() >= 1
        assert all(w.winfo_ismapped() for w in barra.voci()), geometria


def test_la_disposizione_delle_barre_non_innesca_un_ciclo(applicazione):
    """H2: un `<Configure>` che non cambia nulla non tocca nessun widget."""
    eventi = {"n": 0}
    barra = applicazione._barra_azioni
    identificatore = barra.bind(
        "<Configure>", lambda _e: eventi.__setitem__("n", eventi["n"] + 1),
        add="+")
    try:
        for geometria in ("1280x750", "1366x768", "1920x1080", "1280x750"):
            _dimensiona(applicazione, geometria)
        assert eventi["n"] <= 8, eventi["n"]
    finally:
        barra.unbind("<Configure>", identificatore)


def test_con_una_finestra_larga_le_azioni_tornano_su_una_riga(applicazione):
    """Il gruppo di destra resta a destra finché tutto ci sta."""
    larghezza, _ = _dimensiona(applicazione, "2200x900")
    barra = applicazione._barra_azioni
    assert barra.numero_di_righe() == 1
    ultimo = max(barra.voci(),
                 key=lambda w: w.winfo_rootx() - applicazione.winfo_rootx())
    destra = (ultimo.winfo_rootx() - applicazione.winfo_rootx()
              + ultimo.winfo_width())
    assert destra > larghezza - 80, "il gruppo di destra non è allineato a destra"


@pytest.mark.xfail(strict=True,
                   reason="M04: minsize(1200, 750) impedisce alla finestra di "
                          "essere alta 720")
def test_m04_la_finestra_sta_in_1280x720(applicazione):
    larghezza, altezza = _dimensiona(applicazione, "1280x720")
    assert (larghezza, altezza) == (1280, 720)


@pytest.mark.xfail(strict=True,
                   reason="M04: il contenuto delle schede non ha una "
                          "strategia di overflow")
@pytest.mark.parametrize("chiave", ["simulatore", "explorer"])
def test_m04_il_contenuto_delle_schede_e_raggiungibile(applicazione, chiave):
    """Sotto il bordo va bene, purché ci si possa arrivare scorrendo."""
    _dimensiona(applicazione, "1280x750")
    applicazione._seleziona_scheda(chiave)
    applicazione.update()
    scheda = applicazione._schede[chiave]
    controlli = _discendenti(scheda)

    perduti = [_etichetta(w) for w in _perduti(controlli)]
    fuori = [_etichetta(w) for w in _oltre_il_bordo(applicazione, controlli)]
    scorrevole = any(isinstance(w, (ttk.Scrollbar, tk.Scrollbar))
                     and w.winfo_ismapped()
                     for w in _discendenti(scheda, (ttk.Scrollbar, tk.Scrollbar)))
    assert perduti == [], perduti
    assert fuori == [] or scorrevole, fuori


# ═══════════════ tastiera: il banner d'aiuto di ogni scheda ═════════════════

def _banner_di(widget):
    from gioco27.gui.help_banner import HelpBanner

    trovati = []
    for figlio in widget.winfo_children():
        if isinstance(figlio, HelpBanner):
            trovati.append(figlio)
        trovati.extend(_banner_di(figlio))
    return trovati


def test_il_banner_daiuto_c_e_su_ogni_scheda(applicazione):
    """È il punto in cui si legge che cosa fa una scheda e si apre la Guida."""
    con_banner = [chiave for chiave, w in applicazione._schede.items()
                  if _banner_di(w)]
    assert len(con_banner) >= 8, con_banner


@pytest.mark.xfail(strict=True,
                   reason="M04: «Apri Guida» e «Mostra di più» sono Label "
                          "legate solo a <Button-1>")
def test_le_azioni_del_banner_si_usano_anche_da_tastiera(applicazione):
    banner = _banner_di(applicazione._schede["analisi"])[0]
    azioni = [w for w in banner.winfo_children()
              for w in [w] + list(w.winfo_children())
              if isinstance(w, tk.Label) and w.bind("<Button-1>")]
    assert azioni, "nessuna label cliccabile trovata"
    for azione in azioni:
        assert azione.cget("takefocus"), _etichetta(azione)
        assert azione.bind("<Return>") or azione.bind("<KeyPress-Return>")
        assert azione.bind("<space>") or azione.bind("<KeyPress-space>")


@pytest.mark.xfail(strict=True,
                   reason="M04: il testo lungo del banner si apre solo col "
                          "mouse, e non c'è altro modo di leggerlo")
def test_il_testo_lungo_del_banner_si_apre_da_tastiera(applicazione):
    banner = _banner_di(applicazione._schede["analisi"])[0]
    assert hasattr(banner, "_toggle")
    banner._toggle.focus_set()
    banner._toggle.event_generate("<Return>")
    applicazione.update()
    assert banner._open is True


def test_la_scheda_analisi_ha_gia_una_strategia_di_overflow(applicazione):
    """Non tutto è rotto: l'Analisi scorre già, ed è il modello da estendere."""
    _dimensiona(applicazione, "1280x750")
    applicazione._seleziona_scheda("analisi")
    applicazione.update()
    scheda = applicazione._schede["analisi"]
    barre = [w for w in _discendenti(scheda, (ttk.Scrollbar, tk.Scrollbar))
             if w.winfo_ismapped()]
    assert barre, "nessuna barra di scorrimento visibile"
    assert _perduti(_discendenti(scheda)) == []


# ══════════════════════ dialoghi: focus iniziale ════════════════════════════

#: I dialoghi principali del programma, con il modulo e la classe.
DIALOGHI = (
    ("cayley_dialog", "CayleyDialog"),
    ("conjugacy_dialog", "ConjugacyDialog"),
)

@pytest.mark.xfail(strict=True,
                   reason="M04: nessun dialogo sceglie il proprio focus "
                          "iniziale: lo assegna Tk, a caso")
@pytest.mark.parametrize("modulo,classe", DIALOGHI)
def test_i_dialoghi_scelgono_il_proprio_focus_iniziale(applicazione, modulo,
                                                       classe):
    """«Qualcosa ha il focus» non basta: deve essere una scelta del dialogo."""
    import importlib

    dlg = getattr(importlib.import_module(f"gioco27.gui.{modulo}"), classe)(
        applicazione)
    try:
        applicazione.update()
        atteso = getattr(dlg, "_focus_iniziale", None)
        assert atteso is not None, "il dialogo non dichiara un focus iniziale"
        assert dlg.focus_get() is atteso
    finally:
        dlg.destroy()


@pytest.mark.xfail(strict=True,
                   reason="M04: Esc non chiude i dialoghi di sola lettura")
@pytest.mark.parametrize("modulo,classe", DIALOGHI)
def test_esc_chiude_i_dialoghi_di_sola_lettura(applicazione, modulo, classe):
    """Per questi dialoghi «chiudi» e «annulla» sono la stessa cosa."""
    import importlib

    dlg = getattr(importlib.import_module(f"gioco27.gui.{modulo}"), classe)(
        applicazione)
    try:
        applicazione.update()
        assert dlg.bind("<Escape>"), "nessuna associazione per Esc"
    finally:
        try:
            dlg.destroy()
        except tk.TclError:
            pass


# ═══════════════ Canvas: informativi contro decorativi ══════════════════════

def test_i_canvas_del_programma_sono_censiti():
    """Quattro, e si sa a che cosa servono."""
    import ast

    canvas = {}
    for percorso in sorted((PACCHETTO / "gui").glob("*.py")):
        for n in ast.walk(ast.parse(percorso.read_text(encoding="utf-8"))):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "Canvas"):
                canvas.setdefault(percorso.name, []).append(n.lineno)
    assert set(canvas) == {"onboarding_tab.py", "distribution_tab.py",
                           "explorer_tab.py"}, sorted(canvas)


@pytest.mark.xfail(strict=True,
                   reason="M04: le matrici dell'Explorer sono disegnate e "
                          "basta; senza leggere il disegno non c'è nulla")
def test_le_matrici_dell_explorer_hanno_un_alternativa_testuale(applicazione):
    from gioco27.gui import explorer_tab

    assert hasattr(explorer_tab.ExplorerTabMixin, "_matrice_in_testo")


# ════════════════ metrica di partenza, per il documento ════════════════════

def test_quante_azioni_essenziali_si_perdono_oggi(applicazione):
    """Non è un contratto: è la misura che H2 deve migliorare."""
    misure = {}
    for geometria in TARGET:
        _dimensiona(applicazione, geometria)
        presenti, attese = _azioni_essenziali_presenti(applicazione)
        misure[geometria] = len(attese - presenti)
    assert misure["1920x1080"] == 0
    assert set(misure) == set(TARGET)
