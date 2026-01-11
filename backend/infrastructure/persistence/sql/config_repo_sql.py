# =========================
# backend/infrastructure/persistence/sql/config_repo_sql.py
# =========================
"""SQL implementation of ConfigRepo."""

from __future__ import annotations

from typing import Optional
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from domain.ports.config_repo import ConfigRepo, ConfigScope
from domain.value_objects.configs import (
    TriggerConfig,
    GuardrailConfig,
    OrderPolicyConfig,
    normalize_guardrail_config,
)
from .models import (
    CommissionRateModel,
    TriggerConfigModel,
    GuardrailConfigModel,
    OrderPolicyConfigModel,
)

__all__ = ["SQLConfigRepo"]


class SQLConfigRepo(ConfigRepo):
    """SQL implementation of configuration repository."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory
        # Initialize default global commission rate if it doesn't exist
        # Use a separate session to avoid transaction issues
        self._ensure_default_commission_rate()

    def _ensure_default_commission_rate(self) -> None:
        """Ensure default global commission rate exists."""
        from uuid import uuid4

        with self._sf() as s:
            existing = s.scalar(
                select(CommissionRateModel).where(
                    CommissionRateModel.scope == ConfigScope.GLOBAL.value,
                    CommissionRateModel.tenant_id.is_(None),
                    CommissionRateModel.asset_id.is_(None),
                )
            )
            if not existing:
                default_rate = CommissionRateModel(
                    id=f"cr_{uuid4().hex[:8]}",
                    scope=ConfigScope.GLOBAL.value,
                    tenant_id=None,
                    asset_id=None,
                    rate=0.0001,  # 0.01% default
                )
                s.add(default_rate)
                s.commit()

    def get_commission_rate(
        self,
        tenant_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> float:
        """Get commission rate with hierarchical lookup."""
        with self._sf() as s:
            # Try TENANT_ASSET first
            if tenant_id and asset_id:
                row = s.scalar(
                    select(CommissionRateModel).where(
                        CommissionRateModel.scope == ConfigScope.TENANT_ASSET.value,
                        CommissionRateModel.tenant_id == tenant_id,
                        CommissionRateModel.asset_id == asset_id,
                    )
                )
                if row:
                    return row.rate

            # Try TENANT
            if tenant_id:
                row = s.scalar(
                    select(CommissionRateModel).where(
                        CommissionRateModel.scope == ConfigScope.TENANT.value,
                        CommissionRateModel.tenant_id == tenant_id,
                        CommissionRateModel.asset_id.is_(None),
                    )
                )
                if row:
                    return row.rate

            # Fall back to GLOBAL
            row = s.scalar(
                select(CommissionRateModel).where(
                    CommissionRateModel.scope == ConfigScope.GLOBAL.value,
                    CommissionRateModel.tenant_id.is_(None),
                    CommissionRateModel.asset_id.is_(None),
                )
            )
            if row:
                return row.rate

            # Default if nothing found (shouldn't happen after _ensure_default_commission_rate)
            return 0.0001

    def set_commission_rate(
        self,
        rate: float,
        scope: ConfigScope,
        tenant_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> None:
        """Set commission rate at specified scope."""
        from uuid import uuid4

        with self._sf() as s:
            # Check if exists
            existing = s.scalar(
                select(CommissionRateModel).where(
                    CommissionRateModel.scope == scope.value,
                    CommissionRateModel.tenant_id == tenant_id,
                    CommissionRateModel.asset_id == asset_id,
                )
            )
            if existing:
                existing.rate = rate
                existing.updated_at = datetime.now(timezone.utc)
            else:
                new_rate = CommissionRateModel(
                    id=f"cr_{uuid4().hex[:8]}",
                    scope=scope.value,
                    tenant_id=tenant_id,
                    asset_id=asset_id,
                    rate=rate,
                )
                s.add(new_rate)
            s.commit()

    def get_trigger_config(
        self,
        position_id: str,
    ) -> Optional[TriggerConfig]:
        """Get trigger configuration for a position."""
        with self._sf() as s:
            row = s.scalar(
                select(TriggerConfigModel).where(TriggerConfigModel.position_id == position_id)
            )
            if not row:
                return None
            return TriggerConfig(
                up_threshold_pct=Decimal(str(row.up_threshold_pct)),
                down_threshold_pct=Decimal(str(row.down_threshold_pct)),
            )

    def set_trigger_config(
        self,
        position_id: str,
        config: TriggerConfig,
    ) -> None:
        """Set trigger configuration for a position."""
        with self._sf() as s:
            existing = s.scalar(
                select(TriggerConfigModel).where(TriggerConfigModel.position_id == position_id)
            )
            if existing:
                existing.up_threshold_pct = float(config.up_threshold_pct)
                existing.down_threshold_pct = float(config.down_threshold_pct)
                existing.updated_at = datetime.now(timezone.utc)
            else:
                new_config = TriggerConfigModel(
                    position_id=position_id,
                    up_threshold_pct=float(config.up_threshold_pct),
                    down_threshold_pct=float(config.down_threshold_pct),
                )
                s.add(new_config)
            s.commit()

    def get_guardrail_config(
        self,
        position_id: str,
    ) -> Optional[GuardrailConfig]:
        """Get guardrail configuration for a position."""
        with self._sf() as s:
            row = s.scalar(
                select(GuardrailConfigModel).where(GuardrailConfigModel.position_id == position_id)
            )
            if not row:
                return None
            return normalize_guardrail_config(
                GuardrailConfig(
                    min_stock_pct=Decimal(str(row.min_stock_pct)),
                    max_stock_pct=Decimal(str(row.max_stock_pct)),
                    max_trade_pct_of_position=(
                        Decimal(str(row.max_trade_pct_of_position))
                        if row.max_trade_pct_of_position is not None
                        else None
                    ),
                    max_daily_notional=(
                        Decimal(str(row.max_daily_notional))
                        if row.max_daily_notional is not None
                        else None
                    ),
                    max_orders_per_day=row.max_orders_per_day,
                )
            )

    def set_guardrail_config(
        self,
        position_id: str,
        config: GuardrailConfig,
    ) -> None:
        """Set guardrail configuration for a position."""
        config = normalize_guardrail_config(config)
        with self._sf() as s:
            existing = s.scalar(
                select(GuardrailConfigModel).where(GuardrailConfigModel.position_id == position_id)
            )
            if existing:
                existing.min_stock_pct = float(config.min_stock_pct)
                existing.max_stock_pct = float(config.max_stock_pct)
                existing.max_trade_pct_of_position = (
                    float(config.max_trade_pct_of_position)
                    if config.max_trade_pct_of_position
                    else None
                )
                existing.max_daily_notional = (
                    float(config.max_daily_notional) if config.max_daily_notional else None
                )
                existing.max_orders_per_day = config.max_orders_per_day
                existing.updated_at = datetime.now(timezone.utc)
            else:
                new_config = GuardrailConfigModel(
                    position_id=position_id,
                    min_stock_pct=float(config.min_stock_pct),
                    max_stock_pct=float(config.max_stock_pct),
                    max_trade_pct_of_position=(
                        float(config.max_trade_pct_of_position)
                        if config.max_trade_pct_of_position
                        else None
                    ),
                    max_daily_notional=(
                        float(config.max_daily_notional) if config.max_daily_notional else None
                    ),
                    max_orders_per_day=config.max_orders_per_day,
                )
                s.add(new_config)
            s.commit()

    def get_order_policy_config(
        self,
        position_id: str,
    ) -> Optional[OrderPolicyConfig]:
        """Get order policy configuration for a position."""
        with self._sf() as s:
            row = s.scalar(
                select(OrderPolicyConfigModel).where(
                    OrderPolicyConfigModel.position_id == position_id
                )
            )
            if not row:
                return None
            return OrderPolicyConfig(
                min_qty=Decimal(str(row.min_qty)),
                min_notional=Decimal(str(row.min_notional)),
                lot_size=Decimal(str(row.lot_size)),
                qty_step=Decimal(str(row.qty_step)),
                action_below_min=row.action_below_min,
                rebalance_ratio=Decimal(str(row.rebalance_ratio)),
                order_sizing_strategy=row.order_sizing_strategy,
                allow_after_hours=row.allow_after_hours,
                commission_rate=(
                    Decimal(str(row.commission_rate)) if row.commission_rate is not None else None
                ),
            )

    def set_order_policy_config(
        self,
        position_id: str,
        config: OrderPolicyConfig,
    ) -> None:
        """Set order policy configuration for a position."""
        with self._sf() as s:
            existing = s.scalar(
                select(OrderPolicyConfigModel).where(
                    OrderPolicyConfigModel.position_id == position_id
                )
            )
            if existing:
                existing.min_qty = float(config.min_qty)
                existing.min_notional = float(config.min_notional)
                existing.lot_size = float(config.lot_size)
                existing.qty_step = float(config.qty_step)
                existing.action_below_min = config.action_below_min
                existing.rebalance_ratio = float(config.rebalance_ratio)
                existing.order_sizing_strategy = config.order_sizing_strategy
                existing.allow_after_hours = config.allow_after_hours
                existing.commission_rate = (
                    float(config.commission_rate) if config.commission_rate else None
                )
                existing.updated_at = datetime.now(timezone.utc)
            else:
                new_config = OrderPolicyConfigModel(
                    position_id=position_id,
                    min_qty=float(config.min_qty),
                    min_notional=float(config.min_notional),
                    lot_size=float(config.lot_size),
                    qty_step=float(config.qty_step),
                    action_below_min=config.action_below_min,
                    rebalance_ratio=float(config.rebalance_ratio),
                    order_sizing_strategy=config.order_sizing_strategy,
                    allow_after_hours=config.allow_after_hours,
                    commission_rate=(
                        float(config.commission_rate) if config.commission_rate else None
                    ),
                )
                s.add(new_config)
            s.commit()
