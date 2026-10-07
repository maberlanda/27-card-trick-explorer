"""Behavioural checks for the measured universal detailed PDF layout."""
import io
import re

import pytest

from gioco27.core import detail_pdf as pdf
from gioco27.core.detail import DECK, combination_detail
from gioco27.core.permutations import R_label
from gioco27.core.detail_layout import (
    LAYOUT, ConfigurationTooTall, configuration_rows, measure_config,
    paginate_heights, wrap_text,
)
from gioco27.i18n import get_language, set_language, tr

CLASSIC = [('SCD_U', 'SCD_U', 'DSC_U', 'I_3', 'I_3', 'I_3'),
           ('SCD_U', 'SCD_U', 'CSD_U', 'R_U', 'R_U', 'R_U'),
           ('SCD_U', 'SCD_U', 'SCD_U', 'I_3', 'I_3', 'I_3')]
GENERAL = [('SDC_U', 'CSD_U', 'CDS_U', 'I_3', 'R_U', 'I_3'),
           ('DCS_U', 'SDC_U', 'DSC_U', 'I_3', 'R_U', 'I_3'),
           ('CSD_U', 'CDS_U', 'DCS_U', 'I_3', 'R_U', 'I_3')]


@pytest.fixture(autouse=True)
def restore_language():
    previous = get_language()
    set_language('it')
    yield
    set_language(previous)


def measured(params, references=(), layout=LAYOUT):
    return measure_config(params, references, fonts=pdf._ensure_fonts(),
                          classic_indices=pdf._c_indices(params),
                          impilamenti=tuple(pdf._stage_impilamento(p) for p in params),
                          layout=layout)


def document(params, references=None):
    pytest.importorskip('reportlab')
    reader = pytest.importorskip('pypdf').PdfReader
    buf = io.BytesIO()
    c, painter = pdf._new_detail_canvas(buf)
    pdf.render_detail_pages(c, params, transposes=references,
                            labels=['unused'] * len(params) if references is not None else None,
                            painter=painter)
    c.save()
    return reader(io.BytesIO(buf.getvalue()))


def test_explicit_three_by_six_configuration():
    rows = configuration_rows(GENERAL)
    assert rows == (('SDC', 'CSD', 'CDS', 'I₃', 'Rᵤ', 'I₃'),
                    ('DCS', 'SDC', 'DSC', 'I₃', 'Rᵤ', 'I₃'),
                    ('CSD', 'CDS', 'DCS', 'I₃', 'Rᵤ', 'I₃'))
    assert all(len(row) == 6 for row in rows)
    assert not any(value.isdigit() for row in rows for value in row)


def test_classical_alias_and_core_reversal_are_additional():
    text = document([CLASSIC]).pages[0].extract_text()
    for value in ('Configurazione completa', 'Gioco: P[0][2][3][2]',
                  'R[2] core', 'J prima di MSC', 'M[3]', 'CDS', 'CSD'):
        assert value in text
    assert 'P / J completi' not in text


def test_general_has_no_classical_alias_or_physical_classification():
    plan = measured(GENERAL)
    flags = [b.lines for b in plan.texts if b.lines == ('NO / SÌ / NO',)]
    assert len(flags) == 3
    text = document([GENERAL]).pages[0].extract_text()
    assert 'Configurazione generale' not in text
    assert R_label(GENERAL) in text
    assert 'Configurazione completa' in text
    assert 'NO / SÌ / NO' in text
    assert 'I₃' in text and 'Rᵤ' in text
    assert 'Gesto per livelli' not in text
    assert text.count('J → MSC → P') == 1
    assert text.count('Rovesciamenti') == 3
    assert text.count('Riordini P') == 3
    assert 'Esecuzione fisica' in text
    assert not re.search(r'(?:P|R)\[', text)
    for forbidden in ('non fisico', 'non eseguibile', 'impossibile', 'C[(', ';010'):
        assert forbidden not in text


