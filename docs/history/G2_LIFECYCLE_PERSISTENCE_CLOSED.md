# G2 — Lifecycle dei lavori, persistenza ed export

Chiusura del compartimento G.

## 1. Identità

| | |
|---|---|
| Branch | `main` |
| HEAD iniziale | `d9faae2` — *docs(G1): record service boundary milestone* |
| HEAD finale | il commit di questo documento — *docs(G2): close the application services compartment*, settimo e ultimo di G2 |
| `origin/main` | `54445af`, invariato — **nessun push** |
| Commit locali di G2 | 7 |
| Versione | 3.1.3 (invariata) |

## 2. Nota di perimetro

Tutto il lavoro è avvenuto **dentro il repository corrente**. In particolare:

* **nessun worktree esterno** creato o usato;
* **nessun checkout esterno** consultato;
* **nessuna vecchia copia** del progetto letta o confrontata — la cartella `gioco27_v3.1.2`,
  pur visibile allo stesso livello, non è mai stata aperta;
* **nessuno script di lavoro fuori dal repository**: i controlli occasionali sono stati
  eseguiti come comandi Python inline, e tutto ciò che meritava di restare è diventato un
  test dentro `tests/`;
* **nessun file di appoggio** creato fuori dal repository;
* i percorsi assoluti citati nei documenti tecnici interni non sono stati seguiti.

Gli unici accessi al filesystem esterni al repository sono quelli che il programma compie
normalmente durante i test, attraverso le directory temporanee gestite da pytest (`tmp_path`).

L'ambiente di riferimento per l'esecuzione dei test resta quello dei compartimenti precedenti
(Linux, Python 3.12.3, tkinter 8.6 su Xvfb, NumPy 2.5.3, ReportLab 5.0.1, openpyxl 3.1.5,
pypdf 6.18.1, pikepdf 10.13.0, pytest 9.1.1, pyflakes 3.4.0); l'albero dei sorgenti eseguito è
verificato identico al repository file per file tramite sha256, e ogni commit è stato
confrontato per hash con la versione effettivamente provata.

## 3. Baseline all'ingresso

```text
pytest tests/test_baseline_matematica.py     25 passati
suite completa                               1253 raccolti
                                             1252 passati
                                                1 saltato   (N03, pypdfium2 assente)
                                                0 falliti
```

`git status` all'ingresso: *working tree clean*, `main` avanti di 42 commit su `origin/main`.

## 4. Inventario dei lavori asincroni

Prima di decidere qualunque consolidamento, il censimento. Cinque famiglie di lavoro reali:

| Lavoro | Nasce | Identità | Cancellazione | Termina | Errore | Pubblica | Obsolescenza |
|---|---|---|---|---|---|---|---|
| **Analisi** (`gui/analysis_tab`) | `run_in_thread` | contatore monotono | — | `_analisi_pubblica` o `None` | `on_error` di `run_in_thread` | `_ui(...)` sul thread Tk | revisione ≠ corrente |
| **Export massivi** (`gui/app`) | `run_in_thread` | nessuna (uno alla volta) | `threading.Event` → `annullato()` → `ExportAnnullato` | `_fine_export` in `finally` | `on_error`; l'annullamento **non** è un errore | `_ui(...)` | — |
| **Selftest** (`gui/app`) | `run_in_thread` | nessuna | — | `mostra()` sempre | `AssertionError` → fallita; altro → `on_error` → fallita | `_ui(...)` | — |
| **Decomposizioni** (`gui/decomposition`) | `threading.Thread` + coda + `after` | contatore monotono | — | `("DONE"…)` / `("ERR"…)` in coda | `("ERR", msg)` → stato | polling sul thread Tk | `search_id` ≠ corrente |
| **Distribuzione** (`gui/distribution_tab`) | `threading.Thread` + coda + `after` | nessuna (`_computing`) | — | `("DONE"…)` / `("ERR"…)` | `("ERR", msg)` → etichetta | polling sul thread Tk | — |

A queste si aggiunge il parallelismo interno degli export e delle decomposizioni
(`ProcessPoolExecutor` via `core/parallel.run_export` e `core/kronecker`), che non è un lavoro
applicativo a sé: è il modo in cui uno dei cinque esegue.

### Le cinque parole non sono sinonimi

```text
in corso     il lavoro è partito e non ha ancora un esito
completato   ha prodotto un risultato
fallito      ha sollevato; qualcuno deve dirlo all'utente
annullato    gli è stato CHIESTO di fermarsi — arriva AL lavoro
obsoleto     una richiesta più nuova lo ha superato — riguarda il suo RISULTATO
```

