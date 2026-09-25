# -*- mode: python ; coding: utf-8 -*-
# Spec PyInstaller ufficiale di «Gioco delle 27 carte» (versionata dal
# compartimento K, N04).
#
# Uso (dalla radice del repository, con le dipendenze di build e di export):
#     pip install .[export,build]
#     pyinstaller gioco27.spec
#
# Risultato: dist/Gioco27/Gioco27[.exe] (cartella autonoma, niente Python
# richiesto). Per un singolo file portatile impostare `onefile = True` qui
# sotto (avvio piu' lento).
#
# Tutti i percorsi sono ancorati alla cartella di questo file (SPECPATH),
# non alla cartella corrente. I PDF fonte (LIBRO_MAIN.pdf, Articolo.pdf) NON
# fanno parte del bundle (DP12).

import os

onefile = False
_radice = SPECPATH  # noqa: F821 — definita da PyInstaller durante l'esecuzione della spec


def _qui(*parti):
    return os.path.join(_radice, *parti)


a = Analysis(  # noqa: F821
    [_qui("gioco27.py")],              # launcher: freeze_support() + gioco27.__main__.main
    pathex=[_radice],
    binaries=[],
    datas=[
        (_qui("gioco27", "assets"), os.path.join("gioco27", "assets")),  # font DejaVu + LICENSE-DejaVu.txt
        (_qui("LICENSE"), "."),                                            # GPL-3.0 del programma
    ],
    # Export facoltativi (extra `export` di pyproject.toml): importati in modo
    # pigro dal codice, quindi vanno dichiarati. Se mancano nell'ambiente di
    # build, PyInstaller avvisa e l'eseguibile li segnala come non disponibili.
    hiddenimports=["reportlab", "openpyxl", "pypdf", "pikepdf"],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821

if onefile:
    exe = EXE(  # noqa: F821
        pyz, a.scripts, a.binaries, a.datas,
        name="Gioco27",
        console=False,            # niente finestra console: e' una GUI
        upx=False,
    )
else:
    exe = EXE(  # noqa: F821
        pyz, a.scripts,
        exclude_binaries=True,
        name="Gioco27",
        console=False,
        upx=False,
    )
    coll = COLLECT(exe, a.binaries, a.datas, name="Gioco27")  # noqa: F821
