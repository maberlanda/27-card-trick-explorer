# G1_SERVICES_MODELS_CLOSED — modelli applicativi e confini dei servizi

Primo passo del compartimento **G — Servizi applicativi e modelli di risultato**. Registro
verificabile. Il quadro generale resta in `GIT_BASELINE_AND_RECONCILIATION.md`; le chiusure
precedenti in `A_BASELINE_CLOSED.md`, `D_DOMAIN_CLOSED.md`, `B_IO_CLOSED.md`,
`C_STATE_CLOSED.md`, `E_LANGUAGE_SIMULATION_CLOSED.md` e `F_ANALYSIS_CLOSED.md`.

## 1. Identità

| Voce | Valore |
|---|---|
| Branch | `main` — nessun push: `origin/main` resta a `54445af` |
| HEAD iniziale | `b6bcd7eefc4da2519fe4d97279268a313c4a785a` — «docs(F): record closed analysis compartment» |
| HEAD finale | l'ultimo commit dell'elenco in § 12 |
| Working tree all'avvio | pulito; i commit di A, D, B, C, E ed F presenti e non riscritti |
| Baseline di partenza | 1209 raccolti, **1208 passati, 1 saltato, 0 falliti**; `pytest tests/test_baseline_matematica.py` → 25 passati |
| Perimetro | soltanto il repository corrente |

L'unico skip resta **N03** (`pypdfium2` non installata), debito di K.

## 2. Architettura prima e dopo

```text
PRIMA                                        DOPO

core/algebra.py                              core/algebra.py
  linguaggio (Lexer, Parser, AST, …)           linguaggio, e basta
  + import CSV dell'analisi                  core/analisi.py
  + export CSV/Excel dei risultati             pipeline dell'analisi + ingresso
                                             core/export_analisi.py
gui/analysis_tab.py                            export CSV/Excel dei risultati
  raccoglie input
  pianifica                                  services/modelli.py
  enumera                                      RisultatoAnalisi, Provenienza
  costruisce ogni riga                       services/analisi.py
  aggrega                                      ServizioAnalisi
  compone diagnostica
  costruisce il risultato (×3)               gui/analysis_tab.py
  pubblica                                     raccoglie input
                                               chiede al servizio
                                               decide se pubblicare (revisione)
                                               mostra
```

Responsabilità spostate: **enumerazione, aggregazione, composizione del risultato e della
diagnostica** dalla vista al servizio; **ingresso dell'analisi ed export dei risultati** dal
modulo del linguaggio ai moduli che li possiedono.

Metriche, misurate sull'AST e sul grafo degli import (script di lavoro fuori dal repository):

