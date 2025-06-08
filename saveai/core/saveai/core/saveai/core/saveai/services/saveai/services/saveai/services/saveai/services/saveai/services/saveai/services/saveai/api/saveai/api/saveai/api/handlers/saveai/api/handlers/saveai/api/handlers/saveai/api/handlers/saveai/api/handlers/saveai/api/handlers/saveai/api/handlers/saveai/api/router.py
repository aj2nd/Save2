"""
API Router Configuration
Version: 1.0.0
Created: 2025-06-08 18:06:04
Author: anandhu723
"""

from fastapi import APIRouter, FastAPI, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, Optional
from datetime import datetime

from .handlers import (
    transaction_handler,
    analytics_handler,
    blockchain_handler,
    security_handler,
    tax_handler
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_api_router() -> APIRouter:
    """Create and configure the API router"""
    
    # Create main API router with version prefix
    api_router = APIRouter(prefix="/api/v1")
    
    # Transaction Routes
    api_router.add_api_route(
        "/transactions",
        transaction_handler.create_transaction,
        methods=["POST"],
        tags=["transactions"],
        summary="Create new transaction",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    api_router.add_api_route(
        "/transactions/{transaction_id}",
        transaction_handler.get_transaction,
        methods=["GET"],
        tags=["transactions"],
        summary="Get transaction details",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    api_router.add_api_route(
        "/transactions/{transaction_id}/status",
        transaction_handler.update_transaction_status,
        methods=["PATCH"],
        tags=["transactions"],
        summary="Update transaction status",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    # Analytics Routes
    api_router.add_api_route(
        "/analytics/spending",
        analytics_handler.analyze_spending,
        methods=["GET"],
        tags=["analytics"],
        summary="Analyze spending patterns",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    api_router.add_api_route(
        "/analytics/insights",
        analytics_handler.get_insights,
        methods=["GET"],
        tags=["analytics"],
        summary="Get financial insights",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    api_router.add_api_route(
        "/analytics/trends",
        analytics_handler.get_trends,
        methods=["GET"],
        tags=["analytics"],
        summary="Get spending trends",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    # Blockchain Routes
    api_router.add_api_route(
        "/blockchain/verify/{blockchain_hash}",
        blockchain_handler.verify_transaction,
        methods=["GET"],
        tags=["blockchain"],
        summary="Verify blockchain transaction",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    api_router.add_api_route(
        "/blockchain/status",
        blockchain_handler.get_status,
        methods=["GET"],
        tags=["blockchain"],
        summary="Get blockchain status",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    api_router.add_api_route(
        "/blockchain/history",
        blockchain_handler.get_transaction_history,
        methods=["GET"],
        tags=["blockchain"],
        summary="Get blockchain history",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    api_router.add_api_route(
        "/blockchain/metrics",
        blockchain_handler.get_smart_contract_metrics,
        methods=["GET"],
        tags=["blockchain"],
        summary="Get smart contract metrics",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    # Security Routes
    api_router.add_api_route(
        "/security/token",
        security_handler.generate_token,
        methods=["POST"],
        tags=["security"],
        summary="Generate auth token"
    )
    
    api_router.add_api_route(
        "/security/validate",
        security_handler.validate_request,
        methods=["POST"],
        tags=["security"],
        summary="Validate security request",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    api_router.add_api_route(
        "/security/encrypt",
        security_handler.encrypt_data,
        methods=["POST"],
        tags=["security"],
        summary="Encrypt sensitive data",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    api_router.add_api_route(
        "/security/audit",
        security_handler.audit_security,
        methods=["GET"],
        tags=["security"],
        summary="Audit security events",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    # Tax Routes
    api_router.add_api_route(
        "/tax/calculate",
        tax_handler.calculate_tax,
        methods=["POST"],
        tags=["tax"],
        summary="Calculate transaction tax",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    api_router.add_api_route(
        "/tax/report/{year}",
        tax_handler.generate_report,
        methods=["GET"],
        tags=["tax"],
        summary="Generate tax report",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    api_router.add_api_route(
        "/tax/estimate",
        tax_handler.estimate_liability,
        methods=["GET"],
        tags=["tax"],
        summary="Estimate tax liability",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    api_router.add_api_route(
        "/tax/calendar/{year}",
        tax_handler.get_tax_calendar,
        methods=["GET"],
        tags=["tax"],
        summary="Get tax calendar",
        dependencies=[Depends(oauth2_scheme)]
    )
    
    return api_router

def setup_api(app: FastAPI) -> None:
    """Configure API in FastAPI application"""
    
    # Create router
    api_router = create_api_router()
    
    # Include router in app
    app.include_router(api_router)
    
    # Add API metadata
    app.title = "SaveAI API"
    app.description = "Financial Management and Analytics API"
    app.version = "1.0.0"
    app.docs_url = "/api/docs"
    app.redoc_url = "/api/redoc"
    
    # Add API timestamps
    @app.get("/api/status")
    async def get_api_status() -> Dict[str, Any]:
        return {
            "status": "operational",
            "timestamp": datetime.utcnow(),
            "version": app.version,
            "environment": app.debug
        }
