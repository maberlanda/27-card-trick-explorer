# I1 — Modello di procedura, relazioni e strategie: chiusura

Primo compartimento di implementazione della 4.0. Aggiunge un piccolo modello applicativo immutabile
(core/services + test) sopra la matematica esistente, secondo le decisioni DP3, DP4 e DP5 approvate in
`V4_PRE_I1_PRODUCT_DECISIONS.md`. Non aggiunge viste e non modifica GUI, guida, i18n, core o formati.

## 1. Baseline

**Stato all'ingresso** (verificato):

* branch `main`, HEAD `f20aaba`, `origin/main` `54445af`, 68 commit avanti;
* working tree tracciato pulito; non tracciati intenzionali solo `Articolo.pdf` e `LIBRO_MAIN.pdf`;
* `pytest tests/test_baseline_matematica.py` → **25 passed**.

**Ambiente**: CPython 3.12.14, Tk 9.0.4 sotto xvfb, stesso ambiente dell'audit V4.

## 2. File modificati

| File | Tipo | Contenuto |
|---|---|---|
| `gioco27/services/procedure.py` | nuovo | modello `ProceduraGioco` e `ServizioProcedure` |
| `gioco27/services/__init__.py` | modificato (+7) | esporta i nomi principali di I1 |
| `tests/test_procedure_i1_caratterizzazione.py` | nuovo | 18 test: fatti matematici provati con il solo core e con oracoli indipendenti |
| `tests/test_procedure_i1_servizio.py` | nuovo | 41 test: modello, dominio, classi per trasformazione, relazioni, chiavi, architettura |
| `tests/test_procedure_i1_strategie.py` | nuovo | 19 test: fibre carta→bersaglio, solutore storico, variante sicura, rovesciamenti e k1, casi leggibili |
| `I1_PROCEDURE_EQUIVALENCES_CLOSED.md` | nuovo | questo documento |

Restano invariati:

* `gioco27/core/`, `gioco27/gui/`, `gioco27/i18n.py`;
* guida, glossario, onboarding e presentazione;
* `pyproject.toml`, README e `.gitignore`;
* l'audit V4 e il memo pre-I1.

## 3. Modello introdotto

Il modello è in `gioco27/services/procedure.py` e usa **un solo** tipo di procedura.

| Oggetto | Natura | Contenuto |
|---|---|---|
| `ProceduraGioco` | dataclass congelata | `mescolamenti` (S1, S2, S3), sigle funzionali in ordine cronologico; `rovesciamenti` (e1, e2, e3) ∈ {0,1}³ con **rovesciamento prima della distribuzione dello stadio** (DP3 = A) |
| `Costo` | dataclass congelata | `k1`, `k2`, `k3` separati; nessun punteggio unico |
| `FamigliaGesti` | dataclass congelata | `senza_rovesciamenti`, `senza_raccolte_cicliche`; costanti `FAMIGLIA_TUTTE`, `FAMIGLIA_SEMPLICE`, `FAMIGLIA_SICURA`, `FAMIGLIA_SEMPLICE_SICURA` |
| `GruppoTrasformazione` | dataclass congelata | una trasformazione e le sue 8 procedure della fibra; `.semplice` è l'unica senza rovesciamenti |
| `FibraBersaglio` | dataclass congelata | `carta`, `bersaglio`, 8 `gruppi`; viste derivate `.procedure` (64) e `.semplici` (8) |
| `ConfrontoProcedure` | dataclass congelata | solo dati, nessun testo |
| `AdattamentoFisico` | dataclass congelata | parametri per l'oracolo fisico di `gioco_reale` (convenzione B) |
| `ProceduraNonValida`, `TrasformazioneFuoriDominio` | `ValueError` | `codice` stabile, messaggio neutro (come `PermutazioneNonValida`) |

**Proprietà derivate di `ProceduraGioco`** (nessuna memorizzata in parallelo):

