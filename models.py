import os, sys, requests, re, json, sqlite3, hashlib
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

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
    INVENTORY = "Inventory & Stock"
    LEGAL_FEES = "Legal Fees"
    CONSULTANCY = "Consultancy"
    TRAVEL = "Travel & Accommodation"
    MISCELLANEOUS = "Miscellaneous"

class NotificationChannel(Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TELEGRAM = "telegram"

class AlertType(Enum):
    OVERDUE_INVOICE = "overdue_invoice"
    BUDGET_EXCEEDED = "budget_exceeded"
    PAYMENT_DUE = "payment_due"
    CASH_FLOW_LOW = "cash_flow_low"
    TAX_DEADLINE = "tax_deadline"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    COMPLIANCE_ISSUE = "compliance_issue"
    SYSTEM_ERROR = "system_error"

@dataclass
class InvoiceData:
    """Enhanced invoice data class with advanced features"""
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
    status: str = "unpaid"
    tags: List[str] = None
    blockchain_hash: str = ""
    security_signature: str = ""
    
    def __post_init__(self):
        if self.line_items is None:
            self.line_items = []
        if self.validation_errors is None:
            self.validation_errors = []
        if self.extracted_fields is None:
            self.extracted_fields = {}
        if self.tags is None:
            self.tags = []

@dataclass
class Budget:
    """Enhanced budget tracking with AI forecasting"""
    category: str
    monthly_limit: float
    current_spent: float = 0.0
    period_start: str = ""
    period_end: str = ""
    alert_threshold: float = 0.8
    auto_adjust: bool = False
    historical_data: List[Dict] = None
    trend_analysis: Dict = None
    variance_threshold: float = 0.1
    last_updated: str = "2025-06-08 15:53:19"
    
    def __post_init__(self):
        if self.historical_data is None:
            self.historical_data = []
        if self.trend_analysis is None:
            self.trend_analysis = {}

@dataclass
class CashFlowProjection:
    """Enhanced cash flow projection with ML predictions"""
    date: str
    projected_inflow: float = 0.0
    projected_outflow: float = 0.0
    net_cash_flow: float = 0.0
    running_balance: float = 0.0
    confidence_score: float = 0.0
    risk_factors: List[str] = None
    ai_insights: List[str] = None
    
    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
        if self.ai_insights is None:
            self.ai_insights = []
