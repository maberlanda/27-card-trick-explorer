"""Regressioni B3-B5: contenuto, fallimenti parziali e cancellazione."""
import csv
import io
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from gioco27.core import combinations, detail_pdf, parallel, permutations
from gioco27.core.parallel import ExportAnnullato


def _filters():
    filters = [dict(p0="SCD_U", p1="SCD_U", p2="SCD_U",
                    j0="I_3", j1="I_3", j2="I_3") for _ in range(3)]
    filters[0]["j0"] = "*"
    return filters


def _inline(worker, tasks, n_workers, **kwargs):
    for task in tasks:
        yield worker(task)


def _force_parallel(monkeypatch):
    monkeypatch.setattr(parallel, "plan_workers", lambda total, n_workers=None,
                        *a, **kw: None if n_workers == 1 else (2, 1))
    monkeypatch.setattr(detail_pdf, "plan_workers", lambda total, n_workers=None,
                        *a, **kw: None if n_workers == 1 else (2, 2))
    monkeypatch.setattr(parallel, "imap_ordered", _inline)
    monkeypatch.setattr(detail_pdf, "imap_ordered", _inline)


def _export(kind, path, **kwargs):
    routes = {
        "csv": (permutations.write_csv, {}),
        "csv_fallback": (permutations.write_csv_parallel, {"n_workers": 1}),
        "csv_parallel": (permutations.write_csv_parallel, {"n_workers": 2}),
        "pdf": (combinations.generate_pdf, {}),
        "pdf_parallel": (combinations.generate_pdf_parallel, {"n_workers": 2}),
        "pdf_ex": (combinations.generate_pdf_ex, {}),
        "pdf_ex_parallel": (combinations.generate_pdf_ex_parallel, {"n_workers": 2}),
        "detail": (detail_pdf.generate_detail_pdf, {}),
        "detail_parallel": (detail_pdf.generate_detail_pdf_parallel, {"n_workers": 2}),
    }
    if not kind.startswith("csv"):
        pytest.importorskip("reportlab")
        pytest.importorskip("pypdf")
    fn, options = routes[kind]
    return fn(path, _filters(), **options, **kwargs)


def _content(kind, path):
    if kind.startswith("csv"):
        with path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f, delimiter=";"))
        assert len(rows) == 3  # intestazione + due combinazioni
        assert [r[0] for r in rows[1:]] == ["1", "2"]
        assert len({tuple(r) for r in rows[1:]}) == 2
        return rows
    from pypdf import PdfReader
    pages = PdfReader(io.BytesIO(path.read_bytes())).pages
    assert len(pages) == 2
    texts = [page.extract_text() for page in pages]
    assert "#1" in texts[0] and "#2" in texts[1]
    assert texts[0] != texts[1]
    return texts


@pytest.mark.parametrize("kind", ["csv", "pdf", "pdf_ex"])
@pytest.mark.parametrize("preexisting", [False, True])
def test_errore_dopo_primo_blocco_non_pubblica_output_parziale(
        kind, preexisting, tmp_path, monkeypatch):
    dest = tmp_path / ("out.csv" if kind == "csv" else "out.pdf")
    old_bytes = old_content = None
    if preexisting:
        assert _export(kind, dest) == 2
        old_bytes = dest.read_bytes()
        old_content = _content(kind, dest)
    _force_parallel(monkeypatch)
    progress = []

    def fail_after_one(worker, tasks, n_workers, **kwargs):
        yield worker(next(iter(tasks)))
        assert progress == [1]  # il primo blocco è stato consumato
        raise RuntimeError("errore dopo primo blocco")

    monkeypatch.setattr(parallel, "imap_ordered", fail_after_one)
    with pytest.raises(RuntimeError, match="errore dopo primo blocco"):
        _export(kind + "_parallel", dest, progress_cb=progress.append)
    if preexisting:
        assert dest.read_bytes() == old_bytes
        assert _content(kind, dest) == old_content
    else:
        assert not dest.exists()
    assert not list(tmp_path.glob("*.parziale"))


@pytest.mark.parametrize("kind", ["csv", "pdf", "pdf_ex"])
@pytest.mark.parametrize("early_failure", [False, True])
def test_export_completo_e_fallback_prima_dei_dati(
        kind, early_failure, tmp_path, monkeypatch):
    reference = tmp_path / "reference"
    assert _export(kind, reference) == 2
    expected = _content(kind, reference)
    _force_parallel(monkeypatch)
    if early_failure:
        def fail_before_one(*args, **kwargs):
            raise RuntimeError("pool non disponibile")
        monkeypatch.setattr(parallel, "imap_ordered", fail_before_one)
    dest = tmp_path / "out"
    assert _export(kind + "_parallel", dest) == 2
    assert _content(kind, dest) == expected
    assert not list(tmp_path.glob("*.parziale"))


def test_consume_parzialmente_fallito_non_ammette_fallback(monkeypatch):
    _force_parallel(monkeypatch)
    written = []

    def consume(result, count):
        written.append(result)
        raise OSError("scrittura interrotta")

    def sequential():
        pytest.fail("fallback dopo scrittura parziale")

    with pytest.raises(OSError, match="scrittura interrotta"):
        parallel.run_export(total=2, items_iter=iter([1, 2]),
                            sequential=sequential,
                            parallel_worker=lambda start, block: block,
                            consume=consume, n_workers=2)
    assert written == [[1]]


