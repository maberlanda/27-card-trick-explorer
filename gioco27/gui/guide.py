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

I7 — percorso didattico. Le sezioni hanno un identificatore stabile
(``s01``…``s33`` per quelle storiche, ``i1``…``i6``, ``i2m``, ``i2t`` e
``storia`` per le nuove) e sono raccolte in PARTI che seguono la
progressione del programma, non l'ordine dei file. Il numero mostrato è la
posizione nel percorso: banner e riferimenti incrociati usano l'identificatore
(``numero_sezione``, placeholder ``{ref_<id>}`` nei testi), quindi riordinare
le parti non rompe nessun collegamento.
"""

from .i18n import tr
from .glossary import GLOSSARIO_MATEMATICO, GLOSSARIO_NARRATIVO
from .livelli import LIVELLI


#: Il percorso: (chiave della parte, identificatori delle sezioni).
PARTI = (
    ("guide.part.a", ("s29", "s25")),                       # Inizia qui
    ("guide.part.b", ("s01", "s19")),                       # Il gesto fisico
    ("guide.part.c", ("s02", "s03", "i2m")),                # Posizioni e base 3
    ("guide.part.d", ("s04", "s05", "s10", "s11", "i2t")),  # Tavola e tabellone
    ("guide.part.e", ("s06", "s07", "s08", "s14", "s20", "s17", "s18")),
    ("guide.part.f", ("i1",)),                              # Procedure e strategie
    ("guide.part.g", ("i3",)),                              # Errori e recupero
    ("guide.part.h", ("i4",)),                              # Spettatore
    ("guide.part.i", ("s16", "i5", "s24")),                 # Riconoscimento
    ("guide.part.j", ("s09", "s22", "s23")),                # Struttura di H e Γ
    ("guide.part.k", ("s12", "s13", "s15", "s21", "i6")),   # Laboratorio
    ("guide.part.l", ("storia",)),                          # Storia (facoltativa)
    ("guide.part.m", ("s30", "s31", "s26", "s32", "s27", "s28", "s33")),
)

#: Identificatori nell'ordine del percorso; il numero di sezione è la posizione.
SEZIONI = tuple(sid for _parte, sezioni in PARTI for sid in sezioni)
_NUMERO = {sid: n for n, sid in enumerate(SEZIONI, 1)}

#: Chiavi dei titoli, nell'ordine dell'indice (compatibilità con app/test).
SECTION_TITLE_KEYS = tuple(f"guide.{sid}.title" for sid in SEZIONI)

# Frammenti matematici con parentesi graffe, passati come placeholder nominati
# per non confonderli con i campi di formattazione del catalogo.
_DIGITS = "{0,1,2}"
_DIGITS_SPACED = "{0, 1, 2}"
_J_VALUES = "{I_3, R_U}"
_MSC_INVERSE_POWER = "MSC^{(3−k) mod 3}"

#: Placeholder dei riferimenti incrociati: «sezione {ref_s10}» → numero reale.
_RIFERIMENTI = {f"ref_{sid}": str(n) for sid, n in _NUMERO.items()}


def numero_sezione(sezione):
    """Numero mostrato di una sezione, dato l'identificatore (o il numero)."""
    if sezione is None:
        return None
    sezione = str(sezione)
    if sezione in _NUMERO:
        return _NUMERO[sezione]
    if sezione.isdigit() and 1 <= int(sezione) <= len(SEZIONI):
        return int(sezione)
    raise KeyError(sezione)


def _t(key, **valori):
    """`tr` con i riferimenti incrociati sempre disponibili per le chiavi guide.*."""
    if key.startswith("guide."):
        valori = {**_RIFERIMENTI, "digits": _DIGITS, **valori}
    return tr(key, **valori)


def _h2(ins, sid):
    """Intestazione di sezione: «N.  Titolo» con il titolo localizzato."""
    ins("h2", f"{_NUMERO[sid]}.  {_t(f'guide.{sid}.title')}\n")


def _s01(ins, sep):
    _h2(ins, "s01")
    ins("body", _t("guide.s01.intro"))
    ins("bullet", _t("guide.s01.steps"))
    ins("body", _t("guide.s01.outro"))
    sep()


def _s02(ins, sep):
    _h2(ins, "s02")
    ins("body", _t("guide.s02.intro"))
    ins("formula", _t("guide.s02.formula", digits=_DIGITS_SPACED))
    ins("body", _t("guide.s02.coordinates", digits=_DIGITS))
    ins("bullet", _t("guide.s02.digits"))
    ins("body", _t("guide.s02.convention"))
    sep()


