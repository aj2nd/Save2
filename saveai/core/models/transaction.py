"""
Transaction Models
Version: 1.0.0
Created: 2025-06-08 23:39:20
Author: anandhu723
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class TransactionType(str, Enum):
    """Transaction type enumeration"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"

class TransactionStatus(str, Enum):
    """Transaction status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Transaction(BaseModel):
    """Transaction model"""
    id: UUID
    type: TransactionType
    amount: float = Field(..., gt=0)
    currency: str = Field(default="AED", min_length=3, max_length=3)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    user_id: UUID
    blockchain_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
