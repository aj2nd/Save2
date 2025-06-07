import os
import logging
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
from google.cloud import vision

# turn on debug logging
logging.basicConfig(level=logging.INFO)

# The path to your service‐account JSON is provided by Render as an env var:
# GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/<your‐filename>.json
# So we don’t need to reassign it here—just rely on the SDK finding it.

# initialize the Vision client
client = vision.ImageAnnotatorClient()

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming = request.values.get("Body", "").strip().lower()
    num_media = int(request.values.get("NumMedia", 0))
    resp = MessagingResponse()
    msg = resp.message()

    if num_media > 0:
        # grab the first attachment
        media_url  = request.values.get("MediaUrl0")
        media_type = request.values.get("MediaContentType0", "")
        ext = media_type.split("/")[-1] or "jpg"
        filename = f"invoice.{ext}"

        try:
            # download it
            data = requests.get(media_url).content
            with open(filename, "wb") as f:
                f.write(data)
            logging.info(f"Saved {filename}, size {len(data)} bytes")

            # run OCR
            with open(filename, "rb") as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            ocr = client.text_detection(image=image)

            if ocr.error.message:
                raise RuntimeError(ocr.error.message)

            texts = ocr.text_annotations
            if texts:
                full_text = texts[0].description
                msg.body("Here’s your invoice text:\n\n" + full_text)
            else:
                msg.body("Sorry, I couldn't read any text from your invoice.")

        except Exception as e:
            logging.exception("OCR failed")
            msg.body(f"Error processing invoice: {e}")

    elif "invoice" in incoming:
        msg.body("Sure—please send your invoice as a document or clear image, and I'll extract the text for you.")
    elif incoming.startswith(("hi","hello")):
        msg.body("Hi there! 👋 I'm SaveAi—your smart cost-saving assistant. Send me an invoice to get started.")
    else:
        msg.body("I can scan invoices for you. Try sending the word `invoice` or just upload a picture.")

    return str(resp), 200

if __name__ == "__main__":
    # Render gives us PORT via env; default to 3000 locally
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
