# F_ANALYSIS_CLOSED — chiusura del compartimento F (Analisi, filtri, aggregazione e performance)

Registro verificabile. Il quadro generale resta in `GIT_BASELINE_AND_RECONCILIATION.md`;
le chiusure precedenti in `A_BASELINE_CLOSED.md`, `D_DOMAIN_CLOSED.md`, `B_IO_CLOSED.md`,
`C_STATE_CLOSED.md` ed `E_LANGUAGE_SIMULATION_CLOSED.md`.

## 1. Identità

| Voce | Valore |
|---|---|
| Branch | `main` — nessun push: `origin/main` resta a `54445af` |
| HEAD iniziale | `83f02f0bde8f044654fe414dc6bb7b4a9caf8d87` — «docs(E): record closed language compartment» |
| HEAD finale | l'ultimo commit dell'elenco in § 12 |
| Working tree all'avvio | pulito; i commit di A, D, B, C ed E presenti e non riscritti |
| Baseline di partenza | 1097 raccolti, **1096 passati, 1 saltato, 0 falliti** — coincide con quella attesa dopo E; `pytest tests/test_baseline_matematica.py` → 25 passati |
| Perimetro | soltanto il repository corrente; nessuna directory esterna letta o confrontata |

L'unico skip resta **N03** (`pypdfium2` non installata), debito di K.

## 2. B05 — gli ingressi dell'analisi vengono validati

**Casi precedentemente accettati.** `analizza_righe` leggeva `T_permutazione` con un `int()`
dentro un `try/except ValueError: continue`; `analizza_csv` cercava le colonne per sottostringa.

```text
[0,0,99]                     accettata come T valida (duplicati + fuori intervallo)
26 elementi / 28 elementi    accettate
[-1, ...] / [99, ...]        accettate
[0,1,2]                      accettata
[] , "" , [a,b,c] , [0.0,…]  riga scartata in silenzio, nessuna diagnostica
intestazione «foo;bar»       → []  (analisi valida con zero risultati)
file vuoto                   → StopIteration non gestita
formula «MSC» con T identità → nessuna incoerenza segnalata
```

**Schema riconosciuto.** Gli schemi non sono stati inventati: sono quelli che il programma
produce.

| Schema | Origine | Campi obbligatori | Importabile |
|---|---|---|---|
| `combinazioni` | `core.permutations.CSV_HEADER` (`write_csv`) | `T_permutazione` | **sì** |
| `analisi` | `core.algebra.scrivi_output` | `T_permutazione`, `T_simboliche_distinte` | **no**, e lo dice |

Campi opzionali dello schema `combinazioni`: `#`, `Stage0..2`, `A0..A2`, `T_simbolica`. Il
riconoscimento guarda il **primo token** dell'intestazione, perché le celle reali portano una
descrizione (`T_permutazione  [lista 0..26]`), e l'apertura usa `utf-8-sig`, così il BOM di
Excel non finisce nel nome della prima colonna.

**Compatibilità legacy.** Un file con la sola colonna `T_permutazione` — i formati storici
senza colonne Stage — resta leggibile: l'assenza di formula non è un errore. Non è invece
stata conservata l'accettazione *per sottostringa* di qualunque intestazione: era il
meccanismo che rendeva «foo;bar» un'analisi vuota. L'export dell'analisi viene riconosciuto
**per rifiutarlo con il suo nome**: rileggerlo come CSV combinazioni darebbe molteplicità 1
ovunque, un risultato plausibile e falso.

**Contratto di validazione.** Ogni `T` passa dal contratto di dominio introdotto in D —
`valida_permutazione(..., 27)`: 27 valori, interi secondo la politica di D (niente `bool`,
niente `float`, niente stringhe numeriche), tutti in 0..26, tutti distinti. Nessuna terza
validazione di permutazione è stata scritta.

**Formula ↔ T.** Quando la riga porta anche una formula — la Stage-level
`T = [Stage2] o [Stage1] o [Stage0]` o la `T_simbolica` — la coerenza viene verificata con il
**parser unico di E**: `permutazione_di(formula)` deve dare esattamente la `T` della riga.
Alias storici (`R_U`, `I_3`) e prefisso `T =` restano validi perché il linguaggio di E li
conosce. Nessuna grammatica è stata duplicata dentro l'import (misurato: ~51 µs a formula,
mezzo secondo su diecimila righe).

