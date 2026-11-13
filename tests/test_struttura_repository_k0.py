"""Compartimento K0 — la struttura bonificata del repository resta tale.

Protegge: radice ordinata, documentazione classificata in `docs/`, nessun
artefatto generato versionato, un solo Tooltip, riferimenti correnti ai
documenti risolvibili, archivio storico separato, PDF
dell'utente mai versionati.
"""
import ast
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: cio' che ha senso al primo livello (K0). Un file nuovo in radice va
#: aggiunto qui con una ragione, o messo nella sua cartella.
RADICE_AMMESSA = {
    ".gitattributes", ".gitignore", "CONTRIBUTORS.md", "LICENSE", "README.md", "avvia.bat",
    "conftest.py", "controlla_requisiti.py", "docs", "gioco27", "gioco27.py", "tools",
    "pyproject.toml", "requirements-dev.txt", "requirements.txt", "tests",
    "gioco27.spec",        # K (N04): ricetta PyInstaller ufficiale, versionata
    "MANIFEST.in",         # K: contenuto esplicito della sdist
    ".github",             # K: workflow di CI
}
PDF_UTENTE = ("Articolo.pdf", "LIBRO_MAIN.pdf")


def _git(*args):
    try:
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        pytest.skip("git non disponibile")
    if r.returncode != 0:
        pytest.skip("non e' un checkout git")
    return r.stdout.splitlines()


@pytest.fixture(scope="module")
def tracciati():
    return _git("ls-files")


def test_radice_ordinata(tracciati):
    primo_livello = {p.split("/")[0] for p in tracciati}
    assert primo_livello <= RADICE_AMMESSA, sorted(primo_livello - RADICE_AMMESSA)


def test_documentazione_classificata(tracciati):
    assert not [p for p in tracciati if "/" not in p and p.endswith((".md", ".csv"))
                and p not in {"CONTRIBUTORS.md", "README.md"}]
    documenti = {p for p in tracciati if p.startswith("docs/")}
    corrente = ("docs/audits/", "docs/decisions/", "docs/release/")
    archivio = ("docs/archive/audits/", "docs/archive/compartments/", "docs/archive/releases/")
    indici = {"docs/README.md", "docs/archive/README.md"}
    assert indici <= documenti
    assert all(p in indici or p.startswith(corrente + archivio) for p in documenti)
    assert all(p.startswith(archivio) for p in documenti if p.endswith("_CLOSED.md"))
    assert all(p.startswith(archivio) for p in documenti if p.endswith("K0_FILE_INVENTORY.csv"))


def test_nessun_artefatto_generato_versionato(tracciati):
    vietati = re.compile(r"(__pycache__/|\.py[cod]$|^build/|^dist/|\.egg-info/|"
                         r"^\.local-archive/|^tree\.txt$|\.pytest_cache/|\.coverage|"
                         r"\.parziale$|~$|\.bak$|\.tmp$|\.log$)")
    assert not [p for p in tracciati if vietati.search(p)]


def test_pdf_utente_mai_versionati(tracciati):
    assert not set(PDF_UTENTE) & set(tracciati)


def test_una_sola_classe_tooltip():
    definizioni = [p.relative_to(ROOT).as_posix() for p in (ROOT / "gioco27").rglob("*.py")
                   if any(isinstance(n, ast.ClassDef) and n.name == "Tooltip"
                          for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))))]
    assert definizioni == ["gioco27/gui/tooltip.py"]


def test_riferimenti_correnti_ai_documenti_esistono():
    """Ogni `docs/…` citato da codice, test, README o indice esiste."""
    sorgenti = list((ROOT / "gioco27").rglob("*.py")) + list((ROOT / "tests").glob("*.py"))
    sorgenti += [ROOT / "README.md", ROOT / "docs" / "README.md"]
    citati = set()
    for s in sorgenti:
        citati |= set(re.findall(r"docs/[A-Za-z0-9_./-]+\.(?:md|csv)", s.read_text(encoding="utf-8")))
    citati.discard("docs/…")
    mancanti = sorted(c for c in citati if not (ROOT / c).is_file()
                      and not (ROOT / "docs" / c[len("docs/"):]).is_file())
    assert citati and not mancanti, mancanti


def test_collegamenti_relativi_della_documentazione():
    mancanti = []
    for doc in [ROOT / "README.md", *(ROOT / "docs").rglob("*.md")]:
        for destinazione in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
            percorso = destinazione.split("#", 1)[0]
            if percorso and "://" not in percorso and not (doc.parent / percorso).exists():
                mancanti.append((doc.relative_to(ROOT).as_posix(), percorso))
    assert not mancanti, mancanti
