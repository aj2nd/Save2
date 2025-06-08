import os, sys, requests, re, json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import vision
from datetime import datetime, timedelta
import dateparser

# Initialize Flask app and Google Vision client
app = Flask(__name__)
vision_client = vision.ImageAnnotatorClient()

# UAE-specific accounting categories
UAE_EXPENSE_CATEGORIES = {
    "medical_supplies": ["syringe", "gloves", "mask", "bandage", "medicine", "pharmaceutical"],
    "office_rent": ["rent", "lease", "property", "office space"],
    "utilities": ["electricity", "water", "internet", "telephone", "wifi", "etisalat", "du"],
    "equipment": ["equipment", "machine", "computer", "printer", "medical device"],
    "insurance": ["insurance", "takaful", "medical insurance"],
    "licenses": ["license", "permit", "dha", "doh", "mohap", "trade license"],
    "professional_fees": ["consultation", "audit", "legal", "accounting", "ca fees"],
    "marketing": ["advertisement", "marketing", "social media", "website"],
    "transportation": ["taxi", "uber", "careem", "fuel", "parking", "salik"],
    "meals": ["restaurant", "food", "lunch", "dinner", "catering"]
}

# Common UAE vendors/suppliers
UAE_VENDORS = [
    "emirates nbd", "adcb", "fab", "mashreq", "cbd", "rakbank",
    "etisalat", "du", "dewa", "addc", "sewa", "fewa",
    "carrefour", "lulu", "spinneys", "waitrose", "union coop"
]

