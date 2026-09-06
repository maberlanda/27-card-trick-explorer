"""
Analisi algebrica del gruppo G = GEN3 x GEN3 x GEN3  (|G| = 216).

Funzioni principali:
  get_group_data()        -> GroupData (singleton lazy)
  GroupData.classes       -> lista di classi di coniugio
  GroupData.center        -> indici degli elementi del centro Z(G)
  GroupData.cayley        -> tabella di Cayley (216x216 np.int32)
  GroupData.orders        -> ordine di ogni elemento (array 216)
  export_cayley_csv(path) -> scrive la tabella su CSV
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from typing import List

import numpy as np

from .kronecker import _get_kron_table


# ---------------------------------------------------------------- dataclass --

@dataclass
class GroupData:
    """Dati precalcolati del gruppo G = GEN3^3."""

    kron_arr:  np.ndarray          # (216, 27) int32
    kron_names: List[tuple]        # [(f3,f2,f1), ...]  lunghezza 216

    # Lazy: calcolati su richiesta
    _cayley:  "np.ndarray | None" = field(default=None, repr=False)
    _inverse: "np.ndarray | None" = field(default=None, repr=False)
    _orders:  "np.ndarray | None" = field(default=None, repr=False)
    _classes: "list | None"       = field(default=None, repr=False)
    _center:  "list | None"       = field(default=None, repr=False)

    # ---------------------------------------------------------- composition --

    def compose(self, i: int, j: int) -> int:
        """Indice di kron_arr[i] o kron_arr[j]."""
        return int(self.cayley[i, j])

    # --------------------------------------------------------------- cayley --

    @property
    def cayley(self) -> np.ndarray:
        if self._cayley is None:
            self._cayley = self._build_cayley()
        return self._cayley

    def _build_cayley(self) -> np.ndarray:
        """
        Tabella di Cayley vectorizzata.
        cayley[i,j] = indice di (kron_arr[i] o kron_arr[j])
        """
        arr = self.kron_arr
        n   = len(arr)
        # Per ogni i: arr[i][arr[j]] per tutti j
        # arr[i] ha shape (27,); arr ha shape (n, 27)
        # arr[i][arr] -> shape (n, 27) -> tabella composizioni riga i
        lookup = {arr[k].tobytes(): k for k in range(n)}
        cayley = np.empty((n, n), dtype=np.int32)
        for i in range(n):
            row = arr[i][arr]          # (n, 27): arr[i] composto con tutti
            for j in range(n):
                cayley[i, j] = lookup[row[j].tobytes()]
        return cayley

    # -------------------------------------------------------------- inverse --

    @property
    def inverse(self) -> np.ndarray:
        """inverse[i] = indice dell'inverso di kron_arr[i]."""
        if self._inverse is None:
            # kron_arr[i] e una permutazione; inv = argsort
            arr = self.kron_arr
            lookup = {arr[k].tobytes(): k for k in range(len(arr))}
            inv_perms = np.argsort(arr, axis=1).astype(np.int32)   # (n, 27)
            self._inverse = np.array(
                [lookup[inv_perms[i].tobytes()] for i in range(len(arr))],
                dtype=np.int32)
        return self._inverse

    # --------------------------------------------------------------- orders --

    @property
    def orders(self) -> np.ndarray:
        """orders[i] = ordine di kron_arr[i] nel gruppo."""
        if self._orders is None:
            n    = len(self.kron_arr)
            cay  = self.cayley
            iden = self._identity_index()
            ord_arr = np.empty(n, dtype=np.int32)
            for i in range(n):
                # Parto da g^0 = identita e itero g^k = g * g^(k-1)
                cur = iden
                cnt = 0
                while True:
                    cur = int(cay[i, cur])
                    cnt += 1
                    if cur == iden or cnt > n:
                        break
                ord_arr[i] = cnt
            self._orders = ord_arr
        return self._orders

    def _identity_index(self) -> int:
        """Indice dell'elemento neutro (e tale che e o g = g per ogni g)."""
        cay = self.cayley
        n   = len(self.kron_arr)
        for i in range(n):
            if np.all(cay[i] == np.arange(n, dtype=np.int32)):
                return i
        return 0   # fallback

    # ------------------------------------------------------- conjugacy ------

    @property
    def classes(self) -> list:
        """Lista di classi di coniugio (liste di indici), ordinate per dim."""
        if self._classes is None:
            self._classes, self._center = self._build_classes()
        return self._classes

    @property
    def center(self) -> list:
        """Lista di indici degli elementi del centro Z(G)."""
        if self._center is None:
            self._classes, self._center = self._build_classes()
        return self._center

    def _build_classes(self):
        """
        Calcola classi di coniugio e centro in O(n^2) con numpy.
        coniugato(g, h) = h o g o h^-1
        """
        n   = len(self.kron_arr)
        cay = self.cayley
        inv = self.inverse

        visited = np.zeros(n, dtype=bool)
        classes: list = []

        for g in range(n):
            if visited[g]:
                continue
            # h o g = cay[h, g]; (h o g) o h^-1 = cay[cay[h, g], inv[h]]
            conj_indices = cay[cay[:, g], inv]   # shape (n,)
            cls = np.unique(conj_indices).tolist()
            for idx in cls:
                visited[idx] = True
            classes.append(cls)

        classes.sort(key=len)

        # Centro: elementi con classe di coniugio di dimensione 1
        center = [cls[0] for cls in classes if len(cls) == 1]
        return classes, center

    # --------------------------------------------------------------- export --

    def export_cayley_csv(self, path: str) -> None:
        """
        Scrive la tabella di Cayley su CSV.
        Prima riga e prima colonna: nomi degli elementi.
        """
        names = ["{} x {} x {}".format(*t) for t in self.kron_names]
        cay   = self.cayley
        n     = len(names)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";", quotechar='"', quoting=__import__("csv").QUOTE_ALL)
            writer.writerow([""] + names)
            for i in range(n):
                writer.writerow([names[i]] + [names[int(cay[i, j])] for j in range(n)])

    def name(self, idx: int) -> str:
        """Nome leggibile di kron_arr[idx]."""
        t = self.kron_names[idx]
        return "({} x {} x {})".format(*t)


# ---------------------------------------------------------------- singleton --

_instance: "GroupData | None" = None


def get_group_data() -> GroupData:
    """Restituisce il singleton GroupData (costruisce lazy al primo accesso)."""
    global _instance
    if _instance is None:
        kron_arr, kron_names, _ = _get_kron_table()
        _instance = GroupData(kron_arr=kron_arr, kron_names=kron_names)
    return _instance
