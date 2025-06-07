import os
import sys
import io
import re
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import vision

app = Flask(__name__)
vision_client = vision.ImageAnnotatorClient()

def parse_invoice_details(text):
    """
    Given the full OCR text of an invoice, extract:
      - vat_rate  (e.g. 5.0)
      - total_due (float)
    Then compute:
      - subtotal = total_due / (1 + vat_rate/100)
      - vat_amount = total_due - subtotal
    Returns a dict or None if parsing fails.
    """
    # 1) VAT rate
    vat_m = re.search(r"VAT\s*@\s*([\d\.]+)%", text, re.IGNORECASE)
    vat_rate = float(vat_m.group(1)) if vat_m else 0.0

    # 2) Total Amount Due
    tot_m = re.search(
        r"Total\s*Amount\s*Due\s*[:\-]?\s*\$?([\d,\.]+)",
        text, re.IGNORECASE
    )
    if not tot_m:
        tot_m = re.search(r"Total\s*[:\-]?\s*\$?([\d,\.]+)", text, re.IGNORECASE)
    if not tot_m:
        return None

    total_due = float(tot_m.group(1).replace(",", ""))

    # 3) Compute subtotal & VAT amount
    if vat_rate > 0:
        subtotal   = total_due / (1 + vat_rate/100)
        vat_amount = total_due - subtotal
    else:
        subtotal, vat_amount = total_due, 0.0

    return {
        "vat_rate":   vat_rate,
        "subtotal":   subtotal,
        "vat_amount": vat_amount,
        "total_due":  total_due
    }

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    # — Debug: log the incoming Twilio payload
    print("📥 Payload:", request.values.to_dict(), file=sys.stderr)
    sys.stderr.flush()

    resp      = MessagingResponse()
    num_media = int(request.values.get("NumMedia", 0))
    body      = request.values.get("Body", "").strip().lower()

    # === IMAGE CASE: OCR + invoice parsing ===
    if num_media > 0:
        media_url = request.values.get("MediaUrl0")
        sid, token = (
            os.environ["TWILIO_ACCOUNT_SID"],
            os.environ["TWILIO_AUTH_TOKEN"]
        )

        try:
            # download the image from Twilio
            twr = requests.get(media_url, auth=(sid, token))
            twr.raise_for_status()
            content = twr.content

            # send to Google Vision
            img    = vision.Image(content=content)
            vresp  = vision_client.text_detection(image=img)
            anns   = vresp.text_annotations

            if not anns:
                resp.message("⚠️ I couldn’t detect any text in that image.")
            else:
                ocr_text = anns[0].description

                # try to parse it as an invoice
                details = parse_invoice_details(ocr_text)
                if details:
                    resp.message(
                        f"🧾 *Invoice Summary* 🧾\n"
                        f"• Subtotal:   ${details['subtotal']:.2f}\n"
                        f"• VAT @ {details['vat_rate']:.1f}%:   ${details['vat_amount']:.2f}\n"
                        f"• *Total Due*: ${details['total_due']:.2f}"
                    )
                else:
                    # fallback: just show raw OCR
                    resp.message(f"📝 I read:\n\n{ocr_text}")

        except Exception as e:
            resp.message(f"⚠️ Image processing error: {e}")

    # === GREETINGS ===
    elif body in ("hi", "hello", "hey", "hola", "yo"):
        resp.message("👋 Hey there! Send me an invoice image and I'll give you a summary.")

    # === OTHER TEXT ===
    elif body:
        resp.message(f"You said: {body}")

    # === NOTHING/UNKNOWN ===
    else:
        resp.message("🤖 Please send me an invoice image and I'll extract the numbers for you.")

    return str(resp)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
