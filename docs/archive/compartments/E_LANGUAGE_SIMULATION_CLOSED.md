# E_LANGUAGE_SIMULATION_CLOSED — chiusura del compartimento E (Linguaggio, AST e simulazione)

Registro verificabile. Il quadro generale resta in `GIT_BASELINE_AND_RECONCILIATION.md`;
le chiusure precedenti in `A_BASELINE_CLOSED.md`, `D_DOMAIN_CLOSED.md`, `B_IO_CLOSED.md` e
`C_STATE_CLOSED.md`.

## 1. Identità

| Voce | Valore |
|---|---|
| Branch | `main` — nessun push: `origin/main` resta a `54445af` |
| HEAD iniziale | `2b99dda7c3bf5ebc1f9a234462b720b6da9db09a` — «docs(C): record closed state compartment» |
| HEAD finale | l'ultimo commit dell'elenco in § 11 |
| Working tree all'avvio | pulito; i commit di A, D, B e C presenti e non riscritti |
| Baseline di partenza | 869 raccolti, **868 passati, 1 saltato, 0 falliti** — coincide con quella attesa dopo C; `pytest tests/test_baseline_matematica.py` → 25 passati |
| Perimetro | soltanto il repository corrente; nessuna directory esterna letta o confrontata |

L'unico skip resta **N03** (`pypdfium2` non installata), debito di K.

## 2. B07 — la divergenza, misurata prima di correggerla

Due grammatiche leggevano lo stesso testo: quella dell'Explorer (`core/algebra.py`, Lexer +
Parser + AST) e una seconda, a espressioni regolari, dentro
`gui/shuffle.py::_validate_and_parse`. Quest'ultima normalizzava gli operatori, **cancellava
l'operatore finale** (`re.sub(r"\s+o\s*$", "", e)`), sostituiva i blocchi Kronecker con
segnaposto e poi **buttava via tutte le parentesi rimaste**, valide o spaiate che fossero.

Il corpus condiviso — ricavato da `Lexer.VALID_ATOMS`, dalla grammatica
`expr ::= term (∘ term)*`, `term ::= factor (⊗ factor)*`, `factor ::= ATOM | '(' expr ')'`,
dai test preesistenti e dalle stringhe prodotte dall'Analisi — è fatto di **29 espressioni
valide**, **3 sintatticamente valide ma di tipo 3**, **29 invalide** e **64 combinazioni
«espressione valida + coda invalida»**: 125 casi in tutto. Nessuna sintassi è stata inventata.

Su quel corpus, **prima** della correzione:

```text
accettate dall'Explorer, rifiutate dal Mescolamento   (5)
    I
    J
    J o J
    MSC o J
    ((SCD_U o CDS_U) x SCD_U x SCD_U)

accettate dal Mescolamento, rifiutate dall'Explorer   (8)
    MSC o      MSC ∘      MSC @      MSC)
    (MSC       MSC))      ((MSC)     [MSC

code invalide ignorate dal Mescolamento: 36 su 64
```

**Comportamento finale**: 0 discordanze su 125. I tre casi storici citati dalla baseline:

| Espressione | Explorer | Mescolamento |
|---|---|---|
| `MSC o` | rifiutata | **rifiutata** (prima: accettata) |
| `MSC)` | rifiutata | **rifiutata** (prima: accettata) |
| `I` | accettata | **accettata** (prima: rifiutata) |

`I` appartiene al linguaggio valido: è uno dei simboli di `Lexer.VALID_ATOMS` e vale
l'identità di 27, come il corpus autorevole conferma (`perm == list(range(27))`).

La regressione è stata **prima rossa e poi verde**: il primo commit introduce il corpus con
tre prove marcate `xfail(strict=True)` — falliscono sul codice non ancora toccato e, grazie a
`strict`, sarebbero diventate rosse anche passando per caso; il terzo commit toglie i
marcatori e le trasforma in asserzioni normali su tutto il corpus.

## 3. Il linguaggio

