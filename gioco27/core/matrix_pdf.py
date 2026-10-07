"""One A3 landscape page per configuration; shared by both export routes."""
from collections import Counter
from itertools import product

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape

from .analysis import cycle_decomposition, order_of
from .detail import inverse_perm, marker_positions
from .detail_pdf import _c_indices, _ensure_fonts, _j_key, _p_key
from .parallel import ExportAnnullato
from .permutations import (MAT3_J, MAT3_P, R_label, compute_R,
                           compute_stage, mat_to_perm27, stage_label)
from .pdfgrid import GridPainter, GridSpec
from .. import __version__
from ..i18n import tr


def ordered_configurations(filters):
    """Lazy C/detail ordering, with only the three stage domains in memory."""
    from .combinations import normalizza_filtri
    groups = []
    for stage in normalizza_filtri(filters):
        grouped = {}
        for option in sorted(stage.combinazioni(), key=lambda p: (_p_key(p), _j_key(p))):
            grouped.setdefault(option[:3], []).append(option[3:])
        groups.append(grouped)
    for p2, p1, p0 in product(groups[2], groups[1], groups[0]):
        for j0, j1, j2 in product(groups[0][p0], groups[1][p1], groups[2][p2]):
            yield [p0+j0, p1+j1, p2+j2]


def painter_for(c):
    return GridPainter(c, [
        GridSpec('m3', 7.5, 3, thin_w=.25),
        GridSpec('m27', 4.4, 27, thin_w=.12, thick_at=(9, 18), thick_w=.75),
        GridSpec('stage', 5.5, 27, thin_w=.12, thick_at=(9, 18), thick_w=.75),
        GridSpec('final', 6, 27, thin_w=.12, thick_at=(9, 18), thick_w=.75),
    ])


