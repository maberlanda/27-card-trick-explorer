"""
ProtocolDialog: genera e apre nel browser un documento HTML stampabile,
completo e didattico, con il protocollo del trucco delle 27 carte.

Sezioni (ognuna attivabile dal dialog):
  1. Il trucco in sintesi
  2. Legenda dei simboli GEN3
  3. Fasi dettagliate per il presentatore (con i tre livelli f3/f2/f1)
  4. Verifica pratica (mazzo numerato 1..27 prima/dopo)
  5. Struttura ciclica (cicli colorati, punti fissi, significato del periodo)
  6. Tabelle delle permutazioni T e T⁻¹
  7. Matrice 27×27
  8. Perché funziona (la matematica in breve)
"""
import tkinter as tk
from tkinter import ttk, messagebox
from .help_banner import HelpBanner
from .i18n import tr
from .i18n import get_language
import webbrowser
import tempfile
import os
import html as _html

from ..core.constants import PERM3
from ..core.analysis import cycle_decomposition, order_of
from ..core.kronecker import decomposition_perm, decomposition_context

# Palette per i cicli (riusa i colori del tab Cicli)
_CYCLE_COLORS = ["#4E79A7", "#E15759", "#59A14F", "#B07AA1", "#F28E2B",
                 "#76B7B2", "#EDC948", "#FF9DA7", "#9C755F", "#1F77B4",
                 "#D62728", "#2CA02C", "#9467BD", "#8C564B", "#E377C2"]

# Descrizione fisica dei sei elementi GEN3 (come ordine di raccolta colonne)
_GEN3_INFO = {
    "SCD_U": ("[0,1,2]", "export.document.protocol.gen3.identity", "export.document.protocol.self", 1),
    "SDC_U": ("[0,2,1]", "export.document.protocol.gen3.swap_center_right", "export.document.protocol.self", 2),
    "CSD_U": ("[1,0,2]", "export.document.protocol.gen3.swap_left_center", "export.document.protocol.self", 2),
    "CDS_U": ("[1,2,0]", "export.document.protocol.gen3.rotate_forward", "DSC_U", 3),
    "DSC_U": ("[2,0,1]", "export.document.protocol.gen3.rotate_backward", "CDS_U", 3),
    "DCS_U": ("[2,1,0]", "export.document.protocol.gen3.swap_left_right", "export.document.protocol.self", 2),
}


def _compose(a, b):
    """(a∘b)[i] = a[b[i]]"""
    return [a[b[i]] for i in range(len(a))]


