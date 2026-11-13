# A4 — Audit finale dell'inglese e dell'equivalenza IT/EN

Data: 27 settembre 2026. Prodotto: Gioco delle 27 carte, release candidate
4.0.0.

## 1. Stato e perimetro

Audit diagnostico dell'intero inglese corrente destinato all'utente e della
sua equivalenza con l'italiano consolidato da A3-FIX. Lo stato iniziale era:

- ramo `main`, avanti di 18 commit rispetto a `origin/main`;
- HEAD: `docs(A3): close Italian language verification`;
- nessuna modifica tracciata;
- soli `Articolo.pdf` e `LIBRO_MAIN.pdf` non tracciati.

Sono autorizzati e prodotti soltanto questo documento e il CSV associato.
Non sono stati corretti cataloghi, codice, test, formule, interfaccia,
documentazione corrente o schemi. A4-FIX e A5 non sono iniziati.

## 2. Metodo

La verifica ha combinato:

1. confronto integrale delle 2.108 coppie di chiavi IT/EN;
2. lettura delle stringhe nel loro contesto funzionale, raggruppate per le 43
   famiglie di prefisso del catalogo;
3. lettura continua delle 41 sezioni effettive della Guida, nell'ordine
   definito da `SEZIONI`;
4. controllo di termine, definizione breve e definizione estesa dei 63 lemmi;
5. espansione dei conteggi dinamici per 0, 1 e 2;
6. costruzione del parser inglese e lettura dell'help principale e degli otto
   sottocomandi;
7. generazione e lettura di campioni reali TXT, HTML, LaTeX, SVG, PDF, XLSX,
   CSV e JSON;
8. estrazione del testo e ispezione visiva della prima pagina dei PDF
   standard, esteso e dettagliato;
9. ricerca mirata di false friends, calchi, varianti US/UK, numeri,
   virgolette, notazione e termini controllati.

Per «unità testuale» si intende ogni riga non vuota ottenuta separando i
valori del catalogo sui ritorni a capo: il conteggio riproducibile è 2.431.

## 3. Vincoli A1/A2/A3

A1/A1-FIX, A2/A2-FIX e A3/A3-FIX sono assunti come vincolanti. L'italiano
corrente determina il contenuto, non la sintassi inglese. Non sono state
riaperte matematica, composizione, formule, convenzioni, distinzione fra
carta/posizione/indice, disposizione/trasformazione/permutazione, oppure gli
schemi macchina.

## 4. Copertura

| Area | Copertura verificata |
|---|---:|
| Chiavi inglesi | 2.108 / 2.108 |
| Chiavi italiane corrispondenti | 2.108 / 2.108 |
| Chiavi mancanti o aggiuntive | 0 |
| Differenze nei placeholder IT/EN | 0 |
| Unità testuali non vuote | 2.431 |
| Famiglie funzionali del catalogo | 43 / 43 |
| Chiavi `guide.*` | 458 / 458 |
| Sezioni effettive della Guida | 41 / 41 |
| Lemmi del glossario | 63 / 63 (56 matematici, 7 narrativi) |
| Chiavi del glossario | 189 / 189 |
| Comandi CLI | 8 / 8, più help principale |
| Formati di export | 8 / 8, con 10 campioni reali |
| Documenti correnti | README e note 4.0.0 |

Le superfici comprendono finestra principale, menu, schede, filtri,
Simulatore, Pratica, Spettatore, Tavola, Explorer, Riconoscimento,
Laboratorio, Presentazione, Protocollo, Sessione/L90, dialoghi, errori,
banner, suggerimenti, Guida, glossario, CLI ed export.

## 5. Equivalenza IT/EN

La copertura strutturale è completa: le chiavi e i placeholder coincidono.
L'equivalenza semantica non è però completa. Sono state trovate tre famiglie
`ITEN-MISMATCH`:

- `nav.in_table` chiama *arrangement* una riga/trasformazione della Tavola;
- il PDF dettagliato inglese contiene etichette italiane;
- l'intestazione CSV inglese conserva la descrizione italiana `lista 0..26`.

La simmetria delle chiavi, quindi, non garantisce equivalenza del testo
effettivamente mostrato.

## 6. Grammatica

