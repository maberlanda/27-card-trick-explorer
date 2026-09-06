# Gioco delle 27 carte — note della versione 3.1.1

> **3.1.0** — numero minore incrementato rispetto alla 3.0.x perché la
> numerazione a base 0 **rompe la compatibilità**: cambiano le intestazioni del
> CSV e le vecchie chiavi dei filtri vengono rifiutate con un errore esplicito.
>
> **3.1.1** — documentata la convenzione sui nomi doppi (nessun cambiamento di
> comportamento) e aggiunto l'annullamento degli export.
>
> Punto di partenza: **3.0.1** (82 test). Arrivo: **3.1.1** (218 test).

Revisione di robustezza e prestazioni. **Nessun cambiamento di risultati**:
CSV identico byte per byte, PDF visivamente identico, `--selftest` invariato.

## 1. Correzioni di robustezza

### Export massivi: esaurimento memoria con i filtri di default (grave)

Con i filtri appena aperti (tutto su `*`) le combinazioni sono
**1728³ = 5.159.780.352**. Le quattro funzioni di export parallelo
cominciavano con:

```python
all_params = list(iter_combinations_ex(filters))
```

cioè provavano a costruire in RAM una lista di cinque miliardi di tuple. Il
processo moriva prima di scrivere un byte. L'export CSV era il più esposto:
non aveva **nessuna** finestra di conferma, quindi bastava un clic su
«CSV» a finestra appena aperta.

Correzioni:

* nuovo modulo `core/parallel.py`: la generazione resta un **flusso**
  (`chunked` + `imap_ordered` con finestra limitata di task in volo), quindi
  la memoria non dipende più dal totale;
* limite di sicurezza `MAX_EXPORT_ITEMS = 20.000.000` con eccezione
  `ExportTooLarge` e messaggio che spiega come restringere i filtri;
* il PDF dettagliato ha un limite più basso (`MAX_DETAIL_COMBOS = 200.000`)
  perché deve tenere tutte le combinazioni in RAM per l'«Elenco matrici
  trasposte»: è un vincolo del formato, ora documentato invece che implicito;
* il controllo avviene **prima** di aprire il file di destinazione: un export
  rifiutato non lascia più un CSV con la sola intestazione;
* l'export CSV ha ora una conferma sopra 100.000 righe.

### GUI

* **Export concorrenti**: i pulsanti non erano protetti, due export avviati
  insieme si rubavano la progress bar e lanciavano 2×N processi. Aggiunto un
  flag `_export_busy`, rilasciato anche in caso di errore.
* **`after()` su finestra chiusa**: chiudere la finestra durante un export
  faceva sollevare `TclError` dentro il thread di lavoro. Aggiunti
  `App._ui()` e `common.ui_call()` che ignorano il caso.
* **Thread nudi nei dialoghi**: `CayleyDialog` e `ConjugacyDialog` avviavano
  `threading.Thread` senza gestione errori: un fallimento lasciava la finestra
  bloccata su «Calcolo in corso…» per sempre. Ora usano `run_in_thread`.
* **`assert` in codice di produzione**: `conjugacy_dialog.py` verificava la
  coerenza teoria/calcolo con un `assert`, che `python -O` rimuove — proprio
  nella configurazione in cui l'errore passerebbe inosservato. Sostituito con
  un controllo esplicito che registra nel log e marca la classe con «⚠».

### Cache su disco: da `pickle` a JSON

`cache.py` usava `pickle.load` su file letti da `~/.gioco27/cache/`.
`pickle` può eseguire codice arbitrario in deserializzazione: un file
modificato diventava un vettore di esecuzione. I dati sono solo liste di nomi
GEN3, quindi ora il formato è JSON (`CACHE_FORMAT_VERSION = 2`), scritto in
modo atomico, ispezionabile a mano, con file corrotti ignorati senza
eccezioni. Aggiunto un tetto complessivo di 200 MB (`prune()`): prima esisteva
solo il limite d'età di 30 giorni e la cartella poteva crescere senza limite.
`_cache_key` non usa più `bytes(perm)`, che funziona solo per valori 0..255 e
liste Python.

### Validazione della configurazione

`config.json` è un file di testo nella home: può essere modificato a mano o
arrivare da una versione precedente. Un valore fuori range veniva accettato e
propagato nella GUI (`"help_font_scale": 0` → font invisibili;
`"livello": "GURU"` → schede mancanti). Ogni chiave ha ora un validatore; i
valori non validi vengono scartati in favore del default, con una riga nel log.

## 2. Prestazioni

Tutte le misure su questa macchina, confronto diretto 3.0.1 → 3.1.x.

| Operazione | prima | dopo | guadagno |
|---|---|---|---|
| CSV, 373.248 righe | 37,4 s | 3,2 s | **11,6×** |
| PDF esteso, 1.728 pagine | 11,2 s | 5,4 s | **2,1×** |
| …dimensione del PDF | 16,4 MB | 6,3 MB | **2,6× più leggero** |
| Distribuzione decomposizioni | ~7 s | 0,05 s | **~140×** |
| Rendering griglie (micro-benchmark) | 4,26 ms/pag | 1,41 ms/pag | **3,0×** |

### T su vettori di permutazione invece di matrici

`compute_T_full` costruiva, per **ogni** combinazione, tre prodotti di
Kronecker 27×27 (`np.kron` due volte ciascuno) e cinque moltiplicazioni di
matrici 27×27 in float64: ~95 µs per combinazione. Ma T è una permutazione, e
comporre permutazioni è un'indicizzazione di liste.

Nuova `compute_T_perm()`: A_i memoizzato per parametri di stadio (al massimo
6³·2³ = 1728 chiavi, quindi la cache è naturalmente limitata) e T ottenuto con
cinque composizioni di liste. **95 µs → 3,4 µs.** `compute_T_full` resta
disponibile e delega, costruendo la matrice una volta sola dalla permutazione
finale. Il CSV prodotto è identico byte per byte.

### Griglie PDF come Form XObject

Ogni matrice 27×27 veniva disegnata con 56 `canvas.line()` più 4 linee spesse,
ripetute identiche su ogni pagina: ~700 operatori di path per pagina, tutti
scritti nel file. La griglia dipende solo dal passo della cella, quindi ora è
disegnata **una volta** in un Form XObject (nuovo `core/pdfgrid.py`) e ogni
matrice emette un solo operatore `Do`. Le celle piene restano disegnate
normalmente. Applicato ai tre renderer (base, esteso, dettagliato).

