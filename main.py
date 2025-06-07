# main.py

import os
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import vision

from model import parse_invoice_text  # ← separate parser

# ─── CONFIG ──────────────────────────────────────────────────────────

# Twilio creds (set these in Render as ENV vars)
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN  = os.environ["TWILIO_AUTH_TOKEN"]

# Google Vision creds (mount JSON & set this path in Render ENV)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ[
    "GOOGLE_APPLICATION_CREDENTIALS"
]

vision_client = vision.ImageAnnotatorClient()

# ─── FLASK / WHATSAPP ────────────────────────────────────────────────

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    resp  = MessagingResponse()
    reply = resp.message()

    num_media = int(request.values.get("NumMedia", 0))
    if num_media > 0:
        # Download image
        url  = request.values["MediaUrl0"]
        ctype= request.values["MediaContentType0"]
        ext  = ctype.split("/")[-1]
        fname= f"invoice.{ext}"
        data = requests.get(url).content
        with open(fname, "wb") as f:
            f.write(data)

        # OCR
        img = vision.Image(content=data)
        result = vision_client.text_detection(image=img)
        if result.error.code:
            reply.body(f"Error: {result.error.message}")
        else:
            raw = result.text_annotations and result.text_annotations[0].description
            if not raw:
                reply.body("Sorry, I couldn't read any text from your invoice.")
            else:
                inv = parse_invoice_text(raw)
                reply.body(
                    f"✅ Parsed invoice:\n"
                    f"No: {inv.invoice_no}\n"
                    f"Date: {inv.date}\n"
                    f"Vendor: {inv.vendor}\n"
                    f"Total: {inv.total:.2f}"
                )
    else:
        txt = request.values.get("Body", "").strip().lower()
        if "invoice" in txt:
            reply.body("Please send me your invoice image or PDF.")
        elif txt in ("hi","hello"):
            reply.body("👋 Send an invoice and I'll pull out the key details.")
        else:
            reply.body("Send 'invoice' to get started.")

    return str(resp), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
