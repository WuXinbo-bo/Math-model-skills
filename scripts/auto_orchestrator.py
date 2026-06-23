#!/usr/bin/env python3
"""
Auto Orchestrator (v1.1) — Auto Mode for Meta-model-skills-max
===============================================================
Drives the S0→S10 pipeline fully automatically, replacing human decision points
with rule-based auto-decisions and safety circuit breakers.

Architecture:
  - This is a PURE TOOLING module (no LLM calls).
  - All reasoning/analysis/writing is still done by the main Codex agent.
  - This script handles: auto-advance, auto-rework, gate verdict, pause, decision log.
  - The main agent calls this script at each decision point to decide: advance/rework/pause.

Commands:
  auto-start       Initialize auto mode for current pipeline
  auto-next        Determine next action: advance/rework/pause
  auto-decide      Make an auto-decision for a specific decision point
  auto-gate-verdict Run gate check and return auto-verdict
  auto-pause       Pause auto mode (user intervention requested)
  auto-resume      Resume auto mode after human intervention
  auto-log         Show decision log
  auto-status      Show auto mode status and safety metrics

Safety Rules:
  1. Gate fail → auto rework (up to max_reworks per stage)
  2. Consecutive reworks exceed threshold → PAUSE, request human
  3. All decisions logged to decision_log.json
  4. User can pause anytime: python main.py auto-pause
  5. Auto mode requires one-time explicit activation
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from workspace_utils import resolve_workspace, resolve_skill_root
SKILL_ROOT = resolve_skill_root()
WORKSPACE = resolve_workspace()
STATE_DIR = WORKSPACE / "state"
PIPELINE = STATE_DIR / "pipeline.json"
AUTO_STATE = STATE_DIR / "auto_state.json"
DECISION_LOG = STATE_DIR / "decision_log.json"


# ═══════════════════════════════════════════════════════════════
# Auto Mode Configuration
# ═══════════════════════════════════════════════════════════════

# Default max reworks per depth mode
REWORK_LIMITS = {
    "FAST": 2,
    "STANDARD": 3,
    "CHAMPIONSHIP": 5,
}

# Safety: consecutive reworks across stages before hard pause
CONSECUTIVE_REWORK_THRESHOLD = 5

# Auto-decision rules per decision point
AUTO_DECISIONS = {
    "S0_competition_type": {
        "rule": "auto_detect_from_keywords",
        "description": "从题目文本自动识别竞赛类型",
    },
    "S0_subquestion_count": {
        "rule": "auto_count_from_text",
        "description": "从题目文本自动统计子问题数量",
    },
    "S3_model_selection": {
        "rule": "auto_score_matrix",
        "description": "评分矩阵自动打分，选最高分方案",
    },
    "S3_model_selection_strategy": {
        "rule": "default_precision_first",
        "description": "默认精度优先（推荐）",
    },
    "S5_code_execution": {
        "rule": "auto_sandbox_execute",
        "description": "自动执行代码 + 检查输出合理性",
    },
    "S8_paper_route": {
        "rule": "default_fresh_markdown",
        "description": "默认从零撰写 Markdown → DOCX",
    },
    "S9_revision_direction": {
        "rule": "auto_fix_all_p0_p1",
        "description": "自动修复所有 P0/P1 问题",
    },
    "stage_transition": {
        "rule": "gate_pass_advance",
        "description": "门禁通过 → 自动 advance；不通过 → 自动 rework",
    },
}

# Depth-mode-specific overrides
DEPTH_OVERRIDES = {
    "FAST": {
        "skip_stages": ["S4_experiment_race"],
        "S6_sensitivity_range": ["10"],
        "S9_max_iterations": 1,
        "abstract_refinement_rounds": 1,
    },
    "STANDARD": {
        "skip_stages": [],
        "S6_sensitivity_range": ["10", "20", "50"],
        "S9_max_iterations": 1,
        "abstract_refinement_rounds": 1,
    },
    "CHAMPIONSHIP": {
        "skip_stages": [],
        "S6_sensitivity_range": ["10", "20", "50"],
        "S9_max_iterations": 3,
        "abstract_refinement_rounds": 3,
        "extra_consistency_check": True,
    },
}


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ═══════════════════════════════════════════════════════════════
# State Management
# ═══════════════════════════════════════════════════════════════

def load_pipeline():
    if not PIPELINE.exists():
        sys.exit("[auto] Pipeline not initialized. Run 'python main.py init' first.")
    with PIPELINE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_pipeline(data):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with PIPELINE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_auto_state():
    if not AUTO_STATE.exists():
        return _default_auto_state()
    with AUTO_STATE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_auto_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with AUTO_STATE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _default_auto_state():
    return {
        "mode": "auto",
        "status": "idle",
        "activated_at": None,
        "paused_at": None,
        "depth_mode": "STANDARD",
        "consecutive_reworks": 0,
        "total_advances": 0,
        "total_reworks": 0,
        "total_pauses": 0,
        "stage_reworks": {},
        "last_decision": None,
        "activation_confirmed": False,
    }


def load_decision_log():
    if not DECISION_LOG.exists():
        return {"decisions": []}
    with DECISION_LOG.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_decision_log(log):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with DECISION_LOG.open("w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def log_decision(stage, decision_type, details, auto_state):
    """Append a decision to the log."""
    log = load_decision_log()
    entry = {
        "timestamp": now(),
        "stage": stage,
        "decision_type": decision_type,
        "details": details,
        "consecutive_reworks": auto_state.get("consecutive_reworks", 0),
    }
    log["decisions"].append(entry)
    # Keep last 200 entries
    if len(log["decisions"]) > 200:
        log["decisions"] = log["decisions"][-200:]
    save_decision_log(log)


# ═══════════════════════════════════════════════════════════════
# Stage Order (from workflow.yaml — imported at runtime)
# ═══════════════════════════════════════════════════════════════

def _get_stage_order():
    """Get stage order from pipeline_manager's workflow.yaml parsing."""
    try:
        from pipeline_manager import STAGE_ORDER
        return STAGE_ORDER
    except ImportError:
        # Fallback hardcoded order
        return [
            "S0_input_registration",
            "S1_problem_analysis",
            "S2_data_governance",
            "S3_model_selection",
            "S4_experiment_race",
            "S5_modeling_and_solve",
            "S5.5_model_evolution",
            "S6_verification",
            "S7_evidence_chain",
            "S8_paper_drafting",
            "S9_adversarial_review",
            "S10_final_build",
        ]


