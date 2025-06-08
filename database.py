import os, sys, sqlite3, json, hashlib, logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .models import InvoiceData, Budget, CashFlowProjection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Enhanced SQLite database manager with advanced features"""
    
    def __init__(self, db_path="saveai.db"):
        self.db_path = db_path
        self.init_database()
        self.last_backup = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption for sensitive data"""
        self.encryption_key = os.getenv("DB_ENCRYPTION_KEY", "default_key")
        self.cipher_suite = self._create_cipher_suite()
    
    def init_database(self):
        """Initialize all database tables with enhanced features"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enhanced Invoices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    invoice_hash TEXT UNIQUE,
                    blockchain_hash TEXT,
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
                    tags TEXT,
                    recurring BOOLEAN DEFAULT FALSE,
                    recurring_frequency TEXT,
                    next_due_date TEXT,
                    approval_status TEXT DEFAULT 'pending',
                    approved_by TEXT,
                    approval_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    security_signature TEXT,
                    ml_classification_confidence REAL,
                    compliance_status TEXT,
                    audit_trail TEXT
                )
            """)
            
            # Enhanced Budget Management table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    monthly_limit REAL NOT NULL,
                    alert_threshold REAL DEFAULT 0.8,
                    period_start TEXT,
                    period_end TEXT,
                    active BOOLEAN DEFAULT TRUE,
                    auto_adjust BOOLEAN DEFAULT FALSE,
                    historical_data TEXT,
                    trend_analysis TEXT,
                    variance_threshold REAL DEFAULT 0.1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_notification_date TEXT,
                    UNIQUE(user_id, category)
                )
            """)
            
            # Enhanced Tax Records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tax_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    tax_period TEXT NOT NULL,
                    total_vat_collected REAL DEFAULT 0,
                    total_vat_paid REAL DEFAULT 0,
                    net_vat_due REAL DEFAULT 0,
                    filing_due_date TEXT,
                    status TEXT DEFAULT 'pending',
                    filed_date TEXT,
                    payment_date TEXT,
                    fta_reference TEXT,
                    submission_hash TEXT,
                    supporting_docs TEXT,
                    compliance_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    blockchain_verification TEXT
                )
            """)
            
            # Enhanced Analytics Data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    period TEXT NOT NULL,
                    metrics TEXT,
                    insights TEXT,
                    predictions TEXT,
                    confidence_scores TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, data_type, period)
                )
            """)
            
            # Enhanced Security Audit Log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    action_details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    status TEXT,
                    risk_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    geographic_location TEXT,
                    device_fingerprint TEXT
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_user ON invoices(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_user ON budgets(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tax_records_user ON tax_records(user_id)")
            
            conn.commit()
            conn.close()
            logger.info("Enhanced database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    async def save_invoice(self, user_id: str, invoice_data: InvoiceData) -> int:
        """Enhanced invoice saving with security and blockchain features"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate enhanced invoice hash
            invoice_hash = self._generate_secure_hash(invoice_data)
            
            # Encrypt sensitive data
            encrypted_data = self._encrypt_sensitive_fields(invoice_data)
            
            # Prepare blockchain data
            blockchain_data = {
                "hash": invoice_hash,
                "timestamp": "2025-06-08 15:55:54",
                "user": "anandhu723",
                "invoice_number": invoice_data.invoice_number,
                "amount": invoice_data.amount,
                "vendor_trn": invoice_data.vendor_trn
            }
            
            # Store invoice with enhanced security
            cursor.execute("""
                INSERT OR REPLACE INTO invoices 
                (user_id, invoice_hash, blockchain_hash, invoice_number, amount,
                 subtotal, vat_amount, vat_rate, date, due_date, vendor_name,
                 vendor_trn, category, description, currency, confidence,
                 needs_review, raw_text, line_items, status, security_signature,
                 ml_classification_confidence, compliance_status, audit_trail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, invoice_hash, json.dumps(blockchain_data),
                encrypted_data["invoice_number"], invoice_data.amount,
                invoice_data.subtotal, invoice_data.vat_amount,
                invoice_data.vat_rate, invoice_data.date,
                invoice_data.due_date, encrypted_data["vendor_name"],
                encrypted_data["vendor_trn"], invoice_data.category,
                invoice_data.description, invoice_data.currency,
                invoice_data.confidence, invoice_data.needs_review,
                encrypted_data["raw_text"], json.dumps(invoice_data.line_items),
                "pending", self._generate_security_signature(invoice_data),
                invoice_data.confidence, "pending_review",
                json.dumps(self._create_audit_trail(user_id, "invoice_creation"))
            ))
            
            invoice_id = cursor.lastrowid
            
            # Update analytics
            await self._update_analytics(user_id, invoice_data)
            
            # Update tax records
            await self._update_tax_records(user_id, invoice_data)
            
            # Log security audit
            await self._log_security_audit(user_id, "invoice_save", invoice_id)
            
            conn.commit()
            conn.close()
            
            return invoice_id
            
        except Exception as e:
            logger.error(f"Error saving invoice: {e}")
            raise

    async def get_financial_insights(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive financial insights with ML predictions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_invoices,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount,
                    MAX(amount) as max_amount,
                    COUNT(CASE WHEN status = 'unpaid' THEN 1 END) as unpaid_count,
                    SUM(CASE WHEN status = 'unpaid' THEN amount ELSE 0 END) as unpaid_amount
                FROM invoices 
                WHERE user_id = ? AND date >= date('now', '-12 months')
            """, (user_id,))
            
            basic_stats = dict(cursor.fetchone())
            
            # Get category breakdown
            cursor.execute("""
                SELECT category, 
                       SUM(amount) as total,
                       COUNT(*) as count,
                       AVG(amount) as average,
                       MAX(amount) as highest
                FROM invoices 
                WHERE user_id = ?
                GROUP BY category
                ORDER BY total DESC
            """, (user_id,))
            
            categories = [dict(row) for row in cursor.fetchall()]
            
            # Get time series data
            cursor.execute("""
                SELECT strftime('%Y-%m', date) as month,
                       SUM(amount) as monthly_total,
                       COUNT(*) as invoice_count
                FROM invoices
                WHERE user_id = ?
                GROUP BY month
                ORDER BY month DESC
                LIMIT 12
            """, (user_id,))
            
            time_series = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                "basic_stats": basic_stats,
                "categories": categories,
                "time_series": time_series,
                "predictions": await self._generate_predictions(user_id),
                "generated_at": "2025-06-08 15:55:54",
                "generated_by": "anandhu723"
            }
            
        except Exception as e:
            logger.error(f"Error getting financial insights: {e}")
            raise

    # ... (More methods to be continued)
