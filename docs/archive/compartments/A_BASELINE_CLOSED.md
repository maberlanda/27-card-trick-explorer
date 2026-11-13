# A_BASELINE_CLOSED — chiusura del compartimento A

Registro dell'intervento **A2 — Chiusura della baseline**.
Il quadro tecnico completo resta in `GIT_BASELINE_AND_RECONCILIATION.md`, che questo
documento non duplica: qui c'e' solo ciò che A2 ha cambiato e come è stato verificato.

## 1. Commit iniziale

| Voce | Valore |
|---|---|
| Commit di partenza | `54445af9c5e499523986a227c0bb7dba32ded763` — «Prepara release 3.1.3» |
| Branch | `main`, allineato a `origin/main` |
| Working tree all'avvio | pulito; unico file non tracciato: `GIT_BASELINE_AND_RECONCILIATION.md` (deliverable di A0/A1, conservato) |
| Modifiche preesistenti dell'utente | nessuna |
| Stash | nessuno |

## 2. Interventi eseguiti

1. **N01** — chiusura dei due warning pyflakes che rendevano rossa la suite statica.
2. **N05** — rimozione degli artefatti runtime locali (`__pycache__/`, `*.pyc`, `.pytest_cache/`),
   più un `.git/index.lock` vuoto e abbandonato che bloccava ogni comando git di scrittura.
3. **Baseline matematica** resa riproducibile dal repository come test pytest.
4. **Confine architetturale**: il catalogo i18n esce dal package GUI.
5. **Documentazione**: questo registro; `GIT_BASELINE_AND_RECONCILIATION.md` portato sotto
   controllo di versione.

Non è stato corretto alcun bug B01–B12, non è stata aggiunta alcuna funzionalità, non è stato
avviato alcun refactoring ulteriore, non è stato iniziato il compartimento D.

## 3. N01 — soluzione

| File | Warning | Intervento |
|---|---|---|
| `gioco27/gui/export_dialog.py:244` | `f-string is missing placeholders` | I due literal del blocco `\multicolumn` non contengono segnaposto: tolto il prefisso `f` e riportate le graffe da doppie a singole |
| `gioco27/gui/onboarding_tab.py:12` | `'.glossary.ONBOARD_INTRO' imported but unused` | Rimosso il solo nome inutilizzato dall'import; `GLOSSARY` e `ONBOARD_STEPS` restano |

La stringa LaTeX prodotta è **identica carattere per carattere** prima e dopo (verificata su tre
input, compreso quello vuoto):

```text
  \multicolumn{4}{c}{\emph{<testo tradotto>}}} \\
```

Nessuna pulizia collaterale negli stessi file, nessuna rinomina, nessuna whitelist, nessuna
modifica al test: `tests/test_static.py` è invariato e pyflakes non è stato disabilitato.

## 4. N05 — trattamento

Prima di cancellare: `git ls-files | grep -E "__pycache__|\.pyc$|\.pytest_cache"` → **0 file
tracciati**; `git check-ignore -v` conferma che tutti rientrano in `.gitignore:2` e `:51`.

| Elemento | Prima | Dopo |
|---|---:|---:|
| File `.pyc` | 75 | 0 |
| Directory `__pycache__/` | 5 | 0 |
| `.pytest_cache/` | presente | rimossa |

La rimozione ha usato `find . -path ./.git -prune -o …`, quindi **non ha attraversato `.git/` né
alcuna directory esterna al repository**; i percorsi della vecchia copia incorporati nei `.pyc`
non sono stati seguiti né cercati. Dopo la pulizia `git ls-files --deleted` restituisce **0**:
nessun file versionato è stato toccato.