def _s03(ins, sep):
    _h2(ins, "s03")
    ins("body", _t("guide.s03.intro"))
    ins("formula",
        "    MSC:  (i₂, i₁, i₀)  →  (i₀, i₂, i₁)\n\n")
    ins("body", _t("guide.s03.properties_intro"))
    ins("bullet", _t("guide.s03.properties", digits=_DIGITS))
    sep()


def _s04(ins, sep):
    _h2(ins, "s04")
    ins("body", _t("guide.s04.intro", digits=_DIGITS))
    rows_P = [
        ("SCD_U", "[0,1,2]", "guide.s04.row.SCD_U", _t("guide.order", order=1)),
        ("SDC_U", "[0,2,1]", "guide.s04.row.SDC_U", _t("guide.order", order=2)),
        ("CSD_U", "[1,0,2]", "guide.s04.row.CSD_U", _t("guide.order", order=2)),
        ("CDS_U", "[1,2,0]", "guide.s04.row.CDS_U", "= DSC⁻¹"),
        ("DSC_U", "[2,0,1]", "guide.s04.row.DSC_U", "= CDS⁻¹"),
        ("DCS_U", "[2,1,0]", "guide.s04.row.DCS_U", _t("guide.order", order=2)),
    ]
    for name, perm, desc_key, alg in rows_P:
        ins("bullet", "  •  ")
        ins("code", f"{name}  {perm}")
        ins("bullet", f"  —  {_t(desc_key)}   ")
        ins("note", f"[{alg}]\n")
    ins("body", _t("guide.s04.kronecker"))
    ins("note", _t("guide.s04.real_game_note"))
    sep()


def _s05(ins, sep):
    _h2(ins, "s05")
    ins("body", _t("guide.s05.intro"))
    rows_J = [
        ("I_3", "[0,1,2]", "guide.s05.row.I_3", _t("guide.order", order=1)),
        ("R_U", "[2,1,0]", "guide.s05.row.R_U", _t("guide.order", order=2)),
    ]
    for name, perm, desc_key, alg in rows_J:
        ins("bullet", "  •  ")
        ins("code", f"{name}  {perm}")
        ins("bullet", f"  —  {_t(desc_key)}   ")
        ins("note", f"[{alg}]\n")
    ins("body", _t("guide.s05.kronecker", j_values=_J_VALUES))
    ins("hilight", _t("guide.s05.uniform"))
    ins("body", _t("guide.s05.real_game"))
    sep()

    ins("h3", _t("guide.s05.double_names.title") + "\n")
    ins("body", _t("guide.s05.double_names.intro", digits=_DIGITS))
    ins("formula", _t("guide.s05.double_names.formula"))
    ins("body", _t("guide.s05.double_names.body"))


def _s06(ins, sep):
    _h2(ins, "s06")
    ins("body", _t("guide.s06.intro"))
    ins("formula",
        "    Stageᵢ  =  Pᵢ  ∘  MSC  ∘  Jᵢ\n\n")
    ins("bullet", _t("guide.s06.steps"))
    ins("body", _t("guide.s06.global"))
    ins("formula",
        "    T  =  Stage₂ ∘ Stage₁ ∘ Stage₀\n"
        "       =  P₂ ∘ MSC ∘ J₂ ∘ P₁ ∘ MSC ∘ J₁ ∘ P₀ ∘ MSC ∘ J₀\n\n")
    ins("body", _t("guide.s06.composition"))
    sep()


def _s07(ins, sep):
    _h2(ins, "s07")
    ins("body", _t("guide.s07.intro"))
    ins("formula",
        "    MSC ∘ (A₂ ⊗ A₁ ⊗ A₀)  =  (A₀ ⊗ A₂ ⊗ A₁) ∘ MSC\n\n")
    ins("body", _t("guide.s07.rotation"))
    ins("warn", _t("guide.s07.wrong_formula"))
    sep()