Verifica: rendering a 1,6× di tre pagine confrontate pixel per pixel — 0,099%
dei pixel differisce con delta massimo 39/255, cioè solo antialiasing sulle
linee della griglia.

### Distribuzione delle decomposizioni

`_distribution_partial` iterava su 216³ = 10.077.696 terne con indicizzazione
numpy elemento per elemento. Sfruttando la relazione di trasporto
`MSC ∘ K = rot₂(K) ∘ MSC`:

```
A3 ∘ MSC ∘ A2 ∘ MSC ∘ A1 ∘ MSC = A3 ∘ rot₂(A2) ∘ rot₁(A1) ∘ MSC³
                               = A3 ∘ rot₂(A2) ∘ rot₁(A1)
```

quindi ogni T raggiungibile è esso stesso un Kronecker: i T distinti sono 216,
e ciascuno riceve esattamente 216² = 46.656 decomposizioni.

Il codice **non assume** questo risultato: per tutte le 46.656 coppie (A1, A2)
verifica che `C = MSC∘A2∘MSC∘A1∘MSC` sia davvero un Kronecker (altrimenti
solleva `_KronNotFound`) e conta con la tabella di Cayley. 46.656 iterazioni
invece di 10.077.696: stesso risultato, ~200× più veloce, **e una proprietà
verificata in più**. Un test confronta il conteggio con la forza bruta
autentica su un sottoinsieme di indici.

## 3. Pulizia e manutenibilità

* **Codice morto rimosso** (121 righe): `_all_reachable_T()` e
  `compute_distribution()` in `analysis.py` non erano chiamate da nessuna parte
  (la GUI usa `compute_distribution_parallel`) e contenevano entrambe un triplo
  ciclo Python su 10 milioni di iterazioni — ore di calcolo se qualcuno le
  avesse invocate.
* **18 `for` annidati** in `iter_combinations` sostituiti da un unico
  `itertools.product`. L'ordine di emissione è identico (verificato da un test):
  la numerazione «Combinazione #N» non cambia.
* **Quattro wrapper paralleli quasi identici** ridotti a `parallel.run_export`
  più un `_pdf_parallel` condiviso fra variante base ed estesa.
* **Due funzioni di disegno duplicate** per renderer (`draw3`/`draw27`)
  unificate in `pdfgrid.GridPainter`.
* **Zero warning pyflakes** su tutto il progetto: `test_static.py` passa
  (prima falliva su 4 warning — import inutilizzati in `combinations.py` e
  `presentation.py`, due f-string senza placeholder in `simulator_tab.py`).
* `python gioco27.py --selftest` ora funziona come `python -m gioco27
  --selftest`, invece di ignorare l'argomento e aprire la GUI.
* `requirements.txt` distingue esplicitamente obbligatorie e opzionali.

## 4. Test

Da 82 a **113 test**, tutti verdi. Il nuovo `tests/test_hardening.py` copre:
limite degli export e assenza di file parziali, ordine di `imap_ordered`,
pigrizia di `chunked`, ordine di `iter_combinations` contro un riferimento
`itertools`, `compute_T_perm` contro la matrice, conteggio distribuzione
contro la forza bruta, round-trip della cache JSON e rifiuto di versioni
vecchie e file corrotti, validazione della config (15 casi), e presenza del
Form XObject nel PDF.

Suite verde anche con `python -O`. `--selftest` invariato: 6 controlli su 6.

## 5. Osservazioni non corrette (per scelta)

* **`compose3` restituisce `DCS_U` dove ci si aspetterebbe `R_U`.** `R_U` e
  `DCS_U` sono la stessa permutazione `[2,1,0]`, e la tavola `_MULT3` risolve
  il nome scandendo `_ALL3`, dove `DCS_U` viene prima. Le etichette A_i possono
  quindi mostrare un nome di tipo P dove semanticamente c'è un'inversione J.
  **Nessun errore di calcolo** (le permutazioni coincidono), solo una
  potenziale confusione di lettura. Non toccato perché cambierebbe le etichette
  in CSV e PDF già prodotti: da decidere insieme.
* **Assenza di annullamento negli export.** Un export avviato va portato a
  termine o si chiude la finestra. Aggiungere un flag di cancellazione
  propagato ai worker è un intervento sull'interfaccia, non una correzione:
  vale la pena farlo, ma come modifica esplicita.

---

# Allineamento della Guida (How-To) al programma

Verifica sistematica di `gui/guide.py` (1 000+ righe), `glossary.py`,
`help_banner.py`, `onboarding_tab.py` e `README.md` contro il codice reale.
Trovate **12 divergenze**, tutte corrette.

## Divergenze strutturali

| # | Divergenza | Realtà |
|---|---|---|
| 1 | Il link «ⓘ Apri Guida» dei banner **non funzionava** | `_open_guide(section)` accettava il numero di sezione e lo ignorava: ogni link apriva la Guida in cima. Ora la Guida registra un mark tkinter per ogni sezione e vi scorre davvero. |
| 2 | Tre schede su otto **non avevano** una sezione di riferimento | Simulatore, Tavola 216 e Distribuzione passavano `section=None`: il loro link «Apri Guida» non aveva destinazione. Ora tutte e otto la indicano. |
| 3 | La scheda **Tavola 216 non era documentata affatto** | È una scheda visibile anche in modalità Principiante. Aggiunta come nuova sezione 11 (subito dopo «Il Gioco Reale», di cui è la tabulazione); le sezioni 11-32 sono diventate 12-33, con indice e riferimenti incrociati rinumerati coerentemente. |

## Contenuti che descrivevano cose inesistenti

| # | Diceva | È |
|---|---|---|
| 4 | «I **sei** sotto-tab» dell'Explorer | Sono **sette**: mancava «🎴 Mescolamento», che è per giunta il primo. |
| 5 | Nomi dei sotto-tab: «📝 Traccia», «🧮 Algebra», «📊 Passi», «⧆ Canonica» | Etichette reali: «✏️ Traccia riscrittura», «🧮 Forma algebrica», «📋 Passi parziali», «⧆ Forma canonica». |
| 6 | Tab **Distribuzione**: «distribuzione degli ordini, delle firme, classi di coniugio, centro del gruppo», calcolata «sui filtri» | Nessuna di queste. La scheda conta, per ogni T raggiungibile, quante decomposizioni Kronecker ammette, e mostra Istogramma + Tabella dati. Non dipende dai filtri. Sezione riscritta, con il risultato (216 T × 46 656) e il perché. |
| 7 | Tab Distribuzione: «Pulsante Classi di Coniugio» | Quel pulsante non è lì: 🔬 Coniugio e 🔮 Cayley sono nella barra azioni. |
| 8 | Tab **Cicli**: «Firma della permutazione: +1/−1» e «istogramma delle lunghezze» | Non esistono. La scheda mostra Ordine, N° cicli e Tipo, più i sotto-tab «Cicli disgiunti» e «Orbite carte» — quest'ultimo non era documentato. |

