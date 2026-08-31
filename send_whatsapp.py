"""
WhatsApp-Benachrichtigung fuer LetsGO Signal-Bot.
Wird NUR bei einem echten Invest-Change (Allokationswechsel) aufgerufen.

Zwei Wege (per Umgebungsvariablen / GitHub Secrets gesteuert):

  Option A -- CallMeBot (kostenlos, einfach):
      Secrets:  WHATSAPP_PHONE   (z.B. 4915112345678, ohne + und ohne Leerzeichen)
                CALLMEBOT_APIKEY (bekommst du beim CallMeBot-Setup)
      Setup: Fuege +34 644 51 95 23 als WhatsApp-Kontakt hinzu und sende
             "I allow callmebot to send me messages" -> du bekommst deinen apikey.

  Option B -- Meta WhatsApp Cloud API (offiziell, mehr Setup):
      Secrets:  WA_CLOUD_TOKEN, WA_CLOUD_PHONE_ID, WA_CLOUD_TO
      (unten auskommentiert; aktivieren wenn du den offiziellen Weg gehst)
"""

import os
import urllib.parse
import urllib.request
import json


def send_whatsapp(message):
    """Versucht WhatsApp zu senden. Gibt True/False zurueck. Wirft NIE."""
    # ---- Option A: CallMeBot ----
    phone = os.environ.get("WHATSAPP_PHONE")
    apikey = os.environ.get("CALLMEBOT_APIKEY")
    if phone and apikey:
        try:
            text = urllib.parse.quote(message)
            url = (
                f"https://api.callmebot.com/whatsapp.php?"
                f"phone={phone}&text={text}&apikey={apikey}"
            )
            with urllib.request.urlopen(url, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
            print(f"CallMeBot response: {body[:200]}")
            return True
        except Exception as e:
            print(f"CallMeBot failed: {e}")
            # faellt weiter zu Option B durch

    # ---- Option B: Meta WhatsApp Cloud API (auskommentiert) ----
    # token = os.environ.get("WA_CLOUD_TOKEN")
    # phone_id = os.environ.get("WA_CLOUD_PHONE_ID")
    # to = os.environ.get("WA_CLOUD_TO")
    # if token and phone_id and to:
    #     try:
    #         url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    #         payload = json.dumps({
    #             "messaging_product": "whatsapp",
    #             "to": to,
    #             "type": "text",
    #             "text": {"body": message},
    #         }).encode("utf-8")
    #         req = urllib.request.Request(url, data=payload, method="POST")
    #         req.add_header("Authorization", f"Bearer {token}")
    #         req.add_header("Content-Type", "application/json")
    #         with urllib.request.urlopen(req, timeout=30) as resp:
    #             print(f"WA Cloud response: {resp.read().decode()[:200]}")
    #         return True
    #     except Exception as e:
    #         print(f"WA Cloud API failed: {e}")

    print("No WhatsApp credentials configured (skipping WhatsApp).")
    return False


if __name__ == "__main__":
    # Manueller Test
    send_whatsapp("LetsGO Test-Nachricht ✅")
