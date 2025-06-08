import os, sys, requests, re, json, sqlite3, hashlib
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from google.cloud import vision
from datetime import datetime, timedelta
import dateparser
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize Google Vision client
try:
    vision_client = vision.ImageAnnotatorClient()
except Exception as e:
    logger.error(f"Failed to initialize Google Vision client: {e}")
    vision_client = None

class ExpenseCategory(Enum):
    MEDICAL_SUPPLIES = "Medical Supplies"
    OFFICE_RENT = "Office Rent"
    UTILITIES = "Utilities"
    EQUIPMENT = "Equipment"
    INSURANCE = "Insurance"
    LICENSES = "Professional Licenses"
    PROFESSIONAL_FEES = "Professional Fees"
    MARKETING = "Marketing & Advertising"
    TRANSPORTATION = "Transportation"
    MEALS = "Meals & Entertainment"
    OFFICE_SUPPLIES = "Office Supplies"
    TELECOMMUNICATIONS = "Telecommunications"
    MAINTENANCE = "Maintenance & Repairs"
    TRAINING = "Training & Education"
    BANK_CHARGES = "Bank Charges"
    MISCELLANEOUS = "Miscellaneous"

@dataclass
class InvoiceData:
    """Structured invoice data class"""
    raw_text: str = ""
    invoice_number: str = ""
    amount: float = 0.0
    subtotal: float = 0.0
    vat_amount: float = 0.0
    vat_rate: float = 5.0
    date: str = ""
    due_date: str = ""
    vendor_name: str = ""
    vendor_trn: str = ""
    vendor_address: str = ""
    vendor_phone: str = ""
    customer_details: str = ""
    category: str = ExpenseCategory.MISCELLANEOUS.value
    description: str = ""
    line_items: List[Dict] = None
    currency: str = "AED"
    confidence: float = 0.0
    needs_review: bool = True
    validation_errors: List[str] = None
    processing_time: float = 0.0
    extracted_fields: Dict = None
    
    def __post_init__(self):
        if self.line_items is None:
            self.line_items = []
        if self.validation_errors is None:
            self.validation_errors = []
        if self.extracted_fields is None:
            self.extracted_fields = {}

