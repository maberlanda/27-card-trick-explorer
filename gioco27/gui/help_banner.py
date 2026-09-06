"""
HelpBanner: banner d'aiuto riusabile da mettere in cima a schede e dialog.

  short          testo breve sempre visibile ("Cosa fa questa scheda?").
  long           testo esteso, mostrato/nascosto con "Mostra di più".
  on_open_guide  callback opzionale (riceve `guide_section`) per aprire la Guida.

Esempio:
    HelpBanner(parent, "Calcola una singola combinazione.",
               long="Inserisci P e J per ciascuno stadio e premi Calcola...",
               on_open_guide=self._open_guide,
               guide_section="13").pack(fill="x")
"""
import tkinter as tk


class HelpBanner(tk.Frame):
    BG = "#EAF2FB"
    BORDER = "#9BC1E8"
    FG = "#1F4E79"
    FG2 = "#33475b"

    def __init__(self, parent, short, long=None,
                 on_open_guide=None, guide_section=None):
        super().__init__(parent, bg=self.BG, bd=0,
                         highlightthickness=1, highlightbackground=self.BORDER)
        self._long = long
        self._on_open = on_open_guide
        self._section = guide_section
        self._open = False

        row = tk.Frame(self, bg=self.BG)
        row.pack(fill="x", padx=8, pady=6)

        tk.Label(row, text="ⓘ", bg=self.BG, fg=self.FG,
                 font="GiocoHelpBold").pack(side="left", padx=(0, 6))
        tk.Label(row, text="Cosa fa questa scheda?", bg=self.BG, fg=self.FG,
                 font="GiocoHelpBold").pack(side="left")
        tk.Label(row, text="  " + short, bg=self.BG, fg=self.FG2,
                 font="GiocoHelp", wraplength=560, justify="left"
                 ).pack(side="left")

        if on_open_guide is not None:
            link = tk.Label(row, text="ⓘ Apri Guida", bg=self.BG, fg=self.FG,
                            font="GiocoHelpLink", cursor="hand2")
            link.pack(side="right")
            link.bind("<Button-1>",
                      lambda e: self._on_open(self._section))

        if long:
            self._toggle = tk.Label(row, text="Mostra di più ▾",
                                    bg=self.BG, fg=self.FG,
                                    font="GiocoHelpLink",
                                    cursor="hand2")
            self._toggle.pack(side="right", padx=(0, 14))
            self._toggle.bind("<Button-1>", self._toggle_long)
            self._longlbl = tk.Label(self, text=long, bg=self.BG, fg=self.FG2,
                                     font="GiocoHelp", wraplength=640,
                                     justify="left")

    def _toggle_long(self, _event=None):
        self._open = not self._open
        if self._open:
            self._longlbl.pack(fill="x", padx=34, pady=(0, 8))
            self._toggle.config(text="Mostra meno ▴")
        else:
            self._longlbl.pack_forget()
            self._toggle.config(text="Mostra di più ▾")
