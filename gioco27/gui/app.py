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

from ..core.permutations import write_csv_parallel
from ..core.combinations import count_combinations_ex, generate_pdf_ex_parallel
from ..core.detail_pdf import MAX_DETAIL_COMBOS, generate_detail_pdf_parallel
from ..core.config import get_config
from ..core.parallel import (MAX_EXPORT_ITEMS, ExportAnnullato,
                             ExportTooLarge)
from ..core.log import get_logger
from .common import EtaEstimator, run_in_thread, ui_call
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
from .guide import build_guide_content
from .preview_tab import PreviewTabMixin
from .analysis_tab import AnalysisTabMixin
from .explorer_tab import ExplorerTabMixin
from .onboarding_tab import OnboardingTabMixin
from . import tooltip as _tooltip
from .i18n import set_language, tr
from .help_banner import HelpBanner
from .glossary import TAB_HELP
from . import uifont

_log = get_logger(__name__)


def _window_title(version):
    """Return the localized title for the main application window."""

    return tr("app.title", version=version)


def _shell_tab_text(key, icon="", **values):
    """Return a localized main-notebook label while preserving its icon."""

    icon_prefix = f"{icon}  " if icon else ""
    return f"  {icon_prefix}{tr(key, **values)}  "


class App(PreviewTabMixin, AnalysisTabMixin, ExplorerTabMixin,
          OnboardingTabMixin, tk.Tk):

    # ── Colori semantici ──────────────────────────────────────────────────────
    C_BG        = "#F5F7FA"
    C_ACTION_BG = "#E8EDF5"
    C_PRESET_BG = "#FFF8F0"

    def __init__(self):
        super().__init__()
        from .. import __version__ as _APP_VER
        self.configure(bg=self.C_BG)
        self.resizable(True, True)
        self.minsize(1200, 750)

        # ── Config persistente ─────────────────────────────────────────────
        self._cfg = get_config()
        # Seleziona la lingua prima di costruire i widget.  La conversione
        # delle stringhe esistenti a tr() avverrà in blocchi successivi.
        set_language(self._cfg.get("language", "it"))
        self.title(_window_title(_APP_VER))
        self._livello = self._cfg.get("livello", "principiante")
        # Migrazione una-tantum: alla prima apertura della nuova UI guidata
        # si parte sempre in modalità Principiante (anche su config esistenti).
        if not self._cfg.get("ui_intro_done", False):
            self._livello = "principiante"
            self._cfg["livello"] = "principiante"
            self._cfg["ui_intro_done"] = True
            try:
                self._cfg.save()
            except Exception:
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
        self._build_ui()
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

        inner = ttk.Frame(action_bar, padding=(10, 8))
        inner.pack(fill="x")

        _b = ttk.Button(inner, text="🔢  Conta",
                   style="Action.TButton",
                   command=self._count)
        _b.configure(text=f"🔢  {tr('button.count')}")
        _b.pack(side="left", padx=4)
        _tooltip.attach(_b, tr("tooltip.count"))
        gen_mb = tk.Menubutton(inner, text="⬇  Genera…", relief="raised")
        gen_mb.configure(text=f"⬇  {tr('button.generate')}")
        gen_menu = tk.Menu(gen_mb, tearoff=0)
        gen_menu.add_command(label="📄  PDF",    command=self._gen_pdf)
        gen_menu.add_command(label=f"📄  {tr('menu.pdf_detailed')}", command=self._gen_pdf_detail)
        gen_menu.add_command(label="📊  CSV (;)", command=self._gen_csv)
        gen_mb["menu"] = gen_menu
        gen_mb.pack(side="left", padx=4)
        _tooltip.attach(gen_mb, tr("tooltip.generate"))
        _b = ttk.Button(inner, text="↺  Reset tutto",
                   style="Action.TButton",
                   command=self._reset)
        _b.configure(text=f"↺  {tr('button.reset_all')}")
        _b.pack(side="left", padx=4)
        _tooltip.attach(_b, tr("tooltip.reset_all"))

        ttk.Separator(inner, orient="vertical").pack(
            side="left", fill="y", padx=10)
        self._beginner_var = tk.BooleanVar(
            value=(self._livello == "principiante"))
        self._beginner_chk = ttk.Checkbutton(
            inner, text="🎓  Modalità principiante",
            variable=self._beginner_var, command=self._toggle_livello)
        self._beginner_chk.configure(text=f"🎓  {tr('button.beginner_mode')}")
        self._beginner_chk.pack(side="left", padx=4)
        _tooltip.attach(self._beginner_chk,
            "In modalità principiante restano visibili solo le schede "
            "essenziali. Disattivala per sbloccare Explorer, Cicli e "
            "Distribuzione.")

        ttk.Separator(inner, orient="vertical").pack(
            side="left", fill="y", padx=10)

        # Contatore live (aggiornato al cambio di qualsiasi filtro)
        count_frame = ttk.Frame(inner, style="Action.TFrame")
        count_frame.pack(side="left", padx=4)
        ttk.Label(count_frame, text=tr("label.combinations"),
                  style="Status.TLabel").pack(side="left")
        self.count_var = tk.StringVar(value="—")
        ttk.Label(count_frame, textvariable=self.count_var,
                  style="Count.TLabel").pack(side="left", padx=(6, 0))

        self.status_var = tk.StringVar(value="")
        ttk.Label(inner, textvariable=self.status_var,
                  style="Status.TLabel",
                  wraplength=380).pack(side="left", padx=14)

        ttk.Separator(inner, orient="vertical").pack(
            side="right", fill="y", padx=10)
        _b = ttk.Button(inner, text="⏻  Esci",
                   style="Quit.TButton",
                   command=self._on_close)
        _b.configure(text=f"⏻  {tr('button.exit')}")
        _b.pack(side="right", padx=(0, 4))
        _tooltip.attach(_b, tr("tooltip.exit"))

        # ── Strumenti avanzati (destra) ───────────────────────────────────────
        _b = ttk.Button(inner, text="⚙️  Impostazioni",
                   command=self._open_settings)
        _b.configure(text=f"⚙️  {tr('button.settings')}")
        _b.pack(side="right", padx=2)
        _tooltip.attach(_b, tr("tooltip.settings"))
        _b = ttk.Button(inner, text="✔  Verifica",
                   command=self._run_selftest)
        _b.configure(text=f"✔  {tr('button.verify')}")
        _b.pack(side="right", padx=2)
        _tooltip.attach(_b, "Verifica di integrità: simulazione fisica vs modello "
                        "matriciale (1728 combinazioni), ancore del libro, "
                        "statistiche del capitolo 100.")
        _b = ttk.Button(inner, text="🖥️  Presentazione",
                   command=self._open_presentation)
        _b.configure(text=f"🖥️  {tr('button.presentation')}")
        _b.pack(side="right", padx=2)
        _tooltip.attach(_b, tr("tooltip.presentation"))
        _b = ttk.Button(inner, text="📋  Protocollo",
                   command=self._open_protocol)
        _b.configure(text=f"📋  {tr('button.protocol')}")
        _b.pack(side="right", padx=2)
        _tooltip.attach(_b, "Genera un protocollo passo-passo dell'ultima T calcolata.")
        ttk.Separator(inner, orient="vertical").pack(
            side="right", fill="y", padx=6)
        _b = ttk.Button(inner, text="🔮  Cayley",
                   command=self._open_cayley)
        _b.pack(side="right", padx=2)
        _tooltip.attach(_b, "Tavola di Cayley: prodotti A∘B tra le mosse del gruppo.")
        _b = ttk.Button(inner, text="🔬  Coniugio",
                   command=self._open_conjugacy)
        _b.configure(text=f"🔬  {tr('button.conjugacy')}")
        _b.pack(side="right", padx=2)
        _tooltip.attach(_b, "Classi di coniugio e centro del gruppo G = GEN3³.")
        ttk.Separator(inner, orient="vertical").pack(
            side="right", fill="y", padx=6)

        # ── Barra preset ──────────────────────────────────────────────────────
        preset_bar = tk.Frame(self, bg=self.C_PRESET_BG,
                              bd=0, highlightthickness=0,
                              highlightbackground="#E65100")
        preset_bar.pack(fill="x")

        pinner = ttk.Frame(preset_bar, padding=(10, 6))
        pinner.pack(fill="x")

        ttk.Label(pinner, text=tr("label.quick_presets"),
                  font=("Segoe UI", 10, "bold"),
                  foreground="#7b4000",
                  background=self.C_PRESET_BG).pack(side="left", padx=(0, 8))

        _b = ttk.Button(pinner,
                   text="🎴  Gioco Reale  (1 728 combinazioni)",
                   style="GiocoReale.TButton",
                   command=self._preset_gioco_reale)
        _b.configure(text=f"🎴  {tr('button.real_game')}")
        _b.pack(side="left", padx=4)
        _tooltip.attach(_b, tr("tooltip.real_game"))

        _b = ttk.Button(pinner,
                   text="⚡  J Uniformi per tutti gli stadi",
                   style="Preset.TButton",
                   command=self._preset_j_uniform)
        _b.configure(text=f"⚡  {tr('button.uniform_j')}")
        _b.pack(side="left", padx=4)
        _tooltip.attach(_b, tr("tooltip.uniform_j"))

        _b = ttk.Button(pinner,
                   text="↺  Reset filtri",
                   style="Preset.TButton",
                   command=self._reset)
        _b.configure(text=f"↺  {tr('button.quick_reset')}")
        _b.pack(side="left", padx=4)
        _tooltip.attach(_b, tr("tooltip.quick_reset"))

        # ── Progress bar + Annulla ────────────────────────────────────────────
        prog_row = ttk.Frame(self)
        prog_row.pack(fill="x", padx=12, pady=(4, 0))
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

        # Scheda introduttiva, in testa a tutto
        nb.add(self._build_onboarding_tab(nb),
               text=_shell_tab_text("tab.start", "🚀"))

        # Stadi (ciascuno con il suo banner d'aiuto)
        self.filter_frames = []
        self._stadi_wraps = []
        for i in range(3):
            wrap = ttk.Frame(nb)
            self._mk_banner(wrap, *TAB_HELP["stadio"], section="12").pack(fill="x")
            ff = FilterFrame(wrap, stage_num=i, on_change=self._update_count)
            ff.pack(fill="both", expand=True)
            self.filter_frames.append(ff)
            self._stadi_wraps.append(wrap)
            nb.add(wrap, text=_shell_tab_text("tab.stage", number=i))

        # Percorso lineare del principiante: gioco → tavola → esplorazione
        nb.add(self._wrap_tab(self._build_simulator_tab, "simulatore", "19"),
               text=_shell_tab_text("tab.simulator", "🎩"))
        nb.add(self._wrap_tab(self._build_tavola_tab, "tavola", "11"),
               text=_shell_tab_text("tab.table", "📚"))
        nb.add(self._wrap_tab(self._build_anteprima_tab, "anteprima", "14"),
               text=_shell_tab_text("tab.preview", "🔍"))
        nb.add(self._wrap_tab(self._build_analisi_tab, "analisi", "15"),
               text=_shell_tab_text("tab.analysis", "📊"))
        self._tab_explorer = self._wrap_tab(self._build_explorer_tab,
                                            "explorer", "16")
        nb.add(self._tab_explorer,
               text=_shell_tab_text("tab.explorer", "🔬"))
        nb.add(self._build_guide_tab(nb),
               text=_shell_tab_text("tab.guide", "📖"))
        self._tab_cycles = self._wrap_tab(self._build_cycles_tab, "cicli", "20")
        nb.add(self._tab_cycles,
               text=_shell_tab_text("tab.cycles", "🔄"))
        self._tab_distrib = self._wrap_tab(self._build_distrib_tab,
                                           "distribuzione", "21")
        nb.add(self._tab_distrib,
               text=_shell_tab_text("tab.distribution", "📊"))

        # Schede avanzate: nascoste in modalità principiante
        self._advanced_tabs = [self._tab_explorer, self._tab_cycles,
                               self._tab_distrib]
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
            _tooltip.attach(
                chip, f"{name}: una delle 6 mosse base su 3 elementi. "
                      "Questo colore evidenzia il nome nelle formule dell'Explorer.")
        tk.Label(bar,
                 text=tr("label.legend_note"),
                 bg=self.C_ACTION_BG, fg="#8a96a3",
                 font=("Segoe UI", 8, "italic")).pack(side="left", padx=10)
        return bar

    # ── Modalità Principiante / Esperto e navigazione ─────────────────────────

    def _mk_banner(self, parent, short, long=None, section=None):
        return HelpBanner(parent, short, long,
                          on_open_guide=self._open_guide, guide_section=section)

    def _wrap_tab(self, build_fn, key, section=None):
        """Crea un contenitore con banner d'aiuto + la scheda costruita da build_fn."""
        wrap = ttk.Frame(self._nb)
        short, long = TAB_HELP[key]
        self._mk_banner(wrap, short, long, section=section).pack(fill="x")
        inner = build_fn(wrap)
        inner.pack(fill="both", expand=True)
        return wrap

    def _toggle_livello(self):
        self._livello = ("principiante" if self._beginner_var.get()
                         else "esperto")
        self._cfg["livello"] = self._livello
        self._apply_livello()

    def _apply_livello(self):
        """Mostra/nasconde le schede avanzate secondo la modalità corrente."""
        nb = getattr(self, "_nb", None)
        if nb is None:
            return
        beginner = (self._livello == "principiante")
        hidden = list(getattr(self, "_advanced_tabs", [])) \
            + list(getattr(self, "_stadi_wraps", []))
        for tab in hidden:
            try:
                nb.tab(tab, state=("hidden" if beginner else "normal"))
            except tk.TclError:
                pass
        if beginner:
            try:
                sel = nb.select()
                hidden_ids = {str(t) for t in hidden}
                if sel in hidden_ids:
                    nb.select(0)
            except tk.TclError:
                pass
        if hasattr(self, "_beginner_var"):
            self._beginner_var.set(beginner)

    def _select_tab_by_text(self, substr):
        """Seleziona la prima scheda il cui titolo contiene `substr`."""
        nb = getattr(self, "_nb", None)
        if nb is None:
            return
        # L'onboarding usa ancora i nomi italiani come alias interni; il
        # titolo visualizzato della scheda può invece essere inglese.
        aliases = {
            "Simulatore": "tab.simulator",
            "Anteprima": "tab.preview",
            "Guida": "tab.guide",
        }
        needle = tr(aliases[substr]) if substr in aliases else substr
        for tab in nb.tabs():
            if needle.lower() in nb.tab(tab, "text").lower():
                try:
                    nb.select(tab)
                except tk.TclError:
                    pass
                return

    def _open_guide(self, section=None):
        """
        Porta in primo piano la scheda Guida e, se indicata, scorre fino alla
        sezione richiesta.

        `section` e' il numero della sezione (stringa, es. "13") passato dal
        banner d'aiuto della scheda. Prima veniva accettato e ignorato: ogni
        link «Apri Guida» apriva la Guida in cima, qualunque fosse la scheda
        di partenza.
        """
        self._select_tab_by_text("Guida")
        if not section:
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
        resets = [
            ("Anteprima",      self._reset_anteprima),
            ("Analisi",        self._reset_analisi),
            ("Explorer",       self._explorer_clear),
            ("Cicli",          lambda: self._cycles_frame.reset()),
            ("Simulatore",     lambda: self._simulator_frame.reset()),
            ("Mescolamento",   lambda: self._shuffle_viewer.clear_all()),
        ]
        falliti = []
        for nome, fn in resets:
            try:
                fn()
            except Exception:
                _log.exception("Reset del tab %s fallito", nome)
                falliti.append(nome)

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
            messagebox.showinfo(
                "Export in corso",
                "C'e' gia' un export in corso.\n"
                "Attendi che finisca prima di avviarne un altro.")
            return

        filters = self._get_filters()
        n = count_combinations_ex(filters)
        if n == 0:
            messagebox.showwarning("Nessuna combinazione",
                                   "I filtri attuali non producono combinazioni.")
            return

        # Limite di sicurezza: con i filtri di default le combinazioni sono
        # 1728³ = 5.159.780.352. Meglio dirlo subito con un messaggio utile
        # che avviare un export che non finira' mai.
        limit = max_items if max_items is not None else MAX_EXPORT_ITEMS
        if n > limit:
            messagebox.showerror("Export troppo grande", str(ExportTooLarge(n, limit)))
            return

        if confirm_threshold is not None and n > confirm_threshold:
            if not messagebox.askyesno("Conferma", confirm_msg.format(n=n)):
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
        _par = f", {_nw} processi" if _nw > 1 else ""
        self.status_var.set(f"Generazione {kind} in corso... (0/{n:,}{_par})")
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
                    f"✓ {kind} salvato: {os.path.basename(path)}  "
                    f"({t:,} {unit_plural})"))
            except ExportAnnullato as exc:
                # Non e' un errore: nessun messaggio di guasto, solo la barra
                # di stato. Il file non e' stato creato (scrittura atomica).
                _log.info("%s annullato dall'utente", kind)
                self._ui(lambda e=exc: (
                    self.progress.__setitem__("value", 0),
                    self.status_var.set(
                        f"✕ {kind} annullato — nessun file creato "
                        f"({e.fatti:,} {unit_plural} calcolate)")))
            finally:
                # Il flag va rilasciato anche se l'export solleva: altrimenti
                # un errore bloccherebbe per sempre tutti gli export
                # successivi.
                self._ui(self._fine_export)

        def on_error(_exc):
            self._fine_export()
            self.status_var.set(f"✗ {kind} non completato.")

        run_in_thread(self, job, error_title=f"Errore {kind}", on_error=on_error)

    def _annulla_export(self):
        """Chiede l'interruzione dell'export in corso."""
        if not self._export_busy:
            return
        self._export_stop.set()
        self._btn_annulla.configure(state="disabled")
        self.status_var.set("Annullamento in corso…")

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
            kind="PDF", unit="pagina", unit_plural="pagine", step=10,
            confirm_threshold=500,
            confirm_msg=("Verranno generate {n:,} pagine PDF.\n"
                         "Potrebbe richiedere molto tempo.\n\nProcedere?"),
            dialog_kw=dict(defaultextension=".pdf",
                           filetypes=[("PDF", "*.pdf")],
                           title="Salva PDF"))

    def _gen_pdf_detail(self):
        """Export PDF dettagliato: due combinazioni per pagina con disposizioni
        del mazzo, posizioni dei marcatori, settori, periodo e matrici."""
        self._run_generation(
            gen_func=generate_detail_pdf_parallel,
            kind="PDF dettagliato", unit="combinazione",
            unit_plural="combinazioni", step=5,
            max_items=MAX_DETAIL_COMBOS,
            confirm_threshold=300,
            confirm_msg=("Verranno esportate {n:,} combinazioni dettagliate "
                         "(2 per pagina).\nOgni pagina e' ricca (matrici + "
                         "carte): puo' richiedere tempo.\n\nProcedere?"),
            dialog_kw=dict(defaultextension=".pdf",
                           filetypes=[("PDF", "*.pdf")],
                           initialfile="dettaglio_disposizioni.pdf",
                           title="Salva PDF dettagliato"))

    def _gen_csv(self):
        self._run_generation(
            gen_func=write_csv_parallel,
            kind="CSV", unit="riga", unit_plural="righe", step=100,
            confirm_threshold=100_000,
            confirm_msg=("Verranno scritte {n:,} righe CSV "
                         "(circa {n:,} x 400 byte).\n"
                         "Potrebbe richiedere molto tempo e molto spazio su "
                         "disco.\n\nProcedere?"),
            dialog_kw=dict(defaultextension=".csv",
                           filetypes=[("CSV", "*.csv")],
                           title="Salva CSV"))


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
        self._cycles_frame = CyclesFrame(nb)
        return self._cycles_frame

    # ── Tab Distribuzione ───────────────────────────────────────────────────
    def _build_distrib_tab(self, nb):
        self._distrib_frame = DistributionFrame(nb)
        return self._distrib_frame

    # ── Tab Simulatore ──────────────────────────────────────────────────────
    def _build_simulator_tab(self, nb):
        self._simulator_frame = SimulatorFrame(nb, on_new_T=self._on_simulator_T)
        return self._simulator_frame

    def _on_simulator_T(self, perm_27):
        """Il simulatore ha calcolato una nuova sequenza di gioco."""
        self._notify_T_changed(perm_27)

    # ── Tab Tavola 216 ──────────────────────────────────────────────────────
    def _build_tavola_tab(self, nb):
        self._tavola_frame = TavolaFrame(nb)
        return self._tavola_frame

    # ── Notifica cambio T ───────────────────────────────────────────────────
    def _notify_T_changed(self, perm_27):
        """Chiamata ogni volta che una nuova T viene calcolata."""
        self._last_T_perm = list(perm_27)
        if hasattr(self, "_cycles_frame"):
            self._cycles_frame.set_permutation(perm_27)
        if hasattr(self, "_distrib_frame"):
            try:
                self._distrib_frame.set_permutation(perm_27)
            except Exception:
                pass
        if self._presentation_win is not None:
            try:
                self._presentation_win.update_from_T({"perm": perm_27})
            except Exception:
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
        """Esegue la verifica di integrità (core/gioco_reale.selftest) in un thread."""
        self.status_var.set(tr("status.integrity_running"))

        def worker():
            try:
                from ..core.gioco_reale import selftest
                rapporto = selftest()
                testo = "\n".join(f"{k:26s} {v}" for k, v in rapporto.items())
                ok = True
            except AssertionError as e:
                testo, ok = f"INCOERENZA RILEVATA:\n{e}", False
            def mostra():
                self.status_var.set(
                    tr("status.integrity_completed" if ok
                       else "status.integrity_failed"))
                (messagebox.showinfo if ok else messagebox.showerror)(
                    tr("dialog.integrity.title"),
                    (tr("status.integrity_all_passed") if ok else "") + testo,
                    parent=self)
            self._ui(mostra)

        import threading
        threading.Thread(target=worker, daemon=True).start()

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
                "Nessuna T calcolata",
                "Calcola prima una permutazione T nell'Explorer,\n"
                "poi usa il pulsante Protocollo.",
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
    def _save_language_preference(self, language, parent):
        """Persist a language choice; the current widget tree is unchanged."""

        if language not in ("it", "en"):
            return False
        self._cfg["language"] = language
        self._cfg.save()
        messagebox.showinfo(tr("dialog.settings.title"),
                            tr("status.language_restart"), parent=parent)
        return True

    def _open_settings(self):
        """Dialog impostazioni: worker paralleli e cache."""
        import multiprocessing
        dlg = tk.Toplevel(self)
        dlg.title(tr("dialog.settings.title"))
        dlg.resizable(False, False)
        dlg.grab_set()

        HelpBanner(
            dlg,
            "Numero di processi paralleli, ricerca parallela e gestione della cache.",
            long=("Più worker accelerano le ricerche di decomposizioni ma usano "
                  "più CPU. La cache conserva i risultati già calcolati per "
                  "riaprirli all'istante."),
        ).pack(fill="x")

        fr = ttk.Frame(dlg, padding=(20, 14))
        fr.pack(fill="both", expand=True)

        # Worker paralleli
        ttk.Label(fr, text=tr("settings.workers"),
                  font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=4)
        n_cpu = multiprocessing.cpu_count()
        cur_w  = self._cfg.get("n_workers") or max(1, n_cpu - 1)
        w_var  = tk.IntVar(value=cur_w)
        ttk.Spinbox(fr, from_=1, to=n_cpu, textvariable=w_var,
                    width=5).grid(row=0, column=1, padx=10, sticky="w")
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
                    messagebox.showerror("Errore", str(e), parent=dlg)

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
            self._save_language_preference(code, dlg)

        language_combo.bind("<<ComboboxSelected>>", on_language_change)

        ttk.Separator(fr, orient="horizontal").grid(
            row=7, column=0, columnspan=3, sticky="ew", pady=8)

        def do_save():
            self._cfg["n_workers"]    = int(w_var.get())
            self._cfg["use_parallel"] = bool(par_var.get())
            scale = _scale_map.get(hs_var.get(), 1.0)
            self._cfg["help_font_scale"] = scale
            uifont.apply_scale(scale, root=self)
            self._cfg.save()
            dlg.destroy()

        btn_row = ttk.Frame(fr)
        btn_row.grid(row=8, column=0, columnspan=3, sticky="e")
        ttk.Button(btn_row, text=tr("button.cancel"),
                   command=dlg.destroy).pack(side="left", padx=4)
        ttk.Button(btn_row, text=f"✔  {tr('button.save')}",
                   command=do_save).pack(side="left")

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
