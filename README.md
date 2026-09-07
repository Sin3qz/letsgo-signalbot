# SpyTips-Cool Signal-Bot — Finale Strategie C

Ein GitHub-Actions-Bot, der taeglich das Regime prueft und eine Nachricht an einen
**Discord**-Kanal sendet; bei einem echten Signalwechsel (Buy/Sell) zusaetzlich
ein **ntfy**-Push aufs Handy.

## Strategie C (fixiert)

Entscheidung taeglich auf **USD-1x-Kursen** (zuverlaessig & frueh bei Yahoo):

| Bedingung | Allokation |
|---|---|
| US-TIPS > SMA160 **und** S&P 500 > SMA160 | **70% 3x-S&P500 + 30% 1x-BTC** |
| sonst | **100% Cash** |

- **15-Handelstage-Freeze** (beidseitig) nach jedem MARKT<->CASH-Wechsel.
- **Kein Gold, kein TLT, kein BTC-SMA-Gate** (Variante C: BTC im Markt fix 30%,
  daher ist BTC **kein** Entscheidungssignal — nur Info-Anzeige).
- Signale: `^SP500TR` (S&P 500 Total Return) und `TIP` (US-TIPS).
- Parameter = **Zentren der robusten Parameterwolken**, bestimmt mit Anti-Overfitting-
  Methodik (nicht-ueberlappende Fenster 2014-18/2018-22/2022-26 + Minimax +
  Nachbarschafts-Flachheit, **Sortino** als Entscheider, kein Look-Ahead): SPY-SMA
  **160** / TIPS-SMA **160** / Freeze **15** / BTC-Anteil **30%**. Bewusst NICHT der
  Roh-Peak (180/160). Kennzahlen (unabh. nachgerechnet): 2018+ CAGR ~44%,
  MaxDD ~-29%, Sortino ~1.44; Worst-Case (3 Fenster) min-Sortino 1.12.

## Nachricht
- **Status-Zeile (immer):** `MARKT — investiert: 3xSPY und 1xBTC (N Cooldown-Tage)`
  bzw. `CASH — 100% Cash`. (Beimischungs-Prozente werden bewusst nicht angezeigt.)
- **Kopfzeile nur bei echtem Wechsel:** `🟢 BUY — GO IN MARKET NOW` /
  `🔴 SELL — GO IN CASH NOW`. Nur dann geht auch der ntfy-Push raus.
- Ganz unten immer die Backtest-Hinweise (Gesamt-Sortino 30-40%, Worst-Case 20-30%,
  MaxDD >40% BTC).

### Warum USD statt EUR-hedged?
Backtest: USD-Signal ist signalgleich zum EUR-hedged-Signal. Aber die frueher
genutzten `.DE`-EUR-hedged-Ticker (IBCF.DE/IBC5.DE) haengen auf Yahoo einen
Handelstag hinterher (Xetra-Lag) -> verspaetetes Signal + Dauer-Retries. US-Kurse
(Close ~22:00 CET) liegen bei Yahoo frueh vor.

## Setup
1. Secret `DISCORD_WEBHOOK_URL` anlegen (Repo > Settings > Secrets and variables >
   Actions). Discord-Webhook: Kanal-Einstellungen > Integrationen > Webhook.
2. Secret `NTFY_TOPIC` anlegen = ein langer, nicht erratbarer Topic-Name. Denselben
   Namen in der ntfy-App (Android/iOS) oder auf https://ntfy.sh abonnieren. (Optional
   `NTFY_SERVER`, falls eigener ntfy-Server; Default `https://ntfy.sh`.)
3. Actions-Tab aktivieren. Laeuft taeglich **05:17 UTC (07:17 CEST)**.

## Test
- Manuell: Actions-Tab > Workflow **LETSGO cooldown** > „Run workflow".
- Erst-Lauf baut `history_160_160_15_USD.txt` neu auf und postet den Status.

## Umsetzung im Depot (Xetra/DE, selbst pruefen — keine Anlageberatung)
- 3x-S&P500: WisdomTree S&P 500 3x Daily Leveraged (IE00B7Y34M31, 3USL).
- BTC: physisches ETP; Steuer je nach Struktur (§23 mit Lieferanspruch = steuerfrei
  nach 1 J.; oder §20/Abgeltungsteuer). Fuer haeufiges Traden oft §20 guenstiger.