def _s08(ins, sep):
    _h2(ins, "s08")
    ins("body", _t("guide.s08.intro"))
    ins("formula",
        "    Stageᵢ  =  [(P2ᵢ∘J0ᵢ) ⊗ (P1ᵢ∘J2ᵢ) ⊗ (P0ᵢ∘J1ᵢ)]  ∘  MSC\n"
        "             =  Aᵢ  ∘  MSC\n\n")
    ins("body", _t("guide.s08.components"))
    ins("formula",
        "    Aᵢ  =  (P2ᵢ ∘ J0ᵢ)  ⊗  (P1ᵢ ∘ J2ᵢ)  ⊗  (P0ᵢ ∘ J1ᵢ)\n\n")
    ins("warn", _t("guide.s08.crossed_indices"))
    ins("body", _t("guide.s08.simplified"))
    ins("formula",
        "    T  =  A₂ ∘ MSC ∘ A₁ ∘ MSC ∘ A₀ ∘ MSC\n\n")
    ins("body", _t("guide.s08.symbolic_t"))
    sep()


def _s09(ins, sep):
    _h2(ins, "s09")
    ins("body", _t("guide.s09.intro"))
    ins("bullet", _t("guide.s09.properties"))
    ins("body", _t("guide.s09.extended_group"))
    ins("body", _t("guide.s09.multiplicity"))
    sep()


def _s10(ins, sep):
    _h2(ins, "s10")
    ins("hilight", _t("guide.s10.preset"))
    ins("body", _t("guide.s10.intro"))
    ins("bullet", _t("guide.s10.parameters"))
    ins("body", _t("guide.s10.terminology"))
    ins("body", _t("guide.s10.count_intro"))
    ins("formula", _t("guide.s10.count"))
    ins("ok", _t("guide.s10.activate"))
    sep()


def _s11(ins, sep):
    _h2(ins, "s11")
    ins("body", _t("guide.s11.intro"))
    ins("bullet", _t("guide.s11.columns"))
    ins("h3", _t("guide.s11.reconstruction.title") + "\n")
    ins("body", _t("guide.s11.reconstruction.body"))
    ins("note", _t("guide.s11.anchors_note"))
    sep()


def _s12(ins, sep):
    _h2(ins, "s12")
    ins("body", _t("guide.s12.intro"))
    ins("h3", _t("guide.s12.p_panel.title") + "\n")
    ins("body", _t("guide.s12.p_panel.intro"))
    ins("bullet", _t("guide.s12.p_panel.rows"))
    ins("h3", _t("guide.s12.j_panel.title") + "\n")
    ins("body", _t("guide.s12.j_panel.body"))
    ins("h3", _t("guide.s12.counter.title") + "\n")
    ins("body", _t("guide.s12.counter.body"))
    sep()


def _s13(ins, sep):
    _h2(ins, "s13")
    ins("h3", f"  🎴 {_t('button.real_game')}\n")
    ins("body", _t("guide.s13.real_game.body"))
    ins("h3", f"  ⚡ {_t('button.uniform_j')}\n")
    ins("body", _t("guide.s13.uniform_j.body"))
    ins("h3", f"  ↺ {_t('button.quick_reset')}\n")
    ins("body", _t("guide.s13.reset.body"))
    sep()


def _s14(ins, sep):
    _h2(ins, "s14")
    ins("body", _t("guide.s14.intro"))
    ins("bullet", _t("guide.s14.results"))
    sep()


def _s15(ins, sep):
    _h2(ins, "s15")
    ins("body", _t("guide.s15.intro"))
    ins("h3", _t("guide.s15.how_to.title") + "\n")
    ins("bullet", _t("guide.s15.how_to.steps_1_4"))
    ins("bullet2", _t("guide.s15.how_to.columns"))
    ins("bullet", _t("guide.s15.how_to.steps_5_6"))

    ins("h3", _t("guide.s15.detail.title") + "\n")
    ins("body", _t("guide.s15.detail.intro"))
    ins("formula", _t("guide.s15.detail.formula"))
    ins("body", _t("guide.s15.detail.link"))
    ins("note", _t("guide.s15.detail.note"))

    ins("h3", _t("guide.s15.export.title") + "\n")
    ins("body", _t("guide.s15.export.intro"))
    ins("h3", _t("guide.s15.export.summary.title") + "\n")
    ins("bullet", _t("guide.s15.export.summary.items"))
    ins("h3", _t("guide.s15.export.raw.title") + "\n")
    ins("bullet", _t("guide.s15.export.raw.items"))
    ins("note", _t("guide.s15.export.excel_note"))
    sep()


