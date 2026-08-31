#!/usr/bin/env python3
"""
LetsGO / SPYTIPS -- Rohdaten-Sammler ("Proxy")
==============================================
Laedt alle fuer den Backtest noetigen Assets als LANGHISTORIE-Proxys
(Semigrowth-Stil: Indizes/US-ETFs, EUR/USD zur Waehrungssynthese).

Lokal ausfuehren (dort ist Yahoo erreichbar), dann letsgo_data.csv hochladen.

Setup:   pip install yfinance pandas
Start:   python letsgo_downloader.py
Ergebnis: letsgo_data.csv  (Datum x alle Serien, adjustierte Schlusskurse)
"""

import sys
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    sys.exit("Bitte zuerst:  pip install yfinance pandas")

START = "1990-01-01"   # so weit wie moeglich; einzelne Serien starten spaeter

# name -> Yahoo-Ticker. Kommentar erklaert Rolle.
TICKERS = [
    # ---- S&P 500 Basis (Semigrowth: S&P 500 TOTAL RETURN) ----
    ("SP500_TR_USD",   "^SP500TR"),   # Backtest-Basis 1x, USD, ab 1988
    ("SP500_PR_USD",   "^GSPC"),      # Fallback Price Return
    ("SSO_2x_USD",     "SSO"),        # echter 2x (ab 2006) -- nur zur Validierung der Hebel-Synthese

    # ---- TIPS (Regime-Signal) ----
    ("TIPS_US_USD",    "TIP"),        # US-TIPS ETF, USD, ab 2003 (Semigrowth-Signal)

    # ---- Gold ----
    ("GOLD_USD",       "GC=F"),       # Gold Futures USD, lange Historie
    ("GLD_USD",        "GLD"),        # SPDR Gold, USD (Fallback)
    ("UGL_2x_USD",     "UGL"),        # 2x Gold (ab 2008) -- Validierung 2x-Gold-Synthese

    # ---- Cash / Kurzzins ----
    ("USD_TBILL_3M",   "^IRX"),       # 13-Week T-Bill Rate (USD Cash-Proxy / Hebelfinanzierung)
    ("BIL_USD",        "BIL"),        # 1-3M T-Bill ETF (Fallback Cash USD)

    # ---- Zins / Bond-Regime-Kandidaten ----
    ("US_1_3Y_SHY",    "SHY"),
    ("US_7_10Y_IEF",   "IEF"),
    ("US_20Y_TLT",     "TLT"),

    # ---- Bitcoin ----
    ("BTC_USD",        "BTC-USD"),    # ab 2014
    ("BTC_EUR",        "BTC-EUR"),

    # ---- Wechselkurs (EUR<->USD Synthese: unhedged-EUR & Hedging-Kosten) ----
    ("EURUSD",         "EURUSD=X"),

    # ---- Deine echten ETFs (nur Kurzfenster-Validierung der Synthese) ----
    ("IBCF_SP500_EURH","IBCF.DE"),    # IE00B3ZW0K18  (ab 2010)
    ("IBC5_TIPS_EURH", "IBC5.DE"),    # IE00BDZVH966  (ab 2018)
    ("GOLD_EUR_4GLD",  "4GLD.DE"),    # DE000A0S9GB0  Xetra-Gold
    ("CASH_EUR_XEON",  "XEON.DE"),    # LU0290358497  Xeon (EUR Cash)
]

def main():
    frames, failed = {}, []
    for name, tkr in TICKERS:
        try:
            df = yf.download(tkr, start=START, progress=False, auto_adjust=True)
            if df is None or len(df) == 0:
                failed.append((name, tkr, "leer")); continue
            s = df["Close"]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            s.name = name
            frames[name] = s
            print(f"OK   {name:18s} {tkr:10s} {len(s):5d} Zeilen  "
                  f"{s.index.min().date()} -> {s.index.max().date()}")
        except Exception as e:
            failed.append((name, tkr, str(e)[:70]))
            print(f"FAIL {name:18s} {tkr:10s} {str(e)[:60]}")

    if not frames:
        sys.exit("Nichts geladen -- Internet/yfinance pruefen.")

    out = pd.concat(frames.values(), axis=1)
    out.index.name = "Date"
    out.to_csv("letsgo_data.csv")
    print("\n" + "=" * 60)
    print(f"GESPEICHERT: letsgo_data.csv  ({out.shape[0]} Zeilen, {out.shape[1]} Spalten)")
    print("Diese Datei bitte im Chat hochladen.")
    if failed:
        print("\nNicht geladen (Fallbacks/Synthese fangen das ab):")
        for name, tkr, why in failed:
            print(f"   - {name} ({tkr}): {why}")

if __name__ == "__main__":
    main()
