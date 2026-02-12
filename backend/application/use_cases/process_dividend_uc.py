# =========================
# backend/application/use_cases/process_dividend_uc.py
# =========================
from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from domain.entities.dividend import Dividend, DividendReceivable
from domain.entities.event import Event
from domain.ports.dividend_repo import DividendRepo, DividendReceivableRepo
from domain.ports.dividend_market_data import DividendMarketDataRepo
from domain.ports.positions_repo import PositionsRepo
from domain.ports.events_repo import EventsRepo
from infrastructure.time.clock import Clock


class ProcessDividendUC:
    """Use case for processing dividend-related operations."""

    def __init__(
        self,
        dividend_repo: DividendRepo,
        dividend_receivable_repo: DividendReceivableRepo,
        dividend_market_data_repo: DividendMarketDataRepo,
        positions_repo: PositionsRepo,
        events_repo: EventsRepo,
        clock: Clock,
    ):
        self.dividend_repo = dividend_repo
        self.dividend_receivable_repo = dividend_receivable_repo
        self.dividend_market_data_repo = dividend_market_data_repo
        self.positions_repo = positions_repo
        self.events_repo = events_repo
        self.clock = clock

    def announce_dividend(
        self,
        ticker: str,
        ex_date: datetime,
        pay_date: datetime,
        dps: float,
        currency: str = "USD",
        withholding_tax_rate: float = 0.25,
    ) -> Dividend:
        """Announce a new dividend."""
        dividend = Dividend(
            id=f"div_{ticker}_{ex_date.strftime('%Y%m%d')}",
            ticker=ticker,
            ex_date=ex_date,
            pay_date=pay_date,
            dps=Decimal(str(dps)),
            currency=currency,
            withholding_tax_rate=withholding_tax_rate,
        )

        created_dividend = self.dividend_repo.create_dividend(dividend)

        # Create announcement event
        self._create_event(
            position_id=None,  # Global event
            event_type="ex_div_announced",
            inputs={
                "ticker": ticker,
                "ex_date": ex_date.isoformat(),
                "pay_date": pay_date.isoformat(),
                "dps": float(dps),
                "currency": currency,
                "withholding_tax_rate": withholding_tax_rate,
            },
            outputs={
                "dividend_id": created_dividend.id,
                "announced_at": self.clock.now().isoformat(),
            },
            message=f"Dividend announced: {ticker} ${dps:.4f} per share, ex-date {ex_date.strftime('%Y-%m-%d')}",
        )

        return created_dividend

    def process_ex_dividend_date(
        self, tenant_id: str, portfolio_id: str, position_id: str
    ) -> Optional[Dict[str, Any]]:
        """Process ex-dividend date for a position."""
        position = self.positions_repo.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not position:
            return None

        # Cash lives in position (cash lives in PositionCell per target state model)

        # Check if today is ex-dividend date
        dividend = self.dividend_market_data_repo.check_ex_dividend_today(
            position.asset_symbol
        )  # Use asset_symbol instead of ticker

        if not dividend:
            return None

        # Adjust anchor price
        old_anchor = position.anchor_price
        position.adjust_anchor_for_dividend(float(dividend.dps))

        # Create dividend receivable
        gross_amount = dividend.calculate_gross_amount(position.qty)
        net_amount = dividend.calculate_net_amount(position.qty)
        withholding_tax = dividend.calculate_withholding_tax(position.qty)

        receivable = DividendReceivable(
            id=f"rec_{position_id}_{dividend.id}",
            position_id=position_id,
            dividend_id=dividend.id,
            shares_at_record=position.qty,
            gross_amount=gross_amount,
            net_amount=net_amount,
            withholding_tax=withholding_tax,
        )

        created_receivable = self.dividend_receivable_repo.create_receivable(receivable)

        # Add receivable to position (dividend_receivable is still on position entity)
        position.add_dividend_receivable(float(net_amount))

        # Update position
        self.positions_repo.save(position)

        # Note: Cash is not updated here - it will be updated when dividend is paid via process_payment

        # Create events
        self._create_event(
            position_id=position_id,
            event_type="ex_div_effective",
            inputs={
                "ticker": position.asset_symbol,  # Use asset_symbol instead of ticker
                "ex_date": dividend.ex_date.isoformat(),
                "dps": float(dividend.dps),
                "shares_at_record": position.qty,
                "withholding_tax_rate": dividend.withholding_tax_rate,
            },
            outputs={
                "gross_amount": float(gross_amount),
                "net_amount": float(net_amount),
                "withholding_tax": float(withholding_tax),
                "receivable_id": created_receivable.id,
            },
            message=f"Ex-dividend effective: {position.asset_symbol} ${dividend.dps:.4f} per share, receivable ${float(net_amount):.2f}",
        )

        self._create_event(
            position_id=position_id,
            event_type="anchor_adjusted_for_dividend",
            inputs={
                "old_anchor": old_anchor,
                "dps": float(dividend.dps),
                "ex_date": dividend.ex_date.isoformat(),
            },
            outputs={
                "new_anchor": position.anchor_price,
                "adjustment": float(dividend.dps),
            },
            message=f"Anchor adjusted for dividend: ${old_anchor:.2f} → ${position.anchor_price:.2f}",
        )

        return {
            "dividend": dividend,
            "receivable": created_receivable,
            "old_anchor": old_anchor,
            "new_anchor": position.anchor_price,
        }

    def process_dividend_payment(
        self, tenant_id: str, portfolio_id: str, position_id: str, receivable_id: str
    ) -> Optional[Dict[str, Any]]:
        """Process dividend payment for a receivable."""
        receivable = self.dividend_receivable_repo.get_receivable(receivable_id)
        if not receivable or receivable.position_id != position_id:
            return None

        position = self.positions_repo.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not position:
            return None

        # Cash lives in position (cash lives in PositionCell per target state model)

        # Mark receivable as paid
        receivable.mark_paid()
        self.dividend_receivable_repo.mark_receivable_paid(receivable_id)

        # Clear receivable (dividend_receivable is still on position entity)
        # Note: clear_dividend_receivable already adds cash to position.cash
        net_amount_float = float(receivable.net_amount)
        position.clear_dividend_receivable(net_amount_float)

        # Update dividend aggregate (per spec)
        position.total_dividends_received += net_amount_float

        # Note: Cash is already added by clear_dividend_receivable, no need to add again

        # Update position
        self.positions_repo.save(position)

        # Create event
        self._create_event(
            position_id=position_id,
            event_type="dividend_cash_received",
            inputs={
                "receivable_id": receivable_id,
                "dividend_id": receivable.dividend_id,
                "net_amount": float(receivable.net_amount),
                "withholding_tax": float(receivable.withholding_tax),
            },
            outputs={
                "amount_net": float(receivable.net_amount),
                "receivable_cleared": True,
                "new_cash_balance": position.cash,  # Cash lives in PositionCell
            },
            message=f"Dividend received: ${float(receivable.net_amount):.2f} added to cash",
        )

        return {
            "receivable": receivable,
            "amount_received": float(receivable.net_amount),
            "new_cash_balance": position.cash,  # Cash lives in PositionCell
        }

    def get_dividend_status(
        self, tenant_id: str, portfolio_id: str, position_id: str
    ) -> Dict[str, Any]:
        """Get dividend status for a position."""
        position = self.positions_repo.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not position:
            return {}

        # Get pending receivables
        pending_receivables = self.dividend_receivable_repo.get_pending_receivables(position_id)

        # Get upcoming dividends
        upcoming_dividends = self.dividend_market_data_repo.get_upcoming_dividends(
            position.asset_symbol
        )  # Use asset_symbol instead of ticker

        # Cash lives in position (cash lives in PositionCell)

        return {
            "position_id": position_id,
            "ticker": position.asset_symbol,  # Use asset_symbol instead of ticker
            "dividend_receivable": position.dividend_receivable,
            "effective_cash": position.get_effective_cash(),  # Cash lives in PositionCell
            "pending_receivables": [
                {
                    "id": rec.id,
                    "dividend_id": rec.dividend_id,
                    "net_amount": float(rec.net_amount),
                    "pay_date": rec.paid_at.isoformat() if rec.paid_at else None,
                }
                for rec in pending_receivables
            ],
            "upcoming_dividends": [
                {
                    "ex_date": div.ex_date.isoformat() if div.ex_date else None,
                    "pay_date": div.pay_date.isoformat() if div.pay_date else None,
                    "dps": float(div.dps),
                    "currency": div.currency,
                }
                for div in (upcoming_dividends or [])
            ],
        }

    def _create_event(
        self,
        position_id: Optional[str],
        event_type: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        message: str,
    ) -> Event:
        """Create an event record."""
        event = Event(
            id=f"evt_{event_type}_{self.clock.now().strftime('%Y%m%d_%H%M%S_%f')}",
            position_id=position_id or "system",
            type=event_type,
            inputs=inputs,
            outputs=outputs,
            message=message,
            ts=self.clock.now(),
        )

        self.events_repo.append(event)
        return event
