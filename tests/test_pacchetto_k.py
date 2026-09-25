"""Compartimento K — sdist/wheel costruite da una copia pulita e installazione
in un ambiente virtuale nuovo, usate da una cartella fuori dal checkout.

Costoso (build + due ambienti virtuali): richiede il modulo `build` (extra
`build`) e l'accesso all'indice dei pacchetti o a una cache locale. Senza
`build` i test sono saltati con il motivo; qualunque altro fallimento e' un
fallimento.
"""
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

import gioco27

ROOT = Path(__file__).resolve().parents[1]
VERSIONE = gioco27.__version__
WHEEL = f"gioco27-{VERSIONE}-py3-none-any.whl"
SDIST = f"gioco27-{VERSIONE}.tar.gz"
FIXTURE_313 = ROOT / "tests" / "fixtures" / "esperimento_j1_programma_3.1.3.json"
VIETATI = (".pdf", ".pyc", "__pycache__", ".pytest_cache", ".git/", ".egg-info/", "build/k")


def _esegui(args, **kw):
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    kw.setdefault("timeout", 900)
    return subprocess.run([str(a) for a in args], **kw)


def _file_tracciati():
    try:
        r = _esegui(["git", "ls-files", "-z"], cwd=ROOT, timeout=60)
    except (OSError, subprocess.SubprocessError):
        r = None
    if r is None or r.returncode != 0:
        return None
    return [p for p in r.stdout.split("\0") if p]


@pytest.fixture(scope="module")
def artefatti(tmp_path_factory):
    """sdist e wheel costruite da una copia dei soli file versionati."""
    import importlib.util
    spec = importlib.util.find_spec("build")
    # una cartella `build/` nella directory corrente sarebbe un namespace package vuoto
    if spec is None or spec.origin is None:
        pytest.skip("modulo 'build' non installato (extra build)")
    base = tmp_path_factory.mktemp("k_pacchetto")
    sorgente = base / "sorgente"
    tracciati = _file_tracciati()
    if tracciati is None:                       # sdist estratta: gia' pulita
        shutil.copytree(ROOT, sorgente, ignore=shutil.ignore_patterns(
            "*.pdf", "__pycache__", "*.pyc", "build", "dist", "*.egg-info", ".git"))
    else:
        for rel in tracciati:
            dest = sorgente / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dest)
    for pdf in ("LIBRO_MAIN.pdf", "Articolo.pdf"):
        assert not (sorgente / pdf).exists()
    dist = base / "dist"
    r = _esegui([sys.executable, "-m", "build", "--outdir", dist, sorgente], cwd=base,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-3000:]
    assert (dist / WHEEL).is_file() and (dist / SDIST).is_file(), os.listdir(dist)
    return dist


def _python_venv(cartella):
    sub = "Scripts" if os.name == "nt" else "bin"
    return cartella / sub / ("python.exe" if os.name == "nt" else "python"), cartella / sub


def _crea_ambiente(cartella, requisito):
    """Ambiente virtuale nuovo con la sola wheel (+ dipendenze dichiarate)."""
    uv = shutil.which("uv")
    if uv:
        r = _esegui([uv, "venv", "-q", "--python", sys.executable, cartella])
        assert r.returncode == 0, r.stderr
        py, _ = _python_venv(cartella)
        r = _esegui([uv, "pip", "install", "-q", "--python", py, requisito])
    else:
        r = _esegui([sys.executable, "-m", "venv", cartella])
        assert r.returncode == 0, r.stderr
        py, _ = _python_venv(cartella)
        r = _esegui([py, "-m", "pip", "install", "-q", "--disable-pip-version-check", requisito])
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    return _python_venv(cartella)


def _ambiente_isolato():
    env = {k: v for k, v in os.environ.items()
           if k not in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "PYTHONSTARTUP")}
    env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    return env


@pytest.fixture(scope="module")
def installato(artefatti, tmp_path_factory):
    """(python, bin, cwd): wheel senza extra, usata da una cartella qualsiasi."""
    base = tmp_path_factory.mktemp("k_venv_minimo")
    py, binari = _crea_ambiente(base / "venv", str(artefatti / WHEEL))
    lavoro = base / "altrove"
    lavoro.mkdir()
    return py, binari, lavoro


def _nel_venv(installato, *args):
    py, _binari, lavoro = installato
    return _esegui([py, "-B", *args], cwd=lavoro, env=_ambiente_isolato())


# ───────────────────────────── contenuto ─────────────────────────────────────

