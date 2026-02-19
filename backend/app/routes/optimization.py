# =========================
# backend/app/routes/optimization.py
# =========================

from typing import List, Optional
from uuid import UUID
from datetime import datetime
import concurrent.futures
import traceback

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from application.use_cases.parameter_optimization_uc import (
    ParameterOptimizationUC,
    CreateOptimizationRequest,
    OptimizationProgress,
)
from domain.entities.optimization_config import OptimizationConfig, OptimizationStatus
from domain.entities.optimization_result import OptimizationResult
from domain.value_objects.parameter_range import ParameterRange, ParameterType
from domain.value_objects.optimization_criteria import (
    OptimizationCriteria,
    OptimizationMetric,
    Constraint,
    ConstraintType,
)
from app.di import get_parameter_optimization_uc

router = APIRouter(prefix="/v1/optimization", tags=["optimization"])

# Thread pool for background optimization runs
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


# Pydantic models for API requests/responses


class ParameterRangeRequest(BaseModel):
    """Request model for parameter range."""

    min_value: float
    max_value: float
    step_size: float
    parameter_type: str
    name: str
    description: str = ""
    categorical_values: Optional[List[str]] = None

    def to_domain(self) -> ParameterRange:
        """Convert to domain object."""
        return ParameterRange(
            min_value=self.min_value,
            max_value=self.max_value,
            step_size=self.step_size,
            parameter_type=ParameterType(self.parameter_type),
            name=self.name,
            description=self.description,
            categorical_values=self.categorical_values,
        )


class ConstraintRequest(BaseModel):
    """Request model for optimization constraint."""

    metric: str
    constraint_type: str
    value: float
    weight: float = 1.0
    description: str = ""

    def to_domain(self) -> Constraint:
        """Convert to domain object."""
        return Constraint(
            metric=OptimizationMetric(self.metric),
            constraint_type=ConstraintType(self.constraint_type),
            value=self.value,
            weight=self.weight,
            description=self.description,
        )


class OptimizationCriteriaRequest(BaseModel):
    """Request model for optimization criteria."""

    primary_metric: str
    secondary_metrics: List[str]
    constraints: List[ConstraintRequest]
    weights: dict
    minimize: bool = False
    description: str = ""

    def to_domain(self) -> OptimizationCriteria:
        """Convert to domain object."""
        return OptimizationCriteria(
            primary_metric=OptimizationMetric(self.primary_metric),
            secondary_metrics=[OptimizationMetric(m) for m in self.secondary_metrics],
            constraints=[c.to_domain() for c in self.constraints],
            weights={OptimizationMetric(k): v for k, v in self.weights.items()},
            minimize=self.minimize,
            description=self.description,
        )


class CreateOptimizationRequestModel(BaseModel):
    """Request model for creating optimization configuration."""

    name: str
    ticker: str
    start_date: datetime
    end_date: datetime
    parameter_ranges: dict  # Will be converted to ParameterRange objects
    optimization_criteria: OptimizationCriteriaRequest
    created_by: str  # Will be converted to UUID
    description: Optional[str] = None
    max_combinations: Optional[int] = None
    batch_size: int = 10
    initial_cash: float = 10000.0
    intraday_interval_minutes: int = 30
    include_after_hours: bool = False

    def to_domain(self) -> CreateOptimizationRequest:
        """Convert to domain object."""
        # Convert parameter ranges
        param_ranges = {}
        for name, range_data in self.parameter_ranges.items():
            param_ranges[name] = ParameterRangeRequest(**range_data).to_domain()

        return CreateOptimizationRequest(
            name=self.name,
            ticker=self.ticker,
            start_date=self.start_date,
            end_date=self.end_date,
            parameter_ranges=param_ranges,
            optimization_criteria=self.optimization_criteria.to_domain(),
            created_by=UUID(self.created_by),
            description=self.description,
            max_combinations=self.max_combinations,
            batch_size=self.batch_size,
            initial_cash=self.initial_cash,
            intraday_interval_minutes=self.intraday_interval_minutes,
            include_after_hours=self.include_after_hours,
        )