def test_general_header_reuses_complete_core_formula_without_wrapping():
    from reportlab.pdfbase.pdfmetrics import stringWidth
    for js in (('I_3',) * 3, ('R_U',) * 3, ('I_3', 'R_U', 'I_3')):
        params = [stage[:3] + js for stage in GENERAL]
        plan = measured(params)
        formula = next(b for b in plan.texts if b.x == LAYOUT.header_columns[1])
        assert formula.lines == (R_label(params),)
        assert formula.lines[0].count('o MSC o') == 3
        assert formula.lines[0].startswith('T = [(DCS_U x CDS_U x CSD_U)')
        right = formula.x + stringWidth(formula.lines[0], pdf._ensure_fonts()[0], formula.size)
        assert right < LAYOUT.page_width - LAYOUT.margin - LAYOUT.general_order_width
        assert plan.height == 346


@pytest.mark.parametrize('language', ['it', 'en'])
@pytest.mark.parametrize('params', [CLASSIC, GENERAL])
def test_board_grids_are_centered_under_their_titles(monkeypatch, language, params):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.pdfbase.pdfmetrics import stringWidth
    set_language(language)
    titles = {}
    cells = []
    original_string = Canvas.drawString
    original_rect = Canvas.rect
    board_titles = (tr('export.document.detail.board_t'),
                    tr('export.document.detail.board_inverse'))

    def draw_string(c, x, y, text, *args, **kwargs):
        if text in board_titles:
            titles[text] = x
        return original_string(c, x, y, text, *args, **kwargs)

    def rect(c, x, y, width, height, *args, **kwargs):
        if width == LAYOUT.board_cell_width and height == LAYOUT.board_cell_height:
            cells.append((x, y, width, height))
        return original_rect(c, x, y, width, height, *args, **kwargs)

    monkeypatch.setattr(Canvas, 'drawString', draw_string)
    monkeypatch.setattr(Canvas, 'rect', rect)
    document([params])
    top = max(cell[1] for cell in cells)
    first_row = [cell for cell in cells if cell[1] == top]
    assert len(first_row) == 7
    for title, grid in zip(board_titles, (first_row[:3], first_row[3:])):
        center = (grid[0][0] + grid[-1][0] + grid[-1][2]) / 2
        title_center = titles[title] + stringWidth(
            title, pdf._ensure_fonts()[1], LAYOUT.heading_font) / 2
        assert center == pytest.approx(title_center)
    assert len(cells) == 24


def test_nonuniform_j_is_not_a_whole_deck_reversal_or_r_alias():
    params = [GENERAL[0][:3]+('R_U', 'I_3', 'I_3')]+GENERAL[1:]
    assert not pdf._reversed_stage(params[0])
    assert pdf._r_index(params) is None
    assert ('SÌ / NO / NO',) in [b.lines for b in measured(params).texts]


def test_historical_indices_reuse_sigle_not_p_options_order():
    params = [('SCD_U', 'SCD_U', p, 'I_3', 'I_3', 'I_3')
              for p in ('DSC_U', 'CDS_U', 'SCD_U')]
    assert pdf._c_indices(params) == (0, 4, 3, 0)
    assert configuration_rows(params)[0][2] == 'DSC'
    assert configuration_rows(params)[1][2] == 'CDS'


def test_before_after_draws_full_stage_outputs(monkeypatch):
    records = []
    cards = []
    original = pdf.combination_detail
    original_card = pdf._card
    def detail(params):
        d = original(params)
        records.append(d)
        return d
    monkeypatch.setattr(pdf, 'combination_detail', detail)
    def card(ch):
        cards.append(ch)
        return original_card(ch)
    monkeypatch.setattr(pdf, '_card', card)
    document([GENERAL])
    d = records[0]
    plan = measured(GENERAL)
    for stage, (before, after) in enumerate(plan.before_after):
        assert (before, after) == (stage, stage + 1)
        assert sorted(d['dispositions'][before]) == sorted(DECK)
        assert sorted(d['dispositions'][after]) == sorted(DECK)
        if stage < 2:
            assert d['dispositions'][after] == d['dispositions'][plan.before_after[stage+1][0]]
    assert d['dispositions'][-1] == combination_detail(GENERAL)['dispositions'][-1]
    # Drawing visits PRIMA and DOPO alternately for every cell in each grid.
    expected = []
    for before, after in ((0, 0),) + plan.before_after:
        for a, b in zip(d['dispositions'][before], d['dispositions'][after]):
            expected.extend((a, b))
    assert cards[:216] == expected


