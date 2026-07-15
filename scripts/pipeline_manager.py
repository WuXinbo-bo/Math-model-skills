from __future__ import annotations

import argparse
import json
from pathlib import Path

from manifest import find_step
from state_store import append_event, get_step_state, load_state, save_state


def workspace_path(raw: str) -> Path:
    return Path(raw).resolve()


def require_state(workspace: Path) -> dict:
    try:
        return load_state(workspace)
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing workflow state. Run workspace_init.py first. ({exc})") from exc


def all_baseline_steps_completed(state: dict) -> bool:
    return all(step["status"] == "completed" for step in state["steps"])


def current_step_info(state: dict) -> dict:
    step = find_step(state["current_stage_id"])
    if step is None:
        raise SystemExit(f"Unknown current stage: {state['current_stage_id']}")
    step_state = get_step_state(state, step["stage_id"])
    assert step_state is not None
    merged = dict(step)
    merged["runtime_status"] = step_state["status"]
    merged["attempts"] = step_state["attempts"]
    merged["reworks"] = step_state["reworks"]
    return merged


def next_action(state: dict) -> dict:
    if state.get("active_checkpoint"):
        cp = state["active_checkpoint"]
        return {
            "kind": "checkpoint",
            "message": f"Resolve checkpoint for {cp['stage_id']} ({cp['checkpoint_type']})",
            "command": f"python scripts/stage_executor.py checkpoint {cp['stage_id']} --workspace . --action approve --note \"...\"",
        }
    current = current_step_info(state)
    status = current["runtime_status"]
    review = state.get("championship_review", {})
    if (
        state.get("quality_mode") == "championship"
        and current["stage_id"] == "ASSURANCE"
        and status in {"ready", "pending"}
        and review.get("status") != "completed"
    ):
        return {
            "kind": "championship_review",
            "message": "Complete the championship multi-round paper review before final assurance.",
            "command": "python scripts/championship_review.py init --workspace .",
        }
    if status in {"ready", "pending"}:
        return {
            "kind": "begin",
            "message": f"Start {current['stage_id']} {current['display_name']}",
            "command": f"python scripts/stage_executor.py begin {current['stage_id']} --workspace .",
        }
    if status == "running":
        return {
            "kind": "execute",
            "message": f"Load {current['source_prompt']} and {current['stage_guide']}, then execute the stage work.",
            "command": f"python scripts/stage_executor.py validate {current['stage_id']} --workspace .",
        }
    if status == "waiting_checkpoint":
        return {
            "kind": "checkpoint",
            "message": f"Checkpoint is waiting for {current['stage_id']}",
            "command": f"python scripts/stage_executor.py checkpoint {current['stage_id']} --workspace . --action approve --note \"...\"",
        }
    if status == "completed" and state["workflow_status"] == "completed":
        if state["phase"] == "baseline":
            return {
                "kind": "phase",
                "message": "Baseline is complete. You may switch to enhancement.",
                "command": "python scripts/pipeline_manager.py set-phase enhancement --workspace .",
            }
        return {
            "kind": "enhancement",
            "message": "Enhancement phase is active. Review enhancement targets, then pick a stage to rework under stricter evidence.",
            "command": "python scripts/enhancement_audit.py --workspace .",
        }
    return {"kind": "inspect", "message": "Inspect workflow status.", "command": "python scripts/pipeline_manager.py overview --workspace ."}


def cmd_overview(args: argparse.Namespace) -> int:
    state = require_state(workspace_path(args.workspace))
    current = current_step_info(state)
    payload = {
        "phase": state["phase"],
        "quality_mode": state.get("quality_mode", "standard"),
        "workflow_status": state["workflow_status"],
        "current": current,
        "active_checkpoint": state.get("active_checkpoint"),
        "championship_review": state.get("championship_review"),
        "next_action": next_action(state),
        "steps": state["steps"],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    state = require_state(workspace_path(args.workspace))
    print(json.dumps(next_action(state), ensure_ascii=False, indent=2))
    return 0


def cmd_set_phase(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    target = args.phase
    if target == state["phase"]:
        print(f"[phase] already in {target}")
        return 0
    if target == "enhancement" and not args.force and not all_baseline_steps_completed(state):
        raise SystemExit("Cannot enter enhancement before baseline steps are all completed. Use --force to override.")
    state["phase"] = target
    save_state(workspace, state)
    append_event(workspace, "phase_change", {"phase": target, "force": args.force})
    print(f"[phase] switched to {target}")
    return 0


def cmd_set_mode(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    target = args.mode
    state["quality_mode"] = target
    review = state.setdefault("championship_review", {})
    if target == "championship":
        if review.get("status") in {None, "not_required"}:
            review.update({
                "status": "pending",
                "rounds": [],
                "final_score": None,
                "final_paper": None,
                "completed_at": None,
            })
        assurance = get_step_state(state, "ASSURANCE")
        if assurance and assurance.get("status") == "completed":
            assurance["status"] = "ready"
            assurance["completed_at"] = None
            assurance["artifacts"] = []
            assurance["last_gate"] = None
            assurance["notes"].append("invalidated by championship mode activation")
            state["current_stage_id"] = "ASSURANCE"
            state["workflow_status"] = "ready"
    elif review.get("status") != "completed":
        review["status"] = "not_required"
    save_state(workspace, state)
    append_event(workspace, "quality_mode_change", {"quality_mode": target})
    print(f"[mode] switched to {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the Meta-model-agent research-to-paper workflow.")
    sub = parser.add_subparsers(dest="command", required=True)

    overview = sub.add_parser("overview")
    overview.add_argument("--workspace", default=".")
    overview.set_defaults(func=cmd_overview)

    nxt = sub.add_parser("next")
    nxt.add_argument("--workspace", default=".")
    nxt.set_defaults(func=cmd_next)

    phase = sub.add_parser("set-phase")
    phase.add_argument("phase", choices=["baseline", "enhancement"])
    phase.add_argument("--workspace", default=".")
    phase.add_argument("--force", action="store_true")
    phase.set_defaults(func=cmd_set_phase)

    mode = sub.add_parser("set-mode")
    mode.add_argument("mode", choices=["standard", "championship"])
    mode.add_argument("--workspace", default=".")
    mode.set_defaults(func=cmd_set_mode)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
