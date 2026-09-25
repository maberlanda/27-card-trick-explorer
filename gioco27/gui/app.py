"""
App: finestra principale e orchestrazione di tutti i tab.

I tab principali sono implementati come mixin in moduli separati:
  preview_tab.py   → PreviewTabMixin   (🔍 Anteprima)
  analysis_tab.py  → AnalysisTabMixin  (📊 Analisi)
  explorer_tab.py  → ExplorerTabMixin  (🔬 Explorer)
e come Frame autonomi: cycles_tab, distribution_tab, simulator_tab.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import threading

from ..core.export_combinazioni import write_csv_parallel
from ..core.combinations import count_combinations_ex, generate_pdf_ex_parallel
from ..core.detail_pdf import MAX_DETAIL_COMBOS, generate_detail_pdf_parallel
from ..core.config import ConfigNonSalvata, get_config
from ..core.parallel import (MAX_EXPORT_ITEMS, ExportAnnullato,
                             ExportTooLarge)
from ..core.log import get_logger
from .common import (EtaEstimator, prepara_dialogo, rendi_menu_apribile,
                     run_in_thread, ui_call)
from .errori import per_file, per_utente
from .filter_frame import FilterFrame
from .cycles_tab import CyclesFrame
from .distribution_tab import DistributionFrame
from .simulator_tab import SimulatorFrame
from .tavola_tab import TavolaFrame
from .export_dialog import ExportDialog
from .conjugacy_dialog import ConjugacyDialog
from .cayley_dialog import CayleyDialog
from .presentation import PresentationWindow
from .protocol_dialog import ProtocolDialog
from .guide import build_guide_content, numero_sezione
from .preview_tab import PreviewTabMixin
from .analysis_tab import AnalysisTabMixin
from .barra import BarraAdattiva
from .scorrimento import AreaScorrevole
from .explorer_tab import ExplorerTabMixin
from .onboarding_tab import OnboardingTabMixin
from .sessione_tab import SessioneMixin
from . import tooltip as _tooltip
from .i18n import set_language, tr
from .help_banner import HelpBanner
from .glossary import TAB_HELP, testo_aiuto_scheda
from . import livelli as _livelli
from . import uifont

_log = get_logger(__name__)


def _window_title(version):
    """Return the localized title for the main application window."""

    return tr("app.title", version=version)


# Etichette e valori del rapporto di `selftest()`: il dizionario restituito dal
# core resta un dato (chiavi e valori invariati, usati anche da riga di
# comando e dai test); la GUI lo mostra nella lingua attiva.
_SELFTEST_VALUE_KEYS = {
    "saltato (numpy assente)": "verify.value.skipped_numpy",
    "TUTTO OK": "verify.value.all_ok",
}


def format_selftest_report(rapporto):
    """Testo del rapporto di verifica, una riga per controllo, localizzato."""
    from .i18n import CATALOGS
    righe = []
    for key, value in rapporto.items():
        label_key = f"verify.label.{key}"
        label = tr(label_key) if label_key in CATALOGS["it"] else key
        value_key = _SELFTEST_VALUE_KEYS.get(value)
        shown = tr(value_key) if value_key else value
        righe.append(f"{label:26s} {shown}")
    return "\n".join(righe)


def _shell_tab_text(key, icon="", **values):
    """Return a localized main-notebook label while preserving its icon."""

    icon_prefix = f"{icon}  " if icon else ""
    return f"  {icon_prefix}{tr(key, **values)}  "


class App(PreviewTabMixin, AnalysisTabMixin, ExplorerTabMixin,
          OnboardingTabMixin, SessioneMixin, tk.Tk):

    # ── Colori semantici ──────────────────────────────────────────────────────
    C_BG        = "#F5F7FA"
    C_ACTION_BG = "#E8EDF5"
    C_PRESET_BG = "#FFF8F0"

    def __init__(self):
        super().__init__()
        from .. import __version__ as _APP_VER
        self.configure(bg=self.C_BG)
        self.resizable(True, True)
        # H2: la dimensione minima era 1200x750, e da sola impediva alla
        # finestra di stare in 1280x720. Il contenuto delle schede scorre
        # (AreaScorrevole) e le barre vanno a capo (BarraAdattiva), quindi la
        # finestra non ha più bisogno di quello spazio per esistere: resta un
        # minimo sotto il quale la finestra smetterebbe di avere senso.
        self.minsize(900, 560)

        # ── Config persistente ─────────────────────────────────────────────
        self._cfg = get_config()
        # Seleziona la lingua prima di costruire i widget.  La conversione
        # delle stringhe esistenti a tr() avverrà in blocchi successivi.
        set_language(self._cfg.get("language", "it"))
        self.title(_window_title(_APP_VER))
        # DP7 (I7): quattro livelli; i valori salvati dalle versioni
        # precedenti sono migrati da core.config (principiante → base,
        # esperto → laboratorio).
        self._livello = _livelli.normalizza(self._cfg.get("livello", "base"))
        # Alla prima apertura della UI guidata si parte da Base: gli strumenti
        # non sono rimossi, si mostrano salendo di livello.
        if not self._cfg.get("ui_intro_done", False):
            self._livello = _livelli.BASE
            self._cfg["livello"] = _livelli.BASE
            self._cfg["ui_intro_done"] = True
            try:
                self._cfg.save()
            except Exception:
                # Migrazione una-tantum, durante la costruzione della finestra:
                # non c'e' ancora una UI su cui mostrare un errore, e non aver
                # potuto scrivere il flag non impedisce di partire. `save()` lo
                # ha gia' registrato nel log. Qui il silenzio e' deliberato, non
                # un falso successo: nulla viene annunciato all'utente.
                pass

        # Font dei testi d'aiuto, scalabili dall'utente (utile su 4K)
        uifont.apply_scale(self._cfg.get("help_font_scale", 1.0), root=self)
        self._presentation_win = None   # finestra presentazione (singleton)
        self._last_T_perm      = None   # ultima T calcolata (per protocollo)
        # Un solo export massivo alla volta: due export concorrenti si
        # rubavano la progress bar e saturavano la CPU con 2xN processi.
        self._export_busy      = False
        self._closing          = False
        # Impostato dal pulsante «Annulla»; letto dal thread di lavoro tramite
        # la callback `annullato` passata alle funzioni di export.
        self._export_stop      = threading.Event()
        self._last_inv_perm    = None   # ultima T⁻¹ calcolata

        # Ripristina geometria finestra
        geom = self._cfg.get("window_geometry")
        if geom:
            try:
                self.geometry(geom)
            except Exception:
                pass

        self._configure_styles()
        self._sessione_init()      # J: sessione scientifica e cronologia
        self._build_ui()
        self._sessione_collega()
        self._update_count()   # conteggio iniziale

        # Salva config alla chiusura
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Stili ttk ─────────────────────────────────────────────────────────────

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Aspetto coerente per tutti i pulsanti standard
        style.configure("TButton", font=("Segoe UI", 10), padding=(8, 4))
        style.map("TButton", background=[("active", "#DCE6F2")])

        # LabelFrame principale stadio
        style.configure("TLabelframe",
                        background=self.C_BG,
                        bordercolor="#B0BEC5")
        style.configure("TLabelframe.Label",
                        font=("Segoe UI", 11, "bold"),
                        foreground="#1a1a2e",
                        background=self.C_BG)

        # Sezione P (bordo blu)
        style.configure("PSection.TLabelframe",
                        background="#EBF5FB",
                        bordercolor="#1a5276",
                        borderwidth=2)
        style.configure("PSection.TLabelframe.Label",
                        font=("Segoe UI", 10, "bold"),
                        foreground="#1a5276",
                        background=self.C_BG)

        # Sezione J (bordo arancione)
        style.configure("JSection.TLabelframe",
                        background="#FFF3E0",
                        bordercolor="#E65100",
                        borderwidth=2)
        style.configure("JSection.TLabelframe.Label",
                        font=("Segoe UI", 10, "bold"),
                        foreground="#BF360C",
                        background=self.C_BG)

        # Checkbutton P (blu)
        style.configure("P.TCheckbutton",
                        font=("Consolas", 10),
                        foreground="#1a5276",
                        background="#EBF5FB")
        style.map("P.TCheckbutton",
                  background=[("active", "#D6EAF8")])

        # Checkbutton J (arancione)
        style.configure("J.TCheckbutton",
                        font=("Consolas", 10),
                        foreground="#7b4000",
                        background="#FFF3E0")
        style.map("J.TCheckbutton",
                  background=[("active", "#FFE0B2")])

        # Checkbutton J Uniformi (prominente)
        style.configure("JUniform.TCheckbutton",
                        font=("Segoe UI", 11, "bold"),
                        foreground="#BF360C",
                        background="#FFF3E0")
        style.map("JUniform.TCheckbutton",
                  background=[("active", "#FFE0B2")])

        # Bottoni azione principali
        style.configure("Action.TButton",
                        font=("Segoe UI", 12, "bold"),
                        padding=(10, 6))

        # Bottoni preset
        style.configure("Preset.TButton",
                        font=("Segoe UI", 11),
                        padding=(8, 5))
        style.configure("GiocoReale.TButton",
                        font=("Segoe UI", 11, "bold"),
                        foreground="#7b4000",
                        padding=(8, 5))
        style.configure("Quit.TButton",
                        font=("Segoe UI", 11, "bold"),
                        foreground="#8b0000",
                        padding=(8, 5))
        style.map("Quit.TButton",
                  background=[("active", "#fdecea")],
                  foreground=[("active", "#c00000")])

        # Label generiche
        style.configure("TLabel",
                        font=("Segoe UI", 11),
                        background=self.C_BG)
        style.configure("Status.TLabel",
                        font=("Segoe UI", 11),
                        foreground="#2c3e50",
                        background=self.C_ACTION_BG)
        style.configure("Count.TLabel",
                        font=("Segoe UI", 13, "bold"),
                        foreground="#1a5276",
                        background=self.C_ACTION_BG)

    # ── Costruzione UI ────────────────────────────────────────────────────────

    def _quit_app(self):
        """Usa la stessa procedura della chiusura della finestra."""
        self._on_close()

    def _build_ui(self):
        # ── Barra azioni ──────────────────────────────────────────────────────
        action_bar = tk.Frame(self, bg=self.C_ACTION_BG,
                              bd=0, highlightthickness=0)
        action_bar.pack(fill="x")

        # H2: la barra va a capo invece di lasciar fuori i pulsanti. Prima era
        # una riga di `pack(side=...)`: a 1280x720 cinque azioni — Verifica,
        # Presentazione, Protocollo, Cayley, Coniugio — sparivano del tutto.
        inner = BarraAdattiva(action_bar, padding=(10, 8))
        inner.pack(fill="x")
        self._barra_azioni = inner

        def _azione(widget, suggerimento=None, padx=4, a_destra=False,
                    elastico=False):
            inner.aggiungi(widget, padx=padx, a_destra=a_destra,
                           elastico=elastico)
            if suggerimento:
                _tooltip.attach(widget, suggerimento)
            return widget

        #: I7 (DP7): azioni della barra governate dal livello (gui/livelli.py)
        self._azioni_livello = {}
        self._azioni_livello["conteggio"] = _azione(
            ttk.Button(inner, text=f"🔢  {tr('button.count')}",
                       style="Action.TButton", command=self._count),
            tr("tooltip.count"))
        gen_mb = tk.Menubutton(inner, text=f"⬇  {tr('button.generate')}",
                               relief="raised")
        gen_menu = tk.Menu(gen_mb, tearoff=0)
        gen_menu.add_command(label="📄  PDF",    command=self._gen_pdf)
        gen_menu.add_command(label=f"📄  {tr('menu.pdf_detailed')}", command=self._gen_pdf_detail)
        gen_menu.add_command(label="📊  CSV (;)", command=self._gen_csv)
        gen_mb["menu"] = gen_menu
        rendi_menu_apribile(gen_mb)
        self._azioni_livello["genera"] = _azione(gen_mb, tr("tooltip.generate"))
        _azione(ttk.Button(inner, text=f"↺  {tr('button.reset_all')}",
                           style="Action.TButton", command=self._reset),
                tr("tooltip.reset_all"))

        inner.separatore()
        # DP7: selettore dei quattro livelli (tastiera: Tab, poi frecce)
        scelta = ttk.Frame(inner, style="Action.TFrame")
        ttk.Label(scelta, text=f"🎓  {tr('level.label')}",
                  style="Status.TLabel").pack(side="left")
        self._livello_cb = ttk.Combobox(
            scelta, state="readonly", width=13,
            values=[tr(f"level.name.{l}") for l in _livelli.LIVELLI])
        self._livello_cb.current(_livelli.indice(self._livello))
        self._livello_cb.pack(side="left", padx=(6, 0))
        self._livello_cb.bind("<<ComboboxSelected>>",
                              lambda e: self._imposta_livello(
                                  _livelli.LIVELLI[self._livello_cb.current()]))
        _azione(scelta, tr("tooltip.level"))

        inner.separatore()

        # Contatore live (aggiornato al cambio di qualsiasi filtro)
        count_frame = ttk.Frame(inner, style="Action.TFrame")
        ttk.Label(count_frame, text=tr("label.combinations"),
                  style="Status.TLabel").pack(side="left")
        self.count_var = tk.StringVar(value="—")
        ttk.Label(count_frame, textvariable=self.count_var,
                  style="Count.TLabel").pack(side="left", padx=(6, 0))
        self._azioni_livello["combinazioni"] = _azione(count_frame, None)

        self.status_var = tk.StringVar(value="")
        self._status_lbl = ttk.Label(inner, textvariable=self.status_var,
                                     style="Status.TLabel", wraplength=380)
        # La riga di stato è l'elemento che cede: è l'unico che può stare
        # stretto senza che si perda un'azione.
        _azione(self._status_lbl, None, padx=14, elastico=True)

        # ── Strumenti avanzati: a destra quando tutto sta su una riga ─────────
        inner.separatore(padx=6, a_destra=True)
        self._azioni_livello["coniugio"] = _azione(
            ttk.Button(inner, text=f"🔬  {tr('button.conjugacy')}",
                       command=self._open_conjugacy),
            tr("tooltip.conjugacy"), padx=2, a_destra=True)
        self._azioni_livello["cayley"] = _azione(
            ttk.Button(inner, text=f"🔮  {tr('button.cayley')}",
                       command=self._open_cayley),
            tr("tooltip.cayley"), padx=2, a_destra=True)
        inner.separatore(padx=6, a_destra=True)
        self._azioni_livello["protocollo"] = _azione(
            ttk.Button(inner, text=f"📋  {tr('button.protocol')}",
                       command=self._open_protocol),
            tr("tooltip.protocol"), padx=2, a_destra=True)
        # J: esperimento, cronologia, undo/redo e successione (tutti i livelli)
        self._btn_sessione = _azione(
            ttk.Button(inner, text=f"🗂  {tr('button.session')}", command=self._open_sessione),
            tr("tooltip.session"), padx=2, a_destra=True)
        _azione(ttk.Button(inner, text=f"🖥️  {tr('button.presentation')}",
                           command=self._open_presentation),
                tr("tooltip.presentation"), padx=2, a_destra=True)
        _azione(ttk.Button(inner, text=f"✔  {tr('button.verify')}",
                           command=self._run_selftest),
                tr("tooltip.verify"), padx=2, a_destra=True)
        _azione(ttk.Button(inner, text=f"⚙️  {tr('button.settings')}",
                           command=self._open_settings),
                tr("tooltip.settings"), padx=2, a_destra=True)
        _azione(ttk.Button(inner, text=f"⏻  {tr('button.exit')}",
                           style="Quit.TButton", command=self._on_close),
                tr("tooltip.exit"), padx=2, a_destra=True)
        # Il separatore che chiudeva la barra all'estremo destro non separava
        # nulla: costava 42 px di larghezza e non portava informazione.

        # ── Barra preset ──────────────────────────────────────────────────────
        preset_bar = tk.Frame(self, bg=self.C_PRESET_BG,
                              bd=0, highlightthickness=0,
                              highlightbackground="#E65100")
        preset_bar.pack(fill="x")
        self._barra_preset_frame = preset_bar

        pinner = BarraAdattiva(preset_bar, padding=(10, 6))
        pinner.pack(fill="x")
        self._barra_preset = pinner

        pinner.aggiungi(ttk.Label(pinner, text=tr("label.quick_presets"),
                                  font=("Segoe UI", 10, "bold"),
                                  foreground="#7b4000",
                                  background=self.C_PRESET_BG), padx=0)

        _b = pinner.aggiungi(ttk.Button(
            pinner, text=f"🎴  {tr('button.real_game')}",
            style="GiocoReale.TButton", command=self._preset_gioco_reale))
        _tooltip.attach(_b, tr("tooltip.real_game"))

        _b = pinner.aggiungi(ttk.Button(
            pinner, text=f"⚡  {tr('button.uniform_j')}",
            style="Preset.TButton", command=self._preset_j_uniform))
        _tooltip.attach(_b, tr("tooltip.uniform_j"))

        _b = pinner.aggiungi(ttk.Button(
            pinner, text=f"↺  {tr('button.quick_reset')}",
            style="Preset.TButton", command=self._reset))
        _tooltip.attach(_b, tr("tooltip.quick_reset"))

        # ── Progress bar + Annulla ────────────────────────────────────────────
        prog_row = ttk.Frame(self)
        prog_row.pack(fill="x", padx=12, pady=(4, 0))
        self._riga_progresso = prog_row
        self.progress = ttk.Progressbar(prog_row, orient="horizontal",
                                        mode="determinate", length=400)
        self.progress.pack(side="left", fill="x", expand=True)
        # Disabilitato finche' non c'e' un export in corso: un pulsante che non
        # fa nulla e' peggio di un pulsante assente.
        self._btn_annulla = ttk.Button(prog_row, text="✕  Annulla",
                                       state="disabled",
                                       command=self._annulla_export)
        self._btn_annulla.configure(text=f"✕  {tr('button.cancel_export')}")
        self._btn_annulla.pack(side="left", padx=(8, 0))
        _tooltip.attach(self._btn_annulla, tr("tooltip.cancel_export"))

        # ── Notebook ─────────────────────────────────────────────────────────
        # Legenda colori sempre visibile, in fondo alla finestra
        self._build_legend_bar().pack(fill="x", side="bottom")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        self._nb = nb
        #: chiave stabile → widget della scheda. Le etichette sono tradotte,
        #: le chiavi no: e' cio' che rende la navigazione indipendente dalla
        #: lingua (H1).
        self._schede = {}
        #: chiave della scheda → area scorrevole che ne contiene il corpo (H2)
        self._aree_scorrevoli = {}

        # Scheda introduttiva, in testa a tutto
        self._aggiungi_scheda(nb, "inizio", self._build_onboarding_tab(nb),
                              _shell_tab_text("tab.start", "🚀"))

        # Stadi (ciascuno con il suo banner d'aiuto)
        self.filter_frames = []
        self._stadi_wraps = []
        for i in range(3):
            wrap = ttk.Frame(nb)
            short_key, long_key = TAB_HELP["stadio"]
            self._mk_banner(wrap, tr(short_key), tr(long_key),
                            section="s12").pack(fill="x")
            area = AreaScorrevole(wrap)
            area.pack(fill="both", expand=True)
            ff = FilterFrame(area.contenuto, stage_num=i,
                             on_change=self._update_count)
            ff.pack(fill="both", expand=True)
            self._aree_scorrevoli[f"stadio{i}"] = area
            self.filter_frames.append(ff)
            self._stadi_wraps.append(wrap)
            self._aggiungi_scheda(nb, f"stadio{i}", wrap,
                                  _shell_tab_text("tab.stage", number=i))

        # Percorso lineare (livello Base): gioco → tavola → esplorazione
        self._aggiungi_scheda(
            nb, "simulatore",
            self._wrap_tab(self._build_simulator_tab, "simulatore", "s19"),
            _shell_tab_text("tab.simulator", "🎩"))
        self._aggiungi_scheda(
            nb, "tavola", self._wrap_tab(self._build_tavola_tab, "tavola", "s11"),
            _shell_tab_text("tab.table", "📚"))
        self._aggiungi_scheda(
            nb, "anteprima",
            self._wrap_tab(self._build_anteprima_tab, "anteprima", "s14"),
            _shell_tab_text("tab.preview", "🔍"))
        self._aggiungi_scheda(
            nb, "analisi",
            self._wrap_tab(self._build_analisi_tab, "analisi", "s15"),
            _shell_tab_text("tab.analysis", "📊"))
        self._tab_explorer = self._aggiungi_scheda(
            nb, "explorer",
            self._wrap_tab(self._build_explorer_tab, "explorer", "s16"),
            _shell_tab_text("tab.explorer", "🔬"))
        self._aggiungi_scheda(nb, "guida", self._build_guide_tab(nb),
                              _shell_tab_text("tab.guide", "📖"))
        self._tab_cycles = self._aggiungi_scheda(
            nb, "cicli", self._wrap_tab(self._build_cycles_tab, "cicli", "s20"),
            _shell_tab_text("tab.cycles", "🔄"))
        self._tab_distrib = self._aggiungi_scheda(
            nb, "distribuzione",
            self._wrap_tab(self._build_distrib_tab, "distribuzione", "s21"),
            _shell_tab_text("tab.distribution", "📊"))

        # DP7: visibilita' dal mapping dichiarativo di gui/livelli.py
        self._apply_livello()

    # ── Legenda colori ────────────────────────────────────────────────────────

    def _build_legend_bar(self):
        """Striscia in fondo con i 6 colori dei generatori GEN3 (sempre visibile)."""
        from ..core.constants import PERM3_COLORS
        bar = tk.Frame(self, bg=self.C_ACTION_BG)
        tk.Label(bar, text=tr("label.color_legend"), bg=self.C_ACTION_BG,
                 fg="#2c3e50", font=("Segoe UI", 9, "bold")).pack(
                     side="left", padx=(12, 8), pady=3)
        for name, col in PERM3_COLORS.items():
            chip = tk.Frame(bar, bg=self.C_ACTION_BG)
            chip.pack(side="left", padx=6)
            tk.Label(chip, text="  ", bg=col, width=2,
                     relief="solid", bd=1).pack(side="left")
            tk.Label(chip, text=" " + name, bg=self.C_ACTION_BG, fg=col,
                     font=("Consolas", 9, "bold")).pack(side="left")
            _tooltip.attach(chip, tr("tooltip.color_chip", name=name))
        tk.Label(bar,
                 text=tr("label.legend_note"),
                 bg=self.C_ACTION_BG, fg="#8a96a3",
                 font=("Segoe UI", 8, "italic")).pack(side="left", padx=10)
        return bar

    # ── Livelli didattici (DP7) e navigazione ──────────────────────────────────

    def _mk_banner(self, parent, short, long=None, section=None):
        return HelpBanner(parent, short, long,
                          on_open_guide=self._open_guide, guide_section=section)

    def _wrap_tab(self, build_fn, key, section=None):
        """Contenitore con banner d'aiuto + la scheda, dentro un'area scorrevole.

        H2: il banner resta fermo in cima — è la spiegazione della scheda, e
        deve essere sempre leggibile — mentre il contenuto scorre quando non ci
        sta. Se ci sta, l'area non mostra nulla in più: le barre compaiono solo
        quando servono.
        """
        wrap = ttk.Frame(self._nb)
        short_key, long_key = TAB_HELP[key]
        self._mk_banner(wrap, tr(short_key), testo_aiuto_scheda(key),
                        section=section).pack(fill="x")
        area = AreaScorrevole(wrap)
        area.pack(fill="both", expand=True)
        inner = build_fn(area.contenuto)
        inner.pack(fill="both", expand=True)
        self._aree_scorrevoli[key] = area
        return wrap

    def _imposta_livello(self, livello):
        """DP7: cambia livello, lo ricorda nella config e aggiorna le viste."""
        self._livello = _livelli.normalizza(livello)
        self._cfg["livello"] = self._livello
        self._apply_livello()

    @property
    def _advanced_tabs(self):
        """Le schede principali nascoste al livello Base (vista derivata)."""
        schede = getattr(self, "_schede", None) or {}
        return [w for k, w in schede.items()
                if not _livelli.visibile(_livelli.SCHEDE[k], _livelli.BASE)]

    def _apply_livello(self):
        """Mostra/nasconde schede, sotto-schede e azioni secondo il livello.

        Solo visibilita': nessun widget viene distrutto e nessuna sessione
        viene azzerata. Se la scheda aperta sparisce si torna a «Inizia qui».
        """
        self._livello = _livelli.normalizza(self._livello)
        nb = getattr(self, "_nb", None)
        if nb is None:
            return
        corrente = self._livello
        schede = getattr(self, "_schede", None) or {}
        # la selezione va letta PRIMA di nascondere: Tk sposta da solo la
        # scheda aperta sulla successiva visibile
        try:
            aperta = nb.select()
        except tk.TclError:
            aperta = ""
        for chiave, widget in schede.items():
            vedi = _livelli.visibile(_livelli.SCHEDE[chiave], corrente)
            try:
                nb.tab(widget, state=("normal" if vedi else "hidden"))
            except tk.TclError:
                pass
        try:
            if aperta and nb.tab(aperta, "state") == "hidden":
                nb.select(schede.get("inizio", 0))
        except tk.TclError:
            pass
        enb = getattr(self, "_explorer_nb", None)
        sotto = getattr(self, "_sottoschede_explorer", None) or {}
        # Le sotto-schede contano solo quando l'Explorer stesso e' visibile
        # (ttk non nasconde l'ultima sotto-scheda rimasta di un notebook).
        if enb is not None and _livelli.visibile(_livelli.SCHEDE["explorer"], corrente):
            try:
                aperta = enb.select()
            except tk.TclError:
                aperta = ""
            for chiave, widget in sotto.items():
                vedi = _livelli.visibile(_livelli.SOTTOSCHEDE_EXPLORER[chiave], corrente)
                try:
                    enb.tab(widget, state=("normal" if vedi else "hidden"))
                except tk.TclError:
                    pass
            try:
                if aperta and enb.tab(aperta, "state") == "hidden":
                    enb.select(0)
            except tk.TclError:
                pass
        barra = getattr(self, "_barra_azioni", None)
        for chiave, widget in (getattr(self, "_azioni_livello", None) or {}).items():
            if barra is not None:
                barra.mostra(widget, _livelli.visibile(_livelli.AZIONI[chiave], corrente))
        preset = getattr(self, "_barra_preset_frame", None)
        if preset is not None:
            vedi = _livelli.visibile(_livelli.AZIONI["preset"], corrente)
            if vedi and not preset.winfo_manager():
                preset.pack(fill="x", before=self._riga_progresso)
            elif not vedi and preset.winfo_manager():
                preset.pack_forget()
        cb = getattr(self, "_livello_cb", None)
        if cb is not None:
            cb.current(_livelli.indice(corrente))
        onb = getattr(self, "_livello_onboarding_var", None)
        if onb is not None:
            onb.set(corrente)
        if hasattr(self, "_tavola_frame"):
            self._tavola_frame.aggiorna_navigazione()

    def _aggiungi_scheda(self, nb, chiave, widget, testo):
        """Aggiunge una scheda al notebook e ne registra la chiave stabile.

        H1: l'etichetta e' tradotta, la chiave no. Cercare una scheda per
        titolo funzionava finche' le due lingue scrivevano quella parola allo
        stesso modo — «Explorer» lo faceva per caso, «Guida»/«Guide» no, e
        infatti c'era gia' una tabella di alias per rimediare.
        """
        nb.add(widget, text=testo)
        self._schede[chiave] = widget
        return widget

    def _seleziona_scheda(self, chiave):
        """Porta in primo piano la scheda `chiave`. True se c'e' riuscita."""
        nb = getattr(self, "_nb", None)
        widget = (getattr(self, "_schede", None) or {}).get(chiave)
        if nb is None or widget is None:
            return False
        try:
            nb.select(widget)
        except tk.TclError:
            return False
        return True

    def _open_guide(self, section=None):
        """
        Porta in primo piano la scheda Guida e, se indicata, scorre fino alla
        sezione richiesta.

        `section` e' il numero della sezione (stringa, es. "13") passato dal
        banner d'aiuto della scheda. Prima veniva accettato e ignorato: ogni
        link «Apri Guida» apriva la Guida in cima, qualunque fosse la scheda
        di partenza.
        """
        self._seleziona_scheda("guida")
        if not section:
            return
        # I7: i banner indicano la sezione con l'identificatore stabile
        # (es. "s12"); il numero mostrato dipende dalla posizione nel percorso.
        try:
            section = numero_sezione(section)
        except KeyError:
            return
        txt = getattr(self, "_guide_text", None)
        mark = getattr(self, "_guide_marks", {}).get(str(section))
        if txt is None or mark is None:
            return
        try:
            # after_idle: la scheda deve essere gia' visibile, altrimenti Tk
            # non conosce ancora l'altezza del widget e `see` non scorre.
            self.after_idle(lambda: (txt.see(mark),
                                     txt.yview_scroll(-1, "units")))
        except tk.TclError:
            pass

    # ── Preset ───────────────────────────────────────────────────────────────

    def _preset_gioco_reale(self):
        """
        Imposta il preset "Gioco Reale":
          • P2 = libero (le 6 raccolte fisiche — livello dei blocchi)
          • P0 = P1 = SCD_U  (identità — non modificano l'ordine)
          • J uniformi attivi per ogni stadio  (J0=J1=J2)
        Risultato: 6³ × 2³ = 216 × 8 = 1728 combinazioni totali
        (allineato al gioco fisico e alla tavola del libro: v. gioco_reale.py)
        """
        for ff in self.filter_frames:
            ff.set_preset_gioco_reale()
        self._update_count()
        self.status_var.set(
            tr("status.real_game_preset"))

    def _preset_j_uniform(self):
        """Attiva J uniformi per tutti e tre gli stadi."""
        for ff in self.filter_frames:
            ff.set_j_uniform(True)
        self._update_count()
        self.status_var.set(tr("status.uniform_j_preset"))

    # ── Aggiornamento contatore live ──────────────────────────────────────────

    def _update_count(self):
        try:
            filters = self._get_filters()
            n = count_combinations_ex(filters)
            self.count_var.set(f"{n:,}")
        except Exception:
            self.count_var.set("?")

    # ── Filtri ────────────────────────────────────────────────────────────────

    def _get_filters(self):
        return [ff.get_filter() for ff in self.filter_frames]

    # ── Azioni ───────────────────────────────────────────────────────────────

    def _count(self):
        filters = self._get_filters()
        n = count_combinations_ex(filters)
        self.count_var.set(f"{n:,}")
        self.status_var.set(tr("status.count_summary", count=f"{n:,}"))

    def _reset(self):
        """«Reset tutto»: azzera i filtri E ogni form in ogni tab."""
        for ff in self.filter_frames:
            ff.reset()
        self.count_var.set("—")
        self.progress["value"] = 0
        self._update_count()

        # ogni tab torna allo stato iniziale; ogni reset è indipendente:
        # un errore in uno non deve bloccare gli altri
        # (nome per il log, chiave i18n del nome mostrato all'utente, reset)
        resets = [
            ("Anteprima",    "tab.preview",          self._reset_anteprima),
            ("Analisi",      "tab.analysis",         self._reset_analisi),
            ("Explorer",     "tab.explorer",         self._explorer_clear),
            ("Cicli",        "tab.cycles",           lambda: self._cycles_frame.reset()),
            ("Simulatore",   "tab.simulator",        lambda: self._simulator_frame.reset()),
            ("Mescolamento", "explorer.tab.shuffle", lambda: self._shuffle_viewer.clear_all()),
        ]
        falliti = []
        for nome, label_key, fn in resets:
            try:
                fn()
            except Exception:
                _log.exception("Reset del tab %s fallito", nome)
                falliti.append(tr(label_key))

        # anche lo stato "ultima T" viene dimenticato
        self._last_T_perm = None
        self._last_inv_perm = None
        if hasattr(self, "_last_decompositions"):
            self._last_decompositions = None
        self._prev_T_perm = None
        if hasattr(self, "_prev_export_btn"):
            self._prev_export_btn.configure(state="disabled")

        if falliti:
            self.status_var.set(
                tr("status.reset_with_problems", tabs=", ".join(falliti)))
        else:
            self.status_var.set(tr("status.reset_complete"))

    def _run_generation(self, *, gen_func, kind, unit, unit_plural, step,
                        dialog_kw, confirm_threshold=None, confirm_msg=None,
                        max_items=None):
        """
        Schema comune degli export massivi (PDF, PDF dettagliato, CSV):
        conteggio -> limite di sicurezza -> conferma -> dialog salvataggio ->
        generazione in thread con progress bar, ETA e gestione errori.

        `max_items`, se dato, e' il tetto specifico dell'export (il PDF
        dettagliato ha un limite piu' basso perche' deve tenere in RAM tutte
        le combinazioni per calcolare le trasposte).
        """
        if getattr(self, "_closing", False):
            return
        if self._export_busy:
            messagebox.showinfo(tr("export.busy.title"),
                                tr("export.busy.message"))
            return

        filters = self._get_filters()
        n = count_combinations_ex(filters)
        if n == 0:
            messagebox.showwarning(tr("analysis.no_combinations_title"),
                                   tr("analysis.no_combinations"))
            return

        # Limite di sicurezza: con i filtri di default le combinazioni sono
        # 1728³ = 5.159.780.352. Meglio dirlo subito con un messaggio utile
        # che avviare un export che non finira' mai.
        limit = max_items if max_items is not None else MAX_EXPORT_ITEMS
        if n > limit:
            # Il messaggio dell'eccezione del core resta per il log; qui si
            # mostra il testo localizzato con gli stessi numeri.
            exc = ExportTooLarge(n, limit)
            messagebox.showerror(
                tr("export.too_large.title"),
                tr("export.too_large.message", requested=f"{exc.requested:,}",
                   limit=f"{exc.limit:,}"))
            return

        if confirm_threshold is not None and n > confirm_threshold:
            if not messagebox.askyesno(tr("export.confirm.title"),
                                       tr(confirm_msg, count=f"{n:,}")):
                return

        path = filedialog.asksaveasfilename(**dialog_kw)
        if not path or getattr(self, "_closing", False):
            return

        _cfg = get_config()
        _nw = _cfg.effective_n_workers if _cfg.get("use_parallel", True) else 1

        self._export_busy = True
        self._export_stop.clear()
        self._btn_annulla.configure(state="normal")
        self.progress["maximum"] = n
        self.progress["value"]   = 0
        _par = tr("status.generation_workers", count=_nw) if _nw > 1 else ""
        self.status_var.set(tr("status.generation_started", kind=kind,
                               total=f"{n:,}", workers=_par))
        self.update_idletasks()

        def job():
            _eta = EtaEstimator()
            def cb(i):
                # Aggiornamenti GUI marshallati sul thread principale (Tk non e'
                # thread-safe): si usa self.after(0, ...) invece di toccare i
                # widget direttamente dal thread di lavoro.
                if i % step == 0 or i >= n:
                    msg = f"{kind}: {unit} {i:,}/{n:,}{_eta.text(i, n)}"
                    self._ui(lambda v=i, m=msg: (
                        self.progress.__setitem__("value", v),
                        self.status_var.set(m)))
            try:
                tot = gen_func(path, filters, n_workers=_nw, progress_cb=cb,
                               annullato=self._export_stop.is_set)
                _log.info("%s generato: %s (%s %s)", kind, path, tot, unit_plural)
                self._ui(lambda t=tot: self.status_var.set(
                    tr("status.generation_saved", kind=kind,
                       filename=os.path.basename(path), count=f"{t:,}",
                       unit=unit_plural)))
            except ExportAnnullato as exc:
                # Non e' un errore: nessun messaggio di guasto, solo la barra
                # di stato. Il file non e' stato creato (scrittura atomica).
                _log.info("%s annullato dall'utente", kind)
                self._ui(lambda e=exc: (
                    self.progress.__setitem__("value", 0),
                    self.status_var.set(
                        tr("status.generation_cancelled", kind=kind,
                           count=f"{e.fatti:,}", unit=unit_plural))))
            finally:
                # Il flag va rilasciato anche se l'export solleva: altrimenti
                # un errore bloccherebbe per sempre tutti gli export
                # successivi.
                self._ui(self._fine_export)

        def on_error(_exc):
            self._fine_export()
            self.status_var.set(tr("status.generation_failed", kind=kind))

        run_in_thread(self, job, error_title=tr("error.with_kind", kind=kind),
                      on_error=on_error)

    def _annulla_export(self):
        """Chiede l'interruzione dell'export in corso."""
        if not self._export_busy:
            return
        self._export_stop.set()
        self._btn_annulla.configure(state="disabled")
        self.status_var.set(tr("status.cancelling"))

    def _fine_export(self):
        """Ripristina lo stato dei controlli a export concluso o annullato."""
        if getattr(self, "_closing", False):
            return
        self._export_busy = False
        self._export_stop.clear()
        try:
            self._btn_annulla.configure(state="disabled")
        except tk.TclError:
            pass

    def _ui(self, fn):
        """
        Esegue `fn` sul thread Tk, ignorando l'errore se la finestra e' stata
        chiusa nel frattempo.

        Chiamare `after()` su un widget distrutto solleva TclError dentro il
        thread di lavoro: senza questa guardia, chiudere la finestra durante un
        export produceva un traceback invece di una chiusura pulita.
        """
        ui_call(self, fn)

    def _gen_pdf(self):
        self._run_generation(
            gen_func=generate_pdf_ex_parallel,
            kind="PDF", unit=tr("export.unit.page"),
            unit_plural=tr("export.unit.pages"), step=10,
            confirm_threshold=500,
            confirm_msg="export.confirm.pdf",
            dialog_kw=dict(defaultextension=".pdf",
                           filetypes=[("PDF", "*.pdf")],
                           title=tr("export.save.pdf")))

    def _gen_pdf_detail(self):
        """Export PDF dettagliato: due combinazioni per pagina con disposizioni
        del mazzo, posizioni dei marcatori, settori, periodo e matrici."""
        self._run_generation(
            gen_func=generate_detail_pdf_parallel,
            kind=tr("export.kind.pdf_detailed"),
            unit=tr("export.unit.combination"),
            unit_plural=tr("export.unit.combinations"), step=5,
            max_items=MAX_DETAIL_COMBOS,
            confirm_threshold=300,
            confirm_msg="export.confirm.pdf_detailed",
            dialog_kw=dict(defaultextension=".pdf",
                           filetypes=[("PDF", "*.pdf")],
                           initialfile="dettaglio_disposizioni.pdf",
                           title=tr("export.save.pdf_detailed")))

    def _gen_csv(self):
        self._run_generation(
            gen_func=write_csv_parallel,
            kind="CSV", unit=tr("export.unit.row"),
            unit_plural=tr("export.unit.rows"), step=100,
            confirm_threshold=100_000,
            confirm_msg="export.confirm.csv",
            dialog_kw=dict(defaultextension=".csv",
                           filetypes=[("CSV", "*.csv")],
                           title=tr("export.save.csv")))


    # ── Tab Guida ─────────────────────────────────────────────────────────────

    def _build_guide_tab(self, parent):
        """Tab Guida — documentazione completa, scrollabile, read-only."""
        frame = ttk.Frame(parent, padding=0)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        txt = tk.Text(frame, wrap="word", font=("Segoe UI", 11),
                      bg="#FAFCFF", fg="#1a1a2e",
                      padx=28, pady=18, relief="flat", borderwidth=0,
                      spacing1=2, spacing3=5)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=vsb.set)
        txt.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        txt.tag_configure("h1",  font=("Segoe UI", 16, "bold"),
                          foreground="#1F4E79", spacing1=18, spacing3=8)
        txt.tag_configure("h2",  font=("Segoe UI", 13, "bold"),
                          foreground="#2E75B6", spacing1=14, spacing3=5)
        txt.tag_configure("h3",  font=("Segoe UI", 11, "bold"),
                          foreground="#333", spacing1=8, spacing3=2)
        txt.tag_configure("body",    font=("Segoe UI", 11), foreground="#1a1a2e")
        txt.tag_configure("note",    font=("Segoe UI", 10, "italic"),
                          foreground="#555")
        txt.tag_configure("code",    font=("Consolas", 10), foreground="#1F4E79",
                          background="#EBF3FB")
        txt.tag_configure("formula", font=("Consolas", 11),
                          foreground="#7B2D00", background="#FFF8F0",
                          spacing1=3, spacing3=3, lmargin1=20, lmargin2=20)
        txt.tag_configure("bullet",  font=("Segoe UI", 11), foreground="#1a1a2e",
                          lmargin1=30, lmargin2=50)
        txt.tag_configure("bullet2", font=("Segoe UI", 11), foreground="#444",
                          lmargin1=55, lmargin2=72)
        txt.tag_configure("sep",     font=("Segoe UI", 4),
                          foreground="#AAAAAA", spacing1=6, spacing3=6)
        txt.tag_configure("hilight", font=("Segoe UI", 11, "bold"),
                          foreground="#7b4000", background="#FFF3E0")
        txt.tag_configure("warn",    font=("Segoe UI", 11, "bold"),
                          foreground="#C0392B", background="#FDECEA")
        txt.tag_configure("ok",      font=("Segoe UI", 11, "bold"),
                          foreground="#1a7a1a", background="#EAF8EA")
        txt.tag_configure("toc",     font=("Segoe UI", 11), foreground="#2E75B6",
                          lmargin1=20, lmargin2=20)
        # I7: le parti del percorso (A…M), nell'indice e nel testo
        txt.tag_configure("tocpart", font=("Segoe UI", 11, "bold"),
                          foreground="#1F4E79", spacing1=6)
        txt.tag_configure("part",    font=("Segoe UI", 14, "bold"),
                          foreground="#1F4E79", background="#EAF2FB",
                          spacing1=22, spacing3=6)

        # Mappa "numero di sezione" -> mark tkinter, popolata mentre la Guida
        # viene scritta. Serve a far funzionare davvero il link «Apri Guida»
        # dei banner, che finora portava sempre in cima al documento.
        self._guide_marks = {}
        self._guide_text = txt

        def ins(tag, text):
            if tag == "h2":
                num = text.strip().split(".", 1)[0].strip()
                if num.isdigit():
                    name = f"sec{num}"
                    txt.mark_set(name, "end-1c")
                    txt.mark_gravity(name, "left")
                    self._guide_marks[num] = name
            txt.insert("end", text, tag)

        def sep():
            ins("sep", "\n" + "─" * 90 + "\n")

        # Contenuto della Guida spostato in guide.py (vedi build_guide_content)
        build_guide_content(ins, sep)

        txt.configure(state="disabled")
        return frame
    # ── Tab Cicli ───────────────────────────────────────────────────────────
    def _build_cycles_tab(self, nb):
        self._cycles_frame = CyclesFrame(
            nb, on_mostra_nella_tavola=lambda n: self._mostra_nella_tavola(n))
        return self._cycles_frame

    # ── Tab Distribuzione ───────────────────────────────────────────────────
    def _build_distrib_tab(self, nb):
        self._distrib_frame = DistributionFrame(nb)
        return self._distrib_frame

    # ── Tab Simulatore ──────────────────────────────────────────────────────
    def _build_simulator_tab(self, nb):
        self._simulator_frame = SimulatorFrame(
            nb, on_new_T=self._on_simulator_T,
            on_mostra_nella_tavola=lambda n: self._mostra_nella_tavola(n))
        return self._simulator_frame

    def _on_simulator_T(self, perm_27):
        """Il simulatore ha calcolato una nuova sequenza di gioco."""
        self._notify_T_changed(perm_27)
        if hasattr(self, "_sessione_nota"):
            self._sessione_nota("simulatore")

    # ── Tab Tavola 216 ──────────────────────────────────────────────────────
    def _build_tavola_tab(self, nb):
        # I2d: callback tardivi (lambda), perche' le schede di destinazione
        # si costruiscono dopo e i test possono sostituire _notify_T_changed.
        self._tavola_frame = TavolaFrame(
            nb, on_usa_T=lambda perm: (self._notify_T_changed(perm),
                                       self._sessione_nota("tavola", perm)),
            on_apri_explorer=lambda espr: self._apri_nell_explorer(espr),
            on_apri_cicli=lambda perm: self._apri_nei_cicli(perm),
            scheda_disponibile=lambda k: self._scheda_disponibile(k),
            on_pratica=lambda n: self._pratica_disposizione(n))
        return self._tavola_frame

    def _pratica_disposizione(self, numero):
        """I3e (D-I3-7): la Pratica usa la riga #numero come piano fisso."""
        sim = self._simulator_frame
        sim.imposta_disposizione_fissa(numero)
        self._seleziona_scheda("simulatore")
        sim._find_sequence()

    # ── Navigazione minima (I2d, D-I2-7) ────────────────────────────────────
    def _scheda_disponibile(self, chiave):
        """True se la scheda esiste e non e' nascosta dal livello corrente."""
        widget = (getattr(self, "_schede", None) or {}).get(chiave)
        if widget is None or getattr(self, "_nb", None) is None:
            return False
        try:
            return self._nb.tab(widget, "state") != "hidden"
        except tk.TclError:
            return False

    def _mostra_nella_tavola(self, numero):
        """Seleziona la riga `numero` della Tavola e porta la Tavola in vista."""
        self._tavola_frame.vai_alla_riga(numero)
        self._seleziona_scheda("tavola")

    def _apri_nell_explorer(self, espressione):
        self._explorer_entry.delete("1.0", "end")
        self._explorer_entry.insert("1.0", espressione)
        self._switch_to_explorer()
        self._explorer_calc()

    def _apri_nei_cicli(self, perm):
        self._notify_T_changed(perm)
        self._seleziona_scheda("cicli")

    # ── Notifica cambio T ───────────────────────────────────────────────────
    def _notify_T_changed(self, perm_27):
        """Chiamata ogni volta che una nuova T viene calcolata.

        Contratto delle viste (M03): riceve la nuova T soltanto chi la
        rappresenta davvero.

        * **Cicli** espone `set_permutation` e mostra i cicli della T corrente:
          e' il destinatario naturale.
        * **Presentazione**, se aperta, espone `update_from_T`.
        * **Distribuzione** NON viene notificata. La sua scheda e' globale:
          calcola, per ogni T raggiungibile, quante decomposizioni possiede, e
          non rappresenta la T selezionata. Qui veniva invocato un
          `set_permutation` che quella vista non ha mai avuto, dentro un
          `except Exception: pass` che nascondeva l'AttributeError a ogni
          calcolo. La chiamata e' stata rimossa: non si inventa una
          funzionalita' per dare ragione a una riga sbagliata.
        """
        self._last_T_perm = list(perm_27)
        if hasattr(self, "_cycles_frame"):
            self._cycles_frame.set_permutation(perm_27)
        if self._presentation_win is not None:
            try:
                self._presentation_win.update_from_T({"perm": perm_27})
            except tk.TclError:
                # la finestra e' stata chiusa fra un calcolo e l'altro: e'
                # l'unico errore atteso, e il rimedio e' dimenticarla.
                self._presentation_win = None

    # ── Export dialog ────────────────────────────────────────────────────────
    def _open_export_dialog(self, perm=None, inv_perm=None,
                             decompositions=None, title_label="T"):
        ExportDialog(self, perm=perm, inv_perm=inv_perm,
                     decompositions=decompositions, title_label=title_label)

    # ── Analisi gruppo ────────────────────────────────────────────────────────
    def _open_conjugacy(self):
        """Apre il dialog classi di coniugio e centro di GEN3³."""
        ConjugacyDialog(self)

    def _open_cayley(self):
        """Apre il calcolatore prodotti e tavola di Cayley."""
        CayleyDialog(self)

    # ── Presentazione fullscreen ──────────────────────────────────────────────
    def _run_selftest(self):
        """Esegue la verifica di integrità (core/gioco_reale.selftest) in un thread.

        R05: il worker intercettava soltanto `AssertionError`. Qualunque altro
        guasto — una dipendenza mancante, un errore di runtime — usciva dal
        thread senza toccare la UI, che restava con «verifica in corso…» per
        sempre. Ora il lavoro termina sempre in uno stato conclusivo:

        * incoerenza matematica (`AssertionError`, quindi anche `VerificaFallita`
          introdotta in D): rapporto di incoerenza, stato «fallita»;
        * qualunque altro errore: `run_in_thread` lo registra nel log, lo mostra
          all'utente e `on_error` riporta comunque lo stato a «fallita»;
        * successo: rapporto completo, stato «completata».

        Il worker non tocca widget: pubblica solo attraverso `self._ui`.
        """
        self.status_var.set(tr("status.integrity_running"))

        def worker():
            from ..core.gioco_reale import selftest
            try:
                testo, ok = format_selftest_report(selftest()), True
            except AssertionError as e:
                testo, ok = tr("verify.inconsistency", detail=e), False

            def mostra():
                self.status_var.set(
                    tr("status.integrity_completed" if ok
                       else "status.integrity_failed"))
                (messagebox.showinfo if ok else messagebox.showerror)(
                    tr("dialog.integrity.title"),
                    (tr("status.integrity_all_passed") if ok else "") + testo,
                    parent=self)
            self._ui(mostra)

        return run_in_thread(self, worker,
                             error_title=tr("dialog.integrity.title"),
                             on_error=lambda _e: self.status_var.set(
                                 tr("status.integrity_failed")))

    def _open_presentation(self):
        """Apre (o porta in primo piano) la finestra presentazione."""
        if self._presentation_win is None or not self._presentation_win.winfo_exists():
            self._presentation_win = PresentationWindow(self)
            if self._last_T_perm is not None:
                self._presentation_win.update_from_T({"perm": self._last_T_perm})
        else:
            self._presentation_win.lift()
            self._presentation_win.focus_force()

    # ── Protocollo HTML ───────────────────────────────────────────────────────
    def _open_protocol(self):
        """Apre il dialog export protocollo per l'ultima T calcolata."""
        r = getattr(self, "_explorer_last_result", None)
        if not r or not r.get("ok") or r.get("perm") is None:
            messagebox.showinfo(
                tr("protocol.no_result.title"),
                tr("protocol.no_result.message"),
                parent=self)
            return
        import numpy as _np
        from ..core.kronecker import decomposition_context
        perm     = list(r.get("perm") or [])
        inv_perm = list(r.get("inverse_perm") or
                        (_np.argsort(perm).tolist() if perm else []))
        cf       = r.get("canonical_form")
        T_data = {
            "perm":          perm,
            "inverse_perm":  inv_perm,
            "label":         r.get("normalized_str", "T"),
            "period":        r.get("period"),
            "decompositions": decomposition_context(
                getattr(self, "_last_decompositions", None), perm, inv_perm),
            "canonical_sym": cf.symbolic() if cf is not None else None,
        }
        ProtocolDialog(self, T_data)

    # ── Impostazioni ──────────────────────────────────────────────────────────
    def _save_language_preference(self, language, parent, avviso=None):
        """Persist a language choice; the current widget tree is unchanged.

        R07: se il salvataggio non riesce, l'utente non deve leggere «riavvia
        per applicare la nuova lingua» — non c'e' nulla da applicare al
        prossimo avvio. La scelta resta valida per questa sessione (nulla e'
        stato annullato in memoria), ma il fallimento viene detto.

        H2: `avviso(testo, errore=...)` permette a chi chiama di mostrare il
        riscontro dove l'utente sta lavorando — un'etichetta dentro il
        dialogo — invece di aprire una finestra sopra un'altra. Senza
        `avviso` il comportamento e' quello di G2: una messagebox.
        """

        if language not in ("it", "en"):
            return False
        self._cfg["language"] = language
        try:
            self._cfg.save()
        except ConfigNonSalvata as exc:
            if avviso is None:
                self._segnala_config_non_salvata(exc, parent)
            else:
                avviso(per_utente(exc)[1])
            return False
        if avviso is None:
            messagebox.showinfo(tr("dialog.settings.title"),
                                tr("status.language_restart"), parent=parent)
        else:
            avviso(tr("status.language_restart"), errore=False)
        return True

    def _segnala_config_non_salvata(self, exc, parent):
        """Unico punto in cui un salvataggio fallito diventa visibile.

        G2 si ferma qui: rendere osservabile il fallimento. La revisione del
        testo e della sua collocazione nella UI appartiene al compartimento H.
        """
        messagebox.showerror(
            tr("config.save_failed.title"),
            tr("config.save_failed", path=exc.percorso, detail=exc.causa),
            parent=parent)

    def _open_settings(self):
        """Dialog impostazioni: worker paralleli e cache."""
        import multiprocessing
        dlg = tk.Toplevel(self)
        dlg.title(tr("dialog.settings.title"))
        dlg.resizable(False, False)
        dlg.grab_set()

        HelpBanner(
            dlg,
            tr("settings.help.short"),
            long=tr("settings.help.long"),
        ).pack(fill="x")

        fr = ttk.Frame(dlg, padding=(20, 14))
        fr.pack(fill="both", expand=True)

        # Worker paralleli
        ttk.Label(fr, text=tr("settings.workers"),
                  font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=4)
        n_cpu = multiprocessing.cpu_count()
        cur_w  = self._cfg.get("n_workers") or max(1, n_cpu - 1)
        w_var  = tk.IntVar(value=cur_w)
        worker_box = ttk.Spinbox(fr, from_=1, to=n_cpu, textvariable=w_var,
                                 width=5)
        worker_box.grid(row=0, column=1, padx=10, sticky="w")
        ttk.Label(fr, text=tr("settings.logical_cpus_default",
                              count=n_cpu, default=n_cpu - 1),
                  foreground="#666", font=("Segoe UI", 9)).grid(
                      row=0, column=2, sticky="w")

        # Usa parallelo
        ttk.Label(fr, text=tr("settings.parallel_search"),
                  font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=4)
        par_var = tk.BooleanVar(value=bool(self._cfg.get("use_parallel", True)))
        ttk.Checkbutton(fr, variable=par_var).grid(
            row=1, column=1, sticky="w", padx=10)

        # Cache info
        try:
            from ..core.cache import cache_size_mb, cache_entries, clear_cache
            mb  = cache_size_mb()
            ent = cache_entries()
            cache_info = f"{ent} file  ({mb:.1f} MB)"
        except Exception:
            cache_info = "—"
            clear_cache = None

        ttk.Separator(fr, orient="horizontal").grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=8)
        ttk.Label(fr, text=tr("settings.cache"),
                  font=("Segoe UI", 10)).grid(row=3, column=0, sticky="w")
        ttk.Label(fr, text=(tr("settings.cache_info", entries=ent, size=mb)
                           if clear_cache is not None else cache_info),
                  foreground="#444", font=("Segoe UI", 9)).grid(
                      row=3, column=1, columnspan=2, sticky="w", padx=10)

        def do_clear_cache():
            if clear_cache is not None:
                try:
                    clear_cache()
                    messagebox.showinfo(tr("dialog.cache.title"),
                                        tr("status.cache_cleared"), parent=dlg)
                except Exception as e:
                    messagebox.showerror(
                        *per_file(e, "", titolo=tr("error.generic")),
                        parent=dlg)

        ttk.Button(fr, text=f"🗑️  {tr('settings.clear_cache')}",
                   command=do_clear_cache).grid(
                       row=4, column=0, columnspan=2, sticky="w", pady=4)

        # Dimensione testo aiuti (scalabile, utile su monitor 4K)
        ttk.Label(fr, text=tr("settings.help_font_size"),
                  font=("Segoe UI", 10)).grid(row=5, column=0, sticky="w", pady=4)
        _scale_opts = [(tr("settings.scale.normal"), 1.0),
                       (tr("settings.scale.large"), 1.3),
                       (tr("settings.scale.very_large"), 1.6),
                       (tr("settings.scale.huge"), 2.0)]
        _scale_map = dict(_scale_opts)
        cur_scale = float(self._cfg.get("help_font_scale", 1.0))
        _cur_lbl = min(_scale_opts, key=lambda o: abs(o[1] - cur_scale))[0]
        hs_var = tk.StringVar(value=_cur_lbl)
        ttk.Combobox(fr, textvariable=hs_var,
                     values=[l for l, _ in _scale_opts],
                     state="readonly", width=20).grid(
                         row=5, column=1, columnspan=2, sticky="w", padx=10)

        # La lingua viene salvata subito; la GUI corrente resta invariata e
        # la nuova lingua viene applicata al successivo avvio.
        ttk.Label(fr, text=tr("settings.language"),
                  font=("Segoe UI", 10)).grid(
                      row=6, column=0, sticky="w", pady=4)
        language_labels = {
            "it": tr("settings.italian"),
            "en": tr("settings.english"),
        }
        language_codes = {label: code for code, label in language_labels.items()}
        language_var = tk.StringVar(
            value=language_labels.get(self._cfg.get("language", "it"),
                                      language_labels["it"]))
        language_combo = ttk.Combobox(
            fr, textvariable=language_var, values=list(language_labels.values()),
            state="readonly", width=20)
        language_combo.grid(row=6, column=1, columnspan=2,
                            sticky="w", padx=10)

        def on_language_change(_event=None):
            code = language_codes.get(language_var.get())
            if code is None or code == self._cfg.get("language", "it"):
                return
            self._save_language_preference(code, dlg, avviso=mostra_avviso)

        language_combo.bind("<<ComboboxSelected>>", on_language_change)

        ttk.Separator(fr, orient="horizontal").grid(
            row=7, column=0, columnspan=3, sticky="ew", pady=8)

        # H2: il riscontro del salvataggio resta dentro il dialogo. Una
        # messagebox sopra il dialogo sposta il fuoco, chiede un secondo
        # clic e, a ogni tentativo, si ripresenta: qui il testo compare
        # sopra i pulsanti e il fuoco torna su «Salva», che e' il controllo
        # con cui si riprova. L'etichetta e' fuori dalla griglia finche'
        # non c'e' nulla da dire.
        avviso = ttk.Label(fr, wraplength=520, justify="left")
        self._avviso_impostazioni = avviso

        btn_row = ttk.Frame(fr)
        btn_row.grid(row=9, column=0, columnspan=3, sticky="e")
        ttk.Button(btn_row, text=tr("button.cancel"),
                   command=dlg.destroy).pack(side="left", padx=4)
        salva = ttk.Button(btn_row, text=f"✔  {tr('button.save')}")
        salva.pack(side="left")
        self._salva_impostazioni = salva

        def mostra_avviso(testo, errore=True):
            avviso.configure(text=testo,
                             foreground="#b00020" if errore else "#1b5e20")
            avviso.grid(row=8, column=0, columnspan=3, sticky="w",
                        pady=(0, 6))
            salva.focus_set()

        def nascondi_avviso():
            avviso.grid_remove()

        def do_save():
            nascondi_avviso()
            self._cfg["n_workers"]    = int(w_var.get())
            self._cfg["use_parallel"] = bool(par_var.get())
            scale = _scale_map.get(hs_var.get(), 1.0)
            self._cfg["help_font_scale"] = scale
            uifont.apply_scale(scale, root=self)
            try:
                self._cfg.save()
            except ConfigNonSalvata as exc:
                # R07: chiudere il dialogo significa «fatto». Se il file non
                # e' stato scritto non e' fatto: l'errore si legge qui, il
                # dialogo resta aperto e «Salva» e' ancora premibile.
                mostra_avviso(per_utente(exc)[1])
                return
            dlg.destroy()

        salva.configure(command=do_save)
        # Il fuoco iniziale va sul primo controllo modificabile, non su
        # «Salva»: chi apre le impostazioni vuole cambiare qualcosa.
        prepara_dialogo(dlg, worker_box)

    # ── Chiusura applicazione ─────────────────────────────────────────────────
    def _on_close(self):
        """Salva config, libera memoria e chiude."""
        if getattr(self, "_closing", False):
            return
        self._closing = True
        stop = getattr(self, "_export_stop", None)
        if stop is not None and not stop.is_set():
            stop.set()
        try:
            self._cfg["window_geometry"] = self.geometry()
            self._cfg.save()
        except Exception:
            # Un salvataggio fallito non deve impedire di chiudere, e in
            # chiusura non c'e' piu' una finestra su cui mostrare un errore.
            # Anche qui nulla viene annunciato come riuscito: l'unica cosa che
            # si perde e' la geometria della finestra, e `save()` ha gia'
            # registrato la causa nel log.
            pass
        if hasattr(self, "_analisi_risultati"):
            self._analisi_risultati.clear()
        if hasattr(self, "_analisi_righe_raw"):
            self._analisi_righe_raw.clear()
        if hasattr(self, "_explorer_last_result"):
            self._explorer_last_result = None
        self.destroy()
        import sys
        sys.exit(0)




# ──────────────────────────────────────────────────────
