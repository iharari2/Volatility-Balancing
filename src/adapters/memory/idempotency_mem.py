import threading
from typing import Dict, Optional

class InMemoryIdempotency:
    def __init__(self):
        self._reserved: set[str] = set()
        self._map: Dict[str, str] = {}
        self._lock = threading.Lock()

    def reserve(self, key: str, ttl_seconds: int) -> bool:
        # ttl ignored in memory; lock for per-process atomicity
        with self._lock:
            if key in self._reserved:
                return False
            self._reserved.add(key)
            return True

    def set_mapping(self, key: str, order_id: str) -> None:
        with self._lock:
            self._map[key] = order_id

    def get_mapping(self, key: str) -> Optional[str]:
        return self._map.get(key)