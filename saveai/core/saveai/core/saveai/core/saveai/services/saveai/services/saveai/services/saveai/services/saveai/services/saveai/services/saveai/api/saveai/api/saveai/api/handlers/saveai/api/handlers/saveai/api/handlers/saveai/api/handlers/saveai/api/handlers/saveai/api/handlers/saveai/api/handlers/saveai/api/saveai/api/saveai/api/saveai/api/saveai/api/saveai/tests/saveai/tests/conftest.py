"""
PyTest Configuration and Fixtures
Version: 1.0.0
Created: 2025-06-08 18:11:57
Author: anandhu723
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any, Generator
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from ..api.config import get_settings, APISettings
from ..api.models import (
    TransactionType,
    SecurityLevel,
    TransactionRequest,
    TokenRequest
)

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_settings() -> APISettings:
    """Get test settings"""
    settings = get_settings()
    settings.DATABASE_URL = "sqlite:///./test.db"
    settings.REDIS_URL = "redis://localhost:6379/1"
    settings.DEBUG = True
    return settings

@pytest.fixture(scope="function")
def test_client(test_settings) -> Generator:
    """Create test client"""
    from fastapi import FastAPI
    from ..api.router import setup_api
    from ..api.middleware import setup_middleware
    
    app = FastAPI()
    setup_api(app)
    setup_middleware(app)
    
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
def auth_headers() -> Dict[str, str]:
    """Create authentication headers"""
    return {
        "Authorization": "Bearer test_token",
        "X-API-Key": "test_api_key"
    }

@pytest.fixture(scope="function")
def sample_transaction() -> TransactionRequest:
    """Create sample transaction"""
    return TransactionRequest(
        request_id="test_req_001",
        amount=Decimal("100.50"),
        type=TransactionType.PAYMENT,
        currency="AED",
        metadata={
            "description": "Test payment",
            "category": "testing"
        }
    )

@pytest.fixture(scope="function")
def sample_token_request() -> TokenRequest:
    """Create sample token request"""
    return TokenRequest(
        request_id="test_req_002",
        user_id="test_user",
        permissions=["read", "write"],
        expiry_hours=24
    )

@pytest.fixture(scope="session")
def blockchain_mock():
    """Mock blockchain service"""
    class BlockchainMock:
        def verify_transaction(self, hash: str) -> Dict[str, Any]:
            return {
                "verified": True,
                "timestamp": datetime.utcnow(),
                "block_number": 12345
            }
    return BlockchainMock()

@pytest.fixture(scope="session")
def analytics_mock():
    """Mock analytics service"""
    class AnalyticsMock:
        def analyze_spending(self, user_id: str) -> Dict[str, Any]:
            return {
                "total_spend": 1000.00,
                "categories": {
                    "food": 300.00,
                    "transport": 200.00,
                    "entertainment": 500.00
                }
            }
    return AnalyticsMock()

# Database Fixtures
@pytest.fixture(scope="function")
async def test_db():
    """Create test database"""
    # Setup test database
    yield
    # Cleanup test database

# Test Data Fixtures
@pytest.fixture(scope="function")
def sample_user_data() -> Dict[str, Any]:
    """Create sample user data"""
    return {
        "user_id": "test_user",
        "email": "test@saveai.com",
        "tier": "standard",
        "created_at": datetime.utcnow()
    }

@pytest.fixture(scope="function")
def sample_transaction_data() -> Dict[str, Any]:
    """Create sample transaction data"""
    return {
        "transaction_id": "tr_001",
        "user_id": "test_user",
        "amount": 100.50,
        "currency": "AED",
        "type": "payment",
        "status": "completed",
        "created_at": datetime.utcnow()
    }

# Utility Fixtures
@pytest.fixture(scope="function")
def time_machine():
    """Time travel utility"""
    class TimeMachine:
        @staticmethod
        def travel(days: int) -> datetime:
            return datetime.utcnow() + timedelta(days=days)
    return TimeMachine()

@pytest.fixture(scope="function")
def error_generator():
    """Generate test errors"""
    class ErrorGenerator:
        @staticmethod
        def validation_error():
            return {
                "error": "validation_error",
                "details": "Invalid input data"
            }
            
        @staticmethod
        def permission_error():
            return {
                "error": "permission_denied",
                "details": "Insufficient permissions"
            }
    return ErrorGenerator()
