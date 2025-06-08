"""
Security API Tests
Version: 1.0.0
Created: 2025-06-08 18:18:55
Author: anandhu723
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any
import jwt

pytestmark = pytest.mark.asyncio

async def test_generate_token(
    test_client: TestClient,
    sample_token_request: dict
):
    """Test token generation"""
    response = test_client.post(
        "/api/v1/security/token",
        json=sample_token_request.dict()
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "expires_at" in data
    assert isinstance(data["permissions"], list)
    
    # Verify token structure
    token = data["token"]
    decoded = jwt.decode(token, verify=False)
    assert "user_id" in decoded
    assert "permissions" in decoded
    assert "exp" in decoded

async def test_validate_request(
    test_client: TestClient,
    auth_headers: dict
):
    """Test request validation"""
    validation_request = {
        "request_id": "test_req_003",
        "token": auth_headers["Authorization"].split()[1],
        "resource": "transactions",
        "action": "read"
    }
    
    response = test_client.post(
        "/api/v1/security/validate",
        headers=auth_headers,
        json=validation_request
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "security_level" in data

async def test_encrypt_data(
    test_client: TestClient,
    auth_headers: dict
):
    """Test data encryption"""
    sensitive_data = {
        "request_id": "test_req_004",
        "data": {
            "card_number": "4111111111111111",
            "cvv": "123"
        }
    }
    
    response = test_client.post(
        "/api/v1/security/encrypt",
        headers=auth_headers,
        json=sensitive_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "encrypted_data" in data
    assert data["encrypted_data"] != str(sensitive_data["data"])

async def test_audit_security(
    test_client: TestClient,
    auth_headers: dict,
    sample_user_data: dict
):
    """Test security audit log retrieval"""
    response = test_client.get(
        "/api/v1/security/audit",
        headers=auth_headers,
        params={
            "user_id": sample_user_data["user_id"],
            "days": 7
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "audit_logs" in data
    assert isinstance(data["audit_logs"], list)
    assert "summary" in data

async def test_invalid_token_request(
    test_client: TestClient
):
    """Test token generation with invalid request"""
    invalid_request = {
        "request_id": "test_req_005",
        "user_id": "",  # Invalid empty user_id
        "permissions": ["read", "write"],
        "expiry_hours": 24
    }
    
    response = test_client.post(
        "/api/v1/security/token",
        json=invalid_request
    )
    
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert "user_id" in data["error"].lower()

async def test_expired_token(
    test_client: TestClient,
    sample_user_data: dict
):
    """Test validation of expired token"""
    # Create expired token
    expired_token = jwt.encode(
        {
            "user_id": sample_user_data["user_id"],
            "exp": datetime.utcnow() - timedelta(hours=1)
        },
        "test_secret"
    )
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = test_client.get(
        "/api/v1/security/audit",
        headers=headers
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "expired" in data["error"].lower()

async def test_invalid_permissions(
    test_client: TestClient,
    auth_headers: dict
):
    """Test access with invalid permissions"""
    validation_request = {
        "request_id": "test_req_006",
        "token": auth_headers["Authorization"].split()[1],
        "resource": "admin",
        "action": "write"
    }
    
    response = test_client.post(
        "/api/v1/security/validate",
        headers=auth_headers,
        json=validation_request
    )
    
    assert response.status_code == 403
    data = response.json()
    assert data["valid"] is False
    assert "permission" in data["error"].lower()

async def test_security_rate_limiting(
    test_client: TestClient
):
    """Test rate limiting for token generation"""
    responses = []
    for _ in range(20):  # Attempt multiple token generations
        response = test_client.post(
            "/api/v1/security/token",
            json=sample_token_request.dict()
        )
        responses.append(response)
    
    assert any(r.status_code == 429 for r in responses)

async def test_encryption_key_rotation(
    test_client: TestClient,
    auth_headers: dict
):
    """Test encryption with key rotation"""
    data_to_encrypt = {
        "request_id": "test_req_007",
        "data": "sensitive_info",
        "rotate_key": True
    }
    
    response = test_client.post(
        "/api/v1/security/encrypt",
        headers=auth_headers,
        json=data_to_encrypt
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "key_version" in data
    assert data["key_version"] > 1

async def test_audit_log_filtering(
    test_client: TestClient,
    auth_headers: dict
):
    """Test audit log filtering"""
    response = test_client.get(
        "/api/v1/security/audit",
        headers=auth_headers,
        params={
            "event_type": "authentication",
            "severity": "high"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "audit_logs" in data
    for log in data["audit_logs"]:
        assert log["event_type"] == "authentication"
        assert log["severity"] == "high"
