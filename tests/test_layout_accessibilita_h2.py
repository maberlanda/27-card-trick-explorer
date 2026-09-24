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
    """Quelli che non sono sullo schermo pur essendo nella vista corrente.

    Non conta chi non è ancora stato collocato (`winfo_manager()` vuoto) né
    chi sta dentro un pannello che al momento non è mostrato: nel Simulatore e
    nel visualizzatore dei mescolamenti molti controlli appartengono a una
    fase che non è ancora cominciata, e la loro assenza non è un difetto di
    layout. Conta chi è collocato, ha il genitore sullo schermo e nonostante
    questo non compare: quello è spazio che non basta.
    """
    persi = []
    for w in controlli:
        if w.winfo_ismapped() or w.winfo_manager() == "":
            continue
        try:
            if w.master.winfo_ismapped():
                persi.append(w)
        except tk.TclError:
            pass
    return persi


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


@pytest.mark.parametrize("geometria", list(TARGET))
def test_m04_la_finestra_prende_la_dimensione_chiesta(applicazione, geometria):
    larghezza, altezza = _dimensiona(applicazione, geometria)
    assert f"{larghezza}x{altezza}" == geometria


@pytest.mark.parametrize("geometria", list(TARGET))
def test_nessun_controllo_resta_fuori_portata(applicazione, geometria):
    """Il contratto di H2-G1/G2/G3, su tutte le schede e in un colpo solo."""
    _dimensiona(applicazione, geometria)
    perduti = {}
    for chiave in sorted(applicazione._schede):
        applicazione._seleziona_scheda(chiave)
        applicazione.update()
        persi = _perduti(_discendenti(applicazione._schede[chiave]))
        if persi:
            perduti[chiave] = [_etichetta(w) for w in persi]
    assert perduti == {}, perduti


def test_le_aree_scorrevoli_mostrano_le_barre_solo_quando_servono(applicazione):
    """Se il contenuto ci sta, l'area non aggiunge niente da guardare."""
    _dimensiona(applicazione, "1920x1080")
    applicazione._seleziona_scheda("stadio0")
    applicazione.update()
    assert applicazione._aree_scorrevoli["stadio0"].barre_visibili() == (False,
                                                                        False)

    _dimensiona(applicazione, "1280x720")
    applicazione._seleziona_scheda("explorer")
    applicazione.update()
    assert applicazione._aree_scorrevoli["explorer"].puo_scorrere()


def test_l_area_scorrevole_si_usa_da_tastiera(applicazione):
    """La tela prende il focus con Tab e le frecce la muovono."""
    _dimensiona(applicazione, "1280x720")
    applicazione._seleziona_scheda("explorer")
    applicazione.update()
    area = applicazione._aree_scorrevoli["explorer"]
    assert area.tela.cget("takefocus")

    area.tela.focus_set()
    applicazione.update()
    partenza = area.tela.yview()[0]
    area.tela.event_generate("<Next>")
    applicazione.update()
    assert area.tela.yview()[0] > partenza, "PagGiù non ha mosso nulla"
    area.tela.event_generate("<Home>")
    applicazione.update()
    assert area.tela.yview()[0] == 0


@pytest.mark.parametrize("chiave", ["simulatore", "explorer", "tavola"])
def test_m04_il_contenuto_delle_schede_e_raggiungibile(applicazione, chiave):
    """Sotto il bordo va bene, purché ci si possa arrivare scorrendo."""
    _dimensiona(applicazione, "1280x720")
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


def test_il_testo_lungo_del_banner_si_apre_da_tastiera(applicazione):
    """Invio apre, Spazio richiude: senza toccare il mouse.

    La scheda va selezionata prima: Tk non consegna eventi a un widget che
    non è sullo schermo, e su una scheda non selezionata il banner non c'è.
    """
    _dimensiona(applicazione, "1280x720")
    applicazione._seleziona_scheda("analisi")
    applicazione.update()
    banner = _banner_di(applicazione._schede["analisi"])[0]
    assert banner._toggle.winfo_ismapped()

    banner._toggle.focus_set()
    applicazione.update()
    banner._toggle.event_generate("<Return>")
    applicazione.update()
    assert banner._open is True, "Invio non ha aperto il testo lungo"

    banner._toggle.event_generate("<space>")
    applicazione.update()
    assert banner._open is False, "Spazio non ha richiuso il testo lungo"


def test_il_collegamento_alla_guida_si_usa_da_tastiera(applicazione):
    _dimensiona(applicazione, "1280x720")
    applicazione._seleziona_scheda("analisi")
    applicazione.update()
    banner = _banner_di(applicazione._schede["analisi"])[0]
    assert hasattr(banner, "_link_guida")
    banner._link_guida.focus_set()
    applicazione.update()
    banner._link_guida.event_generate("<space>")
    applicazione.update()
    assert applicazione._nb.select() == str(applicazione._schede["guida"])


def test_il_focus_si_vede_sui_collegamenti_del_banner(applicazione):
    """H2-G6: il bordo cambia colore, così si capisce dove si è."""
    applicazione._seleziona_scheda("analisi")
    applicazione.update()
    banner = _banner_di(applicazione._schede["analisi"])[0]
    for etichetta in (banner._toggle, banner._link_guida):
        assert int(etichetta.cget("highlightthickness")) >= 1
        assert etichetta.cget("highlightcolor") != etichetta.cget(
            "highlightbackground")


def test_i_suggerimenti_compaiono_anche_col_focus(applicazione):
    """H2-G8: la stessa informazione, per chi non usa il mouse.

    Sotto Xvfb non c'è un gestore di finestre, quindi la finestra non riceve
    mai il focus dal sistema e `<FocusIn>` non arriverebbe da solo: l'evento
    si genera, ed è la logica del suggerimento che si sta verificando.
    """
    _dimensiona(applicazione, "1280x720")
    pulsante = applicazione._barra_azioni.voci()[0]
    assert pulsante.bind("<FocusIn>"), "nessuna reazione al focus"

    def riquadri():
        trovati = []

        def scendi(w):
            for figlio in w.winfo_children():
                if isinstance(figlio, tk.Toplevel):
                    trovati.append(figlio)
                scendi(figlio)
        scendi(applicazione)
        return trovati

    from gioco27.gui.tooltip import Tooltip

    prima = len(riquadri())
    pulsante.event_generate("<FocusIn>")
    # Il suggerimento compare dopo il ritardo previsto dal widget: si aspetta
    # quello, non un tempo inventato.
    applicazione.after(Tooltip.RITARDO + 150, applicazione.quit)
    applicazione.mainloop()
    assert len(riquadri()) == prima + 1, "nessun suggerimento comparso"

    pulsante.event_generate("<FocusOut>")
    applicazione.update()
    assert len(riquadri()) == prima


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

#: Ogni Canvas del programma, e a che cosa serve. Un Canvas «di struttura»
#: non porta informazione: è il modo in cui Tk fa scorrere un contenuto.
CANVAS = {
    "scorrimento.py":     "struttura — la tela di AreaScorrevole",
    "onboarding_tab.py":  "struttura — la tela che fa scorrere la scheda",
    "distribution_tab.py": "informativo — l'istogramma delle decomposizioni",
    "explorer_tab.py":    "informativo — le matrici 27×27 e i fattori 3×3",
}


