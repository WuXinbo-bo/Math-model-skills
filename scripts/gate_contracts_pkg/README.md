# P2-2: Gate Contracts Package Refactoring Plan

## Current State (v4.0)

- **Original file**: `scripts/gate_contracts.py` (3160 lines)
- **Package structure**: `scripts/gate_contracts_pkg/` (lightweight wrapper)

## Why Lightweight Wrapper?

The original `gate_contracts.py` is a 3160-line monolithic file with:
- 32 gate contract definitions
- 28 gate checker functions
- Complex interdependencies between functions
- Shared helper functions (e.g., `get_mode_thresholds`)

Full modularization would require:
1. Extracting all 28 functions to separate modules
2. Resolving circular dependencies
3. Updating all import statements across the codebase
4. Extensive testing to ensure no regressions

**Risk**: High probability of breaking existing functionality during full refactoring.

## Recommended Migration Path

### Phase 1 (Done): Create Package Structure
- [x] Create `gate_contracts_pkg/` directory
- [x] Create `__init__.py` as compatibility layer
- [x] Import all public APIs from original file

### Phase 2 (Future): Gradual Modularization
When time permits, split into submodules:

```
gate_contracts_pkg/
├── __init__.py          # Re-export all APIs
├── definitions.py       # GATE_CONTRACTS dict (32 contracts)
├── thresholds.py        # MODE_THRESHOLDS, SCORING_WEIGHT_THRESHOLDS
├── propagation.py       # propagation_check, print_propagation_report
├── audit.py             # run_g6_audit_enhanced, print_g6_enhanced_report
├── verdict.py           # auto_verdict routing
└── checkers/
    ├── __init__.py
    ├── s0_s1.py         # gate_g0, gate_g1_problem_parsed
    ├── s2_s3.py         # gate_data_quality, gate_metric_guardian, gate_g2_poc, etc.
    ├── s4_s5.py         # gate_race_completed, gate_evolution_converged, etc.
    ├── s6_s7.py         # gate_g4_frozen_staleness, gate_per_subquestion, etc.
    ├── s8.py            # gate_g5_paper_quality, gate_abstract_quality, etc.
    └── s9_s10.py        # gate_g5_5_adversarial, gate_publication_ready, etc.
```

### Phase 3 (Future): Update Imports
- Update `stage_executor.py` to use `from gate_contracts_pkg import ...`
- Update `auto_orchestrator.py` similarly
- Update any other scripts that import from `gate_contracts`
- Deprecate original `gate_contracts.py`

## Current Usage

All existing code continues to use:
```python
from gate_contracts import auto_verdict, gate_g0, ...
```

The package provides a clean migration path without breaking existing code.

## Benefits of Current Approach

1. **Zero risk**: No changes to existing functionality
2. **Clean API**: Package structure ready for future refactoring
3. **Backward compatible**: All imports still work
4. **Documented**: Clear migration path for future developers

## When to Do Full Refactoring?

Consider full modularization when:
- You have dedicated testing time (2-3 days)
- You're adding new gate checkers (easier to add to submodules)
- You're updating the CI/CD pipeline
- Multiple developers are working on gate contracts simultaneously

For now, the lightweight wrapper provides the best balance of safety and future-proofing.
