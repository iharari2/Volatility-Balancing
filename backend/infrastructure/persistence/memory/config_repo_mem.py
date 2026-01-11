# =========================
# backend/infrastructure/persistence/memory/config_repo_mem.py
# =========================
"""In-memory implementation of ConfigRepo."""

from typing import Optional, Dict, Tuple

from domain.ports.config_repo import ConfigRepo, ConfigScope
from domain.value_objects.configs import (
    TriggerConfig,
    GuardrailConfig,
    OrderPolicyConfig,
    normalize_guardrail_config,
)


class InMemoryConfigRepo(ConfigRepo):
    """In-memory configuration repository."""

    def __init__(self):
        # Store commission rates as (scope, tenant_id, asset_id) -> value
        self._commission_rates: Dict[Tuple[ConfigScope, Optional[str], Optional[str]], float] = {}
        # Set default global commission rate
        self._commission_rates[(ConfigScope.GLOBAL, None, None)] = 0.0001  # 0.01%

        # Store trigger configs by position_id
        self._trigger_configs: Dict[str, TriggerConfig] = {}

        # Store guardrail configs by position_id
        self._guardrail_configs: Dict[str, GuardrailConfig] = {}

        # Store order policy configs by position_id
        self._order_policy_configs: Dict[str, OrderPolicyConfig] = {}

    def get_commission_rate(
        self,
        tenant_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> float:
        """Get commission rate with hierarchical lookup."""
        # Try TENANT_ASSET first
        if tenant_id and asset_id:
            key = (ConfigScope.TENANT_ASSET, tenant_id, asset_id)
            if key in self._commission_rates:
                return self._commission_rates[key]

        # Try TENANT
        if tenant_id:
            key = (ConfigScope.TENANT, tenant_id, None)
            if key in self._commission_rates:
                return self._commission_rates[key]

        # Fall back to GLOBAL
        key = (ConfigScope.GLOBAL, None, None)
        return self._commission_rates.get(key, 0.0001)  # Default 0.01%

    def set_commission_rate(
        self,
        rate: float,
        scope: ConfigScope,
        tenant_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> None:
        """Set commission rate at specified scope."""
        key = (scope, tenant_id, asset_id)
        self._commission_rates[key] = rate

    def get_trigger_config(
        self,
        position_id: str,
    ) -> Optional[TriggerConfig]:
        """Get trigger configuration for a position."""
        return self._trigger_configs.get(position_id)

    def set_trigger_config(
        self,
        position_id: str,
        config: TriggerConfig,
    ) -> None:
        """Set trigger configuration for a position."""
        self._trigger_configs[position_id] = config

    def get_guardrail_config(
        self,
        position_id: str,
    ) -> Optional[GuardrailConfig]:
        """Get guardrail configuration for a position."""
        config = self._guardrail_configs.get(position_id)
        return normalize_guardrail_config(config) if config else None

    def set_guardrail_config(
        self,
        position_id: str,
        config: GuardrailConfig,
    ) -> None:
        """Set guardrail configuration for a position."""
        self._guardrail_configs[position_id] = normalize_guardrail_config(config)

    def get_order_policy_config(
        self,
        position_id: str,
    ) -> Optional[OrderPolicyConfig]:
        """Get order policy configuration for a position."""
        return self._order_policy_configs.get(position_id)

    def set_order_policy_config(
        self,
        position_id: str,
        config: OrderPolicyConfig,
    ) -> None:
        """Set order policy configuration for a position."""
        self._order_policy_configs[position_id] = config