def test_i_canvas_del_programma_sono_censiti():
    """Se ne compare uno nuovo, qualcuno deve dire a che cosa serve."""
    import ast

    trovati = set()
    for percorso in sorted((PACCHETTO / "gui").glob("*.py")):
        for n in ast.walk(ast.parse(percorso.read_text(encoding="utf-8"))):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "Canvas"):
                trovati.add(percorso.name)
    assert trovati == set(CANVAS), sorted(trovati ^ set(CANVAS))


def test_le_matrici_dell_explorer_hanno_un_alternativa_testuale(lingua):
    """I 27 valori e i tre fattori, scritti: non un riassunto, la permutazione."""
    from gioco27.gui.explorer_tab import ExplorerTabMixin

    perm = list(range(27))
    lingua("it")
    testo = ExplorerTabMixin._matrice_in_testo(perm, ["SCD_U", "CDS_U", "I_3"])
    for valore in (0, 13, 26):
        assert str(valore) in testo
    assert "SCD_U" in testo and "CDS_U" in testo
    assert "In testo" in testo

    lingua("en")
    inglese = ExplorerTabMixin._matrice_in_testo(perm)
    assert "As text" in inglese and "In testo" not in inglese
    assert "26" in inglese


def test_l_alternativa_testuale_compare_nella_vista(applicazione):
    """Non basta che il metodo esista: deve essere nella scheda, e leggibile."""
    _dimensiona(applicazione, "1280x720")
    applicazione._seleziona_scheda("explorer")
    applicazione.update()

    for area in (applicazione._mat_txt_t, applicazione._mat_txt_inv):
        assert area.cget("takefocus"), "non si raggiunge con Tab"
        assert area.cget("state") == "disabled", "è di sola lettura"
        assert area.get("1.0", "end").strip()

    perm = list(range(27))
    applicazione._fill_matrix_panel(
        perm, None, applicazione._mat_cv_t, applicazione._mat_lbl_t,
        applicazione._mat_fcvs_t, applicazione._mat_flbls_t,
        applicazione._mat_txt_t)
    applicazione.update()
    mostrato = applicazione._mat_txt_t.get("1.0", "end")
    assert "26" in mostrato and "0" in mostrato


def test_l_istogramma_ha_un_alternativa_testuale(lingua):
    """Totale, estremi e picco in parole; l'elenco completo è già testo."""
    from gioco27.gui.distribution_tab import DistributionFrame

    risultato = {"histogram": {1: 4, 2: 40, 3: 12}, "total_T": 56,
                 "total_decomp": 200}
    lingua("it")
    testo = DistributionFrame.istogramma_in_testo(risultato)
    assert "56" in testo and "Tabella dati" in testo
    assert "2" in testo                      # il picco

    lingua("en")
    inglese = DistributionFrame.istogramma_in_testo(risultato)
    assert "Data table" in inglese and "Tabella dati" not in inglese

    vuoto = DistributionFrame.istogramma_in_testo({"histogram": {}})
    assert vuoto and "56" not in vuoto


def test_la_tabella_dati_si_raggiunge_con_tab(applicazione):
    """È l'alternativa testuale dell'istogramma: deve essere focusabile."""
    _dimensiona(applicazione, "1280x720")
    applicazione._seleziona_scheda("distribuzione")
    applicazione.update()
    assert applicazione._distrib_frame._tbl_txt.cget("takefocus")


def test_i_canvas_informativi_hanno_tutti_un_alternativa():
    """Se ne compare uno informativo nuovo, deve portarsi dietro il testo."""
    informativi = {nome for nome, ruolo in CANVAS.items()
                   if ruolo.startswith("informativo")}
    assert informativi == {"distribution_tab.py", "explorer_tab.py"}

    from gioco27.gui.distribution_tab import DistributionFrame
    from gioco27.gui.explorer_tab import ExplorerTabMixin
    assert callable(ExplorerTabMixin._matrice_in_testo)
    assert callable(DistributionFrame.istogramma_in_testo)


# ═════════ il riscontro di un salvataggio: dentro il dialogo ════════════════
#
# G2 ha reso *visibile* il fallimento di `Config.save()` (R07) e H1 ha scritto
# il testo; il flusso e' rimasto un debito dichiarato. Una messagebox sopra il
# dialogo delle impostazioni sposta il fuoco, chiede un clic per essere
# chiusa e si ripresenta a ogni tentativo: tre finestre per un errore che non
# ha cambiato niente. Qui si fissa il flusso: il dialogo resta aperto, il
# messaggio si legge dove si stava lavorando, «Salva» e' ancora premibile.


class _CfgFinta(dict):
    """Una config con lo stesso contratto di `core.config.Config`."""

    def __init__(self, guasto=None):
        super().__init__(n_workers=2, use_parallel=True,
                         help_font_scale=1.0, language="it")
        self.guasto = guasto
        self.salvataggi = 0

    def save(self):
        self.salvataggi += 1
        if self.guasto is not None:
            raise self.guasto


@pytest.fixture
def impostazioni(applicazione, monkeypatch):
    """Apre il dialogo impostazioni con una config finta, e lo richiude.

    `messagebox` e' sostituito per intero: qualunque finestra il flusso
    provasse ad aprire finisce nella lista invece che sullo schermo, ed e'
    esattamente cio' che i test qui sotto contano.
    """
    from types import SimpleNamespace

    from gioco27.gui import app as app_module

    finestre = []
    monkeypatch.setattr(app_module, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: finestre.append(("info", a)),
        showerror=lambda *a, **k: finestre.append(("errore", a)),
        showwarning=lambda *a, **k: finestre.append(("avviso", a)),
        askyesno=lambda *a, **k: True))

    aperti = []

    def apri(cfg):
        monkeypatch.setattr(applicazione, "_cfg", cfg)
        applicazione._open_settings()
        applicazione.update()
        dlg = applicazione._avviso_impostazioni.winfo_toplevel()
        aperti.append(dlg)
        return dlg

    try:
        yield apri, finestre
    finally:
        for dlg in aperti:
            try:
                dlg.grab_release()
                dlg.destroy()
            except tk.TclError:
                pass
        try:
            applicazione.update()
        except tk.TclError:
            pass


def _guasto():
    from gioco27.core.config import ConfigNonSalvata

    return ConfigNonSalvata("/non/scrivibile/config.json", "Permission denied")


def test_il_dialogo_impostazioni_dichiara_il_suo_focus_iniziale(impostazioni):
    """Chi apre le impostazioni vuole cambiare qualcosa: il fuoco va la'."""
    apri, _ = impostazioni
    dlg = apri(_CfgFinta())
    atteso = getattr(dlg, "_focus_iniziale", None)
    assert atteso is not None, "il dialogo non dichiara un focus iniziale"
    assert isinstance(atteso, ttk.Spinbox), _etichetta(atteso)
    # `focus_lastfor` e' il fuoco *dentro* il dialogo: senza window
    # manager (Xvfb) la finestra puo' non avere il fuoco d'ingresso di X,
    # e allora `focus_get()` risponde None pur essendo tutto in ordine.
    assert dlg.focus_lastfor() is atteso
    assert dlg.bind("<Escape>"), "nessuna associazione per Esc"