def _get_current_stage(data):
    """Find the first non-approved, non-skipped stage."""
    stage_order = _get_stage_order()
    parallel_groups = data.get("parallel_groups", {})
    sub_stage_ids = set()
    for group in parallel_groups.values():
        sub_stage_ids.update(group.get("sub_stages", []))

    for stage in stage_order:
        if stage in sub_stage_ids:
            continue
        s = data["stages"].get(stage, {})
        status = s.get("status", "not_started")
        if status in ("not_started", "rework", "in_progress"):
            return stage
    return None  # All done


def _get_next_stage(current_stage):
    """Get the next stage after current."""
    stage_order = _get_stage_order()
    try:
        idx = stage_order.index(current_stage)
        if idx + 1 < len(stage_order):
            return stage_order[idx + 1]
    except ValueError:
        pass
    return None


# ═══════════════════════════════════════════════════════════════
# Gate Auto-Verdict
# ═══════════════════════════════════════════════════════════════

def auto_gate_verdict(stage, depth_mode="STANDARD"):
    """Check gates for a stage and return auto-verdict.

    Delegates to gate_contracts.auto_verdict() for unified gate checking.

    Returns: dict with {
        "passed": bool,
        "gates": list of {gate_id, passed, message},
        "action": "advance" | "rework" | "pause",
        "fix_instructions": list of strings (if rework),
    }
    """
    try:
        from pipeline_manager import STAGE_GATES
    except ImportError:
        return {
            "passed": False, "gates": [], "action": "pause",
            "fix_instructions": ["BLOCKED: pipeline_manager not available — cannot determine stage gates"],
        }

    gates = STAGE_GATES.get(stage, [])
    if not gates:
        # No gates defined for this stage → auto-pass
        return {"passed": True, "gates": [], "action": "advance",
                "fix_instructions": []}

    gate_results = []
    all_passed = True
    fix_instructions = []

    for gate_id in gates:
        passed, message = _check_gate_by_id(gate_id, depth_mode)
        gate_results.append({
            "gate_id": gate_id,
            "passed": passed,
            "message": message,
        })
        if not passed:
            all_passed = False
            fix_instructions.append(f"[{gate_id}] {message}")

    if all_passed:
        return {
            "passed": True,
            "gates": gate_results,
            "action": "advance",
            "fix_instructions": [],
        }
    else:
        return {
            "passed": False,
            "gates": gate_results,
            "action": "rework",
            "fix_instructions": fix_instructions,
        }


