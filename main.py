import traceback
from strategies.spytips_cool import spy_tips_cool

try:
    from send_ntfy import send_ntfy
except Exception:
    def send_ntfy(_title, _msg):
        print("send_ntfy module not available.")
        return False


def saveText(text):
    """Schreibt die fertige Nachricht (bereits inkl. Buy/Sell-Kopf) nach message.txt."""
    if not text:
        return
    with open("message.txt", "w") as d:
        d.write(text)


def main():
    # signal: None (nur Status), "MARKET"/"CASH" (echter Wechsel heute), "Error"
    signal, _unused, text = spy_tips_cool()

    if text is None:
        print("Skipped")
        return

    saveText(text)

    # ntfy NUR bei echtem Signalwechsel (Buy/Sell). Kein Push bei Daily/Fehler.
    if signal in ("MARKET", "CASH"):
        title = "LetsGO: BUY - GO IN MARKET" if signal == "MARKET" else "LetsGO: SELL - GO IN CASH"
        try:
            send_ntfy(title, text)
        except Exception as e:
            # Discord-Flow darf durch ntfy-Fehler nie gestoert werden:
            print(f"ntfy send raised (ignored): {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error = "".join(traceback.format_exception(e))
        saveText("Error\n\n" + error)
