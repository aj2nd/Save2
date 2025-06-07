# main.py

import os, sys, io, requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import vision

app = Flask(__name__)

# Make sure GOOGLE_APPLICATION_CREDENTIALS is set to your JSON key
vision_client = vision.ImageAnnotatorClient()

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    # 1) DEBUG: dump incoming payload to your logs
    print("📥 Payload:", request.values.to_dict(), file=sys.stderr)
    sys.stderr.flush()

    resp = MessagingResponse()
    num_media = int(request.values.get("NumMedia", 0))
    body      = request.values.get("Body", "").strip()

    # 2) IMAGE CASE
    if num_media > 0:
        media_url = request.values.get("MediaUrl0")
        sid, token = os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"]
        try:
            # fetch bytes from Twilio
            twr = requests.get(media_url, auth=(sid, token))
            twr.raise_for_status()
            content = twr.content

            # send to Vision API
            img    = vision.Image(content=content)
            vresp  = vision_client.text_detection(image=img)
            anns   = vresp.text_annotations

            if anns:
                resp.message(f"📝 Here’s what I read:\n\n{anns[0].description}")
            else:
                resp.message("⚠️ I couldn’t detect any text in that image.")
        except Exception as e:
            resp.message(f"⚠️ Image processing error: {e}")

    # 3) GREETINGS
    elif body.lower() in ["hi", "hello", "hey", "hola", "yo"]:
        resp.message("👋 Hey there! Send me an invoice image and I'll read it for you.")

    # 4) ANY OTHER TEXT
    elif body:
        resp.message(f"You said: {body}")

    # 5) NOTHING / UNKNOWN
    else:
        resp.message("🤖 Please send me an invoice image and I'll extract the text for you.")

    return str(resp)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