**Grammatica autorevole**: quella di `gioco27/core/algebra.py`, invariata.

```text
expr   ::= term (COMPOSE term)*        COMPOSE:  o | ∘ | @
term   ::= factor (KRON factor)*       KRON:     x | ⊗   (esattamente 3 fattori)
factor ::= ATOM | '(' expr ')'         parentesi tonde e quadre equivalenti
ATOM   ::= MSC | J | I | GEN3 | R_U | I_3
```

**Sintassi deliberatamente preservata** (tutta verificata dal corpus): i sei nomi dei
generatori; gli alias storici `R_U` = `DCS_U` e `I_3` = `SCD_U`; `MSC`, `J`, `I`; i tre
operatori di composizione e i due di Kronecker; le parentesi quadre dei turni; il prefisso
`T =` delle stringhe dell'Analisi; spazi multipli e a capo; le forme `((...))`,
`(a) o (b)`, i raggruppamenti a sinistra e a destra; i fattori Kronecker composti.

**Sintassi permissiva eliminata**, perché non apparteneva alla grammatica reale: operatore
finale (`MSC o`, `MSC ∘`, `MSC @`), parentesi spaiate in qualunque verso (`MSC)`, `(MSC`,
`MSC))`, `((MSC)`, `[MSC`) e, in generale, qualunque coda dopo un prefisso valido. I due
linguaggi **non** sono stati uniti prendendo l'unione permissiva: il più permissivo è stato
cancellato, il più povero è stato allineato a quello autorevole.

## 4. AST

**Proprietario**: `gioco27/core/algebra.py` — `SymbolicExpr`, invariata nei nodi:

| Nodo | Significato |
|---|---|
| `atom` | simbolo terminale (`MSC`, `J`, `I`, generatori di tipo 3) |
| `compose` | composizione n-aria, figli in ordine testuale |
| `kron` | prodotto di Kronecker, esattamente 3 fattori di tipo 3 |
| `value` | foglia con permutazione già calcolata (prodotta dal Rewriter) |

Nessun nodo è stato aggiunto: l'AST esistente era sufficiente ed è stata resa accessibile ai
consumatori invece di crearne una seconda. L'unica aggiunta è un attributo, `origine`, che
conserva la grafia con cui l'atomo compariva nel testo: `name` continua a normalizzare gli
alias di gioco per la matematica, `origine` permette di rimostrare la formula com'era scritta
senza ricostruirla. `clone()` lo propaga; `__repr__` e la normalizzazione continuano a usare
`name`, quindi nulla cambia per l'Explorer.

Una espressione viene parsata **una volta sola**: Explorer e Mescolamento partono dalla stessa
AST e non ne ricostruiscono due interpretazioni.

## 5. Valutazione

Invariata. `Evaluator` valuta l'AST con `(a ∘ b)[i] = a[b[i]]`, cioè in `A ∘ B` si applica
**prima B**; il Kronecker resta `9·a[i₂] + 3·b[i₁] + c[i₀]`. Restano intatte le convenzioni
protette da D:

```text
T[carta] = posizione di destinazione
mazzo[posizione] = carta
M[T[i], i] = 1
```

Da cui la relazione fra i due mondi, che prima era implicita in un solo test e ora è
formalizzata e verificata su tutto il corpus:

```text
mazzo finale della simulazione = inversa(T)        (la carta c finisce in posizione T[c])
```

L'ordine cronologico della simulazione è **opposto** a quello di lettura della forma algebrica:
non è un'inversione «intuitiva», è la conseguenza di `(a ∘ b)` che applica prima `b`, ed è
dimostrata da due prove indipendenti (§ 7).

## 6. Traccia

`gioco27/core/espressione.py` — il contratto che mancava, senza nessuna grammatica propria:

```text
analizza(testo)            → SymbolicExpr        (Lexer + Parser di core/algebra.py)
permutazione_di(espr)      → T
traccia_simulazione(espr)  → TracciaEsecuzione
```

