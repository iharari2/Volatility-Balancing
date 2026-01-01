# =========================
# backend/infrastructure/persistence/sql/simulation_repo_sql.py
# =========================

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import desc

from domain.entities.simulation_result import SimulationResult
from domain.ports.simulation_repo import SimulationRepo
from infrastructure.persistence.sql.models import SimulationResultModel


def _entity_from_model(model: SimulationResultModel) -> SimulationResult:
    """Convert SQLAlchemy model to domain entity."""
    return SimulationResult(
        id=UUID(model.id),
        ticker=model.ticker,
        start_date=model.start_date.isoformat(),
        end_date=model.end_date.isoformat(),
        total_trading_days=model.total_trading_days,
        initial_cash=model.initial_cash,
        algorithm_trades=model.algorithm_trades,
        algorithm_pnl=model.algorithm_pnl,
        algorithm_return_pct=model.algorithm_return_pct,
        algorithm_volatility=model.algorithm_volatility,
        algorithm_sharpe_ratio=model.algorithm_sharpe_ratio,
        algorithm_max_drawdown=model.algorithm_max_drawdown,
        buy_hold_pnl=model.buy_hold_pnl,
        buy_hold_return_pct=model.buy_hold_return_pct,
        buy_hold_volatility=model.buy_hold_volatility,
        buy_hold_sharpe_ratio=model.buy_hold_sharpe_ratio,
        buy_hold_max_drawdown=model.buy_hold_max_drawdown,
        excess_return=model.excess_return,
        alpha=model.alpha,
        beta=model.beta,
        information_ratio=model.information_ratio,
        trade_log=model.trade_log or [],
        daily_returns=model.daily_returns or [],
        dividend_analysis=model.dividend_analysis or {},
        price_data=model.price_data or [],
        trigger_analysis=model.trigger_analysis or [],
        time_series_data=model.time_series_data or [],
        debug_info=model.debug_info or [],
        created_at=model.created_at,
    )


def _model_from_entity(entity: SimulationResult) -> SimulationResultModel:
    """Convert domain entity to SQLAlchemy model."""
    return SimulationResultModel(
        id=str(entity.id),
        ticker=entity.ticker,
        start_date=datetime.fromisoformat(entity.start_date.replace("Z", "+00:00")),
        end_date=datetime.fromisoformat(entity.end_date.replace("Z", "+00:00")),
        total_trading_days=entity.total_trading_days,
        initial_cash=entity.initial_cash,
        algorithm_trades=entity.algorithm_trades,
        algorithm_pnl=entity.algorithm_pnl,
        algorithm_return_pct=entity.algorithm_return_pct,
        algorithm_volatility=entity.algorithm_volatility,
        algorithm_sharpe_ratio=entity.algorithm_sharpe_ratio,
        algorithm_max_drawdown=entity.algorithm_max_drawdown,
        buy_hold_pnl=entity.buy_hold_pnl,
        buy_hold_return_pct=entity.buy_hold_return_pct,
        buy_hold_volatility=entity.buy_hold_volatility,
        buy_hold_sharpe_ratio=entity.buy_hold_sharpe_ratio,
        buy_hold_max_drawdown=entity.buy_hold_max_drawdown,
        excess_return=entity.excess_return,
        alpha=entity.alpha,
        beta=entity.beta,
        information_ratio=entity.information_ratio,
        trade_log=entity.trade_log,
        daily_returns=entity.daily_returns,
        dividend_analysis=entity.dividend_analysis,
        price_data=entity.price_data,
        trigger_analysis=entity.trigger_analysis,
        time_series_data=entity.time_series_data,
        debug_info=entity.debug_info,
        created_at=entity.created_at,
        updated_at=datetime.now(timezone.utc),
    )


