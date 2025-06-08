"""
Analytics API Handler
Version: 1.0.0
Created: 2025-06-08 17:50:07
Author: anandhu723
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from datetime import datetime, timedelta

from .base import BaseHandler
from ...core.models import AnalyticsData
from ...services.analytics import AnalyticsService
from ...services.security import SecurityService

class AnalyticsHandler(BaseHandler):
    """Handles analytics-related API endpoints"""
    
    def __init__(self):
        super().__init__()
        self.analytics_service = AnalyticsService()
        self.security_service = SecurityService()
    
    async def analyze_spending(
        self,
        user_id: str,
        timeframe_days: int = 30,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze user spending patterns"""
        try:
            # Security validation
            security_check = self.security_service.validate_request({
                "user_id": user_id,
                "action": "analyze",
                "scope": "spending"
            })
            
            if not security_check["valid"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Get spending analysis
            analysis = self.analytics_service.analyze_spending_patterns(
                user_id=user_id,
                timeframe_days=timeframe_days
            )
            
            if not analysis:
                raise HTTPException(status_code=404, detail="No data available")
            
            # Filter by categories if specified
            if categories:
                analysis["patterns"] = [
                    p for p in analysis["patterns"]
                    if p.get("category") in categories
                ]
            
            return self.format_response({
                "user_id": user_id,
                "timeframe_days": timeframe_days,
                "analysis": analysis,
                "categories": categories or "all"
            })
            
        except HTTPException as he:
            return await self.handle_error(he)
        except Exception as e:
            return await self.handle_error(e)
    
    async def get_insights(
        self,
        user_id: str,
        insight_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get financial insights for user"""
        try:
            # Security validation
            security_check = self.security_service.validate_request({
                "user_id": user_id,
                "action": "read",
                "scope": "insights"
            })
            
            if not security_check["valid"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Generate insights
            insights = self.analytics_service.generate_insights(user_id)
            
            # Filter by insight types if specified
            if insight_types:
                insights = [
                    i for i in insights
                    if i.get("type") in insight_types
                ]
            
            return self.format_response({
                "user_id": user_id,
                "insights": insights,
                "generated_at": datetime.utcnow()
            })
            
        except HTTPException as he:
            return await self.handle_error(he)
        except Exception as e:
            return await self.handle_error(e)
    
    async def create_report(
        self,
        user_id: str,
        report_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Create analytics report"""
        try:
            # Security validation
            security_check = self.security_service.validate_request({
                "user_id": user_id,
                "action": "create",
                "scope": "report"
            })
            
            if not security