def _check_gate_by_id(gate_id, depth_mode="STANDARD"):
    """Route gate check to gate_contracts.auto_verdict() — single source of truth."""
    try:
        from gate_contracts import auto_verdict as gc_auto_verdict
        passed, msg, _fix = gc_auto_verdict(gate_id, mode=depth_mode.lower())
        return passed, msg
    except ImportError:
        # CRITICAL: never auto-pass when gate_contracts is unavailable
        return False, (
            f"BLOCKED: gate_contracts not available — "
            f"cannot auto-pass gate [{gate_id}]. "
            f"Fix: ensure scripts/gate_contracts.py is importable."
        )
    except Exception as e:
        return False, f"Gate check error [{gate_id}]: {e}"


# ═══════════════════════════════════════════════════════════════
# Auto-Decisions (for specific decision points)
# ═══════════════════════════════════════════════════════════════

def auto_decide(decision_point, context=None, depth_mode="STANDARD"):
    """Make an auto-decision for a specific decision point.

    Returns: dict with {
        "decision_point": str,
        "chosen": str,
        "reasoning": str,
        "confidence": float (0-1),
    }
    """
    ctx = context or {}

    if decision_point == "S3_model_selection":
        # Auto-score: prefer the agent's recommended option
        return {
            "decision_point": decision_point,
            "chosen": "recommend",
            "reasoning": "Auto mode: use agent's综合评估推荐（评分矩阵最高分）",
            "confidence": 0.85,
        }

    if decision_point == "S8_paper_route":
        return {
            "decision_point": decision_point,
            "chosen": "fresh_markdown",
            "reasoning": "Auto mode: 默认从零撰写 Markdown → 转 DOCX",
            "confidence": 0.9,
        }

    if decision_point == "S9_revision_direction":
        return {
            "decision_point": decision_point,
            "chosen": "fix_all_p0_p1",
            "reasoning": "Auto mode: 自动修复所有 P0/P1 问题",
            "confidence": 0.8,
        }

    if decision_point == "S5_code_execution":
        return {
            "decision_point": decision_point,
            "chosen": "auto_sandbox",
            "reasoning": "Auto mode: 自动执行沙箱 + 检查输出",
            "confidence": 0.9,
        }

    if decision_point == "S0_competition_type":
        # Handled by agent parsing — just confirm auto-detect
        return {
            "decision_point": decision_point,
            "chosen": ctx.get("detected_type", "CUMCM"),
            "reasoning": "Auto mode: 从题目关键词自动识别",
            "confidence": ctx.get("detection_confidence", 0.8),
        }

    if decision_point == "S0_subquestion_count":
        return {
            "decision_point": decision_point,
            "chosen": str(ctx.get("detected_count", 1)),
            "reasoning": "Auto mode: 从题目文本自动统计子问题",
            "confidence": ctx.get("detection_confidence", 0.7),
        }

    # Default: pick the recommended option
    return {
        "decision_point": decision_point,
        "chosen": "auto_default",
        "reasoning": f"Auto mode: 使用默认推荐选项 ({decision_point})",
        "confidence": 0.75,
    }


# ═══════════════════════════════════════════════════════════════
# Safety Circuit Breaker
# ═══════════════════════════════════════════════════════════════

