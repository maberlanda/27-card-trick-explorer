# H2 — Layout adattivo, tastiera e accessibilità

Secondo e ultimo blocco del compartimento H.

## 1. Identità

| | |
|---|---|
| Branch | `main` |
| HEAD iniziale | `e866266` — *docs(H1): record presentation correctness milestone* |
| HEAD finale | il commit di questo documento — *docs(H2): close the accessibility and layout compartment*, nono e ultimo di H2 |
| `origin/main` | `54445af`, invariato — **nessun push** |
| Commit locali di H2 | 9 |
| Versione | 3.1.3 (invariata) |

## 2. Nota di perimetro

Tutto il lavoro è avvenuto **dentro il repository corrente**: nessun worktree, checkout, clone,
copia o script di lavoro esterno; nessuna directory padre o sorella consultata; nessun file di
appoggio fuori dal repository; nessuna vecchia copia del progetto aperta. I controlli occasionali
sono stati comandi Python inline, e ciò che meritava di restare è diventato un test dentro
`tests/`. Gli unici accessi esterni sono le directory temporanee di pytest e i display X di
collaudo (Xvfb), che non toccano il filesystem del progetto.

## 3. Ambiente di riferimento

```text
Linux · Python 3.12.3 · tkinter 8.6 · Xvfb (1920x1080x24)
NumPy 2.5.3 · ReportLab 5.0.1 · openpyxl 3.1.5 · pypdf 6.18.1 · pikepdf 10.13.0
pytest 9.1.1 · pyflakes 3.4.0

PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m pytest -p no:cacheprovider -ra -q
```

Il collaudo grafico richiede un display: senza, i test di layout si saltano da soli invece di
fallire (`_display_o_salta`).

## 4. Audit d'ingresso — M04, misurato

Il primo commit di H2 non ha corretto nulla: ha misurato l'applicazione vera, sotto un display,
alle tre dimensioni di collaudo.

```text
minsize dichiarata                       1200 × 750
dimensione richiesta dalla finestra      2000 × 1208
la finestra non può essere alta 720      (minsize la rialza a 750)

a 1280 × 720   5 pulsanti della barra azioni spariscono del tutto
               (Verifica, Presentazione, Protocollo, Cayley, Coniugio)
a 1366 × 768   4 pulsanti spariscono
Simulatore     perde «Conferma impilamento» e «Ricomincia» — le azioni primarie
Explorer       28 controlli sotto il bordo, senza modo di arrivarci
```

Non erano tagliati a metà né raggiungibili scorrendo: `pack` li lasciava semplicemente fuori.
A questo si aggiungevano tre difetti indipendenti dalla dimensione: il banner d'aiuto presente su
ogni scheda si usava **solo col mouse**, i dialoghi non davano il focus a nulla all'apertura, e i
Canvas che portano informazione non avevano alternativa testuale nella loro vista.

Il collaudo finale ha trovato un quarto difetto, non visibile dalla sola geometria: i cinque menu
a tendina del programma — «Genera…», l'export dell'analisi, Cayley, coniugio, decomposizione —
sono `tk.Menubutton`, che nasce con `takefocus 0`; erano sullo schermo a ogni dimensione ma Tab
non li raggiungeva. È stato marcato `xfail(strict=True)` e corretto nel commit successivo.

## 5. Le barre vanno a capo

`gioco27/gui/barra.py` — **nuovo**, 186 righe. `BarraAdattiva` è un `ttk.Frame` che dispone le
proprie voci su una o più righe a seconda della larghezza disponibile:

* `aggiungi(widget, padx, a_destra, elastico)`, `separatore()`, `elastico()`;
* `_righe(larghezza)` impacchetta in ordine: nessun widget viene mai omesso, cambia solo il numero
  di righe;
* il widget elastico (la riga di stato) riceve `sticky="ew"` e `columnconfigure(weight=1,
  minsize=40)`; i separatori `sticky="ns"`; gli altri `"w"`;
* su una riga sola viene inserita una colonna elastica prima del gruppo `a_destra`, così il
  gruppo resta a destra finché tutto ci sta.

Il ciclo `configure → geometry → configure` è evitato alla radice: `_su_configure` calcola una
**firma** della disposizione e, se non è cambiata, esce senza toccare un solo widget. Quattro
ridimensionamenti producono cinque eventi `<Configure>` sulla barra azioni; il test ne ammette al
massimo otto.

