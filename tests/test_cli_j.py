"""Compartimento J — riga di comando batch, come processo reale e senza Tk."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from gioco27.services import esperimento as E

ROOT = Path(__file__).resolve().parents[1]


def _run(*args, cwd=None):
    env = {k: v for k, v in os.environ.items() if k != "DISPLAY"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    p = subprocess.run([sys.executable, "-B", "-m", "gioco27", *map(str, args)],
                       cwd=cwd or ROOT, env=env, capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout, p.stderr


def _json(*args):
    rc, out, err = _run(*args, "--json")
    return rc, json.loads(out.strip().splitlines()[-1])


@pytest.fixture
def esperimento(tmp_path):
    f = tmp_path / "seq.json"
    rc, out = _json("sequence", "--random", "12", "--seed", "7", "--out", f)
    assert rc == 0 and out["status"] == "OK" and out["result"]["seed"] == 7
    return f


def test_help_nelle_due_lingue():
    rc, out, _ = _run("--help")
    assert rc == 0 and "validate" in out and "senza interfaccia grafica" in out
    rc, out, _ = _run("validate", "--help", "--lang", "en")
    assert rc == 0 and "recomputation" in out


def test_versione_senza_stdout_per_eseguibile_gui(monkeypatch):
    from gioco27 import cli

    monkeypatch.setattr(sys, "stdout", None)
    assert cli.main(["--version"]) == 0


def test_validate_e_replay(esperimento):
    rc, out = _json("validate", esperimento)
    assert rc == 0 and out["status"] == "VERIFIED" and out["result"]["diagnosi"] == []
    rc, out = _json("replay", esperimento)
    assert rc == 0
    cammino = out["result"]["replay_inverso"]
    assert len(cammino) == 13 and cammino[-1] == list(range(27))


@pytest.mark.parametrize("guasto,rc_atteso,stato", [
    (lambda d: d["voci"][0]["risultato"].__setitem__("numero_cumulativo", -1), 4, "MISMATCH"),
    (lambda d: d["convenzioni"].__setitem__("versione", "J0"), 5, "INCOMPATIBLE_CONVENTION"),
    (lambda d: d.__setitem__("schema_version", 2), 6, "UNSUPPORTED_SCHEMA"),
    (lambda d: d.pop("digest"), 3, "CORRUPT"),
])
def test_exit_code_stabili(esperimento, tmp_path, guasto, rc_atteso, stato):
    d = json.loads(esperimento.read_text(encoding="utf-8"))
    guasto(d)
    f = tmp_path / "alterato.json"
    f.write_text(json.dumps(d), encoding="utf-8")
    rc, out = _json("validate", f)
    assert (rc, out["status"]) == (rc_atteso, stato)


def test_input_malformato(tmp_path):
    f = tmp_path / "rotto.json"
    f.write_text("{", encoding="utf-8")
    assert _json("validate", f)[0] == 3
    assert _json("validate", tmp_path / "manca.json")[0] == 3
    assert _json("recognize", "1", "2", "3")[0] == 3
    assert _json("sequence", "--random", "3")[0] == 3
    assert _json("sequence", "--proc", "300,0")[0] == 3
    assert _json("property", "inventata")[0] == 3
    assert _run("validate")[0] == 2                     # uso errato


def test_recognize_e_property(tmp_path):
    rc, out = _json("recognize", *range(9, 27), *range(9))
    assert rc == 0 and out["result"]["numero_tavola"] == 144      # C9
    rc, out = _json("property", "due_carte_forzabili", "--domain", "h",
                    "--out", tmp_path / "p.json")
    assert rc == 0 and out["result"]["risultato"]["esito"] == "falsa"
    assert _json("validate", tmp_path / "p.json")[0] == 0
    rc, out = _json("property", "--all", "--csv", tmp_path / "i6.csv")
    assert rc == 0 and len(out["result"]) >= 40
    manifesto = json.loads((tmp_path / "i6.csv.manifest.json").read_text(encoding="utf-8"))
    assert manifesto["sha256"] == E.sha256((tmp_path / "i6.csv").read_bytes())
    assert manifesto["convenzioni"]["versione"] == E.CONVENTION_VERSION


def test_sequence_export_e_compare(esperimento, tmp_path):
    for cosa in ("successione", "replay", "mapping"):
        out = tmp_path / f"{cosa}.csv"
        rc, js = _json("export", esperimento, "--csv", out, "--what", cosa)
        assert rc == 0 and out.exists() and js["result"]["contenuto"] == cosa
    assert _json("export", esperimento, "--csv", tmp_path / "x.csv", "--what", "proprieta")[0] == 3
    altro = tmp_path / "altro.json"
    _json("sequence", "--random", "12", "--seed", "7", "--out", altro)
    rc, js = _json("compare", esperimento, altro)
    assert rc == 0 and "SAME_SCIENTIFIC_CONTENT" in js["result"]["codici"]
    diverso = tmp_path / "diverso.json"
    _json("sequence", "--random", "12", "--seed", "8", "--out", diverso)
    rc, js = _json("compare", esperimento, diverso)
    assert "SAME_SCIENTIFIC_CONTENT" not in js["result"]["codici"]


def test_errore_di_scrittura(tmp_path):
    cartella = tmp_path / "cartella"
    cartella.mkdir()
    rc, js = _json("recognize", *range(27), "--out", cartella)
    assert rc == 7 and js["status"] == "WRITE_ERROR"


def test_selftest_integrato():
    rc, out, _ = _run("selftest")
    assert rc == 0
    rc2, out2, _ = _run("--selftest")
    assert rc2 == 0


def test_nessun_tk_e_nessuna_gui(esperimento):
    codice = ("import sys; from gioco27.cli import main; "
              f"rc = main(['validate', r'{esperimento}', '--json']); "
              "print('TK' if any(m.startswith(('tkinter', 'gioco27.gui')) for m in sys.modules) "
              "else 'NOTK', rc)")
    env = {k: v for k, v in os.environ.items() if k != "DISPLAY"}
    p = subprocess.run([sys.executable, "-B", "-c", codice], cwd=ROOT, env=env,
                       capture_output=True, text=True, timeout=120)
    assert p.stdout.strip().splitlines()[-1] == "NOTK 0"
    src = (ROOT / "gioco27" / "cli.py").read_text(encoding="utf-8")
    assert "tkinter" not in src and "from .gui" not in src


def test_sequence_proc_ripetuto_si_accumula(tmp_path):
    """`--proc` ripetuto accumula le Procedure invece di tenere solo l'ultima."""
    out = tmp_path / "succ.json"
    rc, js = _json("sequence", "--proc", "100,0", "--proc", "56,0", "17,5", "--out", out)
    assert rc == 0
    r = js["result"]["risultato"]
    assert r["passi"] == [100, 56, 11] and r["numero_cumulativo"] == 117
    rc, js = _json("validate", out)
    assert rc == 0 and js["status"] == "VERIFIED"