def test_contenuto_della_wheel(artefatti):
    with zipfile.ZipFile(artefatti / WHEEL) as z:
        nomi = z.namelist()
        meta = z.read(f"gioco27-{VERSIONE}.dist-info/METADATA").decode("utf-8")
        punti = z.read(f"gioco27-{VERSIONE}.dist-info/entry_points.txt").decode("utf-8")
    assert not [n for n in nomi if any(v in n for v in VIETATI)]
    assert not [n for n in nomi if n.split("/")[0] not in ("gioco27", f"gioco27-{VERSIONE}.dist-info")]
    for atteso in ("gioco27/__init__.py", "gioco27/cli.py", "gioco27/i18n.py",
                   "gioco27/assets/DejaVuSans.ttf", "gioco27/assets/DejaVuSans-Bold.ttf",
                   "gioco27/assets/LICENSE-DejaVu.txt",
                   f"gioco27-{VERSIONE}.dist-info/licenses/LICENSE",
                   f"gioco27-{VERSIONE}.dist-info/licenses/gioco27/assets/LICENSE-DejaVu.txt"):
        assert atteso in nomi, atteso
    moduli = {p.relative_to(ROOT).as_posix() for p in (ROOT / "gioco27").rglob("*.py")}
    assert moduli <= set(nomi), moduli - set(nomi)
    assert f"Version: {VERSIONE}" in meta and "License-Expression: GPL-3.0-only" in meta
    assert "Requires-Python: >=3.10" in meta and "Proprietary" not in meta
    assert "Requires-Dist: numpy>=1.21" in meta
    assert "gioco27-cli = gioco27.cli:main_console" in punti
    assert "gioco27 = gioco27.__main__:main" in punti
    assert "/home/" not in meta and "/sessions/" not in meta


def test_contenuto_della_sdist(artefatti):
    with tarfile.open(artefatti / SDIST) as t:
        nomi = [n.split("/", 1)[1] for n in t.getnames() if "/" in n]
    assert not [n for n in nomi if any(v in n for v in VIETATI if v != ".egg-info/")]
    for atteso in ("pyproject.toml", "README.md", "LICENSE", "MANIFEST.in", "gioco27.spec",
                   "gioco27.py", "avvia.bat", "controlla_requisiti.py", "conftest.py",
                   "requirements.txt", "requirements-dev.txt",
                   "gioco27/assets/LICENSE-DejaVu.txt", "gioco27/assets/DejaVuSans.ttf",
                   "tests/fixtures/esperimento_j1_programma_3.1.3.json",
                   "docs/README.md", "docs/audits/V4_COVERAGE_MATRIX.csv"):
        assert atteso in nomi, atteso
    assert not [n for n in nomi if n.startswith((".github", "build/", "dist/"))]


# ───────────────────────── installazione pulita ──────────────────────────────

def test_import_dall_installazione_non_dal_checkout(installato):
    py, _binari, _lavoro = installato
    r = _nel_venv(installato, "-c",
                  "import gioco27, sys; print(gioco27.__version__); print(gioco27.__file__); "
                  "print(sys.prefix)")
    assert r.returncode == 0, r.stderr
    versione, file_, prefisso = r.stdout.strip().splitlines()
    assert versione == VERSIONE
    assert Path(file_).resolve().is_relative_to(Path(prefisso).resolve())
    assert not Path(file_).resolve().is_relative_to(ROOT.resolve())


@pytest.mark.parametrize("ottimizzato", [False, True])
def test_selftest_installato(installato, ottimizzato):
    args = (["-O"] if ottimizzato else []) + ["-m", "gioco27", "--selftest"]
    r = _nel_venv(installato, *args)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "TUTTO OK" in r.stdout and f"v{VERSIONE}" in r.stdout


def test_entry_point_installati(installato):
    py, binari, lavoro = installato
    env = _ambiente_isolato()
    suff = ".exe" if os.name == "nt" else ""
    cli = binari / f"gioco27-cli{suff}"
    gui = binari / f"gioco27{suff}"
    assert cli.exists() and gui.exists()
    for comando in ([cli, "--version"], [gui, "--version"], [py, "-m", "gioco27", "--version"]):
        r = _esegui(comando, cwd=lavoro, env=env)
        assert r.returncode == 0 and r.stdout.strip() == f"gioco27 {VERSIONE}", (comando, r.stderr)
    for lingua in ("it", "en"):
        r = _esegui([cli, "--help", "--lang", lingua], cwd=lavoro, env=env)
        assert r.returncode == 0 and "validate" in r.stdout, r.stderr
    r = _esegui([cli, "selftest", "--json"], cwd=lavoro, env=env)
    assert r.returncode == 0 and json.loads(r.stdout)["status"] == "OK", r.stdout + r.stderr