| Struttura | Contenuto |
|---|---|
| `TracciaEsecuzione` | `passi`, `mazzo_iniziale`, `permutazione`, proprietà `mazzo_finale` |
| `PassoEsecuzione` | `indice` / `totale` (ordine **cronologico**), `operazione` (`MSC`, `KRON`, `ATOMO`), `etichetta` (la grafia del testo, alias compresi), `permutazione` del solo fattore, `mazzo` dopo il passo |

**Come viene derivata**: l'AST viene appiattita nei fattori applicati al mazzo (un nodo
`compose` contribuisce con i figli, un nodo `kron` resta **un solo** passo anche se i suoi
fattori sono composizioni di tipo 3), la lista viene percorsa da destra a sinistra e ogni
permutazione viene applicata allo stato corrente. Il raggruppamento non cambia nulla:
`((A ∘ B) ∘ C)`, `(A ∘ (B ∘ C))` e `A ∘ B ∘ C` producono la **stessa** traccia, non solo lo
stesso prodotto.

**Come la consuma il Mescolamento**: `_build_steps` e `_build_steps_card_by_card` scorrono i
passi nell'ordine ricevuto e prendono lo stato del mazzo dalla traccia. Non invertono più
nulla e non calcolano più nessuna permutazione.

Questa «history» è soltanto la cronologia matematica di **una** valutazione. Non è un bus di
eventi (G) e non è la cronologia dell'utente con undo/redo ed esperimenti salvati (J):
nessuno dei due è stato iniziato.

## 7. Explorer e Mescolamento: prima, dopo, prova

```text
PRIMA                                      DOPO

testo ──► Lexer/Parser ──► AST ──► T       testo ──► Lexer/Parser ──► AST ──┬──► T
     └──► regex shuffle ──► token ──► passi                                  └──► traccia ──► passi
```

**Prova di equivalenza**, su ognuna delle 29 espressioni valide e sulle 140 del corpus
generativo, con tre controlli che non condividono l'implementazione:

1. un **oracolo scritto nel test**, in aritmetica elementare, senza numpy e senza funzioni del
   package: applica i passi al mazzo ordinato e deve dare `inversa(T)`, con `T` calcolata
   dall'Explorer attraverso `Controller.process` (parsing, normalizzazione, valutazione);
2. la **fattorizzazione**: componendo le permutazioni dei passi in ordine testuale con una
   `_componi` locale si riottiene esattamente `T`;
3. il **passaggio attraverso la vista**: `_build_steps(traccia)` arriva allo stesso mazzo
   finale, e produce esattamente `len(traccia) + 1` passi visivi (lo stato iniziale più uno
   per trasformazione).

Esempio (`T = [(SCD_U x SCD_U x DCS_U) o MSC o (R_U x R_U x R_U)]`):

```text
passo 0  KRON   (R_U x R_U x R_U)            ← il fattore più a destra è il primo applicato
passo 1  MSC    MSC
passo 2  KRON   (SCD_U x SCD_U x DCS_U)
mazzo finale == argsort(T)                    ✓
```

Gli alias restano visibili: l'etichetta del passo è `(R_U x R_U x R_U)`, non
`(DCS_U x DCS_U x DCS_U)`, mentre la permutazione usata è quella normalizzata.

## 8. Errori

| Caso | Explorer | Mescolamento |
|---|---|---|
| Non è una formula | `ok=False`, messaggio, `perm=None` | `ParseError` |
| È una formula, ma di tipo 3 | `ok=False`, messaggio `explorer.error.type3_result` | `EspressioneNonSimulabile` |

`EspressioneNonSimulabile` è una `ValueError` distinta da `ParseError`: la grammatica non è
stata violata, è il risultato a non appartenere al dominio della simulazione. Nessun recupero
silenzioso — un test verifica che su ogni input invalido l'Explorer non produca né
permutazione, né forma normalizzata, né passi parziali, e che il Mescolamento non restituisca
mai una traccia. Il testo dei messaggi resta un problema di presentazione: nessuna chiave è
stata spostata in H.

