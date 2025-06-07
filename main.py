import os, sys, io, re, requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import vision
import dateparser

app = Flask(__name__)
vision_client = vision.ImageAnnotatorClient()

def extract_invoice_data(text):
    lines = text.split("\n")
    result = {}

    for line in lines:
        l = line.lower()

        if 'invoice' in l and 'no' in l:
            result['Invoice No'] = line.strip()

        elif any(word in l for word in ['gst', 'tax']) and '₹' in l:
            result['GST'] = line.strip()

        elif 'total' in l or 'amount' in l:
            amt = re.findall(r'₹\s?[\d,]+', line)
            if amt:
                result['Total Amount'] = amt[0].strip()

        elif not result.get('Date'):
            parsed_date = dateparser.parse(line, settings={"PREFER_DATES_FROM": "past"})
            if parsed_date:
                result['Date'] = parsed_date.strftime("%Y-%m-%d")

    return result

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    print("📥 Payload:", request.values.to_dict(), file=sys.stderr)
    sys.stderr.flush()

    resp = MessagingResponse()
    num_media = int(request.values.get("NumMedia", 0))
    body = request.values.get("Body", "").strip()

    if num_media > 0:
        media_url = request.values["MediaUrl0"]
        sid, token = os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"]

        try:
            twr = requests.get(media_url, auth=(sid, token))
            twr.raise_for_status()
            img = vision.Image(content=twr.content)
            anns = vision_client.text_detection(image=img).text_annotations

            if anns:
                raw_text = anns[0].description
                parsed = extract_invoice_data(raw_text)
                pretty = "\n".join([f"{k}: {v}" for k, v in parsed.items()])
                if pretty:
                    resp.message(f"🧾 Here's what I found:\n\n{pretty}")
                else:
                    resp.message(f"📝 Raw OCR result:\n\n{raw_text}")
            else:
                resp.message("⚠️ I couldn’t detect any text in that image.")

        except Exception as e:
            resp.message(f"⚠️ Image processing error: {e}")

    elif body.lower() in ["hi", "hello", "hey", "hola", "yo"]:
        resp.message("👋 Hey! Send me a photo of an invoice or bill and I’ll extract the data for you.")

    elif body:
        resp.message(f"🤖 You said: {body}")

    else:
        resp.message("📷 Please send me an invoice image and I'll read it for you.")

    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
