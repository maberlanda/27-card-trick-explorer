"""Adattamento dell'analisi delle fibre al grafo della trasformazione corrente."""

from math import cos, radians, sin
from tkinter import font as tkfont

from ..riferimenti import riferimento
from ..services.grafi import Arco, GrafoOrientato, Parte, Vertice
from ..services.riconoscimento import COSTANTI_C
from .i18n import get_language, tr
from .vista_grafo import VistaGrafoConTabella


def _lista(elementi):
    return ", ".join(map(str, elementi))


def _dati_fibra(analisi, fibra):
    i, t = fibra.livello, fibra.cifra
    diretto = analisi.diretta.livelli[i]
    inverso = analisi.inversa.livelli[i]
    fattore = analisi.separabilita.livelli[i].fattore
    return dict(
        level=i, digit=t, free=_lista(j for j in range(3) if j != i),
        members=_lista(fibra.elementi), total=fibra.somma, image=_lista(fibra.immagine),
        target=tr("fibres.split") if fibra.arrivo is None else _nome(*fibra.arrivo),
        sigma=diretto.somme[t], lam=inverso.somme[t], constant=COSTANTI_C[i],
        forward=diretto.candidati[t], backward=inverso.candidati[t],
        factor=tr("fibres.no_factor") if fattore is None else f"({_lista(fattore)})",
    )


def _nome(i, t):
    return f"F({i},{t})"


def prepara_fibre(analisi):
    """Dispone le tre famiglie in settori, con un arco per ogni arrivo esatto."""
    vertici = []
    archi = []
    coordinate = {}
    famiglie = [[], [], []]
    for fibra in analisi.fibre:
        i, t = fibra.livello, fibra.cifra
        nome = _nome(i, t)
        famiglie[i].append(nome)
        angolo = radians(-130 + (3 * i + t) * 40)
        coordinate[nome] = (275 * cos(angolo), 185 * sin(angolo))
        if fibra.arrivo is not None:
            archi.append(Arco(nome, _nome(*fibra.arrivo)))
        dettaglio = tr("fibres.detail", **_dati_fibra(analisi, fibra))
        vertici.append(Vertice(nome, nome, dettaglio))
    parti = tuple(Parte(tr("fibres.level", level=i), tuple(membri))
                  for i, membri in enumerate(famiglie))
    return GrafoOrientato(tuple(vertici), tuple(archi), parti), coordinate


def didascalia_fibre():
    return tr("fibres.scope", theorem=riferimento("ricostruzione_fibre", get_language()))


class VistaFibre(VistaGrafoConTabella):
    _CHIAVE_INTESTAZIONI = "fibres.table_headers"
    _COLONNE = ("fibre", "target", "sigma", "lam", "forward", "backward",
                "factor", "level", "digit", "free", "members", "total", "image", "constant")

    def __init__(self, parent):
        self._analisi = None
        font_vertice = tkfont.nametofont("TkDefaultFont", root=parent).copy()
        font_vertice.configure(size=-20, weight="bold")
        super().__init__(parent, righe_dettaglio=10, font_vertice=font_vertice, raggio=38)

    def mostra_analisi(self, analisi):
        self._analisi = analisi
        self.mostra(*(prepara_fibre(analisi) if analisi is not None else (GrafoOrientato(), {})))

    def _righe_tabella(self):
        if self._analisi is not None:
            for fibra, vertice in zip(self._analisi.fibre, self._grafo.vertici):
                dati = _dati_fibra(self._analisi, fibra)
                dati["fibre"] = vertice.etichetta
                yield vertice.id, dati
