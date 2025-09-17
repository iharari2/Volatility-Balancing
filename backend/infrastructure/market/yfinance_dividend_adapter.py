# =========================
# backend/infrastructure/market/yfinance_dividend_adapter.py
# =========================
from __future__ import annotations
import yfinance as yf
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from decimal import Decimal

from domain.entities.dividend import Dividend
from domain.ports.dividend_market_data import DividendMarketDataRepo


class YFinanceDividendAdapter(DividendMarketDataRepo):
    """yfinance implementation of dividend market data repository."""

    def __init__(self):
        self.tz_utc = timezone.utc

    def get_dividend_info(self, ticker: str) -> Optional[Dividend]:
        """Get current dividend information for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get dividend data
            dividend_rate = info.get("dividendRate", 0)
            ex_dividend_date = info.get("exDividendDate")

            if not dividend_rate or not ex_dividend_date:
                return None

            # Convert ex-dividend date
            if isinstance(ex_dividend_date, (int, float)):
                ex_date = datetime.fromtimestamp(ex_dividend_date, tz=self.tz_utc)
            else:
                ex_date = datetime.fromisoformat(str(ex_dividend_date).replace("Z", "+00:00"))

            # Calculate pay date (typically 1-2 weeks after ex-date)
            pay_date = ex_date + timedelta(days=14)

            return Dividend(
                id=f"div_{ticker}_{ex_date.strftime('%Y%m%d')}",
                ticker=ticker,
                ex_date=ex_date,
                pay_date=pay_date,
                dps=Decimal(str(dividend_rate)),
                currency="USD",
                withholding_tax_rate=0.25,  # Default 25%
            )

        except Exception as e:
            print(f"Error fetching dividend info for {ticker}: {e}")
            return None

    def get_dividend_history(
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> List[Dividend]:
        """Get dividend history for a ticker."""
        try:
            stock = yf.Ticker(ticker)

            # Get dividend history
            dividends = stock.dividends

            if dividends.empty:
                return []

            # Filter by date range
            dividends = dividends[(dividends.index >= start_date) & (dividends.index <= end_date)]

            dividend_list = []
            for date, amount in dividends.items():
                # Convert timestamp to UTC
                if date.tzinfo is None:
                    ex_date = date.replace(tzinfo=self.tz_utc)
                else:
                    ex_date = date.astimezone(self.tz_utc)

                # Calculate pay date
                pay_date = ex_date + timedelta(days=14)

                dividend = Dividend(
                    id=f"div_{ticker}_{ex_date.strftime('%Y%m%d')}",
                    ticker=ticker,
                    ex_date=ex_date,
                    pay_date=pay_date,
                    dps=Decimal(str(amount)),
                    currency="USD",
                    withholding_tax_rate=0.25,
                )

                dividend_list.append(dividend)

            return dividend_list

        except Exception as e:
            print(f"Error fetching dividend history for {ticker}: {e}")
            return []

    def get_upcoming_dividends(self, ticker: str) -> List[Dividend]:
        """Get upcoming dividends for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get next dividend date
            ex_dividend_date = info.get("exDividendDate")
            dividend_rate = info.get("dividendRate", 0)

            if not ex_dividend_date or not dividend_rate:
                return []

            # Convert ex-dividend date
            if isinstance(ex_dividend_date, (int, float)):
                ex_date = datetime.fromtimestamp(ex_dividend_date, tz=self.tz_utc)
            else:
                ex_date = datetime.fromisoformat(str(ex_dividend_date).replace("Z", "+00:00"))

            # Only return if it's in the future
            if ex_date <= datetime.now(self.tz_utc):
                return []

            # Calculate pay date
            pay_date = ex_date + timedelta(days=14)

            dividend = Dividend(
                id=f"div_{ticker}_{ex_date.strftime('%Y%m%d')}",
                ticker=ticker,
                ex_date=ex_date,
                pay_date=pay_date,
                dps=Decimal(str(dividend_rate)),
                currency="USD",
                withholding_tax_rate=0.25,
            )

            return [dividend]

        except Exception as e:
            print(f"Error fetching upcoming dividends for {ticker}: {e}")
            return []

    def check_ex_dividend_today(self, ticker: str) -> Optional[Dividend]:
        """Check if today is ex-dividend date for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            ex_dividend_date = info.get("exDividendDate")
            dividend_rate = info.get("dividendRate", 0)

            if not ex_dividend_date or not dividend_rate:
                return None

            # Convert ex-dividend date
            if isinstance(ex_dividend_date, (int, float)):
                ex_date = datetime.fromtimestamp(ex_dividend_date, tz=self.tz_utc)
            else:
                ex_date = datetime.fromisoformat(str(ex_dividend_date).replace("Z", "+00:00"))

            # Check if today is ex-dividend date
            today = datetime.now(self.tz_utc).date()
            if ex_date.date() != today:
                return None

            # Calculate pay date
            pay_date = ex_date + timedelta(days=14)

            return Dividend(
                id=f"div_{ticker}_{ex_date.strftime('%Y%m%d')}",
                ticker=ticker,
                ex_date=ex_date,
                pay_date=pay_date,
                dps=Decimal(str(dividend_rate)),
                currency="USD",
                withholding_tax_rate=0.25,
            )

        except Exception as e:
            print(f"Error checking ex-dividend date for {ticker}: {e}")
            return None
