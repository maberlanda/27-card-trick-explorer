# J — Esperimenti, sessioni, cronologia, undo/redo e riproducibilità

**Stato: completato; tutti i gate tecnici verdi. La chiusura formale resta
subordinata all'accettazione della deviazione di processo registrata in § 19.1
(gate J-G40).** Nessuna nuova matematica: J riusa I1–I7 e il parser
autorevole. K/K0 non iniziati.

---

## 1. Stato iniziale

| voce | valore |
|---|---|
| branch | `main` |
| HEAD iniziale | `bc266b9` (chiusura della correzione I7) |
| origin/main | `54445af`, 127 commit avanti, nessun push |
| baseline | 2242 raccolti · 2240 passati · 1 saltato · 1 fallito noto (Tk 9: `test_lo_scorrimento_si_accende_quando_il_testo_cresce`) |
| versione programma | `gioco27.__version__` = 3.1.3 (riusata, non modificata) |
| non tracciati | `Articolo.pdf`, `LIBRO_MAIN.pdf` (immutati, § 18) |

Il documento `PROJECT_EVOLUTION_PLAN.md` citato dal prompt non esiste nel
repository (deviazione D1, § 19.2): J è stato costruito sul prompt stesso e
sui documenti di chiusura A…I7.

## 2. Architettura

Tre storie distinte, mai confuse:

| storia | dove | che cosa contiene |
|---|---|---|
| **A — matematica** | `services/successione.py` | la successione P1…PN, il cumulativo e le tappe (L90) |
| **B — applicativa** | `services/cronologia.py` | eventi scientifici, annulla/ripristina, eventi esterni non reversibili |
| **C — job** | `core.parallel` (esistente, invariato) | ciclo di vita degli export |

Moduli nuovi:

| modulo | righe | ruolo |
|---|---|---|
| `services/successione.py` | 201 | modello immutabile `Successione`, C_N, ritorno, replay |
| `services/esperimento.py` | 754 | schema, convenzioni, JSON canonico, digest, validazione, migrazioni, ricalcolo, confronto |
| `services/archivio.py` | 134 | salvataggio/caricamento atomici, CSV + manifest |
| `services/cronologia.py` | 176 | storia B con undo/redo |
| `services/sessione.py` | 123 | `SessioneLavoro`: stato scientifico + presentazione + cronologia |
| `cli.py` | 322 | CLI batch |
| `gui/sessione_tab.py` | 552 | `SessioneMixin` + finestra `SessioneDialog` |

Confini (verificati da `tests/test_architettura_j.py`): core → services/gui
= 0; services → gui = 0; services → tkinter = 0; `cli.py` → gui/tkinter = 0;
cicli di import nel pacchetto = 0; `class Controller` definita solo in
`core/algebra.py` (parser autorevole = 1); i moduli nuovi non contengono
parser propri né `re.compile`. Un sottoprocesso importa CLI e persistenza e
verifica che nessun modulo `tkinter`/`gioco27.gui` venga caricato.

## 3. Schema

`schema = "gioco27.esperimento"`, `schema_version = 1`. Campi di primo
livello (tutti obbligatori, campi sconosciuti rifiutati):

`schema, schema_version, convenzioni{versione, regole}, programma{nome,
versione}, algoritmi, id, creato, modificato, annotazioni{titolo, nota},
seed, voci[], presentazione, cronologia, fonti[], digest{scientifico,
documento}`.

Ogni **voce** (istantanea di risultato) ha: `id` stabile, `strumento`,
`tipo`, `revisione` dell'input, `algoritmo`, `input`, `risultato`, `digest`.
Una voce per strumento (explorer → espressione, simulatore → trucco, tavola →
procedura, riconoscimento, laboratorio → proprietà, successione).

Nessuna matrice 27×27 è persistita: si salvano gli input (espressione,
procedure con i rovesciamenti, permutazioni come liste di 27 interi) e i
risultati ricalcolabili. Le Procedure conservano i rovesciamenti.

