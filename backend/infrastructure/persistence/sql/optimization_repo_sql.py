# =========================
# backend/infrastructure/persistence/sql/optimization_repo_sql.py
# =========================

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import desc

from domain.entities.optimization_config import OptimizationConfig, OptimizationStatus
from domain.entities.optimization_result import (
    OptimizationResult,
    OptimizationResultStatus,
    ParameterCombination,
)
from domain.ports.optimization_repo import (
    HeatmapDataRepo,
    OptimizationConfigRepo,
    OptimizationResultRepo,
)
from domain.value_objects.heatmap_data import HeatmapCell, HeatmapData, HeatmapMetric
from domain.value_objects.optimization_criteria import (
    Constraint,
    ConstraintType,
    OptimizationCriteria,
    OptimizationMetric,
)
from domain.value_objects.parameter_range import ParameterRange, ParameterType
from infrastructure.persistence.sql.models import (
    HeatmapDataModel,
    OptimizationConfigModel,
    OptimizationResultModel,
)


# --- ParameterRange serialization ---

def _parameter_ranges_to_json(ranges: Dict[str, ParameterRange]) -> Dict[str, Any]:
    result = {}
    for key, pr in ranges.items():
        result[key] = {
            "min_value": pr.min_value,
            "max_value": pr.max_value,
            "step_size": pr.step_size,
            "parameter_type": pr.parameter_type.value,
            "name": pr.name,
            "description": pr.description,
            "categorical_values": pr.categorical_values,
        }
    return result


def _parameter_ranges_from_json(data: Dict[str, Any]) -> Dict[str, ParameterRange]:
    result = {}
    for key, d in data.items():
        result[key] = ParameterRange(
            min_value=d["min_value"],
            max_value=d["max_value"],
            step_size=d["step_size"],
            parameter_type=ParameterType(d["parameter_type"]),
            name=d["name"],
            description=d.get("description", ""),
            categorical_values=d.get("categorical_values"),
        )
    return result


# --- OptimizationCriteria serialization ---

def _criteria_to_json(criteria: OptimizationCriteria) -> Dict[str, Any]:
    return {
        "primary_metric": criteria.primary_metric.value,
        "secondary_metrics": [m.value for m in criteria.secondary_metrics],
        "constraints": [
            {
                "metric": c.metric.value,
                "constraint_type": c.constraint_type.value,
                "value": c.value,
                "weight": c.weight,
                "description": c.description,
            }
            for c in criteria.constraints
        ],
        "weights": {m.value: w for m, w in criteria.weights.items()},
        "minimize": criteria.minimize,
        "description": criteria.description,
    }


def _criteria_from_json(data: Dict[str, Any]) -> OptimizationCriteria:
    return OptimizationCriteria(
        primary_metric=OptimizationMetric(data["primary_metric"]),
        secondary_metrics=[OptimizationMetric(m) for m in data["secondary_metrics"]],
        constraints=[
            Constraint(
                metric=OptimizationMetric(c["metric"]),
                constraint_type=ConstraintType(c["constraint_type"]),
                value=c["value"],
                weight=c.get("weight", 1.0),
                description=c.get("description", ""),
            )
            for c in data.get("constraints", [])
        ],
        weights={OptimizationMetric(k): v for k, v in data["weights"].items()},
        minimize=data.get("minimize", False),
        description=data.get("description", ""),
    )


# --- Metrics serialization ---

def _metrics_to_json(metrics: Dict[OptimizationMetric, float]) -> Dict[str, float]:
    return {m.value: v for m, v in metrics.items()}


def _metrics_from_json(data: Dict[str, float]) -> Dict[OptimizationMetric, float]:
    return {OptimizationMetric(k): v for k, v in data.items()}


# --- Config converters ---

def _config_from_model(model: OptimizationConfigModel) -> OptimizationConfig:
    return OptimizationConfig(
        id=UUID(model.id),
        name=model.name,
        ticker=model.ticker,
        start_date=model.start_date,
        end_date=model.end_date,
        parameter_ranges=_parameter_ranges_from_json(model.parameter_ranges),
        optimization_criteria=_criteria_from_json(model.optimization_criteria),
        status=OptimizationStatus(model.status),
        created_by=UUID(model.created_by),
        created_at=model.created_at,
        updated_at=model.updated_at,
        description=model.description,
        max_combinations=model.max_combinations,
        batch_size=model.batch_size,
        initial_cash=model.initial_cash,
        intraday_interval_minutes=model.intraday_interval_minutes,
        include_after_hours=model.include_after_hours,
    )


