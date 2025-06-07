import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
from requests.auth import HTTPBasicAuth
from google.cloud import vision

# Set credentials for Google Vision
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/etc/secrets/sustained-spark-462115-v9-117f1dfb50a9.json"

# Twilio credentials (set these as environment variables in Render)
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

app = Flask(__name__)

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').lower()
    num_media = int(request.values.get('NumMedia', 0))
    resp = MessagingResponse()
    reply = resp.message()

    if num_media > 0:
        media_url = request.values.get('MediaUrl0')
        media_type = request.values.get('MediaContentType0')
        file_extension = media_type.split('/')[-1]
        filename = f"invoice.{file_extension}"

        # Download with Twilio Auth
        response = requests.get(
            media_url,
            auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            stream=True
        )
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            file_size = os.path.getsize(filename)
            print(f"DEBUG: Saved {filename} with size: {file_size} bytes")
        else:
            reply.body("Error downloading the invoice image. Try again.")
            return str(resp), 200

        try:
            client = vision.ImageAnnotatorClient()
            with open(filename, "rb") as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            # Use document_text_detection for invoices
            response = client.document_text_detection(image=image)
            texts = response.text_annotations

            if texts:
                full_text = texts[0].description
                reply.body("Invoice text extracted:\n" + full_text)
            else:
                reply.body("Sorry, I couldn't read any text from your invoice.")
        except Exception as e:
            reply.body(f"Error processing invoice: {e}")
    elif 'invoice' in incoming_msg:
        reply.body("Sure! Please upload your invoice and I'll analyze it for you.")
    elif 'hello' in incoming_msg or 'hi' in incoming_msg:
        reply.body("Hi there! 👋 I'm SaveAi — your smart cost-saving assistant. Send me an invoice or ask me to scan expenses.")
    elif incoming_msg.startswith("how much"):
        reply.body("SaveAI: Let me fetch your data and get back to you.")
    else:
        reply.body("I'm here to help you save money. Send me a keyword like 'invoice' or say 'hi' to begin.")

    return str(resp), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