La grammatica di base è generalmente comprensibile. Il difetto sistematico è
la flessione dei conteggi: 18 template producono forme come `1 files`,
`1 decompositions`, `1 rows`, `1 processes`, `1 procedures` o `1 stages`.
Sono stati controllati esplicitamente 0, 1 e 2. Sono inoltre registrati due
difetti locali di maiuscole proprie (`numpy`, nome del prodotto).

## 7. Sintassi

Sono presenti costruzioni modellate sull'italiano, per esempio `all
three-stage T`, `Generation PDF`, `verify whether it is ∈`, `the card in 13`
e `the order of the T just calculated`. La direzione proposta non è una
traduzione più letterale, ma una ristrutturazione idiomatica che conservi il
medesimo contenuto.

## 8. Naturalezza

La risposta alla domanda «un redattore tecnico madrelingua scriverebbe
proprio così?» è negativa per sei famiglie: messaggio sul `type 3`,
collocazioni tecniche della Guida, ritorno/riproduzione a ritroso, protocollo,
prosa narrativa e quattro paragrafi troppo densi. Gli altri periodi lunghi
sono stati classificati `LONG-BUT-CLEAR` e non sono issue.

## 9. Calchi dall'italiano

I calchi più evidenti sono:

- `Psychohistory is the image of a theory`;
- `the figure of one who is not content that the Plan works`;
- `the intermediate checkpoints come back`;
- `every checkpoint recovered backwards`;
- `Continue and lose them?`;
- `Generation PDF`.

Sono registrati nelle famiglie `A4-EN-MEDIUM-01`, `02` e `04`.

## 10. False friends

Sono state cercate tutte le parole indicate dal mandato: `actual`,
`eventually`, `sensible`, `argument`, `disposition`, `resume`, `comprise`,
`convenient`, `evidence`, `verify`, `control`, `current`, `return`,
`passage`, `correspondence`, `resulting`, `respective` e `proper`. Gli usi
incontrati di *current*, *resulting*, *same*, *corresponding* e *return* sono
per lo più inglesi autentici; non è stata aperta una famiglia di false friend
autonoma. I problemi reali sono calchi sintattici o terminologici già
registrati.

## 11. Articoli e preposizioni

I nomi ufficiali delle viste funzionano come nomi propri nelle azioni:
`Open in Explorer`, `Open in Cycles`, `Use as current T`. L'articolo è
corretto quando il nome modifica un sostantivo (`the Explorer tab`) o in un
possessivo (`the Explorer's T`). Non è stata rilevata un'oscillazione
sistematica `Explorer/the Explorer` nello stesso costrutto. Restano cinque
microproblemi di preposizione o referente, raccolti in `A4-EN-LOW-01`.

## 12. Terminologia vincolata

Le distinzioni card/position/index, arrangement/transformation/permutation,
deal/pickup, chosen card/target position, conjugacy class/cycle type,
permutation vector/canonical form/block signature sono generalmente
rispettate. L'eccezione concreta arrangement/transformation è
`nav.in_table`. Le famiglie `Procedure` e pickup/collection richiedono una
revisione contestuale vincolata, non sostituzioni globali.

## 13. Stage/phase/step/checkpoint

La distinzione è quasi sempre conservata:

- *stage* per `Pᵢ ∘ MSC ∘ Jᵢ`;
- *phase* per l'esecuzione fisica/interattiva;
- *step* per una singola istruzione o operazione;
- *checkpoint* per `v_k`.

Due casi sono da riesaminare: `at step i` nel Simulatore e `instead of
{stages} stages` nella successione L90. Sono `A4-SEM-03`.

## 14. Inverse/reversal

La distinzione fra *inverse* (`T⁻¹`) e *reversal* (`R_U`, `J`) è mantenuta.
Gli usi verbali di *reverse* e *flip* descrivono gesti fisici o complementi
di cifre e non introducono un terzo concetto. Nessun issue autonomo.

## 15. Return/replay/recovery

I tre concetti restano semanticamente distinti: return row, compressed
return, backward replay, recovery. Il problema è linguistico, non
concettuale: `come back`, `recovered backwards` e `succession of Procedures`
sono poco idiomatici. La famiglia è `A4-EN-MEDIUM-02`.

## 16. Pickup/collection

Sono state trovate 22 chiavi contenenti *collection/collecting*. Gli usi
qualificati `collection permutation` possono essere legittimi; 12 contesti
richiedono revisione perché *collection* indica ora un'azione fisica, ora
`Aᵢ`, ora un elemento arbitrario di H. La correzione futura dovrà usare
*pickup* per il gesto, *pickup permutation* o *collection permutation* per P,
e *transformation/element* per gli oggetti generali. Issue `A4-SEM-02`.

