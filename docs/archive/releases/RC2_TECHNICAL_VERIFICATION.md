# Verifica tecnica finale — fase locale pre-RC2

Verifica iniziata il 28 settembre 2026 e conclusa il 29 settembre 2026 sul
progetto Gioco delle 27 carte 4.0.0.

## 1. Stato iniziale e perimetro

La verifica è iniziata sul ramo `main`, con HEAD
`dbcde4753e26db6c522bed29bcf053bf7ff06a07` e `origin/main` fermo a
`6e77210f31e467f0915e3cca0af4c9ef39328e44`. Il ramo locale era avanti di 26
commit e tutti i file tracciati erano puliti.

PDF invariati e non tracciati.

La fase ha riguardato esclusivamente controlli tecnici locali: ambiente,
analisi statica, suite, packaging, installazione dal wheel, PyInstaller,
export, persistenza, dipendenze architetturali e stato del repository. Non
sono stati ripetuti gli audit A1–A5, non è stato eseguito alcun push e non
sono stati creati tag o documenti relativi al libro.

## 2. Ambiente

- sistema operativo: Windows 10, build `10.0.26200`, 64 bit;
- Python: CPython 3.10.11, 64 bit;
- Tcl/Tk dichiarato dall'interprete: 8.6;
- NumPy 1.24.2, pytest 9.1.1, reportlab 4.4.10, openpyxl 3.1.5,
  pypdf 6.12.2;
- nell'ambiente temporaneo di verifica sono stati installati soltanto gli
  extra dichiarati mancanti: pyflakes 4.0.0, pikepdf 10.13.0.post1,
  pypdfium2 5.13.0, build 1.6.1 e PyInstaller 6.22.3;
- Pillow è stato portato a 12.3.0 nell'ambiente temporaneo come dipendenza di
  pikepdf; setuptools 84.0.0 è stato usato come backend dichiarato dalla
  build.

`controlla_requisiti.py --dev` ha confermato che nell'ambiente temporaneo non
mancava alcuna dipendenza dichiarata.

La creazione di una finestra Tk fallisce prima del codice del progetto:
l'installazione locale di Python non trova un `init.tcl` utilizzabile. Non è
stato costruito artificialmente un display alternativo.

## 3. Controlli statici

`pyflakes` è stato eseguito su `gioco27`, `tests`, `gioco27.py`,
`controlla_requisiti.py` e `conftest.py` senza segnalazioni. Non risultano
altri analizzatori statici configurati ufficialmente nel progetto.

`git diff --check` è superato.

## 4. Suite completa

La prima esecuzione completa ha prodotto:

```text
2109 superati, 307 esclusi, 1 fallito, 9 errori
```

Le 307 esclusioni sono tutte motivate dall'indisponibilità del display Tk.
I nove errori provenivano da un'unica fixture di packaging: il certificato
locale impediva al build isolato di scaricare `setuptools>=77`. Non erano
errori del progetto. Il fallimento reale era l'inventario K0, che non
classificava ancora i due documenti A5.

Dopo la correzione tecnica e l'aggiornamento dell'inventario, la seconda e
ultima esecuzione completa ammessa ha prodotto:

```text
2218 superati, 2 esclusi, 9 falliti, 198 errori
```

Questa seconda esecuzione, autorizzata alla rete per il build isolato, ha
esposto anche un display parziale. I test GUI sono quindi entrati invece di
essere esclusi, ma l'installazione Tk incompleta non regge una suite
monolitica: 198 errori derivano soprattutto dal riuso fra file diversi di
font legati a un'applicazione Tk già distrutta. Il workflow CI evita
esplicitamente questo caso eseguendo ogni file GUI in un processo separato.

I nove fallimenti hanno permesso di individuare aspettative GUI anteriori
alle formulazioni già validate da A2–A4. Sono state aggiornate soltanto le
aspettative: notazione con pedici, `MSC` al posto del vecchio `R`, “riga di
ritorno”, sentence case e separatori numerici dipendenti dalla lingua. I
controlli direttamente coinvolti, rilanciati in processi separati, hanno dato
7 superati e 2 esclusi per l'indisponibilità intermittente del display.

