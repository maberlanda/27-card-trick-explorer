"""Componente Tk condiviso per grafi orientati di posizioni e fibre."""

import tkinter as tk
from math import hypot, isfinite
from tkinter import font as tkfont, ttk

from ..services.grafi import Arco, GrafoOrientato
from .i18n import tr


_SFONDO = "#ffffff"
_TESTO = "#172b40"
_TRATTO = "#425b73"
_SELEZIONE = "#005a9c"
_RIEMPIMENTO = "#eaf4ff"
_RAGGIO = 20
_MARGINE = 40


def _tracciato_arco(arco, coordinate, reciproco, r=_RAGGIO):
    """Punti per una freccia con estremi sul bordo dei vertici."""
    x, y = coordinate[arco.origine]
    u, v = coordinate[arco.destinazione]
    if arco.origine == arco.destinazione:
        return (x - .6*r, y - .8*r, x - r - 4, y - r - 14,
                x + r + 4, y - r - 14, x + .6*r, y - .8*r)
    dx, dy = u - x, v - y
    lunghezza = hypot(dx, dy)
    dx, dy = dx / lunghezza, dy / lunghezza
    scarto = 10 if reciproco else 0
    bordo = (r * r - scarto * scarto) ** 0.5
    return (x + bordo * dx - scarto * dy, y + bordo * dy + scarto * dx,
            u - bordo * dx - scarto * dy, v - bordo * dy + scarto * dx)


def testo_grafo(grafo):
    """Equivalente testuale localizzato, ricavato dagli stessi dati del disegno."""
    if not grafo.vertici:
        return tr("graph.empty")
    etichette = {vertice.id: vertice.etichetta for vertice in grafo.vertici}
    righe = [tr("graph.vertices")]
    for vertice in grafo.vertici:
        righe.append(vertice.etichetta)
        if vertice.dettaglio:
            righe.append(vertice.dettaglio)
    if grafo.partizione:
        righe.extend(("", tr("graph.parts")))
        for numero, parte in enumerate(grafo.partizione, 1):
            membri = ", ".join(etichette[id_vertice] for id_vertice in parte.vertici)
            righe.append(f"{numero}. {parte.etichetta} — {membri}")
    righe.extend(("", tr("graph.arrows")))
    righe.extend(f"{etichette[arco.origine]} → {etichette[arco.destinazione]}"
                 for arco in grafo.archi)
    if not grafo.archi:
        righe.append(tr("graph.no_arrows"))
    return "\n".join(righe)


