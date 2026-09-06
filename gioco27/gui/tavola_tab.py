"""
Tab "📚 Tavola 216" — la tavola delle disposizioni semplici del libro.

Per ciascuna delle 216 sequenze di tre mescolamenti (senza rovesciamenti):
numero #, mescolamenti, impilamenti (gesto fisico), posizioni finali dei
tre Assi, periodo, punti fissi, tipo ciclico, parità, auto-inversa.

Strumenti:
  • filtro live su qualunque colonna;
  • ricostruzione del tabellone dalle posizioni degli Assi;
  • dettaglio T / T⁻¹ con doppio clic;
  • esportazione CSV.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

from ..core import gioco_reale as gr


class TavolaFrame(ttk.Frame):

    _COLS = (
        ("num",  "#",            46),
        ("mesc", "Mescolamenti", 130),
        ("imp",  "Impilamenti",  130),
        ("assi", "Assi (A♠ A♣ A♥)", 120),
        ("per",  "Periodo",      64),
        ("fix",  "Punti fissi",  80),
        ("tipo", "Tipo ciclico", 150),
        ("par",  "Parità",       60),
        ("auto", "Auto-inversa", 96),
    )

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._righe = gr.tavola_216()
        self._build_ui()
        self._popola()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        top = ttk.Frame(self, padding=(8, 6))
        top.pack(fill="x")

        ttk.Label(top, text="Filtro:").pack(side="left")
        self._filtro_var = tk.StringVar()
        ent = ttk.Entry(top, textvariable=self._filtro_var, width=24)
        ent.pack(side="left", padx=(4, 12))
        self._filtro_var.trace_add("write", lambda *a: self._popola())
        ttk.Label(top, foreground="#666",
                  text="(cerca in tutte le colonne: es. CDS, 6, auto…)"
                  ).pack(side="left")

        ttk.Button(top, text="⬇  Esporta CSV",
                   command=self._esporta_csv).pack(side="right", padx=4)

        # ── ricostruzione dagli assi ──
        rec = ttk.LabelFrame(self, text="  Ricostruzione dagli Assi  "
                             "(posizioni finali 0–26, dal dorso)  ",
                             padding=(8, 6))
        rec.pack(fill="x", padx=8, pady=(0, 4))
        self._asso_vars = []
        for lbl in ("A♠ (da 0):", "A♣ (da 13):", "A♥ (da 26):"):
            ttk.Label(rec, text=lbl).pack(side="left", padx=(8, 2))
            v = tk.StringVar()
            ttk.Spinbox(rec, from_=0, to=26, width=4,
                        textvariable=v).pack(side="left")
            self._asso_vars.append(v)
        ttk.Button(rec, text="🔎  Trova disposizione",
                   command=self._ricostruisci).pack(side="left", padx=12)
        self._rec_lbl = ttk.Label(rec, text="", foreground="#00427e")
        self._rec_lbl.pack(side="left", padx=6)

        # ── tabella ──
        wrap = ttk.Frame(self)
        wrap.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        cols = [c for c, _, _ in self._COLS]
        tv = ttk.Treeview(wrap, columns=cols, show="headings",
                          selectmode="browse")
        for c, testo, w in self._COLS:
            tv.heading(c, text=testo)
            tv.column(c, width=w, anchor="center", stretch=(c in ("mesc", "imp", "tipo")))
        vs = ttk.Scrollbar(wrap, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=vs.set)
        tv.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")
        tv.bind("<Double-1>", self._dettaglio)
        tv.tag_configure("pari", background="#f4f9f4")
        tv.tag_configure("evid", background="#fff2c4")
        self._tv = tv

        self._status = ttk.Label(self, text="", padding=(10, 2),
                                 foreground="#555")
        self._status.pack(fill="x")

    # ── dati ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _valori(r):
        return (
            r["numero"],
            " ".join(r["mescolamenti"]),
            " ".join(r["impilamenti"]),
            "{:2d} {:2d} {:2d}".format(*r["assi"]),
            r["periodo"],
            r["punti_fissi"],
            "·".join(str(l) for l in r["tipo_ciclo"] if l > 1) or "identità",
            "pari" if r["parita"] > 0 else "dispari",
            "sì" if r["autoinversa"] else "",
        )

    def _popola(self, evidenzia=None):
        f = self._filtro_var.get().strip().lower()
        tv = self._tv
        tv.delete(*tv.get_children())
        n_vis = 0
        for r in self._righe:
            vals = self._valori(r)
            if f and f not in " ".join(str(v).lower() for v in vals):
                continue
            tags = []
            if evidenzia is not None and r["numero"] == evidenzia:
                tags.append("evid")
            elif n_vis % 2:
                tags.append("pari")
            tv.insert("", "end", iid=str(r["numero"]), values=vals,
                      tags=tuple(tags))
            n_vis += 1
        self._status.configure(
            text=f"{n_vis} / 216 disposizioni mostrate.   "
                 "Doppio clic su una riga per T e T⁻¹ complete.")

    # ── azioni ────────────────────────────────────────────────────────────────

    def _ricostruisci(self):
        try:
            pos = [int(v.get()) for v in self._asso_vars]
        except ValueError:
            messagebox.showwarning("Assi", "Inserisci tre numeri interi 0–26.")
            return
        try:
            mesc, num = gr.tabellone_da_assi(*pos)
        except ValueError as e:
            self._rec_lbl.configure(text="✗ nessuna disposizione", foreground="#aa0000")
            messagebox.showinfo(
                "Ricostruzione dagli Assi",
                f"Nessuna disposizione semplice produce questi Assi.\n\n{e}")
            return
        self._rec_lbl.configure(
            text=f"→ #{num}:  {' '.join(mesc)}", foreground="#006400")
        self._filtro_var.set("")
        self._popola(evidenzia=num)
        try:
            self._tv.see(str(num))
            self._tv.selection_set(str(num))
        except tk.TclError:
            pass

    def _dettaglio(self, _ev=None):
        sel = self._tv.selection()
        if not sel:
            return
        r = self._righe[int(sel[0])]
        win = tk.Toplevel(self)
        win.title(f"Disposizione #{r['numero']}")
        txt = tk.Text(win, width=88, height=24, font=("Consolas", 10),
                      wrap="none", padx=10, pady=8)
        txt.pack(fill="both", expand=True)

        def riga27(nome, arr):
            testa = "  ".join(f"{i:2d}" for i in range(27))
            corpo = "  ".join(f"{v:2d}" for v in arr)
            return f"{nome}\n   n  {testa}\n      {corpo}\n\n"

        mesc, imp = r["mescolamenti"], r["impilamenti"]
        txt.insert("end",
            f"Disposizione semplice #{r['numero']}\n"
            f"{'='*60}\n"
            f"Mescolamenti (righe del tabellone, prima in basso): "
            f"{' '.join(mesc)}\n"
            f"Impilamenti (gesto fisico, mazzetti dal dorso):     "
            f"{' '.join(imp)}\n"
            f"Assi: A♠→{r['assi'][0]}  A♣→{r['assi'][1]}  A♥→{r['assi'][2]}\n"
            f"Periodo {r['periodo']}   punti fissi {r['punti_fissi']}   "
            f"{'auto-inversa' if r['autoinversa'] else 'non auto-inversa'}\n\n")
        txt.insert("end", riga27("T (posizione finale della carta n):", r["T"]))
        txt.insert("end", riga27("T⁻¹ (carta che finisce in posizione k):", r["T_inv"]))
        txt.insert("end",
            "Tabellone (dal basso verso l'alto):\n" +
            "".join(f"   riga {i}:  {m}   (impila: {p})\n"
                    for i, (m, p) in enumerate(zip(mesc, imp), 1)))
        txt.configure(state="disabled")

    def _esporta_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile="tavola_216.csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh, delimiter=";")
                w.writerow(["numero", "mesc_1", "mesc_2", "mesc_3",
                            "imp_1", "imp_2", "imp_3",
                            "asso_picche", "asso_fiori", "asso_cuori",
                            "periodo", "punti_fissi", "tipo_ciclico",
                            "parita", "autoinversa"] +
                           [f"T_{i}" for i in range(27)])
                for r in self._righe:
                    w.writerow([r["numero"], *r["mescolamenti"],
                                *r["impilamenti"], *r["assi"],
                                r["periodo"], r["punti_fissi"],
                                "-".join(map(str, r["tipo_ciclo"])),
                                r["parita"], int(r["autoinversa"])] +
                               list(r["T"]))
        except OSError as e:
            messagebox.showerror("Esportazione", f"Impossibile scrivere il file:\n{e}")
            return
        messagebox.showinfo("Esportazione", f"Tavola esportata in:\n{path}")