## 17. Istruzioni

Gli imperativi principali sono coerenti: `Select`, `Choose`, `Enter`,
`Click`, `Double-click`, `Press`, `Open`, `Check`, `Compare`. Non compare il
calco *make a click*. `Click` e `Press` sono distinti in modo ragionevole fra
azioni del mouse e pulsanti/tasti. Restano solo le collocazioni locali già
registrate.

## 18. Errori e messaggi

La maggioranza dei messaggi indica errore, campo e forma attesa. Il caso
grave è `explorer.error.type3_result`: espone tipi numerici poco trasparenti
e omette il requisito dei tre fattori presente nell'italiano. È
`A4-EN-HIGH-01`. I messaggi di schema hanno inoltre virgolette francesi,
problema stilistico separato.

## 19. Plurali

Le coppie esplicite `analysis.detail.multiplicity.one/many` e
`simulator.summary.errors.one/many` sono corrette. Non lo sono 18 template
generici che usano sempre il plurale. La correzione futura deve essere
locale-aware e non deve cambiare placeholder o campi macchina. Issue
`A4-TYPO-01`.

## 20. Maiuscole

Si propone questa convenzione:

- nomi ufficiali delle viste con iniziale maiuscola;
- titoli e intestazioni in sentence case;
- acronimi e simboli secondo la loro grafia;
- termine tecnico `Procedure` maiuscolo solo quando indica l'oggetto I1.

Il catalogo alterna sentence case e title case in almeno 14 titoli. La
famiglia è `A4-STYLE-05`.

## 21. Trattini e composti

Sono stati controllati `base-3`, `27-card`, `target position`, `fixed point`,
`card-by-card`, `step-by-step`, `user-facing`, `machine-readable`,
`full-screen` e `simple-pickup`. Molte alternanze sono grammaticalmente
legittime perché il composto è attributivo in un contesto e nominale o
avverbiale in un altro. Non è stata aperta una famiglia automatica basata
solo sulla presenza del trattino; i casi realmente innaturali confluiscono
nelle famiglie di naturalezza.

## 22. Numeri

La convenzione inglese rilevata e proposta è:

- `1,728`, `46,656`, `23,887,872`;
- `0.2 s`;
- intervalli `0–26`.

Ventuno chiavi inglesi usano invece spazi come separatori delle migliaia,
ereditando la convenzione italiana. I valori dinamici passati a
`format_integer` sono già formattati con la virgola in inglese. Issue
`A4-STYLE-02`.

## 23. Virgolette e punteggiatura

Dieci chiavi inglesi contengono caporali. Si propone:

- virgolette inglesi curve per citazioni e nomi di controlli;
- backtick o virgolette dritte per codice e identificatori;
- nessun caporale nell'inglese corrente;
- ellissi Unicode nella prosa e tre punti soltanto nei frammenti ASCII o di
  codice che lo richiedono.

La famiglia è `A4-STYLE-03`.

## 24. Notazione matematica

La matematica è equivalente, ma la tipografia per canale non lo è. Sono state
contate 57 chiavi con almeno una forma ricca ancora resa come `S27`, `S3`,
`MSC^k`, `3^(2+i)`, `x` o `o`. Anche i PDF standard ed esteso usano `x/o`.
La direzione è `S₂₇`, `S₃`, `MSCᵏ`, `3²⁺ⁱ`, `⊗`, `∘` nei canali ricchi;
LaTeX proprio nei `.tex`; identificatori stabili nei formati macchina. Issue
`A4-STYLE-04`.

## 25. Glossario

Controllati 63/63 lemmi: termine, definizione breve, definizione estesa,
rimandi e corrispondente italiano. Le distinzioni concettuali sono per lo più
corrette. Gli issue trasversali sono numeri, variante US/UK, `Procedure`,
collection/pickup, `S27/S3` e il calco narrativo su Psychohistory. Non sono
stati trovati lemmi mancanti o short/long in contraddizione matematica.

## 26. Guida

Letta in continuità nell'ordine reale di 41 sezioni, non nel semplice ordine
numerico delle chiavi. Sono state controllate tutte le 458 chiavi `guide.*`,
compresi i moduli I1–I6, macchina dell'oblio, Tavola/tabellone e storia.
Quattro passaggi sono `TOO-DENSE`; gli altri lunghi sono
`LONG-BUT-CLEAR`. Le transizioni e i riferimenti sono comprensibili; gli
issue sono quelli elencati nel CSV.

