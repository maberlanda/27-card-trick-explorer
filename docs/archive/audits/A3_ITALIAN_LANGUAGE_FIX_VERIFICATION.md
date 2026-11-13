# A3-FIX — Verifica della revisione linguistica italiana

Data di verifica: 27 settembre 2026. Ambito: release candidate 4.0.0.

## Esito

Le 19 segnalazioni dell'audit A3 sono state corrette e protette da regressioni.
La revisione non modifica risultati matematici, convenzioni di composizione,
ordine dei fattori, significato di inversa e rovesciamento, oppure schemi CSV e
JSON. Le etichette rivolte alla persona sono ora distinte dagli identificatori
di macchina.

| Issue | Correzione verificata | Evidenza principale | Esito |
|---|---|---|---|
| A3-LANG-MEDIUM-01 | «Apri in Explorer» | `analysis.open_explorer`, riepilogo Analisi, Guida | VERIFIED FIXED |
| A3-LANG-MEDIUM-02 | microcopy generale italianizzata; prestiti ammessi circoscritti | comandi Mescolamento, impostazioni, export TXT/HTML | VERIFIED FIXED |
| A3-LANG-MEDIUM-03 | periodi densi divisi per prerequisito, azione ed esito | filtri; decomposizioni; PDF dettagliato; Sessione | VERIFIED FIXED |
| A3-LANG-MEDIUM-04 | operando sinistro esplicito: `A₂ appartiene a GEN3⊗GEN3⊗GEN3` | `guide.s16.decompositions.body` | VERIFIED FIXED |
| A3-LANG-MEDIUM-05 | i tre turni «hanno la stessa struttura» | HTML Protocollo generato | VERIFIED FIXED |
| A3-LANG-LOW-01 | imperativo diretto e grafia «fai clic/doppio clic» | Analisi, Distribuzione, Coniugio, Guida | VERIFIED FIXED |
| A3-LANG-LOW-02 | rimosso «basta» dai passaggi didattici non banali | Simulatore e Guida | VERIFIED FIXED |
| A3-LANG-LOW-03 | «Analisi della molteplicità delle permutazioni» | UI, Guida, foglio XLSX di riepilogo | VERIFIED FIXED |
| A3-LANG-LOW-04 | errore di tipo 3 con oggetto, dimensione e rimedio | `explorer.error.type3_result` | VERIFIED FIXED |
| A3-TYPO-01 | accenti e apostrofi italiani nelle superfici umane | Guida, export, footer, conferme | VERIFIED FIXED |
| A3-TYPO-02 | concordanze «La terna … rappresenta» e «Questa è …» | sezioni 2 e 7 della Guida | VERIFIED FIXED |
| A3-TYPO-03 | messaggi validi con conteggi 0, 1 e 2 | status, Explorer, export, Pratica, CLI | VERIFIED FIXED |
| A3-STYLE-01 | sentence case per prodotto, viste e titoli | Simulatore, Protocollo, export | VERIFIED FIXED |
| A3-STYLE-02 | «doppio clic», «carta per carta», «passo per passo» | UI e Guida | VERIFIED FIXED |
| A3-STYLE-03 | Unicode nelle superfici ricche; sintassi propria in LaTeX e formati macchina | S₂₇/S₃, T⁻¹, MSCᵏ, 3²⁺ⁱ | VERIFIED FIXED |
| A3-STYLE-04 | spazi per migliaia, virgola decimale e lineetta negli intervalli di prosa | UI, Guida, README, note 4.0.0 | VERIFIED FIXED |
| A3-STYLE-05 | caporali per etichette/citazioni; delimitatori tecnici conservati negli schemi | Guida, messaggi, documenti | VERIFIED FIXED |
| A3-SEM-01 | `stadio`, `fase`, `passo` e `tappa` restano distinti secondo A2 | glossario, successione, Guida | VERIFIED FIXED |
| A3-SEM-02 | etichette PDF localizzate; identificatori CSV/JSON invariati | PDF standard/esteso/dettagliato; CSV; JSON | VERIFIED FIXED |

## Correzione aggiuntiva

| ID | Calco trovato oltre l'inventario A3 | Correzione | Esito |
|---|---|---|---|
| A3F-EXTRA-01 | «ordine pubblico» usato per l'ordine matematico dei fattori o di enumerazione | «ordine dei fattori» / «ordine di enumerazione» in audit A1, audit A3 e test I1 | VERIFIED FIXED |

