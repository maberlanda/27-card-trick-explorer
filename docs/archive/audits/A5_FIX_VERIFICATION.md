# A5-FIX — Verifica delle correzioni finali

Data: 28 settembre 2026. Prodotto: Gioco delle 27 carte, release candidate
4.0.0.

## Esito

| Rilievo | Stato | Verifica |
|---|---|---|
| A5-MEDIUM-01 | **VERIFIED FIXED** | `guide.s10.count` e `tooltip.verify` chiamano coerentemente **Procedure** i 1 728 oggetti del Gioco reale, in italiano e in inglese. |
| A5-MEDIUM-02 | **VERIFIED FIXED** | Le quattro formulazioni inglesi individuate in glossario e CLI usano **sequence** al posto del calco **succession**. |

Le modifiche sono puntuali. Non sono state eseguite sostituzioni globali:
`sequence` e `combination` restano nei contesti in cui indicano oggetti
diversi; l'etichetta tecnica preesistente `Succession (L90)` resta invariata.

## File modificati

- `gioco27/i18n.py`
- `tests/test_a5_terminology_fixes.py`
- `docs/audits/A5_FIX_VERIFICATION.md`

`docs/audits/A5_FINAL_CROSSCHECK.md` non è stato modificato: il blob Git prima
e dopo la correzione è
`3d506dbf1ba9bc3477055731c3ab45de3a1c100c`.

## Test eseguiti

Sono stati eseguiti soltanto i test direttamente coinvolti e le regressioni
terminologiche pertinenti di A2 e A4:

```text
tests/test_a5_terminology_fixes.py
tests/test_a2_terminology_fixes.py
tests/test_a4_english_language_fixes.py

38 superati, 0 errori
```

`git diff --check` è superato. La suite completa non è stata eseguita.

## Invarianti

Le correzioni riguardano esclusivamente testi dei cataloghi e relative
aspettative di test. Matematica, formule, schema `gioco27.esperimento`,
`schema_version = 1`, colonne CSV, chiavi JSON, nomi dei fogli XLSX, token CLI,
serializzazione e identificatori tecnici non sono cambiati.

Non sono stati rigenerati export, pacchetti o eseguibili. Non è stata avviata
la verifica tecnica finale e non è stato eseguito alcun push.
