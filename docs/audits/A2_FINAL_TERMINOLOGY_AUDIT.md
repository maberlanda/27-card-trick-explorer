# A2 — Audit finale terminologico

**Prodotto:** Gioco delle 27 carte — release candidate 4.0.0

**Data:** 2026-09-26

**Natura:** audit diagnostico; nessuna correzione terminologica applicata
**Esito del gate:** **A2 CONCLUSO CON ISSUE APERTI**

## 1. Stato e perimetro

L'audit è iniziato sul ramo `main`, HEAD `4c0fd3a823eafa6e6cc25a4d9273d5dea1cd5ee8`, con `origin/main` a `6e77210f31e467f0915e3cca0af4c9ef39328e44` e ramo locale avanti di 10 commit. Gli unici file non tracciati iniziali erano le fonti intenzionali `Articolo.pdf` e `LIBRO_MAIN.pdf`. A1 e A1-FIX risultavano conclusi.

Sono state controllate 24 classi di superfici user-facing: UI generale, menu, schede, finestre/dialog, pulsanti, tooltip, help banner, Guida, glossario, onboarding, errori, messaggi informativi, CLI human-readable, help CLI, README, note di release, export TXT, HTML, LaTeX, SVG, PDF, XLSX, CSV/JSON con etichette e titoli/intestazioni generati. Il testo localizzato è materializzato in 2.048 chiavi IT e 2.048 chiavi EN simmetriche, richiamate da 50 moduli Python con `tr(...)`; sono stati inoltre letti i testi correnti non localizzati pertinenti.

L'inventario normativo allegato contiene **110 concetti/termini**. I documenti `docs/history/` sono stati usati soltanto come riferimento storico. Nessun testo corrente, traduzione, formula, codice, test o UI è stato modificato.

## 2. Metodo

Per ogni concetto sono stati registrati termine principale IT/EN, varianti ammesse, forme da evitare, termini di fonte, superfici, stato e issue. Il controllo è stato eseguito in entrambe le direzioni:

1. una nozione deve mantenere un nome stabile tra superfici;
2. una stessa parola o sigla non deve fondere oggetti incompatibili;
3. IT ed EN devono designare lo stesso concetto, senza giudizi di eleganza;
4. fonte, alias narrativo, termine tecnico e nome UI devono restare riconoscibili;
5. i significati fissati da A1/A1-FIX hanno prevalenza sulle convenienze lessicali.

Le occorrenze sono state cercate nel catalogo i18n, nei call site, nelle stringhe CLI/export, nei documenti correnti e nelle fonti PDF. I casi positivi e negativi sono stati classificati per concetto, non per semplice frequenza testuale. Le pure varianti ortografiche o tipografiche sono state separate come `STYLE-DEFERRED`.

Risultato: **16 issue terminologici** (`3 TERM-HIGH`, `9 TERM-MEDIUM`, `3 TERM-LOW`, `1 TERM-ITEN`), **8 mappature SOURCE-TERM** e **3 famiglie STYLE-DEFERRED**. Le righe CSV possono condividere lo stesso issue; i conteggi precedenti sono per finding univoco.

## 3. Fonti

### Fonti primarie

| fonte | impronta SHA-256 | uso terminologico |
|---|---|---|
| `Articolo.pdf` | `293BA88C1942A2D7CFDC44B29BB6AD5B7B9B87D4A449B3A7009BFBAABFC8D5A9` | stadio, mazzetto/colonna, rotazione, separabilità, fibre e fattorizzazione |
| `LIBRO_MAIN.pdf` | `1E1C9A7E4A8B19E723EBEA39EF4F636AEBA2E954E7C4900F2D322E7663235E6A` | notazione e convenzioni; Gaia/G, Cronaca, Giullare; disposizione semplice; pile/mazzetti; crisi; ritorno e rovesciamenti |

Sono stati verificati direttamente, fra gli altri, Libro pp. PDF 12–15 (notazione narrativa/tecnica), p. 217 (tagli), p. 363 e seguenti (Tavola delle disposizioni semplici), pp. 401–416 (Appendice D), e Articolo pp. PDF 1–11.

### Fonti progettuali

Sono stati letti `docs/audits/A1_FINAL_MATHEMATICAL_AUDIT.md`, `docs/audits/A1_MATHEMATICAL_FIX_VERIFICATION.md`, le decisioni pertinenti, i documenti storici necessari, `README.md`, `docs/README.md`, `docs/release/NOTE_VERSIONE_4.0.0.md`, Guida e glossario correnti. La matematica verificata in A1/A1-FIX non è stata reinterpretata.

## 4. Vocabolario controllato proposto

