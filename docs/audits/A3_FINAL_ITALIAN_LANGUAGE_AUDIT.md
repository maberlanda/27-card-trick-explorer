# A3 — Audit finale linguistico italiano

**Prodotto:** Gioco delle 27 carte — release candidate 4.0.0

**Data:** 2026-09-27

**Natura:** audit diagnostico; nessuna correzione linguistica applicata

**Esito del gate:** **A3 CONCLUSO CON ISSUE APERTI**

## 1. Stato e perimetro

L'audit è iniziato sul ramo main, sul commit corrente successivo ad A2-FIX, con il ramo locale avanti rispetto a origin/main. Il perimetro comprende tutto l'italiano user-facing corrente: UI, Guida, glossario, CLI, documenti di rilascio e output generati. I documenti storici CLOSED non sono stati trattati come testo corrente.

Sono stati creati soltanto questo report e il CSV associato. Non sono stati modificati testo applicativo, cataloghi i18n, codice, formule, test, UI o documentazione corrente. A3-FIX e A4 non sono stati iniziati.

## 2. Metodo

L'esame ha combinato:

1. inventario completo delle 2.108 chiavi italiane;
2. classificazione delle unità come label, title, instruction, explanation, tooltip, error, status, glossary, guide, CLI, export o document;
3. lettura continua della Guida renderizzata, non soltanto delle singole chiavi;
4. lettura strutturata di tutti i 63 lemmi del glossario, ciascuno con termine, definizione breve e definizione estesa;
5. ricostruzione di blocchi UI e famiglie di messaggi;
6. esecuzione dell'help CLI e di casi dinamici con 0, 1 e 2 elementi;
7. generazione e ispezione di campioni reali TXT, HTML, LaTeX, SVG, PDF, XLSX, CSV e JSON;
8. lettura di README.md e docs/release/NOTE_VERSIONE_4.0.0.md secondo il loro genere editoriale.

Gli issue ripetuti da uno stesso modello sono consolidati in una sola famiglia. Ogni finding include testo corrente, problema e direzione di correzione; la direzione non è una patch.

## 3. Vincoli A1/A2

Sono stati assunti come vincolanti A1, A1-FIX, A2 e A2-FIX. Non sono state reinterpretate:

- la direzione della matrice inversa;
- l'ordine dei fattori P₂ ⊗ P₁ ⊗ P₀;
- la formula di rotazione di T⁻¹;
- la posizione di J_i prima della distribuzione nello stesso stadio;
- la separabilità della trasformazione relativa per mazzi gemelli in H;
- le distinzioni fra disposizione, trasformazione, permutazione, Procedura, stadio, fase, passo, checkpoint, carta, posizione, inversa e rovesciamento.

Quando una migliore prosa potrebbe spostare uno di questi confini, il rilievo è marcato SEMANTICALLY-CONSTRAINED.

## 4. Copertura

Sono state lette **2.276 unità testuali sorgente univoche**. I campioni renderizzati e gli output eseguiti sono strati di verifica e non sono ricontati.

| classe | unità |
|---|---:|
| label | 185 |
| title | 64 |
| instruction | 64 |
| explanation | 711 |
| tooltip | 67 |
| error | 72 |
| status | 69 |
| glossary | 189 |
| guide | 458 |
| CLI | 22 |
| export | 207 |
| document | 168 |
| **totale** | **2.276** |

Le superfici A–N sono coperte dalle 1.232 unità UI; O dalla Guida; P dal glossario; Q–Y dai prefissi Presentazione, Simulatore, Pratica, Spettatore, Tavola, Explorer, Riconoscimento, Laboratorio e Sessione/L90; Z–AA dalla CLI; AB–AC dai due documenti correnti; AD–AK dai campioni di export e dalle intestazioni generate. Tutte le classi A–AK risultano quindi coperte.

## 5. Grammatica e sintassi

La base linguistica è solida: la maggior parte delle spiegazioni è grammaticalmente completa e conserva bene i rapporti logici. Gli errori certi sono circoscritti.

I casi principali sono due concordanze evidenti — «La terna (...) sono» e «Questo è la diretta conseguenza» — e l'ellissi «verifica se ∈ GEN3», che lascia implicito l'operando sinistro. Quest'ultimo non è un semplice refuso: è sintatticamente ambiguo e la riparazione deve mantenere l'oggetto matematico fissato da A1.

