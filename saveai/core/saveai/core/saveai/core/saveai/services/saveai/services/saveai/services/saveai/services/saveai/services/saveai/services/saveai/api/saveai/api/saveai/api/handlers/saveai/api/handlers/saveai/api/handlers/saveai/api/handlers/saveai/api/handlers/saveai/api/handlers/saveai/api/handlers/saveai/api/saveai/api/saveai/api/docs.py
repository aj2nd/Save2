"""
API Documentation and OpenAPI Specs
Version: 1.0.0
Created: 2025-06-08 18:08:22
Author: anandhu723
"""

from fastapi.openapi.models import OpenAPI
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any

def custom_openapi_schema() -> Dict[str, Any]:
    """Generate custom OpenAPI schema"""
    
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "SaveAI API",
            "description": """
            # SaveAI Financial Management API
            
            Secure and efficient financial management API for the SaveAI platform.
            
            ## Key Features
            - Transaction Management
            - Analytics and Insights
            - Blockchain Integration
            - Security Controls
            - Tax Calculations
            
            ## Authentication
            All API endpoints require OAuth2 authentication. Use the `/security/token`
            endpoint to obtain an access token.
            
            ## Rate Limiting
            - Standard tier: 100 requests/minute
            - Premium tier: 1000 requests/minute
            
            ## Environment Support
            - Production: api.saveai.com
            - Staging: api-staging.saveai.com
            - Development: api-dev.saveai.com
            """,
            "version": "1.0.0",
            "contact": {
                "name": "SaveAI API Support",
                "email": "api-support@saveai.com",
                "url": "https://docs.saveai.com"
            },
            "license": {
                "name": "Proprietary",
                "url": "https://saveai.com/terms"
            }
        },
        "servers": [
            {
                "url": "https://api.saveai.com",
                "description": "Production"
            },
            {
                "url": "https://api-staging.saveai.com",
                "description": "Staging"
            },
            {
                "url": "https://api-dev.saveai.com",
                "description": "Development"
            }
        ],
        "tags": [
            {
                "name": "transactions",
                "description": "Transaction management endpoints"
            },
            {
                "name": "analytics",
                "description": "Analytics and insights endpoints"
            },
            {
                "name": "blockchain",
                "description": "Blockchain integration endpoints"
            },
            {
                "name": "security",
                "description": "Security and authentication endpoints"
            },
            {
                "name": "tax",
                "description": "Tax calculation and reporting endpoints"
            }
        ],
        "components": {
            "securitySchemes": {
                "OAuth2": {
                    "type": "oauth2",
                    "flows": {
                        "password": {
                            "tokenUrl": "/security/token",
                            "scopes": {
                                "read": "Read access",
                                "write": "Write access",
                                "admin": "Admin access"
                            }
                        }
                    }
                },
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            }
        },
        "security": [
            {
                "OAuth2": ["read", "write"]
            }
        ]
    }

def get_api_docs() -> Dict[str, Any]:
    """Get API documentation metadata"""
    
    return {
        "endpoints": {
            "transactions": {
                "create_transaction": {
                    "summary": "Create new transaction",
                    "description": """
                    Create a new financial transaction with blockchain verification.
                    
                    ### Requirements:
                    - Valid authentication token
                    - Transaction amount > 0
                    - Valid currency code
                    
                    ### Process:
                    1. Validate request
                    2. Security check
                    3. Record on blockchain
                    4. Return confirmation
                    """,
                    "response_time_sla": "500ms"
                }
            },
            "analytics": {
                "analyze_spending": {
                    "summary": "Analyze spending patterns",
                    "description": """
                    Analyze user spending patterns and provide insights.
                    
                    ### Features:
                    - Pattern recognition
                    - Category analysis
                    - Trend detection
                    - Anomaly identification
                    """,
                    "response_time_sla": "1000ms"
                }
            }
        },
        "models": {
            "Transaction": {
                "description": "Financial transaction model",
                "required_fields": ["amount", "type", "currency"],
                "optional_fields": ["metadata"]
            },
            "Analytics": {
                "description": "Analytics data model",
                "required_fields": ["user_id", "timeframe"],
                "optional_fields": ["categories"]
            }
        },
        "errors": {
            "400": "Bad Request - Invalid input data",
            "401": "Unauthorized - Missing or invalid token",
            "403": "Forbidden - Insufficient permissions",
            "404": "Not Found - Resource doesn't exist",
            "429": "Too Many Requests - Rate limit exceeded",
            "500": "Internal Server Error - System failure"
        }
    }

def setup_api_docs(app) -> None:
    """Configure API documentation"""
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
            
        app.openapi_schema = get_openapi(
            title="SaveAI API",
            version="1.0.0",
            description="SaveAI Financial Management API",
            routes=app.routes,
        )
        
        # Update with custom schema
        custom_schema = custom_openapi_schema()
        app.openapi_schema.update(custom_schema)
        
        return app.openapi_schema
    
    app.openapi = custom_openapi
