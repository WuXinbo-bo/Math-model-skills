#!/usr/bin/env python3
"""
SubagentRunner v1.0 - 子 Agent 调度器 (三级容错策略)

Architecture:
  - This script is a PURE SCHEDULING TOOL. It never calls any LLM API.
  - The main Codex agent calls this script to:
    1. Generate spawn instruction files for subagents
    2. Validate subagent outputs (via SubagentWatchdog)
    3. Manage retry with enriched context
    4. Fallback to role-play mode when all retries fail
  - The main agent reads the generated instruction files and spawns
    subagents via Codex's native spawn mechanism.

Three-Level Fault Tolerance:
  Level 1: spawn subagent -> validate output
  Level 2: retry with enriched context (max 2 retries)
  Level 3: fallback to main agent role-play (BLOCKED for inspector: block + report error)

CLI Commands:
  prepare   --agent-id X --task-json '{}'   Generate spawn instruction
  validate  --agent-id X --task-json '{}'   Validate subagent output
  enrich    --agent-id X --task-json '{}' --attempt N   Generate enriched retry
  fallback  --agent-id X --task-json '{}'   Generate role-play fallback
  run       --agent-id X --task-json '{}'   Full prepare+validate cycle
  meeting   --meeting-id M001 --stage-id S1  Generate all meeting spawns
  status    --meeting-id M001               Show meeting execution status
  log       --agent-id X --task-id T        Show execution log
"""

import argparse
import json
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
SPAWN_DIR = DOCS_DIR / "spawns"
EXEC_LOG_DIR = DOCS_DIR / "command" / "execution_logs"
MEETING_TEMPLATES_FILE = PROJECT_ROOT / "scripts" / "meeting_protocol.py"

# Maximum retry attempts before fallback
MAX_RETRIES = 2

# Agent role-play fallback descriptions
ROLEPLAY_FALLBACKS = {
    "planner": "以规划组(Planner)视角进行战略规划分析",
    "analyst": "以分析组(Analyst)视角进行数据治理分析",
    "proposer": "以提案组(Proposer)视角进行候选模型生成（精度+稳健性）",
    "builder": "以构建组(Builder)视角进行代码实现与实验",
    "critic": "以审查组(Critic)视角进行对抗审查",
    "reviewer": "以评审组(Reviewer)视角进行评审裁决",
    "writer": "以写作组(Writer)视角进行论文撰写与交付",
    "inspector": "以审查官(Inspector)视角进行质量打分",
}


def _ensure_dirs():
    SPAWN_DIR.mkdir(parents=True, exist_ok=True)
    EXEC_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _task_id(agent_id: str, meeting_id: Optional[str] = None) -> str:
    """Generate a unique task ID."""
    prefix = meeting_id or "standalone"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{agent_id}_{ts}"


def _load_execution_log(meeting_id: str) -> Dict[str, Any]:
    """Load or create execution log for a meeting."""
    log_file = EXEC_LOG_DIR / f"{meeting_id}_exec.json"
    if log_file.exists():
        try:
            return json.loads(log_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "meeting_id": meeting_id,
        "created_at": _now(),
        "agents": {},
        "status": "in_progress",
    }


def _save_execution_log(meeting_id: str, log: Dict[str, Any]):
    """Save execution log."""
    log_file = EXEC_LOG_DIR / f"{meeting_id}_exec.json"
    log["updated_at"] = _now()
    log_file.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


# ═══════════════════════════════════════════════════════════════
# Layer 1: Spawn Instruction Generation
# ═══════════════════════════════════════════════════════════════

