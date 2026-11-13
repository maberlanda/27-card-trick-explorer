# B_IO_CLOSED — chiusura del compartimento B (Integrità I/O)

Registro verificabile. Il quadro generale resta in `GIT_BASELINE_AND_RECONCILIATION.md`;
le chiusure precedenti in `A_BASELINE_CLOSED.md` e `D_DOMAIN_CLOSED.md`.

## 1. Identità

| Voce | Valore |
|---|---|
| Branch | `main` — nessun push: `origin/main` resta a `54445af` |
| HEAD iniziale | `defd192942f2a638c314c4bf029d44787baef4bf` — «docs(D): record closed domain compartment» |
| HEAD finale | l'ultimo commit dell'elenco in § 11 |
| Working tree all'avvio | pulito; commit di A e D presenti e non riscritti |
| Baseline di partenza | 801 raccolti, **800 passati, 1 saltato, 0 falliti**, 82,2 s — coincide con quella attesa dopo D; `pytest tests/test_baseline_matematica.py` → 25 passati |

L'unico skip resta **N03** (`pypdfium2` non installata), debito di K.

## 2. B01 — Excel grezzo: nessuna sequenza persa

**Riproduzione.** `_export_analisi_raw_excel` concatenava tutte le sequenze Stage di una
permutazione in una sola cella. Con 400 sequenze: **46.799 caratteri attesi, 32.767 riletti**;
l'ultima sequenza sparita, e l'app che dichiarava `✓ Excel grezzi: …`.

**Soluzione.**

* Nuovo terzo foglio **«Simbolica -> Perm»**, *una sequenza per riga* (colonne
  `T_simbolica | T_permutazione | n_sim_distinte`): il dettaglio è sempre completo e
  ricostruibile, e non esiste più una concatenazione che possa essere troncata.
* Il riepilogo compatto resta dov'era; quando supera il limite diventa **esplicito** e rimanda al
  foglio di dettaglio, con lo stesso messaggio già usato da `core.algebra.scrivi_excel`
  (`export.excel.summary_overflow`).
* Il limite è ora la costante condivisa `EXCEL_MAX_CELL_CHARS = 32767` in `core/algebra.py`,
  usata da entrambi gli esportatori.

**Compatibilità Excel.** I due fogli storici — «Dati grezzi» e «Analisi molteplicità» — restano
**identici** per nome, intestazioni, ordine delle colonne e struttura delle righe; il terzo è
un'aggiunta. Nessuna chiave i18n aggiunta o rimossa (**1288 + 1288**): il testo della Guida
(IT/EN) che descriveva «due fogli» ora ne descrive tre, e il test che tiene allineati Guida e
codice è stato aggiornato di conseguenza.

**Test** (`tests/test_io_integrita_b.py`, sempre sul **file riletto**, mai sul workbook in
memoria): 400 sequenze tutte ritrovate; confini **32.766 / 32.767 / 32.768** (sotto soglia il
riepilogo resta intero, sopra diventa il messaggio esplicito, e in ogni caso il dettaglio contiene
le sequenze intere); nomi e intestazioni dei tre fogli.

## 3. B08 / N06 — la cache distingue validità e completezza

**Vecchio contratto.** `validate_decompositions(target, results)` controllava solo che ogni
decomposizione presente ricostruisse il bersaglio. `cache.load_decompositions` usava quello:
un `results: []` veniva restituito come risposta definitiva anche per un bersaglio che di
decomposizioni ne ha 46.656.

**Nuovo contratto.** Due funzioni distinte in `core/kronecker.py`:

| Funzione | Controlla | Uso |
|---|---|---|
| `validate_decompositions` (invariata) | validità **interna**: ogni terna presente ricostruisce il bersaglio | viste filtrate, contesti deliberatamente parziali, risultati in corso |
| `validate_complete_decompositions` (nuova) | in più: **cardinalità attesa** e **unicità** | cache su disco |

`cardinalita_attesa(target)` è un fatto matematico, non un'euristica: **46.656** se il bersaglio
appartiene a G (deciso con `appartiene_a_G`, introdotto in D), **0** se ne sta fuori. Solleva
`DecomposizioniIncomplete(ValueError)`.

