# D_DOMAIN_CLOSED — chiusura del compartimento D (Dominio matematico)

Registro verificabile dell'intervento. Il quadro tecnico generale resta in
`GIT_BASELINE_AND_RECONCILIATION.md`; la chiusura del compartimento A in
`A_BASELINE_CLOSED.md`. Qui c'è solo ciò che D ha cambiato e come è stato provato.

## 1. Identità

| Voce | Valore |
|---|---|
| Branch | `main` (nessun push: `origin/main` resta a `54445af`) |
| HEAD iniziale | `0c8536c8fa59461bb5c0440e338c0af801d7b5dd` — «docs(A): record closed baseline» |
| HEAD finale | l'ultimo commit di questo elenco (§ 11) |
| Working tree all'avvio | pulito, nessuna modifica preesistente dell'utente |
| Commit di A2 presenti | `28283e5`, `12d343d`, `36d6b87`, `0c8536c` — non riscritti, non toccati |

Misura di partenza (ambiente di riferimento, § 9): **703 raccolti, 702 passati,
1 saltato, 74,89 s**; `pytest tests/test_baseline_matematica.py` → **25 passati**.

## 2. B09 — selftest indipendente da `assert`

**Riproduzione.** Iniettando una simulazione fisica guasta (`T_da_partita` che
restituisce `[0]*27`) nel codice a `0c8536c`:

```text
normale -> ERRORE AssertionError riga 0
con -O  -> ESITO TUTTO OK            ← il guasto spariva con l'ottimizzazione
```

**Soluzione.** Ogni confronto di `selftest()` (e il controllo finale di
`risolvi_trucco`) diventa un `if` esplicito che solleva **`VerificaFallita`**,
definita in `core/gioco_reale.py`. È sottoclasse di `AssertionError` per scelta
conservativa: la GUI intercetta `AssertionError` (R05 appartiene a C e non è
stato toccato), quindi il contratto verso i chiamanti non cambia — ma un `if`
non dipende dai flag dell'interprete. Messaggi, chiavi del rapporto e
significato delle verifiche sono identici; nel modulo non resta alcun `assert`.

**Esito dopo la correzione:**

```text
normale -> ERRORE VerificaFallita riga 0
con -O  -> ERRORE VerificaFallita riga 0
```

**Regressione.** `tests/test_dominio_selftest.py` (7 test): l'iniezione viene
eseguita in due sottoprocessi reali, normale e `-O`, verificando anche
`sys.flags.optimize`; più il controllo che `VerificaFallita` resti sottoclasse
di `AssertionError`, che nel modulo non esistano più nodi `Assert` nell'AST, e
che il messaggio dell'ancora #100 sia ancora esattamente `ancora #100`.

## 3. R04 — contratti ai confini delle API matematiche

**Riproduzione.** Sul codice a `0c8536c`, in sottoprocesso:
`orbit_of([1, 1], 0)` **non termina** (timeout 15 s).

**Contratto.** Nuovo modulo **`gioco27/core/dominio.py`** (unico punto di
verità, nessuna dipendenza oltre `numbers`):

* lunghezza esatta quando `n` è richiesto;
* ogni elemento intero secondo la politica sotto;
* valori in `0..n-1`;
* valori distinti — quindi bigezione;
* errore dedicato **`PermutazioneNonValida(ValueError)`**, neutro: niente Tk,
  niente filesystem, niente i18n.

**Politica sui tipi, dichiarata ed esercitata dai test:**

| Ingresso | Esito | Perché |
|---|---|---|
| `int` Python, interi NumPy | accettati (convertiti con `int`) | è il caso normale |
| `bool` (`True`/`False`) | **rifiutati** benché `Integral` | un flag usato come indice è quasi sempre un errore |
| `float`, `Decimal`, `"3"` | **rifiutati** anche se "valgono" un intero | `int(...)` maschererebbe l'errore invece di segnalarlo |
| list, tuple, `range`, ndarray 1-D | accettati | contenitori leciti |
| `str`, `bytes`, `dict`, ndarray n-D | **rifiutati** | iterabili, ma mai una permutazione |

