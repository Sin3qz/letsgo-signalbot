"""
SpyTips-Cool — Finale Strategie C  (3x-S&P500 60% + 1x-BTC 40%)

Entscheidung ausschliesslich auf ZUVERLAESSIGEN USD-1x-Kursen:
    S&P 500 Total Return  ->  ^SP500TR   (SMA150)
    US-TIPS               ->  TIP        (SMA200)

Warum USD statt EUR-hedged?
  - Backtest: USD-Signal ist signalgleich zum EUR-hedged-Signal (Sharpe 0,99),
    aber EUR-unhedged zerstoert v.a. das ruhige TIPS-Signal.
  - Praxis: die frueher genutzten .DE-EUR-hedged-Ticker (IBCF.DE/IBC5.DE) haengen
    auf Yahoo einen Handelstag hinterher (Xetra-Lag) -> falsches/verspaetetes
    Signal + Dauer-Retries. ^SP500TR und TIP (US-Close ~22:00 CET) liegen bei
    Yahoo frueh und zuverlaessig vor.

BTC ist KEIN Signal (Variante C haelt BTC im Markt fix mit 40%). BTC wird nur
optional als Info-Kurs angezeigt und blockiert die Entscheidung nie.
"""

import os
import json
import time
import numpy as np
import pandas as pd
from .constants import *

# ---- Entscheidungs-Ticker (USD, 1x) ----
SPY_USD_TICKER = "^SP500TR"
TIPS_USD_TICKER = "TIP"
# ---- reiner Info-Ticker (nicht entscheidungsrelevant) ----
BTC_USD_TICKER = "BTC-USD"

STATUS_FILE = "letsgo_status.json"


# ==========================================================================
#  STRATEGIE-KERN (reine Funktionen, ohne I/O -> testbar)
# ==========================================================================

def raw_target_allocation(spy_on, tips_on):
    """Reine Signal-Logik ohne Cooldown:  MARKT wenn beide > SMA, sonst CASH."""
    if spy_on and tips_on:
        return "MARKET"
    return "CASH"


def advance_allocation(prev_alloc, cooldown, spy_on, tips_on, cooldown_days=COOLDOWN_DAYS):
    """
    Ein Handelstag. Gibt (allocation, cooldown, changed) zurueck.
    Freeze: nach jedem MARKT<->CASH-Wechsel wird die Allokation 'cooldown_days'
    Handelstage eingefroren (beidseitig).
    """
    if cooldown > 0:
        cooldown -= 1

    target = raw_target_allocation(spy_on, tips_on)

    if prev_alloc is None:          # Initialisierung
        return target, 0, False

    if cooldown == 0 and target != prev_alloc:
        return target, cooldown_days, True

    return prev_alloc, cooldown, False


def compute_allocation_series(spy_diff, tips_diff, cooldown_days=COOLDOWN_DAYS):
    """Laeuft ueber die ausgerichteten diff-Serien -> Listen (alloc, cooldown) pro Tag."""
    allocs, cds = [], []
    prev, cd = None, 0
    for i in range(len(spy_diff)):
        prev, cd, _ = advance_allocation(prev, cd,
                                         spy_diff.iloc[i] > 0,
                                         tips_diff.iloc[i] > 0,
                                         cooldown_days=cooldown_days)
        allocs.append(prev)
        cds.append(cd)
    return allocs, cds


# ==========================================================================
#  DATEN & INDIKATOREN
# ==========================================================================

def _download_history(ticker):
    import yahooquery as yq  # lazy: Modul laedt auch ohne yahooquery (Tests)
    return yq.Ticker(ticker).history(period="max", adj_ohlc=True, adj_timezone=False)


def _prepare_close(df):
    """Robuste Close-Reihe: Datumsindex normalisieren, nur Close, nur bis gestern (Berlin)."""
    date_level_str = pd.Index([str(x) for x in df.index.get_level_values("date")])
    colon_mask = date_level_str.str.contains(":")
    df.index = pd.to_datetime(
        date_level_str.where(~colon_mask, date_level_str.str.split(" ").str[0])
    )
    close = pd.to_numeric(df["close"], errors="coerce").dropna()
    close = close[~close.index.duplicated(keep="last")].sort_index()

    berlin_today = pd.Timestamp.now(tz="Europe/Berlin").date()
    berlin_yesterday = berlin_today - pd.Timedelta(days=1)
    return close[close.index.date <= berlin_yesterday]


