# I7 — Percorso didattico, guida, glossario e livelli

**Stato: CHIUSO**, con tre righe P0/P1 dell'audit fuori da I7 la cui
giustificazione va approvata (§ 11). Non è stata aggiunta matematica e non
sono stati toccati gli algoritmi di I1–I6. J e K non sono stati iniziati;
nessun push.

| | |
|---|---|
| HEAD iniziale | `7c308c8` (main, `origin/main` = `54445af`, 120 avanti) |
| Baseline | 2179 raccolti · 2177 passati · 1 skipped · 1 failure nota Tk9 |
| Suite finale | **2240 raccolti · 2238 passati · 1 skipped · 1 failure nota Tk9** |
| Test nuovi | 61 (`test_didattica_i7.py` 39, H2 20, D1 +1, guida allineata +1) |
| Catalogo i18n | 1750 → 1960 chiavi per lingua, IT/EN simmetrici |

---

## 1. Audit iniziale (prima fase di I7)

Prima di scrivere ho confrontato UI, guida, glossario, TAB_HELP, onboarding, I1–I6 e le fonti. La matrice
interna aveva le colonne strumento, spiegato?, terminologia, livello, esempio e fonte. Il riepilogo:

| Tipo | Riscontri principali |
|---|---|
| **Funzione senza spiegazione** | Tabellone diretto/inverso, macchina che dimentica, «Una carta», «27 posizioni», ritorno e (R) (I2). Pratica con conseguenze reali, E1–E6 e recupero (I3). Spettatore e B12 (I4). La Guida non nominava né Tabellone, né Pratica, né Spettatore; Riconoscimento e Laboratorio avevano una riga ciascuno. |
| **Spiegazione senza funzione** | La variante «sicura» di I1 esiste nel service ma non ha una vista: ora la Guida lo dice esplicitamente. Nel § 29 c'erano la casella «Modalità principiante» e l'azione rapida «Vai all'Anteprima», entrambe sostituite. |
| **Termine incoerente** | G = 216 e G_ext nei testi utente (Guida § 9, 22, 23, § 16 decomposizioni; finestre Cayley e Coniugio; tooltip). Il glossario era cablato in italiano dentro `glossary.py`. |
| **Riferimento obsoleto** | «capitolo 100» in tooltip, Guida § 29, README e docstring (le statistiche sono in App. B.9 e § 7.1.5–7.1.6). «Posizione 14, il centro» (in base 0 è la 13). «Naviga i sette sotto-tab» (§ 25). «Le tre schede» del Simulatore (sono quattro). |
| **Livello sbagliato** | In Principiante si vedevano Anteprima e Analisi ma non Cicli. Il livello non governava né le sotto-schede né le azioni. Le finestre Cayley e Coniugio erano sempre visibili. |

## 2. Decisioni applicate

### DP2 — H, Γ, S27

Ogni occorrenza è stata classificata prima di migrare.

| Classe | Esito |
|---|---|
| Testi UI (Cayley, Coniugio, tooltip, aiuto del coniugio) | migrati: `H = GEN3³ (\|H\| = 216)`, `Z(H)` |
| Guida (§ 9, 16, 22, 23 e sezioni nuove), glossario, onboarding, TAB_HELP | H = 216, Γ = 648, S27; una sola nota «nel codice storico e nel cap. 6 del libro H è indicato come G» (§ 9 della Guida e voce «Gruppo H» del glossario) |
| Identificatori (`core.group_theory`, `G_ext` interno) | non migrati (K0) |
| Export (`export.document.*`: LaTeX, TXT, SVG, HTML di Cayley e Coniugio) | non migrati: sono formati di output (debito K0) |
| Documenti CLOSED | non toccati |

Il test `test_dp2_nei_testi_utente` sorveglia la migrazione. Fuori da `export.document.*` non devono comparire
`G_ext`, `|G|`, `G = GEN3` o `Z(G)`; H non deve mai valere 648; ogni «648» deve stare accanto a Γ. Il guard D1
(`test_documentazione_d1d3`) è stato riscritto su H/Γ e rifiuta anche «G_ext = ⟨S₃³, MSC⟩».