class VistaGrafo(ttk.Frame):
    """Mostra il grafo e il dettaglio del vertice selezionato.

    La vista ospite dispone i vertici in coordinate Canvas distinte, con
    più di due raggi di distanza. Il componente fornisce interazione e stile.
    """

    def __init__(self, parent, *, righe_dettaglio=6, font_vertice=None, raggio=_RAGGIO):
        super().__init__(parent)
        self._grafo = GrafoOrientato()
        self._indice = None
        self._contorni = []
        self._parti = {}
        self._font = font_vertice or tkfont.nametofont("TkDefaultFont", root=self)
        self._raggio = raggio
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        schede = ttk.Notebook(self, takefocus=True)
        schede.grid(row=0, column=0, sticky="nsew")
        schede.enable_traversal()
        grafica = ttk.Frame(schede)
        testuale = ttk.Frame(schede)
        schede.add(grafica, text=tr("graph.diagram"))
        schede.add(testuale, text=tr("graph.text"))
        grafica.rowconfigure(1, weight=1)
        ttk.Label(grafica, text=tr("graph.keys")).grid(row=0, column=0, sticky="w", padx=6)
        self._canvas = tk.Canvas(grafica, background=_SFONDO, takefocus=True,
                                 highlightthickness=2, highlightbackground=_TRATTO,
                                 highlightcolor=_SELEZIONE)
        self._area_scorribile(grafica, self._canvas, riga=1, orizzontale=True)
        self._canvas.bind("<Button-1>", self._clic)
        self._canvas.bind("<Left>", lambda event: self._sposta(-1))
        self._canvas.bind("<Up>", lambda event: self._sposta(-1))
        self._canvas.bind("<Right>", lambda event: self._sposta(1))
        self._canvas.bind("<Down>", lambda event: self._sposta(1))
        self._canvas.bind("<Home>", lambda event: self._seleziona(0))
        self._canvas.bind("<End>", lambda event: self._seleziona(len(self._contorni) - 1))

        testuale.rowconfigure(0, weight=1)
        self._crea_equivalente(testuale)

        dettaglio = ttk.LabelFrame(self, text=tr("graph.detail"), padding=4)
        dettaglio.grid(row=1, column=0, sticky="ew")
        self._dettaglio = self._campo_testo(dettaglio, altezza=righe_dettaglio)
        self._area_scorribile(dettaglio, self._dettaglio)
        self.mostra(self._grafo, {})

    @staticmethod
    def _area_scorribile(parent, widget, riga=0, orizzontale=False):
        parent.columnconfigure(0, weight=1)
        widget.grid(row=riga, column=0, sticky="nsew")
        verticale = ttk.Scrollbar(parent, orient="vertical", command=widget.yview)
        verticale.grid(row=riga, column=1, sticky="ns")
        widget.configure(yscrollcommand=verticale.set)
        if orizzontale:
            barra = ttk.Scrollbar(parent, orient="horizontal", command=widget.xview)
            barra.grid(row=riga + 1, column=0, sticky="ew")
            widget.configure(xscrollcommand=barra.set)

    @staticmethod
    def _campo_testo(parent, altezza=12):
        return tk.Text(parent, height=altezza, width=1, wrap="word", takefocus=True,
                       state="disabled", font="TkDefaultFont", padx=6, pady=4)

    @staticmethod
    def _scrivi(widget, testo):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", testo)
        widget.configure(state="disabled")
        widget.yview_moveto(0)

    def _crea_equivalente(self, parent):
        self._testo = self._campo_testo(parent)
        self._area_scorribile(parent, self._testo)

    def _aggiorna_equivalente(self):
        self._scrivi(self._testo, testo_grafo(self._grafo))

    def _seleziona_equivalente(self, vertice):
        pass

    @property
    def selezionato(self):
        return None if self._indice is None else self._grafo.vertici[self._indice]

    def mostra(self, grafo, coordinate):
        """Carica dati e disposizione. Le coordinate ammettono anche valori negativi."""
        if set(coordinate) != {vertice.id for vertice in grafo.vertici}:
            raise ValueError("Serve una coordinata per ogni vertice")
        punti = list(coordinate.values())
        for indice, (x, y) in enumerate(punti):
            if not isfinite(x) or not isfinite(y):
                raise ValueError("Coordinate non finite")
            if any(hypot(x - u, y - v) <= 2 * self._raggio for u, v in punti[:indice]):
                raise ValueError("Vertici troppo vicini")
        # L'area scorrevole comincia a (0, 0), anche con coordinate negative.
        if punti:
            margine = max(_MARGINE, self._raggio + 20)
            sinistra = min(x for x, _ in punti) - margine
            alto = min(y for _, y in punti) - margine
            coordinate = {chiave: (x - sinistra, y - alto)
                          for chiave, (x, y) in coordinate.items()}
        self._grafo = grafo
        self._parti = {id_vertice: (numero, parte.etichetta)
                       for numero, parte in enumerate(grafo.partizione, 1)
                       for id_vertice in parte.vertici}
        self._indice = None
        self._contorni.clear()
        canvas = self._canvas
        canvas.delete("all")
        archi = set(grafo.archi)
        for arco in grafo.archi:
            reciproco = Arco(arco.destinazione, arco.origine) in archi
            canvas.create_line(*_tracciato_arco(arco, coordinate, reciproco, self._raggio),
                               arrow=tk.LAST, width=2, fill=_TRATTO, tags=("arco",))
        for indice, vertice in enumerate(grafo.vertici):
            self._disegna_vertice(indice, vertice, *coordinate[vertice.id])
        if not grafo.vertici:
            canvas.create_text(8, 8, text=tr("graph.empty"), anchor="nw", fill=_TESTO)
        _, _, destra, basso = canvas.bbox("all")
        canvas.configure(scrollregion=(0, 0, destra + 8, basso + 8))
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)
        self._aggiorna_equivalente()
        if grafo.vertici:
            self._seleziona(0)
        else:
            self._scrivi(self._dettaglio, tr("graph.empty"))

    def esporta_svg(self, titolo):
        """Serializza il diagramma completo, anche oltre l'area visibile."""
        from xml.etree import ElementTree as xml

        canvas = self._canvas
        _, _, larghezza, altezza = canvas.cget("scrollregion").split()
        radice = xml.Element("svg", xmlns="http://www.w3.org/2000/svg",
                             width=larghezza, height=altezza,
                             viewBox=f"0 0 {larghezza} {altezza}", role="img",
                             attrib={"aria-labelledby": "titolo descrizione"})
        xml.SubElement(radice, "title", id="titolo").text = titolo
        xml.SubElement(radice, "desc", id="descrizione").text = testo_grafo(self._grafo)
        xml.SubElement(radice, "rect", width=larghezza, height=altezza, fill=_SFONDO)
        definizioni = xml.SubElement(radice, "defs")
        freccia = xml.SubElement(definizioni, "marker", id="freccia",
                                 markerWidth="8", markerHeight="8", markerUnits="userSpaceOnUse",
                                 refX="7", refY="4", orient="auto")
        xml.SubElement(freccia, "path", d="M0 0 L8 4 L0 8 Z", fill=_TRATTO)
        for elemento in canvas.find_withtag("arco"):
            punti = " ".join(f"{valore:.3f}" for valore in canvas.coords(elemento))
            xml.SubElement(radice, "polyline", points=punti, fill="none", stroke=_TRATTO,
                           attrib={"stroke-width": "2", "marker-end": "url(#freccia)"})
        r = self._raggio
        dimensione = self._font.cget("size")
        pixel = -dimensione if dimensione < 0 else self.winfo_fpixels(f"{dimensione}p")
        for indice, vertice in enumerate(self._grafo.vertici):
            x1, y1, x2, y2 = canvas.coords(self._contorni[indice])
            x, y = (x1 + x2) / 2, (y1 + y2) / 2
            gruppo = xml.SubElement(radice, "g")
            xml.SubElement(gruppo, "title").text = vertice.dettaglio or vertice.etichetta
            xml.SubElement(gruppo, "circle", cx=f"{x:.3f}", cy=f"{y:.3f}",
                           r=str(r), fill=_SFONDO, stroke=_TRATTO)
            xml.SubElement(gruppo, "text", x=f"{x:.3f}", y=f"{y:.3f}", dy=".35em",
                           fill=_TESTO, attrib={"text-anchor": "middle", "font-size": f"{pixel:.1f}",
                                                "font-weight": self._font.cget("weight"),
                                                "font-family": "sans-serif"}).text = vertice.etichetta
            if vertice.id in self._parti:
                numero, _ = self._parti[vertice.id]
                xml.SubElement(gruppo, "text", x=f"{x + r - 3:.3f}", y=f"{y + r + 6:.3f}",
                               fill=_TESTO, attrib={"font-size": "10",
                                                    "font-family": "sans-serif"}).text = str(numero)
        return xml.tostring(radice, encoding="utf-8", xml_declaration=True)

    def _disegna_vertice(self, indice, vertice, x, y):
        canvas = self._canvas
        tag = f"vertice_{indice}"
        r = self._raggio
        contorno = canvas.create_oval(x-r, y-r, x+r, y+r, fill=_SFONDO, outline=_TRATTO,
                                      width=1, tags=(tag,))
        etichetta = vertice.etichetta
        if self._font.measure(etichetta) > 2 * r - 8:
            while etichetta and self._font.measure(etichetta + "…") > 2 * r - 8:
                etichetta = etichetta[:-1]
            etichetta += "…"
        canvas.create_text(x, y, text=etichetta, fill=_TESTO, font=self._font, tags=(tag,))
        if vertice.id in self._parti:
            numero, _ = self._parti[vertice.id]
            canvas.create_text(x + r - 3, y + r - 4, text=str(numero), font="TkSmallCaptionFont",
                               fill=_TESTO, anchor="nw", tags=(tag,))
        self._contorni.append(contorno)

    def _clic(self, event):
        self._canvas.focus_set()
        for tag in self._canvas.gettags("current"):
            if tag.startswith("vertice_"):
                self._seleziona(int(tag.removeprefix("vertice_")))
                break

    def _sposta(self, delta):
        if self._indice is not None:
            nuovo = min(max(0, self._indice + delta), len(self._contorni) - 1)
            self._seleziona(nuovo)
        return "break"

    def _seleziona(self, indice):
        if not 0 <= indice < len(self._contorni):
            return "break"
        if self._indice is not None:
            self._canvas.itemconfigure(self._contorni[self._indice], fill=_SFONDO,
                                       outline=_TRATTO, width=1)
        self._indice = indice
        contorno = self._contorni[indice]
        self._canvas.itemconfigure(contorno, fill=_RIEMPIMENTO, outline=_SELEZIONE, width=3)
        vertice = self.selezionato
        righe = [vertice.etichetta]
        if vertice.id in self._parti:
            numero, nome = self._parti[vertice.id]
            righe.append(tr("graph.part", number=numero, name=nome))
        if vertice.dettaglio:
            righe.append(vertice.dettaglio)
        dettaglio = "\n".join(righe)
        self._scrivi(self._dettaglio, dettaglio)
        self._seleziona_equivalente(vertice)
        self._mostra_selezione(contorno)
        return "break"

    def _mostra_selezione(self, contorno):
        canvas = self._canvas
        x1, y1, x2, y2 = canvas.bbox(contorno)
        _, _, destra, basso = map(int, canvas.cget("scrollregion").split())
        for inizio, fine, estensione, visibile, offset, muovi in (
            (x1, x2, destra, canvas.winfo_width(), canvas.canvasx(0), canvas.xview_moveto),
            (y1, y2, basso, canvas.winfo_height(), canvas.canvasy(0), canvas.yview_moveto),
        ):
            if visibile > 1 and not (offset <= inizio and fine <= offset + visibile):
                centro = (inizio + fine - visibile) / 2
                muovi(max(0, centro) / estensione)