| area | termine IT principale | termine EN principale | confine concettuale |
|---|---|---|---|
| identità fisica | carta | card | oggetto seguito, non posto numerico |
| sede | posizione | position | posto `0..26` nel mazzo |
| stato | disposizione | arrangement | ordine corrente delle carte, per esempio `v_k` |
| azione fisica | distribuzione / raccolta | deal / pickup | operazioni distinte |
| supporto fisico | colonna / mazzetto | column / pile | vista distribuita / gruppo fisico |
| codici | mescolamento `M_i` / impilamento | stage shuffle / stacking | funzione / gesto eseguibile |
| unità algebrica | stadio | stage | `P_i ∘ MSC ∘ J_i` |
| unità interattiva | fase | phase | intervallo fisico dell'esecuzione |
| esecuzione | Procedura | Procedure | scelta concreta; dominio 1.728 |
| risultato | trasformazione | transformation | permutazione risultante; dominio H di 216 |
| oggetto generale | permutazione | permutation | biiezione, anche fuori dal gioco |
| annullamento | inversa `T⁻¹` | inverse `T⁻¹` | mappa che annulla T |
| gesto/canonica | rovesciamento | reversal | locale `R_U` o globale J, non inversa |
| successione | storia / successione | history / sequence | conserva i passi eseguiti |
| risultato globale | cumulativo `C_k` | cumulative transformation | non conserva la storia |
| recupero origine | ritorno compresso | compressed return | `C_N⁻¹`, recupera `v_0` |
| recupero tappe | replay a ritroso | backward replay | usa le inverse dei singoli passi |
| classificazione H | classe di coniugio | conjugacy class | 27 classi interne |
| classificazione ambiente | tipo ciclico | cycle type | 7 tipi in S27 incontrati da H |
| fisico/algebrico | taglio / traslazione | cut / translation | azione / mappa `C_k` |
| azione di MSC | rotazione dei fattori | rotation of digit factors | non taglio e non reversal |

La tabella completa, inclusi sinonimi e forme da evitare, è in `A2_FINAL_TERMINOLOGY_AUDIT.csv`.

## 5. Mappa IT/EN

Le coppie centrali semanticamente equivalenti sono: `procedura/procedure`, `trasformazione/transformation`, `permutazione/permutation`, `disposizione/arrangement`, `distribuzione/deal`, `raccolta/pickup`, `rovesciamento/reversal`, `inversa/inverse`, `ritorno/return`, `percorso/path`, `storia/history`, `taglio/cut`, `traslazione/translation`, `classe di coniugio/conjugacy class`, `tipo ciclico/cycle type`.

È emersa una non-equivalenza effettiva: `sequence.stage` rende l'IT `Tappa v{k}` con EN `Stage v{k}`. Il valore `v_k` è uno stato/checkpoint di L90, non lo `Stage_i` algebrico. È `A2-TERM-ITEN-01`.

Le varianti EN `collection`, `pickup` e `gathering` sono semanticamente vicine ma non distribuite per ruolo: `pickup` deve essere il termine operativo preferito, `collection permutation` l'oggetto P, `gathering` soltanto alias discorsivo. L'incoerenza locale è `A2-TERM-LOW-02`, non una traduzione falsa.

## 6. Carta / posizione / disposizione / mazzo

`Carta` indica l'identità, `posizione` il posto numerato e `indice` il numero usato come coordinata o chiave. Il glossario dichiara correttamente che carta e posizione non coincidono, ma poi definisce il punto fisso come «una carta che torna al suo posto» e afferma che J «fissa soltanto la carta 13». `T[x]=x` fissa anzitutto la posizione x; l'equivalenza con la carta etichettata x richiede il mazzo iniziale ordinato. Lo stesso rischio compare nelle etichette `Carta bersaglio` e negli input dove la carta è specificata tramite posizione iniziale. Questo è `A2-TERM-MEDIUM-04`.

`Disposizione` è coerente in L90 (`Disposizione v_k (carta in ogni posizione)`), ma la Tavola chiama anche le proprie 216 righe `disposizioni`, `Disposizione #n` e `disposizioni semplici`. Una riga è una trasformazione/riga della Tavola, non lo stato corrente del mazzo. L'origine è il legittimo termine di fonte «Tavola delle disposizioni semplici», ma l'uso non marcato nelle superfici tecniche crea `A2-TERM-HIGH-01`.

## 7. Distribuzione / raccolta / pile

La distribuzione mette visivamente le carte in tre colonne; la raccolta ricompone i tre gruppi fisici. Il prodotto distingue bene `impilamento` come gesto e `mescolamento` come lettura funzionale, ma usa anche `MSC` come «mescolamento di base» che comprende distribuire e raccogliere. Ne risulta una sovrapposizione tra operatore fisso MSC, mescolamento locale `M_i`, raccolta P e azioni fisiche. È `A2-TERM-MEDIUM-01`.

Per i gruppi fisici si alternano `mazzetto`, `pila`, `pacchetto` e, una volta, `mucchio`; in EN `pile` e `packet`. `Colonna` designa anche correttamente la griglia visiva. Il controllo proposto è: `colonna/column` per il layout, `mazzetto/pile` per il gruppo fisico, `pacchetto/packet` per un blocco quando il contesto tensoriale lo richiede, `pila` come variante di fonte. L'oscillazione corrente è `A2-TERM-MEDIUM-02`.

