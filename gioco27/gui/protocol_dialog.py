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
    "SCD_U": ("[0,1,2]", "identità — non cambia nulla", "sé stesso", 1),
    "SDC_U": ("[0,2,1]", "scambia Centro ↔ Destra", "sé stesso", 2),
    "CSD_U": ("[1,0,2]", "scambia Sinistra ↔ Centro", "sé stesso", 2),
    "CDS_U": ("[1,2,0]", "rotazione S→C→D→S", "DSC_U", 3),
    "DSC_U": ("[2,0,1]", "rotazione S→D→C→S", "CDS_U", 3),
    "DCS_U": ("[2,1,0]", "scambia Sinistra ↔ Destra", "sé stesso", 2),
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
    labels = ("Sinistra", "Centro", "Destra")
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
            f"<tr{gap}><th>pos {start}–{start + 8}</th>{top}</tr>"
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
        f"</svg><figcaption>{_html.escape(label)} — cella verde in "
        f"(colonna i, riga {label}[i]): la carta in posizione i va in "
        f"posizione {label}[i]. Le linee scure delimitano i blocchi da 9 e "
        f"le terzine.</figcaption></figure>")


def _ai_phase_html(triple, stage_num: int) -> str:
    """Blocco HTML completo per la fase `stage_num` con A_i = (f3, f2, f1)."""
    f3, f2, f1 = triple
    ord_str = _col_order(f3)
    is_last = (stage_num == 3)

    livelli = []
    livelli.append(
        f"<li><strong>f₂ = {_html.escape(f3)}</strong> — agisce sui "
        f"<em>3 pacchetti da 9</em> (le colonne raccolte): "
        f"ordine di raccolta <strong>{_html.escape(ord_str)}</strong>.</li>")
    if f2 == "SCD_U":
        livelli.append("<li><strong>f₁ = SCD_U</strong> — identità: le 3 "
                       "terzine dentro ogni pacchetto restano in ordine.</li>")
    else:
        livelli.append(
            f"<li><strong>f₁ = {_html.escape(f2)}</strong> — permuta le "
            f"<em>3 terzine</em> dentro ogni pacchetto da 9 "
            f"({_html.escape(_GEN3_INFO[f2][1])}).</li>")
    if f1 == "SCD_U":
        livelli.append("<li><strong>f₀ = SCD_U</strong> — identità: le 3 "
                       "carte dentro ogni terzina restano in ordine.</li>")
    else:
        livelli.append(
            f"<li><strong>f₀ = {_html.escape(f1)}</strong> — permuta le "
            f"<em>3 carte</em> dentro ogni terzina "
            f"({_html.escape(_GEN3_INFO[f1][1])}).</li>")

    semplice = (f2 == "SCD_U" and f1 == "SCD_U")
    nota_semplice = (
        "<p class='ok'>✓ Fase a <strong>raccolta semplice</strong>: basta "
        "raccogliere le colonne nell'ordine indicato, senza altri "
        "riarrangiamenti.</p>" if semplice else
        "<p class='warn'>⚠ Fase NON a raccolta semplice: oltre all'ordine "
        "delle colonne servono i riarrangiamenti interni indicati da f₁/f₀ "
        "(più difficile da eseguire dal vivo).</p>")

    finale = ("<p>4. <strong>Fine del trucco</strong>: il mazzo è ora "
              "nell'ordine dato dalla permutazione del protocollo "
              "(vedi «Verifica pratica»).</p>" if is_last else "")
    return f"""
    <div class='step s{stage_num}'>
      <p><span class='badge b{stage_num}'>FASE {stage_num}</span>
         <strong>A{stage_num - 1} = ({_html.escape(f3)} ⊗ {_html.escape(f2)} ⊗ {_html.escape(f1)})</strong></p>
      <div class='istr'>
        <p>1. Distribuisci le 27 carte una alla volta, <em>da sinistra a
           destra</em>, in 3 colonne da 9 (questo è MSC: la carta in
           posizione p va nella colonna p&nbsp;mod&nbsp;3).</p>
        <p>2. Chiedi allo spettatore in quale colonna si trova la sua carta
           (Sinistra / Centro / Destra).</p>
        <p>3. Raccogli le colonne nell'ordine:
           <strong>{_html.escape(ord_str)}</strong>, dall'alto verso il basso
           del mazzo finale, senza invertire le carte dentro le colonne.</p>
        {finale}
      </div>
      <p class='lvl-title'>Cosa fa A{stage_num - 1}, livello per livello:</p>
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
    <h1>Protocollo — Gioco delle 27 Carte</h1>
    <p class='meta'>
      <span class='kv'>Espressione: <strong><code>{_html.escape(label)}</code></strong></span>
      {'<span class="kv">Periodo: <strong>' + str(period) + '</strong></span>' if period else ''}
      {'<span class="kv">Forma canonica: <strong>' + _html.escape(can_sym) + '</strong></span>' if can_sym else ''}
    </p>
    """

    if o["sintesi"]:
        body += """
    <h2>1 · Il trucco in sintesi</h2>
    <p class='lead'>Il trucco è una sequenza di <strong>3 turni identici nella
       forma</strong>: distribuire le 27 carte in 3 colonne da 9 (operazione
       <code>MSC</code>), chiedere allo spettatore in quale colonna è la sua
       carta, e raccogliere le colonne in un certo ordine (operazione
       <code>A</code>). Tutto l'effetto dipende dagli ordini di
       raccolta scelti.</p>
    <div class='formula'>P_protocollo  =  A2 ∘ MSC ∘ A1 ∘ MSC ∘ A0 ∘ MSC

si legge da DESTRA a SINISTRA:  prima MSC (1ª distribuzione),
poi A0 (1ª raccolta), poi MSC, A1, MSC e infine A2 (ultima raccolta).</div>
    <p class='lead'>Ogni posizione del mazzo (0–26) si scrive in base 3 con
       tre cifre (i₂,i₁,i₀): <em>pacchetto da 9 · terzina · carta nella
       terzina</em>. MSC ruota le tre cifre; ogni A le permuta
       indipendentemente. Tre distribuzioni «toccano» quindi tutte e tre le
       cifre: per questo bastano 3 turni per controllare qualunque posizione.</p>
        """

    if o["legenda"]:
        rows = ""
        for nm, (pv, desc, inv, ordn) in _GEN3_INFO.items():
            rows += (f"<tr><td class='nm'>{nm}</td><td>{pv}</td>"
                     f"<td>{_col_order(nm)}</td><td>{desc}</td>"
                     f"<td>{inv}</td><td>{ordn}</td></tr>")
        body += f"""
    <h2>2 · Legenda dei simboli</h2>
    <p class='lead'>I sei elementi di GEN3 sono le permutazioni di
       {{Sinistra, Centro, Destra}}. Il nome indica le destinazioni delle
       colonne; l'<em>ordine di raccolta</em> usa la permutazione inversa.
       La prima colonna indicata va in cima, le successive sotto.</p>
    <table class='gen3'>
      <tr><th>Nome</th><th>Permutazione</th><th>Ordine di raccolta</th>
          <th>Effetto</th><th>Inverso</th><th>Ordine</th></tr>
      {rows}
    </table>
    <p class='meta'>Nelle espressioni compaiono anche <code>I_3</code>
       (alias di SCD_U, identità) e <code>R_U</code> (alias di DCS_U,
       inversione) per i fattori J di capovolgimento.</p>
        """

    if o["fasi"]:
        body += "<h2>3 · Le tre fasi, passo per passo</h2>"
        if chosen:
            body += f"""
    <div class='infobox'>
      <p><strong>Preparazione:</strong> mostra le 27 carte e fa' scegliere
         mentalmente una carta allo spettatore. Qui sotto è sviluppata
         {"una decomposizione <strong>a raccolta semplice</strong> (tutte le fasi si eseguono col solo ordine di raccolta)" if chosen_is_simple else "la <strong>prima</strong> decomposizione trovata"}
         tra le <strong>{len(decomps)}</strong> disponibili: ognuna è un modo
         diverso di eseguire la stessa permutazione.</p>
    </div>"""
            a1, a2, a3 = chosen
            body += _ai_phase_html(a1, 1)
            body += _ai_phase_html(a2, 2)
            body += _ai_phase_html(a3, 3)
        else:
            body += """
    <div class='infobox'>
      <p>Nessuna decomposizione disponibile: calcola le decomposizioni
         nell'Explorer (pulsante «🔍 Decomposizioni T⁻¹») per ottenere le
         istruzioni specifiche di raccolta per ciascuna fase.</p>
    </div>"""

    if o["verifica"] and chosen:
        p_proto = _protocol_perm(chosen)
        inv_p   = [0] * 27
        for i, v in enumerate(p_proto):
            inv_p[v] = i
        final_deck = [inv_p[j] + 1 for j in range(27)]
        quale = ("T⁻¹ (la permutazione inversa)" if context["inverse"]
                 else "T (la permutazione diretta)")
        hl = {j for j in range(27) if final_deck[j] == j + 1}
        body += f"""
    <h2>4 · Verifica pratica</h2>
    <p class='lead'>Per provare il protocollo senza pubblico: ordina il mazzo
       da 1 a 27 (1 in cima), esegui le tre fasi esattamente come sopra
       (ignora la domanda allo spettatore), e confronta il risultato.
       Eseguendo le fasi si applica al mazzo <strong>{quale}</strong>.</p>
    <p class='meta'>Mazzo iniziale (posizioni 0–26, dall'alto):</p>
    {_deck_row_html(list(range(1, 28)))}
    <p class='meta'>Mazzo finale atteso:</p>
    {_deck_row_html(final_deck, highlight=hl)}
    <p class='meta'>Le celle evidenziate sono le carte che tornano nella
       posizione di partenza (punti fissi della permutazione).</p>
    <p class='lead'>Esempio di lettura: la carta che parte in posizione 0
       (cima) finisce in posizione {p_proto[0]}; quella in posizione 13
       (centro) finisce in posizione {p_proto[13]}.</p>
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
            cyc_html += (f"<p class='cyc'><span class='c fix'>punti fissi</span>"
                         f"{', '.join(str(x) for x in fixed)}"
                         f" — queste posizioni non si muovono mai.</p>")
        spiega = (f"Ripetendo l'<em>intero trucco</em> {ordr} volte il mazzo "
                  f"torna esattamente all'ordine iniziale: il periodo è il "
                  f"minimo comune multiplo delle lunghezze dei cicli."
                  if ordr else "")
        body += f"""
    <h2>5 · Struttura ciclica di T</h2>
    <p class='lead'>La permutazione si scompone in <strong>cicli
       disgiunti</strong>: ogni posizione viaggia solo dentro il proprio
       ciclo. {spiega}</p>
    {cyc_html}
    <p class='meta'>Ordine (periodo) di T: <strong>{ordr}</strong>.</p>
        """

    if o["tabelle"]:
        body += "<h2>6 · Tabelle delle permutazioni</h2>"
        body += ("<p class='lead'>Lettura: la carta in posizione i va in "
                 "posizione T[i]. La tabella di T⁻¹ risponde alla domanda "
                 "inversa: «chi finisce in posizione i?».</p>")
        is_involution = (perm == inv_perm)
        if is_involution:
            body += ("<p class='invol'>⚠ T è un'<strong>involuzione</strong> "
                     "(T² = I): la permutazione inversa coincide con quella "
                     "diretta, quindi le due tabelle sono identiche.</p>")
        body += "<div class='two-col'>"
        body += _perm_to_html_table(perm, "T  (diretta)")
        body += _perm_to_html_table(inv_perm,
                                    "T⁻¹ (inversa)" +
                                    ("  [= T]" if is_involution else ""))
        body += "</div>"

    if o["matrice"]:
        body += "<h2>7 · Matrice di permutazione</h2>"
        body += ("<p class='lead'>Ogni colonna ha esattamente una cella "
                 "piena: una «fotografia» della permutazione. Blocchi e "
                 "terzine (linee scure) rendono visibile l'eventuale "
                 "struttura di Kronecker.</p>")
        body += _matrix_svg(perm, label="T")
        body += _matrix_svg(inv_perm, label="T⁻¹")

    if o["matematica"]:
        body += """
    <h2>8 · Perché funziona (la matematica in breve)</h2>
    <p class='lead'>Numeriamo le posizioni 0–26 e scriviamole in base 3:
       pos = 9·i₂ + 3·i₁ + i₀.</p>
    <div class='formula'>MSC:   (i₂, i₁, i₀)  →  (i₀, i₂, i₁)      rotazione delle cifre
