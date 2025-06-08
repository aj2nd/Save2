"""
API Configuration and Environment Settings
Version: 1.0.0
Created: 2025-06-08 18:10:52
Author: anandhu723
"""

from pydantic_settings import BaseSettings
from typing import Dict, List, Optional
import os
from functools import lru_cache
from enum import Enum

class EnvironmentType(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRES = "postgres"
    MONGODB = "mongodb"

class APISettings(BaseSettings):
    """API Configuration Settings"""
    
    # Basic Settings
    APP_NAME: str = "SaveAI API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    API_TITLE: str = "SaveAI Financial Management API"
    API_DESCRIPTION: str = "Secure and efficient financial management API"
    DOCS_URL: str = "/api/docs"
    REDOC_URL: str = "/api/redoc"
    
    # Security Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SECURITY_BCRYPT_ROUNDS: int = 12
    
    # Rate Limiting
    RATE_LIMIT_STANDARD: int = 100  # requests per minute
    RATE_LIMIT_PREMIUM: int = 1000  # requests per minute
    
    # Database Settings
    DATABASE_TYPE: DatabaseType = DatabaseType.POSTGRES
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_TIMEOUT: int = 30
    
    # Blockchain Settings
    BLOCKCHAIN_NETWORK: str = "ethereum"
    BLOCKCHAIN_NODE_URL: str
    SMART_CONTRACT_ADDRESS: str
    WEB3_PROVIDER: str
    
    # Cache Settings
    REDIS_URL: str
    CACHE_TTL: int = 300  # seconds
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Service Timeouts
    DEFAULT_TIMEOUT: int = 10  # seconds
    BLOCKCHAIN_TIMEOUT: int = 30  # seconds
    ANALYTICS_TIMEOUT: int = 60  # seconds
    
    # Feature Flags
    ENABLE_BLOCKCHAIN: bool = True
    ENABLE_ANALYTICS: bool = True
    ENABLE_TAX_CALCULATION: bool = True
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        case_sensitive = True

class DevelopmentSettings(APISettings):
    """Development environment settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # Override timeouts for development
    DEFAULT_TIMEOUT: int = 30
    BLOCKCHAIN_TIMEOUT: int = 60
    ANALYTICS_TIMEOUT: int = 120

class StagingSettings(APISettings):
    """Staging environment settings"""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Stricter security settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    SECURITY_BCRYPT_ROUNDS: int = 13

class ProductionSettings(APISettings):
    """Production environment settings"""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    
    # Production security settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
    SECURITY_BCRYPT_ROUNDS: int = 14
    CORS_ORIGINS: List[str] = [
        "https://app.saveai.com",
        "https://api.saveai.com"
    ]

@lru_cache()
def get_settings() -> APISettings:
    """Get configuration settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    settings_class = {
        "development": DevelopmentSettings,
        "staging": StagingSettings,
        "production": ProductionSettings
    }.get(env, DevelopmentSettings)
    
    return settings_class()

# Environment variables validation
def validate_environment() -> None:
    """Validate required environment variables"""
    required_vars = [
        "SECRET_KEY",
        "DATABASE_URL",
        "BLOCKCHAIN_NODE_URL",
        "SMART_CONTRACT_ADDRESS",
        "REDIS_URL"
    ]
    
    missing_vars = [
        var for var in required_vars
        if not os.getenv(var)
    ]
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

# Feature flag checking
def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled"""
    settings = get_settings()
    return getattr(settings, f"ENABLE_{feature_name.upper()}", False)

# Configuration helpers
def get_database_config() -> Dict:
    """Get database configuration"""
    settings = get_settings()
    return {
        "url": settings.DATABASE_URL,
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "timeout": settings.DATABASE_TIMEOUT
    }

def get_blockchain_config() -> Dict:
    """Get blockchain configuration"""
    settings = get_settings()
    return {
        "network": settings.BLOCKCHAIN_NETWORK,
        "node_url": settings.BLOCKCHAIN_NODE_URL,
        "contract_address": settings.SMART_CONTRACT_ADDRESS,
        "provider": settings.WEB3_PROVIDER,
        "timeout": settings.BLOCKCHAIN_TIMEOUT
    }
