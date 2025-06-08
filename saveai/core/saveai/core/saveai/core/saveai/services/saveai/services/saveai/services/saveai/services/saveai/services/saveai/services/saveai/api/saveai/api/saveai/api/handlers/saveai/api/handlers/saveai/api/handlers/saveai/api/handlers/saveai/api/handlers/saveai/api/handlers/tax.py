"""
Tax API Handler
Version: 1.0.0
Created: 2025-06-08 17:59:22
Author: anandhu723
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException
from datetime import datetime, timedelta

from .base import BaseHandler
from ...core.models import Transaction, TaxRecord
from ...services.tax import TaxService
from ...services.security import SecurityService

class TaxHandler(BaseHandler):
    """Handles tax-related API endpoints"""
    
    def __init__(self):
        super().__init__()
        self.tax_service = TaxService()
        self.security_service = SecurityService()
    
    async def calculate_tax(self, transaction: Transaction) -> Dict[str, Any]:
        """Calculate tax for a transaction"""
        try:
            # Security validation
            security_check = self.security_service.validate_request({
                "transaction_id": transaction.id,
                "action": "calculate",
                "scope": "tax"
            })
            
            if not security_check["valid"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Calculate VAT
            vat_calculation = self.tax_service.calculate_vat(transaction)
            
            if not vat_calculation:
                raise HTTPException(
                    status_code=500,
                    detail="VAT calculation failed"
                )
            
            return self.format_response({
                "transaction_id": transaction.id,
                "calculation": vat_calculation,
                "timestamp": datetime.utcnow()
            })
            
        except HTTPException as he:
            return await self.handle_error(he)
        except Exception as e:
            return await self.handle_error(e)
    
    async def generate_report(
        self,
        user_id: str,
        year: int,
        quarter: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate tax report"""
        try:
            # Security validation
            security_check = self.security_service.validate_request({
                "user_id": user_id,
                "action": "report",
                "scope": "tax"
            })
            
            if not security_check["valid"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Generate tax report
            report = self.tax_service.generate_tax_report(
                user_id=user_id,
                year=year
            )
            
            if not report:
                raise HTTPException(
                    status_code=500,
                    detail="Report generation failed"
                )
            
            # Filter by quarter if specified
            if quarter:
                report = self._filter_report_by_quarter(report, quarter)
            
            return self.format_response({
                "user_id": user_id,
                "year": year,
                "quarter": quarter,
                "report": report
            })
            
        except HTTPException as he:
            return await self.handle_error(he)
        except Exception as e:
            return await self.handle_error(e)
    
    async def estimate_liability(
        self,
        user_id: str,
        forecast_months: int = 12
    ) -> Dict[str, Any]:
        """Estimate future tax liability"""
        try:
            # Security validation
            security_check = self.security_service.validate_request({
                "user_id": user_id,
                "action": "estimate",
                "scope": "tax"
            })
            
            if not security_check["valid"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Get tax estimate
            estimate = self.tax_service.estimate_tax_liability(user_id)
            
            if not estimate:
                raise HTTPException(
                    status_code=500,
                    detail="Estimation failed"
                )
            
            return self.format_response({
                "user_id": user_id,
                "forecast_months": forecast_months,
                "estimate": estimate
            })
            
        except HTTPException as he:
            return await self.handle_error(he)
        except Exception as e:
            return await self.handle_error(e)
    
    async def get_tax_calendar(
        self,
        user_id: str,
        year: int
    ) -> Dict[str, Any]:
        """Get tax filing calendar"""
        try:
            calendar = self._generate_tax_calendar(year)
            
            return self.format_response({
                "user_id": user_id,
                "year": year,
                "calendar": calendar
            })
            
        except Exception as e:
            return await self.handle_error(e)
    
    def _filter_report_by_quarter(
        self,
        report: Dict[str, Any],
        quarter: int
    ) -> Dict[str, Any]:
        """Filter tax report data by quarter"""
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3
        
        filtered_transactions = [
            t for t in report["transactions"]
            if start_month <= t["date"].month <= end_month
        ]
        
        report["transactions"] = filtered_transactions
        report["summary"] = self._calculate_quarter_summary(filtered_transactions)
        return report
    
    def _generate_tax_calendar(self, year: int) -> List[Dict[str, Any]]:
        """Generate tax filing calendar"""
        return [
            {
                "period": "Q1",
                "filing_deadline": datetime(year, 4, 21),
                "payment_deadline": datetime(year, 4, 21),
                "requirements": ["VAT Return", "Payment"]
            },
            {
                "period": "Q2",
                "filing_deadline": datetime(year, 7, 21),
                "payment_deadline": datetime(year, 7, 21),
                "requirements": ["VAT Return", "Payment"]
            },
            {
                "period": "Q3",
                "filing_deadline": datetime(year, 10, 21),
                "payment_deadline": datetime(year, 10, 21),
                "requirements": ["VAT Return", "Payment"]
            },
            {
                "period": "Q4",
                "filing_deadline": datetime(year + 1, 1, 21),
                "payment_deadline": datetime(year + 1, 1, 21),
                "requirements": ["VAT Return", "Payment", "Annual Summary"]
            }
        ]
    
    def _calculate_quarter_summary(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate summary for quarterly report"""
        total_vat = sum(t.get("vat_amount", 0) for t in transactions)
        total_taxable = sum(t.get("taxable_amount", 0) for t in transactions)
        
        return {
            "total_transactions": len(transactions),
            "total_vat": total_vat,
            "total_taxable_amount": total_taxable,
            "average_vat_rate": (total_vat / total_taxable * 100) if total_taxable else 0
        }