## 9. Architettura

```text
parser sintattici autorevoli = 1        gioco27/core/algebra.py
```

| Responsabilità | Proprietario |
|---|---|
| Grammatica (Lexer, Parser) | `gioco27/core/algebra.py` |
| AST (`SymbolicExpr`) | `gioco27/core/algebra.py` |
| Valutazione (`Evaluator`, `Rewriter`, `Controller`) | `gioco27/core/algebra.py` |
| Traccia (`TracciaEsecuzione`, `PassoEsecuzione`) | `gioco27/core/espressione.py` |
| Adapter legacy | `gui/shuffle.py::_validate_and_parse`, che delega interamente a `traccia_simulazione` e non contiene grammatica |

Dipendenze, verificate da test e non solo dichiarate:

```text
parser/AST → tkinter      0     (test su sorgente + prova a runtime in sottoprocesso)
parser/AST → gui          0     (importare core.espressione non carica gioco27.gui)
parser/AST → filesystem   0     (le classi Token, Lexer, Parser, SymbolicExpr, Evaluator
                                 non nominano open, os, pathlib, csv, openpyxl)
```

`core/algebra.py` resta proprietario anche di funzioni di export che il filesystem lo toccano:
il modulo, nel suo insieme, non è neutro. La verifica è quindi fatta **sui simboli del
linguaggio**, non sul file, come il perimetro di E consente: il contratto è unico e non
esistono parser paralleli. La separazione fisica del modulo resta un debito di G.

Nel visualizzatore non esistono più: `import re`, l'insieme `GEN3`, `_make_kron27`, `PERM3`,
`_MSC_PERM` e ogni `argsort` — 725 righe prima, 665 dopo. Un test lo verifica sul sorgente,
e un altro che nel package esista una sola classe `Lexer` e una sola `Parser`.

## 10. Non-regressione

Riproduzioni rieseguite **dopo** E, nello stesso ambiente:

```text
B01  CORRETTO   400/400 sequenze nel file riletto, tre fogli
B02  CORRETTO   dopo A e import B: aggregati [B], grezzi [], origine 'csv'
B03  CORRETTO   reset durante il lavoro → il completamento tardivo non pubblica
B04  CORRETTO   campi cambiati a (1,5): «ricomincia» usa ancora carta=0 bersaglio=13
B05  PRESENTE   [0,0,99] ancora accettata come T                        (F)
B06  PRESENTE   4 stadi: count=6, iter=1                                (F)
B07  CORRETTO   'MSC o' e 'MSC)' rifiutate da entrambi, 'I' accettata da entrambi;
                discordanze su 125 espressioni: 0
B08  CORRETTO   cache vuota per un bersaglio in G → miss
B09  CORRETTO   con -O il guasto iniettato resta rilevato               (D)
B10  CORRETTO   registrazione font fallita → ('Helvetica', 'Helvetica-Bold')
B11  CORRETTO   ExportTooLarge su 5.159.780.352, nessun file creato
B12  CORRETTO   generatore guasto → _Generato(ok=False)
M03  CORRETTO   notifiche: Cicli=1, Distribuzione=[]
```

**B05 e B06 restano presenti e invariati**: appartengono a F e non sono stati toccati. Le
funzioni che il compartimento non doveva modificare — `analizza_righe`, `analizza_csv`,
`valida_filtri`, `count_combinations_ex`, `iter_combinations_ex` — sono rimaste identiche:
nessuna compare fra le righe cambiate del diff.

I contratti introdotti in C (`RisultatoAnalisi`, revisioni dell'analisi, `SessionePratica`,
`run_in_thread` per il selftest) non sono stati toccati: i loro test passano invariati.
`R04` e `N02` (D) e `N06` (B) restano chiusi.

## 11. Test

Ambiente di riferimento invariato (Linux, **Python 3.12.3**, tkinter 8.6 con Xvfb, NumPy
2.5.3, ReportLab 5.0.1, openpyxl 3.1.5, pypdf 6.18.1, pikepdf 10.13.0, pytest 9.1.1,
pyflakes 3.4.0). Comando:
`PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m pytest -p no:cacheprovider -ra -q`.