## Pulsanti e funzioni non documentati

| # | Mancava |
|---|---|
| 9 | L'intera **barra delle azioni**: 🔢 Conta, ⬇ Genera…, ↺ Reset tutto, ✔ Verifica, 🖥️ Presentazione, ⏻ Esci. In particolare «↺ Reset tutto» veniva confuso con il preset «↺ Reset filtri», che è un pulsante diverso e fa meno cose. |
| 10 | La finestra **Presentazione** (vista esecutore a schermo intero, 194 righe di codice) e i suoi tasti →/←/F11/Esc. Aggiunta con il pulsante ✔ Verifica in una nuova sottosezione. |
| 11 | Scheda «Inizia qui»: la Guida elencava **tre** azioni rapide, sono **quattro** (mancava «🎩 Prova il Simulatore»). |

## Dati numerici sbagliati

| # | Diceva | È |
|---|---|---|
| 12 | «Python **3.8** o superiore» | `pyproject.toml` richiede **3.9**. |
| | Piè di pagina: «Versione: gioco27 **v2.7.2**» | Il programma era alla 3.0.1 — due major di distanza, e la sezione 29 diceva «dalla versione 2.8». Ora la versione è letta da `gioco27.__version__`. |
| | «~1 000 righe CSV/s; ~140 pagine PDF/s» | Era già sbagliato di 10× sul CSV nella 3.0.1 (~10 000/s). Ora misurato: **~115 000 righe/s** e **~320 pagine/s**. |
| | «Nessun filtro → non avviare!» / «J uniformi → solo CSV, ore» | Ora quegli export vengono **rifiutati**. Sezione riscritta con le soglie reali (20 000 000 e 200 000) lette dal codice. |

## Il rimedio strutturale: `tests/test_guida_allineata.py`

Correggere i testi non basta: senza un controllo automatico la Guida
ridiverge alla prossima modifica. I 19 nuovi test leggono il **sorgente** della
Guida e lo confrontano col programma:

* indice ↔ intestazioni: stessi numeri e stessi titoli, numerazione consecutiva;
* ogni «vedi sezione N» punta a una sezione esistente;
* ogni `section=` dei banner esiste, e **nessuna scheda** passa `None`;
* `_open_guide` usa davvero il parametro `section`;
* numero e **etichette reali** dei sotto-tab di Explorer, Cicli e Distribuzione;
* ogni pulsante delle barre in alto (estratto da `_build_ui` con l'AST) compare
  nella Guida;
* azioni rapide e passi della scheda «Inizia qui»;
* i limiti citati coincidono con `MAX_EXPORT_ITEMS` e `MAX_DETAIL_COMBOS`;
* il totale delle combinazioni coincide con `count_combinations_ex`;
* la versione minima di Python coincide con `pyproject.toml`;
* le dipendenze elencate coincidono con quelle di `controlla_requisiti.py`;
* la versione nel piè di pagina viene da `__version__`, non scritta a mano.

Cinque di queste divergenze (punti 4, 5, 9, 10, 11) sono state trovate **dai
test stessi** mentre li scrivevo, non dalla lettura.

**Totale: 132 test, tutti verdi.**

---

# Nuova funzione: il tabellone di T⁻¹ nel PDF dettagliato

Nel PDF dettagliato, sotto la griglia `A_1/A_2/A_3` esistente, ne compare ora
una seconda con le stesse righe **in maiuscolo** e con ogni sigla sostituita
dalla propria inversa (CDS↔DSC; le altre quattro sono auto-inverse).

## Perché è il tabellone di T⁻¹, non solo una comodità notazionale

La griglia esistente, letta **per righe** da sinistra a destra, dà le sigle dei
mescolamenti in ordine cronologico inverso — riga in alto = terzo
mescolamento. È il «tabellone» di `core/gioco_reale.py`: i tre mescolamenti
impilati, il primo in basso.

Il tabellone agisce cifra per cifra, cioè come prodotto di Kronecker
`T = B₂ ⊗ B₁ ⊗ B₀`. L'inversa di un prodotto di Kronecker è il prodotto delle
inverse:

    T⁻¹ = B₂⁻¹ ⊗ B₁⁻¹ ⊗ B₀⁻¹

quindi invertire ogni singola riga inverte l'intera permutazione. E poiché la
sigla d'impilamento **è** l'inversa di quella di mescolamento (è la definizione
di `IMPILAMENTO_DI`), la stessa tabella si legge in due modi: il gesto fisico
da eseguire, e il tabellone della permutazione inversa.

Verifica sull'ancora #100 del libro:

| | |
|---|---|
| mescolamenti (cronologici) | CDS, CDS, CSD |
| Assi | 13, 8, 18 → settori `ccc`, `sdd`, `dss` |
| TABELLONE MESCOLAMENTI (righe) | CSD, CDS, CDS |
| TABELLONE T⁻¹ (righe) | CSD, DSC, DSC |

## Layout finale

Le due griglie stanno dentro **un'unica cornice**, così si leggono come una
sola tabella:

* **TABELLONE DI T** (sopra) — colonne `A_1/A_2/A_3`: ogni colonna è un Asso e,
  letta dall'alto in basso, dà il suo settore ternario. Minuscolo, come le
  `<td>` dell'HTML del programma C. Lette per **righe**, invece, le tre sigle
  formano il tabellone: rileggendole si riottiene esattamente T.
* **TABELLONE DI T⁻¹** (sotto) — si legge in **orizzontale**, quindi le
  intestazioni `A_1/A_2/A_3` non avrebbero senso: al loro posto ci sono le
  etichette di riga `M_2 / M_1 / M_0` dall'alto in basso, con **M_0 in fondo**.
  Maiuscolo.

### Perché le didascalie dicono «T» e non «mescolamenti»

Una prima versione le intitolava TABELLONE MESCOLAMENTI e TABELLONE T⁻¹
(IMPILAMENTI). **Era falso in 1512 casi su 1728**, e l'ha scoperto una stampa
reale: nella combinazione D#122 i mescolamenti sono `DSC/CSD/SCD` ma la griglia
mostra `DCS/DSC/SDC`.

Non è un errore di calcolo. Quella combinazione ha un rovesciamento
(`M1 = TRUE`), e un rovesciamento è a sua volta un'inversione su ogni cifra:
si fonde nelle righe del tabellone e le sigle effettive diventano altre. Le
righe restano un tabellone **valido** — sono le sigle di un gioco equivalente
senza rovesciamenti che produce la stessa T — ma chiamarle «mescolamenti» le
metteva in contraddizione con la riga stampata due centimetri più in alto.

Le righe coincidono con i mescolamenti nominali **solo** nelle 216 combinazioni
senza rovesciamenti. La proprietà su T e T⁻¹ invece regge sempre, ed è quella
che le didascalie ora dichiarano.

Perché i test non l'avevano colto: verificavano la proprietà giusta (T e T⁻¹)
ma su un insieme troppo ristretto — le sole 216 sequenze senza rovesciamenti.
La fixture ora ne offre due: `sequenze` (216) e `tutte_le_sequenze` (1728).

Le colonne dei dati delle due griglie sono incolonnate: la griglia superiore è
rientrata della larghezza della colonna delle etichette.

## Note di implementazione

* Due funzioni pure e testabili in `detail_pdf.py`: `righe_tabellone(markers)`
  e `righe_impilamenti(markers)`.
* Il disegno delle due griglie è stato fattorizzato in una sola funzione
  `griglia(y, righe, titolo, colore)`, così restano identiche per costruzione.
* I titoli sono su due righe corte, perché devono stare **dentro** la larghezza
  della griglia: la matrice 27×27 viene disegnata dopo e riempie il proprio
  sfondo di bianco, quindi un titolo più largo veniva coperto. Il primo tentativo
  aveva esattamente questo difetto, visibile solo rasterizzando il PDF.
* Verificato su entrambe le metà della pagina (le combinazioni sono due per
  pagina): nessun taglio, nessuna sovrapposizione.
* Il corridoio fra la tabella POSIZIONE ASSO (finisce a `xm2+156`) e la matrice
  27×27 (inizia a `xm2+260`) è di 104 pt. Con celle da 20 pt e colonna
  etichette da 16, la cornice occupa 92 pt e resta a 6 pt da entrambe. Un primo
  tentativo usava `xg` come bordo della cornice invece che come inizio delle
  celle, e la cornice mordeva di 2 pt il bordo della tabella POSIZIONE ASSO:
  visibile solo rasterizzando il PDF.
* La griglia superiore resta in minuscolo, fedele alle `<td>` dell'HTML del
  programma C; solo la nuova usa le maiuscole, così il contrasto rende evidente
  che sono due cose diverse.

## Test

`tests/test_tabellone_inverso.py`, 9 test su **tutte e 216** le sequenze del
gioco (non su un campione):

* le righe della prima griglia sono i mescolamenti in ordine inverso;
* il primo tabellone, riletto con `T_da_tabellone`, ricostruisce esattamente T;
* **il secondo tabellone ricostruisce esattamente T⁻¹**;
* controllo esplicito dell'ancora #100;
* lo scambio è un'involuzione e tocca solo CDS e DSC;
* le righe della seconda griglia sono maiuscole;
* una riga che non è una sigla valida (combinazioni non eseguibili
  fisicamente, dove i settori degli Assi non formano una permutazione) viene
  lasciata invariata invece di far fallire l'export;
* le etichette di riga sono nell'ordine M_2/M_1/M_0 dall'alto (verificato sul
  sorgente: invertirle renderebbe la tabella silenziosamente sbagliata);
* la riga M_0 è l'impilamento del primo mescolamento, M_1 del secondo, M_2 del
  terzo — su tutte e 216 le sequenze senza rovesciamenti;
* **su tutte e 1728 le sequenze, rovesciamenti compresi**: la griglia superiore
  ricostruisce T e quella inferiore T⁻¹;
* tutte le righe sono sempre sigle valide, mai triple tipo `SSD`;
* con almeno un rovesciamento le righe differiscono, in generale, dai
  mescolamenti nominali — il comportamento che ha reso false le vecchie
  didascalie, ora documentato da un test;
* le didascalie non contengono le parole MESCOLAMENTI/IMPILAMENTI (verificato
  sul sorgente: rimetterle fa fallire il test, controllato).

## Validità universale — e una verifica finalmente esaustiva

I test qui sopra girano sulle 1728 sequenze «di gioco» (P1 = P2 = identità, J
uniforme). Ma i due tabelloni **non hanno bisogno di quelle ipotesi**: valgono
per qualunque combinazione del modello, compreso il rovesciamento di un solo
mazzetto — che non è nemmeno una sequenza eseguibile con un gesto solo.

Il motivo sta in dove partono i tre Assi: posizioni 0, 13 e 26, cioè `(0,0,0)`,
`(1,1,1)`, `(2,2,2)` — la **diagonale ternaria**. Se `T = B₂ ⊗ B₁ ⊗ B₀` agisce
cifra per cifra, allora

    T(j,j,j) = (B₂(j), B₁(j), B₀(j))

quindi la colonna dell'Asso *j*, letta dall'alto in basso, dà le tre cifre; e la
riga *r*, letta per intero, **è la sigla completa di B₂₋ᵣ**.

Da qui segue una conseguenza che cambia la natura della verifica: **la griglia
dipende solo da T**, non dai parametri che l'hanno prodotta. E ogni T del
modello è un prodotto di Kronecker GEN3³, di cui esistono esattamente 216.
Verificare tutti e 216 i T possibili è quindi una verifica **esaustiva su tutte
e 1728³ = 5 159 780 352 le combinazioni**, non un campione.

Test aggiunti:

* i due tabelloni ricostruiscono T e T⁻¹ su **tutti e 216** i T possibili;
* ogni combinazione del modello (P e J arbitrari) produce un T fra quei 216;
* validità col rovesciamento di **un solo mazzetto** (J non uniforme), 18 casi
  che non sono sequenze di gioco;
* gli Assi stanno sulla diagonale ternaria — è l'ipotesi da cui dipende tutto,
  e spostarli romperebbe silenziosamente entrambi i tabelloni.

**Totale: 152 test, tutti verdi.**

---

# Efficienza su macchine molti-core, e i PDF uniti

## Il sintomo: 5% di CPU su 128 core

Tre cause, misurate. **La stampa PDF non era fra queste**: la fusione con pypdf
pesa 0,25 ms su 3,5 ms per pagina, cioè il 7% — un tetto di Amdahl di 14×, non
di 5%.

### 1. Il tetto sui worker (causa principale)

`plan_workers` limitava i processi a `totale ÷ 80` per il PDF e `÷ 400` per il
CSV. Con l'export standard del Gioco Reale (1728 combinazioni): **21 worker per
il PDF e 4 per il CSV**, cioè il 16% e il 3% di 128 core. Le soglie erano tarate
su macchine da 4-8 core, dove non mordono mai.

Il modello era sbagliato: i processi figli si avviano **in parallelo**, quindi
lo spawn è una latenza quasi costante (~1-2 s su Windows, dove ogni figlio
re-importa numpy e reportlab), non un costo per worker. Conviene quindi usarne
molti. La decisione ora si basa sul **lavoro stimato**:

* sotto `LAVORO_MINIMO_S = 0,5 s` di calcolo totale → si resta in-process;
* sopra, si usano tutti i core, dando a ciascun worker almeno
  `LAVORO_PER_WORKER_S = 0,20 s` di lavoro utile;
* **un blocco per worker** invece di quattro: le pagine hanno costo uniforme,
  quindi la suddivisione statica è già bilanciata, e ogni blocco in più è un PDF
  parziale in più da unire.

Risultato su 128 core, export da 1728 combinazioni: da 21 a **28 worker** per il
PDF standard e a **48** per il dettagliato; su un export da 46 656, tutti e 127.

### 2. Il lavoro è semplicemente poco

Dopo le ottimizzazioni, 1728 pagine sono ~5,7 s di rendering totale e 1728 righe
CSV sono ~15 ms. Non c'è abbastanza da distribuire su 128 core. Per saturarli
servono circa 10 000 pagine (PDF) o 56 000 righe (CSV).

### 3. Due percorsi paralleli erano diventati controproducenti

Un difetto introdotto ottimizzando il calcolo senza rivedere la soglia di
parallelizzazione:

| | prima della 3.0.2 | ora | parallelo |
|---|---|---|---|
| decomposizioni Kronecker | secondi | 0,025 s | **più lento già con 2 worker** |
| distribuzione | ~7 s | 0,086 s | inutile |

Entrambi sono ora sequenziali, con il motivo scritto nel codice.

## I PDF uniti: 87 copie dello stesso font

Ogni processo figlio genera un PDF autonomo, quindi vi **incorpora la propria
copia dei font**. L'export dettagliato del Gioco Reale su una macchina a 128
core si divide in ~87 blocchi, e il file finale conteneva 87 copie identiche di
ciascun font, tutte con lo stesso nome `/AAAAAA+DejaVuSans`.

Nuovo modulo `core/pdfmerge.py`: deduplicazione per hash del contenuto con
pikepdf (ripiego su `pypdf.compress_identical_objects`, e in mancanza di
entrambi il file resta valido, solo più grande).

| export (1728 combinazioni) | prima | dopo |
|---|---|---|
| PDF standard parallelo | 6,3 MB | **4,6 MB** |
| PDF dettagliato parallelo | 11,1 MB | **5,8 MB** |
| copie dei font incorporati | 87 | **1** |

Il file parallelo è ora **più piccolo del sequenziale** (7,4 MB), grazie agli
object stream.

## Scrittura atomica

Tutti gli export (PDF, PDF dettagliato, CSV, sequenziali e paralleli) scrivono
ora su un file temporaneo e lo rinominano con `os.replace` solo a scrittura
conclusa. Un export interrotto — errore, chiusura della finestra, disco pieno —
non lascia più al posto del file buono un PDF o un CSV troncato.

## Sul PDF illeggibile da Acrobat: non riprodotto

**Non sono riuscito a riprodurre il problema.** Ho generato i quattro export
grandi (1728 pagine standard, 864 dettagliato, sequenziali e paralleli) e li ho
validati con cinque strumenti indipendenti — pypdf, pdfium, pikepdf, `qpdf
--check`, Ghostscript su tutte le pagine. Tutti li accettano, prima e dopo le
modifiche.

Ho corretto un difetto reale e plausibilmente collegato (87 risorse font
duplicate con lo stesso nome) e reso atomica la scrittura, ma **non posso
affermare di aver risolto**, perché non ho mai visto il guasto.

Servono due informazioni per andare avanti: il **messaggio esatto** di Acrobat,
e l'esito di un export con il parallelismo **disattivato** in Impostazioni. Se
il file sequenziale si apre e quello parallelo no, il problema è nella fusione;
se falliscono entrambi, è altrove.

**Totale: 160 test, tutti verdi.**

---

# Il vero motivo dell'1-2% di CPU: il limite di 61 worker di Windows

Segnalazione dal campo: **13 000 pagine in 2m39s, CPU all'1-2%, identico alla
versione precedente.** Se il tetto sui worker fosse stato l'unica causa, la
3.0.3 avrebbe dovuto essere più veloce — e a 13 000 elementi anche la versione
precedente chiedeva già 127 worker. Quindi il parallelismo non partiva affatto.

## La causa

Su Windows `ProcessPoolExecutor` **non accetta più di 61 worker**:

    ValueError: max_workers must be <= 61

Il limite viene da `WaitForMultipleObjects`, che gestisce al massimo 64 handle,
ed è codificato in `concurrent.futures.process._MAX_WINDOWS_WORKERS`.

Su una macchina a 128 core `effective_n_workers` valeva 127. Ogni export
chiedeva 127 worker, il pool veniva **rifiutato alla creazione**, e il blocco
`except Exception` faceva ripiegare sul sequenziale registrando l'errore solo
nel file di log.

Conseguenza: **su quelle macchine il parallelismo non ha mai funzionato**, per
nessun export e in nessuna versione del programma. L'utente vedeva l'1-2% di
CPU e nessun messaggio.

## Le correzioni

* `max_workers_piattaforma()` restituisce il tetto della piattaforma (61 su
  Windows, nessun limite altrove), letto da `_MAX_WINDOWS_WORKERS` quando
  disponibile.
* `default_workers()` lo applica sempre, e registra la riduzione nel log.
  Anche `Config.effective_n_workers` passa da lì, così il numero mostrato dalla
  GUI è quello realmente usato.
* `imap_ordered` accetta `executor_factory` e, se il pool viene comunque
  rifiutato, **riprova col tetto** invece di far fallire l'export.
* `compute_distribution_parallel` applica il tetto al proprio pool.
* Il ripiego sul sequenziale non è più invisibile: viene registrato come
  WARNING con il numero di worker richiesto, prima del traceback.

Su 128 core Windows l'export da 13 000 pagine passa da **1 processo a 61**.

## Nota su cosa aspettarsi

Anche con 61 worker la CPU non arriverà al 100%: l'export standard del Gioco
Reale è ~5,7 s di rendering totale, e il tempo è dominato dall'avvio dei
processi e dalla fusione. Il guadagno vero si vede sugli export grandi, dove i
61 worker hanno abbastanza lavoro da ammortizzare l'avvio.

## Nota di metodo

Questo difetto era invisibile a chi sviluppa su una macchina normale: sotto i
62 core logici il tetto non morde mai e tutto funziona. È stato trovato solo
grazie a una misura di CPU su hardware reale — nessun test della suite avrebbe
potuto scoprirlo, perché la suite gira dove il problema non esiste. Ora esiste
un test che simula Windows a 128 core.

**Totale: 166 test, tutti verdi.**

## Le 2m39 dopo la barra: strumentazione invece di ipotesi

Segnalazione successiva: con il limite di 61 worker corretto, **la barra si
riempie in 1-2 secondi** — il rendering parallelo ora funziona — ma poi
l'esportazione dura ancora 2m39.

Ho misurato qui ogni fase successiva al rendering, su un file da **13 824
pagine e 50 MB**:

| fase | tempo |
|---|---|
| unione di 61 blocchi (`add_page`) | 3,9 s |
| scrittura pypdf del file finale | 0,7 s |
| deduplicazione con pikepdf | 3,9 s |
| deduplicazione di ripiego con pypdf | 5,9 s |
| **totale dopo il rendering** | **~10 s** |

Nessuna di queste spiega 2m39. Le differenze fra il mio ambiente e quello di
chi segnala il problema — Windows, 128 core, disco, antivirus, e soprattutto
*quale* export — non sono riproducibili qui, e continuare a formulare ipotesi
sarebbe inutile.

Ho quindi aggiunto la **strumentazione**: ogni fase dell'export registra la
propria durata in `~/.gioco27/gioco27.log`, insieme al piano di
parallelizzazione. Un export produce ora righe come:

    Export PDF esteso: 1728 elementi, 4 worker, blocchi da 432
      (4 blocchi, ~1.4 s di lavoro stimato per worker)
    tempi: Export PDF esteso: calcolo+unione blocchi       3.21 s
    tempi: Export PDF esteso: scrittura del PDF finale     0.08 s
    tempi: Export PDF esteso: deduplicazione risorse       0.51 s
    Export PDF esteso: completato, 1728 elementi -> ...

Per il PDF dettagliato è cronometrata anche la fase `ordinamento e trasposte`,
che è interamente seriale e con molte combinazioni non è trascurabile.

Basta rifare l'export e allegare quelle righe: diranno quale fase consuma le
2m39, senza bisogno di riprodurre il problema.

**Totale: 166 test, tutti verdi.**

---

# PermissionError su Windows nella deduplicazione

Dal log di un export da 27 648 combinazioni (13 824 pagine):

    PermissionError: [WinError 5] Accesso negato:
      'C:/.../dettaglio_disposizioni.pdf.parziale' -> '.../dettaglio_disposizioni.pdf'
    tempi: PDF dettagliato: deduplicazione risorse    26.36 s

## La causa

`PdfReader(path)` e `pikepdf.open(path)` tengono il file **aperto** per la
lettura pigra. Su Windows `os.replace` su una destinazione ancora aperta
fallisce con WinError 5. Su Linux la stessa sequenza funziona — POSIX consente
di rinominare sopra un file aperto — quindi il difetto era **invisibile** fuori
da Windows, esattamente come il limite dei 61 worker.

Il danno era doppio: 26 secondi di lavoro buttati, e il PDF restava non
deduplicato (valido, ma più grande).

## Le correzioni

* `pikepdf.open(path, allow_overwriting_input=True)`: legge in memoria invece
  di tenere il file aperto. Il salvataggio avviene dentro il `with`, la
  sostituzione **dopo** la chiusura.
* Il ripiego pypdf legge i byte con `open(path,'rb').read()` e lavora su un
  `BytesIO`: il file di origine è chiuso prima della sostituzione.
* `_sostituisci()` isola la sostituzione e documenta il motivo.
* In caso di errore il file temporaneo viene rimosso e il PDF originale resta
  intatto.
* Il ripiego pypdf non viene più tentato sopra `MAX_MB_RIPIEGO_PYPDF = 20 MB`:
  costa decine di secondi (26 s misurati) e non deduplica i font incorporati.
  Sopra la soglia il log suggerisce di installare pikepdf.

## Test

Quattro test nuovi, di cui uno verifica l'invariante **con l'AST** invece che
con una ricerca testuale — la prima versione trovava `PdfReader(path)` nei
commenti che spiegano il difetto e falliva a vuoto:

* nessuna chiamata apre il percorso di destinazione per poi sostituirlo;
* `pikepdf.open` usa `allow_overwriting_input=True`;
* dopo un fallimento della sostituzione il PDF originale è intatto e non
  restano file temporanei;
* il ripiego pypdf salta i file grandi.

Verificato che entrambe le regressioni vengano colte: rimettendo
`PdfReader(path)` o togliendo `allow_overwriting_input` il test fallisce.

**Totale: 170 test, tutti verdi.**

---

# Combinazioni fuori dalle 1728 del gioco: etichette impazzite

Da una stampa reale con filtri oltre i limiti del gioco (P1/P2 diversi
dall'identità). Tre difetti, tutti nelle etichette.

## 1. `M[SCD×CSD×SDC]` — l'argomento di M dovrebbe essere un numero

Il difetto di merito, non solo estetico. Nel programma C `M[k]` è un **indice
numerico** nella tabella dei mescolamenti; il PDF ci infilava dentro
l'etichetta di stadio, che per queste combinazioni è un prodotto di Kronecker.
Il risultato era una notazione che sembra corretta e non lo è.

Ora, quando gli indici non esistono, il PDF lo dice:

    raccolte (P3×P2×P1):
    [SCD×CSD×SDC]x[SCD×CSD×SDC]x[SCD]
    indici M[...] non definiti: fuori dalle 1728 del gioco

Dove gli indici esistono, `M[k]xM[j]xM[i]` resta esattamente come prima —
verificato da un test apposito.

## 2. Intestazioni dei mazzi sovrapposte

`Mescolamento 1 = SCD×CSD×SDC` a corpo fisso è largo circa il triplo della
colonna del mazzo (78 pt), quindi finiva sopra l'intestazione successiva:
nella stampa si leggeva `Mescolamento 1 = SCD×S0Cx8CDlamento 2 = ...`.

Titolo ed etichetta sono ora su **righe distinte**, e l'etichetta viene
ridimensionata per stare nella colonna.

## 3. La riga sotto la matrice sconfinava nelle trasposte

`Mescolamenti SCD×CSD×SDC x SCD×CSD×SDC x SCD` superava la larghezza della
matrice e finiva sopra l'«Elenco matrici trasposte». Ora è adattata alla
larghezza della matrice, e dice «Raccolte» invece di «Mescolamenti» quando gli
stadi non sono raccolte singole.

## `adatta_testo`: una funzione pura, non una closure

La logica di adattamento è a livello di modulo e riceve la funzione di misura
iniettata, quindi è verificabile senza un canvas PDF:

    adatta_testo(testo, max_w, misura, size, min_size) -> (testo, corpo)

Scritta come closure dentro il renderer sarebbe rimasta non testabile — ed è
proprio il test che ha trovato un difetto nella prima versione: il corpo
scendeva **sotto** il minimo dichiarato (3,85 con `min_size=4,0`), perché il
decremento avveniva dopo il controllo.

## Test

Nuovo `tests/test_fuori_dal_gioco.py`, 10 test:

* `adatta_testo` lascia intatto il testo corto, rimpicciolisce quello lungo,
  tronca con l'ellissi quando non basta, e **non supera mai** la larghezza
  richiesta né scende sotto il corpo minimo (verificato su 20 combinazioni di
  lunghezza e larghezza);
* nessun `M[` seguito da una lettera compare nel PDF;
* la pagina fuori dal gioco dichiara «raccolte (P3×P2×P1)» e «non definiti»;
* le combinazioni di gioco **mantengono** gli indici `M[k]` e le righe
  mescolamenti/impilamenti;
* titolo ed etichetta del mazzo stanno su righe distinte.

**Totale: 180 test, tutti verdi.**

---

# Numerazione a base 0 e audit di coerenza

## Perché

Tutto il programma era già a base 0 — cifre ternarie i₂i₁i₀, posizioni 0-26,
numerazione D# da 0, flag di rovesciamento M0/M1/M2, righe del tabellone
M_2/M_1/M_0 — tranne gli stadi (1, 2, 3) e i fattori (P1/P2/P3, J1/J2/J3).

Il sintomo più netto: **nella stessa pagina del PDF dettagliato lo stesso
stadio compariva come «Mescolamento 1» e come «M0»**.

## Cosa cambia

| | prima | dopo |
|---|---|---|
| schede e stadi | Stadio 1, 2, 3 | **Stadio 0, 1, 2** |
| fattori P e J | P1/P2/P3, J1/J2/J3 | **P0/P1/P2, J0/J1/J2** |
| intestazioni CSV | Stage1..3, A1..A3 | **Stage0..2, A0..A2** |
| PDF dettagliato | Mescolamento 1, 2, 3 | **Mescolamento 0, 1, 2** |
| chiavi interne dei filtri | `p1`…`j3` | **`p0`…`j2`** |
| Assi | #1, #2, #3 | invariati (sono tre carte, non indici) |

Ora **P_k agisce sulla cifra i_k** e lo Stadio k è il k-esimo, senza
conversioni mentali.

## Una regolarità che la numerazione nascondeva

La regola degli indici incrociati era documentata come tre casi separati:

    P3 ← J1     P2 ← J3     P1 ← J2

In base 0 è una formula sola:

    f_k = P_k ∘ J_(k+1 mod 3)

Aggiunta al codice, alla Guida e a un test che la verifica.

## Migrazione: errore esplicito, non silenzioso

La vecchia chiave `p2` (terzine) è la **nuova `p1`**: un filtro scritto con i
nomi vecchi verrebbe interpretato in modo diverso senza alcun segnale. Per
questo `valida_filtri` rifiuta le chiavi legacy con un messaggio esplicito,
invece di ignorarle.

## Errori preesistenti trovati durante l'audit

Rileggendo riga per riga il diff della Guida sono emersi **tre errori che non
c'entravano con la rinumerazione**: la Guida descriveva il preset «Gioco
Reale» come se lasciasse libero il fattore delle CARTE e fissasse gli altri
due. È il contrario — libera il fattore dei PACCHETTI, cioè la raccolta
fisica. Le tre affermazioni sbagliate:

* «Nel gioco reale tradizionale P2 = P3 = SCD_U e solo P1 varia»
* «Per stadio: 6 (P1) × 1 (P2 fisso) × 1 (P3 fisso)»
* «Imposta su tutti e tre gli stadi: P1 libero, P2 = P3 = SCD_U»

Tutte corrette, e ora c'è un test che estrae dal **codice** del preset quali
fattori vengono fissati e verifica che la Guida dica la stessa cosa: l'errore
non può tornare.

Sistemate anche due incoerenze minori: «fattore di grado 3 / posizione 3»
erano rimasti a base 1 accanto a fattori a base 0, e l'export LaTeX delle
decomposizioni aveva ancora le colonne $A_1$/$A_2$/$A_3$.

## Cosa NON è stato cambiato

* **Assi #1/#2/#3** e colonne A_1/A_2/A_3 del tabellone: sono tre carte
  fisiche, non indici di una struttura a base 0.
* **Numeri di riga** negli elenchi (`enumerate(..., 1)`): sono progressivi di
  stampa, giustamente a base 1.
* **Nomi dei parametri interni** `p1n, p2n, p3n` nelle firme di
  `compute_Ai_symbolic`: posizionalmente sono P₀, P₁, P₂ e la docstring lo
  dice; rinominarli avrebbe toccato le firme senza effetti visibili.

## Resta aperto

`compose3('I_3', 'R_U')` restituisce `DCS_U` invece di `R_U`: sono la stessa
permutazione `[2,1,0]` e la tavola risolve il nome scandendo `_ALL3`, dove
`DCS_U` viene prima. Nessun errore di calcolo, ma un'inversione J può
comparire con un nome da fattore P. Non toccato perché cambierebbe le
etichette in CSV e PDF già prodotti: da decidere insieme.

## Test

Nuovo `tests/test_numerazione_base0.py`, 10 test: chiavi a base 0, rifiuto
esplicito delle chiavi legacy, intestazioni e formule del CSV, la regola
chiusa `f_k = P_k ∘ J_(k+1 mod 3)` verificata numericamente, mescolamenti e
flag M con la stessa base nel PDF, e la Guida allineata al codice del preset.

**Totale: 190 test, tutti verdi.**

---

# Layout del PDF dettagliato: i tabelloni in cima

I due tabelloni stavano a metà altezza, sotto la tabella degli Assi: il blocco
più recente finiva nel punto meno visibile della pagina, mentre in alto restava
spazio inutilizzato.

La colonna centrale è ora ordinata dall'alto in basso:

1. **riquadro dei due TABELLONI** — allineato in cima come i mazzi
2. **ROVESCIAMENTO** — R[m] e i flag M0/M1/M2
3. **MOLTIPLICAZIONE** — indici M[...], mescolamenti, impilamenti, POSIZIONE ASSO

Le tre posizioni sono costanti di modulo (`OFF_TABELLONI`,
`OFF_ROVESCIAMENTO`, `OFF_MOLTIPLICAZIONE`), relative al bordo superiore dei
mazzi, invece di numeri sparsi nel renderer: così i test possono verificarle.

## Perché serve un test

La metà **inferiore** del foglio ha poco margine — il blocco più basso è la
tabella degli Assi — e uno spostamento di troppo uscirebbe dalla pagina senza
che nulla protesti. `tests/test_layout_dettaglio.py`, 5 test:

* ordine dei tre blocchi dall'alto in basso;
* il riquadro dei tabelloni parte **sopra** il bordo dei mazzi;
* il riquadro non invade il blocco MOLTIPLICAZIONE;
* tutto resta dentro la pagina in **entrambe** le metà, e la metà superiore non
  sconfina oltre la linea di separazione;
* verifica funzionale: la pagina viene rasterizzata e i quattro margini devono
  essere bianchi — coglie gli sconfinamenti che il calcolo sulle costanti non
  prevede, come un'etichetta lunga adattata.

Verificato che rimettendo i tabelloni a metà altezza il test fallisce.

## Le etichette verticali erano sotto il proprio blocco

`vtext` disegna il testo ruotato **centrato** sulla y ricevuta, e le due
etichette usavano scostamenti fissi (`-72`, `-78`) che le facevano cadere sotto
il testo che dovevano etichettare.

Ora la posizione si calcola dal punto medio del blocco, con l'ingombro in due
costanti (`ALTEZZA_ROVESCIAMENTO`, `ALTEZZA_MOLTIPLICAZIONE`): ROVESCIAMENTO
sale di 51 pt, MOLTIPLICAZIONE di 41, e se un blocco si sposta l'etichetta lo
segue da sola.

Tre test in più. Il terzo è quello che conta davvero: i primi due verificano le
costanti, ma non coglierebbero chi rimette un numero magico nella chiamata.
Quello guarda l'**AST** e pretende che la y derivi dalle costanti di ingombro —
verificato che rimettendo `-72` fallisce.

**Totale: 198 test, tutti verdi.**

---

# I due punti rimasti aperti

## 1. Nomi doppi: I_3/SCD_U e R_U/DCS_U

Due permutazioni su {0,1,2} hanno due nomi ciascuna:

    [0,1,2]  =  SCD_U (raccolta identica)  =  I_3 (nessuna inversione)
    [2,1,0]  =  DCS_U (raccolta S↔D)       =  R_U (inversione completa)

`compose3` restituisce l'identità come **I_3** (nome J) e l'inversione come
**DCS_U** (nome P): una convenzione non uniforme, che sorprende chi imposta
J = R_U e ritrova DCS_U nell'etichetta.

**Non è stata cambiata**, ed è la scelta giusta: `compose3` vede solo il
risultato, non da dove viene. Una raccolta P genuinamente `DCS_U` e
un'inversione J danno la stessa permutazione, quindi nessuna regola basata sul
risultato può distinguerle. Uniformare avrebbe un costo in entrambe le
direzioni: o l'identità smette di chiamarsi I_3 (cambiando moltissime etichette
già prodotte), o una raccolta viene mostrata come R_U.

È ora documentata nel codice, nella Guida e da 7 test che la **pinnano**: se un
giorno si decide di uniformarla, falliscono e obbligano a farlo
consapevolmente. Uno dei test verifica anche la cosa che conta davvero — che la
*permutazione* sia corretta per tutte le 64 coppie, qualunque nome le venga
dato: l'ambiguità è solo di etichetta.

## 2. Annullamento degli export

Un export grande poteva solo essere portato a termine o interrotto chiudendo la
finestra. Ora accanto alla barra c'è **«✕ Annulla»**, attivo solo mentre un
export è in corso.

**Non lascia alcun file**: la destinazione resta com'era, anche se conteneva
già qualcosa. La garanzia viene dalla scrittura atomica introdotta prima.

Punti di controllo:

* export sequenziali — a ogni pagina, o ogni 200 righe per il CSV;
* export paralleli — mentre si aspettano i risultati, ogni 0,2 s.

Il dettaglio che rende utile il pulsante: con **un blocco per worker**,
aspettare il completamento significherebbe minuti. `imap_ordered` chiude quindi
il pool con `wait=False, cancel_futures=True`: i processi che stanno già
macinando un blocco lo finiscono per conto loro, il risultato viene scartato e
l'interfaccia torna subito disponibile.

`ExportAnnullato` non è trattata come un errore: nessun messaggio di guasto,
solo la barra di stato che riporta quanti elementi erano stati calcolati.

### Test

`tests/test_annullamento.py`, 13 test. L'annullamento attraversa **sei**
percorsi (PDF standard, PDF esteso, PDF dettagliato e CSV, in versione
sequenziale e parallela) e sono coperti tutti: dimenticarne uno significherebbe
un pulsante che a volte non risponde. In più:

* un export annullato non tocca un file preesistente;
* la sentinella predefinita non interferisce con gli export normali;
* il pool viene chiuso **senza attendere** quando si annulla, e regolarmente
  quando no;
* la GUI collega davvero il pulsante alle funzioni di export (verificato sul
  sorgente, perché l'interfaccia non è avviabile nei test).

**Totale: 218 test, tutti verdi.**
