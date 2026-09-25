# GIT_BASELINE_AND_RECONCILIATION

**Compartimenti A0 (riconciliazione audit ↔ repository Git) e A1 (baseline tecnica e di regressione).**
Documento di sola analisi: nessun bug è stato corretto, nessun refactoring è stato avviato,
nessun commit e nessun push sono stati eseguiti.

| Voce | Valore |
|---|---|
| Data di esecuzione | 22 settembre 2026 |
| Repository analizzato | `C:\Users\Maurizio\Codex_Progetti\27-card-trick-explorer` |
| Commit di riferimento | `54445af9c5e499523986a227c0bb7dba32ded763` |
| Fonte di verità | il repository Git (l'audit è una checklist, non una descrizione byte-per-byte) |
| Documento di partenza | `PROJECT_EVOLUTION_PLAN.md` (presente solo nella copia Astra) |
| Esito sintetico | B01–B12 **tutti presenti**; baseline matematica **integra**; suite **rossa** in un ambiente con pyflakes installato (criticità nuova N01) |

---

## 1. Identità del repository

| Voce | Valore osservato |
|---|---|
| Path | `C:\Users\Maurizio\Codex_Progetti\27-card-trick-explorer` |
| Branch | `main`, allineato a `origin/main` (né avanti né indietro) |
| HEAD | `54445af9c5e499523986a227c0bb7dba32ded763` |
| Messaggio HEAD | `Prepara release 3.1.3` |
| Autore/data HEAD | `maberlanda <mberlanda@hotmail.com>` — mer 16 set 2026 04:22:48 +0200 |
| Numero di commit | 33 |
| Tag presenti | `v3.1.2`, `v3.1.3` — `git describe --tags` su HEAD restituisce `v3.1.3` |
| Remote | `origin  https://github.com/maberlanda/27-card-trick-explorer.git` (fetch e push) |
| Working tree iniziale | **pulito**: `git status --porcelain=v1 -b` restituiva solo `## main...origin/main` |
| Stash | nessuno (`git stash list` vuoto) |
| Versione dichiarata | `3.1.3` in `pyproject.toml:7` **e** in `gioco27/__init__.py` (`__version__`) — coerenti, nessuna terza sorgente di versione |
| Dimensione | 8,0 MB totali, di cui 3,4 MB in `.git` |

**Stato preesistente vs modifiche di questo incarico.** Il working tree era pulito *prima*
dell'incarico e nessun file versionato è stato toccato. L'unica variazione prodotta è la
**creazione di questo documento** nella radice del repository, che risulta quindi *untracked*
(§ 16). Nessun `reset`, `rebase`, `checkout` distruttivo, `commit`, `tag` o `push` è stato eseguito.

**Ambiente di analisi.** Il repository vive su Windows. Le verifiche dinamiche sono state
eseguite in due ambienti Linux distinti, documentati in § 6: la VM locale della sessione
(Python 3.10.12, **senza tkinter**) e un container cloud (Python 3.12.3, **con tkinter 8.6 e Xvfb**),
su una copia di sola lettura dei file tracciati. Il repository non è stato eseguito né modificato
in loco.

---

## 2. Inventario

### 2.1 Struttura e dimensioni

| Gruppo | File | Righe |
|---|---:|---:|
| `gioco27/core/` | 17 moduli `.py` | 6 544 |
| `gioco27/gui/` | 26 moduli `.py` | 12 240 |
| `tests/` | 26 file | 8 326 |
| entry point e config di radice | `gioco27.py`, `conftest.py`, `controlla_requisiti.py` | 144 |
| **Totale sorgente Python** | **72 file** | **27 254** |
| Asset | `gioco27/assets/DejaVuSans.ttf`, `DejaVuSans-Bold.ttf` | 1,4 MB |
| Documentazione | `README.md`, `NOTE_VERSIONE_3.md`, `NOTE_VERSIONE_3.1.1.md`, `NOTE_VERSIONE_3.1.3.md`, `LICENSE` | — |
| Configurazione | `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `.gitignore`, `.gitattributes` | — |
| Launcher | `avvia.bat`, `gioco27.py`, `gioco27/__main__.py`, `[project.gui-scripts] gioco27` | — |

Moduli più grandi: `gui/i18n.py` (2 659), `core/algebra.py` (1 735), `gui/app.py` (1 188),
`core/detail_pdf.py` (923), `gui/explorer_tab.py` (759), `gui/shuffle.py` (725),
`gui/simulator_tab.py` (691), `core/combinations.py` (676).

### 2.2 File tracciati e artefatti runtime

* `git ls-files` → **87 file tracciati**.
* File presenti su disco escludendo `.git/`, `__pycache__/`, `.pytest_cache/` → **88**.
* L'unico file su disco non tracciato è **`gioco27.spec`** (la configurazione PyInstaller),
  escluso da `.gitignore:33` (`*.spec`). Vedi § 9 e la criticità **N04**.
* Artefatti runtime presenti ma ignorati: `.pytest_cache/`, 74 file `.pyc` in cinque directory
  `__pycache__/`. Vedi la criticità **N05**.

**Distinzione sorgente/artefatto.** L'assenza di `~/.gioco27/cache/*.json` nel repository **non**
implica l'assenza del sottosistema cache: `gioco27/core/cache.py` esiste, è completo
(`load_decompositions`, `save_decompositions`, versione formato 2, scadenza `_MAX_AGE_DAYS`) ed è
coperto da `tests/test_decomposition_integrita.py`. Lo stesso vale per `config.py` rispetto a
`~/.gioco27/config.json` e per `log.py` rispetto a `~/.gioco27/gioco27.log`.

### 2.3 Impronta di contenuto riproducibile

Con l'algoritmo dichiarato nell'audit (§ 1.3 del piano: percorsi ordinati da
`sorted(Path.cwd().rglob('*'))`, soli file, esclusione di `__pycache__` e `.pytest_cache`; per ogni
file: percorso relativo POSIX in UTF-8 + byte nullo + digest SHA-256 binario del contenuto):

| Insieme | File | SHA-256 aggregata |
|---|---:|---|
| Repository Git (escluso `.git/`) | 88 | `ebd4b8a0a289aa8c1c3f5861073aad835936c13857077ea38b677865d4279b61` |
| Copia Astra, escluso `PROJECT_EVOLUTION_PLAN.md` | 87 | `68b80ba56a03fa50b716bbb8924aaf8d95666585846407b4f14bb847668d4082` |
| Sottoinsieme codice + configurazione, **repository** | 82 | `f4b3f49e93fecf99b3b970f35e5c09e1fc41505dcfdb6e9526006165ef421264` |
| Sottoinsieme codice + configurazione, **copia Astra** | 82 | `f4b3f49e93fecf99b3b970f35e5c09e1fc41505dcfdb6e9526006165ef421264` |

Il secondo valore **riproduce esattamente l'impronta dichiarata dall'audit**. Questo è un risultato
importante e va registrato come fatto: la copia analizzata da Astra è oggi bit-per-bit quella
dell'audit, e il codice del repository coincide con essa (quarta riga = terza riga).

*Nota metodologica.* L'ordinamento va eseguito con la semantica dei `Path` **Windows**
(confronto sulle componenti del percorso, ripiegate a minuscolo). Con l'ordinamento POSIX
la stessa cartella produce `10155107…`: l'impronta dipende dalla piattaforma di calcolo, non solo
dal contenuto. Chi la ricalcolerà in futuro deve usare la chiave
`tuple(x.lower() for x in rel.split('/'))`.

---

## 3. Differenze rispetto alla copia Astra

Confronto diretto (`diff -rq`, escluse `.git`, `__pycache__`, `.pytest_cache`) fra
`27-card-trick-explorer` e `gioco27_v3.1.2`. Entrambe le cartelle erano disponibili: **il confronto
è un fatto misurato, non un'inferenza.**

| Tipo | File | Dettaglio |
|---|---|---|
| Solo nel repository | `LICENSE` | GPL v3.0 completa, 35 823 byte, assente dalla copia |
| Solo nella copia | `PROJECT_EVOLUTION_PLAN.md` | 89 741 byte; è il documento di audit, mai versionato |
| Contenuto diverso | `README.md` | il repository contiene due sezioni in più: «Articolo associato» (link a `27-card-tensor-structure`) e «Licenza» |
| Contenuto diverso | `NOTE_VERSIONE_3.1.3.md` | unica differenza: tabella qualità, **repository 673 passati / 5 saltati**, copia **674 passati / 4 saltati** |
| **Tutti gli altri 85 file** | `gioco27/**`, `tests/**`, config, launcher, asset | **byte-per-byte identici** |

**Conseguenza per A0.** Poiché l'intero package e l'intera suite sono identici, le conclusioni
dell'audit sul codice sono trasferibili al repository *senza adattamenti*, e i numeri di riga citati
dal piano sono validi anche qui (verificati uno per uno: § 10.1 elenca le tre sole eccezioni).
Non esistono correzioni «già applicate» nel repository e assenti dalla copia, né viceversa.

Nessuna differenza strutturale: stessa gerarchia di directory, stesso numero di moduli, stessa
versione dichiarata (3.1.3 in entrambe).

---

## 4. Matrice B01–B12

Tutte le verifiche sono state eseguite sul codice del repository, con lo script
`verifica_bug.py` (Appendice A). Le righe citate sono quelle reali del repository.

| ID | Stato | File e simbolo reali | Verifica eseguita e risultato |
|---|---|---|---|
| **B01** | **PRESENTE** | `gui/analysis_tab.py:596` `_export_analisi_raw_excel`, cella a `:653` | Chiamato il metodo reale con `filedialog` sostituito da un path temporaneo e 400 sequenze distinte. Atteso in cella: 46 799 caratteri; riletto con openpyxl: **32 767**; l'ultima sequenza **non** è più presente; lo stato dichiarato dall'app resta `✓ Excel grezzi: grezzi.xlsx`. |
| **B02** | **PRESENTE** | `gui/analysis_tab.py:243` `_analisi_load_csv` | Harness con grezzo sentinella `SENTINELLA-A`; eseguito il job reale su un CSV identità. `_analisi_risultati` viene sostituito, `_analisi_righe_raw` **conserva i dati della sessione precedente**: l'export grezzo unirebbe due esperimenti. |
| **B03** | **PRESENTE** | `gui/analysis_tab.py:191` `_run_analisi`, reset a `:174` | Catturato il job, eseguito `_reset_analisi` (stato `(0, 0)`), poi eseguito il job tardivo: lo stato torna `(1, 1)`. Il worker controlla solo `_closing`, non una revisione. |
| **B04** | **PRESENTE** | `gui/simulator_tab.py:519` `SimulatorFrame._practice_reset`, riepilogo a `:635` | `_practice_reset` rilegge `int(self._card_var.get())` e `_show_practice_summary` rilegge `int(self._target_var.get())`. Con il piano 0→13 e carta cambiata a 1, la carta 1 finisce in posizione **12** (simulazione indipendente). |
| **B05** | **PRESENTE** | `core/algebra.py:1572` `analizza_righe`, `:1607` `analizza_csv` | `analizza_righe([{"T_permutazione": "[0,0,99]"}])` → 1 risultato con `perm_str = [0,0,99]`. Un CSV `foo;bar` → 0 risultati, nessun errore di schema. |
| **B06** | **PRESENTE** | `core/combinations.py:37` `valida_filtri`, `:402` `iter_combinations_ex`, `:449` `count_combinations_ex` | Quattro stadi (tre fissi, quarto con `p0` libero): `valida_filtri` **accetta**, `count = 6`, `iter = 1`. La GUI costruisce sempre tre stadi: il difetto è al confine API. |
| **B07** | **PRESENTE** | `gui/shuffle.py:259` `ShuffleViewerFrame._validate_and_parse` vs `core/algebra.py:1165` `Parser` (via `Controller.process`) | `MSC o` e `MSC)` → accettate dal visualizzatore (1 passo), **rifiutate** dall'Explorer (`Errore di parsing: token inatteso`). `I` → **rifiutata** dal visualizzatore (`ValueError`), accettata dall'Explorer. Due linguaggi incompatibili confermati in entrambe le direzioni. |
| **B08** | **PRESENTE** | `core/kronecker.py:99` `validate_decompositions`, `core/cache.py:66` `load_decompositions` | `validate_decompositions(identità, [])` → `[]`: un elenco vuoto è accettato come valido, mentre per un bersaglio in G le terne attese sono 46 656 (cardinalità verificata in § 7, M11). |
| **B09** | **PRESENTE** | `core/gioco_reale.py:325` `selftest` | Sorgente compilato con `optimize=1` in memoria e `T_da_partita` sostituita con `[0]*27`: il rapporto resta **`TUTTO OK`**. Con `optimize=0` la stessa iniezione solleva `AssertionError: riga 0`. Il launcher non usa `-O`: difetto condizionale, non osservato nella baseline ordinaria. |
| **B10** | **PRESENTE** | `core/detail_pdf.py:306` `_ensure_fonts` | `pdfmetrics.registerFont` sostituita con una funzione che solleva `ValueError`, `_FONTS_READY = None`: `_ensure_fonts()` restituisce comunque **`('DV', 'DVB')`**, cioè font non registrati. |
| **B11** | **PRESENTE** | `core/permutations.py:413` `write_csv` | Filtri tutti liberi (**5 159 780 352** combinazioni): `write_csv` entra nell'enumeratore senza alcun `ExportTooLarge` (sentinella che interrompe subito; nessun file creato). `write_csv_parallel` (`:499`) e le rotte GUI chiamano invece `check_export_size`. |
| **B12** | **PRESENTE** | `gui/export_group_dialog.py:159` `_PreviewExportDialog._content`, salvataggio a `:181` | Un generatore che solleva `ValueError` produce e mette in cache la stringa `% Errore nella generazione: generatore guasto`, che `_export_all` scriverebbe come file `.svg` conteggiandolo fra i riusciti. |

### 4.1 Copertura di test esistente e regressioni da aggiungere

| ID | Test esistente che tocca l'area | Copre il difetto? | Regressione da introdurre nel compartimento competente |
|---|---|---|---|
| B01 | `tests/test_output_integrita.py::test_b13_excel_400_formule_disponibili_dopo_riapertura` (copre `core.algebra.scrivi_excel`) | **No** — esporta un altro modulo | Riapertura dell'Excel grezzo con ricostruzione di *tutte* le sequenze; confini 32 766/32 767/32 768 |
| B02 | `tests/test_rischi_concorrenza.py::test_r1_analisi_csv_completa_o_interrotta` | No | A→import B→export: nessun residuo A presentato come B |
| B03 | `test_r1_analisi_si_ferma_fra_due_elementi` (copre solo la chiusura) | No | Reset fra avvio e completamento; completamenti fuori ordine A/B |
| B04 | `tests/test_core.py` (pratica, percorso felice) | No | Modifica dei campi prima/durante/dopo la pratica; valori vuoti e non numerici; estensione alle 729 coppie |
| B05 | `tests/test_core.py` (analisi di righe valide) | No | Duplicati, negativi, 26/28 elementi, 99, header mancante, BOM, formula incoerente |
| B06 | `tests/test_numerazione_base0.py` (chiavi legacy), `test_hardening.py::test_iter_combinations_ordine_come_i_cicli_annidati` | No | 0/2/4 stadi, domini errati, `count == len(list(iter))` per tutti i filtri piccoli ammessi |
| B07 | `tests/test_gui_stato.py` (T verso le viste) | No | Corpus condiviso valido/non valido; per ogni espressione ammessa, inversa del mazzo finale = T del controller |
| B08 | `tests/test_decomposition_integrita.py::test_b11_cache_json_v2_valida_accettata[results0]` | **Copre il caso ma congela il bug**: asserisce che `results = []` sia accettato e restituito | Distinzione «contesto parziale» / «cache completa»; il test citato andrà rinegoziato esplicitamente (§ 10.3) |
| B09 | `tests/test_tabellone_inverso.py`, `test_i18n_audit_finale.py` (selftest in condizioni normali) | No | Stesso esito negativo con processo normale e con `-O`, errore iniettato in ciascun ramo |
| B10 | `tests/test_hardening.py:537-578` (font e deduplica) | Parziale: non copre il fallimento di `registerFont` | Font mancante, corrotto, registrazione parziale, processo appena avviato |
| B11 | `test_hardening.py::test_export_csv_rifiuta_subito_i_filtri_vuoti` (rotta GUI/parallela) | No per `write_csv` diretto | Stessa policy su **ogni** entry point pubblico CSV/PDF |
| B12 | `tests/test_export_integrita.py` (export massivi) | No | Generatore fallito, batch misto, nessun falso `.svg`/`.tex` valido |

**Nessun bug è stato corretto.** Per ciascuno restano registrati: l'input che lo riproduce
(Appendice A), il comportamento attuale (tabella sopra) e il comportamento atteso (piano § 5).

---

## 5. Matrice R01–R07 e M01–M06

| ID | Stato | Evidenza nel repository |
|---|---|---|
| **R01** | **PRESENTE** | `gui/analysis_tab.py`: soglia di conferma `50_000` presente, accumulo integrale via `righe.append(...)`, **nessun** `check_export_size` nel modulo. Nessun OOM provocato: resta un rischio, come nell'audit. |
| **R02** | **PRESENTE (sfumato)** | `core/algebra.py:1735` salva con `wb.save(output_path)` direttamente sulla destinazione. `atomic_write` esiste in `core/parallel.py` **ed è importato anche da `algebra.py`**: la scrittura atomica è usata per alcune rotte, non per l'Excel di `scrivi_excel`. La disuguaglianza di garanzia fra export massivi e dialoghi minori è confermata. |
| **R03** | **PRESENTE** | `core/pdfmerge.py:73` `tmp = f"{path}.dedup"`; nessun uso di `mkstemp`/`NamedTemporaryFile` nel modulo. |
| **R04** | **PRESENTE — aggravato** | Il simbolo è `core/analysis.py:63 orbit_of` (non `permutations.py:65`, § 10.1). `orbit_of([1,1], 0)` in sottoprocesso: **nessuna terminazione entro 10 s** (ciclo infinito), non semplice orbita che «non torna a 0». Nessuna validazione agli ingressi pubblici. |
| **R05** | **PRESENTE** | `gui/app.py:960`, worker di `_run_selftest`: intercetta `AssertionError` e **non** `Exception`. Un `ImportError`/`RuntimeError` lascia la UI senza esito conclusivo. |
| **R06** | **PRESENTE** | `requirements.txt` e `pyproject.toml` dichiarano **solo minimi** (nessun `==`), nessun lock file, nessuna CI (§ 9), build non riproducibile dal repository (**N04**). |
| **R07** | **PRESENTE** | `core/config.py` `save()` non restituisce esito (nessun `return True/False`), l'eccezione viene solo registrata a log; i validatori agiscono al load, non al set. |
| **M01** | **PRESENTE** | `gui/filter_frame.py:232`: `result[name.lower()] = opts[0]   # fallback` — nessuna casella selezionata diventa la prima opzione, non «insieme vuoto». |
| **M02** | **PRESENTE, da riformulare** | Numerazione base 1 residua nelle firme e nelle docstring: `core/permutations.py:112 stage_label(i, p1, p2, p3, j1, j2, j3)`, `core/detail.py:6` «stadio 1, dopo stadio 2», `core/detail_pdf.py:200,216,232` «stadio 3 = i, stadio 2 = j, stadio 1 = k», mentre le **chiavi dei filtri sono base 0** (`p0,p1,p2`). La seconda parte dell'accusa («descrizione della rotazione inesatta in `algebra`») **non è confermata**: le formule documentate a `core/algebra.py:525-531` (`MSC ∘ (P1⊗P2⊗P3) = (P3⊗P1⊗P2) ∘ MSC`, rotazione sinistra di 2 = destra di 1) sono state verificate **esaustivamente corrette** (§ 7, M6 e M12c). Qui vale la regola «non correggere una convenzione verificata perché una docstring usa parole diverse». |
| **M03** | **PRESENTE** | `gui/app.py:924 _notify_T_changed`: chiamata a `set_permutation` su una vista che non la espone, eccezione silenziata. |
| **M04** | **PRESENTE** | `App.minsize(1200, 750)` fisso; wrap e dimensioni costanti; link su `Label`. |
| **M05** | **PRESENTE, parziale** | `gui/protocol_dialog.py` usa **già** `Path.as_uri()` e non compone `file://` a mano; restano però i temporanei HTML senza politica di conservazione. La composizione manuale `f"file://{path}"` sopravvive altrove: `gui/analysis_tab.py:561`, `gui/cayley_dialog.py:342`, `gui/conjugacy_dialog.py:367`, `gui/decomposition.py:579`. |
| **M06** | **PRESENTE** | `core/detail_pdf.py:740`: `Tt(f"... (+{len(trans) - max_shown} altre)", ...)` non localizzato (l'audit cita 739: scostamento di una riga). |

### 5.1 Criticità architetturali dell'audit, verificate

| Criticità | Esito | Evidenza |
|---|---|---|
| Import `core → gui.i18n` | **CONFERMATA, 4 occorrenze** | `core/algebra.py`, `core/combinations.py`, `core/detail_pdf.py`, `core/gioco_reale.py` importano `..gui.i18n` |
| Ciclo `combinations ↔ permutations` | **CONFERMATO, unico ciclo del package** | `combinations.py` importa `permutations` in testa; `permutations.write_csv:421` importa `combinations` localmente «per evitare un import circolare» |
| Operazioni Tk dentro moduli matematici | **CONFERMATA (nuova evidenza, N02)** | `core/permutations.py:25 configure_matrix_tags(txt_widget, …)` e `:32 insert_colored(txt_widget, …)` manipolano un `tk.Text` |
| Due classi Tooltip | **CONFERMATA** | `gui/tooltip.py` e `gui/common.py` |
| BFS di gruppo dentro la GUI | **CONFERMATA** | `gui/cayley_dialog.py` usa `deque(...)`; la teoria dei gruppi vive in `core/group_theory.py` |
| Tabelle GEN3/MSC duplicate | **CONFERMATA** | `core/kronecker.py::_build_kron_table` e `core/analysis.py::_build_kron_table_27` costruiscono due tabelle equivalenti; `analysis.py` ha anche `_build_cayley216`, `group_theory.py` ha `_build_cayley` |
| Inverse/cicli duplicati | **CONFERMATA, con avvertenza** | Inversa in `core/algebra.py`, `core/detail.py`, `core/group_theory.py`; decomposizione in cicli in `core/analysis.py` (unica). **Queste duplicazioni funzionano oggi da oracoli indipendenti** nei test: non vanno rimosse prima che esista un oracolo sostitutivo davvero indipendente. |
| Due parser | **CONFERMATA** | `gui/shuffle.py::_validate_and_parse` (regex) e `core/algebra.py::Lexer/Parser` (grammatica tipizzata) — vedi B07 |
| Ramo morto in `find_all_kron_decompositions_parallel` | **CONFERMATA** | `core/kronecker.py:245` è un `return`; le righe 247-289 (costruzione chunk, worker, dedup) sono **irraggiungibili** |
| `except Exception:` | **41 occorrenze** | Più densi: `gui/app.py` (8), `core/cache.py` (6), `core/pdfmerge.py` (4), `core/detail_pdf.py` (3), `core/parallel.py` (3). Non tutti sono difetti: molti proteggono chiusure Tk. Quelli che **sopprimono** l'esito sono già tracciati come B10, B12, M03. |

---

## 6. Baseline dei test

### 6.1 Ambiente A — container Linux con tkinter (baseline di riferimento)

| Voce | Valore |
|---|---|
| Interprete | `/usr/bin/python3.12` — **Python 3.12.3** (GCC 13.3.0) |
| tkinter | presente, `TkVersion 8.6`; `DISPLAY=:99` fornito da **Xvfb** 21.1.12 |
| Dipendenze | NumPy 2.5.3, ReportLab 5.0.1, openpyxl 3.1.5, pypdf 6.18.1, pikepdf 10.13.0.post1, pytest 9.1.1, pyflakes 3.4.0, **pypdfium2 assente** |
| Comando | `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m pytest -p no:cacheprovider -ra -q` |
| Raccolti | **678** |
| Passati | **676** |
| Falliti | **1** |
| Saltati | **1** |
| xfail/xpass | 0 |
| Durata | **78,93 s** (seconda esecuzione: 75,23 s — risultato stabile) |
| Motivo dell'unico skip | `tests/test_layout_dettaglio.py:73` — `could not import 'pypdfium2'` |
| Unico fallimento | `tests/test_static.py::test_no_pyflakes_warnings` |

Il fallimento è riproducibile e **non** dipende dall'ambiente:

```text
gioco27/gui/export_dialog.py:244:26: f-string is missing placeholders
gioco27/gui/onboarding_tab.py:12:1: '.glossary.ONBOARD_INTRO' imported but unused
```

`test_no_undefined_names`, che usa lo stesso comando pyflakes filtrando i soli «undefined name»,
**passa**. Vedi la criticità **N01**.

### 6.2 Ambiente B — VM locale della sessione (non utilizzabile come baseline)

Python 3.10.12, NumPy 2.2.6, ReportLab 5.0.1, openpyxl 3.1.5, pypdf 6.18.0, pikepdf 10.13.0,
pytest 9.1.1, pyflakes 3.4.0, **tkinter assente**, nessun display, 2 core.

Con il comando completo la raccolta si interrompe: `5 errors during collection`
(`ModuleNotFoundError: No module named 'tkinter'` per `test_chiusura_regressioni.py`,
`test_decomposition_integrita.py`, `test_documentazione_d1d3.py`, `test_gui_stato.py`,
`test_rischi_concorrenza.py`). Ignorando quei cinque moduli: **506 passati, 26 falliti, 8 saltati
in 42,49 s**; 25 dei 26 fallimenti sono lo stesso `ModuleNotFoundError` in test che importano la GUI
per via indiretta, il ventiseiesimo è `test_no_pyflakes_warnings`. `tkinter` non è installabile in
quella VM (nessun privilegio di root). **Questo ambiente non produce una baseline valida** ed è
riportato solo per documentare perché non è stato usato.

### 6.3 Riconciliazione con i numeri storici

| Fonte | Passati | Saltati | Falliti | Totale |
|---|---:|---:|---:|---:|
| Audit Astra (Windows, Python 3.10.11) | 665 | 13 | 0 | 678 |
| `NOTE_VERSIONE_3.1.3.md` nel **repository** | 673 | 5 | 0 | 678 |
| `NOTE_VERSIONE_3.1.3.md` nella **copia** | 674 | 4 | 0 | 678 |
| **Questa baseline (ambiente A)** | **676** | **1** | **1** | **678** |

Il totale 678 coincide ovunque: **la suite non è cambiata**, cambia solo quanti test l'ambiente
consente di eseguire. La differenza è spiegata integralmente dai 13 salti dichiarati dall'audit
(9 display + 1 pikepdf + 1 pypdfium2 + 2 pyflakes):

```text
665 (audit)
 +9  test con display   → eseguiti qui grazie a Xvfb
 +1  pikepdf            → installato qui
 +1  pyflakes           → test_no_undefined_names, qui eseguito e superato
 = 676 passati
 +1  pypdfium2          → unico skip residuo
 +1  pyflakes           → test_no_pyflakes_warnings, qui eseguito e FALLITO
 = 678
```

Nessun file è stato modificato per far coincidere i numeri. Le differenze `673/5` e `674/4` fra le
due note di versione riguardano solo la tabella di qualità della documentazione e non il codice.

---

## 7. Baseline matematica

Script `baseline_matematica.py` (Appendice A), **32 controlli, 32 superati, 0 falliti**.
Dove possibile il confronto è con un oracolo ricostruito indipendentemente, e le dipendenze fra
oracoli sono dichiarate.

| ID | Controllo | Dominio verificato | Esito |
|---|---|---|---|
| M1 | `S3` ha 6 elementi; `PERM3` = tutte le permutazioni di {0,1,2}; `PERM3_J = {I_3, R_U}` | 6/6 | OK |
| M2 | `MSC(n) = 9·(n mod 3) + ⌊n/3⌋`; matrice `MSC` coerente con `M[T[i], i] = 1`; `MSC³ = I` | 27/27 | OK |
| M3 | Prodotto di Kronecker `build_Ai_matrix` = oracolo sulle cifre base 3 | **216/216** terne | OK |
| M4 | `M[T[i], i] = 1`, round-trip permutazione↔matrice; `M(a ∘ b) = M(a) @ M(b)` | 200 permutazioni casuali (seed 20260922) + 1 600 coppie in G | OK |
| M5 | `G = GEN3³`: 216 elementi distinti, chiusura, tavola di Cayley contro composizione diretta, identità unica, inversi, associatività | **46 656 = 216²** coppie esaustive | OK |
| M6 | `MSC ∘ (a ⊗ b ⊗ c) = (c ⊗ a ⊗ b) ∘ MSC` | **216/216** terne esaustive | OK |
| M7 | `H = G ⋊ C3`: 648 elementi distinti, chiusura | **419 904 = 648²** coppie esaustive | OK |
| M8a | Simulazione fisica del programma (`T_da_partita`) contro **oracolo fisico riscritto da zero** | 216/216 | OK |
| M8b | Idem con i rovesciamenti | **1 728 = 216 × 8** parametrizzazioni di stadio | OK |
| M8c | Formula a cifre `T_da_tabellone` contro l'oracolo fisico indipendente | 216/216 | OK |
| M9 | `tabellone_da_assi` inversa di `riga_tavola`; terne di assi tutte distinte; statistiche del capitolo 100 | 216/216; periodi `{1:1, 2:63, 3:26, 6:126}`, 64 auto-inverse, 7 tipi di ciclo | OK |
| M10 | `risolvi_trucco(c, t)` verificato con l'oracolo fisico indipendente | **729/729** coppie carta/bersaglio | OK |
| M11 | Bersaglio in G: **46 656** decomposizioni, tutte uniche, tutte ricostruttive; bersaglio `MSC ∘ g` fuori da G: **0** | 46 656 + 2 000 ricomposizioni campionate | OK |
| M12a | `try_kron_decompose` riconosce **esattamente** G | 216 riconosciuti, 0 falsi positivi su 432 elementi di `H \ G` | OK |
| M12b | `K ∘ MSCᵏ` parametrizza H in modo bigettivo | 648 coppie `(K, k)` → 648 permutazioni distinte, insieme **uguale a H** | OK |
| M12c | Legge di composizione canonica = composizione diretta delle permutazioni | **419 904 = 648²** coppie esaustive | OK |
| M13 | Cicli, ordine e periodo coerenti con il mcm delle lunghezze dei cicli | 216/216 righe della tavola | OK |

**Convenzioni confermate nel repository:** `T[carta] = posizione di destinazione`;
`deck[posizione] = carta`; `M[T[i], i] = 1`; `(a ∘ b)[i] = a[b[i]]`; `M(a ∘ b) = M(a) @ M(b)`;
`MSC(n) = 9·(n mod 3) + ⌊n/3⌋`; `MSC³ = I`; forma canonica `K ∘ MSCᵏ` con trasporto
`MSC ∘ K = rot₂(K) ∘ MSC` (rotazione sinistra di **due** posti, equivalente a destra di uno);
distinzione mescolamento/impilamento con `IMPILAMENTO_DI` che scambia solo `CDS ↔ DSC`.

**Indipendenza degli oracoli — dichiarazione esplicita.**

* M8a/M8b/M8c usano una simulazione fisica **riscritta dalla descrizione del gioco** in
  `baseline_matematica.py`, che non chiama `distribuisci`/`raccogli`/`esegui_partita`. Oracolo
  **indipendente** dal percorso verificato.
* M8c confronta la formula a cifre con quella stessa simulazione: i due percorsi sono
  **realmente indipendenti** (fisica carta-per-carta contro aritmetica in base 3).
* Il confronto `compute_T_full` (matrici) contro `T_da_partita` eseguito dal `selftest` interno
  **non è indipendente** in senso stretto: entrambi i percorsi derivano dalla stessa convenzione
  `M[T[i], i] = 1` e dalle stesse tabelle `PERM3`. È stato quindi *affiancato*, non sostituito,
  dall'oracolo fisico.
* M3 e M6 confrontano `build_Ai_matrix`/`mat_to_perm27` con una formula sulle cifre scritta a
  parte: indipendenti.
* M5 e M12c confrontano strutture precalcolate del programma (tavola di Cayley, legge canonica)
  con la composizione diretta `a[b[i]]`: indipendenti quanto basta, perché la composizione diretta
  non usa le tabelle.
* M11 e M12a usano la stessa tabella `_KRON_LOOKUP` che il programma usa per cercare: il controllo
  è di **cardinalità e unicità**, non di correttezza indipendente della tabella — che è però
  coperta da M3.

**Il core matematico del repository coincide con quello verificato da Astra**: i file sono
identici (§ 3) e i risultati qui ottenuti riproducono le cardinalità dichiarate dall'audit
(1 728, 648, 419 904, 216, 46 656, 10 077 696 = 216 × 46 656, 729).

---

## 8. Architettura corrente

### 8.1 Responsabilità e proprietario attuale

| Responsabilità | Proprietario attuale | Duplicazioni | Accoppiamenti impropri |
|---|---|---|---|
| Dominio matematico | `core/permutations.py`, `core/kronecker.py`, `core/group_theory.py`, `core/gioco_reale.py`, `core/analysis.py`, `core/constants.py` | tabelle GEN3/MSC e Cayley in due moduli; inversa in tre | `permutations.py` contiene due funzioni **Tk** (N02); quattro moduli core importano `gui.i18n` |
| Linguaggio / AST | `core/algebra.py` (`Lexer`, `Parser`, `AlgebraEngine`, `CanonicalForm`, `Controller`) | secondo parser regex in `gui/shuffle.py` | `algebra.py` contiene anche analisi CSV ed export Excel |
| Simulazione | `core/gioco_reale.py` (fisica), `gui/shuffle.py` (animazione), `gui/simulator_tab.py` (pratica) | — | la pratica legge lo stato dai widget (B04) |
| Analisi | `core/analysis.py`, `core/algebra.analizza_righe/analizza_csv`, `gui/analysis_tab.py` | — | l'aggregazione vive nel tab GUI (R01, B02, B03) |
| Stato / job | `gui/common.run_in_thread`, `core/parallel.py`, flag `_closing`/`_export_busy` sparsi nei tab | tre meccanismi di cancellazione diversi | nessun job manager unico (B03, R05) |
| Persistenza | `core/config.py` (`~/.gioco27/config.json`), `core/log.py` | — | `save()` non riporta l'esito (R07) |
| Cache | `core/cache.py` (formato v2, scadenza) | — | validazione incompleta (B08) |
| Export | `core/parallel.py` (`atomic_write`, `check_export_size`), `core/combinations.py`, `core/permutations.py`, `core/detail_pdf.py`, `core/pdfgrid.py`, `core/pdfmerge.py`, più sei dialoghi GUI | policy applicata in modo disomogeneo (B11, R02) | export mescolato con parser e analisi in `algebra.py` |
| Presentation / i18n | `gui/i18n.py` (1 288 chiavi IT + 1 288 EN), `gui/presentation.py`, `gui/glossary.py` | — | **il core dipende dalla GUI** per tradurre |
| GUI | `gui/app.py` + 25 moduli | due `Tooltip` | BFS di gruppo in `gui/cayley_dialog.py` |
| Packaging | `pyproject.toml`, `requirements*.txt`, `avvia.bat`, `gioco27.spec` **non versionato** | — | nessuna CI, nessun lock (R06, N04) |

### 8.2 Grafo delle dipendenze — fatti misurati

```text
import core -> gui (4, tutti verso gui.i18n)
    core/algebra.py        -> gui/i18n.py
    core/combinations.py   -> gui/i18n.py
    core/detail_pdf.py     -> gui/i18n.py
    core/gioco_reale.py    -> gui/i18n.py

cicli diretti fra moduli del package: 1
    core/combinations.py  <->  core/permutations.py
        (combinations importa permutations in testa;
         permutations.write_csv importa combinations dentro la funzione)
```

Stato globale mutabile nel core: `core/detail_pdf._FONTS_READY`, `core/kronecker._KRON_LOOKUP`,
`core/permutations._STAGE_CACHE`, `core/analysis._G216`, `core/group_theory._instance`,
più la lingua corrente in `gui/i18n`. Sono cache di processo, non condivise fra thread in modo
protetto: rilevanti per il compartimento C.

Codice apparentemente morto: `core/kronecker.py:247-289` (dopo un `return` incondizionato).

---

## 9. Dipendenze e build

`requires-python = ">=3.9"`. Nessun file di lock, nessuna directory `.github`, **nessuna CI**.

| Pacchetto | Dichiarato | Realmente importato | Natura | Note |
|---|---|---|---|---|
| `numpy` | `dependencies` e `requirements.txt` (`>=1.20`) | 15 moduli | **runtime obbligatoria** | usata anche da `gioco_reale.selftest` per il confronto matriciale |
| `tkinter` | non dichiarabile (stdlib), citata nei commenti di `requirements.txt` | tutta la GUI e 5 moduli di test | **runtime obbligatoria per l'app** | su Linux richiede `python3-tk`; la sua assenza blocca la raccolta di 5 file di test (§ 6.2) |
| `reportlab` | extra `export` (`>=3.6`) | 5 moduli | opzionale (PDF) | necessaria a molti test |
| `openpyxl` | extra `export` (`>=3.0`) | `core/algebra.py`, `gui/analysis_tab.py` | opzionale (Excel) | necessaria ai test di export |
| `pypdf` | extra `export` (`>=3.0`) | 8 moduli | opzionale (unione PDF) | necessaria a molti test |
| `pikepdf` | extra `export` (`>=8.0`) | `core/pdfmerge.py` | opzionale (deduplica) | se assente, 1 skip |
| `pytest` | `requirements-dev.txt`, extra `dev` | 25 file di test | sviluppo | — |
| `pyflakes` | `requirements-dev.txt`, extra `dev` | `tests/test_static.py` (via `importorskip`) | sviluppo | **se installata la suite fallisce** (N01) |
| `pyinstaller` | extra `dev` | mai importato | build | lo spec non è versionato (N04) |
| `setuptools>=68` | `[build-system]` | — | build | backend `setuptools.build_meta` |
| **`pypdfium2`** | **mai dichiarata** | `tests/test_layout_dettaglio.py:73` (`importorskip`) | test | **N03**: dipendenza di test non dichiarata in alcun file |

Nessuna dipendenza dichiarata risulta mai importata: `dichiarate − importate = ∅`.
Non sono stati installati pacchetti nel repository né nella VM dell'utente per «sistemare»
l'ambiente: le installazioni sono avvenute solo nel container di analisi e sono elencate in § 6.1.

Entry point: `gioco27.py`, `python -m gioco27` (`gioco27/__main__.py`), `avvia.bat`,
`[project.gui-scripts] gioco27 = gioco27.__main__:main`. Dati di package: `gioco27/assets/*.ttf`
dichiarati in `[tool.setuptools.package-data]`.

---

## 10. Discrepanze con `PROJECT_EVOLUTION_PLAN.md`

### 10.1 Riferimenti da correggere nel piano

| Piano | Realtà del repository | Impatto |
|---|---|---|
| R04: «`orbit_of:65`» in `permutations` | la funzione è `core/analysis.py:63 orbit_of`; `permutations.py:65` è la matrice `MSC` | nessun impatto sostanziale, ma il rischio è **più grave** del descritto: ciclo infinito, non orbita anomala |
| B08: «`cache.py:64`» | `load_decompositions` inizia a `core/cache.py:66` (a 64 c'è una riga vuota) | nessuno |
| M06: «`detail_pdf:739`» | la stringa non localizzata è a `core/detail_pdf.py:740` | nessuno |
| Impronta «87 file» | 87 file **nella copia**, 88 nel repository (`LICENSE` in più, `PROJECT_EVOLUTION_PLAN.md` in meno, `gioco27.spec` non tracciato) | va riformulata per il repository: § 2.3 |
| Baseline «665 passed, 13 skipped» | valida per l'ambiente dell'audit; in un ambiente completo diventa 676/1/**1 fallito** | il piano non poteva vedere il fallimento pyflakes perché quei due test erano saltati |

Tutti gli altri riferimenti di riga controllati (26 posizioni citate da B01–B12, R01–R07, M01–M06)
**coincidono esattamente**, coerentemente con l'identità dei file (§ 3).

### 10.2 Affermazioni del piano che il repository ridimensiona

* **M02, seconda parte** — «descrizione della rotazione inesatta in `algebra`»: non confermata.
  Le regole documentate sono verificate esaustivamente corrette (M6, M12c). Resta valida la prima
  parte (numerazione base 1 nelle docstring).
* **M05** — `protocol_dialog` usa già `Path.as_uri()`; la composizione manuale di `file://`
  sopravvive invece in quattro **altri** moduli, che il piano non nomina.
* **R02** — `atomic_write` è già importato da `core/algebra.py`: la disomogeneità è interna al
  modulo, non un'assenza totale di atomicità.

### 10.3 Criticità **nuove**, non presenti nell'audit

| ID | Criticità | Evidenza | Proprietario proposto |
|---|---|---|---|
| **N01** | **La suite è rossa in qualunque ambiente con pyflakes installato.** `tests/test_static.py::test_no_pyflakes_warnings` fallisce su due warning reali del codice versionato (`gui/export_dialog.py:244` f-string senza segnaposto; `gui/onboarding_tab.py:12` `ONBOARD_INTRO` importato e non usato). L'audit non poteva rilevarlo perché nel suo ambiente quei test erano fra i 13 saltati. | § 6.1 | **A** — va chiuso prima di qualunque lavoro di regressione |
| **N02** | Due funzioni **Tk** in un modulo del dominio matematico: `core/permutations.py:25 configure_matrix_tags`, `:32 insert_colored`. | § 8.1 | **D**, con interfaccia verso H |
| **N03** | `pypdfium2` è richiesta da `tests/test_layout_dettaglio.py` ma non è dichiarata in `requirements*.txt` né in `pyproject.toml`: il salto è silenzioso e permanente. | § 9 | **K** |
| **N04** | `gioco27.spec` (configurazione PyInstaller) è escluso da `.gitignore:33` (`*.spec`): **la build non è riproducibile dal solo repository**. | § 2.2 | **K** |
| **N05** | 74 file `.pyc` nel working tree contengono percorsi assoluti di una **terza cartella** (`C:\Users\Maurizio\Codex_Progetti\gioco-27-carte\...`): cache byte-compilate di una copia precedente, che compaiono nei traceback e possono confondere la diagnosi. Sono artefatti ignorati da Git, non contenuto del repository. Nessuna cancellazione è stata eseguita. | § 2.2 | **A** (igiene di ambiente, previa autorizzazione) |
| **N06** | Un test esistente **congela B08 come specifica**: `tests/test_decomposition_integrita.py::test_b11_cache_json_v2_valida_accettata[results0]` asserisce che una cache con `results = []` sia accettata e restituita. Correggere B08 richiederà una modifica dichiarata di quel test. | § 4.1 | **B/F**, con decisione esplicita |

---

## 11. Aggiornamento proposto della roadmap (compartimenti A–K)

| Compartimento | Applicabilità al repository reale | Prerequisiti | Cambiamenti rispetto all'audit | Dipendenze reali | Già soddisfatto |
|---|---|---|---|---|---|
| **A — Baseline e sicurezza** | Applicabile, **in corso con questo documento** | nessuno | si aggiungono N01 (suite rossa), N05 (cache estranee) e la certificazione dell'ambiente (R06) | — | Impronta di contenuto, baseline test, baseline matematica (32 controlli), grafo architetturale, mappa dipendenze, matrici B/R/M |
| **B — Integrità I/O** (filesystem, cache, export) | Applicabile | A chiuso (suite verde) | proprietario di B01, B08, B10, B11, B12, R02, R03, M05, N06 | `core/parallel`, `core/cache`, `core/pdfmerge`, `core/permutations`, `core/combinations`, sei dialoghi GUI | `atomic_write` e `check_export_size` esistono già e sono testati: si tratta di **estenderne l'applicazione**, non di scriverli |
| **C — Stato e concorrenza** | Applicabile | A | proprietario di B02, B03, B04, R01 (parte di cancellazione), R05, M03 | `gui/common.run_in_thread`, i flag `_closing`/`_export_busy`, i tre tab con job | `tests/test_rischi_concorrenza.py` e `tests/test_chiusura_regressioni.py` forniscono già harness riutilizzabili |
| **D — Dominio matematico** | Applicabile | A | proprietario di B09, R04, M02, N02; **nessuna correzione di convenzione**: la matematica è verificata corretta | `core/permutations`, `kronecker`, `group_theory`, `gioco_reale`, `analysis` | Baseline § 7 al completo; le duplicazioni GEN3/MSC restano come oracoli finché non esiste un sostituto indipendente |
| **E — Linguaggio e simulazione** | Applicabile | D | proprietario di B07 (AST unico Explorer/Shuffle) | `core/algebra` (Lexer/Parser/Controller), `gui/shuffle` | La grammatica tipizzata esiste già ed è completa: il lavoro è far generare i passi dall'AST |
| **F — Analisi e performance** | Applicabile | D, E | proprietario di B05, B06, R01 (budget e aggregazione incrementale) | `core/analysis`, `core/algebra.analizza_*`, `core/combinations`, `gui/analysis_tab` | Misure di parallelismo già presenti in `test_hardening.py` |
| **G — Servizi applicativi e modelli di risultato** | Applicabile | B, C, D/E/F | invariato (F04, F05, F06 del piano) | tutti i precedenti | — |
| **H — UI/UX, presentation e i18n** | Applicabile | G, **ma vedi § 14: una parte deve anticipare** | proprietario di M01, M04, M06, dei due Tooltip, del BFS da spostare fuori dalla GUI | `gui/*`, `gui/i18n` | i18n completa (1 288 + 1 288 chiavi), coperta da quattro file di test dedicati |
| **I — Laboratorio matematico** | Applicabile | D, G, H | invariato | `core/group_theory`, nuove viste | `GroupData` espone già Cayley, inverse, ordini, classi, centro |
| **J — Sessioni, esperimenti, cronologia** | Applicabile | G | invariato | `core/config`, `core/cache`, nuovo modello di sessione | Cache e configurazione esistono e sono testate |
| **K — Packaging, CI, documentazione, release** | Applicabile | B…J | si aggiungono N03 (pypdfium2 non dichiarata) e N04 (`gioco27.spec` non versionato) | `pyproject.toml`, `requirements*`, `.gitignore`, `.github` (da creare) | Versione coerente 3.1.3, tag `v3.1.3` su HEAD, note di versione presenti |

---

## 12. Gate iniziali

| Gate | Domanda | Esito |
|---|---|---|
| **G0 — suite verde** | La suite passa in un ambiente completo? | **NO.** Un fallimento reale (N01). È l'unico ostacolo formale e si chiude dentro A. |
| **G1 — contenuto identificato** | Sappiamo su cosa stiamo costruendo? | **SÌ.** Commit `54445af`, impronta `ebd4b8a0…`, identità col contenuto dell'audit dimostrata. |
| **G2 — matematica integra** | Le convenzioni sono preservate? | **SÌ.** 32/32 controlli, domini esaustivi. |
| **G3 — architettura nota** | Cicli, duplicazioni e dipendenze improprie sono mappati? | **SÌ.** § 8. |
| **G4 — dipendenze note** | Dichiarato vs reale? | **SÌ**, con due scoperte (N03, N04). |

**Il repository è pronto per iniziare il compartimento D** (dominio matematico) **immediatamente**:
la baseline matematica è verde ed esaustiva e nessun lavoro di D dipende dalla suite statica.

**È pronto per B e per C subito dopo la chiusura di N01**, che è un intervento di due righe di codice
(non un fix B01–B12) e appartiene ad A. Finché la suite è rossa, nessuna regressione introdotta da
B o C sarebbe distinguibile dal rumore.

Due avvertenze operative, dimostrate dal repository:

1. **B e D condividono due file.** `core/permutations.py` e `core/combinations.py` contengono
   insieme la matematica degli stadi e le rotte di export (ed è lì che vive l'unico ciclo di
   import). B e D non sono parallelizzabili su quei due file senza concordare prima la divisione.
2. **C e B si incontrano su `core/parallel.py`** (cancellazione cooperativa + scrittura atomica).
   Stessa raccomandazione.

---

## 13. Verifica della copertura del piano

| Elemento del piano | Proprietario | Dipendenze | Criteri di accettazione | Test previsti | Duplicazioni |
|---|---|---|---|---|---|
| B01, B11, B12, B10 | B | A | nessun output pubblicato da dati incompleti o da un errore | riapertura/ricostruzione, ogni entry point | nessuna |
| B08 + cache | B | A | distinzione contesto parziale / cache completa | cache vuota, troncata, duplicati, fuori G | **N06**: test esistente da rinegoziare |
| B02, B03, B04 | C | A | risultati sempre coerenti con l'input che li ha generati | completamenti fuori ordine, reset in corsa, campi modificati | nessuna |
| B05, B06 | F | D, E | ingressi malformati rifiutati prima del calcolo; `count == len(list(iter))` | corpus di ingressi invalidi | nessuna |
| B07 | E | D | una sola interpretazione dell'espressione | corpus condiviso valido/non valido | due parser **da unificare**, non da duplicare |
| B09, R04 | D | A | diagnostica indipendente dai flag dell'interprete; API pubbliche validate | processo normale e `-O`; subprocess con timeout | nessuna |
| R01 | F (+ C per la cancellazione) | D, E | il caso enorme è rifiutato o pianificato senza enumerarlo | budget di preflight | responsabilità condivisa: **proprietario F**, C espone solo la cancellazione |
| R02, R03, M05 | B | A | atomicità su tutte le rotte; temporanei univoci | due deduplicazioni concorrenti; path con spazi e accenti | nessuna |
| R05, M03 | C | A | ogni lavoro termina con uno stato conclusivo | iniezione di ImportError/RuntimeError in Tk reale | nessuna |
| R06, N03, N04 | K | B…J | ambiente certificato e build riproducibile | installazione minima e completa, build | nessuna |
| R07 | C (config) o G (servizi) | A | esito esplicito della scrittura | home in sola lettura, disco pieno | **proprietario principale: C**; G consuma l'esito |
| M01, M04, M06 | H | G | scelte di UI esplicite e localizzate | test IT/EN, schermi piccoli | nessuna |
| M02, N02 | D | A | glossario unico di indici; Tk fuori dal dominio | test mirati alle formule | nessuna |
| F01…F09 | G, poi H | B, C, D/E/F | comportamento invariato a parità di input | confronto vecchio/nuovo | F07 tocca le tabelle duplicate: **serve prima un oracolo sostitutivo** |
| i18n | H | — | cataloghi simmetrici | già coperto | nessuna |
| N01 | A | — | suite verde con pyflakes installato | il test esistente | nessuna |

Nessun elemento del piano resta senza proprietario. Le sole responsabilità realmente condivise
(R01 fra F e C, R07 fra C e G, F07 fra D e G) sono indicate sopra con il proprietario principale e
l'interfaccia dell'altro.

---

## 14. Dipendenze fra compartimenti

Grafo proposto nell'incarico, **verificato contro il repository**:

```text
A
├── B
├── C
└── D
     └── E
          └── F

B + C + D/E/F  →  G  →  H → I
                   \
                    → J
B...J  →  K
```

Il repository conferma `A → {B, C, D}`, `D → E`, `E → F`, `{B,C,D,E,F} → G`, `G → {H, J}`,
`H → I`, `{B…J} → K`. Due correzioni sono però imposte dai fatti:

1. **Serve un arco `A → (porzione di H)`, oppure lo spostamento di `i18n` fuori da `gui`.**
   Oggi `core/algebra.py`, `core/combinations.py`, `core/detail_pdf.py` e `core/gioco_reale.py`
   importano `gui.i18n`. Qualunque lavoro di B, D, E o F che tocchi i messaggi d'errore dipende
   dal contratto di presentazione, che il grafo colloca a valle (H). È un contratto tecnico reale,
   non una comodità: il codice non compila diversamente. Proposta: in **A o K**, spostare il
   catalogo in un package neutro (per esempio `gioco27/i18n`) con un semplice ri-export da
   `gioco27.gui.i18n`, **senza alcun cambiamento di comportamento**, così che l'arco improprio
   sparisca prima che B/D/E/F lo consolidino.
2. **`B ↔ D` condividono `core/permutations.py` e `core/combinations.py`** (unico ciclo di import
   del package). Non è una dipendenza d'ordine, è un **vincolo di co-locazione**: va scelto se la
   separazione export/dominio di quei due moduli appartiene a B o a D, *prima* di aprirli
   entrambi. Proposta: assegnarla a **B**, che possiede già `core/parallel.py`.

Nessun altro arco è stato aggiunto. In particolare **non** è stata introdotta una dipendenza
`C → B` (i job non hanno bisogno della scrittura atomica per esistere) né `I → J`.

---

## 15. Criterio di completamento — risposte con evidenza

| Domanda | Risposta |
|---|---|
| Su quale commit stiamo costruendo? | `54445af9c5e499523986a227c0bb7dba32ded763`, branch `main`, tag `v3.1.3`, allineato a `origin/main` (§ 1) |
| Qual è la baseline reale dei test? | 678 raccolti, **676 passati, 1 saltato, 1 fallito**, 78,9 s, Python 3.12.3 con tkinter e Xvfb (§ 6.1); il fallimento è N01 |
| Il core matematico coincide con quello verificato da Astra? | **Sì**, e in modo dimostrato: i file del package sono byte-identici (§ 3) e l'impronta della copia riproduce quella dell'audit (§ 2.3); inoltre 32/32 controlli esaustivi indipendenti (§ 7) |
| Quali B01–B12 esistono davvero? | **Tutti e dodici**, riprodotti uno per uno sul codice del repository (§ 4) |
| Quali sono già risolti? | **Nessuno.** Nessuna voce risulta GIÀ RISOLTO, NON APPLICABILE o NON RIPRODOTTO |
| Quali dipendenze dell'audit non si applicano? | Nessuna in senso proprio; tre riferimenti di posizione sono imprecisi (§ 10.1) e tre affermazioni vanno ridimensionate (§ 10.2) |
| Esistono criticità nuove? | **Sì, sei**: N01 suite rossa, N02 Tk nel dominio, N03 `pypdfium2` non dichiarata, N04 build non versionata, N05 cache `.pyc` estranee, N06 test che congela B08 (§ 10.3) |
| Il piano A–K copre tutto il programma? | **Sì** (§ 13); ogni voce ha proprietario, dipendenze, criteri e test previsti |
| Ci sono responsabilità duplicate? | Tre parziali (R01, R07, F07), con proprietario principale già assegnato; più le duplicazioni di codice della § 5.1, che oggi **servono da oracoli** e non vanno rimosse senza sostituto |
| Ci sono dipendenze circolari o insoddisfatte? | Una circolare reale (`combinations ↔ permutations`) e una insoddisfatta nel grafo dei compartimenti (`core → gui.i18n`), entrambe affrontate in § 14 |
| Quali compartimenti sono sviluppabili indipendentemente? | **D** da subito; **B** e **C** in parallelo fra loro dopo N01, con le due avvertenze di co-locazione della § 12 |
| Qual è il prossimo compartimento implementabile senza destabilizzare gli altri? | **Chiusura di A** (solo N01 + dichiarazione di N03/N04/N05), poi **D**, che non tocca alcun file condiviso con B o C |

---

## 16. File creati o modificati da questo incarico

| File | Operazione | Perché |
|---|---|---|
| `GIT_BASELINE_AND_RECONCILIATION.md` | **creato** nella radice del repository | è il deliverable richiesto dall'incarico; resta *untracked* (nessun commit è stato eseguito) |

**Nessun altro file è stato creato, modificato, spostato o cancellato nel repository.**
In particolare: nessun file di `gioco27/`, nessun test, nessuna configurazione, nessun file
ignorato (i 74 `.pyc` di N05 sono stati soltanto ispezionati), nessun commit, nessun tag,
nessun push, nessun `reset`, nessun `rebase`.

Gli script di verifica (`baseline_matematica.py`, `verifica_bug.py`, `verifica_rischi.py`,
`architettura.py`) sono stati eseguiti **fuori dal repository**, su una copia di sola lettura dei
file tracciati, e non sono stati depositati nel repository: sono riportati integralmente in
Appendice A per la riproducibilità.

---

## Appendice A — Come riprodurre queste verifiche

**Ambiente.** Linux con `python3-tk` e `xvfb`, oppure Windows con Python 3.10+; installare
`numpy reportlab openpyxl pypdf pikepdf pytest pyflakes` (e `pypdfium2` per azzerare anche
l'ultimo skip).

```bash
# 1. Baseline della suite (ambiente A di § 6.1)
Xvfb :99 -screen 0 1280x1024x24 &
DISPLAY=:99 PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -p no:cacheprovider -ra -q

# 2. Baseline matematica: 32 controlli esaustivi
python3 baseline_matematica.py        # atteso: 32 controlli, 32 superati, 0 falliti

# 3. Riproduzione di B01-B12
DISPLAY=:99 python3 verifica_bug.py   # atteso: 12 voci, tutte PRESENTE

# 4. Riconciliazione R01-R07 e M01-M06
python3 verifica_rischi.py

# 5. Grafo architetturale, duplicazioni e dipendenze reali
python3 architettura.py

# 6. Impronta di contenuto (algoritmo dell'audit, ordinamento Windows)
python3 - <<'EOF'
import hashlib, pathlib
h = hashlib.sha256()
root = pathlib.Path('.')
files = []
for p in root.rglob('*'):
    if not p.is_file(): continue
    rel = p.relative_to(root).as_posix(); parts = rel.split('/')
    if {'__pycache__', '.pytest_cache'} & set(parts) or parts[0] == '.git': continue
    files.append(rel)
for rel in sorted(files, key=lambda s: tuple(x.lower() for x in s.split('/'))):
    h.update(rel.encode()); h.update(b'\0')
    h.update(hashlib.sha256(pathlib.Path(rel).read_bytes()).digest())
print(h.hexdigest(), len(files))
EOF
```

I quattro script sono conservati fuori dal repository. Possono essere versionati in futuro, ma
solo nel compartimento **A** o **K**, come strumenti di baseline, e con una decisione esplicita:
questo incarico non li ha depositati per non introdurre file non richiesti nel repository.