## 8. Trasformazione / permutazione / procedura

La distinzione fondamentale è per lo più corretta e protetta dal glossario: 1.728 Procedure realizzano 216 trasformazioni in H; `permutazione` è l'oggetto matematico generale. Non sono state trovate affermazioni correnti che attribuiscano 1.728 trasformazioni alla Tavola o 216 Procedure a H.

Resta `A2-TERM-MEDIUM-06`: il preset `Gioco Reale` è presentato come «1 728 combinazioni», «1 728 sequenze» o «1 728 combinazioni canoniche», mentre il nome controllato del dominio è `1.728 Procedure`. `Sequenza` va riservata a una successione ordinata di più Procedure o usata come parola generica con il referente esplicito.

## 9. Fase / stadio / round

Il prodotto possiede una distinzione utile: `stadio/stage` è l'unità algebrica, `fase/phase` la fase fisica/interattiva, `passo/step` un passo UI o di replay, `tappa/checkpoint` uno stato intermedio L90. Tuttavia glossario, tabellone inverso e alcuni testi passano da stadio a fase per la stessa struttura; l'oscillazione è `A2-TERM-MEDIUM-03`. `Round/giro` non ha un uso matematico corrente materiale e non richiede uniformazione.

La resa `Tappa/Stage` di L90 è separatamente classificata `A2-TERM-ITEN-01`.

## 10. H / Γ / S27

La nomenclatura principale è corretta: H = 216 trasformazioni, Γ = 648 elementi, S27 = ambiente. Non sono emersi residui user-facing di G con il significato tecnico corrente di H, né H usato per 648, né una confusione tra le 27 classi interne e i 7 tipi ciclici ambientali. `G/Gaia` è dichiarato come termine storico/narrativo della fonte.

Esiste però `A2-TERM-HIGH-02`: il simbolo bare `R` indica MSC nelle formule di Γ e delle classi laterali, il rovesciamento locale `d ↦ 2-d` nella formula dei reversal, e il ritorno compresso `C_N⁻¹` in L90. I tre concetti sono incompatibili anche se ogni formula isolata è corretta. Il vocabolario proposto usa `MSC` nelle classi laterali, `R_U` (o una sigla esplicitamente locale) per il reversal e `C_N⁻¹`/`ritorno compresso` senza assegnargli il bare `R`.

## 11. Inversa / rovesciamento

`Inversa T⁻¹` e `rovesciamento/reversal` sono matematicamente distinti e il glossario li spiega. L'etichetta italiana `guide.s05.row.R_U = "Inversione — S↔D"`, tuttavia, chiama inversione il reversal locale, mentre l'EN dice `Reversal`. Insieme alle occorrenze generiche di inversione, questo indebolisce il confine con l'inversa. È `A2-TERM-MEDIUM-09`.

Il vocabolario controllato deve mantenere `inversa/inverse` per T⁻¹ e `rovesciamento/reversal` per DP3=A, `R_U` e J. `Invertire` è ammesso solo con oggetto esplicito: invertire una permutazione, invertire l'ordine dei mazzetti o rovesciare il mazzo non sono la stessa operazione.

## 12. Ritorno / percorso / storia

La logica L90 è matematicamente corretta: il cumulativo recupera l'origine ma non il cammino; il replay indietro ricostruisce le tappe dalla successione conservata. Non è stata trovata la formulazione vietata «ritorno del cammino».