class AccountingIntelligence:
    def __init__(self):
        self.confidence_threshold = 0.8
    
    def extract_invoice_data(self, ocr_text):
        """Extract structured data from OCR text"""
        data = {
            "raw_text": ocr_text,
            "amount": self.extract_amount(ocr_text),
            "date": self.extract_date(ocr_text),
            "vendor": self.extract_vendor(ocr_text),
            "category": self.categorize_expense(ocr_text),
            "vat_amount": self.extract_vat(ocr_text),
            "confidence": 0.0,
            "needs_review": False
        }
        
        # Calculate confidence score
        data["confidence"] = self.calculate_confidence(data)
        data["needs_review"] = data["confidence"] < self.confidence_threshold
        
        return data
    
    def extract_amount(self, text):
        """Extract monetary amounts in AED"""
        # Look for AED amounts
        aed_patterns = [
            r'AED\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*AED',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*د\.إ',
            r'Total[:\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Amount[:\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in aed_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return None
    
    def extract_vat(self, text):
        """Extract VAT amount (5% in UAE)"""
        vat_patterns = [
            r'VAT[:\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Tax[:\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'5%[:\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vat_str = match.group(1).replace(',', '')
                try:
                    return float(vat_str)
                except ValueError:
                    continue
        return None
    
    def extract_date(self, text):
        """Extract date from invoice"""
        # Common date patterns in UAE invoices
        date_patterns = [
            r'Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Invoice Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed_date = dateparser.parse(date_str)
                if parsed_date:
                    return parsed_date.strftime('%Y-%m-%d')
        
        return datetime.now().strftime('%Y-%m-%d')  # Default to today
    
    def extract_vendor(self, text):
        """Identify vendor from text"""
        text_lower = text.lower()
        
        # Check against known UAE vendors
        for vendor in UAE_VENDORS:
            if vendor in text_lower:
                return vendor.title()
        
        # Extract from common invoice patterns
        vendor_patterns = [
            r'From[:\s]*([A-Za-z\s&]+)',
            r'Vendor[:\s]*([A-Za-z\s&]+)',
            r'Company[:\s]*([A-Za-z\s&]+)'
        ]
        
        for pattern in vendor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vendor = match.group(1).strip()
                if len(vendor) > 2:
                    return vendor.title()
        
        return "Unknown Vendor"
    
    def categorize_expense(self, text):
        """Categorize expense based on content"""
        text_lower = text.lower()
        
        # Score each category
        category_scores = {}
        for category, keywords in UAE_EXPENSE_CATEGORIES.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return best_category.replace('_', ' ').title()
        
        return "General Expense"
    
    def calculate_confidence(self, data):
        """Calculate confidence score for the extracted data"""
        score = 0.0
        
        # Amount extraction (most important)
        if data["amount"]:
            score += 0.4
        
        # Date extraction
        if data["date"]:
            score += 0.2
        
        # Vendor identification
        if data["vendor"] != "Unknown Vendor":
            score += 0.2
        
        # Category classification
        if data["category"] != "General Expense":
            score += 0.1
        
        # VAT extraction (bonus for UAE compliance)
        if data["vat_amount"]:
            score += 0.1
        
        return min(score, 1.0)
    
    def format_summary(self, data):
        """Format extracted data into readable summary"""
        summary = "📊 *Invoice Analysis*\n\n"
        
        if data["amount"]:
            summary += f"💰 Amount: AED {data['amount']:.2f}\n"
        
        if data["vat_amount"]:
            summary += f"🏛️ VAT (5%): AED {data['vat_amount']:.2f}\n"
        
        summary += f"📅 Date: {data['date']}\n"
        summary += f"🏪 Vendor: {data['vendor']}\n"
        summary += f"📂 Category: {data['category']}\n"
        summary += f"✅ Confidence: {data['confidence']*100:.0f}%\n"
        
        if data["needs_review"]:
            summary += "\n⚠️ *Needs Review* - Low confidence score\n"
            summary += "I'll forward this to our CA team for verification."
        else:
            summary += "\n✅ *Auto-processed* - High confidence\n"
            summary += "This expense has been recorded automatically."
        
        return summary

# Initialize accounting intelligence
ai = AccountingIntelligence()

# Simple in-memory storage (replace with database in production)
user_sessions = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    try:
        # Logging incoming payload
        payload = request.values.to_dict()
        print("📥 Incoming Payload:", payload, file=sys.stderr)
        sys.stderr.flush()

        resp = MessagingResponse()
        from_number = request.values.get("From", "")
        num_media = int(request.values.get("NumMedia", 0))
        body = request.values.get("Body", "").strip()

        # Initialize user session
        if from_number not in user_sessions:
            user_sessions[from_number] = {"expenses": [], "last_activity": datetime.now()}

        # Case 1: Invoice/Receipt Image received
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
                    
                    # Process with accounting intelligence
                    invoice_data = ai.extract_invoice_data(detected_text)
                    
                    # Store the expense
                    user_sessions[from_number]["expenses"].append({
                        **invoice_data,
                        "timestamp": datetime.now().isoformat(),
                        "processed": not invoice_data["needs_review"]
                    })
                    
                    # Send formatted response
                    summary = ai.format_summary(invoice_data)
                    resp.message(summary)
                    
                    # If needs review, simulate CA handoff
                    if invoice_data["needs_review"]:
                        resp.message("👨‍💼 A certified accountant will review this within 2 hours and get back to you.")
                
                else:
                    resp.message("🤔 I couldn't detect any text in the image. Please make sure the image is clear and try again.")

            except Exception as img_error:
                print(f"❌ Error processing image: {img_error}", file=sys.stderr)
                resp.message("⚠️ Error reading the image. Make sure it's clear and try again.")

        # Case 2: Commands
        elif body.lower() in ["report", "summary", "total"]:
            user_data = user_sessions[from_number]
            if user_data["expenses"]:
                total_amount = sum(exp.get("amount", 0) for exp in user_data["expenses"] if exp.get("amount"))
                total_vat = sum(exp.get("vat_amount", 0) for exp in user_data["expenses"] if exp.get("vat_amount"))
                processed_count = sum(1 for exp in user_data["expenses"] if exp.get("processed"))
                pending_count = len(user_data["expenses"]) - processed_count
                
                report = f"📈 *Monthly Summary*\n\n"
                report += f"💰 Total Expenses: AED {total_amount:.2f}\n"
                report += f"🏛️ Total VAT: AED {total_vat:.2f}\n"
                report += f"✅ Processed: {processed_count}\n"
                report += f"⏳ Pending Review: {pending_count}\n"
                
                resp.message(report)
            else:
                resp.message("📊 No expenses recorded yet. Send me some invoice images to get started!")

        # Case 3: Greetings
        elif body.lower() in ["hi", "hello", "hey", "hola", "yo", "start"]:
            welcome_msg = "👋 *Welcome to SaveAI!*\n\n"
            welcome_msg += "🤖 I'm your AI accountant for UAE healthcare practices.\n\n"
            welcome_msg += "*What I can do:*\n"
            welcome_msg += "📸 Process invoice images\n"
            welcome_msg += "💰 Extract amounts & VAT\n"
            welcome_msg += "📂 Categorize expenses\n"
            welcome_msg += "📊 Generate reports\n"
            welcome_msg += "👨‍💼 Connect you with CAs when needed\n\n"
            welcome_msg += "*Try sending:*\n"
            welcome_msg += "• An invoice photo\n"
            welcome_msg += "• 'report' for summary\n"
            welcome_msg += "• 'help' for commands"
            
            resp.message(welcome_msg)

        # Case 4: Help
        elif body.lower() in ["help", "commands"]:
            help_msg = "🆘 *SaveAI Commands*\n\n"
            help_msg += "📸 *Send photo* - Process invoice/receipt\n"
            help_msg += "📊 *'report'* - View expense summary\n"
            help_msg += "💰 *'total'* - Show total expenses\n"
            help_msg += "🆘 *'help'* - Show this menu\n\n"
            help_msg += "📞 Need human help? Just ask!"
            
            resp.message(help_msg)

        # Case 5: Request for human help
        elif any(word in body.lower() for word in ["human", "accountant", "ca", "help me", "complex"]):
            resp.message("👨‍💼 Connecting you with our certified accountant...\n\nA CA from our partner network will contact you within 1 hour. In the meantime, feel free to send more invoices for processing!")

        # Case 6: Any other message
        elif body:
            resp.message(f"🤔 I didn't understand '{body}'. Send 'help' to see what I can do, or just send me an invoice image!")

        # Case 7: Nothing sent
        else:
            resp.message("🤖 Please send me a message or an invoice image to get started.")

        return str(resp)

    except Exception as e:
        # Catch any global error and respond
        print(f"🔥 FATAL ERROR: {e}", file=sys.stderr)
        sys.stderr.flush()
        return str(MessagingResponse().message("⚠️ Something went wrong. Our technical team has been notified. Please try again in a few minutes."))

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SaveAI", "version": "1.0.0"}

# Flask entry point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
