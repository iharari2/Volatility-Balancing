from infrastructure.persistence.memory.idempotency_repo_mem import InMemoryIdempotencyRepo

def test_reserve_new_then_put_then_replay():
    repo = InMemoryIdempotencyRepo()
    key = "K1"
    sig = "S1"
    # first reserve -> new (None)
    assert repo.reserve(key, sig) is None
    # put order id
    repo.put(key, "ord_abc123", sig)
    # replay with same signature returns the order_id
    assert repo.reserve(key, sig) == "ord_abc123"

def test_reserve_conflict_when_signature_differs():
    repo = InMemoryIdempotencyRepo()
    key = "K2"
    # reserve with one sig
    assert repo.reserve(key, "SIG_A") is None
    # reserve with different sig -> conflict:<existing>
    out = repo.reserve(key, "SIG_B")
    assert isinstance(out, str) and out.startswith("conflict:")

def test_clear_resets_state():
    repo = InMemoryIdempotencyRepo()
    key = "K3"
    sig = "S3"
    assert repo.reserve(key, sig) is None
    repo.put(key, "ord_x", sig)
    assert repo.reserve(key, sig) == "ord_x"
    repo.clear()
    # After clear we can reserve again as new
    assert repo.reserve(key, sig) is None