Limiti: file 5 MB, titolo 200, nota 20 000, espressione 4096, procedure
1000, eventi 2000, fonti 16, voci 6.

## 4. Convenzioni

`convention_version = "J1"`, con undici regole nominate una per una
(posizioni 0..26; `T[origine] = destinazione`; `deck[posizione] = carta`;
applicazione `v′[T[i]] = v[i]`; composizione `(a∘b)[i] = a[b[i]]`;
rovesciamento DP3 = A; cifre `digits3 = (n2, n1, n0)`; `MSC_PERM` dal core;
H = 216, Γ = 648; numero di tavola; Procedura con `m = 4e1 + 2e2 + e3`). Al
caricamento le regole sono confrontate chiave per chiave: una differenza
produce `INCOMPATIBLE_CONVENTION` con la regola discorde nella diagnosi.

## 5. Manifest e provenienza

* `programma.versione` riusa `gioco27.__version__`.
* `algoritmi` registra l'origine di ogni calcolo (I1, I5, I6, J1-L90,
  `core.algebra.Controller`); una differenza è segnalata dal confronto
  (`DIFFERENT_ALGORITHM_METADATA`), non blocca.
* `fonti`: `{nome, ruolo ∈ libro/articolo/altro, disponibile, sha256}`.
  L'hash è calcolato **solo se il file esiste**; nessun percorso viene
  salvato; `disponibile = false` ⇔ `sha256 = null`. La GUI calcola gli hash
  di `LIBRO_MAIN.pdf`/`Articolo.pdf` solo se presenti nella radice e senza
  copiarli né spostarli. **DP12 resta aperta**: J non aggiunge, non ignora,
  non copia e non decide la distribuzione dei PDF.
* Ogni CSV esportato ha accanto `<file>.manifest.json` con schema, versioni,
  convenzioni, contenuto, digest SHA-256 del CSV, fonti e data.

## 6. Persistenza

* JSON rigoroso: `json_canonico` (chiavi ordinate, separatori compatti,
  UTF-8, `allow_nan=False`); la lettura rifiuta NaN/Infinity, chiavi
  duplicate e file sopra il limite (controllato con `stat` prima di leggere).
