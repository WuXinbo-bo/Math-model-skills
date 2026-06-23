#!/usr/bin/env python3
"""
Math Modeling Contest - Pipeline Manager (v3.0.0)
Report generation and workflow.yaml parsing.

**P1-5 DEPRECATION NOTICE (v3.0)**:
  State management is DEPRECATED in this script.
  stage_executor.py is the SOLE AUTHORITY for pipeline state.
  State file: state/stage_execution.json (managed by stage_executor.py)

  Legacy commands (init, start-stage, advance, rework, etc.) that modify
  pipeline.json are RETAINED for backward compatibility but SHOULD NOT
  be used. All state operations MUST go through stage_executor.py.

  Commands retained as ACTIVE:
  - status                  (read-only, delegates to stage_executor)
  - workflow-info           (read-only, workflow.yaml parsing)
  - check-gate              (read-only, delegates to gate_contracts.py)
  - parallel-status         (read-only)
  - parallel-merge-status   (read-only)
  - save_stage_output       (report generation, no state mutation)
  - _save_pipeline_overview (report generation, no state mutation)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Determine script directory for path resolution
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from workspace_utils import resolve_workspace, resolve_skill_root
SKILL_ROOT = resolve_skill_root()
CONFIG_DIR = SKILL_ROOT / "config"
WORKFLOW_YAML = CONFIG_DIR / "workflow.yaml"

WORKSPACE    = resolve_workspace()
STATE_DIR    = WORKSPACE / "state"
PIPELINE     = STATE_DIR / "pipeline.json"
REVIEW_REQ   = STATE_DIR / "review_request.md"
HUMAN_FILE   = STATE_DIR / "human_intervention.md"
EVAL_LOG     = WORKSPACE / "memory" / "evaluation_log.md"

_INJECTION_PATTERNS = ["[APPROVED]", "[REWORK]", "[MANUAL_SPEC]"]


def _sanitize(text: str) -> str:
    """Remove possible injection of pipeline control markers."""
    for pat in _INJECTION_PATTERNS:
        text = text.replace(pat, pat.replace("[", "\u2983").replace("]", "\u2984"))
    return text


# ═══════════════════════════════════════════════════════════════
# workflow.yaml Parser — SINGLE SOURCE OF TRUTH
# ═══════════════════════════════════════════════════════════════

def load_workflow() -> dict:
    """Load and parse workflow.yaml. Returns structured workflow config.

    Supports both PyYAML and a minimal inline parser for environments
    without PyYAML installed.
    """
    if not WORKFLOW_YAML.exists():
        sys.exit(f"[pipeline] workflow.yaml not found at {WORKFLOW_YAML}")

    content = WORKFLOW_YAML.read_text(encoding="utf-8")

    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        pass

    # Minimal YAML parser for our specific workflow.yaml structure
    return _parse_workflow_yaml_inline(content)


def _parse_workflow_yaml_inline(content: str) -> dict:
    """Minimal inline parser for workflow.yaml — handles our specific format."""
    import re

    result = {"workflow": {}, "stages": [], "gates": {}}
    lines = content.split("\n")

    current_section = None
    current_stage = None
    current_gate = None
    indent_stack = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # Top-level keys
        if indent == 0:
            if stripped == "workflow:":
                current_section = "workflow"
                current_stage = None
                current_gate = None
                continue
            elif stripped == "stages:":
                current_section = "stages"
                current_stage = None
                current_gate = None
                continue
            elif stripped == "gates:":
                current_section = "gates"
                current_stage = None
                current_gate = None
                continue

        if current_section == "workflow":
            m = re.match(r'(\w[\w\s]*?):\s*"?(.*?)"?\s*$', stripped)
            if m:
                result["workflow"][m.group(1).strip()] = m.group(2).strip().strip('"')

        elif current_section == "stages":
            if stripped.startswith("- id:"):
                current_stage = {}
                current_stage["id"] = stripped.split(":", 1)[1].strip()
                result["stages"].append(current_stage)
            elif current_stage and indent >= 4:
                m = re.match(r'(\w[\w_]*?):\s*(.*)', stripped)
                if m:
                    key = m.group(1).strip()
                    val = m.group(2).strip()
                    if val.startswith("[") and val.endswith("]"):
                        # Parse YAML list inline: ["item1", "item2"]
                        items = [s.strip().strip('"').strip("'")
                                 for s in val[1:-1].split(",") if s.strip()]
                        current_stage[key] = items
                    elif val.startswith('"') or val.startswith("'"):
                        current_stage[key] = val.strip('"').strip("'")
                    else:
                        current_stage[key] = val

        elif current_section == "gates":
            if stripped.endswith(":") and not stripped.startswith("-"):
                gate_id = stripped.rstrip(":")
                current_gate = {"id": gate_id}
                result["gates"][gate_id] = current_gate
            elif current_gate and "description" not in current_gate:
                m = re.match(r'description:\s*"?(.*?)"?\s*$', stripped)
                if m:
                    current_gate["description"] = m.group(1).strip().strip('"')

    return result


def parse_workflow_stages(workflow_data: dict) -> dict:
    """Parse workflow.yaml data into structured pipeline config.

    Returns:
        {
            "stages": [ordered stage ids],
            "stage_map": {stage_id: stage_config},
            "gates": {gate_id: gate_config},
            "stage_gates": {stage_id: [gate_ids]},
            "dependencies": {stage_id: [dep_ids]},
            "meetings": {stage_id: meeting_id},
            "stage_agents": {stage_id: [agent_ids]},
        }
    """
    stages_data = workflow_data.get("stages", [])
    gates_data = workflow_data.get("gates", {})

    config = {
        "stages": [],
        "stage_map": {},
        "gates": gates_data,
        "stage_gates": {},
        "dependencies": {},
        "meetings": {},
        "stage_agents": {},
    }

    for stage in stages_data:
        sid = stage.get("id", "")
        config["stages"].append(sid)
        config["stage_map"][sid] = stage
        config["stage_gates"][sid] = stage.get("gates", [])
        config["dependencies"][sid] = stage.get("dependencies", [])
        if "meeting" in stage:
            config["meetings"][sid] = stage["meeting"]
        config["stage_agents"][sid] = stage.get("agents", [])

    return config


# Load workflow config at module import time
_workflow_data = load_workflow()
_workflow_config = parse_workflow_stages(_workflow_data)

# PRIMARY: stage order from workflow.yaml
STAGE_ORDER = _workflow_config["stages"]
STAGE_MAP = _workflow_config["stage_map"]
WORKFLOW_GATES = _workflow_config["gates"]
STAGE_GATES = _workflow_config["stage_gates"]
STAGE_DEPS = _workflow_config["dependencies"]
STAGE_MEETINGS = _workflow_config["meetings"]
STAGE_AGENTS = _workflow_config["stage_agents"]


def _build_parallel_groups() -> dict:
    """Auto-detect parallel groups from workflow dependencies.
    Stages with the same set of dependencies and no meeting can run in parallel.
    Only groups stages from workflow.yaml — no hardcoded groups.
    """
    groups = {}
    dep_key_stages = {}
    for sid in STAGE_ORDER:
        deps = tuple(sorted(STAGE_DEPS.get(sid, [])))
        if deps not in dep_key_stages:
            dep_key_stages[deps] = []
        dep_key_stages[deps].append(sid)

    group_idx = 0
    for deps, stages in dep_key_stages.items():
        if len(stages) > 1:
            group_name = f"group_{group_idx}"
            groups[group_name] = {
                "stages": stages,
                "prerequisite": deps[0] if deps else None,
                "description": f"Auto-detected parallel group: {', '.join(stages)}",
            }
            group_idx += 1

    return groups


PARALLEL_GROUPS = _build_parallel_groups()

STATUS_ICONS = {
    "not_started":    "\u25cb",
    "in_progress":    "\u25b6",
    "pending_review": "\u23f3",
    "approved":       "\u2714",
    "rework":         "\u21a9",
    "skipped":        "\u2014",
}


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load():
    if not PIPELINE.exists():
        sys.exit("[pipeline] Pipeline not initialized. Run 'init' first.")
    with PIPELINE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with PIPELINE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def cmd_status(_args=None):
    data = load()
    parallel_groups = data.get("parallel_groups", {})

    # Collect sub-stage IDs to skip in main loop
    sub_stage_ids = set()
    for group in parallel_groups.values():
        sub_stage_ids.update(group.get("sub_stages", []))

    print(f"\n{'='*70}")
    print(f"  Pipeline Status — {now()}  (workflow.yaml driven)")
    print(f"{'='*70}")
    print(f"  Contest:  {data.get('contest', 'N/A')}")
    print(f"  Problems: {data.get('problems', 'N/A')}")
    print(f"  Mode:     {data.get('mode', 'N/A')}")
    print(f"  Stages:   {len(STAGE_ORDER)} (from workflow.yaml)")
    print(f"  Gates:    {len(WORKFLOW_GATES)} defined")
    print()

    for stage in STAGE_ORDER:
        # Skip sub-stages in main loop; they're shown under their parent
        if stage in sub_stage_ids:
            continue

        s = data["stages"].get(stage, {})
        status = s.get("status", "not_started")
        icon = STATUS_ICONS.get(status, "?")
        stage_info = STAGE_MAP.get(stage, {})
        name = stage_info.get("name", stage)

        detail = ""
        if status == "approved":
            detail = f" (approved {s.get('approved_at', '')})"
        elif status == "in_progress":
            detail = f" (started {s.get('started_at', '')})"
        elif status == "rework":
            detail = f" (attempt {s.get('attempt', 1)})"
        elif status == "pending_review":
            detail = " (awaiting review)"

        # Show gates
        gates = STAGE_GATES.get(stage, [])
        gate_str = ""
        if gates:
            gate_str = f" gates=[{','.join(gates)}]"

        print(f"  {icon} {stage:<30s} {name}{detail}{gate_str}")

        # Show parallel sub-stages if this stage has them
        if stage in parallel_groups:
            group = parallel_groups[stage]
            for sub_id in group.get("sub_stages", []):
                sub_s = data["stages"].get(sub_id, {})
                sub_status = sub_s.get("status", "not_started")
                sub_icon = STATUS_ICONS.get(sub_status, "?")
                sub_q = sub_s.get("subquestion", sub_id.split("_")[-1])
                sub_detail = ""
                if sub_status == "approved":
                    sub_detail = " done"
                elif sub_status == "in_progress":
                    sub_detail = " running"
                elif sub_status == "rework":
                    sub_detail = f" attempt {sub_s.get('attempt', 1)}"
                print(f"    {sub_icon} {sub_id:<28s} [{sub_q}]{sub_detail}")

    # Show gate summary
    approved = {s for s, v in data["stages"].items() if v.get("status") == "approved"}
    blocked_gates = []
    for gate_id, gate_info in WORKFLOW_GATES.items():
        # Find which stage requires this gate
        for sid, gates in STAGE_GATES.items():
            if gate_id in gates:
                # Check if the stage BEFORE this one is approved
                deps = STAGE_DEPS.get(sid, [])
                if deps and all(d in approved for d in deps):
                    if sid not in approved:
                        blocked_gates.append(gate_id)
                break

    total_stages = len(STAGE_ORDER)
    approved_count = len(approved)
    print(f"\n  Approved: {approved_count}/{total_stages}")
    if blocked_gates:
        print(f"  Pending gates: {', '.join(blocked_gates)}")
    print(f"{'='*70}\n")


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

def cmd_init(args):
    contest = args.contest.upper()
    stages = {}
    parallel_groups = {}

    for s in STAGE_ORDER:
        stages[s] = {"status": "not_started", "attempt": 0, "reworks": 0}

        # Dynamically generate sub-stages for parallel_subquestions stages
        stage_info = STAGE_MAP.get(s, {})
        if stage_info.get("parallel_subquestions") in (True, "true", "True"):
            sub_stage_ids = []
            for q in range(1, args.problems + 1):
                sub_id = f"{s}_Q{q}"
                stages[sub_id] = {
                    "status": "not_started",
                    "attempt": 0,
                    "reworks": 0,
                    "parent_stage": s,
                    "subquestion": f"Q{q}",
                }
                sub_stage_ids.append(sub_id)

            parallel_groups[s] = {
                "sub_stages": sub_stage_ids,
                "description": stage_info.get("parallel_description",
                                               f"Parallel sub-stages for {s}"),
            }

    data = {
        "version": "3.0.0",
        "contest": contest,
        "problems": args.problems,
        "mode": args.mode.upper(),
        "max_reworks": args.max_reworks,
        "created_at": now(),
        "stages": stages,
        "parallel_groups": parallel_groups,
    }
    save(data)
    print(f"[pipeline] Initialized: contest={contest}, problems={args.problems}, mode={data['mode']}")
    if parallel_groups:
        for parent, group in parallel_groups.items():
            print(f"[pipeline] Parallel group '{parent}': {', '.join(group['sub_stages'])}")


def _get_stage(data: dict, stage: str) -> dict:
    if stage not in data["stages"]:
        sys.exit(f"[pipeline] Unknown stage: {stage}")
    return data["stages"][stage]


# ---------------------------------------------------------------------------
# Start Stage
# ---------------------------------------------------------------------------

def cmd_start_stage(args):
    data = load()
    s = _get_stage(data, args.stage)
    if s["status"] not in ("not_started", "rework"):
        sys.exit(f"[pipeline] Cannot start '{args.stage}' — current status: {s['status']}")
    s["status"] = "in_progress"
    s["started_at"] = now()
    s["attempt"] = s.get("attempt", 0) + 1
    save(data)
    print(f"[pipeline] {args.stage} → in_progress (attempt {s['attempt']})")


# ---------------------------------------------------------------------------
# Request Review
# ---------------------------------------------------------------------------

def cmd_request_review(args):
    data = load()
    s = _get_stage(data, args.stage)
    s["status"] = "pending_review"
    s["review_requested_at"] = now()

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_REQ.write_text(
        f"Stage: {args.stage}\n"
        f"Summary: {args.summary}\n"
        f"Results: {args.results}\n"
        f"Concerns: {args.concerns}\n"
        f"Next: {args.next}\n"
        f"Requested: {now()}\n",
        encoding="utf-8",
    )
    HUMAN_FILE.write_text(
        f"# Human Intervention Required\n\n"
        f"Stage `{args.stage}` is awaiting review.\n\n"
        f"## Summary\n{args.summary}\n\n"
        f"Write `[APPROVED]` or `[REWORK]` here, then run `check-approval {args.stage}`.\n",
        encoding="utf-8",
    )
    save(data)
    print(f"[pipeline] {args.stage} → pending_review")
    print(f"[pipeline] Write [APPROVED] or [REWORK] in {HUMAN_FILE}")


# ---------------------------------------------------------------------------
# Check Approval
# ---------------------------------------------------------------------------

def cmd_check_approval(args):
    data = load()
    stage = args.stage
    if not stage:
        if REVIEW_REQ.exists():
            for line in REVIEW_REQ.read_text(encoding="utf-8").splitlines():
                if line.startswith("Stage:"):
                    stage = line.split(":", 1)[1].strip()
                    break
    if not stage:
        sys.exit("[pipeline] No stage specified and none found in review_request.md")
    s = _get_stage(data, stage)

    if not HUMAN_FILE.exists():
        print("PENDING")
        return

    content = HUMAN_FILE.read_text(encoding="utf-8").upper()
    if "[APPROVED]" in content:
        s["status"] = "approved"
        s["approved_at"] = now()
        save(data)
        print(f"[pipeline] {stage} → APPROVED")
    elif "[REWORK]" in content:
        s["status"] = "rework"
        s["reworks"] = s.get("reworks", 0) + 1
        save(data)
        print(f"[pipeline] {stage} → REWORK (attempt {s.get('reworks', 0)})")
    else:
        print("PENDING")


# ---------------------------------------------------------------------------
# Advance
# ---------------------------------------------------------------------------

def cmd_advance(args):
    data = load()
    s = _get_stage(data, args.stage)
    s["status"] = "approved"
    s["approved_at"] = now()
    save(data)
    print(f"[pipeline] {args.stage} → approved")

    # v13.0: S9 approved 后强制预警 S9.5
    if args.stage in ("S9_adversarial_review", "S9"):
        print(f"\n  🚨 CRITICAL: S9 完成！下一步必须是 S9.5（出版规范审查）！")
        print(f"  ⛔ 禁止跳过 S9.5 直接进入 S10！")
        print(f"  🔧 运行: python scripts/stage_executor.py begin S9.5")
        print(f"  🔧 MANDATORY: python scripts/publication_checker.py check outputs/paper/paper_revised.md --mode <mode>")


# ---------------------------------------------------------------------------
# Rework
# ---------------------------------------------------------------------------

def cmd_rework(args):
    data = load()
    s = _get_stage(data, args.stage)
    s["status"] = "rework"
    s["reworks"] = s.get("reworks", 0) + 1
    if args.feedback:
        s["last_feedback"] = _sanitize(args.feedback)
    save(data)
    print(f"[pipeline] {args.stage} → rework (attempt {s['reworks']})")


# ---------------------------------------------------------------------------
# Parallel Commands
# ---------------------------------------------------------------------------

def cmd_parallel_start(args):
    data = load()
    for stage in args.stages:
        s = _get_stage(data, stage)
        s["status"] = "in_progress"
        s["started_at"] = now()
    save(data)
    print(f"[pipeline] Parallel start: {', '.join(args.stages)}")


def cmd_parallel_status(args):
    data = load()
    for stage in args.stages:
        s = data["stages"].get(stage, {})
        status = s.get("status", "not_started")
        icon = STATUS_ICONS.get(status, "?")
        print(f"  {icon} {stage}: {status}")


def cmd_parallel_all_done(args):
    data = load()
    all_approved = True
    for stage in args.stages:
        s = data["stages"].get(stage, {})
        if s.get("status") != "approved":
            all_approved = False
            break
    if all_approved:
        print("[pipeline] All parallel stages approved.")
    else:
        print("[pipeline] NOT all parallel stages approved.")
        sys.exit(1)


def cmd_suggest_parallel(_args=None):
    data = load()
    approved = {s for s, v in data["stages"].items() if v.get("status") == "approved"}
    candidates = []
    for s in STAGE_ORDER:
        if s not in approved and data["stages"][s].get("status") == "not_started":
            candidates.append(s)

    for group_name, group in PARALLEL_GROUPS.items():
        stages_in_group = [s for s in group["stages"] if s in candidates]
        prereq = group.get("prerequisite")
        if stages_in_group and (not prereq or prereq in approved):
            print(f"  [{group_name}] {', '.join(stages_in_group)}")
            print(f"    {group['description']}")

    # Also suggest parallel sub-question groups
    pgroups = data.get("parallel_groups", {})
    for parent_id, group in pgroups.items():
        parent_status = data["stages"].get(parent_id, {}).get("status", "not_started")
        if parent_status != "in_progress":
            continue
        not_done = [s for s in group.get("sub_stages", [])
                    if data["stages"].get(s, {}).get("status") != "approved"]
        if not_done:
            print(f"  [subquestion:{parent_id}] {', '.join(not_done)}")
            print(f"    {group.get('description', 'Parallel sub-question modeling')}")


# ---------------------------------------------------------------------------
# Parallel Merge Commands
# ---------------------------------------------------------------------------

def cmd_parallel_merge_status(args):
    """Check if all sub-stages of a parallel group are done."""
    data = load()
    parent_id = args.stage
    pgroups = data.get("parallel_groups", {})

    if parent_id not in pgroups:
        sys.exit(f"[pipeline] No parallel group found for '{parent_id}'")

    group = pgroups[parent_id]
    sub_stages = group.get("sub_stages", [])
    statuses = {}
    for sub_id in sub_stages:
        s = data["stages"].get(sub_id, {})
        statuses[sub_id] = s.get("status", "not_started")

    all_done = all(v == "approved" for v in statuses.values())
    for sub_id, st in statuses.items():
        icon = STATUS_ICONS.get(st, "?")
        print(f"  {icon} {sub_id}: {st}")

    if all_done:
        print(f"[pipeline] All sub-stages of '{parent_id}' approved. Ready to merge.")
    else:
        pending = [k for k, v in statuses.items() if v != "approved"]
        print(f"[pipeline] Not ready to merge. Pending: {', '.join(pending)}")
        sys.exit(1)


def cmd_parallel_merge(args):
    """Merge: approve the parent stage after all sub-stages are approved."""
    data = load()
    parent_id = args.stage
    pgroups = data.get("parallel_groups", {})

    if parent_id not in pgroups:
        sys.exit(f"[pipeline] No parallel group found for '{parent_id}'")

    group = pgroups[parent_id]
    sub_stages = group.get("sub_stages", [])

    # Verify all sub-stages approved
    for sub_id in sub_stages:
        s = data["stages"].get(sub_id, {})
        if s.get("status") != "approved":
            sys.exit(f"[pipeline] Cannot merge '{parent_id}': sub-stage '{sub_id}' "
                     f"is '{s.get('status', 'not_started')}' (must be approved)")

    # Approve parent
    parent = _get_stage(data, parent_id)
    parent["status"] = "approved"
    parent["approved_at"] = now()
    parent["merge_completed"] = True
    save(data)
    print(f"[pipeline] Merged '{parent_id}': parent approved after all "
          f"{len(sub_stages)} sub-stages completed")


# ---------------------------------------------------------------------------
# Checkpoint Banner
# ---------------------------------------------------------------------------

def cmd_checkpoint_banner(args):
    stage_name = args.stage or ""
    print("\n" + "=" * 60)
    print(f"  CHECKPOINT: {stage_name}")
    print("  Waiting for human review.")
    print("  Write [APPROVED] in state/human_intervention.md to continue.")
    print("=" * 60 + "\n")
    sys.exit(0)


# ---------------------------------------------------------------------------
# Utility Functions (pure file I/O)
# ---------------------------------------------------------------------------

def save_stage_output(stage_name, status, summary, duration=0):
    """Save stage output to outputs/<stage_name>/ directory."""
    stage_dir = Path("outputs") / stage_name
    stage_dir.mkdir(parents=True, exist_ok=True)

    timestamp = now()
    summary_content = f"""# Stage: {stage_name}