**API protette** (solo i confini pubblici; le funzioni interne non ripetono la
validazione):

| Modulo | Funzioni |
|---|---|
| `core/analysis.py` | `cycle_decomposition`, `orbit_of` (+ indice `card`) — `order_of` e `cycle_type` ereditano la validazione da `cycle_decomposition` e non la duplicano |
| `core/gioco_reale.py` | `periodo`, `tipo_ciclo`, `punti_fissi`, `parita` |
| `core/kronecker.py` | `find_all_kron_decompositions`, `try_kron_decompose` |

**Difesa strutturale.** `orbit_of` tiene ora l'insieme dei visitati: su una
permutazione valida quel ramo è irraggiungibile (l'orbita ha al più `n`
elementi), quindi è una difesa, non il modo normale di terminare. Nessun timeout
è entrato nell'algoritmo: il timeout compare solo *nel test*, come protezione
del runner.

**Comportamento sugli input invalidi:** `PermutazioneNonValida` con messaggio che
indica il primo problema e la posizione, per esempio
`orbit_of: valore 1 ripetuto (posizione 1): non e' una bigezione`.

**Test.** `tests/test_dominio_permutazioni.py` (74 test): duplicati, negativi,
valori ≥ n, lunghezza errata, tipi errati, input vuoto, permutazione valida,
identità; la regressione in sottoprocesso che dimostra che il caso prima pendente
ora **termina** con errore controllato; l'equivalenza dei risultati validi con un
oracolo di iterazione diretta.

## 4. N02 — Tk fuori dal dominio

`core/permutations.py` conteneva `configure_matrix_tags` e `insert_colored`, che
configurano tag e scrivono su un widget `tk.Text`.

| Voce | Esito |
|---|---|
| Funzioni | `configure_matrix_tags`, `insert_colored` |
| Vecchio proprietario | `gioco27/core/permutations.py` |
| Nuovo proprietario | `gioco27/gui/common.py` — dove **esistevano già identiche carattere per carattere** |
| Chiamanti | `gui/analysis_tab.py` e `gui/explorer_tab.py` le importavano **già** da `gui/common.py`: nel core erano copie morte |
| Compatibilità | nessun adapter necessario: nessun modulo e nessun test importava le versioni del core |

Sono state quindi **rimosse**, non spostate, con una nota nel modulo che indica
il proprietario reale. Resta nel core `_compile_perm3_pat` (una regex sui nomi
GEN3, nessun Tk), importata da `gui/common.py`: la sua collocazione definitiva,
insieme a `PERM3_COLORS`, è materia di **H** e non è stata anticipata qui.

Verifica: **`core → tkinter = 0`**, e nel dominio non resta alcuna operazione su
widget (`tag_configure`, `insert("end", …)`, `txt_widget`).

## 5. M02 — numerazione e terminologia

**Ambiguità corretta.** I parametri di `core/permutations.py` si chiamavano
`p1n/p2n/p3n` pur essendo posizionalmente `P₀/P₁/P₂` — una nota nel codice lo
ammetteva già («rimasti a base 1 per non toccare le firme interne»), mentre le
chiavi dei filtri sono `p0/p1/p2`. Ora:

* parametri e variabili locali passano alla numerazione base 0 del dominio:
  `p0n/p1n/p2n`, `j0n/j1n/j2n`, `f2/f1/f0`, `stage_index`, `a0l/a1l/a2l`;
* le docstring dicono quale argomento tocca quale cifra, e che `build_P27`
  riceve le cifre in ordine **crescente** mentre `build_Ai_matrix` le riceve in
  ordine **decrescente** (due convenzioni opposte che prima non erano scritte);
* il **glossario unico** (`stage_index`, `digit_index`, numerazione storica a
  base 1) sta in `core/dominio.py`;
* `core/detail.py` e `core/detail_pdf.py` dichiarano che il loro «stadio 1/2/3»
  è la numerazione **storica** del programma C (`stadio = stage_index + 1`),
  conservata perché è un formato esportato.

