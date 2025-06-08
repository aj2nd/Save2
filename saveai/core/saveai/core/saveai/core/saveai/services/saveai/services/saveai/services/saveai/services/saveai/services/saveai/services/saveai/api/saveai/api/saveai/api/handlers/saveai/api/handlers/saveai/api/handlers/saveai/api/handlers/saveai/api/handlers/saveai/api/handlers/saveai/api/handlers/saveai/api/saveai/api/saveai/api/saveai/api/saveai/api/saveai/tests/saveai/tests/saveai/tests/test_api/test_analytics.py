"""
Analytics API Tests
Version: 1.0.0
Created: 2025-06-08 18:14:35
Author: anandhu723
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any

pytestmark = pytest.mark.asyncio

async def test_analyze_spending(
    test_client: TestClient,
    auth_headers: dict,
    sample_user_data: dict,
    analytics_mock
):
    """Test spending analysis endpoint"""
    response = test_client.get(
        "/api/v1/analytics/spending",
        headers=auth_headers,
        params={
            "user_id": sample_user_data["user_id"],
            "timeframe_days": 30
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_spend" in data
    assert "categories" in data
    assert isinstance(data["categories"], dict)
    assert len(data["categories"]) > 0

async def test_get_insights(
    test_client: TestClient,
    auth_headers: dict,
    sample_user_data: dict
):
    """Test getting financial insights"""
    response = test_client.get(
        "/api/v1/analytics/insights",
        headers=auth_headers,
        params={"user_id": sample_user_data["user_id"]}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "insights" in data
    assert isinstance(data["insights"], list)
    assert "summary" in data

async def test_get_trends(
    test_client: TestClient,
    auth_headers: dict,
    sample_user_data: dict
):
    """Test getting spending trends"""
    response = test_client.get(
        "/api/v1/analytics/trends",
        headers=auth_headers,
        params={
            "user_id": sample_user_data["user_id"],
            "category": "food"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "trends" in data
    assert "period" in data
    assert isinstance(data["trends"], list)

async def test_invalid_timeframe(
    test_client: TestClient,
    auth_headers: dict,
    sample_user_data: dict
):
    """Test analytics with invalid timeframe"""
    response = test_client.get(
        "/api/v1/analytics/spending",
        headers=auth_headers,
        params={
            "user_id": sample_user_data["user_id"],
            "timeframe_days": 400  # Exceeds maximum allowed
        }
    )
    
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert "timeframe" in data["error"].lower()

async def test_category_analysis(
    test_client: TestClient,
    auth_headers: dict,
    sample_user_data: dict
):
    """Test category-specific analysis"""
    categories = ["food", "transport", "entertainment"]
    
    response = test_client.get(
        "/api/v1/analytics/spending",
        headers=auth_headers,
        params={
            "user_id": sample_user_data["user_id"],
            "categories": categories
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    for category in categories:
        assert category in data["categories"]

async def test_trend_comparison(
    test_client: TestClient,
    auth_headers: dict,
    sample_user_data: dict
):
    """Test trend comparison between periods"""
    response = test_client.get(
        "/api/v1/analytics/trends",
        headers=auth_headers,
        params={
            "user_id": sample_user_data["user_id"],
            "compare_periods": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "comparison" in data
    assert "current_period" in data["comparison"]
    assert "previous_period" in data["comparison"]

async def test_unauthorized_analytics_access(
    test_client: TestClient,
    sample_user_data: dict
):
    """Test unauthorized access to analytics"""
    response = test_client.get(
        "/api/v1/analytics/insights",
        params={"user_id": sample_user_data["user_id"]}
    )
    
    assert response.status_code == 401

async def test_invalid_user_analytics(
    test_client: TestClient,
    auth_headers: dict
):
    """Test analytics for non-existent user"""
    response = test_client.get(
        "/api/v1/analytics/spending",
        headers=auth_headers,
        params={
            "user_id": "non_existent_user",
            "timeframe_days": 30
        }
    )
    
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "error"
    assert "user" in data["error"].lower()

async def test_analytics_rate_limiting(
    test_client: TestClient,
    auth_headers: dict,
    sample_user_data: dict
):
    """Test rate limiting for analytics endpoints"""
    # Make multiple rapid requests
    responses = []
    for _ in range(150):  # Exceeds rate limit
        response = test_client.get(
            "/api/v1/analytics/insights",
            headers=auth_headers,
            params={"user_id": sample_user_data["user_id"]}
        )
        responses.append(response)
    
    # Check if rate limiting kicked in
    assert any(r.status_code == 429 for r in responses)
    rate_limited = next(r for r in responses if r.status_code == 429)
    assert "rate limit" in rate_limited.json()["error"].lower()
