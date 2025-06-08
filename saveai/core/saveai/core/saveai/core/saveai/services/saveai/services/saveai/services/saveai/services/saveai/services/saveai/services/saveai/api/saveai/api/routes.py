"""
API Routes Configuration
Version: 1.0.0
Created: 2025-06-08 17:44:39
Author: anandhu723
"""

from fastapi import APIRouter, FastAPI
from .handlers import (
    TransactionHandler,
    AnalyticsHandler,
    BlockchainHandler,
    SecurityHandler,
    TaxHandler
)

def setup_routes(app: FastAPI) -> None:
    """Configure all API routes"""
    
    # Create API router
    api_router = APIRouter(prefix="/api/v1")
    
    # Transaction routes
    api_router.add_api_route(
        "/transactions",
        TransactionHandler.create_transaction,
        methods=["POST"],
        tags=["transactions"],
        summary="Create new transaction"
    )
    api_router.add_api_route(
        "/transactions/{transaction_id}",
        TransactionHandler.get_transaction,
        methods=["GET"],
        tags=["transactions"],
        summary="Get transaction details"
    )
    
    # Analytics routes
    api_router.add_api_route(
        "/analytics/spending",
        AnalyticsHandler.analyze_spending,
        methods=["GET"],
        tags=["analytics"],
        summary="Analyze spending patterns"
    )
    api_router.add_api_route(
        "/analytics/insights",
        AnalyticsHandler.get_insights,
        methods=["GET"],
        tags=["analytics"],
        summary="Get financial insights"
    )
    
    # Blockchain routes
    api_router.add_api_route(
        "/blockchain/verify",
        BlockchainHandler.verify_transaction,
        methods=["POST"],
        tags=["blockchain"],
        summary="Verify blockchain transaction"
    )
    api_router.add_api_route(
        "/blockchain/status",
        BlockchainHandler.get_status,
        methods=["GET"],
        tags=["blockchain"],
        summary="Get blockchain status"
    )
    
    # Security routes
    api_router.add_api_route(
        "/security/token",
        SecurityHandler.generate_token,
        methods=["POST"],
        tags=["security"],
        summary="Generate auth token"
    )
    api_router.add_api_route(
        "/security/validate",
        SecurityHandler.validate_request,
        methods=["POST"],
        tags=["security"],
        summary="Validate security request"
    )
    
    # Tax routes
    api_router.add_api_route(
        "/tax/calculate",
        TaxHandler.calculate_tax,
        methods=["POST"],
        tags=["tax"],
        summary="Calculate tax for transaction"
    )
    api_router.add_api_route(
        "/tax/report/{year}",
        TaxHandler.generate_report,
        methods=["GET"],
        tags=["tax"],
        summary="Generate tax report"
    )
    
    # Include router in app
    app.include_router(api_router)