def _diff_to_sma(close, sma_window):
    sma_rolling = close.rolling(window=sma_window).mean()
    diff = (close - sma_rolling) / sma_rolling
    return sma_rolling, diff


def _align_two(spy_close, tips_close):
    """SMAs auf der VOLLEN Reihe rechnen, dann auf gemeinsame Handelstage ausrichten."""
    spy_sma, spy_diff = _diff_to_sma(spy_close, SPY_SMA)
    tips_sma, tips_diff = _diff_to_sma(tips_close, TIPS_SMA)
    common = spy_close.index.intersection(tips_close.index).sort_values()
    a = lambda s: s.reindex(common)
    return {
        "index": common,
        "spy_close": a(spy_close), "tips_close": a(tips_close),
        "spy_sma": a(spy_sma), "tips_sma": a(tips_sma),
        "spy_diff": a(spy_diff), "tips_diff": a(tips_diff),
    }


def _last_weekday_on_or_before(date_value):
    d = pd.Timestamp(date_value)
    while d.weekday() >= 5:      # Sa/So zurueck auf Fr
        d = d - pd.Timedelta(days=1)
    return d.strftime("%Y-%m-%d")


def _expected_fresh_date():
    berlin_yesterday = pd.Timestamp.now(tz="Europe/Berlin").date() - pd.Timedelta(days=1)
    return _last_weekday_on_or_before(berlin_yesterday)


def _date_de(date_string):
    try:
        return pd.to_datetime(date_string).strftime("%d.%m.%Y")
    except Exception:
        return str(date_string)


def _build_signal_status(key, name, ticker, close, sma_rolling, diff):
    """
    FIX: Frische ist jetzt rein DATUMSBASIERT (currentDate >= erwarteter letzter
    Handelstag). Die fruehere 'valueChanged'-Bedingung wurde ENTFERNT — sie
    feuerte an ruhigen Tagen faelschlich Dauer-Retries aus.
    """
    expected_date = _expected_fresh_date()
    current_date = close.index[-1].strftime("%Y-%m-%d")
    # FIX (Feiertage): An US-Boersenfeiertagen (Wochentag ohne Handel) ist der
    # letzte echte Handelstag aelter als 'expected_date'. Ohne Toleranz wuerde
    # needsRetry=True gesetzt -> 60 Min Leerlauf-Retry + faelschliche stale-Warnung,
    # obwohl die Daten korrekt sind. Daten gelten daher auch als frisch, wenn der
    # letzte Close hoechstens 4 Kalendertage alt ist (Wochenende + 1 Feiertag).
    berlin_yesterday = pd.Timestamp.now(tz="Europe/Berlin").date() - pd.Timedelta(days=1)
    recent = (berlin_yesterday - close.index[-1].date()).days <= 4
    plausible = (current_date >= expected_date) or recent
    return {
        "key": key, "name": name, "ticker": ticker,
        "currentDate": current_date,
        "expectedDate": expected_date,
        "current": float(close.iloc[-1]),
        "sma": float(sma_rolling.iloc[-1]),
        "diffPct": float(diff.iloc[-1] * 100),
        "fresh": bool(plausible),
    }


def _save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)


# ==========================================================================
#  HISTORY  (neues, schlankes Format, 7 Spalten)
#  date, spy_close, tips_close, spy_sma, tips_sma, cooldown, allocation
# ==========================================================================

def _write_entry(f, A, i, alloc, cooldown):
    f.write(
        f"{A['index'][i]},"
        f"{A['spy_close'].iloc[i]},"
        f"{A['tips_close'].iloc[i]},"
        f"{A['spy_sma'].iloc[i]},"
        f"{A['tips_sma'].iloc[i]},"
        f"{cooldown},"
        f"{alloc}\n"
    )