## 6. Naturalezza

Il testo appare in larga parte scritto o rielaborato in italiano competente, ma non in modo uniforme. Le superfici didattiche migliori hanno periodi lineari, verbi concreti e transizioni esplicite. Le zone meno naturali accumulano:

- nomi inglesi dentro sintassi italiana;
- sequenze nominali senza preposizione, come «Analisi Molteplicità»;
- collocazioni rigide, come «turni identici nella forma»;
- formule procedurali eterogenee, da «Clic su» a «Si preme».

Il giudizio complessivo non è quello di una traduzione meccanica integrale, ma di un prodotto cresciuto per strati redazionali non ancora armonizzati.

## 7. Calchi

La ricerca mirata ha individuato 44 chiavi rappresentative con prestiti o calchi quali How-To, workflow, Target, Step, Play, Replay, dropdown, checkbox, slider, default, live, fallback e len. Non ogni prestito è scorretto: alcuni appartengono all'uso informatico e altri sono termini controllati. Il problema è la loro concentrazione nelle stesse superfici rivolte a lettori non specialisti.

L'issue A3-LANG-MEDIUM-02 propone di italianizzare la microcopy generale e di definire una lista esplicita di prestiti ammessi. Stage e checkpoint sono esclusi dalla sostituzione automatica e confluiscono in A3-SEM-01.

## 8. Ambiguità

Sono stati cercati soggetti impliciti, antecedenti incerti, incisi mal collegati e formule senza referente. I due casi più rilevanti sono:

- «verifica se ∈ GEN3», in cui manca l'oggetto della verifica;
- il titolo PDF «R:» immediatamente seguito da «T = ...», che non permette al lettore di capire se R sia un risultato, un rovesciamento o un'etichetta legacy.

Il primo è classificato AMBIGUOUS; il secondo è SEMANTICALLY-CONSTRAINED perché coinvolge notazione e compatibilità degli export.

## 9. Densità

Sono state applicate tre classi:

- **LONG-BUT-CLEAR:** periodi lunghi ma progressivi, per esempio guide.i1.reversals, guide.i5.directions e glossary.long.inverse;
- **TOO-DENSE:** guide.s29.session.body, filter.intro e parti della sezione sul PDF dettagliato, dove prerequisiti, formule, limiti e conseguenze convivono nello stesso periodo;
- **AMBIGUOUS:** guide.s16.decompositions.body, per l'operando implicito.

La lunghezza non è stata penalizzata quando necessaria alla spiegazione matematica. A3-LANG-MEDIUM-03 riguarda cinque blocchi in cui la segmentazione migliorerebbe la comprensione senza ridurre il contenuto.

## 10. Tono didattico

Il tono è generalmente adulto, preciso e rispettoso. Non emerge un uso sistematico di «ovviamente» o «banalmente». Due occorrenze di «basta» anticipano però come semplice un passaggio non immediato: la scelta nel Simulatore e una condizione di mescolamento nella Guida.

Non tutte le occorrenze vanno eliminate: «basta raccogliere» nella descrizione di una singola fase fisica è adeguato. L'issue A3-LANG-LOW-02 è quindi selettivo.

## 11. Istruzioni e persona

La persona prevalente è il tu con imperativo diretto: scegli, seleziona, inserisci, osserva. Nelle stesse procedure compaiono tuttavia «Clic su», «Clicca», «Si preme», «doppio-click» e «doppio clic».

La convenzione proposta è:

- imperativo diretto per le azioni dell'utente;
- forma impersonale per spiegazioni generali, non per passi consecutivi;
- «fai clic» e «doppio clic» come grafie editoriali;
- «giocatore» e «spettatore» soltanto quando indicano ruoli del gioco, non come sostituti generici di tu.

## 12. Articoli/preposizioni/concordanze

L'errore più visibile è «Apri nel Explorer», presente in tre contesti. La reggenza va resa naturale mantenendo Explorer come nome ufficiale della vista.

Le concordanze errate sono due e sono registrate in A3-TYPO-02. Le costruzioni matematiche «appartiene a H», «inversa di T», «comporre con» e «immagine di x» risultano invece coerenti e non richiedono rilievi.

## 13. Pluralizzazione

