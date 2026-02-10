# backend/application/use_cases/create_experiment_uc.py
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any
from uuid import uuid4

from domain.ports.trading_experiment_repo import TradingExperimentRepo
from domain.ports.portfolio_repo import PortfolioRepo
from domain.ports.positions_repo import PositionsRepo
from domain.ports.market_data import MarketDataRepo
from domain.entities.trading_experiment import TradingExperiment


class CreateExperimentUC:
    """Use case for creating a new trading experiment."""

    _logger = logging.getLogger(__name__)

    def __init__(
        self,
        experiment_repo: TradingExperimentRepo,
        portfolio_repo: PortfolioRepo,
        positions_repo: PositionsRepo,
        market_data: MarketDataRepo,
    ) -> None:
        self.experiment_repo = experiment_repo
        self.portfolio_repo = portfolio_repo
        self.positions_repo = positions_repo
        self.market_data = market_data

    def execute(
        self,
        tenant_id: str,
        name: str,
        ticker: str,
        initial_capital: float,
    ) -> Dict[str, Any]:
        """
        Create a new trading experiment.

        Steps:
        1. Fetch current price for baseline
        2. Create portfolio (type=EXPERIMENT)
        3. Create position with initial cash
        4. Record experiment with baseline metrics

        Args:
            tenant_id: Tenant identifier
            name: Experiment name
            ticker: Stock ticker symbol
            initial_capital: Starting capital amount

        Returns:
            Dict with experiment details
        """
        self._logger.info(
            "Creating experiment: name=%s, ticker=%s, capital=%.2f",
            name,
            ticker,
            initial_capital,
        )

        # Step 1: Fetch current price for baseline
        price_data = self.market_data.get_reference_price(ticker)
        if not price_data:
            raise ValueError(f"Unable to fetch price for ticker: {ticker}")

        baseline_price = price_data.price
        baseline_shares_equivalent = initial_capital / baseline_price

        self._logger.debug(
            "Baseline established: price=%.2f, equivalent_shares=%.4f",
            baseline_price,
            baseline_shares_equivalent,
        )

        # Step 2: Create portfolio for experiment
        portfolio = self.portfolio_repo.create(
            tenant_id=tenant_id,
            name=f"Experiment: {name}",
            description=f"Trading experiment for {ticker} with ${initial_capital:.2f} initial capital",
            portfolio_type="EXPERIMENT",
            trading_state="RUNNING",
            trading_hours_policy="OPEN_ONLY",
        )

        self._logger.debug("Created portfolio: %s", portfolio.id)

        # Step 3: Create position with initial cash (no shares yet)
        position = self.positions_repo.create(
            tenant_id=tenant_id,
            portfolio_id=portfolio.id,
            asset_symbol=ticker,
            qty=0.0,  # Start with no shares
            anchor_price=baseline_price,  # Set anchor to baseline
            avg_cost=None,
            cash=initial_capital,  # All capital in cash initially
        )

        # Link position to portfolio
        self.portfolio_repo.add_position(tenant_id, portfolio.id, position.id)

        self._logger.debug("Created position: %s", position.id)

        # Step 4: Create and save experiment
        now = datetime.now(timezone.utc)
        experiment = TradingExperiment(
            id=f"exp_{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            name=name,
            ticker=ticker,
            initial_capital=initial_capital,
            status="RUNNING",
            started_at=now,
            position_id=position.id,
            portfolio_id=portfolio.id,
            baseline_price=baseline_price,
            baseline_shares_equivalent=baseline_shares_equivalent,
            current_portfolio_value=initial_capital,  # Start equals initial
            current_buyhold_value=initial_capital,  # Start equals initial
            created_at=now,
            updated_at=now,
        )

        self.experiment_repo.save(experiment)

        self._logger.info(
            "Experiment created: id=%s, position=%s, portfolio=%s",
            experiment.id,
            position.id,
            portfolio.id,
        )

        return {
            "experiment_id": experiment.id,
            "name": experiment.name,
            "ticker": experiment.ticker,
            "initial_capital": experiment.initial_capital,
            "position_id": position.id,
            "portfolio_id": portfolio.id,
            "baseline_price": baseline_price,
            "baseline_shares_equivalent": baseline_shares_equivalent,
            "status": experiment.status,
        }
