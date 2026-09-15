"""
PresentationWindow — "Vista esecutore" a schermo intero.

Un gobbo (prompter) per chi esegue il trucco davanti al pubblico:
passi grandi e leggibili, uno alla volta, navigabili con frecce / spazio /
clic. Per ogni fase mostra SOLO il gesto fisico da compiere
(l'impilamento), tenendo la matematica in una riga piccola in basso.

Sorgente dei passi:
  • se l'ultima T calcolata (Explorer o Simulatore) è una disposizione
    semplice del gioco, i passi sono i tre impilamenti + il finale con
    le posizioni degli Assi;
  • altrimenti mostra un riepilogo della T con l'avviso che non
    corrisponde a una sequenza fisica di sole raccolte.

Tasti:  →/spazio avanti,  ← indietro,  F11 fullscreen,  Esc esci.
"""
import tkinter as tk

from ..core import gioco_reale as gr
from .i18n import tr

_BG     = "#0d1117"
_FG     = "#e8eaf6"
_ACCENT = "#ffd54f"
_OK     = "#7bd88f"
_DIM    = "#8a91a0"
_STAGE_COLORS = ["#6fb3ff", "#7bd88f", "#ffb86c"]


class PresentationWindow(tk.Toplevel):
    """Vista esecutore a schermo intero."""

    def __init__(self, parent):
        super().__init__(parent)
        self._app = parent
        self.configure(background=_BG)
        self.title(tr("presentation.window_title"))
        self.attributes("-fullscreen", True)
        self._fullscreen = True
        self._steps = []
        self._idx = 0

        self.bind("<Escape>",    self._exit_full)
        self.bind("<F11>",       self._toggle_full)
        self.bind("<Right>",     lambda e: self._advance(+1))
        self.bind("<space>",     lambda e: self._advance(+1))
        self.bind("<Left>",      lambda e: self._advance(-1))
        self.bind("<Button-1>",  lambda e: self._advance(+1))
        self._build_ui()
        self._show_idle()
        self.focus_set()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        top = tk.Frame(self, background=_BG)
        top.pack(fill="x", padx=24, pady=(16, 0))
        self._title_lbl = tk.Label(top, text=tr("presentation.title"),
                                   font=("Segoe UI", 20, "bold"),
                                   background=_BG, foreground=_ACCENT)
        self._title_lbl.pack(side="left")
        tk.Label(top,
                 text=tr("presentation.navigation_hint"),
                 font=("Segoe UI", 10), background=_BG,
                 foreground=_DIM).pack(side="right")

        mid = tk.Frame(self, background=_BG)
        mid.pack(fill="both", expand=True, padx=48, pady=8)

        self._phase_lbl = tk.Label(mid, text="", font=("Segoe UI", 26, "bold"),
                                   background=_BG, foreground=_DIM)
        self._phase_lbl.pack(pady=(30, 6))

        self._main_lbl = tk.Label(mid, text="", font=("Segoe UI", 44, "bold"),
                                  background=_BG, foreground=_FG,
                                  wraplength=1100, justify="center")
        self._main_lbl.pack(pady=18, expand=True)

        self._sub_lbl = tk.Label(mid, text="", font=("Segoe UI", 20),
                                 background=_BG, foreground=_OK,
                                 wraplength=1100, justify="center")
        self._sub_lbl.pack(pady=(0, 30))

        bottom = tk.Frame(self, background=_BG)
        bottom.pack(fill="x", padx=24, pady=(0, 14))
        self._math_lbl = tk.Label(bottom, text="", font=("Consolas", 11),
                                  background=_BG, foreground=_DIM)
        self._math_lbl.pack(side="left")
        self._prog_lbl = tk.Label(bottom, text="", font=("Segoe UI", 12, "bold"),
                                  background=_BG, foreground=_DIM)
        self._prog_lbl.pack(side="right", padx=(0, 16))
        tk.Button(bottom, text=tr("button.close"), command=self.destroy,
                  background="#21262d", foreground=_FG,
                  activebackground="#30363d", relief="flat",
                  font=("Segoe UI", 10)).pack(side="right")

    # ── API pubblica ──────────────────────────────────────────────────────────

    def update_from_T(self, T_data: dict):
        """Chiamata da App._notify_T_changed con {'perm': list[int], ...}."""
        perm = T_data.get("perm")
        self._steps = self._costruisci_passi(perm) if perm else []
        self._idx = 0
        self._render()

    # ── Costruzione dei passi ─────────────────────────────────────────────────

    @staticmethod
    def _costruisci_passi(T):
        T = list(T)
        passi = [dict(fase=tr("presentation.phase.ready"),
                      testo=tr("presentation.ready.deck"),
                      sotto=tr("presentation.ready.spectator"),
                      math="")]
        # è una disposizione semplice del gioco?
        mesc = None
        try:
            cand, num = gr.tabellone_da_assi(T[0], T[13], T[26])
            if gr.T_da_tabellone(cand) == T:
                mesc = cand
        except (ValueError, IndexError):
            pass
        if mesc is None:
            passi.append(dict(
                fase=tr("presentation.phase.analysis"),
                testo=tr("presentation.analysis.unsupported"),
                sotto=tr("presentation.analysis.hint"),
                math="T = [" + " ".join(f"{x}" for x in T) + "]"))
            return passi
        num = gr.numero_tavola(mesc)
        for i, m in enumerate(mesc, start=1):
            imp = gr.IMPILAMENTO_DI[m]
            nomi = {"S": tr("presentation.direction.left"),
                    "C": tr("presentation.direction.center"),
                    "D": tr("presentation.direction.right")}
            gesto = "  →  ".join(nomi[ch] for ch in imp)
            avviso = ("" if m == imp else
                      tr("presentation.shuffle_inverse_note", shuffle=m))
            passi.append(dict(
                fase=tr("presentation.phase.progress", current=i, total=3),
                testo=tr("presentation.phase.action", stacking=gesto),
                sotto=tr("presentation.phase.packet_order", note=avviso),
                math=tr("presentation.phase.math", shuffle=m, stacking=imp),
                colore=_STAGE_COLORS[i - 1]))
        passi.append(dict(
            fase=tr("presentation.phase.final"),
            testo=tr("presentation.final.ready"),
            sotto=tr("presentation.final.aces", spades=T[0], clubs=T[13],
                     hearts=T[26]),
            math=tr("presentation.final.math", number=num,
                    shuffles=" ".join(mesc), period=gr.periodo(T))))
        return passi

    # ── Rendering / navigazione ───────────────────────────────────────────────

    def _render(self):
        if not self._steps:
            self._show_idle()
            return
        p = self._steps[self._idx]
        self._phase_lbl.configure(text=p["fase"],
                                  foreground=p.get("colore", _DIM))
        self._main_lbl.configure(text=p["testo"])
        self._sub_lbl.configure(text=p["sotto"])
        self._math_lbl.configure(text=p["math"])
        self._prog_lbl.configure(
            text=f"{self._idx + 1} / {len(self._steps)}")

    def _advance(self, delta):
        if not self._steps:
            return
        self._idx = max(0, min(len(self._steps) - 1, self._idx + delta))
        self._render()

    def _show_idle(self):
        self._phase_lbl.configure(text=tr("presentation.phase.waiting"),
                                  foreground=_DIM)
        self._main_lbl.configure(text=tr("presentation.title"))
        self._sub_lbl.configure(
            text=tr("presentation.waiting.hint"))
        self._math_lbl.configure(text="")
        self._prog_lbl.configure(text="")

    # ── Fullscreen ────────────────────────────────────────────────────────────

    def _toggle_full(self, _event=None):
        self._fullscreen = not self._fullscreen
        self.attributes("-fullscreen", self._fullscreen)

    def _exit_full(self, _event=None):
        self._fullscreen = False
        self.attributes("-fullscreen", False)
