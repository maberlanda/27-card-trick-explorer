"""Corrispondenza fra la Vista Posizioni e i dati del programma."""

from math import dist
import tkinter as tk
from xml.etree import ElementTree as xml

import pytest

from gioco27.core.analysis import cycle_decomposition
from gioco27.gui.cycles_tab import CyclesFrame
from gioco27.gui import cycles_tab
from gioco27.gui.vista_posizioni import prepara_posizioni
from gioco27.services import laboratorio


def test_grafi_sulle_648_trasformazioni_e_su_un_ciclo_di_27():
    lungo = (*range(1, 27), 0)
    for perm in (*laboratorio._gamma(), lungo):
        cicli = cycle_decomposition(perm)
        grafo, coordinate = prepara_posizioni(perm, cicli)
        assert len(grafo.vertici) == len(grafo.archi) == len(coordinate) == 27
        assert {int(a.origine): int(a.destinazione) for a in grafo.archi} == dict(enumerate(perm))
        assert [parte.vertici for parte in grafo.partizione] == [
            tuple(map(str, ciclo)) for ciclo in cicli]
        punti = list(coordinate.values())
        assert min(dist(a, b) for i, a in enumerate(punti) for b in punti[i + 1:]) > 40


def test_vista_posizioni_esporta_e_si_aggiorna(tmp_path, monkeypatch):
    try:
        root = tk.Tk()
    except tk.TclError as errore:
        pytest.skip(f"Tk non disponibile: {errore}")
    try:
        root.geometry("1280x720")
        vista = CyclesFrame(root)
        vista.pack(fill="both", expand=True)
        assert vista._btn_svg.instate(["disabled"])
        vista.set_permutation((4, 2, 1, 0, 3, *range(5, 27)))
        root.update()
        assert vista._order_var.get() == "6"
        posizioni = vista._vista_posizioni
        assert "0 → 4 → 3 → 0" in posizioni.selezionato.dettaglio
        posizioni.master.master.select(posizioni.master)
        tabella = posizioni._tabella
        tabella.master.master.select(tabella.master)
        root.update()
        assert tabella.get_children() == tuple(map(str, range(27)))
        assert tabella.item("1", "values")[:3] == ("1", "2", "2")
        assert tabella.set("4", "orbit") == "4 → 3 → 0 → 4"
        tabella.selection_set("4")
        root.update()
        assert posizioni.selezionato.id == "4"
        assert "4 → 3 → 0 → 4" in posizioni._dettaglio.get("1.0", "end")
        assert vista._btn_svg.instate(["!disabled"])
        percorso = tmp_path / "posizioni.svg"
        monkeypatch.setattr(cycles_tab.filedialog, "asksaveasfilename", lambda **kw: percorso)
        vista._btn_svg.invoke()
        svg = xml.parse(percorso)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        archi = svg.findall("svg:polyline", ns)
        assert len(archi) == 27
        assert all(arco.get("marker-end") == "url(#freccia)" for arco in archi)
        assert len(svg.findall("svg:g/svg:circle", ns)) == 27
        vista.set_permutation((*range(1, 27), 0))
        root.update()
        assert tabella.set("0", "orbit").endswith("25 → 26 → 0")
        assert tabella.xview()[1] < 1
        vista.set_permutation(range(27))
        assert vista._order_var.get() == "1"
        assert "0 → 0" in vista._vista_posizioni.selezionato.dettaglio
        vista.reset()
        assert vista._btn_svg.instate(["disabled"])
        assert vista._vista_posizioni.selezionato is None
        assert not tabella.get_children()
    finally:
        root.destroy()