La distinzione che conta, e che il compartimento C aveva introdotto, è l'ultima coppia. Un
lavoro annullato riceve una richiesta e si interrompe; un lavoro obsoleto **non sa nulla** e
può benissimo arrivare in fondo — semplicemente il suo risultato viene scartato. Fonderle in
un unico booleano avrebbe perso esattamente questo.

### Che cosa era davvero condiviso

Solo due nozioni, e in modo asimmetrico:

* **obsolescenza** — scritta **due volte a mano** come contatore monotono
  (`_analisi_revisione` nella scheda Analisi, `_search_id` nella finestra delle
  decomposizioni). Questa è duplicazione vera.
* **annullamento** — aveva già **un solo** contratto, e sta nel core: la callable
  `annullato() -> bool` di `core/parallel`, con `mai_annullato` come sentinella ed
  `ExportAnnullato` come esito, accettata da ogni rotta di export.

## 5. Consolidamento del lifecycle

### Cosa è stato introdotto

`gioco27/services/lavoro.py` — 91 righe, un solo tipo:

```python
class Revisioni:
    def nuova(self) -> int          # apre una richiesta; le precedenti sono obsolete
    def e_corrente(self, r) -> bool # r è ancora quella valida?
    @property
    def corrente(self) -> int
```

Il contatore è protetto da un `threading.Lock`: `nuova()` è «leggi, incrementa, scrivi», che
il GIL **non** rende atomico, e `e_corrente` viene interrogata da un worker. Il valore
restituito è un intero, così chi lo riceve non ha bisogno di conoscere la classe e può
portarselo in una chiusura, in una coda o in un `after`.

Il modulo importa solo `threading`: non conosce Tk, la GUI, il filesystem né gli altri
servizi. Un test lo verifica (`_archi()["gioco27.services.lavoro"] == set()`).

Migrati i due soli utenti: `gui/analysis_tab` (che conserva i nomi `_analisi_nuova_revisione`
e `_analisi_e_corrente`, cioè il seam di C) e `gui/decomposition`.

### Cosa NON è stato introdotto, e perché

| Non fatto | Motivo |
|---|---|
| `JobManager` / orchestratore generale | le cinque famiglie eseguono in modi incompatibili (thread + `ui_call`, thread + coda + `after`, pool di processi). Un gestore comune avrebbe dovuto o perdere la semantica, o essere una facciata vuota |
| `JobState` / enum degli stati | **nessun flusso memorizza o interroga uno stato del lavoro**: sarebbe stato un tipo senza lettori. Gli stati esistono come comportamento, e come tali sono sotto test |
| Coda e **priorità** | il debito di G1 le citava per prudenza. L'inventario non ha trovato alcuna semantica di priorità fra lavori: non ce n'è una da consolidare, e inventarla sarebbe stato progettare un futuro |
| Un secondo tipo «annullamento» | ne esiste già uno solo, nel core, ed è riusato invariato |
| Astrazione unica thread/processi | thread e `multiprocessing` restano quello che sono; il lifecycle condivide l'identità della richiesta, non il modo di eseguire |

Un test rende esplicite queste decisioni (`test_g2_non_ha_inventato_uno_scheduler`): fallisce
se compare una classe `JobManager`, `Scheduler`, `TaskQueue`, `JobState` o simili, o se la
primitiva inizia a nominare code, priorità o executor. Reintrodurle sarà una scelta, non una
svista.

### Revisione ≠ cancellazione, verificato

`test_la_revisione_non_e_un_annullamento` controlla che `Revisioni` non abbia alcun modo di
chiedere a un lavoro di fermarsi (`annulla`, `cancel`, `stop`, `set`, `is_set`) e che il
contratto di annullamento viva altrove. Sul comportamento, tre test su flussi reali:

```text
analisi obsoleta   il servizio viene chiamato, si ferma, restituisce None,
                   il lavoro non pubblica e NON è un errore
analisi fallita    l'eccezione esce, on_error la vede, non pubblica
export annullato   ExportAnnullato → nessun messaggio di guasto, stato terminale,
                   destinazione intatta
export fallito     l'errore esce, ma _export_busy torna comunque False
```

## 6. R07 — il salvataggio della configurazione

### Riproduzione