| Voce | Prima di E | Dopo E |
|---|---:|---:|
| Raccolti | 869 | **1097** |
| Passati | 868 | **1096** |
| Falliti | 0 | **0** |
| Saltati | 1 | **1** (N03) |

* Nuovo file `tests/test_linguaggio_espressioni_e.py` → **228 test** in 0,6 s.
* Baseline matematica → **25 passati**; dominio di D → **163**; I/O di B → **149**; stato e
  concorrenza di C → **78**; i18n → **176**; statici di A (N01) → **2**.
* `pyflakes` su `gioco27`, `tests`, `conftest.py`, `gioco27.py`: nessun avviso, a ogni passo.
* Nessun test dipende da tempi, rete o risorse esterne. Il corpus generativo è costruito per
  enumerazione, senza casualità e senza dipendenze nuove: 140 espressioni, le stesse a ogni
  esecuzione.

**Ogni commit è stato verificato singolarmente con la suite completa**, ricostruendo l'albero
esatto di quel commit nell'ambiente di riferimento (confronto per hash degli otto file):

| Commit | Suite |
|---|---|
| `test(E)` divergenza | 870 passati, 1 saltato, **3 xfailed**, 0 falliti |
| `refactor(E)` parser e AST | 938 passati, 1 saltato, 3 xfailed, 0 falliti |
| `refactor(E)` traccia dallo Shuffle | 1065 passati, 1 saltato, 0 falliti |
| `test(E)` equivalenza | 1096 passati, 1 saltato, 0 falliti |

## 12. File modificati

| File | Tema |
|---|---|
| `gioco27/core/espressione.py` | **nuovo** — `analizza`, `permutazione_di`, `traccia_simulazione`, `TracciaEsecuzione`, `PassoEsecuzione`, `EspressioneNonSimulabile` |
| `gioco27/core/algebra.py` | `SymbolicExpr.origine`; il prefisso «T =» passa al parser; il Controller non lo ripete |
| `gioco27/gui/shuffle.py` | il secondo parser sparisce; i passi vengono dalla traccia (−60 righe nette) |
| `gioco27/i18n.py` | una chiave nuova in IT e EN: `shuffle.operation_atom` |
| `tests/test_linguaggio_espressioni_e.py` | **nuovo** — corpus condiviso e 228 test |
| `tests/test_i18n.py` | conteggio del catalogo; il test che leggeva i token del vecchio parser ora legge le etichette della traccia |
| `tests/test_i18n_anomalie_ui.py`, `tests/test_i18n_audit_finale.py` | conteggio del catalogo 1288 → 1289 |

Diff sintetico `2b99dda..HEAD`: **8 file, 811 inserimenti, 162 cancellazioni**.

Chiavi i18n: **1288 → 1289** in entrambe le lingue, simmetriche e con gli stessi segnaposto.
L'unica aggiunta, `shuffle.operation_atom`, serve ai passi `J` e `I`, che prima il
visualizzatore non poteva mostrare perché non li accettava; il log riusa `shuffle.log_kron`,
già generico. Nessuna chiave rimossa, nessun testo esistente modificato, nessun cambiamento di
layout, tooltip o accessibilità: H non è stato iniziato.

## 13. Commit locali

| # | Hash | Messaggio |
|---|---|---|
| 1 | `11523dc` | `test(E): expose Explorer/Shuffle parser divergence (B07)` |
| 2 | `bd6ec37` | `refactor(E): establish single expression parser and AST` |
| 3 | `9d44ed4` | `refactor(E): derive shuffle trace from parsed expression` |
| 4 | `c04bc42` | `test(E): enforce Explorer/Shuffle semantic equivalence` |
| 5 | — | `docs(E): record closed language compartment` (questo documento) |

Nessun push, nessun `reset`/`rebase` distruttivo, nessun commit precedente riscritto.
`origin/main` resta a `54445af`.

