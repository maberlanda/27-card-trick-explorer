"""
Contenuto della Guida / How-To del Gioco delle 27 carte.

Separato da app.py per mantenere snella la finestra principale e per poter
modificare la documentazione senza toccare la logica della GUI.

Tutto il rendering avviene tramite i due callback passati da app.py:
    ins(tag, text) -> inserisce `text` nel widget Text con lo stile `tag`
    sep()          -> inserisce una riga separatrice
Gli stili (tag) sono definiti in app.py._build_guide_tab.

I testi leggibili stanno nei cataloghi di `i18n.py` (chiavi ``guide.*``):
qui restano solo la struttura (ordine, tag, numerazione delle sezioni) e le
parti invarianti in ogni lingua — formule, codici, nomi dei generatori.
La Guida segue la lingua attiva al momento della costruzione della scheda.
"""

from .i18n import tr


# Chiavi dei titoli delle 33 sezioni, nell'ordine dell'indice. Il numero di
# sezione (1-based) resta fuori dal testo tradotto: app.py lo legge
# dall'intestazione h2 per creare le ancore «secN» usate da «Apri Guida».
SECTION_TITLE_KEYS = tuple(f"guide.s{n:02d}.title" for n in range(1, 34))

# Frammenti matematici con parentesi graffe, passati come placeholder nominati
# per non confonderli con i campi di formattazione del catalogo.
_DIGITS = "{0,1,2}"
_DIGITS_SPACED = "{0, 1, 2}"
_J_VALUES = "{I_3, R_U}"
_MSC_INVERSE_POWER = "MSC^{(3−k) mod 3}"


def _h2(ins, number):
    """Intestazione di sezione: «N.  Titolo» con il titolo localizzato."""
    ins("h2", f"{number}.  {tr(SECTION_TITLE_KEYS[number - 1])}\n")


