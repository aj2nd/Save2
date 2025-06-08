"""
Configuration settings for SaveAI
Version: 1.0.0
Created: 2025-06-08 17:26:53
Author: anandhu723
"""

import os
from typing import Dict, Any
from datetime import datetime

class Config:
    """Configuration management for the system"""
    
    def __init__(self):
        self.initialized_at = datetime.utcnow()
        self.environment = os.getenv("SAVEAI_ENV", "development")
        
        # Database configurations
        self.db_config = {
            "primary_host": os.getenv("SAVEAI_DB_HOST", "localhost"),
            "primary_port": int(os.getenv("SAVEAI_DB_PORT", "5432")),
            "blockchain_enabled": bool(os.getenv("SAVEAI_BLOCKCHAIN_ENABLED", "True")),
            "analytics_enabled": bool(os.getenv("SAVEAI_ANALYTICS_ENABLED", "True"))
        }
        
        # Security configurations
        self.security_config = {
            "encryption_level": os.getenv("SAVEAI_ENCRYPTION_LEVEL", "high"),
            "jwt_secret": os.getenv("SAVEAI_JWT_SECRET", "your-secret-key"),
            "token_expiry": int(os.getenv("SAVEAI_TOKEN_EXPIRY", "3600"))
        }
        
        # Blockchain configurations
        self.blockchain_config = {
            "network": os.getenv("SAVEAI_BLOCKCHAIN_NETWORK", "ethereum"),
            "node_url": os.getenv("SAVEAI_BLOCKCHAIN_NODE", "http://localhost:8545"),
            "contract_address": os.getenv("SAVEAI_CONTRACT_ADDRESS", "")
        }
        
        # Analytics configurations
        self.analytics_config = {
            "enabled": bool(os.getenv("SAVEAI_ANALYTICS_ENABLED", "True")),
            "batch_size": int(os.getenv("SAVEAI_ANALYTICS_BATCH", "100")),
            "processing_interval": int(os.getenv("SAVEAI_ANALYTICS_INTERVAL", "300"))
        }
        
        # Tax configurations for UAE
        self.tax_config = {
            "vat_rate": float(os.getenv("SAVEAI_VAT_RATE", "5.0")),
            "tax_year": int(os.getenv("SAVEAI_TAX_YEAR", "2025")),
            "reporting_currency": os.getenv("SAVEAI_CURRENCY", "AED")
        }

    @property
    def debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.environment == "development"

    def get_database_url(self) -> str:
        """Get the database URL based on environment"""
        return f"postgresql://{self.db_config['primary_host']}:{self.db_config['primary_port']}/saveai_{self.environment}"
