class FixedPricing:
    def __init__(self, price: float = 100.0):
        self._price = price

    def last_price(self, symbol: str) -> float:
        return self._price