# ============================================================================
#  SpyTips-Cool  —  FINALE STRATEGIE C   (3x-S&P500 75%  +  1x-BTC 25%)
# ============================================================================
#
#  Taegliche Entscheidung (Signale auf 1x-USD-Kursen gerechnet):
#
#     MARKT  =  US-TIPS > SMA160   UND   S&P 500 > SMA160
#               ->  75% 3x-S&P500   +   25% 1x-BTC
#     sonst  ->  100% CASH
#
#     15-Handelstage-Freeze (beidseitig) auf jeden MARKT<->CASH-Wechsel.
#
#  KEIN Gold, KEIN TLT, KEIN BTC-SMA-Gate (Variante C ist ungegatet:
#  BTC wird im Markt fix gehalten -> BTC ist KEIN Entscheidungssignal).
#
#  Parameter = ZENTREN der robusten Parameterwolken (nicht Peaks). Bestimmt mit
#  ANTI-OVERFITTING-Methodik: nicht-ueberlappende Fenster (2014-18/2018-22/2022-26)
#  + Minimax (bestes schlechtestes Fenster) + Nachbarschafts-Flachheit + Sharpe UND
#  Sortino, kein Look-Ahead, rf=Cash:
#     SPY-SMA 160 / TIPS-SMA 160  (Minimax-Sieger; flachste Nachbarschaft der
#                                  Wolke; gleiche SMA fuer beide Signale =
#                                  parameter-sparsam; Roh-Peak 180/160 gemieden.
#                                  TIPS-SMA 160 statt 200, weil 200 im Zinsschock
#                                  2022 spuerbar einbricht (Sharpe 0.73 vs 1.01).)
#     Freeze 15                   (Plateau 12-15 flach)
#     BTC-Anteil 25%              (Maximum des kombinierten Minimax-Robustheits-
#                                  Scores z(minSharpe)+z(minSortino)+z(worstDD);
#                                  Plateau 25-30%. 25% = bestes risikoadjustiertes
#                                  Worst-Case UND geringste Abhaengigkeit vom
#                                  einzigen BTC-Bullenzyklus; naeher am Mean-
#                                  Variance-Korridor (Tangency ~19%).)
#
#  Kennzahlen (unabh. nachgerechnet): 2018+ CAGR ~46%, MaxDD ~-30%, Sharpe ~1.37,
#  Sortino ~1.44; 2014+ voll Sharpe 1.32. Minimax ueber getrennte Fenster:
#  min-Sharpe 1.10, min-Sortino 1.15.  (Alt 150/200/40%: 2018+ Sharpe 1.09.)
# ============================================================================

SPY_SMA = 160
TIPS_SMA = 160
COOLDOWN_DAYS = 15

# Zielgewichte im MARKT-Regime
SPY3X_WEIGHT = 0.75
BTC_WEIGHT = 0.25

# Anzeige-Text der Produkte (nur fuer die Nachricht, NICHT fuer die Entscheidung)
SPY_PRODUCT = "3x-S&P500 (z.B. WisdomTree 3USL, IE00B7Y34M31)"
BTC_PRODUCT = "1x-Bitcoin-ETP"

# Anzahl Download-Versuche pro Lauf
TRY_COUNT = 3

# True = taegliche Statusmeldung; False = nur bei Allokationswechsel
DAILY_NOTIFICATION = True

# ---- DO NOT CHANGE ----
HISTORY_FILENAME = "history"