class OptimizationConfigResponse(BaseModel):
    """Response model for optimization configuration."""

    id: str
    name: str
    ticker: str
    start_date: datetime
    end_date: datetime
    status: str
    created_by: str
    description: Optional[str]
    max_combinations: Optional[int]
    batch_size: int
    total_combinations: int
    parameter_ranges: dict
    optimization_criteria: dict
    constraints: list
    created_at: datetime
    updated_at: datetime
    initial_cash: float
    intraday_interval_minutes: int
    include_after_hours: bool

    @classmethod
    def from_domain(cls, config: OptimizationConfig) -> "OptimizationConfigResponse":
        """Create from domain object."""
        return cls(
            id=str(config.id),
            name=config.name,
            ticker=config.ticker,
            start_date=config.start_date,
            end_date=config.end_date,
            status=config.status.value,
            created_by=str(config.created_by),
            description=config.description,
            max_combinations=config.max_combinations,
            batch_size=config.batch_size,
            total_combinations=config.calculate_total_combinations(),
            parameter_ranges={
                name: {
                    "parameter_type": pr.parameter_type.value,
                    "min_value": pr.min_value,
                    "max_value": pr.max_value,
                    "step_size": pr.step_size,
                    "name": pr.name,
                    "description": pr.description,
                }
                for name, pr in config.parameter_ranges.items()
            },
            optimization_criteria={
                "primary_metric": config.optimization_criteria.primary_metric.value,
                "secondary_metrics": [m.value for m in config.optimization_criteria.secondary_metrics],
                "minimize": config.optimization_criteria.minimize,
            },
            constraints=[
                {
                    "metric": c.metric.value,
                    "constraint_type": c.constraint_type.value,
                    "value": c.value,
                }
                for c in config.optimization_criteria.constraints
            ],
            created_at=config.created_at,
            updated_at=config.updated_at,
            initial_cash=config.initial_cash,
            intraday_interval_minutes=config.intraday_interval_minutes,
            include_after_hours=config.include_after_hours,
        )


class OptimizationProgressResponse(BaseModel):
    """Response model for optimization progress."""

    config_id: str
    total_combinations: int
    completed_combinations: int
    failed_combinations: int
    status: str
    progress_percentage: float
    remaining_combinations: int
    started_at: Optional[datetime]
    estimated_completion: Optional[datetime]

    @classmethod
    def from_domain(cls, progress: OptimizationProgress) -> "OptimizationProgressResponse":
        """Create from domain object."""
        return cls(
            config_id=str(progress.config_id),
            total_combinations=progress.total_combinations,
            completed_combinations=progress.completed_combinations,
            failed_combinations=progress.failed_combinations,
            status=progress.status,
            progress_percentage=progress.progress_percentage,
            remaining_combinations=progress.remaining_combinations,
            started_at=progress.started_at,
            estimated_completion=progress.estimated_completion,
        )


class OptimizationResultResponse(BaseModel):
    """Response model for optimization result."""

    id: str
    config_id: str
    parameter_combination: dict
    combination_id: str
    metrics: dict
    status: str
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    execution_time_seconds: Optional[float]
    simulation_result: Optional[dict] = None

    @classmethod
    def from_domain(cls, result: OptimizationResult) -> "OptimizationResultResponse":
        """Create from domain object."""
        return cls(
            id=str(result.id),
            config_id=str(result.config_id),
            parameter_combination={
                "combination_id": result.parameter_combination.combination_id,
                "parameters": result.parameter_combination.parameters,
            },
            combination_id=result.parameter_combination.combination_id,
            metrics={k.value: v for k, v in result.metrics.items()},
            status=result.status.value,
            error_message=result.error_message,
            created_at=result.created_at,
            completed_at=result.completed_at,
            execution_time_seconds=result.execution_time_seconds,
            simulation_result=result.simulation_result,
        )


# API Endpoints


