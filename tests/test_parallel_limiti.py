"""Regressioni B6-B8: input limitato, ingressi PDF e attesa ordinata."""
import concurrent.futures as futures

import pytest

from gioco27.core import combinations, detail_pdf, parallel, permutations


class _ImmediatePool:
    """Esegue task reali senza processi, usando Future reali completate."""

    def __init__(self, **kwargs):
        pass

    def submit(self, fn, task):
        future = futures.Future()
        future.set_result(fn(task))
        return future

    def shutdown(self, **kwargs):
        pass


def _inject_pool(monkeypatch):
    original = parallel.imap_ordered

    def imap(worker, tasks, n_workers, **kwargs):
        return original(worker, tasks, n_workers,
                        executor_factory=_ImmediatePool, **kwargs)

    monkeypatch.setattr(parallel, "imap_ordered", imap)


@pytest.mark.parametrize("total", [16, 10_000, 100_000,
                                  detail_pdf.MAX_DETAIL_COMBOS,
                                  parallel.MAX_EXPORT_ITEMS - 1,
                                  parallel.MAX_EXPORT_ITEMS])
def test_b6_input_prima_del_primo_risultato_limitato(total, monkeypatch):
    _inject_pool(monkeypatch)
    consumed = 0
    first = []

    def source():
        nonlocal consumed
        for value in range(total):
            consumed += 1
            yield value

    def consume(block, count):
        first.extend(block)
        assert count == len(block)
        raise parallel.ExportAnnullato()  # non enumera milioni di elementi

    nw, size = parallel.plan_workers(total, 2)
    assert nw == 2
    assert 1 <= size <= parallel.MAX_CHUNK_ITEMS == 1024
    with pytest.raises(parallel.ExportAnnullato):
        parallel.run_export(total=total, items_iter=source(), n_workers=2,
                            sequential=lambda: pytest.fail("fallback inatteso"),
                            parallel_worker=lambda start, block: block,
                            consume=consume)
    assert first == list(range(size))
    assert consumed <= min(total, 3 * nw * parallel.MAX_CHUNK_ITEMS)
    if total >= 10_000:
        assert consumed == 6144


@pytest.mark.parametrize("window", [1, 3, 6])
def test_b6_finestra_esplicita_limita_input(window):
    consumed = 0

    def source():
        nonlocal consumed
        for value in range(100_000):
            consumed += 1
            yield value

    nw, size = parallel.plan_workers(100_000, 2)
    results = parallel.imap_ordered(lambda block: block,
                                   parallel.chunked(source(), size), nw,
                                   max_pending=window,
                                   executor_factory=_ImmediatePool)
    try:
        assert next(results) == list(range(size))
        assert consumed == window * size
        assert consumed <= window * parallel.MAX_CHUNK_ITEMS
    finally:
        results.close()


@pytest.mark.parametrize("total", [17, 32_771])
def test_b6_worker_csv_ordine_e_copertura_dei_blocchi(total, monkeypatch):
    _inject_pool(monkeypatch)
    # Isola il costo matematico della singola riga, mantenendo il vero worker.
    monkeypatch.setattr(permutations, "make_csv_row",
                        lambda index, params: (index, params))
    rows, sizes = [], []

    def consume(block, count):
        rows.extend(block)
        sizes.append(count)
        assert len(block) == count

    assert parallel.run_export(
        total=total, items_iter=iter(range(total)), n_workers=2,
        sequential=lambda: pytest.fail("fallback inatteso"),
        parallel_worker=permutations._csv_chunk_worker, consume=consume) == total
    assert rows == list(enumerate(range(total), 1))
    assert sum(sizes) == total
    assert max(sizes) <= parallel.MAX_CHUNK_ITEMS
    assert sizes[-1] > 0


@pytest.mark.parametrize("total", [7, 10_000])
def test_b6_un_worker_usa_il_sequenziale_senza_preparazione(total):
    consumed, rows = [], []

    def source():
        for value in range(total):
            consumed.append(value)
            yield value

    items = source()

    def sequential():
        assert consumed == []
        rows.extend(items)
        return len(rows)

    assert parallel.plan_workers(total, 1) is None
    assert parallel.run_export(
        total=total, items_iter=items, n_workers=1, sequential=sequential,
        parallel_worker=lambda *a: pytest.fail("worker parallelo inatteso"),
        consume=lambda *a: pytest.fail("consumo parallelo inatteso")) == total
    assert rows == list(range(total))


def test_b6_oltre_limite_non_consuma_input():
    def forbidden():
        pytest.fail("input consumato oltre il limite")
        yield

    with pytest.raises(parallel.ExportTooLarge):
        parallel.run_export(total=parallel.MAX_EXPORT_ITEMS + 1,
                            items_iter=forbidden(), n_workers=2,
                            sequential=lambda: pytest.fail("fallback inatteso"),
                            parallel_worker=None, consume=None)


@pytest.mark.parametrize("minimum", [1, detail_pdf.COMBOS_PER_PAGE, 1024])
def test_b6_minimo_compatibile_e_allineamento_dettagliato(minimum):
    nw, size = parallel.plan_workers(parallel.MAX_EXPORT_ITEMS, 2,
                                     min_chunk=minimum)
    assert nw == 2
    assert minimum <= size <= parallel.MAX_CHUNK_ITEMS
    assert size + size % detail_pdf.COMBOS_PER_PAGE <= parallel.MAX_CHUNK_ITEMS