### DP7 — quattro livelli

Il mapping è dichiarativo, in `gui/livelli.py` (niente Tk), e controlla solo la visibilità.

| Livello | Schede principali | In più |
|---|---|---|
| **Base** | Inizia qui, Simulatore (istruzioni, mazzo, Pratica, Spettatore), Tavola 216 (tabellone, macchina che dimentica, ritorno), Guida | — |
| **Intermedio** | + Anteprima, Cicli | — |
| **Avanzato** | + Explorer (otto sotto-schede, Riconoscimento compreso) | azioni Cayley, Coniugio, Protocollo |
| **Laboratorio** | + Stadio 0/1/2, Analisi, Distribuzione | sotto-scheda Laboratorio I6; Conta, Genera, contatore combinazioni, barra preset |

* **Anomalia storica corretta.** Cicli (Intermedio) compare prima dell'Explorer (Avanzato); Anteprima sta in
  Intermedio; Analisi, Distribuzione e Laboratorio stanno in Laboratorio.
* **Prerequisiti.** `PREREQUISITI` dichiara le dipendenze tra viste e un test verifica che nessuna vista abbia un
  livello inferiore ai suoi prerequisiti (per esempio Analisi e Stadi, Explorer e Cicli).
* **Visibilità senza distruzione.**
  * Schede e sotto-schede vengono nascoste con `state=hidden`.
  * Le azioni della barra usano il nuovo `BarraAdattiva.mostra`, che le esclude senza distruggerle.
  * La barra preset usa `pack_forget` e poi `pack(before=…)`.
  * Se la scheda aperta sparisce si torna a «Inizia qui»; la selezione viene letta prima di nascondere.
  * I dati restano: il test riporta al livello superiore un'espressione scritta nell'Explorer e la ritrova.
* **Selettori.**
  * Una combobox di sola lettura «🎓 Livello» nella barra sostituisce la casella «Modalità principiante».
  * Quattro radiobutton in «Inizia qui».
  * I due selettori restano sincronizzati.
* **Migrazione della configurazione**, esplicita in `core.config`:
  * `principiante` diventa `base`;
  * `esperto` diventa `laboratorio`, così chi vedeva tutto continua a vedere tutto;
  * valori non validi diventano `base`, il default;
  * il valore migrato viene riscritto al salvataggio successivo, ed è testato.
* **Prima apertura**: parte da Base.
* **Compatibilità**: `App._livello` accetta ancora i valori legacy (i test esistenti usano `"esperto"`), e
  `_advanced_tabs` è ora una vista derivata.

### DP8 — lessico narrativo

Il glossario ha una sezione «nomi del libro» con sette alias: Gaia, Cronaca, Giullare/Jester, Mondo-di-Mazzo,
Hari Seldon/Psicostoria, Prima Crisi e Seconda Crisi. Ogni voce rimanda al termine matematico che il libro stesso
indica (Notazioni e convenzioni, pp. xi–xii; § 2.4.5; § 2.5):

* Gaia = il gruppo delle 216 trasformazioni (H);
* Cronaca = una trasformazione;
* Giullare/Jester = J.

Non ho inventato equivalenze. Un test impedisce i nomi narrativi nelle etichette e nei risultati (`lab.*`,
`recognition.*`, `button.*`, `tab.*`, `level.*`); fanno eccezione le fonti citate, che riportano titoli del libro.
«Prima Crisi» resta nella Guida (Simulatore, E1) e nel glossario.

### DP9 — storia

La Parte L, «Storia e cornice narrativa», è facoltativa e dichiarata tale; nessuna istruzione operativa sta lì.
Contiene, solo nella misura sostenuta dal testo:

* Prefazione e Psicostoria;
* Gaal Dornick;
* «Le carte prima della Psicostoria»: Pacioli, Verini 1542, Galasso 1593, Gergonne 1813 con il problema inverso,
  il trucco delle 21 carte, Gardner 1956, Elmsley come parallelo binario e non come derivazione;
* il passaggio dal problema diretto a quello inverso;
* il perché di 27 = 3³.

## 3. Struttura della Guida

