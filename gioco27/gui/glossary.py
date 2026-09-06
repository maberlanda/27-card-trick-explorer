"""
Testi della scheda "Inizia qui" e del glossario, in italiano semplice.

Tenuti separati dalla GUI così si possono rivedere senza toccare il codice.
Ogni voce del glossario è (termine, descrizione_breve, descrizione_estesa):
la breve compare nella lista, l'estesa nel tooltip al passaggio del mouse.
"""

ONBOARD_INTRO = (
    "Questa scheda ti accompagna nei primi passi: parti da un preset, "
    "guarda l'Anteprima, poi esplora il resto quando vuoi."
)

# (icona/numero, titolo, descrizione)
ONBOARD_STEPS = [
    ("1", "Prova il Simulatore",
     "Nella scheda Simulatore esegui il trucco come col mazzo vero: "
     "istruzioni, fotografie del mazzo e pratica guidata."),
    ("2", "Sfoglia la Tavola 216",
     "Le 216 disposizioni semplici del libro: mescolamenti, impilamenti, "
     "posizioni degli Assi e proprietà di ogni sequenza."),
    ("3", "Approfondisci",
     "Carica il preset «Gioco Reale», guarda l'Anteprima e, quando te la "
     "senti, attiva la modalità Esperto per Stadi, Explorer, Cicli e "
     "Distribuzione."),
]

# (termine, breve, estesa)
GLOSSARY = [
    ("MSC",
     "Il mescolamento di base: distribuisci le 27 carte in 3 colonne e le raccogli.",
     "MSC indica il mescolamento elementare del gioco. È l'operazione "
     "ripetuta a ogni stadio: cambia l'ordine delle carte in modo "
     "prevedibile, distribuendole in colonne e raccogliendole."),
    ("Permutazione",
     "Un modo di rimescolare: a ogni posizione di partenza associa una posizione d'arrivo.",
     "Una permutazione di 27 elementi dice dove finisce ciascuna delle 27 "
     "carte. Tutto il gioco è una composizione (un concatenamento) di "
     "permutazioni."),
    ("Stadio",
     "Una singola «mossa» del gioco: una raccolta P, il mescolamento MSC e un'orientazione J.",
     "In formula Stadioᵢ = Pᵢ ∘ MSC ∘ Jᵢ. Il gioco completo concatena 3 stadi, "
     "uno dopo l'altro."),
    ("P (raccolta)",
     "Come raccogli i tre pacchetti dopo averli messi in colonna.",
     "P è la permutazione che descrive l'ordine con cui riprendi in mano i "
     "pacchetti dopo il mescolamento. Nel gioco fisico la raccolta agisce "
     "al livello dei blocchi: nel modello è il fattore P₂."),
    ("Mescolamento",
     "La sigla funzionale della raccolta: la cifra N va nella N-esima lettera.",
     "È la lettura «permutativa» della sigla (es. CDS: S→C, C→D, D→S) ed è "
     "la riga del tabellone. Il tabellone sono i tre mescolamenti impilati, "
     "il primo in basso."),
    ("Impilamento",
     "Il gesto fisico: l'ordine dei mazzetti dal dorso verso il fondo.",
     "È la permutazione INVERSA del mescolamento. Le sigle CDS e DSC si "
     "scambiano fra i due ruoli (la «Prima Crisi di Seldon»), le altre "
     "quattro coincidono con la propria inversa."),
    ("J (orientazione)",
     "Come orienti o giri il mazzo prima del mescolamento.",
     "J è la permutazione che descrive l'orientamento del mazzo a inizio "
     "stadio (ad esempio mazzo dritto o capovolto)."),
    ("Gioco Reale",
     "Un insieme pronto di 1 728 sequenze: l'esempio classico da cui partire.",
     "Il preset «Gioco Reale» imposta i filtri sulle 1 728 combinazioni "
     "canoniche, l'esempio standard per familiarizzare con il programma."),
    ("T  /  T⁻¹",
     "La trasformazione totale delle 3 mosse (T) e la sua inversa (T⁻¹).",
     "T è la permutazione che riassume l'effetto complessivo dei 3 stadi. "
     "T⁻¹ è la mossa che riporta tutto al punto di partenza."),
    ("Coniugio",
     "Due mosse «coniugate» fanno la stessa cosa, a meno di rinominare le posizioni.",
     "x e y sono coniugate se esiste g tale che g∘x∘g⁻¹ = y: hanno la stessa "
     "struttura e lo stesso comportamento, cambia solo l'etichetta delle "
     "posizioni del mazzo."),
    ("Cayley (tavola)",
     "La tabella di tutti i prodotti possibili tra due mosse del gruppo.",
     "La tavola di Cayley elenca il risultato di A∘B per ogni coppia di mosse "
     "A e B del gruppo (qui 216 mosse, quindi una tabella 216×216)."),
    ("Kronecker",
     "Scompone una mossa in tre pezzi indipendenti: pacchetti, terzine e carte.",
     "La decomposizione di Kronecker (⊗) spezza una permutazione in tre "
     "fattori che agiscono separatamente sui tre livelli del mazzo."),
    ("Ciclo",
     "Un gruppetto di posizioni che ruotano tra loro ripetendo la mossa.",
     "Un ciclo (a b c) significa: a va in b, b va in c, c torna in a. Ogni "
     "permutazione si scompone in cicli disgiunti."),
    ("Ordine",
     "Quante volte ripetere una mossa per tornare al punto di partenza.",
     "L'ordine di una mossa è il numero minimo di ripetizioni dopo cui il "
     "mazzo torna identico a com'era all'inizio."),
]