`Config.save()` apriva un `try` attorno a tutto e chiudeva con
`except Exception: _log.exception(...)`. Dal punto di vista del chiamante, disco pieno,
cartella non creabile e salvataggio riuscito erano **la stessa cosa**. Quattro modi di
fallire, tutti riprodotti con guasti iniettati — mai con i permessi POSIX, che su Windows non
hanno lo stesso effetto:

```text
cartella non creabile          un file al posto della cartella → mkdir fallisce
errore durante la scrittura    json.dump solleva a metà
errore nella pubblicazione     os.replace solleva
destinazione non scrivibile    atomic_write solleva all'apertura
```

In tutti e quattro `save()` tornava `None`. Due chiamanti ne approfittavano senza saperlo:

* **preferenza di lingua** — mostrava «la nuova lingua sarà applicata al prossimo avvio» e
  restituiva `True`;
* **dialogo impostazioni** — chiudeva il dialogo, che è il modo in cui una UI dice «fatto».

### Contratto finale

Un'eccezione applicativa esplicita, coerente con il resto del programma (`FiltroNonValido`,
`SchemaNonRiconosciuto`, `ExportTooLarge`, `PermutazioneNonValida`) e non un `False` che
nessuno controllerebbe:

```python
class ConfigNonSalvata(OSError):
    percorso      # dove
    causa         # perché (e __cause__ resta agganciato)
    operazione    # che cosa
```

Deriva da `OSError` perché ciò che fallisce è sempre un'operazione di I/O: chi già intercetta
`OSError` attorno a un salvataggio continua a funzionare. Porta le tre informazioni che
servono a riferirlo, senza costruire una gerarchia di eccezioni per ogni modo di fallire.

### Atomicità

**Esisteva già** e non è stata toccata: `Config.save()` usa `parallel.atomic_write`, la stessa
primitiva di ogni export — temporaneo accanto alla destinazione e `os.replace` a scrittura
conclusa. Nessuna seconda implementazione è stata scritta; un test verifica che
`core/config.py` non importi `tempfile` per conto proprio e che un guasto a metà lasci il
`config.json` precedente byte per byte.

### Comportamento della UI

Quattro punti di chiamata, due esiti ammessi ciascuno:

| Punto | Prima | Dopo |
|---|---|---|
| preferenza di lingua | «riavvia per applicare» + `True` | errore mostrato, `False`, nessun annuncio |
| dialogo impostazioni | il dialogo si chiude | errore mostrato, il dialogo **resta aperto** |
| migrazione all'avvio | silenzio | silenzio **deliberato** — non c'è ancora una UI, e nulla viene dichiarato riuscito |
| chiusura finestra | silenzio | silenzio **deliberato** — si perde la geometria, non si impedisce di chiudere |

Due chiavi i18n nuove, simmetriche IT/EN (`config.save_failed.title`, `config.save_failed`):
il minimo perché il fallimento sia visibile. La formulazione elegante e la sua collocazione
nella UI restano al compartimento H.

Un test architetturale (`test_r07_ogni_salvataggio_nella_gui_e_gestito`) censisce i quattro
punti e fallisce se ne compare un quinto non protetto; un altro verifica strutturalmente che
`do_save` chiuda il dialogo **solo dopo** un tentativo riuscito.

## 7. Export — inventario delle rotte che pubblicano file

| Rotta | Formato | Prima | Dopo |
|---|---|---|---|
| `core/config.Config.save` | JSON | atomica | atomica |
| `core/cache.save_decompositions` | JSON | atomica | atomica |
| `core/permutations.write_csv` → `core/export_combinazioni` | CSV | atomica | atomica |
| `core/permutations.write_csv_parallel` → `core/export_combinazioni` | CSV | atomica | atomica |
| `core/combinations.generate_pdf` / `generate_pdf_ex` / `_pdf_parallel` | PDF | atomica | atomica |
| `core/detail_pdf.generate_detail_pdf` (+ parallela) | PDF | atomica | atomica |
| `core/pdfmerge.unisci` | PDF | atomica | atomica |
| `core/export_analisi.scrivi_output` / `scrivi_excel` | CSV / XLSX | atomica | atomica |
| `gui/analysis_tab` — TXT, CSV, XLSX | 3 rotte | atomiche | atomiche |
| `gui/cayley_dialog` — HTML | HTML | atomica | atomica |
| `gui/conjugacy_dialog` — HTML | HTML | atomica | atomica |
| `gui/decomposition` — HTML | HTML | atomica | atomica |
| `gui/export_group_dialog._export_all` | TeX / SVG | atomica (B12) | atomica |
| **`gui/export_dialog._export_all`** | 5 file TeX/SVG/TXT | **non atomica** | **migrata** |
| **`gui/conjugacy_dialog._export_txt`** | TXT | **non atomica** | **migrata** |
| **`gui/decomposition._export_txt`** | TXT | **non atomica** | **migrata** |
| **`gui/decomposition._export_csv`** | CSV | **non atomica** | **migrata** |
| **`gui/tavola_tab._esporta_csv`** | CSV | **non atomica** | **migrata** |
| **`core/group_theory.export_cayley_csv`** | CSV | **non atomica** | **migrata** |
| `core/pdfmerge._dedup_*` | PDF | temporaneo proprio + `_sostituisci` | invariata |
| `gui/protocol_dialog._open_browser` | HTML temporaneo | non applicabile (M05 → H) | invariata |

