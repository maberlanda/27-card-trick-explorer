# I4 — Spettatore e dinamica informativa: chiusura

Compartimento I4 della 4.0: il Gioco delle 27 carte quando la carta pensata non è nota all'esecutore. Il
compartimento separa, nel service, nella vista e nei test, due dinamiche:

* **dinamica fisica**: il mazzo evolve per permutazioni biiettive;
* **dinamica informativa**: si restringe l'insieme delle posizioni iniziali candidate, 27 → 9 → 3 → 1.

**Etichette di provenienza**:

| Etichetta | Significato |
|---|---|
| **FONTE** | libro (`LIBRO_MAIN.pdf`) o articolo (`Articolo.pdf`), letti direttamente |
| **CODICE** | lettura del codice |
| **TEST** | test del repository |
| **ESEC** | esecuzioni fatte in questa sessione |
| **INFERENZA** | deduzione argomentata dalle voci precedenti |

## 1. Baseline d'ingresso

ESEC:

| Voce | Atteso | Trovato |
|---|---|---|
| branch | `main` | `main` |
| HEAD | `3755369` | `3755369 docs(I3): close physical errors and recovery compartment` |
| `origin/main` | `54445af` | `54445af` |
| ahead | 89 | 89 |
| working tree tracciato | pulito | pulito |
| non tracciati | i due PDF | `Articolo.pdf`, `LIBRO_MAIN.pdf` |
| `test_baseline_matematica.py` | 25 passed | 25 passed |
| suite dopo I3 | 1664 / 1662 / 1 / 1 | confermata (§ 17) |

## 2. Fonti verificate

FONTE, lette direttamente dal PDF (estrazione su stdout, senza file intermedi):

| Punto | Contenuto usato |
|---|---|
| § 1.6 «La macchina che dimentica» | le stesse lettere S, C, D scrivono un indirizzo statico **o** raccontano la storia delle distribuzioni; la prima distribuzione classifica per resto modulo 3, cioè rivela la cifra fine `n0` |
| § 1.9 | ogni lettera restringe le posizioni compatibili: 9, 3, 1. Prop. 1.6: la storia delle distribuzioni è `rev ω(n)`, **indipendente dalle raccolte** («i termini introdotti dalle ricomposizioni possiedono pesi divisibili per 3»). § 1.9.1: la storia dipende dall'origine, la destinazione dalle raccolte |
| § 7.1.11 A11 | `n = a1 + 3 a2 + 9 a3`, «la prima risposta vale le unità». Esempio 17 = (1, 2, 2), risposte 2, 2, 1 |
| § 7.2.2 B1 | premessa (ordine iniziale noto), procedura, esempio C, D, S → 7. Limite onesto: senza ordine noto la carta non si nomina |
| § 7.2.13 B12 | protocollo completo (§ 11), esempio #100 |
| § 11.11.5 | due dinamiche: «Non è dunque il mazzo a perdere informazione [...] È l'insieme delle ipotesi dell'osservatore a restringersi». Usato solo come confronto concettuale (21 carte) |
| Articolo, App. A | stessa distinzione, sul caso rettangolare (21 carte, `F_c` molti-a-uno) |

**Convenzione verificata, non assunta.** TEST (`test_esempio_a11_posizione_17`, `test_le_27_terne_…`,
`test_l_ordine_delle_cifre_non_e_quello_opposto`):
* la risposta `a_k` è la cifra `n_{k−1}`;
* l'ordine opposto `9a1 + 3a2 + a3` sbaglia su 18 posizioni su 27: coincide solo sulle 9 parole palindrome.

**Nel 27 e nel 21 le posizioni candidate non sono dello stesso tipo.**
* Nel 27 (I4) sono **posizioni iniziali**.
* Nel 21 (§ 11.11, fuori perimetro) sono posizioni correnti, perché lì la mappa `F_c` è molti-a-uno.

Il 21 non è implementato.

## 3. Modello informativo

CODICE `services/spettatore.py`. `SessioneSpettatore` è immutabile e registra **solo i fatti**:

