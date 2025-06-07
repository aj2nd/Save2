import os, sys, io, requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import vision

app = Flask(__name__)
vision_client = vision.ImageAnnotatorClient()

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    print("📥 Payload:", request.values.to_dict(), file=sys.stderr)
    sys.stderr.flush()

    resp = MessagingResponse()
    num_media = int(request.values.get("NumMedia", 0))

    if num_media > 0:
        media_url = request.values.get("MediaUrl0")
        sid, token = os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"]
        try:
            twr = requests.get(media_url, auth=(sid, token)); twr.raise_for_status()
            image = vision.Image(content=twr.content)
            docs = vision_client.text_detection(image=image).text_annotations
            if docs:
                resp.message(f"📝 Here’s what I read:\n\n{docs[0].description}")
            else:
                resp.message("⚠️ I couldn’t find any text in that image.")
        except Exception as e:
            resp.message(f"⚠️ Error processing image: {e}")
    else:
        # only this line changed:
        resp.message("🤖 Please send me an invoice image and I'll read it for you.")

    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
