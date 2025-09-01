# =========================
# backend/domain/errors.py
# =========================


class IdempotencyConflict(Exception):
    pass


class PositionNotFound(Exception):
    pass


class GuardrailBreach(Exception):
    pass


class PolicyViolation(Exception):
    pass