def test_geometry_and_fixed_size_wrapping():
    assert LAYOUT.matrix_cell * 27 == 175.5
    assert LAYOUT.card_row_height * 9 == 252
    fonts = pdf._ensure_fonts()
    from reportlab.pdfbase.pdfmetrics import stringWidth
    text = 'SDC⊗CSD⊗CDS ' * 8
    lines = wrap_text(text, 73, fonts[0], 9)
    assert ''.join(lines).replace(' ', '') == text.replace(' ', '')
    assert all(stringWidth(line, fonts[0], 9) <= 73 for line in lines)
    for params in (CLASSIC, GENERAL):
        p = measured(params)
        assert all(b.size >= 8.5 for b in p.texts)


def test_two_normal_blocks_and_indivisible_overflow():
    available = LAYOUT.available_height(841.8897638)
    normal = measured(CLASSIC).height
    assert normal == 346
    pages = paginate_heights([normal] * 4, available)
    assert [(p.start, p.end) for p in pages] == [(0, 2), (2, 4)]
    pages = paginate_heights([normal, available-normal+1], available)
    assert [(p.start, p.end) for p in pages] == [(0, 1), (1, 2)]
    with pytest.raises(ConfigurationTooTall):
        paginate_heights([available+1], available)


def test_real_text_growth_moves_second_config_to_next_page(monkeypatch):
    # Three different J triples require three separate, fully written gestures.
    tall = [GENERAL[0], GENERAL[1][:3]+('R_U', 'I_3', 'R_U'),
            GENERAL[2][:3]+('I_3', 'I_3', 'R_U')]
    normal = measured(CLASSIC).height
    larger = measured(tall).height
    assert normal + LAYOUT.config_gap + larger > LAYOUT.available_height(841.8897638)
    doc = document([CLASSIC, tall])
    assert len(doc.pages) == 2
    assert 'D#0' in doc.pages[0].extract_text()
    assert 'D#1' not in doc.pages[0].extract_text()
    assert 'D#1' in doc.pages[1].extract_text()
    assert 'Configurazione completa' in doc.pages[1].extract_text()


@pytest.mark.parametrize('count', [0, 3, 8, 9, 15])
def test_transpose_count_first_eight_and_remainder(count):
    text = document([CLASSIC], [[f'E#{i}' for i in range(count)]]).pages[0].extract_text()
    assert f'Totale nel filtro: {count}' in text
    for i in range(min(8, count)):
        assert f'E#{i}' in text
    assert 'E#8' not in text
    if count > 8:
        assert tr('export.document.pdf.transpose_more_one') in text if count == 9 else (
            tr('export.document.pdf.transpose_more', count=count-8) in text)
    else:
        assert '+1 altra' not in text and 'altre' not in text
    assert 'T inversa' in text


def test_compact_inverse_annotations_preserve_exact_count():
    identity = [('SCD_U',)*3+('I_3',)*3]*3
    params = [identity]*20
    _, full = pdf.annotate_like_c(params)
    _, compact = pdf.annotate_like_c(params, compact=True)
    assert [t.total for t in compact] == [len(t) for t in full]
    assert [t.shown for t in compact] == [tuple(t[:8]) for t in full]
    assert all(len(t.shown) <= 8 for t in compact)
    assert compact[0].total == 20
    assert compact[0] is compact[-1]