| Campo | Significato |
|---|---|
| `bersaglio` | t |
| `mazzo_iniziale` | carte per posizione iniziale; `None` = ordine ignoto (B12) |
| `risposte` | `(a1, …)` nel tempo, 0 = S, 1 = C, 2 = D |
| `raccolte` | mescolamenti eseguiti, uno per fase conclusa |

Tutto il resto **si deriva** e non viene memorizzato come verità indipendente:

| Grandezza | Funzione | Dinamica |
|---|---|---|
| mazzo corrente, per posizione iniziale | `ordine_corrente` | fisica, una permutazione |
| distribuzione della fase | `distribuzione_corrente` | fisica |
| dove stanno ora le carte candidate | `posizioni_correnti_dei_candidati` | fisica, immagine biiettiva di X_k |
| X_k | `posizioni_iniziali_candidate` | informativa |
| posizione iniziale, se unica | `posizione_iniziale_determinata` | informativa |
| carta, se unica e con ordine noto | `carta_determinata` | informativa |
| fase 0..3, attesa della raccolta, conclusa | proprietà | controllo |

**X_k si calcola dalla fisica**, come intersezione con le carte del mazzetto indicato lette per posizione iniziale.
L'aritmetica delle cifre resta come oracolo nei test: i due calcoli coincidono su tutte le 27 terne. Non esiste una
«permutazione parziale».

## 4. API del service

| API | Contratto |
|---|---|
| `avvia_spettatore(bersaglio, mazzo_iniziale=None)` | X0 = {0, …, 26} |
| `scelta_raccolta(bersaglio, fase, risposta)` | **l'unico punto** in cui si sceglie la raccolta; chiama `gioco_reale.mescolamento_per_colonna` (la regola per fase estratta in I3) |
| `rispondi(s, risposta)` | registra una risposta, validata |
| `risposte_possibili(s)` | le risposte che non svuotano X_k |
| `esegui_raccolta(s, mescolamento=None)` | senza argomento: la scelta adattiva. Una sigla esplicita è ammessa per caratterizzare l'indipendenza dalle raccolte, ma allora il bersaglio non è garantito |
| `storia_informativa(s)` → `PassoInformativo` | per fase: risposta, indice della cifra, candidati prima e dopo, sede, raccolta, se adattiva |
| `esito(s)` → `Ricostruzione` | risposte, storia, n, cifre, ω(n), carta, raccolte, `ProceduraGioco`, numero della disposizione, posizione finale, bersaglio raggiunto, protocollo adattivo |
| `RiavvolgimentoB12`, `avvia_b12(impilamenti_osservati)` | B12 (§ 11) |
| `RispostaNonAccettata(ValueError)` | `codice` stabile e `dati`, sul modello di `procedure.ProceduraNonValida`: `risposta_fuori_dominio`, `risposta_incoerente`, `raccolta_in_sospeso`, `risposta_mancante`, `sessione_conclusa`, `raccolta_fuori_dominio` |
| `lettera_mazzetto(g)` | nome del mazzetto = ultima lettera di `gioco_reale.parola(g)` (I2) |

Il service è puro: niente Tk, niente testo, niente I/O (TEST `test_il_service_e_puro`).

## 5. 27 → 9 → 3 → 1

TEST:
* per ognuna delle 27 terne, la cardinalità di X_k vale 27, 9, 3, 1 e X_k coincide con l'oracolo aritmetico
  `{x : cifre di x = risposte}`;
* nei 729 casi (§ 9) la sequenza è la stessa e il candidato finale è la posizione iniziale reale;
* dopo ogni passo il mazzo resta una permutazione di 27 elementi, e le posizioni correnti dei candidati sono
  tante quante i candidati.

## 6. Protocollo adattivo

La sequenza è: risposta → `scelta_raccolta(t, k, a_k)` → gesto → nuovo stato. Nulla viene precalcolato: la
raccolta della fase k esiste solo dopo la risposta k. Il mazzetto indicato va nella sede `t_{k−1}`, la cifra k
del bersaglio nell'ordine del tempo (TEST `test_esempi_didattici`: `M(a_k) = sede`).