**Equivalenza dimostrata.** Confronto esaustivo fra la versione precedente e
quella attuale, caricate insieme nello stesso processo:

```text
1.728 configurazioni di stadio: compute_stage, compute_Ai_symbolic,
                                stage_label, _stage_Ai              → 0 differenze
216 + 8 terne:  build_P27, build_J27, build_Ai_matrix,
                Ai_label, _kron_vec                                 → 0 differenze
500 terne di stadi: compute_T_perm, R_label, compute_T_full,
                    make_csv_row                                    → 0 differenze
```

**Deliberatamente NON rinominati** (la rinomina avrebbe propagato confusione o
rotto un formato):

| Elemento | Motivo |
|---|---|
| intestazioni CSV, etichette `Stage{n}`, `(a x b x c)`, `T = … o MSC o …` | formato esportato e storico: identici prima e dopo |
| «stadio 1/2/3» in `detail.py` / `detail_pdf.py` | numerazione del programma C, ora **documentata** invece che rinumerata |
| `D#`, tavola, indici `P[i][j][k][m]` | formati storici |
| nomi delle chiavi di filtro `p0…j2` | già in base 0, invariati |
| variabili locali di `core/combinations.py` | appartengono a F: fuori dal perimetro di D |
| formule di rotazione in `core/algebra.py` | verificate corrette in modo esaustivo: la baseline è arbitro, non la docstring |

**Test.** `tests/test_dominio_indici.py` (17 test) fissa l'ordine degli
argomenti: se qualcuno invertisse P₀ e P₂ «per coerenza con una docstring»,
fallirebbero.

## 6. Contratti del dominio introdotti

| Elemento | Motivazione | Note |
|---|---|---|
| `core/dominio.py` — `PermutazioneNonValida`, `valida_permutazione`, `valida_indice` | validazione **una volta sola**, politica sui tipi esplicita, errori neutri | nessuna dipendenza oltre `numbers`: niente Tk, filesystem, i18n, export |
| glossario indici (docstring dello stesso modulo) | rende inequivoca la terminologia senza toccare i formati | |
| `kronecker.appartiene_a_G` / `appartiene_a_H` | l'appartenenza diventa un test esplicito, non un'euristica implicita | verificate su G (216), H\G (432), fuori da H |

**Tipi di dominio NON introdotti** — deliberatamente: `Permutation3`,
`Permutation27`, `Permutation`, `Deck`, `StageSpec`. Il programma rappresenta
oggi tutto con liste e array NumPy, in percorsi caldi misurati; avvolgerli in
classi avrebbe toccato decine di chiamanti senza risolvere alcun problema che la
validazione al confine non risolva già, e avrebbe invaso il perimetro di E, F e
G. Il minimo insieme di astrazioni che serviva è quello della tabella sopra.

**Adapter legacy.** Nessuno nuovo. Resta quello del compartimento A
(`gioco27/gui/i18n.py` → `gioco27/i18n.py`).

## 7. Matematica: invariata

| Verifica | Prima di D | Dopo D |
|---|---|---|
| `tests/test_baseline_matematica.py` | 25 passati | **25 passati** |
| \|S3\| / \|G\| / \|H\| | 6 / 216 / 648 | **6 / 216 / 648** |
| prodotti in G / in H | 46.656 / 419.904 | **46.656 / 419.904** |
| configurazioni di stadio | 1.728 | **1.728** |
| coppie carta/bersaglio | 729 | **729** |
| righe della tavola | 216 | **216** |
| decomposizioni per target in G | 46.656 | **46.656** |
| statistiche cap. 100 | `{1:1, 2:63, 3:26, 6:126}`, 64 auto-inverse | **identiche** |

Verifiche **nuove** aggiunte da D (98 test in tutto): contratto di permutazione,
terminazione di `orbit_of`, simmetria diagnostica normale/`-O`, ordine degli
argomenti delle primitive, appartenenza a G e H con i tre confini
(G, H\G, fuori da H).

