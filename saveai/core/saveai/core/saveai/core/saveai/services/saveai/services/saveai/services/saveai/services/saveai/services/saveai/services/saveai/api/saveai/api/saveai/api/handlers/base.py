"""
Base API Handler
Version: 1.0.0
Created: 2025-06-08 17:44:39
Author: anandhu723
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException
from datetime import datetime

from ...core.config import Config

class BaseHandler:
    """Base class for all API handlers"""
    
    def __init__(self):
        self.config = Config()
        self.initialized_at = datetime.utcnow()
    
    async def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle API errors consistently"""
        if isinstance(error, HTTPException):
            return {
                "error": error.detail,
                "status_code": error.status_code,
                "timestamp": datetime.utcnow()
            }
        
        return {
            "error": str(error),
            "status_code": 500,
            "timestamp": datetime.utcnow()
        }
    
    def validate_request(self, data: Dict[str, Any]) -> bool:
        """Validate incoming request data"""
        return bool(data)
    
    def format_response(self, data: Any) -> Dict[str, Any]:
        """Format API response consistently"""
        return {
            "data": data,
            "timestamp": datetime.utcnow(),
            "status": "success"
        }