**Nessuna scorciatoia sulla carta**, TEST strutturali:
* la firma di `scelta_raccolta` è esattamente `(bersaglio, fase, risposta)`;
* nessun parametro «carta» in `rispondi`, `esegui_raccolta` e `avvia_spettatore`;
* i campi della sessione sono esattamente i quattro del § 3;
* il nome `risolvi_trucco` non compare nel codice del service (AST; è solo citato nella docstring);
* `mescolamento_per_colonna` è chiamato in un solo punto.

Nella vista, `sp.esegui_raccolta` è chiamato sempre senza sigla.

## 7. Modalità A — ordine iniziale noto (B1)

**Nota all'inizio**: l'ordine del mazzo (identità C00…C26, oppure mescolato e mostrato).

**Osservazioni**: tre risposte S/C/D.

**Determinato alla fine**: la posizione iniziale n, la carta `mazzo_iniziale[n]` e la posizione finale t.

TEST: con 10 mazzi mescolati × 27 posizioni, la carta resta indeterminata dopo due risposte, è determinata dopo tre
e differisce dalla posizione.

## 8. Modalità B12 — ordine iniziale ignoto

Protocollo ricostruito dal § 7.2.13, FONTE:

1. lo spettatore sceglie una carta e la rimette nel mazzo; l'ordine è ignoto all'esecutore;
2. l'esecutore osserva tre raccolte, cioè gli impilamenti R0, R1, R2, e ne ricava `M_i = R_i⁻¹`;
3. ricava il tabellone T della disposizione osservata;
4. calcola `T⁻¹`;
5. lo realizza come in (R): `tabellone.ritorno`, già di I2. Il mazzo torna com'era prima delle raccolte osservate;
6. a ogni distribuzione chiede in quale mazzetto sta la carta e lo raccoglie **in mezzo**;
7. dopo tre interrogazioni la carta è in posizione 13.

| | B12 |
|---|---|
| noto all'inizio | gli impilamenti osservati; non l'ordine, non la carta |
| osservazioni | le tre raccolte osservate, poi tre risposte S/C/D |
| determinato alla fine | la posizione della carta nel mazzo riavvolto (n) e la sua posizione finale (13) |
| **non** determinato | l'identità della carta: `carta = None`. La si può mostrare solo girando la carta in 13 |

**Scelte di prodotto**, INFERENZA dichiarata, nessuna inventata:
* **«In mezzo» = sede C.** Coincide con `scelta_raccolta(13, k, a)`: 13 = (1, 1, 1), quindi la regola unica basta
  e non ne serve una seconda.
* **Riavvolgimento facoltativo.** La fonte lo dice «non indispensabile»; qui è eseguito, come nella procedura del
  libro.
* **Nessun bersaglio diverso da 13** in B12, perché la fonte non lo prevede.
* **Le posizioni «iniziali»** della sessione B12 sono quelle del mazzo riavvolto, come scritto nella docstring di
  `avvia_b12`.

TEST:
* esempio #100: R = (DSC, DSC, CSD) → M = (CDS, CDS, CSD) → #100; ritorno con impilamenti (CDS, CDS, CSD), come
  nel libro;
* esaustivo sulle 216 disposizioni osservate × 27 posizioni, con un mazzo di facce casuali ignote al service:
  `T⁻¹T = I`, n determinato, carta 13, identità `None`.

**Nessun blocker.** La fonte è completa per la parte implementata.

## 9. I 729 casi carta → bersaglio (gate centrale)

Per ogni c ∈ 0..26 e t ∈ 0..26, uno spettatore onesto risponde leggendo la propria carta nei mazzetti
(`test_i729_casi_carta_bersaglio`). Esito:

| Verifica | Esito |
|---|---|
| 27 → 9 → 3 → 1 | 729/729 |
| candidato finale = c | 729/729 |
| raccolte adattive = `risolvi_trucco(c, t)["mescolamenti"]` (DP5 storico) | **729/729** |
| risposte = `risolvi_trucco(c, t)["colonne"]` | 729/729 |
| numero di disposizione uguale | 729/729 |
| posizione finale = t, via `esito` | 729/729 |
| posizione finale = t, rigiocando il mazzo col core fisico (oracolo indipendente) | **729/729** |