Sei rotte migrate. Erano `open(path, "w")` sul file finale — in `export_dialog` **senza
nemmeno un `with`**, affidando la chiusura al refcount. Un guasto a metà sostituiva il file
buono con uno troncato: un `.tex` che LaTeX rifiuta, un CSV che Excel apre male, una tavola di
Cayley 648×648 dimezzata.

Restano due `open(..., "w")` nel package, ed entrambi scrivono **temporanei, non
destinazioni**: il file HTML che `protocol_dialog` apre nel browser (il cui residuo, M05,
appartiene a H) e il temporaneo interno di `pdfmerge`, che pubblica già con una sostituzione
atomica. Un test li elenca per nome e fallisce se ne compare un terzo.

### Compatibilità e formati

Nessun formato è cambiato: stesso encoding, stesso delimitatore, stesso `newline`, stesse
intestazioni, stesso ordine delle righe, stessi nomi di file proposti. `atomic_write` inoltra
i propri `kwargs` a `open`, quindi l'output è byte-identico.

### Prove

Per ogni rotta migrata, tre scenari: successo, guasto **durante la generazione**, guasto
**durante la pubblicazione** (`os.replace`). In tutti i casi la destinazione precedente resta
identica, nessun temporaneo sopravvive, e il fallimento viene riportato — le rotte della GUI
lo mostrano, quella del core lo solleva. L'export multiplo è provato anche a metà elenco: i
file già pubblicati restano com'erano e il terzo non compare troncato.

## 8. Il ciclo di importazione

### Grafo prima

```text
core.combinations ──────► core.permutations     compute_stage, kron_label, …
core.permutations ──────► core.combinations     l'enumeratore, dentro write_csv
```

Un solo ciclo elementare in tutto il package, dichiarato da G1 come debito di G2.

### Causa

Non è matematica. `core.permutations` costruisce **una riga** (`CSV_HEADER`, `make_csv_row`) e
non ha bisogno di sapere quante righe esistano né da dove vengano. A saperlo è
l'orchestrazione dell'export: preflight, enumerazione, parallelismo, pubblicazione atomica.
Era ospitata nel modulo sbagliato.

### Soluzione

`write_csv` e `write_csv_parallel`, con i due worker dei blocchi, passano in
`gioco27/core/export_combinazioni.py` — accanto a `core/export_analisi.py`, che G1 aveva
estratto per la stessa ragione. La collocazione è nel core e non nei servizi perché queste
funzioni non orchestrano un caso d'uso applicativo: sono l'export del dominio, non conoscono
la GUI, e i servizi non le usano.

**Nessuna matematica si è spostata.** `compute_stage`, `compute_R`, `compute_T_perm`,
`compute_T_full`, `compose3`, `build_P27`, `build_J27`, `perm_to_mat3`, `mat_to_perm27`,
`make_csv_row`, MSC, GEN3 e le matrici restano dove erano; un test lo verifica per nome,
modulo per modulo.

I nomi storici restano importabili da `core.permutations` con la stessa facciata differita
(PEP 562) introdotta da G1 per `core.algebra`. La risoluzione avviene **per nome**
(`import_module`) e non con un `from … import`, perché un import scritto lì — anche dentro una
funzione — sarebbe di nuovo la freccia appena tolta.

L'orchestrazione usa i due moduli per nome (`permutations.make_csv_row`,
`combinations.iter_combinations_ex`) invece che «da»: sono i punti in cui i test di B, B6 e
hardening infilano una sentinella o un guasto, e legare il nome all'import li congelerebbe.

### Grafo dopo

```text
core.combinations ─┐
                   ├──► core.export_combinazioni ──► core.parallel
core.permutations ─┘

core.permutations ──► {core.constants, core.log}      e nient'altro
```

