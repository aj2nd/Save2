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
import csv
from io import StringIO

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
    PAYROLL = "Payroll"
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
    status: str = "unpaid" # New: unpaid, paid, overdue
    
    def __post_init__(self):
        if self.line_items is None:
            self.line_items = []
        if self.validation_errors is None:
            self.validation_errors = []
        if self.extracted_fields is None:
            self.extracted_fields = {}

class DatabaseManager:
    """SQLite database manager for storing all financial data"""
    
    def __init__(self, db_path="saveai.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize all database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Invoices table - Added status and payment_date
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
                    status TEXT DEFAULT 'unpaid',
                    payment_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Bank Transactions table (New for Reconciliation)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bank_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    transaction_date TEXT,
                    description TEXT,
                    amount REAL,
                    is_reconciled BOOLEAN DEFAULT FALSE,
                    matched_invoice_id INTEGER,
                    FOREIGN KEY (matched_invoice_id) REFERENCES invoices(id)
                )
            """)

            # Employees table (New for Payroll)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    monthly_salary REAL NOT NULL,
                    active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Payroll Records table (New for Payroll)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payroll_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    employee_id INTEGER NOT NULL,
                    pay_period TEXT,
                    net_salary REAL,
                    status TEXT,
                    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
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
            logger.info("Database initialized/validated successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    # All other database methods from your original code would go here
    # (save_invoice, get_user_stats, etc.)
    # For brevity, I'll omit the identical methods and only add new ones.
    def save_invoice(self, user_id: str, invoice_data: InvoiceData) -> bool:
    """Save invoice data to database"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for duplicate invoice
        if invoice_data.invoice_hash:
            cursor.execute("SELECT id FROM invoices WHERE invoice_hash = ?", 
                         (invoice_data.invoice_hash,))
            if cursor.fetchone():
                logger.info("Duplicate invoice detected, skipping")
                return False
        
        # Insert invoice data
        cursor.execute("""
            INSERT INTO invoices (
                user_id, invoice_hash, invoice_number, amount, subtotal,
                vat_amount, vat_rate, date, due_date, vendor_name,
                vendor_trn, category, description, currency,
                confidence, needs_review, raw_text, line_items
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, invoice_data.invoice_hash, invoice_data.invoice_number,
            invoice_data.amount, invoice_data.subtotal, invoice_data.vat_amount,
            invoice_data.vat_rate, invoice_data.date, invoice_data.due_date,
            invoice_data.vendor_name, invoice_data.vendor_trn, invoice_data.category,
            invoice_data.description, invoice_data.currency, invoice_data.confidence,
            invoice_data.needs_review, invoice_data.raw_text,
            json.dumps(invoice_data.line_items) if invoice_data.line_items else None
        ))
        
        # Update category stats
        cursor.execute("""
            INSERT INTO category_stats (user_id, category, total_amount, invoice_count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id, category) DO UPDATE SET
            total_amount = total_amount + ?,
            invoice_count = invoice_count + 1,
            last_updated = CURRENT_TIMESTAMP
        """, (user_id, invoice_data.category, invoice_data.amount, invoice_data.amount))
        
        conn.commit()
        conn.close()
        logger.info(f"Successfully saved invoice {invoice_data.invoice_number}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving invoice: {e}")
        return False

    def save_bank_transactions(self, user_id: str, transactions: List[Dict]) -> int:
        """Saves a list of bank transactions to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        count = 0
        for tx in transactions:
            cursor.execute("""
                INSERT INTO bank_transactions (user_id, transaction_date, description, amount)
                VALUES (?, ?, ?, ?)
            """, (user_id, tx['date'], tx['description'], tx['amount']))
            count += 1
        conn.commit()
        conn.close()
        logger.info(f"Saved {count} new bank transactions.")
        return count

    def get_unreconciled_data(self, user_id: str) -> Tuple[List, List]:
        """Fetches unpaid invoices and unreconciled bank transactions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM invoices WHERE user_id = ? AND status = 'unpaid'", (user_id,))
        invoices = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM bank_transactions WHERE user_id = ? AND is_reconciled = FALSE", (user_id,))
        transactions = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return invoices, transactions

    def mark_as_reconciled(self, invoice_id: int, transaction_id: int, payment_date: str):
        """Updates invoice and transaction status after a successful match."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Mark invoice as paid
        cursor.execute("""
            UPDATE invoices SET status = 'paid', payment_date = ? WHERE id = ?
        """, (payment_date, invoice_id))
        
        # Mark transaction as reconciled
        cursor.execute("""
            UPDATE bank_transactions SET is_reconciled = TRUE, matched_invoice_id = ? WHERE id = ?
        """, (invoice_id, transaction_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Reconciled invoice {invoice_id} with transaction {transaction_id}")

    def get_active_employees(self, user_id: str) -> List[Dict]:
        """Fetches all active employees for payroll processing."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE user_id = ? AND active = TRUE", (user_id,))
        employees = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return employees

    def save_payroll_run(self, user_id: str, payroll_data: List[Dict]):
        """Saves the results of a payroll run to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for record in payroll_data:
            # Add a payroll expense to the invoices table for tracking
            payroll_invoice = InvoiceData(
                user_id=user_id,
                invoice_number=f"PAYROLL-{record['pay_period']}-{record['employee_id']}",
                amount=record['net_salary'],
                date=datetime.now().strftime('%Y-%m-%d'),
                vendor_name=record['employee_name'],
                category=ExpenseCategory.PAYROLL.value,
                description=f"Payroll for {record['pay_period']}",
                status="paid"
            )
            self.save_invoice(user_id, payroll_invoice) # Assumes save_invoice exists

            cursor.execute("""
                INSERT INTO payroll_records (user_id, employee_id, pay_period, net_salary, status)
                VALUES (?, ?, ?, ?, 'processed')
            """, (user_id, record['employee_id'], record['pay_period'], record['net_salary']))
        conn.commit()
        conn.close()
        
# Your existing AdvancedInvoiceParser and ResponseFormatter classes would be here.
# I'll add the new service classes below.
class ResponseFormatter:
    """Formats responses for WhatsApp messages"""
    
    def format_invoice_summary(self, invoice: InvoiceData) -> str:
        """Format invoice details for WhatsApp message"""
        summary = ["📑 Invoice processed successfully!"]
        
        if invoice.invoice_number:
            summary.append(f"Invoice #: {invoice.invoice_number}")
        
        if invoice.amount:
            summary.append(f"Amount: {invoice.currency} {invoice.amount:,.2f}")
            
        if invoice.vendor_name:
            summary.append(f"Vendor: {invoice.vendor_name}")
            
        if invoice.date:
            summary.append(f"Date: {invoice.date}")
            
        if invoice.category:
            summary.append(f"Category: {invoice.category}")
            
        if invoice.needs_review:
            summary.append("\n⚠️ This invoice needs review.")
            
        confidence = invoice.confidence * 100
        summary.append(f"\nConfidence: {confidence:.1f}%")
        
        return "\n".join(summary)
        
    def format_monthly_report(self, stats: Dict) -> str:
        """Format monthly expense report"""
        report = ["📊 Monthly Expense Report"]
        
        if 'total_expenses' in stats:
            report.append(f"\nTotal Expenses: AED {stats['total_expenses']:,.2f}")
            
        if 'total_invoices' in stats:
            report.append(f"Total Invoices: {stats['total_invoices']}")
            
        if 'categories' in stats:
            report.append("\nExpenses by Category:")
            for cat in stats['categories']:
                report.append(f"- {cat['name']}: AED {cat['amount']:,.2f}")
                
        return "\n".join(report)

# Add the class right before this comment:
class BankReconciliation:
class BankReconciliation:
    """Handles parsing bank statements and matching transactions."""
    
    def parse_csv_statement(self, csv_content: str) -> List[Dict]:
        """Parses a CSV string into a list of transaction dictionaries."""
        transactions = []
        # Assuming a simple CSV format: Date,Description,Amount
        reader = csv.reader(StringIO(csv_content))
        next(reader) # Skip header row
        for row in reader:
            try:
                transactions.append({
                    "date": dateparser.parse(row[0]).strftime('%Y-%m-%d'),
                    "description": row[1],
                    "amount": float(row[2])
                })
            except (IndexError, ValueError) as e:
                logger.warning(f"Skipping invalid bank transaction row: {row} - Error: {e}")
                continue
        return transactions

    def run(self, user_id: str, db_manager: DatabaseManager) -> Dict:
        """The main reconciliation logic."""
        unpaid_invoices, unreconciled_txs = db_manager.get_unreconciled_data(user_id)
        
        matches = []
        match_count = 0
        
        for tx in unreconciled_txs:
            # We only care about outgoing payments (negative amounts in statement)
            if tx['amount'] >= 0:
                continue
            
            tx_amount = abs(tx['amount'])
            
            for inv in unpaid_invoices:
                # Simple matching logic: exact amount and vendor name in description
                if inv['amount'] == tx_amount and inv['vendor_name'].lower() in tx['description'].lower():
                    db_manager.mark_as_reconciled(inv['id'], tx['id'], tx['transaction_date'])
                    matches.append(f"Matched Invoice {inv['invoice_number']} with payment to {inv['vendor_name']}")
                    match_count += 1
                    # Remove invoice from list to prevent double matching
                    unpaid_invoices.remove(inv)
                    break # Move to next transaction
                    
        return {
            "total_transactions": len(unreconciled_txs),
            "matches_found": match_count,
            "details": matches
        }

class PayrollManager:
    """Handles payroll calculations and processing."""
    
    def run_payroll(self, user_id: str, period: str, db_manager: DatabaseManager) -> Dict:
        """Processes payroll for all active employees for a given period."""
        employees = db_manager.get_active_employees(user_id)
        if not employees:
            return {"status": "error", "message": "No active employees found to process payroll."}
        
        payroll_run_data = []
        total_payroll_cost = 0
        
        for emp in employees:
            net_salary = emp['monthly_salary'] # Assuming no deductions for MVP
            payroll_run_data.append({
                "employee_id": emp['id'],
                "employee_name": emp['full_name'],
                "pay_period": period,
                "net_salary": net_salary
            })
            total_payroll_cost += net_salary
        
        # Save the records
        db_manager.save_payroll_run(user_id, payroll_run_data)
        
        return {
            "status": "success",
            "employees_processed": len(employees),
            "total_payroll_cost": total_payroll_cost,
            "period": period
        }
        
# --- Main App ---

# Assume db_manager, parser, and formatter are initialized
db_manager = DatabaseManager()
class AdvancedInvoiceParser:
    """Advanced invoice parser with enhanced text extraction and validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def parse(self, text: str, image_text: str = None) -> InvoiceData:
        """Parse invoice text and return structured data"""
        invoice_data = InvoiceData()
        invoice_data.raw_text = text
        
        try:
            # Extract invoice number
            invoice_number = self._extract_invoice_number(text)
            if invoice_number:
                invoice_data.invoice_number = invoice_number
            
            # Extract amount
            amount = self._extract_amount(text)
            if amount:
                invoice_data.amount = amount
                
            # Extract dates
            dates = self._extract_dates(text)
            if dates.get('invoice_date'):
                invoice_data.date = dates['invoice_date']
            if dates.get('due_date'):
                invoice_data.due_date = dates['due_date']
                
            # Extract vendor details
            vendor_info = self._extract_vendor_info(text)
            invoice_data.vendor_name = vendor_info.get('name', '')
            invoice_data.vendor_trn = vendor_info.get('trn', '')
            invoice_data.vendor_address = vendor_info.get('address', '')
            
            # Categorize the invoice
            invoice_data.category = self._categorize_invoice(text)
            
            # Set confidence based on extracted fields
            invoice_data.confidence = self._calculate_confidence(invoice_data)
            
            # Set needs_review flag
            invoice_data.needs_review = invoice_data.confidence < 0.8
            
        except Exception as e:
            self.logger.error(f"Error parsing invoice: {e}")
            invoice_data.validation_errors.append(str(e))
            
        return invoice_data
    
    def _extract_invoice_number(self, text: str) -> str:
        """Extract invoice number using regex patterns"""
        patterns = [
            r'Invoice\s*#?\s*(\w+[-/]?\w+)',
            r'Invoice Number:?\s*(\w+[-/]?\w+)',
            r'Bill Number:?\s*(\w+[-/]?\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""
    
    def _extract_amount(self, text: str) -> float:
        """Extract total amount from invoice"""
        patterns = [
            r'Total:?\s*AED\s*([\d,]+\.?\d*)',
            r'Amount Due:?\s*AED\s*([\d,]+\.?\d*)',
            r'Grand Total:?\s*AED\s*([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return 0.0
    
    def _extract_dates(self, text: str) -> Dict[str, str]:
        """Extract invoice and due dates"""
        dates = {}
        
        # Invoice date patterns
        invoice_patterns = [
            r'Invoice Date:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'Date:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        ]
        
        # Due date patterns
        due_patterns = [
            r'Due Date:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'Payment Due:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        ]
        
        # Extract invoice date
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dates['invoice_date'] = self._standardize_date(match.group(1))
                break
                
        # Extract due date
        for pattern in due_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dates['due_date'] = self._standardize_date(match.group(1))
                break
                
        return dates
    
    def _standardize_date(self, date_str: str) -> str:
        """Convert date string to standard format"""
        try:
            parsed_date = dateparser.parse(date_str)
            if parsed_date:
                return parsed_date.strftime('%Y-%m-%d')
        except Exception:
            pass
        return date_str
    
    def _extract_vendor_info(self, text: str) -> Dict[str, str]:
        """Extract vendor details from invoice"""
        vendor_info = {
            'name': '',
            'trn': '',
            'address': ''
        }
        
        # Extract TRN (Tax Registration Number)
        trn_match = re.search(r'TRN:?\s*(\d{15})', text)
        if trn_match:
            vendor_info['trn'] = trn_match.group(1)
        
        # TODO: Add more sophisticated vendor name and address extraction
        # This would need more complex pattern matching or NLP
        
        return vendor_info
    
    def _categorize_invoice(self, text: str) -> str:
        """Categorize invoice based on content"""
        # Simple keyword-based categorization
        keywords = {
            ExpenseCategory.MEDICAL_SUPPLIES.value: ['medical', 'medicine', 'pharmacy', 'prescription'],
            ExpenseCategory.OFFICE_RENT.value: ['rent', 'lease', 'property'],
            ExpenseCategory.UTILITIES.value: ['electricity', 'water', 'gas', 'utility'],
            ExpenseCategory.EQUIPMENT.value: ['equipment', 'machine', 'device'],
            ExpenseCategory.INSURANCE.value: ['insurance', 'coverage', 'policy'],
            ExpenseCategory.PROFESSIONAL_FEES.value: ['consultation', 'professional', 'service fee'],
            ExpenseCategory.OFFICE_SUPPLIES.value: ['supplies', 'stationery', 'paper']
        }
        
        text_lower = text.lower()
        for category, words in keywords.items():
            if any(word in text_lower for word in words):
                return category
                
        return ExpenseCategory.MISCELLANEOUS.value
    
    def _calculate_confidence(self, invoice_data: InvoiceData) -> float:
        """Calculate confidence score based on extracted fields"""
        required_fields = {
            'invoice_number': 0.2,
            'amount': 0.3,
            'date': 0.2,
            'vendor_name': 0.2,
            'vendor_trn': 0.1
        }
        
        confidence = 0.0
        
        if invoice_data.invoice_number:
            confidence += required_fields['invoice_number']
        if invoice_data.amount > 0:
            confidence += required_fields['amount']
        if invoice_data.date:
            confidence += required_fields['date']
        if invoice_data.vendor_name:
            confidence += required_fields['vendor_name']
        if invoice_data.vendor_trn:
            confidence += required_fields['vendor_trn']
            
        return confidence
invoice_parser = AdvancedInvoiceParser()
response_formatter = ResponseFormatter()
reconciliation_engine = BankReconciliation()
payroll_manager = PayrollManager()

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Main webhook to handle incoming WhatsApp messages."""
    incoming_msg = request.values
    user_id = incoming_msg.get("From")
    message_body = incoming_msg.get("Body", "").lower().strip()
    resp = MessagingResponse()
    
    # 1. Handle Text Commands
    if message_body:
        if message_body.startswith("run payroll"):
            period = message_body.replace("run payroll", "").strip()
            if not period:
                period = datetime.now().strftime("%B %Y") # Default to current month
            result = payroll_manager.run_payroll(user_id, period, db_manager)
            # You would format this 'result' dictionary into a nice message
            response_text = f"Payroll run for {period} processed. Total cost: AED {result['total_payroll_cost']}"
            resp.message(response_text)
            
        elif message_body == "report":
            # This can be expanded to generate a full P&L style report
            stats = db_manager.get_user_stats(user_id)
            report = response_formatter.format_monthly_report(stats)
            resp.message(report)
        else:
            # Default help message
            resp.message("Hi! Send me an invoice image to process it. You can also use commands like 'run payroll' or 'report'.")
        
        return str(resp)

    # 2. Handle Media (Invoices & Bank Statements)
    if incoming_msg.get("NumMedia", 0) != "0":
        media_url = incoming_msg.get("MediaUrl0")
        media_type = incoming_msg.get("MediaContentType0")
        
        # A. Process Invoice Images
        # A. Process Invoice Images
if "image" in media_type:
    try:
        # Download the image
        response = requests.get(media_url)
        image_content = response.content

        # Create vision image object
        image = vision.Image(content=image_content)

        # Perform OCR using Google Vision
        if vision_client:
            result = vision_client.text_detection(image=image)
            texts = result.text_annotations

            if texts:
                # Extract full text from the first annotation
                ocr_text = texts[0].description
                
                # Parse the text using our invoice parser
                invoice_data = invoice_parser.parse(ocr_text)
                
                # Generate invoice hash to prevent duplicates
                text_hash = hashlib.md5(ocr_text.encode()).hexdigest()
                invoice_data.invoice_hash = text_hash
                
                # Save to database
                if db_manager.save_invoice(user_id, invoice_data):
                    # Format response
                    summary = response_formatter.format_invoice_summary(invoice_data)
                    resp.message(summary)
                else:
                    resp.message("This invoice has already been processed.")
            else:
                resp.message("No text was detected in the image. Please ensure the image is clear and try again.")
        else:
            resp.message("Sorry, OCR service is currently unavailable. Please try again later.")
            
    except Exception as e:
        logger.error(f"Error processing invoice image: {e}")
        resp.message("Sorry, there was an error processing your invoice. Please try again.")
        # B. Process Bank Statement CSVs
        elif "csv" in media_type:
            response = requests.get(media_url)
            csv_content = response.text
            
            transactions = reconciliation_engine.parse_csv_statement(csv_content)
            count = db_manager.save_bank_transactions(user_id, transactions)
            
            resp.message(f"Received your bank statement. Saved {count} transactions. Running reconciliation...")
            # Run reconciliation immediately
            result = reconciliation_engine.run(user_id, db_manager)
            summary = f"Reconciliation complete! Found {result['matches_found']} matches."
            resp.message(summary)

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