Il glossario definisce però `Ritorno` soltanto come riga della Tavola che realizza T⁻¹, mentre le superfici usano anche `ritorno compresso`, `ritorno all'origine` e l'alternativa di ritorno dopo un errore. È `A2-TERM-MEDIUM-05`. Il controllo proposto distingue `riga di ritorno`, `ritorno compresso all'origine` e `ricostruzione del percorso a ritroso`; `storia/cronologia/successione` conserva dati che `C_N` non conserva.

## 13. Separabilità / riconoscimento

`Separabilità digitale` è la proprietà; `riconoscimento` è il workflow; `fattorizzazione` recupera i fattori; `ricostruzione` ricompone un oggetto dai dati. La Guida I5 separa esplicitamente test diretto, criterio delle somme e fattori, quindi non è emersa una fusione matematica ad alta severità.

Il termine ombrello `Riconoscimento` e concetti operativi importanti come `indice`, `orbita`, `trasformazione cumulativa`, `trasformazione relativa`, `taglio/traslazione` non hanno però una voce di glossario. Le lacune sono raggruppate in `A2-TERM-LOW-03`.

## 14. Fibre / fattori / firme

`Fibra`, `somma di fibra`, `fattore locale`, `fattorizzazione`, `decomposizione di Kronecker` e `forma canonica` sono semanticamente stabili. `Fattorizzazione` deve restare il recupero dei fattori; `decomposizione` è l'ombrello e richiede il qualificatore quando sono possibili più decomposizioni.

È invece grave `A2-TERM-HIGH-03`: `firma` designa almeno tre oggetti diversi:

- nell'Explorer, la stringa/vettore completo della permutazione (`Firma canonica`, `Signature`);
- nella Guida/protocollo, la forma algebrica `K ∘ MSC^k` (`firma algebrica`);
- in I2m, le somme 36/117/198 (`firma dei blocchi`).

Il controllo proposto usa `vettore della permutazione`, `forma canonica` e `firma di blocco` rispettivamente.

## 15. Classi / tipi ciclici

La distinzione richiesta è rispettata: `classe di coniugio in H` indica una delle 27 classi interne; `tipo ciclico in S27` indica una delle 7 partizioni ambientali incontrate da H; `struttura ciclica` è la decomposizione effettiva in cicli; `orbita` è il percorso iterato di un elemento. Non è emerso un issue fra classe e tipo.

`Ordine` e `periodo` indicano invece lo stesso invariante della permutazione senza essere dichiarati sinonimi: il glossario definisce `Ordine`, mentre Tavola ed Explorer mostrano `Periodo`. È `A2-TERM-MEDIUM-07`. Il termine preferito è `ordine della permutazione`, con `periodo` ammesso soltanto se dichiarato alias.

## 16. Tagli / traslazioni

Il prodotto distingue sostanzialmente l'azione fisica `taglio` dalla mappa indotta `traslazione C_k`. `Rotazione` è usata per la rotazione delle cifre/fattori operata da MSC e non deve diventare sinonimo del taglio. Il confine è matematicamente recuperabile; le voci mancanti nel glossario rientrano in `A2-TERM-LOW-03`.

La notazione bare `R` per la rotazione MSC non è accettabile nel prodotto insieme a reversal e return; questo punto è già contabilizzato in `A2-TERM-HIGH-02`.

## 17. Errori / recupero

I3 distingue correttamente `previsto`, `eseguito`, `errore fisico`, `deviazione` e `recupero`. `Recupero` modifica le sole fasi future per mantenere il bersaglio; `ritorno` annulla invece una trasformazione; `correzione` è riservabile a testo/software oppure deve avere un oggetto esplicito. Non è emersa una collisione corrente che richieda issue aggiuntivo.

## 18. L90/J

L90 mantiene separati `cronologia` degli eventi, `successione di Procedure`, `cumulativo C_k`, `disposizione v_k`, `ritorno compresso` e `replay indietro`. Le due anomalie sono il simbolo R del ritorno, già `A2-TERM-HIGH-02`, e `Tappa/Stage`, `A2-TERM-ITEN-01`.

J è stabilmente il rovesciamento globale `i ↦ 26-i`, orientazione ammessa nelle Procedure e riga #215. `Giullare/Jester` resta alias di fonte. L'espressione «fissa la carta 13» partecipa invece al problema carta/posizione `A2-TERM-MEDIUM-04`.

## 19. Glossario

Sono state controllate **tutte le 43 voci**, inclusi termine, short, long, equivalenza EN, rimandi e uso nel prodotto.

| voce | esito | riferimento |
|---|---|---|
| `card` | definizione corretta; uso numerico da qualificare | MEDIUM-04 |
| `position` | corretta | MEDIUM-04 per il confine con carta |
| `board` | corretta | — |
| `inverse_board` | fase/stadio oscillante | MEDIUM-03 |
| `forgetting_machine` | corretta; usa alias locale `mucchio/pile` | MEDIUM-02 |
| `procedure` | definizione corretta | MEDIUM-06 fuori voce |
| `transformation` | corretta | HIGH-01 fuori voce |
| `inverse` | corretta | MEDIUM-09 fuori voce |
| `fixed_point` | definito come carta anziché posizione | MEDIUM-04 |
| `return` | corretta ma copre un solo ambito | MEDIUM-05 |
| `guide_cards` | corretta | — |
| `recovery` | corretta | — |
| `local_factor` | corretta | — |
| `separability` | corretta | — |
| `fiber` | corretta | — |
| `fiber_sum` | corretta | — |
| `canonical_form` | corretta; collide con `firma canonica` altrove | HIGH-03 |
| `center` | corretta | — |
| `group_h` | corretta; G dichiarato storico | SOURCE-02 |
| `group_gamma` | concetto corretto; simbolo R collidente | HIGH-02 |
| `s27` | corretta | — |
| `coset` | concetto corretto; simbolo R collidente | HIGH-02 |
| `msc` | fonde operatore, deal e raccolta nella descrizione breve | MEDIUM-01 |
| `permutation` | corretta | — |
| `stage` | corretta; oscillazione esterna con fase | MEDIUM-03 |
| `collection` | corretta nel modello; sinonimi fisici non governati | MEDIUM-01/02 |
| `shuffle` | corretta localmente; collisione con MSC | MEDIUM-01 |
| `stacking` | corretta | — |
| `orientation` | corretta | — |
| `real_game` | usa sequenze/combinazioni invece di Procedure | MEDIUM-06 |
| `total_transform` | corretta | — |
| `conjugacy` | corretta | — |
| `cayley` | corretta | — |
| `kronecker` | corretta | — |
| `cycle` | corretta | — |
| `order` | corretta; alias periodo non dichiarato | MEDIUM-07 |
| `gaia` | source term correttamente mappato | SOURCE-02 |
| `cronaca` | source term corretto; leak tecnico | SOURCE-03 / LOW-01 |
| `giullare` | source term correttamente mappato | SOURCE-04 |
| `mondo_di_mazzo` | source term correttamente circoscritto | SOURCE-05 |
| `seldon` | cornice narrativa corretta | SOURCE-06 |
| `prima_crisi` | source term corretto | SOURCE-07 |
| `seconda_crisi` | source term corretto | SOURCE-08 |

Non sono state trovate voci completamente inutilizzate. Le quasi-duplicazioni (`total_transform/transformation`, `inverse/return`, `collection/shuffle/stacking`) restano concetti distinguibili ma richiedono i confini riportati sopra. I termini usati ma assenti sono inventariati in `A2-TERM-LOW-03` e nel CSV.

## 20. CLI/export

CLI `recognize`, `property`, `sequence`, `replay`, `validate` ed `export` seguono in prevalenza il lessico delle viste. `cli.replay.steps` parla correttamente di cammino ricostruito e tappe riottenute all'indietro. CSV/JSON distinguono successione, replay, cronologia, proprietà e mapping.

Gli export TXT, HTML, LaTeX, SVG, PDF e XLSX ereditano le principali anomalie dal catalogo: `firma`, `periodo/ordine`, `fase/stadio`, `disposizione` per la riga della Tavola e i sinonimi di raccolta. Non è stato trovato un lessico autonomo che introduca nuove collisioni oltre ai finding già registrati.

## 21. IT/EN

I cataloghi hanno 2.048 chiavi ciascuno e insieme di chiavi simmetrico. La maggioranza delle coppie tecniche è equivalente. `Tappa/Stage` è l'unica non-equivalenza concettuale autonoma (`A2-TERM-ITEN-01`).

`Inversione/Reversal` è registrato come issue concettuale italiano (`A2-TERM-MEDIUM-09`), non come TERM-ITEN separato, perché l'EN chiarisce il concetto ma il problema è l'ambiguità della famiglia italiana `inversa/inversione`. `Collection/pickup/gathering` rimane una dispersione di sinonimi equivalenti (`A2-TERM-LOW-02`).

## 22. Termini delle fonti

| ID | termine di fonte | mappa prodotto | esito |
|---|---|---|---|
| `A2-SOURCE-01` | disposizione semplice / simple arrangement | riga della Tavola / trasformazione | legittimo in citazione; non controllato nella UI corrente |
| `A2-SOURCE-02` | G / Gaia | gruppo H | mappatura esplicita e corretta |
| `A2-SOURCE-03` | Cronaca | trasformazione | mappatura corretta; un leak tecnico LOW-01 |
| `A2-SOURCE-04` | Giullare / Jester | J, rovesciamento globale | mappatura corretta |
| `A2-SOURCE-05` | Mondo-di-Mazzo | sistema di posizioni e azioni | correttamente narrativo |
| `A2-SOURCE-06` | Seldon / Psicostoria | cornice narrativa | correttamente narrativo |
| `A2-SOURCE-07` | Prima Crisi | shuffle vs stacking | mappatura corretta |
| `A2-SOURCE-08` | Seconda Crisi | introduzione del reversal J | mappatura corretta |

Queste differenze non sono errori in sé. Diventano issue solo quando l'alias di fonte entra in una superficie tecnica senza segnalazione o collide con il vocabolario corrente.

## 23. Issue

### `A2-TERM-HIGH-01` — Disposizione: stato del mazzo contro riga/trasformazione

- **Termini concorrenti:** `disposizione/arrangement` per `v_k`; `Disposizione #n`, `disposizioni mostrate`, `simple arrangement` per le righe della Tavola.
- **Superfici:** `table.status_shown`, `table.detail_title`, `table.detail.heading`, `table.no_arrangement`, `simulator.instructions.arrangement`, Presentazione, onboarding/help; controesempio corretto `sequence.deck`.
- **Esempio:** «216 disposizioni mostrate» indica in realtà 216 trasformazioni.
- **Motivo:** fonde stato e mappa fra stati.
- **Vocabolario proposto:** disposizione = stato/ordine corrente; riga della Tavola/trasformazione = uno dei 216 elementi. `Disposizione semplice` solo come source term marcato.

