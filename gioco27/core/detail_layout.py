"""Measured A3 detailed cards: one geometry for classical and general inputs.

Coordinates are points from the top left of a configuration. Text wrapping
is planned once by ``measure_config`` and consumed unchanged by ``draw_config``.
Pagination retains only page ranges, never all matrices or drawing plans.
"""
from dataclasses import dataclass

from .gioco_reale import MESCOLAMENTO
from .parallel import _check_cancelled
from .permutations import R_label
from ..i18n import tr


@dataclass(frozen=True)
class DetailLayout:
    margin: float = 22
    content_top: float = 46
    bottom_margin: float = 44
    config_gap: float = 12
    legend_height: float = 24
    legend_gap: float = 10
    normal_height: float = 346
    bottom_padding: float = 6
    heading_font: float = 10
    data_font: float = 9
    caption_font: float = 8.5
    id_font: float = 12
    before_font: float = 8
    after_font: float = 8.5
    text_leading: float = 11
    page_header_baseline: float = 30
    page_header_rule: float = 35
    footer_baseline: float = 22
    footer_rule: float = 34
    config_header_baseline: float = 9
    config_header_rule: float = 20
    header_columns: tuple = (112, 234, 430, 855)
    general_order_width: float = 85
    header_gap: float = 12
    section_baseline: float = 37
    section_rule: float = 43
    caption_baseline: float = 54
    card_stack_width: float = 30
    card_column_width: float = 56 / 3
    card_row_height: float = 28
    grid_top: float = 65
    stage_x: tuple = (122, 298, 474)
    operation_x: tuple = (218, 394, 570)
    operation_width: float = 73
    math_x: float = 654
    math_width: float = 185
    table_top: float = 46
    table_row_height: float = 15
    table_label_width: float = 47
    board_top: float = 149
    board_title_top: float = 111
    board_cell_width: float = 22
    board_cell_height: float = 15
    board_gap: float = 9
    aces_title_top: float = 225
    aces_top: float = 248
    ace_row_height: float = 16
    ace_column_widths: tuple = (67, 48, 70)
    matrix_x: float = 855
    matrix_cell: float = 6.5
    transpose_x: float = 1050
    max_transposes: int = 8
    physical_top: float = 244
    sequence_top: float = 316
    sequence_gap: float = 15
    sequence_label_width: float = 53

    @property
    def page_width(self):
        from reportlab.lib.pagesizes import A3, landscape
        return landscape(A3)[0]

    @property
    def deck_width(self):
        return self.card_stack_width + 3 * self.card_column_width

    def available_height(self, page_height):
        return (page_height - self.content_top - self.bottom_margin
                - self.legend_height - self.legend_gap)


LAYOUT = DetailLayout()
PARAMETER_HEADINGS = ('P₀', 'P₁', 'P₂', 'J₀', 'J₁', 'J₂')
STAGE_FORMULA = 'Sᵢ = (P₂⊗P₁⊗P₀) ∘ MSC ∘ (J₂⊗J₁⊗J₀)'


@dataclass(frozen=True)
class TextBlock:
    x: float
    top: float
    lines: tuple
    size: float
    bold: bool = False
    tone: str = 'text'

    def bottom(self, layout):
        return self.top + len(self.lines) * layout.text_leading


@dataclass(frozen=True)
class ConfigPlan:
    height: float
    rows: tuple
    texts: tuple
    sequence_top: float
    before_after: tuple


@dataclass(frozen=True)
class PageSpan:
    start: int
    end: int


class ConfigurationTooTall(ValueError):
    """Fixed-size content cannot fit a page; do not clip or shrink it."""


def configuration_rows(params):
    """Chronological six-parameter rows, directly reversible to core names."""
    return tuple(tuple({'I_3': 'I₃', 'R_U': 'Rᵤ'}.get(p, p[:-2]) for p in stage)
                 for stage in params)


