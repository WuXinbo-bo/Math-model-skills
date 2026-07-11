from __future__ import annotations

import argparse
import json
from pathlib import Path

from manifest import ordered_steps
from state_store import get_step_state, load_state


ENHANCEMENT_FOCUS = {
    "DISCOVERY": [
        "Complete the sentence-level coverage tables and remove ambiguous interpretations.",
        "Tighten roadmap / flow-diagram planning so every downstream figure has an explicit owner.",
    ],
    "FORMULATION": [
        "Convert key assumptions into explicit parameters and export stronger validation checkpoints.",
        "Review every enhancement suggestion from DISCOVERY and record accept/reject reasons in the report.",
    ],
    "COMPUTATION": [
        "Keep executable evidence for each sub-problem and tighten JSON-to-results consistency.",
        "检测到用户数据时增加数据读取校验，并保留逐问题执行轨迹。",
    ],
    "EVIDENCE": [
        "Reconcile planned data figures with generated outputs and latex include entries.",
        "Make figure sizing, labels, and publication quality checks more explicit.",
    ],
    "SCHEMATICS": [
        "Reconcile every planned DrawIO/TikZ source with a generated PDF and section embedding target.",
        "Preserve EVIDENCE include blocks while appending diagram blocks deterministically.",
    ],
    "MANUSCRIPT": [
        "Tighten template integrity, full figure embedding, and section completeness.",
        "Recheck abstract, conclusion, bibliography, appendix, and upstream numeric consistency.",
    ],
    "ASSURANCE": [
        "Tighten anonymity, stale-figure detection, and compile diagnostics.",
        "Treat compile compliance as a real audit, not just PDF existence.",
    ],
}


def workspace_path(raw: str) -> Path:
    return Path(raw).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="Identify high-value rework targets for Meta-model-agent research and paper quality.")
    parser.add_argument("--workspace", default=".")
    args = parser.parse_args()

    workspace = workspace_path(args.workspace)
    state = load_state(workspace)
    all_completed = all(step["status"] == "completed" for step in state["steps"])

    payload = {
        "phase": state["phase"],
        "workflow_status": state["workflow_status"],
        "baseline_completed": all_completed,
        "next_command": "",
        "stages": [],
    }

    if not all_completed:
        payload["next_command"] = "python scripts/pipeline_manager.py overview --workspace ."
    elif state["phase"] != "enhancement":
        payload["next_command"] = "python scripts/pipeline_manager.py set-phase enhancement --workspace ."
    else:
        payload["next_command"] = "python scripts/stage_executor.py rework DISCOVERY --workspace . --reason \"enhancement tightening\""

    for step in ordered_steps():
        step_state = get_step_state(state, step["stage_id"])
        gate_report = workspace / "审查" / "门禁" / f"{step['display_name']}.json"
        payload["stages"].append(
            {
                "stage_id": step["stage_id"],
                "skill_name": step["skill_name"],
                "display_name": step["display_name"],
                "baseline_status": step_state["status"] if step_state else "unknown",
                "gate_report_exists": gate_report.exists(),
                "enhancement_focus": ENHANCEMENT_FOCUS.get(step["stage_id"], []),
                "suggested_commands": [
                    f"python scripts/stage_executor.py rework {step['stage_id']} --workspace . --reason \"enhancement tightening\"",
                    f"python scripts/stage_executor.py begin {step['stage_id']} --workspace .",
                ],
            }
        )

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