*Errata*: il messaggio del commit 1 dice «30 invalide»; le espressioni invalide del corpus
sono **29** (29 valide + 3 di tipo 3 + 29 invalide = 61, più 64 combinazioni con coda = 125).
I conteggi di questo documento sono quelli verificati.

## 14. `git status` finale

```text
On branch main
Your branch is ahead of 'origin/main' by 28 commits.

nothing to commit, working tree clean
```

Nessun `__pycache__`, nessun `.pytest_cache`, nessun artefatto di esecuzione lasciato nel
repository.

## 15. Gate di uscita

| Gate | Esito |
|---|---|
| E-G1 esiste un solo parser autorevole | **OK** — § 9, verificato da test sul package |
| E-G2 Explorer e Mescolamento accettano lo stesso linguaggio | **OK** — § 2, 29/29 valide |
| E-G3 rifiutano lo stesso corpus invalido | **OK** — § 2, 29 invalide + 3 di tipo 3 |
| E-G4 nessun parser permissivo ignora token o coda | **OK** — 64 combinazioni, 0 tollerate |
| E-G5 `MSC o` viene rifiutata | **OK** — § 2 |
| E-G6 `MSC)` viene rifiutata | **OK** — § 2 |
| E-G7 `I` accettata da entrambi | **OK** — § 2, confermata valida dal parser autorevole |
| E-G8 lo Shuffle deriva i passi da AST/semantica unica | **OK** — § 6 |
| E-G9 T dell'Explorer e mazzo finale coerenti | **OK** — § 7, oracolo indipendente |
| E-G10 ordine di composizione invariato | **OK** — § 5, `(a ∘ b)[i] = a[b[i]]` |
| E-G11 baseline matematica verde | **OK** — 25/25 |
| E-G12 A/B/C/D restano corretti | **OK** — § 10 |
| E-G13 B05 e B06 presenti e invariati | **OK** — § 10 |
| E-G14 parser/AST non dipendono da GUI/Tk/filesystem | **OK** — § 9, con la precisazione sul file `algebra.py` |
| E-G15 nessun nuovo linguaggio inventato | **OK** — § 3, corpus ricavato dall'esistente |
| E-G16 nessun altro compartimento iniziato | **OK** — F, G, H, I, J, K intatti |
| E-G17 suite completa verde | **OK** — 1096 passati, 1 saltato, 0 falliti |
| E-G18 nessun push | **OK** — `origin/main` fermo a `54445af` |

**Il compartimento E è chiuso.**

## 16. Debiti rimasti

| Voce | Stato | Proprietario |
|---|---|---|
| **B07** | **chiuso in E** | — |
| **B05, B06** | presenti, non toccati | **F** — semantica dell'analisi e dei filtri |
| **R01** | aspetto revisione/annullamento coperto in C; il resto aperto | F |
| **R06** | presente | K |
| **R07** | presente | G |
| **M01, M04, M06** | presenti | H |
| **M05 residuo** | conservazione dei temporanei HTML di `protocol_dialog` | H |
| **N03** `pypdfium2` non dichiarata | aperto: unico skip della suite | K |
| **N04** `gioco27.spec` non versionato | aperto | K |
| Separare fisicamente il linguaggio dalle funzioni di export di `core/algebra.py` | aperto: il contratto è unico, il file no | G |
| Modello condiviso dei risultati fra schede (`AnalysisResult`) | aperto | G |
| Ciclo di vita generale dei lavori (coda, priorità, annullamento) | aperto | G |
| Localizzazione dei messaggi d'errore del linguaggio | aperto: resta presentation concern | H |
| Ramo morto in `core/kronecker.py` dopo il `return` incondizionato | aperto | F |
| Rotte di export non ancora migrate ad `atomic_write` | aperto | G |
| Duplicazioni preservate come oracoli | **da non rimuovere** senza sostituto indipendente | G, E |

Nessun compartimento successivo è stato iniziato: F, G, H, I, J e K restano intatti.
