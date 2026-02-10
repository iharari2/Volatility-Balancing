# backend/application/dto/experiments.py
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class CreateExperimentRequest(BaseModel):
    """Request to create a new trading experiment."""
    name: str
    ticker: str
    initial_capital: float


class CreateExperimentResponse(BaseModel):
    """Response after creating an experiment."""
    experiment_id: str
    name: str
    ticker: str
    initial_capital: float
    position_id: str
    portfolio_id: str
    baseline_price: float
    baseline_shares_equivalent: float
    status: str


class ExperimentResponse(BaseModel):
    """Full experiment details response."""
    experiment_id: str
    tenant_id: str
    name: str
    ticker: str
    initial_capital: float
    status: str
    started_at: str
    ended_at: Optional[str] = None
    position_id: str
    portfolio_id: str
    baseline_price: float
    baseline_shares_equivalent: float
    current_portfolio_value: float
    current_buyhold_value: float
    evaluation_count: int
    trade_count: int
    total_commission_paid: float
    created_at: str
    updated_at: str


class ExperimentProgressResponse(BaseModel):
    """Progress comparison between portfolio and buy-and-hold."""
    experiment_id: str
    name: str
    days_running: int
    current_price: float

    # Portfolio metrics
    portfolio_value: float
    buyhold_value: float

    # Return percentages
    portfolio_return_pct: float
    buyhold_return_pct: float
    excess_return_pct: float

    # Activity metrics
    evaluation_count: int
    trade_count: int
    total_commission: float


class TickExperimentResponse(BaseModel):
    """Response after running an evaluation tick."""
    experiment_id: str
    current_price: float
    previous_portfolio_value: float
    new_portfolio_value: float
    buyhold_value: float
    trigger_detected: bool
    trade_executed: bool
    action_taken: Optional[str] = None
    order_qty: Optional[float] = None
    evaluation_count: int
    message: str


class CompleteExperimentResponse(BaseModel):
    """Response after completing an experiment."""
    experiment_id: str
    status: str
    started_at: str
    ended_at: str
    days_running: int

    # Final metrics
    initial_capital: float
    final_portfolio_value: float
    final_buyhold_value: float

    # Final returns
    portfolio_return_pct: float
    buyhold_return_pct: float
    excess_return_pct: float

    # Activity summary
    total_evaluations: int
    total_trades: int
    total_commission: float


class ExperimentListResponse(BaseModel):
    """List of experiments."""
    experiments: list[ExperimentResponse]
    total: int
