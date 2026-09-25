# I6 — Laboratorio matematico: proprietà, gruppo di riferimento e piccoli grafi

**Stato: CHIUSO.** Implementazione completa, suite senza nuove failure,
nessuna scrittura discrezionale fuori dal repository (§ 15).
I7, J e K non sono stati iniziati. Nessun push.

| | |
|---|---|
| HEAD iniziale | `96a83af` (I5: implementazione completa, chiusura formale non soddisfatta per G29 — non toccato) |
| HEAD dei commit di codice | `f172af4` |
| Service | `gioco27/services/laboratorio.py` (puro: niente Tk, niente testo) |
| Vista | `gioco27/gui/laboratorio_tab.py` → Explorer, nono sotto-tab «🧪 Laboratorio» |
| Test nuovi | 17 caratterizzazione + 27 service + 16 GUI + 25 H2 = **85** |
| Suite | 2179 raccolti · 2177 passati · 1 skipped · 1 failure nota Tk9 |

---

## 1. DP2 applicata

* **H = 216** (trasformazioni separabili), **Γ = 648** (gruppo esteso,
  Γ = H ⊔ H∘R ⊔ H∘R², R = MSC), **S27** gruppo ambiente. Così nei testi
  nuovi (chiavi `lab.*`), nel service e in questo documento.
* Nessuna rinomina di massa. `core.group_theory` (legacy «G» = 216) è letto
  solo tramite `_Adattatore`, che mappa gli indici legacy sui numeri di
  Tavola. Le API I5 `separabile` e `classe_estesa` restano neutre e vengono
  riusate (non duplicate) da `laboratorio.etichetta`.
* Una sola nota tecnica sui nomi, in cima alla vista (`lab.legacy_note`):
  «nel core il gruppo di 216 si chiama ancora G … in alcune viste H indica i
  648 elementi. Qui H = 216 e Γ = … = 648».
* La **Guida** usa ancora la notazione legacy (G = S₃³, G_ext) ed è
  sorvegliata dal guard D1 (niente «648» nel testo). La riga della Guida per
  il Laboratorio perciò non usa i simboli H/Γ: «sul gruppo delle 216
  trasformazioni, sul gruppo esteso e su S27». Così nessun testo usa H con
  due significati, né G e H per lo stesso gruppo. La migrazione dei nomi resta
  un compito di K0.
* Tensione registrata: nel libro il cap. 6 intitola G il gruppo di 216, mentre
  la riga 490, il § 11.7 e l'App. B dicono H. DP2 segue H.

## 2. Fonti rilette

Le fonti sono state lette solo in pipe (`pdftotext -layout … - | grep/sed`),
senza creare file.

* **LIBRO_MAIN.pdf**:
  * § 6.6–6.10: coniugio componente per componente, 27 classi, equazione
    delle classi, centro, J;
  * App. B.9: 7 tipi ciclici e punti fissi;
  * A4 § 7.1.4 (limite di Kronecker), A5 § 7.1.5, A10;
  * cap. 8 § 8.2–8.5: tavola 6×6, composizione per livelli, decomposizioni;
  * § 11.7 e Teor. 11.68 (classi laterali e forma normale);
  * § 4.2; Prop. 5.53; Prop. 9.58; § 10.2.1.
* **Articolo.pdf**: Def. 4.1 e Teor. 4.2; App. D Teor. 6.4.
* **Audit § 18.3/18.4**: proposte [PROP]. Il libro non contiene grafi
  espliciti; i tre grafi scelti sono quelli che l'audit collega a strutture
  del libro (S3, H = S3³, «sostituire gradualmente un mescolamento»).
* **I5_DECODING_RECOGNITION_CLOSED.md** e i documenti I1/I2: convenzioni,
  riuso di `riconoscimento`, `procedure` e numerazione della Tavola.

## 3. Catalogo (chiuso, 21 proprietà)

Ogni voce ha un id stabile, una fonte, domini espliciti (`Dominio`: S3, H,
GAMMA, S27, PROCEDURE), una verifica per dominio ed eventuali note di
dominio. Chiedere un dominio non dichiarato solleva `DominioNonPrevisto`:
non c'è nessuna estensione tacita.

