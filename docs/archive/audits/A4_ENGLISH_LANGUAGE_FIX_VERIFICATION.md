# A4-FIX — Verifica finale dell'inglese e dell'equivalenza IT/EN

Data: 28 settembre 2026. Prodotto: Gioco delle 27 carte, release candidate
4.0.0.

## 1. Stato iniziale e limiti del lavoro

Il lavoro è iniziato sul ramo `main`, con HEAD
`docs(A4): audit final English language quality` e `origin/main` fermo a
`docs(K): close technical release compartment`. Il ramo locale era avanti di
19 commit. I file tracciati erano puliti; gli unici file non tracciati erano
`Articolo.pdf` e `LIBRO_MAIN.pdf`.

Sono state corrette soltanto le 23 famiglie registrate dall'audit A4. Non sono
state cambiate la matematica validata da A1, la terminologia fissata da A2,
le formulazioni italiane consolidate da A3, le formule, i nomi dei campi,
gli schemi CSV/JSON, i token della CLI o gli altri identificatori stabili.
I due documenti storici di A4 non sono stati modificati.

## 2. Esito sintetico

| ID | Stato |
|---|---|
| A4-EN-HIGH-01 | VERIFIED FIXED |
| A4-EN-MEDIUM-01 | VERIFIED FIXED |
| A4-EN-MEDIUM-02 | VERIFIED FIXED |
| A4-EN-MEDIUM-03 | VERIFIED FIXED |
| A4-EN-MEDIUM-04 | VERIFIED FIXED |
| A4-EN-MEDIUM-05 | VERIFIED FIXED |
| A4-EN-LOW-01 | VERIFIED FIXED |
| A4-EN-LOW-02 | VERIFIED FIXED |
| A4-ITEN-MISMATCH-01 | VERIFIED FIXED |
| A4-ITEN-MISMATCH-02 | VERIFIED FIXED |
| A4-ITEN-MISMATCH-03 | HUMAN-FACING FIXED / IDENTIFIER PRESERVED |
| A4-STYLE-01 | VERIFIED FIXED |
| A4-STYLE-02 | VERIFIED FIXED |
| A4-STYLE-03 | VERIFIED FIXED |
| A4-STYLE-04 | VERIFIED FIXED |
| A4-STYLE-05 | VERIFIED FIXED |
| A4-TYPO-01 | VERIFIED FIXED |
| A4-TYPO-02 | VERIFIED FIXED |
| A4-SEM-01 | VERIFIED FIXED |
| A4-SEM-02 | VERIFIED FIXED |
| A4-SEM-03 | VERIFIED FIXED |
| A4-SEM-04 | HUMAN-FACING FIXED / IDENTIFIER PRESERVED |
| A4-SOURCE-TERM-01 | VERIFIED PRESERVED |

## 3. Verifica delle 23 famiglie

### A4-EN-HIGH-01 — messaggio type 3 / type-27

- **Problema:** l'inglese esponeva i numeri di tipo e ometteva i tre fattori.
- **Decisione:** descrivere il risultato e il requisito matematico con parole
  comprensibili, senza cambiare parser o algebra.
- **Parti modificate:** `explorer.error.type3_result`.
- **Prima:** `The result is of type 3. Use a Kronecker product to obtain a
  type-27 transformation.`
- **Dopo:** `The expression produces a permutation of 3 elements. A
  transformation of the 27 positions requires a Kronecker product with three
  factors.`
- **Verifica IT/EN:** sono presenti gli stessi tre dati dell'italiano:
  permutazione su tre elementi, trasformazione sulle 27 posizioni e prodotto
  di Kronecker con tre fattori.
- **Test:** regressione dedicata e test bilingue dell'Explorer.
- **Stato:** **VERIFIED FIXED**.

### A4-EN-MEDIUM-01 — calchi tecnici

- **Problema:** collocazioni come `all three-stage T`, `Generation PDF` e
  `verify whether it is ∈` riproducevano la sintassi italiana.