**Diagnostica.** Le righe rifiutate non spariscono:

```text
RigaScartata(numero=3, campo="T_permutazione",
             motivo="T_permutazione: valore 99 fuori dall'intervallo 0..26 (posizione 0)")
```

`RisultatiImport` è una `list` — ogni chiamante la usa come tale — con in più `schema`,
`lette`, `scartate`, `parziale` e `diagnostica()`. La scheda Analisi la mostra accanto al
riepilogo, così un import parziale si vede invece di doverlo dedurre. Il contratto distingue:

| Situazione | Esito |
|---|---|
| Schema non riconosciuto / file vuoto | `SchemaNonRiconosciuto` — l'import **fallisce** |
| Riga semanticamente invalida | scartata, elencata con numero, campo e motivo |
| Schema valido, zero righe | risultati vuoti **e** schema riconosciuto |

## 3. B06 — un solo contratto per i filtri

**Causa della divergenza.** Tre descrizioni dello stesso filtro:

```text
valida_filtri            non guardava né il numero di stadi né i valori
count_combinations_ex    percorreva TUTTI gli stadi ricevuti
iter_combinations_ex     leggeva solo i PRIMI TRE
```

Da cui il caso di regressione (quattro stadi, il quarto con `p0` libero): **count = 6,
iter = 1**. Con due stadi o nessuno il conteggio rispondeva e l'iteratore sollevava
`IndexError`. Un nome di permutazione inesistente, un intero al posto di un nome, una chiave
sconosciuta o un elenco con duplicati passavano senza un fiato.

**Modello unico.** `normalizza_filtri` è l'unica porta d'ingresso e restituisce una tupla di
`FiltroStadio` congelati, con le scelte già espanse (`ANY` → elenco completo, un nome → tupla
di uno). `cardinalita()` e `combinazioni()` leggono lo **stesso** oggetto: non possono più
descrivere domini diversi. Conteggio, enumerazione, export e analisi passano tutti da lì — un
test lo verifica sull'AST delle quattro funzioni pubbliche.

**Numero di stadi.** `N_STADI = 3`, esplicito e imposto. Non è un parametro: la matematica del
mazzo è definita su tre stadi (`T = S2 o S1 o S0`), gli export hanno tre colonne Stage e la
baseline conta 1.728 configurazioni **per stadio**. Zero, uno, due, quattro o più stadi
vengono rifiutati prima di qualunque calcolo. Il gioco non è stato generalizzato a N stadi.

**Domini.** `p0, p1, p2` ∈ `P_OPTS` (sei nomi), `j0, j1, j2` ∈ `J_OPTS` (due nomi); ogni
chiave accetta `ANY`, un nome o un elenco non vuoto di nomi distinti; `j_uniform` è un
booleano. Rifiutati esplicitamente: chiavi sconosciute, chiavi legacy a base 1 (`p3`/`j3` —
erano già rifiutate e restano tali, perché la vecchia `p2` è la nuova `p1`), chiavi mancanti,
nomi inesistenti, tipi non testuali, elenchi vuoti, duplicati e `j_uniform` non booleano. Ogni
messaggio nomina stadio, chiave e motivo. Le due coppie di funzioni — i nomi storici e le
varianti `_ex` — avevano due semantiche per lo stesso filtro (la prima ignorava elenchi e
`j_uniform`); ora sono la stessa cosa, conservate con entrambi i nomi.

**Prova `count == iter`.** Su una famiglia deterministica di quattordici filtri piccoli —
tutto fissato, un parametro libero (tutte e sei le chiavi), più parametri liberi, sottoinsiemi
espliciti, J uniforme in tutte le sue forme — con, per ciascuno, l'assenza di combinazioni
ripetute e l'appartenenza di ogni nome al proprio dominio. Il conteggio resta matematico: un
test sostituisce l'enumeratore con una sentinella che esplode se viene avviata, e verifica che
`count_combinations_ex` risponda comunque, anche su 5.159.780.352. L'ordine di emissione è
verificato contro un oracolo costruito con `itertools`, perché la numerazione
«Combinazione #N» di CSV e PDF ci si appoggia.