## 8. Architettura

```text
core -> gui        : 0
core -> tkinter    : 0        (e nessuna operazione su widget nel dominio)
core -> filesystem : nessuna nuova dipendenza — dominio.py importa solo `numbers`
core -> i18n       : 4 moduli (algebra, combinations, detail_pdf, gioco_reale),
                     invariati: messaggi legacy verso la GUI.
                     Il nuovo dominio è neutro: sollevare PermutazioneNonValida
                     non richiede traduzioni.
```

Dipendenza residua da documentare, come chiede il compartimento:

| Voce | Valore |
|---|---|
| Proprietario reale dei cataloghi | `gioco27/i18n.py` (compartimento A) |
| Adapter legacy | `gioco27/gui/i18n.py`, re-export |
| Direzione | `core → gioco27.i18n` (neutro) e `gui → gioco27.gui.i18n → gioco27.i18n` |
| Piano di rimozione | l'adapter sparisce quando H riorganizzerà la presentation; i 4 import di `core` verso i18n si chiudono in **G**, con un modello di risultato che porti codici d'errore invece di messaggi |

## 9. Test

Ambiente di riferimento (immutato dalla baseline A1 § 6.1): Linux,
**Python 3.12.3**, tkinter 8.6 con Xvfb, NumPy 2.5.3, ReportLab 5.0.1,
openpyxl 3.1.5, pypdf 6.18.1, pikepdf 10.13.0, pytest 9.1.1, pyflakes 3.4.0.

```text
PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m pytest -p no:cacheprovider -ra -q
```

| Voce | Prima di D | Dopo D |
|---|---:|---:|
| Raccolti | 703 | **801** |
| Passati | 702 | **800** |
| Falliti | 0 | **0** |
| Saltati | 1 | **1** |
| Durata | 74,89 s | **78,63 s** |

Unico skip: `tests/test_layout_dettaglio.py:73` — `pypdfium2` assente (**N03**,
debito noto di K, non toccato qui).

Test mirati di D: `tests/test_dominio_selftest.py` (7),
`tests/test_dominio_permutazioni.py` (74), `tests/test_dominio_indici.py` (17) —
**98 passati**. Baseline matematica: **25 passati**.
Statici: `test_no_pyflakes_warnings` e `test_no_undefined_names` verdi.

Ogni commit di D è stato verificato singolarmente, in un worktree separato, sul
sottoinsieme non-GUI della suite: **102 / 176 / 186 / 167 passati**, nessun
fallimento. Nessun commit intermedio è rosso.

Controllo di non-regressione dei bug non assegnati a D: la riproduzione di
B01–B12 è stata rieseguita dopo le modifiche. **B01–B08 e B10–B12 restano
riproducibili identici**; solo B09 cambia esito, come previsto:

```text
B09: con optimize=1 e simulazione guasta -> RILEVATO (VerificaFallita: riga 0)
```

## 10. File modificati

| File | Tema | Nota |
|---|---|---|
| `gioco27/core/dominio.py` | R04 / M02 | **nuovo** — contratto e glossario |
| `gioco27/core/gioco_reale.py` | B09 + R04 | `VerificaFallita`, niente `assert`, validazione di 4 funzioni |
| `gioco27/core/analysis.py` | R04 | validazione + difesa strutturale in `orbit_of` |
| `gioco27/core/kronecker.py` | R04 | validazione dei bersagli, `appartiene_a_G` / `appartiene_a_H` |
| `gioco27/core/permutations.py` | N02 + M02 | rimozione delle funzioni Tk; rinomine base 0 |
| `gioco27/core/detail.py` | M02 | nota sulla numerazione storica |
| `gioco27/core/detail_pdf.py` | M02 | idem, due punti |
| `tests/test_dominio_selftest.py` | B09 | **nuovo** |
| `tests/test_dominio_permutazioni.py` | R04 | **nuovo** |
| `tests/test_dominio_indici.py` | M02 | **nuovo** |
| `D_DOMAIN_CLOSED.md` | documentazione D | questo file |