- **Decisione:** riscrivere le frasi nel loro contesto, conservando soggetto,
  formula e affermazione matematica.
- **Parti modificate:** Guida, Explorer, analisi e titoli degli export.
- **Prima:** `all three-stage T`; `Generation PDF`.
- **Dopo:** `all three-stage transformations T`; `PDF generation`.
- **Verifica IT/EN:** il confronto con le frasi italiane conferma che non sono
  stati aggiunti né rimossi requisiti matematici.
- **Test:** i18n, Guida, A1 e A2.
- **Stato:** **VERIFIED FIXED**.

### A4-EN-MEDIUM-02 — return, replay e Session

- **Problema:** i checkpoint `come back` o erano `recovered backwards`, e il
  messaggio di abbandono non parlava dei dati non salvati.
- **Decisione:** usare `reconstructed`, `replaying ... in reverse` e `discard
  unsaved changes`, mantenendo distinti ritorno compresso e riproduzione a
  ritroso.
- **Parti modificate:** CLI replay, sequenze, Sessione e Guida L90.
- **Prima:** `the intermediate checkpoints come back`; `Continue and lose
  them?`.
- **Dopo:** `The intermediate checkpoints can be reconstructed only by
  replaying the stored sequence in reverse.`; `Continue and discard them?`.
- **Verifica IT/EN:** il ritorno ricostruisce l'origine; solo il replay inverso
  ricostruisce il percorso.
- **Test:** regressione semantica A4, CLI e Sessione tramite la suite completa.
- **Stato:** **VERIFIED FIXED**.

### A4-EN-MEDIUM-03 — inglese del Protocollo

- **Problema:** il Protocollo usava collocazioni letterali e `collection` per
  l'azione fisica.
- **Decisione:** descrivere tre round, le istruzioni per chi esegue il gioco e
  le pickup instructions, senza cambiare fasi o formule.
- **Parti modificate:** riepilogo HTML, messaggio senza decomposizione e Guida
  del Protocollo.
- **Prima:** `3 turns of the same form`; `collection instructions specific to
  each phase`.
- **Dopo:** `three rounds with the same structure`; `pickup instructions for
  each phase`.
- **Verifica IT/EN:** il Protocollo inglese generato conserva ordine delle
  operazioni, formule e contenuto dell'italiano.
- **Test:** generazione HTML reale, i18n ed export.
- **Stato:** **VERIFIED FIXED**.

### A4-EN-MEDIUM-04 — calchi narrativi

- **Problema:** la prosa su Seldon e Psychohistory era comprensibile ma non
  naturale.
- **Decisione:** riscrivere la frase inglese, preservando nomi e contenuto
  narrativo.
- **Parti modificate:** glossario e storia nella Guida.
- **Prima:** `Psychohistory is the image of a theory`.
- **Dopo:** `Seldon's Psychohistory represents a theory that does not predict
  every individual event but instead sets the bounds of possible futures.`
- **Verifica IT/EN:** la funzione della teoria e delle crisi resta identica.
- **Test:** glossario, Guida e controllo dei termini storici.
- **Stato:** **VERIFIED FIXED**.

### A4-EN-MEDIUM-05 — paragrafi troppo densi

- **Problema:** quattro passaggi concentravano premessa, azione, eccezione e
  conseguenza in un solo periodo.
- **Decisione:** dividerli in unità più brevi, lasciando formule e condizioni
  accanto alla relativa spiegazione.
- **Parti modificate:** decomposizioni, tabelloni del PDF dettagliato, Sessione
  e riconoscimento A8.
- **Prima:** un unico periodo esteso per ogni passaggio.
- **Dopo:** paragrafi distinti per condizione, risultato ed eccezione.
- **Verifica IT/EN:** nessuna condizione o eccezione dell'italiano è stata
  eliminata.
- **Test:** Guida, A1, A2 e controllo manuale in continuità.
- **Stato:** **VERIFIED FIXED**.

