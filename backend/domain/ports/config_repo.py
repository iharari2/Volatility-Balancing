# =========================
# backend/domain/ports/config_repo.py
# =========================
"""Port for configuration repository."""

from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum

from domain.value_objects.configs import TriggerConfig, GuardrailConfig, OrderPolicyConfig


class ConfigScope(Enum):
    """Configuration scope levels."""

    GLOBAL = "GLOBAL"
    TENANT = "TENANT"
    TENANT_ASSET = "TENANT_ASSET"
    POSITION = "POSITION"  # Position-specific config


class ConfigRepo(ABC):
    """Repository interface for configuration storage."""

    @abstractmethod
    def get_commission_rate(
        self,
        tenant_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> float:
        """
        Get commission rate with hierarchical lookup:
        1. TENANT_ASSET (if tenant_id and asset_id provided)
        2. TENANT (if tenant_id provided)
        3. GLOBAL (default)

        Returns default rate (0.0001 = 0.01%) if not found.
        """
        pass

    @abstractmethod
    def set_commission_rate(
        self,
        rate: float,
        scope: ConfigScope,
        tenant_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> None:
        """Set commission rate at specified scope."""
        pass

    @abstractmethod
    def get_trigger_config(
        self,
        position_id: str,
    ) -> Optional[TriggerConfig]:
        """
        Get trigger configuration for a position.

        Returns None if not found (caller should handle default).
        """
        pass

    @abstractmethod
    def set_trigger_config(
        self,
        position_id: str,
        config: TriggerConfig,
    ) -> None:
        """Set trigger configuration for a position."""
        pass

    @abstractmethod
    def get_guardrail_config(
        self,
        position_id: str,
    ) -> Optional[GuardrailConfig]:
        """
        Get guardrail configuration for a position.

        Returns None if not found (caller should handle default).
        """
        pass

    @abstractmethod
    def set_guardrail_config(
        self,
        position_id: str,
        config: GuardrailConfig,
    ) -> None:
        """Set guardrail configuration for a position."""
        pass

    @abstractmethod
    def get_order_policy_config(
        self,
        position_id: str,
    ) -> Optional[OrderPolicyConfig]:
        """
        Get order policy configuration for a position.

        Returns None if not found (caller should handle default).
        """
        pass

    @abstractmethod
    def set_order_policy_config(
        self,
        position_id: str,
        config: OrderPolicyConfig,
    ) -> None:
        """Set order policy configuration for a position."""
        pass
