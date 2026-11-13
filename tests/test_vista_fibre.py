"""Verifica trasporto, somme, ricostruzione e integrazione della Vista Fibre."""

import tkinter as tk
from xml.etree import ElementTree as xml

import pytest

from gioco27.gui import cycles_tab, i18n
from gioco27.gui.guide import render_guide_segments
from gioco27.gui.vista_fibre import prepara_fibre
from gioco27.riferimenti import riferimento
from gioco27.services import laboratorio, riconoscimento as rc


def test_fibre_e_grafo_su_gamma():
    trasformazioni = laboratorio._gamma()
    assert len(trasformazioni) == 648
    for perm in trasformazioni:
        analisi = rc.analizza_fibre(perm)
        grafo, _ = prepara_fibre(analisi)
        assert len(grafo.vertici) == len(grafo.archi) == 9
        assert [len(parte.vertici) for parte in grafo.partizione] == [3, 3, 3]
        archi = {arco.origine: arco.destinazione for arco in grafo.archi}
        per_fibra = {(f.livello, f.cifra): f.elementi for f in analisi.fibre}
        assert analisi.diretta.coincide == analisi.inversa.coincide
        for fibra, vertice in zip(analisi.fibre, grafo.vertici):
            i, t = fibra.livello, fibra.cifra
            assert len(fibra.elementi) == 9
            assert all(x // 3**i % 3 == t for x in fibra.elementi)
            assert fibra.somma == sum(fibra.elementi)
            assert fibra.immagine == per_fibra[fibra.arrivo]
            assert set(fibra.immagine) == {perm[x] for x in fibra.elementi}
            k, u = fibra.arrivo
            assert archi[vertice.id] == grafo.partizione[k].vertici[u]
            assert analisi.diretta.livelli[i].somme[t] == sum(fibra.immagine)
            assert analisi.inversa.livelli[i].somme[t] == sum(
                x for x, y in enumerate(perm) if y in fibra.elementi)
            if analisi.separabilita.separabile:
                assert analisi.diretta.coincide and analisi.inversa.coincide
                assert analisi.diretta.livelli[i].candidati[t] == u
                assert analisi.inversa.livelli[i].candidati[u] == t


def test_fibra_distribuita_e_trasporto_parziale():
    analisi = rc.analizza_fibre((1, 0, *range(2, 27)))
    grafo, _ = prepara_fibre(analisi)
    assert len(grafo.archi) == 7
    assert [f.cifra for f in analisi.fibre if f.arrivo is None] == [0, 1]
    assert not analisi.diretta.vero and not analisi.inversa.vero
    assert i18n.tr("fibres.split") in grafo.vertici[0].dettaglio
    assert i18n.tr("fibres.no_factor") in grafo.vertici[0].dettaglio
    assert "Σ" in grafo.vertici[0].dettaglio and "Λ" in grafo.vertici[0].dettaglio


@pytest.mark.parametrize("lingua", ["it", "en"])
def test_guida_fibre_cita_il_teorema(lingua):
    guida = "".join(testo for _, testo in render_guide_segments(lingua))
    assert riferimento("ricostruzione_fibre", lingua) in guida
    assert "⟦rif:ricostruzione_fibre⟧" not in guida


@pytest.mark.parametrize("lingua", ["it", "en"])
def test_vista_fibre_tastiera_testo_svg_e_reset(lingua, tmp_path, monkeypatch):
    try:
        root = tk.Tk()
    except tk.TclError as errore:
        pytest.skip(f"Tk non disponibile: {errore}")
    precedente = i18n.get_language()
    i18n.set_language(lingua)
    try:
        root.geometry("900x560")
        frame = cycles_tab.CyclesFrame(root)
        frame.pack(fill="both", expand=True)
        vista, pulsante = frame._vista_fibre, frame._btn_fibre_svg
        assert pulsante.instate(["disabled"])
        scheda = vista.master
        scheda.master.select(scheda)
        frame.set_permutation(range(27))
        root.update()
        assert vista._canvas.winfo_viewable()
        assert vista._canvas.winfo_height() > 100
        x1, y1, x2, y2 = vista._canvas.coords(vista._contorni[1])
        x = round((x1 + x2) / 2 - vista._canvas.canvasx(0))
        y = round((y1 + y2) / 2 - vista._canvas.canvasy(0))
        vista._canvas.event_generate("<Motion>", x=x, y=y)
        vista._canvas.event_generate("<Button-1>", x=x, y=y)
        assert vista.selezionato.id == "F(0,1)"
        vista._canvas.focus_force()
        root.update()
        vista._canvas.event_generate("<End>")
        assert vista.selezionato.id == "F(2,2)"
        vista._canvas.event_generate("<Left>")
        assert vista.selezionato.id == "F(2,1)"
        assert "117" in vista._dettaglio.get("1.0", "end")
        assert vista._dettaglio.yview() == (0.0, 1.0)
        tabella = vista._tabella
        tabella.master.master.select(tabella.master)
        root.update()
        assert len(tabella.get_children()) == 9
        assert tabella.set("F(2,1)", "sigma") == "117"
        assert tabella.selection() == ("F(2,1)",)
        tabella.selection_set("F(0,0)")
        root.update()
        assert vista.selezionato.id == "F(0,0)"
        assert tabella.xview()[1] < 1
        percorso = tmp_path / "fibre.svg"
        monkeypatch.setattr(cycles_tab.filedialog, "asksaveasfilename", lambda **kw: percorso)
        pulsante.invoke()
        svg = xml.parse(percorso)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        assert len(svg.findall("svg:g/svg:circle", ns)) == 9
        assert len(svg.findall("svg:polyline", ns)) == 9
        etichetta = svg.find("svg:g/svg:text", ns)
        assert etichetta.text == "F(0,0)"
        assert float(etichetta.get("font-size")) == 20
        frame.reset()
        assert vista.selezionato is None
        assert not tabella.get_children()
        assert pulsante.instate(["disabled"])
    finally:
        root.destroy()
        i18n.set_language(precedente)