La Guida passa da 33 a **41 sezioni in 13 parti**. Ogni sezione ha un identificatore stabile (`s01`…`s33`, `i1`,
`i2m`, `i2t`, `i3`, `i4`, `i5`, `i6`, `storia`); il numero mostrato è la posizione nel percorso. Banner d'aiuto,
`_open_guide` e riferimenti incrociati usano l'identificatore (`numero_sezione`, placeholder `{ref_<id>}`), quindi
riordinare le parti non rompe nessun collegamento.

| Parte | Sezioni (numero · id) |
|---|---|
| A Inizia qui | 1 livelli e interfaccia (s29) · 2 flusso consigliato (s25) |
| B Il gesto fisico | 3 gioco fisico (s01) · 4 Simulatore (s19) |
| C Posizioni e base 3 | 5 coordinate (s02) · 6 MSC (s03) · **7 macchina che dimentica (i2m)** |
| D Tavola e tabellone | 8 P (s04) · 9 J (s05) · 10 Gioco Reale (s10) · 11 Tavola (s11) · **12 tabellone diretto/inverso, (R), ritorno (i2t)** |
| E Permutazioni, inversa, cicli e matrici | 13–15 modello (s06–s08) · 16 Anteprima (s14) · 17 Cicli (s20) · 18 Matrice (s17) · 19 Mescolamento (s18) |
| F Procedure ed equivalenze | **20 procedura, trasformazione, carta al bersaglio (i1)** |
| G Errori e recupero | **21 conseguenze reali, E1–E6, recupero, piano fissato (i3)** |
| H Spettatore | **22 carta ignota, 27 → 9 → 3 → 1, B12 (i4)** |
| I Riconoscimento | 23 Explorer (s16) · **24 Riconoscimento (i5)** · 25 Protocollo (s24) |
| J Struttura di H e Γ | 26 T e i gruppi H, Γ, S27 (s09) · 27 Coniugio (s22) · 28 Cayley (s23) |
| K Laboratorio | 29 Stadi (s12) · 30 preset (s13) · 31 Analisi (s15) · 32 Distribuzione (s21) · **33 Laboratorio I6 (i6)** |
| L Storia (facoltativa) | **34 (storia)** |
| Appendice | 35 glossario (s30, generato) · 36 esempio · 37 formati · 38 LaTeX/SVG · 39 prestazioni · 40 installazione · 41 FAQ |

La Guida spiega come si usa il programma e rimanda alla matematica: non duplica capitoli del libro. Sono state
riscritte le sezioni che non erano più vere: § 1 (base 0), § 9 (DP2), § 19 (quattro schede), § 25 («sette
sotto-tab», Gioco Reale ora in Laboratorio), § 29 (livelli, azioni rapide, «capitolo 100»), § 31, FAQ 1.

## 4. Copertura di I1–I6

Il test `test_ogni_funzionalita_i1_i6_ha_una_spiegazione` controlla la copertura in IT ed EN.