La prova dinamica della CLI ha verificato 0, 1 e 2 Procedure. L'output corrente produce «0 procedure», «1 procedure», «2 procedure»: il valore 1 è errato. La stessa struttura compare in status, Explorer, export e Pratica, per esempio «1 combinazioni», «1 pagine», «Trovate 1 decomposizioni» ed «Esportati 1 file».

A3-TYPO-03 consolida otto chiavi o famiglie. La direzione richiesta è una pluralizzazione esplicita con test 0/1/2, senza intervenire in A3 sul codice.

## 14. Punteggiatura

Virgole, due punti, punti e virgola ed elenchi sono nel complesso ben gestiti. Nei testi matematici lunghi la difficoltà deriva più dalla densità sintattica che da errori puntuali di punteggiatura.

Le oscillazioni editoriali riguardano soprattutto apostrofi ASCII, tre punti rispetto al carattere ellissi, frecce ASCII rispetto a frecce Unicode e trattino rispetto a lineetta. Sono assorbite negli issue TYPO e STYLE pertinenti. Non è emersa una famiglia autonoma di punteggiatura tale da giustificare un issue duplicato.

## 15. Maiuscole

**Chiusura di audit A2-STYLE-02.** La convenzione proposta è:

- maiuscola per il nome ufficiale di viste e moduli: Tavola, Laboratorio, Riconoscimento, Explorer, Simulatore, Pratica, Sessione e Gioco Reale;
- minuscola quando la parola è nome comune o processo: tavola numerica, laboratorio generico, riconoscimento di una permutazione, simulatore come categoria;
- sentence case italiano per titoli e intestazioni;
- maiuscole per sigle e simboli secondo la notazione matematica, non per enfasi.

L'oscillazione «Gioco delle 27 carte» / «Gioco delle 27 Carte» e titoli come «Simulatore del Trucco delle 27 Carte» costituiscono A3-STYLE-01.

## 16. Composti/trattini

**Chiusura di audit A2-STYLE-01.** La forma preferita è aperta per i composti italiani del prodotto:

- base 3;
- caso base 3;
- carta bersaglio;
- posizione bersaglio;
- punto fisso;
- gioco delle 27 carte;
- doppio clic.

Il trattino va riservato a intervalli o locuzioni davvero cristallizzate, non importato automaticamente dall'inglese. Gli ibridi How-To e doppio-click, insieme alle oscillazioni carta-per-carta/passo-passo, formano A3-STYLE-02.

## 17. Tipografia matematica

**Chiusura di audit A2-STYLE-03.** La convenzione è per canale:

| canale | forme proposte |
|---|---|
| UI, Guida, HTML, SVG, PDF | S₂₇, S₃, Γ, T⁻¹, MSC², ×, ⊗, → |
| CLI/TXT human-readable | Unicode quando affidabile; altrimenti S27, S3, Gamma, T^-1, MSC^2 in modo coerente |
| CSV/JSON e schemi | ASCII stabile quando richiesto dalla compatibilità |
| LaTeX | S_{27}, S_3, \Gamma, T^{-1}, \mathrm{MSC}^2 |

Non si richiede la stessa codifica in tutti i formati. Si richiede coerenza interna: nella Guida e nella UI ricorrono invece S27/S₂₇, S3/S₃ e potenze Unicode/ASCII miste. A3-STYLE-03 registra la famiglia senza cambiare formule.

## 18. Numeri

La convenzione proposta per la prosa italiana è:

- spaziatura delle migliaia: 1 728, 46 656, 5 159 780 352;
- virgola decimale: 0,2 s;
- lineetta negli intervalli: 0–26;
- nessuna spaziatura interna nei numeri macchina o identificatori;
- 1728, 0..26 e punto decimale ammessi quando imposti da sintassi, CLI o schema.

README, Guida e note di rilascio alternano spazi e punti per le migliaia; Guida e output alternano punto e virgola decimale; prosa ed export alternano 0..26 e 0–26. A3-STYLE-04 riguarda la convenzione, non i valori.

## 19. Microcopy

Le etichette operative principali — Annulla, Chiudi, Applica, Ripristina, Carica, Salva, Esporta, Copia, Verifica, Riconosci e Calcola — descrivono correttamente l'azione attesa. Non emerge una famiglia diffusa di pulsanti vaghi come «Vai» o «Procedi».