### `A2-TERM-HIGH-02` — Collisione del simbolo R

- **Termini concorrenti:** `R=MSC`; `R` reversal locale; `R=C_N⁻¹` ritorno compresso.
- **Superfici:** `glossary.group_gamma`, `glossary.coset`, `guide.i6.sections`, `guide.i1.reversals`, `sequence.return`, `guide.s29.session.body`.
- **Esempio:** nello stesso prodotto R può ruotare fattori, rovesciare una cifra o annullare un cumulativo.
- **Motivo:** stessa sigla per tre operatori incompatibili.
- **Vocabolario proposto:** `MSC`; `R_U`/rovesciamento locale; `C_N⁻¹`/ritorno compresso.

### `A2-TERM-HIGH-03` — Firma per tre invarianti/rappresentazioni

- **Termini concorrenti:** firma della permutazione, firma algebrica, firma di blocco.
- **Superfici:** `explorer.canonical_signature`, `explorer.status.result`, `explorer.partial.signature`, help Explorer, protocollo HTML, `guide.i2m.signature`.
- **Esempio:** «Firma canonica» è il vettore serializzato, mentre la forma canonica è `K ∘ MSC^k`.
- **Motivo:** una parola identifica tre oggetti non intercambiabili.
- **Vocabolario proposto:** vettore della permutazione; forma canonica; firma di blocco.