Nessun altro file toccato: `conftest.py`, `pyproject.toml`, `requirements*`,
`.gitignore`, la GUI e tutti i test preesistenti restano **invariati**.

## 11. Commit locali

| Commit | Messaggio |
|---|---|
| `91b65e1` | `fix(D): make selftest independent of assert (B09)` |
| `887fca2` | `fix(D): harden permutation domain boundaries (R04)` |
| `a3ace56` | `refactor(D): move Tk helpers out of mathematical core (N02)` |
| `dc84ce4` | `refactor(D): clarify domain index conventions (M02)` |
| (quinto) | `docs(D): record closed domain compartment` |

Temi non mescolati: dove un file conteneva due temi (`gioco_reale.py`,
`permutations.py`) la separazione è stata fatta per contenuto, non per file, e
ogni commit risultante è autoconsistente e verde. Nessun push.

## 12. `git status` finale

```text
On branch main
Your branch is ahead of 'origin/main' by 9 commits.
nothing to commit, working tree clean
```

## 13. Gate di uscita

| Gate | Esito |
|---|---|
| D-G1 B09 corretto, verificato con Python normale e `-O` | **OK** — § 2 |
| D-G2 R04 non può più causare loop infinito | **OK** — `orbit_of([1,1],0)` termina con errore controllato |
| D-G3 contratti espliciti ai confini | **OK** — § 3, politica dichiarata e testata |
| D-G4 matematica valida invariata | **OK** — equivalenza esaustiva su 1.728 configurazioni + suite |
| D-G5 baseline matematica verde | **OK** — 25/25 |
| D-G6 suite completa verde | **OK** — 800 passati, 1 saltato, 0 falliti |
| D-G7 nessuna dipendenza `core → gui` | **OK** — 0 |
| D-G8 funzioni Tk fuori dal dominio | **OK** — `core → tkinter = 0` |
| D-G9 nessuna duplicazione-oracolo eliminata | **OK** — inverse, tabelle GEN3/MSC e tavole di Cayley restano tutte; le uniche copie rimosse erano due funzioni **di presentazione**, non oracoli, e il loro proprietario GUI resta |
| D-G10 nessun altro compartimento iniziato | **OK** — § 14 |
| D-G11 nessun push | **OK** |

**Il compartimento D è chiuso.**

## 14. Debiti rimasti

| Voce | Stato | Proprietario |
|---|---|---|
| **B01, B02, B03, B04, B05, B06, B07, B08, B10, B11, B12** | tutti presenti e riprodotti dopo D; nessuno toccato | B, C, E, F |
| **B09** | **chiuso in D** | — |
| **R04** | **chiuso in D** | — |
| **N02** | **chiuso in D** | — |
| **M02** | **chiuso in D** (la seconda parte dell'accusa, «rotazione inesatta», resta non confermata: le formule sono verificate corrette) | — |
| R01, R02, R03, R05, R06, R07 | invariati | B, C, K |
| M01, M03, M04, M05, M06 | invariati | B, C, H |
| **N03** `pypdfium2` non dichiarata | aperto — unico skip della suite | K |
| **N04** `gioco27.spec` non versionato | aperto | K |
| **N06** test che congela B08 | aperto, e **non toccato** come richiesto | B/F |
| Ramo morto in `core/kronecker.py` dopo il `return` incondizionato | aperto | F |
| `_compile_perm3_pat` e `PERM3_COLORS` nel core | presentazione residua, senza Tk | H |
| Duplicazioni preservate deliberatamente: inverse in `algebra`/`detail`/`group_theory`, tabelle GEN3/MSC in `kronecker`/`analysis`, tavole di Cayley in `group_theory`/`analysis`, due parser | **da non rimuovere** finché non esiste un oracolo sostitutivo indipendente | G (consolidamento), E (parser) |

Nessun compartimento successivo è stato iniziato: E, B, C, F, G, H, I, J e K
restano intatti.