### A4-EN-LOW-01 — articoli, preposizioni e referenti

- **Problema:** cinque frasi usavano preposizioni o referenti poco naturali.
- **Decisione:** esplicitare posizione, candidato e azione della
  trasformazione.
- **Parti modificate:** riconoscimento, Tavola e passaggi collegati della
  Guida.
- **Prima:** `the card in 13`; `the order of the T just calculated`.
- **Dopo:** `the card at position 13`; `the order of the T just computed`.
- **Verifica IT/EN:** carta, posizione e trasformazione restano oggetti
  distinti.
- **Test:** i18n, Guida e A2.
- **Stato:** **VERIFIED FIXED**.

### A4-EN-LOW-02 — abbreviazioni e microtesti

- **Problema:** otto etichette erano troppo telegrafiche fuori da colonne
  realmente ristrette.
- **Decisione:** espandere solo le abbreviazioni poco chiare.
- **Parti modificate:** cicli, Explorer, distribuzione ed export.
- **Prima:** `len`; `perm`; `comb.`; `ord.`.
- **Dopo:** `Length`; `Permutation`; `Combinations`; `Order`.
- **Verifica IT/EN:** le etichette descrivono gli stessi valori dell'italiano.
- **Test:** catalogo A4 e i18n.
- **Stato:** **VERIFIED FIXED**.

### A4-ITEN-MISMATCH-01 — arrangement e riga della Tavola

- **Problema:** una riga della Tavola era chiamata arrangement.
- **Decisione:** usare il termine A2 `Table row`.
- **Parti modificate:** `nav.in_table`.
- **Prima:** `Arrangement #{number} of the table`.
- **Dopo:** `Table row #{number}`.
- **Verifica IT/EN:** corrisponde a `Riga #{number} della Tavola`; arrangement
  resta riservato all'ordine corrente del mazzo.
- **Test:** regressione IT/EN dedicata e A2.
- **Stato:** **VERIFIED FIXED**.

### A4-ITEN-MISMATCH-02 — etichette del PDF inglese

- **Problema:** il PDF dettagliato inglese conteneva etichette italiane.
- **Decisione:** localizzare soltanto il testo per il lettore.
- **Parti modificate:** generatore del PDF dettagliato e cinque nuove coppie
  di chiavi IT/EN.
- **Prima:** `Mescolamento`, `impilamento`, `TABELLONE DI T`.
- **Dopo:** `Shuffle`, `stacking`, `BOARD OF T`.
- **Verifica IT/EN:** indici C, matrici, formule, ordine e struttura dei dati
  sono invariati.
- **Test:** regressione PDF, estrazione testuale e controllo visivo dei tre PDF
  inglesi.
- **Stato:** **VERIFIED FIXED**.

### A4-ITEN-MISMATCH-03 — descrizione nell'intestazione CSV

- **Problema:** la descrizione leggibile `lista 0..26` restava italiana.
- **Decisione:** lasciare immutato il nome stabile e localizzare solo la nota
  tra parentesi quadre.
- **Parti modificate:** intestazione degli export CSV grezzi e di analisi.
- **Prima:** `T_permutazione  [lista 0..26]`.
- **Dopo:** `T_permutazione  [list 0..26]`.
- **Verifica IT/EN:** nomi, ordine delle colonne e riconoscimento dello schema
  non cambiano.
- **Test:** compatibilità CSV dedicata ed export reale.
- **Stato:** **HUMAN-FACING FIXED / IDENTIFIER PRESERVED**.

### A4-STYLE-01 — American English

- **Problema:** la prosa mescolava grafie britanniche e americane.
- **Decisione:** adottare American English per la prosa corrente.
- **Parti modificate:** catalogo inglese, Guida e glossario.
- **Prima:** `centre`, `analyse`, `colour`, `recognised`, `realised`,
  `catalogue`, `factorisation`.
- **Dopo:** `center`, `analyze`, `color`, `recognized`, `realized`, `catalog`,
  `factorization`.
