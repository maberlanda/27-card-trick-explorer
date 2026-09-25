"""
Scheda "🚀 Inizia qui": orientamento rapido, azioni rapide e glossario.

Mixin per App: fornisce _build_onboarding_tab(). Richiede da App i metodi
_preset_gioco_reale(), _seleziona_scheda() e _open_guide().
"""
import tkinter as tk
from tkinter import ttk

from .tooltip import attach as _tip
from .help_banner import HelpBanner
from .glossary import GLOSSARIO_MATEMATICO, GLOSSARIO_NARRATIVO, ONBOARD_STEPS
from .i18n import tr
from . import livelli as _livelli


class OnboardingTabMixin:

    def _build_onboarding_tab(self, parent):
        BG = "#F5F7FA"
        outer = ttk.Frame(parent)
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        body = ttk.Frame(canvas, padding=(18, 14))
        win = canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>",
                  lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(win, width=e.width))

        def _wheel(e):
            canvas.yview_scroll(int(-e.delta / 120), "units")
        canvas.bind("<Enter>",
                    lambda e: canvas.bind_all("<MouseWheel>", _wheel))
        canvas.bind("<Leave>",
                    lambda e: canvas.unbind_all("<MouseWheel>"))

        body.columnconfigure(0, weight=1)

        ttk.Label(body, text=f"🚀  {tr('onboarding.title')}",
                  font=("Segoe UI", 16, "bold"),
                  foreground="#1F4E79").grid(row=0, column=0, sticky="w")
        ttk.Label(body,
                  text=tr("onboarding.subtitle"),
                  font="GiocoHelpItalic",
                  foreground="#555").grid(row=1, column=0, sticky="w",
                                          pady=(0, 10))

        HelpBanner(
            body, tr("onboarding.intro"),
            long=tr("onboarding.help.long"),
            on_open_guide=getattr(self, "_open_guide", None),
        ).grid(row=2, column=0, sticky="ew", pady=(0, 14))

        steps = ttk.Frame(body)
        steps.grid(row=3, column=0, sticky="ew")
        for i in range(3):
            steps.columnconfigure(i, weight=1, uniform="step")
        for i, (icon, title_key, desc_key) in enumerate(ONBOARD_STEPS):
            title, desc = tr(title_key), tr(desc_key)
            card = tk.Frame(steps, bg="white", bd=0,
                            highlightthickness=1, highlightbackground="#D6E0EC")
            card.grid(row=0, column=i, sticky="nsew",
                      padx=(0 if i == 0 else 8, 0))
            tk.Label(card, text=icon, bg="white", fg="#1F4E79",
                     font=("Segoe UI", 18, "bold")).pack(anchor="w",
                                                         padx=12, pady=(10, 0))
            tk.Label(card, text=title, bg="white", fg="#1a1a2e",
                     font="GiocoHelpBold").pack(anchor="w", padx=12)
            tk.Label(card, text=desc, bg="white", fg="#555",
                     font="GiocoHelp", wraplength=210, justify="left"
                     ).pack(anchor="w", padx=12, pady=(2, 12))

        # ── DP7: i quattro livelli ────────────────────────────────────────────
        lv = ttk.LabelFrame(body, text=f"  🎓 {tr('onboarding.levels.title')}  ",
                            padding=10)
        lv.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        lv.columnconfigure(1, weight=1)
        ttk.Label(lv, text=tr("onboarding.levels.intro"), font="GiocoHelp",
                  wraplength=900, justify="left").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        self._livello_onboarding_var = tk.StringVar(
            value=_livelli.normalizza(getattr(self, "_livello", _livelli.BASE)))
        self._livelli_rb = []
        for r, livello in enumerate(_livelli.LIVELLI, start=1):
            rb = ttk.Radiobutton(
                lv, text=f"{r} · {tr(f'level.name.{livello}')}",
                value=livello, variable=self._livello_onboarding_var,
                command=lambda: self._imposta_livello(
                    self._livello_onboarding_var.get()))
            rb.grid(row=r, column=0, sticky="w", padx=(0, 12), pady=1)
            ttk.Label(lv, text=tr(f"level.desc.{livello}"), font="GiocoHelp",
                      wraplength=760, justify="left").grid(
                row=r, column=1, sticky="w", pady=1)
            self._livelli_rb.append(rb)

        qa = ttk.LabelFrame(body, text=f"  {tr('onboarding.quick_actions')}  ", padding=10)
        qa.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        b0 = ttk.Button(qa, text=f"🎩  {tr('onboarding.button.try_simulator')}",
                        command=lambda: self._seleziona_scheda("simulatore"))
        b0.pack(side="left", padx=(0, 8))
        _tip(b0, tr("tooltip.try_simulator"))
        b1 = ttk.Button(qa, text=f"📚  {tr('onboarding.button.open_table')}",
                        command=lambda: self._seleziona_scheda("tavola"))
        b1.pack(side="left", padx=8)
        _tip(b1, tr("tooltip.open_table"))
        b3 = ttk.Button(qa, text=f"📖  {tr('onboarding.button.open_guide')}",
                        command=lambda: self._open_guide())
        b3.pack(side="left", padx=8)
        _tip(b3, tr("banner.open_guide"))

        riga = 6
        for titolo, chiavi in (("onboarding.glossary.math", GLOSSARIO_MATEMATICO),
                               ("onboarding.glossary.narrative", GLOSSARIO_NARRATIVO)):
            gl = ttk.LabelFrame(
                body, text=f"  {tr('onboarding.glossary.title')} — {tr(titolo)}  ",
                padding=(4, 6))
            gl.grid(row=riga, column=0, sticky="ew", pady=(16, 4))
            riga += 1
            gl.columnconfigure(0, weight=1)
            if titolo.endswith("narrative"):
                ttk.Label(gl, text=tr("onboarding.glossary.narrative_note"),
                          font="GiocoHelpItalic", wraplength=900,
                          justify="left").grid(row=0, column=0, sticky="w",
                                               padx=6, pady=(0, 4))
            for r, chiave in enumerate(chiavi, start=1):
                term = tr(f"glossary.term.{chiave}")
                short = tr(f"glossary.short.{chiave}")
                rowf = tk.Frame(gl, bg="#FAFCFF")
                rowf.grid(row=r, column=0, sticky="ew", pady=1)
                rowf.columnconfigure(1, weight=1)
                t = tk.Label(rowf, text=term, bg="#FAFCFF", fg="#1F4E79",
                             font="GiocoHelpMonoBold", width=22, anchor="w")
                t.grid(row=0, column=0, sticky="nw", padx=(6, 8), pady=3)
                d = tk.Label(rowf, text=short, bg="#FAFCFF", fg="#1a1a2e",
                             font="GiocoHelp", wraplength=640,
                             justify="left", anchor="w")
                d.grid(row=0, column=1, sticky="w", pady=3)
                long = tr(f"glossary.long.{chiave}")
                _tip(t, long)
                _tip(d, long)

        return outer
