"""R3: nessun buffer applicativo dell'intero PDF nei percorsi sequenziali."""
import io
import threading

import pytest

from gioco27.core import combinations, detail_pdf
from gioco27.core.parallel import ExportAnnullato


def _filters(total):
    filters = [dict(p0="SCD_U", p1="SCD_U", p2="SCD_U",
                    j0="I_3", j1="I_3", j2="I_3") for _ in range(3)]
    for i in (range(1) if total == 6 else range(3)):
        filters[i]["p2"] = "*"
    return filters


def _route(kind, fallback):
    mod = detail_pdf if kind == "detail" else combinations
    name = {"standard": "generate_pdf", "extended": "generate_pdf_ex",
            "detail": "generate_detail_pdf"}[kind]
    if fallback:
        name += "_parallel"
    return getattr(mod, name), ({"n_workers": 1} if fallback else {})


def _factory(kind):
    return ((detail_pdf, "_new_detail_canvas") if kind == "detail"
            else (combinations, "_new_canvas"))


def _reference(kind, filters):
    """Vecchio percorso in memoria, per confrontare tutti i byte del PDF."""
    buffer = io.BytesIO()
    if kind == "detail":
        params, labels, transposes = detail_pdf._prepare(filters)
        c, painter = detail_pdf._new_detail_canvas(buffer)
        detail_pdf.render_detail_pages(c, params, labels=labels,
                                       transposes=transposes, painter=painter)
    else:
        extended = kind == "extended"
        c, painter = combinations._new_canvas(buffer, ex=extended)
        generate = combinations.iter_combinations_ex if extended else combinations.iter_combinations
        render = combinations._render_combinations_ex if extended else combinations._render_combinations
        render(c, generate(filters), painter=painter)
    c.save()
    return buffer.getvalue()


@pytest.mark.parametrize("kind", ["standard", "extended", "detail"])
@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("total", [6, 216])
def test_pdf_scrive_su_file_senza_buffer_completo(
        kind, fallback, total, tmp_path, monkeypatch):
    pytest.importorskip("reportlab")
    pypdf = pytest.importorskip("pypdf")
    from reportlab import rl_config
    monkeypatch.setattr(rl_config, "invariant", 1)  # esclude timestamp e ID casuali
    filters = _filters(total)
    reference = _reference(kind, filters)
    module, name = _factory(kind)
    factory = getattr(module, name)
    targets = []

    def observe(target, *args, **kwargs):
        # Un vero descrittore: BytesIO.fileno() solleva UnsupportedOperation.
        assert isinstance(target.fileno(), int)
        assert not isinstance(target, io.BytesIO)
        targets.append(target)
        return factory(target, *args, **kwargs)

    monkeypatch.setattr(module, name, observe)
    generate, options = _route(kind, fallback)
    path = tmp_path / "output.pdf"
    assert generate(str(path), filters, **options) == total
    assert len(targets) == 1 and targets[0].closed
    actual = path.read_bytes()
    assert actual == reference  # stesso ordine, annotazioni, pagine e risorse
    reader = pypdf.PdfReader(io.BytesIO(actual))
    assert len(reader.pages) == (total // 2 if kind == "detail" else total)
    assert set(tmp_path.iterdir()) == {path}


@pytest.mark.parametrize("kind", ["standard", "extended", "detail"])
@pytest.mark.parametrize("preexisting", [False, True])
@pytest.mark.parametrize("outcome", ["error", "cancel"])
def test_serializzazione_pdf_interrotta_non_pubblica_parziali(
        kind, preexisting, outcome, tmp_path, monkeypatch):
    pytest.importorskip("reportlab")
    module, name = _factory(kind)
    factory = getattr(module, name)
    stop = threading.Event()
    path = tmp_path / "output.pdf"
    previous = b"destinazione precedente\x00\xff\r\n"
    if preexisting:
        path.write_bytes(previous)

    def interrupted(target, *args, **kwargs):
        canvas, painter = factory(target, *args, **kwargs)

        def save():
            target.write(b"%PDF-parziale")
            if outcome == "error":
                raise OSError("serializzazione interrotta")
            stop.set()

        canvas.save = save
        return canvas, painter

    monkeypatch.setattr(module, name, interrupted)
    generate, options = _route(kind, False)
    expected_error = OSError if outcome == "error" else ExportAnnullato
    with pytest.raises(expected_error):
        generate(str(path), _filters(6), annullato=stop.is_set, **options)
    if preexisting:
        assert path.read_bytes() == previous
    else:
        assert not path.exists()
    assert set(tmp_path.iterdir()) == ({path} if preexisting else set())
