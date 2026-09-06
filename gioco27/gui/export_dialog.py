"""
ExportDialog — Esportazione per il libretto

Genera:
  1. Tabella LaTeX permutazione T e T^-1
  2. Tabella LaTeX cicli disgiunti + ordine
  3. Diagramma freccia SVG della permutazione
  4. Blocco LaTeX decomposizioni Kronecker (longtable)
  5. File testo riassuntivo

Avvio: app._open_export_dialog(perm, inv_perm, decompositions, title_label)
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

from ..core.analysis import cycle_decomposition, order_of, cycle_type


class ExportDialog(tk.Toplevel):

    def __init__(self, parent, perm=None, inv_perm=None,
                 decompositions=None, title_label="T"):
        super().__init__(parent)
        self.title("Esportazione per il libretto")
        self.geometry("860x640")
        self.resizable(True, True)

        self._perm    = list(perm)     if perm     else list(range(27))
        self._inv     = list(inv_perm) if inv_perm else list(range(27))
        self._decomps = decompositions or []
        self._lbl     = title_label

        self._build_ui()
        self._refresh_preview()

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        opt = ttk.LabelFrame(self, text=" Contenuto da esportare ", padding=(12, 6))
        opt.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))

        self._opt_perm   = tk.BooleanVar(value=True)
        self._opt_cycles = tk.BooleanVar(value=True)
        self._opt_svg    = tk.BooleanVar(value=True)
        self._opt_decomp = tk.BooleanVar(value=bool(self._decomps))
        self._opt_txt    = tk.BooleanVar(value=True)

        items = [
            (self._opt_perm,   "LaTeX — Tabella permutazione T e T⁻¹"),
            (self._opt_cycles, "LaTeX — Cicli disgiunti e ordine"),
            (self._opt_svg,    "SVG — Diagramma freccia"),
            (self._opt_decomp, "LaTeX — Decomposizioni Kronecker"),
            (self._opt_txt,    "TXT — Riepilogo testuale"),
        ]
        for i, (var, text) in enumerate(items):
            ttk.Checkbutton(opt, text=text, variable=var,
                             command=self._refresh_preview).grid(
                row=i//3, column=i%3, sticky="w", padx=10, pady=2)

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)

        self._tabs = {}
        for key, label in [
            ("latex_perm",   "LaTeX – Permutazione"),
            ("latex_cycles", "LaTeX – Cicli"),
            ("svg",          "SVG – Frecce"),
            ("latex_decomp", "LaTeX – Decomp."),
            ("txt",          "Testo"),
        ]:
            fr = ttk.Frame(nb)
            nb.add(fr, text=f"  {label}  ")
            fr.columnconfigure(0, weight=1)
            fr.rowconfigure(0, weight=1)
            t = tk.Text(fr, font=("Courier New", 9), wrap="none",
                         background="#FAFBFC", relief="flat")
            vsb = ttk.Scrollbar(fr, orient="vertical",   command=t.yview)
            hsb = ttk.Scrollbar(fr, orient="horizontal", command=t.xview)
            t.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            t.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")
            self._tabs[key] = t

        bf = ttk.Frame(self, padding=(10, 4))
        bf.grid(row=2, column=0, sticky="ew")
        ttk.Button(bf, text="💾  Esporta tutto in una cartella…",
                    command=self._export_all).pack(side="left", padx=(0, 8))
        ttk.Button(bf, text="✕  Chiudi",
                    command=self.destroy).pack(side="left")

    # ─── Preview ─────────────────────────────────────────────────────────────

    def _refresh_preview(self):
        p, iv, lb = self._perm, self._inv, self._lbl
        self._fill("latex_perm",   self._latex_perm(p, iv, lb))
        self._fill("latex_cycles", self._latex_cycles(p, lb))
        self._fill("svg",          self._svg_arrows(p, lb))
        self._fill("latex_decomp", self._latex_decomp(lb))
        self._fill("txt",          self._txt_summary(p, iv, lb))

    def _fill(self, key, content):
        t = self._tabs[key]
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("end", content)
        t.configure(state="disabled")

    # ─── Generatori ──────────────────────────────────────────────────────────

    def _latex_perm(self, perm, inv, lb):
        def tbl(arr, cap):
            header = " & ".join(str(i) for i in range(27))
            values = " & ".join(str(v) for v in arr)
            return (f"% {cap}\n"
                    f"\\begin{{center}}\\small\n"
                    f"\\begin{{tabular}}{{r{'c'*27}}}\n"
                    "\\toprule\n"
                    f"$i$ & {header} \\\\\n"
                    f"\\midrule\n"
                    f"${cap}(i)$ & {values} \\\\\n"
                    f"\\bottomrule\n"
                    f"\\end{{tabular}}\n"
                    "\\end{center}\n")
        return ("% Richiede: \\usepackage{booktabs}\n\n"
                + tbl(perm, lb) + "\n" + tbl(inv, lb + "^{-1}") + "\n"
                + "% Notazione ciclica:\n"
                + f"% ${lb} = {self._cyclenot(perm)}$\n"
                + f"% ${lb}^{{-1}} = {self._cyclenot(inv)}$\n"
                + f"% $\\mathrm{{ord}}({lb}) = {order_of(perm)}$\n")

    def _latex_cycles(self, perm, lb):
        cycs = cycle_decomposition(perm)
        ct   = cycle_type(perm)
        ord_ = order_of(perm)
        type_str = " + ".join(
            f"${cnt}\\cdot({ln})$" for ln, cnt in sorted(ct.items()))
        rows = []
        for i, c in enumerate(cycs, 1):
            inner = " \\to ".join(str(x) for x in c)
            suffix = "  [fisso]" if len(c) == 1 else ""
            rows.append(f"  {i} & {len(c)} & $({inner})${suffix} \\\\")
        return (f"% Richiede: \\usepackage{{booktabs, amsmath}}\n\n"
                f"$\\mathrm{{ord}}({lb}) = {ord_}$\n\n"
                f"Tipo: {type_str}\n\n"
                f"$${lb} = {self._cyclenot(perm)}$$\n\n"
                "\\begin{center}\n"
                "\\begin{tabular}{rrl}\n"
                "\\toprule\n"
                "  \\# & len & ciclo \\\\\n"
                "\\midrule\n"
                + "\n".join(rows) + "\n"
                "\\bottomrule\n"
                "\\end{tabular}\n"
                "\\end{center}\n")

    def _svg_arrows(self, perm, lb):
        W, H  = 920, 300
        M     = 28
        N     = 27
        step  = (W - 2*M) / (N - 1)
        pal   = ["#4E79A7","#F28E2B","#E15759","#76B7B2","#59A14F",
                 "#EDC948","#B07AA1","#FF9DA7","#9C755F","#BAB0AC"]
        cycs  = cycle_decomposition(perm)
        ct    = cycle_type(perm)
        col4len = {l: pal[i % len(pal)] for i,l in enumerate(sorted(ct.keys()))}
        c4card  = {}
        for cyc in cycs:
            col = col4len[len(cyc)]
            for x in cyc: c4card[x] = col

        YTOP, YBOT = 65, 220
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
               f'<rect width="{W}" height="{H}" fill="#FAFBFC"/>',
               f'<text x="{W//2}" y="20" text-anchor="middle" '
               f'font-family="Segoe UI,Arial" font-size="13" font-weight="bold" '
               f'fill="#1a3a5c">Permutazione {lb} — diagramma freccia</text>']

        for i in range(N):
            x = M + i*step; col = c4card.get(i, "#999")
            svg.append(f'<circle cx="{x:.1f}" cy="{YTOP}" r="9" '
                        f'fill="{col}" stroke="white" stroke-width="1.5"/>')
            svg.append(f'<text x="{x:.1f}" y="{YTOP+4}" text-anchor="middle" '
                        f'font-family="Courier New" font-size="7.5" fill="white">{i}</text>')
            svg.append(f'<circle cx="{x:.1f}" cy="{YBOT}" r="9" '
                        f'fill="{col}" stroke="white" stroke-width="1.5"/>')
            svg.append(f'<text x="{x:.1f}" y="{YBOT+4}" text-anchor="middle" '
                        f'font-family="Courier New" font-size="7.5" fill="white">{i}</text>')

        for i, j in enumerate(perm):
            if i == j: continue
            xi = M + i*step; xj = M + j*step; col = c4card.get(i, "#999")
            mx = (xi+xj)/2; my = (YTOP+YBOT)/2 + (30 if xi < xj else -30)
            svg.append(f'<path d="M{xi:.1f},{YTOP+9} Q{mx:.1f},{my:.1f} '
                        f'{xj:.1f},{YBOT-9}" stroke="{col}" stroke-width="1.2" '
                        f'fill="none" opacity="0.65"/>')

        svg.append(f'<text x="{M}" y="{YTOP-16}" font-family="Segoe UI,Arial" '
                    f'font-size="10" fill="#555">posizione iniziale i</text>')
        svg.append(f'<text x="{M}" y="{YBOT+26}" font-family="Segoe UI,Arial" '
                    f'font-size="10" fill="#555">posizione finale {lb}(i)</text>')
        svg.append('</svg>')
        return "\n".join(svg)

    def _latex_decomp(self, lb):
        if not self._decomps:
            return ("% Nessuna decomposizione disponibile.\n"
                    "% Aprire prima 'Tutte le decomposizioni' nell'Explorer.")
        lines = [
            f"% Decomposizioni $\\mathrm{{{lb}}}^{{-1}}$ — prime "
            f"{min(len(self._decomps),200)}",
            "% Richiede: \\usepackage{booktabs, longtable}",
            "",
            "\\begin{longtable}{r l l l}",
            "\\toprule",
            "  \\# & $A_0$ & $A_1$ & $A_2$ \\\\",
            "\\midrule\\endfirsthead",
            "\\midrule",
            "  \\# & $A_0$ & $A_1$ & $A_2$ \\\\",
            "\\midrule\\endhead",
            "\\bottomrule\\endlastfoot",
        ]
        for i, (a1, a2, a3) in enumerate(self._decomps[:200], 1):
            def fmt(t):
                return "{} \\mathbin{{\\otimes}} {} \\mathbin{{\\otimes}} {}".format(*t
                       ).replace("_U","")
            lines.append(f"  {i} & $\\scriptscriptstyle {fmt(a1)}$ "
                         f"& $\\scriptscriptstyle {fmt(a2)}$ "
                         f"& $\\scriptscriptstyle {fmt(a3)}$ \\\\")
        if len(self._decomps) > 200:
            lines.append(f"  \\multicolumn{{4}}{{c}}"
                         f"{{\\emph{{... e altre "
                         f"{len(self._decomps)-200} decomposizioni}}}} \\\\")
        lines.append("\\end{longtable}")
        return "\n".join(lines)

    def _txt_summary(self, perm, inv, lb):
        cycs = cycle_decomposition(perm)
        ct   = cycle_type(perm)
        ord_ = order_of(perm)
        idx  = "  " + "  ".join(f"{i:2d}" for i in range(27))
        p_s  = "  " + "  ".join(f"{v:2d}" for v in perm)
        iv_s = "  " + "  ".join(f"{v:2d}" for v in inv)
        lines = [
            f"PERMUTAZIONE {lb}  —  generato da gioco27",
            "=" * 64, "",
            f"Indici:{idx}",
            f"{lb}:     {p_s}",
            f"{lb}^-1:  {iv_s}", "",
            f"Ordine di {lb}: {ord_}",
            "Tipo di ciclo: " +
                "  ".join(f"{cnt}×(len {l})" for l,cnt in sorted(ct.items())), "",
            "Notazione ciclica:",
            f"  {lb}     = {self._cyclenot(perm)}",
            f"  {lb}^-1 = {self._cyclenot(inv)}", "",
            "Cicli disgiunti:",
        ]
        for i, c in enumerate(cycs, 1):
            s = " → ".join(f"C{x:02d}" for x in c)
            suf = "  [fisso]" if len(c)==1 else ""
            lines.append(f"  {i:3d}.  ({s}){suf}")
        if self._decomps:
            lines += ["", f"Decomposizioni Kronecker di {lb}^-1: {len(self._decomps)}",
                       "(prime 10)", ""]
            for i,(a1,a2,a3) in enumerate(self._decomps[:10],1):
                a1s="({} x {} x {})".format(*a1)
                a2s="({} x {} x {})".format(*a2)
                a3s="({} x {} x {})".format(*a3)
                lines.append(f"  {i:3d}.  {lb}^-1 = {a3s} o MSC o "
                              f"{a2s} o MSC o {a1s} o MSC")
        return "\n".join(lines)

    # ─── Helper ───────────────────────────────────────────────────────────────

    def _cyclenot(self, perm):
        cycs = cycle_decomposition(perm)
        parts = ["("+  " ".join(str(x) for x in c)+")"
                 for c in cycs if len(c) > 1]
        return " ".join(parts) if parts else r"\mathrm{id}"

    # ─── Export ───────────────────────────────────────────────────────────────

    def _export_all(self):
        folder = filedialog.askdirectory(parent=self,
                                          title="Scegli cartella per l'export")
        if not folder:
            return
        lb  = self._lbl.replace("^","").replace("{","").replace("}","")
        p, iv = self._perm, self._inv
        done = []
        try:
            if self._opt_perm.get():
                f = os.path.join(folder, f"{lb}_permutazione.tex")
                open(f,"w",encoding="utf-8").write(self._latex_perm(p,iv,self._lbl))
                done.append(f)
            if self._opt_cycles.get():
                f = os.path.join(folder, f"{lb}_cicli.tex")
                open(f,"w",encoding="utf-8").write(self._latex_cycles(p,self._lbl))
                done.append(f)
            if self._opt_svg.get():
                f = os.path.join(folder, f"{lb}_frecce.svg")
                open(f,"w",encoding="utf-8").write(self._svg_arrows(p,self._lbl))
                done.append(f)
            if self._opt_decomp.get() and self._decomps:
                f = os.path.join(folder, f"{lb}_decomposizioni.tex")
                open(f,"w",encoding="utf-8").write(self._latex_decomp(self._lbl))
                done.append(f)
            if self._opt_txt.get():
                f = os.path.join(folder, f"{lb}_analisi.txt")
                open(f,"w",encoding="utf-8").write(self._txt_summary(p,iv,self._lbl))
                done.append(f)
            messagebox.showinfo(
                "Export completato",
                f"Esportati {len(done)} file in:\n{folder}\n\n" +
                "\n".join(os.path.basename(x) for x in done),
                parent=self)
        except OSError as e:
            messagebox.showerror("Errore export", str(e), parent=self)
