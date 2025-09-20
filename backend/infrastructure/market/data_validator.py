# =========================
# backend/infrastructure/market/data_validator.py
# =========================
from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from domain.entities.market_data import PriceData


@dataclass
class DataQualityIssue:
    """Represents a data quality issue found during validation."""
    severity: str  # 'error', 'warning', 'info'
    message: str
    timestamp: Optional[datetime] = None
    field: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None


class DataValidator:
    """Validates market data quality and consistency."""
    
    def __init__(self):
        self.issues: List[DataQualityIssue] = []
    
    def validate_price_data(self, price_data: PriceData) -> List[DataQualityIssue]:
        """Validate a single PriceData object."""
        issues = []
        
        # Check for missing required fields
        if not price_data.ticker:
            issues.append(DataQualityIssue(
                severity='error',
                message='Missing ticker',
                field='ticker'
            ))
        
        if price_data.price <= 0:
            issues.append(DataQualityIssue(
                severity='error',
                message=f'Invalid price: {price_data.price}',
                field='price',
                actual_value=price_data.price
            ))
        
        # Validate OHLC consistency
        if hasattr(price_data, 'open') and price_data.open is not None:
            if price_data.open <= 0:
                issues.append(DataQualityIssue(
                    severity='error',
                    message=f'Invalid open price: {price_data.open}',
                    field='open',
                    actual_value=price_data.open
                ))
        
        if hasattr(price_data, 'high') and price_data.high is not None:
            if price_data.high <= 0:
                issues.append(DataQualityIssue(
                    severity='error',
                    message=f'Invalid high price: {price_data.high}',
                    field='high',
                    actual_value=price_data.high
                ))
        
        if hasattr(price_data, 'low') and price_data.low is not None:
            if price_data.low <= 0:
                issues.append(DataQualityIssue(
                    severity='error',
                    message=f'Invalid low price: {price_data.low}',
                    field='low',
                    actual_value=price_data.low
                ))
        
        if hasattr(price_data, 'close') and price_data.close is not None:
            if price_data.close <= 0:
                issues.append(DataQualityIssue(
                    severity='error',
                    message=f'Invalid close price: {price_data.close}',
                    field='close',
                    actual_value=price_data.close
                ))
        
        # Check OHLC relationships
        if (hasattr(price_data, 'open') and price_data.open is not None and
            hasattr(price_data, 'high') and price_data.high is not None and
            hasattr(price_data, 'low') and price_data.low is not None and
            hasattr(price_data, 'close') and price_data.close is not None):
            
            # High should be >= all other prices
            if price_data.high < max(price_data.open, price_data.close):
                issues.append(DataQualityIssue(
                    severity='error',
                    message=f'High price {price_data.high} is less than open/close',
                    field='high',
                    actual_value=price_data.high,
                    expected_value=f'>= {max(price_data.open, price_data.close)}'
                ))
            
            # Low should be <= all other prices
            if price_data.low > min(price_data.open, price_data.close):
                issues.append(DataQualityIssue(
                    severity='error',
                    message=f'Low price {price_data.low} is greater than open/close',
                    field='low',
                    actual_value=price_data.low,
                    expected_value=f'<= {min(price_data.open, price_data.close)}'
                ))
        
        # Validate bid/ask spread
        if (hasattr(price_data, 'bid') and price_data.bid is not None and
            hasattr(price_data, 'ask') and price_data.ask is not None):
            
            if price_data.bid >= price_data.ask:
                issues.append(DataQualityIssue(
                    severity='warning',
                    message=f'Invalid bid/ask spread: bid {price_data.bid} >= ask {price_data.ask}',
                    field='bid_ask',
                    actual_value=f'bid={price_data.bid}, ask={price_data.ask}'
                ))
            
            # Check for excessive spread (> 10% of price)
            spread_pct = (price_data.ask - price_data.bid) / price_data.price * 100
            if spread_pct > 10:
                issues.append(DataQualityIssue(
                    severity='warning',
                    message=f'Excessive bid/ask spread: {spread_pct:.2f}%',
                    field='bid_ask',
                    actual_value=f'{spread_pct:.2f}%'
                ))
        
        # Validate volume
        if hasattr(price_data, 'volume') and price_data.volume is not None:
            if price_data.volume < 0:
                issues.append(DataQualityIssue(
                    severity='error',
                    message=f'Negative volume: {price_data.volume}',
                    field='volume',
                    actual_value=price_data.volume
                ))
        
        # Validate timestamp
        if price_data.timestamp:
            if price_data.timestamp > datetime.now():
                issues.append(DataQualityIssue(
                    severity='warning',
                    message=f'Future timestamp: {price_data.timestamp}',
                    field='timestamp',
                    actual_value=price_data.timestamp
                ))
        
        return issues
    
    def validate_price_data_series(self, price_data_list: List[PriceData]) -> List[DataQualityIssue]:
        """Validate a series of PriceData objects for consistency."""
        issues = []
        
        if not price_data_list:
            issues.append(DataQualityIssue(
                severity='warning',
                message='Empty price data series'
            ))
            return issues
        
        # Validate individual data points
        for i, price_data in enumerate(price_data_list):
            point_issues = self.validate_price_data(price_data)
            for issue in point_issues:
                issue.timestamp = price_data.timestamp
                issues.append(issue)
        
        # Check for data gaps (missing timestamps)
        if len(price_data_list) > 1:
            timestamps = [pd.timestamp for pd in price_data_list if pd.timestamp]
            timestamps.sort()
            
            for i in range(1, len(timestamps)):
                gap = timestamps[i] - timestamps[i-1]
                # Check for gaps larger than 1 day
                if gap.total_seconds() > 86400:  # 24 hours
                    issues.append(DataQualityIssue(
                        severity='info',
                        message=f'Data gap: {gap} between {timestamps[i-1]} and {timestamps[i]}',
                        timestamp=timestamps[i]
                    ))
        
        # Check for duplicate timestamps
        timestamp_counts = {}
        for price_data in price_data_list:
            if price_data.timestamp:
                timestamp_counts[price_data.timestamp] = timestamp_counts.get(price_data.timestamp, 0) + 1
        
        for timestamp, count in timestamp_counts.items():
            if count > 1:
                issues.append(DataQualityIssue(
                    severity='warning',
                    message=f'Duplicate timestamp: {timestamp} appears {count} times',
                    timestamp=timestamp
                ))
        
        return issues
    
    def get_quality_summary(self, issues: List[DataQualityIssue]) -> Dict[str, Any]:
        """Get a summary of data quality issues."""
        error_count = sum(1 for issue in issues if issue.severity == 'error')
        warning_count = sum(1 for issue in issues if issue.severity == 'warning')
        info_count = sum(1 for issue in issues if issue.severity == 'info')
        
        return {
            'total_issues': len(issues),
            'errors': error_count,
            'warnings': warning_count,
            'info': info_count,
            'quality_score': max(0, 100 - (error_count * 10) - (warning_count * 5) - (info_count * 1)),
            'issues_by_field': self._group_issues_by_field(issues)
        }
    
    def _group_issues_by_field(self, issues: List[DataQualityIssue]) -> Dict[str, int]:
        """Group issues by field for analysis."""
        field_counts = {}
        for issue in issues:
            if issue.field:
                field_counts[issue.field] = field_counts.get(issue.field, 0) + 1
        return field_counts
