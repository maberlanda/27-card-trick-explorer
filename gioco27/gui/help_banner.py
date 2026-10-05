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

from .common import rendi_azionabile
from .i18n import tr
from .scorrimento import AreaScorrevole


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
        row.pack(fill="x", padx=8, pady=3)   # K: era 6, riga unica (H2 a 1280×720)

        tk.Label(row, text="ⓘ", bg=self.BG, fg=self.FG,
                 font="GiocoHelpBold").pack(side="left", padx=(0, 6))
        tk.Label(row, text=tr("banner.what_this_tab_does"), bg=self.BG, fg=self.FG,
                 font="GiocoHelpBold").pack(side="left")
        tk.Label(row, text="  " + short, bg=self.BG, fg=self.FG2,
                 font="GiocoHelp", wraplength=560, justify="left"
                 ).pack(side="left")

        if on_open_guide is not None:
            link = tk.Label(row, text=f"ⓘ {tr('banner.open_guide')}", bg=self.BG, fg=self.FG,
                            font="GiocoHelpLink", cursor="hand2")
            link.pack(side="right")
            rendi_azionabile(link, self._apri_guida,
                             sfondo=self.BG, colore_focus=self.FG)
            self._link_guida = link

        if long:
            self._toggle = tk.Label(row, text=tr("banner.show_more"),
                                    bg=self.BG, fg=self.FG,
                                    font="GiocoHelpLink",
                                    cursor="hand2")
            self._toggle.pack(side="right", padx=(0, 14))
            rendi_azionabile(self._toggle, self._toggle_long,
                             sfondo=self.BG, colore_focus=self.FG)
            self._long_area = AreaScorrevole(self)
            self._long_area.tela.configure(height=180, width=640, bg=self.BG)
            self._longlbl = tk.Label(self._long_area.contenuto, text=long, bg=self.BG, fg=self.FG2,
                                     font="GiocoHelp", wraplength=640,
                                     justify="left")
            self._longlbl.pack(fill="x", anchor="w")
            self._long_area.bind("<Configure>", lambda e: self._longlbl.configure(
                wraplength=max(180, min(900, e.width - 28))), add="+")

    def _apri_guida(self):
        owner = getattr(self._on_open, "__self__", None)
        window = self.winfo_toplevel()
        if owner is not None and isinstance(owner, tk.Tk) and window is not owner:
            owner._guide_origin_window = window
            owner._guide_restore_grab = window.grab_current() is window
            if owner._guide_restore_grab:
                window.grab_release()
            owner._guide_hidden_windows = []
            ancestor = window
            while ancestor is not owner:
                if ancestor.state() != "withdrawn":
                    owner._guide_hidden_windows.append(ancestor)
                    ancestor.withdraw()
                parent = getattr(ancestor, "master", None)
                if parent is None:
                    break
                ancestor = parent.winfo_toplevel()
            owner.lift()
        self._on_open(self._section)

    def _toggle_long(self, _event=None):
        self._open = not self._open
        if self._open:
            self._long_area.pack(fill="x", padx=12, pady=(0, 8))
            self._toggle.config(text=tr("banner.show_less"))
        else:
            self._long_area.pack_forget()
            self._toggle.config(text=tr("banner.show_more"))