@router.post("/configs", response_model=OptimizationConfigResponse)
async def create_optimization_config(
    request: CreateOptimizationRequestModel,
    optimization_uc: ParameterOptimizationUC = Depends(get_parameter_optimization_uc),
):
    """Create a new optimization configuration."""
    try:
        config = optimization_uc.create_optimization_config(request.to_domain())
        return OptimizationConfigResponse.from_domain(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/configs", response_model=List[OptimizationConfigResponse])
async def list_optimization_configs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    optimization_uc: ParameterOptimizationUC = Depends(get_parameter_optimization_uc),
):
    """List optimization configurations."""
    try:
        configs = optimization_uc.config_repo.get_all(limit=limit, offset=offset)
        return [OptimizationConfigResponse.from_domain(config) for config in configs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/configs/{config_id}", response_model=OptimizationConfigResponse)
async def get_optimization_config(
    config_id: str,
    optimization_uc: ParameterOptimizationUC = Depends(get_parameter_optimization_uc),
):
    """Get a specific optimization configuration."""
    try:
        config_uuid = UUID(config_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid config ID format")

    try:
        config = optimization_uc.config_repo.get_by_id(config_uuid)
        if not config:
            raise HTTPException(status_code=404, detail="Optimization config not found")
        return OptimizationConfigResponse.from_domain(config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def _run_optimization_background(optimization_uc: ParameterOptimizationUC, config_id: UUID):
    """Run optimization in background thread."""
    try:
        optimization_uc.run_optimization(config_id)
    except Exception as e:
        print(f"[Optimization] Background run failed: {e}")
        traceback.print_exc()
        # Try to mark as failed
        try:
            optimization_uc.config_repo.update_status(config_id, OptimizationStatus.FAILED.value)
        except Exception:
            pass


@router.post("/configs/{config_id}/start")
async def start_optimization(
    config_id: str,
    optimization_uc: ParameterOptimizationUC = Depends(get_parameter_optimization_uc),
):
    """Start an optimization run (non-blocking)."""
    try:
        config_uuid = UUID(config_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid config ID format")

    try:
        # Check if config exists and can start
        config = optimization_uc.config_repo.get_by_id(config_uuid)
        if not config:
            raise HTTPException(status_code=404, detail="Optimization config not found")
        if not config.can_start():
            raise HTTPException(
                status_code=400,
                detail=f"Cannot start optimization in status: {config.status.value}",
            )

        # Submit to background thread pool
        _executor.submit(_run_optimization_background, optimization_uc, config_uuid)

        return {
            "status": "running",
            "config_id": config_id,
            "message": "Optimization started in background",
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/configs/{config_id}/progress", response_model=OptimizationProgressResponse)
async def get_optimization_progress(
    config_id: str,
    optimization_uc: ParameterOptimizationUC = Depends(get_parameter_optimization_uc),
):
    """Get optimization progress."""
    try:
        progress = optimization_uc.get_optimization_progress(UUID(config_id))
        return OptimizationProgressResponse.from_domain(progress)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/configs/{config_id}/results", response_model=List[OptimizationResultResponse])
async def get_optimization_results(
    config_id: str,
    optimization_uc: ParameterOptimizationUC = Depends(get_parameter_optimization_uc),
):
    """Get optimization results."""
    try:
        results = optimization_uc.get_optimization_results(UUID(config_id))
        return [OptimizationResultResponse.from_domain(r) for r in results]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/configs/{config_id}/heatmap")
async def get_heatmap_data(
    config_id: str,
    x_parameter: str = Query(..., description="X-axis parameter name"),
    y_parameter: str = Query(..., description="Y-axis parameter name"),
    metric: str = Query(..., description="Metric to visualize"),
    optimization_uc: ParameterOptimizationUC = Depends(get_parameter_optimization_uc),
):
    """Get heatmap data for specific parameters and metric."""
    try:
        heatmap_data = optimization_uc.get_heatmap_data(
            UUID(config_id), x_parameter, y_parameter, metric
        )
        if not heatmap_data:
            # Generate heatmap data if it doesn't exist
            heatmap_data = optimization_uc.generate_heatmap_data(
                UUID(config_id), x_parameter, y_parameter, metric
            )

        return {
            "config_id": heatmap_data.config_id,
            "x_parameter": heatmap_data.x_parameter,
            "y_parameter": heatmap_data.y_parameter,
            "metric": heatmap_data.metric.value,
            "cells": [
                {
                    "x_value": cell.x_value,
                    "y_value": cell.y_value,
                    "metric_value": cell.metric_value,
                    "combination_id": cell.parameter_combination_id,
                    "is_valid": cell.is_valid,
                    "error_message": cell.error_message,
                }
                for cell in heatmap_data.cells
            ],
            "x_values": heatmap_data.x_values,
            "y_values": heatmap_data.y_values,
            "statistics": heatmap_data.get_statistics(),
            "created_at": heatmap_data.created_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/metrics")
async def get_available_metrics():
    """Get list of available optimization metrics."""
    return {
        "metrics": [
            {
                "value": metric.value,
                "name": metric.name,
                "description": f"Optimize for {metric.value.replace('_', ' ').title()}",
            }
            for metric in OptimizationMetric
        ]
    }


@router.get("/parameter-types")
async def get_parameter_types():
    """Get list of available parameter types."""
    return {
        "parameter_types": [
            {
                "value": param_type.value,
                "name": param_type.name,
                "description": f"Parameter type: {param_type.value}",
            }
            for param_type in ParameterType
        ]
    }