### `A2-TERM-MEDIUM-01` — MSC, mescolamento, raccolta e distribuzione

- **Termini concorrenti:** mescolamento di base MSC; mescolamento `M_i`; raccolta P; gesto fisico.
- **Superfici:** glossario `msc/collection/shuffle`, filtro, Tavola, Simulatore, Pratica, Guida, export.
- **Esempio:** MSC è descritto come distribuire e raccogliere, mentre `mescolamento` è anche la sigla funzionale della raccolta.
- **Motivo:** livelli fisico e funzionale oscillano.
- **Vocabolario proposto:** distribuzione/operatore MSC; raccolta P; codice di mescolamento `M_i`; impilamento come gesto.

### `A2-TERM-MEDIUM-02` — Colonna, pila, mazzetto, pacchetto

- **Termini concorrenti:** colonna, pila, mazzetto, pacchetto, mucchio; column, pile, packet.
- **Superfici:** glossario, Simulatore, Spettatore, Shuffle viewer, Guida, protocollo.
- **Esempio:** il registro della macchina che dimentica riceve la cifra del «mucchio», mentre la pratica nomina mazzetti e il glossario pacchetti.
- **Motivo:** oggetto visivo, gruppo fisico e blocco tensoriale non hanno ruoli lessicali stabili.
- **Vocabolario proposto:** colonna visuale; mazzetto/pile fisico; pacchetto/packet per blocco qualificato; pila come alias di fonte.

### `A2-TERM-MEDIUM-03` — Fase contro stadio

- **Termini concorrenti:** fase/phase e stadio/stage per la stessa unità in alcune spiegazioni.
- **Superfici:** glossario `stage`, `inverse_board`, Simulatore/Pratica, Guida, tabellone.
- **Esempio:** il tabellone ha una riga per stadio, ma il tabellone inverso dichiara lo «stesso ordine delle fasi».
- **Motivo:** sfuma il confine tra operatore algebrico e intervallo fisico.
- **Vocabolario proposto:** stadio algebrico; fase fisica; passo UI; tappa/checkpoint L90.

### `A2-TERM-MEDIUM-04` — Carta, posizione e punto fisso

- **Termini concorrenti:** carta 13, posizione 13, indice 13.
- **Superfici:** glossario `card/position/fixed_point`, Laboratorio J, Guida I6, input del Simulatore.
- **Esempio:** «J fissa soltanto la carta 13» senza premessa di mazzo ordinato.
- **Motivo:** l'uguaglianza numerica delle etichette non identifica gli oggetti.
- **Vocabolario proposto:** punto/posizione fissa; carta etichettata 13 solo sotto convenzione iniziale esplicita.

### `A2-TERM-MEDIUM-05` — Ritorno senza ambito stabile

- **Termini concorrenti:** riga di ritorno, ritorno all'origine, ritorno compresso, alternativa di ritorno.
- **Superfici:** glossario `return/inverse/recovery`, Tavola, L90, Simulatore, Spettatore, CLI.
- **Esempio:** la voce `Ritorno` definisce solo la riga della Tavola, ma L90 usa lo stesso sostantivo per `C_N⁻¹`.
- **Motivo:** inverse correlate ma con oggetto e informazione conservata diversi.
- **Vocabolario proposto:** riga di ritorno; ritorno compresso all'origine; replay/ricostruzione a ritroso.

### `A2-TERM-MEDIUM-06` — Dominio del Gioco Reale