def _check_circuit_breaker(auto_state):
    """Check if safety circuit breaker should activate.

    Returns: (should_pause: bool, reason: str)
    """
    # Check consecutive reworks
    consecutive = auto_state.get("consecutive_reworks", 0)
    if consecutive >= CONSECUTIVE_REWORK_THRESHOLD:
        return True, (
            f"安全熔断：连续 {consecutive} 次 rework（阈值 {CONSECUTIVE_REWORK_THRESHOLD}）。"
            f"请人工介入检查问题。"
        )

    # Check total reworks for current stage
    depth = auto_state.get("depth_mode", "STANDARD").upper()
    max_reworks = REWORK_LIMITS.get(depth, 3)
    current_stage = auto_state.get("current_stage", "")
    stage_reworks = auto_state.get("stage_reworks", {}).get(current_stage, 0)
    if stage_reworks >= max_reworks:
        return True, (
            f"安全熔断：阶段 {current_stage} 已 rework {stage_reworks} 次"
            f"（{depth} 模式上限 {max_reworks}）。请人工介入。"
        )

    return False, ""


# ═══════════════════════════════════════════════════════════════
# CLI Commands
# ═══════════════════════════════════════════════════════════════

def cmd_auto_start(args):
    """Initialize auto mode for current pipeline."""
    data = load_pipeline()
    auto_state = _default_auto_state()
    auto_state["status"] = "active"
    auto_state["activated_at"] = now()
    auto_state["depth_mode"] = (args.depth or data.get("mode", "STANDARD")).upper()
    auto_state["activation_confirmed"] = True

    # Set rework limit based on depth
    max_rw = REWORK_LIMITS.get(auto_state["depth_mode"], 3)
    auto_state["max_reworks_per_stage"] = max_rw

    save_auto_state(auto_state)
    log_decision("_init", "auto_start", {
        "depth_mode": auto_state["depth_mode"],
        "max_reworks_per_stage": max_rw,
    }, auto_state)

    print(f"[auto] Auto mode activated: depth={auto_state['depth_mode']}")
    print(f"[auto] Max reworks per stage: {max_rw}")
    print(f"[auto] Consecutive rework threshold: {CONSECUTIVE_REWORK_THRESHOLD}")
    print(f"[auto] All decisions will be logged to {DECISION_LOG}")


def cmd_auto_next(args):
    """Determine next action: advance/rework/pause.

    This is the core decision command called by the agent at each stage boundary.
    """
    auto_state = load_auto_state()
    if auto_state.get("status") != "active":
        print(json.dumps({"action": "error", "message": "Auto mode not active"}))
        return

    data = load_pipeline()
    current = _get_current_stage(data)
    if current is None:
        # All stages complete
        auto_state["status"] = "complete"
        auto_state["completed_at"] = now()
        save_auto_state(auto_state)
        print(json.dumps({
            "action": "complete",
            "message": "All stages completed in auto mode.",
        }))
        return

    auto_state["current_stage"] = current

    # Check circuit breaker
    should_pause, reason = _check_circuit_breaker(auto_state)
    if should_pause:
        auto_state["status"] = "paused"
        auto_state["paused_at"] = now()
        auto_state["total_pauses"] = auto_state.get("total_pauses", 0) + 1
        save_auto_state(auto_state)
        log_decision(current, "circuit_breaker_pause", {"reason": reason}, auto_state)
        print(json.dumps({
            "action": "pause",
            "stage": current,
            "reason": reason,
        }))
        return

    stage_status = data["stages"].get(current, {}).get("status", "not_started")

    if stage_status == "in_progress":
        # Stage is being worked on — run gate check
        depth = auto_state.get("depth_mode", "STANDARD")
        verdict = auto_gate_verdict(current, depth)

        if verdict["action"] == "advance":
            auto_state["consecutive_reworks"] = 0
            auto_state["total_advances"] = auto_state.get("total_advances", 0) + 1
            auto_state["last_decision"] = {"stage": current, "action": "advance"}
            save_auto_state(auto_state)
            log_decision(current, "auto_advance", {
                "gates_passed": len(verdict["gates"]),
            }, auto_state)
            print(json.dumps({
                "action": "advance",
                "stage": current,
                "gates": verdict["gates"],
            }))
        else:
            # Rework needed
            auto_state["consecutive_reworks"] = auto_state.get("consecutive_reworks", 0) + 1
            sr = auto_state.get("stage_reworks", {})
            sr[current] = sr.get(current, 0) + 1
            auto_state["stage_reworks"] = sr
            auto_state["total_reworks"] = auto_state.get("total_reworks", 0) + 1
            auto_state["last_decision"] = {"stage": current, "action": "rework"}
            save_auto_state(auto_state)
            log_decision(current, "auto_rework", {
                "failed_gates": [g["gate_id"] for g in verdict["gates"] if not g["passed"]],
                "fix_instructions": verdict["fix_instructions"],
                "rework_count": sr[current],
            }, auto_state)
            print(json.dumps({
                "action": "rework",
                "stage": current,
                "fix_instructions": verdict["fix_instructions"],
                "rework_count": sr[current],
            }))

    elif stage_status in ("not_started", "rework"):
        # Ready to start — just report next stage
        auto_state["last_decision"] = {"stage": current, "action": "start"}
        save_auto_state(auto_state)
        log_decision(current, "auto_next_stage", {}, auto_state)
        print(json.dumps({
            "action": "start",
            "stage": current,
            "message": f"Ready to execute {current}",
        }))

    elif stage_status == "pending_review":
        # Shouldn't happen in auto mode, but handle gracefully
        print(json.dumps({
            "action": "error",
            "message": f"Stage {current} is pending_review in auto mode — this shouldn't happen",
        }))

    else:
        print(json.dumps({
            "action": "unknown",
            "stage": current,
            "status": stage_status,
        }))