**Cache miss / ricalcolo.** `load_decompositions` usa il contratto completo: elenco incompleto,
con duplicati o semanticamente corrotto → il file viene **rimosso** e la funzione restituisce
`None`, quindi il chiamante ricalcola. Per un bersaglio fuori da G l'elenco vuoto è la risposta
completa e viene restituito. La scrittura resta permissiva (l'unico produttore è la ricerca
completa): il controllo che conta è in lettura, e nulla di incompleto può essere presentato come
risposta.

**N06 — test aggiornato esplicitamente.** `test_b11_cache_json_v2_valida_accettata`
pretendeva che una cache con **0 o 1** decomposizioni fosse riletta tale e quale: *descriveva il
bug*. È stato sostituito — con la motivazione scritta nel file, non nascosta — da:

* `test_b08_cache_parziale_non_e_accettata_come_completa` (0, 1, 1, e con duplicati);
* `test_b08_cache_completa_accettata` (46.656, round trip in formato 2);
* `test_b08_fuori_da_G_zero_e_completo`;
* `test_b08_validate_decompositions_resta_parziale` (il contratto parziale non è cambiato).

Tre test di hardening/concorrenza usavano la cache come semplice scrittore di file, con payload
giocattolo: ora verificano il **JSON pubblicato** invece del valore restituito da
`load_decompositions`. Continuano a testare atomicità e collisioni fra istanze, senza dipendere
dalla semantica che è cambiata.

## 4. B10 — fallback dei font realmente utilizzabile

Se `registerFont` falliva, l'eccezione veniva ingoiata e `_ensure_fonts` restituiva comunque
`("DV", "DVB")`: nomi non registrati, che il chiamante passava a `setFont`.

I nomi DejaVu vengono ora restituiti **solo dopo una registrazione riuscita**; in ogni altro caso
si ripiega su Helvetica (sempre disponibile in ReportLab) e il motivo finisce nel log. Anche una
registrazione **parziale** (primo font sì, secondo no) ripiega su entrambi i font base: non si
mescolano i due insiemi.

**Failure injection nei test:** font presenti e validi, font mancanti, font corrotti, errore di
`registerFont`, registrazione parziale. In più, in un **processo nuovo** (sottoprocesso, così
nessun font è già registrato da un test precedente) viene davvero disegnato un PDF con i nomi
restituiti: un fallback inutilizzabile farebbe fallire `setFont`.

## 5. B11 — limite di sicurezza uniforme

**Policy comune:** `check_export_size` di `core/parallel.py`, chiamato **prima** di aprire il file
e prima di avviare l'enumerazione. Nessuna logica duplicata.

| Entry point | Prima | Dopo |
|---|---|---|
| `permutations.write_csv` | **nessun preflight** | `check_export_size(count_combinations_ex(filters))` |
| `permutations.write_csv_parallel` | già protetto | invariato |
| `combinations.generate_pdf`, `generate_pdf_ex` | già protetti | invariati |
| `combinations._pdf_parallel` (usato da entrambe le rotte PDF parallele) | già protetto | invariato |

**Test:** con i filtri tutti liberi (**5.159.780.352** combinazioni) `write_csv` solleva
`ExportTooLarge` mentre una sentinella al posto di `iter_combinations_ex` dimostra che il
generatore **non viene nemmeno avviato**; nessun file e nessun temporaneo restano sul disco; un
export piccolo continua a funzionare; un test sintattico verifica che tutte le rotte pubbliche
analoghe abbiano il preflight.

## 6. B12 — errore e contenuto sono tipi distinti

`_content` restituisce ora `_Generato(ok, testo, errore)` invece di una stringa che, in caso di
guasto, conteneva `% Errore nella generazione: …` e finiva salvata come file `.svg`/`.tex`
riuscito.

* Anteprima: l'errore si vede, localizzato come prima.
* `_export_all`: un esito fallito **non produce alcun file**; i fallimenti vengono segnalati a
  parte e il riepilogo elenca **solo i file davvero scritti**.