```text
cicli statici applicativi:  1 → 0
```

### Come è misurato

Il contatore dei cicli non è più un'ispezione a occhio di due moduli: enumera i **cicli
elementari** dell'intero package, conta **anche gli import scritti dentro le funzioni** (un
import differito resta una dipendenza) e risolve correttamente sia gli `__init__.py` sia la
forma `from . import a, b` — che la misura di G1 perdeva, facendo sparire archi veri.

Le due sole facciate differite sono elencate una per una in un test dedicato, che fallisce se
ne compare una terza; per ciascuna è verificato quali nomi risolve. Un terzo `__getattr__`
esiste in `gui/i18n.py`, ma non è una traslocazione: è un proxy che riesporta `gioco27.i18n`,
già importato in cima al file, quindi non nasconde alcun arco.

La prova che conta è a runtime, non nell'AST: importare `core.permutations` in un processo
pulito **non** tira dentro `core.combinations` né `core.export_combinazioni`.

## 9. Persistenza e filesystem

Una sola primitiva di pubblicazione atomica in tutto il programma: `core/parallel.atomic_write`.
G2 non ne ha scritta una seconda e non ha creato alcun `FilesystemRepository`,
`StorageEngine` o `PersistenceFramework`: la duplicazione reale era «chi non la usa», non
«quante ne esistono», e si risolveva usandola.

Gli errori di persistenza conservano operazione, destinazione e causa (`ConfigNonSalvata`),
senza trasformare ogni `OSError` in una gerarchia: le rotte di export continuano a lasciar
passare l'`OSError` così com'è, che è già abbastanza per H.

Il cleanup resta quello di `atomic_write`: su qualunque `BaseException` il temporaneo viene
rimosso e la destinazione non viene toccata. I temporanei sono distinti per destino e nessuno
riceve un cleanup indiscriminato:

```text
temporaneo di costruzione     atomic_write, rimosso sempre
temporaneo interno            pdfmerge, sostituisce il file appena pubblicato
temporaneo da aprire          protocol_dialog → browser: sopravvive di proposito (M05 → H)
```

Cache (formato v2, TTL, limite 200 MB, completezza B08/N06) e soglie dell'analisi
(`LIMITE_GREZZI = 100_000`, `LIMITE_ANALISI = 1_000_000`) sono invariate.

## 10. Architettura finale del compartimento G

```text
                    core  —  matematica e linguaggio
       constants · permutations · combinations · algebra · espressione
       dominio · analisi · kronecker · group_theory · gioco_reale
                                   │
                    core  —  I/O ed export del dominio
       parallel (atomic_write, run_export, annullato) · cache · config
       export_combinazioni · export_analisi · detail_pdf · pdfgrid · pdfmerge
                                   │
                                   ▼
                    services  —  casi d'uso applicativi
              modelli (RisultatoAnalisi, Provenienza)
              analisi  (ServizioAnalisi, sincrono)
              lavoro   (Revisioni)
                                   │
                                   ▼
                    gui  —  presentation
              App · schede · dialoghi · thread e marshalling Tk
```

Regole verificate da test, non solo dichiarate:

```text
services → gui      = 0
core → services     = 0
core → gui          = 0
services → tkinter  = 0        (e nessun thread/pool creato nei servizi)
cicli statici       = 0
parser autorevoli   = 1        (Lexer, Parser, Evaluator: solo in core/algebra.py)
worker che toccano widget Tk = 0
```

L'ultima riga è verificata sui sette worker reali del programma (analisi, export, selftest,
decomposizioni, distribuzione, Cayley, coniugio): nessuno modifica un widget al proprio
livello, e ogni callable annidata che ne tocca uno è consegnata al thread Tk con
`_ui`/`ui_call`/`after` o messa in una coda che il thread Tk svuota. Il guardiano è stato
provato per mutazione — introdurre una `configure()` diretta in `_compute_worker` lo fa
fallire.

## 11. API legacy

| API storica | Nuovo proprietario | Adapter |
|---|---|---|
| `core.permutations.write_csv` | `core.export_combinazioni` | facciata differita `__getattr__` (G2) |
| `core.permutations.write_csv_parallel` | `core.export_combinazioni` | facciata differita `__getattr__` (G2) |
| `core.algebra.analizza_righe` | `core.analisi` | facciata differita `__getattr__` (G1), conservata |
| `core.algebra.analizza_csv` | `core.analisi` | facciata differita `__getattr__` (G1), conservata |
| `core.algebra.scrivi_output` | `core.export_analisi` | facciata differita `__getattr__` (G1), conservata |
| `core.algebra.scrivi_excel` | `core.export_analisi` | facciata differita `__getattr__` (G1), conservata |
| `core.algebra.EXCEL_MAX_CELL_CHARS` | `core.export_analisi` | facciata differita `__getattr__` (G1), conservata |