class VistaGrafoConTabella(VistaGrafo):
    """Usa righe collegate ai vertici come equivalente del diagramma."""

    def _crea_equivalente(self, parent):
        # Le colonne eccedenti restano raggiungibili dalla barra orizzontale.
        parent.grid_propagate(False)
        self._font_tabella = tkfont.nametofont("TkDefaultFont", root=self).copy()
        self._font_tabella.configure(size=12)
        self._font_intestazione = self._font_tabella.copy()
        self._font_intestazione.configure(weight="bold")
        stile = ttk.Style(self)
        stile.configure("Grafo.Tabella.Treeview", font=self._font_tabella,
                        rowheight=self._font_tabella.metrics("linespace") + 8)
        stile.configure("Grafo.Tabella.Treeview.Heading", font=self._font_intestazione)
        self._tabella = ttk.Treeview(parent, columns=self._COLONNE, show="headings",
                                    style="Grafo.Tabella.Treeview", height=9, selectmode="browse",
                                    takefocus=True)
        self._intestazioni = dict(zip(self._COLONNE, tr(self._CHIAVE_INTESTAZIONI).split("|"),
                                     strict=True))
        for colonna, titolo in self._intestazioni.items():
            self._tabella.heading(colonna, text=titolo)
        self._area_scorribile(parent, self._tabella, orizzontale=True)
        self._tabella.bind("<<TreeviewSelect>>", self._riga_selezionata)
        self._tabella.bind("<Shift-Left>", lambda event: self._scorri_tabella(-1))
        self._tabella.bind("<Shift-Right>", lambda event: self._scorri_tabella(1))

    def _scorri_tabella(self, verso):
        self._tabella.xview_scroll(verso, "units")
        return "break"

    def _aggiorna_equivalente(self):
        self._tabella.delete(*self._tabella.get_children())
        larghezze = {colonna: self._font_intestazione.measure(titolo)
                     for colonna, titolo in self._intestazioni.items()}
        self._indici_vertici = {vertice.id: i for i, vertice in enumerate(self._grafo.vertici)}
        for id_vertice, dati in self._righe_tabella():
            valori = tuple(str(dati[colonna]) for colonna in self._COLONNE)
            self._tabella.insert("", "end", iid=id_vertice, values=valori)
            for colonna, valore in zip(self._COLONNE, valori):
                larghezze[colonna] = max(larghezze[colonna], self._font_tabella.measure(valore))
        for colonna, larghezza in larghezze.items():
            self._tabella.column(colonna, width=larghezza + 24, stretch=False, anchor="w")
        self._tabella.xview_moveto(0)
        self._tabella.yview_moveto(0)

    def _riga_selezionata(self, _evento):
        selezione = self._tabella.selection()
        if selezione and (self.selezionato is None or selezione[0] != self.selezionato.id):
            self._seleziona(self._indici_vertici[selezione[0]])

    def _seleziona_equivalente(self, vertice):
        if self._tabella.selection() != (vertice.id,):
            self._tabella.selection_set(vertice.id)
            self._tabella.focus(vertice.id)
            self._tabella.see(vertice.id)
