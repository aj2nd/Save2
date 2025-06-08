"""
Transaction API Handler
Version: 1.0.0
Created: 2025-06-08 17:48:22
Author: anandhu723
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException
from datetime import datetime

from .base import BaseHandler
from ...core.models import Transaction, TransactionType
from ...services.blockchain import BlockchainService
from ...services.security import SecurityService

class TransactionHandler(BaseHandler):
    """Handles transaction-related API endpoints"""
    
    def __init__(self):
        super().__init__()
        self.blockchain_service = BlockchainService()
        self.security_service = SecurityService()
    
    async def create_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new financial transaction"""
        try:
            # Validate request
            if not self.validate_request(data):
                raise HTTPException(status_code=400, detail="Invalid request data")
            
            # Security validation
            security_validation = self.security_service.validate_transaction({
                "user_id": data.get("user_id"),
                "amount": data.get("amount"),
                "type": data.get("type"),
                "metadata": data.get("metadata", {})
            })
            
            if not security_validation["valid"]:
                raise HTTPException(status_code=403, detail="Security validation failed")
            
            # Create transaction
            transaction = Transaction(
                id=data.get("id"),
                type=TransactionType(data.get("type")),
                amount=data.get("amount"),
                currency=data.get("currency", "AED"),
                timestamp=datetime.utcnow(),
                status="pending",
                user_id=data.get("user_id"),
                metadata=data.get("metadata", {}),
            )
            
            # Record on blockchain
            blockchain_result = self.blockchain_service.record_transaction(transaction)
            if not blockchain_result:
                raise HTTPException(status_code=500, detail="Blockchain recording failed")
            
            # Update transaction with blockchain hash
            transaction.blockchain_hash = blockchain_result.get("blockchain_hash")
            
            return self.format_response({
                "transaction": transaction.__dict__,
                "blockchain_hash": blockchain_result.get("blockchain_hash"),
                "security_level": security_validation["security_level"]
            })
            
        except HTTPException as he:
            return await self.handle_error(he)
        except Exception as e:
            return await self.handle_error(e)
    
    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Retrieve transaction details"""
        try:
            # Security check
            security_check = self.security_service.validate_request({
                "transaction_id": transaction_id,
                "action": "read"
            })
            
            if not security_check["valid"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Get blockchain verification
            blockchain_verification = self.blockchain_service.verify_transaction(transaction_id)
            if not blockchain_verification:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            return self.format_response({
                "transaction": blockchain_verification.get("transaction"),
                "verification": blockchain_verification.get("verification"),
                "timestamp": datetime.utcnow()
            })
            
        except HTTPException as he:
            return await self.handle_error(he)
        except Exception as e:
            return await self.handle_error(e)
    
    async def update_transaction_status(self, transaction_id: str, status: str) -> Dict[str, Any]:
        """Update transaction status"""
        try:
            # Security check
            security_check = self.security_service.validate_request({
                "transaction_id": transaction_id,
                "action": "update",
                "new_status": status
            })
            
            if not security_check["valid"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Update blockchain record
            update_result = self.blockchain_service.update_transaction(
                transaction_id,
                {"status": status}
            )
            
            if not update_result:
                raise HTTPException(status_code=500, detail="Update failed")
            
            return self.format_response({
                "transaction_id": transaction_id,
                "status": status,
                "updated_at": datetime.utcnow()
            })
            
        except HTTPException as he:
            return await self.handle_error(he)
        except Exception as e:
            return await self.handle_error(e)
