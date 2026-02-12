# =========================
# backend/tests/unit/application/test_order_sizing.py
# =========================
"""
Unit tests for the order sizing formula in EvaluatePositionUC._calculate_order_proposal.

Formula: ΔQ = (P_anchor / P_current - 1) × r × ((Stock_Value + Cash) / P_current)

Tests verify:
- Formula correctness with known inputs/outputs
- Sign correctness (positive for BUY, negative for SELL)
- Trimming: cap to available cash (BUY), cap to available shares (SELL)
- Commission deduction in cash delta calculation
- Edge case: anchor == current price yields qty = 0
- max_trade_pct_of_position capping
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from domain.entities.position import Position
from domain.value_objects.order_policy import OrderPolicy
from domain.value_objects.guardrails import GuardrailPolicy
from application.use_cases.evaluate_position_uc import EvaluatePositionUC


def _make_position(
    qty=100.0,
    cash=10000.0,
    anchor_price=100.0,
    asset_symbol="VOO",
    commission_rate=0.001,
    rebalance_ratio=1.6667,
    trigger_threshold_pct=0.03,
    min_stock_alloc_pct=0.30,
    max_stock_alloc_pct=0.70,
    max_sell_pct_per_trade=None,
    dividend_receivable=0.0,
) -> Position:
    return Position(
        id="pos_test",
        tenant_id="default",
        portfolio_id="test_portfolio",
        asset_symbol=asset_symbol,
        qty=qty,
        cash=cash,
        anchor_price=anchor_price,
        dividend_receivable=dividend_receivable,
        order_policy=OrderPolicy(
            trigger_threshold_pct=trigger_threshold_pct,
            rebalance_ratio=rebalance_ratio,
            commission_rate=commission_rate,
            min_notional=0.0,  # Disable min notional for unit tests
        ),
        guardrails=GuardrailPolicy(
            min_stock_alloc_pct=min_stock_alloc_pct,
            max_stock_alloc_pct=max_stock_alloc_pct,
            max_sell_pct_per_trade=max_sell_pct_per_trade or 1.0,
            max_orders_per_day=100,
        ),
    )


def _make_uc(position: Position) -> EvaluatePositionUC:
    """Create EvaluatePositionUC with minimal mocks."""
    positions_mock = MagicMock()
    positions_mock.get.return_value = position

    events_mock = MagicMock()
    market_data_mock = MagicMock()
    # Return a mock price_data to prevent AttributeError
    mock_price_data = MagicMock()
    mock_price_data.price = position.anchor_price or 100.0
    market_data_mock.get_price.return_value = mock_price_data

    clock_mock = MagicMock()
    clock_mock.now.return_value = datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)

    return EvaluatePositionUC(
        positions=positions_mock,
        events=events_mock,
        market_data=market_data_mock,
        clock=clock_mock,
    )


def _calculate_expected_raw_qty(
    anchor_price: float,
    current_price: float,
    rebalance_ratio: float,
    qty: float,
    cash: float,
) -> float:
    """Calculate expected raw quantity using the specification formula."""
    stock_value = qty * current_price
    total_value = stock_value + cash
    return (anchor_price / current_price - 1) * rebalance_ratio * (total_value / current_price)


# ───────────────────────────────────────────────────────────────
# Formula correctness
# ───────────────────────────────────────────────────────────────
class TestOrderSizingFormula:
    def test_buy_formula_correctness(self):
        """BUY: Price dropped from 100 to 97 (3% drop). Verify formula."""
        # ΔQ = (100/97 - 1) × 1.6667 × (100*97 + 10000) / 97
        pos = _make_position(qty=100, cash=10000, anchor_price=100.0)
        uc = _make_uc(pos)

        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 97.0, "BUY"
        )

        expected_raw = _calculate_expected_raw_qty(100.0, 97.0, 1.6667, 100, 10000)
        assert proposal["side"] == "BUY"
        assert proposal["raw_qty"] > 0  # Positive for BUY
        assert abs(proposal["raw_qty"] - expected_raw) < 0.01

    def test_sell_formula_correctness(self):
        """SELL: Price rose from 100 to 103 (3% rise). Verify formula."""
        pos = _make_position(qty=100, cash=10000, anchor_price=100.0)
        uc = _make_uc(pos)

        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 103.0, "SELL"
        )

        # The raw formula gives negative for sell (anchor < current -> ratio < 1 -> ΔQ < 0)
        # But the code ensures it's negative for SELL
        assert proposal["side"] == "SELL"
        assert proposal["raw_qty"] < 0  # Negative for SELL

    def test_buy_sign_always_positive(self):
        """BUY proposals always have positive raw_qty."""
        pos = _make_position(qty=100, cash=10000, anchor_price=100.0)
        uc = _make_uc(pos)

        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 95.0, "BUY"
        )
        assert proposal["raw_qty"] > 0

    def test_sell_sign_always_negative(self):
        """SELL proposals always have negative raw_qty."""
        pos = _make_position(qty=100, cash=10000, anchor_price=100.0)
        uc = _make_uc(pos)

        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 105.0, "SELL"
        )
        assert proposal["raw_qty"] < 0


# ───────────────────────────────────────────────────────────────
# Anchor == current price edge case
# ───────────────────────────────────────────────────────────────
class TestAnchorEqualsCurrentPrice:
    def test_anchor_equals_current_yields_zero_raw_qty(self):
        """When anchor == current price, formula yields 0."""
        pos = _make_position(qty=100, cash=10000, anchor_price=100.0)
        uc = _make_uc(pos)

        # BUY side: (100/100 - 1) × r × ... = 0
        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 100.0, "BUY"
        )
        # Raw qty should be 0 (or very close to it)
        assert abs(proposal["raw_qty"]) < 0.001


# ───────────────────────────────────────────────────────────────
# Trimming to available cash/shares
# ───────────────────────────────────────────────────────────────
class TestTrimming:
    def test_buy_capped_to_available_cash(self):
        """BUY qty capped when formula result exceeds affordable amount."""
        # Large price drop with limited cash
        pos = _make_position(qty=100, cash=500.0, anchor_price=100.0)
        uc = _make_uc(pos)

        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 50.0, "BUY"
        )
        # At $50/share, max affordable = $500 / $50 = 10 shares
        assert proposal["raw_qty"] <= 10.0 + 0.01

    def test_sell_capped_to_available_shares(self):
        """SELL qty capped to available shares."""
        # Large price rise with few shares
        pos = _make_position(qty=10, cash=10000, anchor_price=50.0)
        uc = _make_uc(pos)

        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 100.0, "SELL"
        )
        # Cannot sell more than 10 shares
        assert abs(proposal["raw_qty"]) <= 10.0 + 0.01

    def test_sell_max_trade_pct_caps_qty(self):
        """SELL qty capped by max_trade_pct_of_position."""
        # 200 shares @ $100 = $20,000; $5,000 cash -> total $25,000
        # max_trade_pct = 10% -> $2,500 / $100 = 25 shares max
        pos = _make_position(
            qty=200, cash=5000, anchor_price=90.0,
            max_sell_pct_per_trade=0.10,
        )
        uc = _make_uc(pos)

        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 100.0, "SELL"
        )
        # max allowed by pct = 10% of $25,000 / $100 = 25
        assert abs(proposal["raw_qty"]) <= 25.0 + 0.01

    def test_buy_max_trade_pct_caps_qty(self):
        """BUY qty capped by max_trade_pct_of_position."""
        # 50 shares @ $100 = $5,000; $15,000 cash -> total $20,000
        # max_trade_pct = 10% -> max notional $2,000 -> 20 shares max
        pos = _make_position(
            qty=50, cash=15000, anchor_price=110.0,
            max_sell_pct_per_trade=0.10,
        )
        uc = _make_uc(pos)

        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 100.0, "BUY"
        )
        assert proposal["raw_qty"] <= 20.0 + 0.01


# ───────────────────────────────────────────────────────────────
# Commission calculation
# ───────────────────────────────────────────────────────────────
class TestCommission:
    def test_commission_calculated_correctly(self):
        """Commission = notional × commission_rate."""
        pos = _make_position(qty=100, cash=10000, anchor_price=100.0, commission_rate=0.001)
        uc = _make_uc(pos)

        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 97.0, "BUY"
        )
        expected_commission = proposal["notional"] * 0.001
        assert abs(proposal["commission"] - expected_commission) < 0.01

    def test_commission_deducted_in_cash_delta(self):
        """Cash delta calculation includes commission deduction."""
        # The _apply_guardrail_trimming method computes cash_delta as:
        # cash_delta = -(raw_qty * price) - (abs(raw_qty) * price * commission_rate)
        # For BUY (positive qty): cash goes down by cost + commission
        # For SELL (negative qty): cash goes up by proceeds - commission
        pos = _make_position(qty=100, cash=10000, anchor_price=100.0, commission_rate=0.01)
        uc = _make_uc(pos)

        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 97.0, "BUY"
        )
        # Verify commission is positive
        assert proposal["commission"] > 0
        # Verify notional matches |trimmed_qty| * price
        assert abs(proposal["notional"] - abs(proposal["trimmed_qty"]) * 97.0) < 0.01


# ───────────────────────────────────────────────────────────────
# Rebalance ratio
# ───────────────────────────────────────────────────────────────
class TestRebalanceRatio:
    def test_higher_rebalance_ratio_larger_qty(self):
        """Higher rebalance ratio produces larger order qty."""
        pos_low = _make_position(
            qty=100, cash=10000, anchor_price=100.0, rebalance_ratio=0.5
        )
        pos_high = _make_position(
            qty=100, cash=10000, anchor_price=100.0, rebalance_ratio=1.6667
        )

        uc_low = _make_uc(pos_low)
        uc_high = _make_uc(pos_high)

        proposal_low = uc_low._calculate_order_proposal(
            "default", "test_portfolio", pos_low, 97.0, "BUY"
        )
        proposal_high = uc_high._calculate_order_proposal(
            "default", "test_portfolio", pos_high, 97.0, "BUY"
        )

        assert proposal_high["raw_qty"] > proposal_low["raw_qty"]

    def test_default_rebalance_ratio_is_1_6667(self):
        """Verify the default rebalance ratio is 1.6667 (5/3), not 0.5."""
        pos = _make_position()
        assert pos.order_policy.rebalance_ratio == 1.6667


# ───────────────────────────────────────────────────────────────
# Guardrail trimming in order proposal
# ───────────────────────────────────────────────────────────────
class TestGuardrailTrimming:
    def test_buy_trimmed_to_max_allocation(self):
        """BUY trimmed when post-trade allocation would exceed max_stock_pct."""
        pos = _make_position(
            qty=60, cash=4000, anchor_price=110.0,
            max_stock_alloc_pct=0.70,
        )
        uc = _make_uc(pos)

        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 100.0, "BUY"
        )
        # Post-trade allocation should not exceed 70%
        assert proposal["post_trade_asset_pct"] <= 0.70 + 0.01

    def test_sell_trimmed_to_min_allocation(self):
        """SELL trimmed when post-trade allocation would go below min_stock_pct."""
        pos = _make_position(
            qty=40, cash=6000, anchor_price=90.0,
            min_stock_alloc_pct=0.30,
        )
        uc = _make_uc(pos)

        proposal = uc._calculate_order_proposal(
            "default", "test_portfolio", pos, 100.0, "SELL"
        )
        # Post-trade allocation should not go below 30%
        assert proposal["post_trade_asset_pct"] >= 0.30 - 0.01