## 4. R01 — preflight, budget, aggregazione

**Vecchio comportamento.** L'analisi contava, chiedeva «sei sicuro?» sopra 50.000 e poi
accumulava ogni riga in una lista prima di aggregare. Con i filtri liberi sono 5.159.780.352
combinazioni.

**Preflight.** Prima di toccare l'enumeratore:

```text
valida filtri → conta il dominio → costruisci il piano → applica il budget → solo allora enumera
```

`pianifica_analisi` non enumera nulla — la cardinalità è un prodotto di lunghezze — e un test
lo prova con una sentinella che esplode se l'enumeratore parte.

**Budget.** Le soglie sono misurate, non scelte a occhio. Campione di 15.552 combinazioni
nell'ambiente di riferimento:

| Voce | Misura |
|---|---:|
| Riga grezza trattenuta | ~796 B |
| Aggregati (formule distinte) | ~220 B per riga |
| Generazione + aggregazione | ~59 µs per riga |

da cui:

| Dominio | Memoria | Tempo | Modalità |
|---:|---:|---:|---|
| 100.000 | ~105 MB | ~6 s | **completa** — aggregati + grezzi |
| 1.000.000 | ~220 MB | ~59 s | **aggregata** — solo aggregati |
| 5.159.780.352 | ~5,4 TB | ~85 ore | **rifiutata** |

`LIMITE_GREZZI = 100_000`, `LIMITE_ANALISI = 1_000_000`. Il limite di export resta un'altra
cosa e resta dov'era: `MAX_EXPORT_ITEMS` vale 20 milioni perché un export scrive su disco
senza trattenere nulla, mentre l'analisi tiene in memoria gruppi e formule. La differenza è
scritta accanto alle costanti.

**Aggregazione.** Le righe entrano nei contatori una per volta. L'implementazione
dell'aggregazione resta **una sola** — la classe `Aggregatore`, che `analizza_righe` usa già:
cambia solo il momento. In modalità completa le righe ci sono comunque tutte e i gruppi li
costruisce `analizza_righe` alla fine; in modalità aggregata l'aggregatore conta al volo e non
trattiene nulla.

**Gestione dei grezzi.** Quando non vengono conservati, il risultato lo dichiara: la
diagnostica lo scrive accanto al riepilogo e il contratto di C fa il resto da solo — con
`grezzi=()` le due voci di export dei dati grezzi si disabilitano. Nessuna analisi parziale
viene presentata come completa.

**Integrazione con le revisioni di C.** Le primitive di C non sono state sostituite:
l'aggregazione interroga `_analisi_e_corrente(revisione)` a ogni riga e prima di pubblicare,
quindi un reset o una nuova richiesta invalidano il lavoro anche a metà aggregazione. Nessun
Job Manager è stato introdotto.

## 5. Kronecker — il ramo morto

**Verificato prima di togliere.** In `find_all_kron_decompositions_parallel` il `return`
verso la versione sequenziale è incondizionato: le ~40 righe successive — pool,
serializzazione dei buffer, `as_completed`, deduplicazione — erano irraggiungibili, e con esse
il worker `_worker_chunk`, usato solo lì. Nessun test, monkeypatch o chiamante tocca quei
simboli: `_worker_chunk` non compare altrove nel repository, e l'unico test della funzione
(`test_documentazione_d4d5`) verifica proprio che deleghi alla sequenziale.

**Rimozione.** 432 → 357 righe; spariti anche i due import che solo il ramo morto usava. La
firma resta invariata (`n_workers` accettato e ignorato) perché la scheda Decomposizioni e i
test lo passano. Nessuna nuova implementazione parallela è stata scritta.

**Prova di non-regressione.** Comportamento pubblico confrontato prima/dopo su identità, MSC e
una permutazione fuori da G, con `n_workers` None/1/2/8: stesse decomposizioni, stessi
conteggi — **46.656** per un bersaglio in G, **0** fuori. `validate_complete_decompositions`,
`appartiene_a_G`, `appartiene_a_H` e il contratto della cache di B sono rimasti identici. Un
test verifica che nel modulo non resti codice dopo un `return` incondizionato, in nessuna
funzione.

## 6. Performance