# Testi dei banner d'aiuto in cima a ciascuna scheda: chiave -> (breve, esteso)
TAB_HELP = {
    "stadio": (
        "Le matrici 3×3 (Kronecker) che compongono P ∘ MSC ∘ J di questo stadio.",
        "P e J sono prodotti di Kronecker di tre matrici 3×3 — P₂⊗P₁⊗P₀ — una "
        "per livello: le 3 carte di ogni terzina, le 3 terzine di ogni "
        "pacchetto, i 3 pacchetti. Fissa un valore col menu per vincolarlo, o "
        "spunta più caselle per esplorare le combinazioni. Liberi tutti i "
        "livelli ci sono 1 728 possibilità per stadio; il «Gioco Reale» tiene "
        "solo le 12 fisicamente eseguibili. Se non sai da dove iniziare, usa un "
        "preset dalla barra arancione in alto."),
    "anteprima": (
        "Calcola e mostra cosa succede alle carte per UNA singola combinazione.",
        "Imposta P e J per i tre stadi e premi Calcola: vedrai la "
        "permutazione risultante e l'effetto sul mazzo, passo per passo."),
    "analisi": (
        "Raggruppa e conta le combinazioni per molteplicità, con dettaglio ed export.",
        "Analizza l'insieme filtrato: quante combinazioni producono la stessa "
        "trasformazione, con tabelle di dettaglio esportabili."),
    "explorer": (
        "Analisi algebrica di un'espressione: forma normale, matrici, decomposizioni.",
        "Scrivi un'espressione in P / MSC / J e ottieni forma normalizzata, "
        "periodo, forma canonica K ∘ MSCᵏ, le matrici di T e T⁻¹ e le "
        "decomposizioni di Kronecker."),
    "cicli": (
        "Mostra la struttura ciclica della permutazione totale T.",
        "Ogni permutazione si scompone in cicli disgiunti. Qui vedi i cicli, "
        "le loro lunghezze e l'ordine (quante ripetizioni riportano il mazzo "
        "all'origine)."),
    "distribuzione": (
        "Statistiche e distribuzione delle proprietà sulle combinazioni filtrate.",
        "Grafici e conteggi su ordine, tipo di ciclo e altre proprietà "
        "dell'insieme di combinazioni selezionato."),
    "simulatore": (
        "Pratica guidata del trucco, passo per passo.",
        "Simula l'esecuzione del gioco come la faresti con il mazzo vero, "
        "con eventuale evidenziazione degli errori."),
    "tavola": (
        "La tavola delle 216 disposizioni semplici del libro.",
        "Per ogni sequenza di tre mescolamenti: impilamenti (gesto fisico), "
        "posizioni finali degli Assi, periodo, punti fissi e tipo ciclico. "
        "Puoi anche ricostruire il tabellone dalle sole posizioni degli Assi."),
}
