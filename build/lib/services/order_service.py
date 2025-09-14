import uuid
from app.domain.models import Order, Side, Event
from app.ports.repositories import PositionRepo, OrderRepo, TradeRepo, EventRepo
from app.ports.services import IdempotencyPort, PricingPort, ClockPort, BrokerPort

IDEMP_TTL = 48 * 3600

class BadRequest(Exception): ...
class NotFound(Exception): ...
class Conflict(Exception): ...

class OrderService:
    def __init__(self, positions: PositionRepo, orders: OrderRepo, trades: TradeRepo, events: EventRepo,
                 idem: IdempotencyPort, pricing: PricingPort, clock: ClockPort, broker: BrokerPort):
        self.positions = positions
        self.orders = orders
        self.trades = trades
        self.events = events
        self.idem = idem
        self.pricing = pricing
        self.clock = clock
        self.broker = broker

    def submit(self, position_id: str, side: Side, qty: float, idemp_key: str) -> Order:
        if not idemp_key or not idemp_key.strip():
            raise BadRequest("missing_idempotency_key")
        if qty <= 0:
            raise BadRequest("qty_must_be_positive")

        mapped = self.idem.get_mapping(idemp_key)
        if mapped:
            existing = self.orders.get(mapped)
            if existing:
                return existing

        if not self.idem.reserve(idemp_key, IDEMP_TTL):
            mapped = self.idem.get_mapping(idemp_key)
            if mapped:
                existing = self.orders.get(mapped)
                if existing:
                    return existing
            raise Conflict("idempotency_conflict")

        pos = self.positions.get(position_id)
        if not pos:
            raise NotFound("position_not_found")

        order = Order(
            id=f"ord_{uuid.uuid4().hex[:8]}",
            position_id=position_id,
            side=side,
            qty=qty,
            idempotency_key=idemp_key,
            created_at=self.clock.now(),
        )
        self.orders.save(order)
        self.idem.set_mapping(idemp_key, order.id)

        self.events.append(Event(
            id=f"evt_{uuid.uuid4().hex[:8]}",
            position_id=position_id,
            type="order_submitted",
            ts=self.clock.now(),
            payload={"order_id": order.id, "side": side, "qty": qty},
        ))

        price = self.pricing.last_price(pos.symbol)
        trade = self.broker.execute(order, price)
        self.trades.save(trade)

        if side == Side.BUY:
            pos.asset_qty += trade.qty
            pos.cash -= trade.qty * trade.price + trade.commission
        else:
            pos.asset_qty -= trade.qty
            pos.cash += trade.qty * trade.price - trade.commission
        self.positions.save(pos)

        self.events.append(Event(
            id=f"evt_{uuid.uuid4().hex[:8]}",
            position_id=position_id,
            type="order_filled",
            ts=self.clock.now(),
            payload={"order_id": order.id, "trade_id": trade.id, "price": trade.price},
        ))

        return order