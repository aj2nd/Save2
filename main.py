from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
from google.cloud import vision
import os

# Set Google Vision credentials (the mount path on Render)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/etc/secrets/sustained-spark-462115-v9-117f1dfb50a9.json"

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
        media_content = requests.get(media_url).content

        with open(filename, 'wb') as f:
            f.write(media_content)

            # ---- OCR code starts here ----
            try:
                client = vision.ImageAnnotatorClient()
                with open(filename, "rb") as image_file:
                    content = image_file.read()
                image = vision.Image(content=content)
                response = client.text_detection(image=image)
                texts = response.text_annotations

                if texts:
                    full_text = texts[0].description
                    reply.body("Invoice text extracted:\n" + full_text)
                else:
                    reply.body("Sorry, I couldn't read any text from your invoice.")
            except Exception as e:
                reply.body(f"Error processing invoice: {e}")
            # ---- OCR code ends here ----

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
    app.run(host="0.0.0.0", port=10000)