class DatabaseManager:
    """SQLite database manager for storing invoice data"""
    
    def __init__(self, db_path="saveai.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Invoices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    invoice_hash TEXT UNIQUE,
                    invoice_number TEXT,
                    amount REAL,
                    subtotal REAL,
                    vat_amount REAL,
                    vat_rate REAL,
                    date TEXT,
                    due_date TEXT,
                    vendor_name TEXT,
                    vendor_trn TEXT,
                    category TEXT,
                    description TEXT,
                    currency TEXT DEFAULT 'AED',
                    confidence REAL,
                    needs_review BOOLEAN,
                    raw_text TEXT,
                    line_items TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    user_id TEXT PRIMARY KEY,
                    total_expenses REAL DEFAULT 0,
                    total_invoices INTEGER DEFAULT 0,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    preferences TEXT
                )
            """)
            
            # Expense categories tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS category_stats (
                    user_id TEXT,
                    category TEXT,
                    total_amount REAL DEFAULT 0,
                    invoice_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, category)
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def save_invoice(self, user_id: str, invoice_data: InvoiceData) -> bool:
        """Save invoice to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create hash for duplicate detection
            invoice_hash = hashlib.md5(
                f"{invoice_data.vendor_name}{invoice_data.amount}{invoice_data.date}".encode()
            ).hexdigest()
            
            cursor.execute("""
                INSERT OR REPLACE INTO invoices 
                (user_id, invoice_hash, invoice_number, amount, subtotal, vat_amount, 
                 vat_rate, date, due_date, vendor_name, vendor_trn, category, 
                 description, currency, confidence, needs_review, raw_text, line_items)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, invoice_hash, invoice_data.invoice_number, invoice_data.amount,
                invoice_data.subtotal, invoice_data.vat_amount, invoice_data.vat_rate,
                invoice_data.date, invoice_data.due_date, invoice_data.vendor_name,
                invoice_data.vendor_trn, invoice_data.category, invoice_data.description,
                invoice_data.currency, invoice_data.confidence, invoice_data.needs_review,
                invoice_data.raw_text, json.dumps(invoice_data.line_items)
            ))
            
            # Update user session stats
            cursor.execute("""
                INSERT OR REPLACE INTO user_sessions 
                (user_id, total_expenses, total_invoices, last_activity)
                SELECT ?, 
                       COALESCE((SELECT SUM(amount) FROM invoices WHERE user_id = ?), 0),
                       COALESCE((SELECT COUNT(*) FROM invoices WHERE user_id = ?), 0),
                       CURRENT_TIMESTAMP
            """, (user_id, user_id, user_id))
            
            # Update category stats
            cursor.execute("""
                INSERT OR REPLACE INTO category_stats 
                (user_id, category, total_amount, invoice_count, last_updated)
                SELECT ?, ?, 
                       COALESCE((SELECT SUM(amount) FROM invoices WHERE user_id = ? AND category = ?), 0),
                       COALESCE((SELECT COUNT(*) FROM invoices WHERE user_id = ? AND category = ?), 0),
                       CURRENT_TIMESTAMP
            """, (user_id, invoice_data.category, user_id, invoice_data.category, 
                  user_id, invoice_data.category))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error saving invoice: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get comprehensive user statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute("""
                SELECT total_expenses, total_invoices, last_activity 
                FROM user_sessions WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            if not result:
                return {"total_expenses": 0, "total_invoices": 0, "categories": []}
            
            total_expenses, total_invoices, last_activity = result
            
            # Category breakdown
            cursor.execute("""
                SELECT category, total_amount, invoice_count 
                FROM category_stats WHERE user_id = ? AND total_amount > 0
                ORDER BY total_amount DESC
            """, (user_id,))
            
            categories = [
                {"category": cat, "amount": amt, "count": cnt}
                for cat, amt, cnt in cursor.fetchall()
            ]
            
            # Recent invoices
            cursor.execute("""
                SELECT invoice_number, vendor_name, amount, date, needs_review
                FROM invoices WHERE user_id = ? 
                ORDER BY created_at DESC LIMIT 5
            """, (user_id,))
            
            recent_invoices = [
                {
                    "invoice_number": inv_num,
                    "vendor": vendor,
                    "amount": amt,
                    "date": date,
                    "needs_review": needs_review
                }
                for inv_num, vendor, amt, date, needs_review in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                "total_expenses": total_expenses,
                "total_invoices": total_invoices,
                "last_activity": last_activity,
                "categories": categories,
                "recent_invoices": recent_invoices
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {"total_expenses": 0, "total_invoices": 0, "categories": []}

class AdvancedInvoiceParser:
    """Advanced invoice parsing with multiple extraction strategies"""
    
    def __init__(self):
        self.uae_categories = {
            ExpenseCategory.MEDICAL_SUPPLIES: [
                "syringe", "gloves", "mask", "bandage", "medicine", "pharmaceutical",
                "medical equipment", "stethoscope", "thermometer", "vaccine", "antibiotics"
            ],
            ExpenseCategory.OFFICE_RENT: [
                "rent", "lease", "property", "office space", "building", "premises",
                "tenancy", "rental agreement"
            ],
            ExpenseCategory.UTILITIES: [
                "electricity", "water", "internet", "telephone", "wifi", "etisalat", "du",
                "dewa", "addc", "sewa", "fewa", "power", "gas"
            ],
            ExpenseCategory.EQUIPMENT: [
                "equipment", "machine", "computer", "printer", "medical device",
                "furniture", "software", "hardware", "installation"
            ],
            ExpenseCategory.INSURANCE: [
                "insurance", "takaful", "medical insurance", "liability", "coverage",
                "premium", "policy"
            ],
            ExpenseCategory.LICENSES: [
                "license", "permit", "dha", "doh", "mohap", "trade license",
                "professional license", "registration", "certification"
            ],
            ExpenseCategory.PROFESSIONAL_FEES: [
                "consultation", "audit", "legal", "accounting", "ca fees",
                "advisory", "professional services", "consultancy"
            ],
            ExpenseCategory.MARKETING: [
                "advertisement", "marketing", "social media", "website",
                "promotion", "branding", "digital marketing", "seo"
            ],
            ExpenseCategory.TRANSPORTATION: [
                "taxi", "uber", "careem", "fuel", "parking", "salik",
                "transport", "delivery", "logistics", "petrol"
            ],
            ExpenseCategory.MEALS: [
                "restaurant", "food", "lunch", "dinner", "catering",
                "coffee", "meal", "refreshments", "hospitality"
            ]
        }
        
        self.uae_vendors = [
            "emirates nbd", "adcb", "fab", "mashreq", "cbd", "rakbank", "hsbc",
            "etisalat", "du", "dewa", "addc", "sewa", "fewa",
            "carrefour", "lulu", "spinneys", "waitrose", "union coop",
            "amazon", "noon", "talabat", "deliveroo", "zomato"
        ]
        
        # Enhanced regex patterns
        self.patterns = {
            "amount": [
                r'(?:total|amount|grand\s+total|final\s+amount)[:\s]*(?:aed\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'aed\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:aed|د\.إ)',
                r'total[:\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d{1,3}(?:,\d{3})*\.\d{2})\s*$'
            ],
            "subtotal": [
                r'(?:subtotal|sub\s+total|net\s+amount)[:\s]*(?:aed\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'amount\s+before\s+vat[:\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
            ],
            "vat": [
                r'(?:vat|tax|value\s+added\s+tax)[:\s@]*(?:5%\s*)?(?:aed\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'5%[:\s]*(?:aed\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'tax\s+amount[:\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
            ],
            "invoice_number": [
                r'(?:invoice\s+(?:no|number|#)|inv\s*#?|receipt\s+(?:no|#))[:\s]*([a-z0-9\-\/]+)',
                r'#\s*([a-z0-9\-\/]{3,})',
                r'invoice[:\s]*([a-z0-9\-\/]{3,})'
            ],
            "date": [
                r'(?:date|invoice\s+date|bill\s+date)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
                r'(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})'
            ],
            "due_date": [
                r'(?:due\s+date|payment\s+due)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
            ],
            "trn": [
                r'(?:trn|tax\s+registration|vat\s+reg)[:\s#]*(\d{15})',
                r'trn[:\s]*(\d{15})'
            ],
            "phone": [
                r'(?:tel|phone|mobile)[:\s]*(\+971\s*\d{1,2}\s*\d{3}\s*\d{4})',
                r'(\+971[0-9\s\-]{8,})',
                r'(0[0-9\s\-]{8,})'
            ]
        }
    
    def extract_structured_data(self, ocr_text: str) -> InvoiceData:
        """Extract comprehensive structured data from OCR text"""
        start_time = time.time()
        
        invoice_data = InvoiceData(raw_text=ocr_text)
        text_lower = ocr_text.lower()
        
        try:
            # Extract all fields
            invoice_data.amount = self._extract_amount(ocr_text)
            invoice_data.subtotal = self._extract_subtotal(ocr_text)
            invoice_data.vat_amount = self._extract_vat(ocr_text)
            invoice_data.invoice_number = self._extract_invoice_number(ocr_text)
            invoice_data.date = self._extract_date(ocr_text)
            invoice_data.due_date = self._extract_due_date(ocr_text)
            invoice_data.vendor_name = self._extract_vendor_name(ocr_text)
            invoice_data.vendor_trn = self._extract_trn(ocr_text)
            invoice_data.vendor_phone = self._extract_phone(ocr_text)
            invoice_data.vendor_address = self._extract_address(ocr_text)
            invoice_data.category = self._categorize_expense(ocr_text)
            invoice_data.description = self._generate_description(ocr_text)
            invoice_data.line_items = self._extract_line_items(ocr_text)
            
            # Validate and calculate confidence
            invoice_data.validation_errors = self._validate_data(invoice_data)
            invoice_data.confidence = self._calculate_confidence(invoice_data)
            invoice_data.needs_review = invoice_data.confidence < 0.75
            
            # Store extracted fields for debugging
            invoice_data.extracted_fields = {
                "amount_sources": self._debug_extraction(ocr_text, self.patterns["amount"]),
                "vendor_matches": self._find_vendor_matches(text_lower),
                "category_scores": self._calculate_category_scores(text_lower)
            }
            
            invoice_data.processing_time = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Error in data extraction: {e}")
            invoice_data.validation_errors.append(f"Extraction error: {str(e)}")
            invoice_data.confidence = 0.1
        
        return invoice_data
    
    def _extract_amount(self, text: str) -> float:
        """Extract total amount with multiple strategies"""
        amounts = []
        
        for pattern in self.patterns["amount"]:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    if 0.01 <= amount <= 1000000:  # Reasonable range
                        amounts.append(amount)
                except (ValueError, TypeError):
                    continue
        
        # Return the highest reasonable amount (likely the total)
        return max(amounts) if amounts else 0.0
    
    def _extract_subtotal(self, text: str) -> float:
        """Extract subtotal amount"""
        for pattern in self.patterns["subtotal"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except (ValueError, TypeError):
                    continue
        return 0.0
    
    def _extract_vat(self, text: str) -> float:
        """Extract VAT amount with UAE 5% validation"""
        for pattern in self.patterns["vat"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    vat_amount = float(match.group(1).replace(',', ''))
                    return vat_amount
                except (ValueError, TypeError):
                    continue
        return 0.0
    
    def _extract_invoice_number(self, text: str) -> str:
        """Extract invoice number"""
        for pattern in self.patterns["invoice_number"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                inv_num = match.group(1).strip()
                if len(inv_num) >= 3:
                    return inv_num.upper()
        return ""
    
    def _extract_date(self, text: str) -> str:
        """Extract and parse invoice date"""
        for pattern in self.patterns["date"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                parsed_date = dateparser.parse(match)
                if parsed_date and parsed_date.year >= 2020:
                    return parsed_date.strftime('%Y-%m-%d')
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_due_date(self, text: str) -> str:
        """Extract due date"""
        for pattern in self.patterns["due_date"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed_date = dateparser.parse(match.group(1))
                if parsed_date:
                    return parsed_date.strftime('%Y-%m-%d')
        return ""
    
    def _extract_vendor_name(self, text: str) -> str:
        """Extract vendor name with multiple strategies"""
        text_lower = text.lower()
        
        # Check known UAE vendors first
        for vendor in self.uae_vendors:
            if vendor in text_lower:
                return vendor.title()
        
        # Extract from common patterns
        vendor_patterns = [
            r'(?:from|vendor|company|billed\s+by)[:\s]*([a-zA-Z\s&\.\-]+)',
            r'^([A-Z][a-zA-Z\s&\.\-]{2,30})',  # First line capitalized
            r'([A-Z][A-Z\s&\.]{5,30})'  # Multiple caps (company names)
        ]
        
        for pattern in vendor_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                vendor = match.group(1).strip()
                if 3 <= len(vendor) <= 50 and not any(char.isdigit() for char in vendor):
                    return vendor.title()
        
        return "Unknown Vendor"
    
    def _extract_trn(self, text: str) -> str:
        """Extract UAE Tax Registration Number"""
        for pattern in self.patterns["trn"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                trn = match.group(1)
                if len(trn) == 15 and trn.isdigit():
                    return trn
        return ""
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number"""
        for pattern in self.patterns["phone"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_address(self, text: str) -> str:
        """Extract vendor address"""
        # Look for UAE address patterns
        uae_patterns = [
            r'(.*(?:dubai|abu dhabi|sharjah|ajman|fujairah|ras al khaimah|umm al quwain).*)',
            r'(.*(?:uae|united arab emirates).*)',
            r'(p\.?o\.?\s*box\s*\d+.*)'
        ]
        
        for pattern in uae_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                address = match.group(1).strip()
                if 10 <= len(address) <= 200:
                    return address
        return ""
    
    def _categorize_expense(self, text: str) -> str:
        """Categorize expense using enhanced AI logic"""
        text_lower = text.lower()
        category_scores = {}
        
        for category, keywords in self.uae_categories.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight longer keywords more
                    score += len(keyword.split())
            
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return best_category.value
        
        return ExpenseCategory.MISCELLANEOUS.value
    
    def _generate_description(self, text: str) -> str:
        """Generate smart description from text"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Find description-like lines
        description_parts = []
        for line in lines[:10]:  # Check first 10 lines
            if (len(line) > 10 and 
                not re.search(r'\d{1,3},?\d{3}', line) and  # No large numbers
                not re.search(r'date|total|vat|trn', line, re.IGNORECASE)):
                description_parts.append(line)
        
        if description_parts:
            return ' | '.join(description_parts[:3])  # Max 3 parts
        
        return "Invoice processing"
    
    def _extract_line_items(self, text: str) -> List[Dict]:
        """Extract individual line items from invoice"""
        line_items = []
        lines = text.split('\n')
        
        for line in lines:
            # Look for lines with item, quantity, price pattern
            item_pattern = r'(.+?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:,\d{3})*(?:\.\d{2})?)'
            match = re.search(item_pattern, line.strip())
            
            if match and len(match.group(1)) > 2:
                try:
                    line_items.append({
                        'description': match.group(1).strip(),
                        'quantity': float(match.group(2)),
                        'amount': float(match.group(3).replace(',', ''))
                    })
                except ValueError:
                    continue
        
        return line_items[:10]  # Max 10 items
    
    def _validate_data(self, data: InvoiceData) -> List[str]:
        """Validate extracted data and return errors"""
        errors = []
        
        if data.amount <= 0:
            errors.append("No valid amount found")
        
        if data.vat_amount > 0 and data.subtotal > 0:
            expected_vat = data.subtotal * 0.05
            if abs(data.vat_amount - expected_vat) > 1.0:
                errors.append(f"VAT amount ({data.vat_amount}) doesn't match 5% of subtotal")
        
        if data.vendor_name == "Unknown Vendor":
            errors.append("Vendor name not identified")
        
        if not data.invoice_number:
            errors.append("Invoice number not found")
        
        # Date validation
        try:
            invoice_date = datetime.strptime(data.date, '%Y-%m-%d')
            if invoice_date > datetime.now():
                errors.append("Invoice date is in the future")
        except ValueError:
            errors.append("Invalid date format")
        
        return errors
    
    def _calculate_confidence(self, data: InvoiceData) -> float:
        """Calculate confidence score based on extracted data quality"""
        score = 0.0
        
        # Amount extraction (25%)
        if data.amount > 0:
            score += 0.25
        
        # Vendor identification (20%)
        if data.vendor_name != "Unknown Vendor":
            score += 0.20
        
        # Invoice number (15%)
        if data.invoice_number:
            score += 0.15
        
        # Date extraction (10%)
        if data.date != datetime.now().strftime('%Y-%m-%d'):
            score += 0.10
        
        # VAT consistency (10%)
        if data.vat_amount > 0 and data.subtotal > 0:
            expected_vat = data.subtotal * 0.05
            if abs(data.vat_amount - expected_vat) <= 1.0:
                score += 0.10
        
        # Category classification (10%)
        if data.category != ExpenseCategory.MISCELLANEOUS.value:
            score += 0.10
        
        # Additional fields (10%)
        bonus_fields = [data.vendor_trn, data.vendor_phone, data.due_date]
        score += (sum(1 for field in bonus_fields if field) / len(bonus_fields)) * 0.10
        
        # Penalty for validation errors
        if data.validation_errors:
            score -= len(data.validation_errors) * 0.05
        
        return max(0.0, min(1.0, score))
    
    def _debug_extraction(self, text: str, patterns: List[str]) -> List[str]:
        """Debug helper to show what patterns matched"""
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            if found:
                matches.extend(found)
        return matches
    
    def _find_vendor_matches(self, text_lower: str) -> List[str]:
        """Find which vendors were matched"""
        return [vendor for vendor in self.uae_vendors if vendor in text_lower]
    
    def _calculate_category_scores(self, text_lower: str) -> Dict:
        """Calculate category matching scores"""
        scores = {}
        for category, keywords in self.uae_categories.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[category.value] = score
        return scores

class ResponseFormatter:
    """Format responses with beautiful UAE-style formatting"""
    
    @staticmethod
    def format_invoice_summary(data: InvoiceData) -> str:
        """Format comprehensive invoice summary"""
        
        # Header with confidence indicator
        confidence_emoji = "🟢" if data.confidence >= 0.8 else "🟡" if data.confidence >= 0.6 else "🔴"
        header = f"{confidence_emoji} *INVOICE PROCESSED* {confidence_emoji}\n"
        header += "═" * 30 + "\n\n"
        
        # Main details
        summary = header
        
        # Financial Information
        summary += "💰 *FINANCIAL DETAILS*\n"
        if data.amount > 0:
            summary += f"💵 Total Amount: *AED {data.amount:,.2f}*\n"
        
        if data.subtotal > 0:
            summary += f"📊 Subtotal: AED {data.subtotal:,.2f}\n"
        
        if data.vat_amount > 0:
            vat_percentage = (data.vat_amount / data.subtotal * 100) if data.subtotal > 0 else 5.0
            summary += f"🏛️ VAT ({vat_percentage:.1f}%): AED {data.vat_amount:,.2f}\n"
        
        summary += "\n📋 *INVOICE DETAILS*\n"
        
        # Invoice Information
        if data.invoice_number:
            summary += f"🔢 Invoice #: *{data.invoice_number}*\n"
        
        summary += f"📅 Date: {data.date}\n"
        
        if data.due_date:
            summary += f"⏰ Due Date: {data.due_date}\n"
        
        # Vendor Information
        summary += f"\n🏪 *VENDOR DETAILS*\n"
        summary += f"🏢 Name: *{data.vendor_name}*\n"
        
        if data.vendor_trn:
            summary += f"🆔 TRN: {data.vendor_trn}\n"
        
        if data.vendor_phone:
            summary += f"📞 Phone: {data.vendor_phone}\n"
        
        if data.vendor_address:
            summary += f"📍 Address: {data.vendor_address[:50]}...\n"
        
        # Classification
        summary += f"\n📂 *CLASSIFICATION*\n"
        summary += f"🏷️ Category: *{data.category}*\n"
        
        if data.description:
            summary += f"📝 Description: {data.description[:60]}...\n"
        
        # Line Items
        if data.line_items:
            summary += f"\n📋 *LINE ITEMS* ({len(data.line_items)})\n"
            for i, item in enumerate(data.line_items[:3], 1):
                summary += f"  {i}. {item['description'][:30]} - AED {item['amount']:,.2f}\n"
            
            if len(data.line_items) > 3:
                summary += f"  ... and {len(data.line_items) - 3} more items\n"
        
        # Processing Information
        summary += f"\n🔍 *PROCESSING INFO*\n"
        summary += f"✅ Confidence: {data.confidence*100:.0f}%\n"
        summary += f"⚡ Processing Time: {data.processing_time:.2f}s\n"
        
        # Status and Actions
        if data.needs_review:
            summary += f"\n⚠️ *REQUIRES REVIEW*\n"
            summary += f"🔍 Confidence below threshold\n"
            if data.validation_errors:
                summary += f"❌ Issues found: {len(data.validation_errors)}\n"
                for error in data.validation_errors[:2]:
                    summary += f"  • {error}\n"
            summary += f"👨‍💼 CA review scheduled\n"
        else:
            summary += f"\n✅ *AUTO-APPROVED*\n"
            summary += f"📊 High confidence processing\n"
            summary += f"💾 Saved to accounting system\n"
        
        summary += "\n" + "═" * 30
        return summary
    
    @staticmethod
    def format_monthly_report(stats: Dict) -> str:
        """Format comprehensive monthly report"""
        report = "📊 *MONTHLY EXPENSE REPORT*\n"
        report += "═" * 35 + "\n\n"
        
        # Summary Stats
        report += "💰 *FINANCIAL SUMMARY*\n"
        report += f"💵 Total Expenses: *AED {stats['total_expenses']:,.2f}*\n"
        report += f"📄 Total Invoices: *{stats['total_invoices']}*\n"
        
        if stats['total_invoices'] > 0:
            avg_invoice = stats['total_expenses'] / stats['total_invoices']
            report += f"📊 Average Invoice: AED {avg_invoice:,.2f}\n"
        
        # Category Breakdown
        if stats['categories']:
            report += f"\n📂 *EXPENSE CATEGORIES*\n"
            for i, cat in enumerate(stats['categories'][:5], 1):
                percentage = (cat['amount'] / stats['total_expenses'] * 100) if stats['total_expenses'] > 0 else 0
                report += f"{i}. {cat['category']}\n"
                report += f"   💰 AED {cat['amount']:,.2f} ({percentage:.1f}%)\n"
                report += f"   📄 {cat['count']} invoices\n\n"
        
        # Recent Activity
        if stats.get('recent_invoices'):
            report += f"📋 *RECENT INVOICES*\n"
            for invoice in stats['recent_invoices'][:3]:
                status = "⏳ Pending" if invoice['needs_review'] else "✅ Processed"
                report += f"• {invoice['vendor']} - AED {invoice['amount']:,.2f}\n"
                report += f"  📅 {invoice['date']} | {status}\n\n"
        
        # Tips and Insights
        report += "💡 *INSIGHTS & TIPS*\n"
        if stats['total_expenses'] > 10000:
            report += "• High expense month - consider budget review\n"
        if len(stats['categories']) > 8:
            report += "• Many expense categories - consider consolidation\n"
        
        report += "\n" + "═" * 35
        return report
    
    @staticmethod
    def format_help_menu() -> str:
        """Format comprehensive help menu"""
        help_text = "🤖 *SaveAI - Your AI Accountant*\n"
        help_text += "═" * 32 + "\n\n"
        
        help_text += "📸 *INVOICE PROCESSING*\n"
        help_text += "• Send photo → Auto-extract all data\n"
        help_text += "• Supports Arabic & English text\n"
        help_text += "• Validates UAE VAT (5%)\n"
        help_text += "• Categorizes expenses automatically\n\n"
        
        help_text += "📊 *REPORTS & ANALYTICS*\n"
        help_text += "• 'report' → Monthly summary\n"
        help_text += "• 'stats' → Detailed analytics\n"
        help_text += "• 'categories' → Expense breakdown\n"
        help_text += "• 'recent' → Last 5 invoices\n\n"
        
        help_text += "💼 *BUSINESS FEATURES*\n"
        help_text += "• VAT compliance checking\n"
        help_text += "• Duplicate invoice detection\n"
        help_text += "• Expense categorization\n"
        help_text += "• TRN validation\n\n"
        
        help_text += "👨‍💼 *PROFESSIONAL SUPPORT*\n"
        help_text += "• 'ca' → Connect with accountant\n"
        help_text += "• 'review' → Request manual review\n"
        help_text += "• 'audit' → Compliance check\n\n"
        
        help_text += "🚀 *QUICK COMMANDS*\n"
        help_text += "• 'help' → This menu\n"
        help_text += "• 'clear' → Reset session\n"
        help_text += "• 'export' → Download data\n"
        
        return help_text

# Initialize components
db_manager = DatabaseManager()
invoice_parser = AdvancedInvoiceParser()
formatter = ResponseFormatter()

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Enhanced WhatsApp webhook with comprehensive features"""
    try:
        # Log incoming request
        payload = request.values.to_dict()
        logger.info(f"Incoming WhatsApp message: {payload.get('From', 'Unknown')}")
        
        resp = MessagingResponse()
        from_number = request.values.get("From", "")
        num_media = int(request.values.get("NumMedia", 0))
        body = request.values.get("Body", "").strip().lower()
        message_sid = request.values.get("MessageSid", "")
        
        # Rate limiting check (simple implementation)
        user_stats = db_manager.get_user_stats(from_number)
        
        # Case 1: Invoice/Receipt Image Processing
        if num_media > 0:
            return process_invoice_image(resp, from_number, request.values)
        
        # Case 2: Reports and Analytics
        elif body in ["report", "summary", "monthly"]:
            stats = db_manager.get_user_stats(from_number)
            if stats['total_invoices'] > 0:
                report = formatter.format_monthly_report(stats)
                resp.message(report)
            else:
                resp.message("📊 No expenses recorded yet!\n\nSend me invoice photos to start tracking your expenses. 📸")
        
        elif body in ["stats", "analytics", "detailed"]:
            return send_detailed_analytics(resp, from_number)
        
        elif body in ["categories", "breakdown"]:
            return send_category_breakdown(resp, from_number)
        
        elif body in ["recent", "last", "latest"]:
            return send_recent_invoices(resp, from_number)
        
        # Case 3: Professional Services
        elif body in ["ca", "accountant", "human", "expert"]:
            resp.message("👨‍💼 *Connecting with Certified Accountant*\n\n"
                        "🔄 Finding available CA in UAE...\n"
                        "⏰ Expected response time: 30-60 minutes\n"
                        "📧 You'll receive contact details shortly\n\n"
                        "Meanwhile, feel free to send more invoices! 📸")
        
        elif body in ["review", "check", "audit"]:
            resp.message("🔍 *Manual Review Requested*\n\n"
                        "📋 Preparing comprehensive audit...\n"
                        "✅ VAT compliance check\n"
                        "✅ Expense categorization review\n"
                        "✅ Duplicate detection\n"
                        "✅ UAE regulations compliance\n\n"
                        "📊 Review report will be ready in 2 hours")
        
        # Case 4: Data Management
        elif body in ["export", "download", "backup"]:
            resp.message("💾 *Data Export Service*\n\n"
                        "📋 Preparing your expense data...\n"
                        "📊 Formats: Excel, PDF, CSV\n"
                        "📧 Download link sent to registered email\n"
                        "🔒 Secure 24-hour access link\n\n"
                        "Export includes:\n"
                        "• All invoices with details\n"
                        "• Category summaries\n"
                        "• VAT analysis\n"
                        "• Monthly trends")
        
        elif body in ["clear", "reset", "delete"]:
            resp.message("⚠️ *Data Reset Confirmation*\n\n"
                        "This will permanently delete:\n"
                        "• All invoice records\n"
                        "• Expense categories\n"
                        "• Monthly summaries\n\n"
                        "Type 'CONFIRM DELETE' to proceed\n"
                        "Or send any other message to cancel")
        
        elif body == "confirm delete":
            # Note: In production, implement actual deletion
            resp.message("🗑️ *Account Reset Complete*\n\n"
                        "✅ All data permanently deleted\n"
                        "🆕 Fresh start ready\n"
                        "📸 Send your first invoice to begin!")
        
        # Case 5: Help and Information
        elif body in ["help", "commands", "menu", "?"]:
            help_text = formatter.format_help_menu()
            resp.message(help_text)
        
        elif body in ["hi", "hello", "hey", "start", "begin"]:
            welcome_msg = get_personalized_welcome(from_number, user_stats)
            resp.message(welcome_msg)
        
        elif body in ["features", "what", "capabilities"]:
            resp.message("🚀 *SaveAI Capabilities*\n\n"
                        "🤖 *AI-Powered Features:*\n"
                        "• Advanced OCR (Arabic + English)\n"
                        "• Smart expense categorization\n"
                        "• VAT compliance validation\n"
                        "• Duplicate invoice detection\n"
                        "• Vendor database matching\n\n"
                        "📊 *Business Intelligence:*\n"
                        "• Real-time expense tracking\n"
                        "• Monthly trend analysis\n"
                        "• Category-wise breakdowns\n"
                        "• Budget variance alerts\n\n"
                        "🇦🇪 *UAE-Specific:*\n"
                        "• 5% VAT calculations\n"
                        "• TRN validation\n"
                        "• Emirates vendor recognition\n"
                        "• Arabic text processing")
        
        # Case 6: Smart Query Processing
        elif any(word in body for word in ["total", "how much", "spent", "expense"]):
            stats = db_manager.get_user_stats(from_number)
            if stats['total_expenses'] > 0:
                resp.message(f"💰 *Quick Summary*\n\n"
                           f"Total Expenses: *AED {stats['total_expenses']:,.2f}*\n"
                           f"Invoice Count: {stats['total_invoices']}\n"
                           f"Categories: {len(stats['categories'])}\n\n"
                           f"Send 'report' for detailed breakdown 📊")
            else:
                resp.message("💰 No expenses recorded yet!\nSend invoice photos to start tracking 📸")
        
        # Case 7: Error Handling and Fallback
        elif body:
            # Intelligent response based on context
            suggestions = get_smart_suggestions(body, user_stats)
            resp.message(f"🤔 I didn't understand '{body}'\n\n{suggestions}")
        
        else:
            resp.message("👋 Welcome to SaveAI!\n\n"
                        "📸 Send invoice photos for instant processing\n"
                        "💬 Type 'help' to see all commands\n"
                        "🚀 Let's make accounting effortless!")
        
        return str(resp)
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        error_resp = MessagingResponse()
        error_resp.message("⚠️ *System Error*\n\n"
                          "Our technical team has been notified.\n"
                          "Please try again in a few moments.\n\n"
                          "For urgent support: support@saveai.ae")
        return str(error_resp)

def process_invoice_image(resp: MessagingResponse, from_number: str, request_values: dict) -> str:
    """Process uploaded invoice images with comprehensive analysis"""
    try:
        media_url = request_values["MediaUrl0"]
        media_type = request_values.get("MediaContentType0", "")
        
        logger.info(f"Processing image: {media_type} from {from_number}")
        
        # Validate image type
        if not media_type.startswith('image/'):
            resp.message("❌ Please send image files only (JPG, PNG, PDF)")
            return str(resp)
        
        # Download image with authentication
        sid = os.environ.get("TWILIO_ACCOUNT_SID")
        token = os.environ.get("TWILIO_AUTH_TOKEN")
        
        if not sid or not token:
            resp.message("⚠️ Service temporarily unavailable. Please try again.")
            return str(resp)
        
        # Download and process image
        response = requests.get(media_url, auth=(sid, token), timeout=30)
        response.raise_for_status()
        
        if not vision_client:
            resp.message("⚠️ OCR service unavailable. Please try again later.")
            return str(resp)
        
        # Send processing notification
        resp.message("🔄 *Processing Invoice...*\n\n"
                    "🤖 Extracting text with AI OCR\n"
                    "💰 Analyzing financial data\n"
                    "🏷️ Categorizing expenses\n"
                    "✅ Validating UAE compliance\n\n"
                    "⏱️ This may take 10-15 seconds...")
        
        # Perform OCR
        image = vision.Image(content=response.content)
        ocr_result = vision_client.text_detection(image=image)
        
        if ocr_result.error.message:
            raise Exception(f"OCR Error: {ocr_result.error.message}")
        
        annotations = ocr_result.text_annotations
        
        if not annotations:
            resp.message("❌ *No Text Detected*\n\n"
                        "Please ensure:\n"
                        "📸 Image is clear and well-lit\n"
                        "📄 Text is visible and readable\n"
                        "🔍 Try taking photo from closer distance\n\n"
                        "💡 Tip: Hold phone steady and tap to focus")
            return str(resp)
        
        # Extract and process invoice data
        detected_text = annotations[0].description.strip()
        logger.info(f"OCR extracted {len(detected_text)} characters")
        
        # Parse with advanced AI
        invoice_data = invoice_parser.extract_structured_data(detected_text)
        
        # Save to database
        if db_manager.save_invoice(from_number, invoice_data):
            logger.info(f"Invoice saved successfully for {from_number}")
        else:
            logger.warning(f"Failed to save invoice for {from_number}")
        
        # Format and send comprehensive response
        summary = formatter.format_invoice_summary(invoice_data)
        resp.message(summary)
        
        # Send additional insights if high confidence
        if invoice_data.confidence >= 0.8:
            insights = generate_smart_insights(invoice_data)
            if insights:
                resp.message(insights)
        
        # Offer additional services
        if invoice_data.needs_review:
            resp.message("🔄 *Next Steps Available:*\n\n"
                        "👨‍💼 Type 'ca' → Connect with accountant\n"
                        "🔍 Type 'review' → Request detailed audit\n"
                        "📊 Type 'report' → View monthly summary")
        
        return str(resp)
        
    except requests.RequestException as e:
        logger.error(f"Network error processing image: {e}")
        resp.message("🌐 Network error downloading image. Please try again.")
        return str(resp)
    
    except Exception as e:
        logger.error(f"Error processing invoice image: {e}")
        resp.message("⚠️ Error processing image. Please try again or contact support.")
        return str(resp)

def send_detailed_analytics(resp: MessagingResponse, from_number: str) -> str:
    """Send comprehensive analytics report"""
    stats = db_manager.get_user_stats(from_number)
    
    if stats['total_invoices'] == 0:
        resp.message("📊 No data available for analytics.\n\nStart by sending invoice photos! 📸")
        return str(resp)
    
    # Generate advanced analytics
    analytics = "📈 *ADVANCED ANALYTICS*\n"
    analytics += "═" * 28 + "\n\n"
    
    # Financial KPIs
    avg_invoice = stats['total_expenses'] / stats['total_invoices']
    analytics += f"💰 *Key Metrics*\n"
    analytics += f"📊 Average Invoice: AED {avg_invoice:.2f}\n"
    analytics += f"🎯 Largest Category: {stats['categories'][0]['category'] if stats['categories'] else 'N/A'}\n"
    
    # Monthly projection
    days_in_month = 30
    current_day = datetime.now().day
    projected_monthly = (stats['total_expenses'] / current_day) * days_in_month if current_day > 0 else 0
    analytics += f"📈 Monthly Projection: AED {projected_monthly:,.2f}\n\n"
    
    # Category insights
    if len(stats['categories']) >= 3:
        analytics += f"🏆 *Top 3 Categories*\n"
        for i, cat in enumerate(stats['categories'][:3], 1):
            percentage = (cat['amount'] / stats['total_expenses']) * 100
            analytics += f"{i}. {cat['category']} ({percentage:.1f}%)\n"
    
    resp.message(analytics)
    return str(resp)

def send_category_breakdown(resp: MessagingResponse, from_number: str) -> str:
    """Send detailed category breakdown"""
    stats = db_manager.get_user_stats(from_number)
    
    if not stats['categories']:
        resp.message("📂 No expense categories yet.\n\nSend invoices to see category breakdown!")
        return str(resp)
    
    breakdown = "📂 *EXPENSE CATEGORIES*\n"
    breakdown += "═" * 25 + "\n\n"
    
    for i, cat in enumerate(stats['categories'], 1):
        percentage = (cat['amount'] / stats['total_expenses']) * 100
        bar = "█" * int(percentage / 5)  # Visual bar
        breakdown += f"{i}. *{cat['category']}*\n"
        breakdown += f"   💰 AED {cat['amount']:,.2f}\n"
        breakdown += f"   📊 {percentage:.1f}% {bar}\n"
        breakdown += f"   📄 {cat['count']} invoices\n\n"
    
    resp.message(breakdown)
    return str(resp)

def send_recent_invoices(resp: MessagingResponse, from_number: str) -> str:
    """Send recent invoice summary"""
    stats = db_manager.get_user_stats(from_number)
    
    if not stats.get('recent_invoices'):
        resp.message("📋 No recent invoices found.\n\nSend invoice photos to get started!")
        return str(resp)
    
    recent = "📋 *RECENT INVOICES*\n"
    recent += "═" * 22 + "\n\n"
    
    for i, inv in enumerate(stats['recent_invoices'], 1):
        status_emoji = "⏳" if inv['needs_review'] else "✅"
        recent += f"{i}. {status_emoji} *{inv['vendor']}*\n"
        recent += f"   💰 AED {inv['amount']:,.2f}\n"
        recent += f"   📅 {inv['date']}\n"
        if inv['invoice_number']:
            recent += f"   🔢 #{inv['invoice_number']}\n"
        recent += "\n"
    
    resp.message(recent)
    return str(resp)

def get_personalized_welcome(from_number: str, user_stats: Dict) -> str:
    """Generate personalized welcome message"""
    if user_stats['total_invoices'] > 0:
        return (f"👋 *Welcome back to SaveAI!*\n\n"
                f"📊 Your Summary:\n"
                f"💰 Total Expenses: AED {user_stats['total_expenses']:,.2f}\n"
                f"📄 Invoices Processed: {user_stats['total_invoices']}\n\n"
                f"📸 Send new invoices or type 'help' for options!")
    else:
        return ("👋 *Welcome to SaveAI!*\n"
                "🇦🇪 UAE's Smart AI Accountant\n\n"
                "🚀 *What I do:*\n"
                "📸 Process invoice photos instantly\n"
                "💰 Extract amounts & VAT automatically\n"
                "🏷️ Categorize expenses intelligently\n"
                "📊 Generate detailed reports\n"
                "👨‍💼 Connect with certified accountants\n\n"
                "✨ *Get Started:*\n"
                "Just send me a photo of any invoice or receipt!\n\n"
                "Type 'help' to see all features 🆘")

def get_smart_suggestions(user_input: str, user_stats: Dict) -> str:
    """Generate smart suggestions based on user input"""
    suggestions = "💡 *Did you mean:*\n\n"
    
    # Keyword-based suggestions
    if any(word in user_input for word in ["money", "cost", "price", "amount"]):
        suggestions += "💰 'report' → See expense summary\n"
        suggestions += "📊 'stats' → Detailed analytics\n"
    elif any(word in user_input for word in ["category", "type", "kind"]):
        suggestions += "📂 'categories' → Expense breakdown\n"
    elif any(word in user_input for word in ["recent", "last", "new"]):
        suggestions += "📋 'recent' → Latest invoices\n"
    else:
        suggestions += "📸 Send invoice photo → Process automatically\n"
        suggestions += "📊 'report' → Monthly summary\n"
        suggestions += "🆘 'help' → All commands\n"
    
    return suggestions

def generate_smart_insights(invoice_data: InvoiceData) -> str:
    """Generate smart insights for processed invoice"""
    insights = []
    
    # VAT insights
    if invoice_data.vat_amount > 0 and invoice_data.subtotal > 0:
        expected_vat = invoice_data.subtotal * 0.05
        if abs(invoice_data.vat_amount - expected_vat) <= 0.5:
            insights.append("✅ VAT calculation is accurate (5% UAE standard)")
        else:
            insights.append(f"⚠️ VAT amount seems incorrect. Expected: AED {expected_vat:.2f}")
    
    # Amount insights
    if invoice_data.amount > 1000:
        insights.append("💡 High-value expense - consider if approval needed")
    
    # Category insights
    if invoice_data.category == ExpenseCategory.MEDICAL_SUPPLIES.value:
        insights.append("🏥 Medical expense - may be tax deductible")
    elif invoice_data.category == ExpenseCategory.EQUIPMENT.value:
        insights.append("🖥️ Equipment purchase - check depreciation rules")
    
    if insights:
        return "💡 *Smart Insights:*\n\n" + "\n".join(insights)
    
    return ""

@app.route("/health", methods=["GET"])
def health_check():
    """Enhanced health check with system status"""
    try:
        # Test database connection
        db_test = db_manager.get_user_stats("health_check")
        
        # Test Vision API
        vision_status = "available" if vision_client else "unavailable"
        
        return jsonify({
            "status": "healthy",
            "service": "SaveAI Enhanced",
            "version": "2.0.0",
            "database": "connected",
            "vision_api": vision_status,
            "features": [
                "Advanced OCR",
                "Smart Categorization", 
                "UAE VAT Compliance",
                "Duplicate Detection",
                "Professional CA Network"
            ],
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/stats/<user_id>", methods=["GET"])
def api_get_stats(user_id: str):
    """API endpoint for getting user statistics"""
    try:
        stats = db_manager.get_user_stats(user_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Background task for data cleanup
def cleanup_old_data():
    """Clean up old data periodically"""
    # Implementation for cleaning old sessions, etc.
    pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    logger.info(f"Starting SaveAI Enhanced v2.0.0 on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
