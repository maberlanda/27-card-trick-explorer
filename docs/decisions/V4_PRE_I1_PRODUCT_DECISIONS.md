# V4 — Decisioni di prodotto pre-I1 (DP3, DP4, DP5)

> **Natura del documento.** Decision memo tecnico e di prodotto. Formula **raccomandazioni pronte per
> l'approvazione**, non decisioni prese. Nessuna delle tre raccomandazioni va considerata approvata finché
> l'utente non la approva esplicitamente. **I1 non è iniziato** e non deve iniziare prima dell'approvazione.

Etichette di provenienza usate in tutto il documento:

| Etichetta | Significato |
|---|---|
| **FONTE** | testo di `LIBRO_MAIN.pdf` (pagina stampata) o di `Articolo.pdf` |
| **CODICE** | lettura del codice nel repository |
| **TEST** | test già presenti nel repository |
| **ESEC** | misura eseguita con Python inline sul codice corrente (nessun file creato) |
| **INFERENZA** | deduzione argomentata dalle voci precedenti |
| **RACCOMANDAZIONE** | proposta di prodotto: **non** è un risultato matematico |

Convenzioni (invariate rispetto all'audit V4): posizioni 0..26, `n = 9·n2 + 3·n1 + n0`; `T[carta] = posizione
finale`; `(a∘b)[i] = a[b[i]]`; `MSC(n) = 9·(n mod 3) + ⌊n/3⌋`; `J = R⊗R⊗R`, `R = (2,1,0)`, cioè `J(p) = 26 − p`
(complemento cifra per cifra). Numerazione della tavola `# = k1 + 6·k2 + 36·k3` (App. C). G216 = S3³ e Γ648 =
G216 ⋊ C3 sono usati solo come **nomi descrittivi neutrali** (DP2 non è risolta).

---

## 1. Identità e perimetro

* **Repository**: il checkout Git corrente, e nient'altro. Nessun accesso a directory padre o sorelle, copie,
  backup, worktree, clone o script esterni.
* **Fonti ammesse**: codice e documentazione del repository, `LIBRO_MAIN.pdf`, `Articolo.pdf` (entrambi **non
  tracciati**: restano fuori da Git), comandi Python inline, test esistenti.
* **Oggetto**: tre decisioni che bloccano I1:
  * **DP3**: momento canonico del rovesciamento;
  * **DP4**: equivalenza mostrata di default fra strategie;
  * **DP5**: metrica di costo e strategia proposta di default.
* **Fuori perimetro**:
  * DP1, DP2 e DP6–DP12 (eventuali dipendenze sono solo segnalate, § 13);
  * l'implementazione di I1 e l'avvio di I2–I7, J e K;
  * qualunque modifica a `gioco27/`, `tests/`, `pyproject.toml`, README, guida, i18n e PDF.
* **Unico file tracciato nuovo**: questo memo. Nessun CSV di supporto e nessun test aggiunto: le misure sono
  state fatte con Python inline e sono descritte al § 14 in forma riproducibile.

## 2. Fonti e stato iniziale

**Stato Git iniziale** (ESEC):

* branch `main`, HEAD `36b97d4 docs(v4): audit mathematical and didactic coverage`;
* `origin/main` = `54445af` (67 commit avanti, nessun push);
* file non tracciati: solo `Articolo.pdf` e `LIBRO_MAIN.pdf`;
* un `.git/index.lock` orfano, lasciato da un comando Git interrotto, è stato rimosso prima di iniziare.

**Baseline** (TEST, ESEC):

* `pytest tests/test_baseline_matematica.py` → **25 passed**;
* `test_gioco_reale.py` 9 passed, `test_tabellone_inverso.py` 20 passed, `test_dominio_selftest.py` 7 passed.

La suite completa non è stata rieseguita. Il codice è identico a quello dell'audit (l'unico commit successivo è di
sola documentazione), dove la suite aveva dato 1427 passed, 1 skipped e 1 fallimento ambientale noto. Quel
fallimento è `test_layout_accessibilita_h2.py::test_lo_scorrimento_si_accende_quando_il_testo_cresce` e dipende
dalle metriche dei font di Tk 9.0.4 nella VM, contro Tk 8.6 nell'ambiente H2 di riferimento: non è una regressione.

**Fonti consultate**, nell'ordine libro → codice → test → audit → articolo:

| Fonte | Punti usati |
|---|---|
| FONTE Libro | Notazioni p. xiii; § 2.5 (pp. 72–75); introduzione del cap. 5 e § 5.1.1 (pp. 111–112); § 5.1.17 (p. 133); § 6.10 (p. 169); App. C (p. 363); App. D § 1 (p. 373) e § 5, Prop. 5.1 e Cor. 5.2 (pp. 378–381) |
| CODICE | `core/gioco_reale.py` (`raccogli`, `esegui_partita`, `risolvi_trucco`, `selftest` 1b); `core/permutations.py` (`compute_stage`, `compute_T_full`); `core/constants.py`; `core/detail_pdf.py` (`_reversed_stage`, `_r_index`); `gui/filter_frame.py` (preset «Gioco Reale»); `gui/simulator_tab.py`; `gui/presentation.py`; `gui/app.py` (`_notify_T_changed`) |
| TEST | `test_baseline_matematica.py`, `test_gioco_reale.py`, `test_i18n.py`, `test_stato_concorrenza_c.py` (asserzioni sul piano del solutore) |
| Audit | `V4_MATHEMATICAL_DIDACTIC_COVERAGE_AUDIT.md` § 13.4 (definizioni), § 14.3, § 21 (DP3–DP5), tabella ESEC finale |
| Articolo | nessun rovesciamento: non pertinente per DP3 salvo conferma che la sua App. D coincide con quella del libro |

---

## 3. DP3 — evidenza

### 3.1 Ricostruzione esatta

**Formula di stadio nel libro** (FONTE):

* Notazioni p. xiii e § 5.1.1 p. 112: `Ti = Pi ∘ MSC ∘ J^εi`, con `εi ∈ {0,1}`, `Pi = P2,i ⊗ P1,i ⊗ P0,i` e
  `J^εi = R^εi ⊗ R^εi ⊗ R^εi`.
* Nel gioco fisico `Pi = P2,i ⊗ I3 ⊗ I3` (§ 5.1.17 p. 133): la raccolta agisce solo sulla cifra più significativa.

**Posizione di J** (FONTE):

* nella composizione `∘`, J sta **a destra**, cioè agisce **per primo** nello stadio;
* App. D § 5 p. 378 lo dice testualmente: «Il blocco Jh agisce per primo, quindi il rovesciamento precede la
  distribuzione»;
* App. D § 1 p. 373: «un rovesciamento globale prefissato del mazzo, applicato prima della distribuzione».

**Significato fisico** (FONTE, pp. 111–112):

* J capovolge l'intero mazzo, per cui la carta in posizione `i` va in `26 − i`;
* `J⁻¹ = Jᵀ = J`;
* sulle cifre ternarie è il complemento `d ↦ 2 − d` su tutte e tre le cifre.

**Commutazione e assorbimento** (FONTE, § 5.1.17):

* `MSC ∘ J^ε = J^ε ∘ MSC`;
* `Li = (P2,i ∘ R^εi) ⊗ R^εi ⊗ R^εi`, da cui `Ti = Li ∘ MSC`;
* `M2 = P2,2∘R^ε2∘R^ε1∘R^ε0`, `M1 = R^ε2∘P2,1∘R^ε1∘R^ε0`, `M0 = R^ε2∘R^ε1∘P2,0∘R^ε0`.