## 27. CLI

Controllati help principale e sottocomandi `validate`, `replay`, `recognize`,
`property`, `sequence`, `export`, `compare`, `selftest`. I nomi dei comandi
sono stabili. Problemi: variante `recognise`, frase `succession of
Procedures`, output del replay non idiomatico, plurali dinamici e valori
italiani stabili di `--what` esposti nell'help. Quest'ultimo è un vincolo di
compatibilità (`A4-SEM-04`), non un'autorizzazione a rinominare i token.

## 28. Export

Generati e letti dieci campioni reali:

- TXT;
- HTML Protocollo;
- LaTeX;
- SVG;
- PDF standard;
- PDF esteso;
- PDF dettagliato;
- XLSX;
- CSV;
- JSON.

I tre PDF sono stati estratti e renderizzati. Layout, griglie, carte,
intestazioni e marcatori sono leggibili e non sovrapposti. Il PDF dettagliato
inglese contiene però etichette italiane; il CSV contiene `lista 0..26`.
XLSX e JSON espongono identificatori o valori versionati misti/italiani,
registrati come vincolo. I temporanei di audit devono essere rimossi prima
della chiusura.

## 29. README/release notes

README e note 4.0.0 sono documenti correnti prevalentemente italiani. Sono
state controllate le porzioni inglesi, i nomi di funzioni, i comandi, i nomi
di librerie e i termini di prodotto; non esiste una sezione inglese continua
da revisionare. Gli identificatori tecnici non sono stati trattati come
prosa.

## 30. Variante US/UK

Il progetto è misto. Prevalgono le forme americane: `center` 34 contro
`centre` 10; `analyze` 13 contro `analyse` 1; `color` 21 contro `colour` 2.
Restano però `recognised/recognise`, `realised/realises`, `fibre`, `centre` e
`catalogue`. Poiché l'uso maggioritario e numerose API/microcopie sono
americani, A4 propone **American English** come convenzione. Issue
`A4-STYLE-01`.

## 31. Source terms

Sono stati preservati e verificati nei contesti storici/narrativi: *simple
arrangement*, G/Gaia, Chronicle, Giullare/Jester, Deck-World, Seldon,
Psychohistory, First Crisis e Second Crisis. Non invadono sistematicamente le
parti tecniche. La famiglia `A4-SOURCE-TERM-01` documenta che non vanno
normalizzati; l'inglese circostante può invece essere migliorato.

## 32. Issue

| ID | Classe | Sintesi | Occorrenze |
|---|---|---|---:|
| A4-EN-HIGH-01 | EN-HIGH | Messaggio opaco `type 3/type-27` | 1 |
| A4-EN-MEDIUM-01 | EN-MEDIUM | Collocazioni tecniche calcate | 9 |
| A4-EN-MEDIUM-02 | EN-MEDIUM | Return/replay/session non idiomatici | 4 |
| A4-EN-MEDIUM-03 | EN-MEDIUM | Inglese del Protocollo | 5 |
| A4-EN-MEDIUM-04 | EN-MEDIUM | Calchi narrativi | 3 |
| A4-EN-MEDIUM-05 | EN-MEDIUM | Paragrafi TOO-DENSE | 4 |
| A4-EN-LOW-01 | EN-LOW | Articoli, preposizioni, referenti | 5 |
| A4-EN-LOW-02 | EN-LOW | Abbreviazioni telegrafiche | 8 |
| A4-ITEN-MISMATCH-01 | ITEN-MISMATCH | Arrangement usato per una riga della Tavola | 1 |
| A4-ITEN-MISMATCH-02 | ITEN-MISMATCH | Etichette italiane nel PDF inglese | 4 |
| A4-ITEN-MISMATCH-03 | ITEN-MISMATCH | Descrizione italiana nell'header CSV | 1 |
| A4-STYLE-01 | STYLE | Variante US/UK mista | 5 famiglie |
| A4-STYLE-02 | STYLE | Raggruppamento numerico italiano | 21 |
| A4-STYLE-03 | STYLE | Virgolette e punteggiatura miste | 10 |
| A4-STYLE-04 | STYLE | Notazione ASCII nei canali ricchi | 57 |
| A4-STYLE-05 | STYLE | Title case/sentence case misti | 14 |
| A4-TYPO-01 | TYPO | Plurali dinamici per 1 | 18 |
| A4-TYPO-02 | TYPO | Maiuscole di nomi propri | 3 |
| A4-SEM-01 | SEMANTICALLY-CONSTRAINED | Procedure tecnico/comune | 57 chiavi |
| A4-SEM-02 | SEMANTICALLY-CONSTRAINED | Pickup/collection/elemento | 12 da rivedere |
| A4-SEM-03 | SEMANTICALLY-CONSTRAINED | Stage/phase/step/checkpoint | 2 |
| A4-SEM-04 | SEMANTICALLY-CONSTRAINED | Identificatori macchina visibili | 3 superfici |
| A4-SOURCE-TERM-01 | SOURCE-TERM | Termini storici intenzionali | 10 termini |

