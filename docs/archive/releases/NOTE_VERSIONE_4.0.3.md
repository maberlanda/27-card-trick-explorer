# Gioco delle 27 carte — note della versione 4.0.3

La 4.0.3 è una patch di manutenzione basata sulla [4.0.2](NOTE_VERSIONE_4.0.2.md).

## Eseguibile Windows e PDF

- Il pacchetto autonomo Windows include il modulo del **PDF matriciale**.
  Nello ZIP della 4.0.2 il comando **Genera → PDF matriciale** falliva
  perché il modulo caricato dinamicamente era assente dall'eseguibile.
- La verifica automatica del bundle avvia l'interfaccia, genera un PDF
  matriciale e un PDF dettagliato di prova e verifica che siano leggibili. Il comando di collaudo
  è `Gioco27.exe --smoke-gui`.

## Interfaccia e lavori in background

- A 1280×720, in **Explorer → Riconoscimento**, la barra delle schede dei
  risultati è raggiungibile senza scorrere. Gli avvisi occupano spazio solo
  quando contengono un messaggio.
- La barra di stato mostra un riepilogo su una riga. Il messaggio completo
  è disponibile nel tooltip.
- I lavori in background consegnano gli aggiornamenti attraverso una coda
  gestita dal thread di Tk. Alla chiusura della finestra, le notifiche
  ancora in coda vengono scartate.

## Sviluppo

La [roadmap 4.x](../../release/ROADMAP_4.x.md) parte dalla 4.0.3. La 4.1.0 comprende
l'infrastruttura grafica comune, la Vista Posizioni e la Vista Fibre.
La Vista Gruppo è una milestone successiva della 4.1.x.
