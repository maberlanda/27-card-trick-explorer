"""
Controllo statico con pyflakes su tutto il package.

Due livelli:
  1. `test_no_undefined_names` — nessun «nome indefinito»: intercetta bug che
     né py_compile né i test funzionali (che non importano i moduli GUI,
     perché richiedono tkinter) riescono a vedere, ad esempio l'uso di
     `time.time()` senza aver importato `time`.
  2. `test_no_pyflakes_warnings` — zero warning pyflakes in assoluto
     (import inutilizzati, variabili morte, f-string senza placeholder...).
     Il codice è stato ripulito nella v2.8.0: questo test impedisce
     regressioni.

Usa pyflakes, che analizza il codice senza eseguirlo. Se pyflakes non è
installato i test vengono saltati.
"""
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGETS = [
    ROOT / "gioco27",
    ROOT / "tests",
    ROOT / "conftest.py",
    ROOT / "controlla_requisiti.py",
    ROOT / "gioco27.py",
]


def _run_pyflakes():
    pytest.importorskip("pyflakes")
    res = subprocess.run(
        [sys.executable, "-m", "pyflakes", *map(str, TARGETS)],
        capture_output=True, text=True,
    )
    return (res.stdout + res.stderr).splitlines()


def test_no_undefined_names():
    undefined = [line for line in _run_pyflakes() if "undefined name" in line]
    assert not undefined, "Nomi indefiniti rilevati:\n" + "\n".join(undefined)


def test_no_pyflakes_warnings():
    warnings = [line for line in _run_pyflakes() if line.strip()]
    assert not warnings, "Warning pyflakes rilevati:\n" + "\n".join(warnings)