def _parse_entry(cols):
    return {
        "date": cols[0],
        "spy_close": float(cols[1]), "tips_close": float(cols[2]),
        "spy_sma": float(cols[3]), "tips_sma": float(cols[4]),
        "cooldown": int(cols[5]), "allocation": cols[6].strip(),
    }


# ==========================================================================
#  NACHRICHT
# ==========================================================================

def _fmt_pct(x):
    return f"{x:+.2%}" if x == x else "n/a"


def _build_message(allocation, cooldown, spy_st, tips_st, btc_info, data_stale):
    if allocation == "MARKET":
        head = (f"📈 MARKT — investiert: {int(round(SPY3X_WEIGHT*100))}% 3x-S&P500 "
                f"+ {int(round(BTC_WEIGHT*100))}% BTC")
    else:
        head = "💵 CASH — 100% Cash (nicht investiert)"

    lines = [
        head,
        f"({cooldown} Cooldown-Tage verbleibend)",
        "",
        "Entscheidungssignale (USD, auf 1x-Kursen):",
        (f"• US-TIPS:  {_fmt_pct(tips_st['diffPct']/100)}  "
         f"({'über' if tips_st['diffPct'] > 0 else 'unter'} SMA{TIPS_SMA})   "
         f"Stand: {_date_de(tips_st['currentDate'])}"),
        (f"• S&P 500: {_fmt_pct(spy_st['diffPct']/100)}  "
         f"({'über' if spy_st['diffPct'] > 0 else 'unter'} SMA{SPY_SMA})   "
         f"Stand: {_date_de(spy_st['currentDate'])}"),
        "",
        f"Regel: MARKT wenn US-TIPS > SMA{TIPS_SMA} UND S&P > SMA{SPY_SMA}, sonst Cash.",
    ]
    if btc_info is not None:
        lines += ["", f"BTC (nur Info): {btc_info['price']:,.0f} USD   "
                      f"Stand: {_date_de(btc_info['date'])}"]
    if data_stale:
        lines += ["", "⚠️ Hinweis: Kursdaten evtl. noch nicht vom letzten Handelstag "
                      "— Signal wird beim naechsten Lauf bestaetigt."]
    return "\n".join(lines)


# ==========================================================================
#  HAUPTFUNKTION
# ==========================================================================

