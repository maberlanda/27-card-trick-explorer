"""
Contenuto della Guida / How-To del Gioco delle 27 carte.

Separato da app.py per mantenere snella la finestra principale e per poter
modificare la documentazione senza toccare la logica della GUI.

Tutto il rendering avviene tramite i due callback passati da app.py:
    ins(tag, text) -> inserisce `text` nel widget Text con lo stile `tag`
    sep()          -> inserisce una riga separatrice
Gli stili (tag) sono definiti in app.py._build_guide_tab.
"""


def build_guide_content(ins, sep):
    """Popola il tab Guida usando i callback `ins` e `sep` forniti da app.py."""
    # ═══════════════════════════════════════════════════════════════════════
    ins("h1", "Gioco delle 27 carte  —  Guida completa & How-To\n")
    sep()

    ins("h3", "Indice\n")
    toc = [
        ("1",  "Il gioco — come funziona fisicamente"),
        ("2",  "Coordinate ternarie e codifica delle posizioni"),
        ("3",  "La permutazione MSC — messa in colonne"),
        ("4",  "Le permutazioni P — raccolta delle carte"),
        ("5",  "Le permutazioni J — orientazione del mazzo"),
        ("6",  "Il modello matematico — Stageᵢ = Pᵢ ∘ MSC ∘ Jᵢ"),
        ("7",  "Relazione fondamentale di commutazione con MSC"),
        ("8",  "Forma ridotta — Stageᵢ = Aᵢ ∘ MSC  (indici incrociati)"),
        ("9",  "Trasformazione globale T e struttura del gruppo"),
        ("10", "Il Gioco Reale — le 1 728 sequenze canoniche"),
        ("11", "Tab Tavola 216 — la tavola del libro"),
        ("12", "I filtri — Tab Stadio 0, 1, 2"),
        ("13", "Preset rapidi"),
        ("14", "Tab Anteprima — calcolo di una singola combinazione"),
        ("15", "Tab Analisi Molteplicità — raggruppamento, conteggio, dettaglio e export"),
        ("16", "Tab Explorer — analisi algebrica, decomposizioni e protocollo"),
        ("17", "Sotto-tab Matrice — visualizzazione grafica di T e T⁻¹"),
        ("18", "Sotto-tab Mescolamento — simulazione visiva passo per passo"),
        ("19", "Tab Simulatore — pratica guidata del trucco"),
        ("20", "Tab Cicli — struttura ciclica della permutazione"),
        ("21", "Tab Distribuzione — decomposizioni per ogni T raggiungibile"),
        ("22", "Finestra Classi di Coniugio e Centro"),
        ("23", "Finestra Tavola di Cayley"),
        ("24", "Finestra Protocollo — istruzioni per il mazziere"),
        ("25", "Flusso di lavoro consigliato"),
        ("26", "Formato dei file esportati"),
        ("27", "Prestazioni e limiti pratici"),
        ("28", "Installazione e dipendenze"),
        ("29", "Interfaccia guidata — modalità, aiuti e accessibilità"),
        ("30", "Glossario dei termini"),
        ("31", "Esempio passo-passo — dal Gioco Reale all'analisi"),
        ("32", "Export LaTeX / SVG — Anteprima, Explorer, Cayley, Coniugio"),
        ("33", "Domande frequenti (FAQ)"),
    ]
    for n, titolo in toc:
        ins("toc", f"    {n:>2}.  {titolo}\n")
    sep()

    # ── 1 ──────────────────────────────────────────────────────────────────
    ins("h2", "1.  Il gioco — come funziona fisicamente\n")
    ins("body",
        "Il gioco delle 27 carte è un classico trucco di magia matematica. "
        "Un mazziere dispone 27 carte sul tavolo in 3 colonne da 9 carte ciascuna, "
        "chiede allo spettatore di indicare mentalmente una carta, e con tre "
        "mescolamenti la porta esattamente in una posizione prestabilita (di solito "
        "la posizione 14, il centro del mazzo).\n\n"
        "La procedura fisica per ogni stadio è:\n\n")
    ins("bullet", "  1.  Il mazziere dispone le 27 carte in 3 colonne da 9 (MSC = Messa in Colonne).\n")
    ins("bullet", "  2.  Lo spettatore indica la colonna in cui si trova la propria carta.\n")
    ins("bullet", "  3.  Il mazziere raccoglie le tre colonne in un certo ordine (permutazione P).\n")
    ins("bullet", "  4.  Facoltativamente, il mazziere capovolge il mazzo prima dello stadio successivo (orientazione J).\n")
    ins("body",
        "\nDopo tre ripetizioni di questo ciclo la posizione finale della carta "
        "è determinata in modo esatto dalle scelte (P e J) fatte dal mazziere "
        "in ogni stadio, indipendentemente da quale carta ha scelto lo spettatore "
        "(purché sia indicata la colonna giusta). Il trucco è interamente algebrico: "
        "le tre scelte di raccolta controllano le tre cifre ternarie della posizione finale.\n")
    sep()

    # ── 2 ──────────────────────────────────────────────────────────────────
    ins("h2", "2.  Coordinate ternarie e codifica delle posizioni\n")
    ins("body",
        "Le 27 posizioni del mazzo sono numerate 0–26 e codificate in base 3:\n\n")
    ins("formula",
        "    posizione  =  9·i₂  +  3·i₁  +  i₀\n"
        "    con  i₂, i₁, i₀ ∈ {0, 1, 2}\n\n")
    ins("body",
        "La terna (i₂, i₁, i₀) sono le «coordinate» della carta nello "
        "spazio ternario {0,1,2}³. Ogni coordinata è controllata da uno stadio:\n\n")
    ins("bullet", "  •  i₀  (cifra delle unità, peso 1)   =  coordinata controllata allo Stadio 0\n")
    ins("bullet", "  •  i₁  (cifra dei 3, peso 3)          =  coordinata controllata allo Stadio 1\n")
    ins("bullet", "  •  i₂  (cifra dei 9, peso 9)          =  coordinata controllata allo Stadio 2\n")
    ins("body",
        "\nLa convenzione nel codice è P2 ⊗ P1 ⊗ P0 (i₂ come fattore più significativo), "
        "coerente con il prodotto di Kronecker. I tre stadi agiscono separatamente "
        "sulle tre cifre: questa struttura tensoriale è la chiave matematica del gioco.\n")
    sep()

    # ── 3 ──────────────────────────────────────────────────────────────────
    ins("h2", "3.  La permutazione MSC — messa in colonne\n")
    ins("body",
        "MSC (Messa in Colonne) descrive come le 27 carte vengono distribuite "
        "in 3 colonne da 9 e poi rilette per righe. Sulle coordinate ternarie "
        "realizza una rotazione ciclica:\n\n")
    ins("formula",
        "    MSC:  (i₂, i₁, i₀)  →  (i₀, i₂, i₁)\n\n")
    ins("body", "Proprietà fondamentali di MSC:\n\n")
    ins("bullet", "  •  MSC è fissa — identica per tutti gli stadi e tutte le combinazioni.\n")
    ins("bullet", "  •  Ordine 3: MSC³ = I₂₇ (applicata tre volte = identità).\n")
    ins("bullet", "  •  Fisicamente: disporre il mazzo in colonne (per righe) e raccoglierlo per colonne.\n")
    ins("bullet", "  •  La rotazione degli indici è σ = (0 → 2 → 1 → 0) su {0,1,2}, cioè un 3-ciclo.\n")
    sep()

    # ── 4 ──────────────────────────────────────────────────────────────────
    ins("h2", "4.  Le permutazioni P — raccolta delle carte\n")
    ins("body",
        "Pᵢ descrive l'ordine in cui il mazziere raccoglie le 3 colonne. "
        "Le colonne sono S (Sinistra=0), C (Centro=1), D (Destra=2). "
        "Ci sono 3! = 6 ordini di raccolta. "
        "Ogni P è un prodotto di Kronecker P2ᵢ ⊗ P1ᵢ ⊗ P0ᵢ, "
        "dove ciascun fattore è una delle 6 permutazioni su {0,1,2}:\n\n")
    rows_P = [
        ("SCD_U", "[0,1,2]", "Identità — S→S, C→C, D→D  (nessun riordino)",    "ord. 1"),
        ("SDC_U", "[0,2,1]", "Scambia C↔D  (involuzione)",                      "ord. 2"),
        ("CSD_U", "[1,0,2]", "Scambia S↔C  (involuzione)",                      "ord. 2"),
        ("CDS_U", "[1,2,0]", "Rotazione ciclica  S→C→D→S",                      "= DSC⁻¹"),
        ("DSC_U", "[2,0,1]", "Rotazione inversa  S→D→C→S",                      "= CDS⁻¹"),
        ("DCS_U", "[2,1,0]", "Scambia S↔D  (involuzione)",                      "ord. 2"),
    ]
    for name, perm, desc, alg in rows_P:
        ins("bullet", "  •  ")
        ins("code", f"{name}  {perm}")
        ins("bullet", f"  —  {desc}   ")
        ins("note", f"[{alg}]\n")
    ins("body",
        "\nPᵢ = P2ᵢ ⊗ P1ᵢ ⊗ P0ᵢ: P0, P1, P2 scelti indipendentemente tra le 6 "
        "permutazioni → 6³ = 216 combinazioni per stadio.\n\n")
    ins("note",
        "Nel gioco reale tradizionale P0 = P1 = SCD_U (identità) e solo P2 varia: "
        "rappresenta fisicamente l'ordine in cui vengono raccolte le colonne.\n")
    sep()

    # ── 5 ──────────────────────────────────────────────────────────────────
    ins("h2", "5.  Le permutazioni J — orientazione del mazzo\n")
    ins("body",
        "Jᵢ descrive se il mazziere capovolge il mazzo tra uno stadio e il successivo. "
        "Sono disponibili solo 2 permutazioni:\n\n")
    rows_J = [
        ("I_3", "[0,1,2]", "Identità — nessun capovolgimento",          "ord. 1"),
        ("R_U", "[2,1,0]", "Inversione — S↔D, C fisso (involuzione)",   "ord. 2"),
    ]
    for name, perm, desc, alg in rows_J:
        ins("bullet", "  •  ")
        ins("code", f"{name}  {perm}")
        ins("bullet", f"  —  {desc}   ")
        ins("note", f"[{alg}]\n")
    ins("body",
        "\nAnche Jᵢ = J2ᵢ ⊗ J1ᵢ ⊗ J0ᵢ è un prodotto di Kronecker, "
        "con J0, J1, J2 ∈ {I_3, R_U}. Senza vincoli: 2³ = 8 combinazioni J per stadio. "
        "Il vincolo «J uniformi» forza J0 = J1 = J2:\n\n")
    ins("hilight",
        "    J uniformi:  J0 = J1 = J2\n"
        "    → triple ammissibili: (I_3, I_3, I_3)  e  (R_U, R_U, R_U)\n"
        "    → 2 combinazioni per stadio invece di 8\n\n")
    ins("body",
        "Nel gioco reale il mazzo viene capovolto uniformemente (J uniforme), "
        "quindi questo vincolo modella correttamente il gioco fisico.\n")
    sep()

    # ── 6 ──────────────────────────────────────────────────────────────────
    ins("h3", "  Nomi doppi: I_3/SCD_U e R_U/DCS_U\n")
    ins("body",
        "Due permutazioni su {0,1,2} hanno due nomi ciascuna, perche' le si "
        "puo' guardare come raccolta (nome P) o come orientazione (nome J):\n\n")
    ins("formula",
        "    [0,1,2]  =  SCD_U (raccolta identica)  =  I_3 (nessuna inversione)\n"
        "    [2,1,0]  =  DCS_U (raccolta S\u2194D)       =  R_U (inversione completa)\n\n")
    ins("body",
        "Nelle formule A\u1d62 il programma stampa l'identita' come I_3 e "
        "l'inversione come DCS_U. Se imposti J = R_U e ritrovi DCS_U "
        "nell'etichetta non e' un errore: e' la stessa permutazione. "
        "La convenzione non e' uniforme di proposito \u2014 il calcolo vede solo "
        "il risultato, non da dove viene, e una raccolta genuinamente DCS_U e' "
        "indistinguibile da un'inversione. Uniformare avrebbe un costo in "
        "entrambe le direzioni: o l'identita' smetterebbe di chiamarsi I_3, o "
        "una raccolta verrebbe mostrata come R_U.\n\n")

    ins("h2", "6.  Il modello matematico  —  Stageᵢ = Pᵢ ∘ MSC ∘ Jᵢ\n")
    ins("body",
        "Ogni stadio i (0, 1, 2) applica in sequenza, da destra a sinistra:\n\n")
    ins("formula",
        "    Stageᵢ  =  Pᵢ  ∘  MSC  ∘  Jᵢ\n\n")
    ins("bullet", "  1.  Jᵢ   — eventuale capovolgimento del mazzo\n")
    ins("bullet", "  2.  MSC  — distribuzione in colonne e raccolta\n")
    ins("bullet", "  3.  Pᵢ   — riordino nell'ordine scelto dal mazziere\n\n")
    ins("body", "La trasformazione globale dopo i tre stadi è:\n\n")
    ins("formula",
        "    T  =  Stage₂ ∘ Stage₁ ∘ Stage₀\n"
        "       =  P₂ ∘ MSC ∘ J₂ ∘ P₁ ∘ MSC ∘ J₁ ∘ P₀ ∘ MSC ∘ J₀\n\n")
    ins("body",
        "Nel codice ∘ corrisponde alla moltiplicazione di matrici 27×27; "
        "A ∘ B significa «applica prima B, poi A».\n")
    sep()

    # ── 7 ──────────────────────────────────────────────────────────────────
    ins("h2", "7.  Relazione fondamentale di commutazione con MSC\n")
    ins("body",
        "Per qualsiasi operatore decomponibile A = A₂ ⊗ A₁ ⊗ A₀ vale:\n\n")
    ins("formula",
        "    MSC ∘ (A₂ ⊗ A₁ ⊗ A₀)  =  (A₀ ⊗ A₂ ⊗ A₁) ∘ MSC\n\n")
    ins("body",
        "MSC «ruota ciclicamente» i fattori del prodotto di Kronecker: "
        "(A₂, A₁, A₀) → (A₀, A₂, A₁). "
        "Questo è la diretta conseguenza della rotazione σ degli indici. "
        "Attenzione: la rotazione corretta è (2,1,0) → (0,2,1), non (2,1,0) → (0,1,2):\n\n")
    ins("warn",
        "    Formula errata (non usare):\n"
        "    MSC ∘ (A₂ ⊗ A₁ ⊗ A₀)  ≠  (A₀ ⊗ A₁ ⊗ A₂) ∘ MSC    ← SBAGLIATA\n\n")
    sep()

    # ── 8 ──────────────────────────────────────────────────────────────────
    ins("h2", "8.  Forma ridotta  —  Stageᵢ = Aᵢ ∘ MSC  (indici incrociati)\n")
    ins("body",
        "Applicando la relazione di commutazione alla parte Jᵢ, ogni stadio diventa:\n\n")
    ins("formula",
        "    Stageᵢ  =  [(P2ᵢ∘J0ᵢ) ⊗ (P1ᵢ∘J2ᵢ) ⊗ (P0ᵢ∘J1ᵢ)]  ∘  MSC\n"
        "             =  Aᵢ  ∘  MSC\n\n")
    ins("body", "I componenti di Aᵢ (attenzione agli indici incrociati!):\n\n")
    ins("formula",
        "    Aᵢ  =  (P2ᵢ ∘ J0ᵢ)  ⊗  (P1ᵢ ∘ J2ᵢ)  ⊗  (P0ᵢ ∘ J1ᵢ)\n\n")
    ins("warn",
        "    Indici incrociati — leggere con attenzione:\n"
        "    Il fattore di grado 2 (P2) si compone con J0  [J0 → posizione 2]\n"
        "    Il fattore di grado 1 (P1) si compone con J2  [J2 → posizione 1]\n"
        "    Il fattore di grado 0 (P0) si compone con J1  [J1 → posizione 0]\n\n"
        "    cioè, in forma chiusa:  f_k = P_k ∘ J_(k+1 mod 3)\n\n")
    ins("body",
        "Questo incrocio è la conseguenza diretta della rotazione ciclica di MSC "
        "ed è gestito automaticamente dalla funzione compute_Ai_symbolic(). "
        "La composizione globale T si semplifica in:\n\n")
    ins("formula",
        "    T  =  A₂ ∘ MSC ∘ A₁ ∘ MSC ∘ A₀ ∘ MSC\n\n")
    ins("body",
        "Questa è la «T simbolica» che appare nel CSV e nell'Explorer.\n")
    sep()

    # ── 9 ──────────────────────────────────────────────────────────────────
    ins("h2", "9.  Trasformazione globale T e struttura del gruppo\n")
    ins("body",
        "L'insieme di tutte le T a tre stadi al variare dei parametri è il gruppo del gioco G = S₃³ "
        "di permutazioni su 27 elementi. Proprietà principali:\n\n")
    ins("bullet", "  •  Ordine:  |G| = 216\n")
    ins("bullet", "  •  Struttura:  G = S₃³  (tre fattori locali indipendenti)\n")
    ins("bullet", "  •  G è non abeliano: l'ordine di composizione conta.\n")
    ins("bullet", "  •  Azione transitiva su tutte le 27 posizioni.\n")
    ins("bullet", "  •  27 classi di coniugio (calcolabili dal tab Distribuzione).\n")
    ins("body",
        "Il gruppo esteso G_ext = ⟨S₃³, MSC⟩ si ottiene aggiungendo MSC a G. "
        "MSC non appartiene a G: il gruppo esteso va distinto dal gruppo del gioco.\n")
    ins("body",
        "\nPermutazioni diverse prodotte da sequenze di parametri diverse "
        "possono coincidere (molteplicità > 1): il tab Analisi quantifica questo fenomeno.\n")
    sep()

    # ── 10 ─────────────────────────────────────────────────────────────────
    ins("h2", "10.  Il Gioco Reale — le 1 728 sequenze canoniche\n")
    ins("hilight",
        "    Preset:  🎴 Gioco Reale  →  P0 = P1 = SCD_U,  P2 libero,  J uniformi\n\n")
    ins("body",
        "Nel gioco reale tradizionale i parametri liberi per ogni stadio sono:\n\n")
    ins("bullet", "  •  P2  libero tra 6 valori: è la RACCOLTA delle 3 colonne, che agisce "
                  "al livello dei blocchi (fattore più significativo del prodotto di Kronecker)\n")
    ins("bullet", "  •  P0 = P1 = SCD_U  (identità: il mazziere non riordina dentro la colonna)\n")
    ins("bullet", "  •  J uniformi: J0 = J1 = J2  (mazzo capovolto uniformemente, 2 scelte)\n\n")
    ins("body",
        "Attenzione alla terminologia del libro: la sigla della raccolta è il "
        "MESCOLAMENTO (lettura funzionale: la cifra N va nella N-esima lettera, "
        "riga del tabellone); il gesto fisico con cui si impilano i mazzetti è "
        "l'IMPILAMENTO, che è la permutazione inversa. Le sigle CDS e DSC si "
        "scambiano fra i due ruoli, le altre quattro coincidono.\n\n")
    ins("body", "Conteggio:\n\n")
    ins("formula",
        "    Per stadio:  6 (P2) × 1 (P0 fisso) × 1 (P1 fisso) × 2 (J unif.) = 12\n"
        "    Tre stadi:  12³ = 1 728  sequenze distinte\n\n")
    ins("ok",
        "    Come attivare:  barra inferiore → pulsante  🎴 Gioco Reale (1 728 combinazioni)\n\n")
    sep()

    # ── 11 ─────────────────────────────────────────────────────────────────
    ins("h2", "11.  Tab Tavola 216 — la tavola del libro\n")
    ins("body",
        "È la messa in tabella delle 216 sequenze di tre mescolamenti descritte "
        "nella sezione 10, nello stesso ordine e con la stessa numerazione del "
        "libro (# = i₁ + 6·i₂ + 36·i₃, con i mescolamenti in ordine cronologico "
        "SCD, SDC, CSD, DSC, CDS, DCS). Per ogni riga:\n\n")
    ins("bullet", "  •  i tre MESCOLAMENTI (sigla funzionale) e i tre IMPILAMENTI "
        "(il gesto fisico, cioè la sigla inversa: CDS↔DSC si scambiano, le altre "
        "quattro coincidono con la propria inversa);\n")
    ins("bullet", "  •  le posizioni finali dei tre Assi;\n")
    ins("bullet", "  •  il periodo (dopo quante ripetizioni il mazzo torna in ordine);\n")
    ins("bullet", "  •  i punti fissi e il tipo ciclico.\n\n")
    ins("h3", "  Ricostruzione dagli Assi\n")
    ins("body",
        "La tavola si può percorrere anche all'indietro: date le posizioni finali "
        "dei tre Assi, il programma risale all'unica riga che le produce. È la "
        "verifica «ricostruzione_assi» del selftest, eseguita su tutte e 216 le "
        "righe.\n\n")
    ins("note",
        "Le righe #100 e #82 sono le due ancore usate dal selftest per "
        "controllare l'allineamento col libro.\n")
    sep()

    # ── 12 ─────────────────────────────────────────────────────────────────
    ins("h2", "12.  I filtri — Tab Stadio 0, 1, 2\n")
    ins("body",
        "Ogni tab Stadio ha due pannelli affiancati per configurare i parametri "
        "di quel singolo stadio.\n\n")
    ins("h3", "  Pannello blu — Permutazioni P\n")
    ins("body",
        "Controlla P0, P1, P2 per lo stadio. Per ogni riga:\n\n")
    ins("bullet",
        "  •  Dropdown con valore preciso (es. SCD_U)  →  valore fisso per tutte "
        "le combinazioni. Il dropdown ha priorità sulle checkbox.\n")
    ins("bullet",
        "  •  Dropdown impostato su «*»  →  valore libero. Le checkbox a destra "
        "determinano quali valori sono inclusi. Tutte spuntate = tutti i 6 valori. "
        "Sottoinsieme spuntato = solo quei valori. Nessuna = fallback al primo valore.\n\n")
    ins("h3", "  Pannello arancione — Permutazioni J\n")
    ins("body",
        "Stessa struttura del pannello P, con il checkbox prominente "
        "«J UNIFORMI (J0=J1=J2)». Quando attivo forza J1 = J2 = J0, "
        "riducendo le combinazioni J da 2³=8 a 2 per stadio.\n\n")
    ins("h3", "  Contatore live\n")
    ins("body",
        "Il numero di combinazioni compatibili con i filtri correnti è aggiornato "
        "automaticamente non appena si modifica un filtro. "
        "Verificarlo sempre prima di avviare la generazione.\n")
    sep()

    # ── 12 ─────────────────────────────────────────────────────────────────
    ins("h2", "13.  Preset rapidi\n")
    ins("h3", "  🎴 Gioco Reale (1 728 combinazioni)\n")
    ins("body",
        "Imposta su tutti e tre gli stadi: P2 libero, P0 = P1 = SCD_U, "
        "J uniformi con J0 libero. Risultato: 12³ = 1 728 combinazioni.\n\n")
    ins("h3", "  ⚡ J Uniformi per tutti gli stadi\n")
    ins("body",
        "Attiva il vincolo J uniformi su tutti e tre gli stadi senza toccare "
        "i filtri P.\n\n")
    ins("h3", "  ↺ Reset filtri\n")
    ins("body",
        "Azzera completamente tutti i filtri: dropdown a *, checkbox tutte attive, "
        "J uniformi disabilitato. Senza filtri il totale è ~5 miliardi — "
        "non generare CSV o PDF in questo stato!\n")
    sep()

    # ── 13 ─────────────────────────────────────────────────────────────────
    ins("h2", "14.  Tab Anteprima — calcolo di una singola combinazione\n")
    ins("body",
        "Permette di calcolare e visualizzare il risultato di una combinazione "
        "scelta con esattezza, senza generare CSV o PDF. "
        "Per ogni stadio si scelgono P0, P1, P2, J0, J1, J2 tramite dropdown. "
        "Premendo «▶ Calcola» il pannello risultati mostra:\n\n")
    ins("bullet", "  •  Stageᵢ simbolico:  (P2×P1×P0) ∘ MSC ∘ (J2×J1×J0)  per ogni stadio\n")
    ins("bullet", "  •  Forma ridotta Aᵢ:  (P2∘J0) ⊗ (P1∘J2) ⊗ (P0∘J1)\n")
    ins("bullet", "  •  T simbolica completa:  T = A₂ ∘ MSC ∘ A₁ ∘ MSC ∘ A₀ ∘ MSC\n")
    ins("bullet", "  •  T permutazione numerica, in 3 blocchi da 9 elementi\n")
    sep()

    # ── 14 ─────────────────────────────────────────────────────────────────
    ins("h2", "15.  Tab Analisi Molteplicità — raggruppamento, conteggio, dettaglio e export\n")
    ins("body",
        "Risponde alla domanda: quante sequenze Stage distinte producono "
        "la stessa permutazione numerica T?\n\n"
        "Funzionamento: i filtri dei tab Stadio definiscono il dominio; "
        "tutte le combinazioni vengono generate in memoria, raggruppate "
        "per T_permutazione e conteggiate per molteplicità. "
        "Non è richiesto nessun file esterno: i dati vengono calcolati internamente.\n\n")
    ins("h3", "  Come usare\n")
    ins("bullet", "  1.  Imposta i filtri nei tab Stadio (o usa un preset).\n")
    ins("bullet", "  2.  Premi «🔄 Genera & Analizza».\n")
    ins("bullet", "  3.  L'operazione avviene in background; la barra di stato indica l'avanzamento.\n")
    ins("bullet", "  4.  La tabella mostra una riga per ogni T distinta:\n")
    ins("bullet2", "  ◦  Molt.  — numero di sequenze Stage distinte (molteplicità)\n")
    ins("bullet2", "  ◦  T_permutazione  — lista numerica [0..26]\n")
    ins("bullet2", "  ◦  Prima T_simbolica distinta  — la prima in ordine lessicografico\n")
    ins("bullet", "  5.  Un singolo clic seleziona la riga e apre il pannello di dettaglio.\n")
    ins("bullet", "  6.  Doppio clic o «🔬 Apri nel Explorer» invia la prima T_simbolica all'Explorer.\n\n")

    ins("h3", "  Pannello di dettaglio — P e J per ogni sequenza Stage\n")
    ins("body",
        "Il pannello inferiore mostra tutte le sequenze Stage distinte della riga selezionata, "
        "con la scomposizione P e J per ciascuno dei tre stadi. "
        "Ogni riga del pannello mostra:\n\n")
    ins("formula",
        "    #   Stage0 — P                J               Stage1 — P                J               Stage2 — P                J\n"
        "    1   (SCD_U x SCD_U x CDS_U)   (I_3 x I_3 x I_3)    ...                               ...\n"
        "        → T = (CSD_U x ...) o MSC o ...  (apri Explorer)  ← link cliccabile\n\n")
    ins("body",
        "Ogni riga del dettaglio termina con un link «→ T_simbolica  (apri Explorer)» "
        "(testo blu sottolineato): un clic la carica direttamente nell'Explorer, "
        "permettendo di scegliere qualsiasi doppione tra quelli con la stessa T_permutazione.\n\n")
    ins("note",
        "Il pannello mostra «← seleziona una riga» prima di qualsiasi selezione. "
        "Se i dati grezzi non sono disponibili (analisi da CSV), i link all'Explorer "
        "potrebbero non essere attivi.\n")

    ins("h3", "  Esportazione risultati (menu «Esporta…»)\n")
    ins("body",
        "Cinque voci divise in due gruppi:\n\n")
    ins("h3", "  Analisi — riepilogo molteplicità\n")
    ins("bullet", "  •  CSV (;)  —  tre colonne: T_permutazione ; T_simboliche_distinte ; n_sim_distinte\n")
    ins("bullet", "  •  Excel    —  due fogli: «Perm→Simboliche» e «Analisi molteplicità»\n")
    ins("bullet", "  •  HTML     —  tabella formattata con sfondo colorato, una riga per T, "
        "una <div> per ogni sequenza Stage → leggibilità ottimale\n\n")
    ins("h3", "  Dati grezzi — una riga per ogni combinazione\n")
    ins("bullet", "  •  CSV (;)  —  9 colonne: #; Stage0; Stage1; Stage2; A0; A1; A2; T_simbolica; T_permutazione\n")
    ins("bullet", "  •  Excel    —  due fogli: «Dati grezzi» (combinazioni) e «Analisi molteplicità» (riepilogo)\n\n")
    ins("note", "Excel richiede openpyxl  (pip install openpyxl).\n")
    sep()

    # ── 15 ─────────────────────────────────────────────────────────────────
    ins("h2", "16.  Tab Explorer — analisi algebrica, decomposizioni e protocollo\n")
    ins("body",
        "Analizzatore algebrico simbolico. Accetta una T_simbolica e la scompone "
        "in sei sotto-tab. Ha anche i pulsanti per le decomposizioni di T⁻¹ "
        "e per generare il protocollo per il mazziere.\n\n")
    ins("h3", "  Come caricare un'espressione\n")
    ins("bullet", "  •  Doppio clic su riga Analisi  →  carica la prima T_simbolica.\n")
    ins("bullet", "  •  Clic su T_simbolica sottolineata nel pannello dettaglio  →  carica quella specifica.\n")
    ins("bullet", "  •  Digitazione manuale + Ctrl+Invio o «▶ Calcola».\n")
    ins("formula",
        "    Sintassi:  (CDS_U x SCD_U x SCD_U) o MSC o (DCS_U x SCD_U x SCD_U) o MSC o ...\n\n")
    ins("h3", "  I sette sotto-tab\n")
    ins("bullet", "  🎴 Mescolamento     —  simulazione visiva passo per passo (vedi sezione 18).\n")
    ins("bullet", "  🔢 Numerico         —  permutazione T e T⁻¹, periodo, firma, passi di normalizzazione.\n")
    ins("bullet", "  ✏️ Traccia riscrittura  —  riscrittura passo per passo dell'espressione.\n")
    ins("bullet", "  🧮 Forma algebrica  —  forma normale: tipo, esponente MSC, fattori Kronecker.\n")
    ins("bullet", "  📋 Passi parziali   —  permutazione parziale e firma per ogni sotto-espressione.\n")
    ins("bullet", "  ⧆ Forma canonica   —  forma K∘MSCᵏ con K = P₀⊗P₁⊗P₂, k∈{0,1,2}; fattori GEN3; verifica. "
        "Per T non decomponibili in Kronecker puri viene tentata la decomposizione numerica.\n")
    ins("bullet", "  📐 Matrice          —  griglie 27×27 di T e T⁻¹ (vedi sezione 17).\n\n")

    ins("h3", "  Pulsante 🔍  Decomposizioni T⁻¹\n")
    ins("body",
        "Compare dopo ogni calcolo riuscito. Trova tutte le triple (A₀,A₁,A₂) "
        "con Aᵢ ∈ GEN3⊗GEN3⊗GEN3 tali che  A₂∘MSC∘A₁∘MSC∘A₀∘MSC = T⁻¹.\n\n"
        "Algoritmo: fissa (A₀,A₁), calcola A₂ deterministicamente e verifica se ∈ GEN3⊗GEN3⊗GEN3. "
        "216² = 46 656 iterazioni numpy, < 0.2 s con cache.\n\n"
        "Risultato strutturale: per ogni T ∈ G = S₃³ esistono "
        "46 656 decomposizioni, pari a 46 656 × 8³ = 23 887 872 combinazioni (P,J) totali "
        "(8 preimmagini Stage per ogni Aᵢ, quindi 8³ per ogni terna). "
        "La promessa non si estende a tutto G_ext: per MSC si ottengono 0 decomposizioni a tre stadi.\n\n")
    ins("bullet", "  •  La finestra elenca le decomposizioni; Esporta… salva in TXT, CSV(;) o HTML.\n")
    ins("bullet", "  •  Una barra di avanzamento mostra la progressione (X/216) e il contatore live.\n")
    ins("bullet", "  •  Clic su una riga sottolineata  →  la formula viene inviata all'Explorer "
        "(il campo lampeggia in giallo pastello per segnalare la modifica).\n")
    ins("note", "Il pulsante è disabilitato fino al primo calcolo con T⁻¹ disponibile.\n\n")

    ins("h3", "  Pulsante 📋  Protocollo\n")
    ins("body",
        "Genera una pagina HTML con le istruzioni operative per il mazziere "
        "(vedi sezione 24).\n")
    sep()

    # ── 16 ─────────────────────────────────────────────────────────────────
    ins("h2", "17.  Sotto-tab Matrice — visualizzazione grafica di T e T⁻¹\n")
    ins("body",
        "Il sotto-tab Matrice (sesto sotto-tab dell'Explorer) mostra le matrici di "
        "permutazione di T e T⁻¹ come griglie a punti colorati, nella stessa "
        "rappresentazione visiva del PDF.\n\n")
    ins("h3", "  Pannello sinistro — T\n")
    ins("body",
        "Matrice 27×27 di T: M[i][j] = 1 se T(j) = i (la carta alla posizione j "
        "va alla posizione i). Ogni riga e colonna hanno esattamente un punto verde.\n\n"
        "Linee di separazione ogni 3 celle (grigie, blocchi Kronecker) e ogni 9 celle "
        "(nere, struttura ternaria). Sotto la griglia: fattori Kronecker P₀,P₁,P₂ "
        "come piccole griglie 3×3 quando la forma canonica è disponibile.\n\n")
    ins("h3", "  Pannello destro — T⁻¹\n")
    ins("body",
        "Matrice 27×27 di T⁻¹ (trasposta di T). Un punto verde in (i,j) di T⁻¹ "
        "significa che la carta alla posizione i viene riportata alla posizione j. "
        "Anche i fattori Kronecker di T⁻¹ sono mostrati:\n\n")
    ins("formula",
        "    Se  T = K ∘ MSCᵏ  con  K = P₀ ⊗ P₁ ⊗ P₂\n"
        "    allora  T⁻¹ = rot₂ₖ(K⁻¹) ∘ MSC^{(3−k) mod 3}\n"
        "    con  K⁻¹ = P₀⁻¹ ⊗ P₁⁻¹ ⊗ P₂⁻¹,  Pᵢ⁻¹ ∈ GEN3\n\n")
    ins("note",
        "Il tab Matrice è disponibile solo dopo aver calcolato un'espressione. "
        "Prima del calcolo le griglie sono vuote.\n")
    sep()

    # ── 17 ─────────────────────────────────────────────────────────────────
    ins("h2", "18.  Sotto-tab Mescolamento — simulazione visiva passo per passo\n")
    ins("body",
        "Permette di osservare, passo per passo, come le 27 carte vengono "
        "fisicamente riordinate dalle operazioni MSC e Kron di una formula algebrica. "
        "Il mazzo parte ordinato (C00…C26); ogni passo mostra lo stato corrente "
        "come griglia 9×3 e come vettore lineare.\n\n")
    ins("h3", "  Come caricare una formula\n")
    ins("bullet", "  1.  Inserisci (o calcola) una formula nel tab Explorer.\n")
    ins("bullet", "  2.  Apri il sotto-tab 🎴 Mescolamento.\n")
    ins("bullet", "  3.  Premi «📥 Carica da Explorer»: la formula viene validata e i passi vengono costruiti.\n")
    ins("body",
        "\nSintassi accettata: sequenza di blocchi Kron e MSC separati da «o»:\n\n")
    ins("formula",
        "    (P2 x P1 x P0) o MSC o (P2 x P1 x P0) o MSC o ...\n\n")
    ins("body",
        "Dalla v2.8.3 sono accettati anche i nomi dei fattori J (R_U, I_3 — "
        "alias di DCS_U e SCD_U), le parentesi quadre e il prefisso «T = »: "
        "si può quindi incollare un turno di gioco completo cosi' come appare "
        "nel dettaglio dell'Analisi:\n\n")
    ins("formula",
        "    (P2 x P1 x P0) o MSC o (J2 x J1 x J0)        con J ∈ {I_3, R_U}\n"
        "    T = [(...) o MSC o (...)] o [(...) o MSC o (...)] o [...]\n\n")
    ins("note",
        "Passi in modalità normale: 1 (iniziale) + 2×n (dove n = blocchi Kron). "
        "In modalità carta-per-carta: fino a ~24 sub-passi per MSC e ~27 per Kron.\n")

    ins("h3", "  La griglia 3×9 e il vettore\n")
    ins("body",
        "La griglia mostra il mazzo come 3 colonne da 9 carte (layout fisico del tavolo). "
        "Posizione (riga r, colonna c) = indice c·9+r nel vettore lineare.\n"
        "Le celle arancioni indicano le posizioni cambiate rispetto al passo precedente.\n\n")

    ins("h3", "  Pulsanti di riproduzione\n")
    for btn, desc in [
        ("⏮  Reset",            "Torna allo step 0 (mazzo ordinato iniziale)"),
        ("⏭  Step",             "Avanza di un passo"),
        ("▶ Play / ⏸ Pausa",   "Avvia o mette in pausa la riproduzione automatica"),
        ("🔁  Replay",           "Riparte dall'inizio con la riproduzione automatica"),
    ]:
        ins("bullet", "  •  ")
        ins("code", btn)
        ins("bullet", f"  —  {desc}\n")
    ins("body", "\nLo slider «Velocità» regola l'intervallo tra un passo e il successivo (100–3 000 ms).\n")

    ins("h3", "  Navigazione rapida\n")
    for btn, desc in [
        ("⏮ Inizio",         "Vai allo step 0 (inizio assoluto)"),
        ("⏪ Inizio step",    "Vai alla prima carta dell'operazione corrente"),
        ("◄ Indietro",        "Torna indietro di un passo"),
        ("Fine step ⏩",      "Salta all'ultima carta dell'operazione corrente"),
        ("Pross. step ⏭",    "Vai alla prima carta dell'operazione successiva"),
        ("Fine ⏭",           "Vai all'ultimo step (fine assoluta)"),
    ]:
        ins("bullet", "  •  ")
        ins("code", btn)
        ins("bullet", f"  —  {desc}\n")

    ins("h3", "  Modalità carta-per-carta\n")
    ins("body",
        "Attivando il checkbox «Carta per carta», ogni operazione MSC o Kron viene "
        "espansa in sub-passi (uno per ogni carta che cambia posizione). "
        "La griglia mostra esattamente una cella arancione per sub-passo. "
        "Il vettore parte vuoto e si popola posizione per posizione.\n\n")
    ins("note",
        "Gli stati intermedi in modalità carta-per-carta non sono permutazioni valide "
        "(possono comparire valori duplicati). Solo l'ultimo sub-passo è valido.\n")

    ins("h3", "  Vettore T⁻¹\n")
    ins("body",
        "Sotto la griglia compare una riga di 27 celle «T⁻¹»: "
        "la cella di indice v mostra la posizione nel mazzo della carta di valore v, "
        "cioè deck⁻¹[v]. Cella grigia = carta non ancora rivelata (carta-per-carta); "
        "verde chiaro = carta già a destinazione; arancione = carta appena mossa.\n")
    sep()

    # ── 18 ─────────────────────────────────────────────────────────────────
    ins("h2", "19.  Tab Simulatore — pratica guidata del trucco\n")
    ins("body",
        "Il Simulatore calcola in forma chiusa (nessuna ricerca) i tre "
        "mescolamenti che portano la carta del pubblico nella posizione "
        "desiderata: al passo i la carta si trova in una colonna nota e basta "
        "il mescolamento che manda quella colonna nella cifra ternaria giusta "
        "del bersaglio. È ideale per imparare la procedura fisica del gioco.\n\n")
    ins("h3", "  Impostazione\n")
    ins("bullet", "  •  Scegli la posizione iniziale della carta (0 = dorso) e quella finale (default 13, il centro).\n")
    ins("bullet", "  •  Premi «▶ Calcola sequenza»: istruzioni, fotografie del mazzo e pratica si aggiornano subito.\n\n")
    ins("h3", "  Le tre schede\n")
    ins("bullet", "  1.  Istruzioni per il mago: per ogni fase, il MESCOLAMENTO (sigla funzionale) "
        "e l'IMPILAMENTO (gesto fisico, mazzetti dal dorso) — con l'avvertenza della "
        "Prima Crisi quando le due sigle differiscono (CDS↔DSC).\n")
    ins("bullet", "  2.  Visualizzazione mazzo: le 7 fotografie fisiche (mazzo iniziale, "
        "colonne e raccolta per ciascuna fase) con la carta del pubblico evidenziata.\n")
    ins("bullet", "  3.  Pratica interattiva: indichi la colonna e l'impilamento, il contatore "
        "registra gli errori. Impilare la sigla del mescolamento quando serve l'inversa "
        "è l'errore classico — il log te lo segnala.\n\n")
    ins("h3", "  Contatore errori\n")
    ins("body",
        "Ogni volta che si clicca la colonna sbagliata o si sceglie l'impilamento "
        "errato il contatore in alto si incrementa. A zero errori significa "
        "esecuzione perfetta.\n")
    sep()

    # ── 19 ─────────────────────────────────────────────────────────────────
    ins("h2", "20.  Tab Cicli — struttura ciclica della permutazione\n")
    ins("body",
        "Analizza la struttura ciclica della permutazione T correntemente calcolata "
        "nell'Explorer. Mostra:\n\n")
    ins("bullet", "  •  Ordine (periodo) di T: minimo comune multiplo delle lunghezze dei cicli.\n")
    ins("bullet", "  •  N° cicli: quanti cicli disgiunti compongono T (punti fissi inclusi).\n")
    ins("bullet", "  •  Tipo: il tipo ciclico, cioè quanti cicli per ciascuna lunghezza.\n\n")
    ins("body", "Sotto il riepilogo ci sono due sotto-tab:\n\n")
    ins("bullet", "  •  Cicli disgiunti  —  l'elenco dei cicli (a₁ a₂ … aₖ), colorati per "
        "lunghezza, con i punti fissi segnalati.\n")
    ins("bullet", "  •  Orbite carte     —  scelta una carta, la sequenza completa delle "
        "posizioni che occupa applicando T ripetutamente, fino al ritorno all'origine.\n\n")
    ins("note",
        "Il tab Cicli si aggiorna ogni volta che si calcola una nuova T, "
        "sia nell'Explorer sia nel tab Anteprima.\n")
    sep()

    # ── 20 ─────────────────────────────────────────────────────────────────
    ins("h2", "21.  Tab Distribuzione — decomposizioni per ogni T raggiungibile\n")
    ins("body",
        "Questa scheda NON dipende dai filtri: risponde a una domanda globale sul "
        "gruppo. Per ogni T raggiungibile come  A₂∘MSC∘A₁∘MSC∘A₀∘MSC  con "
        "Aᵢ ∈ GEN3⊗GEN3⊗GEN3, conta quante terne (A₀,A₁,A₂) la producono.\n\n")
    ins("body", "Si preme «▶ Calcola distribuzione» e compaiono due sotto-tab:\n\n")
    ins("bullet", "  •  Istogramma   —  in ascissa il numero di decomposizioni Kronecker, "
        "in ordinata quante T hanno quel numero.\n")
    ins("bullet", "  •  Tabella dati —  gli stessi valori in forma numerica, con i totali.\n\n")
    ins("ok",
        "    Risultato: i T distinti sono esattamente 216 e ciascuno ammette "
        "216² = 46 656 decomposizioni,\n"
        "    per un totale di 216³ = 10 077 696. La distribuzione è quindi "
        "perfettamente uniforme.\n"
        "    Il motivo è nella sezione 7: la relazione di trasporto porta tutti "
        "gli MSC a destra e MSC³ = I,\n"
        "    quindi ogni T raggiungibile è a sua volta un prodotto di Kronecker.\n\n")
    ins("note",
        "Le finestre «Classi di coniugio» (sezione 22) e «Tavola di Cayley» "
        "(sezione 23) NON si aprono da qui: i pulsanti 🔬 Coniugio e 🔮 Cayley "
        "sono nella barra delle azioni in alto, sempre disponibili.\n")
    sep()

    # ── 21 ─────────────────────────────────────────────────────────────────
    ins("h2", "22.  Finestra Classi di Coniugio e Centro\n")
    ins("body",
        "Accessibile dal tab Distribuzione. Calcola le 27 classi di coniugio del gruppo del gioco G = S₃³, "
        "mostrando per ognuna:\n\n")
    ins("bullet", "  •  Un rappresentante canonico (in notazione T_simbolica)\n")
    ins("bullet", "  •  La dimensione della classe (numero di elementi coniugati)\n")
    ins("bullet", "  •  L'ordine del rappresentante\n\n")
    ins("body", "Mostra anche il Centro di G: l'insieme degli elementi g tali che g∘h = h∘g per ogni h∈G.\n\n")
    ins("h3", "  Export\n")
    ins("bullet", "  •  TXT — lista testuale delle classi e del centro\n")
    ins("bullet", "  •  HTML — tabella formattata con stile, apribile nel browser\n")
    sep()

    # ── 22 ─────────────────────────────────────────────────────────────────
    ins("h2", "23.  Finestra Tavola di Cayley\n")
    ins("body",
        "Accessibile dall'Explorer (o dal menu). Calcola la tavola moltiplicativa "
        "di un sottoinsieme di G. Permette di:\n\n")
    ins("bullet", "  •  Inserire due espressioni T_simbolica e calcolarne il prodotto (composizione).\n")
    ins("bullet", "  •  Verificare le proprietà del gruppo: associatività, inverso, elemento neutro.\n")
    ins("bullet", "  •  Visualizzare la tabella completa di un generato per sottogruppi piccoli.\n\n")
    ins("h3", "  Export\n")
    ins("bullet", "  •  CSV (;) — tavola in formato tabellare\n")
    ins("bullet", "  •  HTML — tabella colorata con intestazione, apribile nel browser\n")
    sep()

    # ── 23 ─────────────────────────────────────────────────────────────────
    ins("h2", "24.  Finestra Protocollo — istruzioni per il mazziere\n")
    ins("body",
        "Accessibile dall'Explorer tramite il pulsante «📋 Protocollo» "
        "dopo aver calcolato una T_simbolica. "
        "Genera una pagina HTML con le istruzioni operative per eseguire il trucco:\n\n")
    ins("bullet", "  •  Periodo e forma canonica di T\n")
    ins("bullet", "  •  Tabella T / T⁻¹ con permutazioni numeriche\n")
    ins("bullet", "  •  Per ogni stadio: Stage simbolico, fattori P e J, istruzioni pratiche "
        "(es. «Raccogli nell'ordine: Sinistra → Destra → Centro»)\n")
    ins("bullet", "  •  Quale colonna raccogliere per portare la carta in ciascuna delle 27 posizioni\n\n")
    ins("body",
        "Il protocollo HTML si apre direttamente nel browser predefinito "
        "ed è progettato per essere stampato o proiettato durante l'esibizione.\n\n")
    ins("note",
        "Il pulsante Protocollo è attivo solo dopo aver premuto «▶ Calcola» nell'Explorer "
        "e aver eseguito le decomposizioni T⁻¹ (necessarie per la tabella delle posizioni).\n")
    sep()

    # ── 24 ─────────────────────────────────────────────────────────────────
    ins("h2", "25.  Flusso di lavoro consigliato\n")
    ins("h3", "  Esplorare il Gioco Reale:\n")
    for n, step in [
        ("1", "Premi 🎴 Gioco Reale → filtri impostati automaticamente (1 728 combinazioni)"),
        ("2", "Vai nel tab Analisi → premi «🔄 Genera & Analizza»"),
        ("3", "Clicca una riga: il pannello inferiore mostra tutte le sequenze Stage con P/J"),
        ("4", "Clicca un link → (testo blu) per aprire quella T_simbolica nell'Explorer"),
        ("5", "Nell'Explorer premi «▶ Calcola» poi naviga i sette sotto-tab"),
        ("6", "Sotto-tab Matrice: osserva le griglie 27×27 di T e T⁻¹"),
        ("7", "Premi «🔍 Decomposizioni T⁻¹» → 46 656 decomposizioni per T ∈ S₃³ in < 0.2 s"),
        ("8", "Premi «📋 Protocollo» → pagina HTML con istruzioni per il mazziere"),
        ("9", "Apri il sotto-tab 🎴 Mescolamento → Carica da Explorer → ▶ Play"),
    ]:
        ins("bullet", f"  {n}.  {step}\n")
    ins("body", "\n")

    ins("h3", "  Analizzare un'espressione specifica:\n")
    for n, step in [
        ("1", "Vai nel tab Explorer"),
        ("2", "Digita:  (CDS_U x SCD_U x SCD_U) o MSC o ...  e premi Ctrl+Invio"),
        ("3", "Naviga tra i sette sotto-tab per vedere i risultati"),
        ("4", "Premi «🔍 Decomposizioni T⁻¹» per le decomposizioni complete"),
        ("5", "Apri 🎴 Mescolamento → Carica da Explorer per la simulazione visiva"),
    ]:
        ins("bullet", f"  {n}.  {step}\n")
    ins("body", "\n")

    ins("h3", "  Esportare i dati:\n")
    for n, step in [
        ("1", "Imposta i filtri nei tab Stadio"),
        ("2", "Controlla il contatore live"),
        ("3", "Per il CSV completo: barra principale → «📊 Genera CSV» → scegli destinazione"),
        ("4", "Per l'analisi molteplicità: tab Analisi → Genera & Analizza → Esporta… (5 formati)"),
        ("5", "Per il PDF: barra principale → «📄 Genera PDF» (attenzione ai limiti di prestazione)"),
    ]:
        ins("bullet", f"  {n}.  {step}\n")
    sep()

    # ── 25 ─────────────────────────────────────────────────────────────────
    ins("h2", "26.  Formato dei file esportati\n")

    ins("h3", "  CSV generazione combinazioni  (sep=; , tutti i campi tra \"\")\n")
    ins("body", "9 colonne:\n\n")
    for col, desc in [
        ("#",             "Numero progressivo (intero, 1-based)"),
        ("Stage0",        "(P2×P1×P0) ∘ MSC ∘ (J2×J1×J0)  — Stadio 0 esteso"),
        ("Stage1",        "Stadio 1 esteso"),
        ("Stage2",        "Stadio 2 esteso"),
        ("A0",            "(P2∘J0) ⊗ (P1∘J2) ⊗ (P0∘J1)  — forma ridotta Stadio 0"),
        ("A1",            "Forma ridotta Stadio 1"),
        ("A2",            "Forma ridotta Stadio 2"),
        ("T_simbolica",   "T = A2 ∘ MSC ∘ A1 ∘ MSC ∘ A0 ∘ MSC"),
        ("T_permutazione","Lista numerica [0..26] della permutazione finale"),
    ]:
        ins("bullet", "  •  ")
        ins("code", f"{col}")
        ins("bullet", f"  —  {desc}\n")
    ins("body",
        "\nPer aprire in Excel: Dati → Da testo/CSV, separatore punto e virgola.\n\n")

    ins("h3", "  Analisi molteplicità — CSV  (sep=;)\n")
    ins("body", "3 colonne:\n\n")
    for col, desc in [
        ("T_permutazione",          "La permutazione numerica [0..26]"),
        ("T_simboliche_distinte",   "Tutte le sequenze Stage distinte, separate da virgola"),
        ("n_sim_distinte",          "Molteplicità (numero di sequenze Stage distinte)"),
    ]:
        ins("bullet", "  •  ")
        ins("code", col)
        ins("bullet", f"  —  {desc}\n")
    ins("body", "\n")

    ins("h3", "  Analisi molteplicità — Excel\n")
    ins("body", "Due fogli:\n\n")
    ins("bullet", "  •  «Perm → Simboliche»  —  una riga per permutazione T\n")
    ins("bullet", "  •  «Analisi molteplicità»  —  idem, con celle a capo automatico per le sequenze\n\n")

    ins("h3", "  Analisi molteplicità — HTML\n")
    ins("body",
        "Tabella con sfondo colorato, intestazione blu, righe alternate. "
        "Ogni sequenza Stage è in un proprio <div> con word-wrap attivo: "
        "le stringhe lunghe vanno a capo senza troncatura.\n\n")

    ins("h3", "  Dati grezzi — CSV  (sep=;)\n")
    ins("body", "9 colonne: #; Stage0; Stage1; Stage2; A0; A1; A2; T_simbolica; T_permutazione\n\n")

    ins("h3", "  Dati grezzi — Excel\n")
    ins("body", "Due fogli: «Dati grezzi» (combinazioni) e «Analisi molteplicità» (riepilogo). "
        "Font Courier New, intestazioni colorate, freeze panes, larghezze ottimizzate.\n\n")

    ins("h3", "  PDF generazione\n")
    ins("body",
        "Formato A2 orizzontale, una pagina per combinazione. Struttura:\n\n")
    ins("bullet", "  •  In alto: numero combinazione e descrizione simbolica degli stadi\n")
    ins("bullet", "  •  Colonna sinistra: matrici 3×3 di P0,P1,P2 e J0,J1,J2 per ogni stadio\n")
    ins("bullet", "  •  Colonne centrali: matrici 27×27 di Pᵢ, Jᵢ, Stageᵢ\n")
    ins("bullet", "  •  In basso: matrice 27×27 di T\n\n")
    ins("warn",
        "    Attenzione: il PDF per migliaia di combinazioni può richiedere molti minuti.\n"
        "    Usare i filtri per limitare le righe.\n\n")
    sep()

    # ── 26 ─────────────────────────────────────────────────────────────────
    ins("h2", "27.  Prestazioni e limiti pratici\n")
    ins("body", "Numero di combinazioni a seconda dei filtri:\n\n")
    for scenario, n, approx, consiglio in [
        ("Nessun filtro",              "5 159 780 352", "~5 miliardi",  "RIFIUTATO: oltre il limite"),
        ("J uniformi tutti gli stadi", "   80 621 568", "~80 milioni",  "RIFIUTATO: oltre il limite"),
        ("Un livello P fissato nei tre stadi", "23 887 872", "~24 milioni", "RIFIUTATO: oltre il limite"),
        ("Gioco Reale (preset)",       "        1 728", "1 728",        "uso normale, rapido"),
        ("Singolo stadio filtrato",    "1 – 1 728",     "variabile",    "ideale per esplorazione"),
    ]:
        ins("bullet", f"  •  {scenario:40}  →  {n:>18} ({approx})\n")
        ins("bullet2", f"     {consiglio}\n")
    ins("body", "\n")
    ins("h3", "  Limiti di sicurezza\n")
    ins("body",
        "Dalla versione 3.1.0 gli export si RIFIUTANO di partire sopra una certa "
        "soglia, invece di provarci e far esaurire la memoria:\n\n")
    ins("bullet", "  •  CSV e PDF:        20 000 000 di elementi\n")
    ins("bullet", "  •  PDF dettagliato:     200 000 combinazioni — soglia più bassa perché "
        "questo export deve tenere in memoria l'intero insieme per calcolare "
        "l'«Elenco matrici trasposte»\n")
    ins("body",
        "\nSopra la soglia compare un messaggio che spiega di restringere i filtri, "
        "e nessun file viene creato. Sotto la soglia ma sopra i 100 000 elementi "
        "(500 pagine per il PDF, 300 combinazioni per il PDF dettagliato) viene "
        "chiesta una conferma.\n\n")
    ins("ok",
        "    Il contatore live in alto mostra il numero PRIMA di avviare la generazione: verificarlo sempre.\n"
        "    Velocità misurate su un core: ~115 000 righe CSV/s; ~320 pagine PDF/s.\n\n")
    ins("h3", "Parallelismo (multiprocessing)\n")
    ins("body",
        "I calcoli pesanti e gli export sfruttano piu' core della CPU tramite "
        "processi paralleli. Non si usano i thread perche' in Python il GIL impedisce "
        "ai thread di accelerare il codice CPU-bound: i thread servono solo a tenere "
        "reattiva l'interfaccia. Sono parallelizzati:\n\n")
    ins("bullet", "  -  Export CSV e PDF (per export grandi)\n")
    ins("bullet", "  -  Tab Distribuzione (statistica globale sul gruppo)\n")
    ins("bullet", "  -  Ricerca delle decomposizioni Kronecker (Explorer)\n")
    ins("body",
        "\nL'attivazione del parallelismo e il numero di processi si regolano in "
        "Impostazioni. Il numero di worker e' adattivo e si basa sul LAVORO "
        "stimato, non su una soglia fissa di elementi: sotto mezzo secondo di "
        "calcolo si resta in-process (avviare dei processi costerebbe di piu'), "
        "sopra si usano tutti i core disponibili, dando a ciascun worker almeno "
        "un quinto di secondo di lavoro utile.\n\n")
    ins("note",
        "Alcuni calcoli non sono piu' parallelizzati perche' sono diventati "
        "troppo rapidi: la ricerca delle decomposizioni Kronecker dura circa "
        "0,03 s e la distribuzione circa 0,09 s. Distribuirle su piu' processi, "
        "ognuno dei quali re-importa numpy, costerebbe da dieci a cento volte "
        "il calcolo stesso.\n")
    ins("note",
        "I PDF prodotti in parallelo vengono deduplicati: ogni processo figlio "
        "incorpora la propria copia dei font, e senza deduplicazione un export "
        "di 864 pagine pesa 11 MB invece di 6. Serve pikepdf; senza, il file "
        "resta valido ma piu' grande.\n\n")
    ins("h3", "Export PDF dettagliato (carte, marcatori, periodo)\n")
    ins("body",
        "Oltre al PDF standard (matrici), il menu Genera offre «PDF dettagliato»: "
        "due combinazioni per pagina, layout fedele all'output HTML del programma in C. "
        "Ogni pagina mostra:\n\n")
    ins("bullet", "  -  DISP_INIZIO e Mescolamento 1/2/3 (con l'impilamento fra parentesi): il mazzo "
                  "iniziale e dopo ogni mescolamento, reso come nel C (9 righe x 4 colonne) con i semi reali;\n")
    ins("bullet", "  -  DISP INIZIALE / DISP FINALE: le sequenze complete di carte (tabella bordata);\n")
    ins("bullet", "  -  sotto il riquadro: ROVESCIAMENTO (R[m] e flag M0/M1/M2), poi MOLTIPLICAZIONE "
                  "(M[k]xM[j]xM[i] con gli indici numerici del C, mescolamenti e impilamenti) e "
                  "POSIZIONE ASSO #1/#2/#3 con posizione e settore ternario;\n")
    ins("bullet", "  -  in cima alla colonna centrale, un riquadro con DUE griglie (allineato ai mazzi, "
                  "cosi' resta la prima cosa che si legge dopo le disposizioni):\n")
    ins("bullet2", "        TABELLONE DI T  \u2014  i settori ternari degli Assi (minuscoli, come nel C): "
                   "ogni colonna e' un Asso, letta dall'alto in basso. Lette per RIGHE, invece, le tre sigle "
                   "formano il tabellone, in ordine cronologico INVERSO (riga in alto = terza): rileggendole "
                   "si riottiene esattamente T.\n")
    ins("bullet2", "        TABELLONE DI T\u207b\u00b9  \u2014  le stesse righe con ogni sigla sostituita "
                   "dalla propria inversa (CDS\u2194DSC; le altre quattro sono auto-inverse), in MAIUSCOLO. "
                   "Poiche' T = B\u2082 \u2297 B\u2081 \u2297 B\u2080 agisce cifra per cifra, invertire ogni "
                   "riga inverte l'intera permutazione. Si legge in orizzontale, quindi porta le etichette di "
                   "riga M_2 / M_1 / M_0 dall'alto in basso, con M_0 in fondo.\n")
    ins("ok",
        "    I due tabelloni valgono per QUALUNQUE combinazione, non solo per le 1 728 del gioco reale:\n"
        "    anche rovesciando un solo mazzetto (J non uniforme) o con P0/P1 diversi dall'identita'.\n"
        "    Il motivo: i tre Assi partono da 0, 13 e 26, cioe' (0,0,0), (1,1,1), (2,2,2) \u2014 la diagonale\n"
        "    ternaria. Se T = B\u2082 \u2297 B\u2081 \u2297 B\u2080 agisce cifra per cifra, allora\n"
        "    T(j,j,j) = (B\u2082(j), B\u2081(j), B\u2080(j)): la colonna dell'Asso j da' le tre cifre, e la riga r\n"
        "    letta per intero e' la sigla completa di B\u2082\u208b\u1d63. La griglia dipende solo da T, e i T\n"
        "    possibili sono 216: verificarli tutti copre tutte e 5 159 780 352 le combinazioni.\n")
    ins("note",
        "    Le righe del primo tabellone coincidono con i mescolamenti stampati sopra SOLO quando non c'e'\n"
        "    alcun rovesciamento (216 combinazioni su 1728). Un rovesciamento e' un'inversione su ogni cifra\n"
        "    e si fonde nelle righe, quindi le sigle effettive cambiano: restano un tabellone valido \u2014\n"
        "    quello di un gioco equivalente senza rovesciamenti che da' la stessa T \u2014 ma non sono piu'\n"
        "    i mescolamenti nominali. Per questo le didascalie parlano di T e T\u207b\u00b9, non di\n"
        "    mescolamenti e impilamenti: quelle parole sarebbero vere solo in 216 casi su 1728.\n")
    ins("bullet", "  -  la matrice 27x27 (verde/bianco) intestata P[i][j][k][m] come nel C, con "
                  "mescolamenti, periodo ed elenco delle matrici trasposte presenti nell'export.\n")
    ins("body",
        "\nLe combinazioni sono stampate nello STESSO ordine del programma C "
        "(cicli annidati i, j, k, m: terzo mescolamento piu' esterno, poi secondo, "
        "primo, infine gli 8 pattern di inversione): per il gioco reale la "
        "numerazione D# coincide esattamente con quella del C. Con parametri piu' "
        "ampi l'ordine si estende in modo analogo.\n\n")
    ins("body",
        "\nA differenza del programma C (limitato alle 1728 sequenze del gioco reale), "
        "qui l'export rispetta i filtri correnti e copre qualsiasi sottoinsieme di "
        "parametri. Vale lo stesso avviso sui numeri elevati: una pagina ricca per "
        "combinazione, quindi conviene filtrare.\n\n")
    ins("h3", "Combinazioni fuori dalle 1728 del gioco\n")
    ins("body",
        "Quando P0 o P1 non sono l'identita', o J non e' uniforme, lo stadio non e' "
        "piu' una raccolta eseguibile con un gesto solo: e' un prodotto di Kronecker. "
        "Il PDF lo segnala invece di far finta di niente:\n\n")
    ins("bullet", "  -  l'etichetta di stadio diventa P2xP1xP0 (es. SCD\u00d7CSD\u00d7SDC) al posto "
                  "della sigla di tre lettere, e va su una riga propria sotto il titolo del mazzo, "
                  "ridimensionata per stare nella colonna;\n")
    ins("bullet", "  -  gli INDICI M[k] NON vengono stampati: nel programma C M[k] e' un indice "
                  "numerico nella tabella dei mescolamenti, e per queste combinazioni non esiste. "
                  "Al suo posto compare l'elenco delle raccolte con la nota «indici M[...] non "
                  "definiti: fuori dalle 1728 del gioco»;\n")
    ins("bullet", "  -  non compare l'impilamento, perche' non c'e' un gesto fisico singolo che "
                  "realizzi lo stadio;\n")
    ins("bullet", "  -  i due tabelloni restano invece validi: dipendono solo da T, e valgono per "
                  "qualunque combinazione (vedi sopra).\n\n")
    ins("h3", "Annullare un export\n")
    ins("body",
        "Accanto alla barra di avanzamento compare il pulsante «✕ Annulla», "
        "attivo solo mentre un export e' in corso. Premendolo l'operazione si "
        "ferma appena possibile e NON viene creato alcun file: se al posto di "
        "destinazione c'era gia' qualcosa, resta intatto.\n\n")
    ins("bullet", "  -  negli export sequenziali il controllo avviene a ogni pagina o ogni "
                  "200 righe, quindi la risposta e' immediata;\n")
    ins("bullet", "  -  in quelli paralleli i processi che stanno gia' calcolando un blocco "
                  "lo terminano per conto loro, ma il risultato viene scartato e "
                  "l'interfaccia torna subito disponibile.\n")
    ins("note",
        "La garanzia «nessun file» viene dalla scrittura atomica: gli export "
        "scrivono su un file temporaneo e lo rinominano solo a lavoro "
        "concluso.\n\n")
    ins("h3", "Stima del tempo rimanente (ETA)\n")
    ins("body",
        "Durante gli export (CSV, PDF) e i calcoli lunghi (Generazione, Distribuzione) "
        "la barra di stato mostra una stima del tempo rimanente, ad es. "
        "\u00abPDF: pagina 320/2 000  -  ~12s rimanenti\u00bb. La stima si affina man "
        "mano che l'operazione procede. La stima usa la VELOCITA' RECENTE (media "
        "sugli ultimi campioni), non la media dall'inizio: cosi' ignora il tempo "
        "di avvio e converge subito al valore corretto, senza il transitorio "
        "iniziale gonfiato.\n\n")
    ins("warn",
        "    Senza filtri le combinazioni sarebbero miliardi: l'export viene rifiutato.\n"
        "    Anche sotto la soglia, un CSV di milioni di righe occupa gigabyte di disco.\n"
        "    Il PDF resta poco pratico oltre qualche migliaio di pagine (~2,5 KB a pagina).\n\n")
    sep()

    # ── 27 ─────────────────────────────────────────────────────────────────
    ins("h2", "28.  Installazione e dipendenze\n")
    ins("body",
        "Il programma richiede Python 3.9 o superiore. "
        "Librerie necessarie:\n\n")
    ins("formula", "    pip install numpy reportlab openpyxl pypdf pikepdf\n\n")
    for pkg, desc in [
        ("numpy",     "Calcolo matriciale e prodotti di Kronecker   (RICHIESTO)"),
        ("tkinter",   "Interfaccia grafica - inclusa in Python       (RICHIESTO)"),
        ("reportlab", "Export PDF con le matrici grafiche            (opzionale)"),
        ("openpyxl",  "Export Excel .xlsx (Analisi e Dati grezzi)    (opzionale)"),
        ("pypdf",     "Unione dei PDF nell'export parallelo          (opzionale)"),
        ("pikepdf",   "Deduplica le risorse nei PDF uniti            (opzionale)"),
    ]:
        ins("bullet", "  -  ")
        ins("code", pkg)
        ins("bullet", f"  -  {desc}\n")
    ins("body",
        "\nLe librerie 'opzionali' servono solo per le funzioni indicate: senza "
        "reportlab/openpyxl/pypdf il programma parte comunque, ma quegli export non "
        "sono disponibili. L'elenco completo e' in requirements.txt.\n\n")
    ins("note",
        "Installare tutto in un colpo:   pip install -r requirements.txt\n"
        "Controllare cosa e' installato:  python controlla_requisiti.py\n")
    ins("body", "\nAvvio del programma:\n\n")
    ins("formula",
        "    Windows (doppio clic):   avvia.bat\n"
        "    Riga di comando:         python gioco27.py\n"
        "    Come package Python:     python -m gioco27\n\n")
    ins("note",
        "Su Linux, in caso di errore «No module named tkinter»:\n"
        "    sudo apt install python3-tk\n")
    sep()

    # ── 28 ──────────────────────────────────────────────────────────────────
    ins("h2", "29.  Interfaccia guidata — modalità, aiuti e accessibilità\n")
    ins("body",
        "Dalla versione 2.8 il programma ha un'interfaccia guidata pensata anche "
        "per chi non conosce la teoria. Tutte le funzioni di analisi restano "
        "identiche: cambia solo quanto aiuto hai sotto mano.\n")
    ins("h3", "  La barra delle azioni in alto\n")
    ins("body",
        "È sempre visibile, sopra le schede, e non dipende dalla scheda "
        "corrente:\n\n")
    for btn, desc in [
        ("🔢  Conta",
         "conta le combinazioni che soddisfano i filtri correnti, senza generare nulla"),
        ("⬇  Genera…",
         "menu di export: PDF, PDF dettagliato (stile C: carte+matrici), CSV (;)"),
        ("↺  Reset tutto",
         "azzera i filtri di tutti gli stadi E riporta ogni scheda allo stato "
         "iniziale — da non confondere con «↺ Reset filtri» dei preset, che "
         "tocca solo i filtri"),
        ("🎓  Modalità principiante",
         "mostra o nasconde le schede avanzate (vedi sotto)"),
        ("Combinazioni:",
         "il contatore live, aggiornato a ogni modifica dei filtri"),
        ("🔮  Cayley",
         "apre la Tavola di Cayley del gruppo (sezione 23)"),
        ("🔬  Coniugio",
         "apre Classi di coniugio e centro (sezione 22)"),
        ("📋  Protocollo",
         "genera il protocollo passo-passo dell'ultima T calcolata (sezione 24)"),
        ("🖥️  Presentazione",
         "apre la «vista esecutore» a schermo intero (vedi sotto)"),
        ("✔  Verifica",
         "esegue la verifica di integrità del programma (vedi sotto)"),
        ("⚙️  Impostazioni",
         "processi paralleli e dimensione del testo d'aiuto"),
        ("⏻  Esci",
         "chiude il programma salvando le impostazioni"),
        ("✕  Annulla",
         "accanto alla barra di avanzamento, ferma l'export in corso senza "
         "creare alcun file"),
    ]:
        ins("bullet", "  •  ")
        ins("code", btn)
        ins("bullet", f"  —  {desc}\n")
    ins("body", "\n")
    ins("h3", "  Pulsante ✔ Verifica — controllo di integrità\n")
    ins("body",
        "Esegue in background la stessa verifica disponibile da riga di comando "
        "con  python -m gioco27 --selftest  e riporta l'esito nella barra di "
        "stato. Confronta:\n\n")
    ins("bullet", "  •  la simulazione fisica carta-per-carta con il modello "
        "matriciale, su tutte le 1 728 combinazioni;\n")
    ins("bullet", "  •  le ancore della tavola del libro (righe #100 e #82);\n")
    ins("bullet", "  •  le statistiche del capitolo 100 (periodi, auto-inverse, "
        "tipi ciclici);\n")
    ins("bullet", "  •  la ricostruzione della riga a partire dalle sole posizioni "
        "degli Assi, su tutte e 216 le righe.\n")
    ins("note",
        "Se una qualsiasi di queste verifiche fallisce, il modello matematico e "
        "la simulazione fisica non sono più d'accordo: è un allarme, non un "
        "avviso.\n")

    ins("h3", "  Pulsante 🖥️ Presentazione — vista esecutore\n")
    ins("body",
        "Apre una finestra a schermo intero pensata come gobbo per chi esegue il "
        "trucco davanti al pubblico: un passo alla volta, in caratteri grandi, "
        "con SOLO il gesto fisico da compiere (l'impilamento); la matematica "
        "resta in una riga piccola in fondo.\n\n"
        "I passi vengono dall'ultima T calcolata nel Simulatore o nell'Explorer: "
        "se corrisponde a una disposizione semplice del gioco mostra i tre "
        "impilamenti più il finale con le posizioni degli Assi, altrimenti "
        "mostra un riepilogo della T avvertendo che non è una sequenza "
        "fisicamente eseguibile con sole raccolte.\n\n")
    ins("bullet", "  •  → / spazio / clic  —  passo successivo\n")
    ins("bullet", "  •  ←                  —  passo precedente\n")
    ins("bullet", "  •  F11                —  attiva/disattiva schermo intero\n")
    ins("bullet", "  •  Esc                —  esce dallo schermo intero\n\n")

    ins("h3", "  Modalità Principiante / Esperto\n")
    ins("body",
        "In alto, accanto ai pulsanti, c'è la casella «Modalità principiante».\n")
    ins("bullet",
        "Principiante (predefinita): restano visibili solo le schede essenziali "
        "— Inizia qui, Simulatore, Tavola 216, Anteprima, Analisi, Guida. Sono nascoste le "
        "schede Stadio 0/1/2 e quelle avanzate (Explorer, Cicli, Distribuzione).\n")
    ins("bullet",
        "Esperto: togli la spunta e ricompaiono tutte le schede.\n")
    ins("note",
        "La scelta viene ricordata tra una sessione e l'altra. Alla primissima "
        "apertura della nuova interfaccia si parte sempre in Principiante.\n")
    ins("h3", "  Scheda «Inizia qui»\n")
    ins("body",
        "È la prima scheda: una mappa rapida con i tre passi base (Prova il "
        "Simulatore, Sfoglia la Tavola 216, Approfondisci), quattro pulsanti di "
        "azione rapida — 🎩 Prova il Simulatore, 🎴 Carica «Gioco Reale», "
        "🔍 Vai all'Anteprima, 📖 Apri la Guida completa — e un glossario dei "
        "termini in parole semplici (passa il mouse per la definizione "
        "estesa).\n")
    ins("h3", "  Banner d'aiuto «Cosa fa questa scheda?»\n")
    ins("body",
        "In cima a ogni scheda e a molte finestre c'è una riga azzurra che "
        "riassume a cosa serve quella vista. «Mostra di più» apre una spiegazione "
        "estesa; «Apri Guida» porta a questa documentazione.\n")
    ins("h3", "  Tooltip contestuali\n")
    ins("body",
        "Passando il mouse su pulsanti, menu e termini tecnici compare un breve "
        "suggerimento. Nei tab Stadio, ad esempio, ogni casella P o J mostra cosa "
        "fa quella permutazione (es. «CDS_U — Rotazione in avanti: S->C, C->D, "
        "D->S»).\n")
    ins("h3", "  Legenda colori GEN3\n")
    ins("body",
        "In fondo alla finestra, sempre visibile, c'è la legenda dei 6 colori dei "
        "generatori GEN3 (SCD_U, SDC_U, CSD_U, CDS_U, DSC_U, DCS_U): sono gli "
        "stessi colori con cui i nomi compaiono nelle formule dell'Explorer.\n")
    ins("h3", "  Stati vuoti\n")
    ins("body",
        "Prima di premere «Calcola», i riquadri dei risultati mostrano una frase "
        "guida invece di restare vuoti (es. nell'Anteprima «Imposta P e J... e "
        "premi Calcola»). Il segnaposto sparisce appena arrivano i dati.\n")
    ins("h3", "  Dimensione testo aiuti (utile su 4K)\n")
    ins("body",
        "Su schermi ad altissima risoluzione il testo d'aiuto può risultare "
        "piccolo. In Impostazioni (ingranaggio in alto) c'è «Dimensione testo "
        "aiuti»: scegli Normale, Grande, Molto grande o Enorme. Il cambiamento è "
        "immediato e riguarda tooltip, banner, glossario, pannelli esplicativi e "
        "stati vuoti.\n")
    sep()

    # ── 29 ──────────────────────────────────────────────────────────────────
    ins("h2", "30.  Glossario dei termini\n")
    ins("body", "I termini ricorrenti, spiegati in modo semplice.\n")
    ins("bullet", "MSC — il mescolamento di base: distribuisci le 27 carte in 3 "
                  "colonne e le raccogli. È l'operazione elementare ripetuta a "
                  "ogni stadio.\n")
    ins("bullet", "Permutazione — un modo di rimescolare: a ogni posizione di "
                  "partenza associa una posizione d'arrivo. Tutto il gioco è "
                  "composizione di permutazioni.\n")
    ins("bullet", "Stadio — una «mossa» del gioco: Stadioᵢ = Pᵢ ∘ MSC ∘ Jᵢ. Il "
                  "gioco completo concatena 3 stadi.\n")
    ins("bullet", "P (raccolta) — come riprendi i pacchetti dopo la messa in "
                  "colonna. È un prodotto di Kronecker P₂ ⊗ P₁ ⊗ P₀.\n")
    ins("bullet", "J (orientazione) — come orienti il mazzo prima del "
                  "mescolamento (identità o inversione, a ciascun livello).\n")
    ins("bullet", "GEN3 — le 6 permutazioni elementari su 3 elementi "
                  "(S=sinistra, C=centro, D=destra): SCD_U è l'identità, le altre "
                  "scambi o rotazioni.\n")
    ins("bullet", "Kronecker (⊗) — il prodotto che combina tre matrici 3×3 in "
                  "una trasformazione su 27 = 3×3×3 posizioni: un livello per le "
                  "carte, uno per le terzine, uno per i pacchetti.\n")
    ins("bullet", "T / T⁻¹ — la trasformazione totale dei 3 stadi (T) e la sua "
                  "inversa (T⁻¹), che riporta il mazzo all'origine.\n")
    ins("bullet", "Ciclo — un gruppetto di posizioni che ruotano tra loro "
                  "ripetendo la mossa; ogni permutazione si scompone in cicli "
                  "disgiunti.\n")
    ins("bullet", "Ordine — quante volte ripetere una mossa per tornare al punto "
                  "di partenza (il minimo comune multiplo delle lunghezze dei "
                  "cicli).\n")
    ins("bullet", "Coniugio — due mosse coniugate fanno la stessa cosa a meno di "
                  "rinominare le posizioni (g ∘ x ∘ g⁻¹ = y).\n")
    ins("bullet", "Cayley (tavola) — la tabella di tutti i prodotti A ∘ B tra le "
                  "216 mosse del gruppo.\n")
    ins("bullet", "Centro Z(G) — gli elementi che commutano con tutti; qui è "
                  "banale (solo l'identità).\n")
    ins("bullet", "Sottogruppo, commutatore — strumenti per misurare quanto due "
                  "mosse «si intrecciano» (vedi tab Explorer e finestra Cayley).\n")
    ins("bullet", "Forma canonica K ∘ MSCᵏ — la scrittura ridotta e unica di una "
                  "trasformazione senza J, con un blocco di Kronecker K e una "
                  "potenza di MSC.\n")
    sep()

    # ── 30 ──────────────────────────────────────────────────────────────────
    ins("h2", "31.  Esempio passo-passo — dal Gioco Reale all'analisi\n")
    ins("body", "Un percorso completo per prendere confidenza:\n")
    ins("bullet", "1. Nella scheda «Inizia qui» premi «Carica Gioco Reale» (oppure "
                  "il preset nella barra arancione). Il contatore in alto mostra "
                  "1 728 combinazioni.\n")
    ins("bullet", "2. Vai in «Anteprima», scegli un valore per ogni P e J e premi "
                  "«▶ Calcola»: vedrai le formule dei tre stadi e la permutazione "
                  "T risultante.\n")
    ins("bullet", "3. Attiva la modalità Esperto e apri «Explorer»: scrivi o "
                  "ritrova un'espressione e premi «Calcola» per ottenere forma "
                  "normalizzata, periodo, forma canonica e le matrici di T e "
                  "T⁻¹.\n")
    ins("bullet", "4. In «Cicli» osserva la struttura ciclica e l'ordine della "
                  "T appena calcolata.\n")
    ins("bullet", "5. Esporta ciò che ti serve: LaTeX/SVG dall'Explorer o "
                  "dall'Anteprima, CSV/Excel dall'Analisi (vedi sezioni 26 e 31).\n")
    sep()

    # ── 31 ──────────────────────────────────────────────────────────────────
    ins("h2", "32.  Export LaTeX / SVG — Anteprima, Explorer, Cayley, Coniugio\n")
    ins("body",
        "Diverse viste permettono di esportare i dati in formati pronti per "
        "documenti e libretti.\n")
    ins("h3", "  Anteprima ed Explorer\n")
    ins("body",
        "Il pulsante «Esporta LaTeX / SVG» apre un dialog con anteprima a schede "
        "e «Esporta tutto in una cartella»: tabella LaTeX di T e T⁻¹, cicli "
        "disgiunti, diagramma a frecce SVG, decomposizioni di Kronecker e un "
        "riepilogo testuale.\n")
    ins("h3", "  Finestra Tavola di Cayley\n")
    ins("body",
        "Dal menu «Esporta…» trovi, oltre a CSV e HTML, la voce «LaTeX / SVG»: "
        "una heatmap SVG 216×216 colorata per elemento risultante, una griglia "
        "TikZ colorata e il LaTeX del calcolo selezionato (A∘B, B∘A, inversi, "
        "commutatore, potenze, sottogruppo ⟨A,B⟩).\n")
    ins("h3", "  Finestra Classi di Coniugio\n")
    ins("body",
        "Dal menu «Esporta…», oltre a TXT e HTML, la voce «LaTeX / SVG» genera la "
        "tabella LaTeX delle 27 classi con gli elementi, una griglia SVG dei 216 "
        "elementi colorati per classe e un istogramma SVG delle dimensioni delle "
        "classi.\n")
    sep()

    # ── 32 ──────────────────────────────────────────────────────────────────
    ins("h2", "33.  Domande frequenti (FAQ)\n")
    ins("h3", "  Non vedo i tab Stadio / Explorer / Cicli. Perché?\n")
    ins("body",
        "Sei in modalità Principiante: quelle schede sono nascoste per "
        "semplificare. Togli la spunta a «Modalità principiante» in alto per "
        "rivederle tutte.\n")
    ins("h3", "  Il testo d'aiuto è troppo piccolo (monitor 4K).\n")
    ins("body",
        "Apri Impostazioni e alza «Dimensione testo aiuti» (Grande / Molto "
        "grande / Enorme). L'effetto è immediato.\n")
    ins("h3", "  Quante combinazioni esistono in tutto?\n")
    ins("body",
        "A tutti i livelli liberi ogni stadio ha 6×6×6 (P) × 2×2×2 (J) = 1 728 "
        "possibilità, quindi 1 728³ ≈ 5,16 miliardi in totale. Il «Gioco Reale» "
        "ne seleziona 12 per stadio fisicamente eseguibili → 12³ = 1 728 "
        "sequenze.\n")
    ins("h3", "  Qual è la differenza tra P e J?\n")
    ins("body",
        "P è la raccolta (come riprendi i pacchetti): 6 scelte per livello. J è "
        "l'orientazione del mazzo (identità o inversione): 2 scelte per livello. "
        "Insieme, con MSC, formano lo stadio P ∘ MSC ∘ J.\n")
    ins("h3", "  Cos'è la «forma canonica»?\n")
    ins("body",
        "Per le espressioni senza J, ogni trasformazione si riduce in modo unico "
        "a K ∘ MSCᵏ (un blocco di Kronecker più una potenza di MSC). È la «carta "
        "d'identità» algebrica della mossa, utile per confrontare trasformazioni "
        "diverse.\n")
    ins("h3", "  Le mie impostazioni dove vengono salvate?\n")
    ins("body",
        "In un file di configurazione nella tua cartella utente "
        "(~/.gioco27/config.json): modalità, dimensione testo, worker paralleli e "
        "geometria della finestra.\n")
    sep()

    from .. import __version__ as _ver
    ins("body",
        f"Versione: gioco27 v{_ver}  -  package modulare con Analisi Molteplicita', "
        "Explorer, Simulatore, Tavola 216, Cicli, Distribuzione, Coniugio, Cayley, "
        "Protocollo.\n"
        "Novita' della 3.1.1: annullamento degli export con il pulsante \u2715 Annulla. "
        "Dalla 3.1.0: numerazione di stadi e fattori a base 0 (Stadio 0-2, "
        "P0/P1/P2, J0/J1/J2), export a flusso con limiti di sicurezza (niente piu' "
        "esaurimento di memoria sui filtri larghi), CSV ~11x piu' veloce, PDF ~2x "
        "piu' veloce e ~2,5x piu' leggero, distribuzione delle decomposizioni "
        "immediata, cache su JSON e validazione della configurazione. Nel PDF "
        "dettagliato, il tabellone di T\u207b\u00b9 accanto a quello dei "
        "mescolamenti.\n")