- **Verifica IT/EN:** cambia soltanto la grafia inglese. `fibre` resta il
  termine matematico specialistico; gli esempi di sintassi accettata dal
  parser conservano l'ASCII richiesto.
- **Test:** scansione del catalogo e regressione A4.
- **Stato:** **VERIFIED FIXED**.

### A4-STYLE-02 — numeri

- **Problema:** 21 testi inglesi usavano spazi come separatori delle migliaia.
- **Decisione:** usare la convenzione americana nella prosa e la formattazione
  dipendente dalla lingua per i valori dinamici.
- **Parti modificate:** catalogo inglese e scenari numerici della Guida.
- **Prima:** `1 728`; `46 656`; `23 887 872`.
- **Dopo:** `1,728`; `46,656`; `23,887,872`.
- **Verifica IT/EN:** i valori sono identici; l'italiano conserva gli spazi.
- **Test:** regressione numerica A4, i18n e A3.
- **Stato:** **VERIFIED FIXED**.

### A4-STYLE-03 — virgolette e punteggiatura

- **Problema:** dieci testi inglesi usavano caporali.
- **Decisione:** usare virgolette inglesi curve nella prosa e mantenere
  virgolette dritte o backtick dove il formato lo richiede.
- **Parti modificate:** messaggi, Guida, glossario e documenti generati.
- **Prima:** `«Save»`.
- **Dopo:** `“Save”`.
- **Verifica IT/EN:** il contenuto citato non cambia; l'italiano conserva la
  propria convenzione.
- **Test:** assenza di caporali nel catalogo inglese e test i18n.
- **Stato:** **VERIFIED FIXED**.

### A4-STYLE-04 — notazione matematica

- **Problema:** le parti inglesi ricche mostravano ancora notazione ASCII.
- **Decisione:** usare Unicode dove il canale lo supporta e preservare ASCII
  e LaTeX nei rispettivi formati.
- **Parti modificate:** interfaccia, Guida, HTML e SVG.
- **Prima:** `S27`, `S3`, `MSC^k`, `3^(2+i)`, `x`, `o`.
- **Dopo:** `S₂₇`, `S₃`, `MSCᵏ`, `3²⁺ⁱ`, `⊗`, `∘`.
- **Verifica IT/EN:** cambia solo la resa tipografica, non la formula.
- **Test:** regressione A4, A1 e campioni LaTeX/SVG/HTML.
- **Stato:** **VERIFIED FIXED**.

### A4-STYLE-05 — maiuscole nei titoli

- **Problema:** i titoli alternavano title case e sentence case.
- **Decisione:** usare sentence case, lasciando maiuscoli i nomi ufficiali
  delle viste e gli acronimi.
- **Parti modificate:** titoli di analisi, anteprima, coniugio, Cayley e Guida.
- **Prima:** `Permutation Multiplicity Analysis`.
- **Dopo:** `Permutation multiplicity analysis`.
- **Verifica IT/EN:** la gerarchia dei titoli e i nomi delle viste restano
  riconoscibili.
- **Test:** i18n e Guida.
- **Stato:** **VERIFIED FIXED**.

### A4-TYPO-01 — plurali dinamici

- **Problema:** 18 template producevano forme come `1 files` o `1 stages`.
- **Decisione:** usare formulazioni invarianti rispetto al numero, senza
  cambiare placeholder.
- **Parti modificate:** stato, cache, decomposizioni, export, pratica, CLI e
  ritorno compresso.
- **Prima:** `1 combinations`; `1 files`; `1 stages`.
- **Dopo:** `Combination count: 1`; `File count: 1`; `original stage count: 1`.
- **Verifica IT/EN:** il conteggio e il significato coincidono con l'italiano.
- **Test:** tutti i 18 template sono verificati con 0, 1 e 2.
- **Stato:** **VERIFIED FIXED**.

### A4-TYPO-02 — nomi propri

