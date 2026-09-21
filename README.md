# levSpyBits — UPDATE (nur EINE Datei)

Dein bestehender **levSpyBits-Bot** (vormals „SpyTips-Cool" / `letsgo-signalbot`)
bleibt komplett unverändert — bis auf **eine** Datei. Final gilt
**75 % 3x-S&P500 + 25 % 1x-BTC** (BTC nur im Markt-Regime, kein Buy&Hold).

**So einspielen:**
> Ersetze in deinem Repo die Datei `strategies/constants.py` durch die hier
> beiliegende. Geändert: `SPY3X_WEIGHT 0.70→0.75`, `BTC_WEIGHT 0.30→0.25`
> (plus Umbenennung im Kommentar auf levSpyBits). Sonst nichts.

Wenn du das Repo auf `levspybits-signalbot` umbenennst, passt es zur
Dashboard-Quelle (`levspybits-signalbot/main/letsgo_status.json`). Der übrige
Code (main.py, send_ntfy.py, Downloader, Workflow) ist geprüft — nicht anfassen.

**KEINE ANLAGEBERATUNG.**