def test_un_salvataggio_fallito_non_chiude_il_dialogo(impostazioni, lingua):
    """Il contratto di G2, ora osservato sul dialogo vero."""
    lingua("it")
    apri, finestre = impostazioni
    cfg = _CfgFinta(_guasto())
    dlg = apri(cfg)

    applicazione = dlg.master
    prima = dlg.winfo_reqheight()
    applicazione._salva_impostazioni.invoke()
    applicazione.update()

    assert cfg.salvataggi == 1
    assert dlg.winfo_exists(), "il dialogo si e' chiuso senza aver salvato"
    assert finestre == [], f"una messagebox sopra il dialogo: {finestre}"

    avviso = applicazione._avviso_impostazioni
    assert avviso.winfo_ismapped(), "l'avviso non e' sullo schermo"
    assert "config.json" in avviso.cget("text")
    assert "Permission denied" in avviso.cget("text")
    assert dlg.winfo_reqheight() > prima, \
        "l'avviso compare ma il dialogo non gli fa spazio"

    # «Salva» e' il controllo con cui si riprova: ha il fuoco ed e' premibile.
    salva = applicazione._salva_impostazioni
    assert dlg.focus_lastfor() is salva
    assert "disabled" not in str(salva.state())


def test_riprovare_non_impila_messaggi(impostazioni, lingua):
    """Tre tentativi, un solo avviso: nessuna cascata."""
    lingua("it")
    apri, finestre = impostazioni
    cfg = _CfgFinta(_guasto())
    dlg = apri(cfg)
    applicazione = dlg.master
    avviso = applicazione._avviso_impostazioni

    for _ in range(3):
        applicazione._salva_impostazioni.invoke()
        applicazione.update()

    assert cfg.salvataggi == 3
    assert finestre == []
    assert avviso.winfo_ismapped()
    assert len([w for w in dlg.winfo_children()
                if isinstance(w, tk.Toplevel)]) == 0
    assert dlg.winfo_exists()


def test_un_salvataggio_riuscito_chiude_il_dialogo(impostazioni):
    """Il rovescio del contratto: quando ha salvato, «fatto» e' vero."""
    apri, finestre = impostazioni
    cfg = _CfgFinta()
    dlg = apri(cfg)
    applicazione = dlg.master

    applicazione._salva_impostazioni.invoke()
    applicazione.update()

    assert cfg.salvataggi == 1
    assert not dlg.winfo_exists()
    assert finestre == []


def test_l_avviso_riappare_solo_se_serve(impostazioni, lingua):
    """Un tentativo riuscito dopo uno fallito non lascia l'errore in vista."""
    lingua("it")
    apri, _ = impostazioni
    cfg = _CfgFinta(_guasto())
    dlg = apri(cfg)
    applicazione = dlg.master

    applicazione._salva_impostazioni.invoke()
    applicazione.update()
    assert applicazione._avviso_impostazioni.winfo_ismapped()

    cfg.guasto = None
    applicazione._salva_impostazioni.invoke()
    applicazione.update()
    assert not dlg.winfo_exists()


def test_la_scelta_della_lingua_si_riscontra_nel_dialogo(impostazioni, lingua):
    """Anche il riscontro «riavvia per applicare» resta dentro il dialogo."""
    lingua("it")
    apri, finestre = impostazioni
    cfg = _CfgFinta()
    dlg = apri(cfg)
    applicazione = dlg.master

    inglese = catalogo.tr("settings.english")
    combo = next(c for c in _discendenti(dlg, (ttk.Combobox,))
                 if inglese in c.cget("values"))
    combo.set(inglese)
    combo.event_generate("<<ComboboxSelected>>")
    applicazione.update()

    assert cfg["language"] == "en"
    assert finestre == [], f"una messagebox sopra il dialogo: {finestre}"
    avviso = applicazione._avviso_impostazioni
    assert avviso.winfo_ismapped()
    assert avviso.cget("text") == catalogo.tr("status.language_restart")
    # non e' un errore: non lo dice col colore dell'errore
    assert str(avviso.cget("foreground")) != "#b00020"
    assert dlg.winfo_exists(), "cambiare lingua non chiude il dialogo"


def test_senza_un_avviso_il_comportamento_resta_quello_di_g2(monkeypatch):
    """La messagebox non e' stata rimossa: e' il ripiego di chi non ha dove
    scrivere in linea. Il default del metodo non cambia."""
    from types import SimpleNamespace

    from gioco27.gui import app as app_module

    finestre = []
    monkeypatch.setattr(app_module, "messagebox", SimpleNamespace(
        showinfo=lambda *a, **k: finestre.append(("info", a)),
        showerror=lambda *a, **k: finestre.append(("errore", a))))

    finto = SimpleNamespace(
        _cfg=_CfgFinta(),
        _segnala_config_non_salvata=lambda exc, parent: None)
    assert app_module.App._save_language_preference(finto, "en", None) is True
    assert [tipo for tipo, _ in finestre] == ["info"]

    riferiti = []
    finto = SimpleNamespace(
        _cfg=_CfgFinta(_guasto()),
        _segnala_config_non_salvata=lambda exc, parent: riferiti.append(exc))
    assert app_module.App._save_language_preference(finto, "en", None) is False
    assert len(riferiti) == 1 and [t for t, _ in finestre] == ["info"]


# ═══════════ errori del sistema operativo: una cornice sola ═════════════════

def test_la_cornice_dice_quale_file_e_lascia_il_dettaglio(lingua):
    """Il messaggio del sistema operativo non si traduce; il contorno si'."""
    from gioco27.gui.errori import per_file

    exc = OSError("Permission denied")
    for codice, atteso in (("it", "Non è stato possibile scrivere"),
                           ("en", "could not be written")):
        lingua(codice)
        titolo, messaggio = per_file(exc, "/tmp/cartella/analisi.csv")
        assert titolo and atteso in messaggio
        assert "analisi.csv" in messaggio
        assert "/tmp/cartella" not in messaggio, "il percorso intero non serve"
        assert "Permission denied" in messaggio, "il dettaglio resta intatto"


def test_senza_un_file_solo_la_cornice_generica(lingua):
    """Un export multiplo o la pulizia della cache non hanno «quel» file."""
    from gioco27.gui.errori import per_file

    exc = OSError("No space left on device")
    lingua("it")
    titolo, messaggio = per_file(exc, "")
    assert "«»" not in messaggio and "None" not in messaggio
    assert "No space left on device" in messaggio
    assert titolo == catalogo.tr("errore.file.titolo")

    # una rotta che ha gia' il suo titolo localizzato lo conserva
    titolo, _ = per_file(exc, "", titolo=catalogo.tr("export.error_title"))
    assert titolo == catalogo.tr("export.error_title")

    lingua("en")
    _, messaggio = per_file(exc, "")
    assert "The system reports" in messaggio


