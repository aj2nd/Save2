# main.py

import os
import sys
import io
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import vision

app = Flask(__name__)

# Initialize the Vision client (make sure GOOGLE_APPLICATION_CREDENTIALS is set)
vision_client = vision.ImageAnnotatorClient()

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    # Log the full incoming payload for debugging
    print("📥 Incoming payload:", request.values.to_dict(), file=sys.stderr)
    sys.stderr.flush()

    resp = MessagingResponse()
    num_media = int(request.values.get("NumMedia", 0))

    if num_media > 0:
        # 1) Grab the first media URL Twilio sent
        media_url = request.values.get("MediaUrl0")

        # 2) Fetch the image bytes from Twilio (authenticated)
        account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        auth_token  = os.environ["TWILIO_AUTH_TOKEN"]
        try:
            twilio_resp = requests.get(media_url, auth=(account_sid, auth_token))
            twilio_resp.raise_for_status()
            image_content = twilio_resp.content
        except Exception as e:
            resp.message(f"❌ Failed to download image: {e}")
            return str(resp)

        # 3) Send bytes to Google Vision for OCR
        try:
            image = vision.Image(content=image_content)
            vision_resp = vision_client.text_detection(image=image)
            annotations = vision_resp.text_annotations
            if annotations:
                extracted_text = annotations[0].description
                resp.message(f"📝 Here’s what Vision read:\n\n{extracted_text}")
            else:
                resp.message("⚠️ Vision returned no text.")
        except Exception as e:
            resp.message(f"⚠️ Vision API error: {e}")
    else:
        # Just echo back any incoming text
        body = request.values.get("Body", "").strip()
        resp.message(f"You said: {body}" if body else "🤖 (Send me an image to OCR.)")

    return str(resp)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