- **Termini concorrenti:** 1.728 combinazioni, sequenze, combinazioni canoniche, Procedure.
- **Superfici:** pulsante/preset Gioco Reale, status, glossario `real_game`, Guida e filtri.
- **Esempio:** «insieme pronto di 1 728 sequenze».
- **Motivo:** il numero è normativamente il dominio delle Procedure; sequenza ha già un ruolo L90.
- **Vocabolario proposto:** 1.728 Procedure; configurazioni di stadio solo nel dominio esteso espressamente qualificato.

### `A2-TERM-MEDIUM-07` — Ordine contro periodo

- **Termini concorrenti:** ordine della permutazione; periodo.
- **Superfici:** glossario `order`, Tavola, Explorer, Presentazione, protocollo ed export.
- **Esempio:** la stessa quantità è `Ordine` nel glossario e `Periodo` nelle colonne/stato.
- **Motivo:** sinonimo matematico non dichiarato.
- **Vocabolario proposto:** ordine della permutazione; periodo solo come alias esplicitato.

### `A2-TERM-MEDIUM-08` — Carta bersaglio contro posizione bersaglio

- **Termini concorrenti:** carta scelta, carta bersaglio, bersaglio, posizione bersaglio.
- **Superfici:** `simulator.practice.step_target`, `simulator.summary.target_card`, `spectator.target`, recupero e Guida.
- **Esempio:** `Target card Cxx` convive con un target che è la destinazione numerica della carta scelta.
- **Motivo:** l'oggetto mosso e la destinazione vengono entrambi chiamati target.
- **Vocabolario proposto:** carta scelta/chosen card; posizione bersaglio/target position.

### `A2-TERM-MEDIUM-09` — Inversione contro rovesciamento

- **Termini concorrenti:** inversa, inversione, rovesciamento.
- **Superfici:** glossario `inverse`, `guide.s05.row.R_U`, Guida I1, Procedure e Laboratorio.
- **Esempio:** IT «Inversione — S↔D» corrisponde a EN «Reversal».
- **Motivo:** la radice di inversa viene applicata al reversal locale.
- **Vocabolario proposto:** inversa/inverse per T⁻¹; rovesciamento/reversal per `R_U` e J.

### `A2-TERM-LOW-01` — Cronaca fuori dal recinto narrativo

- **Termini concorrenti:** Cronaca; trasformazione/riga della Tavola.
- **Superfici:** `lab.graph.raccolte.meaning`; glossario e sezione narrativa come uso corretto.
- **Esempio:** «Le 216 Cronache» in un risultato tecnico del grafo.
- **Motivo:** la Guida dichiara che i controlli usano termini tecnici.
- **Vocabolario proposto:** trasformazioni/righe nel Laboratorio; Cronaca nelle citazioni e nella cornice narrativa.

### `A2-TERM-LOW-02` — Collection/pickup/gathering

- **Termini concorrenti:** collection, pickup, gathering per raccolta.
- **Superfici:** glossario EN, Spettatore, grafi, messaggi B12 ed export.
- **Esempio:** la stessa azione fisica è chiamata `collection`, `pickup` e `gathering`.
- **Motivo:** equivalenti nel contesto, ma senza distribuzione controllata dei ruoli.
- **Vocabolario proposto:** pickup fisico; collection permutation P; gathering soltanto discorsivo.

### `A2-TERM-LOW-03` — Lacune del glossario

- **Termini mancanti principali:** disposizione, indice, colonna/mazzetto, fase, tappa, trasformazione cumulativa, trasformazione relativa, mazzi gemelli, orbita, tipo/struttura ciclica, firma di blocco, taglio/traslazione/rotazione, carta/posizione bersaglio, cronologia/storia/percorso/replay, Riconoscimento.
- **Superfici:** Guida, L90, Recognition, Cycles, Simulator/Spectator, Laboratorio, CLI.
- **Esempio:** il glossario definisce il ritorno di una riga ma non il cumulativo e il replay che ne delimitano il significato.
- **Motivo:** concetti ad alta frequenza restano governati solo da testi dispersi.
- **Vocabolario proposto:** aggiungere voci o rimandi distintivi in una futura fase di fix, senza duplicare definizioni.

### `A2-TERM-ITEN-01` — Tappa resa come Stage

- **Termini concorrenti:** IT `Tappa v_k`; EN `Stage v_k`.
- **Superfici:** `sequence.stage`, Sessione L90, Guida/CLI correlati.
- **Esempio:** `Stage v2 of 3` denomina uno stato intermedio, non uno stadio della Procedura.
- **Motivo:** IT ed EN selezionano livelli concettuali diversi.
- **Vocabolario proposto:** `Tappa/Checkpoint v_k` oppure `Stato/State v_k`.

## 24. STYLE-DEFERRED

