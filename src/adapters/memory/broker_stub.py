from datetime import datetime
from app.domain.models import Trade
import uuid

class ImmediateBroker:
    def execute(self, order, price: float) -> Trade:
        commission = round(max(0.01, 0.001 * order.qty * price), 2)  # simple 0.1% fee, min 0.01
        return Trade(
            id=f"trd_{uuid.uuid4().hex[:8]}",
            order_id=order.id,
            position_id=order.position_id,
            side=order.side,
            qty=order.qty,
            price=price,
            commission=commission,
            executed_at=datetime.utcnow(),
        )