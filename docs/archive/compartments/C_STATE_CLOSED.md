# C_STATE_CLOSED — chiusura del compartimento C (Stato e concorrenza)

Registro verificabile. Il quadro generale resta in `GIT_BASELINE_AND_RECONCILIATION.md`;
le chiusure precedenti in `A_BASELINE_CLOSED.md`, `D_DOMAIN_CLOSED.md` e `B_IO_CLOSED.md`.

## 1. Identità

| Voce | Valore |
|---|---|
| Branch | `main` — nessun push: `origin/main` resta a `54445af` |
| HEAD iniziale | `a2fa2c72851812bcf8aff2e0446bfdbdebfec4d7` — «docs(B): record closed I/O compartment» |
| HEAD finale | l'ultimo commit dell'elenco in § 12 |
| Working tree all'avvio | pulito; i commit di A, D e B presenti e non riscritti |
| Baseline di partenza | 833 raccolti, **832 passati, 1 saltato, 0 falliti** — coincide con quella attesa dopo B |
| Perimetro | soltanto il repository corrente; nessuna directory esterna letta o confrontata |

L'unico skip resta **N03** (`pypdfium2` non installata), debito di K.

Il compartimento C possiede **B02, B03, B04, R05, M03**, e di **R01** il solo aspetto di
revisione/annullamento delle richieste dell'analisi. Tutto il resto è rimasto dov'era.

## 2. B02 — gli aggregati e i grezzi vengono dalla stessa richiesta

**Riproduzione.** `_analisi_risultati` e `_analisi_righe_raw` erano due attributi indipendenti,
scritti da worker diversi in momenti diversi. Sequenza: analisi dai filtri A (aggregati di A,
grezzi di A) → import CSV B (che di grezzi non ne ha). Risultato prima della correzione:

```text
aggregati = [B]        grezzi = [{'Stage0': ...}]   ← di A
```

La tabella mostrava B, l'export «dettaglio grezzo» esportava A, e nulla lo segnalava: il file
prodotto univa due esperimenti diversi.

**Soluzione.** `RisultatoAnalisi` (dataclass congelata, in `gioco27/gui/analysis_tab.py`) è un
solo esperimento: `origine` (`"filtri" | "csv" | "pipeline"`), `aggregati`, `grezzi`, `totale`,
`diagnostica`. `_analisi_pubblica(risultato)` è **l'unico punto** in cui quei dati entrano nello
stato del tab, e li sostituisce insieme; i tre produttori (`_run_analisi`, `_analisi_load_csv`,
`_analisi_csv_pipeline`) non assegnano più nulla e pubblicano attraverso `self._ui`.

Un CSV di soli aggregati lascia `grezzi=()`: `_analisi_aggiorna_export()` disabilita le due voci
di menu che li richiedono (`_analisi_voci_grezzi = (4, 5)` — «CSV grezzo» ed «Excel grezzo»)
invece di lasciarle puntare ai dati di prima. Dopo la correzione la stessa sequenza dà:

```text
aggregati = [B]        grezzi = []        origine = 'csv'
```

**Confine.** Il modello condiviso dei risultati fra schede (`AnalysisResult`) appartiene a **G**:
`RisultatoAnalisi` è locale al tab e non ne anticipa la forma.

## 3. B03 — le risposte tardive non ripopolano lo stato

**Riproduzione.** Un'analisi lanciata e poi abbandonata — da un reset, da un import, da una
seconda analisi — continuava a girare e al termine ripopolava la tabella. Con «Reset tutto»
premuto mentre il lavoro era in corso, il worker tardivo riportava in tabella i propri risultati:
lo stato mostrato non era quello richiesto, e quale dei due vincesse dipendeva da chi finiva prima.

**Soluzione.** Ogni richiesta apre una **revisione**, un contatore monotono locale al tab:

| Primitiva | Contratto |
|---|---|
| `_analisi_nuova_revisione()` | apre una richiesta; tutte le precedenti diventano obsolete |
| `_analisi_e_corrente(revisione)` | la risposta in arrivo è ancora attesa **e** la UI è viva |
| `_analisi_pubblica(risultato)` | pubblica solo se corrente; altrimenti `False` senza toccare nulla |
| `_analisi_aggiorna_export()` | riallinea i menu allo stato appena pubblicato |

