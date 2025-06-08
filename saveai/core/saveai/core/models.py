"""
Data Models for SaveAI
Version: 1.0.0
Created: 2025-06-08 17:28:44
Author: anandhu723
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

class TransactionType(Enum):
    """Types of transactions supported by the system"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    INVESTMENT = "investment"
    TAX_PAYMENT = "tax_payment"

class SecurityLevel(Enum):
    """Security levels for different operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Transaction:
    """Represents a financial transaction"""
    id: str
    type: TransactionType
    amount: float
    currency: str
    timestamp: datetime
    status: str
    user_id: str
    metadata: Dict[str, Any]
    blockchain_hash: Optional[str] = None
    tax_details: Optional[Dict[str, Any]] = None

@dataclass
class AnalyticsData:
    """Analytics data for tracking and analysis"""
    id: str
    transaction_id: str
    metrics: Dict[str, float]
    timestamp: datetime
    category: str
    processed: bool = False

@dataclass
class TaxRecord:
    """Tax record for financial transactions"""
    id: str
    transaction_id: str
    vat_amount: float
    tax_year: int
    category: str
    filing_status: str
    timestamp: datetime
    details: Dict[str, Any]