* `_dimentica(key)` scarta l'esito in cache: si ritenta dopo una correzione.

**Batch misto** (4 generatori, 2 guasti): vengono creati esattamente i due file buoni, il
conteggio dei riusciti è 2, nessun `.svg` falso.

## 7. R02 — pubblicazione atomica

Rotte migrate in B, tutte con l'`atomic_write` già esistente in `core/parallel.py` (nessun
secondo sistema di scrittura atomica):

| Rotta | File |
|---|---|
| Excel dell'analisi molteplicità | `core/algebra.py::scrivi_excel` |
| CSV grezzo, Excel grezzo, HTML del tab Analisi | `gui/analysis_tab.py` |
| File dei dialoghi di export di gruppo | `gui/export_group_dialog.py::_export_all` |
| HTML di Cayley, coniugio, decomposizioni | `gui/cayley_dialog.py`, `gui/conjugacy_dialog.py`, `gui/decomposition.py` |

**Semantica di commit:** si scrive su un temporaneo univoco nella stessa directory della
destinazione, e solo a scrittura conclusa `os.replace` pubblica. La destinazione o non esiste, o
è completa.

**Guasti iniettati** (generazione, salvataggio della libreria, scrittura): destinazione
precedente **intatta**, nessun falso successo, nessun temporaneo proprio lasciato in giro,
file vicini non toccati.

## 8. R03 — temporanei PDF univoci

`<path>.dedup` era un nome fisso: due deduplicazioni sulla stessa destinazione si sovrascrivevano
il temporaneo a vicenda e la pulizia dell'una cancellava il lavoro dell'altra. Ora `_temporaneo()`
crea un file univoco con `mkstemp` **nella directory della destinazione**, così `os.replace`
resta atomico e ogni job possiede il suo; il ripiego pypdf rimuove il proprio temporaneo anche
quando esce prima di usarlo.

**Test di concorrenza deterministico:** la seconda deduplicazione parte *dentro* la prima, quando
il suo temporaneo è pronto ma non ancora pubblicato. Verifica: temporanei distinti, nessuno tocca
quello dell'altro, PDF finale valido (2 pagine), nessun residuo.

## 9. M05 — URI e temporanei

**Modificati:** i quattro punti che componevano `"file://" + percorso` —
`gui/analysis_tab.py`, `gui/cayley_dialog.py`, `gui/conjugacy_dialog.py`, `gui/decomposition.py` —
ora usano `Path(path).resolve().as_uri()`.

**Non modificati:** `gui/protocol_dialog.py`, che usava **già** `as_uri` (la baseline A0 lo aveva
già rilevato); la politica di conservazione dei temporanei HTML di quel dialogo resta un debito
aperto, fuori dal perimetro di B.

**Test:** percorsi con spazi, accenti, `#` e i tre insieme; l'URL passato al browser viene
ri-tradotto con `url2pathname` e deve tornare **esattamente** il file scritto. Un test scandisce
tutto il package: nessun URI costruito a mano.

## 10. Compatibilità

**Invariati:** nomi dei file, separatori e encoding del CSV, intestazioni e ordine delle colonne,
nomi dei due fogli Excel storici, numerazioni, alias, D#, tavola, convenzioni matematiche,
formato della cache (versione 2), chiavi i18n (1288 + 1288).

**Aggiunte deliberate e documentate:**

| Aggiunta | Motivo | Dove è documentata |
|---|---|---|
| terzo foglio «Simbolica -> Perm» nell'Excel grezzo | B01: dettaglio completo non troncabile | Guida IT/EN, `test_documentazione_d4d5.py` |
| `EXCEL_MAX_CELL_CHARS` | limite unico per i due esportatori | `core/algebra.py` |
| `validate_complete_decompositions`, `cardinalita_attesa`, `DecomposizioniIncomplete` | B08: completezza ≠ validità | `core/kronecker.py` |
| `_Generato` e `_dimentica` | B12: successo ≠ errore | `gui/export_group_dialog.py` |
| `pdfmerge._temporaneo` | R03 | `core/pdfmerge.py` |