In tabella: ✔ vera, ✘ falsa, **T** teorema citato (nessuna enumerazione).
Un trattino indica un dominio non dichiarato.

| id | S3 | H | Γ | S27 | fonte |
|---|---|---|---|---|---|
| separabile | – | ✔ 216/216 | ✘ | ✘ | Articolo Def. 4.1 |
| chiuso_composizione | – | ✔ 46 656 | ✔ 419 904 | – | § 8.4 |
| commutativo | ✘ | ✘ | ✘ | ✘ | § 8.2 |
| centro_banale | – | ✔ 46 656 | ✔ 419 904 | T | § 6.9 |
| ordini_1_2_3_6 | – | ✔ | ✘ (ordine 9) | ✘ (ordine 4) | § 6.7 |
| punti_fissi_potenze_di_3 | – | ✔ | ✔ | ✘ (25 fissi) | B.9, A5 |
| somma_guide_39 | – | ✔ | ✔ | ✘ (somma 38) | § 10.2.1 |
| coniugati_stesso_tipo | – | ✔ | ✔ | T | B.9 |
| stesso_tipo_coniugati | – | ✘ | ✘ | T | § 6.7 + B.9 |
| carta_bersaglio_otto | – | ✔ 729 | ✘ (24 modi) | – | A4 |
| due_carte_forzabili | – | ✘ | ✘ | T | A4 |
| parita_prodotto_locale | – | ✔ | – | – | A10 |
| autoinversa_fattori_involutivi | – | ✔ | – | – | Prop. 5.53 |
| j_fissa_solo_13 | – | ✔ 27/27 | – | – | § 6.10 |
| somme_riconoscono_h | – | ✔ | ✔ | T (Teor. 6.4) | App. D |
| h_normale_in_gamma | – | – | ✔ 139 968 | – | § 11.7 |
| forma_normale_unica | – | – | ✔ 648 | – | Teor. 11.68 |
| stadi_classe_laterale | – | – | – | – | § 11.7.6 (PROCEDURE ✔ 1884) |
| otto_procedure | – | – | – | – | Prop. 9.58 (PROCEDURE ✔ 1728) |
| tavola_quadrato_latino | ✔ 36 | – | – | – | § 8.2 |
| decomposizioni_uniformi | ✔ 36 | ✔ 46 656 | – | – | § 8.5 |

**Metodi** (`Metodo`): ESAUSTIVO, TEOREMA_FONTE, CONTROESEMPIO,
ESPLORAZIONE.
* ESPLORAZIONE esiste (esito NON_DECISA, «non è una prova»), ma nessuna voce
  del catalogo resta in quello stato.
* Su S27 non si enumera mai: `totale = None`. Il risultato viene da un
  teorema citato oppure da un controesempio trovato scorrendo S27 in ordine
  lessicografico (`itertools.permutations` lo garantisce).
* Un test impone che una proprietà vera su H non compaia mai come «legge» di
  S27 per eredità.

## 4. Controesempi

Sono deterministici e minimi nell'ordine dichiarato: lessicografico sulla
lista T; per le coppie, (a, b); per le carte, le quaterne (c1, c2, t1, t2).
Sono riproducibili: il test svuota la cache e riottiene gli stessi
controesempi. Per semplicità, sotto si riportano solo le code delle
permutazioni.

* **S27**: il controesempio è `(…, 24, 26, 25)`, cioè la trasposizione
  (25 26), la seconda permutazione lessicografica. Nega:
  * `punti_fissi_potenze_di_3` (25 punti fissi);
  * `somma_guide_39` (somma 38);
  * `separabile`.
* **S27, ordini**: `(…, 23, 24, 25, 26, 23)`, di ordine 4.
* **S27, commutativo**: la coppia minima è (25 26), (24 25).
* **Γ, ordini**: il minimo lessicografico con ordine 9. **Γ, separabile**: il
  minimo di Γ \ H, in H∘R².