def build_guide_content(ins, sep):
    """Popola il tab Guida usando i callback `ins` e `sep` forniti da app.py."""
    # ═══════════════════════════════════════════════════════════════════════
    ins("h1", tr("guide.title") + "\n")
    sep()

    ins("h3", tr("guide.toc") + "\n")
    toc = [(str(n), key) for n, key in enumerate(SECTION_TITLE_KEYS, 1)]
    for n, key in toc:
        ins("toc", f"    {n:>2}.  {tr(key)}\n")
    sep()

    # ── 1 ──────────────────────────────────────────────────────────────────
    _h2(ins, 1)
    ins("body", tr("guide.s01.intro"))
    ins("bullet", tr("guide.s01.steps"))
    ins("body", tr("guide.s01.outro"))
    sep()

    # ── 2 ──────────────────────────────────────────────────────────────────
    _h2(ins, 2)
    ins("body", tr("guide.s02.intro"))
    ins("formula", tr("guide.s02.formula", digits=_DIGITS_SPACED))
    ins("body", tr("guide.s02.coordinates", digits=_DIGITS))
    ins("bullet", tr("guide.s02.digits"))
    ins("body", tr("guide.s02.convention"))
    sep()

    # ── 3 ──────────────────────────────────────────────────────────────────
    _h2(ins, 3)
    ins("body", tr("guide.s03.intro"))
    ins("formula",
        "    MSC:  (i₂, i₁, i₀)  →  (i₀, i₂, i₁)\n\n")
    ins("body", tr("guide.s03.properties_intro"))
    ins("bullet", tr("guide.s03.properties", digits=_DIGITS))
    sep()

    # ── 4 ──────────────────────────────────────────────────────────────────
    _h2(ins, 4)
    ins("body", tr("guide.s04.intro", digits=_DIGITS))
    rows_P = [
        ("SCD_U", "[0,1,2]", "guide.s04.row.SCD_U", tr("guide.order", order=1)),
        ("SDC_U", "[0,2,1]", "guide.s04.row.SDC_U", tr("guide.order", order=2)),
        ("CSD_U", "[1,0,2]", "guide.s04.row.CSD_U", tr("guide.order", order=2)),
        ("CDS_U", "[1,2,0]", "guide.s04.row.CDS_U", "= DSC⁻¹"),
        ("DSC_U", "[2,0,1]", "guide.s04.row.DSC_U", "= CDS⁻¹"),
        ("DCS_U", "[2,1,0]", "guide.s04.row.DCS_U", tr("guide.order", order=2)),
    ]
    for name, perm, desc_key, alg in rows_P:
        ins("bullet", "  •  ")
        ins("code", f"{name}  {perm}")
        ins("bullet", f"  —  {tr(desc_key)}   ")
        ins("note", f"[{alg}]\n")
    ins("body", tr("guide.s04.kronecker"))
    ins("note", tr("guide.s04.real_game_note"))
    sep()

    # ── 5 ──────────────────────────────────────────────────────────────────
    _h2(ins, 5)
    ins("body", tr("guide.s05.intro"))
    rows_J = [
        ("I_3", "[0,1,2]", "guide.s05.row.I_3", tr("guide.order", order=1)),
        ("R_U", "[2,1,0]", "guide.s05.row.R_U", tr("guide.order", order=2)),
    ]
    for name, perm, desc_key, alg in rows_J:
        ins("bullet", "  •  ")
        ins("code", f"{name}  {perm}")
        ins("bullet", f"  —  {tr(desc_key)}   ")
        ins("note", f"[{alg}]\n")
    ins("body", tr("guide.s05.kronecker", j_values=_J_VALUES))
    ins("hilight", tr("guide.s05.uniform"))
    ins("body", tr("guide.s05.real_game"))
    sep()

    # ── 6 ──────────────────────────────────────────────────────────────────
    ins("h3", tr("guide.s05.double_names.title") + "\n")
    ins("body", tr("guide.s05.double_names.intro", digits=_DIGITS))
    ins("formula", tr("guide.s05.double_names.formula"))
    ins("body", tr("guide.s05.double_names.body"))

    _h2(ins, 6)
    ins("body", tr("guide.s06.intro"))
    ins("formula",
        "    Stageᵢ  =  Pᵢ  ∘  MSC  ∘  Jᵢ\n\n")
    ins("bullet", tr("guide.s06.steps"))
    ins("body", tr("guide.s06.global"))
    ins("formula",
        "    T  =  Stage₂ ∘ Stage₁ ∘ Stage₀\n"
        "       =  P₂ ∘ MSC ∘ J₂ ∘ P₁ ∘ MSC ∘ J₁ ∘ P₀ ∘ MSC ∘ J₀\n\n")
    ins("body", tr("guide.s06.composition"))
    sep()

    # ── 7 ──────────────────────────────────────────────────────────────────
    _h2(ins, 7)
    ins("body", tr("guide.s07.intro"))
    ins("formula",
        "    MSC ∘ (A₂ ⊗ A₁ ⊗ A₀)  =  (A₀ ⊗ A₂ ⊗ A₁) ∘ MSC\n\n")
    ins("body", tr("guide.s07.rotation"))
    ins("warn", tr("guide.s07.wrong_formula"))
    sep()

    # ── 8 ──────────────────────────────────────────────────────────────────
    _h2(ins, 8)
    ins("body", tr("guide.s08.intro"))
    ins("formula",
        "    Stageᵢ  =  [(P2ᵢ∘J0ᵢ) ⊗ (P1ᵢ∘J2ᵢ) ⊗ (P0ᵢ∘J1ᵢ)]  ∘  MSC\n"
        "             =  Aᵢ  ∘  MSC\n\n")
    ins("body", tr("guide.s08.components"))
    ins("formula",
        "    Aᵢ  =  (P2ᵢ ∘ J0ᵢ)  ⊗  (P1ᵢ ∘ J2ᵢ)  ⊗  (P0ᵢ ∘ J1ᵢ)\n\n")
    ins("warn", tr("guide.s08.crossed_indices"))
    ins("body", tr("guide.s08.simplified"))
    ins("formula",
        "    T  =  A₂ ∘ MSC ∘ A₁ ∘ MSC ∘ A₀ ∘ MSC\n\n")
    ins("body", tr("guide.s08.symbolic_t"))
    sep()

    # ── 9 ──────────────────────────────────────────────────────────────────
    _h2(ins, 9)
    ins("body", tr("guide.s09.intro"))
    ins("bullet", tr("guide.s09.properties"))
    ins("body", tr("guide.s09.extended_group"))
    ins("body", tr("guide.s09.multiplicity"))
    sep()

    # ── 10 ─────────────────────────────────────────────────────────────────
    _h2(ins, 10)
    ins("hilight", tr("guide.s10.preset"))
    ins("body", tr("guide.s10.intro"))
    ins("bullet", tr("guide.s10.parameters"))
    ins("body", tr("guide.s10.terminology"))
    ins("body", tr("guide.s10.count_intro"))
    ins("formula", tr("guide.s10.count"))
    ins("ok", tr("guide.s10.activate"))
    sep()

    # ── 11 ─────────────────────────────────────────────────────────────────
    _h2(ins, 11)
    ins("body", tr("guide.s11.intro"))
    ins("bullet", tr("guide.s11.columns"))
    ins("h3", tr("guide.s11.reconstruction.title") + "\n")
    ins("body", tr("guide.s11.reconstruction.body"))
    ins("note", tr("guide.s11.anchors_note"))
    sep()

    # ── 12 ─────────────────────────────────────────────────────────────────
    _h2(ins, 12)
    ins("body", tr("guide.s12.intro"))
    ins("h3", tr("guide.s12.p_panel.title") + "\n")
    ins("body", tr("guide.s12.p_panel.intro"))
    ins("bullet", tr("guide.s12.p_panel.rows"))
    ins("h3", tr("guide.s12.j_panel.title") + "\n")
    ins("body", tr("guide.s12.j_panel.body"))
    ins("h3", tr("guide.s12.counter.title") + "\n")
    ins("body", tr("guide.s12.counter.body"))
    sep()

    # ── 13 ─────────────────────────────────────────────────────────────────
    _h2(ins, 13)
    ins("h3", f"  🎴 {tr('button.real_game')}\n")
    ins("body", tr("guide.s13.real_game.body"))
    ins("h3", f"  ⚡ {tr('button.uniform_j')}\n")
    ins("body", tr("guide.s13.uniform_j.body"))
    ins("h3", f"  ↺ {tr('button.quick_reset')}\n")
    ins("body", tr("guide.s13.reset.body"))
    sep()

    # ── 14 ─────────────────────────────────────────────────────────────────
    _h2(ins, 14)
    ins("body", tr("guide.s14.intro"))
    ins("bullet", tr("guide.s14.results"))
    sep()

    # ── 15 ─────────────────────────────────────────────────────────────────
    _h2(ins, 15)
    ins("body", tr("guide.s15.intro"))
    ins("h3", tr("guide.s15.how_to.title") + "\n")
    ins("bullet", tr("guide.s15.how_to.steps_1_4"))
    ins("bullet2", tr("guide.s15.how_to.columns"))
    ins("bullet", tr("guide.s15.how_to.steps_5_6"))

    ins("h3", tr("guide.s15.detail.title") + "\n")
    ins("body", tr("guide.s15.detail.intro"))
    ins("formula", tr("guide.s15.detail.formula"))
    ins("body", tr("guide.s15.detail.link"))
    ins("note", tr("guide.s15.detail.note"))

    ins("h3", tr("guide.s15.export.title") + "\n")
    ins("body", tr("guide.s15.export.intro"))
    ins("h3", tr("guide.s15.export.summary.title") + "\n")
    ins("bullet", tr("guide.s15.export.summary.items"))
    ins("h3", tr("guide.s15.export.raw.title") + "\n")
    ins("bullet", tr("guide.s15.export.raw.items"))
    ins("note", tr("guide.s15.export.excel_note"))
    sep()

    # ── 16 ─────────────────────────────────────────────────────────────────
    _h2(ins, 16)
    ins("body", tr("guide.s16.intro"))
    ins("h3", tr("guide.s16.load.title") + "\n")
    ins("bullet", tr("guide.s16.load.items"))
    ins("formula", tr("guide.s16.load.syntax"))
    ins("h3", tr("guide.s16.subtabs.title") + "\n")
    ins("bullet", tr("guide.s16.subtabs.items", digits=_DIGITS))

    ins("h3", tr("guide.s16.decompositions.title") + "\n")
    ins("body", tr("guide.s16.decompositions.body"))
    ins("bullet", tr("guide.s16.decompositions.items"))
    ins("note", tr("guide.s16.decompositions.note"))

    ins("h3", tr("guide.s16.protocol.title") + "\n")
    ins("body", tr("guide.s16.protocol.body"))
    sep()

    # ── 17 ─────────────────────────────────────────────────────────────────
    _h2(ins, 17)
    ins("body", tr("guide.s17.intro"))
    ins("h3", tr("guide.s17.left.title") + "\n")
    ins("body", tr("guide.s17.left.body"))
    ins("h3", tr("guide.s17.right.title") + "\n")
    ins("body", tr("guide.s17.right.body"))
    ins("formula", tr("guide.s17.inverse_formula", msc_power=_MSC_INVERSE_POWER))
    ins("note", tr("guide.s17.note"))
    sep()

    # ── 18 ─────────────────────────────────────────────────────────────────
    _h2(ins, 18)
    ins("body", tr("guide.s18.intro"))
    ins("h3", tr("guide.s18.load.title") + "\n")
    ins("bullet", tr("guide.s18.load.steps"))
    ins("body", tr("guide.s18.syntax_intro"))
    ins("formula",
        "    (P2 x P1 x P0) o MSC o (P2 x P1 x P0) o MSC o ...\n\n")
    ins("body", tr("guide.s18.aliases"))
    ins("formula", tr("guide.s18.aliases_formula", j_values=_J_VALUES))
    ins("note", tr("guide.s18.steps_note"))

    ins("h3", tr("guide.s18.grid.title") + "\n")
    ins("body", tr("guide.s18.grid.body"))

    ins("h3", tr("guide.s18.playback.title") + "\n")
    for btn, desc_key in [
        (f"⏮  {tr('shuffle.reset')}",           "guide.s18.playback.reset"),
        (f"⏭  {tr('shuffle.step_button')}",     "guide.s18.playback.step"),
        (f"▶ {tr('shuffle.play')} / ⏸ {tr('shuffle.pause')}",
                                                "guide.s18.playback.play"),
        (f"🔁  {tr('shuffle.replay')}",          "guide.s18.playback.replay"),
    ]:
        ins("bullet", "  •  ")
        ins("code", btn)
        ins("bullet", f"  —  {tr(desc_key)}\n")
    ins("body", tr("guide.s18.speed"))

    ins("h3", tr("guide.s18.navigation.title") + "\n")
    for btn, desc_key in [
        (f"⏮ {tr('shuffle.start')}",          "guide.s18.navigation.start"),
        (f"⏪ {tr('shuffle.start_step')}",     "guide.s18.navigation.start_step"),
        (f"◄ {tr('shuffle.back')}",           "guide.s18.navigation.back"),
        (f"{tr('shuffle.end_step')} ⏩",       "guide.s18.navigation.end_step"),
        (f"{tr('shuffle.next_step')} ⏭",      "guide.s18.navigation.next_step"),
        (f"{tr('shuffle.end')} ⏭",            "guide.s18.navigation.end"),
    ]:
        ins("bullet", "  •  ")
        ins("code", btn)
        ins("bullet", f"  —  {tr(desc_key)}\n")

    ins("h3", tr("guide.s18.card_by_card.title") + "\n")
    ins("body", tr("guide.s18.card_by_card.body"))
    ins("note", tr("guide.s18.card_by_card.note"))

    ins("h3", tr("guide.s18.inverse_vector.title") + "\n")
    ins("body", tr("guide.s18.inverse_vector.body"))
    sep()

    # ── 19 ─────────────────────────────────────────────────────────────────
    _h2(ins, 19)
    ins("body", tr("guide.s19.intro"))
    ins("h3", tr("guide.s19.setup.title") + "\n")
    ins("bullet", tr("guide.s19.setup.items"))
    ins("h3", tr("guide.s19.tabs.title") + "\n")
    ins("bullet", tr("guide.s19.tabs.items"))
    ins("h3", tr("guide.s19.errors.title") + "\n")
    ins("body", tr("guide.s19.errors.body"))
    sep()

    # ── 20 ─────────────────────────────────────────────────────────────────
    _h2(ins, 20)
    ins("body", tr("guide.s20.intro"))
    ins("bullet", tr("guide.s20.summary"))
    ins("body", tr("guide.s20.subtabs_intro"))
    ins("bullet", tr("guide.s20.subtabs"))
    ins("note", tr("guide.s20.note"))
    sep()

    # ── 21 ─────────────────────────────────────────────────────────────────
    _h2(ins, 21)
    ins("body", tr("guide.s21.intro"))
    ins("body", tr("guide.s21.subtabs_intro"))
    ins("bullet", tr("guide.s21.subtabs"))
    ins("ok", tr("guide.s21.result"))
    ins("note", tr("guide.s21.note"))
    sep()

    # ── 22 ─────────────────────────────────────────────────────────────────
    _h2(ins, 22)
    ins("body", tr("guide.s22.intro"))
    ins("bullet", tr("guide.s22.items"))
    ins("body", tr("guide.s22.center"))
    ins("h3", tr("guide.export_heading") + "\n")
    ins("bullet", tr("guide.s22.export"))
    sep()

    # ── 23 ─────────────────────────────────────────────────────────────────
    _h2(ins, 23)
    ins("body", tr("guide.s23.intro"))
    ins("bullet", tr("guide.s23.items"))
    ins("h3", tr("guide.export_heading") + "\n")
    ins("bullet", tr("guide.s23.export"))
    sep()

    # ── 24 ─────────────────────────────────────────────────────────────────
    _h2(ins, 24)
    ins("body", tr("guide.s24.intro"))
    ins("bullet", tr("guide.s24.items"))
    ins("body", tr("guide.s24.browser"))
    ins("note", tr("guide.s24.note"))
    sep()

    # ── 25 ─────────────────────────────────────────────────────────────────
    _h2(ins, 25)
    ins("h3", tr("guide.s25.real_game.title") + "\n")
    ins("bullet", tr("guide.s25.real_game.steps"))
    ins("body", "\n")

    ins("h3", tr("guide.s25.expression.title") + "\n")
    ins("bullet", tr("guide.s25.expression.steps"))
    ins("body", "\n")

    ins("h3", tr("guide.s25.export.title") + "\n")
    ins("bullet", tr("guide.s25.export.steps"))
    sep()

    # ── 26 ─────────────────────────────────────────────────────────────────
    _h2(ins, 26)

    ins("h3", tr("guide.s26.csv.title") + "\n")
    ins("body", tr("guide.s26.nine_columns"))
    for col, desc_key in [
        ("#",             "guide.s26.csv.number"),
        ("Stage0",        "guide.s26.csv.stage0"),
        ("Stage1",        "guide.s26.csv.stage1"),
        ("Stage2",        "guide.s26.csv.stage2"),
        ("A0",            "guide.s26.csv.a0"),
        ("A1",            "guide.s26.csv.a1"),
        ("A2",            "guide.s26.csv.a2"),
        ("T_simbolica",   "guide.s26.csv.t_symbolic"),
        ("T_permutazione", "guide.s26.csv.t_permutation"),
    ]:
        ins("bullet", "  •  ")
        ins("code", f"{col}")
        ins("bullet", f"  —  {tr(desc_key)}\n")
    ins("body", tr("guide.s26.csv.excel"))

    ins("h3", tr("guide.s26.analysis_csv.title") + "\n")
    ins("body", tr("guide.s26.analysis_csv.intro"))
    for col, desc_key in [
        ("T_permutazione",          "guide.s26.analysis_csv.t_permutation"),
        ("T_simboliche_distinte",   "guide.s26.analysis_csv.distinct"),
        ("n_sim_distinte",          "guide.s26.analysis_csv.count"),
    ]:
        ins("bullet", "  •  ")
        ins("code", col)
        ins("bullet", f"  —  {tr(desc_key)}\n")
    ins("body", "\n")

    ins("h3", tr("guide.s26.analysis_excel.title") + "\n")
    ins("body", tr("guide.s26.two_sheets"))
    ins("bullet", tr("guide.s26.analysis_excel.sheets"))

    ins("h3", tr("guide.s26.analysis_html.title") + "\n")
    ins("body", tr("guide.s26.analysis_html.body"))

    ins("h3", tr("guide.s26.raw_csv.title") + "\n")
    ins("body", tr("guide.s26.raw_csv.body"))

    ins("h3", tr("guide.s26.raw_excel.title") + "\n")
    ins("body", tr("guide.s26.raw_excel.body"))

    ins("h3", tr("guide.s26.pdf.title") + "\n")
    ins("body", tr("guide.s26.pdf.intro"))
    ins("bullet", tr("guide.s26.pdf.items"))
    ins("warn", tr("guide.s26.pdf.warning"))
    sep()

    # ── 27 ─────────────────────────────────────────────────────────────────
    _h2(ins, 27)
    ins("body", tr("guide.s27.intro"))
    for scenario_key, n, approx_key, advice_key in [
        ("guide.s27.scenario.no_filter",   "5 159 780 352",
         "guide.s27.approx.5_billion",     "guide.s27.advice.refused"),
        ("guide.s27.scenario.uniform_j",   "   80 621 568",
         "guide.s27.approx.80_million",    "guide.s27.advice.refused"),
        ("guide.s27.scenario.fixed_level", "23 887 872",
         "guide.s27.approx.24_million",    "guide.s27.advice.refused"),
        ("guide.s27.scenario.real_game",   "        1 728",
         "guide.s27.approx.1728",          "guide.s27.advice.normal"),
        ("guide.s27.scenario.single_stage", "1 – 1 728",
         "guide.s27.approx.variable",      "guide.s27.advice.exploration"),
    ]:
        ins("bullet", f"  •  {tr(scenario_key):40}  →  {n:>18} ({tr(approx_key)})\n")
        ins("bullet2", f"     {tr(advice_key)}\n")
    ins("body", "\n")
    ins("h3", tr("guide.s27.limits.title") + "\n")
    ins("body", tr("guide.s27.limits.intro"))
    ins("bullet", tr("guide.s27.limits.items"))
    ins("body", tr("guide.s27.limits.confirmation"))
    ins("ok", tr("guide.s27.counter"))
    ins("h3", tr("guide.s27.parallel.title") + "\n")
    ins("body", tr("guide.s27.parallel.intro"))
    ins("bullet", tr("guide.s27.parallel.items"))
    ins("body", tr("guide.s27.parallel.workers"))
    ins("note", tr("guide.s27.parallel.sequential_note"))
    ins("note", tr("guide.s27.parallel.dedup_note"))
    ins("h3", tr("guide.s27.detailed_pdf.title") + "\n")
    ins("body", tr("guide.s27.detailed_pdf.intro"))
    ins("bullet", tr("guide.s27.detailed_pdf.items"))
    ins("bullet2", tr("guide.s27.detailed_pdf.boards"))
    ins("ok", tr("guide.s27.detailed_pdf.boards_valid"))
    ins("note", tr("guide.s27.detailed_pdf.boards_note"))
    ins("bullet", tr("guide.s27.detailed_pdf.matrix"))
    ins("body", tr("guide.s27.detailed_pdf.order"))
    ins("body", tr("guide.s27.detailed_pdf.filters"))
    ins("h3", tr("guide.s27.outside.title") + "\n")
    ins("body", tr("guide.s27.outside.intro"))
    ins("bullet", tr("guide.s27.outside.items"))
    ins("h3", tr("guide.s27.cancel.title") + "\n")
    ins("body", tr("guide.s27.cancel.intro"))
    ins("bullet", tr("guide.s27.cancel.items"))
    ins("note", tr("guide.s27.cancel.note"))
    ins("h3", tr("guide.s27.eta.title") + "\n")
    ins("body", tr("guide.s27.eta.body"))
    ins("warn", tr("guide.s27.warning"))
    sep()

    # ── 28 ─────────────────────────────────────────────────────────────────
    _h2(ins, 28)
    ins("body", tr("guide.s28.intro"))
    ins("formula", "    pip install numpy reportlab openpyxl pypdf pikepdf\n\n")
    for pkg, desc_key in [
        ("numpy",     "guide.s28.dep.numpy"),
        ("tkinter",   "guide.s28.dep.tkinter"),
        ("reportlab", "guide.s28.dep.reportlab"),
        ("openpyxl",  "guide.s28.dep.openpyxl"),
        ("pypdf",     "guide.s28.dep.pypdf"),
        ("pikepdf",   "guide.s28.dep.pikepdf"),
    ]:
        ins("bullet", "  -  ")
        ins("code", pkg)
        ins("bullet", f"  -  {tr(desc_key)}\n")
    ins("body", tr("guide.s28.optional"))
    ins("note", tr("guide.s28.install_note"))
    ins("body", tr("guide.s28.startup_intro"))
    ins("formula", tr("guide.s28.startup"))
    ins("note", tr("guide.s28.linux_note"))
    sep()

    # ── 29 ─────────────────────────────────────────────────────────────────
    _h2(ins, 29)
    ins("body", tr("guide.s29.intro"))
    ins("h3", tr("guide.s29.action_bar.title") + "\n")
    ins("body", tr("guide.s29.action_bar.intro"))
    for btn, desc_key in [
        (f"🔢  {tr('button.count')}",           "guide.s29.action.count"),
        (f"⬇  {tr('button.generate')}",         "guide.s29.action.generate"),
        (f"↺  {tr('button.reset_all')}",        "guide.s29.action.reset_all"),
        (f"🎓  {tr('button.beginner_mode')}",   "guide.s29.action.beginner"),
        (tr("label.combinations"),              "guide.s29.action.combinations"),
        (f"🔮  {tr('button.cayley')}",          "guide.s29.action.cayley"),
        (f"🔬  {tr('button.conjugacy')}",       "guide.s29.action.conjugacy"),
        (f"📋  {tr('button.protocol')}",        "guide.s29.action.protocol"),
        (f"🖥️  {tr('button.presentation')}",    "guide.s29.action.presentation"),
        (f"✔  {tr('button.verify')}",           "guide.s29.action.verify"),
        (f"⚙️  {tr('button.settings')}",        "guide.s29.action.settings"),
        (f"⏻  {tr('button.exit')}",             "guide.s29.action.exit"),
        (f"✕  {tr('button.cancel_export')}",    "guide.s29.action.cancel"),
    ]:
        ins("bullet", "  •  ")
        ins("code", btn)
        ins("bullet", f"  —  {tr(desc_key)}\n")
    ins("body", "\n")
    ins("h3", tr("guide.s29.verify.title") + "\n")
    ins("body", tr("guide.s29.verify.intro"))
    ins("bullet", tr("guide.s29.verify.items"))
    ins("note", tr("guide.s29.verify.note"))

    ins("h3", tr("guide.s29.presentation.title") + "\n")
    ins("body", tr("guide.s29.presentation.body"))
    ins("bullet", tr("guide.s29.presentation.keys"))

    ins("h3", tr("guide.s29.mode.title") + "\n")
    ins("body", tr("guide.s29.mode.intro"))
    ins("bullet", tr("guide.s29.mode.items"))
    ins("note", tr("guide.s29.mode.note"))
    ins("h3", tr("guide.s29.start_here.title") + "\n")
    ins("body", tr("guide.s29.start_here.body"))
    ins("h3", tr("guide.s29.banner.title") + "\n")
    ins("body", tr("guide.s29.banner.body"))
    ins("h3", tr("guide.s29.tooltips.title") + "\n")
    ins("body", tr("guide.s29.tooltips.body"))
    ins("h3", tr("guide.s29.legend.title") + "\n")
    ins("body", tr("guide.s29.legend.body"))
    ins("h3", tr("guide.s29.empty_states.title") + "\n")
    ins("body", tr("guide.s29.empty_states.body"))
    ins("h3", tr("guide.s29.text_size.title") + "\n")
    ins("body", tr("guide.s29.text_size.body"))
    sep()

    # ── 30 ─────────────────────────────────────────────────────────────────
    _h2(ins, 30)
    ins("body", tr("guide.s30.intro"))
    ins("bullet", tr("guide.s30.terms"))
    sep()

    # ── 31 ─────────────────────────────────────────────────────────────────
    _h2(ins, 31)
    ins("body", tr("guide.s31.intro"))
    ins("bullet", tr("guide.s31.steps"))
    sep()

    # ── 32 ─────────────────────────────────────────────────────────────────
    _h2(ins, 32)
    ins("body", tr("guide.s32.intro"))
    ins("h3", tr("guide.s32.preview_explorer.title") + "\n")
    ins("body", tr("guide.s32.preview_explorer.body"))
    ins("h3", tr("guide.s32.cayley.title") + "\n")
    ins("body", tr("guide.s32.cayley.body"))
    ins("h3", tr("guide.s32.conjugacy.title") + "\n")
    ins("body", tr("guide.s32.conjugacy.body"))
    sep()

    # ── 33 ─────────────────────────────────────────────────────────────────
    _h2(ins, 33)
    for n in range(1, 7):
        ins("h3", tr(f"guide.s33.q{n}") + "\n")
        ins("body", tr(f"guide.s33.a{n}"))
    sep()

    from .. import __version__ as _ver
    ins("body", tr("guide.footer", version=_ver))


def render_guide_segments(language=None):
    """
    Restituisce la Guida come lista di coppie (tag, testo), senza widget Tk.

    Usa gli stessi callback di app.py (stessa separatrice): serve ai test e a
    chi deve leggere il testo della Guida in una lingua precisa. Se
    `language` è indicato la lingua attiva viene cambiata solo per la durata
    della costruzione e poi ripristinata.
    """
    from . import i18n

    previous = i18n.get_language()
    if language is not None:
        i18n.set_language(language)
    try:
        segments = []
        build_guide_content(lambda tag, text: segments.append((tag, text)),
                            lambda: segments.append(("sep", "\n" + "─" * 90 + "\n")))
    finally:
        i18n.set_language(previous)
    return segments