## 10. Le 27 terne

TEST `test_le_27_terne_identificano_27_posizioni`: la mappa (a1, a2, a3) → n è totale (27 chiavi), iniettiva
(27 immagini distinte) e suriettiva (immagine {0, …, 26}). Vale `n = a1 + 3a2 + 9a3` per ognuna. Lo stesso
risultato è confermato con oracolo indipendente in `test_le_27_terne_sono_una_biiezione` (caratterizzazione).

## 11. Identificazione ≠ controllo della destinazione

| Proprietà | Dominio | Esito |
|---|---|---|
| storia = rev ω(n) con **qualunque** raccolta (Prop. 1.6), solo core fisico e aritmetica | 27 × 216 = 5832 | ✔ |
| idem con un mazzo iniziale mescolato | 20 mazzi × 27 | ✔ |
| identificazione indipendente dalle raccolte, via service | 27 × 216 | ✔ |
| identificazione indipendente dal bersaglio | 27 × 27 | ✔ (risposte e n uguali per ogni t) |
| destinazione: per ogni (c, t) esattamente **8** terne su 216 portano c in t | 27 × 216 | ✔ |

INFERENZA: l'8 è la fibra 8:1 già nota (27 × 8 = 216). Il bersaglio lo decidono le raccolte; il significato delle
risposte no.

## 12. Risposte coerenti e incoerenti

**Legge del 27.** TEST, caratterizzazione e service: con distribuzione corretta, **ogni** risposta S/C/D è sempre
possibile, qualunque siano le raccolte (216 terne × 9 coppie di risposte).

Il motivo, per INFERENZA confermata dal TEST: dopo k risposte i candidati occupano un blocco di 3^(3−k) posizioni
consecutive, che la distribuzione ripartisce in parti uguali fra i tre mazzetti.

Il controllo esiste comunque:
* `risposte_possibili` elenca le risposte ammesse;
* `rispondi` rifiuta con `risposta_incoerente` quella che svuoterebbe X_k.

Il test forza lo stato impossibile con un monkeypatch, perché nel 27 lo stato non si produce. Anche gli altri
passi fuori contratto sono rifiutati con codici tipizzati: dominio, turno, fine sessione, sigla.

## 13. Distinzione fisico / informativo

| Luogo | Fisico | Informativo |
|---|---|---|
| service | `ordine_corrente`, `distribuzione_corrente`, `posizioni_correnti_dei_candidati`, `raccolte` | `posizioni_iniziali_candidate`, `posizione_iniziale_determinata`, `carta_determinata`, `storia_informativa` |
| vista | riquadro «STATO FISICO — il mazzo» | riquadro «STATO DELL'INFORMAZIONE — ciò che sa l'esecutore» |
| testo | «Posizioni attuali occupate dalle carte candidate» | «candidati prima / dopo», come posizioni **iniziali** |

Nessun testo dice che il mazzo «perde informazione» o che la permutazione «collassa» (TEST su tutte le chiavi
`spectator.*` IT/EN). La nota fissa della vista dice che ogni raccolta è una permutazione annullabile e che si
restringe soltanto l'insieme delle posizioni iniziali compatibili.

## 14. Integrazione con I1, I2 e I3

| Compartimento | Uso |
|---|---|
| I1 | `ProceduraGioco` nell'esito; DP3 e DP5 preservati (il confronto è con il default storico di `risolvi_trucco`) |
| I2 | `gioco_reale.digits3`, `parola` e `posizione_da_parola` per la ricostruzione (`n = ω⁻¹(rev storia)`) e per le parole parziali «??C»; `tabellone.ritorno` per B12. Nessuna seconda codifica ternaria |
| I3 | `mescolamento_per_colonna` come unica regola. Il catalogo E1–E6 non è riaperto; E4 (colonna sbagliata con carta tracciata) resta distinto dalla risposta dello spettatore. La risposta **errata** dello spettatore è **rinviata** (facoltativa, non necessaria ai gate) |