class SQLSimulationRepo(SimulationRepo):
    """SQL implementation of simulation repository."""

    def __init__(self, session: Session):
        self.session = session

    def save_simulation_result(self, result: SimulationResult) -> None:
        """Save a simulation result."""
        # Check if result already exists
        existing = (
            self.session.query(SimulationResultModel)
            .filter(SimulationResultModel.id == str(result.id))
            .first()
        )

        if existing:
            # Update existing
            existing.ticker = result.ticker
            existing.start_date = datetime.fromisoformat(result.start_date.replace("Z", "+00:00"))
            existing.end_date = datetime.fromisoformat(result.end_date.replace("Z", "+00:00"))
            existing.total_trading_days = result.total_trading_days
            existing.initial_cash = result.initial_cash
            existing.algorithm_trades = result.algorithm_trades
            existing.algorithm_pnl = result.algorithm_pnl
            existing.algorithm_return_pct = result.algorithm_return_pct
            existing.algorithm_volatility = result.algorithm_volatility
            existing.algorithm_sharpe_ratio = result.algorithm_sharpe_ratio
            existing.algorithm_max_drawdown = result.algorithm_max_drawdown
            existing.buy_hold_pnl = result.buy_hold_pnl
            existing.buy_hold_return_pct = result.buy_hold_return_pct
            existing.buy_hold_volatility = result.buy_hold_volatility
            existing.buy_hold_sharpe_ratio = result.buy_hold_sharpe_ratio
            existing.buy_hold_max_drawdown = result.buy_hold_max_drawdown
            existing.excess_return = result.excess_return
            existing.alpha = result.alpha
            existing.beta = result.beta
            existing.information_ratio = result.information_ratio
            existing.trade_log = result.trade_log
            existing.daily_returns = result.daily_returns
            existing.dividend_analysis = result.dividend_analysis
            existing.price_data = result.price_data
            existing.trigger_analysis = result.trigger_analysis
            existing.time_series_data = result.time_series_data
            existing.debug_info = result.debug_info
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # Create new
            model = _model_from_entity(result)
            self.session.add(model)

        self.session.commit()

    def get_simulation_result(self, result_id: UUID) -> Optional[SimulationResult]:
        """Get a simulation result by ID."""
        model = (
            self.session.query(SimulationResultModel)
            .filter(SimulationResultModel.id == str(result_id))
            .first()
        )

        if model:
            return _entity_from_model(model)
        return None

    def list_simulations(self, limit: int = 100, offset: int = 0) -> List[SimulationResult]:
        """List all simulation results with pagination."""
        models = (
            self.session.query(SimulationResultModel)
            .order_by(desc(SimulationResultModel.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [_entity_from_model(model) for model in models]

    def get_simulations_by_ticker(self, ticker: str, limit: int = 100) -> List[SimulationResult]:
        """Get simulation results for a specific ticker."""
        models = (
            self.session.query(SimulationResultModel)
            .filter(SimulationResultModel.ticker == ticker)
            .order_by(desc(SimulationResultModel.created_at))
            .limit(limit)
            .all()
        )

        return [_entity_from_model(model) for model in models]

    def delete_simulation_result(self, result_id: UUID) -> bool:
        """Delete a simulation result by ID."""
        model = (
            self.session.query(SimulationResultModel)
            .filter(SimulationResultModel.id == str(result_id))
            .first()
        )

        if model:
            self.session.delete(model)
            self.session.commit()
            return True
        return False

    def run_simulation(
        self, ticker: str, start_date: str, end_date: str, parameters: dict
    ) -> SimulationResult:
        """Run a simulation with given parameters."""
        # This is a placeholder implementation
        # In a real implementation, this would call the actual simulation use case
        from domain.entities.simulation_result import SimulationResult as DomainSimulationResult

        # Mock metrics for now
        metrics = {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.05,
            "volatility": 0.12,
            "calmar_ratio": 3.0,
            "sortino_ratio": 1.5,
            "win_rate": 0.6,
            "profit_factor": 1.8,
            "trade_count": 25,
            "avg_trade_duration": 5.2,
        }

        result = DomainSimulationResult.create(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters,
            metrics=metrics,
        )

        self.save_simulation_result(result)
        return result
