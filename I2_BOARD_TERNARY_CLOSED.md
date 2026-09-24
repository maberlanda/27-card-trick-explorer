# I2 — Tabellone, livello ternario e collegamenti fra viste: chiusura

Compartimento I2 della 4.0, implementato secondo `V4_PRE_I2_VIEW_DECISIONS.md`, con le decisioni D-I2-1…D-I2-8
approvate.

**Etichette di provenienza**:

| Etichetta | Significato |
|---|---|
| **FONTE** | libro o documenti autorevoli |
| **CODICE** | lettura del codice |
| **TEST** | test del repository |
| **ESEC** | esecuzioni fatte in questa sessione |
| **INFERENZA** | deduzione argomentata dalle voci precedenti |

## 1. Stato d'ingresso

ESEC:

| Voce | Valore |
|---|---|
| branch | `main` |
| HEAD | `370ee75 docs(v4): analyze pre-I2 board and ternary views` |
| `origin/main` | `54445af` |
| commit avanti | 73 |
| working tree tracciato | pulito |
| non tracciati | solo `Articolo.pdf` e `LIBRO_MAIN.pdf` |
| baseline matematica | 25 passed |
| ambiente | CPython 3.12.14, Tk 9.0.4 sotto xvfb |

## 2. Decisioni D-I2 applicate

| Decisione | Applicazione |
|---|---|
| D-I2-1 perimetro | solo tabellone, base 3 e collegamenti. Niente E1–E6, rovesciamento finale, prompt fisico, errore che accade o recupero |
| D-I2-2 collocazione | pannello ternario ridimensionabile (`ttk.Panedwindow`) a destra della Tavola, con tre schede interne «Tabellone», «Una carta», «27 posizioni». È visibile anche in Principiante; nessuna nuova scheda principale |
| D-I2-3 doppio ordine | striscia cronologica fase 1 → 2 → 3 e griglia con la fase 3 in alto; ogni riga porta «fase · ×peso · cifra» |
| D-I2-4 una sola autorità | `gioco_reale.parola` e `posizione_da_parola`; `detail.num_to_sector` delega con uscita identica, minuscola |
| D-I2-5 rovesciamenti | tre caselle ε per **una** `ProceduraGioco` (la riga selezionata); nessun elenco delle 8 procedure della classe |
| D-I2-6 testi | 63 chiavi nuove, solo nel catalogo `i18n.py`, simmetriche IT/EN; guida, glossario, `TAB_HELP` e onboarding non toccati |
| D-I2-7 navigazione | Tavola ↔ Explorer, Tavola ↔ Cicli, Simulatore → Tavola; nessun Tavola → Simulatore. La selezione non pubblica T: la pubblica solo «Usa come T corrente» |
| D-I2-8 passo-passo | inizio, passo indietro, passo avanti. **Autoplay omesso** (facoltativo): non aggiungeva informazione e avrebbe richiesto temporizzazioni nei test |

## 3. File modificati

**Nuovi**:

* `gioco27/services/tabellone.py`
* `gioco27/gui/pannello_ternario.py`
* `tests/test_tabellone_ternario_i2.py`
* `tests/test_tavola_ternaria_i2.py`
* `tests/test_navigazione_i2.py`
* `I2_BOARD_TERNARY_CLOSED.md`

**Modificati**:

| File | Modifica |
|---|---|
| `gioco27/core/gioco_reale.py` | `parola`, `posizione_da_parola` |
| `gioco27/core/detail.py` | `num_to_sector` delega; `_SECT` rimosso |
| `gioco27/services/procedure.py` | `parametri_gioco_reale` pubblico, alias del privato |
| `gioco27/gui/tavola_tab.py` | divisore, pannello, barra orizzontale della tabella, `vai_alla_riga`, azioni di navigazione |
| `gioco27/gui/app.py` | cablaggio: `_scheda_disponibile`, `_mostra_nella_tavola`, `_apri_nell_explorer`, `_apri_nei_cicli`, aggiornamento della navigazione in `_apply_livello` |
| `gioco27/gui/explorer_tab.py` | «Mostra nella Tavola» con il motivo |
| `gioco27/gui/cycles_tab.py` | «Mostra nella Tavola» con il motivo |
| `gioco27/gui/simulator_tab.py` | «Mostra la disposizione #n nella Tavola» |
| `gioco27/gui/scorrimento.py` | `AreaScorrevole.ricalcola()` |
| `gioco27/i18n.py` | 63 chiavi `ternary.*` e `nav.*` |
| `tests/test_i18n.py`, `tests/test_i18n_audit_finale.py`, `tests/test_i18n_anomalie_ui.py` | conteggio del catalogo 1325 → 1388 (+24 I2b, +30 I2c, +9 I2d) |
| `tests/test_layout_accessibilita_h2.py` | contratti H2 per I2 |
| `tests/test_procedure_i1_strategie.py` | guardia I1 aggiornata (§ 19) |

**Non toccati**:

* guida (`gui/guide.py`), glossario (`gui/glossary.py`, `TAB_HELP`), onboarding e livelli (`_advanced_tabs` invariato);
* `risolvi_trucco`, `procedura_storica`, `procedura_sicura`;
* formati ed export (CSV, PDF, HTML), `R[m]`;
* `pyproject.toml`, README, i PDF.

## 4. API del core introdotte

CODICE, `gioco27/core/gioco_reale.py`:

* `parola(n) -> str`: indirizzo `λ(n2)λ(n1)λ(n0)` con S = 0, C = 1, D = 2, costruito su `digits3`. Esempi: 0 → SSS,
  13 → CCC, 19 → DSC, 26 → DDD. La posizione è validata con `dominio.valida_indice`; booleani, float, stringhe e
  valori fuori da 0..26 danno `ValueError`.
* `posizione_da_parola(parola) -> int`: `ω⁻¹(abc) = 9ν(a) + 3ν(b) + ν(c)`; accetta solo tre lettere maiuscole fra
  S, C, D.
* `detail.num_to_sector(n)` è ora `parola(n).lower()`: uscita identica 27/27 e test di export verdi.

Nessun parser generico: il parser autorevole resta `core.algebra`.

## 5. Service / presenter introdotto

`gioco27/services/tabellone.py`:

* dati immutabili (`dataclass(frozen=True)`), nessun testo localizzato;
* nessun Tk, nessun I/O, nessuno stato globale;
* nessun motore nuovo.

