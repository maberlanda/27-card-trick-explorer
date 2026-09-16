"""
Export LaTeX / SVG per il gruppo G = GEN3^3.

Fornisce due dialog di esportazione, sullo stesso modello dell'ExportDialog
dell'Explorer (anteprima a schede + «Esporta tutto in una cartella…»):

  CayleyExportDialog     — tavola di Cayley:
        · SVG  — heatmap 216×216 (cella colorata per elemento risultante)
        · LaTeX — griglia TikZ colorata 216×216
        · LaTeX — calcolo selezionato (A∘B, B∘A, inversi, commutatore,
                  potenze di A, sottogruppo ⟨A,B⟩)

  ConjugacyExportDialog  — classi di coniugio:
        · LaTeX — tabella delle 27 classi + elenco elementi (longtable)
        · SVG  — griglia dei 216 elementi colorati per classe
        · SVG  — istogramma delle dimensioni delle classi

Avvio:
    CayleyExportDialog(parent, gd, ia, ib)
    ConjugacyExportDialog(parent, gd)
"""
import colorsys
import os
from collections import Counter

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .i18n import tr


# Classe S3 di ciascun generatore GEN3 (id / trasposizione / 3-ciclo) e
# relativa dimensione della classe in S3.  Replicato qui per evitare import
# circolari con conjugacy_dialog.
_S3_CLASS = {
    "SCD_U": ("id",      1),
    "SDC_U": ("trasp.",  3),
    "CSD_U": ("trasp.",  3),
    "DCS_U": ("trasp.",  3),
    "CDS_U": ("3-ciclo", 2),
    "DSC_U": ("3-ciclo", 2),
}


def _class_type(triple):
    """(f3,f2,f1) → ('(id, trasp., 3-ciclo)', dimensione_attesa)."""
    kinds = [_S3_CLASS.get(f, ("?", 1))[0] for f in triple]
    size = 1
    for f in triple:
        size *= _S3_CLASS.get(f, ("?", 1))[1]
    return "(" + ", ".join(kinds) + ")", size


# ── Helper colori ────────────────────────────────────────────────────────────

def _hue_hex(idx, n, s=0.62, v=0.93):
    """Colore esadecimale distinto per l'indice idx in [0, n)."""
    h = (idx % n) / max(1, n)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"


def _hue_rgb(idx, n, s=0.62, v=0.93):
    """Tripla (r,g,b) 0-255 per l'indice idx in [0, n)."""
    h = (idx % n) / max(1, n)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def _tex_escape(s):
    """Escape minimale per testo LaTeX."""
    return (str(s).replace("\\", r"\textbackslash{}")
            .replace("_", r"\_").replace("&", r"\&")
            .replace("%", r"\%").replace("#", r"\#")
            .replace("{", r"\{").replace("}", r"\}"))


def _tex_name(s):
    """Nome elemento in \\texttt{} con underscore protetti."""
    return r"\texttt{" + _tex_escape(s) + "}"


# ── Dialog base con anteprima a schede ───────────────────────────────────────

