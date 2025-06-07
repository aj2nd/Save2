import os
import logging

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
from google.cloud import vision

# ————— CONFIGURE LOGGING —————
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ————— READ CREDS FROM ENV —————
# (in Render: Add env-vars TWILIO_ACCOUNT_SID & TWILIO_AUTH_TOKEN)
TWILIO_SID   = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# GOOGLE_APPLICATION_CREDENTIALS should already point at your mounted JSON

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    resp = MessagingResponse()
    reply = resp.message()

    try:
        incoming = request.values.get("Body", "").strip().lower()
        num_media = int(request.values.get("NumMedia", 0))
        logging.info(f"Received msg='{incoming}', NumMedia={num_media}")

        if num_media > 0:
            # 1) Pull down the image with Twilio credentials
            media_url  = request.values.get("MediaUrl0")
            media_type = request.values.get("MediaContentType0", "")
            ext        = media_type.split("/")[-1] or "jpg"
            filename   = f"invoice.{ext}"

            logging.info(f"Fetching media at {media_url}")
            r = requests.get(media_url, auth=(TWILIO_SID, TWILIO_TOKEN))
            if r.status_code != 200:
                logging.error(f"Media fetch failed: {r.status_code}")
                reply.body("Error fetching your invoice image.")
                return str(resp), 200

            content = r.content
            logging.info(f"Downloaded {len(content)} bytes, saving to {filename}")
            with open(filename, "wb") as f:
                f.write(content)

            # 2) OCR it via Vision
            client   = vision.ImageAnnotatorClient()
            image    = vision.Image(content=content)
            ocr_resp = client.text_detection(image=image)

            if ocr_resp.error.message:
                logging.error(f"OCR failed: {ocr_resp.error.message}")
                reply.body(f"Error processing invoice: {ocr_resp.error.message}")
            else:
                texts = ocr_resp.text_annotations
                if texts:
                    full_text = texts[0].description
                    reply.body("Here’s your invoice text:\n\n" + full_text)
                else:
                    reply.body("Sorry, I couldn’t read any text from your invoice.")

        elif "invoice" in incoming:
            reply.body("Sure—please upload your invoice image and I’ll extract the text for you.")
        else:
            reply.body("Hi there! 👋 Send ‘invoice’ to get started or just say hi!")

    except Exception:
        logging.exception("Unexpected error in /whatsapp")
        reply.body("Oops—something went wrong. Please try again in a moment.")

    return str(resp), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    logging.info(f"Starting on port {port}")
    app.run(host="0.0.0.0", port=port)