Numero di famiglie aggiuntive registrate: **1**. Le altre riscritture di
naturalness (per esempio «calcolata più di recente») appartengono alle famiglie
già censite da A3-LANG-MEDIUM-02 e non sono state ricontate.

## Prestiti e registro

Sono stati sostituiti nella microcopy italiana: `How-To`, `Target`, `Step`,
`Play`, `Replay`, `len`, `workflow`, `worker`, `dropdown`, `checkbox` e
`fallback`, quando erano parole rivolte alla persona.

Restano ammessi perché nomi propri, sigle, formati o termini tecnici consolidati:
Explorer, NumPy, PDF, CSV, JSON, HTML, LaTeX, SVG, CPU, cache, thread e preset.
I nomi dei comandi CLI (`replay`, `sequence`, `export`) e gli identificatori di
schema non vengono tradotti.

## Contratti preservati

| Area | Contratto dopo A3-FIX |
|---|---|
| Matematica A1 | composizione da destra a sinistra, `P₂⊗P₁⊗P₀`, formula dell'inversa, `Jᵢ` prima della distribuzione e risultati enumerativi invariati |
| Terminologia A2 | carta/posizione/indice; disposizione/trasformazione/permutazione/Procedura; distribuzione/raccolta; stadio/fase/passo/tappa; inversa/rovesciamento restano distinti |
| CSV | colonne `Stage0`, `Stage1`, `Stage2`, `A0`, `A1`, `A2`, `T_simbolica`, `T_permutazione` invariate |
| JSON | `schema = gioco27.esperimento`, `schema_version = 1` e chiavi principali invariati |
| XLSX | colonne tecniche e fogli `Perm -> Simboliche` / `Simbolica -> Perm` invariati; corretta soltanto l'etichetta umana «Analisi della molteplicità» |
| PDF | `Stadio`, `T`, `Disposizione iniziale`, `SÌ/NO`, `Rovesciamento`, `Moltiplicazione`, `Posizione asso` nelle etichette umane |

## Verifica dei formati reali

Sono stati generati e riletti campioni reali in italiano dei formati TXT, HTML,
LaTeX, SVG, PDF standard, PDF esteso, PDF dettagliato, XLSX, CSV e JSON. I tre
PDF sono stati convertiti in immagini e ispezionati visivamente: griglie,
carte, intestazioni e marcatori risultano leggibili e non sovrapposti. I file
temporanei di collaudo sono stati rimossi dopo la verifica.

## Regressioni

La protezione mirata è in `tests/test_a3_italian_language_fixes.py` e copre:

- reggenza di Explorer e istruzioni con «fai clic»;
- assenza del calco «ordine pubblico» nelle superfici correnti;
- conteggi 0/1/2;
- operando esplicito della verifica GEN3;
- titolo «Analisi della molteplicità»;
- distinzione stadio/tappa, inversa/rovesciamento e carta/posizione;
- notazione e numeri italiani nelle superfici ricche;
- schemi CSV/JSON invariati ed etichette PDF localizzate.

## Chiusura

La prima esecuzione completa dopo A3-FIX ha individuato due sole aspettative
testuali ancora legate alla grafia precedente `S27`. I casi riguardavano la
Guida italiana in `test_didattica_i7.py` e `test_laboratorio_i6_gui.py`; sono
stati classificati come riferimenti di test da aggiornare, non come problemi
del prodotto. Le aspettative italiane sono ora `S₂₇`, mentre quella inglese
resta `S27`.

Risultati conclusivi:

- test mirati finali A3: **48 superati, 20 esclusi**;
- suite completa finale: **2 094 superati, 320 esclusi, 0 errori**;
- analisi statica `pyflakes` su package, test e script principali: **0
  segnalazioni**;
- problemi ambientali: `pyflakes` non era presente nell'interprete iniziale;
  è stato eseguito da una dipendenza temporanea senza modificare l'ambiente o
  le dipendenze del progetto;
- elementi rinviati: **nessuno**.

A3-FIX è pertanto **CHIUSO**. Il progetto è pronto per la verifica tecnica
finale in vista di RC2.
