# V4 — Audit di copertura matematica e didattica

**Audit preparatorio alla progettazione della versione 4.0 del programma del Gioco delle 27 carte.**
Documento di sola analisi: nessuna funzionalità è stata aggiunta, nessun file del programma è stato
modificato, nessun compartimento I, J o K è stato iniziato.

Allegato macchina-leggibile: `V4_COVERAGE_MATRIX.csv` (la matrice principale del § 7, una riga per concetto).

Legenda della natura delle affermazioni (§ 41 dell'incarico). Quando non è ovvio dal contesto, le affermazioni
sono marcate con: **[FONTE]** contenuto del libro o dell'articolo; **[CODICE]** comportamento letto nel codice;
**[TEST]** proprietà protetta dalla suite; **[UI]** osservazione dell'interfaccia (codice delle viste e testi
della guida); **[ESEC]** verificato eseguendo il core in questo audit; **[INF]** inferenza dell'auditor;
**[PROP]** proposta per la 4.0 — mai contenuto delle fonti.

---

## 1. Identità e perimetro

| Voce | Valore |
|---|---|
| Repository | `27-card-trick-explorer` (unico albero consultato) |
| Branch | `main` |
| HEAD all'ingresso | `9bcc78a78b41fbde2ddfeedfc30a7f01fb1ec2f2` — `docs(H2): close the accessibility and layout compartment` |
| `origin/main` | `54445af` — il ramo locale è **66 commit avanti**, nessun push |
| Working tree all'ingresso | pulito (`git status`: *nothing to commit*); durante l'audit l'utente ha aggiunto nella radice due file **non tracciati**: `LIBRO_MAIN.pdf` e `Articolo.pdf` (vedi § 2) |
| Versione applicativa | `3.1.3` (`pyproject.toml`) |
| Compartimenti chiusi | A, D, B, C, E, F, G1, G2, H1, H2 (documenti `*_CLOSED.md` nella radice) |
| Compartimenti non iniziati | I, J, K — **non iniziati da questo audit** |
| Data | 24 settembre 2026 |

### 1.1 Domanda dell'audit

> Dato il programma stabilizzato dopo H, quanto bene esso rappresenta, permette di esplorare e insegna ogni
> aspetto matematico e didattico significativo del Gioco delle 27 carte trattato nel libro e nell'articolo?

La priorità è la **copertura del contenuto**, non la pulizia architetturale (prevista in K0). La 4.0 resta il
programma del **Gioco delle 27 carte**; la generalizzazione a `b^k` e il frontend web sono **oltre la 4.0** e
compaiono solo nel § 24.

### 1.2 Stato ricostruito dai documenti di chiusura (non riaperto)

Letti `F_ANALYSIS_CLOSED.md`, `G1_SERVICES_MODELS_CLOSED.md`, `G2_LIFECYCLE_PERSISTENCE_CLOSED.md`,
`H1_PRESENTATION_I18N_CLOSED.md`, `H2_ACCESSIBILITY_LAYOUT_CLOSED.md`, `GIT_BASELINE_AND_RECONCILIATION.md` e,
per il contesto matematico, `NOTE_VERSIONE_3*.md`. Ne discendono i vincoli che l'audit rispetta:

* architettura `core → services → presentation` con `services→gui = 0`, `core→services = 0`, `core→gui = 0`,
  cicli statici = 0, un solo parser autorevole (`core/algebra.py`), nessun worker che tocca widget Tk, rotte di
  pubblicazione atomiche (G2 § 10, H2 § 18) — **non toccati**;
* difetti B01–B12, R01, R04, R05, R07, M01, M03, M05, M06 chiusi e protetti; M04 chiuso in H2 — **non riproposti**;
* debiti dichiarati che riguardano I/J/K: «strumenti matematici avanzati» per I; «cronologia utente, nessun
  undo/redo, il lifecycle dei lavori non è la cronologia» per J (G2 § 20); N03 (`pypdfium2`) e N04
  (`gioco27.spec`) per K; facciate legacy di `core.algebra` e `core.permutations` senza compartimento;
* duplicazioni preservate deliberatamente come **oracoli** (inverse, tabelle GEN3/MSC, tavole di Cayley) —
  da non rimuovere senza sostituto indipendente.

### 1.3 Convenzioni verificate nel codice e nei test

Confermate da `tests/test_baseline_matematica.py` (25 test) e ricontrollate in esecuzione [ESEC]:

```text
posizioni 0..26, n = 9·n2 + 3·n1 + n0
T[carta] = posizione finale            deck[posizione] = carta
M[T[i], i] = 1                         (a ∘ b)[i] = a[b[i]]      M(a∘b) = M(a) @ M(b)
MSC(n) = 9·(n mod 3) + ⌊n/3⌋           MSC³ = I     (sulle cifre: (n2,n1,n0) ↦ (n0,n2,n1))
G = GEN3³ (216)      H_programma = G ⋊ ⟨MSC⟩ (648)     forma canonica K ∘ MSC^k
IMPILAMENTO = inversa del MESCOLAMENTO (scambio CDS ↔ DSC)
numerazione della tavola: # = k1 + 6·k2 + 36·k3, sigle nell'ordine SCD, SDC, CSD, DSC, CDS, DCS
```

Tutte coincidono con le convenzioni del libro («Notazioni e convenzioni», pp. vii–xv; Appendice A; Appendice C)
**tranne i nomi dei gruppi**, discussi nei §§ 12 e 21 (il libro chiama `H` il gruppo di 216 elementi e `Γ`
quello di 648; il programma chiama `G` il primo, `H` il secondo nel codice e `G_ext` nella guida).

### 1.4 Vincoli di perimetro rispettati

Nessun accesso fuori dal repository: nessuna directory padre o sorella, nessuna copia o clone, nessuno script
esterno. I controlli sono comandi Python inline sul core del repository, lanciati sul working tree. Gli unici
oggetti fuori dall'albero sono strumenti d'ambiente — l'interprete Python e i pacchetti di test (pytest, numpy,
reportlab, openpyxl, pypdf, pikepdf, pyflakes) in un ambiente virtuale della VM di sessione, più il display
virtuale Xvfb e le directory temporanee di pytest — che non contengono nulla del progetto. Nessun file è stato
cancellato; l'unica cancellazione è stata il `.git/index.lock` orfano lasciato da un `git status` della VM.

---

## 2. Fonti disponibili

### 2.1 Tabella delle fonti

| Fonte | File | Versione/data se disponibile | Pagine/sezioni utilizzabili | Stato |
|---|---|---|---|---|
| **Libro** — *Il gioco delle 27 carte come sistema di permutazioni* (M. Berlanda) | `LIBRO_MAIN.pdf` (radice, **non tracciato**, 30,5 MB, sha256 `1e1c9a7e4a8b19e7…`) | metadati PDF: 17 set 2026, «LaTeX via pandoc», MiKTeX | 419 pp. PDF: front matter i–xxv (Introduzione, Notazioni, Prefazione, Prologo); Parte I capp. «Le carte prima della Psicostoria», 1–7; Parte II capp. 8–12; Parte III App. A, B, C, D. Testo estraibile al 100 % con `pdftotext`; le figure e alcune tavole sono raster (non leggibili come testo) | **PRESENTE** |
| **Articolo** — *Permutazioni digitalmente separabili nei giochi di carte su b^m posizioni* | `Articolo.pdf` (radice, **non tracciato**, 466 KB, sha256 `293ba88c1942a2d7…`) | metadati: 10 set 2026, pdfTeX | 11 pp., §§ 1–8 + App. A + bibliografia | **AMBIGUA** — vedi § 2.2 |
| **Articolo, seconda versione** — stesso titolo, «Articolo originale» | Appendice D di `LIBRO_MAIN.pdf` (pp. PDF 401–419, pp. a stampa 373–391) | successiva al 10 set (libro del 17 set); 19 pp. | §§ 1–9 + App. A | **AMBIGUA** — vedi § 2.2 |
| `PROJECT_EVOLUTION_PLAN.md` | **assente** dal repository; `GIT_BASELINE_AND_RECONCILIATION.md` § 1/§ 3 lo dichiara «presente solo nella copia Astra, mai versionato» | — | nessuna; le idee del «§17» sono note solo dall'elenco riportato nell'incarico | **ASSENTE** |
| Documentazione tecnica corrente | `*_CLOSED.md`, `GIT_BASELINE_AND_RECONCILIATION.md`, `NOTE_VERSIONE_3*.md`, `README.md` | fino a H2 (HEAD `9bcc78a`) | integrali | **PRESENTE** |
| Guida e glossario dell'applicazione | `gioco27/i18n.py` (catalogo IT/EN, 1 325 chiavi per lingua: 354 `guide.*`, 42 `glossary.*`), `gui/guide.py`, `gui/glossary.py` | 3.1.3 + H1/H2 | 33 sezioni della Guida, glossario di 14 voci, banner d'aiuto per scheda | **PRESENTE** |

Il `README.md` rimanda all'articolo tramite il repository esterno `27-card-tensor-structure`: **non è stato
consultato** (vincolo di perimetro e divieto di ricerca sul web).

### 2.2 Le due versioni dell'articolo (ambiguità dichiarata, non risolta)

Il repository contiene due testi con lo stesso titolo e lo stesso autore. Nessun file del repository stabilisce
quale sia autorevole; le date dei PDF suggeriscono che l'Appendice D sia la più recente [INF], ma **non è stato
scelto in silenzio**. Differenze rilevate [FONTE]:

| Aspetto | `Articolo.pdf` (11 pp.) | Libro, App. D (19 pp.) |
|---|---|---|
| Rovesciamenti | «Non sono ammessi rovesciamenti del mazzo» (§ 1) | ammesso «un rovesciamento globale prefissato, applicato prima della distribuzione» (§ 1) |
| Molteplicità | assente | Prop. 5.1 (molteplicità 2^m del modello ordinario con rovesciamento), Cor. 5.2 (formula esplicita di inversione delle raccolte), Prop. 5.3, Teor. 5.4 (saturazione e uniformità della famiglia estesa: 1 728 configurazioni/stadio, 23 887 872 storie per trasformazione) |
| Somme di fibra come criterio | Oss. 5.3: la compatibilità delle somme **non** è assunta come criterio di riconoscimento per una permutazione arbitraria | Teor. 6.4: **criterio di riconoscimento** — una permutazione arbitraria è separabile se e solo se i valori ricostruiti formano permutazioni di D_b a ogni livello |
| Numerazione | Teor. 5.1 formula di fibra, Es. 6.1, Prop. 7.1, Oss. 7.2 | Teor. 6.1, Es. 7.1 + Es. 7.2 (traiettoria ordinaria con rovesciamenti), Prop. 8.1, Oss. 8.2 |

Le due versioni **possono convivere** per quasi tutto (la seconda estende la prima). Richiedono una
**DECISIONE DI PRODOTTO** in due punti: quale testo cita la 4.0, e se lo strumento «riconoscimento per somme»
(§ 13, § 22) si fonda sul Teorema 6.4 dell'App. D. Nel seguito «Articolo» indica `Articolo.pdf`; «App. D» la
seconda versione; le righe della matrice che dipendono dalla differenza lo dichiarano.

### 2.3 Fonti mancanti e conclusioni NON VERIFICABILI

Il piano `PROJECT_EVOLUTION_PLAN.md` non è nel repository. Conseguenze:

* le idee del «§17» sono valutate (§ 18) sulla base dell'elenco fornito dall'incarico, del libro e
  dell'articolo; il **testo** del § 17 non è verificabile, e nessuna affermazione su di esso viene attribuita al piano;
* nessuna riga della matrice dipende dal solo piano, quindi **nessuna riga è marcata NON VERIFICABILE**
  (il libro e l'articolo, arrivati durante l'audit, coprono tutti i temi).

---

## 3. Metodo

1. **Baseline** (§ 27): `git status/branch/HEAD/origin`, `pytest tests/test_baseline_matematica.py`, suite completa.
2. **Prima passata, source-first**: lettura sequenziale del libro (front matter, capp. 0–10 per intero; cap. 11
   nelle sezioni pertinenti al caso 27 — 11.7, 11.8, 11.9 — e per struttura nel resto; cap. 12 per struttura e
   sezioni 12.2–12.9 per contenuto; App. A, B, C integrali; App. D per confronto) e lettura integrale di
   `Articolo.pdf`. Inventario dei concetti con posizione nella fonte (§§ 4–5).
3. **Seconda passata, program-first**: censimento indipendente di viste, dialoghi, servizi e core (§ 6), da
   codice, testi della guida e test.
4. **Esecuzione controllata**: Python inline sul core (`gioco27.core.gioco_reale`, `group_theory`) per
   verificare gli esempi numerici del libro e costruire gli esempi/controesempi del § 13 [ESEC]. L'interfaccia
   non è stata pilotata a mano: il comportamento UI è desunto dal codice delle viste e dalla suite di layout
   (H2), marcato [UI].
5. **Matrice** a quattro livelli per concetto: **C** calcolo, **V** visualizzazione, **I** interazione,
   **D** didattica (valori `sì` / `parz.` / `no` / `n.a.`), stato secondo il § 10 dell'incarico, evidenza
   tipizzata (CODICE/TEST/UI/DOC/ESEC).
6. **Regola di stato** adottata: COMPLETO richiede C=sì e che V, I, D siano `sì` dove pertinenti rispetto al
   livello della fonte; PARZIALE se almeno un livello essenziale è `parz.`/`no` ma esiste una parte
   significativa; ASSENTE se non esiste uno strumento adeguato (anche con C implicito nel core); NON APPLICABILE
   per contenuto editoriale, narrativo, storico o manuale senza traduzione software utile.

Granularità: un concetto per proposizione, operazione o distinzione trattata dalla fonte con un obiettivo
proprio. Le 15 routine del cap. 7 (B1–B15) e i 13 strumenti (A1–A13) hanno una riga ciascuno.

---

## 4. Inventario del libro

Numerazione: pagine **a stampa** (le pagine PDF sono +28 per la Parte I–III). Per ciascun capitolo:
concetti (ID della matrice del § 7), obiettivo matematico, obiettivo didattico, procedura fisica associata.

### 4.1 Front matter (pp. v–xxv)

* **Introduzione generale** — la progressione «gesto → posizioni → trasformazioni → struttura», con cambi
  di linguaggio successivi (L55). Obiettivo didattico dichiarato: «sapere che qualcosa funziona e capire perché
  funzioni sono due esperienze molto diverse».
* **Notazioni e convenzioni** (pp. vii–xv) — indici da 0; carta ≠ posizione; `A∘B` = prima B; matrice con
  `(Pπ)π(i),i = 1`; `J(i) = 26 − i`; tabellone `T=(ρ2,ρ1,ρ0)`; tabellone diretto/inverso; gruppo dei tabelloni
  `G ≅ S3³`; nomi narrativi **Gaia, Cronaca, Procedura, Mondo-di-Mazzo, Giullare/Jester**; `H = ρ(S3³)`
  realizzazione matriciale (216); caso `b^m`, `K_T`, `MSC_m`, stadio `T_i = P_i ∘ MSC ∘ J^εi`; wreath product
  `S_b ≀ S_m`; `K_{j,i}` (L106).
* **Prefazione** (Asimov, psicostoria, Gaia) e **Prologo** (il trucco delle 21 carte, la riga centrale,
  «il valore complessivo delle colonne rimaneva costante») — contenuto narrativo/storico (L01, L107, L108).

### 4.2 Parte I — Il Gioco

| Capitolo / sezioni (pp.) | Concetti (ID) |
|---|---|
| **Le carte prima della Psicostoria** (2–10) | storia (Pacioli, Verini, Galasso, Gergonne, Gardner, Elmsley) L01; problema diretto vs inverso (Gergonne) L02; 27 = 3³ come codifica della destinazione, ACAAN L03; dalla carta singola alla trasformazione globale L14 |
| **1 Hari Seldon e la Prima Fondazione** (11–43) | 1.1–1.2 divisione con resto `P = 3q + r`, etichette dei mazzetti per ordine di generazione L04; 1.3 Prop. 1.1 indirizzo ternario, es. 19 = (2,0,1) L05; 1.4 gerarchia 27→9→3→1, blocchi B0,B1,B2, griglia 3×3×3 L06; 1.5/1.8 codifica ω: posizione ↔ parola in {S,C,D}³, ordine lessicografico, 19 = DSC L07; **1.6 «la macchina che dimentica»**: `P_{k+1} = ⌊P_k/3⌋ + 9 s_k`, `P3 = 9 s2 + 3 s1 + s0` L08; 1.7 flusso delle cifre `(n2,n1,n0)→(s0,n2,n1)→(s1,s0,n2)→(s2,s1,s0)` L09; 1.9 Prop. 1.6 storia delle distribuzioni = rev ω(n), indipendente dalle raccolte L10; 1.10 somme dei blocchi 36/117/198, Prop. 1.8 elemento mancante L11; 1.10.1 configurazione finale come archivio stratificato L12; 1.11 completezza, regola di completamento (due simboli determinano il terzo) L13 |
| **2 Gaal Dornick** (44–75) | 2.1–2.2 carte vs posizioni vs trasformazioni, `f : X → C`, convenzione `π(i) = j` L14; 2.2.2 convenzioni fisiche (dorso in alto, posizione 0 in cima, distribuzione ciclica S,C,D) L15; 2.2.3 mazzo di riferimento A–K♠, A–K♣, A♥; Assi nelle posizioni diagonali 0, 13, 26 L16; 2.3 S_n e S3 come le sei raccolte L17; 2.4.1–2.4.4 **tabellone generatore**: righe = mescolamenti (ultimo in alto), lettura gerarchica → mazzo finale, colonne → destino degli Assi L18; 2.4.5 **Prima crisi di Seldon**: DSC↔CDS, tabellone diretto vs inverso, colonne che rispondono alla domanda speculare (righe 62 vs 56 della tavola) L19; 2.4.6–2.4.8 ricostruzione del mescolamento dalle somme (blocchi→riga alta, terzine→riga media, limite al livello fine), ricetta per ordinamento delle somme, orientazione L20, L22; 2.4.7 «tre leggi delle posizioni» (Prop. 2.28) L21; 2.5 **Seconda crisi**: il rovesciamento globale assorbito nel tabellone L23 |
| **3 Seconda Fondazione** (76–88) | 3.1 combinazioni lineari, sistema lineare, matrice dei coefficienti, prodotto matrice–vettore L24; 3.2.1–3.2.2 matrici di permutazione, Prop. 3.37 biiezione, Prop. 3.39 `P_{π∘ρ} = P_π P_ρ` L25; 3.2.3 trasposta = inversa, matrici simmetriche ↔ involuzioni, Oss. 3.44 (la Prima Crisi era una trasposizione) L26; 3.2.4 **simulazione concreta vs modello matriciale** (menziona esplicitamente il programma) L27; 3.2.5 periodo, Prop. 3.47 mcm dei cicli L28 |
| **4 Primo Oratore** (89–109) | 4.3 prodotto di Kronecker, `B ⊗ A ⊗ I3` L29; 4.4 le sei matrici fondamentali 3×3 `SCD_u … DCS_u`, convenzione `P e_i = e_π(i)`, CDS realizzata fisicamente da DSC L30; 4.5 rigidità della distribuzione `P_{2,i} = P_u ⊗ I ⊗ I` L31; 4.6 le sei permutazioni globali a blocchi 9×9 (Fig. 4.4) L32; 4.7 stadio `T_i = P_{2,i} ∘ MSC` L33; 4.8 identità di slittamento (S1), (S2), `T = P_{u,2} ⊗ P_{u,1} ⊗ P_{u,0}` L34; 4.9 dalla matrice agli indici, tabella di 27 righe L35; 4.10 tabellone inverso come cascata di inverse locali, unicità dell'inverso L36 |
| **5 Arkady Darell e il giullare del Mulo** (110–138) | 5.1.1–5.1.2 stadio generale `(P2⊗P1⊗P0) ∘ MSC ∘ J^ε`, formule B con indici incrociati, chiusura dopo tre stadi L37; 5.1.3–5.1.4 e 5.1.14 vincoli del gioco reale, destino asimmetrico dei rovesciamenti (parità in M2) L38; 5.1.5 flusso dinamico delle coordinate L39; 5.1.7–5.1.8 permutazioni locali vs permutazioni dei posti, **prodotto intrecciato S3 ≀ S3** L40; 5.1.9–5.1.11 costruzione e verifica del tabellone dalle tre carte di calibrazione, esempio della combinazione **82** L41; 5.1.12–5.1.13 MSC numerica `µ(n) = 9n0 + 3n2 + n1`, forma locale-globale `T_i = L_i ∘ MSC` L42; 5.1.15 auto-inversività ⟺ righe di ordine ≤ 2 L43; 5.1.16–5.1.18 classe S3³, ridondanza dinamica, assorbimento del Jester, 1 728 → 216 (8 a 1) L44; 5.2 narrativa L45 |
| **6 Sura Novi di Gaia** (139–172) | 6.1 Procedura vs Cronaca, Gaia L46; 6.2–6.3 S3 come lessico, nascita di G, fedeltà in S27, G come sottogruppo base del wreath product (indice 6) L47, L40; 6.4 convenzione di composizione L48; 6.5 tavola di Cayley 216×216 L49; 6.6–6.7 coniugio, 27 classi, tipi (f2,f1,f0), equazione delle classi L50; 6.8 punti fissi (prodotto dei locali, distribuzione 1/9/27/27/152, media 1, Burnside, transitività) L51; 6.9 centro banale L52; 6.10 **il Giullare** `J = DCS_u⊗DCS_u⊗DCS_u ∈ G`, classe (T,T,T) L53; otto cammini per Cronaca, rovesciamento accidentale non autocorretto L54; 6.11 sintesi L55 |
| **7 Il repertorio del Giullare** (173–224) | effetto/metodo/presentazione L56; **Parte A, 13 strumenti**: A1 equazione della conoscenza L57; A2 leggere e invertire, operazioni (E),(R),(I) L58; A3 ricostruire il tabellone (due assi estremi; somme per fette) L59; A4 forzare (qualunque posizione; limite di Kronecker per più carte) L60; A5 carte ferme L61; A6 periodi e forma ciclica L62; A7 mascheramento 8:1 L63; A8 mazzi gemelli L64; A9 invariante a blocchi L65; A10 parità L66; A11 localizzazione per cifre `n = a1 + 3a2 + 9a3` L67; A12 equivoque L68; A13 taglio L69. **Parte B, 15 trucchi** B1–B15 L70–L84. **Parte C** manipolazioni (glimpse, falso taglio, controlli, forzature cartomagiche) L85 |