def spy_tips_cool():
    # ---- Entscheidungsdaten (USD) laden, mit Wiederholung ----
    for i in range(TRY_COUNT):
        try:
            spy_usd = _download_history(SPY_USD_TICKER)
            tips_usd = _download_history(TIPS_USD_TICKER)
        except Exception as e:
            print(f"({i+1}/{TRY_COUNT}) Download-Fehler (USD): {e}")
            time.sleep(2); continue
        if spy_usd is None or tips_usd is None or spy_usd.empty or tips_usd.empty:
            print(f"({i+1}/{TRY_COUNT}) Leere USD-Signaldaten.")
            time.sleep(2); continue
        break
    else:
        return ("Error",
                "Konnte die USD-Signaldaten (^SP500TR / TIP) nicht laden.",
                "Bitte spaeter erneut versuchen.")

    spy_close = _prepare_close(spy_usd)
    tips_close = _prepare_close(tips_usd)
    A = _align_two(spy_close, tips_close)

    # ---- BTC nur als Info (nicht blockierend) ----
    btc_info = None
    try:
        btc_close = _prepare_close(_download_history(BTC_USD_TICKER))
        if not btc_close.empty:
            btc_info = {"price": float(btc_close.iloc[-1]),
                        "date": btc_close.index[-1].strftime("%Y-%m-%d")}
    except Exception as e:
        print(f"BTC-Infokurs nicht verfuegbar (ignoriert): {e}")

    # ---- Status/Frische (nur Entscheidungssignale zaehlen fuer needsRetry) ----
    spy_st = _build_signal_status("spy_usd", "S&P 500 (USD)", SPY_USD_TICKER,
                                  A["spy_close"], A["spy_sma"], A["spy_diff"])
    tips_st = _build_signal_status("tips_usd", "US-TIPS (USD)", TIPS_USD_TICKER,
                                   A["tips_close"], A["tips_sma"], A["tips_diff"])
    status = {
        "updated": pd.Timestamp.now(tz="Europe/Berlin").isoformat(),
        "strategy": (f"C: {int(round(SPY3X_WEIGHT*100))}% 3xSPY + {int(round(BTC_WEIGHT*100))}% BTC "
                     f"(USD-Signale, SPY-SMA{SPY_SMA}/TIPS-SMA{TIPS_SMA}, Freeze{COOLDOWN_DAYS})"),
        "signals": {"spy_usd": spy_st, "tips_usd": tips_st},
    }
    if btc_info is not None:
        status["btc_info"] = btc_info
    status["needsRetry"] = not (spy_st["fresh"] and tips_st["fresh"])
    _save_status(status)
    data_stale = status["needsRetry"]

    # ---- History fortschreiben ----
    fileName = f"{HISTORY_FILENAME}_{SPY_SMA}_{TIPS_SMA}_{COOLDOWN_DAYS}_USD.txt"

    valid = (~A["spy_diff"].isna()) & (~A["tips_diff"].isna())
    if not valid.any():
        return ("Error", None, "SMA-Berechnung fehlgeschlagen (nur NaN). Bitte spaeter erneut.")

    n = len(A["index"])
    last_entry = None

    if not os.path.exists(fileName):
        first_valid = int(np.argmax(valid.values))
        allocs, cds = compute_allocation_series(
            A["spy_diff"].iloc[first_valid:], A["tips_diff"].iloc[first_valid:])
        with open(fileName, "w") as f:
            for k in range(len(allocs)):
                _write_entry(f, A, first_valid + k, allocs[k], cds[k])
    else:
        with open(fileName, "r") as f:
            rows = f.readlines()
        last_entry = _parse_entry(rows[-1].split(","))

        if last_entry["date"] == str(A["index"][-1]):
            print("Heute bereits geprueft.")
            text = _build_message(last_entry["allocation"], last_entry["cooldown"],
                                  spy_st, tips_st, btc_info, data_stale)
            return "Daily Notification", None, text

        last_date = pd.to_datetime(last_entry["date"])
        new_pos = [j for j in range(n) if A["index"][j] > last_date and valid.iloc[j]]
        if not new_pos:
            print("Kein neuer gueltiger Handelstag nach letztem History-Eintrag.")
            text = _build_message(last_entry["allocation"], last_entry["cooldown"],
                                  spy_st, tips_st, btc_info, data_stale)
            return "Daily Notification", None, text

        prev_alloc = last_entry["allocation"]
        cooldown = last_entry["cooldown"]
        with open(fileName, "a") as f:
            for j in new_pos:
                prev_alloc, cooldown, _ = advance_allocation(
                    prev_alloc, cooldown, A["spy_diff"].iloc[j] > 0, A["tips_diff"].iloc[j] > 0)
                _write_entry(f, A, j, prev_alloc, cooldown)

    # ---- Ergebnis der letzten Zeile lesen ----
    with open(fileName, "r") as f:
        rows = f.readlines()
    new_entry = _parse_entry(rows[-1].split(","))
    allocation = new_entry["allocation"]

    # ---- Subject (nur bei echtem Wechsel) ----
    subject = ""
    if last_entry is not None:
        if allocation != last_entry["allocation"]:
            subject = {"MARKET": "REGIME CHANGED: GO MARKET NOW (60% 3xSPY + 40% BTC)",
                       "CASH": "REGIME CHANGED: GO IN CASH NOW"}.get(allocation, "")
    else:
        subject = {"MARKET": "GO MARKET NOW (60% 3xSPY + 40% BTC)",
                   "CASH": "GO IN CASH NOW"}.get(allocation, "")

    text = _build_message(allocation, new_entry["cooldown"],
                          spy_st, tips_st, btc_info, data_stale)

    if DAILY_NOTIFICATION and subject == "":
        subject = "Daily Notification"

    return subject, "", text
