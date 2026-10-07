"""Compartimento K — metadati, licenze, versione, dipendenze e ricette di build.

Test statici e veloci (nessuna build): la costruzione degli artefatti e
l'installazione pulita sono in `test_pacchetto_k.py`.
"""
import ast
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

import pytest

import gioco27

ROOT = Path(__file__).resolve().parents[1]
VERSIONE = "4.0.2"
PDF_FONTE = ("LIBRO_MAIN.pdf", "Articolo.pdf")
FIXTURE_313 = ROOT / "tests" / "fixtures" / "esperimento_j1_programma_3.1.3.json"


def _pyproject():
    try:
        import tomllib
    except ImportError:                      # Python 3.10
        tomllib = pytest.importorskip("tomli")
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


# ─────────────────────────────── versione ────────────────────────────────────

def test_versione_unica_4_0_0():
    assert gioco27.__version__ == VERSIONE
    progetto = _pyproject()["project"]
    assert "version" not in progetto and "version" in progetto["dynamic"]
    attr = _pyproject()["tool"]["setuptools"]["dynamic"]["version"]["attr"]
    assert attr == "gioco27.__init__.__version__"
    # nessun'altra costante di versione scritta a mano nel package. Il controllo
    # e' sul codice (AST), non sul testo: commenti e docstring possono citare
    # la 4.0.0 come fatto storico (per esempio le note di migrazione della
    # Fase P) senza essere una seconda definizione della versione.
    for p in (ROOT / "gioco27").rglob("*.py"):
        if p.name == "__init__.py" and p.parent.name == "gioco27":
            continue
        assert _letterali_di_versione(p.read_text(encoding="utf-8")) == [], p


def _letterali_di_versione(sorgente):
    """Assegnazioni a `__version__` e letterali di codice uguali alla versione.

    Esclusi solo i commenti (assenti dall'AST) e le docstring di modulo,
    classe e funzione; restano vietati costanti, valori di dizionari,
    argomenti e f-string che contengano la versione.
    """
    albero = ast.parse(sorgente)
    docstring = set()
    for nodo in ast.walk(albero):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and nodo.body:
            primo = nodo.body[0]
            if (isinstance(primo, ast.Expr) and isinstance(primo.value, ast.Constant)
                    and isinstance(primo.value.value, str)):
                docstring.add(id(primo.value))
    trovati = []
    for nodo in ast.walk(albero):
        if isinstance(nodo, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            bersagli = nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
            for b in bersagli:
                for n in ast.walk(b):
                    if (isinstance(n, ast.Name) and n.id == "__version__") or (
                            isinstance(n, ast.Attribute) and n.attr == "__version__"):
                        trovati.append(("__version__", nodo.lineno))
        if (isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)
                and id(nodo) not in docstring and VERSIONE in nodo.value):
            trovati.append((nodo.value, nodo.lineno))
    return trovati


def test_il_controllo_di_versione_distingue_codice_e_commenti():
    """Il controllo vieta le definizioni, non le citazioni."""
    v = VERSIONE
    assert _letterali_di_versione('# Fino alla %s RC2 ...\nx = 1\n' % v) == []
    assert _letterali_di_versione('"""Nota: dalla %s."""\n' % v) == []
    assert _letterali_di_versione('def f():\n    """%s"""\n' % v) == []
    assert _letterali_di_versione('__version__ = "x"\n')
    assert _letterali_di_versione('VERSIONE = "%s"\n' % v)
    assert _letterali_di_versione('d = {"versione": "%s"}\n' % v)
    assert _letterali_di_versione('print(f"gioco27 %s")\n' % v)


