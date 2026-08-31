import traceback
from strategies.spytips_cool import spy_tips_cool

try:
    from send_whatsapp import send_whatsapp
except Exception:
    def send_whatsapp(_msg):
        print("send_whatsapp module not available.")
        return False


def saveText(subject=None, subject2=None, text=None):
    if not subject and not subject2 and not text:
        return

    with open("message.txt", "w") as d:
        if subject:
            d.write(subject + "\n\n")

        if subject2:
            d.write(subject2 + "\n\n")

        if text:
            d.write(text)


def _is_invest_change(subject):
    """
    True nur bei einem echten Allokationswechsel (MARKET<->CASH).
    Nicht bei taeglicher Notification, leerem Subject oder Fehler.
    """
    if not subject:
        return False
    if subject in ("Daily Notification", "Error"):
        return False
    # Wechsel-Subjects: "REGIME CHANGED: ..." oder Erst-Signal "GO ... NOW"
    return ("REGIME CHANGED" in subject) or subject.startswith("GO ")


def main():
    s, s2, t = spy_tips_cool()

    if s is None and s2 is None and t is None:
        print("Skipped")
        return

    saveText(s, s2, t)

    # WhatsApp NUR bei echtem Invest-Change
    if _is_invest_change(s):
        wa_message = s
        if t:
            wa_message += "\n\n" + t
        # Discord-Flow wird durch WhatsApp-Fehler nie gestoert:
        try:
            send_whatsapp(wa_message)
        except Exception as e:
            print(f"WhatsApp send raised (ignored): {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error = "".join(traceback.format_exception(e))
        saveText("Error", None, error)