### 4.3 Parte II — La struttura generale

| Capitolo / sezioni (pp.) | Concetti (ID) |
|---|---|
| **8 Oltre il terzo mescolamento** (226–233) | 8.1–8.4 composizione di tabelloni, tavola di composizione locale 6×6, successioni senza ripetizione (max 6 tabelloni, prodotto = trasposizione per parità), cumulativo L86; 8.5 tavola delle decomposizioni locali, passaggio Y→X L87 |
| **9 La saturazione del tabellone** (234–251) | famiglia estesa (1 728 configurazioni per stadio, 1 728³ storie), blocco effettivo con 8 rappresentazioni, Teor. 9.55 saturazione, Teor. 9.56 uniformità (46 656), Cor. 9.57 (23 887 872), disposizione #132 L88; 9.4 il gioco ordinario come famiglia vincolata (12 blocchi per stadio, 8:1 globale) L89 |
| **10 All'indietro nel tempo** (252–259) | tabellone cumulativo `C_N`, ritorno 3N→3 stadi, ricostruzione del cammino L90; ritorno mediante due carte guida da una disposizione arbitraria L91; somma delle posizioni delle guide = 39 L92; raggiungere una sequenza assegnata `w` da `v` (test di appartenenza a Gaia) L93 |
| **11 Il caso generale b^m** (260–315) | caso generale L94 (oltre 4.0); 11.7 gruppo delle trasformazioni intermedie `Γ_{3,3} ≅ S3³ ⋊ C3` (648), forma normale `h ∘ R^r`, classi laterali percorse dagli stadi L95; 11.8 reversibilità vs chiusura L96; 11.9 fibre digitali e ricostruzione (caso ternario) L97; 11.10 invarianti generali L98; 11.11 disposizione rettangolare, 21 carte, dinamica informativa L99 |
| **12 Dal gesto alla struttura tensoriale** (316–340) | realizzazione tensoriale `V27 ≅ E3^{⊗3}`, rappresentazione fedele, ortogonalità L100; 12.11 confronto con sistemi quantistici L101 |

### 4.4 Parte III — Appendici

* **A** Note di base per i calcoli (pp. 342–350): codifica, MSC, J = R⊗R⊗R, ϑ, `T = A2 ∘ ϑ(A1) ∘ ϑ²(A0)`,
  `Γ = H ⋊ C3` L102.
* **B** Base matematica del programma di manipolazione algebrica (pp. 351–362): descrive `gioco27` v3.0.3 —
  Lexer/Parser/Rewriter, `CanonicalForm`, `rotate_kron_factors`, `_collect_msc_right`,
  `normalize_with_trace`, `find_all_kron_decompositions(_parallel)`, `try_kron_decompose`, distribuzione
  46 656, risultati strutturali (ordini 1/63/26/126, 64 autoinverse, parità 108/108, 7 tipi di ciclo, punti
  fissi) L103.
* **C** La tavola delle disposizioni semplici (pp. 363–372): `# = k1 + 6k2 + 36k3`, indici P[k] e R[k],
  27 colonne del mazzo finale, sottorighe (cifre degli Assi, riga di T in minuscolo, impilamento in maiuscolo)
  L104.
* **D** Articolo originale (pp. 373–391): seconda versione dell'articolo (§ 2.2) L105.

---

## 5. Inventario dell'articolo

`Articolo.pdf`; tra parentesi quadre la numerazione dell'App. D quando differisce.

| § | Concetto | ID |
|---|---|---|
| 1 | contesto (Gergonne, radix sort, perfect shuffles) | A01 |
| 2 | modello posizionale, `val`, regola del singolo stadio `x' = ρ(r)·b^{m−1} + ⌊x/b⌋`, Prop. 2.1 ricorrenza | A02 |
| 3 | rotazione `M_m`, `T_h = (P_h ⊗ I) ∘ M_m`, Teor. 3.1 chiusura tensoriale; «M^m = I non autorizza una cancellazione formale» | A03 |
| 4 | Def. 4.1 permutazione **digitalmente separabile**, fibre `F_{i,t}`, Teor. 4.2 (quattro caratterizzazioni equivalenti, unicità dei fattori) | A04 |
| 4 | Cor. 4.3 omomorfismo iniettivo `S_b^m → S_{b^m}`; 216 su 27! | A05 |
| 5 [6] | Teor. 5.1 formula `Σ_{i,t} = C_i + b^{m−1+i} ρ_i(t)`; Cor. 5.2 sufficienza; Oss. 5.3 non-criterio [App. D: Teor. 6.4 criterio di riconoscimento] | A06 |
| 6 [7] | caso 27: `C0 = 108, C1 = 90, C2 = 36`, tabella dei valori, Es. 6.1 ricostruzione di un codice | A07a |
| 6 [7] | distinzione codice di raccolta / tabellone (esecuzione fisica vs permutazione finale) | A07b |
| 7 [8] | Prop. 7.1 `ord = mcm`, `fix = ∏ fix` | A08 |
| 7 [8] | Oss. 7.2 p(b)^m = 27 classi nel gruppo interno; nel gruppo ambiente `S_{b^m}` classi distinte possono fondersi | A09 |
| 8 [9] | catena procedura → codice → separabile → fattorizzazione; ipotesi (omogeneità, non adattività, [assenza di] rovesciamenti) | A10 |
| App. A | caso rettangolare `N = ij`, matrice di commutazione `K_{j,i}` | A11 |
| App. A | gioco delle 21 carte: mappa `F_c` molti-a-uno, insiemi `X_k` (21→7→3→1), **dinamica fisica vs dinamica informativa**, insiemi condizionati alle risposte | A12 |
| — | [App. D § 5] rovesciamento prima della distribuzione, molteplicità 2^m, formula di inversione, famiglia estesa | A13 |
| — | bibliografia | A14 |

---

## 6. Inventario del programma attuale

Censimento indipendente dalle fonti. «Livello» usa la scala del § 0 dell'incarico:
G = gesto fisico, 3 = rappresentazione ternaria, P = permutazione, M = matrice, Ci = cicli/orbite/ordine,
Gr = struttura di gruppo, S = strategie/equivalenze/proprietà.

### 6.1 Schede, finestre e strumenti

| Strumento | Cosa calcola | Cosa mostra | Cosa si manipola | Cosa spiega | Livello | Collegamenti verso altre viste |
|---|---|---|---|---|---|---|
| **Inizia qui** (`onboarding_tab`) | — | mappa in 3 passi, 4 azioni rapide, glossario di 14 voci con tooltip | pulsanti | orientamento; glossario in «parole semplici» | — | → Simulatore, preset Gioco Reale, Anteprima, Guida |
| **Filtri Stadio 0/1/2** (`filter_frame`) | conteggio live delle combinazioni | P0,P1,P2 e J0,J1,J2 per stadio, vincolo J uniformi | dropdown + checkbox, preset Gioco Reale / J uniformi / reset | tooltip per sigla; nota del livello mai vuoto (M01) | P, M (modello esteso) | → Genera (export), Analisi |
| **Anteprima** (`preview_tab`) | T di una combinazione (P,J) | Stage simbolico, forma ridotta Aᵢ con indici incrociati, T simbolica, T in 3 blocchi da 9 | 18 dropdown | — (testi di stato) | P, M | → Cicli (notifica T), export LaTeX/SVG |
| **Analisi molteplicità** (`analysis_tab`, `services/analisi`) | raggruppa per T le sequenze del dominio filtrato | tabella Molt./T/prima T simbolica; pannello con tutte le sequenze (P,J) | selezione riga, link | banner | P, S (molteplicità) | → Explorer (doppio clic / link) ; export CSV/Excel/HTML |
| **Explorer** (`explorer_tab`, `core/algebra`) | parsing, riscrittura, forma normale, forma canonica K∘MSC^k, T e T⁻¹, periodo, firma | 7 sotto-schede: Numerico, Traccia riscrittura, Forma algebrica, Passi parziali, Forma canonica, Matrice 27×27 (T, T⁻¹ + fattori 3×3 + alternativa testuale H2), Mescolamento | espressione testuale | traccia delle regole (appiattimento, trasporto di MSC, riduzione, fusione) | P, M, Gr (Γ) | → Cicli, Decomposizioni, Protocollo, Mescolamento, Presentazione; export LaTeX/SVG |
| **Mescolamento animato** (`gui/shuffle`, `core/espressione`) | traccia passo-passo dall'AST unico (E) | mazzo come griglia 9×3 e vettore; vettore T⁻¹; celle cambiate | play/step/velocità, modalità carta-per-carta | legenda | G (astratto), P | ← Explorer («Carica da Explorer»); nessun ritorno |
| **Simulatore** (`simulator_tab`, `core/gioco_reale`) | `risolvi_trucco(carta, bersaglio)` in forma chiusa | istruzioni (mescolamento + impilamento, avviso Prima Crisi), 7 fotografie del mazzo, numero della disposizione | carta, bersaglio; slider delle fasi | testo delle istruzioni | G, 3 (implicito), P | → Cicli e Presentazione (notifica T) |
| **Pratica** (sotto-scheda del Simulatore) | confronto risposta/atteso | colonne con la carta nascosta, log, riepilogo con voto | clic sulla colonna, scelta dell'impilamento | messaggio d'errore; errore «Seldon» riconosciuto | G | — |
| **Tavola 216** (`tavola_tab`) | `tavola_216`, `tabellone_da_assi` | 216 righe: #, mescolamenti, impilamenti, Assi, periodo, punti fissi, tipo ciclico, parità, auto-inversa | filtro testuale live, ricostruzione da 3 posizioni degli Assi, doppio clic → T/T⁻¹ | banner, guida s11 | G, P, Ci | nessun collegamento in uscita (isolata) |
| **Cicli e ordine** (`cycles_tab`, `core/analysis`) | decomposizione in cicli, ordine, tipo, orbite | riepilogo, cicli colorati, orbita di una carta | scelta della carta | banner | Ci | ← Explorer, Anteprima, Simulatore |
| **Distribuzione** (`distribution_tab`) | per ogni T raggiungibile, numero di terne (A0,A1,A2) | istogramma (+ alternativa testuale H2), tabella | pulsante Calcola | guida s21 (uniformità, 216³) | Gr, S | nessuno (vista globale per contratto M03) |
| **Decomposizioni** (`decomposition`, `core/kronecker`, `core/cache`) | tutte le 46 656 terne per T o T⁻¹ | albero A0→A1→A2 o tabella | scelta T/T⁻¹ | — | Gr, S | → Explorer (clic) |
| **Tavola di Cayley** (`cayley_dialog`, `core/group_theory`) | prodotti in G, inversi, commutatore, potenze, ⟨A,B⟩ | calcolatore, tavola 216×216 (CSV/HTML/heatmap SVG/TikZ) | scelta di A, B | guida s23 | Gr | nessuno verso le altre viste |
| **Classi di coniugio** (`conjugacy_dialog`) | 27 classi, centro | classi con tipo per fattore (identità/trasposizione/3-ciclo), dimensione, ordine; elementi | selezione classe | guida s22 | Gr | nessuno verso le altre viste |
| **Presentazione / vista esecutore** (`presentation`) | riconoscimento di una disposizione semplice | un gesto per passo (impilamento), finale con gli Assi | frecce/spazio, F11 | riga matematica in basso | G | ← Simulatore, Explorer |
| **Protocollo** (`protocol_dialog`) | istruzioni per stadio, tabella delle 27 destinazioni | HTML stampabile in 8 sezioni (sintesi, legenda, fasi f3/f2/f1, verifica, cicli, T/T⁻¹, matrice, «perché funziona») | scelta delle sezioni | sì (sezione didattica) | G, P, Ci | ← Explorer |
| **Genera… (export)** (`export_dialog`, `core/export_*`, `detail_pdf`) | CSV/PDF/PDF dettagliato «stile C» fino a 20 M elementi | matrici, mazzi con semi, **tabellone di T e di T⁻¹** (solo nel PDF dettagliato) | filtri | note di fuori-gioco | P, M | — |
| **Guida** (`guide.py`) | — | 33 sezioni | navigazione per chiave | sì | tutti | ← banner di ogni scheda |
| **Verifica / selftest** (`gioco_reale.selftest`) | fisica↔algebra (216), fisica↔matrici (1 728), ancore #100/#82, statistiche, ricostruzione Assi (216), trucco (729) | rapporto localizzato | pulsante | guida s29 | P, M | — |

### 6.2 Servizi e core che sostengono il comportamento

* `core/gioco_reale.py` — modello fisico canonico (mescolamento vs impilamento, rovesciamento dopo la
  raccolta), simulazione carta-per-carta, tavola, Assi, statistiche, `risolvi_trucco`, selftest.
* `core/permutations.py`, `core/constants.py`, `core/kronecker.py` — PERM3/GEN3, MSC, matrici, tabelle dei 216
  prodotti di Kronecker, `appartiene_a_G`, `appartiene_a_H` (648), ricerca delle decomposizioni.