* **Γ, carta_bersaglio_otto**: la carta 0 va in posizione 0 in 24 modi, non 8.
* **A4 su H**: (c1, c2, t1, t2) = **(0, 1, 0, 3)**.
  * **Divergenza registrata:** l'audit citava (0, 1) → (0, 9). È un
    controesempio vero, ma non il minimo.
  * La nota compare nella vista (`nota_audit_0_9`).
* **stesso_tipo_coniugati su H**: una coppia di tipo 1⁹ 2⁹ in classi diverse,
  per esempio (I,I,T) e (T,I,I).

Il riuso di C1/C9/C18 è rimasto in I5 (riconoscimento): nel laboratorio non
serviva a nessuna proprietà del catalogo.

## 5. Conteggi esaustivi (tutti verificati nei test)

* **H**: ordini 1:1, 2:63, 3:26, 6:126; punti fissi 0:152, 1:27, 3:27, 9:9,
  27:1; parità 108/108; 7 tipi ciclici.
* **Γ**: ordini 1:1, 2:63, 3:98, 6:342, 9:144; punti fissi 0:296, 1:243,
  3:99, 9:9, 27:1; 10 tipi ciclici.
* **Chiusura e normalità**: chiusura 216² e 648²; normalità 648 × 216; forma
  normale 648/648; classi laterali 216 / 216 / 216.

## 6. Coniugio: 27 → 7

* `classi_h()` restituisce le 27 classi con numerazione del libro (§ 6.7):
  tipo (f₂, f₁, f₀) in I/T/C, cardinalità, ordine, punti fissi, tipo ciclico
  e rappresentante.
* L'equazione delle classi è 216 = 1 + 2·3 + 3·3 + 4·3 + 6·6 + 8 + 9·3 +
  12·3 + 18·3 + 27.
* Doppio oracolo: le classi legacy (adattatore) coincidono con il coniugio
  esplicito calcolato nel test.
* `fusione_in_s27()` restituisce 7 tipi, in ordine App. B.9:

  | # | tipo | elementi | classi di H |
  |---|---|---|---|
  | 1 | 1²⁷ | 1 | #1 |
  | 2 | 1⁹2⁹ | 9 | #5–7 |
  | 3 | 1³2¹² | 27 | #18–20 |
  | 4 | 1 2¹³ | 27 | #27 |
  | 5 | 3⁹ | 26 | #2–4, #8–10, #17 |
  | 6 | 3 6⁴ | 54 | #24–26 |
  | 7 | 3³6³ | 72 | #11–16, #21–23 |

  Sono verificati su tutti i 216 elementi.
* In nessun punto si dice che H ha 7 classi: la vista e la nota
  `nota_27_classi_7_tipi` dicono il contrario.

## 7. Centro e J

