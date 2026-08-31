# SpyTips-Cool Signal-Bot — Finale Strategie C

Ein GitHub-Actions-Bot, der taeglich das Regime prueft und eine Nachricht an einen
**Discord**-Kanal sendet (optional zusaetzlich WhatsApp bei echtem Wechsel).

## Strategie C (fixiert)

Entscheidung taeglich auf **USD-1x-Kursen** (zuverlaessig & frueh bei Yahoo):

| Bedingung | Allokation |
|---|---|
| US-TIPS > SMA160 **und** S&P 500 > SMA160 | **75% 3x-S&P500 + 25% 1x-BTC** |
| sonst | **100% Cash** |

- **15-Handelstage-Freeze** (beidseitig) nach jedem MARKT<->CASH-Wechsel.
- **Kein Gold, kein TLT, kein BTC-SMA-Gate** (Variante C: BTC im Markt fix 25%,
  daher ist BTC **kein** Entscheidungssignal — nur Info-Anzeige).
- Signale: `^SP500TR` (S&P 500 Total Return) und `TIP` (US-TIPS).
- Parameter = **Zentren der robusten Parameterwolken**, bestimmt mit Anti-Overfitting-
  Methodik (nicht-ueberlappende Fenster 2014-18/2018-22/2022-26 + Minimax +
  Nachbarschafts-Flachheit, Sharpe UND Sortino, kein Look-Ahead): SPY-SMA **160** /
  TIPS-SMA **160** / Freeze **15** / BTC-Anteil **25%**. Bewusst NICHT der Roh-Peak
  (180/160). Kennzahlen (unabh. nachgerechnet): 2018+ CAGR ~46%, MaxDD ~-30%,
  Sharpe ~1.37, Sortino ~1.44; Minimax min-Sharpe 1.10.

### Warum USD statt EUR-hedged?
Backtest: USD-Signal ist signalgleich zum EUR-hedged-Signal. Aber die frueher
genutzten `.DE`-EUR-hedged-Ticker (IBCF.DE/IBC5.DE) haengen auf Yahoo einen
Handelstag hinterher (Xetra-Lag) -> verspaetetes Signal + Dauer-Retries. US-Kurse
(Close ~22:00 CET) liegen bei Yahoo frueh vor.

## Setup
1. Repository forken.
2. Secret `DISCORD_WEBHOOK_URL` anlegen (Repo > Settings > Secrets and variables >
   Actions). Discord-Webhook: Kanal-Einstellungen > Integrationen > Webhook.
3. (Optional WhatsApp bei Wechsel) Secrets `WHATSAPP_PHONE` + `CALLMEBOT_APIKEY`.
4. Actions-Tab aktivieren. Laeuft taeglich **05:17 UTC (07:17 CEST)**.

## Test
- Manuell: Actions-Tab > Workflow **LETSGO cooldown** > „Run workflow".
- Erst-Lauf baut `history_160_160_15_USD.txt` neu auf und postet den Status.

## Umsetzung im Depot (Xetra/DE, selbst pruefen — keine Anlageberatung)
- 3x-S&P500: WisdomTree S&P 500 3x Daily Leveraged (IE00B7Y34M31, 3USL).
- BTC: physisches ETP; Steuer je nach Struktur (§23 mit Lieferanspruch = steuerfrei
  nach 1 J.; oder §20/Abgeltungsteuer). Fuer haeufiges Traden oft §20 guenstiger.
