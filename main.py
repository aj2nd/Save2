import os, sys, requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import vision

# Initialize Flask app and Google Vision client
app = Flask(__name__)
vision_client = vision.ImageAnnotatorClient()

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    try:
        # Logging incoming payload
        payload = request.values.to_dict()
        print("📥 Incoming Payload:", payload, file=sys.stderr)
        sys.stderr.flush()

        resp = MessagingResponse()
        num_media = int(request.values.get("NumMedia", 0))
        body = request.values.get("Body", "").strip()

        # Case 1: Image received
        if num_media > 0:
            media_url = request.values["MediaUrl0"]
            print(f"📸 Media received: {media_url}", file=sys.stderr)

            # Auth credentials for Twilio to download image
            sid = os.environ.get("TWILIO_ACCOUNT_SID")
            token = os.environ.get("TWILIO_AUTH_TOKEN")

            if not sid or not token:
                resp.message("⚠️ Missing Twilio credentials.")
                return str(resp)

            # Download and OCR the image
            try:
                image_response = requests.get(media_url, auth=(sid, token))
                image_response.raise_for_status()

                image = vision.Image(content=image_response.content)
                result = vision_client.text_detection(image=image)
                annotations = result.text_annotations

                if annotations:
                    detected_text = annotations[0].description.strip()
                    print(f"📄 OCR Text: {detected_text}", file=sys.stderr)
                    resp.message(f"📝 Here's what I read:\n\n{detected_text}")
                else:
                    resp.message("🤔 I couldn't detect any text in the image.")

            except Exception as img_error:
                print(f"❌ Error processing image: {img_error}", file=sys.stderr)
                resp.message("⚠️ Error reading the image. Make sure it's clear and try again.")

        # Case 2: Text message like "hi", "hello"
        elif body.lower() in ["hi", "hello", "hey", "hola", "yo"]:
            resp.message("👋 Hey there! Send me an invoice image and I’ll read it for you.")

        # Case 3: Any other message
        elif body:
            resp.message(f"You said: {body}")

        # Case 4: Nothing sent
        else:
            resp.message("🤖 Please send me a message or an invoice image to get started.")

        return str(resp)

    except Exception as e:
        # Catch any global error and respond
        print(f"🔥 FATAL ERROR: {e}", file=sys.stderr)
        sys.stderr.flush()
        return str(MessagingResponse().message("⚠️ Something went wrong. Try again shortly."))

# Flask entry point
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