Il vecchio formato della cache continua a essere letto: versione, struttura e chiave di hash non
cambiano; cambia solo il criterio con cui una entry viene accettata.

## 11. Test

Ambiente di riferimento invariato (Linux, **Python 3.12.3**, tkinter 8.6 con Xvfb, NumPy 2.5.3,
ReportLab 5.0.1, openpyxl 3.1.5, pypdf 6.18.1, pikepdf 10.13.0, pytest 9.1.1, pyflakes 3.4.0).

| Voce | Prima di B | Dopo B |
|---|---:|---:|
| Raccolti | 801 | **833** |
| Passati | 800 | **832** |
| Falliti | 0 | **0** |
| Saltati | 1 | **1** (N03) |
| Durata | 82,2 s | **87,2 s** |

* Test mirati di B: `tests/test_io_integrita_b.py` → **28 passati**; B08/N06 in
  `tests/test_decomposition_integrita.py` → **7 passati**.
* Baseline matematica di D: `tests/test_baseline_matematica.py` → **25 passati**; insieme ai test
  di dominio → **123 passati**. Nessuna regressione.
* Statici: `test_no_pyflakes_warnings` e `test_no_undefined_names` verdi.
* Ogni commit di B è stato verificato singolarmente in un worktree separato sul sottoinsieme
  non-GUI (static, core, baseline matematica, hardening, output): **170 passati** su tutti e
  sette, nessun commit rosso.

**Non-regressione dei bug fuori scope** — riproduzioni rieseguite dopo le modifiche:

```text
B01  CORRETTO   400/400 sequenze nel file riletto, tre fogli
B02  PRESENTE   grezzi della sessione precedente ancora presenti      (C)
B03  PRESENTE   il worker tardivo annulla il reset                    (C)
B04  PRESENTE   _practice_reset rilegge il campo carta                (C)
B05  PRESENTE   [0,0,99] ancora accettata come T                      (F)
B06  PRESENTE   4 stadi: count=6, iter=1                              (F)
B07  PRESENTE   'MSC o' accettata dal visualizzatore, non da Explorer (E)
B08  CORRETTO   cache vuota in G -> miss + invalidazione; completa -> 46.656
B09  CORRETTO   con -O il guasto iniettato resta rilevato             (D)
B10  CORRETTO   registrazione fallita -> ('Helvetica', 'Helvetica-Bold')
B11  CORRETTO   ExportTooLarge su 5.159.780.352, nessun file creato
B12  CORRETTO   generatore guasto -> _Generato(ok=False), nessun file
```

## 12. File modificati

| File | Tema |
|---|---|
| `gioco27/core/algebra.py` | B01 (costante, riepilogo) + R02 |
| `gioco27/gui/analysis_tab.py` | B01 (terzo foglio, guardia) + R02 + M05 |
| `gioco27/i18n.py` | B01: testo della Guida IT/EN (nessuna chiave aggiunta) |
| `gioco27/core/kronecker.py` | B08: contratto di completezza |
| `gioco27/core/cache.py` | B08: lettura che invalida e ricalcola |
| `gioco27/core/detail_pdf.py` | B10 |
| `gioco27/core/permutations.py` | B11 (solo il percorso di export) |
| `gioco27/gui/export_group_dialog.py` | B12 + R02 |
| `gioco27/gui/cayley_dialog.py`, `conjugacy_dialog.py`, `decomposition.py` | R02 + M05 |
| `gioco27/core/pdfmerge.py` | R03 |
| `tests/test_io_integrita_b.py` | **nuovo** — B01, B10, B11, B12, R02, R03, M05 |
| `tests/test_decomposition_integrita.py` | B08 / **N06** |
| `tests/test_hardening.py`, `tests/test_rischi_concorrenza.py` | adeguati al nuovo contratto della cache |
| `tests/test_documentazione_d4d5.py` | tre fogli nell'Excel grezzo |
| `tests/test_i18n_audit_finale.py` | anteprima con esito tipizzato (B12) |
| `B_IO_CLOSED.md` | questo file |