def _kron27(f3, f2, f1):
    """Permutazione 27 di f3⊗f2⊗f1 (nomi GEN3)."""
    a, b, c = PERM3[f3], PERM3[f2], PERM3[f1]
    return [9 * a[i // 9] + 3 * b[(i // 3) % 3] + c[i % 3] for i in range(27)]


def _protocol_perm(decomp):
    """Permutazione eseguita dal protocollo: A2 ∘ MSC ∘ A1 ∘ MSC ∘ A0 ∘ MSC."""
    return decomposition_perm(decomp)


def _col_order(name: str) -> str:
    """Converte 'SCD_U' -> 'Sinistra → Centro → Destra'."""
    labels = (tr("export.document.protocol.left"),
              tr("export.document.protocol.center"),
              tr("export.document.protocol.right"))
    perm = list(PERM3[name])
    return " → ".join(labels[perm.index(destination)] for destination in range(3))


def _perm_to_html_table(perm: list, label: str) -> str:
    """Tabella HTML per una permutazione su 27, in 3 blocchi da 9."""
    blocks_html = ""
    for blk in range(3):
        start = blk * 9
        top = "".join(f"<td>{i}</td>" for i in range(start, start + 9))
        bot = "".join(f"<td>{perm[i]}</td>" for i in range(start, start + 9))
        gap = " style='border-top:2px solid #888'" if blk > 0 else ""
        blocks_html += (
            f"<tr{gap}><th>{tr('export.document.protocol.position_range', start=start, end=start + 8)}</th>{top}</tr>"
            f"<tr><th>→</th>{bot}</tr>"
        )
    return (
        f"<p style='margin-top:10px'><strong>{_html.escape(label)}</strong></p>"
        f"<table class='perm'>{blocks_html}</table>"
    )


def _deck_row_html(deck, highlight=None) -> str:
    """Riga di 27 celle (carte 1..27); highlight = set di posizioni 0-based."""
    cells = ""
    for j, v in enumerate(deck):
        hl = " class='hl'" if (highlight and j in highlight) else ""
        cells += f"<td{hl}>{v}</td>"
    return f"<table class='deck'><tr>{cells}</tr></table>"


def _matrix_svg(perm, size=270, label="T") -> str:
    """Matrice di permutazione 27×27 come SVG (cella piena: riga=perm[col])."""
    cell = size / 27
    rects = []
    for col, row in enumerate(perm):
        rects.append(
            f"<rect x='{col * cell:.1f}' y='{row * cell:.1f}' "
            f"width='{cell:.1f}' height='{cell:.1f}' fill='#27AE60'/>")
    grid = []
    for k in range(28):
        w = 2 if k % 9 == 0 else (1 if k % 3 == 0 else 0.4)
        c = "#333" if k % 9 == 0 else ("#777" if k % 3 == 0 else "#ccc")
        p = k * cell
        grid.append(f"<line x1='{p:.1f}' y1='0' x2='{p:.1f}' y2='{size}' "
                    f"stroke='{c}' stroke-width='{w}'/>")
        grid.append(f"<line x1='0' y1='{p:.1f}' x2='{size}' y2='{p:.1f}' "
                    f"stroke='{c}' stroke-width='{w}'/>")
    return (
        f"<figure class='mat'><svg width='{size}' height='{size}' "
        f"viewBox='0 0 {size} {size}' xmlns='http://www.w3.org/2000/svg'>"
        f"<rect width='{size}' height='{size}' fill='white'/>"
        + "".join(rects) + "".join(grid) +
        f"</svg><figcaption>{tr('export.document.protocol.matrix_caption', label=_html.escape(label))}</figcaption></figure>")


def _ai_phase_html(triple, stage_num: int) -> str:
    """Blocco HTML completo per la fase `stage_num` con A_i = (f3, f2, f1)."""
    f3, f2, f1 = triple
    ord_str = _col_order(f3)
    is_last = (stage_num == 3)

    livelli = []
    livelli.append(
        tr("export.document.protocol.phase.level_packets", value=_html.escape(f3),
           order=_html.escape(ord_str)))
    if f2 == "SCD_U":
        livelli.append(tr("export.document.protocol.phase.level_triples_identity"))
    else:
        livelli.append(
            tr("export.document.protocol.phase.level_triples", value=_html.escape(f2),
               effect=_html.escape(tr(_GEN3_INFO[f2][1]))))
    if f1 == "SCD_U":
        livelli.append(tr("export.document.protocol.phase.level_cards_identity"))
    else:
        livelli.append(
            tr("export.document.protocol.phase.level_cards", value=_html.escape(f1),
               effect=_html.escape(tr(_GEN3_INFO[f1][1]))))

    semplice = (f2 == "SCD_U" and f1 == "SCD_U")
    nota_semplice = (
        tr("export.document.protocol.phase.simple") if semplice else
        tr("export.document.protocol.phase.not_simple"))

    finale = tr("export.document.protocol.phase.final") if is_last else ""
    return f"""
    <div class='step s{stage_num}'>
      <p><span class='badge b{stage_num}'>{tr('export.document.protocol.phase.badge', number=stage_num)}</span>
         <strong>A{stage_num - 1} = ({_html.escape(f3)} ⊗ {_html.escape(f2)} ⊗ {_html.escape(f1)})</strong></p>
      <div class='istr'>
        {tr('export.document.protocol.phase.deal')}
        {tr('export.document.protocol.phase.ask')}
        {tr('export.document.protocol.phase.collect', order=_html.escape(ord_str))}
        {finale}
      </div>
      <p class='lvl-title'>{tr('export.document.protocol.phase.level_title', number=stage_num - 1)}</p>
      <ul class='lvl'>{''.join(livelli)}</ul>
      {nota_semplice}
    </div>"""


def generate_protocol_html(T_data: dict, options: dict = None) -> str:
    """
    Costruisce l'HTML del protocollo.

    T_data: perm, inverse_perm, label, period, decompositions, canonical_sym
    options (tutte True di default): sintesi, legenda, fasi, verifica,
                                     cicli, tabelle, matrice, matematica
    """
    o = dict(sintesi=True, legenda=True, fasi=True, verifica=True,
             cicli=True, tabelle=True, matrice=True, matematica=True)
    if options:
        o.update(options)

    perm     = T_data.get("perm") or list(range(27))
    inv_perm = T_data.get("inverse_perm") or list(range(27))
    label    = T_data.get("label", "T")
    period   = T_data.get("period")
    context = decomposition_context(T_data.get("decompositions"), perm, inv_perm)
    decomps = context["results"] if context else []
    can_sym  = T_data.get("canonical_sym")
    # Preferisci una decomposizione «a raccolta semplice» (f2=f1=identità in
    # tutte e tre le fasi): è quella eseguibile dal vivo senza riarrangiare
    # terzine o carte. In assenza, usa la prima disponibile.
    def _is_simple(d):
        return all(t[1] == "SCD_U" and t[2] == "SCD_U" for t in d)
    simple   = [d for d in decomps if _is_simple(d)]
    chosen   = (simple[0] if simple else (decomps[0] if decomps else None))
    chosen_is_simple = bool(simple)

    css = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', Arial, sans-serif; color: #222;
           background: #fff; padding: 24px 36px; max-width: 1140px; margin: auto; }
    h1 { font-size: 1.9em; color: #1a3a5c; margin-bottom: 4px; }
    h2 { font-size: 1.25em; color: #1a5c1a; margin: 30px 0 8px;
         border-bottom: 2px solid #dde; padding-bottom: 4px; }
    .meta  { color: #666; font-size: 0.9em; margin-bottom: 6px; }
    .kv    { display: inline-block; margin-right: 28px; }
    .lead  { font-size: 0.97em; color: #333; margin: 6px 0; }
    .invol { background: #FFF8E1; border-left: 4px solid #F9A825;
             padding: 8px 12px; border-radius: 4px; margin: 8px 0 12px;
             font-size: 0.95em; color: #5D4037; }
    .perm  { border-collapse: collapse; font-size: 0.73em;
             font-family: 'Courier New', monospace; margin: 6px 0 14px;
             overflow-x: auto; display: block; }
    .perm td, .perm th { border: 1px solid #ccc; padding: 2px 5px;
             text-align: center; font-family: 'Courier New', monospace; }
    .perm th { background: #f0f4f0; font-weight: bold; }
    .deck  { border-collapse: collapse; font-size: 0.72em;
             font-family: 'Courier New', monospace; margin: 4px 0 10px; }
    .deck td { border: 1px solid #bbb; padding: 2px 4px; min-width: 22px;
             text-align: center; }
    .deck td.hl { background: #FFF3B0; font-weight: bold; }
    .gen3  { border-collapse: collapse; font-size: 0.85em; margin: 8px 0 14px; }
    .gen3 td, .gen3 th { border: 1px solid #ccc; padding: 4px 10px; }
    .gen3 th { background: #f0f4f0; }
    .gen3 td.nm { font-family: monospace; font-weight: bold; }
    .step  { border: 1px solid #ddd; border-radius: 6px; padding: 13px 17px;
             margin: 11px 0; background: #fafafa; }
    .step.s1 { border-left: 5px solid #1a3a5c; }
    .step.s2 { border-left: 5px solid #1a5c1a; }
    .step.s3 { border-left: 5px solid #7B3F00; }
    .badge { display: inline-block; padding: 2px 10px; border-radius: 12px;
             font-weight: bold; font-size: 0.85em; color: #fff; margin-right: 8px; }
    .b1 { background: #1a3a5c; } .b2 { background: #1a5c1a; }
    .b3 { background: #7B3F00; }
    .formula { font-family: monospace; background: #f0f4ff;
               border: 1px solid #c8d8f8; border-radius: 4px;
               padding: 9px 15px; margin: 8px 0; font-size: 0.93em;
               white-space: pre-wrap; }
    .infobox { background: #fffbe6; border: 1px solid #f0c040;
               border-radius: 6px; padding: 11px 16px; margin: 10px 0; }
    .istr   { background: #f0fff0; border: 1px solid #a0d8a0;
              border-radius: 5px; padding: 10px 15px; margin: 8px 0;
              font-size: 0.93em; }
    .istr p { margin: 4px 0; }
    .lvl-title { margin-top: 10px; font-size: 0.92em; font-weight: bold;
              color: #1a3a5c; }
    .lvl    { margin: 4px 0 4px 22px; font-size: 0.92em; }
    .lvl li { margin: 3px 0; }
    .ok     { color: #1a7a1a; font-size: 0.9em; margin-top: 6px; }
    .warn   { color: #B26A00; font-size: 0.9em; margin-top: 6px; }
    .cyc    { font-family: monospace; font-size: 0.95em; margin: 3px 0; }
    .cyc .c { padding: 1px 6px; border-radius: 4px; color: #fff;
              margin-right: 6px; display: inline-block; }
    .fix    { background: #eee; color: #333 !important; }
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .mat    { display: inline-block; margin: 8px 24px 8px 0;
              text-align: center; }
    .mat figcaption { font-size: 0.78em; color: #555; max-width: 290px;
              margin-top: 4px; }
    @media (max-width: 700px) { .two-col { grid-template-columns: 1fr; } }
    @media print { body { padding: 8px; } .no-print { display: none; }
                   .perm { font-size: 0.62em; } h2 { page-break-after: avoid; } }
    """

    body = f"""
    <h1>{tr('export.document.protocol.title')}</h1>
    <p class='meta'>
      <span class='kv'>{tr('export.document.protocol.expression')}: <strong><code>{_html.escape(label)}</code></strong></span>
      {('<span class="kv">' + tr('export.document.protocol.period') + ': <strong>' + str(period) + '</strong></span>') if period else ''}
      {('<span class="kv">' + tr('export.document.protocol.canonical_form') + ': <strong>' + _html.escape(can_sym) + '</strong></span>') if can_sym else ''}
    </p>
    """

    if o["sintesi"]:
        body += tr("export.document.protocol.summary_html")

    if o["legenda"]:
        rows = ""
        for nm, (pv, desc, inv, ordn) in _GEN3_INFO.items():
            rows += (f"<tr><td class='nm'>{nm}</td><td>{pv}</td>"
                     f"<td>{_col_order(nm)}</td><td>{tr(desc)}</td>"
                     f"<td>{tr(inv) if inv.startswith('export.') else inv}</td><td>{ordn}</td></tr>")
        body += f"""
    <h2>{tr('export.document.protocol.legend_heading')}</h2>
    <p class='lead'>{tr('export.document.protocol.legend_intro')}</p>
    <table class='gen3'>
      <tr><th>{tr('export.document.protocol.name')}</th><th>{tr('export.document.protocol.permutation')}</th><th>{tr('export.document.protocol.collection_order')}</th>
          <th>{tr('export.document.protocol.effect')}</th><th>{tr('export.document.protocol.inverse')}</th><th>{tr('export.document.protocol.order')}</th></tr>
      {rows}
    </table>
    <p class='meta'>{tr('export.document.protocol.legend_note')}</p>
        """

    if o["fasi"]:
        body += f"<h2>{tr('export.document.protocol.phases_heading')}</h2>"
        if chosen:
            body += tr("export.document.protocol.preparation", count=len(decomps),
                       selection=tr("export.document.protocol.simple_decomposition") if chosen_is_simple else tr("export.document.protocol.first_decomposition"))
            a1, a2, a3 = chosen
            body += _ai_phase_html(a1, 1)
            body += _ai_phase_html(a2, 2)
            body += _ai_phase_html(a3, 3)
        else:
            body += tr("export.document.protocol.no_decomposition_html")

    if o["verifica"] and chosen:
        p_proto = _protocol_perm(chosen)
        inv_p   = [0] * 27
        for i, v in enumerate(p_proto):
            inv_p[v] = i
        final_deck = [inv_p[j] + 1 for j in range(27)]
        quale = tr("export.document.protocol.inverse_permutation") if context["inverse"] else tr("export.document.protocol.direct_permutation")
        hl = {j for j in range(27) if final_deck[j] == j + 1}
        body += f"""
    <h2>{tr('export.document.protocol.verification_heading')}</h2>
    <p class='lead'>{tr('export.document.protocol.verification_intro', permutation=quale)}</p>
    <p class='meta'>{tr('export.document.protocol.initial_deck')}</p>
    {_deck_row_html(list(range(1, 28)))}
    <p class='meta'>{tr('export.document.protocol.final_deck')}</p>
    {_deck_row_html(final_deck, highlight=hl)}
    <p class='meta'>{tr('export.document.protocol.highlighted_cells')}</p>
    <p class='lead'>{tr('export.document.protocol.reading_example', first=p_proto[0], middle=p_proto[13])}</p>
        """

    if o["cicli"]:
        cycles = cycle_decomposition(perm)
        ordr   = order_of(perm)
        fixed  = [c[0] for c in cycles if len(c) == 1]
        cyc_html = ""
        ci = 0
        for cyc in cycles:
            if len(cyc) == 1:
                continue
            color = _CYCLE_COLORS[ci % len(_CYCLE_COLORS)]
            ci += 1
            arrow = " → ".join(str(x) for x in cyc)
            cyc_html += (f"<p class='cyc'><span class='c' "
                         f"style='background:{color}'>len {len(cyc)}</span>"
                         f"({arrow} → {cyc[0]})</p>")
        if fixed:
            cyc_html += (f"<p class='cyc'><span class='c fix'>{tr('export.document.protocol.fixed_points')}</span>"
                         f"{', '.join(str(x) for x in fixed)}"
                         f" — {tr('export.document.protocol.fixed_note')}</p>")
        spiega = (tr("export.document.protocol.period_explanation", order=ordr)
                  if ordr else "")
        body += f"""
    <h2>{tr('export.document.protocol.cycles_heading')}</h2>
    <p class='lead'>{tr('export.document.protocol.cycles_intro', explanation=spiega)}</p>
    {cyc_html}
    <p class='meta'>{tr('export.document.protocol.cycles_order', order=ordr)}</p>
        """

    if o["tabelle"]:
        body += f"<h2>{tr('export.document.protocol.tables_heading')}</h2>"
        body += f"<p class='lead'>{tr('export.document.protocol.tables_intro')}</p>"
        is_involution = (perm == inv_perm)
        if is_involution:
            body += tr("export.document.protocol.involution")
        body += "<div class='two-col'>"
        body += _perm_to_html_table(perm, tr("export.document.protocol.direct_label"))
        body += _perm_to_html_table(inv_perm,
                                    tr("export.document.protocol.inverse_label") +
                                    ("  [= T]" if is_involution else ""))
        body += "</div>"

    if o["matrice"]:
        body += f"<h2>{tr('export.document.protocol.matrix_heading')}</h2>"
        body += f"<p class='lead'>{tr('export.document.protocol.matrix_intro')}</p>"
        body += _matrix_svg(perm, label="T")
        body += _matrix_svg(inv_perm, label="T⁻¹")

    if o["matematica"]:
        body += tr("export.document.protocol.mathematics_html")

    body += tr("export.document.protocol.footer_html")

    return f"""<!DOCTYPE html>
<html lang='{get_language()}'>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>{tr('export.document.protocol.title')} — {_html.escape(label)}</title>
<style>{css}</style>
</head>
<body>{body}</body>
</html>"""


class ProtocolDialog(tk.Toplevel):
    """Dialog per scegliere le sezioni e aprire il protocollo nel browser."""

    _SECTIONS = [
        ("sintesi",    "protocol.section.summary"),
        ("legenda",    "protocol.section.legend"),
        ("fasi",       "protocol.section.phases"),
        ("verifica",   "protocol.section.verification"),
        ("cicli",      "protocol.section.cycles"),
        ("tabelle",    "protocol.section.tables"),
        ("matrice",    "protocol.section.matrix"),
        ("matematica", "protocol.section.mathematics"),
    ]

    def __init__(self, parent, T_data: dict):
        super().__init__(parent)
        self._T_data = T_data
        self.title(tr("protocol.dialog.title"))
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text=tr("protocol.heading"),
                  font=("Segoe UI", 13, "bold"),
                  padding=(16, 14, 16, 4)).pack(anchor="w")
        ttk.Label(self,
                  text=tr("protocol.subtitle"),
                  font=("Segoe UI", 10),
                  foreground="#444", justify="left",
                  padding=(16, 2, 16, 10)).pack(anchor="w")

        HelpBanner(
            self,
            tr("protocol.help.short"),
            long=tr("protocol.help.long"),
            on_open_guide=getattr(self.master, "_open_guide", None),
        ).pack(fill="x", padx=16, pady=(0, 8))

        ttk.Separator(self).pack(fill="x")

        opt_fr = ttk.Frame(self, padding=(16, 10))
        opt_fr.pack(fill="x")
        self._vars = {}
        for key, label_key in self._SECTIONS:
            var = tk.BooleanVar(value=True)
            self._vars[key] = var
            ttk.Checkbutton(opt_fr, text=tr(label_key), variable=var).pack(
                anchor="w", pady=1)

        if not self._T_data.get("decompositions"):
            ttk.Label(self,
                      text=tr("protocol.no_decompositions"),
                      font=("Segoe UI", 9, "italic"),
                      foreground="#B26A00",
                      padding=(16, 4, 16, 4)).pack(anchor="w")

        ttk.Separator(self).pack(fill="x")

        bf = ttk.Frame(self, padding=(16, 12))
        bf.pack(fill="x")
        ttk.Button(bf, text=tr("protocol.open_browser"),
                   command=self._open_browser).pack(side="left", padx=(0, 8))
        ttk.Button(bf, text=tr("button.cancel"),
                   command=self.destroy).pack(side="left")

        ttk.Label(self,
                  text=tr("protocol.browser_hint"),
                  font=("Segoe UI", 9, "italic"),
                  foreground="#666",
                  padding=(16, 2, 16, 12)).pack(anchor="w")

    def _open_browser(self):
        options = {k: v.get() for k, v in self._vars.items()}
        html_content = generate_protocol_html(dict(self._T_data), options)
        try:
            import pathlib
            fd, path = tempfile.mkstemp(suffix=".html", prefix="gioco27_proto_")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(html_content)
            webbrowser.open(pathlib.Path(path).as_uri())
            self.destroy()
        except Exception as exc:
            messagebox.showerror(
                tr("error.generic"),
                tr("protocol.error.open", detail=exc),
                parent=self)