Non è stata eseguita una terza suite completa. Restano non certificabili
localmente l'apertura da tastiera di un menu Tk e la creazione di una seconda
applicazione nella stessa sessione: il secondo caso fallisce esplicitamente
per il file `icons.tcl` mancante nell'installazione Python locale.

## 5. Packaging 4.0.0

Il sistema dichiarato `setuptools.build_meta` ha costruito entrambi gli
artefatti. Poiché il bootstrap isolato restava bloccato dal certificato locale,
la build diretta ha riutilizzato nell'ambiente temporaneo `setuptools>=77`
con `python -m build --no-isolation`. Il test ufficiale di packaging ha poi
ripetuto con successo la build isolata in un processo autorizzato alla rete:
9 test superati.

Artefatti verificati:

- `gioco27-4.0.0-py3-none-any.whl`, 1 254 718 byte, SHA-256
  `44FCA8C6353A7FE85A65181F15883C11DD26434136A798A0EF07BA46B85BBDD4`;
- `gioco27-4.0.0.tar.gz`, 1 907 715 byte, SHA-256
  `531622BA428915C12783A4BA0A0EA6B4DCBA094745B7AC08B5F8DEA4C8321A37`.

I metadata dichiarano versione 4.0.0, `Requires-Python: >=3.10`, dipendenza
runtime `numpy>=1.21`, extra `export`, `test`, `build` e `dev`, e licenza
`GPL-3.0-only`. La matrice CI copre Python 3.10, 3.11, 3.12, 3.13 e 3.14.

La wheel contiene i due font DejaVu, la loro licenza e la GPL. La sdist
contiene inoltre README, `pyproject.toml`, `gioco27.spec` e i file necessari
allo sviluppo. Nessuno dei due archivi contiene PDF sorgente, bytecode o
cache.

## 6. Installazione pulita

Un ambiente isolato interno al repository ha installato il wheel appena
costruito, non il sorgente, insieme a NumPy 2.2.6. L'import ha risolto
`gioco27` dalla `site-packages` dell'ambiente pulito e ha restituito la
versione 4.0.0.

Sono riusciti:

- `python -m gioco27 --version`;
- l'help della CLI;
- il selftest normale;
- il selftest con ottimizzazione `-O`;
- `gioco27-cli selftest --json`;
- la validazione del fixture storico prodotto dalla versione 3.1.3, con
  esito `VERIFIED`.

## 7. PyInstaller

La build con `gioco27.spec` è riuscita. Il bundle contiene l'eseguibile, i
cataloghi incorporati nel package, i due font DejaVu, la licenza DejaVu e la
GPL; non contiene PDF sorgente.

La prima build ha rivelato un problema tecnico reale: con `console=False`,
`--version` tentava di scrivere su `sys.stdout = None` e apriva una finestra
di eccezione. La CLI ora gestisce direttamente l'opzione radice e una
regressione simula l'assenza di stdout. Dopo la ricostruzione:

- `Gioco27.exe --version`: codice 0;
- `Gioco27.exe --selftest`: codice 0;
- `Gioco27.exe selftest`: codice 0.

La build locale ha escluso Tk perché l'installazione Tcl/Tk dell'interprete è
incompleta. L'avvio GUI completo dell'eseguibile non è quindi certificabile
su questa macchina; resta demandato alla CI Windows.

## 8. Export

Gli 11 smoke test ufficiali degli export sono superati. Hanno esercitato in
modo rappresentativo TXT, HTML, LaTeX, SVG, PDF standard, PDF esteso, PDF
dettagliato, XLSX, CSV e JSON. I file prodotti nei test erano non vuoti e
riconoscibili dai relativi lettori; CSV e JSON conservano schema e
identificatori stabili.

Non è stato ripetuto alcun audit linguistico e tutti gli output temporanei
sono stati rimossi con le rispettive directory di test.

## 9. Persistenza e architettura

I contratti restano:

- `schema = gioco27.esperimento`;
- `schema_version = 1`;
- `convention_version = J1`.