| Metrica | Prima | Dopo |
|---|---:|---:|
| Moduli GUI che **chiamano** logica di analisi | 2 (`analysis_tab`, `app`) | 1 (`app`, solo `count_combinations_ex` per l'etichetta del conteggio) |
| Chiamate di questo tipo in `analysis_tab.py` | 7 | **0** |
| Moduli core che mescolano linguaggio e I/O | 1 (`algebra.py`) | **0** |
| Punti che costruiscono il risultato dell'analisi | 3, tutti nella GUI | 2, entrambi nel servizio |
| Cicli d'importazione statici | 2 | **1** (`combinations ↔ permutations`, § 9) |
| Archi `gui → services` / `services → core` / `services → gui` | 0 / 0 / 0 | 1 / 4 / **0** |
| Righe di `core/algebra.py` | 1714 | 1633 |

## 3. Modelli applicativi

**Proprietario**: `gioco27/services/modelli.py`. Un solo file definisce `RisultatoAnalisi`, e un
test lo verifica sull'AST dell'intero package; `gui.analysis_tab` ri-esporta **quello**, non una
copia.

| Campo | Significato |
|---|---|
| `origine` | `Provenienza`: `filtri`, `csv`, `pipeline` |
| `aggregati` | le righe aggregate, nella forma di F (`perm_tuple`, `perm_str`, `simboliche`, `n_sim`) |
| `totale` | sequenze rappresentate: combinazioni del dominio, o somma delle molteplicità |
| `grezzi` | le righe di partenza, quando sono state conservate |
| `grezzi_scartati` | il piano ha deciso di non trattenerle |
| `lette` | righe esaminate (import) |
| `scartate` | le `RigaScartata` di F: numero, campo, motivo |
| `nota` | testo già pronto per l'utente |

**Invarianti**: `frozen=True`, sequenze come tuple; `completo`, `parziale`, `vuoto`,
`grezzi_disponibili` e `diagnostica` sono **proprietà derivate**, quindi non possono
contraddire i campi; `con_nota()` produce una copia invece di mutare.

**Stati impossibili eliminati** — prima la vista deduceva tutto da `if righe_grezze:`

```text
zero risultati validi     aggregati == ()            (schema valido, dominio vuoto)
grezzi non conservati     grezzi_scartati = True     (decisione del piano)
origine senza grezzi      grezzi_scartati = False e grezzi == ()
risultato parziale        scartate != ()             (e si sa quali righe)
richiesta fallita         un'eccezione, non un risultato
```

`Provenienza` è un insieme chiuso e nominato, ma sottoclasse di `str`: `Provenienza.FILTRI ==
"filtri"` resta vero, quindi viste e test storici non cambiano.

**Un campo è caduto: `revisione`.** Apparteneva al modello locale di C. Un servizio non ha modo
di sapere quale richiesta sia corrente, e dargli quel campo lo obbligherebbe a inventarselo:
la revisione viaggia ora accanto al risultato, come argomento di
`_analisi_pubblica(risultato, revisione)`. Il meccanismo di C — contatore monotono,
`_analisi_e_corrente`, punto di pubblicazione unico — non cambia di una riga.

Restano dove sono, perché non hanno un secondo consumatore: `RisultatiImport`, `PianoAnalisi`,
`RigaScartata`, `SchemaCsv` (F, contratti dell'ingresso), `TracciaEsecuzione`,
`PassoEsecuzione` (E, contratti del linguaggio), `SessionePratica` (C), `_Generato` (B).

## 4. Servizio di analisi

`gioco27/services/analisi.py` — `ServizioAnalisi`.

| Metodo | Ingresso | Uscita |
|---|---|---|
| `pianifica(filtri)` | filtri | `PianoAnalisi`; `FiltroNonValido` / `AnalisiTroppoGrande` |
| `da_filtri(filtri, piano=, progresso=, ancora_valida=)` | filtri | `RisultatoAnalisi`, o `None` se la richiesta è stata superata |
| `da_csv(percorso)` | percorso | `RisultatoAnalisi`; `SchemaNonRiconosciuto` |
| `pipeline_csv(ingresso, csv, xlsx, ancora_valida=)` | percorsi | `RisultatoAnalisi`, dopo aver scritto i due file |

**Dipendenze**: `core.analisi` (piano, aggregatore, import), `core.combinations`
(enumerazione), `core.permutations` (`make_csv_row`), `core.export_analisi` (le due scritture),
`services.modelli`. Nessun import della GUI, nessun `tkinter`, nessun `threading`.

**Rapporto con F**: gli algoritmi non sono stati riscritti. La policy resta di F e non è stata
toccata — `LIMITE_GREZZI = 100_000`, `LIMITE_ANALISI = 1_000_000`, verificati da un test. Il
servizio orchestra e traduce in modello; l'analisi oltre il milione resta rifiutata come F ha
deciso, e l'export dell'analisi resta non importabile.

**Sincrono per contratto**: il servizio non sa di essere chiamato da un thread. Chi lo chiama da
un worker gli passa `ancora_valida()`, interrogata ogni 200 combinazioni e prima di concludere;
quando dice di no il servizio smette e restituisce `None` — nessun risultato a metà viene
costruito. Nessun JobManager è stato introdotto.

## 5. Linguaggio

| Simbolo | Prima | Dopo |
|---|---|---|
| Lexer, Parser, `SymbolicExpr`, Evaluator, Rewriter, Controller, AlgebraEngine | `core/algebra.py` | invariati, `core/algebra.py` |
| `analizza_righe`, `analizza_csv` | `core/algebra.py` (deleganti da F) | `core/analisi.py` |
| `scrivi_output`, `scrivi_excel`, `EXCEL_MAX_CELL_CHARS` | `core/algebra.py` | `core/export_analisi.py` |

`core/algebra.py` non importa più `csv`, non conosce `openpyxl` e non scrive su disco: un test
lo verifica sull'AST. `core/espressione.py` (E) resta il confine neutro del linguaggio e non è
stato duplicato: nessun `ExpressionService` che faccia da semplice inoltro.

**Adapter legacy.** I cinque nomi traslocati restano importabili da `core.algebra` attraverso un
`__getattr__` di modulo (PEP 562) che li risolve **a richiesta**. La risoluzione differita è
ciò che tiene aciclico il grafo: `core.analisi` usa il parser di `core.espressione`, che importa
`core.algebra`, e un `from … import` in cima ricreerebbe il ciclo. Un test verifica sia che la
facciata risolva verso i nuovi proprietari, sia che non introduca l'import.

## 6. GUI

**Logica rimossa** da `gui/analysis_tab.py`: enumerazione (`iter_combinations_ex`), costruzione
delle righe (`make_csv_row`), aggregazione (`Aggregatore`, `analizza_righe`), import
(`analizza_csv`), pianificazione diretta (`pianifica_analisi`), composizione della diagnostica e
tre costruzioni distinte del risultato. Un test verifica che nel modulo non resti **nessuna**
chiamata a quel motore.

**Responsabilità rimasta**: raccogliere i filtri, mostrare il preflight (troppo grande, filtro
non valido, conferma sopra 50.000), aprire i dialoghi dei file, riportare l'avanzamento,
mantenere la revisione e decidere se pubblicare, popolare tabella e dettaglio, eseguire gli
export che l'utente chiede.

**UX invariata**: nessuna finestra, pulsante, etichetta, chiave i18n o comportamento è cambiato.
La prova è la caratterizzazione del § 10, scritta prima dell'estrazione e mai più toccata.

## 7. API legacy

| Simbolo | Classificazione | Stato |
|---|---|---|
| `core.algebra.analizza_righe`, `.analizza_csv` | pubblica, ancora usata (test) | facciata → `core.analisi` |
| `core.algebra.scrivi_output`, `.scrivi_excel`, `.EXCEL_MAX_CELL_CHARS` | pubblica, ancora usata (test, GUI) | facciata → `core.export_analisi` |
| `core.analisi.aggrega_righe` / `importa_csv` | interne al core, usate dal servizio | invariate |
| `gui.analysis_tab.RisultatoAnalisi` | pubblica, ancora usata | ri-export del modello condiviso |
| `_prep_explorer_expr` | interna alla presentazione | lasciata dov'è |
| `iter_combinations` / `count_combinations` (nomi storici, F) | pubbliche | invariate |

Nessun simbolo è stato rimosso. Nessuna migrazione «flag day»: la facciata resta finché un
compartimento successivo non decida di rompere quei nomi.

## 8. Dipendenze

```text
PRIMA                          DOPO
gui → core        46           gui → core        45
core → core       45           gui → services     1
(nessun services)              services → core    4
                               services → gui     0
                               core → services    0
```

Verificato inoltre, in un sottoprocesso: importare `gioco27.services` non carica
`gioco27.gui` né `tkinter`.

## 9. Ciclo `combinations ↔ permutations`

Esiste ancora. `core.combinations` importa `core.permutations` in cima (gli serve
`compute_stage`, `kron_label`, `MAT3_P` per rendere i PDF); `core.permutations` importa
`core.combinations` **dentro** `write_csv` e `write_csv_parallel`, cioè solo per avere
l'enumeratore al momento dell'export.

Spezzarlo significa spostare l'orchestrazione degli export in un livello proprio — il
consolidamento che il perimetro di G1 esclude. Non è stato creato nessun modulo artificiale per
azzerare un contatore: il ciclo è **dichiarato**, confinato a due import differiti, e un test ne
fissa esattamente la forma perché non si allarghi. Va a **G2**.

## 10. Test

Ambiente di riferimento invariato (Linux, **Python 3.12.3**, tkinter 8.6 con Xvfb, NumPy 2.5.3,
ReportLab 5.0.1, openpyxl 3.1.5, pypdf 6.18.1, pikepdf 10.13.0, pytest 9.1.1, pyflakes 3.4.0).

| Voce | Prima di G1 | Dopo G1 |
|---|---:|---:|
| Raccolti | 1209 | **1253** |
| Passati | 1208 | **1252** |
| Falliti | 0 | **0** |
| Saltati | 1 | **1** (N03) |
| xfail / xpass | 0 / 0 | **0 / 0** |
| Durata | ~90 s | ~91 s |

* **Caratterizzazione** (5 test): guidano la scheda vera con il core vero — finti solo Tk e i
  thread — e fissano aggregati, righe grezze, provenienza e diagnostica delle quattro strade.
  Scritti nel primo commit, mai modificati dopo: sono la prova che G1 non ha cambiato
  comportamento.
* **Equivalenza** (13 test): il percorso storico è riscritto per esteso nel file di test e
  confrontato con il servizio su cinque famiglie di filtri (modalità completa e aggregata),
  sull'import valido, su quello parziale, sullo schema invalido, sull'export non importabile e
  sulla pipeline. Non è la stessa funzione chiamata due volte.
* **Modello** (3 test): stati distinguibili, immutabilità, provenienza chiusa ma testuale.
* **Architettura** (11 test): § 2, § 5, § 8, § 9.
* **Adattatore GUI** (5 test): la scheda pubblica ciò che il servizio restituisce; la revisione
  continua a rifiutare un risultato superato.
* Compartimenti precedenti: baseline matematica **25**, dominio D **163**, I/O B **149**, stato
  C **78**, linguaggio E **228**, analisi F **112**, statici A (N01) **2**.
* `pyflakes` su `gioco27`, `tests`, `conftest.py`, `gioco27.py`: nessun avviso, a ogni passo.

**Ogni commit è stato verificato singolarmente con la suite completa**, ricostruendo l'albero
esatto di quel commit nell'ambiente di riferimento (confronto per hash dei file):

| Commit | Suite |
|---|---|
| `test(G1)` caratterizzazione | 1213 passati, 1 saltato, 0 falliti |
| `refactor(G1)` modello condiviso | 1216 passati, 1 saltato, 0 falliti |
| `refactor(G1)` linguaggio separato | 1219 passati, 1 saltato, 0 falliti |
| `refactor(G1)` servizio + migrazione GUI | 1244 passati, 1 saltato, 0 falliti |
| `test(G1)` confini architetturali | 1252 passati, 1 saltato, 0 falliti |

## 11. Sweep B01–B12

```text
B01 CORRETTO   B02 CORRETTO   B03 CORRETTO   B04 CORRETTO
B05 CORRETTO   B06 CORRETTO   B07 CORRETTO   B08 CORRETTO
B09 CORRETTO   B10 CORRETTO   B11 CORRETTO   B12 CORRETTO
```

Tutti e dodici restano chiusi, come alla fine di F; `M03` pure. Lo sweep gira attraverso la
facciata di `core.algebra`, quindi verifica anche quella.

## 12. File modificati

| File | Tema |
|---|---|
| `gioco27/services/modelli.py` | **nuovo** — `RisultatoAnalisi`, `Provenienza` |
| `gioco27/services/analisi.py` | **nuovo** — `ServizioAnalisi` |
| `gioco27/services/__init__.py` | **nuovo** — superficie pubblica dei servizi |
| `gioco27/core/export_analisi.py` | **nuovo** — export CSV/Excel dei risultati (spostato) |
| `gioco27/core/algebra.py` | resta il linguaggio; facciata differita per i nomi traslocati |
| `gioco27/core/analisi.py` | prende `analizza_righe` e `analizza_csv` |
| `gioco27/gui/analysis_tab.py` | usa il servizio; niente più orchestrazione (−204 righe nette) |
| `tests/test_servizi_g1.py` | **nuovo** — 44 test: caratterizzazione, equivalenza, modello, architettura |
| `tests/test_stato_concorrenza_c.py` | i finti passano dai pezzi dell'algoritmo al servizio; modello senza `revisione` |
| `tests/test_rischi_concorrenza.py` | i finti si spostano dentro il servizio, dove ora vive il lavoro |
| `tests/test_analisi_filtri_f.py` | sentinelle e piano finto spostati sul servizio; forma del modello |

Diff sintetico `b6bcd7e..HEAD`: **11 file, 1332 inserimenti, 340 cancellazioni**.

## 13. Commit locali

| # | Hash | Messaggio |
|---|---|---|
| 1 | `37269fb` | `test(G1): characterize analysis behaviour through the tab` |
| 2 | `4be4ee9` | `refactor(G1): introduce shared analysis result model` |
| 3 | `3162958` | `refactor(G1): separate language from analysis and export responsibilities` |
| 4 | `974c00c` | `refactor(G1): extract analysis application service and migrate the tab` |
| 5 | `f46168d` | `test(G1): enforce architectural boundaries` |
| 6 | — | `docs(G1): record service boundary milestone` (questo documento) |

Nessun push, nessun `reset`/`rebase` distruttivo, nessun commit precedente riscritto.
`origin/main` resta a `54445af`.

## 14. `git status` finale

```text
On branch main
Your branch is ahead of 'origin/main' by 42 commits.

nothing to commit, working tree clean
```

Nessun `__pycache__`, nessun `.pytest_cache`, nessun artefatto di esecuzione.

## 15. Gate di uscita

| Gate | Esito |
|---|---|
| G1-G1 contratto applicativo condiviso del risultato | **OK** — § 3 |
| G1-G2 filtri/import/pipeline convergono sullo stesso tipo | **OK** — § 4, tre metodi, un modello |
| G1-G3 la GUI non ricostruisce la semantica | **OK** — § 6, zero chiamate al motore |
| G1-G4 il calcolo è testabile senza Tk | **OK** — § 10, equivalenza senza GUI |
| G1-G5 i servizi non importano la GUI | **OK** — § 8, verificato anche a runtime |
| G1-G6 parser/AST indipendenti dalla GUI | **OK** — § 5 |
| G1-G7 resta un solo parser autorevole | **OK** — il test di E è invariato e verde |
| G1-G8 semantica F invariata | **OK** — § 4, § 10, 112/112 |
| G1-G9 soglie 100.000 / 1.000.000 invariate | **OK** — verificato da un test |
| G1-G10 contratti di revisione C invariati | **OK** — § 3, 78/78 |
| G1-G11 formati I/O invariati | **OK** — export spostato senza toccarne una riga |
| G1-G12 matematica invariata | **OK** — 25/25 |
| G1-G13 B01–B12 ancora corretti | **OK** — § 11 |
| G1-G14 nessuna duplicazione-oracolo rimossa | **OK** — nessuna toccata |
| G1-G15 nessun JobManager introdotto | **OK** — § 4 |
| G1-G16 R07 non anticipato | **OK** — `config.py` non è stato aperto |
| G1-G17 nessuna nuova funzionalità | **OK** |
| G1-G18 suite completa verde | **OK** — 1252 passati, 1 saltato, 0 falliti |
| G1-G19 nessun compartimento H/I/J/K iniziato | **OK** |
| G1-G20 nessun push | **OK** |

**G1 è chiuso.**

## 16. Debiti espliciti per G2

| Voce | Stato |
|---|---|
| **R07** — `Config.save()` non comunica il fallimento | intatto: `config.py` non è stato toccato |
| Ciclo di vita generale dei lavori (coda, priorità, annullamento condiviso) | le primitive locali di C e F restano; G2 decide se consolidarle |
| Cancellazione e priorità condivise fra schede | aperte |
| Rotte di export residue non migrate ad `atomic_write` | aperte (B ha chiuso quelle critiche) |
| Atomicità residua e servizio di filesystem/persistenza | aperti |
| Adapter legacy di `core.algebra` (`__getattr__`) | da rimuovere quando si potranno rompere i nomi storici |
| Ciclo `combinations ↔ permutations` | § 9: richiede un livello di orchestrazione degli export |
| Analisi oltre 1.000.000 di combinazioni | rifiutata: servirebbe un contratto di risultato diverso |
| Re-import semantico dell'export analisi | non supportato per scelta di F |
| Localizzazione dei messaggi d'errore di dominio | resta a H |
| `N03` `pypdfium2`, `N04` `gioco27.spec` | restano a K |

Nessun altro compartimento è stato iniziato: G2, H, I, J e K restano intatti.
