# =========================
# backend/infrastructure/persistence/redis/idempotency_repo_redis.py
# =========================
from typing import Optional, Any, cast

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import redis  # only for type checking
else:
    redis = None  # at runtime when not installed


from domain.ports.idempotency_repo import IdempotencyRepo


class RedisIdempotencyRepo(IdempotencyRepo):
    """Redis-backed idempotency with SETNX semantics and TTL.

    Keys used (namespaced):
      - {ns}:idemp:{key}:sig   -> signature hash
      - {ns}:idemp:{key}:order -> order_id
    """

    # Type the client as Any so we can support both sync and asyncio Redis without
    # dragging their complex generic types into our code. We cast return values below.
    def __init__(self, client: Any, namespace: str = "vb", ttl_seconds: int = 48 * 3600) -> None:
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
        b = cast(Optional[bytes], val)
        return b.decode() if b is not None else None

    def reserve(self, key: str, signature_hash: str) -> Optional[str]:
        if self.client.set(self._k_sig(key), signature_hash, nx=True, ex=self.ttl):
            return None  # NEW
        existing = self.client.get(self._k_sig(key))
        existing_b = cast(Optional[bytes], existing)
        existing_sig = existing_b.decode() if existing_b is not None else None
        if existing_sig == signature_hash:
            oid = self.client.get(self._k_order(key))
            return oid.decode() if oid else "in_progress"
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
            scan_res = self.client.scan(cursor=cursor, match=pattern, count=500)
            cursor, keys = cast(tuple[int, list[bytes]], scan_res)
            if keys:
                self.client.delete(*keys)
            if cursor == 0:
                break
