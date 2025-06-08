"""
SaveAI API Module
Version: 1.0.0
Created: 2025-06-08 17:44:39
Author: anandhu723
"""

from .routes import setup_routes
from .handlers import (
    TransactionHandler,
    AnalyticsHandler,
    BlockchainHandler,
    SecurityHandler,
    TaxHandler
)

__all__ = [
    'setup_routes',
    'TransactionHandler',
    'AnalyticsHandler',
    'BlockchainHandler',
    'SecurityHandler',
    'TaxHandler'
]