class _PreviewExportDialog(tk.Toplevel):
    """Toplevel con notebook di anteprime + esporta-in-cartella.

    Le sottoclassi devono impostare:
      self._items = [(key, label, filename, generator_callable), ...]
    dove generator_callable() -> str restituisce il contenuto completo.
    Il prefisso del nome file e il titolo della finestra sono passati dal
    costruttore della sottoclasse.
    """

    _PREVIEW_MAX = 60000   # caratteri max mostrati in anteprima

    def __init__(self, parent, win_title, items):
        super().__init__(parent)
        self.title(win_title)
        self.geometry("900x660")
        self.resizable(True, True)
        self._items = items
        self._opts = {}
        self._cache = {}
        self._build_ui()
        self._refresh_preview()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        opt = ttk.LabelFrame(self, text=f" {tr('export.content')} ",
                             padding=(12, 6))
        opt.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        for i, (key, label, _fn, _gen) in enumerate(self._items):
            var = tk.BooleanVar(value=True)
            self._opts[key] = var
            ttk.Checkbutton(opt, text=label, variable=var).grid(
                row=i // 3, column=i % 3, sticky="w", padx=10, pady=2)

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)
        self._tabs = {}
        for key, label, _fn, _gen in self._items:
            fr = ttk.Frame(nb)
            nb.add(fr, text=f"  {label}  ")
            fr.columnconfigure(0, weight=1)
            fr.rowconfigure(0, weight=1)
            t = tk.Text(fr, font=("Courier New", 9), wrap="none",
                        background="#FAFBFC", relief="flat")
            vsb = ttk.Scrollbar(fr, orient="vertical", command=t.yview)
            hsb = ttk.Scrollbar(fr, orient="horizontal", command=t.xview)
            t.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            t.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")
            self._tabs[key] = t

        bf = ttk.Frame(self, padding=(10, 4))
        bf.grid(row=2, column=0, sticky="ew")
        ttk.Button(bf, text=f"💾  {tr('export.export_all')}",
                   command=self._export_all).pack(side="left", padx=(0, 8))
        ttk.Button(bf, text=f"✕  {tr('button.close')}",
                   command=self.destroy).pack(side="left")

    def _content(self, key, gen):
        """Genera (e mette in cache) il contenuto completo per la chiave."""
        if key not in self._cache:
            try:
                self._cache[key] = gen()
            except Exception as exc:   # pragma: no cover - difensivo
                self._cache[key] = f"% Errore nella generazione: {exc}"
        return self._cache[key]

    def _refresh_preview(self):
        for key, _label, _fn, gen in self._items:
            content = self._content(key, gen)
            t = self._tabs[key]
            t.configure(state="normal")
            t.delete("1.0", "end")
            if len(content) > self._PREVIEW_MAX:
                t.insert("end", content[:self._PREVIEW_MAX])
                t.insert("end", "\n\n… [anteprima troncata — "
                                "l'export salverà il file completo] …\n")
            else:
                t.insert("end", content)
            t.configure(state="disabled")

    def _export_all(self):
        folder = filedialog.askdirectory(parent=self,
                                         title=tr("export.choose_folder"))
        if not folder:
            return
        done = []
        try:
            for key, _label, fname, gen in self._items:
                if not self._opts[key].get():
                    continue
                path = os.path.join(folder, fname)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self._content(key, gen))
                done.append(path)
            if not done:
                messagebox.showinfo(tr("export.no_files_title"),
                                    tr("export.no_content_selected"), parent=self)
                return
            messagebox.showinfo(
                tr("export.completed_title"),
                tr("export.completed", count=len(done), folder=folder,
                   files="\n".join(os.path.basename(x) for x in done)),
                parent=self)
        except OSError as exc:
            messagebox.showerror(tr("export.error_title"), str(exc), parent=self)


# ── Dialog Cayley ────────────────────────────────────────────────────────────