def test_superfici_della_versione():
    r = subprocess.run([sys.executable, "-B", "-m", "gioco27", "--version"], cwd=ROOT,
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and r.stdout.strip() == f"gioco27 {VERSIONE}"
    from gioco27.services import esperimento as E
    doc = E.crea_documento({}, seed=None, titolo="", nota="", presentazione=None,
                           cronologia=None, fonti=())
    assert doc["programma"] == {"nome": "gioco27", "versione": VERSIONE}
    from gioco27.gui.guide import render_guide_segments
    assert f"gioco27 v{VERSIONE}" in "".join(t for _k, t in render_guide_segments("it"))


# ─────────────────────────────── licenze ─────────────────────────────────────

def test_licenza_del_programma_coerente():
    progetto = _pyproject()["project"]
    assert progetto["license"] == "GPL-3.0-only"
    assert "LICENSE" in progetto["license-files"]
    testo = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in testo and "Version 3, 29 June 2007" in testo
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "GNU General Public License v3.0" in readme
    for f in ("pyproject.toml", "README.md", "gioco27.spec"):
        assert "Proprietary" not in (ROOT / f).read_text(encoding="utf-8"), f
    assert not [c for c in progetto.get("classifiers", []) if c.startswith("License ::")]


def _nome_font(percorso, nid):
    b = percorso.read_bytes()
    n = struct.unpack(">H", b[4:6])[0]
    for i in range(n):
        tag, _cs, off, _ln = struct.unpack(">4sIII", b[12 + 16 * i:28 + 16 * i])
        if tag == b"name":
            break
    _fmt, count, so = struct.unpack(">HHH", b[off:off + 6])
    for i in range(count):
        pid, eid, lid, x, lung, o = struct.unpack(">HHHHHH", b[off + 6 + 12 * i:off + 18 + 12 * i])
        if (pid, eid, lid, x) == (3, 1, 0x409, nid):
            return b[off + so + o:off + so + o + lung].decode("utf-16-be")
    raise AssertionError(f"nameID {nid} assente in {percorso.name}")


def test_licenza_dei_font_e_quella_incorporata_nei_font():
    """LICENSE-DejaVu.txt riporta alla lettera la licenza scritta nei font."""
    assets = ROOT / "gioco27" / "assets"
    fonts = sorted(assets.glob("*.ttf"))
    assert [f.name for f in fonts] == ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]
    licenza = (assets / "LICENSE-DejaVu.txt").read_text(encoding="utf-8")
    for f in fonts:
        assert _nome_font(f, 13).replace("\r\n", "\n").strip() in licenza, f.name
        assert _nome_font(f, 0).strip() in licenza, f.name
    assert "gioco27/assets/LICENSE-DejaVu.txt" in _pyproject()["project"]["license-files"]
    dati = _pyproject()["tool"]["setuptools"]["package-data"]["gioco27"]
    assert "assets/LICENSE-DejaVu.txt" in dati and "assets/*.ttf" in dati


# ───────────────────────────── dipendenze ────────────────────────────────────

def _requisiti(nome):
    righe = (ROOT / nome).read_text(encoding="utf-8").splitlines()
    return {re.split(r"[<>=!~ ;#]", r.strip())[0].lower()
            for r in righe if r.strip() and not r.strip().startswith(("#", "-r"))}


def test_dipendenze_coerenti():
    progetto = _pyproject()["project"]
    extra = progetto["optional-dependencies"]
    nomi = lambda voci: {re.split(r"[<>=!~ ;\[]", v)[0].lower() for v in voci}
    assert nomi(progetto["dependencies"]) == {"numpy"}
    assert nomi(extra["export"]) == {"reportlab", "openpyxl", "pypdf", "pikepdf"}
    assert nomi(extra["test"]) == {"pytest", "pyflakes", "pypdfium2", "pillow", "tomli"}
    assert nomi(extra["build"]) == {"build", "pyinstaller"}
    assert extra["dev"] == ["gioco27[export,test,build]"]
    assert _requisiti("requirements.txt") == nomi(progetto["dependencies"]) | nomi(extra["export"])
    assert _requisiti("requirements-dev.txt") == nomi(extra["test"]) | nomi(extra["build"])
    assert "-r requirements.txt" in (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    # tkinter e' della distribuzione Python, non una wheel
    assert "tkinter" not in json.dumps(progetto).lower()


def test_ogni_import_esterno_e_dichiarato():
    """Nessuna dipendenza importata e non dichiarata, nessuna dichiarata e morta."""
    progetto = _pyproject()["project"]
    extra = progetto["optional-dependencies"]
    modulo_di = {"pillow": "PIL", "pyinstaller": "PyInstaller"}
    dichiarate = {modulo_di.get(n, n) for n in
                  {re.split(r"[<>=!~ ;\[]", v)[0] for v in
                   progetto["dependencies"] + extra["export"] + extra["test"] + extra["build"]}
                  if n != "gioco27"}
    std = set(getattr(sys, "stdlib_module_names", ())) or pytest.skip("Python < 3.10")
    std.add("tomllib")                       # stdlib da 3.11; su 3.10 si usa tomli
    importati = set()
    sorgenti = list((ROOT / "gioco27").rglob("*.py")) + list((ROOT / "tests").glob("*.py"))
    for p in sorgenti:
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Import):
                importati |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                importati.add(n.module.split(".")[0])
            elif (isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "importorskip"
                  and n.args and isinstance(n.args[0], ast.Constant)):
                importati.add(n.args[0].value.split(".")[0])
    esterni = importati - std - {"gioco27", "conftest"}
    assert esterni - dichiarate == set(), esterni - dichiarate
    # 'build' e PyInstaller servono agli strumenti, non al codice
    assert dichiarate - esterni <= {"build", "PyInstaller", "PIL"}, dichiarate - esterni


def test_requires_python_e_diagnostica_allineati():
    rp = _pyproject()["project"]["requires-python"]
    assert rp == ">=3.10"
    src = (ROOT / "controlla_requisiti.py").read_text(encoding="utf-8")
    assert "PYTHON_MINIMO = (3, 10)" in src