I worker interrogano la revisione al posto del vecchio `getattr(self, "_closing", False)`, e così
si fermano presto anche quando la finestra resta aperta. `_reset_analisi()` apre una revisione
nuova: il lavoro in corso finirà, ma non potrà pubblicarsi. Dopo la correzione, reset durante il
lavoro seguito dal completamento tardivo lascia `risultati = []` e **nessuna** pubblicazione.

**Confine.** È una primitiva deliberatamente minima e confinata al tab: nessun `JobManager`,
`TaskBus`, `EventBus`, `Scheduler` o registro globale delle richieste è stato introdotto. Coda,
priorità, annullamento cooperativo generalizzato e **R07** restano a **G**.

## 4. B04 — la pratica lavora su una sessione congelata

**Riproduzione.** La pratica guidata rileggeva `_card_var` e `_target_var` a ogni passo: nel
riepilogo, in «ricomincia», nella ricostruzione delle fasi del mazzo. Nulla vietava all'utente di
toccare i selettori a pratica avviata: istruzioni, mazzo e giudizio finale finivano per riferirsi a
coppie carta/bersaglio diverse, e «ricomincia» ripartiva con un'altra pratica senza dirlo.

**Soluzione.** `SessionePratica` (dataclass congelata) tiene i tre dati che definiscono una
pratica: `carta`, `bersaglio`, `piano` — quest'ultimo una `MappingProxyType`, quindi non
modificabile. `_find_sequence` è **l'unico punto** che legge i campi della finestra; da lì in poi
`_build_istruzioni`, `_build_deck_phases`, `_init_practice`, `_practice_reset` e
`_show_practice_summary` lavorano sulla sessione ricevuta.

Verifica: con la sessione (0, 13) e i campi cambiati sotto a (1, 5), «ricomincia» riparte ancora da
`carta=0 bersaglio=13`. Un test conta le occorrenze di `_card_var`/`_target_var` nel sorgente e
pretende che siano **due**, entrambe in `_find_sequence`.

Il `try/except Exception: pass` attorno alla notifica della nuova T è stato tolto: nascondeva
qualunque guasto del destinatario.

## 5. R05 — ogni lavoro finisce in uno stato conclusivo

**Riproduzione.** `_run_selftest` creava a mano un `threading.Thread` e intercettava soltanto
`AssertionError`. Qualunque altro guasto — dipendenza mancante, errore di runtime, memoria
esaurita — usciva dal thread senza toccare la UI: lo stato restava «verifica in corso…» per
sempre, l'eccezione spariva e l'utente non aveva modo di sapere che il lavoro era morto.

**Soluzione.** Il lavoro passa ora da `run_in_thread`, che registra l'errore nel log e lo mostra;
`on_error` riporta comunque lo stato a «fallita». I tre esiti sono tutti conclusivi:

| Esito | Cosa vede l'utente | Stato finale |
|---|---|---|
| Incoerenza matematica (`AssertionError`, quindi anche `VerificaFallita` di D) | rapporto di incoerenza | «fallita» |
| Qualunque altro errore | messaggio d'errore + voce nel log | «fallita» |
| Successo | rapporto completo | «completata» |

Il worker non tocca widget: pubblica solo attraverso `self._ui`. I test provano
`VerificaFallita`, `ImportError`, `RuntimeError` e `MemoryError`, con `threading.excepthook`
a garantire che nessuna eccezione si perda per strada, e verificano che lo stato non resti mai
«in corso».

## 6. M03 — la notifica di T va solo a chi rappresenta T

**Riproduzione.** `_notify_T_changed` chiamava `self._distrib_frame.set_permutation(perm_27)`
dentro un `except Exception: pass`. Quel metodo **non è mai esistito** sulla vista Distribuzione:
a ogni calcolo di T partiva un `AttributeError`, inghiottito in silenzio. La riga sembrava una
funzionalità e non lo era.

