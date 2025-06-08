"""
Transaction Repository
Version: 1.0.0
Created: 2025-06-08 23:39:20
Author: anandhu723
"""

from typing import List, Optional
from datetime import datetime
import asyncpg
from uuid import UUID

from ..models import Transaction, TransactionType, TransactionStatus
from ..config import Settings

class TransactionRepository:
    """Handles database operations for transactions"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self) -> None:
        """Initialize database connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(str(self.settings.DATABASE_URL))
    
    async def create(self, transaction: Transaction) -> Transaction:
        """Create a new transaction record"""
        query = """
        INSERT INTO transactions (
            id, type, amount, currency, timestamp, status,
            user_id, blockchain_hash, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
        """
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(
                query,
                transaction.id,
                transaction.type,
                transaction.amount,
                transaction.currency,
                transaction.timestamp,
                transaction.status,
                transaction.user_id,
                transaction.blockchain_hash,
                transaction.metadata
            )
            return Transaction(**dict(record))
    
    async def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """Get a transaction by ID"""
        query = "SELECT * FROM transactions WHERE id = $1"
        async with self.pool.acquire() as conn:
            if record := await conn.fetchrow(query, transaction_id):
                return Transaction(**dict(record))
        return None
    
    async def get_user_transactions(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[TransactionType] = None
    ) -> List[Transaction]:
        """Get all transactions for a user with optional filters"""
        query = "SELECT * FROM transactions WHERE user_id = $1"
        params = [user_id]
        
        if start_date:
            query += " AND timestamp >= $2"
            params.append(start_date)
        
        if end_date:
            query += f" AND timestamp <= ${len(params) + 1}"
            params.append(end_date)
        
        if transaction_type:
            query += f" AND type = ${len(params) + 1}"
            params.append(transaction_type)
        
        query += " ORDER BY timestamp DESC"
        
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, *params)
            return [Transaction(**dict(record)) for record in records]
    
    async def update_status(
        self,
        transaction_id: UUID,
        status: TransactionStatus,
        blockchain_hash: Optional[str] = None
    ) -> Optional[Transaction]:
        """Update transaction status and blockchain hash"""
        query = """
        UPDATE transactions
        SET status = $1, blockchain_hash = $2, updated_at = NOW()
        WHERE id = $3
        RETURNING *
        """
        async with self.pool.acquire() as conn:
            if record := await conn.fetchrow(query, status, blockchain_hash, transaction_id):
                return Transaction(**dict(record))
        return None
