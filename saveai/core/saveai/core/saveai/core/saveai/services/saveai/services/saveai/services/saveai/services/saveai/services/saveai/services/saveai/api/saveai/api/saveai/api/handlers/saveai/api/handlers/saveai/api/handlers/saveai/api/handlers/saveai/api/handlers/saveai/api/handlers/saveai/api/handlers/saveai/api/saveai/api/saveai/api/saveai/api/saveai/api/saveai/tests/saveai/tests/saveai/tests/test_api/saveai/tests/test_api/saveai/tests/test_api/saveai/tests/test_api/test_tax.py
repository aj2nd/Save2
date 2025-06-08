"""
Tax API Tests
Version: 1.0.0
Created: 2025-06-08 18:19:51
Author: anandhu723
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

pytestmark = pytest.mark.asyncio

async def test_calculate_tax(
    test_client: TestClient,
    auth_headers: dict,
    sample_transaction_data: dict
):
    """Test tax calculation"""
    tax_request = {
        "request_id": "test_req_008",
        "transaction_id": sample_transaction_data["transaction_id"],
        "amount": Decimal("100.50"),
        "tax_type": "VAT",
        "country_code": "AE"
    }
    
    response = test_client.post(
        "/api/v1/tax/calculate",
        headers=auth_headers,
        json=tax_request
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "tax_amount" in data
    assert "tax_rate" in data
    assert "breakdown" in data
    assert isinstance(data["tax_amount"], (int, float))

async def test_generate_tax_report(
    test_client: TestClient,
    auth_headers: dict,
    sample_user_data: dict
):
    """Test tax report generation"""
    response = test_client.get(
        "/api/v1/tax/report/2025",
        headers=auth_headers,
        params={
            "user_id": sample_user_data["user_id"],
            "quarter": 2
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "period" in data
    assert "summary" in data
    assert "transactions" in data
    assert data["period"]["year"] == 2025
    assert data["period"]["quarter"] == 2

async def test_estimate_tax_liability(
    test_client: TestClient,
    auth_headers: dict,
    sample_user_data: dict
):
    """Test tax liability estimation"""
    response = test_client.get(
        "/api/v1/tax/estimate",
        headers=auth_headers,
        params={
            "user_id": sample_user_data["user_id"],
            "year": 2025
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "estimated_liability" in data
    assert "confidence_score" in data
    assert "factors" in data

async def test_get_tax_calendar(
    test_client: TestClient,
    auth_headers: dict
):
    """Test tax calendar retrieval"""
    response = test_client.get(
        "/api/v1/tax/calendar/2025",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "deadlines" in data
    assert "reminders" in data
    assert isinstance(data["deadlines"], list)
    assert len(data["deadlines"]) > 0

async def test_invalid_tax_calculation(
    test_client: TestClient,
    auth_headers: dict
):
    """Test tax calculation with invalid data"""
    invalid_request = {
        "request_id": "test_req_009",
        "transaction_id": "invalid_id",
        "amount": -100,  # Invalid negative amount
        "tax_type": "VAT",
        "country_code": "AE"
    }
    
    response = test_client.post(
        "/api/v1/tax/calculate",
        headers=auth_headers,
        json=invalid_request
    )
    
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert "amount" in data["error"].lower()

async def test_tax_report_invalid_year(
    test_client: TestClient,
    auth_headers: dict,
    sample_user_data: dict
):
    """Test tax report for invalid year"""
    response = test_client.get(
        "/api/v1/tax/report/2030",  # Future year
        headers=auth_headers,
        params={"user_id": sample_user_data["user_id"]}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert "year" in data["error"].lower()

async def test_tax_calculation_by_category(
    test_client: TestClient,
    auth_headers: dict,
    sample_transaction_data: dict
):
    """Test tax calculation with different categories"""
    categories = ["business", "personal", "investment"]
    
    for category in categories:
        tax_request = {
            "request_id": f"test_req_{category}",
            "transaction_id": sample_transaction_data["transaction_id"],
            "amount": Decimal("100.00"),
            "tax_type": "VAT",
            "country_code": "AE",
            "category": category
        }
        
        response = test_client.post(
            "/api/v1/tax/calculate",
            headers=auth_headers,
            json=tax_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "category" in data
        assert data["category"] == category

async def test_tax_report_aggregation(
    test_client: TestClient,
    auth_headers: dict,
    sample_user_data: dict
):
    """Test tax report aggregation by different periods"""
    periods = ["monthly", "quarterly", "yearly"]
    
    for period in periods:
        response = test_client.get(
            "/api/v1/tax/report/2025",
            headers=auth_headers,
            params={
                "user_id": sample_user_data["user_id"],
                "aggregation": period
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "aggregation" in data
        assert data["aggregation"]["type"] == period

async def test_tax_jurisdiction_rules(
    test_client: TestClient,
    auth_headers: dict,
    sample_transaction_data: dict
):
    """Test tax calculations for different jurisdictions"""
    jurisdictions = [
        {"country": "AE", "expected_rate": 0.05},
        {"country": "SA", "expected_rate": 0.15},
        {"country": "UK", "expected_rate": 0.20}
    ]
    
    for jurisdiction in jurisdictions:
        tax_request = {
            "request_id": f"test_req_{jurisdiction['country']}",
            "transaction_id": sample_transaction_data["transaction_id"],
            "amount": Decimal("100.00"),
            "tax_type": "VAT",
            "country_code": jurisdiction["country"]
        }
        
        response = test_client.post(
            "/api/v1/tax/calculate",
            headers=auth_headers,
            json=tax_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tax_rate" in data
        assert float(data["tax_rate"]) == jurisdiction["expected_rate"]

async def test_tax_exemption_handling(
    test_client: TestClient,
    auth_headers: dict,
    sample_transaction_data: dict
):
    """Test handling of tax exemptions"""
    tax_request = {
        "request_id": "test_req_exempt",
        "transaction_id": sample_transaction_data["transaction_id"],
        "amount": Decimal("100.00"),
        "tax_type": "VAT",
        "country_code": "AE",
        "exemption_code": "EDU001"  # Education exemption
    }
    
    response = test_client.post(
        "/api/v1/tax/calculate",
        headers=auth_headers,
        json=tax_request
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "tax_amount" in data
    assert float(data["tax_amount"]) == 0
    assert "exemption_applied" in data
    assert data["exemption_applied"] is True