**Soluzione.** La scheda Distribuzione è *globale* — per ogni T raggiungibile conta quante
decomposizioni possiede — e non rappresenta la T selezionata: non c'è nulla da notificarle. La
chiamata è stata **rimossa** invece di inventare il metodo mancante, e il contratto è scritto
nella docstring: riceve la nuova T solo chi la rappresenta davvero.

| Vista | Riceve | Metodo |
|---|---|---|
| Cicli | sì | `set_permutation` |
| Presentazione (se aperta) | sì | `update_from_T` |
| Distribuzione | **no** | — |

`update_from_T` cattura ora soltanto `tk.TclError`, l'unico errore atteso quando la finestra viene
chiusa fra un calcolo e l'altro; il rimedio resta dimenticarla. Un test AST verifica che in
`_notify_T_changed` non resti nessun `except Exception`, nessun `except` nudo e nessun `pass`.

## 7. Test aggiornati deliberatamente

Tre test esistenti sono stati cambiati perché congelavano un comportamento sbagliato o una firma
superata. Ogni sostituzione è dichiarata nel file **e** nel messaggio di commit.

| File | Cosa cambia | Perché |
|---|---|---|
| `tests/test_gui_stato.py` | il finto `_distrib_frame` diventa una spia che registra qualunque attributo richiesto; tre asserzioni passano da «la Distribuzione ha ricevuto la T» a `app.distribution == []` | il vecchio finto esponeva un `set_permutation` che la vista reale non ha mai avuto: il test passava mentre l'applicazione inghiottiva un errore a ogni calcolo (M03) |
| `tests/test_i18n.py` | costruisce `SessionePratica.calcola(7, 19)` e chiama `_build_istruzioni(sessione)`; la classe finta `Value` sparisce | le istruzioni appartengono alla sessione, non ai widget: la firma cambia con B04 |
| `tests/test_rischi_concorrenza.py` | `AppHarness` prende dal mixin le quattro primitive nuove | l'harness già prende dal mixin i metodi di App; senza questo non rappresenta più il tab reale |

Nessun test è stato indebolito o rimosso per far passare il codice.

## 8. Non-regressione

Riproduzioni dei dodici bug rieseguite **dopo** le modifiche di C, nello stesso ambiente:

```text
B01  CORRETTO   400/400 sequenze nel file riletto, tre fogli
B02  CORRETTO   dopo A e import B: aggregati [B], grezzi [], origine 'csv'
B03  CORRETTO   reset durante il lavoro -> il completamento tardivo non pubblica
B04  CORRETTO   campi cambiati a (1,5): «ricomincia» usa ancora carta=0 bersaglio=13
B05  PRESENTE   [0,0,99] ancora accettata come T                       (F)
B06  PRESENTE   4 stadi: count=6, iter=1                               (F)
B07  PRESENTE   'MSC o' accettata dal visualizzatore, non da Explorer  (E)
B08  CORRETTO   cache vuota per un bersaglio in G -> miss
B09  CORRETTO   con -O il guasto iniettato resta rilevato (VerificaFallita)  (D)
B10  CORRETTO   registrazione font fallita -> ('Helvetica', 'Helvetica-Bold')
B11  CORRETTO   ExportTooLarge su 5.159.780.352, nessun file creato
B12  CORRETTO   generatore guasto -> _Generato(ok=False), nessun contenuto
M03  CORRETTO   notifiche: Cicli=1, Distribuzione=[]
```

**B05, B06 e B07 sono presenti e invariati**: appartengono a F ed E e non sono stati toccati.
La matematica di D non è stata sfiorata: `tests/test_baseline_matematica.py` → **25 passati**.

## 9. Test

Ambiente di riferimento invariato (Linux, **Python 3.12.3**, tkinter 8.6 con Xvfb, NumPy 2.5.3,
ReportLab 5.0.1, openpyxl 3.1.5, pypdf 6.18.1, pikepdf 10.13.0, pytest 9.1.1, pyflakes 3.4.0).
Comando: `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m pytest -p no:cacheprovider -ra -q`.