Conteggio per classificazione primaria:

| Classe | Numero |
|---|---:|
| EN-HIGH | 1 |
| EN-MEDIUM | 5 |
| EN-LOW | 2 |
| ITEN-MISMATCH | 3 |
| STYLE | 5 |
| TYPO | 2 |
| SEMANTICALLY-CONSTRAINED | 4 |
| SOURCE-TERM | 1 |
| **Totale famiglie** | **23** |

Il CSV associato contiene testo corrente, riferimento italiano, problema,
direzione, classe di equivalenza A/B/C/D, vincoli, posizione e ricorrenze.

## 33. Vincoli semantici

Le direzioni proposte non autorizzano modifiche automatiche. In particolare:

- niente sostituzione globale `collection → pickup`;
- niente sostituzione globale `procedure → Procedure`;
- niente rinomina di `Stage0/1/2`, campi CSV/JSON, fogli XLSX, token CLI o
  chiavi di persistenza;
- niente cambi a formule, ordine dei fattori, inversa/rovesciamento o
  convenzioni numeriche di macchina;
- le differenze di struttura inglese/italiano classificate D sono legittime.

## 34. Copertura e limiti

La GUI nativa non è stata aperta perché il Python disponibile non trova una
installazione Tcl/Tk utilizzabile. Questo limita soltanto l'ispezione visiva
live: testi, composizione delle superfici, catalogo, Guida, glossario, CLI ed
export sono stati verificati direttamente. I PDF sono stati invece
renderizzati e ispezionati visivamente. Poppler ha segnalato font di sistema
non disponibili, ma i font incorporati/fallback hanno prodotto pagine
leggibili; non è stato classificato un difetto di layout.

## 35. Git/filesystem

A chiusura dell'audit:

- ramo `main`;
- un solo commit documentale A4;
- nessun push;
- nessuna modifica a file diversi dai due documenti A4;
- temporanei di export rimossi;
- file tracciati puliti dopo il commit;
- soli `Articolo.pdf` e `LIBRO_MAIN.pdf` non tracciati.

PDF invariati e non tracciati.

## 36. Criteri di chiusura

| Gate | Esito | Evidenza |
|---|---|---|
| A4-G1–G2 | PASS | 2.108 chiavi, 43 famiglie funzionali |
| A4-G3 | PASS | Guida letta in continuità, 41/41 sezioni |
| A4-G4 | PASS | Glossario 63/63 |
| A4-G5–G12 | PASS | confronto IT/EN, grammatica, sintassi, naturalezza, calchi, false friends, articoli, plurali |
| A4-G13–G17 | PASS | terminologia e quattro distinzioni controllate |
| A4-G18 | PASS | help principale e 8 sottocomandi CLI |
| A4-G19 | PASS | 8 formati, 10 campioni; 3 PDF renderizzati |
| A4-G20–G23 | PASS | documenti correnti, US/UK, numeri, punteggiatura, source terms |
| A4-G24 | PASS | 23 famiglie con evidenza concreta nel CSV |
| A4-G25–G27 | PASS | nessuna correzione, A5 non iniziato, nessun push |
| A4-G28–G29 | PASS | temporanei rimossi; PDF sorgente intatti |
| A4-G30–G31 | PASS | Markdown e CSV presenti |

I temporanei sono stati rimossi e i due documenti verificati. Con il singolo
commit documentale richiesto, A4 soddisfa tutti i criteri di chiusura. Gli
issue restano intenzionalmente non corretti e costituiscono l'ingresso
esclusivo di un eventuale A4-FIX separato.
