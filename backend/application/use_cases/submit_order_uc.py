# backend/application/use_cases/submit_order_uc.py
from __future__ import annotations

import hashlib
import uuid
from typing import Any, Dict

from typing import Optional, Callable

from application.dto.orders import CreateOrderRequest, CreateOrderResponse
from domain.entities.order import Order
from domain.entities.event import Event
from domain.errors import IdempotencyConflict
from domain.ports.events_repo import EventsRepo
from domain.ports.idempotency_repo import IdempotencyRepo
from domain.ports.orders_repo import OrdersRepo
from domain.ports.positions_repo import PositionsRepo
from domain.ports.config_repo import ConfigRepo
from domain.value_objects.configs import GuardrailConfig
from infrastructure.time.clock import Clock
from infrastructure.adapters.converters import guardrail_policy_to_guardrail_config


class SubmitOrderUC:
    """Idempotent order submission flow that returns a CreateOrderResponse."""

    def __init__(
        self,
        positions: PositionsRepo,
        orders: OrdersRepo,
        idempotency: IdempotencyRepo,
        events: EventsRepo,
        config_repo: ConfigRepo,
        clock: Clock,
        guardrail_config_provider: Optional[Callable[[str, str, str], GuardrailConfig]] = None,
    ) -> None:
        self.positions = positions
        self.orders = orders
        self.idempotency = idempotency
        self.events = events
        self.config_repo = config_repo
        self.clock = clock
        # Config provider - if None, will fall back to extracting from Position entity (backward compat)
        self.guardrail_config_provider = guardrail_config_provider

    @staticmethod
    def _signature(position_id: str, req: CreateOrderRequest) -> str:
        payload: Dict[str, Any] = {"position_id": position_id, "side": req.side, "qty": req.qty}
        raw = str(sorted(payload.items())).encode()
        return hashlib.sha256(raw).hexdigest()

    def execute(
        self,
        tenant_id: str,
        portfolio_id: str,
        position_id: str,
        request: CreateOrderRequest,
        idempotency_key: str,
    ) -> CreateOrderResponse:
        # 1) Validate position
        pos = self.positions.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not pos:
            from domain.errors import PositionNotFound

            raise PositionNotFound("position_not_found")

        # 2) Signature + per-position scoped key
        sig = self._signature(position_id, request)
        scoped_key = f"{position_id}:{idempotency_key}"

        # Try to reserve idempotency key; the repo should return:
        # - None if reserved OK
        # - existing order_id if same signature was already processed
        # - a string starting with "conflict:" if same key but different signature
        existing = self.idempotency.reserve(scoped_key, sig)
        if isinstance(existing, str):
            if existing.startswith("conflict:"):
                raise IdempotencyConflict("idempotency_signature_mismatch")
            # existing is an order_id for the same signature → return same response
            return CreateOrderResponse(order_id=existing, accepted=True, position_id=position_id)

        # 3) Daily cap guardrail
        # Get guardrail config from provider or fall back to extracting from Position (backward compat)
        if self.guardrail_config_provider:
            guardrail_config = self.guardrail_config_provider(tenant_id, portfolio_id, position_id)
        else:
            # Fallback: extract from Position entity (for backward compatibility)
            guardrail_config = guardrail_policy_to_guardrail_config(pos.guardrails)

        # Get max_orders_per_day from config (with fallback to Position for backward compat)
        max_orders_per_day = (
            guardrail_config.max_orders_per_day
            if guardrail_config.max_orders_per_day is not None
            else pos.guardrails.max_orders_per_day
        )

        today = self.clock.now().date()
        if self.orders.count_for_position_on_day(position_id, today) >= max_orders_per_day:
            from domain.errors import GuardrailBreach

            raise GuardrailBreach("daily_order_cap_exceeded")

        # Note: Allocation guardrails (%cash/stock) are validated at fill time in ExecuteOrderUC
        # because price is required for validation and is only available at fill time.
        # This ensures all trades respect min_stock_pct and max_stock_pct limits.

        # 4) Get commission rate from config store (with fallback to OrderPolicy)
        commission_rate = self.config_repo.get_commission_rate(
            tenant_id=tenant_id,
            asset_id=pos.asset_symbol,  # Use asset_symbol instead of ticker
        )
        # Fallback to OrderPolicy if config not found (backward compatibility)
        # Note: Config store returns default 0.0001, so we check if it matches OrderPolicy
        # If OrderPolicy has a different rate, use that instead
        if pos.order_policy.commission_rate != 0.0001:
            commission_rate = pos.order_policy.commission_rate

        # Calculate estimated commission (optional, for UI)
        # Note: Price is not in CreateOrderRequest, so we can't calculate exact estimate
        # We'll leave commission_estimated as None for now (can be calculated later when price is known)
        commission_estimated = None

        # 5) Create order with commission snapshot
        order_id = f"ord_{uuid.uuid4().hex[:8]}"
        order = Order(
            id=order_id,
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            side=request.side,
            qty=request.qty,
            status="submitted",
            idempotency_key=idempotency_key,
            request_signature={
                "position_id": position_id,
                "side": request.side,
                "qty": request.qty,
            },
            commission_rate_snapshot=commission_rate,
            commission_estimated=commission_estimated,
        )
        self.orders.save(order)

        # Finalize idempotency outcome
        self.idempotency.put(scoped_key, order_id, sig)

        # 6) Event
        evt = Event(
            id=f"evt_{order_id}",
            position_id=position_id,
            type="order_submitted",
            inputs={"side": request.side, "qty": request.qty},
            outputs={"order_id": order_id},
            message=f"order submitted ({request.side} {request.qty})",
            ts=self.clock.now(),
        )
        self.events.append(evt)

        return CreateOrderResponse(order_id=order_id, accepted=True, position_id=position_id)