| Voce | Prima di C | Dopo C |
|---|---:|---:|
| Raccolti | 833 | **869** |
| Passati | 832 | **868** |
| Falliti | 0 | **0** |
| Saltati | 1 | **1** (N03) |

* Nuovo file `tests/test_stato_concorrenza_c.py` → **36 passati** (B02 6, B03 7, B04 13, R05 6, M03 4, parametrizzazioni comprese).
* Stato e concorrenza nel complesso (`test_stato_concorrenza_c.py`, `test_rischi_concorrenza.py`,
  `test_gui_stato.py`) → **78 passati**.
* Dominio di D (`test_dominio_indici`, `test_dominio_permutazioni`, `test_dominio_selftest`,
  `test_decomposition_integrita`) → **163 passati**; baseline matematica → **25 passati**.
* I/O di B (`test_io_integrita_b`, `test_hardening`, `test_output_integrita`,
  `test_export_integrita`) → **149 passati**.
* Statici di A (N01): `tests/test_static.py` → **2 passati**; `pyflakes` su `gioco27`, `tests`,
  `conftest.py`, `gioco27.py` → **nessun avviso**, a ogni passo.
* I test non dipendono dalla velocità della macchina: i lavori vengono catturati e fatti avanzare
  esplicitamente, e dove serve un thread vero lo si attende con `join` prima di controllare.

**Ogni commit è stato verificato singolarmente con la suite completa**, ricostruendo l'albero
esatto di quel commit nell'ambiente di riferimento (confronto per hash dei sette file):

| Commit | Suite |
|---|---|
| B02 | 838 passati, 1 saltato, 0 falliti |
| B03 | 845 passati, 1 saltato, 0 falliti |
| B04 | 858 passati, 1 saltato, 0 falliti |
| R05 | 864 passati, 1 saltato, 0 falliti |
| M03 | 868 passati, 1 saltato, 0 falliti |

Nessun commit rosso, `pyflakes` pulito su tutti e cinque.

## 10. File modificati

| File | Tema |
|---|---|
| `gioco27/gui/analysis_tab.py` | B02 (`RisultatoAnalisi`, pubblicazione unica, menu grezzi) + B03 (revisioni) |
| `gioco27/gui/simulator_tab.py` | B04 (`SessionePratica`, letture concentrate in `_find_sequence`) |
| `gioco27/gui/app.py` | R05 (`_run_selftest` via `run_in_thread`) + M03 (`_notify_T_changed`) |
| `tests/test_stato_concorrenza_c.py` | **nuovo** — 36 test su B02, B03, B04, R05, M03 |
| `tests/test_gui_stato.py` | contratto M03 (spia al posto del finto `set_permutation`) |
| `tests/test_i18n.py` | firma B04 di `_build_istruzioni` |
| `tests/test_rischi_concorrenza.py` | harness allineato alle primitive del mixin |

Diff sintetico `a2fa2c7..HEAD`: **7 file, 905 inserimenti, 79 cancellazioni**.
Nessun file rinominato, nessun file rimosso, nessuna chiave i18n aggiunta o rimossa.

## 11. Cosa non è stato fatto, di proposito

* Nessun gestore generale dei lavori: niente `JobManager`, `TaskBus`, `EventBus`, `Scheduler`,
  registro globale delle richieste. Le primitive introdotte vivono nel tab Analisi.
* **R07** non è stato affrontato: resta a G.
* **B05, B06** (F) e **B07** (E) non sono stati toccati.
* Nessun worker tocca widget Tk: pubblicano tutti attraverso `self._ui`.
* Nessuna duplicazione conservata come oracolo è stata rimossa.
* Nessun compartimento successivo iniziato: E, F, G, H, I, J, K restano intatti.

## 12. Commit locali

| # | Hash | Messaggio |
|---|---|---|
| 1 | `9dba823` | `fix(C): bind analysis raw data to current result (B02)` |
| 2 | `e8446b0` | `fix(C): discard stale analysis completions (B03)` |
| 3 | `1118655` | `fix(C): snapshot practice session inputs (B04)` |
| 4 | `8fc8808` | `fix(C): make selftest worker failures terminal (R05)` |
| 5 | `16933c1` | `fix(C): remove invalid distribution notification (M03)` |
| 6 | — | `docs(C): record closed state compartment` (questo documento) |