**Misurato**: costo per riga dell'analisi (generazione, aggregazione), memoria delle righe
grezze e degli aggregati, costo del parsing di una formula, cardinalità dei domini. Sono i
numeri su cui poggiano le soglie del § 4 e la decisione di verificare la formula solo
sull'import.

**Deliberatamente non ottimizzato**: la ricerca Kronecker (già a ~0,025 s), il disegno dei
PDF, `compute_T_full`, la cache delle decomposizioni. Nessuna micro-ottimizzazione
speculativa. I test di F sono strutturali — enumeratore non avviato, righe non materializzate,
conteggio senza enumerazione, aggregazione incrementale — e non contengono soglie temporali:
non possono fallire perché una macchina è più lenta.

## 7. Compatibilità

| Voce | Stato |
|---|---|
| CSV COMBINAZIONI prodotto da `write_csv` | invariato, e si rilegge (test di andata e ritorno) |
| CSV ANALISI prodotto da `scrivi_output` | invariato come export; in import viene rifiutato con il suo nome |
| Formati legacy con la sola `T_permutazione` | leggibili |
| Intestazioni con BOM, colonne extra, righe vuote, ultima riga senza newline | gestite |
| Ordine delle combinazioni e numerazione «#N» | invariato, verificato con oracolo |
| Chiavi dei filtri, alias `R_U`/`I_3`, `j_uniform` | invariati |
| Matematica di D, I/O di B, stato di C, linguaggio di E | invariati |
| Chiavi i18n | **1289 → 1292**: `analysis.too_large_title`, `analysis.too_large`, `analysis.raw_not_kept`, simmetriche IT/EN. Nessuna rimossa, nessun testo esistente modificato |

Nessun cambiamento di layout, accessibilità o UX: H non è stato iniziato. I messaggi degli
errori di dominio (`FiltroNonValido`, `SchemaNonRiconosciuto`, `PermutazioneNonValida`, le
righe scartate) restano testo neutro del core, come già per D ed E: la loro localizzazione è
un debito dichiarato di H.

## 8. Sweep B01–B12

```text
B01  CORRETTO   400/400 sequenze nel file riletto, tre fogli
B02  CORRETTO   dopo A e import B: aggregati [B], grezzi [], origine 'csv'
B03  CORRETTO   reset durante il lavoro → il completamento tardivo non pubblica
B04  CORRETTO   campi cambiati a (1,5): «ricomincia» usa ancora carta=0 bersaglio=13
B05  CORRETTO   [0,0,99] scartata e tracciata; intestazione 'foo;bar' → SchemaNonRiconosciuto
B06  CORRETTO   4 stadi → FiltroNonValido da entrambi; count == iter su tutti i filtri validi
B07  CORRETTO   'MSC o' e 'MSC)' rifiutate da entrambi, 'I' accettata; 0 discordanze su 125
B08  CORRETTO   cache vuota per un bersaglio in G → miss
B09  CORRETTO   con -O il guasto iniettato resta rilevato
B10  CORRETTO   registrazione font fallita → ('Helvetica', 'Helvetica-Bold')
B11  CORRETTO   ExportTooLarge su 5.159.780.352, nessun file creato
B12  CORRETTO   generatore guasto → _Generato(ok=False)
```

**È il primo punto del progetto in cui tutti e dodici i bug originali risultano chiusi.**
Restano corretti anche `R04`, `R05`, `M02`, `M03`, `N02`, `N06`, e i tre casi storici di B07
sono stati riverificati da Explorer e Mescolamento.

## 9. Test

Ambiente di riferimento invariato (Linux, **Python 3.12.3**, tkinter 8.6 con Xvfb, NumPy
2.5.3, ReportLab 5.0.1, openpyxl 3.1.5, pypdf 6.18.1, pikepdf 10.13.0, pytest 9.1.1,
pyflakes 3.4.0). Comando:
`PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m pytest -p no:cacheprovider -ra -q`.

| Voce | Prima di F | Dopo F |
|---|---:|---:|
| Raccolti | 1097 | **1209** |
| Passati | 1096 | **1208** |
| Falliti | 0 | **0** |
| Saltati | 1 | **1** (N03) |
| xfail / xpass | 0 / 0 | **0 / 0** |
| Durata | ~62 s | **~62 s** |

