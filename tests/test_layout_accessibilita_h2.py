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


@pytest.mark.parametrize("chiave", ["simulatore", "explorer"])
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