Nessun push, nessun `reset`/`rebase` distruttivo, nessun commit precedente riscritto.
`origin/main` resta a `54445af`.

## 13. `git status` finale

```text
On branch main
Your branch is ahead of 'origin/main' by 23 commits.

nothing to commit, working tree clean
```

Nessun `__pycache__`, nessun `.pytest_cache`, nessun artefatto di esecuzione lasciato nel
repository (la suite gira con `PYTHONDONTWRITEBYTECODE=1 -B -p no:cacheprovider`).

## 14. Gate di uscita

*I testi sono la riformulazione dei sedici gate dell'incarico; l'esito è verificato come indicato.*

| Gate | Esito |
|---|---|
| C-G1 B02 corretto: aggregati e grezzi dalla stessa richiesta | **OK** — § 2 |
| C-G2 B03 corretto: nessuna risposta tardiva ripopola lo stato | **OK** — § 3 |
| C-G3 B04 corretto: la pratica lavora su input congelati | **OK** — § 4 |
| C-G4 R05 corretto: ogni lavoro finisce in uno stato conclusivo | **OK** — § 5 |
| C-G5 M03 corretto: la notifica va solo a chi rappresenta T | **OK** — § 6 |
| C-G6 nessun gestore generale dei lavori introdotto | **OK** — § 11 |
| C-G7 R07 non affrontato, rinviato a G | **OK** — § 11 |
| C-G8 nessun worker tocca widget Tk | **OK** — pubblicazione solo via `self._ui` |
| C-G9 snapshot immutabili al posto delle letture dal vivo | **OK** — `RisultatoAnalisi`, `SessionePratica` |
| C-G10 nessun `except` che inghiotte errori nei punti toccati | **OK** — § 6, verificato via AST |
| C-G11 test aggiornati dichiarati esplicitamente | **OK** — § 7 |
| C-G12 B05, B06, B07 presenti e invariati | **OK** — § 8 |
| C-G13 matematica di D e I/O di B invariati | **OK** — § 8, § 9 |
| C-G14 suite completa verde, ogni commit verde | **OK** — 868 passati, 1 saltato; § 9 |
| C-G15 nessun altro compartimento iniziato | **OK** — § 11 |
| C-G16 nessun push | **OK** — `origin/main` fermo a `54445af` |

**Il compartimento C è chiuso.**

## 15. Debiti rimasti

| Voce | Stato | Proprietario |
|---|---|---|
| **B02, B03, B04** | **chiusi in C** | — |
| **B05, B06** | presenti, non toccati | **F** — semantica dell'analisi e dei filtri |
| **B07** | presente, non toccato | **E** — parser unico Explorer/Shuffle |
| **R01** | aspetto revisione/annullamento coperto in C per l'analisi; il resto aperto | F |
| **R05, M03** | **chiusi in C** | — |
| **R06** | presente | K |
| **R07** | presente | **G** |
| **M01, M04, M06** | presenti | H |
| **M05 residuo** | conservazione dei temporanei HTML di `protocol_dialog` | H |
| **N03** `pypdfium2` non dichiarata | aperto: unico skip della suite | K |
| **N04** `gioco27.spec` non versionato | aperto | K |
| Modello condiviso dei risultati fra schede (`AnalysisResult`) | aperto: `RisultatoAnalisi` è locale al tab | G |
| Ciclo di vita generale dei lavori (coda, priorità, annullamento) | aperto | G |
| Ramo morto in `core/kronecker.py` dopo il `return` incondizionato | aperto | F |
| Rotte di export non ancora migrate ad `atomic_write` | aperto | G |
| Duplicazioni preservate come oracoli | **da non rimuovere** senza sostituto indipendente | G, E |

Nessun compartimento successivo è stato iniziato: E, F, G, H, I, J e K restano intatti.
