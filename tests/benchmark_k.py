#!/usr/bin/env python3
"""Benchmark della 4.0.0 (compartimento K): piccoli, deterministici, senza soglie.

Uso (dalla radice del repository o dalla sdist):
    python tests/benchmark_k.py            # tabella leggibile
    python tests/benchmark_k.py --json     # stesso contenuto in JSON

Non e' un test (pytest non lo raccoglie: il nome non comincia con test_).
Ogni misura riporta la prima esecuzione nel processo («fredda»: include le
cache interne costruite al primo uso) e la migliore di N ripetizioni
(«calda»). I tempi servono da riferimento della 4.0, non da limite: la
macchina e l'interprete sono registrati insieme ai numeri.
"""
import json
import os
import platform
import random
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gioco27  # noqa: E402

RIPETIZIONI = 3


def _selftest():
    from gioco27.core.gioco_reale import selftest
    assert selftest()["esito"] == "TUTTO OK"


def _tavola_216():
    from gioco27.core.gioco_reale import riga_tavola
    from gioco27.services import tabellone as tb
    for n in range(216):
        r = riga_tavola(n)
        assert tb.numero_di(tuple(r["T"])) == n
        tb.tabellone(n)


def _riconoscimento():
    from gioco27.services import riconoscimento as rc
    from gioco27.core.gioco_reale import riga_tavola
    gen = random.Random(27)
    casi = [list(riga_tavola(n)["T"]) for n in range(0, 216, 9)]
    for _ in range(24):
        p = list(range(27))
        gen.shuffle(p)
        casi.append(p)
    for p in casi:
        rc.separabile(p)
        rc.classe_estesa(p)
        rc.criterio_somme(p)


def _laboratorio_i6():
    from gioco27.services import laboratorio as lab
    n = 0
    for pr in lab.CATALOGO:
        for d in pr.domini:
            lab.verifica(pr.id, d)
            n += 1
    assert n > 0


def _esperimento_j():
    from gioco27.services import archivio
    from gioco27.services import esperimento as E
    from gioco27.services.procedure import ProceduraGioco
    stato = {
        "explorer": {"testo": "(SCD_U x SDC_U x SDC_U) o MSC"},
        "tavola": E.procedura_in_dati(ProceduraGioco.da_identificatore(100, 0)),
        "riconoscimento": {"T": list(range(9, 27)) + list(range(9))},
        "successione": {"procedure": [E.procedura_in_dati(ProceduraGioco.da_identificatore(k, k % 8))
                                      for k in range(0, 216, 12)],
                        "mazzo_iniziale": None, "generatore": None},
    }
    doc = E.crea_documento(stato, seed=27, titolo="benchmark", nota="", presentazione=None,
                           cronologia=None, fonti=())
    with tempfile.TemporaryDirectory() as d:
        percorso = Path(d) / "e.json"
        archivio.salva_documento(doc, percorso)
        assert archivio.carica_documento(percorso).verificato


MISURE = (
    ("selftest", "selftest completo (1728 + 216 + 729 controlli)", _selftest),
    ("tavola_216", "216 righe della Tavola + tabellone", _tavola_216),
    ("riconoscimento", "48 permutazioni (24 di H, 24 casuali seed 27): separabilita', classe, somme", _riconoscimento),
    ("laboratorio_i6", "tutte le proprieta' del catalogo I6 su tutti i loro domini", _laboratorio_i6),
    ("esperimento_j", "documento J (4 strumenti, 18 procedure), salvataggio atomico, caricamento con ricalcolo", _esperimento_j),
)


def ambiente():
    try:
        import numpy
        numpy_v = numpy.__version__
    except ImportError:
        numpy_v = None
    return {"gioco27": gioco27.__version__, "python": platform.python_version(),
            "implementazione": platform.python_implementation(),
            "sistema": f"{platform.system()} {platform.release()}", "macchina": platform.machine(),
            "cpu": os.cpu_count(), "numpy": numpy_v}


def esegui():
    risultati = []
    for chiave, descrizione, f in MISURE:
        t0 = time.perf_counter()
        f()
        fredda = time.perf_counter() - t0
        calde = []
        for _ in range(RIPETIZIONI):
            t0 = time.perf_counter()
            f()
            calde.append(time.perf_counter() - t0)
        risultati.append({"misura": chiave, "descrizione": descrizione,
                          "fredda_s": round(fredda, 4), "calda_min_s": round(min(calde), 4)})
    return {"ambiente": ambiente(), "ripetizioni": RIPETIZIONI, "risultati": risultati}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    dati = esegui()
    if "--json" in argv:
        print(json.dumps(dati, ensure_ascii=False, indent=2))
        return 0
    a = dati["ambiente"]
    print(f"gioco27 {a['gioco27']} — Python {a['python']} ({a['implementazione']}), "
          f"{a['sistema']} {a['macchina']}, {a['cpu']} CPU, numpy {a['numpy']}")
    print(f"{'misura':16} {'fredda (s)':>11} {'calda min (s)':>14}  descrizione")
    for r in dati["risultati"]:
        print(f"{r['misura']:16} {r['fredda_s']:11.4f} {r['calda_min_s']:14.4f}  {r['descrizione']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