Le debolezze sono localizzate in «Apri nel Explorer», nei comandi inglesi Step/Play/Replay e nelle istruzioni sul clic. Sono già registrate senza duplicazione in A3-LANG-MEDIUM-01, A3-LANG-MEDIUM-02 e A3-LANG-LOW-01.

## 20. Errori/messaggi

La maggior parte dei messaggi indica l'oggetto non valido e, quando disponibile, il limite atteso. Sei famiglie restano troppo ellittiche o tecniche: «risultato è di tipo 3», errori di token/parsing e proprietà sconosciute non sempre esplicitano il campo o l'azione correttiva.

A3-LANG-LOW-04 propone di aggiungere referente, posizione e recupero quando già disponibili nei dati dell'errore. La concisione propria della CLI non è considerata un difetto.

## 21. Glossario

Il glossario è stato letto **63/63**: 63 termini, 63 definizioni brevi e 63 definizioni estese, per 189 unità. Le definizioni sono semanticamente allineate con A2 e, nel complesso, naturali.

Le criticità linguistiche sono limitate a prestiti come workflow e layout, alla definizione «Una tappa è un checkpoint» e ad alcuni avvii da dizionario («Nel programma: ...»). I termini controllati non sono stati sostituiti: i casi Stage/checkpoint sono confluiti in A3-SEM-01.

## 22. Guida

La Guida è stata letta come testo continuo: titolo, indice, 41 sezioni e footer. Le 458 chiavi sorgente producono 751 segmenti renderizzati, circa 85.600 caratteri e oltre 1.000 interruzioni di riga.

I punti di forza sono la progressione concettuale, gli esempi concreti e l'uso generalmente accurato dei riferimenti interni. Le aree deboli sono:

- titolo ibrido «Guida completa & How-To»;
- due concordanze errate;
- «Apri nel Explorer»;
- istruzioni eterogenee;
- 52 accenti/apostrofi ASCII distribuiti soprattutto nelle sezioni tecniche aggiunte più tardi;
- cinque blocchi TOO-DENSE;
- una frase AMBIGUOUS in guide.s16.decompositions.body.

La varietà conferma una stratificazione redazionale, non un problema uniforme dell'intera Guida.

## 23. CLI

Sono stati controllati l'help principale e gli help di validate, sequence, export, recognize, property, compare, replay e selftest: nove schermate complessive. Le descrizioni applicative sono italiane, ma l'involucro argparse mantiene usage, positional arguments, options e i messaggi standard inglesi.

Questo residuo è incluso nella famiglia dei calchi/localizzazione parziale, non nell'audit inglese. Sono stati inoltre verificati gli output human-readable e i casi 0/1/2 della pluralizzazione. La prima esecuzione in una console con codifica non UTF-8 ha mostrato caratteri sostitutivi; l'esecuzione UTF-8 era corretta, quindi il fenomeno è registrato come limite ambientale e non come issue del prodotto.

## 24. Export

Sono stati generati e letti campioni reali di tutte le famiglie richieste:

| formato | verifica |
|---|---|
| TXT | testo, formule plain, «len 3» |
| HTML | protocollo completo e frase «turni identici nella forma» |
| LaTeX | testo e notazione specifica di formato |
| SVG | titolo e assi italiani |
| PDF | standard, esteso e dettagliato; estrazione testuale e controllo visivo |
| XLSX | nomi foglio e intestazioni |
| CSV | intestazioni Stage0/Stage1/Stage2 e campi di schema |
| JSON | documento scientifico reale, convenzioni descrittive e identificatori |

PDF standard ed esteso mostrano Stage_i, «Stadio 0: Stage0» e «R:» davanti a «T = ...». Il PDF dettagliato mostra intestazioni legacy quali DISP_INIZIO e valori TRUE/FALSE. CSV, XLSX e JSON mescolano descrizioni umane e identificatori di schema. A3-SEM-02 richiede di separarli prima di localizzare, perché una sostituzione indiscriminata potrebbe rompere compatibilità o distinzioni A1/A2.

## 25. README/release notes

Sono stati letti 73 blocchi testuali di README.md e 95 blocchi delle note di rilascio, per 168 unità. Il README alterna spiegazione didattica e istruzioni tecniche; le note di rilascio adottano legittimamente uno stile più telegrafico.