def test_nessuna_rotta_mostra_piu_un_errore_di_sistema_nudo():
    """H2: dov'era `str(exc)` c'e' la cornice, e si conta quante volte."""
    import ast

    incorniciate, nudi = {}, []
    for percorso in sorted((PACCHETTO / "gui").glob("*.py")):
        albero = ast.parse(percorso.read_text(encoding="utf-8"))
        for n in ast.walk(albero):
            if not isinstance(n, ast.Call):
                continue
            if isinstance(n.func, ast.Name) and n.func.id == "per_file":
                incorniciate[percorso.name] = \
                    incorniciate.get(percorso.name, 0) + 1
            if (isinstance(n.func, ast.Attribute)
                    and n.func.attr == "showerror"):
                for a in list(n.args) + [k.value for k in n.keywords]:
                    if any(isinstance(sub, ast.Call)
                           and isinstance(sub.func, ast.Name)
                           and sub.func.id == "str"
                           for sub in ast.walk(a)):
                        nudi.append(f"{percorso.name}:{n.lineno}")

    assert nudi == [], nudi
    assert incorniciate == {
        "analysis_tab.py": 5,        # TXT, CSV, Excel, HTML, PDF
        "app.py": 1,                 # pulizia della cache
        "cayley_dialog.py": 2,
        "conjugacy_dialog.py": 2,
        "decomposition.py": 3,
        "export_dialog.py": 1,       # export multiplo
        "export_group_dialog.py": 1,  # export in cartella
    }


# ═══════ collaudo: ridimensionamento, testo ingrandito, tastiera ════════════
#
# Il compartimento chiede il collaudo a 1280×720, 1366×768 e 1920×1080 e alle
# scale 1.0, 1.5 e 2.0. Le tre dimensioni si provano qui sopra. La scala di
# sistema — `tk scaling`, che deriva dai DPI dello schermo — **non** si cambia
# a programma avviato: Tk risolve la dimensione dei font quando li crea, e
# riscalare dopo non li ridisegna. Il collaudo alle tre scale si fa quindi con
# un processo per scala, sotto un display ai DPI voluti (72/108/144 → 1.0/1.5/
# 2.0): i numeri sono nel documento di chiusura. Quello che si puo' misurare
# in un solo processo, e che qui si fissa, e' la scala che il programma
# possiede davvero: «Dimensione testo aiuti», il knob delle impostazioni.


def _con_scala_aiuti(app, scala):
    from contextlib import contextmanager

    from gioco27.gui import uifont

    @contextmanager
    def contesto():
        precedente = uifont.get_scale()
        uifont.apply_scale(scala, root=app)
        app.update_idletasks()
        try:
            yield
        finally:
            uifont.apply_scale(precedente, root=app)
            app.update_idletasks()

    return contesto()


#: Le tre schede piu' dense: se l'ingrandimento rompe qualcosa, rompe qui.
DENSE = ("explorer", "analisi", "stadio0")


def test_il_programma_non_impone_una_scala_a_tk():
    """La scala di sistema e' dell'utente: nessuno la sovrascrive.

    `tk scaling` viene dai DPI dello schermo. Se il programma la fissasse,
    su un monitor ad alta densita' il testo resterebbe minuscolo — e sarebbe
    un difetto introdotto da noi, non del sistema.
    """
    sospette = []
    for percorso in sorted(PACCHETTO.rglob("*.py")):
        testo = percorso.read_text(encoding="utf-8")
        if '"scaling"' in testo or "'scaling'" in testo:
            sospette.append(percorso.name)
    assert sospette == [], sospette


@pytest.mark.parametrize("scala", [1.0, 1.6, 2.0])
@pytest.mark.parametrize("geometria", list(TARGET))
def test_il_testo_di_aiuto_ingrandito_non_perde_niente(applicazione, scala,
                                                       geometria):
    """Ingrandire il testo d'aiuto non fa sparire ne' azioni ne' controlli."""
    with _con_scala_aiuti(applicazione, scala):
        larghezza, altezza = _dimensiona(applicazione, geometria)
        assert f"{larghezza}x{altezza}" == geometria

        presenti, attese = _azioni_essenziali_presenti(applicazione)
        assert presenti == attese, sorted(attese - presenti)

        perduti = {}
        for chiave in DENSE:
            applicazione._seleziona_scheda(chiave)
            applicazione.update()
            persi = _perduti(_discendenti(applicazione._schede[chiave]))
            if persi:
                perduti[chiave] = [_etichetta(w) for w in persi]
        assert perduti == {}, perduti


def test_lo_scorrimento_si_accende_quando_il_testo_cresce(applicazione):
    """La strategia di overflow non e' decorativa: si vede accendersi.

    Lo stadio 0 a scala 1.0 ci sta tutto e non mostra nulla da scorrere; a
    scala 2.0 il suo contenuto supera la vista e l'area si apre. E' la stessa
    area, la stessa scheda: cambia solo quanto e' alto il testo.
    """
    _dimensiona(applicazione, "1920x1080")
    applicazione._seleziona_scheda("stadio0")
    applicazione.update()
    area = applicazione._aree_scorrevoli["stadio0"]

    with _con_scala_aiuti(applicazione, 1.0):
        applicazione.update()
        basso = area.contenuto.winfo_reqheight()
        assert area.barre_visibili() == (False, False)

    with _con_scala_aiuti(applicazione, 2.0):
        applicazione.update()
        alto = area.contenuto.winfo_reqheight()
        assert alto > basso, (basso, alto)
        assert area.puo_scorrere(), "il contenuto e' cresciuto e non si scorre"


# ─────────────────────────── tastiera, per davvero ──────────────────────────

def test_un_percorso_di_tastiera_arriva_a_un_risultato(applicazione):
    """Focus → Spazio → risultato, senza chiamare nessuna callback.

    Il test non invoca `_preset_gioco_reale`: mette il fuoco sul pulsante e
    manda la pressione del tasto, come farebbe una mano. Cio' che si misura
    e' l'effetto — il conteggio e la riga di stato — non che la funzione sia
    stata chiamata.
    """
    _dimensiona(applicazione, "1366x768")
    pulsanti = [w for w in applicazione._barra_preset.voci()
                if isinstance(w, ttk.Button)]
    atteso = catalogo.tr("button.real_game")
    pulsante = next(w for w in pulsanti if atteso in _etichetta(w))

    applicazione.count_var.set("—")
    # Senza window manager nessuno assegna il fuoco d'ingresso alla
    # finestra, e un dialogo chiuso poco prima lo lascia a un toplevel che
    # non esiste piu': Tk scarta allora i tasti. Su un desktop vero la mano
    # dell'utente non ha questo problema; qui lo si rimedia a mano.
    applicazione.focus_force()
    pulsante.focus_set()
    applicazione.update()
    assert applicazione.focus_lastfor() is pulsante

    pulsante.event_generate("<space>")
    applicazione.update()

    assert applicazione.count_var.get() == "1,728"
    assert applicazione.status_var.get() == catalogo.tr("status.real_game_preset")