- **Problema:** `numpy` e il nome del prodotto avevano maiuscole incoerenti.
- **Decisione:** usare le grafie ufficiali.
- **Parti modificate:** Guida, rapporto di verifica e piè di pagina degli
  export.
- **Prima:** `numpy`; `Gioco delle 27 Carte`.
- **Dopo:** `NumPy`; `Gioco delle 27 carte`.
- **Verifica IT/EN:** nessun identificatore di libreria o package è cambiato.
- **Test:** i18n e A4.
- **Stato:** **VERIFIED FIXED**.

### A4-SEM-01 — Procedure tecnica e procedure comune

- **Problema:** la maiuscola non distingueva sempre l'oggetto tecnico I1 dal
  nome comune.
- **Decisione:** classificare i 57 contesti e correggere solo quelli ambigui.
- **Parti modificate:** catalogo inglese, Guida, CLI e Sessione.
- **Prima:** usi alternati di `procedure` e `Procedure` senza regola chiara.
- **Dopo:** `A Procedure is ...` per I1; `physical procedure` per il nome
  comune.
- **Verifica IT/EN:** l'oggetto delle 1,728 Procedure resta distinto dalla
  descrizione di una procedura ordinaria.
- **Test:** regressione semantica A4 e A2.
- **Stato:** **VERIFIED FIXED**.

### A4-SEM-02 — pickup, collection ed element

- **Problema:** `collection` indicava talvolta il gesto, talvolta P, talvolta
  un elemento arbitrario di H.
- **Decisione:** usare `pickup` per il gesto, `pickup permutation` o
  `collection permutation` per P e `transformation` o `element` per gli altri
  oggetti.
- **Parti modificate:** Protocollo, Explorer, glossario e Guida.
- **Prima:** `three collections Aᵢ`; `collection instructions`.
- **Dopo:** `three transformations Aᵢ`; `pickup instructions`.
- **Verifica IT/EN:** i confini terminologici fissati da A2 sono preservati.
- **Test:** regressione semantica A4, glossario e A2.
- **Stato:** **VERIFIED FIXED**.

### A4-SEM-03 — stage, phase, step e checkpoint

- **Problema:** due frasi usavano step o stage per concetti diversi da quelli
  stabiliti.
- **Decisione:** usare `phase` per il round fisico e descrivere separatamente
  il numero originario di stadi.
- **Parti modificate:** istruzioni del Simulatore e ritorno della sequenza.
- **Prima:** `at step i`; `instead of {stages} stages`.
- **Dopo:** `during phase i`; `original stage count: {stages}`.
- **Verifica IT/EN:** stage resta `Pᵢ ∘ MSC ∘ Jᵢ`, phase resta fisica, step è
  un'operazione e checkpoint è `v_k`.
- **Test:** regressione semantica A4 e A2.
- **Stato:** **VERIFIED FIXED**.

### A4-SEM-04 — identificatori macchina visibili

- **Problema:** alcuni token italiani o misti sono visibili in CLI, CSV, JSON
  e XLSX, ma fanno parte di contratti stabili.
- **Decisione:** conservare i token e aggiungere spiegazioni inglesi dove
  servono.
- **Parti modificate:** help dell'opzione CLI `--what` e descrizioni CSV.
- **Prima:** token come `successione`, `cronologia` e `proprieta` senza una
  spiegazione inglese adiacente.
- **Dopo:** `stable export token: successione (sequence), replay, cronologia
  (history), proprieta (property), or mapping`.
- **Verifica IT/EN:** scelte CLI, campi CSV/JSON, nomi dei fogli XLSX e valori
  di schema restano invariati.
- **Test:** regressione CLI, compatibilità CSV, JSON e XLSX reali.
- **Stato:** **HUMAN-FACING FIXED / IDENTIFIER PRESERVED**.

### A4-SOURCE-TERM-01 — termini storici e narrativi

- **Problema:** l'audit richiedeva di distinguere i termini intenzionali da
  errori di traduzione.
