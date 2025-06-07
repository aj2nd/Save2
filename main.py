import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/etc/secrets/google-sa.json"

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import vision
import requests

# Twilio creds from Render env
TWILIO_SID   = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]

app    = Flask(__name__)
client = vision.ImageAnnotatorClient()

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming = request.values.get("Body", "").lower()
    num_media = int(request.values.get("NumMedia", "0"))
    resp = MessagingResponse()
    msg  = resp.message()

    if num_media > 0:
        media_url  = request.values["MediaUrl0"]
        media_type = request.values["MediaContentType0"]
        ext        = media_type.split("/")[-1]
        filename   = f"invoice.{ext}"

        # fetch with Twilio auth
        r = requests.get(media_url, auth=(TWILIO_SID, TWILIO_TOKEN))
        r.raise_for_status()
        with open(filename, "wb") as f:
            f.write(r.content)

        # OCR
        with open(filename, "rb") as img_f:
            image = vision.Image(content=img_f.read())
        o = client.text_detection(image=image)

        if o.text_annotations:
            txt = o.text_annotations[0].description
            msg.body("Here’s your invoice text:\n" + txt)
        else:
            msg.body("Sorry, I couldn't read any text from your invoice.")
    elif "invoice" in incoming:
        msg.body("Send me your invoice image or PDF as a document and I’ll read it.")
    elif incoming.startswith(("hi","hello")):
        msg.body("Hi there! 👋 Send me an invoice and I'll OCR it for you.")
    else:
        msg.body("I didn’t understand — send ‘invoice’ to start.")

    return str(resp), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