def test_da_tastiera_si_attraversa_la_barra_nell_ordine_visivo(applicazione):
    """Tab segue la barra: l'ordine logico e' quello che si vede."""
    _dimensiona(applicazione, "1366x768")
    barra = applicazione._barra_azioni
    attesi = [w for w in barra.voci()
              if isinstance(w, (ttk.Button, ttk.Menubutton))
              and str(w.cget("takefocus")) not in ("0", "false")]
    assert len(attesi) >= 8, len(attesi)

    visitati, corrente = [], attesi[0]
    for _ in range(8 * len(attesi)):
        corrente = corrente.tk_focusNext()
        if corrente is None or corrente is attesi[0]:
            break
        if corrente in attesi:
            visitati.append(corrente)
    assert visitati == attesi[1:], [_etichetta(w) for w in visitati]


def test_ogni_azione_essenziale_puo_prendere_il_fuoco(applicazione):
    """H2-G6: nessuna azione essenziale e' raggiungibile solo col mouse.

    Trovato dal collaudo: le azioni della barra erano tutte sullo schermo a
    ogni dimensione, ma «Genera…» — il menu che porta a PDF e CSV — e' un
    `tk.Menubutton`, che nasce con `takefocus 0`: Tab non lo raggiungeva e
    la sua associazione di classe per lo spazio non arrivava mai a servire.
    Ora `rendi_menu_apribile` lo mette nel giro di Tab.
    """
    _dimensiona(applicazione, "1280x720")
    attese = {catalogo.tr(k) for k in AZIONI_ESSENZIALI}
    senza_fuoco = []
    for w in _cornice(applicazione):
        testo = _etichetta(w)
        if not any(a and a in testo for a in attese):
            continue
        if not w.winfo_ismapped():
            continue
        try:
            prendibile = str(w.cget("takefocus")) not in ("0", "false")
        except tk.TclError:
            prendibile = False
        if not prendibile:
            senza_fuoco.append(testo)
    assert senza_fuoco == [], senza_fuoco


def test_i_menu_di_esportazione_si_aprono_da_tastiera(applicazione):
    """Non basta raggiungerli: da fermi non servono a niente.

    Il test manda Invio sul pulsante e guarda se la tendina e' sullo schermo;
    poi la chiude, perche' un menu aperto tiene un grab e i test che seguono
    non riceverebbero piu' un tasto.
    """
    _dimensiona(applicazione, "1366x768")
    atteso = catalogo.tr("button.generate")
    menubutton = next(w for w in applicazione._barra_azioni.voci()
                      if isinstance(w, tk.Menubutton)
                      and atteso in _etichetta(w))
    assert str(menubutton.cget("takefocus")) not in ("0", "false")

    menu = applicazione.nametowidget(str(menubutton.cget("menu")))
    assert not menu.winfo_ismapped()

    applicazione.focus_force()
    menubutton.focus_set()
    applicazione.update()
    try:
        menubutton.event_generate("<Return>")
        applicazione.update()
        assert menu.winfo_ismapped(), "Invio non ha aperto la tendina"
    finally:
        try:
            applicazione.tk.call("tk::MenuUnpost", "")
        except tk.TclError:
            pass
        applicazione.update()
    assert not menu.winfo_ismapped()


def test_un_menu_disabilitato_non_si_apre(applicazione):
    """La tastiera non scavalca lo stato: se e' spento resta spento."""
    _dimensiona(applicazione, "1366x768")
    atteso = catalogo.tr("button.generate")
    menubutton = next(w for w in applicazione._barra_azioni.voci()
                      if isinstance(w, tk.Menubutton)
                      and atteso in _etichetta(w))
    menu = applicazione.nametowidget(str(menubutton.cget("menu")))
    precedente = str(menubutton.cget("state"))
    menubutton.configure(state="disabled")
    applicazione.focus_force()
    menubutton.focus_set()
    applicazione.update()
    try:
        menubutton.event_generate("<Return>")
        applicazione.update()
        assert not menu.winfo_ismapped()
    finally:
        try:
            applicazione.tk.call("tk::MenuUnpost", "")
        except tk.TclError:
            pass
        menubutton.configure(state=precedente)
        applicazione.update()


def test_tutti_i_menu_a_tendina_passano_dall_aiuto():
    """Cinque menubutton nel programma: nessuno dimenticato."""
    import ast

    usano, tutti = {}, {}
    for percorso in sorted((PACCHETTO / "gui").glob("*.py")):
        albero = ast.parse(percorso.read_text(encoding="utf-8"))
        for n in ast.walk(albero):
            if not isinstance(n, ast.Call):
                continue
            nome = (n.func.attr if isinstance(n.func, ast.Attribute)
                    else n.func.id if isinstance(n.func, ast.Name) else "")
            if nome == "Menubutton":
                tutti[percorso.name] = tutti.get(percorso.name, 0) + 1
            if nome == "rendi_menu_apribile":
                usano[percorso.name] = usano.get(percorso.name, 0) + 1
    assert sum(tutti.values()) == 5, tutti
    assert usano == tutti, {"senza tastiera": sorted(set(tutti) - set(usano))}


# ────────────────────────── le due lingue, sul posto ────────────────────────

def test_il_layout_regge_anche_in_inglese(lingua):
    """Le etichette inglesi sono larghe in modo diverso: la barra tiene.

    Costruire una seconda applicazione costa qualche secondo, ma la lingua si
    scegli all'avvio: e' l'unico modo di misurare la vista inglese vera
    invece di una traduzione applicata a widget gia' disposti.
    """
    radice = _display_o_salta()
    radice.destroy()
    from gioco27.gui import app as app_module

    lingua("en")
    app = app_module.App()
    try:
        app._livello = "esperto"
        app._apply_livello()
        app.update_idletasks()
        for geometria in TARGET:
            larghezza, altezza = _dimensiona(app, geometria)
            assert f"{larghezza}x{altezza}" == geometria
            presenti, attese = _azioni_essenziali_presenti(app)
            assert presenti == attese, (geometria, sorted(attese - presenti))
            for barra in (app._barra_azioni, app._barra_preset):
                assert all(w.winfo_ismapped() for w in barra.voci()), geometria

        # I2: il pannello ternario e i collegamenti parlano inglese e reggono
        app._seleziona_scheda("tavola")
        app._tavola_frame.vai_alla_riga(100)
        for geometria in TARGET:
            _dimensiona(app, geometria)
            for i in range(3):
                app._tavola_frame.pannello._schede.select(i)
                app.update()
                persi = _perduti(_discendenti(app._schede["tavola"]))
                assert persi == [], (geometria, i, [_etichetta(w) for w in persi])
        # (la lingua effettiva e' quella della configurazione caricata dall'App)
        assert app._tavola_frame._btn_usa_T.cget("text") == catalogo.tr(
            "nav.use_as_current")
        assert app._tavola_frame.pannello._schede.tab(0, "text") == catalogo.tr(
            "ternary.tab.board")

        # i testi che H2 ha aggiunto esistono anche in inglese
        nota = app.filter_frames[0]._nota_lbl.cget("text")
        assert catalogo.tr("filter.never_empty.note") in nota
        assert "mai vuoto" not in nota, "la nota e' rimasta in italiano"
    finally:
        try:
            app.destroy()
        except tk.TclError:
            pass