def prepare_spawn(agent_id: str, task_spec: Dict[str, Any],
                  meeting_id: Optional[str] = None,
                  attempt: int = 0) -> Dict[str, Any]:
    """Generate spawn instruction file for a subagent.

    Creates a structured instruction document that the main agent
    uses to spawn the subagent via Codex's native mechanism.

    Args:
        agent_id: Agent identifier (e.g., "planner")
        task_spec: Task specification with task, input/output files, etc.
        meeting_id: Optional meeting context
        attempt: Current attempt number (0 = first try)

    Returns:
        Dict with spawn_file path and metadata
    """
    _ensure_dirs()

    task_id = task_spec.get("task_id") or _task_id(agent_id, meeting_id)
    output_dir = Path(task_spec.get("output_dir", f"outputs/{meeting_id or 'standalone'}"))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build instruction content
    lines = [
        f"# Spawn Instruction: {agent_id}",
        "",
        f"**Task ID**: {task_id}",
        f"**Meeting**: {meeting_id or 'N/A'}",
        f"**Attempt**: {attempt + 1}/{MAX_RETRIES + 1}",
        f"**Generated**: {_now()}",
        "",
        "---",
        "",
        "## Task",
        "",
        task_spec.get("task", "No task specified."),
        "",
    ]

    # Input files
    input_files = task_spec.get("input_files", [])
    if input_files:
        lines.extend([
            "## Input Files (Read These)",
            "",
        ])
        for f in input_files:
            lines.append(f"- `{f}`")
        lines.append("")

    # Output files
    output_files = task_spec.get("output_files", [])
    if output_files:
        lines.extend([
            "## Output Files (Write These)",
            "",
        ])
        for f in output_files:
            full_path = output_dir / f
            lines.append(f"- `{full_path}`")
        lines.append("")

    # File isolation rules
    read_only = task_spec.get("constraints", {}).get("read_only", [])
    do_not_touch = task_spec.get("constraints", {}).get("do_not_touch", [])
    if read_only or do_not_touch:
        lines.append("## File Isolation Rules")
        lines.append("")
        if read_only:
            lines.append("**Read-only** (upstream artifacts):")
            for f in read_only:
                lines.append(f"- `{f}`")
            lines.append("")
        if do_not_touch:
            lines.append("**Do NOT touch** (other agents' outputs):")
            for f in do_not_touch:
                lines.append(f"- `{f}`")
            lines.append("")

    # Quality expectations
    quality_checks = task_spec.get("quality_checks", [])
    if quality_checks:
        lines.extend([
            "## Quality Requirements",
            "",
        ])
        for check in quality_checks:
            if ":" in check:
                ctype, cval = check.split(":", 1)
                if ctype == "min_length":
                    lines.append(f"- Output must be >= {cval} characters")
                elif ctype == "has_sections":
                    sections = cval.split(",")
                    lines.append(f"- Must contain sections: {', '.join(sections)}")
                elif ctype == "no_placeholders":
                    lines.append("- No TBD/TODO/placeholder text allowed")
                else:
                    lines.append(f"- {check}")
            else:
                lines.append(f"- {check}")
        lines.append("")

    # Retry feedback (if attempt > 0)
    if attempt > 0:
        prev_errors = task_spec.get("previous_errors", [])
        if prev_errors:
            lines.extend([
                "## Previous Attempt Feedback (Fix These Issues)",
                "",
                f"Attempt {attempt} failed with the following issues:",
                "",
            ])
            for err in prev_errors:
                lines.append(f"- {err}")
            lines.append("")
            lines.append("**Please address ALL above issues in this attempt.**")
            lines.append("")

    # Timeout info
    timeout = task_spec.get("timeout_minutes", 15)
    lines.extend([
        "## Constraints",
        "",
        f"- Timeout: {timeout} minutes",
        f"- Output directory: `{output_dir}`",
        f"- All numerical results must be reproducible from code/data",
        "",
    ])

    # Write instruction file
    spawn_file = SPAWN_DIR / f"{task_id}_spawn.md"
    spawn_file.write_text("\n".join(lines), encoding="utf-8")

    result = {
        "status": "prepared",
        "agent_id": agent_id,
        "task_id": task_id,
        "spawn_file": str(spawn_file),
        "output_dir": str(output_dir),
        "output_files": [str(output_dir / f) for f in output_files],
        "attempt": attempt,
        "quality_checks": quality_checks,
    }

    # Log execution
    if meeting_id:
        log = _load_execution_log(meeting_id)
        log["agents"][agent_id] = {
            "task_id": task_id,
            "status": "prepared",
            "attempt": attempt,
            "spawn_file": str(spawn_file),
            "prepared_at": _now(),
        }
        _save_execution_log(meeting_id, log)

    return result