def _s16(ins, sep):
    _h2(ins, "s16")
    ins("body", _t("guide.s16.intro"))
    ins("h3", _t("guide.s16.load.title") + "\n")
    ins("bullet", _t("guide.s16.load.items"))
    ins("formula", _t("guide.s16.load.syntax"))
    ins("h3", _t("guide.s16.subtabs.title") + "\n")
    ins("bullet", _t("guide.s16.subtabs.items", digits=_DIGITS))

    ins("h3", _t("guide.s16.decompositions.title") + "\n")
    ins("body", _t("guide.s16.decompositions.body"))
    ins("bullet", _t("guide.s16.decompositions.items"))
    ins("note", _t("guide.s16.decompositions.note"))

    ins("h3", _t("guide.s16.protocol.title") + "\n")
    ins("body", _t("guide.s16.protocol.body"))
    sep()


def _s17(ins, sep):
    _h2(ins, "s17")
    ins("body", _t("guide.s17.intro"))
    ins("h3", _t("guide.s17.left.title") + "\n")
    ins("body", _t("guide.s17.left.body"))
    ins("h3", _t("guide.s17.right.title") + "\n")
    ins("body", _t("guide.s17.right.body"))
    ins("formula", _t("guide.s17.inverse_formula", msc_power=_MSC_INVERSE_POWER))
    ins("note", _t("guide.s17.note"))
    sep()


def _s18(ins, sep):
    _h2(ins, "s18")
    ins("body", _t("guide.s18.intro"))
    ins("h3", _t("guide.s18.load.title") + "\n")
    ins("bullet", _t("guide.s18.load.steps"))
    ins("body", _t("guide.s18.syntax_intro"))
    ins("formula",
        "    (P2 x P1 x P0) o MSC o (P2 x P1 x P0) o MSC o ...\n\n")
    ins("body", _t("guide.s18.aliases"))
    ins("formula", _t("guide.s18.aliases_formula", j_values=_J_VALUES))
    ins("note", _t("guide.s18.steps_note"))

    ins("h3", _t("guide.s18.grid.title") + "\n")
    ins("body", _t("guide.s18.grid.body"))

    ins("h3", _t("guide.s18.playback.title") + "\n")
    for btn, desc_key in [
        (f"⏮  {_t('shuffle.reset')}",           "guide.s18.playback.reset"),
        (f"⏭  {_t('shuffle.step_button')}",     "guide.s18.playback.step"),
        (f"▶ {_t('shuffle.play')} / ⏸ {_t('shuffle.pause')}",
                                                "guide.s18.playback.play"),
        (f"🔁  {_t('shuffle.replay')}",          "guide.s18.playback.replay"),
    ]:
        ins("bullet", "  •  ")
        ins("code", btn)
        ins("bullet", f"  —  {_t(desc_key)}\n")
    ins("body", _t("guide.s18.speed"))

    ins("h3", _t("guide.s18.navigation.title") + "\n")
    for btn, desc_key in [
        (f"⏮ {_t('shuffle.start')}",          "guide.s18.navigation.start"),
        (f"⏪ {_t('shuffle.start_step')}",     "guide.s18.navigation.start_step"),
        (f"◄ {_t('shuffle.back')}",           "guide.s18.navigation.back"),
        (f"{_t('shuffle.end_step')} ⏩",       "guide.s18.navigation.end_step"),
        (f"{_t('shuffle.next_step')} ⏭",      "guide.s18.navigation.next_step"),
        (f"{_t('shuffle.end')} ⏭",            "guide.s18.navigation.end"),
    ]:
        ins("bullet", "  •  ")
        ins("code", btn)
        ins("bullet", f"  —  {_t(desc_key)}\n")

    ins("h3", _t("guide.s18.card_by_card.title") + "\n")
    ins("body", _t("guide.s18.card_by_card.body"))
    ins("note", _t("guide.s18.card_by_card.note"))

    ins("h3", _t("guide.s18.inverse_vector.title") + "\n")
    ins("body", _t("guide.s18.inverse_vector.body"))
    sep()


def _s19(ins, sep):
    _h2(ins, "s19")
    ins("body", _t("guide.s19.intro"))
    ins("h3", _t("guide.s19.setup.title") + "\n")
    ins("bullet", _t("guide.s19.setup.items"))
    ins("h3", _t("guide.s19.tabs.title") + "\n")
    ins("bullet", _t("guide.s19.tabs.items"))
    ins("h3", _t("guide.s19.errors.title") + "\n")
    ins("body", _t("guide.s19.errors.body"))
    sep()


def _s20(ins, sep):
    _h2(ins, "s20")
    ins("body", _t("guide.s20.intro"))
    ins("bullet", _t("guide.s20.summary"))
    ins("body", _t("guide.s20.subtabs_intro"))
    ins("bullet", _t("guide.s20.subtabs"))
    ins("note", _t("guide.s20.note"))
    sep()