def cmd_auto_decide(args):
    """Make an auto-decision for a specific decision point."""
    auto_state = load_auto_state()
    depth = auto_state.get("depth_mode", "STANDARD")

    context = {}
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError:
            context = {"raw": args.context}

    decision = auto_decide(args.decision_point, context, depth)
    log_decision(args.decision_point, "auto_decide", decision, auto_state)
    print(json.dumps(decision, ensure_ascii=False, indent=2))


def cmd_auto_gate_verdict(args):
    """Run gate check and return auto-verdict for a stage."""
    auto_state = load_auto_state()
    depth = auto_state.get("depth_mode", "STANDARD")
    verdict = auto_gate_verdict(args.stage, depth)
    print(json.dumps(verdict, ensure_ascii=False, indent=2))


def cmd_auto_pause(_args):
    """Pause auto mode — request human intervention."""
    auto_state = load_auto_state()
    auto_state["status"] = "paused"
    auto_state["paused_at"] = now()
    auto_state["total_pauses"] = auto_state.get("total_pauses", 0) + 1
    save_auto_state(auto_state)
    log_decision(auto_state.get("current_stage", "unknown"), "manual_pause", {}, auto_state)
    print("[auto] Auto mode PAUSED. Run 'auto-resume' after human intervention.")


def cmd_auto_resume(_args):
    """Resume auto mode after human intervention."""
    auto_state = load_auto_state()
    auto_state["status"] = "active"
    auto_state["paused_at"] = None
    auto_state["consecutive_reworks"] = 0  # Reset on human intervention
    save_auto_state(auto_state)
    log_decision(auto_state.get("current_stage", "unknown"), "auto_resume", {}, auto_state)
    print("[auto] Auto mode RESUMED. Consecutive rework counter reset.")


def cmd_auto_log(_args):
    """Show decision log."""
    log = load_decision_log()
    decisions = log.get("decisions", [])

    if not decisions:
        print("[auto] No decisions logged yet.")
        return

    print(f"\n{'='*70}")
    print(f"  Auto Decision Log ({len(decisions)} entries)")
    print(f"{'='*70}")
    for d in decisions[-30:]:  # Show last 30
        icon = {
            "auto_advance": "\u2714",
            "auto_rework": "\u21a9",
            "circuit_breaker_pause": "\u23f8",
            "manual_pause": "\u23f8",
            "auto_resume": "\u25b6",
            "auto_start": "\u25cf",
            "auto_decide": "\u2699",
            "auto_next_stage": "\u27a1",
        }.get(d.get("decision_type", ""), "?")
        print(f"  {icon} [{d['timestamp']}] {d.get('stage', '?'):30s} "
              f"{d.get('decision_type', '?')}")
        if d.get("details", {}).get("fix_instructions"):
            for fix in d["details"]["fix_instructions"][:3]:
                print(f"      -> {fix[:80]}")
    print(f"{'='*70}\n")