**Nessun adapter eliminato.** Quello di G1 è rimasto: i suoi chiamanti storici (test compresi)
continuano a funzionare, e toglierlo alla fine di G sarebbe stato un cambiamento di superficie
pubblica senza un motivo. È classificato come debito legacy post-G.

I due nomi privati `_csv_rows_chunk` e `_csv_chunk_worker` **non** sono nella facciata: sono
interni, e l'unico test che li usava è stato aggiornato con il motivo scritto nel file.

## 12. Metriche prima / dopo

| Metrica | Prima (`d9faae2`) | Dopo | Come è misurata |
|---|---:|---:|---|
| Cicli statici applicativi | 1 | **0** | test (`test_nessun_ciclo_statico_fra_i_moduli_applicativi`) |
| `services → gui` | 0 | 0 | test |
| `core → services` | 0 | 0 | test |
| Punti di chiamata di `atomic_write` | 20 | **26** | `git grep` sui due revisioni |
| `open(…, "w"/"wb"/"a")` nel package | 12 | **2** | `git grep` sui due revisioni |
| … di cui su un file di destinazione | 10 | **0** | censimento nel test |
| Rotte di pubblicazione non atomiche | 6 | **0** | § 7 |
| Primitive lifecycle condivise | 0 | **1** (`Revisioni`) | § 5 |
| Implementazioni di «obsoleto» | 2 | **1** | § 5 |
| Implementazioni di «annullato» | 1 | **1** | invariata, nel core |
| Punti che dichiarano successo dopo un fallimento di persistenza | 2 | **0** | test |
| Chiavi i18n | 1292 | 1294 | test |
| `core/permutations.py` | 549 righe | 450 | `wc -l` |
| Parser autorevoli del linguaggio | 1 | 1 | test |

Tutte le misure provengono da test dentro il repository, da comandi inline o da `git` sul
repository stesso. Nessuno script di lavoro esterno è stato creato.

## 13. Sweep dei difetti

Ogni difetto è verificato dai test che lo riproducono, dentro il repository:

```text
B01  CORRETTO     5 test      B02  CORRETTO     6 test
B03  CORRETTO     7 test      B04  CORRETTO    13 test
B05  CORRETTO    32 test      B06  CORRETTO    57 test
B07  CORRETTO   127 test      B08  CORRETTO     7 test
B09  CORRETTO     7 test      B10  CORRETTO    32 test
B11  CORRETTO    17 test      B12  CORRETTO    12 test

R01  CORRETTO    13 test      R04  CORRETTO    74 test
R05  CORRETTO     6 test      R07  CORRETTO    10 test
```

`R05` merita una riga a parte, perché il consolidamento del lifecycle avrebbe potuto
riaprirlo: il selftest raggiunge ancora uno stato terminale per tutti e cinque gli esiti
(`VerificaFallita`, `ImportError`, `RuntimeError`, `MemoryError`, successo). Nessun thread
muore lasciando la UI con «verifica in corso». Un test di G2 lo verifica esito per esito, sul
metodo reale di `App`.

`R07` passa da PRESENTE a CORRETTO in questo compartimento.

## 14. Test

| Suite | Esito |
|---|---|
| Baseline matematica (D) | 25 passati |
| Dominio (permutazioni, indici, selftest) | 98 passati |
| I/O e integrità (B) | 28 passati |
| Stato e concorrenza (C) | 36 passati |
| Linguaggio e simulazione (E) | 228 passati |
| Analisi, filtri e budget (F) | 112 passati |
| Servizi e modelli (G1) | 44 passati |
| **Lifecycle e persistenza (G2)** | **45 passati** |
| Statici (pyflakes, nomi non definiti) | 2 passati |
| **Suite completa** | **1298 raccolti, 1297 passati, 1 saltato (N03), 0 falliti** |

`pyflakes` pulito su `gioco27/` e `tests/`. Nessun `xfail` residuo nel compartimento.

Ogni commit è stato verificato con la suite completa sull'albero effettivamente committato
(confrontato per hash):