* Nessun `pickle`, `eval`, `exec`, `compile`, `__import__` nei moduli nuovi
  (verificato sull'AST).
* Errori tipizzati: `EsperimentoNonValido(codice, percorso, …)`,
  `CronologiaNonValida`, `SuccessioneNonValida`.
* Salvataggio atomico con `core.parallel.atomic_write` (file temporaneo
  `.gioco27-*.parziale` + `os.replace`). Test di iniezione di guasti:
  eccezione in serializzazione, in scrittura, in `replace` → il file
  precedente resta intatto e nessun temporaneo sopravvive.
* Migrazioni: meccanismo `MIGRAZIONI: versione → funzione`, vuoto; nessuna
  v0 inventata. Schema sconosciuto, versione mancante, versione futura e
  migrazione assente hanno codici distinti.

## 7. Ricalcolo

Il caricamento non si fida del file: `verifica_documento` esegue
migrazione → confronto convenzioni → validazione → **ricalcolo indipendente di
ogni voce** → confronto campo per campo → digest. Esito:

| stato | significato | codice di uscita CLI |
|---|---|---|
| `VERIFIED` | tutto ricalcolato identico | 0 |
| `MISMATCH` | un risultato o un digest differisce (diagnosi `voce.campo: registrato ≠ ricalcolato`) | 4 |
| `INCOMPATIBLE_CONVENTION` | una regola di convenzione differisce | 5 |
| `UNSUPPORTED_SCHEMA` | schema estraneo, versione futura o senza migrazione | 6 |
| `CORRUPT` | JSON non valido, campi errati, limiti superati | 3 |

Digest: `digest.scientifico` = SHA-256 del JSON canonico di schema,
versione, convenzioni, seed e voci (strumento, tipo, input, risultato);
`digest.documento` = SHA-256 dell'intero documento escluso `digest`. Le
annotazioni cambiano solo il secondo.

## 8. Sessione

`SessioneLavoro` separa lo **stato scientifico** (input per strumento, seed,
successione) dallo **stato di presentazione** minimo (`livello`, `scheda`,
`sottoscheda`). La presentazione è salvata ma non genera eventi e non entra
nel digest scientifico. Il livello deve appartenere a `LIVELLI_DIDATTICI`:
i valori legacy `principiante`/`esperto` sono **rifiutati** nei documenti di
sessione (la conversione resta solo per le impostazioni, come da I7).

Riapertura: Explorer (espressione, ricalcolata), Simulatore (carta,
bersaglio, piano fissato), Pratica (modalità valutazione/conseguenze),
Tavola (riga), Riconoscimento (permutazione, rianalizzata), Laboratorio
(proprietà e dominio, riverificate), Successione (L90).

Il caricamento è **transazionale**: il documento è verificato per intero
prima di toccare la sessione; se non è `VERIFIED` la sessione corrente resta
identica. Prima di sostituire una sessione modificata si chiede conferma.
Nessun salvataggio automatico.

## 9. Cronologia

`Cronologia` registra solo cambiamenti scientifici significativi: una
registrazione identica allo stato corrente è un no-op; cambiare titolo o nota
è un evento di annotazione (non incrementa la revisione scientifica).
Eventi esterni (`export`, `caricato`) sono registrati a parte e **non
reversibili**. La serializzazione `a_dati`/`da_dati` controlla la coerenza
con lo stato corrente; il numero di eventi è limitato (2000, i più vecchi
escono).

## 10. Undo/redo

`annulla`/`ripristina` spostano lo stato fra passato e futuro; una nuova
modifica dopo un annulla **tronca il ramo di ripristino**. Un export già
scritto non viene mai cancellato né annullato (test: il file e il suo
SHA-256 restano dopo aver annullato tutto). Lo stato "modificato" è
calcolato **per digest** rispetto all'ultimo salvataggio: annullare fino allo
stato salvato riporta la sessione a "salvata". Modello di riferimento: 600
operazioni casuali confrontate con un modello a liste.

GUI: annulla/ripristina riportano lo stato nelle viste senza creare eventi
fantasma (flag `_sessione_applicando`); Ctrl+Z/Ctrl+Y sono legati solo alla
finestra Sessione, per non interferire con l'annulla dei campi di testo.

## 11. L90

`Successione(P1…PN)` con `mazzo_iniziale` (default identità):

* `T(k)` = trasformazione della Procedura k (dal servizio I1);
* cumulativo `C_N = T(N)∘…∘T(1)` con numero di tavola quando separabile;
* disposizioni `v0…vN` con `v_k = applica(T(k), v_{k-1})`;
* ritorno compresso `R = C_N⁻¹`, realizzato come Procedura con
  `tabellone.realizza` (il ritorno di un elemento di H è ancora in H);
* replay inverso: applicando `T(N)⁻¹, …, T(1)⁻¹` si ripercorrono **tutte** le
  tappe fino a `v0`;
* l'origine (`v0`) resta distinta dal cammino: la storia non collassa nella
  sola T (J-G22), e due successioni con lo stesso C_N ma cammini diversi sono
  riconosciute come `SAME_RESULT_DIFFERENT_HISTORY`.

Oracoli nei test: composizione contro prodotto diretto, `applica(R, vN) =
v0`, replay contro le disposizioni in avanti, successioni generate con seed.
Esempio CLI: `#100, #56, #17 con ε=101` → passi `[100, 56, 11]`, cumulativo
riga `#117`, ritorno `CDS SDC CDS`.

## 12. Confronto esperimenti

`confronta(a, b)` → `Confronto(codici, dettagli)` con codici stabili:
`SAME_SCIENTIFIC_CONTENT`, `ANNOTATIONS_ONLY`, `DIFFERENT_SCHEMA`,
`DIFFERENT_CONVENTION`, `DIFFERENT_ALGORITHM_METADATA`,
`DIFFERENT_PROGRAM_VERSION`, `DIFFERENT_SOURCE_HASHES`, `DIFFERENT_SEED`,
`DIFFERENT_INPUT`, `RESULT_MISMATCH`, `SAME_RESULT_DIFFERENT_HISTORY`.

## 13. Interoperabilità

CSV (`;`, intestazioni stabili) + manifest JSON per: successione, replay,
cronologia, proprietà I6, mapping 27 posizioni. JSON: il documento
esperimento stesso. I record I6 sono esportabili e ricalcolabili
(`property --all --csv`, voce `proprieta` riverificata al caricamento). Seed
esplicito: le successioni casuali usano `random.Random(seed)`; senza seed un
generatore è rifiutato.

## 14. CLI

Estende l'entry point esistente (`python -m gioco27 <comando>`); senza
comando parte la GUI come prima e `--selftest` è invariato.

| comando | funzione |
|---|---|
| `validate FILE` | verifica con ricalcolo |
| `replay FILE` | replay L90 della successione salvata |
| `recognize T…` | riconoscimento I5 |
| `property ID --domain D` / `--all --csv` | laboratorio I6 |
| `sequence --proc #,m … \| --random N --seed S [--out] [--csv]` | successione L90 |
| `export FILE --csv OUT --what …` | CSV + manifest |
| `compare A B` | confronto strutturato |
| `selftest` | selftest integrato |

Opzioni comuni `--json` (`{command, status, exit_code, result}`) e
`--lang it|en`. Codici di uscita stabili: 0 OK, 1 SELFTEST, 2 USAGE,
3 INVALID/CORRUPT, 4 MISMATCH, 5 INCOMPATIBLE_CONVENTION,
6 UNSUPPORTED_SCHEMA, 7 WRITE_ERROR. I percorsi nei manifest sono dati,
mai eseguiti. Correzione in corso d'opera: `--proc` ripetuto ora accumula
(prima teneva solo l'ultima occorrenza; commit `6f7e4b3`, test dedicato).

## 15. UI/H2

Pulsante **🗂 Sessione** nella barra delle azioni (visibile a ogni livello)
che apre una finestra con tre schede:

* **Esperimento**: titolo, nota, «Applica annotazioni», Nuovo / Apri… /
  Salva / Salva come… / Verifica (ricalcolo) / ↶ Annulla / ↷ Ripristina,
  riquadro dell'esito con stato e diagnosi testuale;
* **Cronologia**: elenco degli eventi (gli export marcati ⤓) ed «Esporta CSV»;
* **Successione (L90)**: sigle e ε per costruire una Procedura,
  aggiungi/rimuovi/su/giù, tabella (passo, procedura, riga, cumulativo,
  disposizione), replay avanti/indietro, ritorno compresso, export.

La riga di stato usa simboli e testo (✔ salvato / ● non salvato), non solo il
colore. Nessun nuovo Canvas. H2 verificato a 1280×720, 1366×768, 1920×1080:
tutti i controlli visibili e dentro la finestra in ogni scheda; ordine di
Tab corretto nella scheda Successione; pulsante visibile ai quattro livelli.
IT/EN simmetrici (+57 chiavi: 54 sessione/successione + 3 guida; catalogo
2046 per lingua). La Guida documenta il pulsante e la finestra (sezione
«Livelli, interfaccia guidata e accessibilità»), con riferimento a cap. 10,
§ 10.1–10.2 per L90.

## 16. Sicurezza

Nessuna esecuzione di dati (AST dei moduli nuovi); nessun `pickle`/`marshal`/
`shelve`; limiti di dimensione prima della lettura; chiavi duplicate e NaN
rifiutati; campi sconosciuti rifiutati; nessun percorso salvato nelle fonti;
scrittura atomica; caricamento transazionale; test che un'espressione
ostile nel campo `testo` è trattata solo dal parser autorevole.

## 17. Test

| file | test |
|---|---|
| `tests/test_esperimenti_j.py` | 51 |
| `tests/test_cli_j.py` | 13 |
| `tests/test_sessione_j_gui.py` | 14 |
| `tests/test_architettura_j.py` | 6 |
| **totale J** | **84** |

Test esistenti aggiornati (motivati): conteggi del catalogo i18n
(1967 → 2046) in tre file; conteggi della Guida (`N_SEGMENTS` 726 → 731,
`N_GUIDE_KEYS` 455 → 458); `test_nessuna_vista_usa_ancora_il_servizio_delle_procedure`
ammette `sessione_tab.py` fra i consumatori del **modello** `ProceduraGioco`
(nessuna strategia I1 usata).

Suite finale (xvfb, file per file come nei compartimenti precedenti):
**2326 raccolti · 2324 passati · 1 saltato · 1 fallito** — l'unico
fallimento è il noto Tk 9 `test_lo_scorrimento_si_accende_quando_il_testo_cresce`.
Baseline matematica 25/25, I1–I7 verdi, pyflakes pulito, selftest 0.

## 18. Filesystem

* Lavoro solo nel repository; i test usano `tmp_path` di pytest.
* `Articolo.pdf` e `LIBRO_MAIN.pdf`: non tracciati, MD5 invariati
  (`89ad587f…`, `c6fac165…`), mai letti come dati, copiati o aggiunti.
* `.gitignore` invariato.
* Nessun push.
* Eccezione registrata in § 19.1.

## 19. Debiti e deviazioni

### 19.1 Deviazione di processo (gate J-G40)

Durante la suite finale sono stati scritti per errore due file-elenco
temporanei nella home della VM di lavoro (`$HOME/j_lista1`, `$HOME/j_lista2`,
nomi di file di test); sono stati cancellati nel comando successivo senza
essere usati. Inoltre, per recuperare il testo esatto dei gate dopo una
compattazione del contesto, è stata letta la trascrizione della sessione
stessa (non un file di lavoro, non altri progetti). Nessun effetto sul
repository. Poiché J-G40 chiede «nessuna scrittura discrezionale fuori repo»,
la chiusura è dichiarata **subordinata all'accettazione** di questa deviazione.

### 19.2 Deviazioni dal prompt

| # | deviazione | motivo |
|---|---|---|
| D1 | `PROJECT_EVOLUTION_PLAN.md` assente | non esiste nel repository |
| D2 | `atomic_write` senza `fsync` | riuso della funzione esistente; nessun cambio al core |
| D3 | nessuna conferma alla chiusura dell'app con sessione modificata | la conferma c'è su Nuovo/Apri; la chiusura resta quella di G2 |
| D4 | l'export documento (PDF/CSV esistenti) continua a usare G | J aggiunge solo gli export propri con manifest |
| D5 | un file `MISMATCH` è rifiutato, non caricato parzialmente | caricamento transazionale più sicuro |
| D6 | una voce per strumento | la sessione ha un input corrente per vista |
| D7 | la sessione è una finestra `Toplevel` dalla barra azioni | evita una nuova scheda e l'impatto su livelli/sottoschede |
| D8 | tre test esistenti aggiornati (§ 17) | conteggi e consumatori del modello |

### 19.3 Debiti

* `fsync` del file e della directory in `atomic_write` (D2).
* Conferma alla chiusura con sessione non salvata (D3).
* Prima migrazione reale quando esisterà `schema_version = 2`.
* Il test Tk 9 noto resta aperto (ereditato).
* DP12 (distribuzione dei PDF) resta aperta.

## 20. Gate

| gate | esito | evidenza |
|---|---|---|
| J-G1 schema versionato | ✔ | § 3 |
| J-G2 convention version | ✔ | § 4 |
| J-G3 JSON sicuro e validato | ✔ | § 6, § 16 |
| J-G4 salvataggio atomico | ✔ | iniezione di guasti |
| J-G5 load transazionale | ✔ | test servizio e GUI |
| J-G6 ricalcolo al load | ✔ | § 7 |
| J-G7 mismatch diagnosticato | ✔ | § 7 |
| J-G8 provenienza / source hash | ✔ | § 5 |
| J-G9 DP12 non anticipata | ✔ | § 5 |
| J-G10 sessione riapribile | ✔ | § 8 |
| J-G11 scientifico ≠ presentazione | ✔ | § 8 |
| J-G12 history deterministica | ✔ | § 9 |
| J-G13 undo | ✔ | § 10 |
| J-G14 redo | ✔ | § 10 |
| J-G15 nuovo edit tronca redo | ✔ | § 10 |
| J-G16 export non cancellato da undo | ✔ | § 10 |
| J-G17 dirty state | ✔ | per digest |
| J-G18 successione L90 | ✔ | § 11 |
| J-G19 C_N | ✔ | § 11 |
| J-G20 ritorno compresso | ✔ | § 11 |
| J-G21 replay inverso | ✔ | § 11 |
| J-G22 storia non collassata | ✔ | § 11 |
| J-G23 annotazioni | ✔ | § 3, § 15 |
| J-G24 confronto strutturato | ✔ | § 12 |
| J-G25 seed riproducibile | ✔ | § 13 |
| J-G26 digest deterministico | ✔ | § 7 |
| J-G27 CSV/JSON interoperabili | ✔ | § 13 |
| J-G28 verifiche I6 esportabili/ricalcolabili | ✔ | § 13 |
| J-G29 CLI senza Tk | ✔ | sottoprocesso |
| J-G30 exit code testati | ✔ | `test_cli_j.py` |
| J-G31 UI session/history/replay | ✔ | § 15 |
| J-G32 IT/EN | ✔ | § 15 |
| J-G33 H2 alle tre geometrie | ✔ | § 15 |
| J-G34 architettura invariata | ✔ | § 2 |
| J-G35 parser autorevole = 1 | ✔ | § 2 |
| J-G36 baseline matematica | ✔ | 25/25 |
| J-G37 I1–I7 verdi | ✔ | § 17 |
| J-G38 nessuna nuova failure | ✔ | § 17 |
| J-G39 unico failure = Tk 9 | ✔ | § 17 |
| J-G40 nessuna scrittura discrezionale fuori repo | **⚠ deviazione** | § 19.1 |
| J-G41 PDF non tracciati/immutati | ✔ | § 18 |
| J-G42 nessun push | ✔ | § 22 |
| J-G43 K/K0 non iniziati | ✔ | — |

## 21. Commit

| commit | messaggio |
|---|---|
| `6ad8652` | feat(J): versioned experiments, L90 timeline, history and atomic persistence |
| `2630fb4` | feat(J): add reproducible batch CLI |
| `408b402` | feat(J): add experiment session UI with history, undo/redo and L90 timeline |
| `e920f71` | docs(J): document the Session window in the guide; guard simulator hook |
| `55ca9d7` | test(J): admit the Session view among ProceduraGioco model consumers |
| `6f7e4b3` | fix(J): accumulate repeated --proc options in the sequence command |
| (questo) | docs(J): close experiments and reproducibility compartment |

## 22. Git status

Branch `main`; working tree pulito salvo `Articolo.pdf` e `LIBRO_MAIN.pdf`
non tracciati; 134 commit avanti rispetto a `origin/main` (`54445af`)
dopo questo commit; nessun push.
