"""Compartimento J — confini architetturali dei moduli nuovi.

core → services/gui = 0, services → gui/tkinter = 0, persistenza e CLI
senza Tk, nessun ciclo di import nel pacchetto, un solo parser.
"""
import ast
import subprocess
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
PACCHETTO = RADICE / "gioco27"
NUOVI = ("services/successione.py", "services/esperimento.py", "services/archivio.py",
         "services/cronologia.py", "services/sessione.py", "cli.py", "gui/sessione_tab.py")


def _modulo(p):
    parti = list(p.relative_to(RADICE).with_suffix("").parts)
    if parti[-1] == "__init__":
        parti.pop()
    return ".".join(parti)


def _importati(p):
    albero = ast.parse(p.read_text(encoding="utf-8"))
    base = _modulo(p).split(".")
    if p.name != "__init__.py":
        base = base[:-1]
    out = set()
    for n in ast.walk(albero):
        if isinstance(n, ast.Import):
            out.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                radice = base[:len(base) - n.level + 1]
                nome = ".".join(radice + ([n.module] if n.module else []))
            else:
                nome = n.module or ""
            out.add(nome)
            out.update(f"{nome}.{a.name}" for a in n.names)
    return out


def _grafo():
    moduli = {_modulo(p): p for p in PACCHETTO.rglob("*.py")}
    return {m: {i for i in _importati(p) if i in moduli and i != m} for m, p in moduli.items()}


def test_i_moduli_nuovi_esistono():
    for rel in NUOVI:
        assert (PACCHETTO / rel).is_file(), rel


def test_confini_dei_livelli():
    for m, dip in _grafo().items():
        if m.startswith("gioco27.core"):
            assert not {d for d in dip if d.startswith(("gioco27.services", "gioco27.gui"))}, m
        if m.startswith("gioco27.services") or m == "gioco27.cli":
            assert not {d for d in dip if d.startswith("gioco27.gui")}, m
    for p in list((PACCHETTO / "services").rglob("*.py")) + [PACCHETTO / "cli.py"]:
        assert not {i for i in _importati(p) if i.split(".")[0] == "tkinter"}, p


def test_nessun_ciclo_di_import():
    grafo = _grafo()
    colore = {}

    def visita(m, pila):
        colore[m] = 1
        for d in grafo[m]:
            if colore.get(d) == 1:
                raise AssertionError(" → ".join(pila + [m, d]))
            if d not in colore:
                visita(d, pila + [m])
        colore[m] = 2

    for m in grafo:
        if m not in colore:
            visita(m, [])


def test_un_solo_parser():
    definizioni = [p for p in PACCHETTO.rglob("*.py")
                   if "class Controller" in p.read_text(encoding="utf-8")]
    assert [p.relative_to(PACCHETTO).as_posix() for p in definizioni] == ["core/algebra.py"]
    for rel in NUOVI:
        testo = (PACCHETTO / rel).read_text(encoding="utf-8")
        assert "def _parse(" not in testo and "re.compile" not in testo, rel   # _parser() di argparse è ammesso


def test_persistenza_e_cli_non_caricano_tk():
    codice = ("import sys, gioco27.cli, gioco27.services.archivio, gioco27.services.sessione,"
              " gioco27.services.cronologia, gioco27.services.successione;"
              "print(sorted(m for m in sys.modules if m.startswith(('tkinter', 'gioco27.gui'))))")
    r = subprocess.run([sys.executable, "-B", "-c", codice], cwd=RADICE,
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "[]"


def test_nessun_codice_eseguito_dai_dati():
    for rel in NUOVI:
        albero = ast.parse((PACCHETTO / rel).read_text(encoding="utf-8"))
        for n in ast.walk(albero):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                assert n.func.id not in {"eval", "exec", "compile", "__import__"}, rel
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                nomi = [a.name for a in n.names] + [getattr(n, "module", None) or ""]
                assert not {"pickle", "marshal", "shelve"} & set(nomi), rel
