"""
Scheda "🚀 Inizia qui": orientamento rapido, azioni rapide e glossario.

Mixin per App: fornisce _build_onboarding_tab(). Richiede da App i metodi
_preset_gioco_reale(), _select_tab_by_text() e _open_guide().
"""
import tkinter as tk
from tkinter import ttk

from .tooltip import attach as _tip
from .help_banner import HelpBanner
from .glossary import GLOSSARY, ONBOARD_STEPS, ONBOARD_INTRO


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

        ttk.Label(body, text="🚀  Inizia qui",
                  font=("Segoe UI", 16, "bold"),
                  foreground="#1F4E79").grid(row=0, column=0, sticky="w")
        ttk.Label(body,
                  text="Una mappa rapida per orientarti, anche se non conosci "
                       "la teoria.",
                  font="GiocoHelpItalic",
                  foreground="#555").grid(row=1, column=0, sticky="w",
                                          pady=(0, 10))

        HelpBanner(
            body, ONBOARD_INTRO,
            long=("Il programma studia il «gioco delle 27 carte»: come, "
                  "mescolando le carte in colonne, si ottengono permutazioni "
                  "con proprietà matematiche interessanti. Non serve conoscere "
                  "la teoria per usarlo: segui i tre passi qui sotto e usa il "
                  "glossario per ogni termine che non ti è chiaro."),
            on_open_guide=getattr(self, "_open_guide", None),
        ).grid(row=2, column=0, sticky="ew", pady=(0, 14))

        steps = ttk.Frame(body)
        steps.grid(row=3, column=0, sticky="ew")
        for i in range(3):
            steps.columnconfigure(i, weight=1, uniform="step")
        for i, (icon, title, desc) in enumerate(ONBOARD_STEPS):
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

        qa = ttk.LabelFrame(body, text="  Azioni rapide  ", padding=10)
        qa.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        b0 = ttk.Button(qa, text="🎩  Prova il Simulatore",
                        command=lambda: self._select_tab_by_text("Simulatore"))
        b0.pack(side="left", padx=(0, 8))
        _tip(b0, "Esegui il trucco passo per passo, come col mazzo vero.")
        b1 = ttk.Button(qa, text="🎴  Carica «Gioco Reale»",
                        command=getattr(self, "_preset_gioco_reale",
                                        lambda: None))
        b1.pack(side="left", padx=8)
        _tip(b1, "Imposta i filtri sull'esempio standard di 1 728 sequenze.")
        b2 = ttk.Button(qa, text="🔍  Vai all'Anteprima",
                        command=lambda: self._select_tab_by_text("Anteprima"))
        b2.pack(side="left", padx=8)
        _tip(b2, "Mostra cosa succede alle carte per una singola combinazione.")
        b3 = ttk.Button(qa, text="📖  Apri la Guida completa",
                        command=lambda: self._open_guide())
        b3.pack(side="left", padx=8)
        _tip(b3, "La documentazione completa, con tutta la teoria passo passo.")

        gl = ttk.LabelFrame(
            body, text="  Glossario — i termini in parole semplici "
                       "(passa il mouse per i dettagli)  ", padding=(4, 6))
        gl.grid(row=5, column=0, sticky="ew", pady=(16, 4))
        gl.columnconfigure(0, weight=1)
        for r, (term, short, long) in enumerate(GLOSSARY):
            rowf = tk.Frame(gl, bg="#FAFCFF")
            rowf.grid(row=r, column=0, sticky="ew", pady=1)
            rowf.columnconfigure(1, weight=1)
            t = tk.Label(rowf, text=term, bg="#FAFCFF", fg="#1F4E79",
                         font="GiocoHelpMonoBold", width=16, anchor="w")
            t.grid(row=0, column=0, sticky="nw", padx=(6, 8), pady=3)
            d = tk.Label(rowf, text=short, bg="#FAFCFF", fg="#1a1a2e",
                         font="GiocoHelp", wraplength=540,
                         justify="left", anchor="w")
            d.grid(row=0, column=1, sticky="w", pady=3)
            _tip(t, long)
            _tip(d, long)

        return outer