Non è stato trasformato in issue il registro nominale del changelog. Le oscillazioni rilevanti sono editoriali: numeri con punti o spazi, S27 rispetto a S₂₇ e alcuni titoli in maiuscolo inglese. Sono già consolidate negli issue STYLE-01, STYLE-03 e STYLE-04.

## 26. Issue

Sono aperti **19 issue**: 0 LANG-HIGH, 5 LANG-MEDIUM, 4 LANG-LOW, 5 STYLE, 3 TYPO, 2 SEMANTICALLY-CONSTRAINED e 0 A4-CANDIDATE.

| id | classe | evidenza corrente | problema | direzione |
|---|---|---|---|---|
| A3-LANG-MEDIUM-01 | LANG-MEDIUM | «Apri nel Explorer» | articolo/preposizione innaturali | rendere naturale la reggenza mantenendo il nome UI |
| A3-LANG-MEDIUM-02 | LANG-MEDIUM | «How-To», workflow, Target, Step, Replay, «len 3» | registro ibrido e calchi | italianizzare la microcopy generale; lista di prestiti ammessi |
| A3-LANG-MEDIUM-03 | LANG-MEDIUM | periodi fino a 1.197 caratteri | gerarchia logica nascosta | separare prerequisiti, azione ed esito |
| A3-LANG-MEDIUM-04 | LANG-MEDIUM | «verifica se ∈ GEN3» | manca l'operando sinistro | esplicitare il soggetto già definito |
| A3-LANG-MEDIUM-05 | LANG-MEDIUM | «turni identici nella forma» | collocazione rigida | descrivere la struttura operativa ripetuta |
| A3-LANG-LOW-01 | LANG-LOW | «Clicca», «Clic su», «Si preme», «doppio-click» | istruzioni e grafie incoerenti | imperativo diretto e «fai clic/doppio clic» |
| A3-LANG-LOW-02 | LANG-LOW | «basta scegliere» | minimizza un passaggio non banale | formulazione neutra della condizione |
| A3-LANG-LOW-03 | LANG-LOW | «Analisi Molteplicità» | sequenza nominale innaturale | introdurre la preposizione e sentence case |
| A3-LANG-LOW-04 | LANG-LOW | «risultato è di tipo 3» | referente e recupero insufficienti | aggiungere oggetto, posizione e rimedio |
| A3-TYPO-01 | TYPO | e', piu', perche', fa' | accenti/apostrofi ASCII | grafie italiane corrette nelle superfici umane |
| A3-TYPO-02 | TYPO | «La terna sono»; «Questo è la...» | concordanze errate | concordare soggetto/verbo e dimostrativo/nome |
| A3-TYPO-03 | TYPO | «1 procedure», «1 combinazioni» | plurale dinamico errato | selezione singolare/plurale con test 0/1/2 |
| A3-STYLE-01 | STYLE | «27 carte» / «27 Carte» | maiuscole instabili | nomi UI propri + sentence case |
| A3-STYLE-02 | STYLE | base 3 / doppio-click / carta-per-carta | composti e trattini incoerenti | composti italiani aperti salvo casi motivati |
| A3-STYLE-03 | STYLE | S27/S₂₇, T^-1/T⁻¹ | tipografia mista | convenzione specifica per formato |
| A3-STYLE-04 | STYLE | 1.728/1 728, 0.2/0,2, 0..26/0–26 | numeri non uniformi | convenzione italiana in prosa; ASCII negli schemi |
| A3-STYLE-05 | STYLE | «…», '…', ""…"", codice | virgolette senza ruoli stabili | caporali, apostrofo tipografico e codice per funzione |
| A3-SEM-01 | SEMANTICALLY-CONSTRAINED | Stage, checkpoint, workflow | italianizzazione rischiosa | migliorare il contesto senza fondere concetti A2 |
| A3-SEM-02 | SEMANTICALLY-CONSTRAINED | Stage_i, R:, TRUE/FALSE | etichette umane e schema mescolati | separarli e verificare A1/A2 prima del fix |

Il CSV allegato contiene per ogni riga chiavi o file, occorrenze e note di vincolo.

## 27. STYLE

I cinque issue STYLE non sono correzioni cosmetiche isolate: definiscono un sistema editoriale comune.