def test_parallel_chunks_follow_measured_pages_and_global_numbers(tmp_path, monkeypatch):
    reader = pytest.importorskip('pypdf').PdfReader
    tall = [GENERAL[0], GENERAL[1][:3]+('R_U', 'I_3', 'R_U'),
            GENERAL[2][:3]+('I_3', 'I_3', 'R_U')]
    params = [CLASSIC, CLASSIC, tall, GENERAL, CLASSIC, GENERAL]
    labels, refs = pdf.annotate_like_c(params, compact=True)
    monkeypatch.setattr(pdf, '_prepare', lambda *a, **kw: (params, labels, refs))
    monkeypatch.setattr(pdf, '_filter_summary', lambda filters: '')
    monkeypatch.setattr(pdf, 'plan_workers', lambda *a, **kw: (2, 3))
    tasks = []
    def inline(worker, source, workers, **kwargs):
        for task in source:
            tasks.append(task)
            yield worker(task)
    monkeypatch.setattr(pdf, 'imap_ordered', inline)
    seq, par = tmp_path/'s.pdf', tmp_path/'p.pdf'
    pdf.generate_detail_pdf(seq, [])
    pdf.generate_detail_pdf_parallel(par, [], n_workers=2)
    a, b = reader(seq), reader(par)
    assert [p.extract_text() for p in a.pages] == [p.extract_text() for p in b.pages]
    assert sum(len(t[1]) for t in tasks) == len(params)
    assert all(len(ref.shown) <= 8 for t in tasks for ref in t[3])
    pages = pdf._page_plan(params, refs)
    assert all(t[0]-1 in {p.start for p in pages} for t in tasks)


def test_large_progressive_does_not_assume_classical_limit():
    from pypdf import PdfReader
    buf = io.BytesIO()
    c, painter = pdf._new_detail_canvas(buf)
    pdf.render_detail_pages(c, [GENERAL], start_index=2001,
                            total_configurations=7776, painter=painter)
    c.save()
    text = PdfReader(io.BytesIO(buf.getvalue())).pages[0].extract_text()
    assert 'D#2000' in text and '2001 / 7776' in text


def test_misaligned_annotations_cannot_silently_drop_a_config():
    with pytest.raises(ValueError, match='aligned'):
        document([CLASSIC, GENERAL], [[]])


def test_real_pdf_a3_header_footer_legend_and_two_per_page():
    doc = document([CLASSIC]*4)
    assert len(doc.pages) == 2
    for number, page in enumerate(doc.pages, 1):
        assert float(page.mediabox.width) == pytest.approx(1190.551, abs=.001)
        assert float(page.mediabox.height) == pytest.approx(841.8898, abs=.001)
        text = page.extract_text()
        assert text.count('Configurazione completa') == 2
        assert text.count('Legenda comune') == 1
        assert text.count('Ordine ') == 2
        assert 'PDF dettagliato' in text and '4 configurazioni totali' in text
        assert f'Pagina {number} / 2' in text
        assert 'Versione 4.0.2' in text
        assert 'report' not in text.lower()


@pytest.mark.parametrize('language', ['it', 'en'])
def test_both_languages_use_explicit_values(language):
    set_language(language)
    text = document([CLASSIC, GENERAL]).pages[0].extract_text()
    assert tr('export.document.detail.configuration') in text
    assert tr('export.document.detail.physical') in text
    assert tr('export.document.detail.legend') in text
    assert 'Rᵤ' in text and 'I₃' in text
    if language == 'en':
        assert 'BEFORE' in text and 'AFTER' in text
        assert 'Rovesciamenti' not in text and 'Configurazione' not in text


def test_nessun_inchiostro_fuori_dai_margini(tmp_path):
    pdfium = pytest.importorskip('pypdfium2')
    import numpy as np
    path = tmp_path/'layout.pdf'
    params = [CLASSIC, GENERAL]
    labels, references = pdf.annotate_like_c(params)
    pdf._generate_sequential(path, params, labels, references)
    doc = pdfium.PdfDocument(str(path))
    for page in doc:
        bitmap = page.render(scale=1.5)
        g = np.asarray(bitmap.to_pil().convert('L'))
        m = 12
        assert all(not (band < 240).any() for band in
                   (g[:m,:],g[-m:,:],g[:,:m],g[:,-m:]))
        bitmap.close()
        page.close()
    doc.close()
