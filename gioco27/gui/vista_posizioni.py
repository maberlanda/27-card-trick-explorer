"""Adattamento della permutazione corrente alla Vista Posizioni."""

from math import cos, pi, sin

from ..services.grafi import Arco, GrafoOrientato, Parte, Vertice
from .i18n import tr
from .vista_grafo import VistaGrafoConTabella


def _orbita(ciclo, passo):
    return " → ".join(map(str, (*ciclo[passo:], *ciclo[:passo + 1])))


def prepara_posizioni(perm, cicli):
    """Usa i cicli del core come parti e dispone ciascuno in un riquadro."""
    vertici = []
    parti = []
    coordinate = {}
    x = y = altezza_riga = 0
    for numero, ciclo in enumerate(cicli, 1):
        lunghezza = len(ciclo)
        tipo = (tr("cycles.fixed_point") if lunghezza == 1
                else tr("positions.cycle_length", length=lunghezza))
        parti.append(Parte(tipo, tuple(map(str, ciclo))))
        raggio = 0 if lunghezza == 1 else 33 / sin(pi / lunghezza)
        lato = 2 * raggio + 100
        if x and x + lato > 940:
            x, y, altezza_riga = 0, y + altezza_riga, 0
        for passo, posizione in enumerate(ciclo):
            id_vertice = str(posizione)
            dettaglio = tr("positions.detail", origin=posizione, image=perm[posizione],
                           cycle=numero, kind=tipo, orbit=_orbita(ciclo, passo))
            vertici.append(Vertice(id_vertice, id_vertice, dettaglio))
            angolo = 2 * pi * passo / lunghezza - pi / 2
            coordinate[id_vertice] = (x + lato / 2 + raggio * cos(angolo),
                                      y + lato / 2 + raggio * sin(angolo))
        x += lato
        altezza_riga = max(altezza_riga, lato)
    archi = tuple(Arco(str(i), str(j)) for i, j in enumerate(perm))
    return GrafoOrientato(tuple(vertici), archi, tuple(parti)), coordinate


class VistaPosizioni(VistaGrafoConTabella):
    _CHIAVE_INTESTAZIONI = "positions.table_headers"
    _COLONNE = ("origin", "image", "cycle", "kind", "orbit")

    def _righe_tabella(self):
        immagini = {arco.origine: arco.destinazione for arco in self._grafo.archi}
        righe = {}
        for numero, parte in enumerate(self._grafo.partizione, 1):
            for passo, posizione in enumerate(parte.vertici):
                righe[posizione] = dict(origin=posizione, image=immagini[posizione],
                                        cycle=numero, kind=parte.etichetta,
                                        orbit=_orbita(parte.vertici, passo))
        return sorted(righe.items(), key=lambda riga: int(riga[0]))