* `impilamenti`, tramite `IMPILAMENTO_DI`;
* `numero_tavola` # = k1+6k2+36k3, tramite `gioco_reale.numero_tavola` e l'ordine di `SIGLE`;
* `indice_rovesciamenti` m = 4e1+2e2+e3;
* `identificatore` = (#, m);
* `costo`, `semplice` (k3 = 0), `sicura` (k2 = 0).

**Costruttore alternativo**: `ProceduraGioco.da_identificatore(#, m)`.

**Validazione**. Una procedura viene rifiutata con un codice in questi casi:

| Caso | Codice |
|---|---|
| sigla sconosciuta | `sigla_sconosciuta` |
| numero di stadi ≠ 3 | `numero_stadi` |
| rovesciamento non binario (2, `"1"`, 1.0) | `rovesciamento_non_binario` |
| stringa al posto della terna | `tipo_non_ammesso` |
| identificatore fuori intervallo | `identificatore_fuori_intervallo` |

I booleani sono normalizzati a 0 e 1. La nozione di sigla è quella di `gioco_reale.MESCOLAMENTO`: non ne esiste una
seconda.

**Nomi**: tecnici e neutrali. Nessun nome narrativo (Cronaca, Giullare, Seldon, Gaia) e nessun nome di gruppo
(H, Γ, G_ext) compare nell'API. DP2 e DP8 restano libere.

## 4. API e servizio

`servizio_procedure()` restituisce l'istanza condivisa di `ServizioProcedure`, costruita al primo uso (`lru_cache(1)`).
Costa circa 13 ms (misurato): le 1728 trasformazioni vengono precalcolate una volta. Il servizio è immutabile.

| Operazione | Restituisce |
|---|---|
| `procedure` | le 1728 procedure in ordine pubblico **(m, #)** crescente, generato aritmeticamente |
| `trasformazioni` | le 216 T, nell'ordine # delle procedure semplici |
| `trasformazione(p)` | `T(p)` come tupla, con `T[carta] = posizione finale`; calcolata da `core.permutations.compute_T_perm` sul preset «Gioco Reale» (nessuna reimplementazione di MSC, Kronecker, J o composizione) |
| `classe_trasformazione(T)` | le 8 procedure in ordine (m, #); `PermutazioneNonValida` se T non è una permutazione, `TrasformazioneFuoriDominio` se nessuna procedura la realizza |
| `stessa_trasformazione(p, q)` | relazione E_T |
| `stesso_effetto_carta(p, q, c)` | relazione E_carta_c; la carta è validata con `valida_indice` |
| `confronta(p, q, carta=None)` | `ConfrontoProcedure`: stessa procedura, stessa T, stesso effetto su c (oppure `None`), costi, semplici, sicure |
| `fibra_bersaglio(c, t)` | `FibraBersaglio`: 8 gruppi da 8, gruppi ordinati per # della loro procedura semplice |
| `ordina(procedure, chiave)` | tupla ordinata secondo una chiave dichiarata |
| `procedura_storica(c, t)` | argmin di `chiave_storica` = (k1, #) sulle procedure semplici della fibra |
| `procedura_sicura(c, t)` | argmin di `chiave_sicura` = (k3, k2, k1, m, #) sull'intera fibra |

**Funzioni di modulo**:

* `chiave_costo(*metriche)` con metriche fra `"k1"`, `"k2"` e `"k3"`, chiusa sempre da (m, #): è quindi un ordine
  totale;
* `chiave_storica`, `chiave_sicura`;
* `adattamento_fisico(p)`.

Non ci sono una classe astratta di «equivalenza», framework, eventi o cache complesse. Il servizio non fa I/O, non
usa thread e non genera testo localizzato.

## 5. Decisioni applicate

**DP3** — modello canonico **A**:

```
T_i = (S_i ⊗ I3 ⊗ I3) ∘ MSC ∘ J^e_i        T = T3 ∘ T2 ∘ T1        m = 4e1 + 2e2 + e3
```

* La convenzione B di `gioco_reale` (rovesciamento dopo la raccolta) è **solo oracolo**, raggiunto con
  `adattamento_fisico`, per cui `T_A(S; e1,e2,e3) = T_B(S; e2,e3,0) ∘ J^e1`.
* Non esiste una `ProceduraB` (il test lo verifica).
* Il rovesciamento dopo l'ultima raccolta resta fuori dalla famiglia canonica e non è modellato.
* `R[m]` non è stato ridefinito; la divergenza R[m] (A) / R[k] App. C (B) non è corretta qui.

**DP4** — nessuna «strategia equivalente» generica:

* le relazioni sono nominate (identità, stessa trasformazione, stesso effetto sulla carta c);
* famiglie di gesti e costi sono filtri e chiavi dichiarati;
* nel problema c → t l'oggetto è la **fibra completa strutturata** (8 × 8), non appiattita;
* nel contesto di una T l'oggetto è la **classe di 8**.

**DP5** — `risolvi_trucco` non è stato toccato:

* la procedura storica è l'argmin di (k1, #) fra le semplici e coincide con `risolvi_trucco` in 729/729 coppie;
* la **variante sicura** (k3, k2, k1, m, #) è una capacità distinta: non la sostituisce e nessuna vista la usa.

## 6. Invarianti matematici e conteggi verificati

| Invariante | Oracolo indipendente | Esito |
|---|---|---|
| 1728 procedure, 1728 identificatori (#, m) distinti, ricostruzione da (#, m) | aritmetica dell'identificatore | 1728/1728 |
| T(p) = core del preset Gioco Reale (`iter_combinations_ex` + `compute_T_perm`) | formula cifra per cifra del libro | 1728/1728 |
| T(p) = formula del libro | scritta nei test | 1728/1728 |
| DP3: T_A(S;e) = T_B(S;e2,e3,0) ∘ J^e1 | simulazione fisica `T_da_partita` | 1728/1728 |
| DP3: T_B(S;r) = J^r3 ∘ T_A(S;0,r1,r2) | idem | 1728/1728 |
| A e B allo stesso indice | idem | 512/1728: non equivalenti |
| procedure semplici = tavola | `T_da_tabellone` | 216/216 |
| 216 trasformazioni, 8 procedure ciascuna | — | sì |
| profilo k3 (0,1,1,1,2,2,2,3) ed esattamente una procedura semplice per classe | — | 216/216 |
| classe dell'identità: SCD³ con e pari, DCS³ con e dispari | — | sì |
| fibre c → t: 64 procedure, 8 T, 8 gruppi da 8, 8 semplici una per gruppo, classi incluse per intero | forza bruta sulla formula del libro | 729/729 |
| procedura storica = `risolvi_trucco` (sigle, impilamenti, #, T) | core | 729/729 |
| k1 storico = distanza di Hamming ternaria | distanza scritta nel test | 729/729 |
| variante sicura = argmin dichiarato | forza bruta con chiave del test | 729/729 |
| variante sicura: k3 = 0, k2 = 0, k1 uguale alla storica | — | 729/729 |
| coppie con storica ≠ sicura | — | **386** |
| raccolte CDS/DSC eliminate | — | **486** |
| k1 minimo con rovesciamenti = min(d_H(c,t), d_H(26−c,t)) | distanza del test | 729/729 |
| coppie in cui i rovesciamenti riducono k1 | — | **242**: 174 di 1, 60 di 2, 8 di 3 |
| esempio discriminante (CSD,CSD,CSD), 8 gesti A/B | valori del memo § 3.3 | sì |
| esempio del libro § 2.5 = A e=(0,0,1) = #185 | vettore stampato | sì |

**Casi leggibili**: 0→13, 13→13, 0→2, 26→24, 0→20, 7→19, 0→26 e 26→0, con # e costi di storica e sicura come nel
memo. Inoltre 0→13 con #86 e #158 (stesso bersaglio, trasformazioni diverse) e 0→26 con SCD³ ed e=(0,0,1)
(un rovesciamento sostituisce tre raccolte).

**Test-first**:

* i contratti sono stati caratterizzati prima con il solo core (primo commit, verde);
* `test_procedure_i1_servizio.py` è stato eseguito **rosso** prima dell'implementazione (errore di collezione:
  modulo assente) e poi verde;
* nessun test confronta una funzione con sé stessa: gli oracoli sono la formula del libro, la simulazione fisica,
  la forza bruta e la distanza di Hamming scritte nei test.

## 7. Suite di test

La suite è stata eseguita un file per volta con xvfb, come nell'audit, perché l'esecuzione unica va in crash con
Tk 9.

| Insieme | Esito |
|---|---|
| test I1 (3 file) | **78 passed** (18 + 41 + 19) |
| `test_baseline_matematica.py` | **25 passed** |
| suite completa, 41 file, 1507 test | **1505 passed, 1 skipped, 1 failed** |

* **Skipped**: `test_layout_dettaglio.py` (manca `pypdfium2`), come nell'audit.
* **Failed**: `test_layout_accessibilita_h2.py::test_lo_scorrimento_si_accende_quando_il_testo_cresce`. È **lo
  stesso fallimento ambientale noto** (metriche dei font di Tk 9.0.4 contro Tk 8.6 dell'ambiente H2). H2 non è
  stato modificato.
* **Rispetto all'audit**: 1429 test (1427 passed, 1 skipped, 1 failed) + 78 nuovi = 1507. Nessuna nuova
  regressione.

## 8. Compatibilità

| Componente | Effetto |
|---|---|
| `risolvi_trucco` | codice invariato; coincidenza 729/729 verificata |
| Simulatore, Pratica, Presentazione, Protocollo | invariati: nessun file GUI modificato; un test verifica che nessuna vista usi il servizio o la variante sicura |
| export e formati (CSV, PDF, `R[m]`, HTML) | invariati: nessun file di core o di export modificato |
| `gioco27.services` | l'import espone in più i nomi di I1 e non importa GUI né `tkinter` (verificato in un processo separato) |

## 9. Invarianti architetturali

Il grafo è stato verificato con un'analisi AST inline sul package e con i test G1 esistenti
(`test_servizi_g1.py`: 44 passed; `test_static.py` / pyflakes: 2 passed).

| Invariante | Valore |
|---|---|
| core → services | 0 |
| core → gui | 0 |
| services → gui | 0 |
| services → tkinter | 0 |
| cicli d'importazione nel package | 0 |
| worker che toccano Tk | 0 (I1 non ha worker) |
| parser autorevoli | 1 (I1 non aggiunge parser) |

Nessuna eccezione è stata aggiunta agli strumenti statici. Dipendenze di `services.procedure`:
`core.gioco_reale`, `core.permutations.compute_T_perm`, `core.constants.PERM3` e `core.dominio`.

## 10. Debiti per I2 e oltre

1. **Rovesciamento finale** (dopo l'ultima raccolta): fuori dalla famiglia canonica, non modellato. Servirà in I2
   per l'errore E2 alla fase 3, come evento distinto T' = J∘T.
2. **Divergenza R[m] / R[k] App. C**: da documentare nel compartimento appropriato; nessuna modifica di formato.
3. **Etichette UI** delle relazioni e delle fibre: dipendono da DP2 e DP8.
4. **Uso della variante sicura** nelle viste ed eventuali proposte con rovesciamenti (pareggio a 3 vie): decisioni
   di I2 e successive.
5. Un eventuale prompt fisico «capovolgi, poi distribuisci» e l'uso di `adattamento_fisico` nel Simulatore
   appartengono a I2.

Restano aperte DP1, DP2 e DP6–DP12. I2–I7, J e K non sono iniziati.

## 11. Gate

| Gate | Esito |
|---|---|
| G1 un solo modello canonico, DP3 = A | ✔ |
| G2 nessun modello B concorrente | ✔ |
| G3 1728 procedure senza duplicati | ✔ |
| G4 (#, m) identifica univocamente la procedura | ✔ |
| G5 T coincide con il core | ✔ |
| G6 verifica con l'oracolo fisico DP3 completa | ✔ |
| G7 216 T, 8 procedure per T | ✔ |
| G8 profilo k3 | ✔ |
| G9 una sola procedura semplice per classe | ✔ |
| G10 729 fibre da 64 | ✔ |
| G11 8 T per fibra | ✔ |
| G12 8 procedure semplici per fibra | ✔ |
| G13 E_T ed E_carta distinte e testate | ✔ |
| G14 famiglie semplice e sicura esplicite | ✔ |
| G15 k1, k2, k3 separati | ✔ |
| G16 tie-break deterministico | ✔ |
| G17 storica = `risolvi_trucco` 729/729 | ✔ |
| G18 k1 = Hamming 729/729 | ✔ |
| G19 sicura con k2 = 0 in 729/729 | ✔ |
| G20 386 differenze | ✔ |
| G21 486 raccolte eliminate | ✔ |
| G22 242 coppie | ✔ |
| G23 distribuzione 174/60/8 | ✔ |
| G24 nessuna GUI modificata | ✔ |
| G25 `risolvi_trucco` invariato | ✔ |
| G26 nessun formato cambiato | ✔ |
| G27 invarianti architetturali | ✔ |
| G28 baseline 25/25 | ✔ |
| G29 nessuna nuova regressione | ✔ |
| G30 DP aperte restano aperte | ✔ |
| G31 I2+ non iniziati | ✔ |
| G32 PDF non tracciati | ✔ |
| G33 nessun accesso fuori dal repository | ✔ |
| G34 nessun push | ✔ |

## 12. Commit e stato Git

| Commit | Messaggio |
|---|---|
| `e00c9cf` | `test(I1): characterize procedure fibers and strategy costs` |
| `7550473` | `feat(I1): add canonical procedure and equivalence service` |
| `33d03ec` | `test(I1): verify historical and safe strategy selection` |
| (questo) | `docs(I1): close procedure and equivalence compartment` |

Stato prima del commit di chiusura:

```
## main...origin/main [ahead 71]
?? Articolo.pdf
?? LIBRO_MAIN.pdf
```

Dopo il commit di chiusura sono 72 commit avanti, con gli stessi due PDF non tracciati. Nessun push.