# ───────────────────── il colore non porta da solo ──────────────────────────

def test_il_colore_non_e_l_unico_portatore_di_informazione(applicazione):
    """Ogni stato che il programma colora, lo dice anche a parole.

    Non e' una dichiarazione di conformita': e' l'elenco dei posti dove in
    questo programma il colore porta significato, ciascuno con la sua
    controparte testuale, verificata qui.
    """
    from gioco27.gui.distribution_tab import DistributionFrame
    from gioco27.gui.explorer_tab import ExplorerTabMixin

    _dimensiona(applicazione, "1366x768")

    # conteggio e stato: testo, non colore
    applicazione._preset_j_uniform()
    applicazione.update()
    assert applicazione.count_var.get() not in ("", "—")
    assert applicazione.status_var.get() == catalogo.tr("status.uniform_j_preset")

    # i Canvas informativi: alternativa testuale nella loro vista
    testo = ExplorerTabMixin._matrice_in_testo(list(range(27)))
    assert str(26) in testo and testo.strip()
    riassunto = DistributionFrame.istogramma_in_testo(
        {"histogram": {2: 7, 3: 1}, "total_T": 8})
    assert "7" in riassunto and "8" in riassunto, riassunto
    assert DistributionFrame.istogramma_in_testo({"histogram": {}}) == \
        catalogo.tr("distribution.summary_empty")

    # le righe scartate dell'analisi: il motivo e' scritto, non colorato
    from gioco27.core.analisi import RigaScartata
    from gioco27.gui.errori import motivo_di

    scarto = RigaScartata(numero=3, campo="T",
                          motivo="T: lunghezza 2, attesa 27",
                          codice="lunghezza",
                          dati={"nome": "T", "ricevuta": 2, "attesa": 27})
    assert motivo_di(scarto).strip()
    assert "diagnostica_import" in (PACCHETTO / "gui" / "analysis_tab.py")\
        .read_text(encoding="utf-8")

    # l'avviso delle impostazioni: testo (il colore e' in aggiunta)
    sorgente = (PACCHETTO / "gui" / "app.py").read_text(encoding="utf-8")
    assert "avviso.configure(text=testo," in sorgente


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


# ═══════════════ I2 — pannello ternario della Tavola (D-I2-2, D-I2-8) ═══════

def _pannello(applicazione, geometria, numero=100):
    _dimensiona(applicazione, geometria)
    applicazione._seleziona_scheda("tavola")
    applicazione._tavola_frame.vai_alla_riga(numero)
    applicazione.update()
    return applicazione._tavola_frame.pannello


@pytest.mark.parametrize("geometria", TARGET)
@pytest.mark.parametrize("scheda", [0, 1, 2])
def test_i2_il_pannello_ternario_si_raggiunge(applicazione, geometria, scheda):
    """Nessun controllo perso; cio' che sta oltre il bordo si raggiunge scorrendo."""
    pannello = _pannello(applicazione, geometria)
    pannello._schede.select(scheda)
    applicazione.update()
    controlli = _discendenti(applicazione._schede["tavola"])
    assert [_etichetta(w) for w in _perduti(controlli)] == []
    fuori = _oltre_il_bordo(applicazione, controlli)
    area = (pannello._area_tabellone, pannello._area_carta,
            pannello._area_posizioni)[scheda]
    assert fuori == [] or area.puo_scorrere(), [_etichetta(w) for w in fuori]
    # la Tavola nel suo insieme non deve scorrere in orizzontale
    assert applicazione._aree_scorrevoli["tavola"].barre_visibili()[1] is False


def test_i2_le_barre_del_pannello_solo_quando_servono(applicazione):
    pannello = _pannello(applicazione, "1920x1080")
    pannello._schede.select(2)
    applicazione.update()
    assert pannello._area_posizioni.barre_visibili() == (False, False)
    for geometria in TARGET:
        pannello = _pannello(applicazione, geometria)
        for i, area in enumerate((pannello._area_tabellone, pannello._area_carta,
                                  pannello._area_posizioni)):
            pannello._schede.select(i)
            applicazione.update()
            assert area.barre_visibili()[1] is False, (geometria, i)


def test_i2_il_divisore_si_sposta_senza_cicli(applicazione):
    pannello = _pannello(applicazione, "1366x768")
    divisore = applicazione._tavola_frame._divisore
    for pos in (400, 900, 650):
        divisore.sashpos(0, pos)
        applicazione.update()
        prima = pannello._area_tabellone.barre_visibili()
        applicazione.update()
        assert pannello._area_tabellone.barre_visibili() == prima
    assert pannello.winfo_ismapped()


def test_i2_ordine_di_tab_nella_scheda_una_carta(applicazione):
    pannello = _pannello(applicazione, "1920x1080")
    pannello._schede.select(1)
    pannello._vai_al_passo(1)            # tutti i pulsanti del passo attivi
    applicazione.update()
    attesi = [pannello._spin_carta, *pannello._eps_check, pannello._btn_inizio,
              pannello._btn_indietro, pannello._btn_avanti,
              pannello._vai_realizzata, pannello._testo_carta]
    pannello._spin_carta.focus_set()
    applicazione.update()
    visti, w = [], pannello._spin_carta
    for _ in range(40):
        if w in attesi and w not in visti:
            visti.append(w)
        w = w.tk_focusNext()
        if w is None:
            break
    assert visti == attesi


def test_i2_le_alternative_testuali_sono_nella_vista(applicazione):
    pannello = _pannello(applicazione, "1280x720")
    for testo in (pannello._testo_tabellone, pannello._testo_carta):
        assert testo.cget("takefocus") and testo.cget("state") == "disabled"
        assert testo.get("1.0", "end").strip()
    assert str(pannello._tabella.cget("takefocus")) in ("", "1", "True",
                                                      "ttk::takefocus")


def test_i2_nessuna_informazione_solo_nel_colore(applicazione):
    pannello = _pannello(applicazione, "1366x768")
    pannello.imposta_carta(10)
    applicazione.update()
    evidenziate = [c for riga in pannello._celle for c in riga
                   if c.cget("style") == "CellaEvid.TLabel"]
    assert len(evidenziate) == 3
    assert all(c.cget("text").startswith("▶") for c in evidenziate)
    assert pannello._tabella.item("blocco0", "text")


# ═══════════ I3 — Pratica con conseguenze reali (D-I3-4, D-I3-5/6) ══════════

def _pratica_reale(app, geometria, errore=True):
    """Simulatore, sotto-scheda Pratica, modalità «conseguenze reali».

    Con `errore` si esegue una fase con E2 (mazzo rovesciato): il confronto
    si riempie e compare il recupero, cioè la vista più affollata.
    """
    _dimensiona(app, geometria)
    app._seleziona_scheda("simulatore")
    sim = app._simulator_frame
    sim.togli_disposizione_fissa()
    sim._practice_tab.master.select(sim._practice_tab)
    sim._card_var.set(0)
    sim._target_var.set(13)
    sim._find_sequence()
    sim._p_modo_var.set("conseguenze")
    sim._su_modo()
    app.update()
    colonna = next(g for g in range(3) if sim._sessione.carta in sim._p_cols[g])
    sim._practice_choose_col(colonna)
    app.update()
    if errore:
        sim._p_order_var.set(sim._p_impilamento_atteso())
        sim._p_fisico_var.set("E2")
        sim._practice_confirm_order()
        app.update()
        colonna = next(g for g in range(3)
                       if sim._sessione.carta in sim._p_cols[g])
        sim._practice_choose_col(colonna)      # di nuovo alla domanda d'ordine
        app.update()
    return sim