class CayleyExportDialog(_PreviewExportDialog):

    def __init__(self, parent, gd, ia=0, ib=1):
        self._gd = gd
        n = len(gd.kron_arr)
        self._ia = ia if 0 <= ia < n else 0
        self._ib = ib if 0 <= ib < n else (1 if n > 1 else 0)
        # colori precalcolati per indice elemento
        self._cols_hex = [_hue_hex(v, n) for v in range(n)]
        items = [
            ("svg_heat",  tr("export.cayley.heatmap"), "cayley_heatmap.svg",
             self._svg_heatmap),
            ("tex_grid",  tr("export.cayley.grid"),  "cayley_griglia.tex",
             self._latex_tikz),
            ("tex_calc",  tr("export.cayley.calculation"), "cayley_calcolo.tex",
             self._latex_calc),
        ]
        super().__init__(parent, tr("export.cayley_title"), items)

    # ---- SVG heatmap -------------------------------------------------------
    def _svg_heatmap(self):
        gd = self._gd
        cay = gd.cayley
        n = len(gd.kron_arr)
        cell = 3
        M = 46
        W = n * cell + 2 * M
        H = n * cell + 2 * M + 24
        cols = self._cols_hex
        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}">',
            f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>',
            f'<text x="{W/2:.0f}" y="22" text-anchor="middle" '
            f'font-family="Segoe UI,Arial" font-size="15" font-weight="bold" '
            f'fill="#1a3a5c">{tr("export.document.cayley.svg_title", size=n)}</text>',
        ]
        x0 = M
        y0 = M + 6
        for i in range(n):
            y = y0 + i * cell
            row = cay[i]
            # raggruppa celle adiacenti dello stesso colore per ridurre il file
            j = 0
            while j < n:
                v = int(row[j])
                k = j + 1
                while k < n and int(row[k]) == v:
                    k += 1
                w = (k - j) * cell
                out.append(f'<rect x="{x0 + j*cell}" y="{y}" width="{w}" '
                           f'height="{cell}" fill="{cols[v]}"/>')
                j = k
        # cornice
        out.append(f'<rect x="{x0}" y="{y0}" width="{n*cell}" height="{n*cell}" '
                   f'fill="none" stroke="#333" stroke-width="1"/>')
        out.append(f'<text x="{x0}" y="{y0 - 4}" font-family="Segoe UI,Arial" '
                   f'font-size="11" fill="#555">{tr("export.document.cayley.column_axis")}</text>')
        out.append(f'<text x="{x0}" y="{y0 + n*cell + 18}" '
                   f'font-family="Segoe UI,Arial" font-size="11" fill="#555">'
                   f'{tr("export.document.cayley.row_axis", size=n)}</text>')
        out.append('</svg>')
        return "\n".join(out)

    # ---- LaTeX TikZ grid ---------------------------------------------------
    def _latex_tikz(self):
        gd = self._gd
        cay = gd.cayley
        n = len(gd.kron_arr)
        lines = [
            "% " + tr("export.document.cayley.latex.grid"),
            "% " + tr("export.document.latex.requires_tikz"),
            "% " + tr("export.document.cayley.latex.large_figure", size=n, cells=n * n),
            "% " + tr("export.document.cayley.latex.compile_note"),
            "% " + tr("export.document.cayley.latex.cell_color"),
            "",
            "\\begin{center}",
            "\\begin{tikzpicture}[x=2.2pt,y=2.2pt]",
        ]
        for v in range(n):
            r, g, b = _hue_rgb(v, n)
            lines.append(f"\\definecolor{{cay{v}}}{{RGB}}{{{r},{g},{b}}}")
        for i in range(n):
            row = cay[i]
            yt = n - i
            yb = n - 1 - i
            j = 0
            while j < n:
                v = int(row[j])
                k = j + 1
                while k < n and int(row[k]) == v:
                    k += 1
                lines.append(
                    f"\\fill[cay{v}] ({j},{yb}) rectangle ({k},{yt});")
                j = k
        lines.append(f"\\draw[black] (0,0) rectangle ({n},{n});")
        lines.append("\\end{tikzpicture}")
        lines.append("\\end{center}")
        return "\n".join(lines)

    # ---- LaTeX calcolo selezionato ----------------------------------------
    def _calc_data(self):
        """Calcola i valori per A,B correnti (indipendente dalla GUI)."""
        gd = self._gd
        cay = gd.cayley
        inv = gd.inverse
        ia, ib = self._ia, self._ib
        iden = gd._identity_index()
        ab = int(cay[ia, ib]); ba = int(cay[ib, ia])
        inv_a = int(inv[ia]); inv_b = int(inv[ib])
        comm = int(cay[inv_a, int(cay[inv_b, ab])])
        # potenze di A
        pows, cur = [], ia
        while cur != iden:
            pows.append(gd.name(cur))
            cur = int(cay[ia, cur])
            if len(pows) > len(gd.kron_arr):
                break
        pows.append("e")
        # sottogruppo <A,B>
        gens = {ia, ib, inv_a, inv_b}
        sub = {iden}; frontier = {iden}
        while frontier:
            nxt = set()
            for gg in frontier:
                for ge in gens:
                    p = int(cay[gg, ge])
                    if p not in sub:
                        sub.add(p); nxt.add(p)
            frontier = nxt
        sub_list = sorted(sub)
        abelian = all(int(cay[x, y]) == int(cay[y, x])
                      for xi, x in enumerate(sub_list)
                      for y in sub_list[xi + 1:])
        return dict(ia=ia, ib=ib, ab=ab, ba=ba, inv_a=inv_a, inv_b=inv_b,
                    comm=comm, iden=iden, pows=pows, sub_list=sub_list,
                    abelian=abelian)

    def _latex_calc(self):
        gd = self._gd
        d = self._calc_data()
        nm = gd.name
        n = len(gd.kron_arr)
        k = len(d["sub_list"])
        commute = d["ab"] == d["ba"]
        rel = "=" if commute else r"\neq"
        comm_tail = tr("export.document.cayley.identity_tail") if d["comm"] == d["iden"] else "."
        lines = [
            "% " + tr("export.document.cayley.latex.calculation"),
            "% " + tr("export.document.latex.requires_amsmath"),
            "% " + tr("export.document.cayley.latex.composition_note"),
            "",
            "\\begin{align*}",
            f"  A      &= {_tex_name(nm(d['ia']))} "
            f"& \\operatorname{{ord}}(A) &= {int(gd.orders[d['ia']])} \\\\",
            f"  B      &= {_tex_name(nm(d['ib']))} "
            f"& \\operatorname{{ord}}(B) &= {int(gd.orders[d['ib']])} \\\\",
            f"  A\\circ B &= {_tex_name(nm(d['ab']))} "
            f"& \\operatorname{{ord}}(A\\circ B) &= {int(gd.orders[d['ab']])} \\\\",
            f"  B\\circ A &= {_tex_name(nm(d['ba']))} "
            f"& \\operatorname{{ord}}(B\\circ A) &= {int(gd.orders[d['ba']])} \\\\",
            f"  A^{{-1}} &= {_tex_name(nm(d['inv_a']))} "
            f"& B^{{-1}} &= {_tex_name(nm(d['inv_b']))} \\\\",
            "\\end{align*}",
            "",
            f"{tr('export.document.cayley.commute')}: \\textbf{{{tr('common.yes') if commute else tr('common.no')}}} "
            f"($A\\circ B {rel} B\\circ A$). "
            f"Commutatore $[A,B]=A^{{-1}}\\circ B^{{-1}}\\circ A\\circ B = "
            f"{_tex_name(nm(d['comm']))}$" + comm_tail,
            "",
            tr("export.document.cayley.powers"),
            "\\[ " + r" \;\to\; ".join(
                (r"\mathrm{e}" if p == "e" else _tex_name(p)) for p in d["pows"])
            + " \\]",
            "",
            tr("export.document.cayley.subgroup", order=k, index=n // k,
               abelian=tr("export.document.cayley.abelian") if d['abelian'] else tr("export.document.cayley.non_abelian"),
               generates=tr("export.document.cayley.generates_group") if k == n else "",
               size=n),
            "",
            "\\begin{center}\\small",
            "\\begin{tabular}{r l}",
            "\\hline",
            "  \\# & " + tr("export.document.cayley.subgroup_element") + " \\\\",
            "\\hline",
        ]
        for j, idx in enumerate(d["sub_list"], 1):
            lines.append(f"  {j} & {_tex_name(nm(idx))} \\\\")
        lines += ["\\hline", "\\end{tabular}", "\\end{center}"]
        return "\n".join(lines)