A_i:   (i₂, i₁, i₀)  →  (f₂(i₂), f₁(i₁), f₀(i₀))   cifre permutate
                                                    indipendentemente</div>
    <p class='lead'>La colonna in cui cade una carta alla distribuzione k
       rivela la k-esima cifra ternaria della sua posizione. In tre
       distribuzioni il presentatore «legge» tutte e tre le cifre — per
       questo il trucco classico individua la carta — e con le raccolte
       A le «riscrive» a piacere, portando la carta in qualunque
       posizione voluta.</p>
    <div class='formula'>Regola di trasporto:   MSC ∘ (a ⊗ b ⊗ c)  =  (c ⊗ a ⊗ b) ∘ MSC
Conseguenza:           MSC ∘ MSC ∘ MSC  =  I   (3 rotazioni = identità)</div>
    <p class='lead'>Grazie a queste regole ogni sequenza di distribuzioni e
       raccolte si riduce alla forma normale <code>K ∘ MSC^k</code> con
       k ∈ {0,1,2}: è la «firma» algebrica del trucco, visibile
       nell'Explorer.</p>
        """

    body += """
    <hr style='margin:32px 0 16px; border:none; border-top:1px solid #ddd'>
    <p class='meta no-print'>Generato da <em>Gioco delle 27 Carte</em> &mdash;
       <a href='javascript:window.print()'>🖨 Stampa / Salva PDF</a></p>
    """

    return f"""<!DOCTYPE html>
<html lang='it'>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Protocollo — {_html.escape(label)}</title>
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