_ROUTES = ["csv", "csv_fallback", "csv_parallel", "pdf", "pdf_parallel",
           "pdf_ex", "pdf_ex_parallel", "detail", "detail_parallel"]


@pytest.mark.parametrize("kind", _ROUTES)
@pytest.mark.parametrize("moment", ["ingresso", "ultimo_progresso", "prima_replace"])
def test_cancellazione_preserva_destinazione(kind, moment, tmp_path, monkeypatch):
    _force_parallel(monkeypatch)
    dest = tmp_path / "out"
    old = b"contenuto precedente\x00\xff\r\n"
    dest.write_bytes(old)
    stop = threading.Event()
    progress = []
    if moment == "ingresso":
        stop.set()
    elif moment == "prima_replace":
        real_open = open

        class CancelOnClose:
            def __init__(self, f):
                self.f = f

            def __getattr__(self, name):
                return getattr(self.f, name)

            def close(self):
                self.f.close()
                stop.set()

        monkeypatch.setattr(parallel, "open", lambda *a, **kw:
                            CancelOnClose(real_open(*a, **kw)), raising=False)

    def on_progress(done):
        progress.append(done)
        if moment == "ultimo_progresso" and done == 2:
            stop.set()

    with pytest.raises(ExportAnnullato):
        _export(kind, dest, annullato=stop.is_set, progress_cb=on_progress)
    assert stop.is_set()
    assert dest.read_bytes() == old
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out"]
    if moment == "ingresso":
        assert progress == []
    elif moment == "ultimo_progresso":
        assert progress[-1] == 2


@pytest.mark.parametrize("kind", ["csv", "csv_fallback"])
def test_csv_piccolo_annullato_durante_le_righe(kind, tmp_path, monkeypatch):
    dest = tmp_path / "out.csv"
    dest.write_bytes(b"vecchio")
    stop = threading.Event()
    original = permutations.make_csv_row

    def make_row(index, params):
        row = original(index, params)
        if index == 1:
            stop.set()
        return row

    monkeypatch.setattr(permutations, "make_csv_row", make_row)
    with pytest.raises(ExportAnnullato):
        _export(kind, dest, annullato=stop.is_set)
    assert dest.read_bytes() == b"vecchio"
    assert not list(tmp_path.glob("*.parziale"))


def test_dettagliato_annulla_attesa_prima_che_worker_finisca(tmp_path, monkeypatch):
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdf")
    dest = tmp_path / "out.pdf"
    dest.write_bytes(b"PDF precedente")
    started, release, completed = threading.Event(), threading.Event(), threading.Event()
    stop, finished = threading.Event(), threading.Event()
    outcome, pools = [], []
    original_imap = parallel.imap_ordered
    monkeypatch.setattr(detail_pdf, "plan_workers", lambda *a, **kw: (2, 2))

    def pool_factory(**kwargs):
        pool = ThreadPoolExecutor(**kwargs)
        pools.append(pool)
        return pool

    def imap(worker, tasks, n_workers, **kwargs):
        return original_imap(worker, tasks, n_workers,
                             executor_factory=pool_factory, **kwargs)

    def slow_worker(task):
        started.set()
        release.wait(15)  # il test sblocca sempre il worker nel finally
        completed.set()
        return b"risultato tardivo da scartare", len(task[1])

    def run():
        try:
            _export("detail_parallel", dest, annullato=stop.is_set)
        except Exception as exc:
            outcome.append(exc)
        finally:
            finished.set()

    monkeypatch.setattr(detail_pdf, "imap_ordered", imap)
    monkeypatch.setattr(detail_pdf, "_detail_chunk_to_bytes", slow_worker)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    try:
        assert started.wait(5), "worker non avviato"
        stop.set()
        assert finished.wait(5), "la cancellazione attende il completamento del worker"
        assert not completed.is_set()
        assert len(outcome) == 1 and isinstance(outcome[0], ExportAnnullato)
        assert dest.read_bytes() == b"PDF precedente"
        assert sorted(p.name for p in tmp_path.iterdir()) == ["out.pdf"]
    finally:
        release.set()
        thread.join(10)
        for pool in pools:
            pool.shutdown(wait=True, cancel_futures=True)


@pytest.mark.parametrize("phase", ["generazione", "ordinamento", "annotazioni"])
def test_preparazione_dettagliato_osserva_annullamento(phase, tmp_path, monkeypatch):
    dest = tmp_path / "out.pdf"
    dest.write_bytes(b"vecchio")
    stop = threading.Event()
    calls = []
    if phase == "generazione":
        original = detail_pdf.iter_combinations_ex

        def source(filters):
            for params in original(filters):
                calls.append(params)
                stop.set()
                yield params
        monkeypatch.setattr(detail_pdf, "iter_combinations_ex", source)
    else:
        name = "_order_key" if phase == "ordinamento" else "_perm_of"
        original = getattr(detail_pdf, name)

        def operation(params):
            calls.append(params)
            result = original(params)
            stop.set()
            return result
        monkeypatch.setattr(detail_pdf, name, operation)
    with pytest.raises(ExportAnnullato):
        _export("detail_parallel", dest, annullato=stop.is_set)
    assert len(calls) == 1
    assert dest.read_bytes() == b"vecchio"
    assert not list(tmp_path.glob("*.parziale"))