# ── Dialog Coniugio ──────────────────────────────────────────────────────────

class ConjugacyExportDialog(_PreviewExportDialog):

    def __init__(self, parent, gd):
        self._gd = gd
        items = [
            ("tex_classes", tr("export.conjugacy.classes"), "coniugio_classi.tex",
             self._latex_classes),
            ("svg_grid",    tr("export.conjugacy.grid"), "coniugio_griglia.svg",
             self._svg_grid),
            ("svg_hist",    tr("export.conjugacy.histogram"), "coniugio_istogramma.svg",
             self._svg_hist),
        ]
        super().__init__(parent, tr("export.conjugacy_title"), items)

    # ---- LaTeX tabella classi ---------------------------------------------
    def _latex_classes(self):
        gd = self._gd
        classes = gd.classes
        orders = gd.orders
        center = set(gd.center)
        lines = [
            "% " + tr("export.document.conjugacy.latex.classes"),
            "% " + tr("export.document.latex.requires_booktabs_longtable"),
            "",
            f"$|G| = {len(gd.kron_arr)}$, \\quad {tr('export.document.conjugacy.class_count')}: "
            f"${len(classes)}$, \\quad $|Z(G)| = {len(gd.center)}$.",
            "",
            "% --- " + tr("export.document.conjugacy.summary") + " ---",
            "\\begin{center}",
            "\\begin{tabular}{r r r l l}",
            "\\toprule",
            "  \\# & " + tr("export.document.dimension") + " & " + tr("export.document.order") + " & " + tr("export.document.type") + " $(f_3,f_2,f_1)$ & " + tr("export.document.representative") + " \\\\",
            "\\midrule",
        ]
        for i, c in enumerate(classes, 1):
            tipo, _ = _class_type(gd.kron_names[c[0]])
            is_ctr = all(idx in center for idx in c)
            star = "$\\star$ " if is_ctr else ""
            lines.append(
                f"  {i} & {len(c)} & {int(orders[c[0]])} "
                f"& {_tex_escape(tipo)} & {star}{_tex_name(gd.name(c[0]))} \\\\")
        lines += [
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{center}",
            "% $\\star$ = " + tr("export.document.conjugacy.center_class"),
            "",
            "% --- " + tr("export.document.conjugacy.class_elements") + " ---",
            "\\begin{longtable}{r r l}",
            "\\toprule",
            "  " + tr("export.document.conjugacy.class") + " & \\# & " + tr("export.document.element") + " \\\\",
            "\\midrule\\endfirsthead",
            "\\midrule",
            "  " + tr("export.document.conjugacy.class") + " & \\# & " + tr("export.document.element") + " \\\\",
            "\\midrule\\endhead",
            "\\bottomrule\\endlastfoot",
        ]
        for i, c in enumerate(classes, 1):
            for j, idx in enumerate(c, 1):
                first = str(i) if j == 1 else ""
                lines.append(f"  {first} & {j} & {_tex_name(gd.name(idx))} \\\\")
            lines.append("\\midrule")
        lines.append("\\end{longtable}")
        return "\n".join(lines)

    # ---- SVG griglia 216 elementi -----------------------------------------
    def _svg_grid(self):
        gd = self._gd
        classes = gd.classes
        n = len(gd.kron_arr)
        ncls = len(classes)
        # mappa elemento -> indice di classe (per il colore)
        elem_cls = {}
        for ci, c in enumerate(classes):
            for e in c:
                elem_cls[int(e)] = ci
        # ordine di disposizione: elementi raggruppati per classe (blocchi)
        order = [int(e) for c in classes for e in c]
        cols = 18
        rows = (n + cols - 1) // cols
        cell = 30
        M = 40
        W = max(cols * cell + 2 * M, 760)
        H = rows * cell + 2 * M + 70
        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}">',
            f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>',
            f'<text x="{W/2:.0f}" y="26" text-anchor="middle" '
            f'font-family="Segoe UI,Arial" font-size="15" font-weight="bold" '
            f'fill="#1a3a5c">{tr("export.document.conjugacy.svg_grid_title", count=ncls)}</text>',
        ]
        for pos, e in enumerate(order):
            r = pos // cols
            cc = pos % cols
            x = M + cc * cell
            y = M + 14 + r * cell
            col = _hue_hex(elem_cls[e], ncls)
            out.append(f'<rect x="{x}" y="{y}" width="{cell-2}" '
                       f'height="{cell-2}" rx="3" fill="{col}" '
                       f'stroke="#FFFFFF" stroke-width="1"/>')
        # equazione delle classi
        size_counts = Counter(len(c) for c in classes)
        eq = " + ".join(f"{sz}·{cnt}" for sz, cnt in sorted(size_counts.items()))
        yb = M + 14 + rows * cell + 24
        out.append(f'<text x="{M}" y="{yb}" font-family="Segoe UI,Arial" '
                   f'font-size="12" fill="#444">{tr("export.document.conjugacy.class_equation", equation=eq)}</text>')
        out.append(f'<text x="{M}" y="{yb + 20}" font-family="Segoe UI,Arial" '
                   f'font-size="11" fill="#666">{tr("export.document.conjugacy.svg_grid_note")}</text>')
        out.append('</svg>')
        return "\n".join(out)

    # ---- SVG istogramma dimensioni classi ---------------------------------
    def _svg_hist(self):
        gd = self._gd
        classes = gd.classes
        size_counts = Counter(len(c) for c in classes)
        sizes = sorted(size_counts)
        W, H = 720, 420
        M_L, M_B, M_T, M_R = 56, 60, 56, 28
        plot_w = W - M_L - M_R
        plot_h = H - M_T - M_B
        max_cnt = max(size_counts.values())
        k = len(sizes)
        gap = 14
        bw = (plot_w - gap * (k + 1)) / max(1, k)
        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}">',
            f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>',
            f'<text x="{W/2:.0f}" y="30" text-anchor="middle" '
            f'font-family="Segoe UI,Arial" font-size="15" font-weight="bold" '
            f'fill="#1a3a5c">{tr("export.document.conjugacy.svg_hist_title")}</text>',
        ]
        base_y = M_T + plot_h
        # assi
        out.append(f'<line x1="{M_L}" y1="{base_y}" x2="{M_L+plot_w}" '
                   f'y2="{base_y}" stroke="#333" stroke-width="1.5"/>')
        out.append(f'<line x1="{M_L}" y1="{M_T}" x2="{M_L}" y2="{base_y}" '
                   f'stroke="#333" stroke-width="1.5"/>')
        # griglia orizzontale + etichette y
        for gv in range(0, max_cnt + 1, max(1, max_cnt // 5)):
            yy = base_y - (gv / max_cnt) * plot_h
            out.append(f'<line x1="{M_L}" y1="{yy:.1f}" x2="{M_L+plot_w}" '
                       f'y2="{yy:.1f}" stroke="#EEE" stroke-width="1"/>')
            out.append(f'<text x="{M_L-8}" y="{yy+4:.1f}" text-anchor="end" '
                       f'font-family="Segoe UI,Arial" font-size="11" '
                       f'fill="#555">{gv}</text>')
        # barre
        pal = ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
               "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC"]
        for i, sz in enumerate(sizes):
            cnt = size_counts[sz]
            x = M_L + gap + i * (bw + gap)
            bh = (cnt / max_cnt) * plot_h
            y = base_y - bh
            col = pal[i % len(pal)]
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" '
                       f'height="{bh:.1f}" rx="3" fill="{col}"/>')
            out.append(f'<text x="{x+bw/2:.1f}" y="{y-6:.1f}" '
                       f'text-anchor="middle" font-family="Segoe UI,Arial" '
                       f'font-size="12" font-weight="bold" fill="#333">'
                       f'{cnt}</text>')
            out.append(f'<text x="{x+bw/2:.1f}" y="{base_y+20:.1f}" '
                       f'text-anchor="middle" font-family="Segoe UI,Arial" '
                       f'font-size="12" fill="#333">{tr("export.document.dimension")} {sz}</text>')
        out.append(f'<text x="{M_L+plot_w/2:.0f}" y="{H-14}" '
                   f'text-anchor="middle" font-family="Segoe UI,Arial" '
                   f'font-size="12" fill="#555">{tr("export.document.conjugacy.class_dimension")}</text>')
        out.append(f'<text x="16" y="{M_T+plot_h/2:.0f}" '
                   f'transform="rotate(-90 16 {M_T+plot_h/2:.0f})" '
                   f'text-anchor="middle" font-family="Segoe UI,Arial" '
                   f'font-size="12" fill="#555">{tr("export.document.conjugacy.number_of_classes")}</text>')
        out.append('</svg>')
        return "\n".join(out)