# ═══════════════════════════════════════════════════════════════
# Layer 2: Output Validation (delegates to Watchdog)
# ═══════════════════════════════════════════════════════════════

def validate_output(agent_id: str, task_spec: Dict[str, Any],
                    meeting_id: Optional[str] = None) -> Dict[str, Any]:
    """Validate subagent output files.

    Delegates to SubagentWatchdog for actual validation logic.

    Returns:
        Dict with passed status, errors, and evidence
    """
    try:
        from subagent_watchdog import SubagentWatchdog
        watchdog = SubagentWatchdog()
    except ImportError:
        # Fallback: basic validation if watchdog not available
        return _basic_validation(agent_id, task_spec)

    output_dir = Path(task_spec.get("output_dir", f"outputs/{meeting_id or 'standalone'}"))
    output_files = [str(output_dir / f) for f in task_spec.get("output_files", [])]
    quality_checks = task_spec.get("quality_checks", [])

    result = watchdog.validate(agent_id, output_files, quality_checks)

    # Log validation result
    if meeting_id:
        log = _load_execution_log(meeting_id)
        if agent_id in log["agents"]:
            log["agents"][agent_id]["validation"] = {
                "passed": result["passed"],
                "errors": result.get("errors", []),
                "validated_at": _now(),
            }
            _save_execution_log(meeting_id, log)

    return result