def test_b6_minimo_incompatibile_rifiutato():
    with pytest.raises(ValueError, match="min_chunk"):
        parallel.plan_workers(100_000, 2, min_chunk=1025)


_PDF_ROUTES = ["generate_pdf", "generate_pdf_ex", "generate_pdf_parallel",
               "generate_pdf_ex_parallel"]


def _free_filters():
    return [{key: "*" for key in combinations.CHIAVI_FILTRO} for _ in range(3)]


@pytest.mark.parametrize("name", _PDF_ROUTES)
def test_b7_pdf_oltre_limite_rifiutato_prima_di_canvas_e_input(name, tmp_path,
                                                            monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("canvas, renderer o generatore raggiunto oltre il limite")

    for target in ("_new_canvas", "_render_combinations", "_render_combinations_ex",
                   "iter_combinations", "iter_combinations_ex"):
        # I wrapper costruiscono il generatore, ma non devono iterarlo.
        if target.startswith("iter_"):
            def source(*args, **kwargs):
                forbidden()
                yield
            monkeypatch.setattr(combinations, target, source)
        else:
            monkeypatch.setattr(combinations, target, forbidden)
    dest = tmp_path / "out.pdf"
    dest.write_bytes(b"precedente")
    with pytest.raises(parallel.ExportTooLarge) as exc:
        getattr(combinations, name)(dest, _free_filters())
    assert exc.value.requested == 5_159_780_352
    assert exc.value.limit == parallel.MAX_EXPORT_ITEMS
    assert dest.read_bytes() == b"precedente"
    assert len(list(tmp_path.iterdir())) == 1


@pytest.mark.parametrize("name", _PDF_ROUTES)
@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_b7_soglia_identica_fra_ingressi(name, offset, tmp_path, monkeypatch):
    class CanvasReached(Exception):
        pass

    def canvas(*args, **kwargs):
        raise CanvasReached()

    total = parallel.MAX_EXPORT_ITEMS + offset
    counter = "count_combinations_ex" if "_ex" in name else "count_combinations"
    monkeypatch.setattr(combinations, counter, lambda filters: total)
    monkeypatch.setattr(combinations, "_new_canvas", canvas)
    options = {"n_workers": 1} if name.endswith("parallel") else {}
    expected = parallel.ExportTooLarge if offset > 0 else CanvasReached
    with pytest.raises(expected):
        getattr(combinations, name)(tmp_path / "out.pdf", _free_filters(), **options)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("name", _PDF_ROUTES)
def test_b7_pdf_sotto_soglia_conserva_contenuto(name, tmp_path):
    pytest.importorskip("reportlab")
    PdfReader = pytest.importorskip("pypdf").PdfReader
    filters = [dict(p0="SCD_U", p1="SCD_U", p2="SCD_U",
                    j0="I_3", j1="I_3", j2="I_3") for _ in range(3)]
    filters[0]["j0"] = "*"
    dest = tmp_path / "out.pdf"
    options = {"n_workers": 1} if name.endswith("parallel") else {}
    assert getattr(combinations, name)(dest, filters, **options) == 2
    pages = PdfReader(dest).pages
    assert len(pages) == 2
    assert "#1" in pages[0].extract_text()
    assert "#2" in pages[1].extract_text()


@pytest.mark.parametrize("outcome", ["successo", "errore", "annullamento"])
def test_b8_attesa_non_si_risveglia_sui_successivi_completati(outcome, monkeypatch):
    # Il primo future resta incompleto, tutti i successivi sono gia' pronti.
    # Due timeout reali precedono l'evento che sblocca o annulla il primo.
    pending, shutdowns, calls, stop = [], [], [], []

    class Pool:
        def __init__(self, **kwargs):
            pass

        def submit(self, fn, task):
            future = futures.Future()
            if task != 0:
                future.set_result(fn(task))
            pending.append(future)
            return future

        def shutdown(self, **kwargs):
            shutdowns.append(kwargs)

    real_wait = futures.wait

    def observed_wait(fs, **kwargs):
        calls.append(1)
        assert len(calls) <= 3, "risvegli ripetuti sui future successivi"
        assert pending[1].done()
        if len(calls) == 3:
            if outcome == "errore":
                pending[0].set_exception(RuntimeError("errore in testa"))
            else:
                pending[0].set_result(0)
        done, remaining = real_wait(fs, **kwargs)
        if len(calls) < 3:
            # Nessun risultato restituibile: deve essere un timeout,
            # non un risveglio sul secondo future completato.
            assert done == set()
            if outcome == "annullamento" and len(calls) == 2:
                stop.append(True)
        return done, remaining

    monkeypatch.setattr(futures, "wait", observed_wait)
    results = parallel.imap_ordered(lambda value: value, range(9), 2,
                                   max_pending=3, executor_factory=Pool,
                                   annullato=lambda: bool(stop), attesa=0.01)
    if outcome == "successo":
        assert list(results) == list(range(9))
        assert len(calls) == 3
        assert shutdowns == [{"wait": True}]
    elif outcome == "errore":
        with pytest.raises(RuntimeError, match="errore in testa"):
            next(results)
        assert len(calls) == 3
        assert len(pending) == 3
        assert shutdowns == [{"wait": True}]
    else:
        with pytest.raises(parallel.ExportAnnullato):
            next(results)
        assert len(calls) == 2
        assert not pending[0].done()
        assert len(pending) == 3
        assert shutdowns == [{"wait": False, "cancel_futures": True}]
