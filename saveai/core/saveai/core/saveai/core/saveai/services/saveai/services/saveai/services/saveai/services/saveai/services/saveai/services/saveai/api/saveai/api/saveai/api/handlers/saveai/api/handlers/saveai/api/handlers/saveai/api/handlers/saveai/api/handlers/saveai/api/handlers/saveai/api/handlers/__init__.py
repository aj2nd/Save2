"""
API Handlers Initialization
Version: 1.0.0
Created: 2025-06-08 18:00:59
Author: anandhu723
"""

from .base import BaseHandler
from .transaction import TransactionHandler
from .analytics import AnalyticsHandler
from .blockchain import BlockchainHandler
from .security import SecurityHandler
from .tax import TaxHandler

# Export all handlers
__all__ = [
    'BaseHandler',
    'TransactionHandler',
    'AnalyticsHandler',
    'BlockchainHandler',
    'SecurityHandler',
    'TaxHandler'
]

# Handler version information
HANDLERS_VERSION = {
    'base': BaseHandler.__doc__.split('\n')[2].split(': ')[1],
    'transaction': TransactionHandler.__doc__.split('\n')[2].split(': ')[1],
    'analytics': AnalyticsHandler.__doc__.split('\n')[2].split(': ')[1],
    'blockchain': BlockchainHandler.__doc__.split('\n')[2].split(': ')[1],
    'security': SecurityHandler.__doc__.split('\n')[2].split(': ')[1],
    'tax': TaxHandler.__doc__.split('\n')[2].split(': ')[1]
}

# Handler metadata
HANDLERS_METADATA = {
    'base': {
        'name': 'Base Handler',
        'description': 'Base class for all API handlers',
        'version': HANDLERS_VERSION['base'],
        'author': BaseHandler.__doc__.split('\n')[4].split(': ')[1]
    },
    'transaction': {
        'name': 'Transaction Handler',
        'description': 'Handles transaction-related API endpoints',
        'version': HANDLERS_VERSION['transaction'],
        'author': TransactionHandler.__doc__.split('\n')[4].split(': ')[1]
    },
    'analytics': {
        'name': 'Analytics Handler',
        'description': 'Handles analytics-related API endpoints',
        'version': HANDLERS_VERSION['analytics'],
        'author': AnalyticsHandler.__doc__.split('\n')[4].split(': ')[1]
    },
    'blockchain': {
        'name': 'Blockchain Handler',
        'description': 'Handles blockchain-related API endpoints',
        'version': HANDLERS_VERSION['blockchain'],
        'author': BlockchainHandler.__doc__.split('\n')[4].split(': ')[1]
    },
    'security': {
        'name': 'Security Handler',
        'description': 'Handles security-related API endpoints',
        'version': HANDLERS_VERSION['security'],
        'author': SecurityHandler.__doc__.split('\n')[4].split(': ')[1]
    },
    'tax': {
        'name': 'Tax Handler',
        'description': 'Handles tax-related API endpoints',
        'version': HANDLERS_VERSION['tax'],
        'author': TaxHandler.__doc__.split('\n')[4].split(': ')[1]
    }
}

def get_handler_info(handler_name: str) -> dict:
    """Get metadata for a specific handler"""
    return HANDLERS_METADATA.get(handler_name, {})

def get_all_handlers_info() -> dict:
    """Get metadata for all handlers"""
    return HANDLERS_METADATA

def get_handler_version(handler_name: str) -> str:
    """Get version of a specific handler"""
    return HANDLERS_VERSION.get(handler_name, '')

def get_all_handlers_versions() -> dict:
    """Get versions of all handlers"""
    return HANDLERS_VERSION

# Initialize handlers with default configuration
transaction_handler = TransactionHandler()
analytics_handler = AnalyticsHandler()
blockchain_handler = BlockchainHandler()
security_handler = SecurityHandler()
tax_handler = TaxHandler()

# Export initialized handler instances
__instances__ = {
    'transaction': transaction_handler,
    'analytics': analytics_handler,
    'blockchain': blockchain_handler,
    'security': security_handler,
    'tax': tax_handler
}