def wrap_text(text, width, font, size):
    """Wrap at fixed size, including long mathematical products, without loss."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split():
            candidate = (line + ' ' + word).strip()
            if stringWidth(candidate, font, size) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
                line = ''
            while stringWidth(word, font, size) > width:
                split = 1
                while (split < len(word)
                       and stringWidth(word[:split + 1], font, size) <= width):
                    split += 1
                if stringWidth(word[:split], font, size) > width:
                    raise ValueError('column narrower than one fixed-size glyph')
                lines.append(word[:split])
                word = word[split:]
            line = word
        if line:
            lines.append(line)
    return tuple(lines)


def reorder_description(sigla):
    if sigla == 'SCD':
        return tr('export.document.detail.unchanged')
    perm = MESCOLAMENTO[sigla]
    visited = set()
    cycles = []
    for start in range(3):
        if start in visited or perm[start] == start:
            continue
        cycle, current = [], start
        while current not in visited:
            visited.add(current)
            cycle.append('SCD'[current])
            current = perm[current]
        cycles.append('↔'.join(cycle) if len(cycle) == 2
                      else '→'.join(cycle + cycle[:1]))
    return ', '.join(cycles)


def physical_description(js):
    # Only the gestures documented in the approved previews are described
    # physically. Other triples retain their explicit structural instructions.
    if js == ('I_3',) * 3:
        key = 'no_flip'
    elif js == ('R_U',) * 3:
        key = 'whole_flip'
    elif js == ('I_3', 'R_U', 'I_3'):
        key = 'packet_flip'
    else:
        key = 'general_gesture'
    return tr('export.document.detail.' + key)


def measure_config(params, transposes, *, fonts, classic_indices=None,
                   impilamenti=(None, None, None), layout=LAYOUT):
    """Measure text and prepare the exact lines used by the single renderer."""
    regular, bold = fonts
    rows = configuration_rows(params)
    texts = []

    def add(text, x, top, width, size=None, strong=False, tone='text'):
        size = layout.data_font if size is None else size
        lines = wrap_text(text, width, bold if strong else regular, size)
        block = TextBlock(x, top, lines, size, strong, tone)
        texts.append(block)
        return block.bottom(layout)

    if classic_indices is None:
        alias_x = layout.header_columns[1]
        width = (layout.page_width - layout.margin - layout.general_order_width
                 - layout.header_gap - alias_x)
        add(R_label(params), alias_x,
            layout.config_header_baseline - layout.data_font, width, tone='blue')

    operation_ends = []
    for stage, x, imp in zip(params, layout.operation_x, impilamenti):
        t = layout.grid_top - 1
        t = add(tr('export.document.detail.reversals'), x, t,
                layout.operation_width, layout.caption_font, True, 'blue') + 5
        flags = ' / '.join(tr('common.yes').upper() if j == 'R_U'
                           else tr('common.no').upper() for j in stage[3:])
        t = add(flags, x, t, layout.operation_width) + 3
        t = add('J₀ / J₁ / J₂', x, t, layout.operation_width,
                layout.caption_font, tone='muted') + 15
        t = add(tr('export.document.detail.reorders'), x, t,
                layout.operation_width, layout.caption_font, True, 'blue') + 4
        for heading, sig in zip(PARAMETER_HEADINGS[:3], stage[:3]):
            t = add(f'{heading}: {reorder_description(sig[:-2])}', x, t,
                    layout.operation_width) + 2
        if imp:
            t += 12
            t = add(tr('export.document.pdf.stacking').capitalize(), x, t,
                    layout.operation_width, layout.caption_font, True, 'blue') + 4
            t = add(imp, x, t, layout.operation_width)
        operation_ends.append(t)

    # Fattori di T occupies the reclaimed space below stage 2 operations.
    x = layout.operation_x[2]
    t = max(224, operation_ends[2] + 9)
    t = add(tr('export.document.detail.factors'), x, t,
            layout.operation_width, layout.heading_font, True, 'blue') + 3
    if classic_indices is not None:
        t = add(tr('export.document.detail.chronological'), x, t,
                layout.operation_width)
        t = add(' × '.join(f'M[{i}]' for i in reversed(classic_indices[:3])),
                x, t, layout.operation_width)
        t = add(tr('export.document.pdf.collections').capitalize() + ':',
                x, t, layout.operation_width)
        t = add(' × '.join(stage[2][:-2] for stage in params), x, t,
                layout.operation_width)
        t = add(tr('export.document.detail.stacking_short'), x, t,
                layout.operation_width)
        t = add(' × '.join(impilamenti), x, t, layout.operation_width)
    else:
        t = add(tr('export.document.detail.structural_factors'), x, t,
                layout.operation_width)
        for number, row in enumerate(rows):
            t = add(f'{number}: ' + '⊗'.join(reversed(row[:3])), x, t,
                    layout.operation_width)
    factors_end = t

    # Physical instructions grouped only for identical triples of J factors.
    t = layout.physical_top
    t = add(tr('export.document.detail.physical'), layout.matrix_x, t,
            layout.page_width - layout.margin - layout.matrix_x,
            layout.heading_font, True, 'blue') + 5
    groups = {}
    for number, stage in enumerate(params):
        groups.setdefault(tuple(stage[3:]), []).append(str(number))
    for js, numbers in groups.items():
        stages = ', '.join(numbers)
        instruction = tr('export.document.detail.stage_instruction_one'
                         if len(numbers) == 1 else
                         'export.document.detail.stage_instruction',
                         stages=stages, instruction=physical_description(js))
        t = add(instruction, layout.matrix_x, t,
                layout.page_width - layout.margin - layout.matrix_x) + 1
    physical_end = t

    count = transposes.total if hasattr(transposes, 'total') else len(transposes)
    t = layout.grid_top
    transpose_width = layout.page_width - layout.margin - layout.transpose_x
    t = add(tr('export.document.detail.transpose_total', count=count),
            layout.transpose_x, t, transpose_width) + 4
    for reference in list(transposes)[:layout.max_transposes]:
        t = add(reference, layout.transpose_x, t, transpose_width) + 3
    if count > layout.max_transposes:
        remaining = count - layout.max_transposes
        t = add(tr('export.document.pdf.transpose_more_one') if remaining == 1
                else tr('export.document.pdf.transpose_more', count=remaining),
                layout.transpose_x, t, transpose_width, tone='muted') + 3
    t += 12
    t = add(tr('export.document.detail.inverse_references'), layout.transpose_x,
            t, transpose_width, layout.caption_font, tone='muted')

    sequence_top = max(layout.sequence_top, physical_end + 5,
                       layout.aces_top + 4 * layout.ace_row_height + 4)
    height = max(layout.normal_height, factors_end + layout.bottom_padding,
                 sequence_top + layout.sequence_gap + layout.data_font
                 + layout.bottom_padding, t + layout.bottom_padding,
                 max(operation_ends) + layout.bottom_padding)
    return ConfigPlan(height, rows, tuple(texts), sequence_top,
                      tuple((s, s + 1) for s in range(3)))


def paginate_heights(heights, available, gap=LAYOUT.config_gap):
    """Whole configurations only; no fixed number of slots per page."""
    pages, start, used, end = [], 0, 0.0, 0
    for end, height in enumerate(heights, 1):
        if height > available:
            raise ConfigurationTooTall(f'{height:.1f} > {available:.1f} pt')
        needed = height + (gap if used else 0)
        if used and used + needed > available:
            pages.append(PageSpan(start, end - 1))
            start, used = end - 1, 0.0
        used += height + (gap if used else 0)
    if end:
        pages.append(PageSpan(start, end))
    return tuple(pages)


def plan_pages(params_list, transposes, *, fonts, indices, impilamenti,
               page_height, layout=LAYOUT, annullato=None):
    def heights():
        for params, trans in zip(params_list, transposes):
            _check_cancelled(annullato)
            yield measure_config(params, trans, fonts=fonts,
                                 classic_indices=indices(params),
                                 impilamenti=tuple(impilamenti(p) for p in params),
                                 layout=layout).height
    return paginate_heights(heights(), layout.available_height(page_height),
                            layout.config_gap)


def draw_config(c, plan, data, *, top, number, total, params, classic_indices,
                painter, fonts, card, inverse_rows, layout=LAYOUT):
    """Draw the previously measured plan. No wrapping, fitting or shrinking."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A3, landscape
    _, page_height = landscape(A3)
    regular, bold = fonts
    ink = colors.Color(.09, .239, .325)
    blue = colors.Color(.18, .38, .49)
    muted = colors.Color(.388, .463, .518)
    border = colors.Color(.682, .757, .804)
    light = colors.Color(.937, .957, .969)
    red = colors.Color(.8, 0, 0)
    tones = {'text': colors.black, 'blue': blue, 'muted': muted}

    def text(s, x, y, size=layout.data_font, strong=False, fill=colors.black,
             center=False):
        c.setFillColor(fill)
        c.setFont(bold if strong else regular, size)
        (c.drawCentredString if center else c.drawString)(x, page_height-top-y, s)

    def cell(x, y, width, height, fill=colors.white):
        c.setFillColor(fill)
        c.setStrokeColor(border)
        c.setLineWidth(.35)
        c.rect(x, page_height-top-y-height, width, height, fill=1, stroke=1)

    def rule(y, x0, x1):
        c.setStrokeColor(border)
        c.setLineWidth(.4)
        c.line(x0,page_height-top-y,x1,page_height-top-y)

    progress_x, alias_x, reversal_x, order_x = layout.header_columns
    header_y = layout.config_header_baseline
    text(f'D#{number}', layout.margin, header_y, layout.id_font, True, ink)
    text(f'{number+1} / {total}',progress_x,header_y,fill=muted)
    if classic_indices is not None:
        alias = 'P[%d][%d][%d][%d]' % classic_indices
        text(tr('export.document.detail.game_alias', alias=alias),alias_x,header_y,
             strong=True,fill=ink)
        text(tr('export.document.detail.core_reversal', index=classic_indices[3]),
             reversal_x,header_y,layout.caption_font,fill=muted)
        formula = 'T = S₂ ∘ S₁ ∘ S₀'
        text(formula,layout.page_width-layout.margin-c.stringWidth(formula,regular,layout.data_font),header_y,
             fill=ink)
    else:
        order_x = layout.page_width - layout.margin - layout.general_order_width
    text(tr('export.document.detail.order', value=data['period']),order_x,header_y,
         strong=True,fill=ink)
    rule(layout.config_header_rule,layout.margin,layout.page_width-layout.margin)

    def deck(before, after, x):
        stack, cw, rh = (layout.card_stack_width, layout.card_column_width,
                         layout.card_row_height)
        for row in range(9):
            t = layout.grid_top + row*rh
            cell(x,t,stack,rh,light)
            for col in range(3):
                cell(x+stack+col*cw,t,cw,rh)
                ch = before[row*3+col]
                s,is_red = card(ch)
                text(s,x+stack/2,t+9+8*col,layout.before_font,
                     fill=red if is_red else colors.black,center=True)
                ch = after[row*3+col]
                s,is_red = card(ch)
                text(s,x+stack+(col+.5)*cw,t+rh/2+3,
                     layout.after_font,fill=red if is_red else colors.black,
                     center=True)

    text(tr('export.document.detail.initial_state'),layout.margin,layout.section_baseline,
         layout.heading_font,True,ink)
    rule(layout.section_rule,layout.margin,layout.margin+layout.deck_width)
    text(tr('export.document.detail.deck'),layout.margin+layout.card_stack_width/2,
         layout.caption_baseline,layout.caption_font,True,blue,True)
    text(tr('export.document.detail.view'),layout.margin+layout.card_stack_width
         +1.5*layout.card_column_width,layout.caption_baseline,layout.caption_font,fill=blue,center=True)
    deck(data['dispositions'][0],data['dispositions'][0],layout.margin)
    for s,x in enumerate(layout.stage_x):
        title=tr('export.document.detail.stage_title',number=s)
        if classic_indices is not None:
            title += ' · ' + params[s][2][:-2]
        text('→',x-12,layout.section_baseline,fill=muted)
        text(title,x,layout.section_baseline,layout.heading_font,True,ink)
        rule(layout.section_rule,x,layout.operation_x[s]+layout.operation_width)
        text(tr('export.document.detail.before'),x+layout.card_stack_width/2,
             layout.caption_baseline,layout.caption_font,True,blue,True)
        text(tr('export.document.detail.after'),x+layout.card_stack_width
             +1.5*layout.card_column_width,layout.caption_baseline,layout.caption_font,True,blue,True)
        text(tr('export.document.detail.operations'),layout.operation_x[s],layout.caption_baseline,
             layout.caption_font,True,blue)
        before,after=plan.before_after[s]
        deck(data['dispositions'][before],data['dispositions'][after],x)

    text(tr('export.document.detail.configuration'),layout.math_x,layout.section_baseline,
         layout.heading_font,True,ink)
    column_width=(layout.math_width-layout.table_label_width)/6
    widths=(layout.table_label_width,)+(column_width,)*6
    rows=(('',)+PARAMETER_HEADINGS,)+tuple(
        (tr('export.document.detail.stage_title',number=s),)+row
        for s,row in enumerate(plan.rows))
    for row_index,row in enumerate(rows):
        x=layout.math_x
        for col_index,(s,width) in enumerate(zip(row,widths)):
            y=layout.table_top+row_index*layout.table_row_height
            cell(x,y,width,layout.table_row_height,
                 light if not row_index or not col_index else colors.white)
            text(s,x+width/2,y+10.5,
                 layout.caption_font if not row_index else layout.data_font,
                 not row_index,ink,True)
            x+=width

    def board(x,rows,title,inverse=False):
        text(title,x,layout.board_title_top+8,layout.heading_font,True,
             red if inverse else blue)
        cw,ch=layout.board_cell_width,layout.board_cell_height
        grid_width=(4 if inverse else 3)*cw
        x+=(c.stringWidth(title,bold,layout.heading_font)-grid_width)/2
        y=layout.board_top
        if not inverse:
            for col,s in enumerate(('A1','A2','A3')):
                cell(x+col*cw,y,cw,ch)
                text(s,x+(col+.5)*cw,y+11,layout.data_font,True,center=True)
            y+=ch
        for row,line in enumerate(rows):
            if inverse:
                cell(x,y+row*ch,cw,ch)
                text(('M2','M1','M0')[row],x+cw/2,y+row*ch+11,
                     layout.caption_font,True,red,True)
            for col,s in enumerate(line):
                xx=x+(col+(1 if inverse else 0))*cw
                cell(xx,y+row*ch,cw,ch)
                text(s,xx+cw/2,y+row*ch+11,layout.data_font,True,center=True)
    board(layout.math_x,tuple(tuple(data['markers'][a][3][r] for a in range(3))
                              for r in range(3)),
          tr('export.document.detail.board_t'))
    board(layout.math_x+4*layout.board_cell_width+layout.board_gap,inverse_rows,tr('export.document.detail.board_inverse'),
          inverse=True)

    text(tr('export.document.detail.aces'),layout.math_x,layout.aces_title_top+8,
         layout.heading_font,True,blue)
    headers=(tr('export.document.detail.ace'),tr('export.document.detail.position'),
             tr('export.document.detail.sector'))
    ace_rows=(headers,)+tuple((f'A{a} · {card(m[0])[0]}',str(m[2]),m[3])
                             for a,m in enumerate(data['markers'],1))
    for row,row_values in enumerate(ace_rows):
        x=layout.math_x
        for col,(s,width) in enumerate(zip(row_values,layout.ace_column_widths)):
            y=layout.aces_top+row*layout.ace_row_height
            cell(x,y,width,layout.ace_row_height,light if not row else colors.white)
            text(s,x+width/2,y+11,layout.caption_font if not row else layout.data_font,
                 not row or col>0,red if row==3 else colors.black,True)
            x+=width

    text(tr('export.document.detail.matrix'),layout.matrix_x,layout.section_baseline,
         layout.heading_font,True,blue)
    painter.draw('mdet',data['T_matrix'],layout.matrix_x,
                 page_height-top-layout.grid_top,fill=colors.Color(0,.5,0),
                 background=colors.white)
    text(tr('export.document.detail.transposes'),layout.transpose_x,layout.section_baseline,
         layout.heading_font,True,blue)
    for block in plan.texts:
        for n,line in enumerate(block.lines):
            text(line,block.x,block.top+block.size+n*layout.text_leading,
                 block.size,block.bold,tones[block.tone])

    for s,(key,deck_value) in enumerate((('initial',data['dispositions'][0]),
                                        ('final',data['dispositions'][-1]))):
        y=plan.sequence_top+layout.data_font+s*layout.sequence_gap
        text(tr('export.document.detail.'+key),layout.math_x,y,layout.data_font,True,blue)
        x=layout.math_x+layout.sequence_label_width
        for ch in deck_value:
            value,is_red=card(ch)
            text(value,x,y,layout.data_font,fill=red if is_red else colors.black)
            x+=c.stringWidth(value,regular,layout.data_font)+2