def cmd_auto_status(_args):
    """Show auto mode status and safety metrics."""
    auto_state = load_auto_state()
    log = load_decision_log()

    print(f"\n{'='*70}")
    print(f"  Auto Mode Status")
    print(f"{'='*70}")
    print(f"  Status:              {auto_state.get('status', 'idle')}")
    print(f"  Depth Mode:          {auto_state.get('depth_mode', 'N/A')}")
    print(f"  Activated:           {auto_state.get('activated_at', 'N/A')}")
    if auto_state.get("paused_at"):
        print(f"  Paused:              {auto_state.get('paused_at')}")
    if auto_state.get("completed_at"):
        print(f"  Completed:           {auto_state.get('completed_at')}")
    print(f"  Current Stage:       {auto_state.get('current_stage', 'N/A')}")
    print()
    print(f"  --- Safety Metrics ---")
    print(f"  Total Advances:      {auto_state.get('total_advances', 0)}")
    print(f"  Total Reworks:       {auto_state.get('total_reworks', 0)}")
    print(f"  Total Pauses:        {auto_state.get('total_pauses', 0)}")
    print(f"  Consecutive Reworks: {auto_state.get('consecutive_reworks', 0)} "
          f"/ {CONSECUTIVE_REWORK_THRESHOLD}")
    print(f"  Max Reworks/Stage:   {auto_state.get('max_reworks_per_stage', 3)}")

    sr = auto_state.get("stage_reworks", {})
    if sr:
        print(f"\n  --- Per-Stage Reworks ---")
        for stage, count in sorted(sr.items()):
            print(f"    {stage}: {count}")

    decisions = log.get("decisions", [])
    print(f"\n  Decision Log:        {len(decisions)} entries")

    # Pipeline progress
    try:
        data = load_pipeline()
        approved = sum(1 for v in data.get("stages", {}).values()
                       if v.get("status") == "approved")
        total = len(data.get("stages", {}))
        print(f"  Pipeline Progress:   {approved}/{total} stages approved")
    except Exception:
        pass

    print(f"{'='*70}\n")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(
        description="Auto Orchestrator — 全自动模式编排器 (v1.1)")
    sub = p.add_subparsers(dest="command")

    # auto-start
    pa = sub.add_parser("auto-start", help="Initialize auto mode")
    pa.add_argument("--depth", default=None,
                    help="Depth mode: FAST/STANDARD/CHAMPIONSHIP (default: from pipeline)")

    # auto-next
    sub.add_parser("auto-next", help="Determine next action (advance/rework/pause)")

    # auto-decide
    pd = sub.add_parser("auto-decide", help="Auto-decide for a decision point")
    pd.add_argument("decision_point", help="Decision point ID (e.g., S3_model_selection)")
    pd.add_argument("--context", default=None, help="JSON context for the decision")

    # auto-gate-verdict
    pg = sub.add_parser("auto-gate-verdict", help="Run gate check and auto-verdict")
    pg.add_argument("stage", help="Stage ID to check gates for")

    # auto-pause
    sub.add_parser("auto-pause", help="Pause auto mode (request human)")

    # auto-resume
    sub.add_parser("auto-resume", help="Resume auto mode after human intervention")

    # auto-log
    sub.add_parser("auto-log", help="Show decision log")

    # auto-status
    sub.add_parser("auto-status", help="Show auto mode status")

    args = p.parse_args()

    dispatch = {
        "auto-start": cmd_auto_start,
        "auto-next": cmd_auto_next,
        "auto-decide": cmd_auto_decide,
        "auto-gate-verdict": cmd_auto_gate_verdict,
        "auto-pause": cmd_auto_pause,
        "auto-resume": cmd_auto_resume,
        "auto-log": cmd_auto_log,
        "auto-status": cmd_auto_status,
    }

    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