def _s21(ins, sep):
    _h2(ins, "s21")
    ins("body", _t("guide.s21.intro"))
    ins("body", _t("guide.s21.subtabs_intro"))
    ins("bullet", _t("guide.s21.subtabs"))
    ins("ok", _t("guide.s21.result"))
    ins("note", _t("guide.s21.note"))
    sep()


def _s22(ins, sep):
    _h2(ins, "s22")
    ins("body", _t("guide.s22.intro"))
    ins("bullet", _t("guide.s22.items"))
    ins("body", _t("guide.s22.center"))
    ins("h3", _t("guide.export_heading") + "\n")
    ins("bullet", _t("guide.s22.export"))
    sep()


def _s23(ins, sep):
    _h2(ins, "s23")
    ins("body", _t("guide.s23.intro"))
    ins("bullet", _t("guide.s23.items"))
    ins("h3", _t("guide.export_heading") + "\n")
    ins("bullet", _t("guide.s23.export"))
    sep()


def _s24(ins, sep):
    _h2(ins, "s24")
    ins("body", _t("guide.s24.intro"))
    ins("bullet", _t("guide.s24.items"))
    ins("body", _t("guide.s24.browser"))
    ins("note", _t("guide.s24.note"))
    sep()


def _s25(ins, sep):
    _h2(ins, "s25")
    ins("h3", _t("guide.s25.real_game.title") + "\n")
    ins("bullet", _t("guide.s25.real_game.steps"))
    ins("body", "\n")

    ins("h3", _t("guide.s25.expression.title") + "\n")
    ins("bullet", _t("guide.s25.expression.steps"))
    ins("body", "\n")

    ins("h3", _t("guide.s25.export.title") + "\n")
    ins("bullet", _t("guide.s25.export.steps"))
    sep()


def _s26(ins, sep):
    _h2(ins, "s26")

    ins("h3", _t("guide.s26.csv.title") + "\n")
    ins("body", _t("guide.s26.nine_columns"))
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
        ins("bullet", f"  —  {_t(desc_key)}\n")
    ins("body", _t("guide.s26.csv.excel"))

    ins("h3", _t("guide.s26.analysis_csv.title") + "\n")
    ins("body", _t("guide.s26.analysis_csv.intro"))
    for col, desc_key in [
        ("T_permutazione",          "guide.s26.analysis_csv.t_permutation"),
        ("T_simboliche_distinte",   "guide.s26.analysis_csv.distinct"),
        ("n_sim_distinte",          "guide.s26.analysis_csv.count"),
    ]:
        ins("bullet", "  •  ")
        ins("code", col)
        ins("bullet", f"  —  {_t(desc_key)}\n")
    ins("body", "\n")

    ins("h3", _t("guide.s26.analysis_excel.title") + "\n")
    ins("body", _t("guide.s26.two_sheets"))
    ins("bullet", _t("guide.s26.analysis_excel.sheets"))

    ins("h3", _t("guide.s26.analysis_html.title") + "\n")
    ins("body", _t("guide.s26.analysis_html.body"))

    ins("h3", _t("guide.s26.raw_csv.title") + "\n")
    ins("body", _t("guide.s26.raw_csv.body"))

    ins("h3", _t("guide.s26.raw_excel.title") + "\n")
    ins("body", _t("guide.s26.raw_excel.body"))

    ins("h3", _t("guide.s26.pdf.title") + "\n")
    ins("body", _t("guide.s26.pdf.intro"))
    ins("bullet", _t("guide.s26.pdf.items"))
    ins("warn", _t("guide.s26.pdf.warning"))
    sep()