**Molteplicità** (FONTE, App. D Prop. 5.1; § 6.10 p. 169):

* fissata la storia ε, la mappa dalle raccolte alla trasformazione è biunivoca, quindi ogni Cronaca ha 2³ = 8
  realizzazioni;
* il Cor. 5.2 inverte le raccolte data ε;
* § 6.10: «Un rovesciamento accidentale, se le raccolte restano invariate, modifica normalmente la Cronaca».

**Convenzione dell'Appendice C** (FONTE, p. 363):

* testo: «il rovesciamento può essere presente o assente, **a valle della raccolta della fase**; l'indice di R,
  letto in binario su tre cifre, dice quali fasi vengono rovesciate: la cifra più significativa è la prima fase»;
* quindi `k = 4·r1 + 2·r2 + r3`, dove `r_i` = rovesciamento **dopo la raccolta** della fase i;
* la tavola stampata usa soltanto `R[0]`.

**Esempio del § 2.5** (FONTE, pp. 72–74):

* «Dopo uno dei tre mescolamenti, rovesciamo globalmente il mazzo»;
* sequenza `SCD, DCS, J, SCD`, cioè J dopo la seconda raccolta;
* vettore finale `(20,19,18,23,22,21,26,25,24,11,10,9,14,13,12,17,16,15,2,1,0,5,4,3,8,7,6)`, Assi in 20, 13, 6.

**Core attuale** (CODICE):

| Punto del codice | Convenzione | Dettagli |
|---|---|---|
| `gioco_reale.raccogli(cols, sigla, rovescia)` e `esegui_partita(mesc, rovesciamenti)` | **B**: dopo la raccolta | capovolgono il mazzo **dopo** l'impilamento della fase |
| `permutations.compute_stage` | **A**: prima della distribuzione | `Stage = P @ MSC @ J` |
| preset «Gioco Reale» dei Filtri (`filter_frame.set_preset_gioco_reale`) | **A** | `P2` libero, `P1 = P0 = SCD_U`, J uniforme (`R_U`), 12³ = 1728 combinazioni |
| `detail_pdf._r_index` (esportato nel PDF dettagliato come `R[m]`) | **A** | `m = 4·ε1 + 2·ε2 + ε3`, con `ε_k` = J uniforme nello stadio k, cioè **prima della distribuzione**; la docstring la chiama «convenzione del C» (programma C non presente nel repository: non verificabile) |

Oggi Simulatore, Pratica e Tavola **non** usano rovesciamenti: il piano di `risolvi_trucco` non ne contiene, e la
chiave `simulator.phase.after_shuffle_reversed` non viene mai attivata. Gli unici punti del programma in cui
l'utente vede rovesciamenti sono i Filtri, l'Anteprima e il PDF, e usano **A**.

**Adattatore già esistente** (CODICE, `selftest` 1b):

* per un rovesciamento dopo la raccolta della fase s, il selftest usa `p3 = R∘S_s`, `p2 = p1 = R` e J-fattori
  `I_3`;
* cioè lo stadio `(R∘S_s ⊗ R ⊗ R) ∘ MSC = J ∘ (S_s ⊗ I ⊗ I) ∘ MSC`;
* è un **oracolo matriciale di B**, verificato su 1728/1728 combinazioni. Non traduce B in A.

### 3.2 Prova di equivalenza

Si pone `P_i = S_i ⊗ I3 ⊗ I3` e `M = MSC`, con lo stadio 1 che agisce per primo.

```
A (libro):        T_A(S; ε1,ε2,ε3) = (P3∘M∘J^ε3) ∘ (P2∘M∘J^ε2) ∘ (P1∘M∘J^ε1)
B (gioco_reale):  T_B(S; r1,r2,r3) = (J^r3∘P3∘M) ∘ (J^r2∘P2∘M) ∘ (J^r1∘P1∘M)
```

Basta la sola associatività, senza nessuna commutazione:

```
T_B(S; r1,r2,r3) = J^r3 ∘ (P3∘M∘J^r2) ∘ (P2∘M∘J^r1) ∘ (P1∘M∘J^0) = J^r3 ∘ T_A(S; 0, r1, r2)
T_A(S; ε1,ε2,ε3) = T_A(S; 0, ε2, ε3) ∘ J^ε1 = T_B(S; ε2, ε3, 0) ∘ J^ε1
```

**Teorema (INFERENZA dimostrata sopra, ESEC confermata).**

1. Il rovesciamento **dopo la raccolta dello stadio i** e quello **prima della distribuzione dello stadio i+1**
   (per i = 1, 2) sono **lo stesso gesto nello stesso istante**. L'equivalenza è un'identità, non
   un'approssimazione: `r_i ≡ ε_{i+1}`.