1. **Maiuscole:** nomi ufficiali di viste in maiuscolo; usi comuni in minuscolo; sentence case nei titoli.
2. **Composti/trattini:** composti italiani aperti; trattino solo se motivato; «doppio clic».
3. **Notazione:** Unicode nelle superfici ricche, LaTeX nel relativo formato, ASCII stabile negli schemi.
4. **Numeri:** spazi per migliaia, virgola decimale, lineetta per intervalli nella prosa.
5. **Virgolette:** caporali per etichette/citazioni, apostrofo tipografico per l'italiano, codice per identificatori.

Con questa sezione risultano auditati e chiusi A2-STYLE-01, A2-STYLE-02 e A2-STYLE-03. Restano da implementare soltanto in un eventuale A3-FIX separato.

## 28. A4-CANDIDATE

**Nessun A4-CANDIDATE.** L'inglese è stato consultato solo come indizio di calco. Non è stato iniziato un audit autonomo dell'inglese e nessun problema indipendente EN è stato analizzato.

## 29. Copertura e limiti

La copertura è completa rispetto alle classi richieste. I limiti sono:

- il comportamento linguistico è stato verificato su campioni rappresentativi, non su ogni combinazione possibile di dati dinamici;
- la resa visuale dei PDF è stata controllata con rasterizzazione; sostituzioni di font segnalate dal renderer esterno impediscono di attribuire al prodotto differenze minime di metrica;
- la codifica della console dipende dall'ambiente: il controllo linguistico CLI è stato ripetuto in UTF-8;
- CSV e JSON contengono insieme identificatori stabili e alcune descrizioni italiane; non è lecito proporre sostituzioni di schema senza un controllo di compatibilità.

Questi limiti non impediscono il passaggio dei gate A3.

## 30. Git/filesystem

HEAD iniziale: commit A2-FIX corrente sul ramo main.

HEAD finale: un solo commit documentale A3 successivo.

Il ramo resta locale e avanti rispetto a origin/main. Nessun push è stato eseguito.

Il commit contiene esclusivamente:

- docs/audits/A3_FINAL_ITALIAN_LANGUAGE_AUDIT.md
- docs/audits/A3_FINAL_ITALIAN_LANGUAGE_AUDIT.csv

PDF invariati e non tracciati.

## 31. Gate

| gate | esito | evidenza |
|---|---|---|
| A3-G1 | PASS | tutte le classi A–AK coperte |
| A3-G2 | PASS | Guida letta in continuità, 41 sezioni |
| A3-G3 | PASS | glossario 63/63 |
| A3-G4 | PASS | 1.232 unità UI |
| A3-G5 | PASS | 67 tooltip più help e banner |
| A3-G6 | PASS | 72 errori e 69 status |
| A3-G7 | PASS | 9 schermate CLI più output dinamici |
| A3-G8 | PASS | campioni reali TXT, HTML, LaTeX, SVG, PDF, XLSX, CSV, JSON |
| A3-G9 | PASS | 168 blocchi README/release notes |
| A3-G10 | PASS | grammatica e sintassi coperte |
| A3-G11 | PASS | calchi cercati e consolidati |
| A3-G12 | PASS | ambiguità cercate e classificate |
| A3-G13 | PASS | tono didattico controllato |
| A3-G14 | PASS | pluralizzazione 0/1/2 verificata |
| A3-G15 | PASS | punteggiatura controllata |
| A3-G16 | PASS | A2-STYLE-01 auditato |
| A3-G17 | PASS | A2-STYLE-02 auditato |
| A3-G18 | PASS | A2-STYLE-03 auditato |
| A3-G19 | PASS | ogni issue ha evidenza, problema e direzione |
| A3-G20 | PASS | matematica A1 non reinterpretata |
| A3-G21 | PASS | terminologia A2 non reinterpretata |
| A3-G22 | PASS | nessuna correzione implementata |
| A3-G23 | PASS | A4 non iniziato |
| A3-G24 | PASS | nessun push |
| A3-G25 | PASS | soli deliverable A3 aggiunti |
| A3-G26 | PASS | PDF invariati e non tracciati |
| A3-G27 | PASS | report Markdown presente |
| A3-G28 | PASS | CSV presente |

**Conclusione:** tutti i 28 gate passano. A3 è concluso come audit diagnostico, con 19 issue aperti e nessuna correzione applicata.
