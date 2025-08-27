# =========================
# backend/infrastructure/persistence/memory/idempotency_repo_mem.py
# =========================
from typing import Dict, Optional

from domain.ports.idempotency_repo import IdempotencyRepo


class InMemoryIdempotencyRepo(IdempotencyRepo):
    """Simple key → (signature_hash, order_id) store.
    reserve() returns:
      - None if reserved successfully for this signature (new)
      - order_id if this key already exists for same signature (replay)
      - "conflict:<sig>" if exists but for different signature
    """

    def __init__(self) -> None:
        self._sig_by_key: Dict[str, str] = {}
        self._order_by_key: Dict[str, str] = {}

    def get_order_id(self, key: str) -> Optional[str]:
        return self._order_by_key.get(key)

    def reserve(self, key: str, signature_hash: str) -> Optional[str]:
        if key in self._sig_by_key:
            existing_sig = self._sig_by_key[key]
            if existing_sig == signature_hash:
                return self._order_by_key.get(key)  # replay path (may be None before put)
            return f"conflict:{existing_sig}"
        # reserve
        self._sig_by_key[key] = signature_hash
        return None

    def put(self, key: str, order_id: str, signature_hash: str) -> None:
        self._sig_by_key[key] = signature_hash
        self._order_by_key[key] = order_id

    def clear(self) -> None:
        self._sig_by_key.clear()
        self._order_by_key.clear()
