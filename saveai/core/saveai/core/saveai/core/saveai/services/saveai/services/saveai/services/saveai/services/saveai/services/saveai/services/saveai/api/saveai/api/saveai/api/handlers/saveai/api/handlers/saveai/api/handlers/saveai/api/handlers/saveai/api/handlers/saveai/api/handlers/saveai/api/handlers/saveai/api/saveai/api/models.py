"""
API Request/Response Models
Version: 1.0.0
Created: 2025-06-08 18:07:18
Author: anandhu723
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal

class TransactionType(str, Enum):
    """Transaction type enumeration"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"

class SecurityLevel(str, Enum):
    """Security level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Base Models
class BaseRequest(BaseModel):
    """Base request model"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(...)

class BaseResponse(BaseModel):
    """Base response model"""
    status: str = Field(default="success")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
# Transaction Models
class TransactionRequest(BaseRequest):
    """Transaction creation request"""
    amount: Decimal = Field(..., gt=0)
    type: TransactionType
    currency: str = Field(default="AED")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code"""
        if len(v) != 3 or not v.isalpha():
            raise ValueError('Invalid currency code')
        return v.upper()

class TransactionResponse(BaseResponse):
    """Transaction response"""
    transaction_id: str
    status: str
    blockchain_hash: Optional[str]
    security_validation: Dict[str, Any]

# Analytics Models
class AnalyticsRequest(BaseRequest):
    """Analytics request"""
    user_id: str
    timeframe_days: Optional[int] = Field(default=30, gt=0, le=365)
    categories: Optional[List[str]] = None

class AnalyticsResponse(BaseResponse):
    """Analytics response"""
    insights: List[Dict[str, Any]]
    period: Dict[str, datetime]
    summary: Dict[str, Any]

# Blockchain Models
class BlockchainVerificationRequest(BaseRequest):
    """Blockchain verification request"""
    blockchain_hash: str
    verification_type: str = Field(default="full")

class BlockchainVerificationResponse(BaseResponse):
    """Blockchain verification response"""
    verified: bool
    transaction_data: Optional[Dict[str, Any]]
    verification_details: Dict[str, Any]

# Security Models
class TokenRequest(BaseRequest):
    """Token generation request"""
    user_id: str
    permissions: List[str]
    expiry_hours: Optional[int] = Field(default=24, gt=0, le=720)

class TokenResponse(BaseResponse):
    """Token response"""
    token: str
    expires_at: datetime
    permissions: List[str]

class SecurityValidationRequest(BaseRequest):
    """Security validation request"""
    token: str
    resource: str
    action: str
    metadata: Optional[Dict[str, Any]] = None

class SecurityValidationResponse(BaseResponse):
    """Security validation response"""
    valid: bool
    security_level: SecurityLevel
    metadata: Optional[Dict[str, Any]] = None

# Tax Models
class TaxCalculationRequest(BaseRequest):
    """Tax calculation request"""
    transaction_id: str
    amount: Decimal
    tax_type: str = Field(default="VAT")
    country_code: str = Field(default="AE")

class TaxCalculationResponse(BaseResponse):
    """Tax calculation response"""
    tax_amount: Decimal
    tax_rate: Decimal
    breakdown: Dict[str, Any]
    metadata: Dict[str, Any]

class TaxReportRequest(BaseRequest):
    """Tax report request"""
    user_id: str
    year: int
    quarter: Optional[int] = Field(None, ge=1, le=4)

class TaxReportResponse(BaseResponse):
    """Tax report response"""
    user_id: str
    period: Dict[str, Any]
    summary: Dict[str, Any]
    transactions: List[Dict[str, Any]]

# Response Models for Lists
class ListResponse(BaseResponse):
    """Generic list response"""
    total: int
    page: int
    page_size: int
    items: List[Any]

# Error Models
class ErrorResponse(BaseModel):
    """Error response"""
    status: str = Field(default="error")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None

# Validation Models
class ValidationError(BaseModel):
    """Validation error"""
    field: str
    message: str
    code: str

class ValidationResponse(BaseModel):
    """Validation response"""
    valid: bool
    errors: Optional[List[ValidationError]] = None
