# K — Packaging, dipendenze, CI e Release Candidate 4.0.0

**Esito: RELEASE CANDIDATE 4.0.0 — TECNICAMENTE PRONTA PER L'AUDIT FINALE.**
Non è la release 4.0 definitiva: l'audit finale matematico, terminologico e
linguistico resta da eseguire. Nessun push, nessuna pubblicazione, nessun tag.

---

## 1. Stato iniziale

| voce | valore |
|---|---|
| branch | `main` |
| HEAD iniziale | `9e6a0f3` (chiusura K0) |
| origin/main | `54445af`, 139 commit avanti (verificato) |
| working tree | pulito; non tracciati `Articolo.pdf`, `LIBRO_MAIN.pdf`; ignorato `gioco27.spec` |
| baseline | 2333 raccolti · 2331 passati · 1 saltato (N03) · 1 fallito («Tk 9») |
| verifiche d'ingresso | `git status`, baseline matematica 25/25, K0 7/7, `--selftest` TUTTO OK |

## 2. Licenze

**Programma.** `LICENSE` è il testo GPL v3; il README dichiara «GNU General
Public License v3.0». `pyproject.toml` diceva `license = { text =
"Proprietary" }`. La storia Git chiarisce l'autorità: «Proprietary» arriva con
l'importazione della copia 3.1.1 (`337e526`, 2026-09-06); la GPL è stata
aggiunta deliberatamente dopo (`4e2e745` «Add GPL-3.0 license» e `70033be`
«Add license information to README», 2026-09-11). Non c'è ambiguità sulla
licenza: i metadati sono stati allineati a `LICENSE`.

* `license = "GPL-3.0-only"` (espressione SPDX, PEP 639), `license-files =
  ["LICENSE", "gioco27/assets/LICENSE-DejaVu.txt"]`, `setuptools >= 77`;
  nessun classificatore `License ::` (superato da PEP 639).
* *-only* e non *-or-later*: README e LICENSE nominano la versione 3.0 senza la
  clausola «o successive». Allargare a `GPL-3.0-or-later` è una scelta
  dell'autore, registrata per l'audit finale (§ 22).

**Font DejaVu.** `DejaVuSans.ttf` e `DejaVuSans-Bold.ttf` (versione 2.37)
contengono nella tabella OpenType `name` il copyright (nameID 0), il testo
completo della licenza (nameID 13: Bitstream Vera + modifiche DejaVu nel
pubblico dominio + Arev) e l'URL (nameID 14). La licenza richiede che le note
di copyright e il permesso accompagnino ogni copia; consente la
redistribuzione anche dentro un pacchetto più grande, vieta la vendita dei
soli font. Il file mancava: `gioco27/assets/LICENSE-DejaVu.txt` ne è la copia
**letterale estratta dai font stessi** (fonte verificabile nel repository, nulla
ricostruito a memoria); un test confronta il file con i due font.

**Componenti redistribuite** (§ 26): sorgente del programma (GPL-3.0-only),
due font DejaVu (licenza propria, incluso il file). Nella wheel e nella sdist
non ci sono altre componenti di terzi. Il bundle PyInstaller contiene anche
l'interprete Python e le librerie installate nell'ambiente di build (numpy,
reportlab, openpyxl, pypdf, pikepdf, Tcl/Tk): le loro licenze sono quelle che
PyInstaller copia dai pacchetti; il loro elenco definitivo va controllato
sull'artefatto Windows della CI (§ 22).

## 3. DP11 e DP12

Formalizzate in `README.md` e `docs/release/NOTE_VERSIONE_4.0.0.md`:

* **DP11** — Tavola = 216 trasformazioni (H); 1 728 = Procedure, non
  trasformazioni distinte; nessuna Tavola 1 728 nella 4.0.
* **DP12** — i due PDF sono fonti esterne, restano non tracciati, non entrano
  in sdist, wheel o PyInstaller (verificato dai test e da `MANIFEST.in`
  `global-exclude *.pdf`); J può registrarne nome, ruolo e SHA-256. **Non**
  sono stati aggiunti a `.gitignore`.