* `core/algebra.py` — Lexer/Parser/Rewriter/Evaluator/Controller, `CanonicalForm`, `NormalFormInfo`,
  `normalize_with_trace` (l'unico parser autorevole, E).
* `core/group_theory.py` — `GroupData`: Cayley, inversi, ordini, classi, centro, export CSV.
* `core/analysis.py` — cicli, ordine, orbite, tipo, distribuzione.
* `core/espressione.py` — traccia di esecuzione per il mescolamento animato (AST unico, E).
* `core/detail.py`, `core/detail_pdf.py` — dati del PDF dettagliato (settori ternari degli Assi, tabelloni).
* `services/analisi.py`, `services/modelli.py`, `services/lavoro.py` — caso d'uso dell'analisi, modelli di
  risultato, revisioni dei lavori (G).

### 6.3 Ciò che il core calcola ma nessuna vista espone

Rilevati durante il censimento [CODICE]:

* `appartiene_a_G`, `appartiene_a_H` — solo core e test: nessuna vista permette di chiedere «questa
  permutazione arbitraria appartiene a G/Γ?» (l'Explorer accetta solo espressioni simboliche);
* `tabellone_da_assi` accetta tre posizioni; la ricostruzione con **due** Assi del libro (A3, B10, § 10.2.1) non
  è esposta;
* `riga_tavola` contiene `T_inv` e gli impilamenti, ma il **tabellone** come griglia 3×3 (diretto e inverso)
  compare solo nel PDF dettagliato;
* `risolvi_trucco` calcola le colonne attese (`colonne`), cioè la storia delle distribuzioni = cifre
  dell'indirizzo iniziale rovesciate (Prop. 1.6): il dato è usato dalla pratica ma non è mai presentato come tale;
* il selftest verifica 729 coppie carta/bersaglio, ma per ciascuna coppia il solutore restituisce **una** delle
  **otto** sequenze possibili senza mostrarle (§ 13).

---

## 7. Matrice fonte → programma

Stessa matrice di `V4_COVERAGE_MATRIX.csv` (separatore `;`, UTF-8). Colonne C/V/I/D: `sì`, `parz.`, `no`, `n.a.`. Evidenza: CODICE, TEST, UI, DOC, ESEC (§ 12); le sigle «baseline M1…M13» rimandano ai controlli numerati in `GIT_BASELINE_AND_RECONCILIATION.md` § 7, oggi realizzati dai test di `tests/test_baseline_matematica.py` (per esempio M5 = `test_g_chiuso_e_tavola_di_cayley_corretta`, M11 = `test_bersaglio_in_g_ha_46656_decomposizioni_uniche`). Priorità secondo il § 31 (`—` = nessun gap da colmare).

| ID | Fonte | Posizione fonte | Concetto | Obiettivo matematico | Obiettivo didattico | C | V | I | D | Stato | Evidenza programma | Gap | Pri. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L01 | Libro | «Le carte prima della Psicostoria» pp.2-10; Prologo | Storia del trucco a pile (Pacioli, Verini, Galasso, Gergonne, Gardner, Elmsley); 21 vs 27 | — | contesto culturale | n.a. | n.a. | n.a. | n.a. | NON APPLICABILE | DOC: la Guida non contiene parte storica | eventuale nota editoriale nella guida | P3 (editoriale) |
| L02 | Libro | pp.5-7 | Problema diretto vs problema inverso (Gergonne): prevedere vs prescrivere la destinazione | T da una sequenza; sequenza da (carta, bersaglio) | distinguere previsione e costruzione | sì | sì | sì | parz. | PARZIALE | CODICE: gioco_reale.T_da_tabellone, risolvi_trucco; UI: Anteprima/Tavola (diretto), Simulatore (inverso); DOC: guide.s19 | la distinzione non è nominata né collegata fra le viste | V4-P2 |
| L03 | Libro | pp.7-8; A13; B4 | 27 = 3³ come codifica della destinazione; ACAAN (qualunque carta a qualunque numero) | ogni bersaglio 0..26 raggiungibile | dal numero nominato alla posizione n−1 | sì | sì | sì | parz. | PARZIALE | CODICE: risolvi_trucco (729/729); UI: Simulatore; TEST: test_gioco_reale | n-esima carta = posizione n−1 non spiegata; taglio assente (L69) | V4-P2 |
| L04 | Libro | §1.1-1.2 | Divisione con resto P = 3q + r: resto = mazzetto, quoziente = altezza interna; etichette dei mazzetti per ordine di generazione | decomposizione di una posizione | leggere il gesto della distribuzione come aritmetica | sì | parz. | parz. | no | PARZIALE | CODICE: gioco_reale.distribuisci; UI: Simulatore (7 fotografie) | nessuna vista annota q e r sulle carte distribuite | V4-P1 |
| L05 | Libro | §1.3, Prop.1.1, es. 19 | Indirizzo ternario unico n = 9n2 + 3n1 + n0 | biiezione {0..26} ↔ {0,1,2}³ | vedere le tre cifre di una posizione | sì | parz. | no | parz. | PARZIALE | CODICE: gioco_reale.digits3; UI: Anteprima (T in 3 blocchi da 9); PDF dettagliato (settore ternario); DOC: guide.s02 | nessun convertitore interattivo numero ↔ terna ↔ parola | V4-P1 |
| L06 | Libro | §1.4, Fig.1.1 | Gerarchia 27 → 9 → 3 → 1 (blocco, terzina, posto); griglia 3×3×3 | struttura gerarchica delle posizioni | localizzare per livelli | sì | parz. | no | parz. | PARZIALE | UI: linee di separazione ogni 3/9 nella matrice (Explorer, PDF); DOC: guide.s02 | nessuna vista gerarchica o cubica delle posizioni | V4-P1 |
| L07 | Libro | §1.5.2, §1.8 | Codifica ω: posizione ↔ parola in {S,C,D}³ (19 = DSC); ordine lessicografico; «il nome è già la tabella» | isomorfismo con parole | usare le stesse lettere per indirizzi e gesti | parz. | parz. | no | no | PARZIALE | CODICE: detail.num_to_sector (solo PDF); UI: PDF dettagliato | assente in GUI e in guida | V4-P1 |
| L08 | Libro | §1.6 | «La macchina che dimentica»: P_{k+1} = ⌊P_k/3⌋ + 9·s_k; P3 = 9s2 + 3s1 + s0 | indipendenza del finale dalla posizione iniziale | capire perché il trucco funziona | sì | parz. | parz. | parz. | PARZIALE | CODICE: gioco_reale.esegui_partita, risolvi_trucco; UI: Simulatore; DOC: simulator.instructions.placeholder (una frase) | la ricorrenza non è mostrata passo per passo | V4-P0 |
| L09 | Libro | §1.7 | Flusso delle cifre: (n2,n1,n0) → (s0,n2,n1) → (s1,s0,n2) → (s2,s1,s0) | registro a scorrimento | vedere uscire l'origine ed entrare la destinazione | sì | no | no | no | ASSENTE | CODICE: implicito in gioco_reale | nessuna visualizzazione | V4-P0 |
| L10 | Libro | §1.9, Prop.1.6 | Storia delle distribuzioni = rev ω(n), indipendente dalle raccolte; storia delle raccolte → indirizzo finale | dualità tempo/spazio delle cifre | leggere l'origine nel tempo e scrivere la destinazione | sì | parz. | parz. | no | PARZIALE | CODICE: risolvi_trucco()['colonne']; UI: istruzioni del Simulatore, Pratica (chiede la colonna) | non è detto che le colonne osservate sono n0,n1,n2 dell'origine | V4-P1 |
| L11 | Libro | §1.10, Prop.1.7-1.8 | Somme dei blocchi 36/117/198 come firma; elemento mancante | invarianti additivi dei blocchi | riconoscere famiglie senza ordine | no | no | no | no | ASSENTE | — | firme dei blocchi e ricostruzione dell'elemento mancante assenti | V4-P1 |
| L12 | Libro | §1.10.1 | Configurazione finale come archivio stratificato (blocchi ↔ ultimo passaggio …) | lettura gerarchica del mazzo finale | leggere la storia nel risultato | parz. | no | no | no | ASSENTE | CODICE: kronecker.try_kron_decompose legge i fattori dai blocchi (non esposto come lettura) | nessuna lettura guidata del mazzo finale | V4-P1 |
| L13 | Libro | §1.11, Prop.1.10-1.12 | Completezza dei blocchi; regola di completamento (due simboli determinano il terzo) | struttura prodotto | ridondanza come controllo | parz. | no | no | no | ASSENTE | CODICE: tabellone_da_assi verifica che ogni riga sia una permutazione | regola non esposta | V4-P2 |
| L14 | Libro | §2.1-2.2, Prop.2.14-2.15 | Carte vs posizioni vs trasformazioni; configurazione f: X→C; π(i)=j | distinguere mazzo e mappa | non confondere carta e posto | sì | parz. | parz. | parz. | PARZIALE | CODICE: convenzioni T/deck (TEST test_perm_matrix_convention); UI: Mescolamento (vettore mazzo e vettore T⁻¹); DOC: guide.s17-s18 | manca una vista che affianchi mazzo (posizione→carta) e T (carta→posizione) | V4-P1 |
| L15 | Libro | §2.2.2; §7.1 «la fisica della distribuzione» | Convenzioni fisiche: dorso in alto, posizione 0 in cima, distribuzione ciclica S,C,D, prime carte in basso nel mazzetto | modello fisico univoco | eseguire correttamente il gesto | sì | sì | parz. | parz. | PARZIALE | CODICE: gioco_reale (docstring del modello); UI: fotografie del Simulatore; DOC: guide.s01 | la griglia 9×3 del Mescolamento (indice c·9+r) usa una disposizione diversa dalla distribuzione fisica (colonna = p mod 3) senza dichiararlo; guide.s01 non fissa dorso/cima/ordine interno | V4-P1 |
| L16 | Libro | §2.2.3, Oss.2.18-2.19 | Mazzo di riferimento A–K♠, A–K♣, A♥; Assi nelle posizioni diagonali 0, 13, 26 | carte guida sulla diagonale ternaria | seguire tre testimoni | sì | sì | sì | sì | COMPLETO | CODICE: riga_tavola['assi']; UI: Tavola, PDF dettagliato (semi reali); DOC: guide.s11, s27; TEST: test_gioco_reale::test_ancore_libro | — | — |
| L17 | Libro | §2.3, Oss.2.20-2.21 | S_n, n!; le sei raccolte come S3 | gruppo simmetrico locale | sei scelte possibili | sì | sì | sì | sì | COMPLETO | CODICE: constants.PERM3; UI: legenda GEN3, tooltip; DOC: guide.s04, glossario | — | — |
| L18 | Libro | §2.4.1-2.4.4, §2.4.7 | Tabellone generatore: righe = mescolamenti (ultimo in alto); lettura gerarchica → mazzo finale; colonne = destino degli Assi | T come terna (B2,B1,B0) | il tabellone come oggetto operativo | sì | parz. | parz. | parz. | PARZIALE | CODICE: gioco_reale.T_da_tabellone; UI: Tavola (sigle + Assi), griglia solo nel PDF dettagliato; DOC: guide.s11, s27 | nessuna vista 3×3 interattiva del tabellone (diretto/inverso) né lettura «contachilometri» | V4-P0 |
| L19 | Libro | §2.4.5, Oss.2.23; nota 11 (righe 62/56) | Prima crisi di Seldon: mescolamento vs impilamento, CDS↔DSC; tabellone diretto vs inverso | inversione locale | errore classico e sua correzione | sì | sì | sì | sì | COMPLETO | CODICE: IMPILAMENTO_DI; UI: istruzioni del Simulatore, Pratica (errore «Seldon»), Tavola; DOC: glossary.long.stacking, guide.s10; TEST: test_gioco_reale, test_tabellone_inverso; ESEC: righe 62 (4,24,11) e 56 (7,18,14) | la lettura speculare delle colonne del tabellone inverso (quale carta arriva in 0,13,26) è solo nel PDF dettagliato | V4-P2 |
| L20 | Libro | §2.4.6, §2.4.8 «ricetta per ordinamento delle somme» | Ricostruzione dei mescolamenti dalle somme (blocchi → riga alta, terzine → riga media; il livello fine richiede l'ordine) | invarianti di somma, limite strutturale | leggere la storia senza seguire le carte | no | no | no | no | ASSENTE | — | metodo assente | V4-P1 |
| L21 | Libro | §2.4.7, Prop.2.28 | «Tre leggi delle posizioni»: T(n2,n1,n0) = (B2(n2),B1(n1),B0(n0)) | azione cifra per cifra | leggere una destinazione riga per riga | sì | parz. | parz. | sì | PARZIALE | CODICE: T_da_tabellone; UI: fattori 3×3 sotto la matrice, forma canonica; DOC: guide.s02, s08 | nessuna lettura cifra-per-cifra di una posizione | V4-P1 |
| L22 | Libro | §2.4.8 | Ricostruzione del tabellone dal vettore finale (scale 9 → 3 → 1) e orientazione | decodifica gerarchica | dal mazzo alla storia | parz. | parz. | parz. | no | PARZIALE | CODICE: try_kron_decompose, tabellone_da_assi; UI: Explorer (solo espressioni), Tavola (3 Assi) | non si può inserire un mazzo finale e decodificarlo | V4-P1 |
| L23 | Libro | §2.5 | Seconda crisi: il rovesciamento globale J è assorbito nel tabellone | J non esce da G | l'intruso rientra nei ranghi | sì | parz. | parz. | parz. | PARZIALE | CODICE: permutations.compute_T_full, selftest 1b (1 728); UI: Filtri/Anteprima ammettono J; PDF dettagliato (nota); DOC: guide.s27 | Simulatore e Tavola senza rovesciamenti; nessun confronto procedura con J ↔ tabellone equivalente | V4-P1 |
| L24 | Libro | §3.1-3.2.1 | Combinazioni lineari, sistema lineare, matrice dei coefficienti, prodotto matrice–vettore; P_{i,j}=1 ⟺ π(j)=i | linguaggio matriciale | trattare il mazzo come stato | sì | sì | parz. | parz. | PARZIALE | UI: Explorer › Matrice (T, T⁻¹), PDF; DOC: guide.s17 | l'applicazione matrice–vettore al mazzo non è mostrata | V4-P2 |
| L25 | Libro | §3.2.2, Prop.3.37-3.39 | Biiezione permutazioni ↔ matrici; P(π∘ρ) = P(π)·P(ρ) | omomorfismo | composizione = prodotto | sì | parz. | parz. | parz. | PARZIALE | TEST: test_baseline_matematica M4; UI: calcolatore di Cayley (senza matrici) | nessuna verifica visiva del prodotto di matrici | V4-P2 |
| L26 | Libro | §3.2.3, Oss.3.44 | Trasposta = inversa; simmetriche ↔ involuzioni; CDS^T = DSC spiega la Prima Crisi | ortogonalità | la crisi come teorema | sì | sì | parz. | parz. | PARZIALE | UI: T e T⁻¹ affiancate (Explorer), «Elenco matrici trasposte» (PDF); DOC: guide.s17 | il legame trasposizione ↔ Prima Crisi non è fatto | V4-P1 |
| L27 | Libro | §3.2.4 | Simulazione concreta vs modello matriciale (concordanza) | due livelli, stessa dinamica | fiducia nel modello | sì | sì | sì | sì | COMPLETO | CODICE: gioco_reale.selftest; UI: pulsante Verifica; DOC: guide.s29; TEST: test_dominio_selftest, baseline M8 | — | — |
| L28 | Libro | §3.2.5, Prop.3.45-3.47 | Periodo = ordine = mcm delle lunghezze dei cicli | dinamica iterata | quando il mazzo torna | sì | sì | sì | sì | COMPLETO | CODICE: analysis.order_of; UI: Cicli; DOC: guide.s20, glossario; TEST: baseline M13 | — | — |
| L29 | Libro | §4.3, Fig.4.2-4.3 | Prodotto di Kronecker A⊗B, B⊗A⊗I3 | costruzione a blocchi | la complessità è distribuita | sì | parz. | parz. | parz. | PARZIALE | UI: linee di blocco e fattori 3×3 (Explorer); DOC: glossario | nessuna costruzione visiva di A⊗B | V4-P2 |
| L30 | Libro | §4.4, Oss.4.49 | Le sei matrici 3×3 SCD_u … DCS_u; P e_i = e_π(i); CDS si realizza fisicamente con DSC | operatori locali | dalla sigla alla matrice | sì | sì | sì | sì | COMPLETO | UI: fattori 3×3 (Explorer, PDF); DOC: guide.s04; TEST: test_perm_matrix_convention | — | — |
| L31 | Libro | §4.5 | Rigidità della distribuzione: P_{2,i} = P_u ⊗ I ⊗ I | un solo fattore libero | perché il gioco reale ha 6 scelte | sì | sì | sì | sì | COMPLETO | UI: preset Gioco Reale, Filtri; DOC: guide.s04, s10 | — | — |
| L32 | Libro | §4.6, Fig.4.4 | Le sei permutazioni globali come matrici a blocchi 9×9 | geometria dei blocchi | vedere la raccolta come matrice | sì | parz. | parz. | no | PARZIALE | UI: ottenibili digitando l'espressione nell'Explorer | nessun catalogo visivo delle sei matrici globali | V4-P3 |
| L33 | Libro | §4.7 | Stadio T_i = P_{2,i} ∘ MSC (distribuzione ≠ raccolta) | scomposizione dello stadio | separare i due gesti | sì | sì | sì | sì | COMPLETO | UI: Anteprima (Stage simbolico), Mescolamento (MSC e Kron come passi distinti); DOC: guide.s06 | — | — |
| L34 | Libro | §4.8 | Identità di slittamento (S1),(S2); T = P_{u,2} ⊗ P_{u,1} ⊗ P_{u,0} | tempo → struttura | perché dopo tre stadi i fattori si separano | sì | sì | sì | sì | COMPLETO | CODICE: algebra._collect_msc_right, normalize_with_trace; UI: Explorer › Traccia riscrittura; DOC: guide.s07-s08; TEST: baseline M6, test_linguaggio_espressioni_e | — | — |
| L35 | Libro | §4.9, esempio 4.9.1 | Dalla matrice agli indici: n → (n2,n1,n0) → Π(n) → n' (tabella di 27 righe) | legge sugli indici | calcolo a mano della destinazione | sì | parz. | no | parz. | PARZIALE | UI: Explorer › Numerico (solo la lista) | nessuna tabella ternaria posizione per posizione | V4-P1 |
| L36 | Libro | §4.10 | Tabellone inverso come cascata di inverse locali nello stesso ordine temporale; unicità dell'inverso | inversione strutturale | tornare indietro capendo perché | sì | sì | sì | parz. | PARZIALE | UI: Tavola (T⁻¹), Explorer (T⁻¹, Decomposizioni T⁻¹); DOC: guide.s17 (formula) | la procedura di ritorno come tre raccolte (operazione R del cap.7) non è offerta né spiegata | V4-P1 |
| L37 | Libro | §5.1.1-5.1.2 | Stadio generale (P2⊗P1⊗P0) ∘ MSC ∘ J^ε; formule B con indici incrociati; chiusura dopo tre stadi | modello esteso | perché gli indici si incrociano | sì | sì | sì | sì | COMPLETO | CODICE: compute_Ai_symbolic; UI: Anteprima (forma ridotta Aᵢ); DOC: guide.s08; TEST: test_core | — | — |
| L38 | Libro | §5.1.3-5.1.4, §5.1.14 | Vincoli del gioco reale; formule M con R; destino asimmetrico dei rovesciamenti (parità in M2) | effetto dei rovesciamenti per livello | il Mulo sparisce dalla riga alta | sì | parz. | parz. | no | PARZIALE | CODICE: compute_T_full | la regola di parità dei rovesciamenti non è esposta | V4-P2 |
| L39 | Libro | §5.1.5 | Flusso dinamico delle coordinate nello stadio (R^ε, MSC, P) | traiettorie dei fattori | vedere il processo, non solo l'esito | sì | no | no | no | ASSENTE | CODICE: implicito | diagramma di flusso assente | V4-P1 |
| L40 | Libro | §5.1.7-5.1.8, §6.3.1 | Permutazioni locali vs dei posti; prodotto intrecciato S3≀S3 (1 296); G = sottogruppo base, nucleo di φ, indice 6 | perché G è un prodotto diretto | due livelli intrecciati | no | no | no | no | ASSENTE | — (il programma realizza Γ = G⋊C3, non S3≀S3) | assente | V4-P2 |
| L41 | Libro | §5.1.9-5.1.11 | Costruzione e verifica del tabellone dalle tre carte di calibrazione; esempio della combinazione 82 | T da tre immagini | ricostruire da pochi testimoni | sì | sì | sì | sì | COMPLETO | CODICE: tabellone_da_assi; UI: Tavola › ricostruzione; DOC: guide.s11; TEST: test_tabellone_inverso, selftest (216/216); ESEC: #82 → (10,8,21) | la variante a due Assi è in L59 | — |
| L42 | Libro | §5.1.12-5.1.13 | MSC numerica µ(n) = 9n0 + 3n2 + n1; operatori Π_π; forma locale-globale T_i = L_i ∘ MSC | MSC come permutazione dei posti | separare scelta e meccanismo fisso | sì | parz. | parz. | parz. | PARZIALE | CODICE: permutations.MSC; DOC: guide.s03 | la forma µ(n) e la scrittura L_i∘MSC non sono mostrate | V4-P2 |
| L43 | Libro | §5.1.15, Prop.5.53 | T auto-inversa ⟺ ogni riga del tabellone ha ordine ≤ 2 (64 casi) | criterio sul tabellone | leggere l'involuzione a occhio | sì | sì | sì | no | PARZIALE | UI: Tavola (colonna auto-inversa, filtro); CODICE: statistiche_tavola (64) | criterio non spiegato | V4-P2 |
| L44 | Libro | §5.1.16-5.1.18 | Classe S3³ delle trasformazioni finali; ridondanza dinamica; assorbimento del Jester; 1 728 → 216 (8 a 1) | molteplicità uniforme | il Giullare moltiplica le vie, non le mete | sì | sì | sì | parz. | PARZIALE | UI: Analisi (Molt. = 8 sul preset Gioco Reale); DOC: guide.s09, s16; ESEC: 1 728 procedure → 216 T, fibre tutte di 8 | formule di assorbimento e composizione della fibra (2³ scelte di rovesciamento) non esposte | V4-P1 |
| L45 | Libro | §5.2 | «I previsti imprevisti» (narrativa) | — | cornice narrativa | n.a. | n.a. | n.a. | n.a. | NON APPLICABILE | — | — | — |
| L46 | Libro | cap.6 intro, §6.1; Notazioni pp.xi-xii | Procedura (esecuzione fisica) vs Cronaca (trasformazione indotta); Gaia; Mondo-di-Mazzo | relazione molti-a-uno procedura → T | nominare ciò che coincide e ciò che differisce | sì | parz. | parz. | no | PARZIALE | UI: Analisi (sequenze vs T) | termini assenti da guida e glossario | V4-P1 |
| L47 | Libro | §6.2-6.3 | S3 come lessico; nascita di G (216) come biiezione terne ↔ G senza rovesciamenti; fedeltà in S27 | 216 permutazioni distinte | isola finita dentro 27! | sì | sì | sì | parz. | COMPLETO | CODICE: kronecker._build_kron_table; UI: Tavola; DOC: guide.s09; TEST: baseline M5 | il confronto 216 vs 27! ≈ 1,09·10²⁸ non compare | V4-P3 |
| L48 | Libro | §6.4 | Convenzione di composizione A∘B = prima B | ordine di lettura | non commutatività | sì | sì | sì | sì | COMPLETO | DOC: guide.s06; UI: Cayley (A∘B e B∘A) | — | — |
| L49 | Libro | §6.5, Fig.6.7 | Tavola di Cayley 216×216; chiusura | memoria delle composizioni | tutte le composizioni restano in G | sì | sì | sì | parz. | COMPLETO | CODICE: GroupData.cayley; UI: dialogo Cayley, heatmap SVG/TikZ; DOC: guide.s23, s32; TEST: baseline M5 (46 656 coppie) | — | — |
| L50 | Libro | §6.6-6.7, Fig.6.8-6.9 | Coniugio; 27 classi con tipo per fattore (I,T,C); cardinalità e ordini; equazione delle classi | classificazione | dagli individui alle famiglie | sì | sì | parz. | parz. | COMPLETO | CODICE: GroupData.classes, conjugacy_dialog._class_type; UI: dialogo Coniugio, griglia e istogramma SVG; DOC: guide.s22 | regola «cardinalità = prodotto delle locali» non spiegata | V4-P3 |
| L51 | Libro | §6.8 | Punti fissi = prodotto dei locali; distribuzione 27/9/3/1/0 = 1/9/27/27/152; media 1; Burnside; transitività | conteggi strutturali | perché mai 2 o 25 carte ferme | sì | parz. | parz. | no | PARZIALE | CODICE: statistiche_tavola; UI: Tavola (colonna), Cicli; DOC: guide.s09 («azione transitiva», senza spiegazione) | regola del prodotto, media e Burnside assenti | V4-P2 |
| L52 | Libro | §6.9 | Centro banale Z(G) = {e} | struttura | nessun comando nascosto | sì | sì | n.a. | sì | COMPLETO | CODICE: GroupData.center; UI: Coniugio; DOC: glossario | — | — |
| L53 | Libro | §6.10, Fig.6.11 | Il Giullare J = DCS_u ⊗ DCS_u ⊗ DCS_u ∈ G, classe (T,T,T), un solo punto fisso (13) | J come elemento di G | l'imprevisto è una forma | sì | parz. | parz. | parz. | PARZIALE | UI: calcolabile nell'Explorer; DOC: guide.s05 («nomi doppi R_U / DCS_U») | J non è presentato come elemento di G | V4-P2 |
| L54 | Libro | §6.10 | Otto cammini per Cronaca (2³ scelte di rovesciamento); un rovesciamento accidentale non è autocorretto | fibra dell'otto-a-uno | errore vs realizzazione equivalente | sì | parz. | parz. | no | PARZIALE | UI: pannello sequenze dell'Analisi; ESEC: ogni classe ha profilo di rovesciamenti (0,1,1,1,2,2,2,3) | nessuna vista della fibra né delle conseguenze di un rovesciamento accidentale | V4-P1 |
| L55 | Libro | Introduzione; §6.11 | Progressione gesto → procedura → trasformazione → struttura | — | percorso didattico a livelli | n.a. | parz. | parz. | parz. | PARZIALE | UI: Inizia qui (3 passi), modalità principiante; DOC: guide.s25, s31 | la progressione del libro non guida la distribuzione degli strumenti (§ 28) | V4-P1 |
| L56 | Libro | cap.7 intro | Effetto / metodo / presentazione | — | grammatica del prestigiatore | n.a. | n.a. | n.a. | n.a. | NON APPLICABILE | UI: la Presentazione copre il lato esecutivo | eventuale testo in guida | V4-P3 |
| L57 | Libro | §7.1.1 (A1) | Equazione della conoscenza: finale = P · iniziale; note due, si calcola la terza | inversione di una relazione | scegliere cosa l'esecutore conosce | sì | parz. | parz. | no | PARZIALE | UI: Explorer (da espressione), Tavola | nessuno strumento con mazzi reali (iniziale, finale) → P | V4-P1 |
| L58 | Libro | §7.1.2 (A2) | Leggere e invertire; lettura «contachilometri»; operazioni (E) eseguire, (R) realizzare un tabellone, (I) invertire | uso operativo del tabellone | dal tabellone al gesto | sì | parz. | parz. | parz. | PARZIALE | UI: Tavola (T, T⁻¹), Presentazione = (E); DOC: guide.s10 (regola CDS↔DSC) | (R) «realizza questo tabellone / torna indietro» assente | V4-P1 |
| L59 | Libro | §7.1.3 (A3); B10 | Ricostruire il tabellone con due Assi estremi (0, 26) e controllo a_i ≠ b_i; oppure per somme B2(a) = (S_a−36)/81 … | ricostruzione minima | bastano due testimoni | parz. | sì | sì | parz. | PARZIALE | CODICE: tabellone_da_assi (tre posizioni); UI: Tavola | versione a due Assi e metodo per somme assenti | V4-P1 |
| L60 | Libro | §7.1.4 (A4); B14 | Forzare: qualunque posizione (cifre rovesciate); limite di Kronecker per più carte | vincoli di forzatura multipla | libertà e suoi limiti | parz. | sì | sì | parz. | PARZIALE | CODICE: risolvi_trucco (una carta); UI: Simulatore | compatibilità di più forzature simultanee assente | V4-P2 |
| L61 | Libro | §7.1.5 (A5); B3 | Carte ferme: solo 0,1,3,9,27 con frequenze 152/27/27/9/1 | vincolo strutturale | predizione dei punti fissi | sì | sì | sì | no | PARZIALE | UI: Tavola (colonna e filtro); ESEC: statistiche_tavola | il perché del vincolo non è spiegato (vedi L51) | V4-P2 |
| L62 | Libro | §7.1.6 (A6); B11 | Periodi 1/2/3/6 (1/63/26/126); 64 auto-inverse; 7 firme cicliche (#100 condivisa da 72 disposizioni) | ordine e forma ciclica | il mazzo come orologio | sì | sì | sì | sì | COMPLETO | CODICE: statistiche_tavola; UI: Cicli, Tavola; TEST: test_gioco_reale::test_statistiche_capitolo_100; ESEC: 7 tipi, 72 | — | — |
| L63 | Libro | §7.1.7 (A7) | Mascheramento: 1 728 procedure → 216 Cronache (8 : 1) | ridondanza | lo stesso trucco con mani diverse | sì | sì | sì | parz. | PARZIALE | vedi L44 | vedi L44 | V4-P1 |
| L64 | Libro | §7.1.8 (A8); B8, B9 | Due mazzi gemelli: T_B ∘ T_A⁻¹ | traduzione fra mazzi | coincidenze | parz. | no | no | no | ASSENTE | UI: componibile nel calcolatore di Cayley come A∘B⁻¹ (non come mazzi) | non modellato | V4-P3 |
| L65 | Libro | §7.1.9 (A9); B6 | Invariante a blocchi: i nonetti restano compatti | conservazione strutturale | «acqua e olio» | sì | parz. | no | no | ASSENTE | UI: struttura a blocchi della matrice | nessuna visualizzazione dei nonetti | V4-P2 |
| L66 | Libro | §7.1.10 (A10); B13 | Parità: segno = prodotto dei segni delle righe; 108/108 | segno di una permutazione | rete di sicurezza | sì | sì | sì | no | PARZIALE | UI: Tavola (parità), Explorer (firma); CODICE: parita | regola non spiegata | V4-P2 |
| L67 | Libro | §7.1.11 (A11); B1 | Localizzazione per cifre: le tre risposte di pila danno n = a1 + 3a2 + 9a3 | informazione ternaria delle risposte | lo spettatore «detta» le cifre | no | no | no | no | ASSENTE | — | assente (vedi § 14 e § 18, spettatore senza carta nota) | V4-P0 |
| L68 | Libro | §7.1.12 (A12) | Equivoque | — | tecnica scenica | n.a. | n.a. | n.a. | n.a. | NON APPLICABILE | — | — | — |
| L69 | Libro | §7.1.13 (A13) | Taglio: traslazione mod 27, fuori da G | mossa non appartenente al gruppo | dalla posizione al numero contato | no | no | no | no | ASSENTE | — (il linguaggio non ha un atomo di taglio) | assente | V4-P2 |
| L70 | Libro | §7.2 B1 | B1 Localizzazione (tre risposte → carta) | applicazione di uno strumento A | effetto scenico dal metodo | no | no | no | no | ASSENTE | — | dipende da L67 | V4-P0 |
| L71 | Libro | §7.2 B2 | B2 Mazzo memorizzato (posizione ↔ carta con T, T⁻¹) | applicazione di uno strumento A | effetto scenico dal metodo | sì | parz. | parz. | no | PARZIALE | UI: Tavola (dettaglio T/T⁻¹); ESEC: #100 posizione 20 ← carta 25, carta 2 → 12 | nessuna domanda «carta ↔ posizione» interattiva | V4-P2 |
| L72 | Libro | §7.2 B3 | B3 Predizione dei punti fissi | applicazione di uno strumento A | effetto scenico dal metodo | sì | parz. | parz. | no | PARZIALE | UI: Tavola filtrabile; ESEC: #7 → 0, 9, 18 | — | V4-P2 |
| L73 | Libro | §7.2 B4 | B4 Forzatura / ACAAN | applicazione di uno strumento A | effetto scenico dal metodo | sì | parz. | parz. | no | PARZIALE | UI: Simulatore | n-esima carta e taglio assenti | V4-P2 |
| L74 | Libro | §7.2 B5 | B5 Trasposizione a blocchi (#72) | applicazione di uno strumento A | effetto scenico dal metodo | sì | parz. | parz. | no | PARZIALE | UI: Tavola; ESEC: #72 = (CSD,SCD,SCD), 9 punti fissi | nessuna vista per blocchi | V4-P3 |
| L75 | Libro | §7.2 B6 | B6 Acqua e olio (invariante a blocchi) | applicazione di uno strumento A | effetto scenico dal metodo | parz. | no | no | no | ASSENTE | — | vedi L65 | V4-P3 |
| L76 | Libro | §7.2 B7 | B7 Il mazzo che si riavvolge (periodo o inverso) | applicazione di uno strumento A | effetto scenico dal metodo | sì | parz. | parz. | no | PARZIALE | UI: Cicli (ordine), Tavola (T⁻¹) | procedura di ritorno assente | V4-P2 |
| L77 | Libro | §7.2 B8 | B8 Do-as-I-do | applicazione di uno strumento A | effetto scenico dal metodo | parz. | no | no | no | ASSENTE | — | vedi L64 | V4-P3 |
| L78 | Libro | §7.2 B9 | B9 Localizzazione incrociata | applicazione di uno strumento A | effetto scenico dal metodo | parz. | no | no | no | ASSENTE | ESEC: #100/#7, posizione 4 → 9 | vedi L64 | V4-P3 |
| L79 | Libro | §7.2 B10 | B10 Onniscienza (due Assi → tabellone) | applicazione di uno strumento A | effetto scenico dal metodo | sì | parz. | parz. | no | PARZIALE | UI: Tavola (tre Assi) | vedi L59 | V4-P2 |
| L80 | Libro | §7.2 B11 | B11 La forma del rimescolamento | applicazione di uno strumento A | effetto scenico dal metodo | sì | sì | sì | sì | COMPLETO | UI: Cicli, Tavola (tipo ciclico) | — | — |
| L81 | Libro | §7.2 B12 | B12 Interrogo il mazzo (protocollo adattivo del centro) | applicazione di uno strumento A | effetto scenico dal metodo | parz. | no | no | no | ASSENTE | — | protocollo adattivo assente | V4-P1 |
| L82 | Libro | §7.2 B13 | B13 Pari o dispari | applicazione di uno strumento A | effetto scenico dal metodo | sì | parz. | parz. | no | PARZIALE | UI: Tavola, Explorer | regola non spiegata | V4-P3 |
| L83 | Libro | §7.2 B14 | B14 Dimostrazione d'azzardo (forzature multiple) | applicazione di uno strumento A | effetto scenico dal metodo | parz. | no | no | no | ASSENTE | — | vedi L60 | V4-P3 |
| L84 | Libro | §7.2 B15 | B15 Gran finale (due testimoni su mazzo d'ordine ignoto) | applicazione di uno strumento A | effetto scenico dal metodo | sì | parz. | parz. | no | PARZIALE | UI: Tavola (tre Assi, mazzo ordinato) | ricostruzione da testimoni su mazzo qualsiasi assente | V4-P2 |
| L85 | Libro | §7.3 (Parte C) | Manipolazioni: glimpse, break/crimp, falso taglio, falso mescolamento, controlli, forzature cartomagiche | — | la mano come interfaccia | n.a. | n.a. | n.a. | n.a. | NON APPLICABILE | — | la matematica del taglio è in L69 | — |
| L86 | Libro | cap.8 §8.1-8.4 | Composizione oltre il terzo mescolamento: tavola locale 6×6 di S3; cumulativo; successioni senza ripetizione (prodotto dei sei = trasposizione per parità) | chiusura sotto composizione | navigare fra tabelloni | sì | parz. | parz. | no | PARZIALE | UI: Explorer (espressioni di qualunque lunghezza), Cayley | tavola 6×6 e regola di non-ripetizione assenti | V4-P2 |
| L87 | Libro | §8.5 | Tavola delle decomposizioni locali; passaggio da Y a X | ogni elemento ha 6 fattorizzazioni | nessuna memoria univoca del percorso | sì | no | no | no | ASSENTE | — | assente | V4-P3 |
| L88 | Libro | cap.9 §9.1-9.3, §9.5 | Famiglia estesa (1 728 configurazioni per stadio); blocco effettivo (8 rappresentazioni); saturazione; uniformità 46 656; 23 887 872; #132 | saturazione e uniformità | nessuna 217ª trasformazione | sì | sì | sì | sì | COMPLETO | UI: Distribuzione, Decomposizioni, Filtri; DOC: guide.s16, s21; TEST: baseline M11; ESEC: #132 = (SCD,CDS,DSC) | — | — |
| L89 | Libro | §9.4 | Il gioco ordinario come famiglia vincolata: 12 blocchi per stadio, l'8 compare solo sul ciclo completo | due meccanismi dello stesso numero | non confondere coincidenze numeriche | sì | parz. | parz. | no | PARZIALE | UI: Analisi, Distribuzione | il confronto dei due meccanismi non è spiegato | V4-P2 |
| L90 | Libro | cap.10 §10.1-10.2 | Tabellone cumulativo C_N; ritorno in 3 stadi (3N → 3); ricostruzione del cammino con gli inversi in ordine inverso | origine vs cammino | tornare all'origine o rivedere le tappe | sì | parz. | parz. | no | PARZIALE | UI: Explorer (composizione) | nessuno strumento di successione di procedure e ritorno | V4-P1 |
| L91 | Libro | §10.2.1 | Ritorno mediante due carte guida da una disposizione arbitraria A | R = C_N⁻¹ da quattro dati | tornare senza registrare la storia | parz. | parz. | parz. | no | PARZIALE | CODICE: tabellone_da_assi (tre Assi, mazzo iniziale ordinato) | disposizione iniziale arbitraria e due guide non supportate | V4-P1 |
| L92 | Libro | §10.2.1 «Una curiosità decimale» | Somma delle posizioni delle tre guide = 39 | invariante | scorciatoia di controllo | no | no | no | no | ASSENTE | ESEC: vale su tutte le 216 righe | assente | V4-P3 |
| L93 | Libro | §10.2.2 | Raggiungere una sequenza assegnata w da v: candidato dalle due guide, verifica sulle altre 25 carte; altrimenti irraggiungibile | appartenenza a Gaia | riconoscere l'impossibile | parz. | no | no | no | ASSENTE | CODICE: kronecker.appartiene_a_G (non esposto) | assente in UI | V4-P1 |
| L94 | Libro | cap.11 (11.1-11.6, 11.10-11.11) | Caso generale b^m: tabellone in S_b^m, immersione, invarianti generali | generalizzazione | ciò che non dipende dal 27 | n.a. | n.a. | n.a. | n.a. | ASSENTE | — | escluso dal perimetro | OLTRE 4.0 |
| L95 | Libro | §11.7 (caso b=m=3); App.A §A.1.8 | Gruppo delle trasformazioni intermedie Γ ≅ S3³ ⋊ C3 (648); forma normale h ∘ R^r; classi laterali H → HR → HR² → H | trasformazioni parziali | dove sta la trasformazione a metà procedura | sì | parz. | sì | parz. | PARZIALE | CODICE: algebra.CanonicalForm, kronecker.appartiene_a_H; UI: Explorer (esponente MSC); DOC: guide.s09 («G_ext»); TEST: baseline M7, M12 | nome diverso dal libro (Γ); il percorso delle classi laterali non è mostrato | V4-P1 |
| L96 | Libro | §11.8 | Reversibilità (sempre) vs chiusura (dopo 3 stadi); inversa in forma normale | due proprietà distinte | non confonderle | sì | parz. | sì | parz. | PARZIALE | UI: Explorer (T⁻¹); DOC: guide.s17 | distinzione non spiegata | V4-P2 |
| L97 | Libro | §11.9 (caso ternario 11.9.7) | Fibre digitali, trasporto delle fibre, somme Σ, ricostruzione; «che cosa è realmente invariante» | ricostruzione da dati aggregati | informazione nelle somme | no | no | no | no | ASSENTE | — | assente (vedi A06) | V4-P0 |
| L98 | Libro | §11.10 | Invarianti generali: ordine = mcm, punti fissi = prodotto, coniugio per componenti, p(b)^m classi | invarianti | — (caso 27 in L28, L50, L51) | sì | sì | parz. | no | PARZIALE | UI: Cicli, Tavola, Coniugio | regole non spiegate per il 27; caso generale oltre 4.0 | V4-P2 |
| L99 | Libro | §11.11 | Disposizione rettangolare N = ij; gioco delle 21 carte; dinamica informativa | caso rettangolare | fisico vs informativo | no | no | no | no | ASSENTE | — | 21 carte e N = ij oltre il perimetro; la distinzione fisico/informativo per il 27 è in L67 e A12 | OLTRE 4.0 |
| L100 | Libro | cap.12 §12.1-12.10 | Realizzazione tensoriale V27 ≅ E3^{⊗3}, rappresentazione fedele, ortogonalità | seconda rappresentazione | linguaggio tensoriale | sì | parz. | parz. | parz. | PARZIALE | CODICE: numpy.kron in kronecker/permutations; DOC: guide.s02 («struttura tensoriale») | nessuna vista della base tensoriale | V4-P3 |
| L101 | Libro | §12.11 | Confronto con i sistemi quantistici composti | — | analogia (dichiarata senza entanglement) | n.a. | n.a. | n.a. | n.a. | NON APPLICABILE | — | contenuto editoriale | — |
| L102 | Libro | App. A | Note di calcolo: codifica, MSC, J = R⊗R⊗R, ϑ, T = A2∘ϑ(A1)∘ϑ²(A0), Γ = H ⋊ C3 | formulario | riferimento unico | sì | sì | sì | sì | COMPLETO | CODICE: rotate_kron_factors, compute_Ai_symbolic; DOC: guide.s03-s08; TEST: baseline M6, M12c | — | — |
| L103 | Libro | App. B | Base matematica del programma (v3.0.3): oggetti, trasporto, forma normale, motore simbolico, gruppo, decomposizioni | tracciabilità libro ↔ codice | il programma come laboratorio | sì | sì | sì | sì | COMPLETO | CODICE: tutti i nomi citati esistono in 3.1.3 (normalize_with_trace, CanonicalForm, rotate_kron_factors, _collect_msc_right, find_all_kron_decompositions[_parallel], try_kron_decompose, compute_distribution_parallel) | l'appendice è riferita a v3.0.3 | — |
| L104 | Libro | App. C | Tavola delle 216 disposizioni semplici: # = k1 + 6k2 + 36k3, indici P[k] e R[k], mazzo finale, cifre degli Assi, riga di T e impilamento | catalogo completo | consultare le 216 Cronache | sì | sì | sì | sì | COMPLETO | CODICE: numero_tavola, riga_tavola; UI: Tavola 216, PDF dettagliato; DOC: guide.s11; TEST: test_gioco_reale, test_tabellone_inverso; ESEC: #7, #56, #62, #72, #82, #91, #100, #132 coincidono con il testo | la Tavola non mostra il mazzo finale né le sottorighe per cifre degli Assi | V4-P2 |
| L106 | Libro | Notazioni e convenzioni pp.vii-xv | Convenzioni e nomi: carta ≠ posizione, T tabellone/operatore, H = ρ(S3³) (216), Γ (648), Cronaca/Procedura/Gaia/Giullare | lessico condiviso | coerenza terminologica | sì | n.a. | n.a. | parz. | PARZIALE | CODICE: convenzioni coincidenti (§ 1.3); DOC: guide.s09 usa G, G_ext; codice usa H per 648 | conflitto di nomi H/Γ/G_ext; termini narrativi assenti | V4-P1 |
| L107 | Libro | Prefazione pp.xvi-xxii | Cornice asimoviana (Seldon, Gaia, Mulo) | — | motivazione narrativa | n.a. | n.a. | n.a. | n.a. | NON APPLICABILE | — | — | — |
| L108 | Libro | Prologo pp.xxiii-xxv | Il trucco delle 21 carte e la riga centrale; «il valore complessivo delle colonne rimaneva costante» | — | origine della domanda | n.a. | n.a. | n.a. | n.a. | NON APPLICABILE | — | 21 carte oltre 4.0 | — |
| A01 | Articolo | §1 | Contesto (Gergonne, radix sort, perfect shuffles) | — | collocazione | n.a. | n.a. | n.a. | n.a. | NON APPLICABILE | — | — | — |
| A02 | Articolo | §2, Prop.2.1 | Modello posizionale; regola dello stadio x' = ρ(r)·b^{m−1} + ⌊x/b⌋; ricorrenza (caso 27) | estrazione e reinserimento della cifra | perché le cifre ruotano | sì | parz. | parz. | parz. | PARZIALE | CODICE: permutations.MSC, gioco_reale.raccogli; DOC: guide.s03 | la formula del singolo stadio non è mostrata | V4-P1 |
| A03 | Articolo | §3, Teor.3.1 | Rotazione M_m, T_h = (P_h ⊗ I) ∘ M_m, chiusura tensoriale; M^m = I non autorizza cancellazioni formali | chiusura del ciclo | trasporto dei fattori | sì | sì | sì | parz. | COMPLETO | UI: Explorer › Traccia riscrittura; DOC: guide.s07 | l'avvertenza sulla cancellazione formale manca | V4-P3 |
| A04 | Articolo | §4, Def.4.1, Teor.4.2 | Permutazioni digitalmente separabili: fibre F_{i,t}; quattro caratterizzazioni equivalenti; unicità dei fattori | riconoscimento intrinseco della classe | riconoscere G senza conoscere il gesto | parz. | parz. | parz. | no | PARZIALE | CODICE: try_kron_decompose, appartiene_a_G; UI: Explorer (solo espressioni) | termine, fibre e caratterizzazioni assenti; nessun input di permutazione arbitraria | V4-P0 |
| A05 | Articolo | §4, Cor.4.3 | Immersione S_b^m ↪ S_{b^m}; 216 su 27! | omomorfismo iniettivo | piccolezza della classe | sì | parz. | n.a. | parz. | PARZIALE | TEST: baseline M5, M12a; DOC: guide.s09 | confronto con 27! assente | V4-P2 |
| A06 | Articolo | §5 [App.D §6] | Formula Σ_{i,t} = C_i + b^{m−1+i}·ρ_i(t); sufficienza; Oss.5.3 non-criterio [App.D Teor.6.4 criterio] | ricostruzione da statistiche aggregate | l'informazione sopravvive nelle somme | no | no | no | no | ASSENTE | — | assente; la versione del criterio richiede decisione (§ 21) | V4-P0 |
| A07a | Articolo | §6 [App.D §7], Es.6.1 | Caso 27: C0=108, C1=90, C2=36; tabella 108/117/126 …; ricostruzione di un codice | esempio completo | calcolo a mano | no | no | no | no | ASSENTE | ESEC: il core riproduce esattamente la tabella di Es.6.1 | assente | V4-P1 |
| A07b | Articolo | §6 (ultimo capoverso) | Codice di raccolta vs tabellone: esecuzione fisica ≠ permutazione finale | due livelli | non identificare gesto e T | sì | sì | sì | parz. | PARZIALE | UI: Tavola (mescolamenti, impilamenti, T); DOC: glossario | — | V4-P2 |
| A08 | Articolo | §7 [App.D §8], Prop.7.1 | ord = mcm degli ordini locali; fix = prodotto dei fix locali | invarianti leggibili | dal tabellone agli invarianti | sì | sì | parz. | no | PARZIALE | UI: Tavola, Cicli | regole non spiegate | V4-P2 |
| A09 | Articolo | §7, Oss.7.2 | 27 classi nel gruppo interno; nel gruppo ambiente S27 classi distinte si fondono | gruppo di riferimento | non estendere proprietà da G a S27 | parz. | sì | parz. | no | PARZIALE | CODICE: GroupData.classes (27), statistiche_tavola (7 tipi di ciclo = classi di S27 che intersecano G) | la fusione 27 → 7 non è mostrata | V4-P1 |
| A10 | Articolo | §8 [App.D §9] | Catena procedura → codice → separabile → fattorizzazione; ipotesi del modello | sintesi | dove finisce il risultato | n.a. | n.a. | n.a. | parz. | PARZIALE | DOC: guide.s09-s10 (parziale) | ipotesi (non adattività; rovesciamenti secondo la versione) non dichiarate | V4-P2 |
| A11 | Articolo | App.A | Caso rettangolare N = ij; matrice di commutazione K_{j,i} | — | — | n.a. | n.a. | n.a. | n.a. | ASSENTE | — | escluso dal perimetro | OLTRE 4.0 |
| A12 | Articolo | App.A | Gioco delle 21 carte: F_c molti-a-uno, X_k (21 → 7 → 3 → 1); dinamica fisica vs dinamica informativa; insiemi condizionati alle risposte | contrazione dell'incertezza | distinguere mazzo e conoscenza | no | no | no | no | ASSENTE | — | ramo 27 (27 → 9 → 3 → 1) essenziale per la 4.0; ramo 21 oltre il perimetro | V4-P0 (ramo 27) |
| A13 | Articolo | App.D §5, Es.7.2 | Rovesciamento prima della distribuzione; molteplicità 2^m; Cor.5.2 inversione delle raccolte per storia ε nota; famiglia estesa | effetto dei rovesciamenti | ricostruire le raccolte se la storia è nota | sì | parz. | parz. | parz. | PARZIALE | CODICE: compute_T_full, selftest 1b; UI: Filtri/Anteprima, Distribuzione | formula di inversione non esposta; fonte ambigua (§ 2.2) | V4-P1 |
| A14 | Articolo | Riferimenti | Bibliografia | — | — | n.a. | n.a. | n.a. | n.a. | NON APPLICABILE | — | — | — |

Lettura rapida della matrice (i conteggi completi sono nel § 26): **122 concetti**, di cui **23 COMPLETO**,
**62 PARZIALE**, **27 ASSENTE** (3 dei quali oltre la 4.0), **10 NON APPLICABILE**, **0 NON VERIFICABILE**.
Il livello più debole è la **didattica** (D = `no` in 54 righe su 110 pertinenti), seguito dall'interazione.

---

## 8. Matrice programma → fonte

Ogni funzione importante del programma è ricondotta ai concetti delle fonti. Le funzionalità senza
corrispondenza sono classificate senza eliminare nulla.

| Funzione del programma | Concetti delle fonti (ID) | Classificazione |
|---|---|---|
| Inizia qui + glossario | L55 (progressione), L17, L19 | corrispondenza diretta (didattica d'ingresso) |
| Filtri Stadio 0/1/2, J per livello, J uniformi | L37, L88 (famiglia estesa), A13 | corrispondenza diretta (cap. 9, App. D § 5) |
| Preset Gioco Reale (1 728) | L31, L44, L89 | corrispondenza diretta |
| Anteprima | L33, L37, L102 | corrispondenza diretta; **sovrapposta ma utile** con l'Explorer (parametri vs espressione) |
| Analisi molteplicità | L44, L46, L63, L88 | corrispondenza diretta (Procedura → Cronaca, senza i nomi del libro) |
| Explorer › Numerico, Forma algebrica, Passi parziali | L34, L95, L102, L103 | corrispondenza diretta (App. B) |
| Explorer › Traccia riscrittura | L34, A03, L103 (B.5) | corrispondenza diretta |
| Explorer › Forma canonica K∘MSC^k | L95, L96, A04 (caratterizzazione 4) | corrispondenza diretta; gruppo chiamato `G_ext`/`H` invece di Γ |
| Explorer › Matrice 27×27 + fattori 3×3 | L24, L26, L29, L30 | corrispondenza diretta |
| Mescolamento animato (normale e carta-per-carta) | L14, L15, L33 | **ESTENSIONE UTILE** (il libro non ha un'animazione; la modalità carta-per-carta è propria del programma); disposizione della griglia non fisica (L15) |
| Simulatore › istruzioni | L08, L19, L60 | corrispondenza diretta (A4 forzare) |
| Simulatore › 7 fotografie del mazzo | L04, L15 | corrispondenza diretta |
| Pratica interattiva | L19 (errore classico) | corrispondenza parziale: rileva l'errore, non ne mostra le conseguenze (§ 14) |
| Tavola 216 | L104, L16, L41, L61, L62, L66 | corrispondenza diretta (App. C) |
| Ricostruzione dagli Assi | L41, L59, L79 | corrispondenza diretta (tre Assi; il libro ne usa due) |
| Cicli e ordine, orbite | L28, L62, L80 | corrispondenza diretta |
| Distribuzione (istogramma 216 × 46 656) | L88 | corrispondenza diretta (Teor. 9.56) |
| Decomposizioni T / T⁻¹ | L88, L103 (B.8), L36 | corrispondenza diretta |
| Tavola di Cayley (calcolatore, commutatore, potenze, ⟨A,B⟩) | L49, L48 | corrispondenza diretta; commutatore e sottogruppo generato sono **ESTENSIONE UTILE** (non trattati dal libro) |
| Classi di coniugio e centro | L50, L52, A09 | corrispondenza diretta |
| Presentazione (vista esecutore) | L56, cap. 7 (effetto/presentazione), (E) di L58 | **ESTENSIONE UTILE** (supporto scenico) |
| Protocollo HTML | L08, L58, L28 | **ESTENSIONE UTILE**; usa i nomi `f3/f2/f1` (1-based) mentre guida e libro usano `f2,f1,f0`: **DA GIUSTIFICARE** (terminologia) |
| Export CSV / PDF standard / PDF dettagliato fino a 20 M elementi | L104 (layout «stile C» del PDF dettagliato); nessun concetto per l'export massivo | **SUPPORTO TECNICO** (analisi dati); PDF standard e PDF dettagliato si sovrappongono (**ridondante candidata** a livello didattico, non tecnico) |
| Export LaTeX/SVG (Anteprima, Explorer, Cayley, Coniugio) | L49, L50 (le Fig. 6.7–6.9 del libro sono del tipo prodotto da questi export [INF]) | **ESTENSIONE UTILE** (supporto editoriale) |
| Verifica / `--selftest` | L27, L16, L41, L62, L104 | corrispondenza diretta (§ 3.2.4 del libro) |
| Guida (33 sezioni) e banner | trasversale | documentazione (§ 17) |
| Impostazioni, parallelismo, ETA, annullamento, cache | — | **SUPPORTO TECNICO** |
| `appartiene_a_G`, `appartiene_a_H` (solo core) | A04, L93, L95 | calcolo esistente **non esposto** |
| Duplicazioni-oracolo (tabelle GEN3/MSC, Cayley, inverse) | — | **SUPPORTO TECNICO** (verifica indipendente; da preservare per A–H) |

Nessuna funzionalità è risultata **priva di giustificazione** sul piano del contenuto; l'unica voce DA GIUSTIFICARE
è terminologica (`f3/f2/f1`).

---

## 9. Copertura del gesto fisico

Distinzione mantenuta: **modello** = `T`, matrici, forma canonica; **gesto** = distribuzione, raccolta,
impilamento, rovesciamento, ordine cronologico. Nel programma convivono due modelli collegati dal selftest [CODICE]:
il **modello fisico** (`core/gioco_reale.py`: mazzo coperto, posizione 0 al dorso, distribuzione round-robin,
mescolamento come sigla funzionale, impilamento come gesto inverso, rovesciamento **dopo** la raccolta) e il
**modello a stadi** (`Stage = P ∘ MSC ∘ J`, rovesciamento **prima** della distribuzione).

| Aspetto del gesto | Fonte | Programma | Valutazione |
|---|---|---|---|
| Distribuzione ciclica in S, C, D | L15, § 2.2.2 | `distribuisci`; fotografie del Simulatore | coperta; la griglia 9×3 del Mescolamento **non** rappresenta la distribuzione fisica (indice `c·9+r`) e non lo dichiara |
| Scelta della colonna (risposta dello spettatore) | L10, L67, B1, B12 | Pratica: l'utente clicca la colonna in cui compare `C??` | la risposta è un **esercizio di osservazione**, non un'informazione: la carta è sempre nota al programma (§ 14, § 18) |
| Raccolta: ordine delle pile | L17, L19, L30 | istruzioni «impila dal dorso: …» (`descrizione_impilamento`) | coperta, con avviso della Prima Crisi |
| Ordine fisico di impilamento vs sigla | L19 | colonne mescolamento/impilamento in Tavola e Simulatore | **COMPLETO** |
| Rovesciamenti | L23, L44, L54, A13 | ammessi da Filtri, Anteprima, PDF; **esclusi** da Simulatore, Pratica e Tavola | parziale; i due momenti del rovesciamento (prima della distribuzione nel cap. 5 e in App. D; «a valle della raccolta» in App. C e nel modello fisico) sono riconciliati dal selftest ma non spiegati |
| Mescolamento/impilamento: CDS ↔ DSC | L19 | ovunque | coperto |
| Ordine cronologico vs ordine del tabellone | L18, § 2.4.1 | Tavola: mescolamenti in ordine cronologico; tabellone (ultimo in alto) solo nel PDF dettagliato | parziale |
| Posizione della carta | L08 | fotografie del Simulatore; orbita in Cicli | coperta per l'osservazione, non per il ragionamento ternario |
| Bersaglio | L02, L03 | Simulatore (default 13) | coperto; «posizione 14» in `guide.s01` usa il conteggio 1-based senza dirlo (§ 17) |
| Ripetizione dei tre stadi | L28, B7 | Cicli (periodo), non come gesto ripetuto | parziale |
| Più procedure consecutive e ritorno | L90, L91 | solo come composizione simbolica nell'Explorer | parziale |
| Taglio | L69 | assente | assente |

**Sintesi.** Il gesto *corretto* è modellato con precisione e verificato su 1 728 procedure e 729 coppie
carta/bersaglio [TEST]. Mancano: il gesto *con rovesciamento* nelle viste fisiche, il gesto *sbagliato* e le sue
conseguenze, il gesto *adattivo* (la raccolta decisa dopo la risposta dello spettatore), il taglio.

---

## 10. Copertura della base 3

Domanda del § 15 dell'incarico: il programma permette di **vedere e capire** il ruolo delle tre cifre?

| Elemento | Calcolo | Visibile | Manipolabile | Spiegato |
|---|---|---|---|---|
| `n = 9n2 + 3n1 + n0` (L05) | `digits3` | T stampata in 3 blocchi da 9 (Anteprima) | no | guide.s02 |
| gerarchia 27 → 9 → 3 → 1 (L06) | sì | linee di separazione nella matrice | no | parziale |
| parola SCD dell'indirizzo (L07) | solo per il PDF | solo PDF dettagliato («settore ternario» degli Assi) | no | no |
| MSC = rotazione delle cifre (L42, A02) | sì | no (nessuna vista mostra `(n2,n1,n0) ↦ (n0,n2,n1)` su una carta) | no | guide.s03 |
| effetto dei tre stadi: `P3 = 9s2 + 3s1 + s0` (L08) | sì | no | parziale (carta, bersaglio) | una frase nel Simulatore |
| flusso delle cifre, «macchina che dimentica» (L09) | implicito | no | no | no |
| storia delle distribuzioni = cifre dell'origine rovesciate (L10) | sì (`colonne`) | come lista di colonne | la Pratica chiede la colonna | no |
| carta → bersaglio cifra per cifra (L21, L60) | sì | no | sì (Simulatore) | parziale |

**Valutazione [INF].** Il programma **calcola** correttamente tutta la matematica ternaria, ma la rappresentazione
ternaria è quasi sempre **implicita**: nessuna vista mostra le tre cifre di una carta mentre si muove, nessuna
mostra lo scorrimento del registro di cifre del § 1.7, nessuna collega la colonna indicata alla cifra dell'origine.
È il gap didattico più netto rispetto alla Parte I del libro, dove la base 3 è «la chiave interpretativa» (§ 1.5).
Gap specifici: nessun convertitore numero ↔ terna ↔ parola; nessuna animazione del registro; il Simulatore dice
«basta scegliere il mescolamento che manda quella colonna nella cifra ternaria giusta» senza mostrare la cifra.

---

## 11. Permutazioni e matrici

| Oggetto | Programma | Collegamento visivo/concettuale | Valutazione |
|---|---|---|---|
| T come mappa carta → posizione | lista `T`, Numerico, Tavola (dettaglio) | — | coperto |
| mazzo come posizione → carta | vettore del Mescolamento; «deck» nel core | il vettore T⁻¹ del Mescolamento è `deck⁻¹` | coperto ma **mai affiancato a T con la spiegazione della differenza** (L14) |
| T⁻¹ | Explorer, Tavola, Decomposizioni T⁻¹ | T e T⁻¹ affiancate | coperto |
| matrice di permutazione (`M[T[i],i]=1`) | Explorer › Matrice, PDF | guide.s17 spiega la convenzione | coperto; manca l'azione matrice–vettore sul mazzo (L24) |
| composizione | Explorer (espressioni), Cayley (A∘B, B∘A) | — | coperto nel calcolo; `M(a∘b)=M(a)M(b)` protetto da test (M4), non mostrato |
| trasposta = inversa | T⁻¹ come trasposta (guide.s17), «Elenco matrici trasposte» nel PDF | — | coperto; manca il collegamento con la Prima Crisi (Oss. 3.44, L26) |
| fattori 3×3 | sotto la matrice nell'Explorer, PDF | legenda colori GEN3 | coperto |
| Kronecker | espressioni `x`, matrici a blocchi | glossario | coperto nel calcolo; nessuna costruzione visiva A⊗B (L29) |

**Valutazione.** Area **ben coperta** per calcolo e visualizzazione; il passaggio fra rappresentazioni esiste
dentro l'Explorer (permutazione, matrice, forma canonica, fattori), ma manca il ponte fra **matrice** e **gesto**
(nessuna vista mostra che una colonna della matrice è una carta che si sposta nel mazzo fisico) e fra matrice e
**cifre** (i blocchi 9×9/3×3 non sono etichettati come livelli n2/n1).

---

## 12. Struttura di gruppo

Gruppo di riferimento indicato riga per riga, come richiesto (§ 17 dell'incarico).

| Tema | Gruppo | Programma | Valutazione |
|---|---|---|---|
| S3, GEN3, identità, inverse, ordini locali | S3 | PERM3, legenda, tooltip, guide.s04 | COMPLETO |
| G = S3³, 216 elementi, chiusura | G | Tavola, Cayley, TEST M5 | COMPLETO |
| ordine, cicli, orbite | elementi di G (come permutazioni di S27) | Cicli | COMPLETO |
| coniugio (27 classi, tipo per fattore), centro | **G** | dialogo Coniugio | COMPLETO |
| coniugio **in S27** (tipi di ciclo: 7 in G) | S27 ristretto a G | solo come colonna «tipo ciclico» della Tavola | **gap**: la fusione 27 → 7 (Oss. 7.2 dell'articolo) non è mostrata; un utente può credere che le 27 classi siano classi di S27 |
| generatori | G | le sei raccolte sui tre livelli (implicito); calcolatore ⟨A,B⟩ | parziale |
| prodotti, forma canonica | Γ = G ⋊ ⟨MSC⟩ (648) | Explorer (K∘MSC^k), TEST M7, M12 | COMPLETO nel calcolo; **nome** divergente |
| classi laterali degli stadi intermedi (H → HR → HR² → H) | Γ | non mostrate | gap (L95) |
| prodotto intrecciato S3 ≀ S3 (1 296) | S3 ≀ S3 | assente | gap (L40) |
| Burnside, transitività | azione di G su {0,1,2}³ | «azione transitiva» affermata in guide.s09 | gap (L51) |
| J ∈ G | G | calcolabile, non presentato | gap (L53) |

**Conflitto di nomi (da decidere, non da correggere qui).** Libro (Notazioni p. xii; App. A § A.1.8; App. B;
§ 11.7): `G` gruppo astratto dei tabelloni, `H` sua realizzazione matriciale (216), `Γ = H ⋊ C3` (648).
Programma: `G` per i 216 (guida e codice), `G_ext = ⟨S₃³, MSC⟩` nella guida (s09, s16), `H` per i 648 nel codice
(`appartiene_a_H`, test `test_h_ha_648_elementi_distinti`). Lo stesso simbolo `H` indica quindi oggetti diversi
nel libro (216) e nel codice (648). **DECISIONE DI PRODOTTO NECESSARIA** (§ 21).

Nessuna proprietà verificata in G viene dichiarata dal programma valida in S27 [UI, controllato nei testi
della guida]; il rischio nasce dall'assenza di un indicatore esplicito del gruppo di riferimento, non da
affermazioni errate.

---

## 13. Decomposizioni e strategie

### 13.1 Che cosa esiste

* **Molteplicità** (quante sequenze realizzano una T): Analisi, su qualunque dominio filtrato. Sul preset Gioco
  Reale ogni T ha molteplicità 8 [ESEC: 1 728 procedure → 216 T, tutte le fibre di cardinalità 8].
* **Decomposizioni** nel modello esteso: 46 656 terne (A0,A1,A2) per ogni T ∈ G (Decomposizioni, Distribuzione).
* **Strategia carta → bersaglio**: `risolvi_trucco` sceglie **una** sequenza di mescolamenti in forma chiusa.
* **Nessuna** nozione esplicita di equivalenza, costo, alternativa o confronto fra strategie.

### 13.2 Le distinzioni richieste, misurate sul core [ESEC]

| Relazione | Significato | Misura sul dominio del gioco |
|---|---|---|
| stessa T globale (E_T) | stessa Cronaca | 1 728 procedure con rovesciamenti → 216 classi di 8; 216 procedure senza rovesciamenti → 216 classi di 1 |
| stessa azione sulla carta (E_carta) | `T[c]` uguale | per c = 0 e bersaglio 13: **8** procedure semplici, con **8 T distinte**; con i rovesciamenti **64** procedure, sempre 8 T |
| stesso bersaglio | (c, t) fissati | ogni coppia delle 729 ha esattamente **8** soluzioni semplici |
| stessa sequenza fisica | stessi mescolamenti e rovesciamenti | identità delle procedure |
| stesso costo | secondo una metrica dichiarata | dipende dalla metrica (sotto) |

Esempi [ESEC]:

* **E_T senza E_gesti.** La classe dell'identità contiene `(SCD,SCD,SCD)` senza rovesciamenti e con rovesciamenti
  alle fasi (2,3), (1,3), (1,2), e `(DCS,DCS,DCS)` con un numero dispari di rovesciamenti: otto gesti diversi, stessa T.
* **Profilo dei rovesciamenti.** In **ogni** classe E_T il numero di rovesciamenti delle 8 procedure è
  `(0,1,1,1,2,2,2,3)`: ogni Cronaca ha esattamente una realizzazione senza rovesciamenti.
* **E_carta senza E_T.** `(CSD,CSD,CSD)` e `(CSD,CSD,CDS)` portano entrambe la carta 0 in 13 ma sono T diverse.
* **Costo e scelta del solutore.** Metrica 1 «numero di raccolte diverse da SCD»: il solutore attuale è
  **minimo in tutte le 729 coppie**. Metrica 2 «numero di raccolte cicliche CDS/DSC» (quelle in cui mescolamento e
  impilamento differiscono, cioè esposte all'errore della Prima Crisi): il solutore sceglie una sequenza **non
  minima in 386 coppie su 729**, pur esistendo fra le 8 alternative una sequenza con meno raccolte cicliche.
* **Famiglie di gesti.** Le procedure che evitano CDS e DSC raggiungono **64** T senza rovesciamenti e **120** T
  con i rovesciamenti: vietare le raccolte cicliche **riduce** l'insieme delle Cronache raggiungibili.

### 13.3 Valutazione

Il programma sa **contare** (molteplicità, decomposizioni) ma non sa **confrontare**: non espone le 8
alternative di una coppia carta/bersaglio, non dichiara un costo, non distingue fra le relazioni della tabella.
Le relazioni non coincidono (E_T ⊊ E_carta sulla carta fissata; E_gesti ortogonale a E_T), dunque un futuro
servizio deve trattarle come relazioni distinte (§ 23 della richiesta, sviluppato nel § 22 come I1).

### 13.4 Specifica proposta delle equivalenze [PROP]

Dominio `Π` = procedure del gioco (1 728, o 216 senza rovesciamenti); `T : Π → G`.

```text
E_T(p,q)        ⇔ T(p) = T(q)                                    (partizione in 216 classi di 8)
E_carta_c(p,q)  ⇔ T(p)[c] = T(q)[c]                              (27 classi di 64 per ogni c)
E_target_{c,t}  = { p ∈ Π : T(p)[c] = t }                         (insieme, non relazione: 64 elementi, 8 semplici)
E_gesti_F(p)    ⇔ tutte le raccolte e i rovesciamenti di p appartengono alla famiglia F dichiarata
                  (es. F_semplice: nessun rovesciamento; F_sicura: nessuna raccolta CDS/DSC)
E_costo_κ(p,q)  ⇔ κ(p) = κ(q) per una metrica κ dichiarata, per esempio
                  κ1 = numero di raccolte ≠ SCD, κ2 = numero di raccolte CDS/DSC, κ3 = numero di rovesciamenti,
                  κ4 = combinazione lessicografica dichiarata
```

Proprietà da proteggere con test (esaustivi sul dominio): E_T ⊆ E_carta_c per ogni c; |classe E_T| = 8;
|E_target_{c,t}| = 64 (8 semplici); profilo dei rovesciamenti per classe; nessuna implicazione fra E_gesti ed E_T.

---

## 14. Simulazione e pratica

### 14.1 Che cosa esiste [CODICE: `gui/simulator_tab.py`]

* La sessione congela carta, bersaglio e piano (`SessionePratica`, B04).
* Per ogni fase la Pratica mostra le tre colonne con la carta nascosta come `C??`, chiede la colonna, poi
  l'impilamento; ogni risposta sbagliata incrementa un contatore e scrive nel log; l'errore «impilare la sigla del
  mescolamento» è riconosciuto come errore della **Prima Crisi** (`is_seldon`).
* **Dopo ogni risposta, il programma applica comunque il mescolamento corretto** (`# applica SEMPRE il
  mescolamento corretto al mazzo fisico`). Il riepilogo verifica che la carta sia al bersaglio (lo è sempre),
  assegna un voto su 6 errori massimi e elenca gli errori.
* Nessun rovesciamento, nessun errore di distribuzione, nessun errore dello spettatore.

### 14.2 Che cosa manca

1. **Le conseguenze dell'errore.** L'errore è contato ma non accade: il mazzo non diverge, la carta non finisce
   altrove, T non cambia. Il libro, invece, costruisce la Prima Crisi proprio sull'osservazione della
   conseguenza (righe 62 e 56 della tavola, § 2.4.5) e avverte che un rovesciamento accidentale **non è
   autocorretto** (§ 6.10).
2. **Il ruolo informativo della colonna.** La colonna da cliccare è visibile (`C??`); la risposta non trasporta
   informazione, mentre nel gioco reale è l'unica informazione disponibile (§ 18.1).
3. **Il recupero.** Nessuna indicazione su come rimediare (ricalcolare le fasi residue, o ritornare con T⁻¹).

### 14.3 Errori fisici che sarebbe sensato rappresentare [PROP] e loro conseguenze [ESEC]

| Errore | Gesto | Conseguenza matematica | Esempio misurato |
|---|---|---|---|
| E1 Prima Crisi | impilare la sigla del mescolamento invece della sua inversa (solo CDS/DSC) | si esegue l'inversa: cambia **una riga** del tabellone, quindi **una sola cifra** della destinazione | carta 0 → 20 con (DSC, SCD, DSC), riga #111: errore alla fase 1 → carta in **19** (cambia la cifra delle unità, riga #112); errore alla fase 3 → carta in **11** (cambia la cifra dei nove, riga #147) |
| E2 Rovesciamento accidentale dopo la fase i | capovolgere il mazzo | T resta in G ma cambia Cronaca; per effetto dell'8:1 esiste sempre una procedura equivalente, ma non quella eseguita | carta 0 → 13 con (CSD, CSD, CSD): rovesciamento dopo la fase 1 → 25, dopo la fase 2 → 22, dopo la fase 3 → 13 (il centro è fisso sotto J, ma T è un'altra) |
| E3 Ordine interno dei mazzetti invertito (distribuzione «a faccia in giù» o raccolta dal lato sbagliato) | ogni mazzetto capovolto al suo interno | modello esteso: fattori R sui livelli bassi; T in G | stesso piano: fase 1 → 25, fase 2 → 22, fase 3 → 13, con periodo 6 invece di 3 |
| E4 Colonna indicata sbagliata (spettatore o esecutore) | il mago colloca il mazzetto sbagliato nella sede della cifra | la carta riceve una cifra diversa al livello di quella fase | carta 0 → 13, colonna errata alla fase 1: la raccolta scelta diventa SCD e la carta finisce in **12** |
| E5 Pila collocata nella sede sbagliata | raccolta diversa da quella prevista | cambia la riga corrispondente; errore localizzato a un livello | (analogo a E1 per le sigle auto-inverse) |
| E6 Taglio non registrato | traslazione mod 27 | la trasformazione **esce da G**: nessun tabellone la descrive | — (richiede l'operatore taglio, L69) |

Proprietà didattica emersa [ESEC, INF]: un errore alla fase *i* altera la cifra di livello *i* della destinazione
(unità, terzine, nonetti), cioè esattamente la cifra che quella fase «scrive» (§ 1.6 del libro). È un ponte
naturale fra gesto sbagliato e rappresentazione ternaria che oggi non viene sfruttato.

---

## 15. Copertura didattica

Per ogni grande tema: il programma dà soltanto il risultato, o aiuta a capire perché?

| Tema | Spiegazione | Progressione | Feedback | Sperimentazione | Esempio | Controesempio | Collegamento fra rappresentazioni | Errore comprensibile | Giudizio |
|---|---|---|---|---|---|---|---|---|---|
| Gesto fisico | guida s01, istruzioni | sì (fasi) | contatore errori | Simulatore | 7 fotografie | no | foto ↔ istruzioni | parziale (errore contato, non mostrato) | **risultato + perché parziale** |
| Base 3 | guide.s02, una frase nel Simulatore | no | no | no | no | no | no | no | **solo risultato** |
| Tabellone | guide.s11, s27 (PDF) | no | no | Tavola (consultazione) | Tavola | no | Tavola ↔ T/T⁻¹ | no | **risultato** |
| Prima Crisi | glossario, guida, avviso, Pratica | sì | sì | parziale | sì | no (nessun mazzo «sbagliato» mostrato) | mescolamento ↔ impilamento | parziale | **perché, in parte** |
| Permutazioni e matrici | guide.s17 | Explorer a sotto-schede | no | sì (espressioni) | sì | no | T ↔ matrice ↔ forma canonica | no | **buono** |
| Slittamento / forma normale | guide.s07-s08, traccia di riscrittura | sì (passi) | no | sì | sì | «formula errata (non usare)» in guide.s07 | espressione ↔ forma normale | no | **buono** |
| Ordine e cicli | glossario, guide.s20 | no | no | sì | sì | no | T ↔ cicli ↔ orbite | no | **buono** |
| Gruppo G | guide.s09, s22, s23 | no | no | Cayley, Coniugio | sì | no | parziale | no | **risultato** |
| Molteplicità ed equivalenze | guide.s09, s15, s21 | no | no | Analisi, Distribuzione | sì | no | sequenze ↔ T | no | **risultato** |
| Somme e fibre | — | — | — | — | — | — | — | — | **assente** |
| Spettatore / informazione | — | — | — | — | — | — | — | — | **assente** |

**Osservazioni [INF].**

* Dove il programma è forte (algebra simbolica, gruppo, cicli) la didattica è affidata alla guida e alle traccie
  di calcolo; mancano quasi ovunque **controesempi** e **errori osservabili**. L'unico controesempio esplicito è la
  «formula errata» della rotazione in `guide.s07`.
* La Parte I del libro procede per **esperimento → regolarità → crisi → spiegazione** (§ 2.4: «Il tabellone
  funziona. Resta da capire perché»). Il programma offre il risultato finale di questa progressione, raramente
  il percorso: la Prima Crisi è l'unico caso in cui l'esperienza di errore è prevista.
* Il glossario (14 voci) non contiene: tabellone, Cronaca/Procedura, carte guida/Assi, rovesciamento come
  Giullare, fibra, separabilità, forma canonica (presente solo in guide.s30), periodo come orologio.

---

## 16. Collegamenti fra rappresentazioni

Percorsi didatticamente significativi (non una matrice N×N).

| Da | A | Collegamento attuale | Qualità | Gap |
|---|---|---|---|---|
| T (Explorer) | formula / forma normale / forma canonica | stesse sotto-schede | buona | — |
| T (Explorer) | matrice T e T⁻¹ | sotto-scheda Matrice | buona | — |
| T (Explorer) | cicli, ordine, orbite | notifica automatica alla scheda Cicli | buona | — |
| T (Explorer) | decomposizioni | pulsante | buona | — |
| T (Explorer) | gesto fisico (tre raccolte) | solo se T è una disposizione semplice (Presentazione) o via Protocollo | parziale | per le T con rovesciamenti non si propone la procedura ordinaria equivalente |
| T (Explorer) | riga della Tavola | nessuno | assente | «apri nella Tavola» |
| T (qualunque vista) | effetto ternario (cifre) | nessuno | assente | vista delle cifre |
| Simulatore (carta, bersaglio) | Tavola | il numero della disposizione compare nelle istruzioni, senza collegamento | debole | salto alla riga |
| Simulatore | Cicli, Presentazione | notifica di T | buona | — |
| Simulatore | alternative (le altre 7 sequenze) | nessuno | assente | vedi § 13 |
| Tavola (riga) | T/T⁻¹ | doppio clic | buona | — |
| Tavola (riga) | Explorer, Cicli, Simulatore, Presentazione | nessuno | assente | la Tavola è isolata |
| Analisi (riga) | Explorer | doppio clic / link | buona | — |
| Decomposizione | Explorer | clic | buona | — |
| Explorer | Mescolamento animato | «Carica da Explorer» | buona | nessun ritorno |
| Cayley / Coniugio (elemento) | Explorer | nessuno | assente | «apri questo elemento» |
| Anteprima | Cicli | notifica | buona | — |
| Anteprima | Explorer | nessuno diretto | debole | — |
| Pratica (errore) | matrice / T risultante | nessuno | assente | vedi § 14 |
| posizione | parola SCD / terna | nessuno | assente | vedi § 10 |

**Valutazione.** Il nucleo algebrico (Explorer ↔ Cicli ↔ Decomposizioni ↔ Analisi) è ben connesso; il **mondo
fisico** (Simulatore, Pratica, Tavola, Presentazione) e il **mondo strutturale** (Cayley, Coniugio) sono isole.
Il verso «dalla struttura al gesto» è il più debole: da una T non si arriva, in generale, alle raccolte che la
realizzano nel gioco ordinario, benché il libro lo tratti come operazione di base ((R) del § 7.1.2).

---

## 17. Guide e glossario

Confronto fra strumenti, `gioco27/i18n.py` (guida s01–s33, glossario, banner) e fonti.

**Funzioni senza spiegazione (o con spiegazione insufficiente).**
* Pratica: la guida (s19) non dice che l'errore è registrato ma non applicato.
* Tavola: la guida non spiega il vincolo dei punti fissi (0/1/3/9/27) né il criterio di auto-inversività
  leggibile dal tabellone.
* Mescolamento animato: la guida non avverte che la griglia 9×3 non è la disposizione della distribuzione fisica.

**Spiegazioni senza funzione.**
* guide.s24 dichiara che il Protocollo mostra «quale colonna raccogliere per portare la carta in ciascuna delle 27
  posizioni»: la funzione esiste (sezione «fasi») ma dipende dalle decomposizioni di T⁻¹ (guide.s24.note).
* guide.s09 afferma «azione transitiva» senza strumento o spiegazione.
* guide.s23 promette la «tabella completa di un generato per sottogruppi piccoli»: presente come ⟨A,B⟩ nel
  calcolatore e nell'export LaTeX; nessuna vista del sottogruppo come tabella a video [UI, da confermare in I].

**Terminologia incoerente.**
* `H` (libro: 216) vs `H` (codice: 648) vs `G_ext` (guida) vs `Γ` (libro) — § 12.
* «Mescolamento» indica in `glossary.short.msc` l'operazione MSC («il mescolamento di base») e in
  `glossary.short.shuffle` la sigla funzionale della raccolta; il libro usa «mescolamento» sia per lo stadio
  (§ 4.7) sia per la sigla, e chiama MSC la **distribuzione** (App. A § A.1.2). Serve una scelta (§ 21).
* `f3/f2/f1` (Protocollo) vs `f2,f1,f0` (guida, libro) e «P3» nelle note di versione v3.0.0 vs `P2` nella guida.
* guide.s01 «posizione 14, il centro del mazzo» (ordinale) vs Simulatore «default 13, il centro» (indice 0).
* Riferimenti al libro non più validi: «statistiche del capitolo 100» (guide.s29, tooltip.verify, selftest,
  README) — nel libro attuale non esiste un capitolo 100: le statistiche sono in App. B § B.9 e cap. 7 (A5, A6);
  «capitolo 7 del libro» nel segnaposto del Simulatore per «la matematica del tabellone», trattata nei capp. 2, 4,
  5 (il cap. 7 contiene la forzatura, A4). «Cap. 5, riga 82» nei test è invece corretto (§ 5.1.11).

**Concetti delle fonti assenti dalla guida.** Procedura/Cronaca; carte guida come sonde; macchina che dimentica;
storia delle distribuzioni; somme dei blocchi e fibre; separabilità digitale; Seconda Crisi; il Giullare come
elemento di G; otto cammini per Cronaca; tabellone cumulativo e ritorno; localizzazione per cifre; taglio;
mazzi gemelli; Burnside; prodotto intrecciato; classi laterali degli stadi; dinamica informativa.

Nessuna riscrittura della guida è stata eseguita.

---

## 18. Valutazione delle idee §17

Il testo del § 17 di `PROJECT_EVOLUTION_PLAN.md` non è nel repository (§ 2.3); le idee sono quelle elencate
nell'incarico. Classificazione obbligata per `b^k` e frontend web.

| Idea | Classificazione | Motivazione (dalle fonti) |
|---|---|---|
| Spettatore senza carta nota | **4.0 — ESSENZIALE** | è il trucco come si esegue davvero (Prologo; A11, B1, B12 del cap. 7); l'articolo (App. A) e il libro (§ 11.11) distinguono esplicitamente dinamica fisica e dinamica informativa |
| Simulazione degli errori reali | **4.0 — ESSENZIALE** | la Prima Crisi è costruita osservando un errore (§ 2.4.5); rovesciamento accidentale non autocorretto (§ 6.10); obiettivo didattico «commettere errori e comprenderli» |
| Grafo di Cayley | **4.0 — UTILE** | la tavola di Cayley esiste; un grafo ha senso solo su casi piccoli e con generatori dichiarati (§ 18.3) |
| Strategie equivalenti | **4.0 — ESSENZIALE** (motore) / UTILE (vista) | Procedura vs Cronaca è il cuore del cap. 6; l'8:1 (capp. 5, 6, 9); il motore è prerequisito di errori, spettatore e confronto strategie |
| Congettura e controesempio | **4.0 — UTILE** | le fonti enunciano molte proprietà verificabili esaustivamente (§ 18.4) |
| Generalizzazione b^k | **OLTRE 4.0** | decisione vincolante; cap. 11 e articolo trattano b^m |
| Formati interoperabili / CLI batch | **J — RIPRODUCIBILITÀ** | salvataggio, riproduzione, batch |
| Frontend web | **OLTRE 4.0** | decisione vincolante |

### 18.1 Spettatore senza carta nota — definizione [PROP, fondata su FONTE]

| Elemento | Definizione per il 27 |
|---|---|
| Stato iniziale dell'informazione | ordine del mazzo noto all'esecutore (B1) **oppure** ignoto (B12); carta pensata ignota; insieme candidato `X0 = {0,…,26}` (posizioni iniziali possibili) |
| Informazione ricevuta a ogni stadio | il mazzetto (S, C, D) in cui compare la carta, cioè la cifra `n_k` della posizione iniziale (Prop. 1.6, A11) |
| Riduzione dei candidati | `X1 = {x : x mod 3 = a1}` (9), `X2` (3), `X3` (1): 27 → 9 → 3 → 1, **indipendentemente dalle raccolte** (Prop. 1.6) |
| Condizione di determinazione | dopo la terza risposta: `n = a1 + 3·a2 + 9·a3` (A11); se l'ordine iniziale è noto, la carta è nota |
| Controllo della destinazione | adattivo: dopo la risposta k, collocare il mazzetto indicato nella sede `s_k` = cifra k del bersaglio (§ 1.6, A4); le altre due pile sono libere |
| Relazione con il solutore attuale | `risolvi_trucco(c, t)` presuppone la posizione iniziale `c` nota; le «colonne attese» che calcola **sono** le risposte che lo spettatore darebbe; il protocollo adattivo è la stessa formula applicata risposta per risposta |
| Incertezza epistemica vs permutazione fisica | la permutazione del mazzo è sempre biiettiva e non perde informazione (§ 11.8, App. A dell'articolo); ciò che si contrae è l'insieme dei candidati; per il 27 la contrazione è sulle **posizioni iniziali**, mentre nel 21 (oltre 4.0) è sulle posizioni correnti (`F_c` molti-a-uno) |
| Varianti delle fonti | B12: ordine ignoto, riavvolgimento osservato + tre raccolte «al centro»; B1 con gemello come righello (A8) |

### 18.2 Simulazione dell'errore reale — vedi § 14.3 (catalogo E1–E6).

### 18.3 Grafo di Cayley — che cosa esiste e che cosa significherebbe

Esiste [CODICE/UI]: tavola di Cayley 216×216 di G, calcolatore A∘B, B∘A, inversi, commutatore, potenze, ⟨A,B⟩,
heatmap SVG. Non esiste alcun **grafo** (vertici, archi, cammini, distanze).

Casi didatticamente utili [PROP], evitando il grafo di Γ a 648 vertici:
1. **S3 con generatori dichiarati** (6 vertici): archi = le trasposizioni, oppure le sei raccolte; mostra che
   ogni raccolta si ottiene da scambi e la non commutatività.
2. **G come prodotto di tre grafi di S3**: distanza = somma delle distanze per livello; illustra la
   separabilità (una raccolta cambia una sola riga del tabellone).
3. **Grafo «una raccolta alla volta»** sulle 216 Cronache (archi = cambiare un solo mescolamento): è la «Volta»
   del § 4.2 («cammini che permettevano di ritornare alla sequenza originaria sostituendo gradualmente un
   mescolamento con un altro») e ha significato di **costo dei gesti**.
4. Filtri: sottogruppi piccoli, classi di coniugio, cammini fra due T scelte.

### 18.4 Congettura e controesempio — proprietà che si prestano [PROP]

Catalogo, non linguaggio logico generale. Dominio sempre dichiarato (G, Γ, procedure, coppie carta/bersaglio,
campione di S27):

| Proprietà (fonte) | Dominio | Esito atteso |
|---|---|---|
| punti fissi ∈ {0,1,3,9,27} (A5, § 6.8) | G | vera; in S27 falsa (minimo controesempio: una trasposizione, 25 punti fissi) |
| ordine ∈ {1,2,3,6} (A6) | G | vera |
| auto-inversa ⟺ righe di ordine ≤ 2 (Prop. 5.53) | G | vera |
| parità 108/108; segno = prodotto delle righe (A10) | G | vera |
| due carte qualsiasi forzabili in due posizioni qualsiasi (A4) | coppie di posizioni | falsa: controesempio minimo (0,1) → (0,9) |
| somma delle tre guide = 39 (§ 10.2.1) | G, Γ | vera in G e anche in tutto Γ [ESEC: 648/648]; in S27 falsa (controesempio: la trasposizione delle posizioni 0 e 1) |
| ogni coppia carta/bersaglio ha esattamente 8 soluzioni semplici | 729 coppie | vera |
| il centro 13 è fisso sotto J (§ 2.2.3) | {J} | vera |
| MSC ∈ G | Γ | falsa (controesempio: MSC stessa; guide.s16 lo cita) |
| «le somme di fibra riconoscono la classe» | S27 | vera secondo App. D Teor. 6.4, non assunta dall'Articolo: **dipende dalla decisione del § 21** |

Esportazione della verifica: rimandata a J (§ 23).

---

## 19. Top gap per la 4.0

Ordinati per importanza nelle fonti, valore didattico, mancanza attuale e dipendenza per altri strumenti.

1. **Il tabellone come oggetto interattivo** (L18, L21, L35, L36, L58; V4-P0). È «l'arma dell'esecutore» e il
   filo della Parte I (capp. 2, 4, 5, 7). Oggi esiste solo come sigle nella Tavola e come griglia nel PDF
   dettagliato: manca la griglia 3×3 diretta e inversa, la lettura gerarchica «a contachilometri», le colonne
   come destino degli Assi, la lettura di una posizione riga per riga, l'operazione (R) «realizza/inverti».
   È prerequisito di errori, spettatore, ritorno e decodifica.
2. **La base 3 resa visibile e dinamica** (L05–L10, L39, A02; V4-P0). La «macchina che dimentica» (§ 1.6) e il
   flusso delle cifre (§ 1.7) sono la spiegazione del *perché* il trucco funziona; il programma li calcola senza
   mostrarli (§ 10). Senza questa vista, l'errore alla fase *i* che altera la cifra *i* (§ 14.3) resta invisibile.
3. **Lo spettatore senza carta nota e la dinamica informativa** (L67, L70, L81, A12; V4-P0). È il gioco come si
   esegue davvero (Prologo, A11, B1, B12) e la distinzione fisica/informativa dell'articolo; oggi il programma
   conosce sempre la carta.
4. **La simulazione dell'errore reale** (L19, L54, § 14; V4-P0 per la parte didattica, P1 per il catalogo
   completo). La Pratica conta gli errori ma applica sempre il gesto corretto: la conseguenza, che nel libro è il
   motore della comprensione (Prima Crisi, § 2.4.5), non si vede mai.
5. **Separabilità digitale, fibre e somme** (A04, A06, A07a, L11, L20, L59, L97; V4-P0). Due dei risultati
   centrali dell'articolo (caratterizzazione intrinseca e ricostruzione da statistiche aggregate) e un filo del
   libro (1.10, 2.4.6, A3, 11.9) sono assenti; il calcolo della separabilità esiste solo come lettura dei blocchi
   nel core.
6. **Il motore delle equivalenze: Procedura/Cronaca, fibre di 8, alternative e costi** (L44, L46, L54, L63,
   § 13; V4-P1, prerequisito di 3, 4, 8). Il programma conta ma non confronta.
7. **Decodifica di mazzi e permutazioni arbitrari** (L22, L57, L59, L91, L93, A04; V4-P1): inserire un mazzo
   finale o una coppia di mazzi, riconoscere se la trasformazione è in G, ricostruire il tabellone da due guide,
   decidere se `w` è raggiungibile da `v`.
8. **Ritorno e composizione di procedure come gesti** (L36, L58, L76, L90; V4-P1): dalla T (o da più procedure)
   alle tre raccolte che la annullano; tabellone cumulativo; «3N stadi → 3».
9. **Il gruppo di riferimento sempre esplicito** (L95, A09, L40, L106, § 12; V4-P1): G (216) / Γ (648) / S27;
   la fusione 27 classi → 7 tipi di ciclo; classi laterali degli stadi intermedi; conflitto di nomi H/Γ/G_ext.
10. **Terminologia e percorso didattico allineati al libro** (L46, L55, L106, § 17, § 22.1; V4-P1): lessico
    (Procedura, Cronaca, tabellone diretto/inverso, carte guida, nonetti/terzetti, Prima/Seconda crisi),
    riferimenti non più validi («capitolo 100»), distribuzione degli strumenti per livelli.

---

## 20. Aree già ben coperte

Da **non** reinventare in I.

| Tema | Strumenti | Evidenza | Piccolo gap residuo |
|---|---|---|---|
| Modello a stadi e algebra simbolica (Stage = P∘MSC∘J, Aᵢ con indici incrociati, forma normale, forma canonica K∘MSC^k) | Anteprima, Explorer (7 sotto-schede) | `core/algebra`; TEST baseline M6, M12; `test_linguaggio_espressioni_e` (228 test) | nomi dei gruppi (§ 12) |
| Slittamento e trasporto di MSC | Explorer › Traccia riscrittura | `normalize_with_trace`; guide.s07 (con la formula errata come controesempio) | — |
| Tavola delle 216 disposizioni (App. C) | Tavola 216, PDF dettagliato | `riga_tavola`; ancore #100/#82; ESEC su #7, #56, #62, #72, #91, #132 | mazzo finale e sottorighe per cifre non mostrati |
| Mescolamento vs impilamento (Prima Crisi) | Simulatore, Pratica, Tavola, glossario | `IMPILAMENTO_DI`; TEST test_gioco_reale | lettura speculare delle colonne |
| Forzatura di una carta (problema inverso) | Simulatore, Presentazione | `risolvi_trucco` 729/729 | alternative e costo |
| Concordanza fisica ↔ matrici | Verifica / `--selftest` | 1 728 + 216 + 729 controlli | — |
| Molteplicità, saturazione, uniformità (cap. 9) | Analisi, Distribuzione, Decomposizioni | Teor. 9.56 riprodotto (216 × 46 656) | spiegazione dei due meccanismi dell'8 |
| Struttura di G: Cayley, coniugio con tipo per fattore, centro | dialoghi Cayley e Coniugio, export SVG/TikZ | `GroupData`; TEST baseline M5 | equazione delle classi; fusione in S27 |
| Cicli, ordine, orbite, forma ciclica | Cicli, Tavola | 7 tipi, periodi 1/63/26/126 | — |
| Matrici e fattori 3×3 | Explorer › Matrice, PDF | convenzione `M[T[i],i]=1` testata; alternativa testuale (H2) | azione matrice–vettore |
| Supporto all'esecuzione | Presentazione, Protocollo | — | nomi `f3/f2/f1` |

---

## 21. Decisioni di prodotto necessarie

Questioni non decidibili tecnicamente. **Nessuna è stata presa in questo audit.**

| # | Decisione | Opzioni emerse | Dove incide |
|---|---|---|---|
| DP1 | Quale versione dell'articolo è autorevole per la 4.0 | `Articolo.pdf` (senza rovesciamenti, somme non come criterio) · App. D del libro (rovesciamenti, Teor. 6.4 criterio di riconoscimento) · entrambe, citate per versione | I5 (riconoscimento per somme), guida, catalogo delle proprietà |
| DP2 | Nomi dei gruppi nell'interfaccia | adottare H/Γ del libro · mantenere G/G_ext · mostrare entrambi con una nota; attenzione al simbolo `H` usato dal codice per 648 | guida, Explorer, catalogo delle proprietà |
| DP3 | Momento canonico del rovesciamento mostrato all'utente | prima della distribuzione (cap. 5, App. A, App. D, modello a stadi) · dopo la raccolta (App. C, `gioco_reale`) | Simulatore con rovesciamenti, errori E2, Tavola estesa |
| DP4 | Equivalenza mostrata per default fra strategie | E_T · E_carta · E_target · combinazioni | I1, Simulatore |
| DP5 | Metrica di costo dei gesti e scelta del solutore | numero di raccolte ≠ SCD (oggi minimo) · numero di raccolte CDS/DSC (oggi non minimo in 386/729 casi) · rovesciamenti · combinazione dichiarata; e se cambiare la sequenza **proposta per default** (cambierebbe la sequenza mostrata, non la correttezza) | I1, Simulatore, Presentazione |
| DP6 | Quali errori fisici simulare | E1–E6 del § 14.3, in tutto o in parte; errori dello spettatore sì/no | I3 |
| DP7 | Quanta complessità mostrare a un principiante | vedi § 22.1 | modalità, onboarding |
| DP8 | Lessico narrativo (Gaia, Cronaca, Giullare, Seldon) nell'interfaccia | solo termini matematici · termini del libro con glossario · entrambi | guida, glossario |
| DP9 | Contenuti storici/editoriali (cap. «Le carte prima della Psicostoria», Prefazione) nella guida | no · sezione facoltativa | guida |
| DP10 | Operazioni fuori da G nella 4.0 (taglio A13, mazzi gemelli A8) | incluse · escluse · solo come controesempio «fuori da G» | I5, I6 |
| DP11 | Tavola estesa ai rovesciamenti (1 728 righe) | no · sì come vista opzionale · solo come fibra delle 8 procedure di una riga | Tavola, I1 |
| DP12 | Stato dei due PDF nel repository (oggi non tracciati, 30,5 MB + 0,5 MB) | versionarli · tenerli fuori e citarli per hash · pubblicarli altrove | J/K (riproducibilità, licenza) |

---

## 22. Candidati per I

### 22.1 Livelli di utente (§ 28 dell'incarico)

Stato attuale [UI]: *Principiante* mostra Inizia qui, Simulatore, Tavola 216, **Anteprima**, **Analisi**, Guida;
nasconde Stadio 0/1/2, Explorer, **Cicli**, Distribuzione. Rispetto alla progressione del libro [INF]:
l'Anteprima (modello esteso P2⊗P1⊗P0 con J per livello, capp. 5 e 9) e l'Analisi della molteplicità (capp. 5, 6,
9) appartengono a livelli avanzati, mentre i Cicli (periodo, § 3.2.5, e A6) sono uno dei primi strumenti del
repertorio. Criteri proposti per la 4.0 [PROP], ricavati dalla struttura delle fonti:

| Livello | Fonti | Strumenti |
|---|---|---|
| **Base** — il gesto e la base 3 | Prologo, capp. 1–2 (fino a 2.4.5) | Simulatore, Pratica con errori, spettatore, vista delle cifre, tabellone (lettura), Tavola |
| **Intermedio** — permutazioni e matrici | capp. 2.4.6–4, cap. 7 Parte A | T/T⁻¹, matrice, cicli e periodo, tabellone inverso e ritorno, somme dei blocchi |
| **Avanzato** — struttura | capp. 5–6, 8–10 | Explorer, forma canonica, Cayley, coniugio, equivalenze, decodifica, composizione |
| **Laboratorio** | cap. 9, 11.7–11.9, articolo | filtri estesi, Analisi, Distribuzione, Decomposizioni, fibre, catalogo proprietà |

Nessuna modalità è stata cambiata (DP7).

### 22.2 Dipendenze fra le funzionalità (derivate dai requisiti)

```text
            modello Procedura/Cronaca (convenzioni DP3, famiglie di gesti)
                      │
         ┌────────────┼──────────────────────────┬─────────────────────┐
         ▼            ▼                          ▼                     ▼
 motore equivalenze  vista tabellone + cifre   traccia fisica     decodifica/riconoscimento
 (E_T, E_carta, …,   (lettura, inverso, (R))   passo per passo    (G? due guide, v→w, fibre)
  costi, fibre di 8)          │                     │                     │
         │                    ├──────────┐          ▼                     │
         │                    │          └──► simulazione errori ◄───────┤ (E6: taglio fuori da G)
         ▼                    ▼                     │                     │
 confronto strategie   spettatore / dinamica        ▼                     ▼
         │             informativa ◄──────── recupero (ritorno, ripianificazione)
         ▼                                                              catalogo proprietà
 grafo «una raccolta alla volta» (costo dei gesti)                     (congetture/controesempi)
```

Motivazioni: gli errori E1–E5 sono procedure diverse (richiedono il modello di procedura e la traccia); il loro
significato ternario richiede la vista delle cifre; il recupero richiede (R) e l'inverso; lo spettatore richiede le
cifre e il protocollo adattivo; il catalogo delle proprietà richiede domini dichiarati (G, Γ, procedure) e il
riconoscimento.

### 22.3 Compartimenti proposti

La suddivisione segue motore comune, flusso utente, dipendenze, rischio e testabilità; non presuppone un numero
fisso di prompt. Nessuno è stato iniziato.

**I1 — Modello di procedura ed equivalenze (servizio)**
* *Obiettivo*: un modello esplicito di Procedura (raccolte, rovesciamenti con convenzione dichiarata DP3) e
  Cronaca, con le relazioni del § 13.4 e metriche di costo dichiarate.
* *Comprende*: enumerazione delle 1 728 procedure e delle fibre di 8; alternative per (carta, bersaglio);
  costi κ1–κ4; confronto fra due procedure; servizio in `services/` senza Tk.
* *Prerequisiti*: DP3, DP4, DP5.
* *Non comprende*: viste, errori, spettatore.
* *Accettazione*: test esaustivi (1 728 procedure, 729 coppie): |fibra E_T| = 8, profilo dei rovesciamenti
  (0,1,1,1,2,2,2,3), 64/8 soluzioni per coppia, E_T ⊆ E_carta; invarianti G (services→gui = 0, ecc.) intatti;
  `risolvi_trucco` invariato salvo decisione DP5 dichiarata.
* *Rischi*: doppio modello del rovesciamento (prima/dopo) — va tenuto un solo modello con adattatore e test di
  equivalenza con `selftest`.

**I2 — Tabellone e livello ternario (viste)**
* *Obiettivo*: rendere visibili tabellone e cifre.
* *Comprende*: griglia 3×3 diretta/inversa con lettura gerarchica e colonne-Assi; convertitore numero ↔ terna ↔
  parola SCD; animazione della «macchina che dimentica» e del flusso delle cifre (anche per lo stadio con
  rovesciamento, § 5.1.5); storia delle distribuzioni = rev ω(n); tabella n → Π(n) → n'; operazione (R)
  «realizza questo tabellone» (via Tavola) e «procedura di ritorno».
* *Prerequisiti*: I1 (modello di procedura) per (R) e ritorno.
* *Non comprende*: errori, spettatore.
* *Accettazione*: ogni vista con alternativa testuale (contratto H2); test di corrispondenza vista ↔ core su
  tutte le 216 righe; navigazione Tavola ↔ Explorer ↔ Simulatore ↔ Cicli (§ 16).
* *Rischi*: layout (1280×720) e carico didattico; mantenere i contratti H2.

**I3 — Traccia fisica, errori e recupero**
* *Obiettivo*: simulare il gesto sbagliato e le sue conseguenze.
* *Comprende*: catalogo E1–E6 (DP6); nella Pratica, modalità «l'errore accade»; confronto piano/eseguito
  (T, posizione della carta, cifra alterata, riga della Tavola); rovesciamenti nelle viste fisiche; recupero
  (ripianificazione delle fasi residue o ritorno con T⁻¹).
* *Prerequisiti*: I1, I2.
* *Non comprende*: spettatore adattivo.
* *Accettazione*: per ogni errore e ogni fase, test che la cifra alterata sia quella prevista (esempi del § 14.3
  come casi fissi); E6 dichiarato «fuori da G»; la Pratica attuale resta disponibile come modalità.
* *Rischi*: confondere errore ed equivalenza (8:1) — il messaggio deve distinguere «altra Cronaca» da «stessa
  Cronaca con altri gesti».

**I4 — Spettatore e dinamica informativa**
* *Obiettivo*: il trucco con carta ignota.
* *Comprende*: insiemi candidati 27 → 9 → 3 → 1; protocollo adattivo (colloca il mazzetto indicato nella sede
  della cifra); localizzazione `n = a1 + 3a2 + 9a3` (B1); variante B12 (ordine ignoto); separazione esplicita
  incertezza/permutazione.
* *Prerequisiti*: I1, I2 (cifre); I3 facoltativo (risposte errate dello spettatore).
* *Non comprende*: 21 carte (oltre 4.0).
* *Accettazione*: per ognuna delle 27 posizioni iniziali (cioè per ognuna delle 27 terne di risposte coerenti) e
  per ognuno dei 27 bersagli, determinazione dopo tre risposte e arrivo al bersaglio (729 casi); equivalenza con
  `risolvi_trucco` quando la carta è nota.
* *Rischi*: modellare un protocollo **adattivo** nel servizio (oggi i piani sono non adattivi).

**I5 — Decodifica e riconoscimento**
* *Obiettivo*: dal mazzo alla legge.
* *Comprende*: input di una permutazione o di due mazzi; test di appartenenza a G/Γ (esporre `appartiene_a_G/H`);
  lettura dei fattori; ricostruzione da due guide con controllo `a_i ≠ b_i`; `v → w` raggiungibile?; somme dei
  blocchi e fibre Σ in avanti (immagini, righe di T) e all'indietro (valori nei blocchi finali, righe di T⁻¹);
  criterio per somme secondo DP1; A1 «note due, calcola la terza»; taglio come mossa fuori da G (DP10).
* *Prerequisiti*: I1; I2 per la presentazione.
* *Accettazione*: esaustivo su G (216) e Γ (648); campione casuale con seme su S27; esempi dell'articolo (Es. 6.1)
  e del libro (§ 2.4.8, § 10.2.1) come casi fissi.
* *Rischi*: la differenza Articolo/App. D (DP1); orientazione avanti/indietro delle somme (la stessa trappola della
  Prima Crisi, § 2.4.8 del libro).

**I6 — Laboratorio: proprietà, gruppo di riferimento, piccoli grafi**
* *Obiettivo*: esplorare e verificare.
* *Comprende*: catalogo di proprietà del § 18.4 con dominio dichiarato, verifica esaustiva, minimo controesempio;
  indicatore del gruppo di riferimento (G/Γ/S27, DP2); fusione 27 classi → 7 tipi; classi laterali degli stadi;
  grafi piccoli del § 18.3; tavola locale 6×6 e decomposizioni locali (cap. 8); J come elemento di G.
* *Prerequisiti*: I1 (domini), I5 (riconoscimento).
* *Non comprende*: esportazione riproducibile della verifica (J).
* *Accettazione*: ogni proprietà con dominio, esito e controesempio testati; nessuna proprietà di G presentata
  come valida in S27.
* *Rischi*: deriva verso un linguaggio logico generale — da evitare (catalogo chiuso).

**I7 — Percorso didattico e guida allineati al libro**
* *Obiettivo*: rendere coerenti lessico, guida, glossario e livelli.
* *Comprende*: lessico (DP2, DP8); correzione dei riferimenti obsoleti («capitolo 100»); nuove sezioni per gli
  strumenti I1–I6; livelli d'uso (DP7); controesempi ed esercizi guidati tratti dal libro (righe 62/56, #100, #91).
* *Prerequisiti*: I1–I6 (almeno quelli attuati).
* *Accettazione*: test di simmetria IT/EN (H1) e di allineamento guida (`test_guida_allineata`) estesi;
  ogni riga P0/P1 della matrice con D = sì.
* *Rischi*: rompere i contratti di H1 (chiavi, catalogo simmetrico).

---

## 23. Candidati per J

| Candidato | Contenuto | Strumenti di I che devono esistere prima |
|---|---|---|
| J1 Formato dell'esperimento | manifesto: versione del programma, convenzioni (DP3), procedura o espressione, dominio, seme, hash delle fonti | I1 (modello di procedura) |
| J2 Sessione e cronologia | stato riapribile di Simulatore, Pratica, Explorer; cronologia delle T calcolate (il lifecycle dei lavori non è cronologia: G2 § 20) | I1, I3 |
| J3 Undo/redo | nelle viste di manipolazione (Explorer, Pratica, tabellone) | I2, I3 |
| J4 CLI batch | `--selftest` esteso, esecuzione del catalogo di proprietà, export di verifiche e matrici | I6, I5 |
| J5 Riproducibilità e interoperabilità | CSV/JSON di procedure, T, verifiche; confronto fra versioni | I1, I6 |

Il § 17 «formati interoperabili / CLI batch» ricade qui (J4, J5).

---

## 24. Oltre 4.0

* **Generalizzazione a b^k** (cap. 11 del libro; l'intero articolo è formulato su b^m): tabelloni in `S_b^m`,
  immersione, fibre generali, invarianti `p(b)^m`, registro tensoriale generale. Nessuna astrazione è proposta per
  la 4.0; le viste del 27 non devono essere progettate «in attesa» di b^k.
* **Disposizioni rettangolari N = ij e gioco delle 21 carte** (§ 11.11; App. A dell'articolo), inclusa la mappa
  informativa molti-a-uno `F_c`. Il **ramo 27** della dinamica informativa resta nella 4.0 (I4).
* **Frontend web / toolkit alternativi.**
* Confronto con i sistemi quantistici (§ 12.11): contenuto editoriale, nessuno strumento.

---

## 25. Criterio proposto di completezza della 4.0

Punto di partenza (incarico): ogni tema matematico e didattico rilevante del libro e dell'articolo ha una
rappresentazione, uno strumento di esplorazione o una spiegazione interattiva adeguata, oppure è classificato come
non traducibile. Forma operativa proposta [PROP]:

**C1 — Perimetro chiuso.** L'insieme dei concetti è la matrice `V4_COVERAGE_MATRIX.csv` (122 righe),
aggiornabile solo con motivazione. Sono esclusi dal criterio le righe NON APPLICABILE (con motivazione scritta) e
quelle con priorità `OLTRE 4.0`.

**C2 — Soglie per priorità.**
* 100 % delle righe **V4-P0** in stato COMPLETO;
* ≥ 90 % delle righe **V4-P1** in stato COMPLETO e le restanti PARZIALE con D = `sì`;
* ≥ 60 % delle righe **V4-P2** almeno PARZIALE con D ≠ `no`;
* V4-P3: nessuna soglia.

**C3 — Definizione verificabile di COMPLETO.** C = `sì`; V, I, D = `sì` dove pertinenti; evidenza in almeno tre
categorie fra CODICE, TEST, UI, DOC, di cui obbligatoriamente **un TEST** e **una UI o DOC**; per i teoremi, tre
requisiti separati (§ 39 dell'incarico): il programma **verifica** il risultato, **visualizza il meccanismo**,
**spiega** la dimostrazione o rimanda alla pagina del libro.

**C4 — Didattica.** Ogni riga P0/P1 ha: un esempio del libro riproducibile nel programma; per i temi con
un errore tipico (Prima Crisi, rovesciamento, colonna sbagliata, orientazione delle somme) un **controesempio o
errore osservabile**.

**C5 — Collegamenti.** Tutti i percorsi del § 16 marcati «assente» fra viste di livello P0/P1 esistono.

**C6 — Terminologia.** Zero conflitti aperti fra guida, glossario e fonti nei termini elencati nel § 17 (o
decisione DP2/DP8 documentata); zero riferimenti a sezioni del libro inesistenti.

**C7 — Invarianti non regrediti.** Suite verde; invarianti architetturali di G e contratti di H1/H2 intatti;
oracoli matematici preservati.

**C8 — Controllo automatico [PROP per K].** Un test legge `V4_COVERAGE_MATRIX.csv` e verifica che le evidenze di
tipo CODICE/TEST citino simboli e file esistenti e che le soglie C2 siano rispettate.

---

## 26. Metriche

Calcolate sulla matrice del § 7 (script inline al momento della generazione del CSV). Non costituiscono un
punteggio di qualità.

### 26.1 Stato

| Insieme | Concetti | COMPLETO | PARZIALE | ASSENTE | NON APPLICABILE | NON VERIFICABILE |
|---|---:|---:|---:|---:|---:|---:|
| Tutte le righe | 122 | 23 | 62 | 27 | 10 | 0 |
| Libro | 107 | 22 | 54 | 23 | 8 | 0 |
| Articolo | 15 | 1 | 8 | 4 | 2 | 0 |
| Perimetro 4.0 (esclusi NON APPLICABILE e OLTRE 4.0) | 109 | 23 (21 %) | 62 (57 %) | 24 (22 %) | — | 0 |

### 26.2 Livelli C / V / I / D (righe in cui il livello è pertinente)

| Livello | Righe pertinenti | sì | parz. | no |
|---|---:|---:|---:|---:|
| C — calcolo | 108 | 80 (74 %) | 16 | 12 |
| V — visualizzazione | 108 | 40 (37 %) | 44 | 24 |
| I — interazione | 106 | 34 (32 %) | 43 | 29 |
| D — didattica | 110 | 20 (18 %) | 36 | 54 (49 %) |

### 26.3 Priorità dei gap

| V4-P0 | V4-P1 | V4-P2 | V4-P3 | nessun gap da colmare (`—`) | OLTRE 4.0 |
|---:|---:|---:|---:|---:|---:|
| 9 | 35 | 33 | 16 | 26 | 3 |

**Lettura [INF].** Il programma calcola già quasi tutto ciò che le fonti trattano (C = sì nel 74 %); il divario
per la 4.0 è di **rappresentazione, interazione e spiegazione**, con la didattica come collo di bottiglia.

---

## 27. Test e verifiche eseguite

### 27.1 Ambiente

```text
VM di sessione: Linux, Python di sistema 3.10.12 senza tkinter e senza pytest
Ambiente di test (fuori dal repository, solo strumenti):
  CPython 3.12.14 standalone · Tk 9.0.4 · Xvfb 1920x1080x24
  numpy 2.5.3 · pytest 9.1.1 · reportlab · openpyxl · pypdf · pikepdf · pyflakes
Comando: PYTHONDONTWRITEBYTECODE=1 xvfb-run -a python -B -m pytest -p no:cacheprovider -q -ra <file>
```

L'ambiente di riferimento di H2 (Python 3.12.3 con **Tk 8.6**) non è riproducibile nella VM di questa sessione:
non c'è `sudo` per installare `python3-tk`, e le build standalone di CPython con Tk 8.6 (3.12.3, 3.12.9, 3.12.10)
abortiscono sotto Xvfb con un'asserzione di libxcb (`append_pending_request`). L'unico Tk funzionante è il 9.0.4.

### 27.2 Suite iniziale e finale

Con Tk 9.0.4 l'esecuzione della suite in un solo processo termina con un *segmentation fault* dentro Tk quando più
file che costruiscono l'applicazione vera vengono eseguiti di seguito; la suite è stata quindi eseguita **file per
file** (38 processi), con lo stesso risultato all'inizio e alla fine dell'audit:

| Misura | Baseline attesa (H2) | Iniziale | Finale |
|---|---:|---:|---:|
| test raccolti (`--co`) | 1 429 | 1 429 | 1 429 |
| passati | 1 428 | 1 427 | 1 427 |
| saltati | 1 | 1 (N03, `pypdfium2` assente) | 1 (N03) |
| falliti | 0 | 1 | 1 |
| xfail | 0 | 0 | 0 |

`tests/test_baseline_matematica.py`: **25 passati** all'inizio e alla fine.

**Il fallimento è ambientale, non una regressione.**
`test_layout_accessibilita_h2.py::test_lo_scorrimento_si_accende_quando_il_testo_cresce` misura che, a scala
d'aiuto 2.0 e finestra 1920×1080, il contenuto della scheda Stadio 0 superi l'altezza visibile e accenda lo
scorrimento. Con Tk 9.0.4 e il font di default della VM (`nimbus sans l`, 10 pt, 99,9 dpi) il contenuto cresce
(`alto > basso` è verificato) ma non supera la vista. Nessun file tracciato è stato modificato (`git diff` vuoto
sui file versionati), e il test fallisce identico all'inizio e alla fine; con Tk 8.6 (ambiente H2) passava.
Non è stato corretto (vincolo § 5 dell'incarico).

### 27.3 Verifiche puntuali sul core [ESEC]

Eseguite con Python inline sul working tree; nessun file creato.

| Verifica | Esito |
|---|---|
| righe #7, #56, #62, #72, #82, #91, #100, #132 della tavola: mescolamenti, impilamenti, Assi, periodo, punti fissi, parità | coincidono con libro (§§ 2.4.5 nota 11, 5.1.11, 7.1, 7.2, 9.5) |
| statistiche delle 216 righe | periodi {1:1, 2:63, 3:26, 6:126}; punti fissi {27:1, 9:9, 3:27, 1:27, 0:152}; 7 tipi di ciclo; parità 108/108; 64 auto-inverse (App. B § B.9, § 6.8) |
| #100: cicli (3,3,3,6,6,6); firma condivisa da 72 righe | coincide con B11 |
| B2 su #100: posizione 20 ← carta 25; carta 2 → posizione 12 | coincide |
| B9: T_#7 ∘ T_#100⁻¹ (4) = 9 | coincide |
| Articolo Es. 6.1: somme di fibra per ρ0=(1,2,0), ρ1=(2,1,0), ρ2=(1,0,2) | 117/126/108, 144/117/90, 117/36/198: coincide |
| somma delle posizioni delle tre guide = 39 | vera sulle 216 righe e su tutti i 648 elementi di Γ |
| 1 728 procedure → 216 T | tutte le fibre hanno 8 elementi; profilo dei rovesciamenti (0,1,1,1,2,2,2,3) in ogni fibra |
| E_carta: per ogni carta c, T[c] assume ogni valore esattamente 64 volte | vero per tutte le 27 carte |
| solutore `risolvi_trucco` | minimo per κ1 (raccolte ≠ SCD) in 729/729 coppie; non minimo per κ2 (raccolte CDS/DSC) in 386/729 |
| procedure senza CDS/DSC | 64 T senza rovesciamenti, 120 con rovesciamenti |
| errori E1–E4 su piani concreti | § 14.3 |

---

## 28. Limiti dell'audit

* **Fonti arrivate durante l'audit.** Libro e articolo sono comparsi nella radice dopo l'inizio del lavoro e non
  sono tracciati da Git: le conclusioni valgono per i file con gli hash del § 2.1.
* **Lettura del libro.** Letti per intero front matter, capp. 0–10 e App. A, B, C; il cap. 11 è stato letto nelle
  sezioni pertinenti al caso 27 (11.7, 11.8, 11.9) e scorso per struttura nel resto; il cap. 12 scorso per struttura
  e con lettura delle parti sulla rappresentazione tensoriale del 27; l'App. D confrontata con `Articolo.pdf` per
  struttura, enunciati e §§ 5 e 8–9 (non riga per riga). Figure e tavole raster (es. Fig. 1.1, 4.4, 6.7–6.9, il
  corpo della tavola dell'App. C) non sono state lette come immagini.
* **Interfaccia non pilotata.** Le affermazioni [UI] derivano dal codice delle viste, dalla guida e dai test di
  layout H2, non da una sessione interattiva; eventuali dettagli visivi andranno confermati all'avvio di I.
* **Ambiente di test** diverso da quello di riferimento (Tk 9 invece di 8.6, esecuzione file per file): vedi § 27.
* **Piano del progetto assente** (`PROJECT_EVOLUTION_PLAN.md`): le idee del § 17 sono valutate sull'elenco
  dell'incarico, non sul testo del piano.
* **Giudizi di copertura.** La scala C/V/I/D e gli stati sono giudizi motivati riga per riga; le priorità sono
  proposte, non decisioni.
* **Nessun test di caratterizzazione aggiunto**: le verifiche del § 27.3 sono state eseguite inline e non sono
  state trasformate in test (preferenza «nessuna modifica»).

---

## 29. Git status

Stato prima del commit di questo audit:

```text
On branch main
Your branch is ahead of 'origin/main' by 66 commits.
Untracked files:
  Articolo.pdf                                   (aggiunto dall'utente durante l'audit, non incluso nel commit)
  LIBRO_MAIN.pdf                                 (aggiunto dall'utente durante l'audit, non incluso nel commit)
  V4_COVERAGE_MATRIX.csv                         (deliverable)
  V4_MATHEMATICAL_DIDACTIC_COVERAGE_AUDIT.md     (deliverable)
```

Commit previsto: uno solo, di documentazione — `docs(v4): audit mathematical and didactic coverage` — con i due
deliverable. Nessun file del programma o dei test modificato; nessun push; `origin/main` resta `54445af`.
Dopo il commit il ramo è 67 commit avanti e restano non tracciati soltanto i due PDF delle fonti (DP12).

### Gate di uscita

| Gate | Esito |
|---|---|
| A-G1 libro e articolo identificati | **OK** — § 2 (articolo in due versioni, ambiguità dichiarata) |
| A-G2 ogni tema rilevante inventariato | **OK** — §§ 4–5, 122 righe |
| A-G3 stato esplicito per ogni tema | **OK** — § 7 |
| A-G4 evidenza concreta per ogni copertura | **OK** — colonna «Evidenza programma» |
| A-G5 C/V/I/D distinti | **OK** — § 7, § 26.2 |
| A-G6 mappa fonte → programma | **OK** — § 7 |
| A-G7 mappa programma → fonte | **OK** — § 8 |
| A-G8 gesto fisico e modello non confusi | **OK** — § 9 |
| A-G9 base 3 valutata didatticamente | **OK** — § 10 |
| A-G10 permutazioni/matrici valutate | **OK** — § 11 |
| A-G11 struttura di gruppo valutata | **OK** — § 12 |
| A-G12 decomposizioni/strategie valutate | **OK** — § 13 |
| A-G13 idee del § 17 valutate una per una | **OK** — § 18 |
| A-G14 b^k oltre 4.0 | **OK** — §§ 18, 24 |
| A-G15 frontend web oltre 4.0 | **OK** — §§ 18, 24 |
| A-G16 decisioni di prodotto non prese in silenzio | **OK** — § 21 (DP1–DP12) |
| A-G17 compartimenti I proposti, non implementati | **OK** — § 22 |
| A-G18 compartimenti J proposti, non implementati | **OK** — § 23 |
| A-G19 criterio verificabile di completezza | **OK** — § 25 |
| A-G20 matematica e comportamento invariati | **OK** — nessun file tracciato modificato |
| A-G21 suite iniziale e finale verdi | **OK con riserva ambientale** — 1 427 passati, 1 saltato (N03), 1 fallito identico prima e dopo, dovuto a Tk 9.0.4 (§ 27.2) |
| A-G22 nessun I/J/K iniziato | **OK** |
| A-G23 nessun accesso fuori dal repository | **OK** — § 1.4 |
| A-G24 nessun push | **OK** |