| Compartimento | Dove | Contenuto |
|---|---|---|
| I1 | § 20 | procedura (#, m); 216 × 8 = 1 728; 8 procedure per trasformazione (esempio J); le tre relazioni; fibra di 64; costi k1/k2/k3; strategia storica (= Simulatore, 729/729) e variante sicura (386 coppie diverse, senza vista); controesempio «stessa carta ≠ stessa trasformazione» |
| I2 | § 7, § 12 | tabellone diretto/inverso, ternario, macchina che dimentica (P′ = ⌊P/3⌋ + 9·s), n → Π(n) → n′, rev ω(n), ε, (R), ritorno; controesempio T(10) = 5 ≠ T⁻¹(10) = 6 |
| I3 | § 21 | le due modalità; ordine fisico; E1–E6 con perimetro (E6 solo catalogo); previsto ≠ eseguito; recupero; perché E1 ed E4 non si recuperano; piano fissato |
| I4 | § 22 | 27 → 9 → 3 → 1; protocollo adattivo; ordine noto; B12 con l'esempio #100 |
| I5 | § 24 | separabilità, riconoscimento diretto, somme di fibra (formula e C₀, C₁, C₂), avanti/indietro, Teor. 6.4, due guide, A1, A8, v → w, C1/C9/C18; controesempio delle somme equilibrate («intero non basta») |
| I6 | § 33 | dominio di una proprietà; H/Γ/S27/Procedure; metodi; 27 → 7; centro; J; stadi; 6×6; grafi; controesempi |

## 5. Glossario

Il glossario passa da 14 a **43 voci**, 36 matematiche e 7 narrative. «Inizia qui» e la Guida (§ 35, generata)
usano la stessa fonte (`GLOSSARIO_*`, chiavi `glossary.term/short/long.*`).

* **Termini richiesti tutti presenti:**
  * carta, posizione, mescolamento, impilamento;
  * tabellone e tabellone inverso;
  * procedura, trasformazione, permutazione, inversa;
  * ciclo, ordine, punto fisso;
  * fibra, separabilità digitale, fattore locale, somma di fibra;
  * forma canonica, classe di coniugio;
  * gruppo H, gruppo Γ, S27, centro, classe laterale;
  * ritorno, carte guida, recupero.
* **Voci aggiunte**: macchina che dimentica, J/orientazione, Kronecker, Cayley e le voci precedenti.
* **Simmetria**: IT/EN simmetrici, senza placeholder.
* **Testo cablato rimosso**: le vecchie tuple con testo italiano cablato (`GLOSSARY`) sono ora solo chiavi
  (compatibilità).

## 6. Onboarding, TAB_HELP e aiuti

* **«Inizia qui»**:
  * riquadro «Quattro livelli»: consiglia Base, dice che gli strumenti non vengono rimossi, permette di scegliere
    subito Laboratorio;
  * tre passi aggiornati;
  * azioni rapide Simulatore / Tavola 216 / Guida: «Vai all'Anteprima» e «Carica Gioco Reale» puntavano a viste
    dei livelli superiori;
  * glossario in due parti.
* **TAB_HELP e sotto-schede.** `SOTTOSCHEDE_HELP` associa a ogni sotto-scheda una riga d'aiuto, che compare
  nell'aiuto esteso («Mostra di più») della scheda madre:
  * Simulatore: 4 sotto-schede, con Pratica e Spettatore;
  * Tavola: 3 (tabellone, una carta, 27 posizioni);
  * Explorer: le **nove** sotto-schede per nome;
  * Cicli: 2.

  Ogni riga dice cosa mostra, quali dati usa e l'eventuale convenzione critica.
* **Nessuna stringa italiana cablata** nei widget di onboarding (test).

## 7. Esempi didattici

Ogni esempio insegna un punto preciso ed è verificato con il core da `test_esempi_citati_esistono`.

| Esempio | Dove | Punto |
|---|---|---|
| #100 (carta 19; ritorno #93; T(10) = 5, T⁻¹(10) = 6; B12) | § 7, § 12, § 22, § 24 | registro; diretto ≠ inverso; ritorno |
| #91 | § 24 | gemelli #100/#91 (A8) |
| #56 ↔ #62 | § 12 | ritorno reciproco |
| #62 | § 12 | idem |
| C1 / C9 / C18 | § 21, § 24 | taglio fuori da H e da Γ / C9 = #144, C18 = #108 |
| posizione 13 | § 3, § 22, glossario | centro del mazzo, B12 |
| 19 = (2,0,1) = DSC | § 7, glossario | indirizzo |
| 36/117/198 | § 24, glossario | somme dei blocchi |
| 27 → 9 → 3 → 1 | § 22 | dinamica informativa |
| #172, #111/#112/#147 | § 21 | E2 finale = J∘T; E1 |
| #195 | § 24 | § 2.4.8: mazzo finale = T⁻¹ |

**Controesempi** esplicitati:

* stessa carta ≠ stessa trasformazione (§ 20);
* inverso ≠ lettura rovesciata (§ 12);
* E1/E4 non recuperabili (§ 21);
* somme equilibrate (§ 24);
* ordine 9 in Γ, scambio in S27, A4 (0, 1) → (0, 3) (§ 33).

## 8. H2 e accessibilità

Nuovi test in `test_layout_accessibilita_h2.py` alle geometrie 1280×720, 1366×768 e 1920×1080:

* **Selettore di livello**: raggiungibile a ogni livello, dentro la finestra e senza voci perse.
* **Onboarding**:
  * i quattro radiobutton sono nella vista;
  * il Canvas non scorre in orizzontale;
  * l'ordine di Tab li percorre in fila;
  * la pagina sta in 1280 in IT e in EN.
* **Guida**:
  * `wrap=word` e nessuna barra orizzontale;
  * 41 ancore;
  * `_open_guide` porta in vista le sezioni s12, i3, i6, storia e s30.
* **Informazione non affidata al solo colore**: parti e livelli si leggono dalle parole, non dal colore.

Explorer → Matrice, Riconoscimento e Laboratorio restano verdi (suite H2, I5 e I6).

## 9. i18n

* Catalogo: +210 chiavi nette; rimosse le chiavi obsolete, tra cui `button.beginner_mode`,
  `tooltip.beginner_mode`, `onboarding.button.go_preview`, `guide.s30.terms` e `guide.s29.mode.items`.
* Aggiornati i tre test di conteggio.
* Oltre ai conteggi, due test sulle chiavi:
  * ogni chiave `guide.*` viene davvero usata nella costruzione della Guida (spia su `tr`);
  * ogni chiave nuova `level.*`, `help.sub.*`, `onboarding.*` o `glossary.*` è referenziata nel codice o
    appartiene a una famiglia dichiarata.
* Le frasi IT/EN hanno la stessa forma, con gli stessi numeri e le stesse formule (test esistenti adeguati).

## 10. Test di allineamento

In `test_guida_allineata`, `test_i18n_guida` e `test_didattica_i7`:

* 9 sotto-tab dell'Explorer, esistenti e descritti;
* ogni scheda principale ha il suo aiuto;
* ogni voce di livello punta a una scheda, sotto-scheda o azione esistente, e i livelli sono documentati come nel
  mapping;
* nessuna vista ha un livello inferiore ai suoi prerequisiti;
* DP2 nei testi utente;
* glossario simmetrico;
* copertura di I1–I6;
* nessun «capitolo 100», nessun numero di sotto-tab o modalità obsoleti;
* gli esempi citati esistono e tornano col core;
* banner e riferimenti incrociati puntano a sezioni esistenti.

## 11. Matrice di completezza P0/P1 (delta rispetto a `V4_COVERAGE_MATRIX.csv`)

Il vecchio audit e il CSV non sono stati toccati. La matrice I7 è eseguibile: `COPERTURA_AUDIT` in
`test_didattica_i7.py` associa ogni riga V4-P0/P1 a una sezione della Guida e a una frase, e il test verifica che
quella frase sia davvero lì.

| Esito | Righe |
|---|---|
| **D = sì dopo I7** (41 righe) | L04 L05 L06 L07 L08 L09 L10 L12 L14 L15 L18 L20 L21 L22 L23 L26 L35 L36 L39 L44 L46 L54 L55 L57 L58 L59 L63 L67 L70 L81 L91 L93 L95 L97 L106 · A02 A04 A06 A07a A09 A12 (ramo 27) |
| **Fuori da I7, giustificazione da approvare** (3 righe) | **L11**: Prop. 1.8, elemento mancante di un blocco dalle somme; nessuno strumento lo calcola, servirebbe matematica nuova (la firma 36/117/198 è spiegata). **L90**: tabellone cumulativo di una successione di procedure; non esiste nel programma. **A13**: formula di inversione di App. D Cor. 5.2 con rovesciamenti; fonte ambigua (audit § 2.2), nessuna decisione (rovesciamento e fibra di 8 sono spiegati). |
| Ramo 21 di A12 | oltre il perimetro 4.0 per l'audit stesso; citato solo nella storia |

## 12. Suite

La suite è stata eseguita file per file (56 file):

* **2240 raccolti, 2238 passati, 1 skipped, 1 failure**;
* la failure è quella nota Tk9, `test_lo_scorrimento_si_accende_quando_il_testo_cresce`: **nessuna nuova
  failure**;
* comprese la baseline matematica (25/25) e le suite I1–I6.

**Architettura**:

* core→services 0, core→gui 0, services→gui 0, services→tkinter 0;
* cicli di import 0;
* un solo parser autorevole;
* pyflakes pulito.

**Test esistenti adeguati**, solo dove il comportamento documentato è cambiato di proposito:

* numero di sezioni e segmenti della Guida;
* ancore per identificatore;
* D1 (DP2);
* conteggi i18n;
* livello «esperto» nel test di hardening, perché ora viene migrato;
* `Z(H)`;
* azioni rapide e passi di onboarding;
* test «schede nascoste in Principiante», sostituito da «livelli documentati come nel mapping».

## 13. Confine filesystem

* **Scritture discrezionali fuori dal repository: nessuna.** Il PDF del libro è stato letto solo in pipe
  (`pdftotext … - | grep/sed`).
* **File di lavoro nel repository.** Tre script di supporto (applicazione dei testi i18n, testi della Guida,
  estrazione delle sezioni) stavano in `.git/i7tmp/`, dentro il repository e mai tracciati. Li ho cancellati prima
  della chiusura.
* **Lock di git.** A metà di I7 la sessione non poteva più cancellare i lock di git (`index.lock`, `HEAD.lock`).
  Ho chiesto e ottenuto dall'utente il permesso di cancellare dentro la cartella del repository, e l'ho usato solo
  per quei lock, i `tmp_obj_*` di git e `.git/i7tmp`.
* **Metadati della macchina.** Per quella richiesta ho chiamato `get_device_info`, che restituisce anche i *nomi*
  delle cartelle di primo livello della home dell'utente. Non ho elencato né letto nessuna di quelle cartelle. Lo
  registro per trasparenza.
* **Effetti automatici di runtime** (non usati come area di lavoro):
  * directory temporanee di pytest (`tmp_path`, compresi i test di migrazione della configurazione);
  * lock e autorizzazioni di `xvfb-run`;
  * esecuzione del virtualenv esistente;
  * `~/.gioco27`, che l'App può creare o aggiornare nei test GUI; non l'ho letto.
* **Non letti**: `scratch/libro.txt` né altri residui.
* **Invariati**: `Articolo.pdf` e `LIBRO_MAIN.pdf` restano non tracciati e intatti; anche `.gitignore` non è
  cambiato.

## 14. Debiti residui

* **K0**:
  * `export.document.*` (LaTeX, TXT, SVG, HTML di Cayley e Coniugio) scrive ancora G = GEN3³;
  * restano gli identificatori legacy G/H/G_ext.
* **Matrici a livello Intermedio.** La vista delle matrici 27×27 è la sotto-scheda Matrice dell'Explorer
  (Avanzato). A livello Intermedio si vedono T e T⁻¹ nell'Anteprima e nei Cicli, ma non c'è ancora un collegamento
  contestuale alla sola Matrice: esporla da sola avrebbe richiesto un'eccezione nel mapping.
* **Aiuti delle sotto-schede.** Stanno nell'aiuto esteso della scheda madre, non in un banner per ogni sotto-scheda:
  un banner in più avrebbe tolto altezza alle pagine compatte a 1280×720.
* **Variante sicura di I1**: descritta, ma ancora senza vista.
* **Righe L11, L90 e A13** (§ 11): da approvare, oppure da assegnare a un compartimento successivo.
* **Lunghezza della Guida.** Le sezioni storiche del modello algebrico (§ 13–15, § 37–40) sono rimaste com'erano,
  salvo le correzioni; ora 41 sezioni.
* **Azioni sempre visibili**: Presentazione, Verifica, Impostazioni ed Esci compaiono a tutti i livelli.

## 15. Commit

| Commit | Contenuto |
|---|---|
| `307c137` | feat(I7): quattro livelli dichiarativi e migrazione della config |
| `8c84bf1` | docs(I7): via il riferimento «capitolo 100» (README, docstring) |
| `e7ad4ad` | feat(I7): percorso della Guida, glossario, onboarding, aiuti, DP2 |
| `56e04d8` | test(I7): allineamento didattico, livelli, H2 |
| `2d1ebfb` | docs(I7): lacune didattiche P0/P1 e matrice eseguibile |
| (questo) | docs(I7): chiusura |