def test_cli_installata_riconoscimento_ed_esperimenti(installato):
    py, binari, lavoro = installato
    env = _ambiente_isolato()
    cli = binari / ("gioco27-cli.exe" if os.name == "nt" else "gioco27-cli")
    # riconoscimento semplice: l'identita' e' la riga #0 della Tavola (in H)
    r = _esegui([cli, "recognize", *map(str, range(27)), "--json"], cwd=lavoro, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    ris = json.loads(r.stdout)["result"]
    assert ris["separabile"] is True and ris["numero_tavola"] == 0
    # esperimento minimale: successione, salvataggio, verifica con ricalcolo
    out = lavoro / "succ.json"
    r = _esegui([cli, "sequence", "--proc", "100,0", "56,0", "--out", out, "--json"],
                cwd=lavoro, env=env)
    assert r.returncode == 0 and out.is_file(), r.stdout + r.stderr
    r = _esegui([cli, "validate", out, "--json"], cwd=lavoro, env=env)
    assert r.returncode == 0 and json.loads(r.stdout)["status"] == "VERIFIED"
    # un esperimento salvato dalla 3.1.3 si carica e si verifica
    copia = lavoro / FIXTURE_313.name
    shutil.copy2(FIXTURE_313, copia)
    r = _esegui([cli, "validate", copia, "--json"], cwd=lavoro, env=env)
    assert r.returncode == 0 and json.loads(r.stdout)["status"] == "VERIFIED", r.stdout
    r = _esegui([cli, "export", copia, "--csv", lavoro / "succ.csv", "--what", "successione"],
                cwd=lavoro, env=env)
    assert r.returncode == 0 and (lavoro / "succ.csv.manifest.json").is_file(), r.stderr


def test_senza_facoltative_la_diagnosi_e_esplicita(installato):
    codice = (
        "import os\n"
        "from gioco27.core.combinations import generate_pdf\n"
        "from gioco27.gui.errori import per_utente\n"
        "f=[dict(p0='SCD_U',p1='SCD_U',p2='SCD_U',j0='I_3',j1='I_3',j2='I_3') for _ in range(3)]\n"
        "try:\n"
        "    generate_pdf('x.pdf', f)\n"
        "except ImportError as e:\n"
        "    print(per_utente(e)[1].splitlines()[0]); print(os.path.exists('x.pdf'))\n")
    r = _nel_venv(installato, "-c", codice)
    if r.returncode != 0 and "tkinter" in r.stderr:
        pytest.skip("interprete senza tkinter: gui.errori non importabile")
    assert r.returncode == 0, r.stderr
    assert "reportlab" in r.stdout and r.stdout.strip().endswith("False")


def test_export_da_installazione_completa(artefatti, tmp_path_factory):
    base = tmp_path_factory.mktemp("k_venv_export")
    py, _binari = _crea_ambiente(base / "venv", f"{artefatti / WHEEL}[export]")
    lavoro = base / "altrove"
    lavoro.mkdir()
    codice = (
        "from gioco27.core.combinations import generate_pdf, generate_pdf_ex\n"
        "from gioco27.core.detail_pdf import generate_detail_pdf, _ensure_fonts\n"
        "from gioco27.core.export_combinazioni import write_csv\n"
        "from gioco27.core.export_analisi import scrivi_excel\n"
        "f=[dict(p0='SCD_U',p1='SCD_U',p2='SCD_U',j0='I_3',j1='I_3',j2='I_3') for _ in range(3)]\n"
        "f[0]['j0']='*'\n"
        "print(write_csv('c.csv', f), generate_pdf('a.pdf', f), generate_pdf_ex('b.pdf', f),\n"
        "      generate_detail_pdf('d.pdf', f))\n"
        "scrivi_excel([], 'e.xlsx')\n"
        "print(_ensure_fonts()[0])\n"
        "print(all(open(n,'rb').read(5)==b'%PDF-' for n in ('a.pdf','b.pdf','d.pdf')))\n")
    r = _esegui([py, "-B", "-c", codice], cwd=lavoro, env=_ambiente_isolato())
    assert r.returncode == 0, r.stdout + r.stderr
    righe = r.stdout.strip().splitlines()
    assert righe[0] == "2 2 2 2" and righe[1] == "DejaVuSans" and righe[2] == "True", righe
    assert (lavoro / "e.xlsx").is_file()
