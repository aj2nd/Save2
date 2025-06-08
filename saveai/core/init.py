"""
SaveAI Core Module
Version: 1.0.0
Created: 2025-06-08 17:20:43
Author: anandhu723
"""

from .config import Config
from .database import DatabaseManager
from .models import (
    Transaction,
    TransactionType,
    SecurityLevel,
    AnalyticsData,
    TaxRecord
)

# Initialize core components
config = Config()
db = DatabaseManager()

__all__ = [
    'Config',
    'DatabaseManager',
    'Transaction',
    'TransactionType',
    'SecurityLevel',
    'AnalyticsData',
    'TaxRecord',
    'config',
    'db'
]