@pytest.mark.parametrize("geometria", TARGET)
def test_i3_la_pratica_reale_si_raggiunge(applicazione, geometria):
    sim = _pratica_reale(applicazione, geometria)
    controlli = _discendenti(applicazione._schede["simulatore"])
    assert [_etichetta(w) for w in _perduti(controlli)] == []
    for w in (sim._p_recupero_cb, sim._p_recupero_btn, sim._p_confirm_btn,
              *sim._p_fisico_radios, sim._p_modo_conseguenze):
        assert w.winfo_ismapped(), _etichetta(w)
    fuori = _oltre_il_bordo(applicazione, controlli)
    area = applicazione._aree_scorrevoli["simulatore"]
    assert fuori == [] or area.puo_scorrere(), [_etichetta(w) for w in fuori]
    # niente scorrimento orizzontale: la Pratica sta nella larghezza
    assert area.barre_visibili()[1] is False, sim.winfo_reqwidth()


def test_i3_il_confronto_e_testo_leggibile_e_marcato(applicazione):
    sim = _pratica_reale(applicazione, "1366x768")
    testo = sim._p_confronto_txt
    assert testo.cget("takefocus") and testo.cget("state") == "disabled"
    contenuto = testo.get("1.0", "end")
    assert "≠" in contenuto                  # la divergenza non è solo colore
    assert sim._p_recupero_lbl.cget("text").strip()


def test_i3_ordine_di_tab_nella_domanda_d_ordine(applicazione):
    """Impilamento → errore fisico → conferma, come si legge dall'alto."""
    sim = _pratica_reale(applicazione, "1920x1080", errore=False)
    primo = sim._p_order_cb
    attesi = [primo, *sim._p_fisico_radios, sim._p_confirm_btn]
    primo.focus_set()
    applicazione.update()
    visti, w = [], primo
    for _ in range(60):
        if w in attesi and w not in visti:
            visti.append(w)
        w = w.tk_focusNext()
        if w is None:
            break
    assert visti == attesi, [_etichetta(v) for v in visti]


def test_i3_il_ridimensionamento_non_innesca_cicli(applicazione):
    sim = _pratica_reale(applicazione, "1366x768")
    area = applicazione._aree_scorrevoli["simulatore"]
    for geometria in ("1280x720", "1920x1080", "1366x768"):
        _dimensiona(applicazione, geometria)
        prima = area.barre_visibili()
        applicazione.update()
        assert area.barre_visibili() == prima, geometria
    assert sim._p_reale_fr.winfo_ismapped()


def test_i3_la_pratica_reale_sta_in_1280_anche_in_inglese(lingua):
    """La lingua è forzata davvero: il frame si costruisce dopo set_language."""
    lingua("en")
    radice = _display_o_salta()
    try:
        radice.deiconify()
        from gioco27.gui.simulator_tab import SimulatorFrame
        sim = SimulatorFrame(radice)
        sim.pack(fill="both", expand=True)
        sim._card_var.set(0)
        sim._target_var.set(13)
        sim._find_sequence()
        sim._p_modo_var.set("conseguenze")
        sim._su_modo()
        radice.update()
        colonna = next(g for g in range(3)
                       if sim._sessione.carta in sim._p_cols[g])
        sim._practice_choose_col(colonna)
        radice.update()
        assert sim._p_modo_conseguenze.cget("text") == catalogo.tr(
            "practice.real.mode.consequences")
        assert "consequences" in sim._p_modo_conseguenze.cget("text").lower()
        assert sim.winfo_reqwidth() <= 1240, sim.winfo_reqwidth()
    finally:
        radice.destroy()


# ════════════ I4 — Spettatore (carta ignota), sotto-scheda del Simulatore ════

def _spettatore(app, geometria, risposte=2):
    """La vista dello spettatore dopo alcune risposte (testo al suo massimo)."""
    import random
    _dimensiona(app, geometria)
    app._seleziona_scheda("simulatore")
    sim = app._simulator_frame
    vista = sim._spettatore
    sim._notebook.select(vista)
    vista._modo_var.set("noto")
    vista._aggiorna_controlli()
    vista._rnd = random.Random(3)
    vista.avvia()
    app.update()
    for _ in range(risposte):
        vista.rispondi(0)
        vista.esegui_raccolta()
    app.update()
    return vista


@pytest.mark.parametrize("geometria", TARGET)
@pytest.mark.parametrize("risposte", [0, 3])
def test_i4_lo_spettatore_si_raggiunge(applicazione, geometria, risposte):
    vista = _spettatore(applicazione, geometria, risposte)
    controlli = _discendenti(applicazione._schede["simulatore"])
    assert [_etichetta(w) for w in _perduti(controlli)] == []
    for w in (vista._avvia_btn, vista._raccolta_btn, *vista._risposta_btn,
              vista._modo_noto, vista._modo_b12):
        assert w.winfo_ismapped(), _etichetta(w)
    area = applicazione._aree_scorrevoli["simulatore"]
    fuori = _oltre_il_bordo(applicazione, controlli)
    assert fuori == [] or area.puo_scorrere(), [_etichetta(w) for w in fuori]
    assert area.barre_visibili()[1] is False, vista.winfo_reqwidth()


def test_i4_ordine_di_tab(applicazione):
    vista = _spettatore(applicazione, "1920x1080", risposte=0)
    attesi = [vista._modo_noto, vista._modo_b12, vista._bersaglio_spin,
              vista._mescolato_chk, vista._avvia_btn, vista._pile,
              *vista._risposta_btn, vista._fisico_txt, vista._info_txt]
    vista._modo_noto.focus_set()
    applicazione.update()
    visti, w = [], vista._modo_noto
    for _ in range(80):
        if w in attesi and w not in visti:
            visti.append(w)
        w = w.tk_focusNext()
        if w is None:
            break
    assert visti == attesi, [_etichetta(v) for v in visti]


def test_i4_alternative_testuali_e_marcatori(applicazione):
    vista = _spettatore(applicazione, "1366x768", risposte=1)
    for testo in (vista._fisico_txt, vista._info_txt):
        assert testo.cget("takefocus") and testo.cget("state") == "disabled"
        assert testo.get("1.0", "end").strip()
    assert "▶[9]" in vista._conteggio_lbl.cget("text")   # non solo colore
    vista.rispondi(1)
    vista.rispondi(1)                                       # fuori turno
    applicazione.update()
    assert "⚠" in vista._fisico_txt.get("1.0", "end")