2. L'equivalenza **fallisce esattamente ai due bordi**:
   * `ε1` (capovolgere il mazzo iniziale) non ha corrispondente in B: è una composizione a destra `∘J`;
   * `r3` (capovolgere il mazzo dopo l'ultima raccolta) non ha corrispondente in A: è una composizione a
     sinistra `J∘`.
3. Le due famiglie da 1728 procedure sono **diverse come insiemi di gesti**, ma:
   * hanno la **stessa immagine**, cioè le stesse 216 T;
   * hanno la **stessa molteplicità**: 8 procedure per ogni T;
   * hanno lo **stesso profilo dei rovesciamenti** in ogni classe E_T, `(0,1,1,1,2,2,2,3)`.

   Poiché J ∈ G216, `J∘T` e `T∘J` restano in G216: l'assorbimento del Giullare vale in entrambe.
4. Identificare le due convenzioni **allo stesso indice** (`r = ε`) è sbagliato: dà la stessa T solo in
   **512/1728** casi.

**Verifiche ESEC** (Python inline su `compute_T_perm` e `T_da_partita`):

| Verifica | Esito |
|---|---|
| senza rovesciamenti A = B | 216/216 |
| `T_B(S; a,b,0) = T_A(S; 0,a,b)` | 864/864 |
| `T_B(S; a,b,c) = J^c ∘ T_A(S; 0,a,b)` | 1728/1728 |
| `T_A(S; e,a,b) = T_A(S; 0,a,b) ∘ J^e` | 1728/1728 |
| stesso indice `T_B(S; r) = T_A(S; r)` | **512/1728** (quindi non equivalenti) |
| immagini: 216 T in entrambe; fibre di 8; profilo `(0,1,1,1,2,2,2,3)` in ogni classe, in A e in B | sì |

### 3.3 Esempi

Si usa la terna **(CSD,CSD,CSD)**, #86, che discrimina bene. La colonna «Assi» dà le posizioni finali delle carte
0, 13 e 26 (ESEC).

| Gesto fisico | B (dopo la raccolta) | A (prima della distribuzione) | Assi |
|---|---|---|---|
| nessun rovesciamento (base) | `r=(0,0,0)` | `ε=(0,0,0)` | (13, 0, 26) |
| capovolgi dopo la raccolta 1 = prima della distribuzione 2 | `r=(1,0,0)` | `ε=(0,1,0)` | (25, 2, 12) |
| capovolgi dopo la raccolta 2 = prima della distribuzione 3 | `r=(0,1,0)` | `ε=(0,0,1)` | (22, 8, 9) |
| capovolgi il mazzo **iniziale** | — (fuori famiglia B) | `ε=(1,0,0)` | (26, 0, 13) |
| capovolgi dopo la raccolta **3** | `r=(0,0,1)` | — (fuori famiglia A; è `J∘T_A(0,0,0)`) | (13, 26, 0) |
| più rovesciamenti: dopo le raccolte 1 e 2 | `r=(1,1,0)` | `ε=(0,1,1)` | (10, 6, 23) |
| più rovesciamenti: dopo le raccolte 1 e 3 | `r=(1,0,1)` | `J ∘ T_A(0,1,0)` | (1, 24, 14) |
| tutti e tre in B | `r=(1,1,1)` | `J ∘ T_A(0,1,1)` | (16, 20, 3) |

Questi esempi mostrano anche che il **nome** di un indice non basta. A indice identico, cioè leggendo lo stesso `r`
come `ε`, `ε=(1,0,0)` dà (26, 0, 13) mentre `r=(1,0,0)` dà (25, 2, 12).

**Identità.**

* (SCD,SCD,SCD) senza rovesciamenti → Assi (0, 13, 26).
* Un solo rovesciamento al bordo, cioè `ε=(1,0,0)` in A oppure `r=(0,0,1)` in B, dà J → Assi (26, 13, 0).
* Nella classe dell'identità ci sono 8 procedure, identiche in A e in B: SCD³ con `ε ∈ {000, 011, 101, 110}` e
  DCS³ con `ε ∈ {001, 010, 100, 111}`. È coerente con l'audit.

**Configurazione nota del libro (§ 2.5).**

* `SCD, DCS, J, SCD` è B `r=(0,1,0)` ≡ A `ε=(0,0,1)`.
* Il vettore ottenuto coincide **esattamente** con quello stampato, Assi 20, 13, 6 (ESEC).
* La sua Cronaca coincide con quella della disposizione semplice **#185 = (DCS,SCD,DCS)**, che ha gli stessi
  Assi: il rovesciamento è stato assorbito, come afferma l'Oss. 2.35.
* **Attenzione**: questo esempio **non discrimina** le convenzioni, perché per caso anche A `ε=(0,1,0)` dà lo
  stesso vettore. Per i futuri test di I1 va usato un caso discriminante, come (CSD,CSD,CSD).

### 3.4 Confronto dei criteri

| Criterio | A — prima della distribuzione | B — dopo la raccolta |
|---|---|---|
| Modello matematico | **coincide** con `Ti = Pi∘MSC∘J^εi`; Prop. 5.1 e Cor. 5.2 si applicano alla lettera | richiede la riscrittura `J^r3 ∘ T_A(0,r1,r2)` |
| Gesto fisico | «capovolgi, poi distribuisci»; per gli stadi 2 e 3 è lo stesso istante di B | naturale: «hai raccolto, vuoi capovolgere?» |
| Libro | Notazioni, cap. 5, App. A, App. D | App. C (definizione di R[k]) e narrazione del § 2.5 (dove A e B coincidono) |
| Codice corrente | `compute_stage`, preset Gioco Reale, `R[m]` del PDF | `gioco_reale.esegui_partita` (non esposto con rovesciamenti) |
| Didattica | un solo indice ε per stadio, allineato alle formule mostrate dal libro | domanda naturale dopo ogni raccolta; E2 «rovesciamento accidentale dopo la fase k» è diretto |
| Ambiguità | «capovolgere il mazzo iniziale» non ha analogo in B | «capovolgere dopo l'ultima raccolta» non ha analogo in A |
| Semplicità I1/I2/I3 | I1 e I3 (inversione, Cor. 5.2) senza adattatori; I2 (Simulatore) con un adattatore banale verso l'oracolo fisico | I2 diretto; I1 e I3 con adattatore verso le formule |
| Dati e export | **nessuna modifica**: `R[m]` del PDF mantiene il significato | cambiare `R[m]` sarebbe **breaking formato**; lasciarlo così creerebbe due convenzioni visibili |

**Osservazione nuova rispetto all'audit** (ESEC e FONTE; nessuna correzione silenziosa):

* il PDF dettagliato stampa `R[m]` in convenzione **A**;
* l'Appendice C definisce `R[k]` in convenzione **B**;
* lo **stesso indice R[·] denota procedure diverse** in 1216/1728 casi (e la stessa T solo in 512/1728);
* per `r3 = 0` la conversione esatta è `m = k >> 1`, cioè `R_C[k] ≡ R_prog[k/2]` per k pari. Per k dispari serve
  anche il capovolgimento finale.

L'audit (tabella dei concetti trasversali, riga «Rovesciamenti») scrive che i due momenti «sono riconciliati dal
selftest ma non spiegati». Precisazione: il selftest 1b riconcilia **B con il modello matriciale** per
assorbimento; **non** riconcilia la convenzione A dell'etichetta `R[m]` con la definizione B dell'App. C. La
divergenza di etichetta non era registrata.

## 4. DP3 — decisione raccomandata

```text
DP3 = A (prima della distribuzione dello stadio i)   [RACCOMANDAZIONE — richiede approvazione]

Rappresentazione canonica interna:
  Procedura = (S1, S2, S3 ∈ SIGLE ; ε1, ε2, ε3 ∈ {0,1}), con
  T_i = (S_i ⊗ I ⊗ I) ∘ MSC ∘ J^εi  e  T = T3 ∘ T2 ∘ T1,
  cioè esattamente il modello del libro (Notazioni; § 5.1.1; App. D § 5) e di compute_stage.
  Identificatori stabili: # = k1 + 6k2 + 36k3 e m = 4ε1 + 2ε2 + ε3 (= R[m] già esportato).

Rappresentazione mostrata nel gesto fisico:
  stadio i con ε_i = 1 → «capovolgi il mazzo, poi distribuisci».
  Per i = 2, 3 la UI può dirlo, in modo equivalente e senza approssimazione, come
  «dopo la raccolta della fase i−1 capovolgi il mazzo».
  Per i = 1: «prima di iniziare, capovolgi il mazzo».
  Il «capovolgimento dopo l'ultima raccolta» NON fa parte della famiglia canonica.

Adattatore (esplicito, dimostrato al § 3.2):
  B → A :  (S; r1,r2,r3) ↦ (S; 0, r1, r2)  seguito da J^r3,  cioè T_B = J^r3 ∘ T_A(S; 0,r1,r2).
           Se r3 = 1 la procedura B è rappresentata come procedura canonica + «rovesciamento finale»
           (evento fuori famiglia, T' = J∘T ∈ G216). Serve per modellare E2 alla fase 3 e le righe
           App. C con k dispari.
  A → B :  T_A(S; ε) = T_B(S; ε2, ε3, 0) ∘ J^ε1  (oracolo fisico: capovolgi il mazzo iniziale se ε1,
           poi esegui_partita(S, (ε2, ε3, False))).
  Etichette: R_AppC[k] con k pari ≡ R_prog[k >> 1]; k dispari ≡ R_prog[k >> 1] + rovesciamento finale.

Motivazione:
  1. coincide con la formula che il libro usa per tutti i teoremi (M2, M1, M0; Prop. 5.1; Cor. 5.2;
     otto-a-uno del § 6.10);
  2. è la convenzione già visibile all'utente (Filtri, Anteprima, R[m] nei PDF): nessuna modifica di
     formato;
  3. per gli stadi 2 e 3 A e B sono lo stesso gesto: la sola differenza reale sta ai bordi ed è
     un'unica composizione con J, dichiarata;
  4. un solo modello nel core; gioco_reale resta l'oracolo fisico raggiunto tramite adattatore,
     non un secondo modello di Procedura.
```

**Alternative scartate** (RACCOMANDAZIONE):

* **B come canonica**: renderebbe incoerente l'etichetta `R[m]` già esportata (breaking formato) oppure
  imporrebbe due convenzioni visibili.
* **Linea temporale a 4 slot** (rovesciamento possibile prima dello stadio 1, fra gli stadi e dopo lo stadio 3):
  rompe il conteggio del libro 1728 = 12³ e l'«otto-a-uno», perché diventerebbero 3456 procedure con 16 per
  Cronaca.

---

## 5. DP4 — evidenza

**Definizioni**, riprese esattamente dal § 13.4 dell'audit:

```
E_T(p,q)        ⇔ T(p) = T(q)                                    (partizione in 216 classi di 8)
E_carta_c(p,q)  ⇔ T(p)[c] = T(q)[c]                              (27 classi di 64 per ogni c)
E_target_{c,t}  = { p ∈ Π : T(p)[c] = t }                         (insieme, non relazione: 64 elementi, 8 semplici)
E_gesti_F(p)    ⇔ tutte le raccolte e i rovesciamenti di p appartengono alla famiglia F dichiarata
                  (es. F_semplice: nessun rovesciamento; F_sicura: nessuna raccolta CDS/DSC)
E_costo_κ(p,q)  ⇔ κ(p) = κ(q) per una metrica κ dichiarata, per esempio
                  κ1 = numero di raccolte ≠ SCD, κ2 = numero di raccolte CDS/DSC, κ3 = numero di rovesciamenti,
                  κ4 = combinazione lessicografica dichiarata
```

**Struttura** (ESEC, nella convenzione A; in B i conteggi sono identici):

* **Catena di inclusioni**: `p = q ⇒ E_T(p,q) ⇒ E_carta_c(p,q)` per ogni c.
* **Fibre di E_carta_c**: le classi di E_carta_c sono esattamente le fibre `E_target_{c,t}`, per t = 0..26. Quindi
  B (relazione) e C (fibra) sono la stessa partizione, vista come relazione o come singola classe.
* **Ogni fibra E_target (64 procedure) = 8 classi E_T × 8 procedure** (729/729):
  * ogni classe E_T è contenuta per intero nella fibra;
  * le 8 procedure semplici della fibra stanno in 8 classi E_T distinte, **una per classe** (729/729).
* **E_gesti e E_costo sono ortogonali** alla catena: non sono implicate da E_T né la implicano.
  * Esempio: la classe dell'identità contiene SCD³ (κ1 = 0) e DCS³ (κ1 = 3).

**Esempio che separa i tre livelli: carta 0 → bersaglio 13** (ESEC):

* **stesso bersaglio, azione globale diversa**: (CSD,CSD,CSD) = #86 e (CSD,CSD,CDS) = #158 portano entrambe la
  carta 0 in 13, ma sono due Cronache diverse;
* **stessa azione globale, procedura diversa**: #86 e le altre 7 procedure della sua classe E_T, tutte con
  rovesciamenti, hanno la stessa T ma gesti diversi;
* **stessa procedura**: solo l'identità.

**Valutazione delle opzioni** (INFERENZA):

| Opzione | Pro | Contro |
|---|---|---|
| A — E_T ovunque | matematicamente forte; Cronaca ben definita; classi di 8 | per il trucco è **troppo forte**: delle 8 Cronache che risolvono c→t ne mostrerebbe una sola, con 7 realizzazioni su 8 che richiedono rovesciamenti |
| B — E_carta ovunque | è la relazione del trucco | nel contesto T non c'è una carta privilegiata; fonde 8 Cronache e **nasconde** la differenza «stesso bersaglio ≠ stessa azione globale» |
| C — E_target | è l'oggetto giusto per il problema carta→bersaglio | è un insieme, non una relazione; da solo non dice nulla nel contesto T |
| D — contestuale | ogni vista usa l'oggetto che l'utente sta guardando; la gerarchia 64 = 8 × 8 rende visibili tutti e tre i livelli | richiede una terminologia disciplinata, senza «equivalente» non qualificato |

## 6. DP4 — decisione raccomandata

```text
DP4 = D (default contestuale, vocabolario esplicito)   [RACCOMANDAZIONE — richiede approvazione]

Default:
  la parola «equivalente» non compare mai da sola: ogni affermazione di equivalenza nomina la
  relazione. Il servizio (I1) espone tutte le relazioni; la UI sceglie quella di partenza in base
  al contesto.

Nel contesto carta→bersaglio (Simulatore, Pratica, confronto di soluzioni del trucco):
  oggetto di default = fibra E_target_{c,t} (64 procedure, 8 semplici), presentata
  RAGGRUPPATA per E_T: 8 Cronache × 8 procedure; in ogni Cronaca, in evidenza la sua unica
  realizzazione senza rovesciamenti. Relazione nominata: «stesso bersaglio per la carta c».

Nel contesto T (Explorer, Tavola 216, Cicli, Presentazione, Protocollo):
  relazione di default = E_T («stessa Cronaca»), classe di 8 procedure.

Terminologia UI:
  stessa procedura                          ↔ identità
  stessa Cronaca / stessa azione globale    ↔ E_T
  stesso bersaglio (per la carta c)         ↔ E_carta_c; «soluzioni di c→t» ↔ fibra E_target_{c,t}
  stessa famiglia di gesti F                ↔ E_gesti_F (filtro dichiarato)
  stesso costo κ                            ↔ E_costo_κ
  (la parola «Cronaca» dipende da DP2: qui è usata come nome corrente, non come decisione)

Relazioni sempre disponibili:
  identità, E_T, E_carta_c, fibra E_target_{c,t}, E_gesti_F, E_costo_κ; la catena
  identità ⇒ E_T ⇒ E_carta_c va mostrata come tale. E_gesti e E_costo sono presentati come
  filtri o ordinamenti, non come «equivalenza di strategia».
```

Motivo principale: il requisito didattico (stesso bersaglio ≠ stessa azione globale ≠ stessa procedura fisica) è
soddisfatto **per costruzione** dalla vista 64 = 8 × 8. Nessuna delle opzioni A, B o C, presa da sola, mostra i tre
livelli insieme.

---

## 7. DP5 — metriche misurate

Dominio: 729 coppie (carta, bersaglio); 216 procedure semplici; 1728 procedure con rovesciamenti, misurate sia in
A sia in B. Cifre: `c = (c2,c1,c0)`, `t = (b2,b1,b0)`.

### 7.1 κ1 — raccolte diverse da SCD

**Perché il solutore la minimizza** (CODICE, INFERENZA dimostrata, ESEC):

* Alla fase i la carta sta nella colonna `col_i`. Dopo la raccolta la sua posizione è `9·S_i(col_i) + ⌊pos/3⌋`,
  che **dipende solo da `S_i(col_i)`**, cioè dalla cifra richiesta, e non dagli altri due valori di `S_i`.
* Quindi la traiettoria della carta è forzata: le colonne sono `(c0, c1, c2)` e le cifre richieste
  `(b0, b1, b2)`.
* **SCD è candidata alla fase i se e solo se `c_{i−1} = b_{i−1}`**. Di conseguenza, fra le procedure semplici:

```
κ1_min(c,t) = d_H(c,t) = #{ i : c_i ≠ b_i }      (distanza di Hamming fra le cifre ternarie)
```

* `risolvi_trucco` sceglie SCD appena può (`preferisci_semplici=True`): questo è **deliberato e documentato**
  nella docstring («o l'identità quando possibile»).
* La **minimalità globale** è invece **emergente** (le fasi sono indipendenti) e **non documentata**.
* ESEC: κ1(piano corrente) = `d_H(c,t)` in 729/729 coppie.

**Descrizione contrattuale del solutore storico** (ESEC 729/729):

```
risolvi_trucco(c,t) = argmin sulle 8 procedure semplici della fibra E_target_{c,t} della chiave (κ1, #)
```

Qui `#` è il numero di tavola. È la prima volta che il default storico è descritto da una chiave esplicita e stabile.

**Significato fisico e didattico.**

* Una raccolta ≠ SCD è una fase in cui la carta **non** si trova già nella colonna che porta la cifra giusta: il
  prestigiatore deve cambiare l'ordine naturale S, C, D di raccolta.
* **Meno non-SCD non significa automaticamente «più facile»**: CSD, SDC e DCS sono auto-inverse (la sigla coincide
  con il gesto), mentre solo CDS e DSC costringono a invertire la sigla (§ 7.2).

**Precisazione all'audit** (ESEC; nessuna correzione silenziosa):

* il testo del § 14 dell'audit dice correttamente «fra le 8 alternative»;
* la tabella ESEC finale riporta però «minimo per κ1 in 729/729» **senza** l'ambito;
* nella fibra completa di 64 procedure, **con** rovesciamenti, κ1 **non** è minimo in **242/729** coppie, perché:

```
κ1_min con rovesciamenti = min( d_H(c,t), d_H(26−c,t) )        (ESEC 729/729)
```

  Un solo rovesciamento complementa le cifre della carta. Le 242 coppie sono quelle con `d_H(26−c,t) < d_H(c,t)`;
  il calo di κ1 è di 1 in 174 coppie, di 2 in 60 e di 3 in 8.

### 7.2 κ2 — raccolte CDS/DSC

**Significato.** CDS e DSC sono le **sole** due sigle in cui mescolamento e impilamento differiscono. È la Prima
Crisi di Seldon (App. C: «si scambia CDS ↔ DSC»), e la Pratica segnala l'errore «Seldon» proprio su queste fasi
(`is_seldon = chosen == mesc and mesc != correct`).

**Forma chiusa** (INFERENZA dimostrata, ESEC 729/729):

* se `c_i ≠ b_i`, i due candidati sono la trasposizione `col↔dig` e un 3-ciclo;
* il solutore sceglie la permutazione che conserva l'ordine degli altri due gruppi, e questa è il **3-ciclo**
  esattamente quando `{c_i, b_i} = {0, 2}`: `c_i=0, b_i=2` dà DSC; `c_i=2, b_i=0` dà CDS;
* l'alternativa è sempre **DCS** (scambia S e D, auto-inversa), **con lo stesso κ1**.

```
κ2(piano corrente) = #{ i : {c_i, b_i} = {0,2} }          κ2_min = 0 per tutte le 729 coppie
```

| Differenza κ2 corrente − κ2 minimo | Coppie | Forma chiusa |
|---|---|---|
| 0 | 343 | 7³ |
| 1 | 294 | 3·2·7² |
| 2 | 84 | 3·2²·7 |
| 3 | 8 | 2³ |
| **migliorabili** | **386** | 729 − 7³ |

**Il dato 386/729 dell'audit è confermato**, ora con una derivazione in forma chiusa. In tutto i piani correnti
contengono 294 + 2·84 + 3·8 = **486** raccolte CDS/DSC.

### 7.3 κ3 — rovesciamenti

* **Profilo per classe E_T** (ESEC, in A e in B): in ogni classe E_T le 8 procedure hanno profilo
  `(0,1,1,1,2,2,2,3)`. Ogni Cronaca ha **esattamente una** realizzazione senza rovesciamenti.
* **Fibra E_target** (64 procedure): contiene 8 procedure con κ3 = 0, una per classe E_T.

Implicazioni (INFERENZA):

* **Default del solutore.**
  * Il vincolo κ3 = 0 non esclude **nessuna** Cronaca.
  * Però **non è gratuito** su κ1: in 242 coppie un rovesciamento sostituisce da 1 a 3 raccolte non-SCD.
  * Sul totale dei gesti non banali κ1 + κ3, un rovesciamento **migliora strettamente** 68 coppie (60 di 1 e 8
    di 2) e **pareggia** in 174.
  * Evitare i rovesciamenti è una scelta di **famiglia di gesti** (oggi Simulatore e Pratica non li supportano),
    non un ottimo di costo.
* **Visualizzazione delle alternative.**
  * Mostrare per ogni Cronaca il rappresentante senza rovesciamenti dà un elenco di 8 righe, confrontabile con la
    Tavola.
  * Le 7 varianti con rovesciamenti sono l'illustrazione diretta dell'«otto-a-uno».
* **Didattica del Giullare.** Il caso carta 0 → 26 è esemplare:
  * senza rovesciamenti servono tre raccolte non-SCD (DSC³ o DCS³);
  * con un solo capovolgimento basta SCD³.

  Il Giullare, qui, **semplifica** il gesto. Vietarlo per default nasconderebbe proprio questo fenomeno.

### 7.4 Metriche composte

Confronto lessicografico nella fibra `E_target_{c,t}`. Ordine finale stabile per tutte: `(…κ…, m, #)`, con
`m = 4ε1 + 2ε2 + ε3` (convenzione A) e `#` il numero di tavola. È un **ordine totale** sulle 1728 procedure,
perché `(#, m)` identifica univocamente la procedura. ESEC su 729 coppie:

| Metrica | Ambito | Differisce dal solutore corrente | CDS/DSC evitate | Rovesciamenti introdotti | Non-SCD introdotte | Pareggi (prima del tie-break) |
|---|---|---|---|---|---|---|
| κA = (κ2, κ1, κ3) | 8 semplici | 386 | 486 | 0 | 0 | 0 |
| κA = (κ2, κ1, κ3) | 64 con rovesciamenti | 386 | 486 | **242** (1 per coppia) | 0 (anzi −318) | **242** (a 3 vie) |
| κB = (κ3, κ2, κ1) | 8 semplici | 386 | 486 | 0 | 0 | 0 |
| κB = (κ3, κ2, κ1) | 64 con rovesciamenti | 386 | 486 | 0 | 0 | 0 |
| κC = (κ1, κ2, κ3) | 8 semplici | 386 | 486 | 0 | 0 | 0 |
| κC = (κ1, κ2, κ3) | 64 con rovesciamenti | 386 | 486 | **242** | 0 (anzi −318) | **242** (a 3 vie) |

Letture (ESEC e INFERENZA):

* **Fra le procedure semplici le tre metriche coincidono.** Selezionano la stessa procedura, cioè il solutore
  storico con ogni CDS/DSC sostituita da DCS, e **non hanno pareggi**:
  * a ogni fase con `c_i = b_i` SCD è l'unica a κ1 = 0;
  * a ogni fase con `{c_i,b_i} = {0,2}` DCS è l'unica a κ2 = 0.
* **Nella fibra di 64**, κA e κC selezionano **la stessa procedura in 729/729 coppie**.
  * Nelle 242 coppie in cui conviene capovolgere, i pareggi sono **sempre a 3 vie**: stesse raccolte, con il
    rovesciamento allo stadio 1, 2 o 3.
  * Il tie-break sceglie `m = 1` (ε3 = 1: «capovolgi prima della terza distribuzione»).
  * In B lo stesso indice significherebbe «dopo la terza raccolta»: il **gesto** scelto dipende da DP3, il
    **conteggio** no.
* **κB** equivale a «prima nessun rovesciamento, poi sicurezza, poi semplicità»: è l'unica delle tre che, nella
  fibra completa, non introduce rovesciamenti.
* Le misure sono **identiche in A e in B**: stesso insieme di 242 coppie e stessi conteggi.

**Tie-break proposto** (RACCOMANDAZIONE, vale per qualunque metrica adottata):

```
chiave(p) = (κ_primario(p), κ_secondario(p), κ_terziario(p), m(p), #(p))
m = 4ε1 + 2ε2 + ε3   (DP3 = A)      # = k1 + 6k2 + 36k3   (App. C)
```

Sono esclusi l'ordine dei dict, l'ordine casuale e l'ordine di enumerazione di `itertools`. Il default storico è la
chiave `(κ3 = 0 come vincolo, κ1, #)`.

## 8. DP5 — esempi

ESEC. Piano corrente = `risolvi_trucco`; alternativa = minimo κ2 fra le 8 procedure semplici con la chiave
`(κ2, κ1, #)`. Cifre scritte come `(d2, d1, d0)`.

| Carta | Bersaglio | cifre c → t | Piano corrente | # | κ1 | κ2 | Piano alternativo | # | κ1 | κ2 | Nota |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 13 | 000 → 111 | CSD CSD CSD | 86 | 3 | 0 | CSD CSD CSD | 86 | 3 | 0 | **nessuna differenza**; carta 0 |
| 13 | 13 | 111 → 111 | SCD SCD SCD | 0 | 0 | 0 | SCD SCD SCD | 0 | 0 | 0 | nessuna differenza; carta 13 |
| 0 | 2 | 000 → 002 | DSC SCD SCD | 3 | 1 | 1 | DCS SCD SCD | 5 | 1 | 0 | **miglioramento di 1** |
| 26 | 24 | 222 → 220 | CDS SCD SCD | 4 | 1 | 1 | DCS SCD SCD | 5 | 1 | 0 | miglioramento di 1; carta 26 |
| 0 | 20 | 000 → 202 | DSC SCD DSC | 111 | 2 | 2 | DCS SCD DCS | 185 | 2 | 0 | miglioramento di 2; è il piano degli errori E1/E2 dell'audit |
| 7 | 19 | 021 → 201 | SCD CDS DSC | 132 | 2 | 2 | SCD DCS DCS | 210 | 2 | 0 | miglioramento di 2; coppia usata dai test i18n |
| 0 | 26 | 000 → 222 | DSC DSC DSC | 129 | 3 | 3 | DCS DCS DCS | 215 | 3 | 0 | **miglioramento massimo (3)**; carta 0 |
| 26 | 0 | 222 → 000 | CDS CDS CDS | 172 | 3 | 3 | DCS DCS DCS | 215 | 3 | 0 | miglioramento massimo; carta 26 |

Con i rovesciamenti (κA o κC nella fibra di 64):

* per 0 → 26, 26 → 0 e 5 → 21 la procedura scelta è **SCD SCD SCD con ε = (0,0,1)**, cioè κ1 = 0, κ2 = 0,
  κ3 = 1;
* per 0 → 20 è **SCD DCS SCD con ε = (0,0,1)**, cioè κ1 = 1 invece di 2.

In ogni caso diverso dall'originale il piano alternativo è **una Cronaca diversa** (per esempio #129 e #215 hanno
Assi (26,0,13) e (26,13,0)). Minimizzare κ2 cambia la Cronaca, non solo la Procedura (§ 10).

## 9. DP5 — decisione raccomandata

Le due sotto-decisioni restano separate.

**A. Quali metriche esporre.**

```text
Metriche disponibili:     κ1 (raccolte ≠ SCD), κ2 (raccolte CDS/DSC), κ3 (rovesciamenti),
                          ciascuna con la sua spiegazione in forma chiusa
                          (κ1 = d_H(c,t) fra le semplici; κ2 = #{ {c_i,b_i} = {0,2} } per il piano storico).
Metrica mostrata di default: la terna (κ1, κ2, κ3) per ogni procedura, senza un unico scalare.
Metrica per ordinare le alternative: κB con tie-break → chiave (κ3, κ2, κ1, m, #).
                          Prima le realizzazioni senza rovesciamenti, poi le più sicure rispetto alla
                          Prima Crisi, poi le più semplici; le varianti con rovesciamenti restano visibili.
```

**B. Quale strategia proporre automaticamente.**

```text
DP5 = mantenere il default storico, reso contrattuale, e mostrare tutte le alternative
                                                    [RACCOMANDAZIONE — richiede approvazione]
Strategia proposta automaticamente (I1):  argmin su F_semplice ∩ E_target_{c,t} di (κ1, #)
                                          = risolvi_trucco attuale (729/729), nessun cambiamento osservabile.
Alternativa esplicita offerta all'utente: «variante sicura» = argmin (κ3, κ2, κ1, m, #)
                                          (sostituisce CDS/DSC con DCS; stesso κ1; mai rovesciamenti).
```

Motivazione, secondo i criteri richiesti:

* **Riduzione dell'errore fisico.** κB elimina 486 raccolte a rischio di Prima Crisi senza costo in κ1. È un
  argomento forte, ed è per questo che la variante sicura va offerta.
* **Valore didattico.** Con κ2 minimo come default la Pratica non presenterebbe **mai** la Prima Crisi: 0 coppie su
  729 contro le 386 attuali. L'esercizio centrale della Pratica sparirebbe senza che l'utente lo sappia.
* **Coerenza col libro.** Il libro insegna la regola CDS ↔ DSC come competenza, non la evita; nessuna fonte
  prescrive una strategia di default.
* **Stabilità e compatibilità.** Mantenere il default non ha impatti (§ 12); cambiarlo altera in 386 coppie la
  sequenza, il numero #, la T mostrata e ciò che Presentazione e Protocollo ricevono dal Simulatore.
* **Spiegabilità.** «Il solutore minimizza (κ1, #) fra le procedure senza rovesciamenti» è verificabile e ora
  dichiarato.
* **Rovesciamenti.** κA e κC non vanno adottate come default finché Simulatore e Pratica non supportano i
  rovesciamenti (I2), e comunque solo dopo aver scelto come presentare il pareggio a 3 vie.

---

## 10. Interazione DP3/DP4/DP5

**DP3 cambia il conteggio κ3?**

* **No** per singola procedura: un flag è un flag.
* **Sì** per la famiglia: A contiene il capovolgimento del mazzo iniziale, B quello finale.
* Le distribuzioni misurate però coincidono (ESEC): stesso profilo `(0,1,1,1,2,2,2,3)`, stesse 242 coppie e stessi
  conteggi per κA, κB e κC.
* Cambia il **significato fisico** del piano selezionato in caso di pareggio (`m = 1`: «prima della terza
  distribuzione» in A contro «dopo la terza raccolta» in B, cioè gesti e T diverse).
* Per questo DP3 va approvata **prima** di fissare il tie-break.

**DP4 determina quali alternative confrontare?**

* **Sì.** Nel contesto carta→bersaglio l'insieme confrontato è la fibra E_target (64 procedure, 8 senza
  rovesciamenti), raggruppata per E_T.
* Nel contesto T è la classe E_T (8 procedure).
* Una metrica senza un insieme di confronto dichiarato non ha significato.

**DP5 deve operare in una fibra E_target o E_T?**

* **Nella fibra E_target**: il problema del solutore è «portare c in t», non «realizzare una T data».
* Dentro una classe E_T le raccolte sono determinate da ε (Cor. 5.2): ottimizzare lì significa scegliere solo la
  storia dei rovesciamenti, e il minimo di κ3 è sempre la procedura semplice unica.
* La metrica ha senso anche in E_T, ma come **ordinamento delle 8 realizzazioni di una Cronaca**, non come
  solutore.

**Un piano senza rovesciamenti può appartenere alla stessa E_T?**

* **Sì, sempre, ed è unico**: ogni classe E_T contiene esattamente una procedura con κ3 = 0 (ESEC, 216/216).

**Minimizzare κ2 cambia la Cronaca o solo la Procedura?**

* **Cambia la Cronaca.** Le 8 procedure semplici della fibra hanno 8 T distinte (729/729), quindi qualunque cambio
  di piano semplice cambia T (esempio: 0 → 26, da #129 a #215).
* Ne segue che il cambio si propaga a tutto ciò che legge T: Presentazione, Protocollo e Cicli, via
  `_notify_T_changed`.
* Solo dentro una classe E_T, cioè cambiando ε, si cambia la Procedura a Cronaca fissa, ma allora entrano i
  rovesciamenti.

## 11. Contratto concettuale minimo per I1

Qui si descrivono dati e operazioni, non una gerarchia di classi. Semantica: DP3 = A, DP4 = D e DP5 come al § 9,
tutte **subordinate all'approvazione**.

**Dati**

| Nome | Contenuto | Vincoli |
|---|---|---|
| **Procedura** p | `(S1, S2, S3 ∈ SIGLE ; ε1, ε2, ε3 ∈ {0,1})`, cioè raccolte e rovesciamenti | dominio Π di 1728 elementi; identificatori stabili `#(p) = k1+6k2+36k3` e `m(p) = 4ε1+2ε2+ε3` |
| **raccolte** | sigla di **mescolamento** (funzionale, riga del tabellone) per stadio; impilamento derivato = `IMPILAMENTO_DI` | CDS ↔ DSC; le altre quattro sono auto-inverse |
| **rovesciamenti** | ε_i = capovolgimento **prima della distribuzione** dello stadio i | adattatore B dichiarato (§ 4); «rovesciamento finale» solo come evento fuori famiglia |
| **Cronaca** | `T ∈ S27` con `T[carta] = posizione`, equivalentemente `(M2, M1, M0) ∈ G216` | 216 valori |
| **carta**, **bersaglio** | c, t ∈ 0..26 | `T(p)[c] = t` |
| **famiglia di gesti** F | predicato su p: `F_semplice` (ε = 0), `F_sicura` (nessuna CDS/DSC) e loro intersezioni | dichiarata, mai implicita |
| **metriche di costo** | κ1, κ2, κ3 : Π → {0..3}; chiavi composte = tuple + `(m, #)` | ordine totale e deterministico |

**Operazioni**

| Operazione | Firma concettuale | Garanzie da testare in I1 (descritte, non aggiunte ora) |
|---|---|---|
| **T(Procedura)** | p ↦ T | coincide con `compute_T_perm` sul preset Gioco Reale (1728/1728) e con l'oracolo fisico via adattatore `T_B(S; ε2,ε3,0) ∘ J^ε1` (1728/1728) |
| **fibra E_T** | T ↦ 8 procedure, una per ε | raccolte ottenute per inversione (Cor. 5.2); profilo κ3 `(0,1,1,1,2,2,2,3)`; esattamente una semplice |
| **fibra carta→bersaglio** | (c, t) ↦ 64 procedure raggruppate in 8 Cronache | 8 semplici in 8 Cronache distinte; ogni classe E_T inclusa per intero |
| **confronto di procedure** | (p, q[, c]) ↦ insieme delle relazioni vere fra identità, E_T, E_carta_c, stessa F, κ uguali o minori | catena identità ⇒ E_T ⇒ E_carta_c sempre rispettata |
| **ordina(insieme, chiave)** | lista ordinata | chiave `(κ…, m, #)`; stabile e indipendente dall'ordine di enumerazione |
| **solutore storico** | (c, t) ↦ argmin su F_semplice ∩ fibra di (κ1, #) | = `risolvi_trucco(c, t)` in 729/729 coppie |
| **variante sicura** | (c, t) ↦ argmin di (κ3, κ2, κ1, m, #) | κ2 = 0 e κ1 = d_H(c,t) in 729/729 coppie |
| **adattatori** | B ↔ A; R_AppC[k] ↔ R_prog[m] | identità del § 3.2; `k pari ⇒ m = k >> 1` |

Il contratto **non** modifica `risolvi_trucco`, `gioco_reale`, `compute_stage` né alcun export: li usa come
oracoli.

## 12. Impatto sulla compatibilità

**Cambio del piano predefinito del solutore** (per esempio da storico a κB), CODICE e TEST:

| Componente | Effetto | Classificazione |
|---|---|---|
| Simulatore | in 386/729 coppie cambiano sequenza, numero #, avviso «Prima Crisi» e T mostrata; la correttezza resta | **comportamento osservabile compatibile** |
| Pratica | cambiano i gesti attesi in 386 coppie e **scompare** ogni trappola CDS/DSC (0/729); le sessioni in corso sono congelate (`SessionePratica` immutabile) | **breaking UX** (didattico) |
| Presentazione | se alimentata dal Simulatore (`_notify_T_changed`) mostra un'altra disposizione; se alimentata dall'Explorer, nessun effetto | comportamento osservabile compatibile |
| Protocollo | stesso formato; cambia il contenuto se generato dopo il Simulatore (legge `_last_T_perm`) | comportamento osservabile compatibile |
| Test | le asserzioni esistenti verificano solo `T[c] == t`, il determinismo (`test_i18n`) e `T[0] == 13` per 0 → 13 (piano invariato: κ2 = 0); `test_729_coppie_carta_bersaglio` verifica la correttezza fisica | **nessun impatto** |
| Documentazione | `guide.s19.intro` descrive la forma chiusa senza fissare la regola di scelta; nessun esempio della guida o delle note usa un piano del solutore | **solo presentazione** (servirebbe una frase sulla regola) |
| Export e snapshot | il Simulatore non esporta; `R[m]` e i PDF non dipendono dal solutore | **nessun impatto** |

**Scelte DP3 e DP4:**

| Scelta | Effetto | Classificazione |
|---|---|---|
| DP3 = A (raccomandata) | nessuna modifica: il codice espone già A | **nessun impatto** |
| DP3 = B | `R[m]` del PDF da ridefinire, oppure due convenzioni visibili | **breaking formato** |
| DP4 = D | solo terminologia ed etichette, all'arrivo di I1 e I2 | **solo presentazione** |

La raccomandazione DP5 (default storico più alternative) ha **nessun impatto** su tutto ciò che esiste oggi.

## 13. Decisioni ancora aperte

1. **DP3.**
   * Formulazione esatta del prompt fisico in I2 («capovolgi, poi distribuisci» oppure «dopo la raccolta
     capovolgi»).
   * Se e dove esporre il «rovesciamento finale» (solo nel catalogo errori E2, fase 3).
   * Come dichiarare nei PDF e nella guida che `R[m]` segue la convenzione del modello e non la definizione
     testuale dell'App. C (possibile nuova voce, da non decidere qui).
2. **DP4.** Le etichette UI definitive dipendono dai nomi di **DP2**: «Cronaca», G216 e Γ648 non sono risolti qui.
3. **DP5.**
   * Se adottare la variante sicura come default **per contesto**, per esempio in una futura «modalità esecutore»
     di Presentazione, mantenendo lo storico in Pratica.
   * Se proporre piani con rovesciamenti quando I2 li supporterà, e come mostrare il pareggio a 3 vie.
   * Eventuale κ4 pesata (per esempio κ1 + κ3): **non** raccomandata ora, perché introdurrebbe pesi arbitrari.
4. **Precisazioni all'audit da registrare**, senza correzioni silenziose:
   * (a) l'ambito di «κ1 minimo 729/729» è «fra le procedure semplici»; con rovesciamenti non è minimo in 242/729;
   * (b) la divergenza di etichetta `R[m]` del PDF (A) contro `R[k]` dell'App. C (B);
   * (c) il selftest 1b riconcilia B con il modello matriciale, non con l'etichetta `R[m]`.
5. **Dipendenze segnalate e non risolte**: DP1 (versione ufficiale dell'articolo; App. D è citata solo come fonte
   sul modello del rovesciamento); DP2 (nomi); DP6–DP12 invariate.

## 14. Test/verifiche

**Test esistenti** (nessuno modificato):

* `tests/test_baseline_matematica.py` → 25 passed;
* `tests/test_gioco_reale.py` → 9 passed;
* `tests/test_tabellone_inverso.py` → 20 passed;
* `tests/test_dominio_selftest.py` → 7 passed;
* suite completa: non rieseguita (nessun cambiamento di codice; riferimento: audit V4, 1427 passed, 1 skipped,
  1 fallimento ambientale noto Tk 9 contro Tk 8.6, nessuna regressione reale).

**Verifiche ESEC** (Python inline, nessun file creato):

| # | Verifica | Esito |
|---|---|---|
| V1 | A = B senza rovesciamenti | 216/216 |
| V2 | `T_B(S;a,b,c) = J^c ∘ T_A(S;0,a,b)` | 1728/1728 |
| V3 | `T_A(S;e,a,b) = T_A(S;0,a,b) ∘ J^e` | 1728/1728 |
| V4 | coincidenza a indice uguale A/B | 512/1728 |
| V5 | immagini A e B: 216 T, fibre di 8, profilo κ3 `(0,1,1,1,2,2,2,3)` | sì (A e B) |
| V6 | § 2.5: `SCD, DCS, J, SCD` = vettore stampato; Assi 20, 13, 6; stessa Cronaca di #185 | sì |
| V7 | κ1(piano corrente) = d_H(c,t) | 729/729 |
| V8 | solutore = argmin (κ1, #) fra le semplici | 729/729 |
| V9 | κ2(piano corrente) = #{ {c_i,b_i} = {0,2} }; distribuzione 343/294/84/8; migliorabili 386 | 729/729 |
| V10 | κ1 minimo con rovesciamenti = min(d_H(c,t), d_H(26−c,t)); 242 coppie migliorabili | 729/729 |
| V11 | fibra E_target: 8 classi E_T × 8, classi incluse, 8 semplici in 8 classi | 729/729 |
| V12 | metriche κA, κB, κC su 8 e su 64 procedure, in A e in B (tabella § 7.4) | identiche in A e B |
| V13 | piani correnti con almeno una CDS/DSC (trappole di Pratica) | 386/729 |

**Invarianti proposti per i test di I1** (da aggiungere solo dopo l'approvazione): V1–V3, V5, V7–V11, l'esempio
discriminante (CSD,CSD,CSD) del § 3.3 e l'ordine totale della chiave `(κ…, m, #)`.

**Gate P-I1:**

| Gate | Esito |
|---|---|
| G1 DP3 ha una raccomandazione precisa | ✔ § 4 |
| G2 le due convenzioni sono riconciliate o dichiarate non equivalenti | ✔ § 3.2: equivalenti all'interno, non equivalenti ai bordi, con adattatore esplicito |
| G3 un solo modello canonico proposto per I1 | ✔ A |
| G4 DP4 distingue E_T, E_carta, E_target, E_gesti, E_costo | ✔ § 5 |
| G5 DP4 propone un default senza eliminare le altre relazioni | ✔ § 6 |
| G6 κ1 corrente verificata su 729 coppie | ✔ V7, V8 |
| G7 κ2 verificata su 729 coppie | ✔ V9 |
| G8 dato 386/729 confermato o corretto | ✔ confermato |
| G9 κ3 analizzata sulle fibre E_T | ✔ § 7.3, V5 |
| G10 almeno tre metriche composte misurate | ✔ κA, κB, κC |
| G11 tie-break deterministico definito | ✔ `(κ…, m, #)` |
| G12 impatto sul solutore corrente misurato | ✔ § 7.4, § 12 |
| G13 interazioni analizzate | ✔ § 10 |
| G14 contratto concettuale I1 proposto | ✔ § 11 |
| G15 nessun codice applicativo modificato | ✔ |
| G16 nessun test modificato | ✔ |
| G17 I1 non iniziato | ✔ |
| G18 DP1, DP2, DP6–DP12 non risolte implicitamente | ✔ § 13.5 |
| G19 matematica corrente invariata | ✔ baseline 25/25 |
| G20 nessun accesso fuori dal repository | ✔ |
| G21 nessun push | ✔ |

## 15. Git status

Prima del commit (ESEC):

```
## main...origin/main [ahead 67]
?? Articolo.pdf
?? LIBRO_MAIN.pdf
```

Commit previsto, unico: `docs(v4): analyze pre-I1 product decisions`, con il solo file
`V4_PRE_I1_PRODUCT_DECISIONS.md`.

* I PDF restano non tracciati; `.gitignore` non viene toccato.
* Nessun push.
* Dopo il commit `main` sarà avanti di 68 rispetto a `origin/main`, con gli stessi due PDF non tracciati.

---

## Tabella delle decisioni

| Decisione | Raccomandazione | Alternative scartate | Motivo principale | Richiede approvazione utente |
|---|---|---|---|---|
| DP3 — momento canonico del rovesciamento | **A**: ε_i prima della distribuzione dello stadio i; nel gesto, per gli stadi 2 e 3, «dopo la raccolta precedente» (stesso istante); adattatore `T_B = J^r3 ∘ T_A(0,r1,r2)` | B canonica (dopo la raccolta); linea temporale a 4 slot | coincide con le formule e i teoremi del libro e con ciò che il programma già espone (`R[m]`); A e B differiscono solo ai bordi, con un adattatore dimostrato | **SÌ** |
| DP4 — equivalenza di default | **D**: contestuale; carta→bersaglio: fibra E_target raggruppata per E_T (64 = 8 × 8); contesto T: E_T; mai «equivalente» non qualificato | A (E_T ovunque), B (E_carta ovunque), C (solo E_target) | è l'unica che mostra insieme «stesso bersaglio ≠ stessa Cronaca ≠ stessa procedura» | **SÌ** |
| DP5 — metrica e strategia di default | esporre κ1, κ2, κ3; ordinare le alternative con (κ3, κ2, κ1, m, #); **mantenere il default storico**, ora contrattuale = argmin (κ1, #) fra le semplici; offrire la «variante sicura» κB | κ2-min come default (κA o κB); κA o κC con rovesciamenti come default | la variante sicura evita 486 raccolte CDS/DSC ma cancellerebbe tutte le 386 trappole didattiche della Pratica; il default storico non ha impatti ed è ora spiegabile | **SÌ** |
