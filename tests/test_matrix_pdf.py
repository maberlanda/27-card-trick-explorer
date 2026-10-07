"""Targeted content, ordering and worker checks for the matrix report."""
import io
import math
import re

import pytest

from gioco27.core.combinations import (
    _render_chunk_ex_to_bytes, generate_pdf_ex, iter_combinations_ex,
)
from gioco27.core.detail import combination_detail
from gioco27.core.detail_pdf import _c_indices, order_like_c
from gioco27.core.matrix_pdf import ordered_configurations
from gioco27.core.analysis import cycle_decomposition
from gioco27.i18n import CATALOGS, get_language, set_language, tr

CLASSIC = [
    ('SCD_U', 'SCD_U', 'CDS_U', 'I_3', 'I_3', 'I_3'),
    ('SCD_U', 'SCD_U', 'CSD_U', 'R_U', 'R_U', 'R_U'),
    ('SCD_U', 'SCD_U', 'SCD_U', 'I_3', 'I_3', 'I_3'),
]
GENERAL = [
    ('SDC_U', 'CSD_U', 'CDS_U', 'I_3', 'R_U', 'I_3'),
    ('DCS_U', 'SDC_U', 'CSD_U', 'I_3', 'R_U', 'I_3'),
    ('CSD_U', 'CDS_U', 'DCS_U', 'I_3', 'R_U', 'I_3'),
]


def filters(params):
    return [dict(zip(('p0', 'p1', 'p2', 'j0', 'j1', 'j2'), stage)) for stage in params]


@pytest.fixture(autouse=True)
def restore_language():
    language = get_language()
    yield
    set_language(language)


@pytest.mark.parametrize('language', ['it', 'en'])
@pytest.mark.parametrize('params', [CLASSIC, GENERAL])
def test_report_math_and_content(tmp_path, monkeypatch, language, params):
    from pypdf import PdfReader
    from reportlab.pdfgen.canvas import Canvas
    original = Canvas.drawString

    def checked(canvas, x, y, value, *args, **kwargs):
        assert 0 <= x and x+canvas.stringWidth(value) <= canvas._pagesize[0]
        assert 0 <= y <= canvas._pagesize[1]
        return original(canvas, x, y, value, *args, **kwargs)

    monkeypatch.setattr(Canvas, 'drawString', checked)
    set_language(language)
    target = tmp_path / 'matrix.pdf'
    assert generate_pdf_ex(target, filters(params)) == 1
    page = PdfReader(target).pages[0]
    text = ' '.join(page.extract_text().split())
    assert 'D#0' in text and '1 / 1' in text
    assert float(page.mediabox.width) > float(page.mediabox.height)
    assert tr('export.document.matrix.order_definition') in text
    assert tr('export.document.matrix.lcm') in text
    data = combination_detail(params)
    cycles = cycle_decomposition(data['T_perm'])
    assert data['period'] == math.lcm(*map(len, cycles)) == 6
    assert tr('export.document.detail.order', value=data['period']) in text
    assert tr('export.document.matrix.fixed', count=0) in text
    assert tr('export.document.matrix.involutive', value=tr('export.document.matrix.no')) in text
    for origin, dest in enumerate(data['T_perm']):
        assert f'{origin} → {dest}' in text
    for cycle in cycles:
        assert '('+' '.join(map(str, cycle))+')' in text
    for _, _, pos, sector in data['markers']:
        assert sector in text and str(pos) in text
    alias = _c_indices(params)
    if alias:
        assert 'P[%d][%d][%d][%d]' % alias in text and 'R[2]' in text
    else:
        assert 'P[' not in text and 'R[' not in text
        assert tr('export.document.matrix.general') in text
    assert len(re.findall(r'/FormXob\.m3 Do', page.get_contents().get_data().decode('latin1'))) == 18
    assert len(re.findall(r'/FormXob\.m27 Do', page.get_contents().get_data().decode('latin1'))) == 6


@pytest.mark.parametrize('uniform', [False, True])
def test_lazy_order_matches_detail(uniform):
    f = filters(GENERAL)
    for stage in f:
        stage.update(p2=['CDS_U', 'SDC_U'], j0=['R_U', 'I_3'], j_uniform=uniform)
    assert list(ordered_configurations(f)) == order_like_c(list(iter_combinations_ex(f)))


def test_chunk_global_numbering_and_identity():
    from pypdf import PdfReader
    identity = [('SCD_U',)*3+('I_3',)*3]*3
    text = PdfReader(io.BytesIO(_render_chunk_ex_to_bytes(3, [identity], 'en', 7))).pages[0].extract_text()
    assert 'D#2' in text and '3 / 7' in text
    assert 'Fixed points: 27 out of 27' in text
    assert 'Involutive (T = T⁻¹): YES' in text
    assert 'Order 1' in text
    assert '(0)' in text and '(26)' in text


def test_matrix_catalog_parity():
    keys = {k for k in CATALOGS['it'] if k.startswith('export.document.matrix.')}
    assert keys == {k for k in CATALOGS['en'] if k.startswith('export.document.matrix.')}
    assert CATALOGS['it']['menu.pdf_matrix'] == 'PDF matriciale'
    assert CATALOGS['en']['menu.pdf_matrix'] == 'Matrix PDF'
    assert CATALOGS['it']['menu.pdf_detailed'] == 'PDF dettagliato delle configurazioni'
    assert CATALOGS['en']['menu.pdf_detailed'] == 'Detailed configuration PDF'
    from gioco27.gui.guidance import tip
    for language in ('it', 'en'):
        set_language(language)
        assert tr('menu.pdf_matrix') in tip('general', 'menu.pdf_matrix')
        assert tr('menu.pdf_detailed') in tip('general', 'menu.pdf_detailed')


def test_small_parallel_matches_sequential(tmp_path, monkeypatch):
    from pypdf import PdfReader
    from gioco27.core import combinations
    set_language('en')
    f = filters(CLASSIC)
    f[0]['p2'] = ['SCD_U', 'CDS_U']
    f[1]['p2'] = ['SCD_U', 'CSD_U']
    # Four pages suffice to exercise two real workers, without a mass export.
    monkeypatch.setattr(combinations, 'COSTO_PAGINA_PDF', 1)
    seq, par = tmp_path/'seq.pdf', tmp_path/'par.pdf'
    assert combinations.generate_pdf_ex(seq, f) == 4
    assert combinations.generate_pdf_ex_parallel(par, f, n_workers=2) == 4
    texts = [[p.extract_text() for p in PdfReader(path).pages] for path in (seq, par)]
    assert texts[0] == texts[1]
    for i, text in enumerate(texts[1]):
        assert f'D#{i}' in text and f'{i+1} / 4' in text