def _basic_validation(agent_id: str, task_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Basic fallback validation when watchdog is not available."""
    output_dir = Path(task_spec.get("output_dir", "outputs/standalone"))
    output_files = task_spec.get("output_files", [])
    errors = []
    evidence = []

    for f in output_files:
        fpath = output_dir / f
        if not fpath.exists():
            errors.append(f"MISSING: {fpath}")
        else:
            size = fpath.stat().st_size
            if size < 50:
                errors.append(f"TOO_THIN: {fpath} ({size} bytes)")
            else:
                evidence.append(f"{f}: {size} bytes")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "evidence": evidence,
    }


# ═══════════════════════════════════════════════════════════════
# Layer 3: Enriched Retry Context
# ═══════════════════════════════════════════════════════════════

def enrich_for_retry(agent_id: str, task_spec: Dict[str, Any],
                     validation_errors: List[str],
                     attempt: int,
                     meeting_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate enriched context for retry attempt.

    Adds previous failure feedback to the task spec so the
    subagent can address the issues.

    Args:
        agent_id: Agent identifier
        task_spec: Original task specification
        validation_errors: Errors from the previous attempt
        attempt: Current attempt number
        meeting_id: Optional meeting context

    Returns:
        Updated task_spec with previous_errors field
    """
    enriched = dict(task_spec)
    enriched["previous_errors"] = validation_errors
    enriched["attempt"] = attempt

    # Add specific guidance based on error types
    guidance = []
    for err in validation_errors:
        if "MISSING" in err:
            guidance.append("Ensure ALL required output files are created.")
        elif "TOO_SHORT" in err or "TOO_THIN" in err:
            guidance.append("Output content is too short. Add more detail and analysis.")
        elif "MISSING_SECTION" in err:
            section = err.split("'")[1] if "'" in err else "required"
            guidance.append(f"Add the missing section: '{section}'")
        elif "UNFINISHED" in err:
            guidance.append("Remove all TBD/TODO placeholders and fill with real content.")
        elif "PLACEHOLDER" in err:
            guidance.append("Replace all placeholder text with actual analysis.")

    if guidance:
        enriched["retry_guidance"] = list(set(guidance))

    return enriched


# ═══════════════════════════════════════════════════════════════
# Layer 4: Role-Play Fallback
# ═══════════════════════════════════════════════════════════════

def generate_fallback(agent_id: str, task_spec: Dict[str, Any],
                      failure_history: List[Dict[str, Any]],
                      meeting_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate role-play fallback instruction.

    When all subagent spawn attempts fail, generate an instruction
    for the main agent to execute the task via role-switching.

    IMPORTANT: Inspector role is BLOCKED from role-play fallback.
    If inspector spawning fails, the stage must be blocked and
    human intervention required.

    Args:
        agent_id: Agent identifier
        task_spec: Original task specification
        failure_history: List of all failed attempts with errors
        meeting_id: Optional meeting context

    Returns:
        Dict with fallback instruction file path, or blocker info for inspector
    """
    # Inspector MUST NOT fallback to role-play
    if agent_id == "inspector":
        return {
            "status": "blocked",
            "agent_id": "inspector",
            "reason": (
                "Inspector role cannot use role-play fallback. "
                "Quality scoring requires independent sub-agent execution. "
                "Stage must be blocked and human intervention required."
            ),
            "failure_history": failure_history,
        }

    _ensure_dirs()

    task_id = task_spec.get("task_id") or _task_id(agent_id, meeting_id)
    output_dir = Path(task_spec.get("output_dir", f"outputs/{meeting_id or 'standalone'}"))

    roleplay_desc = ROLEPLAY_FALLBACKS.get(agent_id, f"以{agent_id}角色执行任务")

    lines = [
        f"# Role-Play Fallback: {agent_id}",
        "",
        f"**Task ID**: {task_id}",
        f"**Meeting**: {meeting_id or 'N/A'}",
        f"**Generated**: {_now()}",
        f"**Reason**: All {MAX_RETRIES + 1} subagent spawn attempts failed",
        "",
        "---",
        "",
        "## Instruction",
        "",
        f"The main agent should now **switch to {agent_id} role** and execute",
        f"the task directly. {roleplay_desc}.",
        "",
        "## Original Task",
        "",
        task_spec.get("task", "No task specified."),
        "",
        "## Output Files to Create",
        "",
    ]

    for f in task_spec.get("output_files", []):
        lines.append(f"- `{output_dir / f}`")

    lines.extend([
        "",
        "## Failure History (Why Subagent Failed)",
        "",
    ])

    for i, failure in enumerate(failure_history, 1):
        lines.append(f"### Attempt {i}")
        for err in failure.get("errors", []):
            lines.append(f"- {err}")
        lines.append("")

    lines.extend([
        "## Important",
        "",
        "- Execute as the main agent, adopting the role's perspective",
        "- Create ALL required output files",
        "- Meet ALL quality requirements",
        "- This is the LAST resort — must succeed",
        "",
    ])

    fallback_file = SPAWN_DIR / f"{task_id}_fallback.md"
    fallback_file.write_text("\n".join(lines), encoding="utf-8")

    # Log fallback
    if meeting_id:
        log = _load_execution_log(meeting_id)
        if agent_id in log["agents"]:
            log["agents"][agent_id]["status"] = "fallback"
            log["agents"][agent_id]["fallback_file"] = str(fallback_file)
            log["agents"][agent_id]["fallback_at"] = _now()
            log["agents"][agent_id]["failure_history"] = failure_history
        _save_execution_log(meeting_id, log)

    return {
        "status": "fallback",
        "agent_id": agent_id,
        "task_id": task_id,
        "fallback_file": str(fallback_file),
        "roleplay_description": roleplay_desc,
    }


# ═══════════════════════════════════════════════════════════════
# Full Cycle: Prepare + Validate
# ═══════════════════════════════════════════════════════════════

def run_full_cycle(agent_id: str, task_spec: Dict[str, Any],
                   meeting_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute the full prepare-validate cycle for a subagent.

    This is the main entry point for the three-level fault tolerance:
    1. Prepare spawn instruction
    2. (Main agent spawns subagent and waits)
    3. Validate output
    4. If failed: retry with enriched context (up to MAX_RETRIES)
    5. If all failed: generate role-play fallback

    Note: This function only handles the PREPARE phase.
    The main agent must spawn the subagent, then call validate separately.

    Returns:
        Dict with phase status and next action
    """
    # Phase 1: Prepare
    prep_result = prepare_spawn(agent_id, task_spec, meeting_id, attempt=0)

    return {
        "phase": "prepared",
        "agent_id": agent_id,
        "task_id": prep_result["task_id"],
        "spawn_file": prep_result["spawn_file"],
        "next_action": "spawn_subagent",
        "instruction": (
            f"Read {prep_result['spawn_file']} and spawn the {agent_id} subagent. "
            f"After the subagent completes, run: "
            f"python scripts/subagent_runner.py validate "
            f"--agent-id {agent_id} --task-json '<task_spec_json>'"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# Meeting Orchestration
# ═══════════════════════════════════════════════════════════════

def prepare_meeting_spawns(meeting_id: str, stage_id: str,
                           extra_context: Optional[Dict] = None) -> Dict[str, Any]:
    """Generate spawn instructions for ALL agents in a meeting.

    Reads the meeting template from meeting_protocol.py and generates
    spawn instructions for each agent according to the subagent_plan.

    Args:
        meeting_id: Meeting identifier (e.g., "M001_kickoff")
        stage_id: Stage identifier
        extra_context: Additional context to inject into task specs

    Returns:
        Dict with parallel and sequential spawn lists
    """
    _ensure_dirs()

    # Import meeting templates
    try:
        from meeting_protocol import MEETING_TEMPLATES
    except ImportError:
        sys.exit(f"[SubagentRunner] Cannot import meeting_protocol.py")

    template = MEETING_TEMPLATES.get(meeting_id)
    if not template:
        return {"status": "error", "msg": f"Unknown meeting: {meeting_id}"}

    plan = template.get("subagent_plan", {})
    parallel_agents = plan.get("parallel", [])
    sequential_agents = plan.get("sequential", [])

    # Initialize execution log
    log = _load_execution_log(meeting_id)
    log["stage_id"] = stage_id
    log["template_name"] = template["name"]

    # Generate parallel spawns
    parallel_spawns = []
    for item in parallel_agents:
        agent_id = item["agent"]
        # Skip "main (...)" agents — those are role-play, not spawns
        if agent_id.startswith("main"):
            continue

        task_spec = _build_task_spec_from_meeting(agent_id, item, meeting_id,
                                                  stage_id, template, extra_context)
        result = prepare_spawn(agent_id, task_spec, meeting_id)
        parallel_spawns.append(result)

    # Generate sequential spawns
    sequential_spawns = []
    for item in sequential_agents:
        agent_id = item["agent"]
        if agent_id.startswith("main"):
            continue

        task_spec = _build_task_spec_from_meeting(agent_id, item, meeting_id,
                                                  stage_id, template, extra_context)
        result = prepare_spawn(agent_id, task_spec, meeting_id)
        sequential_spawns.append(result)

    log["parallel_count"] = len(parallel_spawns)
    log["sequential_count"] = len(sequential_spawns)
    _save_execution_log(meeting_id, log)

    return {
        "status": "prepared",
        "meeting_id": meeting_id,
        "meeting_name": template["name"],
        "stage_id": stage_id,
        "parallel_spawns": parallel_spawns,
        "sequential_spawns": sequential_spawns,
        "total_agents": len(parallel_spawns) + len(sequential_spawns),
        "instruction": _build_meeting_instruction(meeting_id, parallel_spawns,
                                                  sequential_spawns, template),
    }


def _build_task_spec_from_meeting(agent_id: str, item: Dict, meeting_id: str,
                                  stage_id: str, template: Dict,
                                  extra_context: Optional[Dict] = None) -> Dict[str, Any]:
    """Build a task_spec from meeting template data."""
    output_dir = f"outputs/{meeting_id}"

    # Map agent to expected output files
    output_map = {
        "planner": ["planner_view.md"],
        "analyst": ["analyst_view.md"],
        "reviewer": ["reviewer_review.md"],
        "proposer": ["proposer_proposals.md"],
        "critic": ["critic_attack.md"],
        "builder": ["builder_report.md"],
        "writer": ["writer_revision.md"],
        "inspector": ["inspector_review.md"],
    }

    # Map agent to input files based on meeting type
    input_map = {
        "M001_kickoff": {
            "planner": ["inputs/problem_text.md", "inputs/contest_info.md"],
            "analyst": ["inputs/problem_text.md", "inputs/data_files.md"],
            "reviewer": [f"outputs/{meeting_id}/planner_view.md",
                         f"outputs/{meeting_id}/analyst_view.md"],
        },
        "M002_model_debate": {
            "proposer": ["outputs/problem_analysis/analysis.md",
                         "outputs/problem_analysis/variables.json"],
            "reviewer": [f"outputs/{meeting_id}/proposer_proposals.md"],
        },
        "M004_paper_redteam": {
            "critic": ["paper.md", "outputs/evidence/conclusion_evidence_map.md"],
            "reviewer": ["paper.md", f"outputs/{meeting_id}/critic_attack.md"],
            "writer": ["paper.md", f"outputs/{meeting_id}/critic_attack.md",
                       f"outputs/{meeting_id}/reviewer_review.md"],
        },
    }

    task_spec = {
        "task": item.get("task", f"Execute {agent_id} role in {meeting_id}"),
        "input_files": input_map.get(meeting_id, {}).get(agent_id, []),
        "output_files": output_map.get(agent_id, [f"{agent_id}_output.md"]),
        "output_dir": output_dir,
        "quality_checks": ["min_length:500", "no_placeholders"],
        "timeout_minutes": 15,
    }

    if extra_context:
        task_spec.update(extra_context)

    return task_spec


def _build_meeting_instruction(meeting_id: str, parallel_spawns: List,
                               sequential_spawns: List, template: Dict) -> str:
    """Build human-readable instruction for meeting execution."""
    lines = [
        f"## Meeting Execution Plan: {template['name']}",
        "",
    ]

    if parallel_spawns:
        lines.extend([
            "### Phase 1: Parallel Spawn",
            "",
            "Spawn these agents **simultaneously**:",
            "",
        ])
        for spawn in parallel_spawns:
            lines.append(f"1. Read `{spawn['spawn_file']}` and spawn `{spawn['agent_id']}`")
        lines.append("")
        lines.append("After ALL parallel agents complete, validate each:")
        for spawn in parallel_spawns:
            lines.append(
                f"   ```bash\n"
                f"   python scripts/subagent_runner.py validate "
                f"--agent-id {spawn['agent_id']} "
                f"--task-json '{{\"output_dir\": \"{spawn['output_dir']}\"}}'\n"
                f"   ```"
            )
        lines.append("")

    if sequential_spawns:
        lines.extend([
            "### Phase 2: Sequential Spawn",
            "",
            "Spawn these agents **one at a time** (after parallel phase):",
            "",
        ])
        for i, spawn in enumerate(sequential_spawns, 1):
            lines.append(f"{i}. Read `{spawn['spawn_file']}` and spawn `{spawn['agent_id']}`")
            lines.append(
                f"   Validate: `python scripts/subagent_runner.py validate "
                f"--agent-id {spawn['agent_id']} --task-json '...'`"
            )
        lines.append("")

    lines.extend([
        "### Fallback",
        "",
        "If any agent fails validation after 2 retries, run:",
        "```bash",
        f"python scripts/subagent_runner.py fallback --agent-id <agent> "
        f"--task-json '...' --meeting-id {meeting_id}",
        "```",
        "Then execute the task as the main agent in role-play mode.",
        "",
    ])

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# Status & Logging
# ═══════════════════════════════════════════════════════════════

def get_meeting_status(meeting_id: str) -> Dict[str, Any]:
    """Get execution status for a meeting."""
    log = _load_execution_log(meeting_id)
    agents = log.get("agents", {})

    summary = {
        "meeting_id": meeting_id,
        "status": log.get("status", "unknown"),
        "total_agents": len(agents),
        "agents": {},
    }

    for agent_id, info in agents.items():
        summary["agents"][agent_id] = {
            "status": info.get("status", "unknown"),
            "attempt": info.get("attempt", 0),
            "was_fallback": info.get("status") == "fallback",
            "validation_passed": info.get("validation", {}).get("passed", None),
        }

    # Determine overall status
    statuses = [a["status"] for a in agents.values()]
    if not statuses:
        summary["status"] = "not_started"
    elif all(s in ("completed", "fallback") for s in statuses):
        summary["status"] = "completed"
    elif any(s == "in_progress" for s in statuses):
        summary["status"] = "in_progress"

    return summary


def print_meeting_status(meeting_id: str):
    """Print meeting execution status."""
    status = get_meeting_status(meeting_id)
    print(f"\n{'=' * 60}")
    print(f"  Meeting Execution Status: {meeting_id}")
    print(f"{'=' * 60}")
    print(f"  Overall: {status['status']}")
    print(f"  Agents:  {status['total_agents']}")
    print()

    icons = {
        "prepared": "○",
        "spawned": "▶",
        "completed": "✔",
        "fallback": "↩",
        "failed": "✘",
        "unknown": "?",
    }

    for agent_id, info in status["agents"].items():
        icon = icons.get(info["status"], "?")
        fallback = " (role-play fallback)" if info["was_fallback"] else ""
        validation = ""
        if info["validation_passed"] is True:
            validation = " [validated]"
        elif info["validation_passed"] is False:
            validation = " [validation failed]"
        print(f"  {icon} {agent_id:<20s} {info['status']}{validation}{fallback}")

    print(f"{'=' * 60}\n")


# ═══════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(
        description="SubagentRunner v1.0 - 子 Agent 调度器 (三级容错)"
    )
    sub = p.add_subparsers(dest="command")

    # prepare
    pp = sub.add_parser("prepare", help="Generate spawn instruction")
    pp.add_argument("--agent-id", required=True)
    pp.add_argument("--task-json", required=True)
    pp.add_argument("--meeting-id", default=None)

    # validate
    pv = sub.add_parser("validate", help="Validate subagent output")
    pv.add_argument("--agent-id", required=True)
    pv.add_argument("--task-json", required=True)
    pv.add_argument("--meeting-id", default=None)

    # enrich
    pe = sub.add_parser("enrich", help="Generate enriched retry context")
    pe.add_argument("--agent-id", required=True)
    pe.add_argument("--task-json", required=True)
    pe.add_argument("--attempt", type=int, required=True)
    pe.add_argument("--errors", nargs="+", default=[])
    pe.add_argument("--meeting-id", default=None)

    # fallback
    pf = sub.add_parser("fallback", help="Generate role-play fallback")
    pf.add_argument("--agent-id", required=True)
    pf.add_argument("--task-json", required=True)
    pf.add_argument("--meeting-id", default=None)

    # run (full cycle prepare)
    pr = sub.add_parser("run", help="Full prepare cycle")
    pr.add_argument("--agent-id", required=True)
    pr.add_argument("--task-json", required=True)
    pr.add_argument("--meeting-id", default=None)

    # meeting (generate all meeting spawns)
    pm = sub.add_parser("meeting", help="Generate all meeting spawns")
    pm.add_argument("--meeting-id", required=True)
    pm.add_argument("--stage-id", required=True)

    # status
    ps = sub.add_parser("status", help="Show meeting execution status")
    ps.add_argument("--meeting-id", required=True)

    args = p.parse_args()

    if args.command == "prepare":
        task_spec = json.loads(args.task_json)
        result = prepare_spawn(args.agent_id, task_spec, args.meeting_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "validate":
        task_spec = json.loads(args.task_json)
        result = validate_output(args.agent_id, task_spec, args.meeting_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["passed"] else 1)

    elif args.command == "enrich":
        task_spec = json.loads(args.task_json)
        result = enrich_for_retry(args.agent_id, task_spec, args.errors,
                                  args.attempt, args.meeting_id)
        # Generate new spawn with enriched context
        spawn = prepare_spawn(args.agent_id, result, args.meeting_id,
                              attempt=args.attempt)
        print(json.dumps(spawn, ensure_ascii=False, indent=2))

    elif args.command == "fallback":
        task_spec = json.loads(args.task_json)
        # Load failure history from execution log
        failure_history = []
        if args.meeting_id:
            log = _load_execution_log(args.meeting_id)
            agent_log = log.get("agents", {}).get(args.agent_id, {})
            failure_history = agent_log.get("failure_history", [])
        result = generate_fallback(args.agent_id, task_spec, failure_history,
                                   args.meeting_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "run":
        task_spec = json.loads(args.task_json)
        result = run_full_cycle(args.agent_id, task_spec, args.meeting_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "meeting":
        result = prepare_meeting_spawns(args.meeting_id, args.stage_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "status":
        print_meeting_status(args.meeting_id)

    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