In più è stato rimosso `.git/index.lock`: file di **0 byte**, fermo dalle 16:12 UTC, senza alcun
processo git attivo. Bloccava `git mv`, `git add` e `git commit` (è la rimozione manuale che git
stesso suggerisce nel messaggio d'errore). L'indice e la storia non sono stati toccati.

## 5. Baseline matematica resa riproducibile

Nuovo file **`tests/test_baseline_matematica.py`** — 25 test, **1,9 s**, dentro la suite ordinaria.
Nessuna opzione, nessun marcatore, nessun comando speciale: i due controlli più costosi (le
419.904 coppie di H e le 419.904 composizioni canoniche) costano insieme ~1,5 s e non meritavano
una selezione separata.

```text
pytest                                      # li esegue con tutto il resto
pytest tests/test_baseline_matematica.py    # solo la baseline
```

Convenzioni e domini protetti: `T[carta] = destinazione`; `deck[posizione] = carta`;
`M[T[i], i] = 1`; `(a∘b)[i] = a[b[i]]`; `M(a∘b) = M(a) @ M(b)`;
`MSC(n) = 9·(n mod 3) + ⌊n/3⌋`; `MSC³ = I`; S3 con i nomi GEN3 e `{I_3, R_U}`;
G con 216 elementi, chiusura e tavola di Cayley su **46.656** coppie, identità, inversi,
associatività; H con 648 elementi e chiusura su **419.904** coppie; intreccio
`MSC ∘ (a⊗b⊗c) = (c⊗a⊗b) ∘ MSC`; **1.728** configurazioni di stadio; **729** coppie
carta/bersaglio; tavola dei 216 con bigezione degli assi e statistiche del capitolo 100;
**46.656** decomposizioni per un bersaglio in G e zero fuori da G; forma canonica `K ∘ MSCᵏ`
con la legge di composizione verificata su tutte le coppie.

Vincoli rispettati, dichiarati nel docstring del file:

* l'oracolo fisico `simula_fisicamente` è **riscritto dalla descrizione del gioco** e non chiama
  `distribuisci` / `raccogli` / `esegui_partita`;
* è scritto esplicitamente che il confronto interno vettoriale ↔ matriciale **non** è un confronto
  fra oracoli indipendenti, e che l'oracolo fisico lo affianca senza sostituirlo;
* le implementazioni matematiche duplicate (inverse, tabelle GEN3/MSC, tavole di Cayley) **non**
  sono state unificate: restano oracoli reciproci;
* nessun comportamento di B01–B12 viene congelato come corretto — in particolare non si testa
  `validate_decompositions` con elenco vuoto (B08).

Gli script diagnostici di A0/A1 **non** sono stati importati in blocco: nel repository è entrata
solo la rete di sicurezza matematica.

## 6. Nuova collocazione e contratto i18n

```text
prima:   gioco27/core/{algebra,combinations,detail_pdf,gioco_reale}.py ──> gioco27/gui/i18n.py
dopo:    gioco27/core/{…}.py ──> gioco27/i18n.py  <── gioco27/gui/i18n.py (adattatore)
```

* **Proprietario:** `gioco27/i18n.py`. È il file precedente spostato senza modifiche:
  SHA-256 di `HEAD~1:gioco27/gui/i18n.py` e di `HEAD:gioco27/i18n.py` coincidono
  (`e7afa5ef906c5720…`).
* **Adattatore:** `gioco27/gui/i18n.py`, 27 righe, nessun dato. Ri-esporta `CATALOGS`,
  `tr`, `set_language`, `get_language` e delega ogni altro nome al proprietario con
  `__getattr__`, così che anche lo stato interno (`_language`) resti uno solo.
* **Contratto invariato:** 1.288 chiavi italiane e 1.288 inglesi, stessi testi, stesso fallback
  EN→IT, lingua predefinita `it`. `from .i18n import tr` nella GUI e
  `from gioco27.gui.i18n import CATALOGS, set_language` nei test continuano a funzionare senza
  alcuna modifica: 21 moduli GUI passano ancora dall'adattatore.
* **Nessun ciclo nascosto:** l'adattatore importa il proprietario, mai il contrario; il
  proprietario non importa nulla del package.

Non è stata toccata la presentation layer nel suo insieme, non sono stati modificati i messaggi,
non è stato riscritto il sistema i18n né il fallback.

## 7. Risultati della suite

Ambiente di riferimento (lo stesso di `GIT_BASELINE_AND_RECONCILIATION.md` § 6.1): Linux,
**Python 3.12.3**, tkinter 8.6 con Xvfb, NumPy 2.5.3, ReportLab 5.0.1, openpyxl 3.1.5,
pypdf 6.18.1, pikepdf 10.13.0, pytest 9.1.1, pyflakes 3.4.0.

```text
PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m pytest -p no:cacheprovider -ra -q
```

| Voce | Prima di A2 | Dopo A2 |
|---|---:|---:|
| Raccolti | 678 | **703** |
| Passati | 676 | **702** |
| Falliti | **1** | **0** |
| Saltati | 1 | 1 |
| Durata | 78,9 s | **76,0 s** |

**Unico skip residuo:** `tests/test_layout_dettaglio.py:73` —
`could not import 'pypdfium2'`. È la dipendenza di test non dichiarata registrata come **N03**:
appartiene al compartimento K e non è stata toccata qui.

Test statici richiesti, eseguiti singolarmente: `test_no_undefined_names` e
`test_no_pyflakes_warnings` → **2 passed**. `python3 -m pyflakes gioco27 tests conftest.py
controlla_requisiti.py gioco27.py` → nessun warning.

## 8. Controlli matematici

* `tests/test_baseline_matematica.py` → **25 passed in 1,93 s**.
* La baseline esterna di A0/A1 (32 controlli esaustivi, script indipendente dal repository) è
  stata rieseguita sul codice di A2: **32 controlli, 32 superati, 0 falliti** — esito identico a
  prima di A2. Matematica invariata, zero regressioni.

## 9. Controllo import `core → gui`

Analisi AST di tutti i moduli del package:

```text
import core -> gui: 0
moduli core che usano i18n: algebra.py, combinations.py, detail_pdf.py, gioco_reale.py
   (tutti verso il nuovo proprietario gioco27/i18n.py)
moduli che importano ancora gioco27/gui/i18n: 21, tutti dentro gioco27/gui/
```

Ricerca testuale di conferma: nel package non resta alcun `from ..gui.i18n import` né
`from gioco27.gui import i18n`; l'unica occorrenza della stringa `gioco27.gui.i18n` è nel
docstring dell'adattatore.

## 10. File modificati

| File | Categoria | Nota |
|---|---|---|
| `gioco27/gui/export_dialog.py` | **N01** | 3 righe |
| `gioco27/gui/onboarding_tab.py` | **N01** | 1 riga |
| `tests/test_baseline_matematica.py` | **baseline test** | nuovo, 340 righe |
| `gioco27/i18n.py` | **i18n boundary** | nuovo percorso del catalogo, contenuto invariato |
| `gioco27/gui/i18n.py` | **i18n boundary** | da 2.659 righe di catalogo a 27 righe di adattatore |
| `gioco27/core/algebra.py` | **i18n boundary** | 1 riga di import |
| `gioco27/core/combinations.py` | **i18n boundary** | 1 riga di import |
| `gioco27/core/detail_pdf.py` | **i18n boundary** | 1 riga di import |
| `gioco27/core/gioco_reale.py` | **i18n boundary** | 1 riga di import |
| `GIT_BASELINE_AND_RECONCILIATION.md` | **documentazione A** | portato sotto controllo di versione |
| `A_BASELINE_CLOSED.md` | **documentazione A** | questo file |

Nessun altro file è stato modificato. `conftest.py`, `pyproject.toml`, `requirements.txt`,
`requirements-dev.txt` e `.gitignore` sono **invariati**. Fuori dal versionamento sono stati
rimossi solo gli artefatti runtime della § 4.

## 11. Commit creati (solo locali, nessun push)

| Commit | Messaggio | Contenuto |
|---|---|---|
| `28283e5` | `fix(A): restore clean static baseline` | i due file di N01 |
| `12d343d` | `test(A): make mathematical baseline reproducible` | `tests/test_baseline_matematica.py` |
| `36d6b87` | `refactor(A): decouple core from gui i18n` | nuovo proprietario, adattatore, 4 import di core |
| (quarto) | `docs(A): record closed baseline` | `GIT_BASELINE_AND_RECONCILIATION.md`, `A_BASELINE_CLOSED.md` |

Categorie non mescolate; nessuna modifica preesistente dell'utente è stata inclusa (non ce
n'erano). `origin/main` è rimasto intatto: **nessun push**.

## 12. `git status` finale

```text
On branch main
Your branch is ahead of 'origin/main' by 4 commits.
nothing to commit, working tree clean
```

## 13. Gate di uscita

| Gate | Esito |
|---|---|
| A-G1 suite completa verde nell'ambiente di riferimento | **OK** — 702 passati, 1 saltato (pypdfium2), 0 falliti |
| A-G2 pyflakes verde | **OK** — `test_no_pyflakes_warnings` e `test_no_undefined_names` passano |
| A-G3 baseline matematica invariata | **OK** — 32/32 come prima di A2 |
| A-G4 baseline riproducibile dal repository | **OK** — `pytest tests/test_baseline_matematica.py` |
| A-G5 nessun import `core → gui` | **OK** — 0, verificato con AST |
| A-G6 nessun B01–B12 corretto accidentalmente | **OK** — tutti e dodici ancora riproducibili dopo A2 |
| A-G7 nessuna modifica funzionale non autorizzata | **OK** — output LaTeX identico, catalogo identico, 703 test a conferma |
| A-G8 working tree comprensibile, ogni modifica attribuita | **OK** — § 10 |
| A-G9 nessun push | **OK** |

**Il compartimento A è chiuso.**

## 14. Debiti ancora aperti

| Voce | Stato | Proprietario previsto |
|---|---|---|
| **B01–B12** | tutti e dodici **presenti**, nessuno corretto; input di riproduzione, comportamento attuale e comportamento atteso restano in `GIT_BASELINE_AND_RECONCILIATION.md` § 4 | B, C, D, E, F secondo la § 11 di quel documento |
| **R01, R02, R03, R05, R07, M01, M03, M05** | presenti | B, C, H |
| **R04** | presente e **più grave di quanto scritto nell'audit**: `orbit_of([1,1], 0)` non termina | D |
| **R06** | presente: sole versioni minime, nessun lock, nessuna CI | K |
| **M02** | prima parte presente (numerazione base 1 nelle docstring); la seconda parte (rotazione «inesatta») **non è confermata**: le regole sono verificate corrette | D |
| **M04, M06** | presenti | H |
| **N03** — `pypdfium2` usata da `tests/test_layout_dettaglio.py` e non dichiarata in alcun file | **aperto per decisione**: non toccato in A2, è la causa dell'unico skip della suite | K |
| **N04** — `gioco27.spec` escluso dal versionamento da `.gitignore:33` (`*.spec`): la build non è riproducibile dal solo repository | **aperto per decisione**: non toccato in A2 | K |
| **N06** — `tests/test_decomposition_integrita.py::test_b11_cache_json_v2_valida_accettata[results0]` congela B08 come specifica | aperto: la correzione di B08 richiederà una modifica dichiarata di quel test | B/F |
| **N02** — due funzioni Tk in `gioco27/core/permutations.py` | aperto | D |
| Ramo morto in `gioco27/core/kronecker.py` dopo il `return` incondizionato | aperto | F |

`requirements*.txt` e `.gitignore` non sono stati toccati in A2 proprio perché N03 e N04
appartengono a K: risolverli qui avrebbe ampliato il perimetro senza necessità per la baseline.

## 15. Prossimo passo (non avviato)

Con A chiuso, il repository è pronto per **D — Dominio matematico** (nessun file condiviso con
B o C) e, in parallelo fra loro, per **B** e **C**, con le due avvertenze di co-locazione della
§ 12 di `GIT_BASELINE_AND_RECONCILIATION.md`. Nessuno di questi compartimenti è stato iniziato.
