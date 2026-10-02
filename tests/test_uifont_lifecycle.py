"""Fase P4 — ciclo di vita dei font con nome (`gui/uifont.py`) fra root Tk.

`uifont` tiene in una cache di modulo gli oggetti Font dei testi d'aiuto.
Un Font appartiene all'interprete Tcl della root in cui e' nato: prima della
correzione, dopo la distruzione della prima App una seconda App nello stesso
processo riusava quei Font e falliva con «can't invoke "font" command:
application has been destroyed». Nell'uso normale il programma crea una sola
App per processo, ma la suite completa eseguita in un solo processo (e
qualunque riavvio della finestra) ne crea piu' d'una: da qui la cascata di
errori dei test GUI.

Lo scenario discriminante e' quello reale: App, chiusura, nuova App.
"""
import pytest

tk = pytest.importorskip("tkinter")
tkfont = pytest.importorskip("tkinter.font")

from gioco27.gui import uifont  # noqa: E402


def _root():
    try:
        r = tk.Tk()
    except tk.TclError:
        pytest.skip("display non disponibile")
    r.withdraw()
    return r


def _font_vivo(root, nome="GiocoHelp"):
    return nome in root.tk.splitlist(root.tk.call("font", "names"))


def test_due_root_successive_nello_stesso_processo():
    prima = _root()
    try:
        uifont.apply_scale(1.0, root=prima)
        assert _font_vivo(prima)
    finally:
        prima.destroy()
    seconda = _root()
    try:
        uifont.apply_scale(1.5, root=seconda)          # prima: TclError
        assert _font_vivo(seconda)
        f = tkfont.Font(root=seconda, name="GiocoHelp", exists=True)
        assert f.cget("size") == 15                     # 10 pt × 1,5
        uifont.apply_scale(1.0, root=seconda)            # scala di default per i test successivi
    finally:
        seconda.destroy()


def test_due_root_contemporanee_conservano_i_propri_font():
    prima = _root()
    seconda = None
    try:
        uifont.apply_scale(1.0, root=prima)
        seconda = tk.Toplevel(prima)                    # stesso interprete: nessuna ricreazione
        uifont.apply_scale(1.2, root=seconda)
        assert _font_vivo(prima)
        terza = tk.Tk()
        try:
            terza.withdraw()
            uifont.apply_scale(1.0, root=terza)         # interprete diverso
            assert _font_vivo(terza)
            assert _font_vivo(prima), "il font della prima root non va cancellato"
        finally:
            terza.destroy()
    finally:
        prima.destroy()


def test_app_chiusa_e_riaperta_nello_stesso_processo():
    """Lo scenario reale: due App successive, la seconda deve nascere sana."""
    sonda = _root()
    sonda.destroy()
    from gioco27.gui import app as app_module

    for _ in range(2):
        a = app_module.App()
        try:
            a.update_idletasks()
            assert _font_vivo(a)
        finally:
            a.destroy()