Mirati: `tests/test_analisi_filtri_f.py` → **112 test** in 0,7 s. Compartimenti precedenti:
baseline matematica **25**, dominio D **163**, I/O B **149**, stato C **78**, linguaggio E
**228**, statici A (N01) **2**, combinazioni/filtri/export/annullamento **132**. `pyflakes` su
`gioco27`, `tests`, `conftest.py`, `gioco27.py`: nessun avviso, a ogni passo.

**Ogni commit è stato verificato singolarmente con la suite completa**, ricostruendo l'albero
esatto di quel commit nell'ambiente di riferimento (confronto per hash dei file):

| Commit | Suite |
|---|---|
| `test(F)` B05 | 1097 passati, 1 saltato, **3 xfailed**, 0 falliti |
| `fix(F)` B05 | 1131 passati, 1 saltato, 0 falliti |
| `test(F)` B06 | 1131 passati, 1 saltato, **2 xfailed**, 0 falliti |
| `fix(F)` B06 | 1188 passati, 1 saltato, 0 falliti |
| `fix(F)` R01 preflight | 1197 passati, 1 saltato, 0 falliti |
| `refactor(F)` aggregazione | 1201 passati, 1 saltato, 0 falliti |
| `refactor(F)` kronecker | 1208 passati, 1 saltato, 0 falliti |

## 10. File modificati

| File | Tema |
|---|---|
| `gioco27/core/analisi.py` | **nuovo** — schema, validazione, diagnostica, aggregatore, piano e budget |
| `gioco27/core/combinations.py` | contratto unico dei filtri (`FiltroStadio`, `normalizza_filtri`, `N_STADI`) |
| `gioco27/core/algebra.py` | `analizza_righe` / `analizza_csv` delegano alla pipeline |
| `gioco27/core/kronecker.py` | ramo morto rimosso (432 → 357 righe) |
| `gioco27/gui/analysis_tab.py` | preflight, aggregazione incrementale, diagnostica visibile |
| `gioco27/i18n.py` | tre chiavi nuove, IT e EN |
| `tests/test_analisi_filtri_f.py` | **nuovo** — 112 test su B05, B06, R01, kronecker |
| `tests/test_stato_concorrenza_c.py`, `tests/test_rischi_concorrenza.py` | il finto preflight sostituisce il finto conteggio; il finto widget di stato si legge |
| `tests/test_i18n.py` | `T` di prova valida; conteggi del catalogo |
| `tests/test_i18n_anomalie_ui.py`, `tests/test_i18n_audit_finale.py` | conteggi del catalogo 1289 → 1292 |

Diff sintetico `83f02f0..HEAD`: **12 file, 1518 inserimenti, 299 cancellazioni**.

## 11. Cosa non è stato fatto, di proposito

* Nessun servizio generale di G: niente `ApplicationService`, `AnalysisService`, `JobManager`,
  `ResultSnapshot` condiviso, repository o dependency injection. `RisultatiImport` resta una
  lista e `PianoAnalisi` una dataclass di quattro campi.
* Nessuna correzione di H (`M01`, `M04`, `M06`, `M05` residuo) e nessuna revisione dei testi.
* Nessuna dichiarazione di dipendenze o infrastruttura di K (`N03`, `N04`).
* Nessuna generalizzazione del gioco a N stadi.
* Nessuna modifica alla matematica delle decomposizioni per guadagnare velocità.
* Nessun compartimento successivo iniziato: G, H, I, J, K restano intatti.

## 12. Commit locali

| # | Hash | Messaggio |
|---|---|---|
| 1 | `65fa108` | `test(F): expose invalid analysis input acceptance (B05)` |
| 2 | `df040fc` | `fix(F): validate imported analysis data (B05)` |
| 3 | `c947cdf` | `test(F): expose filter count/iterator divergence (B06)` |
| 4 | `a588b0c` | `fix(F): establish validated three-stage filter contract (B06)` |
| 5 | `7f1969f` | `fix(F): preflight and bound analysis workloads (R01)` |
| 6 | `083ac96` | `refactor(F): aggregate analysis incrementally` |
| 7 | `8e1cdf2` | `refactor(F): remove unreachable kronecker branch` |
| 8 | — | `docs(F): record closed analysis compartment` (questo documento) |