| Oggetto / funzione | Contenuto |
|---|---|
| `tabellone(numero) -> Tabellone` | `cronologia` (fasi 1–3: mescolamento, impilamento); `righe` e `righe_inverse` (dall'alto: fase 3/peso 9/n2, fase 2/3/n1, fase 1/1/n0; `sigla`, `valori`); `colonne_assi` (carta 13·d → T[13·d]); `colonne_inverse` (posizione 13·d ← T⁻¹[13·d]); `destinazioni` (**T**); `mazzo_finale` (**T⁻¹**); `autoinversa`. Nessun campo «configurazione finale» |
| `lettura_cifre(numero, carta) -> LetturaCifre` | cifre e parola iniziali; tre `AzioneCifra` nell'ordine della griglia (fase, peso, cifra, riga visiva, sigla, cifra iniziale, cifra finale); cifre e parola finali; destinazione; `celle` da evidenziare |
| `tabella_posizioni(numero)` | 27 `LetturaCifre` in ordine 0..26 |
| `flussi_procedura(p)` e `flusso_carta(p, c) -> FlussoCarta` | per fase: ε, posizione e cifre prima, posizione distribuita dopo J^ε, colonna, altezza, destinazione `s_k`, posizione e cifre dopo, cifra che esce ed entra, `complementata` (parità del prefisso di ε), parole. `storia_distribuzioni`, `storia_raccolte`, `cifre_origine_nel_tempo` |
| `realizza(T)` | (R): l'unica procedura semplice di `classe_trasformazione(T)`; solleva `PermutazioneNonValida` e `TrasformazioneFuoriDominio` (dati, senza frasi) |
| `ritorno(numero)` | `realizza(T⁻¹)`, con T⁻¹ da `riga_tavola(n)["T_inv"]` |
| `numero_di(T)` | # oppure `None` se T è fuori dalle 216 |
| `disposizione_realizzata(p)` | la riga con la stessa T di una procedura con ε |
| `espressione_per_explorer(p)` | notazione tecnica per l'unico parser: `compute_T_perm(...)[1]` + `_prep_explorer_expr`, lo stesso percorso di Analisi e Decomposizioni |

**Autorità del flusso** (CODICE): la traccia di `esegui_partita` sui parametri di `adattamento_fisico` (oracolo
B di I1).

* Il mazzo distribuito allo stadio k è quello già capovolto.
* La posizione dopo la raccolta, prima di un ε successivo, viene da `gioco_reale.raccogli` senza rovesciamento.
* La ricorrenza `P' = ⌊P/3⌋ + 9·s` è **verificata** dai test contro questa traccia, non calcolata.

## 6. Struttura UI finale

```
Tavola 216
├── barra: filtro · ricostruzione dagli Assi · CSV            (invariati)
└── Panedwindow orizzontale (pesi 1:1, trascinabile)
    ├── tabella delle 216 righe (barre verticale e orizzontale)
    │   └── [Usa come T corrente] [Apri nell'Explorer]* [Apri nei Cicli]*  esito
    └── Pannello ternario (ttk.Notebook, ogni scheda in un'AreaScorrevole)
        ├── Tabellone      striscia cronologica · griglia diretta · griglia inversa ·
        │                  colonne-Assi · auto-inversa? · (R) · Ritorno [Vai alla riga #]
        │                  · «In testo» (Text di sola lettura)
        ├── Una carta      carta · ε1 ε2 ε3 · ⏮ ◀ ▶ · indirizzo · registro · passo ·
        │                  legge · distribuzioni · raccolte · lettura cifra per cifra ·
        │                  disposizione realizzata [Vai alla riga #] · «In testo»
        └── 27 posizioni   Treeview raggruppato n2 = 0/1/2 · dettaglio delle tre azioni
* solo se la scheda di destinazione è visibile nel livello corrente
```

Nessun Canvas nuovo. Le celle evidenziate portano «▶» oltre al colore.

## 7. Tabellone diretto e inverso

* Righe dall'alto: fase 3 (×9, n2), fase 2 (×3, n1), fase 1 (×1, n0).
* La striscia cronologica, sopra, mostra fase 1 → 2 → 3 con mescolamento e impilamento.
* Le due letture sono sempre nominate:
  * «Destinazione di ogni carta (T)»;
  * «Carta in ogni posizione / mazzo finale (T⁻¹)».
* Il tabellone inverso ha lo stesso ordine delle fasi e le sigle inverse (CDS ↔ DSC).
* La vista dichiara se T è auto-inversa (64 righe su 216) e quindi se le due letture coincidono.

## 8. Convertitore

* La scheda «Una carta» mostra «Posizione n = (n2,n1,n0) · indirizzo XYZ». La parola ha sempre il ruolo di
  **indirizzo**.
* Le sigle dei mescolamenti hanno sempre il ruolo di **mescolamento**, per esempio «il mescolamento CDS manda la
  colonna C nel blocco 2».
* La tabella a 27 righe mostra terna e parola, iniziali e finali.

## 9. Macchina che dimentica

* Registro a tre cifre, con i pesi ×9 ×3 ×1, a ogni passo 0..3.
* Il dettaglio del passo riporta:
  * la posizione distribuita;
  * la colonna (con nome S/C/D) e l'altezza;
  * il mescolamento e il blocco `s`;
  * `P′ = altezza + 9·s`;
  * la cifra che esce e quella che entra.
* La legge `P′ = ⌊P/3⌋ + 9·s` è scritta sotto.
* Il log testuale contiene **tutti** i passi, qualunque sia il passo mostrato.

## 10. Legge con ε

* Con ε = 1 il passo mostra prima il capovolgimento: `P = (b2,b1,b0) → 26 − P = (2−b2, 2−b1, 2−b0)`.
* La storia delle distribuzioni:
  * senza rovesciamenti dichiara `= rev ω(n)`;
  * con rovesciamenti elenca le fasi in cui la cifra osservata è complementata (parità dispari del prefisso) e
    scrive che «è la legge, non un errore».
* La disposizione con la stessa T viene mostrata con (R): per esempio (SCD, DCS, SCD; 0,0,1) → #185.

## 11. Tabella delle 27 posizioni

* `Treeview` con tre gruppi testuali «n2 = d (lettera): posizioni 9d–9d+8» e colonne n, terna, indirizzo, terna
  finale, indirizzo finale, n′.
* Selezionare una riga:
  * sincronizza la carta della scheda «Una carta»;
  * evidenzia le tre celle della griglia;
  * mostra le tre azioni locali.

## 12. (R)

`realizza(T)` = unica procedura semplice della classe di T. Non usa `risolvi_trucco`, `procedura_storica` o
`procedura_sicura`: il test lo verifica sostituendole con funzioni che falliscono. Serve per:

* Explorer → Tavola;
* Cicli → Tavola;
* le procedure con ε.

## 13. Ritorno

`ritorno(n) = realizza(T⁻¹)`. La vista scrive «stesso ordine delle fasi, sigle inverse (CDS ↔ DSC)» e offre «Vai
alla riga #…». Ritorni dei casi del libro:

| Riga | Ritorno |
|---|---|
| #100 | #93 |
| #56 | #62 |
| #177 | #142 |
| #78, #193, #0 | sé stesse |

## 14. Navigazione

| Da → a | Azione | Condizione |
|---|---|---|
| Tavola → (Cicli, Presentazione, Protocollo) | «Usa come T corrente» → `_notify_T_changed` | solo esplicita; la selezione non pubblica |
| Tavola → Cicli | «Apri nei Cicli»: pubblica e mostra | solo se la scheda Cicli è visibile |
| Tavola → Explorer | «Apri nell'Explorer»: espressione di `espressione_per_explorer`, calcolo | solo se l'Explorer è visibile |
| Explorer → Tavola | «Mostra nella Tavola» via `numero_di(T)` | disabilitata con il motivo se T è fuori dalle 216 |
| Cicli → Tavola | «Mostra nella Tavola» via `numero_di(T)` | idem |
| Simulatore → Tavola | «Mostra la disposizione #n nella Tavola» | dopo il calcolo della sequenza |

Non c'è nessun collegamento Tavola → Simulatore. In Principiante le azioni verso Explorer e Cicli non compaiono.
La semantica di `_advanced_tabs` e dei livelli non cambia.

## 15. i18n

* 63 chiavi nuove: 24 in I2b, 30 in I2c, 9 in I2d. Il catalogo passa da 1325 a 1388 chiavi, simmetriche e con
  gli stessi segnaposto.
* Nessun termine narrativo (Seldon, Giullare, Gaia, Cronaca) e nessun nome G/H/Γ/G_ext nelle chiavi nuove
  (verificato con grep sul diff).
* Nessun testo per l'utente nel service.

## 16. H2 e layout

**Contratti nuovi** (TEST, `test_layout_accessibilita_h2.py`):

* la Tavola entra in `test_m04_il_contenuto_delle_schede_e_raggiungibile`;
* pannello raggiungibile nelle tre schede × tre geometrie (1280×720, 1366×768, 1920×1080);
* la Tavola non scorre in orizzontale;
* nessuna barra orizzontale nelle schede del pannello; barre verticali solo quando servono;
* divisore trascinabile senza cicli;
* ordine di Tab della scheda «Una carta» coerente con l'ordine visivo;
* alternative testuali presenti, di sola lettura, raggiungibili;
* «▶» oltre al colore;
* il layout della Tavola regge anche nel test della lingua inglese.

**Misure** (ESEC, applicazione vera):

| Geometria | Tabella / pannello (px) |
|---|---|
| 1280×720 | 670 / 549 |
| 1366×768 | 713 / 592 |
| 1920×1080 | 990 / 869 |

Nessun controllo perso.

**Accorgimenti**:

* la tabella non impone più i suoi 876 px di colonne e scorre con la sua barra orizzontale;
* le schede del pannello hanno una richiesta minima contenuta;
* `AreaScorrevole.ricalcola()` rivaluta le barre quando il contenuto si restringe: Tk non emette `<Configure>` in
  quel caso.

**Nota** (TEST, INFERENZA): `test_il_layout_regge_anche_in_inglese` crea l'App dopo `set_language("en")`, ma l'App
riapplica la lingua della configurazione (`app.py`, riga 110). Il test misura quindi la lingua configurata, non
necessariamente l'inglese. Le asserzioni I2 aggiunte lì usano `catalogo.tr(...)`. La vista inglese del pannello è
provata direttamente in `test_tavola_ternaria_i2.py::test_in_inglese_il_pannello_parla_inglese`. Il difetto del
test H2 preesistente è registrato come debito (§ 23).

## 17. Verifiche V1–V11

TEST permanenti, con oracoli indipendenti: aritmetica, formula del libro, simulazione fisica, inversa per
ricerca. Sono provate sia sul core sia tramite il presenter.

| # | Verifica | Esito |
|---|---|---|
| V1 | n ↔ `digits3` ↔ n | 27/27 |
| V2 | n ↔ parola ↔ n; 19 ↔ (2,0,1) ↔ DSC | 27/27 |
| V3 | lettura gerarchica = T | 216/216 |
| V4 | colonne = T[0], T[13], T[26] (e colonne inverse = T⁻¹[0,13,26]) | 216/216 (+216) |
| V5 | legge cifra per cifra = T[n] | 5832/5832 |
| V6 | tabellone inverso = T⁻¹ = mazzo fisico | 216/216 |
| V7 | (R) via I1 | 216/216 |
| V8 | ritorno realizza T⁻¹; composizioni = id; mescolamenti = impilamenti | 216/216 |
| V8b | scorciatoie sbagliate | 24/216 e 36/216 (contro 216/216 per la regola giusta) |
| V9 | rev ω(n) con ε = 0 | 5832/5832 |
| V10 | ricorrenza e registro | 5832/5832 + 5832/5832 |
| V11 | finali, intermedi, colonne | 46656/46656; 46656/46656; 139968/139968 |
| V11b | complementazione per parità del prefisso | 46656/46656 |
| V11b | Prop. 1.6 letterale con ε | 13824/46656: un fatto della legge, non un fallimento |

## 18. F1–F13

Tutti verdi (TEST):

| Caso | Contenuto |
|---|---|
| F1 | 19 = (2,0,1) = DSC |
| F2 | SCD = 5, DSC = 19, CDS = 15 |
| F3 | #78, Assi 9, 7, 23, auto-inversa |
| F4 | #56 ↔ #62; mazzo di #56 «4 3 5 7 6 8 1 0 2 …» |
| F5 | #193, tabella a 27 righe, 1 → 23 |
| F6 | #177 ↔ #142, 10 → 24 → 10 |
| F7 | #100, 10 → 5, T⁻¹(10) = 6, ritorno #93 |
| F8 | #100 carta 19: registro (2,0,1) → (2,2,0) → (1,2,2) → (2,1,2) = 23; colonne 1, 0, 2 |
| F9 | #91: 0 → 15, 1 → 17, 2 → 16 |
| F10 | § 2.5 con ε = (0,0,1): Assi 20, 13, 6 = #185 |
| F11 | (CSD)³: ε = (1,0,0) → (26,0,13); ε = (0,1,0) → (25,2,12) |
| F12 | #82, Assi (10, 8, 21) |
| F13 | #0 identità |

**Nessun conflitto** fra fonte, core e memo.

## 19. Compatibilità

| Oggetto | Stato |
|---|---|
| `risolvi_trucco`, `procedura_storica`, `procedura_sicura` | invariati; nessuna vista usa le strategie |
| Tavola 216, `numero_tavola`, `T_da_tabellone`, `tabellone_da_assi` | invariati |
| dettaglio della Tavola (doppio clic), CSV | invariati |
| PDF, HTML, export | invariati; `num_to_sector` produce la stessa uscita |
| Presentazione e Protocollo | ricevono T solo dalle vie già esistenti e da «Usa come T corrente» |
| Pratica e Simulatore | invariati, salvo il pulsante verso la Tavola |

**Guardia di I1 aggiornata** (TEST, deliberato):

* prima diceva «nessuna vista usa il servizio delle procedure», che valeva finché nessuna vista era prevista;
* ora vieta nelle viste le **strategie** (storica e sicura) e limita l'uso del **modello** `ProceduraGioco` ai
  consumatori approvati in I2 (`pannello_ternario.py`, `tavola_tab.py`).

## 20. Invarianti architetturali

ESEC (analisi AST inline) e TEST (`test_servizi_g1.py` 44 passed, `test_static.py` 2 passed):

| Invariante | Valore |
|---|---|
| core → services | 0 |
| core → gui | 0 |
| services → gui | 0 |
| services → tkinter | 0 |
| cicli d'importazione | 0 |
| parser autorevoli | 1 (`core.algebra.Parser`) |
| worker che toccano Tk | nessuno nuovo |

`services.tabellone` dipende solo da `core` e da `services.procedure`.

## 21. Suite

Stesso metodo dell'audit: un file per volta sotto xvfb, perché l'esecuzione unica va in crash con Tk 9.

| Insieme | Esito |
|---|---|
| test I2 | 48 + 22 + 12 + 15 H2 nuovi = **97** passed |
| baseline matematica | 25/25 |
| test I1 | 18 + 41 + 19 passed |
| suite completa, 44 file, 1604 test | **1602 passed, 1 skipped, 1 failed** |

* **Skipped**: `test_layout_dettaglio.py`, manca `pypdfium2` (come in audit e I1).
* **Failed**: `test_layout_accessibilita_h2.py::test_lo_scorrimento_si_accende_quando_il_testo_cresce`, il noto
  fallimento ambientale Tk 9. È l'unico e non è stato modificato.
* **Rispetto a I1**: 1507 test + 97 nuovi = 1604. Nessuna nuova regressione.

## 22. Gate

| # | Gate | Esito |
|---|---|---|
| G1 | D-I2-1…8 applicate | ✔ § 2 |
| G2 | I2/I3 separati | ✔ |
| G3 | DP3 = A preservata | ✔ |
| G4 | nessun secondo modello del rovesciamento | ✔ (solo `adattamento_fisico` come oracolo) |
| G5 | una sola autorità numero/cifre/parola | ✔ (TEST anti-duplicazione) |
| G6 | `num_to_sector` invariato 27/27 | ✔ |
| G7–G22 | V1–V11b | ✔ § 17 |
| G23 | F1–F13 | ✔ |
| G24 | T e mazzo finale T⁻¹ distinti nella UI | ✔ |
| G25 | cronologia e ordine del tabellone espliciti | ✔ |
| G26 | (R) senza nuovo solutore | ✔ |
| G27 | ritorno = T⁻¹, stessa cronologia, sigle inverse | ✔ |
| G28 | `procedura_sicura` non usata dalle viste | ✔ |
| G29 | `risolvi_trucco` invariato | ✔ |
| G30 | nessuna Tavola 1728 | ✔ |
| G31 | pannello visibile in Principiante, DP7 non decisa | ✔ |
| G32 | azioni Explorer/Cicli condizionate al livello | ✔ |
| G33 | la selezione non pubblica T | ✔ |
| G34 | «Usa come T corrente» pubblica | ✔ |
| G35 | Tavola ↔ Explorer | ✔ |
| G36 | Tavola ↔ Cicli | ✔ |
| G37 | Simulatore → Tavola (0 → 13 → #86) | ✔ |
| G38 | nessun Tavola → Simulatore | ✔ |
| G39 | i18n IT/EN simmetrico | ✔ |
| G40 | guida, `TAB_HELP`, onboarding non modificati | ✔ |
| G41–G43 | H2 per tabellone, flusso, 27 posizioni | ✔ |
| G44 | focus e tastiera | ✔ |
| G45 | niente solo colore | ✔ |
| G46–G48 | 1280×720, 1366×768, 1920×1080 | ✔ |
| G49 | inglese | ✔ (con la nota del § 16) |
| G50 | nessun Canvas nuovo | ✔ |
| G51 | architettura a zero | ✔ |
| G52 | baseline 25/25 | ✔ |
| G53 | test I1 verdi | ✔ |
| G54 | formati ed export senza regressione | ✔ |
| G55 | unico fallimento = Tk 9 noto | ✔ |
| G56 | nessuna nuova regressione | ✔ |
| G57 | I3 non iniziato | ✔ |
| G58 | DP aperte non risolte | ✔ |
| G59 | PDF non tracciati | ✔ |
| G60 | nessun accesso fuori dal repository | ✔ |
| G61 | nessun push | ✔ |
| G62 | autoplay omesso, passo-passo sempre disponibile | ✔ |
| G63 | guardia I1 evoluta in modo dichiarato, senza allentare DP5 | ✔ |

## 23. Debiti

**I3**:

* rovesciamento finale (J∘T) come E2 alla fase 3;
* prompt fisico del rovesciamento nel Simulatore e nella Pratica;
* errori E1–E6 e recupero;
* un Simulatore guidato da una disposizione fissata (l'eventuale Tavola → Simulatore).

**I7**:

* guida e glossario per il pannello ternario e i nuovi pulsanti;
* allineamento del dettaglio della Tavola (doppio clic), che scrive ancora «dal basso verso l'alto: riga 1 …»;
* etichette definitive in funzione di DP2 e DP8.

**H2/J**:

* `test_il_layout_regge_anche_in_inglese` dipende dalla lingua della configurazione (§ 16);
* il fallimento ambientale Tk 9 resta da riesaminare nell'ambiente di riferimento.

**Documentazione**: la divergenza R[m] / R[k] dell'App. C resta da documentare nel compartimento appropriato.

**Aperte**: DP1, DP2, DP6–DP12 invariate.

## 24. Commit

| Commit | Messaggio |
|---|---|
| `8537a41` | `test(I2): characterize ternary board and flow contracts` |
| `f909d5b` | `feat(I2): add canonical ternary presenter and word conversion` |
| `6feab1d` | `feat(I2): add ternary board panel to table` |
| `1ee6a40` | `feat(I2): add card flow and 27-position views` |
| `6ae8ee8` | `feat(I2): connect table explorer cycles and simulator` |
| `f5bd9d8` | `test(I2): enforce accessibility layout and navigation contracts` |
| `9690daf` | `test(I2): let approved board views use the procedure model` |
| (questo) | `docs(I2): close board and ternary views compartment` |

## 25. Stato Git

Prima del commit di chiusura:

```
## main...origin/main [ahead 80]
?? Articolo.pdf
?? LIBRO_MAIN.pdf
```

Dopo il commit di chiusura sono 81 commit avanti, con gli stessi due PDF non tracciati. Nessun push.