def _s27(ins, sep):
    _h2(ins, "s27")
    ins("body", _t("guide.s27.intro"))
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
        ins("bullet", f"  •  {_t(scenario_key):40}  →  {n:>18} ({_t(approx_key)})\n")
        ins("bullet2", f"     {_t(advice_key)}\n")
    ins("body", "\n")
    ins("h3", _t("guide.s27.limits.title") + "\n")
    ins("body", _t("guide.s27.limits.intro"))
    ins("bullet", _t("guide.s27.limits.items"))
    ins("body", _t("guide.s27.limits.confirmation"))
    ins("ok", _t("guide.s27.counter"))
    ins("h3", _t("guide.s27.parallel.title") + "\n")
    ins("body", _t("guide.s27.parallel.intro"))
    ins("bullet", _t("guide.s27.parallel.items"))
    ins("body", _t("guide.s27.parallel.workers"))
    ins("note", _t("guide.s27.parallel.sequential_note"))
    ins("note", _t("guide.s27.parallel.dedup_note"))
    ins("h3", _t("guide.s27.detailed_pdf.title") + "\n")
    ins("body", _t("guide.s27.detailed_pdf.intro"))
    ins("bullet", _t("guide.s27.detailed_pdf.items"))
    ins("bullet2", _t("guide.s27.detailed_pdf.boards"))
    ins("ok", _t("guide.s27.detailed_pdf.boards_valid"))
    ins("note", _t("guide.s27.detailed_pdf.boards_note"))
    ins("bullet", _t("guide.s27.detailed_pdf.matrix"))
    ins("body", _t("guide.s27.detailed_pdf.order"))
    ins("body", _t("guide.s27.detailed_pdf.filters"))
    ins("h3", _t("guide.s27.outside.title") + "\n")
    ins("body", _t("guide.s27.outside.intro"))
    ins("bullet", _t("guide.s27.outside.items"))
    ins("h3", _t("guide.s27.cancel.title") + "\n")
    ins("body", _t("guide.s27.cancel.intro"))
    ins("bullet", _t("guide.s27.cancel.items"))
    ins("note", _t("guide.s27.cancel.note"))
    ins("h3", _t("guide.s27.eta.title") + "\n")
    ins("body", _t("guide.s27.eta.body"))
    ins("warn", _t("guide.s27.warning"))
    sep()


def _s28(ins, sep):
    _h2(ins, "s28")
    ins("body", _t("guide.s28.intro"))
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
        ins("bullet", f"  -  {_t(desc_key)}\n")
    ins("body", _t("guide.s28.optional"))
    ins("note", _t("guide.s28.install_note"))
    ins("body", _t("guide.s28.startup_intro"))
    ins("formula", _t("guide.s28.startup"))
    ins("note", _t("guide.s28.linux_note"))
    sep()


def _s29(ins, sep):
    _h2(ins, "s29")
    ins("body", _t("guide.s29.intro"))
    ins("h3", _t("guide.s29.action_bar.title") + "\n")
    ins("body", _t("guide.s29.action_bar.intro"))
    for btn, desc_key in [
        (f"🔢  {_t('button.count')}",           "guide.s29.action.count"),
        (f"⬇  {_t('button.generate')}",         "guide.s29.action.generate"),
        (f"↺  {_t('button.reset_all')}",        "guide.s29.action.reset_all"),
        (f"🎓  {_t('level.label')}",            "guide.s29.action.level"),
        (_t("label.combinations"),              "guide.s29.action.combinations"),
        (f"🔮  {_t('button.cayley')}",          "guide.s29.action.cayley"),
        (f"🔬  {_t('button.conjugacy')}",       "guide.s29.action.conjugacy"),
        (f"📋  {_t('button.protocol')}",        "guide.s29.action.protocol"),
        (f"🖥️  {_t('button.presentation')}",    "guide.s29.action.presentation"),
        (f"✔  {_t('button.verify')}",           "guide.s29.action.verify"),
        (f"⚙️  {_t('button.settings')}",        "guide.s29.action.settings"),
        (f"⏻  {_t('button.exit')}",             "guide.s29.action.exit"),
        (f"✕  {_t('button.cancel_export')}",    "guide.s29.action.cancel"),
    ]:
        ins("bullet", "  •  ")
        ins("code", btn)
        ins("bullet", f"  —  {_t(desc_key)}\n")
    ins("body", "\n")
    ins("h3", _t("guide.s29.verify.title") + "\n")
    ins("body", _t("guide.s29.verify.intro"))
    ins("bullet", _t("guide.s29.verify.items"))
    ins("note", _t("guide.s29.verify.note"))

    ins("h3", _t("guide.s29.presentation.title") + "\n")
    ins("body", _t("guide.s29.presentation.body"))
    ins("bullet", _t("guide.s29.presentation.keys"))

    ins("h3", _t("guide.s29.mode.title") + "\n")
    ins("body", _t("guide.s29.mode.intro"))
    for n, livello in enumerate(LIVELLI, 1):
        ins("bullet", f"  {n}.  {tr(f'level.name.{livello}')} — "
                      f"{tr(f'level.desc.{livello}')}\n")
    ins("note", _t("guide.s29.mode.note"))
    ins("h3", _t("guide.s29.start_here.title") + "\n")
    ins("body", _t("guide.s29.start_here.body"))
    ins("h3", _t("guide.s29.banner.title") + "\n")
    ins("body", _t("guide.s29.banner.body"))
    ins("h3", _t("guide.s29.tooltips.title") + "\n")
    ins("body", _t("guide.s29.tooltips.body"))
    ins("h3", _t("guide.s29.legend.title") + "\n")
    ins("body", _t("guide.s29.legend.body"))
    ins("h3", _t("guide.s29.empty_states.title") + "\n")
    ins("body", _t("guide.s29.empty_states.body"))
    ins("h3", _t("guide.s29.text_size.title") + "\n")
    ins("body", _t("guide.s29.text_size.body"))
    sep()



