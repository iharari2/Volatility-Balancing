# Golden Tests Implementation Status

## Overview

This document tracks the implementation of golden test scenarios from `backend/docs/testing_scenarios.md`.

## Test Files Created

### ✅ Integration Tests

- **File**: `backend/tests/integration/test_golden_scenarios.py`
- **Scenarios**: A, B, C, D
- **Status**: Implemented
- **Coverage**:
  - Scenario A: Domain level + Orchestrator level
  - Scenario B: Domain level + Orchestrator level (full buy/sell cycle)
  - Scenario C: Guardrail blocking test
  - Scenario D: Portfolio creation and positions

### ✅ Domain Service Tests

- **File**: `backend/tests/unit/domain/services/test_price_trigger_golden.py`
- **Scenarios**: A, B (domain level)
- **Status**: Implemented
- **Coverage**:
  - Scenario A: All prices within trigger band
  - Scenario B: Buy trigger, no trigger, sell trigger
  - Edge cases: No anchor, zero anchor, exact thresholds

## Pending Implementation

### ⏳ Scenario E - Simulation vs Trade Consistency

- **Status**: Pending
- **Reason**: Requires full simulation orchestrator integration
- **File**: To be created when simulation infrastructure is ready

### ⏳ GuardrailEvaluator Golden Tests

- **Status**: Pending
- **File**: `backend/tests/unit/domain/services/test_guardrail_evaluator_golden.py`
- **Scenarios**: B, C (domain level)
- **Notes**: Should test guardrail evaluation logic in isolation

## Test Execution

Run all golden tests:

```bash
pytest backend/tests/integration/test_golden_scenarios.py -v
pytest backend/tests/unit/domain/services/test_price_trigger_golden.py -v
```

Run specific scenario:

```bash
pytest backend/tests/integration/test_golden_scenarios.py::TestScenarioA_NoTradeInsideTriggerBand -v
```

## Next Steps

1. ✅ Implement Scenario A tests (domain + integration)
2. ✅ Implement Scenario B tests (domain + integration)
3. ✅ Implement Scenario C test (integration)
4. ✅ Implement Scenario D test (integration)
5. ⏳ Implement GuardrailEvaluator domain tests
6. ⏳ Implement Scenario E (simulation consistency)
7. ⏳ Add more edge cases and boundary conditions

## Notes

- All tests use the new architecture with config providers
- Tests verify both domain logic (pure) and orchestrator flows (end-to-end)
- Commission tracking is verified in Scenario B and D
- Position state invariants are checked in all scenarios


















