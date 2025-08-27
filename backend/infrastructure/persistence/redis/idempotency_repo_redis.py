# =========================
# backend/infrastructure/persistence/redis/idempotency_repo_redis.py
# =========================
from typing import Optional

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore

from domain.ports.idempotency_repo import IdempotencyRepo


class RedisIdempotencyRepo(IdempotencyRepo):
    """Redis-backed idempotency with SETNX semantics and TTL.

    Keys used (namespaced):
      - {ns}:idemp:{key}:sig   -> signature hash
      - {ns}:idemp:{key}:order -> order_id
    """

    def __init__(self, client: "redis.Redis", namespace: str = "vb", ttl_seconds: int = 48 * 3600) -> None:
        if redis is None:  # pragma: no cover
            raise RuntimeError("redis not installed. Install with extras: pip install '.[redis]'")
        self.client = client
        self.ns = namespace
        self.ttl = ttl_seconds

    def _k_sig(self, key: str) -> str:
        return f"{self.ns}:idemp:{key}:sig"

    def _k_order(self, key: str) -> str:
        return f"{self.ns}:idemp:{key}:order"

    def get_order_id(self, key: str) -> Optional[str]:
        val = self.client.get(self._k_order(key))
        return val.decode() if val else None

    def reserve(self, key: str, signature_hash: str) -> Optional[str]:
        # Try to set the signature if not exists (NX). If set -> new reservation.
        if self.client.set(self._k_sig(key), signature_hash, nx=True, ex=self.ttl):
            return None
        # Already reserved: compare stored signature
        existing = self.client.get(self._k_sig(key))
        existing_sig = existing.decode() if existing else None
        if existing_sig == signature_hash:
            # Replay path: return order_id if already recorded (maybe None pre-put)
            return self.get_order_id(key)
        return f"conflict:{existing_sig}"

    def put(self, key: str, order_id: str, signature_hash: str) -> None:
        pipe = self.client.pipeline()
        pipe.set(self._k_sig(key), signature_hash, ex=self.ttl)
        pipe.set(self._k_order(key), order_id, ex=self.ttl)
        pipe.execute()

    def clear(self) -> None:  # best-effort cleanup for tests
        cursor = 0
        pattern = f"{self.ns}:idemp:*"
        while True:
            cursor, keys = self.client.scan(cursor=cursor, match=pattern, count=500)
            if keys:
                self.client.delete(*keys)
            if cursor == 0:
                break