def _s31(ins, sep):
    _h2(ins, "s31")
    ins("body", _t("guide.s31.intro"))
    ins("bullet", _t("guide.s31.steps"))
    sep()


def _s32(ins, sep):
    _h2(ins, "s32")
    ins("body", _t("guide.s32.intro"))
    ins("h3", _t("guide.s32.preview_explorer.title") + "\n")
    ins("body", _t("guide.s32.preview_explorer.body"))
    ins("h3", _t("guide.s32.cayley.title") + "\n")
    ins("body", _t("guide.s32.cayley.body"))
    ins("h3", _t("guide.s32.conjugacy.title") + "\n")
    ins("body", _t("guide.s32.conjugacy.body"))
    sep()


def _s33(ins, sep):
    _h2(ins, "s33")
    for n in range(1, 7):
        ins("h3", _t(f"guide.s33.q{n}") + "\n")
        ins("body", _t(f"guide.s33.a{n}"))
    sep()


# ═══════════════════════════ sezioni nuove (I7) ═══════════════════════════

def _i2m(ins, sep):
    _h2(ins, "i2m")
    ins("body", _t("guide.i2m.intro"))
    ins("bullet", _t("guide.i2m.register"))
    ins("formula", "    P′  =  ⌊P / 3⌋  +  9·s\n\n")
    ins("body", _t("guide.i2m.example"))
    ins("body", _t("guide.i2m.epsilon"))
    ins("body", _t("guide.i2m.positions"))
    ins("note", _t("guide.i2m.note"))
    sep()


def _i2t(ins, sep):
    _h2(ins, "i2t")
    ins("body", _t("guide.i2t.intro"))
    ins("bullet", _t("guide.i2t.readings"))
    ins("body", _t("guide.i2t.self_inverse"))
    ins("body", _t("guide.i2t.return"))
    ins("bullet", _t("guide.i2t.examples"))
    ins("warn", _t("guide.i2t.counterexample"))
    ins("h3", _t("guide.i2t.actions.title") + "\n")
    ins("bullet", _t("guide.i2t.actions"))
    sep()


def _i1(ins, sep):
    _h2(ins, "i1")
    ins("body", _t("guide.i1.intro"))
    ins("formula", "    (M₀, M₁, M₂ ; e₁, e₂, e₃)   ↦   (#, m),    m = 4e₁ + 2e₂ + e₃\n\n")
    ins("body", _t("guide.i1.count"))
    ins("h3", _t("guide.i1.relations.title") + "\n")
    ins("bullet", _t("guide.i1.relations"))
    ins("body", _t("guide.i1.fiber"))
    ins("h3", _t("guide.i1.strategies.title") + "\n")
    ins("bullet", _t("guide.i1.costs"))
    ins("bullet", _t("guide.i1.strategies"))
    ins("note", _t("guide.i1.where"))
    ins("warn", _t("guide.i1.counterexample"))
    sep()


def _i3(ins, sep):
    _h2(ins, "i3")
    ins("body", _t("guide.i3.intro"))
    ins("bullet", _t("guide.i3.modes"))
    ins("h3", _t("guide.i3.errors.title") + "\n")
    ins("body", _t("guide.i3.order"))
    ins("bullet", _t("guide.i3.errors"))
    ins("body", _t("guide.i3.compare"))
    ins("h3", _t("guide.i3.recovery.title") + "\n")
    ins("body", _t("guide.i3.recovery"))
    ins("warn", _t("guide.i3.no_recovery"))
    ins("h3", _t("guide.i3.plan.title") + "\n")
    ins("body", _t("guide.i3.plan"))
    ins("bullet", _t("guide.i3.examples"))
    sep()