def _config_to_model(entity: OptimizationConfig) -> OptimizationConfigModel:
    return OptimizationConfigModel(
        id=str(entity.id),
        name=entity.name,
        ticker=entity.ticker,
        start_date=entity.start_date,
        end_date=entity.end_date,
        parameter_ranges=_parameter_ranges_to_json(entity.parameter_ranges),
        optimization_criteria=_criteria_to_json(entity.optimization_criteria),
        status=entity.status.value,
        created_by=str(entity.created_by),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        description=entity.description,
        max_combinations=entity.max_combinations,
        batch_size=entity.batch_size,
        initial_cash=entity.initial_cash,
        intraday_interval_minutes=entity.intraday_interval_minutes,
        include_after_hours=entity.include_after_hours,
    )


# --- Result converters ---

def _result_from_model(model: OptimizationResultModel) -> OptimizationResult:
    param_data = model.parameter_combination
    return OptimizationResult(
        id=UUID(model.id),
        config_id=UUID(model.config_id),
        parameter_combination=ParameterCombination(
            parameters=param_data.get("parameters", {}),
            combination_id=model.combination_id,
            created_at=datetime.fromisoformat(param_data["created_at"])
            if "created_at" in param_data
            else model.created_at,
        ),
        metrics=_metrics_from_json(model.metrics or {}),
        simulation_result=model.simulation_result,
        status=OptimizationResultStatus(model.status),
        error_message=model.error_message,
        created_at=model.created_at,
        completed_at=model.completed_at,
        execution_time_seconds=model.execution_time_seconds,
    )


def _result_to_model(entity: OptimizationResult) -> OptimizationResultModel:
    return OptimizationResultModel(
        id=str(entity.id),
        config_id=str(entity.config_id),
        parameter_combination={
            "parameters": entity.parameter_combination.parameters,
            "created_at": entity.parameter_combination.created_at.isoformat(),
        },
        combination_id=entity.parameter_combination.combination_id,
        metrics=_metrics_to_json(entity.metrics),
        simulation_result=entity.simulation_result,
        status=entity.status.value,
        error_message=entity.error_message,
        execution_time_seconds=entity.execution_time_seconds,
        created_at=entity.created_at,
        completed_at=entity.completed_at,
    )


# --- HeatmapData converters ---

def _heatmap_from_model(model: HeatmapDataModel) -> HeatmapData:
    data = model.heatmap_data
    cells = [
        HeatmapCell(
            x_value=c["x_value"],
            y_value=c["y_value"],
            metric_value=c["metric_value"],
            parameter_combination_id=c["parameter_combination_id"],
            is_valid=c.get("is_valid", True),
            error_message=c.get("error_message"),
        )
        for c in data["cells"]
    ]
    return HeatmapData(
        config_id=model.config_id,
        x_parameter=model.x_parameter,
        y_parameter=model.y_parameter,
        metric=HeatmapMetric(model.metric),
        cells=cells,
        x_values=data["x_values"],
        y_values=data["y_values"],
        min_value=data["min_value"],
        max_value=data["max_value"],
        mean_value=data["mean_value"],
        created_at=data.get("created_at", model.created_at.isoformat()),
    )


def _heatmap_to_model(entity: HeatmapData) -> HeatmapDataModel:
    return HeatmapDataModel(
        id=str(uuid4()),
        config_id=str(entity.config_id),
        x_parameter=entity.x_parameter,
        y_parameter=entity.y_parameter,
        metric=entity.metric.value if isinstance(entity.metric, HeatmapMetric) else entity.metric,
        heatmap_data={
            "cells": [
                {
                    "x_value": c.x_value,
                    "y_value": c.y_value,
                    "metric_value": c.metric_value,
                    "parameter_combination_id": c.parameter_combination_id,
                    "is_valid": c.is_valid,
                    "error_message": c.error_message,
                }
                for c in entity.cells
            ],
            "x_values": entity.x_values,
            "y_values": entity.y_values,
            "min_value": entity.min_value,
            "max_value": entity.max_value,
            "mean_value": entity.mean_value,
            "created_at": entity.created_at,
        },
    )


