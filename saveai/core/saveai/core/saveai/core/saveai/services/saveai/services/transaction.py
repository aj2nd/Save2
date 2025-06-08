"""
Transaction Service for SaveAI
Version: 1.0.0
Created: 2025-06-08 23:21:15
Author: anandhu723
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4

from ..core.models import Transaction, TransactionType
from ..core.config import Config
from .blockchain import BlockchainService
from .security import SecurityService

class TransactionService:
    """Handles transaction processing and management"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.initialized_at = datetime.utcnow()
        self._setup_logging()
        self.blockchain_service = BlockchainService()
        self.security_service = SecurityService()
        
    def _setup_logging(self) -> None:
        """Configure logging for transaction operations"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
    
    async def create_transaction(self, transaction_data: Dict[str, Any]) -> Transaction:
        """
        Create a new transaction with security validation and blockchain recording
        """
        try:
            # Generate transaction ID
            transaction_id = str(uuid4())
            
            # Create transaction object
            transaction = Transaction(
                id=transaction_id,
                type=TransactionType(transaction_data['type']),
                amount=float(transaction_data['amount']),
                currency=transaction_data.get('currency', 'AED'),
                timestamp=datetime.utcnow(),
                status='pending',
                user_id=transaction_data['user_id'],
                metadata=transaction_data.get('metadata', {}),
            )
            
            # Validate security
            security_validation = self.security_service.validate_transaction(transaction)
            if not security_validation['valid']:
                self.logger.error(f"Security validation failed for transaction {transaction_id}")
                raise ValueError(f"Security validation failed: {security_validation.get('error', 'Unknown error')}")
            
            # Record on blockchain
            blockchain_result = self.blockchain_service.record_transaction(transaction)
            if not blockchain_result:
                self.logger.error(f"Blockchain recording failed for transaction {transaction_id}")
                raise ValueError("Failed to record transaction on blockchain")
            
            # Update transaction with blockchain hash
            transaction.blockchain_hash = blockchain_result.get('blockchain_hash')
            transaction.status = 'completed'
            
            # Log success
            self.logger.info(f"Successfully created transaction {transaction_id}")
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"Error creating transaction: {str(e)}")
            raise
    
    async def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """
        Retrieve a transaction by ID with blockchain verification
        """
        try:
            # Verify on blockchain
            blockchain_verification = self.blockchain_service.verify_transaction(transaction_id)
            if not blockchain_verification:
                self.logger.error(f"Transaction {transaction_id} not found on blockchain")
                return None
            
            # Get transaction details
            transaction = blockchain_verification.get('transaction')
            if not transaction:
                self.logger.error(f"Transaction {transaction_id} details not found")
                return None
            
            return Transaction(**transaction)
            
        except Exception as e:
            self.logger.error(f"Error retrieving transaction: {str(e)}")
            raise
    
    async def get_user_transactions(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[TransactionType] = None
    ) -> List[Transaction]:
        """
        Get all transactions for a user with optional filters
        """
        try:
            # Security check
            security_check = self.security_service.validate_request({
                'user_id': user_id,
                'action': 'read',
                'scope': 'transactions'
            })
            
            if not security_check['valid']:
                raise ValueError("Access denied")
            
            # Get transactions from blockchain
            transactions = self.blockchain_service._get_transaction_history(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Filter by type if specified
            if transaction_type:
                transactions = [
                    t for t in transactions
                    if t.get('type') == transaction_type.value
                ]
            
            return [Transaction(**t) for t in transactions]
            
        except Exception as e:
            self.logger.error(f"Error getting user transactions: {str(e)}")
            raise
