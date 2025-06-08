"""
Application Settings
Version: 1.0.0
Created: 2025-06-08 23:39:20
Author: anandhu723
"""

from typing import Dict, Any, Optional
from pydantic import BaseSettings, PostgresDsn, RedisDsn

class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    DATABASE_URL: PostgresDsn
    
    # Redis settings
    REDIS_URL: RedisDsn
    
    # Blockchain settings
    BLOCKCHAIN_NODE_URL: str
    BLOCKCHAIN_NETWORK: str = "mainnet"
    SMART_CONTRACT_ADDRESS: str
    
    # Security settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Transaction settings
    DEFAULT_CURRENCY: str = "AED"
    MIN_TRANSACTION_AMOUNT: float = 0.01
    MAX_TRANSACTION_AMOUNT: float = 1000000.00
    
    class Config:
        env_file = ".env"
        case_sensitive = True
