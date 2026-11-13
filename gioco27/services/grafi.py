"""Dati condivisi delle visualizzazioni strutturali."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Vertice:
    id: str
    etichetta: str
    dettaglio: str = ""


@dataclass(frozen=True)
class Arco:
    origine: str
    destinazione: str


@dataclass(frozen=True)
class Parte:
    etichetta: str
    vertici: tuple[str, ...]


@dataclass(frozen=True)
class GrafoOrientato:
    """Grafo semplice orientato, con cappi e partizione facoltativa.

    L'ordine dei vertici determina l'ordine di lettura e di selezione.
    Etichette e dettagli sono forniti dalla vista che conosce il dominio.
    """

    vertici: tuple[Vertice, ...] = ()
    archi: tuple[Arco, ...] = ()
    partizione: tuple[Parte, ...] = ()

    def __post_init__(self):
        identificatori = {vertice.id for vertice in self.vertici}
        if len(identificatori) != len(self.vertici):
            raise ValueError("Identificatori dei vertici duplicati")
        if len(set(self.archi)) != len(self.archi):
            raise ValueError("Archi duplicati")
        for arco in self.archi:
            if arco.origine not in identificatori or arco.destinazione not in identificatori:
                raise ValueError(f"Arco con estremo sconosciuto: {arco}")
        if self.partizione:
            membri = [id_vertice for parte in self.partizione for id_vertice in parte.vertici]
            if any(not parte.vertici for parte in self.partizione):
                raise ValueError("La partizione contiene una parte vuota")
            if len(membri) != len(identificatori) or set(membri) != identificatori:
                raise ValueError("La partizione deve contenere ogni vertice una sola volta")