## 4. Versione

* Unica fonte: `gioco27/__init__.py` → `__version__ = "4.0.0"`.
* `pyproject.toml`: `dynamic = ["version"]`, `[tool.setuptools.dynamic]
  version = { attr = "gioco27.__init__.__version__" }`. *Perché `__init__`*: con
  `attr = "gioco27.__version__"` setuptools cercava il modulo `gioco27` e
  trovava prima il launcher `gioco27.py` della radice (la build falliva). È il
  problema strutturale dimostrato che K0 non poteva vedere; risolto senza
  spostare file.
* Superfici: `python -m gioco27 --version`, `gioco27 --version`,
  `gioco27-cli --version`, titolo della finestra, piè di pagina della Guida,
  `programma.versione` degli esperimenti J, metadati della wheel → tutte 4.0.0
  (test; il titolo della finestra è verificato nello smoke GUI del bundle).
* Esperimenti J salvati con `programma.versione = "3.1.3"`: fixture
  `tests/fixtures/esperimento_j1_programma_3.1.3.json`, **generata dal codice
  3.1.3 prima del cambio di versione** (sei strumenti), si carica VERIFIED
  nella 4.0.0 dal sorgente e dal pacchetto installato; il confronto riporta
  `DIFFERENT_PROGRAM_VERSION` + `SAME_SCIENTIFIC_CONTENT`.

## 5. Dipendenze

| classe | pacchetti | dove |
|---|---|---|
| runtime | `numpy>=1.21` | `dependencies` |
| export (facoltative) | `reportlab>=3.6`, `openpyxl>=3.0`, `pypdf>=3.0`, `pikepdf>=8.0` | extra `export` |
| test | `pytest>=7.0`, `pyflakes>=3.0`, `pypdfium2>=4.0`, `pillow>=9.0`, `tomli>=1.1` (solo Python < 3.11) | extra `test` |
| build | `build>=1.0`, `pyinstaller>=6.0` | extra `build` |
| sviluppo | `gioco27[export,test,build]` | extra `dev` |
| sistema | Tcl/Tk (`tkinter`) | distribuzione Python / pacchetto di sistema, non PyPI |

Un test ricava dall'AST tutti gli import esterni del package e dei test
(incluse le `importorskip`) e verifica che ognuno sia dichiarato e che non
ci siano dipendenze dichiarate e morte. numpy minimo 1.21: la prima con
supporto a Python 3.10.

**Politica dei file requirements** (scritta in testa ai file e nel README):
`pyproject.toml` è la fonte; `requirements.txt` = installazione desktop
completa (runtime + export, equivale a `pip install .[export]`);
`requirements-dev.txt` = `-r requirements.txt` + test + build.

`controlla_requisiti.py`: gruppi Python / Tk / runtime / export e, con
`--dev`, test/build; codice 1 solo per Python troppo vecchio, numpy o tkinter
mancanti; ignora le cartelle omonime nella directory corrente (una `build/`
vuota veniva scambiata per il modulo `build`).

## 6. Python support matrix

`requires-python = ">=3.10"`. Suite completa eseguita file per file sotto xvfb
(1920×1080) su interpreti CPython reali:

| Python | Tk | core | GUI | export | packaging | esito |
|---|---|---|---|---|---|---|
| 3.10.21 | 9.0.4 | ✔ | ✔ | ✔ | ✔ | certificato |
| 3.11.16 | 9.0.4 | ✔ | ✔ | ✔ | ✔ | certificato |
| 3.12.14 | 9.0.4 | ✔ | ✔ | ✔ | ✔ | certificato (ambiente principale) |
| 3.13.15 | 9.0.4 | ✔ | ✔ | ✔ | ✔ | certificato |
| 3.14.7 | 9.0.4 | ✔ | ✔ | ✔ | ✔ | certificato |
| 3.9.25 | 8.6.14 | ✔ | ✔ | ✔ | rifiutato (voluto) | fuori supporto (fine vita 2025-10): tutti i test di core, GUI ed export verdi; falliscono solo i test che verificano il minimo 3.10 (l'installazione della wheel è rifiutata per `Requires-Python`, `controlla_requisiti.py` segnala Python troppo vecchio) |
| 3.12.3 / 3.12.10 | 8.6.12 / 8.6.14 | ✔ | **bloccato** | ✔ | — | BLOCKED BY ENVIRONMENT: queste build standalone abortiscono già in `tkinter.Tk()` sotto xvfb (asserzione xcb), anche senza il programma |

*Motivazione del minimo 3.10*: il codice compila e la suite passa anche su
3.9, ma 3.9 è fuori manutenzione da ottobre 2025 e parte delle dipendenze
(per esempio pikepdf 10) non la supporta più. Supportarla significherebbe
certificare un interprete senza correzioni di sicurezza. È registrato come
cambiamento incompatibile nelle note di versione.

Tk 8.6 è coperto dalla suite completa su 3.9 + Tk 8.6.14 con il codice K: tutti i file GUI verdi (incluso `test_layout_accessibilita_h2.py`, 185/185).

## 7. N03 — pypdfium2

Uso effettivo: **solo test** (`tests/test_layout_dettaglio.py`, rasterizza il
PDF dettagliato per cercare inchiostro fuori margine; `to_pil()` richiede
pillow). Dichiarata nell'extra `test` e in `requirements-dev.txt`, con pillow.
Installata negli ambienti K: il test prima saltato **passa** (8/8) su 3.9,
3.10, 3.11, 3.12, 3.13, 3.14. **N03 chiusa e verificata.**

## 8. N04 — gioco27.spec

La spec è la ricetta PyInstaller ufficiale (README e Guida la citano).

* Versionata: `.gitignore` conserva `*.spec` e riammette solo `!/gioco27.spec`
  (commento con la motivazione); gli altri `.spec` restano ignorati
  (verificato con `git check-ignore`).
* Revisione: percorsi ancorati a `SPECPATH` (nessuna dipendenza dalla cartella
  corrente, nessun percorso personale); launcher `gioco27.py`
  (`freeze_support()` → `gioco27.__main__.main`); `datas` = `gioco27/assets`
  (font + licenza font) e `LICENSE`; `hiddenimports` = i quattro export
  facoltativi (pikepdf mancava); nessun PDF fonte.
* **N04 chiusa.**

## 9. Packaging

Build standard: `python -m build` (sdist, poi wheel dalla sdist), backend
setuptools ≥ 77. Nuovo `MANIFEST.in`: la sdist contiene launcher, spec,
requirements, `conftest.py`, `docs/`, fixture di test; esclude PDF, cache,
`build/`, `dist/`, `.github/`. Entry point: `gioco27` (gui-scripts) e
`gioco27-cli` (console-scripts, `gioco27.cli:main_console`).

`tests/test_pacchetto_k.py` costruisce gli artefatti da una **copia dei soli
file versionati** (`git ls-files`), quindi senza PDF né residui locali.

## 10. Contenuto degli artefatti

Build finale: wheel 1 247 767 byte (87 voci), sdist 1 793 681 byte (211 voci).

* **wheel**: solo `gioco27/` (77 moduli, 2 font, `LICENSE-DejaVu.txt`) e
  `gioco27-4.0.0.dist-info/` con `licenses/LICENSE` e
  `licenses/gioco27/assets/LICENSE-DejaVu.txt`; METADATA 2.4 con
  `License-Expression: GPL-3.0-only`, `Requires-Python: >=3.10`, extra
  corretti; nessun test, PDF, `.pyc`, `__pycache__`, `.git`, percorso assoluto.
* **sdist**: sorgenti, test, fixture, docs, launcher, spec, requirements,
  `MANIFEST.in`, licenze; nessun PDF, cache, build precedente, `.github`.

Controlli automatici in `test_pacchetto_k.py` (e in CI, job packaging).

## 11. Installazione pulita

Per ogni esecuzione: ambiente virtuale nuovo (temporaneo di pytest), solo la
wheel + le dipendenze dichiarate, cartella di lavoro fuori dal checkout,
`PYTHONPATH` rimosso e `PYTHONNOUSERSITE=1`. Verificati: `gioco27.__file__`
dentro l'ambiente e **non** nel checkout; versione; `--selftest`; CLI;
riconoscimento; esperimento J minimale (sequenza → salvataggio → `validate`);
fixture 3.1.3; export CSV con manifest; diagnosi senza export facoltativi;
seconda installazione con `[export]` → CSV, PDF standard/esteso/dettagliato
con font DejaVu registrati, XLSX. 9/9 su 3.10–3.14.

## 12. Selftest

Verde in tutti i modi richiesti: normale, `python -O` (i controlli usano
`VerificaFallita`, non `assert`), da wheel installata, senza GUI (anche da
`gioco27-cli selftest --json`), da cartella arbitraria, dall'eseguibile
PyInstaller Linux. Due `assert` interni restano in `services/laboratorio.py`
(invarianti di costruzione, non controlli del selftest).

## 13. CLI

Riga di comando J invariata nei comandi e nei codici di uscita; aggiunti
`--version` e l'entry point `gioco27-cli`. `python gioco27.py`, `python -m
gioco27`, `gioco27` e `gioco27-cli` convergono su `gioco27.__main__.main` /
`gioco27.cli.main` senza logica duplicata. Nota: su Windows `gioco27` è uno
script GUI (senza console): per la riga di comando si usa `gioco27-cli`.

## 14. CI

`.github/workflows/ci.yml`, quattro job:

* **static-core** (3.10–3.14): installazione `.[export,test]`, diagnostica,
  pyflakes, baseline matematica, selftest normale e `-O`, test K statici;
* **gui-linux** (3.10–3.14): suite completa sotto xvfb, un file per processo,
  il passo fallisce se un file fallisce;
* **packaging**: build, controllo contenuti, `test_pacchetto_k.py`, artefatti
  caricati;
* **windows** (3.12): selftest, CLI, `avvia.bat --selftest`, test senza GUI
  obbligatoria (incluso packaging), build PyInstaller, avvio dell'eseguibile
  tramite codici di uscita, controllo licenze e assenza di PDF.

Nessun `continue-on-error`. **Stato: CI configurata, non ancora eseguita su un
runner reale** (nessun push). La sintassi YAML è stata validata localmente.

## 15. PyInstaller

| livello | Linux (questo ambiente) | Windows |
|---|---|---|
| SPEC VALIDATA STATICAMENTE | ✔ (test) | ✔ (stessa spec) |
| BUILD ESEGUITA | ✔ PyInstaller 6.22.3, CPython 3.12.14 | BLOCKED BY ENVIRONMENT (nessun Windows; job CI configurato) |
| BUILD ESEGUITA E SMOKE VERDE | ✔ | BLOCKED BY ENVIRONMENT |

Smoke Linux, da una cartella temporanea: `--version` 4.0.0; `--selftest`
TUTTO OK; `recognize` e `selftest` della CLI; GUI avviata sotto xvfb, finestra
«Gioco delle 27 carte v4.0.0» presente dopo 12 s, nessun errore; font, licenza
font e `LICENSE` nel bundle; nessun PDF. Bundle 124 MB.

*Nota d'ambiente*: con l'interprete standalone usato qui PyInstaller non
trova `libtcl9.0.so`/`libtcl9tk9.0.so`; la prima build partiva ma la GUI
falliva all'import di tkinter. Esportando `LD_LIBRARY_PATH` sulla `lib/`
dell'interprete la build li risolve (nessun avviso) e la GUI parte. Con i
Python di python.org su Windows il problema non si pone. Non verificati
nell'eseguibile: export PDF e multiprocessing (richiedono interazione con la
GUI); `freeze_support()` è presente nel launcher.

## 16. Export

`tests/test_export_smoke_k.py` (in processo) e `test_pacchetto_k.py` (da
installazione):

| formato | verificato |
|---|---|
| CSV | combinazioni, CSV J + manifest |
| PDF | standard, esteso, dettagliato (font DejaVu registrati) |
| XLSX | analisi (openpyxl) |
| LaTeX | permutazione (libretto), classi di coniugio |
| SVG | frecce (libretto), griglia del coniugio, heatmap di Cayley |
| HTML | protocollo |
| TXT | riepilogo della permutazione (libretto) |
| JSON | esperimento J (salvataggio + verifica) |

**Senza facoltative**: tutto il package si importa (unico modulo che richiede
reportlab già all'import: `core/pdfgrid.py`, caricato solo dagli export PDF) e
il selftest passa. Un export che manca della sua libreria dava «No module
named …» grezzo (e per l'Excel grezzo una falsa «impossibile scrivere il
file»): ora `gui/errori.py` riconosce le quattro librerie facoltative e
mostra un messaggio localizzato con il comando `pip install` (+2 chiavi i18n
per lingua, catalogo 2048). Nessun file parziale resta.

### Terminologia degli export (§ 21 del prompt)

Classificazione delle occorrenze di G/H/G_ext:

| occorrenza | classe | azione |
|---|---|---|
| `export.document.cayley.*`, `export.document.conjugacy.*` (11 chiavi × 2 lingue), `$|G|$`/`$|Z(G)|$` in `export_group_dialog.py` | user-facing | **migrate a H** (`|H| = 216`, `Z(H)`, `[H:…]`, «H ≅ S₃³») |
| `lab.legacy_note`, `glossary.long.group_h`, `glossary.long.gaia`, `guide.s09.extended_group` | user-facing con nota storica esplicita | invariati |
| `appartiene_a_G`, `DECOMPOSIZIONI_PER_TARGET_IN_G`, `appartiene_a_H` (= Γ) | API interne usate dai test | invariati, registrati |
| docstring e commenti (`group_theory`, `kronecker`, `cache`, dialoghi) | internal-only | invariati |
| `G_ext` | — | nessuna occorrenza |
| `guide.part.g` («PARTE G») | non pertinente (lettera di parte) | — |

Nessun formato persistito usa G come chiave. `tests/test_terminologia_export_k.py`
controlla il catalogo (IT/EN) e i LaTeX/SVG generati (fallisce sul testo
precedente, verificato).

## 17. Benchmark

`tests/benchmark_k.py` (non raccolto da pytest): selftest, Tavola 216,
riconoscimento (48 permutazioni, seed 27), catalogo I6 completo, round-trip J
con ricalcolo. Tempi (secondi, fredda / calda min di 3), Linux x86_64 2 CPU:

| misura | 3.10.21 | 3.12.14 | 3.14.7 |
|---|---|---|---|
| selftest | 0,735 / 0,074 | 0,137 / 0,049 | 0,687 / 0,049 |
| Tavola 216 | 0,133 / 0,034 | 0,117 / 0,024 | 0,120 / 0,023 |
| riconoscimento | 0,027 / 0,011 | 0,019 / 0,007 | 0,019 / 0,007 |
| laboratorio I6 | 0,745 / 0,000 | 0,608 / 0,000 | 0,623 / 0,000 |
| esperimento J | 0,035 / 0,004 | 0,034 / 0,003 | 0,032 / 0,003 |

(«calda» 0,000 per I6: risultati in cache nel processo.) Nessuna soglia.

## 18. README e note di release

* `README.md` riscritto per la 4.0 (scopo, H/Γ/S27, livelli, funzioni,
  esperimenti, CLI, requisiti, installazione e politica dei requirements,
  avvio, selftest, fonti esterne, DP11/DP12, build, limiti, licenze); la
  sezione sui limiti degli export è conservata (test D5).
* `docs/release/NOTE_VERSIONE_4.0.0.md`: A–H, I1–I7, J, cambi visibili di K,
  DP11/DP12, compatibilità, cambiamenti incompatibili, limiti noti, benchmark.
* Guida: requisito Python 3.10 e novità della 4.0 nel piè di pagina.

## 19. Suite

Eseguita file per file sotto xvfb (1920×1080), `-B -p no:cacheprovider`.

| | ingresso K | uscita K (3.12.14 / Tk 9.0.4) |
|---|---|---|
| raccolti | 2333 | **2371** |
| passati | 2331 | **2371** |
| saltati | 1 (N03) | **0** |
| falliti | 1 («Tk 9») | **0** |

+38 test K: `test_release_k` 12, `test_pacchetto_k` 9, `test_export_smoke_k`
11, `test_terminologia_export_k` 6. Dentro: baseline matematica 25/25, K0 7/7,
I1–I7 verdi, J 84/84, documentazione D1–D5, architettura J, statica
(pyflakes pulito su package, test e launcher).

**Il «fallimento noto Tk 9» non era legato a Tk 9.**
`test_lo_scorrimento_si_accende_quando_il_testo_cresce` falliva identico con
Tk 8.6.14. Misura: stadio 0 a 1920×1080, contenuto 404 px (scala 1.0), 656
px (2.0), 1012 px (3.0) contro una vista di 818/781/713 px; le barre compaiono
esattamente quando il contenuto supera la vista, con Tk 8.6 e 9. Il test
presumeva che la scala 2.0 bastasse, vero con i font Windows della Guida
(Segoe UI, Consolas), falso con i font di ripiego di Linux. Nessun bug
applicativo: il test ora verifica a ogni scala «barra ⇔ contenuto > vista» e
lo scorrimento alla scala massima (3.0). Nessuna disattivazione.

Altri interpreti (§ 6): 3.10, 3.11, 3.13, 3.14 suite completa verde (l'unico
fallimento intermedio, l'inventario K0 senza i file nuovi di K, è stato
corretto e i file toccati dagli ultimi commit sono stati rieseguiti su ogni
interprete); 3.9 + Tk 8.6.14 verde salvo i test del minimo 3.10.

## 20. Filesystem

* Lavoro nel repository. Ambienti virtuali, artefatti di build, log e bundle
  di prova in `build/k/` (dentro il repository, già ignorato da `build/`),
  **eliminato prima della chiusura**; i test usano `tmp_path` e cartelle
  temporanee automatiche.
* Cache automatiche degli strumenti: interpreti gestiti da uv
  (`~/.local/share/uv`), cache di uv/pip, `~/.gioco27` (effetto normale
  dell'applicazione e dei test). Nessuna lettura di queste aree come dati.
* Pacchetti aggiunti all'ambiente di sviluppo esistente (`build`,
  `pypdfium2`): strumenti, non workspace.
* Nessun file personale, nessuna lista manuale fuori dal repository.
* `Articolo.pdf`, `LIBRO_MAIN.pdf`: non tracciati, non spostati, MD5 invariati
  (`89ad587f…`, `c6fac165…`), assenti da ogni artefatto.
* `gioco27.egg-info/` generata dalle build dalla radice: rimossa.

## 21. Gate

| gate | esito | evidenza |
|---|---|---|
| K-G1 licenza programma coerente | PASS | § 2 |
| K-G2 licenza font verificata | PASS | § 2 (testo estratto dai font, test) |
| K-G3 DP11 documentata | PASS | § 3 |
| K-G4 DP12 documentata | PASS | § 3 |
| K-G5 versione 4.0.0 unica | PASS | § 4 |
| K-G6 J 3.1.3 compatibile | PASS | § 4 (fixture reale 3.1.3) |
| K-G7 N03 risolta | PASS | § 7 (skip scomparso) |
| K-G8 N04 risolta | PASS | § 8 |
| K-G9 dipendenze coerenti | PASS | § 5 |
| K-G10 support matrix Python esplicita | PASS | § 6 |
| K-G11 wheel build | PASS | § 9–10 |
| K-G12 sdist build | PASS | § 9–10 |
| K-G13 artefatti ispezionati | PASS | § 10 |
| K-G14 PDF esclusi | PASS | § 3, § 10, § 15 |
| K-G15 licenze necessarie incluse | PASS | § 2, § 10, § 15 (bundle Windows: vedi K-G24) |
| K-G16 installazione pulita | PASS | § 11 |
| K-G17 selftest pulito | PASS | § 12 |
| K-G18 CLI pulita | PASS | § 11, § 13 |
| K-G19 cwd independence | PASS | § 11, § 15 |
| K-G20 CI configurata | PASS (configurata, non eseguita) | § 14 |
| K-G21 export smoke | PASS | § 16 |
| K-G22 H/Γ export coerenti | PASS | § 16 |
| K-G23 spec PyInstaller valida | PASS | § 8, § 15 |
| K-G24 build PyInstaller verificata se ambiente disponibile | PASS (Linux) · BLOCKED BY ENVIRONMENT (Windows) | § 15 |
| K-G25 README 4.0 | PASS | § 18 |
| K-G26 note release 4.0 | PASS | § 18 |
| K-G27 benchmark | PASS | § 17 |
| K-G28 baseline matematica verde | PASS | § 19 |
| K-G29 K0 verde | PASS | § 19 |
| K-G30 I1–I7 verdi | PASS | § 19 |
| K-G31 J verde | PASS | § 19 |
| K-G32 nessuna nuova regressione | PASS | § 19 |
| K-G33 filesystem conforme | PASS | § 20 |
| K-G34 nessun push | PASS | § 24 |
| K-G35 audit finale ancora non eseguito | PASS (non eseguito, come richiesto) | — |

## 22. Debiti e blocker

**Nessun blocker di distribuzione.** Restano:

1. **Audit finale** matematico, terminologico e linguistico (obbligatorio
   prima della 4.0 definitiva).
2. **CI** mai eseguita su un runner reale; primo run da osservare al primo
   push (build Windows, `avvia.bat`, eseguibile).
3. **Build PyInstaller Windows** non verificata localmente; elenco delle
   licenze di terze parti nel bundle da controllare sull'artefatto.
4. Scelta dell'autore fra `GPL-3.0-only` (adottata, letterale) e
   `GPL-3.0-or-later`.
5. Identificatori interni legacy G/H (`appartiene_a_H` indica Γ): non visibili,
   da decidere nell'audit (rinomina con alias o solo documentazione).
6. Debiti J invariati: nessun `fsync` in `atomic_write`; nessuna conferma alla
   chiusura con sessione non salvata.
7. Export PDF e multiprocessing dentro l'eseguibile non verificati
   automaticamente.
8. Le build standalone 3.12.3/3.12.10 con Tk 8.6 abortiscono sotto xvfb
   (ambiente): Tk 8.6 resta coperto da 3.9 + Tk 8.6.14.

## 23. Commit

| commit | messaggio |
|---|---|
| `19f338b` | build(K): align licensing, dependencies and 4.0.0 metadata |
| `98d2851` | build(K): version the PyInstaller recipe and harden the Windows launcher |
| `e858906` | fix(K): name the group of 216 H in the Cayley and conjugacy exports |
| `9db3e91` | test(K): make the overflow test independent of Windows font metrics |
| `1f0b24a` | feat(K): say which optional export library is missing |
| `37ac633` | build(K): make sdist and wheel build from a clean checkout |
| `49b571a` | test(K): verify release metadata, artifacts and clean installation |
| `68843fd` | test(K): expect the registered DejaVu alias in the installed export smoke |
| `88a6c5f` | test(K): treat tomllib as standard library on Python 3.10 |
| `532734a` | ci(K): add static, GUI, packaging and Windows workflows |
| `9d2e4dc` | docs(K): prepare the 4.0.0 release candidate |
| (questo) | docs(K): close technical release compartment |

## 24. Git status

Branch `main`; working tree pulito salvo `Articolo.pdf` e `LIBRO_MAIN.pdf`
non tracciati (fonti esterne, DP12); `gioco27.spec` ora tracciato; nessun
file ignorato residuo nel repository (`build/`, `gioco27.egg-info/` rimossi);
151 commit avanti rispetto a `origin/main` (`54445af`) dopo questo commit;
nessun push, nessun tag.

**AUDIT FINALE MATEMATICO, TERMINOLOGICO E LINGUISTICO: ANCORA DA ESEGUIRE.**