def render(c, params_list, start_index=1, progress_cb=None, painter=None,
           annullato=None, total=None):
    """Number D# in the filtered C-ordered set, exactly as the detail export."""
    w, h = landscape(A3)
    regular, bold = _ensure_fonts()
    painter = painter or painter_for(c)
    ink = colors.Color(.12, .27, .34)
    muted = colors.Color(.40, .51, .59)
    border = colors.Color(.72, .81, .86)
    light = colors.Color(.94, .97, .98)
    cw = (w-48-30)/3

    def text(s, x, y, size=9, strong=False, fill=ink, center=False):
        c.setFillColor(fill)
        c.setFont(bold if strong else regular, size)
        (c.drawCentredString if center else c.drawString)(x, h-y, s)

    def box(x, y, width, height, fill=colors.white):
        c.setFillColor(fill)
        c.setStrokeColor(border)
        c.setLineWidth(.35)
        c.rect(x, h-y-height, width, height, fill=1, stroke=1)

    def rule(y, left=24, right=None):
        c.setStrokeColor(border)
        c.setLineWidth(.4)
        c.line(left, h-y, right or w-24, h-y)

    def wrapped(s, x, y, width, size=9, leading=12):
        words, line = s.split(), ''
        for word in words:
            candidate = (line+' '+word).strip()
            if line and c.stringWidth(candidate, regular, size) > width:
                text(line, x, y, size)
                y += leading
                line = word
            else:
                line = candidate
        if line:
            text(line, x, y, size)
        return y+leading

    count = 0
    for number, params in enumerate(params_list, start_index-1):
        stages = [compute_stage(*p) for p in params]
        matrix = compute_R(stages)
        perm = mat_to_perm27(matrix)
        cycles = cycle_decomposition(perm)
        alias = _c_indices(params)
        text(tr('menu.pdf_matrix'), 24, 38, 14, True)
        header = f'D#{number}   |   {number+1} / {total if total is not None else "?"}'
        if alias is not None:
            header += '   |   '+tr('export.document.detail.game_alias', alias='P[%d][%d][%d][%d]' % alias)
            header += '   |   '+tr('export.document.detail.core_reversal', index=alias[3])
        else:
            header += '   |   '+tr('export.document.matrix.general')
        text(header, 24, 58, 10, True)
        text(R_label(params).replace(' x ', ' ⊗ ').replace(' o ', ' ∘ '), 24, 78, 9)
        rule(90)
        for i, (p, mats) in enumerate(zip(params, stages)):
            x = 24+i*(cw+15)
            box(x, 102, cw, 440)
            box(x, 102, cw, 25, light)
            text(tr('export.document.matrix.stage', index=i), x+12, 119, 11, True)
            formula = stage_label(i, *p).split(' = ', 1)[1]
            text('S'+'₀₁₂'[i]+' = '+formula.replace(' x ', ' ⊗ ').replace(' o ', ' ∘ '), x+12, 143, 9)
            for k, name in enumerate(p):
                px = x+12+(k+.5)*(cw-24)/6
                label = ('P' if k < 3 else 'J')+'₀₁₂'[k % 3]
                pretty = name.replace('_U', '').replace('I_3', 'I₃').replace('R', 'Rᵤ')
                text(label+' · '+pretty, px, 167, 9, True, center=True)
                painter.draw('m3', (MAT3_P if k < 3 else MAT3_J)[name], px-11.25, h-174)
            rule(209, x+12, x+cw-12)
            for k in range(2):
                px = x+cw*(.25+.5*k)
                text(('P' if k == 0 else 'J')+'⁽'+'⁰¹²'[i]+'⁾ · 27×27', px, 225, 9, True, center=True)
                painter.draw('m27', mats[k], px-59.4, h-235)
            text(tr('export.document.matrix.stage_result', index='₀₁₂'[i]), x+cw/2, 368, 10, True, center=True)
            painter.draw('stage', mats[2], x+(cw-148.5)/2, h-378)
        rule(555)
        text(tr('export.document.matrix.final'), 24, 575, 11, True)
        painter.draw('final', matrix, 24, h-584)
        text(tr('export.document.matrix.summary'), 230, 575, 11, True)
        text(tr('export.document.detail.order', value=order_of(perm)), 230, 597, 10, True)
        wrapped(tr('export.document.matrix.order_definition'), 230, 613, 250, 8.5, 11)
        text(tr('export.document.matrix.fixed', count=sum(i == d for i, d in enumerate(perm))), 230, 639)
        text(tr('export.document.matrix.involutive', value=tr('export.document.matrix.yes' if perm == inverse_perm(perm) else 'export.document.matrix.no')), 230, 655)
        text(tr('export.document.detail.aces')+' · 0-26', 230, 680, 9, True)
        widths = (135, 53, 62)
        headings = [tr('export.document.detail.ace'), tr('export.document.detail.position'), tr('export.document.detail.sector')]
        rows = [headings]+[[f'A{k+1} · {suit}', str(pos), sector] for k, ((_, _, pos, sector), suit) in enumerate(zip(marker_positions(perm), ['A♠', 'A♣', 'A♥']))]
        for row, values in enumerate(rows):
            px = 230
            for width, value in zip(widths, values):
                box(px, 689+16*row, width, 16, light if row == 0 else colors.white)
                text(value, px+width/2, 700+16*row, 9, row == 0, colors.red if row == 3 else ink, True)
                px += width
        text(tr('export.document.matrix.mapping'), 496, 575, 11, True)
        text(tr('export.document.matrix.mapping_note'), 496, 595, 9, fill=muted)
        width = (w-24-496)/9
        for origin, dest in enumerate(perm):
            row, col = divmod(origin, 9)
            box(496+col*width, 604+row*16, width, 16)
            text(f'{origin} → {dest}', 496+(col+.5)*width, 615+row*16, 9, center=True)
        text(tr('export.document.matrix.cycles'), 496, 674, 11, True)
        y = wrapped(' '.join('('+' '.join(map(str, cycle))+')' for cycle in cycles), 496, 693, w-520)
        lengths = Counter(map(len, cycles))
        text('; '.join(tr('export.document.matrix.cycle_count', count=n, length=length) for length, n in sorted(lengths.items())), 496, y, 8.5, fill=muted)
        text(tr('export.document.matrix.lcm'), 496, y+13, 9)
        box(24, 758, w-48, 44, light)
        for line, key in enumerate(('reading', 'levels', 'composition', 'sectors')):
            text(tr('export.document.matrix.legend_'+key), 32, 768+line*10.5, 8.5, fill=muted)
        rule(809)
        text(tr('export.document.detail.version', version=__version__), 24, 824, 8.5, fill=muted)
        footer = tr('export.document.detail.page_number', page=number+1, pages=total if total is not None else '?')
        text(footer, w-24-c.stringWidth(footer, regular, 8.5), 824, 8.5, fill=muted)
        c.showPage()
        count += 1
        if progress_cb:
            progress_cb(number+1)
        if annullato is not None and annullato():
            raise ExportAnnullato(count, total or 0)
    return count
