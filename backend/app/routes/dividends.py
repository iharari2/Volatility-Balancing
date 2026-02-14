# =========================
# backend/app/routes/dividends.py
# =========================
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.di import container
from application.use_cases.process_dividend_uc import ProcessDividendUC


router = APIRouter(prefix="/v1/dividends", tags=["dividends"])


class DividendAnnouncementRequest(BaseModel):
    ticker: str
    ex_date: datetime
    pay_date: datetime
    dps: float
    currency: str = "USD"
    withholding_tax_rate: float = 0.25


class DividendPaymentRequest(BaseModel):
    receivable_id: str


def get_dividend_uc() -> ProcessDividendUC:
    """Get dividend use case with dependencies."""
    return ProcessDividendUC(
        dividend_repo=container.dividend,
        dividend_receivable_repo=container.dividend_receivable,
        dividend_market_data_repo=container.dividend_market_data,
        positions_repo=container.positions,
        events_repo=container.events,
        clock=container.clock,
    )


@router.post("/announce")
async def announce_dividend(
    request: DividendAnnouncementRequest, dividend_uc: ProcessDividendUC = Depends(get_dividend_uc)
) -> Dict[str, Any]:
    """Announce a new dividend."""
    try:
        dividend = dividend_uc.announce_dividend(
            ticker=request.ticker,
            ex_date=request.ex_date,
            pay_date=request.pay_date,
            dps=request.dps,
            currency=request.currency,
            withholding_tax_rate=request.withholding_tax_rate,
        )

        return {
            "dividend_id": dividend.id,
            "ticker": dividend.ticker,
            "ex_date": dividend.ex_date.isoformat(),
            "pay_date": dividend.pay_date.isoformat(),
            "dps": float(dividend.dps),
            "currency": dividend.currency,
            "withholding_tax_rate": dividend.withholding_tax_rate,
            "message": f"Dividend announced for {dividend.ticker}",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/process-ex-dividend"
)
async def process_ex_dividend_date(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    dividend_uc: ProcessDividendUC = Depends(get_dividend_uc),
) -> Dict[str, Any]:
    """Process ex-dividend date for a position."""
    try:
        result = dividend_uc.process_ex_dividend_date(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )

        if not result:
            return {
                "message": f"No ex-dividend date today for position {position_id}",
                "processed": False,
            }

        return {
            "message": "Ex-dividend date processed successfully",
            "processed": True,
            "dividend": {
                "id": result["dividend"].id,
                "ticker": result["dividend"].ticker,
                "dps": float(result["dividend"].dps),
                "ex_date": result["dividend"].ex_date.isoformat(),
            },
            "receivable": {
                "id": result["receivable"].id,
                "net_amount": float(result["receivable"].net_amount),
                "gross_amount": float(result["receivable"].gross_amount),
                "withholding_tax": float(result["receivable"].withholding_tax),
            },
            "anchor_adjustment": {
                "old_anchor": result["old_anchor"],
                "new_anchor": result["new_anchor"],
                "adjustment": float(result["dividend"].dps),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/process-payment"
)
async def process_dividend_payment(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    request: DividendPaymentRequest,
    dividend_uc: ProcessDividendUC = Depends(get_dividend_uc),
) -> Dict[str, Any]:
    """Process dividend payment for a receivable."""
    try:
        result = dividend_uc.process_dividend_payment(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            receivable_id=request.receivable_id,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Receivable not found")

        return {
            "message": "Dividend payment processed successfully",
            "receivable_id": request.receivable_id,
            "amount_received": result["amount_received"],
            "new_cash_balance": result["new_cash_balance"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/status")
async def get_dividend_status(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    dividend_uc: ProcessDividendUC = Depends(get_dividend_uc),
) -> Dict[str, Any]:
    """Get dividend status for a position."""
    try:
        status = dividend_uc.get_dividend_status(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )

        if not status:
            raise HTTPException(status_code=404, detail="Position not found")

        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/market/{ticker}/info")
async def get_dividend_info(
    ticker: str, dividend_uc: ProcessDividendUC = Depends(get_dividend_uc)
) -> Dict[str, Any]:
    """Get dividend information for a ticker from market data."""
    try:
        dividend = dividend_uc.dividend_market_data_repo.get_dividend_info(ticker)

        if not dividend:
            return {
                "ticker": ticker,
                "has_dividend": False,
                "message": f"No dividend information available for {ticker}",
            }

        return {
            "ticker": ticker,
            "has_dividend": True,
            "dividend": {
                "id": dividend.id,
                "ex_date": dividend.ex_date.isoformat(),
                "pay_date": dividend.pay_date.isoformat(),
                "dps": float(dividend.dps),
                "currency": dividend.currency,
                "withholding_tax_rate": dividend.withholding_tax_rate,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/market/{ticker}/upcoming")
async def get_upcoming_dividends(
    ticker: str, dividend_uc: ProcessDividendUC = Depends(get_dividend_uc)
) -> Dict[str, Any]:
    """Get upcoming dividends for a ticker."""
    try:
        dividends = dividend_uc.dividend_market_data_repo.get_upcoming_dividends(ticker)

        return {
            "ticker": ticker,
            "upcoming_dividends": [
                {
                    "id": div.id,
                    "ex_date": div.ex_date.isoformat(),
                    "pay_date": div.pay_date.isoformat(),
                    "dps": float(div.dps),
                    "currency": div.currency,
                }
                for div in dividends
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