def test_i4_il_ridimensionamento_non_innesca_cicli(applicazione):
    vista = _spettatore(applicazione, "1366x768", risposte=3)
    area = applicazione._aree_scorrevoli["simulatore"]
    for geometria in ("1280x720", "1920x1080", "1366x768"):
        _dimensiona(applicazione, geometria)
        prima = area.barre_visibili()
        applicazione.update()
        assert area.barre_visibili() == prima, geometria
    assert vista.winfo_ismapped()


def test_i4_il_simulatore_sta_in_1280_anche_in_inglese(lingua):
    lingua("en")
    radice = _display_o_salta()
    try:
        radice.deiconify()
        from gioco27.gui.simulator_tab import SimulatorFrame
        sim = SimulatorFrame(radice)
        sim.pack(fill="both", expand=True)
        sim._notebook.select(sim._spettatore)
        sim._spettatore.avvia()
        for _ in range(3):
            sim._spettatore.rispondi(2)
            sim._spettatore.esegui_raccolta()
        radice.update()
        assert "Spectator" in sim._notebook.tab(sim._spettatore, "text")
        assert sim.winfo_reqwidth() <= 1240, sim.winfo_reqwidth()
    finally:
        radice.destroy()


# ═══ Explorer → Matrice: i fattori 3×3 prima della matrice 27×27 (fix UX) ═══
#
# H2 garantiva che i fattori fossero *raggiungibili* scorrendo. Qui il
# contratto e' piu' forte: aprendo la sotto-scheda, i fattori 3×3 di T e di
# T⁻¹ sono gia' *visibili* nell'area utile, con lo scorrimento in cima, senza
# che serva una finestra piu' alta di quella di collaudo.

def _matrice_aperta(app, geometria, prima=None):
    if prima is not None:              # es. una finestra alta ricordata dalla config
        _dimensiona(app, prima)
    _dimensiona(app, geometria)
    app._seleziona_scheda("explorer")
    app._explorer_nb.select(app._mat_cv_t.master.master)
    app.update()
    area = app._aree_scorrevoli["explorer"]
    area.tela.yview_moveto(0)
    app.update()
    return area


def _nella_vista(area, widget):
    vista = area.tela
    alto, basso = vista.winfo_rooty(), vista.winfo_rooty() + vista.winfo_height()
    y = widget.winfo_rooty()
    return widget.winfo_ismapped() and y >= alto - 1 and y + widget.winfo_height() <= basso + 1


@pytest.mark.parametrize("prima", [None, "1920x1400"])
@pytest.mark.parametrize("geometria", TARGET)
def test_explorer_fattori_3x3_visibili_senza_scorrere(applicazione, geometria, prima):
    area = _matrice_aperta(applicazione, geometria, prima)
    assert area.tela.yview()[0] == 0.0
    fattori = (applicazione._mat_fcvs_t + applicazione._mat_flbls_t
               + applicazione._mat_fcvs_inv + applicazione._mat_flbls_inv
               + [applicazione._mat_lbl_t, applicazione._mat_lbl_inv])
    fuori = [str(w) for w in fattori if not _nella_vista(area, w)]
    assert fuori == [], (geometria, fuori)


@pytest.mark.parametrize("geometria", TARGET)
def test_explorer_i_fattori_stanno_accanto_alla_matrice_27(applicazione, geometria):
    """Griglia 27×27 a sinistra; a destra forma canonica, fattori 3×3, testo."""
    _matrice_aperta(applicazione, geometria)
    for fattori, etichetta, matrice, testo in (
            (applicazione._mat_fcvs_t, applicazione._mat_lbl_t,
             applicazione._mat_cv_t, applicazione._mat_txt_t),
            (applicazione._mat_fcvs_inv, applicazione._mat_lbl_inv,
             applicazione._mat_cv_inv, applicazione._mat_txt_inv)):
        destra = matrice.winfo_rootx() + matrice.winfo_width()
        meta = matrice.winfo_rooty() + matrice.winfo_height() // 2
        assert all(f.winfo_rootx() >= destra for f in fattori)
        assert all(f.winfo_rooty() + f.winfo_height() <= meta for f in fattori)
        assert etichetta.winfo_rootx() >= destra
        assert etichetta.winfo_rooty() < min(f.winfo_rooty() for f in fattori)
        # l'alternativa testuale resta nel pannello: accanto alla griglia,
        # sotto i fattori
        assert testo.master is matrice.master
        assert testo.winfo_rootx() >= destra
        assert testo.winfo_rooty() >= max(f.winfo_rooty() + f.winfo_height()
                                          for f in fattori)


@pytest.mark.parametrize("geometria", TARGET)
def test_explorer_la_matrice_27_resta_raggiungibile(applicazione, geometria):
    area = _matrice_aperta(applicazione, geometria)
    for widget in (applicazione._mat_cv_t, applicazione._mat_cv_inv,
                   applicazione._mat_txt_t, applicazione._mat_txt_inv):
        if not _nella_vista(area, widget):
            assert area.puo_scorrere()
            visto = False
            for passo in range(21):              # si scorre come farebbe l'utente
                area.tela.yview_moveto(passo / 20)
                applicazione.update()
                if _nella_vista(area, widget):
                    visto = True
                    break
            assert visto, (geometria, str(widget))
            area.tela.yview_moveto(0)
            applicazione.update()
    assert area.barre_visibili()[1] is False


@pytest.mark.parametrize("geometria", TARGET)
def test_explorer_fattori_visibili_anche_dopo_un_calcolo(applicazione, geometria):
    """Con T calcolata le etichette dei fattori si riempiono: restano visibili."""
    _dimensiona(applicazione, geometria)
    applicazione._seleziona_scheda("explorer")
    applicazione._explorer_entry.delete("1.0", "end")
    applicazione._explorer_entry.insert("1.0", "(CDS_U x DSC_U x CSD_U) o MSC")
    applicazione._explorer_calc()
    area = _matrice_aperta(applicazione, geometria)
    try:
        assert applicazione._mat_flbls_t[0].cget("text") != "P1 = —"
        fattori = (applicazione._mat_fcvs_t + applicazione._mat_flbls_t
                   + applicazione._mat_fcvs_inv + applicazione._mat_flbls_inv)
        assert [str(w) for w in fattori if not _nella_vista(area, w)] == []
    finally:
        applicazione._explorer_clear()
        applicazione.update()


@pytest.mark.parametrize("geometria", TARGET)
def test_explorer_pannelli_matrice_con_margini_simmetrici(applicazione, geometria):
    """Il pannello non si allunga nel vuoto: sotto la griglia 27×27 resta lo
    stesso spazio che c'e' fra il titolo e la griglia."""
    _matrice_aperta(applicazione, geometria)
    for matrice in (applicazione._mat_cv_t, applicazione._mat_cv_inv):
        pannello = matrice.master
        titolo = pannello.grid_slaves(row=0, column=0)[0]
        sopra = matrice.winfo_rooty() - (titolo.winfo_rooty() + titolo.winfo_height())
        fondo_pannello = pannello.winfo_rooty() + pannello.winfo_height()
        sotto = fondo_pannello - (matrice.winfo_rooty() + matrice.winfo_height())
        assert sopra >= 10, sopra
        assert abs(sotto - sopra) <= 2, (geometria, sopra, sotto)
