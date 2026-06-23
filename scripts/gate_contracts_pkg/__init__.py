#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate Contracts Package (P2-2)
==============================
Lightweight package structure for future refactoring.

Current state: Original gate_contracts.py (3160 lines) remains as the main file.
This package provides a clean API layer for future modularization.

Migration path:
1. Phase 1 (Done): Create package structure with __init__.py
2. Phase 2 (Future): Gradually move functions to submodules
3. Phase 3 (Future): Update all imports to use package

For now, all imports come from the original gate_contracts.py file.
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import the original gate_contracts
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import everything from the original file
from gate_contracts import (
    GATE_CONTRACTS,
    print_gate_contracts,
    MODE_THRESHOLDS,
    SCORING_WEIGHT_THRESHOLDS,
    get_weight_thresholds,
    get_mode_thresholds,
    auto_verdict,
    propagation_check,
    print_propagation_report,
    run_g6_audit_enhanced,
    print_g6_enhanced_report,
    # Gate checkers
    gate_g0,
    gate_g1_problem_parsed,
    gate_data_quality,
    gate_metric_guardian,
    gate_g2_poc,
    gate_g3_baseline,
    gate_multi_proposal,
    gate_adversarial_round,
    gate_model_selection_v2,
    gate_prototype_validated,
    gate_model_selection,
    gate_innovation_assessment,
    gate_race_completed,
    gate_evolution_converged,
    gate_g5_s8_content_ready,
    gate_g4_frozen_staleness,
    gate_per_subquestion,
    gate_evidence_chain_quality,
    gate_unified_kernel,
    gate_g5_paper_quality,
    gate_abstract_quality,
    gate_paper_structure,
    gate_figure_narrative,
    gate_parallel_merge,
    gate_paper_evaluation_quality,
    gate_g5_5_adversarial,
    gate_publication_ready,
    gate_g6_appendix_complete,
)

__version__ = "3.0.0"
__all__ = [
    "GATE_CONTRACTS",
    "print_gate_contracts",
    "MODE_THRESHOLDS",
    "SCORING_WEIGHT_THRESHOLDS",
    "get_weight_thresholds",
    "get_mode_thresholds",
    "auto_verdict",
    "propagation_check",
    "print_propagation_report",
    "run_g6_audit_enhanced",
    "print_g6_enhanced_report",
    # Gate checkers
    "gate_g0",
    "gate_g1_problem_parsed",
    "gate_data_quality",
    "gate_metric_guardian",
    "gate_g2_poc",
    "gate_g3_baseline",
    "gate_multi_proposal",
    "gate_adversarial_round",
    "gate_model_selection_v2",
    "gate_prototype_validated",
    "gate_model_selection",
    "gate_innovation_assessment",
    "gate_race_completed",
    "gate_evolution_converged",
    "gate_g5_s8_content_ready",
    "gate_g4_frozen_staleness",
    "gate_per_subquestion",
    "gate_evidence_chain_quality",
    "gate_unified_kernel",
    "gate_g5_paper_quality",
    "gate_abstract_quality",
    "gate_paper_structure",
    "gate_figure_narrative",
    "gate_parallel_merge",
    "gate_paper_evaluation_quality",
    "gate_g5_5_adversarial",
    "gate_publication_ready",
    "gate_g6_appendix_complete",
]