def draw_page_chrome(c, *, total, summary, page, pages, fonts, layout=LAYOUT):
    from reportlab.lib.pagesizes import A3, landscape
    from reportlab.lib import colors
    from .. import __version__
    w,h=landscape(A3)
    regular,bold=fonts
    ink=colors.Color(.09,.239,.325)
    muted=colors.Color(.388,.463,.518)
    light=colors.Color(.937,.957,.969)
    border=colors.Color(.682,.757,.804)

    def text(s,x,y,size=layout.caption_font,strong=False):
        c.setFont(bold if strong else regular,size)
        c.setFillColor(ink if strong else muted)
        c.drawString(x,h-y,s)

    text(tr('export.document.detail.page_title'),layout.margin,layout.page_header_baseline,layout.heading_font,True)
    heading=tr('export.document.detail.total',total=total)+(' | '+summary if summary else '')
    # Summaries are deliberately short; wrap rather than changing the font.
    for n,line in enumerate(wrap_text(heading,w-250,regular,layout.data_font)):
        text(line,w-layout.margin-c.stringWidth(line,regular,layout.data_font),
             layout.page_header_baseline+n*layout.text_leading,layout.data_font)
    c.setStrokeColor(border)
    c.setLineWidth(.4)
    c.line(layout.margin,h-layout.page_header_rule,w-layout.margin,h-layout.page_header_rule)
    legend_top=h-layout.bottom_margin-layout.legend_height
    c.setFillColor(light)
    c.rect(layout.margin,h-legend_top-layout.legend_height,w-2*layout.margin,
           layout.legend_height,fill=1,stroke=0)
    text(tr('export.document.detail.legend'),layout.margin+6,legend_top+9,layout.caption_font,True)
    text(tr('export.document.detail.legend_levels'),134,legend_top+9)
    text(tr('export.document.detail.legend_reading'),layout.margin+6,legend_top+21)
    text(STAGE_FORMULA,layout.math_x,legend_top+21)
    c.line(layout.margin,layout.footer_rule,w-layout.margin,layout.footer_rule)
    text(tr('export.document.detail.version',version=__version__),layout.margin,h-layout.footer_baseline)
    footer=tr('export.document.detail.page_number',page=page,pages=pages)
    text(footer,w-layout.margin-c.stringWidth(footer,regular,layout.caption_font),h-layout.footer_baseline)
