"""B09 — la diagnostica del dominio non deve dipendere da `assert`.

`selftest()` confrontava i suoi invarianti con `assert`: con `python -O` quelle
istruzioni spariscono e la funzione dichiara «TUTTO OK» anche su dati sbagliati.
Qui la stessa iniezione di guasto viene eseguita in due sottoprocessi reali, uno
normale e uno ottimizzato: l'esito diagnostico deve essere identico.

Il sottoprocesso serve perche' `-O` e' una proprieta' dell'interprete, non del
singolo modulo: non e' un rimedio applicativo ma il modo corretto di osservare
il difetto.
"""
import os
import pathlib
import subprocess
import sys

import pytest

RADICE = pathlib.Path(__file__).resolve().parents[1]

PROGRAMMA = """
import sys
sys.path.insert(0, {radice!r})
from gioco27.core import gioco_reale as gr

print("OPTIMIZE", sys.flags.optimize)
if {inietta!r}:
    # simulazione fisica guasta: ogni partita "finisce" con tutte le carte in 0
    gr.T_da_partita = lambda *a, **k: [0] * 27
try:
    rapporto = gr.selftest(completo=False)
    print("ESITO", rapporto["esito"])
except AssertionError as exc:
    print("ERRORE", type(exc).__name__, str(exc))
"""


def _esegui(ottimizzato, inietta):
    cmd = [sys.executable]
    if ottimizzato:
        cmd.append("-O")
    cmd += ["-c", PROGRAMMA.format(radice=str(RADICE), inietta=inietta)]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
    assert res.returncode == 0, res.stderr
    righe = dict(r.split(" ", 1) for r in res.stdout.strip().splitlines() if " " in r)
    return righe


@pytest.mark.parametrize("ottimizzato", [False, True])
def test_selftest_integro_supera_in_entrambe_le_modalita(ottimizzato):
    out = _esegui(ottimizzato, inietta=False)
    assert out["OPTIMIZE"] == ("1" if ottimizzato else "0")
    assert out["ESITO"] == "TUTTO OK"
    assert "ERRORE" not in out


@pytest.mark.parametrize("ottimizzato", [False, True])
def test_selftest_rileva_il_guasto_anche_con_O(ottimizzato):
    """Regressione di B09: con -O il guasto veniva ignorato e l'esito era TUTTO OK."""
    out = _esegui(ottimizzato, inietta=True)
    assert out["OPTIMIZE"] == ("1" if ottimizzato else "0")
    assert "ESITO" not in out, "il selftest ha dichiarato successo su dati guasti"
    assert out["ERRORE"].startswith("VerificaFallita ")


def test_verifica_fallita_resta_compatibile_con_i_chiamanti():
    """La GUI intercetta AssertionError: il contratto non deve cambiare."""
    from gioco27.core.gioco_reale import VerificaFallita

    assert issubclass(VerificaFallita, AssertionError)


def test_selftest_non_usa_piu_assert():
    """Nessuna istruzione `assert` deve restare nel modulo diagnostico."""
    import ast

    sorgente = (RADICE / "gioco27" / "core" / "gioco_reale.py").read_text(encoding="utf-8")
    albero = ast.parse(sorgente)
    assert [n for n in ast.walk(albero) if isinstance(n, ast.Assert)] == []


def test_messaggi_diagnostici_invariati(monkeypatch):
    """Il significato del selftest non cambia: stesse chiavi, stessi messaggi."""
    from gioco27.core import gioco_reale as gr

    originale = gr.riga_tavola

    def rotta(n):
        r = dict(originale(n))
        if n == 100:
            r["assi"] = (0, 0, 0)
        return r

    monkeypatch.setattr(gr, "riga_tavola", rotta)
    with pytest.raises(AssertionError) as info:
        gr.selftest(completo=False)
    assert str(info.value) == "ancora #100"
