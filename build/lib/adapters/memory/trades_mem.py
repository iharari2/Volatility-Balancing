from app.domain.models import Trade

class InMemoryTradeRepo:
    def __init__(self):
        self._list = []

    def save(self, trade: Trade) -> None:
        self._list.append(trade)