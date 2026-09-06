"""
Annullamento degli export.

Un export grande poteva solo essere portato a termine o interrotto chiudendo la
finestra. Ora un pulsante «Annulla» lo ferma appena possibile, e — grazie alla
scrittura atomica — **non lascia alcun file**: la destinazione resta com'era.

L'annullamento attraversa cinque percorsi diversi (PDF standard, PDF esteso,
PDF dettagliato, CSV, ciascuno in versione sequenziale e parallela), quindi i
test li coprono tutti: dimenticarne uno significherebbe un pulsante che a volte
non risponde.
"""
import re

import pytest

from gioco27.core.constants import ANY
from gioco27.core.parallel import ExportAnnullato, mai_annullato


def _filtri():
    return [{'p0': 'SCD_U', 'p1': 'SCD_U', 'p2': ANY,
             'j0': ANY, 'j1': ANY, 'j2': ANY, 'j_uniform': True}
            for _ in range(3)]


def _annulla_dopo(n):
    """Sentinella che diventa vera dopo n interrogazioni."""
    stato = {"n": 0}

    def f():
        stato["n"] += 1
        return stato["n"] > n
    return f


def test_sentinella_predefinita_non_annulla():
    assert mai_annullato() is False


@pytest.mark.parametrize("nome,modulo,funzione,kw", [
    ("PDF esteso sequenziale", "combinations", "generate_pdf_ex", {}),
    ("PDF esteso parallelo", "combinations", "generate_pdf_ex_parallel",
     {"n_workers": 2}),
    ("PDF standard sequenziale", "combinations", "generate_pdf", {}),
    ("PDF dettagliato", "detail_pdf", "generate_detail_pdf", {}),
    ("CSV sequenziale", "permutations", "write_csv", {}),
    ("CSV parallelo", "permutations", "write_csv_parallel", {"n_workers": 2}),
])
def test_ogni_export_si_annulla_e_non_lascia_file(nome, modulo, funzione, kw,
                                                  tmp_path):
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdf")
    import importlib
    mod = importlib.import_module(f"gioco27.core.{modulo}")
    fn = getattr(mod, funzione)

    dest = tmp_path / ("uscita.csv" if "CSV" in nome else "uscita.pdf")
    with pytest.raises(ExportAnnullato):
        fn(str(dest), _filtri(), annullato=_annulla_dopo(3), **kw)

    assert not dest.exists(), f"{nome}: la destinazione è stata creata"
    residui = [p.name for p in tmp_path.iterdir()]
    assert not residui, f"{nome}: file temporanei rimasti: {residui}"


def test_un_export_annullato_non_tocca_il_file_esistente(tmp_path):
    """Se al posto di destinazione c'era già un file, deve restare intatto."""
    pytest.importorskip("reportlab")
    from gioco27.core.permutations import write_csv

    dest = tmp_path / "vecchio.csv"
    dest.write_text("contenuto precedente", encoding="utf-8")
    with pytest.raises(ExportAnnullato):
        write_csv(str(dest), _filtri(), annullato=_annulla_dopo(3))
    assert dest.read_text(encoding="utf-8") == "contenuto precedente"


def test_senza_annullamento_l_export_va_a_termine(tmp_path):
    """La sentinella predefinita non deve interferire."""
    pytest.importorskip("reportlab")
    from gioco27.core.permutations import write_csv
    filtri = [{'p0': 'SCD_U', 'p1': 'SCD_U', 'p2': 'CDS_U',
               'j0': 'I_3', 'j1': 'I_3', 'j2': 'I_3'} for _ in range(3)]
    dest = tmp_path / "ok.csv"
    assert write_csv(str(dest), filtri) == 1
    assert dest.exists()


def test_exportannullato_riporta_il_progresso():
    e = ExportAnnullato(120, 5000)
    assert e.fatti == 120 and e.totale == 5000
    assert "120" in str(e)


# ─────────────────────── il parallelo non deve attendere ───────────────────

def test_imap_ordered_annulla_senza_attendere_i_worker():
    """
    Con un blocco per worker, aspettare il completamento significherebbe
    minuti. `imap_ordered` chiude il pool con wait=False e cancel_futures.
    """
    from gioco27.core import parallel

    chiusure = []

    class _Pool:
        def __init__(self, max_workers=None, **kw):
            pass

        def submit(self, fn, *a, **kw):
            from concurrent.futures import Future
            return Future()            # mai completata: simula lavoro in corso

        def shutdown(self, wait=True, cancel_futures=False):
            chiusure.append((wait, cancel_futures))

    compiti = [(i, [i]) for i in range(4)]
    with pytest.raises(ExportAnnullato):
        list(parallel.imap_ordered(lambda t: t, iter(compiti), n_workers=2,
                                   executor_factory=_Pool,
                                   annullato=lambda: True, attesa=0.01))
    assert chiusure == [(False, True)], (
        f"il pool dev'essere chiuso senza attendere: {chiusure}")


def test_senza_annullamento_il_pool_viene_atteso():
    """Nel caso normale il pool si chiude regolarmente, attendendo i worker."""
    from concurrent.futures import Future
    from gioco27.core import parallel

    chiusure = []

    class _Pool:
        def __init__(self, max_workers=None, **kw):
            pass

        def submit(self, fn, *a, **kw):
            f = Future()
            f.set_result(fn(*a, **kw))
            return f

        def shutdown(self, wait=True, cancel_futures=False):
            chiusure.append((wait, cancel_futures))

    compiti = [(i, [i]) for i in range(3)]
    esiti = list(parallel.imap_ordered(lambda t: t, iter(compiti), n_workers=2,
                                       executor_factory=_Pool))
    assert esiti == compiti
    assert chiusure == [(True, False)]


# ───────────────────────────── lato interfaccia ────────────────────────────

def test_la_gui_collega_il_pulsante_all_annullamento():
    """
    Il pulsante deve arrivare fino alle funzioni di export: verificato sul
    sorgente, perché la GUI non è avviabile nei test.
    """
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "gioco27" / "gui" / "app.py").read_text(encoding="utf-8")
    corpo = src.split("def _run_generation", 1)[1].split("\n    def ", 1)[0]
    assert "annullato=self._export_stop.is_set" in corpo, \
        "l'export non riceve la richiesta di annullamento"
    assert "except ExportAnnullato" in corpo, \
        "l'annullamento verrebbe mostrato come un errore"
    for metodo in ("_annulla_export", "_fine_export"):
        assert f"def {metodo}" in src, f"manca {metodo}"
    assert re.search(r'text="✕\s+Annulla"', src), "manca il pulsante Annulla"
