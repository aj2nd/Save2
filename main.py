import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/etc/secrets/google-sa.json"

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
from google.cloud import vision

app = Flask(__name__)
client = vision.ImageAnnotatorClient()

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming = request.values.get("Body", "").lower()
    num_media = int(request.values.get("NumMedia", 0))
    resp = MessagingResponse()
    reply = resp.message()

    if num_media > 0:
        # download the image
        url = request.values.get("MediaUrl0")
        ext = request.values.get("MediaContentType0").split("/")[-1]
        fn = f"invoice.{ext}"
        content = requests.get(url).content
        with open(fn, "wb") as f:
            f.write(content)

        # OCR it
        with open(fn, "rb") as img_f:
            image = vision.Image(content=img_f.read())
        ocr = client.text_detection(image=image)
        if ocr.text_annotations:
            txt = ocr.text_annotations[0].description
            reply.body("Here’s your invoice text:\n" + txt)
        else:
            reply.body("Sorry, I couldn't read any text from your invoice.")
    elif "invoice" in incoming:
        reply.body("Sure—send me your invoice image and I'll read it.")
    elif incoming.startswith(("hi", "hello")):
        reply.body("Hi there! 👋 Send me an invoice or ask me to scan expenses.")
    else:
        reply.body("I didn't get that—send ‘invoice’ to start.")

    return str(resp), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