**Status:** {status}
**Completed:** {timestamp}
**Duration:** {duration:.1f}s

## Summary

{summary}

## Outputs

- Stage directory: `outputs/{stage_name}/`
- Check this directory for stage-specific artifacts

---
"""
    (stage_dir / "summary.md").write_text(summary_content, encoding="utf-8")

    logs_dir = Path("outputs") / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "pipeline.log"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {stage_name}: {status} ({duration:.1f}s)\n")


def _save_pipeline_overview(results):
    """Save pipeline overview to outputs/overview.md"""
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(parents=True, exist_ok=True)

    content = f"""# Pipeline Overview

**Status:** {results.get('status', 'unknown')}
**Total Duration:** {results.get('duration', 0):.1f}s
**Output:** {results.get('output', 'N/A')}
**Generated:** {now()}

## Stage Summary

| Stage | Status | Duration |
|-------|--------|----------|
"""
    for stage_name, stage_info in results.get("stages", {}).items():
        status = stage_info.get("status", "unknown")
        duration = stage_info.get("duration", 0)
        icon = "\u2714" if status == "completed" else "\u2718"
        content += f"| {stage_name} | {icon} {status} | {duration:.1f}s |\n"

    # Auto-generate output structure from STAGE_ORDER
    output_lines = []
    output_lines.append("## Output Structure\n")
    output_lines.append("```")
    output_lines.append("outputs/")
    output_lines.append("├── overview.md")
    output_lines.append("├── logs/pipeline.log")
    for stage_id in STAGE_ORDER:
        output_lines.append(f"├── {stage_id}/summary.md")
    output_lines.append("├── paper/")
    output_lines.append("├── figures/")
    output_lines.append("└── tables/")
    output_lines.append("```")
    content += "\n".join(output_lines)
    (outputs_dir / "overview.md").write_text(content, encoding="utf-8")


def get_output_path(args):
    """Determine output path from args."""
    if hasattr(args, "output") and args.output:
        return args.output
    return "./output/paper_final.docx"


def save_pipeline_state(results):
    """Save pipeline execution state to JSON."""
    state_dir = WORKSPACE / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "pipeline.json"
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Auto-Advance / Auto-Next / Pause (Auto Mode support)
# ---------------------------------------------------------------------------

def cmd_auto_advance(args):
    """Auto-advance: approve current stage and return next actionable stage.

    This command combines advance + find-next in one step for auto mode.
    """
    data = load()
    stage = args.stage
    s = _get_stage(data, stage)
    s["status"] = "approved"
    s["approved_at"] = now()
    s["auto_advanced"] = True
    save(data)
    print(f"[auto] {stage} → approved (auto-advance)")

    # Find next stage
    parallel_groups = data.get("parallel_groups", {})
    sub_stage_ids = set()
    for group in parallel_groups.values():
        sub_stage_ids.update(group.get("sub_stages", []))

    for next_stage in STAGE_ORDER:
        if next_stage in sub_stage_ids:
            continue
        ns = data["stages"].get(next_stage, {})
        if ns.get("status") in ("not_started", "rework"):
            print(f"[auto] Next stage: {next_stage}")
            return
    print("[auto] All stages complete!")


def cmd_auto_next(_args=None):
    """Auto-mode: find the next actionable stage without modifying state."""
    data = load()
    parallel_groups = data.get("parallel_groups", {})
    sub_stage_ids = set()
    for group in parallel_groups.values():
        sub_stage_ids.update(group.get("sub_stages", []))

    for stage in STAGE_ORDER:
        if stage in sub_stage_ids:
            continue
        s = data["stages"].get(stage, {})
        status = s.get("status", "not_started")
        if status in ("not_started", "rework"):
            print(f"{stage}")
            return
        elif status == "in_progress":
            print(f"{stage} (in_progress)")
            return

    print("[auto] All stages complete — no next stage.")


def cmd_pause(_args=None):
    """Pause pipeline for human intervention."""
    data = load()
    data["paused"] = True
    data["paused_at"] = now()
    save(data)
    print("[pipeline] Pipeline PAUSED for human intervention.")
    print("[pipeline] Use 'auto-resume' in auto_orchestrator.py to continue.")


# ---------------------------------------------------------------------------
# Workflow Info (NEW — display parsed workflow.yaml)
# ---------------------------------------------------------------------------

def cmd_workflow_info(_args=None):
    """Print parsed workflow.yaml info for agent reference."""
    print(f"\n{'='*70}")
    print(f"  Workflow Info (from workflow.yaml)")
    print(f"{'='*70}")
    print(f"  Name:    {_workflow_data.get('workflow', {}).get('name', 'N/A')}")
    print(f"  Version: {_workflow_data.get('workflow', {}).get('version', 'N/A')}")
    print(f"  Stages:  {len(STAGE_ORDER)}")
    print(f"  Gates:   {len(WORKFLOW_GATES)}")
    print()

    for i, stage_id in enumerate(STAGE_ORDER, 1):
        info = STAGE_MAP.get(stage_id, {})
        name = info.get("name", "?")
        agents = info.get("agents", [])
        gates = STAGE_GATES.get(stage_id, [])
        meeting = STAGE_MEETINGS.get(stage_id, None)
        deps = STAGE_DEPS.get(stage_id, [])

        print(f"  S{i-1:02d} {stage_id}")
        print(f"      Name:     {name}")
        print(f"      Agents:   {', '.join(agents)}")
        if deps:
            print(f"      Deps:     {', '.join(deps)}")
        if meeting:
            print(f"      Meeting:  {meeting}")
        if gates:
            print(f"      Gates:    {', '.join(gates)}")
        print()

    print("  Gates Definition:")
    for gate_id, gate_info in WORKFLOW_GATES.items():
        desc = gate_info.get("description", "?")
        print(f"    [{gate_id}] {desc}")
    print(f"\n{'='*70}\n")


# ---------------------------------------------------------------------------
# Check Gate (NEW — verify gate contract)
# ---------------------------------------------------------------------------

def cmd_check_gate(args):
    """Check if a specific gate can be evaluated for the current pipeline state."""
    gate_id = args.gate_id

    if gate_id not in WORKFLOW_GATES:
        print(f"[pipeline] Unknown gate: {gate_id}")
        print(f"  Available gates: {', '.join(WORKFLOW_GATES.keys())}")
        return

    gate_info = WORKFLOW_GATES[gate_id]
    data = None
    approved = set()
    if PIPELINE.exists():
        data = load()
        approved = {s for s, v in data["stages"].items() if v.get("status") == "approved"}

    # Find which stage requires this gate
    required_by = None
    for sid, gates in STAGE_GATES.items():
        if gate_id in gates:
            required_by = sid
            break

    print(f"\n  Gate: {gate_id}")
    print(f"  Description: {gate_info.get('description', 'N/A')}")
    print(f"  Required by stage: {required_by or 'N/A'}")

    if required_by and data:
        deps = STAGE_DEPS.get(required_by, [])
        unmet_deps = [d for d in deps if d not in approved]
        if unmet_deps:
            print(f"  Status: BLOCKED (dependencies not met: {', '.join(unmet_deps)})")
        elif required_by in approved:
            print(f"  Status: PASSED (stage already approved)")
        else:
            print(f"  Status: READY (dependencies met, awaiting gate check)")

    # Import gate_contracts if available for detailed checking
    try:
        from gate_contracts import GATE_CONTRACTS
        normalized = gate_id.upper().replace(".", "_").replace("-", "_")
        for contract_key in GATE_CONTRACTS:
            if contract_key.replace(".", "_") == normalized or normalized in contract_key:
                contract = GATE_CONTRACTS[contract_key]
                print(f"\n  Detailed Contract [{contract_key}]:")
                print(f"    Enter: {contract.get('enter_condition', 'N/A')}")
                print(f"    Pass criteria:")
                for c in contract.get("pass_criteria", []):
                    print(f"      - {c}")
                print(f"    Fail fallback: {contract.get('fail_fallback', 'N/A')}")
                break
    except ImportError:
        pass

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Math Modeling Contest Pipeline Manager (v3.0.0 — workflow.yaml driven)")
    sub = p.add_subparsers(dest="command")

    # init
    pi = sub.add_parser("init", help="Initialize pipeline from workflow.yaml")
    pi.add_argument("--mode", required=True, choices=["ap", "AP", "manual", "MANUAL"])
    pi.add_argument("--contest", required=True, choices=["cumcm", "CUMCM", "mcm", "MCM", "icm", "ICM", "51mcm", "51MCM"])
    pi.add_argument("--problems", type=int, default=1)
    pi.add_argument("--max-reworks", type=int, default=5, dest="max_reworks")
    pi.add_argument("--git", action="store_true")

    # status
    sub.add_parser("status", help="Show pipeline status")

    # workflow-info
    sub.add_parser("workflow-info", help="Print parsed workflow.yaml info")

    # check-gate
    pck = sub.add_parser("check-gate", help="Check a specific gate contract")
    pck.add_argument("gate_id", help="Gate ID (e.g., G1_problem_parsed)")

    # start-stage
    ps = sub.add_parser("start-stage", help="Mark stage as in_progress")
    ps.add_argument("stage")

    # request-review
    pr = sub.add_parser("request-review", help="Submit checkpoint review")
    pr.add_argument("--stage", required=True)
    pr.add_argument("--summary", required=True)
    pr.add_argument("--results", default="(see review_request.md)")
    pr.add_argument("--concerns", default="")
    pr.add_argument("--next", default="")

    # check-approval
    pca = sub.add_parser("check-approval", help="Check human approval")
    pca.add_argument("--stage", default="")

    # advance
    pav = sub.add_parser("advance", help="Mark stage approved")
    pav.add_argument("stage")

    # rework
    prw = sub.add_parser("rework", help="Mark stage for rework")
    prw.add_argument("stage")
    prw.add_argument("--feedback", default="")

    # checkpoint-banner
    pcb = sub.add_parser("checkpoint-banner")
    pcb.add_argument("--stage", default="")

    # parallel commands
    pps = sub.add_parser("parallel-start", help="Start stages in parallel")
    pps.add_argument("stages", nargs="+")

    ppst = sub.add_parser("parallel-status", help="Show parallel stage status")
    ppst.add_argument("stages", nargs="+")

    ppad = sub.add_parser("parallel-all-done", help="Check if all parallel stages done")
    ppad.add_argument("stages", nargs="+")

    sub.add_parser("suggest-parallel", help="Suggest parallelizable stages")

    # parallel-merge commands
    pms = sub.add_parser("parallel-merge-status", help="Check parallel sub-stage status")
    pms.add_argument("stage", help="Parent stage ID (e.g., S5_modeling_and_solve)")

    pm = sub.add_parser("parallel-merge", help="Merge parallel sub-stages into parent")
    pm.add_argument("stage", help="Parent stage ID (e.g., S5_modeling_and_solve)")

    # Auto mode commands
    paa = sub.add_parser("auto-advance", help="Auto-advance: approve stage and find next")
    paa.add_argument("stage", help="Stage to auto-advance")

    sub.add_parser("auto-next", help="Auto-mode: find next actionable stage")

    sub.add_parser("pause", help="Pause pipeline for human intervention")

    args = p.parse_args()

    dispatch = {
        "init": cmd_init,
        "status": cmd_status,
        "workflow-info": cmd_workflow_info,
        "check-gate": cmd_check_gate,
        "start-stage": cmd_start_stage,
        "request-review": cmd_request_review,
        "check-approval": cmd_check_approval,
        "advance": cmd_advance,
        "rework": cmd_rework,
        "checkpoint-banner": cmd_checkpoint_banner,
        "parallel-start": cmd_parallel_start,
        "parallel-status": cmd_parallel_status,
        "parallel-all-done": cmd_parallel_all_done,
        "suggest-parallel": cmd_suggest_parallel,
        "parallel-merge-status": cmd_parallel_merge_status,
        "parallel-merge": cmd_parallel_merge,
        "auto-advance": cmd_auto_advance,
        "auto-next": cmd_auto_next,
        "pause": cmd_pause,
    }

    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