def _i4(ins, sep):
    _h2(ins, "i4")
    ins("body", _t("guide.i4.intro"))
    ins("formula", "    27  →  9  →  3  →  1\n\n")
    ins("bullet", _t("guide.i4.how"))
    ins("body", _t("guide.i4.known"))
    ins("h3", _t("guide.i4.b12.title") + "\n")
    ins("bullet", _t("guide.i4.b12"))
    ins("body", _t("guide.i4.example"))
    ins("note", _t("guide.i4.note"))
    sep()


def _i5(ins, sep):
    _h2(ins, "i5")
    ins("body", _t("guide.i5.intro"))
    ins("bullet", _t("guide.i5.input"))
    ins("h3", _t("guide.i5.direct.title") + "\n")
    ins("body", _t("guide.i5.direct"))
    ins("h3", _t("guide.i5.sums.title") + "\n")
    ins("body", _t("guide.i5.sums"))
    ins("formula", "    ρ̂ᵢ(t)  =  (Σᵢ,ₜ − Cᵢ) / 3^(2+i)        C₀ = 108,  C₁ = 90,  C₂ = 36\n\n")
    ins("body", _t("guide.i5.directions"))
    ins("warn", _t("guide.i5.integer_not_enough"))
    ins("h3", _t("guide.i5.other.title") + "\n")
    ins("bullet", _t("guide.i5.other"))
    ins("h3", _t("guide.i5.examples.title") + "\n")
    ins("bullet", _t("guide.i5.examples"))
    sep()


def _i6(ins, sep):
    _h2(ins, "i6")
    ins("body", _t("guide.i6.intro"))
    ins("bullet", _t("guide.i6.domains"))
    ins("body", _t("guide.i6.methods"))
    ins("warn", _t("guide.i6.counterexample"))
    ins("h3", _t("guide.i6.sections.title") + "\n")
    ins("bullet", _t("guide.i6.sections"))
    ins("note", _t("guide.i6.note"))
    sep()


def _storia(ins, sep):
    _h2(ins, "storia")
    ins("note", _t("guide.storia.optional"))
    ins("h3", _t("guide.storia.preface.title") + "\n")
    ins("body", _t("guide.storia.preface"))
    ins("h3", _t("guide.storia.before.title") + "\n")
    ins("body", _t("guide.storia.before"))
    ins("bullet", _t("guide.storia.timeline"))
    ins("body", _t("guide.storia.inverse"))
    ins("body", _t("guide.storia.twenty_seven"))
    ins("h3", _t("guide.storia.names.title") + "\n")
    ins("body", _t("guide.storia.names"))
    sep()


def _s30(ins, sep):
    """Glossario: generato dalle stesse voci della scheda «Inizia qui»."""
    _h2(ins, "s30")
    ins("body", _t("guide.s30.intro"))
    ins("h3", _t("guide.s30.math.title") + "\n")
    for chiave in GLOSSARIO_MATEMATICO:
        ins("bullet", f"  •  {tr(f'glossary.term.{chiave}')} — "
                      f"{tr(f'glossary.short.{chiave}')}\n")
    ins("h3", _t("guide.s30.narrative.title") + "\n")
    ins("note", _t("guide.s30.narrative.note"))
    for chiave in GLOSSARIO_NARRATIVO:
        ins("bullet", f"  •  {tr(f'glossary.term.{chiave}')} — "
                      f"{tr(f'glossary.long.{chiave}')}\n")
    ins("body", "\n")
    sep()


_SEZIONI_FN = {
    **{f"s{n:02d}": globals()[f"_s{n:02d}"] for n in range(1, 34)},
    "i1": _i1, "i2m": _i2m, "i2t": _i2t, "i3": _i3, "i4": _i4,
    "i5": _i5, "i6": _i6, "storia": _storia,
}


def build_guide_content(ins, sep):
    """Popola il tab Guida usando i callback `ins` e `sep` forniti da app.py."""
    ins("h1", tr("guide.title") + "\n")
    sep()

    ins("h3", tr("guide.toc") + "\n")
    for parte, sezioni in PARTI:
        ins("tocpart", f"  {tr(parte)}\n")
        for sid in sezioni:
            ins("toc", f"    {_NUMERO[sid]:>2}.  {_t(f'guide.{sid}.title')}\n")
    sep()

    for parte, sezioni in PARTI:
        ins("part", f"{tr(parte)}\n")
        for sid in sezioni:
            _SEZIONI_FN[sid](ins, sep)

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