# ============================================================
# Repository implementations
# ============================================================


class SQLOptimizationConfigRepo(OptimizationConfigRepo):
    """SQL implementation of optimization configuration repository."""

    def __init__(self, session_factory):
        self._sf = session_factory

    def save(self, config: OptimizationConfig) -> None:
        with self._sf() as session:
            existing = (
                session.query(OptimizationConfigModel)
                .filter(OptimizationConfigModel.id == str(config.id))
                .first()
            )
            if existing:
                existing.name = config.name
                existing.ticker = config.ticker
                existing.start_date = config.start_date
                existing.end_date = config.end_date
                existing.parameter_ranges = _parameter_ranges_to_json(config.parameter_ranges)
                existing.optimization_criteria = _criteria_to_json(config.optimization_criteria)
                existing.status = config.status.value
                existing.description = config.description
                existing.max_combinations = config.max_combinations
                existing.batch_size = config.batch_size
                existing.initial_cash = config.initial_cash
                existing.intraday_interval_minutes = config.intraday_interval_minutes
                existing.include_after_hours = config.include_after_hours
                existing.updated_at = datetime.now(timezone.utc)
            else:
                session.add(_config_to_model(config))
            session.commit()

    def get_by_id(self, config_id: UUID) -> Optional[OptimizationConfig]:
        with self._sf() as session:
            model = (
                session.query(OptimizationConfigModel)
                .filter(OptimizationConfigModel.id == str(config_id))
                .first()
            )
            return _config_from_model(model) if model else None

    def get_by_user(self, user_id: UUID) -> List[OptimizationConfig]:
        with self._sf() as session:
            models = (
                session.query(OptimizationConfigModel)
                .filter(OptimizationConfigModel.created_by == str(user_id))
                .order_by(desc(OptimizationConfigModel.created_at))
                .all()
            )
            return [_config_from_model(m) for m in models]

    def update_status(self, config_id: UUID, status: str) -> None:
        with self._sf() as session:
            model = (
                session.query(OptimizationConfigModel)
                .filter(OptimizationConfigModel.id == str(config_id))
                .first()
            )
            if model:
                model.status = status
                model.updated_at = datetime.now(timezone.utc)
                session.commit()

    def delete(self, config_id: UUID) -> None:
        with self._sf() as session:
            model = (
                session.query(OptimizationConfigModel)
                .filter(OptimizationConfigModel.id == str(config_id))
                .first()
            )
            if model:
                session.delete(model)
                session.commit()

    def list_all(self, limit: int = 100, offset: int = 0) -> List[OptimizationConfig]:
        with self._sf() as session:
            models = (
                session.query(OptimizationConfigModel)
                .order_by(desc(OptimizationConfigModel.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [_config_from_model(m) for m in models]

    def get_all(self, limit: int = 100, offset: int = 0) -> List[OptimizationConfig]:
        return self.list_all(limit=limit, offset=offset)


class SQLOptimizationResultRepo(OptimizationResultRepo):
    """SQL implementation of optimization result repository."""

    def __init__(self, session_factory):
        self._sf = session_factory

    def save_result(self, result: OptimizationResult) -> None:
        with self._sf() as session:
            existing = (
                session.query(OptimizationResultModel)
                .filter(OptimizationResultModel.id == str(result.id))
                .first()
            )
            if existing:
                self._update_model(existing, result)
            else:
                session.add(_result_to_model(result))
            session.commit()

    def _update_model(self, model: OptimizationResultModel, entity: OptimizationResult):
        model.parameter_combination = {
            "parameters": entity.parameter_combination.parameters,
            "created_at": entity.parameter_combination.created_at.isoformat(),
        }
        model.combination_id = entity.parameter_combination.combination_id
        model.metrics = _metrics_to_json(entity.metrics)
        model.simulation_result = entity.simulation_result
        model.status = entity.status.value
        model.error_message = entity.error_message
        model.execution_time_seconds = entity.execution_time_seconds
        model.completed_at = entity.completed_at

    def get_by_config(self, config_id: UUID) -> List[OptimizationResult]:
        with self._sf() as session:
            models = (
                session.query(OptimizationResultModel)
                .filter(OptimizationResultModel.config_id == str(config_id))
                .order_by(OptimizationResultModel.created_at)
                .all()
            )
            return [_result_from_model(m) for m in models]

    def get_by_combination_id(self, combination_id: str) -> Optional[OptimizationResult]:
        with self._sf() as session:
            model = (
                session.query(OptimizationResultModel)
                .filter(OptimizationResultModel.combination_id == combination_id)
                .first()
            )
            return _result_from_model(model) if model else None

    def update_result(self, result: OptimizationResult) -> None:
        with self._sf() as session:
            model = (
                session.query(OptimizationResultModel)
                .filter(OptimizationResultModel.id == str(result.id))
                .first()
            )
            if model:
                self._update_model(model, result)
                session.commit()

    def delete_by_config(self, config_id: UUID) -> None:
        with self._sf() as session:
            session.query(OptimizationResultModel).filter(
                OptimizationResultModel.config_id == str(config_id)
            ).delete()
            session.commit()

    def get_completed_results(self, config_id: UUID) -> List[OptimizationResult]:
        with self._sf() as session:
            models = (
                session.query(OptimizationResultModel)
                .filter(
                    OptimizationResultModel.config_id == str(config_id),
                    OptimizationResultModel.status == "completed",
                )
                .order_by(OptimizationResultModel.created_at)
                .all()
            )
            return [_result_from_model(m) for m in models]

    def get_failed_results(self, config_id: UUID) -> List[OptimizationResult]:
        with self._sf() as session:
            models = (
                session.query(OptimizationResultModel)
                .filter(
                    OptimizationResultModel.config_id == str(config_id),
                    OptimizationResultModel.status == "failed",
                )
                .order_by(OptimizationResultModel.created_at)
                .all()
            )
            return [_result_from_model(m) for m in models]


class SQLHeatmapDataRepo(HeatmapDataRepo):
    """SQL implementation of heatmap data repository."""

    def __init__(self, session_factory):
        self._sf = session_factory

    def save_heatmap_data(self, heatmap_data: HeatmapData) -> None:
        with self._sf() as session:
            # Delete existing data for the same parameters/metric combo
            config_id_str = str(heatmap_data.config_id)
            metric_val = (
                heatmap_data.metric.value
                if isinstance(heatmap_data.metric, HeatmapMetric)
                else heatmap_data.metric
            )
            session.query(HeatmapDataModel).filter(
                HeatmapDataModel.config_id == config_id_str,
                HeatmapDataModel.x_parameter == heatmap_data.x_parameter,
                HeatmapDataModel.y_parameter == heatmap_data.y_parameter,
                HeatmapDataModel.metric == metric_val,
            ).delete()
            session.add(_heatmap_to_model(heatmap_data))
            session.commit()

    def get_heatmap_data(
        self, config_id: UUID, x_parameter: str, y_parameter: str, metric: str
    ) -> Optional[HeatmapData]:
        with self._sf() as session:
            model = (
                session.query(HeatmapDataModel)
                .filter(
                    HeatmapDataModel.config_id == str(config_id),
                    HeatmapDataModel.x_parameter == x_parameter,
                    HeatmapDataModel.y_parameter == y_parameter,
                    HeatmapDataModel.metric == metric,
                )
                .first()
            )
            return _heatmap_from_model(model) if model else None

    def get_available_heatmaps(self, config_id: UUID) -> List[dict]:
        with self._sf() as session:
            models = (
                session.query(HeatmapDataModel)
                .filter(HeatmapDataModel.config_id == str(config_id))
                .all()
            )
            return [
                {
                    "x_parameter": m.x_parameter,
                    "y_parameter": m.y_parameter,
                    "metric": m.metric,
                }
                for m in models
            ]

    def delete_heatmap_data(self, config_id: UUID) -> None:
        with self._sf() as session:
            session.query(HeatmapDataModel).filter(
                HeatmapDataModel.config_id == str(config_id)
            ).delete()
            session.commit()