Moduli esistenti non modificati: core, `services.procedure`, `tabellone`, `errori`, `pratica_reale`, `tavola_tab` e
`app`. Il diff tocca solo `simulator_tab.py` (5 righe: import e aggiunta della sotto-scheda) e `i18n.py` (solo chiavi
nuove).

## 15. UI

**Collocazione**: una quarta sotto-scheda del Simulatore, **«👁 Spettatore (carta ignota)»**
(`gui/spettatore_tab.py`, `SpettatoreFrame`).
* È un modulo a sé, non un mixin: `simulator_tab` lo importa in un solo verso, quindi non può nascere un ciclo.
* Non duplica il Simulatore: riusa solo i nomi delle colonne del catalogo.
* La Pratica storica e le Conseguenze reali di I3 restano invariate (TEST).
* Il Simulatore è visibile a tutti i livelli e la logica dei livelli non cambia, quindi **DP7 non è decisa**.

| Richiesta | Controllo |
|---|---|
| scelta del bersaglio | Spinbox 0..26 (in B12 fisso a 13 e disabilitato) |
| avvio della sessione | «Avvia la sessione»; ordine noto o ignoto; mazzo mescolato; impilamenti osservati per B12 (predefiniti: esempio #100) |
| distribuzione corrente | Treeview S / C / D, 9 righe, con le facce |
| risposta S/C/D | tre pulsanti «S — Sinistra», «C — Centro», «D — Destra» |
| raccolta scelta | etichetta visibile **prima** del gesto: mazzetto, sede, posizioni, impilamento, mescolamento; poi «Esegui la raccolta» |
| avanzamento di fase | «Distribuzione della fase k» |
| candidati | elenco completo delle posizioni iniziali, prima e dopo ogni risposta |
| conteggio | `27 → ▶[9] → 3 → 1` |
| cifra acquisita | «risposta C (1) → cifra n0 = 1 · parola della posizione iniziale ??C» |
| ricostruzione | risposte, `n = a1 + 3·a2 + 9·a3 = …`, cifre, ω(n) e storia rovesciata, carta o «non determinata», controllo della destinazione |
| posizione e carta finali | nel riquadro fisico e nella ricostruzione |

## 16. i18n e accessibilità

**i18n**:
* 46 chiavi `spectator.*`, simmetriche IT/EN; il totale sale a 1487 (TEST aggiornati: `test_i18n`, `…_audit_finale`,
  `…_anomalie_ui`).
* Ogni codice d'errore del service ha il suo testo in entrambe le lingue.
* Il service non contiene testo.
* Nessun termine fra Gaia, Cronaca, Giullare, H, Γ, G_ext: DP2 e DP8 non sono toccate.
* Guida, glossario, `TAB_HELP` e onboarding **non** modificati.
* Il testo inline minimo è l'introduzione, la nota del riquadro informativo e la frase del bersaglio in B12.

**H2**, TEST in `test_layout_accessibilita_h2.py` (10 nuovi):

| Contratto | Esito |
|---|---|
| raggiungibilità a 1280×720, 1366×768 e 1920×1080, prima della prima risposta e dopo la ricostruzione | nessun controllo perso; nessuno scorrimento orizzontale (Simulatore 1003 px, vista 879 px, ESEC) |
| ordine di Tab | ordine → bersaglio → mescolato → avvio → mazzetti → S/C/D → testo fisico → testo informativo |
| alternative testuali | Text di sola lettura che prendono il fuoco; Treeview raggiungibile |
| niente solo colore | `▶[n]` nel conteggio, `⚠` negli errori, riquadri titolati |
| ridimensionamento | barre stabili, nessun ciclo |
| inglese | lingua forzata prima di costruire il frame; ≤ 1240 px |
| Canvas | nessuno nuovo (`test_i_canvas_del_programma_sono_censiti` invariato) |

I test H2 di I4 sono passati alla prima esecuzione: nessun difetto di layout da correggere.

## 17. Architettura e suite

**Architettura**, ESEC (AST inline) e TEST (`test_lifecycle_persistenza_g2.py` 45, `test_static.py` 2,
`test_servizi_g1.py` 44):

| Invariante | Valore |
|---|---|
| core → services | 0 |
| core → gui | 0 |
| services → gui | 0 |
| services → tkinter | 0 |
| cicli applicativi | 0 |
| parser autorevoli | 1 |

`services.spettatore` dipende da `core` (`gioco_reale`, `dominio`) e da `services.tabellone` / `procedure`.
`gui.spettatore_tab` dipende da `core`, `services` e `gui.i18n`.

**Suite**: 49 file, uno per volta sotto xvfb.

| Insieme | Esito |
|---|---|
| I4: caratterizzazione | 229 passed |
| I4: service | 63 passed |
| I4: vista | 17 passed |
| I4: H2 | 10 passed |
| baseline matematica | 25/25 |
| I1, I2, I3 | 18 + 41 + 19; 48 + 22 + 12; 35 + 18: tutti verdi |
| **suite completa** | **1983 raccolti: 1981 passed, 1 skipped, 1 failed** |

* **Skipped**: `test_layout_dettaglio.py` (manca `pypdfium2`).
* **Failed**: `test_layout_accessibilita_h2.py::test_lo_scorrimento_si_accende_quando_il_testo_cresce`, il noto
  fallimento ambientale di Tk 9.0.4, non toccato.
* **Rispetto a I3**: 1664 + 319 = 1983. Nessuna nuova regressione.

## 18. Tensioni e limiti

1. **«Risposta incoerente».** La consegna chiede di non accettarla in silenzio. Nel 27 standard non esiste: è una
   legge, caratterizzata. Il controllo è presente e provato forzando lo stato.
2. **Posizioni candidate.** Nel 27 sono posizioni **iniziali**; nel 21 del libro (§ 11.11) sono posizioni
   correnti. La vista mostra le posizioni correnti dei candidati solo nel riquadro fisico, come immagine biiettiva.
3. **Riavvolgimento in B12.** È una scelta di costruzione della routine, non una necessità logica (fonte). È
   eseguito e dichiarato.
4. **Bersaglio di B12.** In B12 è 13 perché così dice la fonte; altri bersagli non sono proposti.
5. **Il 13 della consegna.** Fra i «bersagli differenti incluso 13» degli esempi fissi, 13 è anche il centro di
   B12. Gli esempi usano 13, 0, 26 e 5.
6. **Debito H2 in inglese.** Resta il debito H2 già noto: il test inglese dell'App intera dipende dalla lingua
   della configurazione. I test I4 forzano la lingua sul frame.
7. **La vista non è uno spettatore automatico.** È l'utente a pensare la carta. I test simulano lo spettatore
   leggendo le facce nella tabella, come farebbe una persona.

## 19. Debiti

**I5**: decodifica generale; B12 con procedura **non** osservata (ricostruire prima il tabellone, come in B10/B15;
limite onesto della fonte).

**I6**: nessuno.

**I7** (da integrare):
* guida e glossario per «posizione iniziale candidata», «dinamica fisica / informativa», B1 e B12;
* `TAB_HELP` e onboarding per la sotto-scheda Spettatore;
* rimando alla Prop. 1.6 e al § 11.11.5;
* il percorso didattico: Pratica (carta nota) → Spettatore (carta ignota).

**J**: salvare e riprodurre una sessione di spettatore.

**Rinviati**:
* risposta errata dello spettatore (distinta da E4);
* variante B1 con il gemello come righello (A8);
* 21 carte (oltre 4.0).

**Aperte**: DP1, DP2, DP7–DP12 invariate. DP3, DP4 e DP5 preservate; DP6 chiusa da I3. Nessun taglio nel
linguaggio.

## 20. Gate I4

| # | Gate | Esito |
|---|---|---|
| I4-G1 | modello esplicito dello stato informativo | ✔ § 3 |
| I4-G2 | stato fisico e informativo distinti | ✔ § 3, § 13 |
| I4-G3 | X0 = 27 posizioni iniziali | ✔ |
| I4-G4 | 9 dopo la prima risposta | ✔ |
| I4-G5 | 3 dopo la seconda | ✔ |
| I4-G6 | 1 dopo la terza | ✔ |
| I4-G7 | candidato finale = posizione reale | ✔ 729/729 |
| I4-G8 | 27 terne biunivoche | ✔ § 10 |
| I4-G9 | `n = a1 + 3a2 + 9a3`, convenzione verificata | ✔ § 2 |
| I4-G10 | ricostruzione con le conversioni I2 | ✔ § 14 |
| I4-G11 | protocollo realmente adattivo | ✔ § 6 |
| I4-G12 | raccolta da fase, bersaglio e risposta | ✔ (firma e campi) |
| I4-G13 | una sola regola riusata | ✔ (una chiamata) |
| I4-G14 | 729/729 raccolte = solutore a carta nota | ✔ |
| I4-G15 | 729/729 al bersaglio | ✔ (due oracoli) |
| I4-G16 | identificazione ≠ destinazione | ✔ § 11 |
| I4-G17 | nessuna «perdita fisica» nei testi | ✔ § 13 |
| I4-G18 | ricostruzione indipendente dal bersaglio | ✔ |
| I4-G19 | indipendenza dalle raccolte caratterizzata | ✔ (5832, oracolo non produttivo) |
| I4-G20 | modalità ordine noto completa | ✔ § 7 |
| I4-G21 | carta identificata con ordine noto | ✔ |
| I4-G22 | B12 secondo la fonte | ✔ § 8 |
| I4-G23 | in B12 posizione ≠ identità | ✔ (`carta = None`) |
| I4-G24 | incoerenze non accettate in silenzio | ✔ § 12 |
| I4-G25 | nessun segreto richiesto | ✔ |
| I4-G26 | la UI mostra i candidati | ✔ |
| I4-G27 | la UI mostra la cifra acquisita | ✔ |
| I4-G28 | la UI distingue fisico e informativo | ✔ |
| I4-G29 | niente solo colore | ✔ |
| I4-G30 | IT/EN simmetrici | ✔ 46 + 46 |
| I4-G31 | tastiera e focus | ✔ |
| I4-G32 | geometrie H2 | ✔ |
| I4-G33 | nessun Canvas senza alternativa | ✔ (nessun Canvas) |
| I4-G34 | I3 non riaperto | ✔ |
| I4-G35 | Pratica storica invariata | ✔ |
| I4-G36 | Conseguenze reali invariata | ✔ (18/18 I3) |
| I4-G37 | nessun gioco da 21 | ✔ |
| I4-G38 | nessun b^k | ✔ |
| I4-G39 | nessun I5/I6/I7/J/K | ✔ |
| I4-G40 | architettura verde | ✔ § 17 |
| I4-G41 | baseline 25/25 | ✔ |
| I4-G42 | nessuna nuova regressione | ✔ |
| I4-G43 | unico failure = Tk 9 | ✔ |
| I4-G44 | PDF non tracciati | ✔ |
| I4-G45 | nessun accesso fuori dal repository | ✔ (PDF letti su stdout; nessun file d'appoggio) |
| I4-G46 | nessun push | ✔ |

## 21. Commit

| Commit | Messaggio |
|---|---|
| `23559cc` | `test(I4): characterize spectator information dynamics` |
| `b3e1e61` | `feat(I4): add adaptive spectator service` |
| `7adaf6e` | `feat(I4): add spectator information view` |
| `54b6e95` | `test(I4): enforce spectator UI and accessibility contracts` |
| (questo) | `docs(I4): close spectator information compartment` |

## 22. Git status

Prima del commit di chiusura:

```
## main...origin/main [ahead 93]
?? Articolo.pdf
?? LIBRO_MAIN.pdf
```

Dopo il commit di chiusura i commit avanti sono 94, con gli stessi due PDF non tracciati. Nessun push; I5 non è
iniziato. Audit e documenti I1–I3 non sono stati corretti: le precisazioni sono in questo documento (§ 18).
