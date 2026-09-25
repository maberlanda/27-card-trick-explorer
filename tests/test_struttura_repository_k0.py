"""Compartimento K0 — la struttura bonificata del repository resta tale.

Protegge: radice ordinata, documentazione classificata in `docs/`, nessun
artefatto generato versionato, un solo Tooltip, riferimenti correnti ai
documenti risolvibili, inventario macchina-leggibile completo, PDF
dell'utente mai versionati.
"""
import ast
import csv
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: cio' che ha senso al primo livello (K0). Un file nuovo in radice va
#: aggiunto qui con una ragione, o messo nella sua cartella.
RADICE_AMMESSA = {
    ".gitattributes", ".gitignore", "LICENSE", "README.md", "avvia.bat",
    "conftest.py", "controlla_requisiti.py", "docs", "gioco27", "gioco27.py",
    "pyproject.toml", "requirements-dev.txt", "requirements.txt", "tests",
    "gioco27.spec",        # K (N04): ricetta PyInstaller ufficiale, versionata
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
                and p != "README.md"]
    chiusure = [p for p in tracciati if p.endswith("_CLOSED.md")]
    assert chiusure and all(p.startswith("docs/history/") for p in chiusure)
    for p in tracciati:
        if p.startswith("docs/"):
            assert p == "docs/README.md" or p.split("/")[1] in {
                "history", "decisions", "audits", "release"}, p


def test_nessun_artefatto_generato_versionato(tracciati):
    vietati = re.compile(r"(__pycache__/|\.py[cod]$|^build/|^dist/|\.egg-info/|"
                         r"\.pytest_cache/|\.coverage|\.parziale$|~$|\.bak$|\.tmp$|\.log$)")
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


def test_inventario_completo(tracciati):
    percorso = ROOT / "docs" / "audits" / "K0_FILE_INVENTORY.csv"
    with percorso.open(encoding="utf-8", newline="") as f:
        righe = list(csv.DictReader(f))
    assert {"path", "category", "tracked", "action", "reason"} <= set(righe[0])
    inventariati = {r["path"] for r in righe}
    # Radice e docs/ devono essere sempre classificati; codice e test nuovi
    # si aggiungono all'inventario alla prossima revisione (audit finale).
    non_classificati = sorted(p for p in set(tracciati) - inventariati
                              if not p.startswith(("gioco27/", "tests/")))
    assert not non_classificati, non_classificati
    for r in righe:
        assert r["category"][:1] in "ABCDEFGHIJKLMNOPQ" and r["action"] in {
            "KEEP", "MOVE", "RENAME", "DELETE", "DEFER", "INVESTIGATE"}, r
        assert r["reason"].strip(), r["path"]
    assert {r["path"] for r in righe if r["category"].startswith("P")} == set(PDF_UTENTE)