| Commit | Suite |
|---|---|
| `test(G2)` caratterizzazione | 1269 passati, 1 saltato, 5 xfail attesi |
| `fix(G2)` fallimento di config esplicito | 1277 passati, 1 saltato |
| `refactor(G2)` identità condivisa delle richieste | 1281 passati, 1 saltato |
| `refactor(G2)` orchestrazione export e ciclo sciolto | 1287 passati, 1 saltato |
| `fix(G2)` rotte residue atomiche | 1292 passati, 1 saltato |
| `test(G2)` confini di lifecycle e dipendenze | 1297 passati, 1 saltato |

### Determinismo

Nessun test usa `sleep`. I lavori vengono catturati e fatti avanzare esplicitamente; dove
serve concorrenza vera (la sicurezza di `Revisioni` fra thread) i thread partono insieme con
una `threading.Barrier` e si aspettano con `join`. I guasti di I/O sono iniettati: mai
`chmod`, mai semantica POSIX di `rename`, mai segnali Unix — le nuove primitive e i loro test
valgono anche su Windows.

## 15. File modificati

| File | Tema |
|---|---|
| `gioco27/services/lavoro.py` | **nuovo** — `Revisioni`, la primitiva del lifecycle |
| `gioco27/core/export_combinazioni.py` | **nuovo** — orchestrazione dell'export CSV (spostata) |
| `gioco27/core/config.py` | `ConfigNonSalvata`; `save()` non inghiotte più l'errore |
| `gioco27/core/permutations.py` | resta la matematica; facciata differita (549 → 450 righe) |
| `gioco27/core/group_theory.py` | CSV di Cayley pubblicato atomicamente |
| `gioco27/gui/app.py` | fallimento di config visibile; import dell'export CSV |
| `gioco27/gui/analysis_tab.py` | usa `Revisioni` |
| `gioco27/gui/decomposition.py` | usa `Revisioni`; TXT e CSV atomici |
| `gioco27/gui/conjugacy_dialog.py` | TXT atomico |
| `gioco27/gui/tavola_tab.py` | CSV atomico |
| `gioco27/gui/export_dialog.py` | cinque file pubblicati atomicamente |
| `gioco27/services/__init__.py` | espone `Revisioni` |
| `gioco27/i18n.py` | +2 chiavi simmetriche IT/EN |
| `tests/test_lifecycle_persistenza_g2.py` | **nuovo** — 45 test |
| `tests/test_servizi_g1.py` | il debito del ciclo è pagato; armatura su `Revisioni` |
| `tests/test_stato_concorrenza_c.py` | armatura su `Revisioni` |
| `tests/test_analisi_filtri_f.py` | armatura su `Revisioni` |
| `tests/test_decomposition_integrita.py` | armatura su `Revisioni` |
| `tests/test_rischi_concorrenza.py` | R2 attende l'eccezione di salvataggio |
| `tests/test_io_integrita_b.py` | mappa delle rotte con preflight |
| `tests/test_parallel_limiti.py` | worker dei blocchi nel nuovo modulo |
| `tests/test_i18n.py`, `test_i18n_anomalie_ui.py`, `test_i18n_audit_finale.py` | conteggio chiavi 1294 |

## 16. Commit locali

```text
61abb13  test(G2): characterize job lifecycle and configuration failure
3fa4be6  fix(G2): make configuration persistence failure explicit
0d95b7a  refactor(G2): share the request identity across jobs
55d7a5d  refactor(G2): extract export orchestration and break the last import cycle
6987281  fix(G2): publish the remaining export routes atomically
816e4b5  test(G2): enforce lifecycle and dependency boundaries
  ⟵      docs(G2): close the application services compartment  (questo documento)
```

Nessun `push`, nessun `reset` o `rebase` distruttivo, nessun commit precedente riscritto.

## 17. Git status finale

```text
On branch main
Your branch is ahead of 'origin/main' by 49 commits.
  (use "git push" to publish your local commits)

nothing to commit, working tree clean
```

Nessun `__pycache__`, nessun `.pytest_cache`, nessun file di lavoro residuo.

## 18. Gate di uscita