Nessun file matematico di D è stato toccato se non `permutations.py`, e lì **solo** dentro
`write_csv`: validazione, nomenclatura base 0, helper di dominio e calcolo delle permutazioni
sono rimasti identici (baseline matematica verde prima e dopo).

## 13. Commit locali

| Commit | Messaggio |
|---|---|
| `5afe0e2` | `fix(B): preserve complete raw Excel data (B01, R02, M05)` |
| `c48f9c0` | `fix(B): validate complete decomposition cache (B08, N06)` |
| `2fc74a4` | `fix(B): make PDF font fallback reliable (B10)` |
| `f3fd117` | `fix(B): enforce export size limits consistently (B11)` |
| `9ec275b` | `fix(B): separate export errors from content (B12, R02)` |
| `bd3cbe5` | `fix(B): atomic HTML export and correct file URIs (R02, M05)` |
| `035f07a` | `fix(B): use unique PDF temporaries (R03)` |
| (ottavo) | `docs(B): record closed I/O compartment` |

Bug indipendenti non mescolati. Dove R02 e M05 viaggiano con un bug (commit 1 e 5) è perché
riguardano **la stessa rotta di pubblicazione** che quel bug ha fatto riscrivere: separarli
avrebbe prodotto commit che toccano le stesse righe senza aggiungere leggibilità. Nessun push.

## 14. `git status` finale

```text
On branch main
Your branch is ahead of 'origin/main' by 17 commits.
nothing to commit, working tree clean
```

## 15. Gate di uscita

| Gate | Esito |
|---|---|
| B-G1 nessuna sequenza Excel persa silenziosamente | **OK** — § 2 |
| B-G2 cache parziale non accettata come completa | **OK** — § 3 |
| B-G3 N06: test aggiornato esplicitamente | **OK** — sostituzione motivata nel file e nel commit |
| B-G4 fallback font realmente utilizzabile | **OK** — § 4, provato disegnando un PDF |
| B-G5 limite applicato da ogni entry point rilevante | **OK** — § 5 |
| B-G6 errore e contenuto separati | **OK** — § 6 |
| B-G7 rotte migrate atomiche | **OK** — § 7 |
| B-G8 nessun temporaneo PDF fisso | **OK** — § 8 |
| B-G9 URI/path corretti dove B ha toccato | **OK** — § 9 |
| B-G10 matematica di D invariata | **OK** — 25/25 e 123/123 |
| B-G11 suite completa verde | **OK** — 832 passati, 1 saltato, 0 falliti |
| B-G12 nessun bug di C/E/F alterato | **OK** — § 11, B02–B07 riprodotti identici |
| B-G13 nessun altro compartimento iniziato | **OK** |
| B-G14 nessun push | **OK** |

**Il compartimento B è chiuso.**

## 16. Debiti rimasti

| Voce | Stato | Proprietario |
|---|---|---|
| **B02, B03, B04** | presenti, non toccati | **C** — stato, revisioni, job lifecycle |
| **B05, B06** | presenti, non toccati | **F** — semantica dell'analisi e dei filtri |
| **B07** | presente, non toccato | **E** — parser unico Explorer/Shuffle |
| **R01** | presente | F (+ C per la cancellazione) |
| **R05, M03** | presenti | C |
| **R06** | presente | K |
| **R07** | presente | C o G |
| **M01, M04, M06** | presenti | H |
| **M05 residuo** | politica di conservazione dei temporanei HTML di `protocol_dialog` | H |
| **N02** | chiuso in D | — |
| **N03** `pypdfium2` non dichiarata | aperto: unico skip della suite | K |
| **N04** `gioco27.spec` non versionato | aperto | K |
| **N06** | **chiuso in B** | — |
| Ramo morto in `core/kronecker.py` dopo il `return` incondizionato | aperto | F |
| Rotte di export non ancora migrate ad atomic_write (dialoghi minori non toccati da B) | aperto | G |
| Duplicazioni preservate come oracoli (inverse, tabelle GEN3/MSC, tavole di Cayley, due parser) | **da non rimuovere** senza sostituto indipendente | G, E |

Nessun compartimento successivo è stato iniziato: C, E, F, G, H, I, J e K restano intatti.