| ID | fenomeno | decisione A2 |
|---|---|---|
| `A2-STYLE-01` | composti: `base 3/base-3`, `carta bersaglio/carta-bersaglio`, `punto fisso/punto-fisso`, `27 carte/27-card` | nessuna differenza concettuale; rinvio editoriale A3/A4 |
| `A2-STYLE-02` | maiuscole di Tavola, Laboratorio, Riconoscimento e nomi comuni corrispondenti | nessuna ambiguità materiale; rinvio della normalizzazione |
| `A2-STYLE-03` | forme tipografiche `S27/S₂₇`, `S3/S₃`, `Γ/Gamma` | stesso oggetto; rinvio tipografico |

La naturalezza generale dell'inglese, la punteggiatura e l'eleganza dell'italiano non sono state giudicate.

## 25. Copertura

| oggetto | copertura |
|---|---|
| concetti/termini inventariati | 110 righe CSV |
| classi di superfici | 24/24 |
| cataloghi | 2.048 IT + 2.048 EN; chiavi simmetriche |
| moduli con stringhe localizzate | 50 call-site modules |
| glossario | 43/43 voci, short/long IT/EN e uso |
| gruppi | H, Γ, S27 e termini legacy |
| domini numerici | 216 trasformazioni; 648 elementi; 1.728 Procedure |
| concetti fisici | deal, colonne, pile, pickup, stacking, reversal, error/recovery |
| concetti L90 | storia, cronologia, successione, cumulativo, disposizione, ritorno, replay |
| formati | GUI/CLI e TXT, HTML, LaTeX, SVG, PDF, XLSX, CSV, JSON |
| fonti | due PDF integri più fonti progettuali correnti e storiche pertinenti |

## 26. Limiti

Non restano aree materiali non verificabili. L'audit terminologico è stato svolto sulle stringhe sorgente, sui loro call site e sui generatori; non era necessario reinterpretare ogni possibile valore dinamico. L'eventuale naturalezza idiomatica di una resa semanticamente corretta è esclusa per mandato e passa ad A3/A4.

I PDF sono stati letti come fonti, non modificati né aggiunti al controllo versione. I documenti storici CLOSED non sono stati giudicati come testo corrente. Non è stato effettuato alcun accesso di rete e nessun push.

## 27. Git/filesystem

- HEAD iniziale: `4c0fd3a823eafa6e6cc25a4d9273d5dea1cd5ee8`.
- `origin/main`: `6e77210f31e467f0915e3cca0af4c9ef39328e44`.
- File autorizzati creati: `docs/audits/A2_FINAL_TERMINOLOGY_AUDIT.md`, `docs/audits/A2_FINAL_TERMINOLOGY_AUDIT.csv`.
- File intenzionali non tracciati e invariati: `Articolo.pdf`, `LIBRO_MAIN.pdf`.
- Nessun altro file creato, modificato, eliminato o tracciato.
- Commit documentale unico previsto: `docs(A2): audit final terminology consistency`.
- Nessun push; A3 non iniziato.

L'hash del commit finale, che non può essere auto-incluso senza alterare il commit stesso, è riportato nel resoconto di consegna.

## 28. Gate

| gate | esito | evidenza |
|---|---|---|
| A2-G1 superfici inventariate | PASS | 24 classi, §1/§25 |
| A2-G2 glossario completo | PASS | 43/43, §19 |
| A2-G3 termini matematici | PASS | CSV e §§8–16 |
| A2-G4 termini fisici | PASS | CSV e §§7,11,17 |
| A2-G5 termini didattici | PASS | CSV e §§9,13,18 |
| A2-G6 H/Γ/S27 | PASS | §10 |
| A2-G7 procedura/trasformazione | PASS | §8 |
| A2-G8 posizione/carta/indice | PASS | §6 |
| A2-G9 distribuzione/raccolta | PASS | §7 |
| A2-G10 rovesciamento/inversa | PASS | §11 |
| A2-G11 ritorno/percorso/storia | PASS | §12/§18 |
| A2-G12 classe/tipo ciclico | PASS | §15 |
| A2-G13 IT/EN | PASS | §§5,21 e CSV |
| A2-G14 termini delle fonti | PASS | §22 |
| A2-G15 issue completi | PASS | §23: superfici, esempio, motivo, proposta |
| A2-G16 STYLE-DEFERRED separati | PASS | §24 |
| A2-G17 nessuna correzione | PASS | solo i due deliverable A2 |
| A2-G18 nessun push | PASS | repository locale |
| A2-G19 PDF intatti/non tracciati | PASS | hash invariati; `??` |
| A2-G20 filesystem conforme | PASS | solo due deliverable più i PDF preesistenti |
| A2-G21 MD presente | PASS | questo documento |
| A2-G22 CSV presente | PASS | 110 righe dati, UTF-8 |
| A2-G23 A3 non iniziato | PASS | nessun deliverable o modifica A3/A4 |

**Conclusione:** A2 è completo come audit diagnostico. Le 16 issue restano intenzionalmente non corrette e costituiscono input per una fase successiva esplicitamente autorizzata.