Il contenuto della barra azioni misura circa 1994 px: due righe fino a 1920, una sola da 2100 in su.
Il separatore in coda (42 px, nessuna informazione) è stato tolto.

## 6. Le schede scorrono, e la finestra si rimpicciolisce

`gioco27/gui/scorrimento.py` — **nuovo**, 187 righe. `AreaScorrevole` avvolge il contenuto di una
scheda in una tela con barre di scorrimento che **compaiono solo quando servono**:

* la finestra della tela è grande `max(contenuto, tela)` in entrambe le direzioni, così i pesi di
  `grid`/`pack` interni continuano a espandere quando c'è spazio;
* `_mostra_barre` commuta solo quando il bisogno cambia davvero, con una tolleranza di 2 px e una
  guardia di rientranza;
* tastiera sulla tela e su entrambe le barre: `↑ ↓ PagSu PagGiù Inizio Fine ← →`, tutte con
  `"break"`;
* la rotellina è associata con `bind_all` solo tra `<Enter>` e `<Leave>`/`<Destroy>`, così non
  ruba lo scorrimento ad altri widget.

Dieci schede su dodici sono avvolte (la tavola non ne ha bisogno; il banner d'aiuto resta fisso
sopra l'area). Con l'overflow gestito, `minsize` scende da **1200 × 750 a 900 × 560**: non è un
numero abbassato per far passare il test, è la conseguenza del fatto che nulla si perde più.

## 7. Tastiera

* `common.rendi_azionabile(etichetta, comando)` — i collegamenti del banner d'aiuto restano
  `Label` per ragioni grafiche ma entrano nel giro di Tab, si attivano con Invio o Spazio e
  mostrano il focus con un bordo colorato;
* `common.rendi_menu_apribile(menubutton)` — i cinque menu a tendina prendono `takefocus` e si
  aprono con Invio, Spazio o Giù (`tk::MbPost` + `tk::MenuFirstEntry`, gli stessi del clic);
  dentro il menu valgono i tasti di Tk. Uno stato `disabled` non si scavalca;
* `common.prepara_dialogo(dialogo, primo)` — Esc chiude, e il dialogo **dichiara** il proprio
  focus iniziale in `_focus_iniziale` invece di lasciarlo al caso. Cinque dialoghi: Cayley
  (`_combo_a`), coniugio (`_cls_tree`), decomposizione (`_tree`), protocollo (`_prima_opzione`),
  impostazioni (lo spinbox dei worker, primo controllo modificabile);
* i suggerimenti compaiono anche col focus (`<FocusIn>`), e in quel caso il riquadro si posiziona
  accanto al widget invece che accanto al puntatore, che potrebbe essere altrove. Vale per tutti i
  tredici punti di innesto, perché la classe `Tooltip` è una sola.

## 8. Canvas: informativi contro decorativi

Quattro Canvas nel programma, censiti nel test:

| File | Ruolo |
|---|---|
| `scorrimento.py` | struttura — la tela di `AreaScorrevole` |
| `onboarding_tab.py` | struttura — la tela che fa scorrere la scheda |
| `distribution_tab.py` | **informativo** — l'istogramma delle decomposizioni |
| `explorer_tab.py` | **informativo** — le matrici 27×27 e i fattori 3×3 |

I due informativi hanno ora un'alternativa testuale **nella propria vista**, non in un tooltip:

* `ExplorerTabMixin._matrice_in_testo(perm27, fattori)` riempie un `tk.Text` di tre righe, in sola
  lettura ma raggiungibile con Tab, sotto ciascun pannello;
* `DistributionFrame.istogramma_in_testo(r)` scrive totale, estremi e picco sotto l'istogramma e
  rimanda alla scheda «Tabella dati» per l'elenco riga per riga.

## 9. Il riscontro di un salvataggio resta nel dialogo

Debito dichiarato da H1 (§ 21 di `H1_PRESENTATION_I18N_CLOSED.md`). G2 aveva reso *visibile* il
fallimento di `Config.save()` e H1 ne aveva scritto il testo; il flusso restava quello di una
messagebox sopra il dialogo — sposta il fuoco, chiede un clic per essere chiusa, e si ripresenta a
ogni tentativo: tre finestre per un errore che non ha cambiato niente.

Ora nel dialogo impostazioni compare un'etichetta sopra i pulsanti, il fuoco torna su «Salva» — il
controllo con cui si riprova — e il dialogo **non si chiude**. Tre tentativi falliti producono un
avviso, non tre finestre. Anche il riscontro del cambio di lingua («riavvia per applicare») resta
in linea: `_save_language_preference` accetta un `avviso` opzionale e, senza, si comporta
esattamente come in G2 — la messagebox non è stata rimossa, è il ripiego di chi non ha dove
scrivere in linea.

Il contratto strutturale di G2 è intatto: un solo blocco protetto attorno a `save()`, `destroy`
fuori dal tentativo, il fallimento interrompe il flusso.

## 10. Errori del sistema operativo: una cornice sola

Secondo debito di H1: otto moduli mostravano ancora `str(exc)` nudo.

`errori.per_file(exc, percorso, titolo=None)` aggiunge nella lingua dell'utente il nome del file e
che cosa si stava tentando, e lascia **intatto** il messaggio del sistema, che è l'unica cosa che
dice davvero che cosa è andato storto. Con `percorso` vuoto — export multiplo, export in cartella,
pulizia della cache — resta la cornice generica invece di nominare un file a caso; `titolo`
conserva il titolo localizzato delle rotte che ne hanno già uno («Errore di esportazione»).

Quindici rotte incorniciate: `analysis_tab` 5, `decomposition` 3, `cayley_dialog` 2,
`conjugacy_dialog` 2, `export_dialog` 1, `export_group_dialog` 1, `app` 1 (cache). **Nessun
`showerror` della GUI mostra più `str(exc)`.** Il censimento di H1 si riduce a `shuffle.py`, dove
il testo arriva già localizzato dal core (compartimento E).

## 11. M01: la nota dei filtri esce dal tooltip

Terzo debito di H1. La regola «ogni livello resta con almeno un valore» viveva in un tooltip,
cioè solo per chi usa il mouse e solo se ci passava sopra. Ora è testo persistente sotto
l'introduzione del pannello filtri, in entrambe le lingue. Il `wraplength` non è più un numero
fisso: `_adatta_testi` lo ricalcola sulla larghezza disponibile, con un massimo di 1100 px — senza
quel tetto il pannello chiedeva 2384 px in un ciclo etichetta → contenuto → tela → etichetta.

## 12. Collaudo alle tre dimensioni e alle tre scale

**Dimensioni.** A 1280 × 720, 1366 × 768 e 1920 × 1080 la finestra prende esattamente la geometria
chiesta, le dodici azioni essenziali sono tutte sullo schermo, e su **tutte e dodici le schede**
nessun controllo collocato con genitore visibile resta fuori portata.

**Scale.** `tk scaling` viene dai DPI dello schermo e **non si cambia a programma avviato**: Tk
risolve la dimensione dei font quando li crea, e riscalare dopo non li ridisegna — verificato,
cambiare la scala e riapplicare gli stili non muove di un pixel la barra. Il collaudo alle tre
scale si fa quindi con un processo per scala, sotto un display ai DPI voluti:

```text
dpi  72  → tk scaling 1.000   richiesta 1231 × 763
   1280×720  righe barra 2/1   pulsanti persi 0   controlli persi 0
   1366×768  righe barra 2/1   pulsanti persi 0   controlli persi 0
   1920×1080 righe barra 1/1   pulsanti persi 0   controlli persi 0
dpi 108  → tk scaling 1.499   richiesta 1495 × 941
   1280×720  righe barra 2/1   pulsanti persi 0   controlli persi 0
   1366×768  righe barra 2/1   pulsanti persi 0   controlli persi 0
   1920×1080 righe barra 2/1   pulsanti persi 0   controlli persi 0
dpi 144  → tk scaling 1.998   richiesta 1866 × 1187
   1280×720  righe barra 3/1   pulsanti persi 0   controlli persi 0
   1366×768  righe barra 2/1   pulsanti persi 0   controlli persi 0
   1920×1080 righe barra 2/1   pulsanti persi 0   controlli persi 0
```

La dimensione richiesta cresce da 1231 × 763 a 1866 × 1187, ben oltre i 1280 × 720, e la finestra
accetta comunque quella geometria: è lo scorrimento ad assorbire l'eccesso.

**Limiti dichiarati.** La misura è su Linux/X11 con Xvfb. Non riproduce il DPI per-monitor di
Windows né il cambio di scala a finestra aperta; un processo per scala è l'unico modo di misurarla
in Tk. Dentro la suite si collauda la scala che il programma possiede davvero — «Dimensione testo
aiuti», 1.0 / 1.6 / 2.0 — che riconfigura i font con nome e fa crescere il contenuto: lo stadio 0
passa da 454 a 780 px di altezza richiesta e l'area di scorrimento si accende, stessa scheda,
stessa area.

**Un test sorveglia che nessuno fissi `tk scaling` nel programma**: la scala di sistema è
dell'utente, e sovrascriverla lascerebbe il testo minuscolo su un monitor ad alta densità.

## 13. Tastiera, dal vivo

Il percorso di collaudo non invoca callback: mette il fuoco sul pulsante «Gioco Reale» e manda la
pressione dello spazio, poi misura l'effetto — 1 728 combinazioni nel contatore e la riga di stato
del preset. Tab attraversa la barra azioni nell'ordine in cui la si vede. La tendina «Genera…» si
apre con Invio e si richiude (un menu aperto tiene un grab).

Nota di metodo: senza window manager nessuno assegna il fuoco d'ingresso di X alla finestra, e un
dialogo chiuso poco prima lo lascia a un toplevel che non esiste più; Tk scarta allora i tasti. I
test usano `focus_force()` prima di mandare un tasto e `focus_lastfor()` — il fuoco *dentro* il
toplevel — per le asserzioni. Su un desktop vero il problema non esiste.

## 14. Il colore non porta da solo

L'elenco dei posti dove in questo programma il colore porta significato, ciascuno con la sua
controparte testuale, verificata dai test:

| Dove | Controparte testuale |
|---|---|
| contatore e riga di stato | testo, non colore |
| istogramma delle decomposizioni | `istogramma_in_testo` sotto il grafico |
| matrici dell'Explorer | `_matrice_in_testo` in ciascun pannello |
| righe scartate dell'analisi | il motivo scritto (`errori.motivo_di` via `diagnostica_import`) |
| avviso delle impostazioni | il testo; il colore è in aggiunta |

**Non si dichiara conformità WCAG.** Quelle sopra sono le proprietà provate, nient'altro.

## 15. IT / EN

Il catalogo passa da 1316 a **1325 chiavi** (+9 in H2: nota dei filtri, alternative testuali ai
Canvas, cornice degli errori su file), simmetrico fra le due lingue, senza segnaposti discordi.

La vista inglese è collaudata costruendo una **seconda applicazione in inglese** — la lingua si
sceglie all'avvio — e ridimensionandola alle tre geometrie: le etichette inglesi sono larghe in
modo diverso, la barra va a capo senza perdere pulsanti e le dodici azioni essenziali ci sono
tutte.

Scelta redazionale dichiarata: i testi inglesi introdotti da H2 usano le virgolette basse `«»`
come le altre cinque frasi inglesi già presenti nel catalogo (da E e H1). Uniformarle alla
convenzione inglese significherebbe riscrivere testi di altri compartimenti, e resta un debito.

## 16. Metriche prima / dopo

| | Prima di H2 | Dopo H2 |
|---|---|---|
| `minsize` | 1200 × 750 | **900 × 560** |
| dimensione richiesta | 2000 × 1208 | 1406 × 909 |
| pulsanti persi a 1280 × 720 | 5 | **0** |
| pulsanti persi a 1366 × 768 | 4 | **0** |
| controlli fuori portata (12 schede, 3 geometrie) | 28 nel solo Explorer | **0** |
| comandi raggiungibili solo col mouse | 7 (5 menu a tendina, 2 collegamenti del banner) | **0** |
| suggerimenti raggiungibili solo col mouse | tutti (13 innesti) | **0** |
| Canvas informativi senza alternativa testuale | 2 su 2 | **0** |
| schede avvolte in un'area scorrevole | 0 (le altre due avevano già la propria strategia) | **10 su 12** |
| dialoghi senza focus iniziale dichiarato | 5 su 5 | **0** |
| rotte che mostrano un OSError nudo | 15 | **0** |
| navigazione per titolo tradotto | 0 — chiavi stabili `_schede`, fatto in H1 | invariato, verificato qui |
| chiavi di catalogo | 1316 | 1325 |

## 17. Test

```text
tests/test_layout_accessibilita_h2.py     66 test, 1217 righe   (nuovo in H2)
tests/test_presentation_i18n_h1.py        65 test               (censimento aggiornato)
tests/test_guida_allineata.py             27 test               (estrattore AST esteso)
tests/test_i18n*.py                      149 test               (conteggi 1325)

suite completa   1429 raccolti
                 1428 passati
                    1 saltato   (N03 — pypdfium2 assente)
                    0 falliti   nessun xfail residuo
                  122 s
```

Tecnica rosso-primo rispettata: il difetto dei menu a tendina è entrato come `xfail(strict=True)`
nel commit di collaudo ed è stato promosso a contratto verde dal commit che lo corregge. Il flusso
del dialogo impostazioni è stato verificato per mutazione: ripristinando la messagebox, tre dei
nuovi test cadono.

## 18. Sweep di non-regressione

```text
B01–B12, R01/R04/R05/R07, M01/M03/M05/M06
  test_io_integrita_b, test_stato_concorrenza_c, test_rischi_concorrenza,
  test_hardening, test_export_integrita, test_baseline_matematica,
  test_output_integrita, test_annullamento, test_parallel_limiti   287 passati

per compartimento
  D (dominio) · E (espressioni) · F (analisi) · G1 (servizi) ·
  G2 (lifecycle) · H1 (presentation) · H2 (layout)               634 passati
```

Matematica invariata: `test_baseline_matematica` 25/25. Gli invarianti di G reggono — core e
services non importano `gioco27.gui`, nessun ciclo `combinations ↔ permutations`, nessuno
scheduler inventato.

## 19. File modificati

```text
 gioco27/gui/analysis_tab.py           |   15 +-
 gioco27/gui/app.py                    |  282 ++++----
 gioco27/gui/barra.py                  |  186 +++++   (nuovo)
 gioco27/gui/cayley_dialog.py          |    9 +-
 gioco27/gui/common.py                 |   77 +++
 gioco27/gui/conjugacy_dialog.py       |    9 +-
 gioco27/gui/decomposition.py          |   11 +-
 gioco27/gui/distribution_tab.py       |   35 +-
 gioco27/gui/errori.py                 |   29 +-
 gioco27/gui/explorer_tab.py           |   58 +-
 gioco27/gui/export_dialog.py          |    5 +-
 gioco27/gui/export_group_dialog.py    |    5 +-
 gioco27/gui/filter_frame.py           |   44 +-
 gioco27/gui/help_banner.py            |    9 +-
 gioco27/gui/protocol_dialog.py        |   10 +-
 gioco27/gui/scorrimento.py            |  187 +++++   (nuovo)
 gioco27/gui/tooltip.py                |   34 +-
 gioco27/i18n.py                       |   26 +
 tests/test_guida_allineata.py         |   39 +-
 tests/test_i18n.py                    |    6 +-
 tests/test_i18n_anomalie_ui.py        |    2 +-
 tests/test_i18n_audit_finale.py       |    2 +-
 tests/test_layout_accessibilita_h2.py | 1217 +++++++++++++++++++++   (nuovo)
 tests/test_presentation_i18n_h1.py    |   33 +-
 24 file, 2156 inserzioni, 174 rimozioni
```

(`git diff --stat e866266..HEAD`, prima del commit di questo documento.)

Nessun file del core o dei servizi è stato toccato da H2.

## 20. Commit locali

| | |
|---|---|
| `0ba3842` | test(H2): characterize layout and keyboard accessibility |
| `2cea87e` | refactor(H2): make the action bars wrap instead of dropping controls |
| `062e6b8` | refactor(H2): give tab contents a scrolling strategy and lower the minimum size |
| `64fa7a8` | fix(H2): make essential actions keyboard reachable |
| `b2e378c` | fix(H2): provide textual alternatives for the informative canvases |
| `ae50f60` | fix(H2): keep save failures inside the settings dialog and frame file errors |
| `85709ee` | test(H2): exercise resize, scaling and keyboard paths |
| `25490fb` | fix(H2): open the drop-down menus from the keyboard |
| *questo* | docs(H2): close the accessibility and layout compartment |

`main` è 66 commit avanti a `origin/main`, fermo a `54445af`. **Nessun push.**

## 21. Git status finale

```text
$ git status --porcelain
(vuoto)

$ git log --oneline -1
<questo commit>  docs(H2): close the accessibility and layout compartment

$ git rev-parse --short origin/main
54445af
```

Albero pulito: nessun `__pycache__`, nessun `.pytest_cache`, nessun file di lavoro residuo. I
test si eseguono con `PYTHONDONTWRITEBYTECODE=1` e `-p no:cacheprovider` proprio per non
lasciarne.

## 22. Gate di uscita

| Gate | Esito |
|---|---|
| H2-G1 la finestra prende la dimensione chiesta a 1280×720, 1366×768, 1920×1080 | **OK** — § 12 |
| H2-G2 nessun controllo collocato resta fuori portata, su tutte le schede | **OK** — § 12 |
| H2-G3 `minsize` abbassata come conseguenza, non come numero | **OK** — § 6, § 16 |
| H2-G4 le barre vanno a capo invece di nascondere pulsanti | **OK** — § 5 |
| H2-G5 lo scorrimento è aggiunto solo dove serve | **OK** — § 6, barre solo al bisogno |
| H2-G6 le azioni essenziali sono raggiungibili da tastiera | **OK** — § 7, § 13 |
| H2-G7 il focus è visibile e in ordine logico | **OK** — § 7, § 13 |
| H2-G8 i suggerimenti compaiono anche col focus | **OK** — § 7 |
| H2-G9 i Canvas informativi hanno un'alternativa testuale | **OK** — § 8 |
| H2-G10 nessuna informazione dipende dal solo colore | **OK** — § 14 |
| H2-G11 i dialoghi dichiarano un focus iniziale sensato | **OK** — § 7 |
| H2-G12 nessuna dichiarazione di conformità WCAG generale | **OK** — § 14 |
| H2-G13 nessun `<Configure>` costoso, nessun ciclo configure→geometry→configure | **OK** — § 5 |
| H2-G14 collaudo alle scale 1.0 / 1.5 / 2.0, con i limiti dichiarati | **OK** — § 12 |
| H2-G15 il flusso del dialogo impostazioni non torna al falso successo | **OK** — § 9 |
| H2-G16 la nota di M01 è al posto giusto e localizzata | **OK** — § 11 |
| H2-G17 gli errori del sistema operativo hanno una cornice localizzata | **OK** — § 10 |
| H2-G18 IT/EN coerenti, layout collaudato in entrambe | **OK** — § 15 |
| H2-G19 non-regressione A–H1, matematica invariata | **OK** — § 18 |
| H2-G20 nessun I/J/K iniziato, nessuna risorsa esterna | **OK** — § 2, § 23 |
| H2-G21 nessun push | **OK** — `origin/main` fermo a `54445af` |

## 23. Debiti espliciti per I, J, K

* `distribution_tab` e `decomposition` mostrano l'errore di un worker come stringa in un'etichetta
  di stato: passano da una coda, non da `run_in_thread`, quindi non dal confine di presentation.
  La cornice ora esiste (`errori.per_file`, `errori.per_utente`); resta da portarcele;
* revisione redazionale delle virgolette nei testi inglesi (§ 15): sei chiavi, di cui quattro di E
  e H1;
* `N03` (`pypdfium2`) e `N04` (PyInstaller) per K, la cronologia utente per J, gli strumenti
  matematici avanzati per I;
* legacy senza compartimento: le facciate differite di `core.algebra` (G1) e `core.permutations`
  (G2), entrambe conservate e sotto test.

## 24. Certificazione

**COMPARTIMENTO H CHIUSO.**

H1 — correttezza della presentation e localizzazione: chiuso, 8 commit, gate H1-G1…H1-G21 tutti
soddisfatti (`H1_PRESENTATION_I18N_CLOSED.md`).

H2 — layout adattivo, tastiera e accessibilità: chiuso, 9 commit, gate H2-G1…H2-G21 tutti
soddisfatti, e i tre debiti che H1 aveva lasciato a H2 — flusso del dialogo impostazioni, cornice
degli errori del sistema operativo, collocazione della nota di M01 — sono saldati (§ 9, § 10,
§ 11).

Suite completa verde: 1429 raccolti, 1428 passati, 1 saltato per una dipendenza opzionale assente,
nessun `xfail` residuo. Matematica invariata. `origin/main` fermo a `54445af`: nessun push.

Il lavoro prosegue con il compartimento I.