- **Decisione:** preservare i termini e migliorare soltanto la prosa
  circostante quando necessario.
- **Parti modificate:** nessun termine della fonte; solo alcune frasi del
  glossario e della storia.
- **Prima:** `simple arrangement`, `G/Gaia`, `Chronicle`, `Jester`,
  `Deck-World`, `Seldon`, `Psychohistory`, `First Crisis`, `Second Crisis`.
- **Dopo:** gli stessi termini, invariati.
- **Verifica IT/EN:** ciascun termine resta nel proprio contesto storico o
  narrativo segnalato.
- **Test:** regressione dedicata dei termini della fonte.
- **Stato:** **VERIFIED PRESERVED**.

## 4. Export e contratti stabili

È stato generato una sola volta un campione inglese reale per ciascuno dei
dieci formati richiesti: TXT, HTML, LaTeX, SVG, PDF standard, PDF esteso, PDF
dettagliato, XLSX, CSV e JSON. Sono stati controllati lingua, titoli, numeri,
notazione, etichette, schema e identificatori. Per i tre PDF sono stati
controllati sia il testo estratto sia la resa grafica.

`CSV_HEADER` conserva il contratto storico; la funzione di localizzazione ne
cambia soltanto la descrizione leggibile. Lo schema JSON resta
`gioco27.esperimento`, versione 1. I nomi stabili dell'XLSX e le scelte della
CLI restano invariati.

## 5. Verifiche eseguite

| Area | Esito |
|---|---:|
| A4-FIX mirato | 9 superati |
| i18n IT/EN | 166 superati, 20 esclusi |
| Glossario | 16 superati, 1 escluso |
| Guida | 28 superati |
| CLI | 13 superati |
| Export | 82 superati |
| A3/A3-FIX | 11 superati |
| A2/A2-FIX | 26 superati |
| A1/A1-FIX | 6 superati |
| Baseline matematica | 25 superati |
| K/K0 | 36 superati, 9 esclusi |
| Analisi statica `pyflakes` | nessun avviso |
| `git diff --check` | superato, anche sulle modifiche preparate per il commit |
| Suite completa finale | 2.105 superati, 318 esclusi |

Gli errori incontrati durante i gruppi mirati erano aspettative testuali
legate alle vecchie formulazioni A4: conteggio del catalogo, messaggio type-3,
grafia `NumPy`, numeri con separatori italiani, microtesto CSV e notazione
ASCII nelle parti inglesi ricche. Sono state aggiornate soltanto queste
aspettative; non sono emersi errori matematici, terminologici o dell'italiano.

La prima esecuzione completa ha inoltre individuato sei aspettative residue
su numeri, notazione, etichette PDF e titoli, più un problema reale: la
localizzazione dell'intestazione CSV aveva introdotto una dipendenza dal
modulo matematico `core.permutations` verso i18n. La funzione di localizzazione
è stata spostata nel modulo di export, ripristinando il grafo delle
dipendenze. I test mirati successivi hanno dato 228 superati e 23 esclusi; la
seconda esecuzione completa, necessaria dopo queste correzioni, è quella
finale riportata nella tabella.

Le 318 esclusioni finali dipendono dall'ambiente: 307 richiedono un display,
9 il modulo facoltativo `build`, una `pikepdf` per la deduplicazione dei
caratteri e una `pypdfium2`. `pyflakes` 3.4.0 è stato eseguito da una copia
temporanea e non ha prodotto avvisi.

## 6. Conclusione

Le 23 famiglie sono chiuse. L'inglese corrente segue una convenzione americana
coerente ed è equivalente all'italiano nei contenuti. Le eccezioni sono
motivate: `fibre` è un termine matematico specialistico; LaTeX usa la propria
sintassi; CLI/TXT, parser e formati macchina conservano ASCII e identificatori
quando la compatibilità lo richiede.

La verifica tecnica finale di RC2 può iniziare in una fase successiva. A5 non
è stato avviato e non è stato eseguito alcun push.