| Gate | Esito |
|---|---|
| G2-G1 R07 corretto: il fallimento di `Config.save` è osservabile | **OK** — § 6 |
| G2-G2 un failure di salvataggio non è presentato come successo | **OK** — § 6, test sui 4 punti |
| G2-G3 configurazione pubblicata atomicamente | **OK** — già garantita, preservata e sotto test |
| G2-G4 lifecycle inventariato e reso coerente | **OK** — § 4, § 5 |
| G2-G5 cancellato, obsoleto e fallito restano distinti | **OK** — § 4, § 5 |
| G2-G6 nessun worker tocca widget Tk | **OK** — § 10, sette worker verificati |
| G2-G7 nessun framework di scheduling/priorità inventato | **OK** — § 5, test esplicito |
| G2-G8 servizi sincroni e GUI-free | **OK** — § 10 |
| G2-G9 rotte residue rese atomiche | **OK** — § 7, sei rotte |
| G2-G10 un failure durante l'export non corrompe la destinazione | **OK** — § 7 |
| G2-G11 ciclo `combinations ↔ permutations` eliminato | **OK** — § 8 |
| G2-G12 nessun nuovo ciclo equivalente | **OK** — § 8, cicli totali = 0 |
| G2-G13 `services → gui` = 0 | **OK** — § 10 |
| G2-G14 `core → services` = 0 | **OK** — § 10 |
| G2-G15 parser autorevole resta uno | **OK** — § 10 |
| G2-G16 B01–B12 ancora corretti | **OK** — § 13 |
| G2-G17 R01/R04/R05 ancora corretti | **OK** — § 13 |
| G2-G18 R07 corretto | **OK** — § 6, § 13 |
| G2-G19 matematica invariata | **OK** — baseline 25/25; nessuna funzione matematica spostata |
| G2-G20 formati invariati | **OK** — § 7 |
| G2-G21 UX invariata salvo il feedback minimo sul fallimento | **OK** — § 6 |
| G2-G22 nessun H/I/J/K iniziato | **OK** — § 20 |
| G2-G23 suite completa verde | **OK** — § 14 |
| G2-G24 nessun push | **OK** — `origin/main` fermo a `54445af` |
| G2-G25 nessuna risorsa di lavoro esterna | **OK** — § 2 |

## 19. COMPARTIMENTO G CHIUSO

Tutti i gate di G1 e di G2 sono soddisfatti. Il risultato architetturale complessivo:

```text
core matematico / linguaggio
        ↓
services applicativi
        ↓
presentation

filesystem e persistenza con failure espliciti
lifecycle coerente: una primitiva per l'obsolescenza, una per l'annullamento
pubblicazione dei file atomica su ogni rotta di destinazione
nessun ciclo statico applicativo
```

Che cosa significa in concreto, al di là del diagramma:

* un servizio applicativo si prova come una funzione qualunque, senza aprire Tk;
* un risultato dell'analisi ha un solo proprietario e non ammette stati impossibili;
* un salvataggio fallito non può più essere scambiato per uno riuscito;
* un export interrotto non lascia mai un artefatto parziale al posto del file buono;
* «annullato» e «obsoleto» sono due cose diverse, e continueranno a esserlo;
* il grafo delle dipendenze si legge in una direzione sola.

Questo documento contiene la certificazione completa di G: non viene creato un ulteriore
`G_CLOSED.md`.

## 20. Debiti che restano

**Per H — presentation, testi e accessibilità**

* `M01`, `M04`, `M06` e il residuo di `M05` (il temporaneo HTML di `protocol_dialog` che
  sopravvive di proposito e non viene ripulito);
* la formulazione e la collocazione del messaggio di fallimento del salvataggio: G2 lo rende
  osservabile con due chiavi minime, non lo progetta;
* il dialogo delle impostazioni che resta aperto dopo un errore è la scelta più onesta
  disponibile senza toccare la UX; una revisione del flusso appartiene a H.

**Per I — strumenti matematici**

* nulla proveniente da G.

**Per J — sessioni, esperimenti e cronologia**

* il lifecycle dei lavori **non** è la cronologia utente: nessun lavoro viene conservato dopo
  la sua conclusione, e non esiste undo/redo. Se J vorrà una cronologia, dovrà costruirla,
  non derivarla da `Revisioni`.

**Per K — dipendenze, packaging e release**

* `N03` (`pypdfium2` assente: un test saltato) e `N04` (spec di PyInstaller); CI, lock delle
  dipendenze, release.

**Legacy, senza compartimento assegnato**

* le facciate differite di `core.algebra` (G1) e `core.permutations` (G2): entrambe
  conservate, entrambe sotto test. Andranno tolte solo quando tutti i chiamanti saranno
  migrati e la superficie pubblica potrà cambiare senza rischio.
* `distribution_tab` e `decomposition` continuano a pubblicare con `coda + after` mentre
  analisi, export e selftest usano `run_in_thread + ui_call`. Sono due stili di marshalling
  corretti e testati: unificarli non risolve un difetto e non era compito di G2.
