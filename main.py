import os
import logging
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from google.cloud import vision

# ——— SET UP LOGGING ———
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# ——— GOOGLE VISION CLIENT ———
# Render will set GOOGLE_APPLICATION_CREDENTIALS to "/etc/secrets/your-file.json"
# The client library reads that automatically—no need to override it in code.
vision_client = vision.ImageAnnotatorClient()

# ——— TWILIO CLIENT ———
twilio_sid   = os.environ["TWILIO_ACCOUNT_SID"]
twilio_token = os.environ["TWILIO_AUTH_TOKEN"]
twilio_client = Client(twilio_sid, twilio_token)

# ——— FLASK APP ———
app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming = request.values.get("Body", "").lower()
    num_media = int(request.values.get("NumMedia", 0))
    resp = MessagingResponse()
    msg  = resp.message()

    if num_media > 0:
        # download the first attachment
        url  = request.values["MediaUrl0"]
        mtype = request.values["MediaContentType0"].split("/")[-1]
        fname = f"invoice.{mtype}"
        content = requests.get(url).content

        with open(fname, "wb") as f:
            f.write(content)
        log.debug(f"Saved {fname} ({len(content)} bytes)")

        # send to Vision API
        with open(fname, "rb") as image_file:
            image = vision.Image(content=image_file.read())

        ocr_resp = vision_client.text_detection(image=image)
        log.debug("==== FULL OCR RESPONSE ====\n%s\n==== END OCR ====", ocr_resp)

        if ocr_resp.error.message:
            log.error("VISION ERROR: %s", ocr_resp.error)
            msg.body("Error processing invoice: " + ocr_resp.error.message)
        elif ocr_resp.text_annotations:
            text = ocr_resp.text_annotations[0].description
            msg.body("Invoice text extracted:\n" + text)
        else:
            msg.body("Sorry, I couldn't read any text from your invoice.")
    else:
        # no media → keyword based
        if "invoice" in incoming:
            msg.body("Sure! Please upload your invoice as an attachment.")
        elif incoming.startswith(("hi","hello")):
            msg.body("Hi there! 👋 Send me an invoice and I'll scan it for you.")
        else:
            msg.body("I'm SaveAi — send me an invoice image and I'll extract the text for you.")

    return str(resp), 200

if __name__ == "__main__":
    # Render listens on $PORT (default 10000)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
