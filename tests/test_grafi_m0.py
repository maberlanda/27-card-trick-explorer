"""Contratti del modello grafico M0 e del componente condiviso."""

import tkinter as tk

import pytest

from gioco27.core.analysis import cycle_decomposition
from gioco27.gui.vista_grafo import VistaGrafo, testo_grafo as descrivi_grafo
from gioco27.i18n import get_language, set_language, tr
from gioco27.services.grafi import Arco, GrafoOrientato, Parte, Vertice
from gioco27.services.riconoscimento import criterio_somme


@pytest.fixture
def posizioni():
    permutazione = (1, 2, 0, 4, 3, *range(5, 27))
    cicli = cycle_decomposition(permutazione)
    return GrafoOrientato(
        tuple(Vertice(str(i), str(i), f"T({i}) = {j}") for i, j in enumerate(permutazione)),
        tuple(Arco(str(i), str(j)) for i, j in enumerate(permutazione)),
        tuple(Parte(f"C{i}", tuple(map(str, ciclo))) for i, ciclo in enumerate(cicli)),
    )


@pytest.fixture
def fibre():
    trasformazione = tuple(3 * (x // 3) + (x + 1) % 3 for x in range(27))
    criterio = criterio_somme(trasformazione)
    assert criterio.coincide
    vertici = []
    archi = []
    parti = []
    for livello in criterio.livelli:
        i = livello.livello
        ids = tuple(f"F{i},{t}" for t in range(3))
        parti.append(Parte(f"L{i}", ids))
        for origine, somma, destinazione in zip(ids, livello.somme, livello.fattore):
            vertici.append(Vertice(origine, origine, f"Σ = {somma}"))
            archi.append(Arco(origine, ids[destinazione]))
    return GrafoOrientato(tuple(vertici), tuple(archi), tuple(parti))


def test_posizioni_archi_e_cicli(posizioni):
    assert len(posizioni.vertici) == len(posizioni.archi) == 27
    assert posizioni.partizione[0].vertici == ("0", "1", "2")
    assert [arco for arco in posizioni.archi if arco.origine == arco.destinazione] == [
        Arco(str(i), str(i)) for i in range(5, 27)
    ]
    testo = descrivi_grafo(posizioni)
    assert "0 → 1" in testo
    assert "1 → 0" not in testo
    assert "3 → 4" in testo and "4 → 3" in testo
    assert "5 → 5" in testo


def test_fibre_trasporto_e_somme(fibre):
    assert len(fibre.partizione) == 3
    assert fibre.archi[:4] == (Arco("F0,0", "F0,1"), Arco("F0,1", "F0,2"),
                              Arco("F0,2", "F0,0"), Arco("F1,0", "F1,0"))
    testo = descrivi_grafo(fibre)
    assert "1. L0 — F0,0, F0,1, F0,2" in testo
    assert "Σ = 117" in testo
    assert "F0,0 → F0,1" in testo


@pytest.mark.parametrize("archi,parti", [
    ((Arco("a", "b"),), ()),
    ((Arco("a", "a"), Arco("a", "a")), ()),
    ((), (Parte("p", ()),)),
    ((), (Parte("p", ("a", "a")),)),
    ((), (Parte("p", ("b",)),)),
])
def test_rifiuta_riferimenti_o_partizioni_non_validi(archi, parti):
    with pytest.raises(ValueError):
        GrafoOrientato((Vertice("a", "A"),), archi, parti)


def test_rifiuta_vertici_duplicati():
    with pytest.raises(ValueError):
        GrafoOrientato((Vertice("a", "A"), Vertice("a", "B")))


@pytest.fixture(params=["it", "en"])
def vista(request):
    precedente = get_language()
    try:
        radice = tk.Tk()
    except tk.TclError as errore:
        pytest.skip(f"Tk non disponibile: {errore}")
    try:
        set_language(request.param)
        radice.geometry("1280x720")
        widget = VistaGrafo(radice)
        widget.pack(fill="both", expand=True)
        radice.update()
        yield radice, widget
    finally:
        radice.destroy()
        set_language(precedente)


def test_disegno_selezione_testo_e_tastiera(vista, posizioni):
    radice, widget = vista
    canvas = widget._canvas
    coordinate = {str(i): (i * 75 - 200, -50) for i in range(27)}
    widget.mostra(posizioni, coordinate)
    assert len(canvas.find_withtag("arco")) == 27
    assert all(canvas.itemcget(item, "arrow") == "last" for item in canvas.find_withtag("arco"))
    assert widget._testo.get("1.0", "end-1c") == descrivi_grafo(posizioni)
    canvas.focus_force()
    radice.update()
    canvas.event_generate("<Right>")
    assert widget.selezionato.id == "1"
    assert "T(1) = 2" in widget._dettaglio.get("1.0", "end")
    canvas.event_generate("<End>")
    assert widget.selezionato.id == "26"
    assert canvas.xview()[1] == 1.0
    canvas.event_generate("<Home>")
    assert widget.selezionato.id == "0"
    radice.update()
    x, y = canvas.coords(widget._contorni[2])[:2]
    x, y = int(x + 20 - canvas.canvasx(0)), int(y + 20 - canvas.canvasy(0))
    canvas.event_generate("<Motion>", x=x, y=y)
    canvas.event_generate("<Button-1>", x=x, y=y)
    assert widget.selezionato.id == "2"


def test_ricaricamento_fibre_e_stato_vuoto(vista, fibre):
    _, widget = vista
    widget.mostra(fibre, {v.id: (75 * (i % 3), 75 * (i // 3))
                         for i, v in enumerate(fibre.vertici)})
    assert len(widget._canvas.find_withtag("arco")) == 9
    assert tr("graph.part", number=1, name="L0") in widget._dettaglio.get("1.0", "end")
    widget.mostra(GrafoOrientato(), {})
    assert widget.selezionato is None
    assert not widget._canvas.find_withtag("arco")
    assert widget._testo.get("1.0", "end-1c") == tr("graph.empty")
