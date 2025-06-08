"""
Transaction Service Tests
Version: 1.0.0
Created: 2025-06-08 23:35:36
Author: anandhu723
"""

import pytest
from datetime import datetime
from uuid import uuid4

from saveai.services.transaction import TransactionService
from saveai.core.models import Transaction, TransactionType
from saveai.core.config import Config

@pytest.fixture
def transaction_service():
    """Create a transaction service instance for testing"""
    return TransactionService()

@pytest.fixture
def sample_transaction_data():
    """Create sample transaction data for testing"""
    return {
        'type': 'deposit',
        'amount': 1000.00,
        'currency': 'AED',
        'user_id': str(uuid4()),
        'metadata': {
            'description': 'Test transaction',
            'category': 'testing'
        }
    }

@pytest.mark.asyncio
async def test_create_transaction(transaction_service, sample_transaction_data):
    """Test creating a new transaction"""
    transaction = await transaction_service.create_transaction(sample_transaction_data)
    
    assert transaction is not None
    assert isinstance(transaction, Transaction)
    assert transaction.type == TransactionType.DEPOSIT
    assert transaction.amount == 1000.00
    assert transaction.currency == 'AED'
    assert transaction.status == 'completed'
    assert transaction.blockchain_hash is not None

@pytest.mark.asyncio
async def test_get_transaction(transaction_service, sample_transaction_data):
    """Test retrieving a transaction"""
    # Create a transaction first
    created_transaction = await transaction_service.create_transaction(sample_transaction_data)
    
    # Try to retrieve it
    retrieved_transaction = await transaction_service.get_transaction(created_transaction.id)
    
    assert retrieved_transaction is not None
    assert retrieved_transaction.id == created_transaction.id
    assert retrieved_transaction.blockchain_hash == created_transaction.blockchain_hash

@pytest.mark.asyncio
async def test_get_user_transactions(transaction_service, sample_transaction_data):
    """Test retrieving user transactions"""
    # Create a few transactions
    user_id = sample_transaction_data['user_id']
    await transaction_service.create_transaction(sample_transaction_data)
    await transaction_service.create_transaction(sample_transaction_data)
    
    # Get user transactions
    transactions = await transaction_service.get_user_transactions(user_id)
    
    assert len(transactions) >= 2
    assert all(t.user_id == user_id for t in transactions)

@pytest.mark.asyncio
async def test_transaction_validation_failure(transaction_service):
    """Test transaction validation failure"""
    invalid_data = {
        'type': 'deposit',
        'amount': -100.00,  # Invalid negative amount
        'currency': 'AED',
        'user_id': str(uuid4())
    }
    
    with pytest.raises(ValueError) as exc_info:
        await transaction_service.create_transaction(invalid_data)
    assert "validation failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_transaction_blockchain_failure(transaction_service, sample_transaction_data, monkeypatch):
    """Test blockchain recording failure"""
    # Mock blockchain service to simulate failure
    async def mock_record_transaction(*args, **kwargs):
        return None
    
    monkeypatch.setattr(
        transaction_service.blockchain_service,
        'record_transaction',
        mock_record_transaction
    )
    
    with pytest.raises(ValueError) as exc_info:
        await transaction_service.create_transaction(sample_transaction_data)
    assert "blockchain" in str(exc_info.value)
