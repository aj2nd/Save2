"""
Blockchain API Handler
Version: 1.0.0
Created: 2025-06-08 17:51:02
Author: anandhu723
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException
from datetime import datetime

from .base import BaseHandler
from ...core.models import Transaction
from ...services.blockchain import BlockchainService
from ...services.security import SecurityService

class BlockchainHandler(BaseHandler):
    """Handles blockchain-related API endpoints"""
    
    def __init__(self):
        super().__init__()
        self.blockchain_service = BlockchainService()
        self.security_service = SecurityService()
    
    async def verify_transaction(self, blockchain_hash: str) -> Dict[str, Any]:
        """Verify transaction on blockchain"""
        try:
            # Security validation
            security_check = self.security_service.validate_request({
                "blockchain_hash": blockchain_hash,
                "action": "verify",
                "scope": "blockchain"
            })
            
            if not security_check["valid"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Verify on blockchain
            verification = self.blockchain_service.verify_transaction(blockchain_hash)
            
            if not verification:
                raise HTTPException(
                    status_code=404,
                    detail="Transaction not found on blockchain"
                )
            
            return self.format_response({
                "blockchain_hash": blockchain_hash,
                "verification": verification,
                "timestamp": datetime.utcnow()
            })
            
        except HTTPException as he:
            return await self.handle_error(he)
        except Exception as e:
            return await self.handle_error(e)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get blockchain network status"""
        try:
            # Get smart contract status
            status = self.blockchain_service.get_smart_contract_status()
            
            if not status:
                raise HTTPException(
                    status_code=500,
                    detail="Unable to fetch blockchain status"
                )
            
            return self.format_response({
                "status": status,
                "timestamp": datetime.utcnow()
            })
            
        except HTTPException as he:
            return await self.handle_error(he)
        except Exception as e:
            return await self.handle_error(e)
    
    async def get_transaction_history(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get blockchain transaction history"""
        try:
            # Security validation
            security_check = self.security_service.validate_request({
                "user_id": user_id,
                "action": "read",
                "scope": "history"
            })
            
            if not security_check["valid"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Get transactions from blockchain
            transactions = self.blockchain_service._get_transaction_history(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return self.format_response({
                "user_id": user_id,
                "transactions": transactions,
                "period": {
                    "start": start_date,
                    "end": end_date
                }
            })
            
        except HTTPException as he:
            return await self.handle_error(he)
        except Exception as e:
            return await self.handle_error(e)
    
    async def get_smart_contract_metrics(self) -> Dict[str, Any]:
        """Get smart contract performance metrics"""
        try:
            # Get contract metrics
            metrics = {
                "total_transactions": self.blockchain_service._get_total_transactions(),
                "contract_balance": self.blockchain_service._get_contract_balance(),
                "network": self.blockchain_service.network,
                "contract_address": self.blockchain_service.contract_address,
                "performance": {
                    "avg_block_time": 15,  # seconds
                    "gas_usage": self._calculate_gas_usage(),
                    "success_rate": 0.99
                }
            }
            
            return self.format_response({
                "metrics": metrics,
                "timestamp": datetime.utcnow()
            })
            
        except Exception as e:
            return await self.handle_error(e)
    
    def _calculate_gas_usage(self) -> Dict[str, float]:
        """Calculate gas usage metrics"""
        return {
            "average": 50000,  # wei
            "highest": 80000,
            "lowest": 21000,
            "total": 1500000
        }