Nessun push, nessun `reset`/`rebase` distruttivo, nessun commit precedente riscritto.
`origin/main` resta a `54445af`.

## 13. `git status` finale

```text
On branch main
Your branch is ahead of 'origin/main' by 36 commits.

nothing to commit, working tree clean
```

Nessun `__pycache__`, nessun `.pytest_cache`, nessun artefatto di esecuzione lasciato nel
repository.

## 14. Gate di uscita

| Gate | Esito |
|---|---|
| F-G1 B05 rifiuta T matematicamente invalide | **OK** — § 2, contratto di D |
| F-G2 schema CSV invalido ≠ zero risultati | **OK** — § 2, `SchemaNonRiconosciuto` |
| F-G3 righe invalide non spariscono | **OK** — § 2, `RigaScartata` con numero, campo, motivo |
| F-G4 formula e T confrontate quando entrambe presenti | **OK** — § 2, parser unico di E |
| F-G5 schemi legacy realmente supportati leggibili | **OK** — § 2, file con la sola `T_permutazione` |
| F-G6 numero di stadi non supportato rifiutato | **OK** — § 3, `N_STADI = 3` |
| F-G7 count e iterator condividono il contratto | **OK** — § 3, verificato sull'AST |
| F-G8 count == iter su tutti i filtri validi piccoli | **OK** — § 3, famiglia di 14 |
| F-G9 R01 intercetta 5.159.780.352 prima dell'enumerazione | **OK** — § 4, sentinella |
| F-G10 aggregazione senza materializzazione illimitata | **OK** — § 4 |
| F-G11 reset/revisione di C continuano a invalidare | **OK** — § 4, test di reset e nuova richiesta |
| F-G12 nessun risultato parziale presentato come completo | **OK** — § 4, `grezzi=()` + diagnostica |
| F-G13 ramo morto Kronecker risolto | **OK** — § 5, rimosso con prova prima/dopo |
| F-G14 semantica/parser E invariati | **OK** — 228/228, tre casi storici riverificati |
| F-G15 matematica D invariata | **OK** — 25/25 e 163/163 |
| F-G16 I/O B invariato | **OK** — 149/149 |
| F-G17 stato/concorrenza C invariato | **OK** — 78/78, contratti verificati da un test di F |
| F-G18 B01–B12 tutti corretti | **OK** — § 8 |
| F-G19 suite completa verde | **OK** — 1208 passati, 1 saltato, 0 falliti |
| F-G20 nessun servizio generale di G introdotto | **OK** — § 11 |
| F-G21 nessun altro compartimento iniziato | **OK** — § 11 |
| F-G22 nessun push | **OK** — `origin/main` fermo a `54445af` |

**Il compartimento F è chiuso.**

## 15. Debiti rimasti

| Voce | Stato | Proprietario |
|---|---|---|
| **B01–B12** | **tutti chiusi** | — |
| **R01** | **chiuso in F** per l'analisi | — |
| **R04, R05** | chiusi in D e C | — |
| **R06** | presente | K |
| **R07** | presente | G |
| **M01, M04, M06** | presenti | H |
| **M05 residuo** | conservazione dei temporanei HTML di `protocol_dialog` | H |
| **N03** `pypdfium2` non dichiarata | aperto: unico skip della suite | K |
| **N04** `gioco27.spec` non versionato | aperto | K |
| Analisi oltre 1.000.000 di combinazioni | rifiutata: servirebbe un'aggregazione che non tenga le formule distinte, cioè un contratto di risultato diverso | G |
| Re-import dell'export analisi con semantica propria | non supportato: oggi viene rifiutato con il suo nome | G |
| Modello condiviso dei risultati fra schede (`AnalysisResult`) | aperto: `RisultatiImport` è una lista locale | G |
| Ciclo di vita generale dei lavori (coda, priorità, annullamento) | aperto | G |
| Separare il linguaggio dalle funzioni di export in `core/algebra.py` | aperto | G |
| Localizzazione dei messaggi d'errore di dominio | aperto: restano testo neutro del core | H |
| Duplicazioni preservate come oracoli | **da non rimuovere** senza sostituto indipendente | G, E |

Nessun compartimento successivo è stato iniziato: G, H, I, J e K restano intatti.