def test_controlla_requisiti_non_e_fatale_per_gli_opzionali(monkeypatch, capsys):
    import importlib.util
    spec = importlib.util.spec_from_file_location("controlla_requisiti", ROOT / "controlla_requisiti.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    reale = mod._prova
    monkeypatch.setattr(mod, "_prova", lambda imp: None if imp in (
        "reportlab", "openpyxl", "pypdf", "pikepdf", "pytest", "build") else reale(imp))
    if reale("tkinter") is None or reale("numpy") is None:
        pytest.skip("ambiente senza tkinter o numpy")
    assert mod.main(["--dev"]) == 0
    monkeypatch.setattr(mod, "_prova", lambda imp: None if imp == "numpy" else reale(imp))
    assert mod.main([]) == 1
    assert "pip install numpy" in capsys.readouterr().out


# ─────────────────────── ricetta PyInstaller e launcher ──────────────────────

def test_spec_pyinstaller_versionata_e_pulita():
    try:
        tracciati = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                                   text=True, timeout=60).stdout.split()
    except (OSError, subprocess.SubprocessError):
        tracciati = None
    if tracciati:
        assert "gioco27.spec" in tracciati
        ignorati = subprocess.run(["git", "check-ignore", "-q", "gioco27.spec"], cwd=ROOT,
                                  timeout=60).returncode
        assert ignorati == 1, "gioco27.spec non deve essere ignorato"
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "*.spec" in gi and "!/gioco27.spec" in gi
    spec = (ROOT / "gioco27.spec").read_text(encoding="utf-8")
    ast.parse(spec)
    assert not re.search(r"[A-Za-z]:\\\\|/home/|/Users/|/sessions/|C:/", spec)
    assert "SPECPATH" in spec and '_qui("gioco27.py")' in spec
    assert '_qui("gioco27", "assets")' in spec and '_qui("LICENSE")' in spec
    assert ".pdf" not in spec.replace("I PDF fonte (LIBRO_MAIN.pdf, Articolo.pdf) NON", "")
    for dip in ("reportlab", "openpyxl", "pypdf", "pikepdf"):
        assert f'"{dip}"' in spec
    lanciatore = (ROOT / "gioco27.py").read_text(encoding="utf-8")
    assert "freeze_support()" in lanciatore and "from gioco27.__main__ import main" in lanciatore


def test_avvia_bat_robusto():
    b = (ROOT / "avvia.bat").read_bytes()
    testo = b.decode("ascii")
    assert "py -3" in testo and testo.index("py -3") < testo.index('python -c')
    assert "sys.version_info >= (3, 10)" in testo
    assert "controlla_requisiti.py" in testo and 'cd /d "%~dp0"' in testo
    assert not re.search(r"[A-Za-z]:\\\\(Users|Python|Program)", testo)
    assert "*.bat text eol=crlf" in (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for et in re.findall(r"goto :(\w+)", testo):
        assert re.search(rf"(?m)^:{et}\s*$", testo), et


# ─────────────────────────────── DP12 e sdist ────────────────────────────────

def test_pdf_fonte_esclusi_da_ogni_ricetta():
    manifesto = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert "global-exclude *.pdf" in manifesto
    dati = json.dumps(_pyproject()["tool"]["setuptools"])
    assert ".pdf" not in dati
    for nome in PDF_FONTE:
        assert nome not in (ROOT / "gioco27.spec").read_text(encoding="utf-8").split("NON")[-1]


# ────────────────────────── J: esperimenti 3.1.3 ─────────────────────────────

def test_esperimento_salvato_da_3_1_3_si_carica_in_4_0_0(tmp_path):
    from gioco27.services import esperimento as E
    from gioco27.services.sessione import SessioneLavoro
    testo = FIXTURE_313.read_text(encoding="utf-8")
    doc = json.loads(testo)
    assert doc["programma"]["versione"] == "3.1.3"
    assert doc["schema_version"] == E.SCHEMA_VERSION and doc["convenzioni"]["versione"] == "J1"
    r = E.verifica_testo(testo)
    assert r.stato is E.Stato.VERIFIED, r.diagnosi
    sessione, r = SessioneLavoro.carica(FIXTURE_313)
    assert sessione is not None and r.stato is E.Stato.VERIFIED
    assert len(doc["voci"]) == 6
    nuovo = sessione.documento()
    assert nuovo["programma"]["versione"] == VERSIONE
    confronto = E.confronta(doc, nuovo)
    assert "DIFFERENT_PROGRAM_VERSION" in confronto.codici
    assert "SAME_SCIENTIFIC_CONTENT" in confronto.codici
    assert "RESULT_MISMATCH" not in confronto.codici