Il fixture storico 3.1.3 è stato verificato sia dal package installato sia
dal test di release. I dieci test mirati su dipendenze, persistenza e
architettura sono superati.

`core.permutations` non dipende da i18n. Non sono state introdotte nuove
dipendenze inverse evidenti fra core, localizzazione, GUI ed export.

## 10. Repository e release

Sono stati controllati `.gitignore`, `gioco27.spec`, il workflow CI,
`pyproject.toml`, README, note 4.0.0 e inventario K0. Il workflow conserva:

- controlli statici/core su Python 3.10–3.14;
- suite GUI Linux sotto Xvfb su Python 3.10–3.14;
- packaging e installazione pulita;
- Windows 3.12 con PyInstaller.

L'inventario K0 è stato aggiornato con i due documenti A5 e con questo
verbale. Ambienti virtuali, directory di build, archivi, bundle, cache e altri
artefatti locali di collaudo vengono rimossi prima della chiusura.

Il controllo mirato di struttura e release ha dato 19 test superati. Il test
ufficiale di packaging ha dato 9 test superati. Non sono entrati nel
repository ambienti, PDF sorgente o artefatti di build.

## 11. Verifiche non eseguibili localmente

- suite GUI: non eseguibile per installazione Tcl/Tk locale incompleta;
- avvio GUI completo del bundle PyInstaller: non certificabile per la stessa
  causa;
- due controlli d'interazione GUI (menu da tastiera e seconda istanza Tk):
  non certificabili localmente per l'installazione Tk incompleta;
- copertura Linux e Python 3.11–3.14: demandata alla matrice CI;
- CI remota sul commit corrente: non eseguita, perché in questa fase non è
  consentito il push.

## 12. Stato conclusivo

Il problema `--version` del bundle è stato corretto nel commit tecnico
separato `dfd58c1`. Le aspettative GUI rimaste sulle vecchie formulazioni
sono state aggiornate nel commit test separato `261a9e3`. Non sono stati
modificati matematica, terminologia consolidata, italiano, inglese, schema o
comportamento scientifico.

La verifica locale non dichiara RC2 completamente certificata fino
all'esecuzione della CI remota sul commit corrente.

**Stato al termine della fase locale: CI REMOTA PENDING.**

## 13. Pubblicazione RC2

La CI remota conclusiva sul commit
`4aa4c90affb6d83e412541256d41ed905fb6a478` è terminata con esito
**SUCCESS** nel workflow `ci`, esecuzione `36526585493`. Il commit è quindi
quello certificato per RC2.

La verifica remota ha coperto:

- analisi statica, baseline matematica, selftest e test K su Python
  3.10, 3.11, 3.12, 3.13 e 3.14;
- suite completa GUI, un file per processo, su Linux/Xvfb e sulle stesse
  cinque versioni di Python;
- sdist, wheel e installazione pulita su Linux con Python 3.12;
- Windows con Python 3.12, launcher, test non GUI, PyInstaller, selftest e
  avvio del bundle.

La CI ha richiesto due correzioni circoscritte:

- il test Windows delle dipendenze facoltative ora fissa esplicitamente il
  protocollo UTF-8 fra processo figlio e processo padre (`abcf361`);
- l'Explorer rientra nei 1 242 px utili del runner a 1280×720 mediante margini
  e linguette piu' compatti (`e6589f9`, diagnostica `977a0d2`, correzione
  misurata `4aa4c90`). I pannelli Matrice sono stati ripristinati nelle loro
  dimensioni originali.

Non sono state modificate matematica, terminologia consolidata, schemi,
identificatori tecnici o comportamento scientifico.

Il tag annotato `v4.0.0-rc2` ha oggetto
`b6b6ed384477d134a9462d7d00a401fc9ab99097` e risolve al commit certificato
`4aa4c90affb6d83e412541256d41ed905fb6a478`. Il tag storico
`v4.0.0-rc1` resta invariato e risolve a
`6e77210f31e467f0915e3cca0af4c9ef39328e44`.

Questa sezione è registrata in un commit documentale successivo alla
pubblicazione: il tag RC2 non viene spostato e identifica il commit della
release candidate effettivamente verificato dalla CI.