* **Centro**: {#0} (identità). Sono controllate 216 × 216 commutazioni con
  numpy; il calcolo legacy concorda e il test ha un oracolo indipendente.
* **J**:
  * riga **#215** DCS·DCS·DCS, i ↦ 26 − i;
  * ordine 2, tipo 1 2¹³, fissa solo 13;
  * classe **#27 (T,T,T)**;
  * realizzata da 8 procedure: (0,1), (0,2), (0,4), (0,7), (215,0), (215,3),
    (215,5), (215,6).
* La vista distingue il **rovesciamento come gesto** (DP3: prima della
  distribuzione dello stadio) da **J come permutazione finale**. DP3 non è
  stato riaperto.

## 8. Classi laterali e stadi

Quattro oggetti distinti, dichiarati nella vista:

* 216 trasformazioni (H);
* 648 elementi di Γ;
* 1728 configurazioni di stadio (core: distribuisci/raccogli, rovescio sì/no);
* 1728 procedure (I1).

| j | senza rovesci | con rovesci | molteplicità | classe laterale |
|---|---|---|---|---|
| 1 | 6 → 6 | 12 → 12 | 1 | H∘R |
| 2 | 36 → 36 | 144 → 72 | 2 | H∘R² |
| 3 | 216 → 216 | 1728 → 216 | 8 | H |

Configurazioni di stadio e procedure I1 danno la stessa trasformazione in
1728 casi su 1728. I1 è riusato (`servizio_procedure`) senza modifiche.

## 9. Tavola locale 6×6 e decomposizioni

* L'ordine è quello del libro: SCD, SDC, CSD, CDS, DSC, DCS.
* La cella è P ∘ Q con (P∘Q)[i] = P[Q[i]].
* `TAVOLA_LOCALE_FONTE` è trascritta dal § 8.2; il confronto automatico con
  le celle calcolate dal core dà **36/36**.
* Inversi: CDS⁻¹ = DSC, gli altri quattro sono auto-inversi. Tipi: I = SCD;
  T = SDC, CSD, DCS; C = CDS, DSC.
* `decomposizioni_locali(R)` restituisce 6 coppie, con P nell'ordine della
  tavola; le 36 coppie sono tutte distinte.
* `transizione_locale(Y, X)` restituisce R = X ∘ Y⁻¹; l'esempio del § 8.5
  (SDC → CDS con R = CSD) è verificato.
* L'esempio del § 8.4 (P∘Q = SCD⊗DSC⊗SCD) è verificato livello per livello.
* In H, ogni elemento ha 216 = 6³ decomposizioni P∘Q (esaustivo, 46 656).

## 10. Piccoli grafi (solo testo, nessun Canvas)

Ogni grafo dichiara vertici, archi, significato, dominio, orientamento (tutti
non orientati), grado, diametro e distribuzione delle distanze dalla radice.
L'elenco di adiacenza è completo.

| id | dominio | V | E | grado | diametro | distanze |
|---|---|---|---|---|---|---|
| cayley_s3 (trasposizioni, K₃,₃) | S3 | 6 | 9 | 3 | 2 | 1, 3, 2 |
| cayley_h (trasposizione su un livello) | H | 216 | 972 | 9 | 6 | 1, 9, 33, 63, 66, 36, 8 |
| raccolte (una raccolta alla volta) | H | 216 | 1620 | 15 | 3 | 1, 15, 75, 125 |

`cammino()` restituisce un cammino minimo deterministico: a parità di
distanza sceglie il vicino con numero minore. Nessun framework generale per
grafi.

## 11. UI

* **Posizione**: nono sotto-tab dell'Explorer (area analitica), nessun nuovo
  tab di primo livello. I guard D4/D5 sono stati aggiornati; la Guida dice
  «I nove sotto-tab / The nine sub-tabs» e ha una riga per il Laboratorio.
  Non è una riscrittura della Guida (I7).
* **Layout**: intestazione «H — 216 · Γ — 648 · S27» e nota legacy, poi un
  notebook interno con cinque sezioni: Proprietà, Classi, Classi laterali /
  Stadi, Tavola locale 6×6, Grafi.
* **Proprietà**: a sinistra il catalogo (Listbox); a destra i radiobutton dei
  domini (quelli non dichiarati sono disattivati) e il pulsante Verifica.
  Il dettaglio mostra ENUNCIATO, DOMINIO, ESITO (✔/✘ con parole), VERIFICA
  (metodo e conteggi), CONTROESEMPIO (con posizione H/Γ/S27), FONTE e NOTA.
* **Altezza**: la pagina è «compatta» in `_exp_adatta_altezza`, come Matrice
  e Riconoscimento. Nessuna pagina verticale gigante; i testi lunghi scorrono
  nei propri Text.

## 12. i18n e H2

* 161 chiavi `lab.*` IT/EN simmetriche; conteggio del catalogo 1589 → 1750
  (tre test di conteggio aggiornati).
* H2 a 1280×720, 1366×768 e 1920×1080:
  * i controlli sono raggiungibili e ogni sezione sta nella vista;
  * nessuna barra orizzontale;
  * la scrollregion segue il contenuto;
  * l'ordine di Tab è catalogo → domini attivi → Verifica → dettaglio;
  * il resize è stabile, senza cicli di Configure;
  * la vista inglese sta in 1200×640.
* Nessuna informazione affidata al solo colore.
* Explorer → Matrice e Riconoscimento restano intatti: test dedicato, più le
  suite H2 e I5.
* Per arrivare a 1280×720 le altezze dei testi sono passate da 13–15 a
  10–12 righe.

## 13. Suite

Eseguita file per file (i lanci multi-file con più radici Tk possono
chiudersi con il crash intermittente già noto):

* **2179 raccolti = 2177 passati + 1 skipped + 1 failure**;
* la failure è quella nota Tk9, `test_lo_scorrimento_si_accende_quando_il_testo_cresce`;
* rispetto alla baseline (2094/2092/1/1): +85 test, **nessuna nuova failure**.

Test di I1–I5 modificati solo dove l'aggiunta del nono sotto-tab lo
richiedeva:

* `test_riconoscimento_i5_gui` (Riconoscimento non è più l'ultimo sotto-tab);
* `test_documentazione_d4d5`, `test_guida_allineata` e `test_i18n_guida`
  (nove sotto-tab);
* `test_layout_accessibilita_h2` (pagine compatte);
* i tre test di conteggio i18n.

Nessun codice di I1–I5 è stato modificato, a parte `explorer_tab.py`
(registrazione del sotto-tab).

**Architettura**:

* core→services 0, core→gui 0, services→gui 0, services→tkinter 0;
* cicli di import 0;
* parser autorevole 1 (`core.algebra.Parser`);
* pyflakes pulito su `gioco27`.

## 14. Commit

| commit | contenuto |
|---|---|
| `90f7f92` | test(I6): caratterizzazione con oracoli dalle fonti |
| `1f2cc51` | feat(I6): service del laboratorio + test |
| `c86ff7e` | feat(I6): sotto-tab Laboratorio, i18n, guida allineata |
| `5b34568` | test(I6): contratti di layout H2 |
| `f172af4` | fix(I6): guida coerente con i nomi legacy (guard D1) |
| (questo) | docs(I6): chiusura |

## 15. Confine filesystem

* **Scritture discrezionali fuori dal repository: nessuna.**
  * Nessun file in `$HOME`, `/tmp` o scratch come area di lavoro.
  * Le PDF sono state lette solo in pipe; gli script Python sono stati
    eseguiti inline (heredoc, `-B`, `PYTHONDONTWRITEBYTECODE=1`).
  * Questo documento e tutti i file sono stati scritti direttamente nel
    repository; nessuno staging esterno.
  * `scratch/libro.txt` e gli altri residui esterni non sono stati letti.
* **Effetti automatici di runtime/infrastruttura (non usati come
  workspace):**
  * directory temporanee di pytest (`tmp_path`);
  * file di lock/autorizzazione di `xvfb-run`;
  * uso in sola esecuzione del virtualenv esistente;
  * `~/.gioco27`, che l'App può creare o aggiornare (log e configurazione)
    durante i test GUI. Non è stato letto né ispezionato.
* Nessun `__pycache__` nuovo nel repository.
* `Articolo.pdf` e `LIBRO_MAIN.pdf` restano non tracciati e intatti;
  `.gitignore` è invariato.
* Nota di metodo: la sessione è stata compattata durante la fase di lettura
  delle fonti. La parte precedente è attestata dal riepilogo di sessione, che
  riporta lo stesso metodo (sola lettura in pipe, nessun file).

## 16. Debiti e limiti

* **K0**:
  * migrazione dei nomi legacy (G = 216 in `core.group_theory`; H/G_ext in
    altre viste; la Guida resta in notazione G/G_ext);
  * rimangono i debiti I3/I4 già registrati in I5 § 16.
* **Grafi**: sono proposte dell'audit (§ 18.3 [PROP]), non figure del libro.
  Si è scelto di non disegnarli (nessun Canvas).
* **Tipo ciclico nella vista**: è scritto come `1^3 2^12` (testo ASCII), non
  con apici tipografici.
* **Fuori ambito, non fatti**:
  * linguaggio logico generale, export/riproducibilità di J, undo/cronologia;
  * guida completa (I7), livelli DP7, lessico DP8, packaging;
  * b^k, 21 carte, frontend web.
