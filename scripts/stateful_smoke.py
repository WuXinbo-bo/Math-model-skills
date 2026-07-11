from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from baseline_smoke import CHECKPOINT_ACTION, GENERATORS, PIPELINE_MANAGER, STAGE_EXECUTOR, WORKSPACE_INIT, ensure_exists
from manifest import find_step


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, *args],
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(args)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    return proc


def load_state(workspace: Path) -> dict:
    return json.loads((workspace / "状态" / "工作流状态.json").read_text(encoding="utf-8"))


def assert_status(workspace: Path, stage_id: str, expected: str) -> None:
    state = load_state(workspace)
    for step in state["steps"]:
        if step["stage_id"] == stage_id:
            actual = step["status"]
            if actual != expected:
                raise RuntimeError(f"Expected {stage_id} status {expected}, got {actual}")
            return
    raise RuntimeError(f"Missing stage in state: {stage_id}")


def stage_gate_exists(workspace: Path, stage_id: str) -> bool:
    step = find_step(stage_id)
    name = step["display_name"] if step else stage_id
    return (workspace / "审查" / "门禁" / f"{name}.json").exists()


def complete_stage(workspace: Path, stage: str) -> None:
    run(str(STAGE_EXECUTOR), "begin", stage, "--workspace", str(workspace))
    GENERATORS[stage](workspace)
    run(str(STAGE_EXECUTOR), "validate", stage, "--workspace", str(workspace))
    run(str(STAGE_EXECUTOR), "gate_check", stage, "--workspace", str(workspace))
    if not stage_gate_exists(workspace, stage):
        raise RuntimeError(f"Missing gate report for {stage}")
    artifacts = {
        "DISCOVERY": "问题分析.md",
        "FORMULATION": "建模报告.md",
        "COMPUTATION": "程序/主程序.py,计算结果.md,图表/全部结果.json,依赖清单.txt",
        "EVIDENCE": "图表/图表引用.tex,图表/结果总览图.pdf",
        "SCHEMATICS": "图表/图表引用.tex,图表/技术路线图.drawio,图表/技术路线图.pdf",
        "MANUSCRIPT": "论文/论文正文.tex",
        "ASSURANCE": "论文/数模论文.pdf",
    }[stage]
    run(str(STAGE_EXECUTOR), "complete", stage, "--workspace", str(workspace), "--artifacts", artifacts)
    if stage in CHECKPOINT_ACTION:
        run(
            str(STAGE_EXECUTOR),
            "checkpoint",
            stage,
            "--workspace",
            str(workspace),
            "--action",
            CHECKPOINT_ACTION[stage],
            "--note",
            "stateful smoke",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Exercise checkpoint rerun, downstream invalidation, and resume behavior.")
    parser.add_argument("--workspace", default=str((Path(__file__).resolve().parent.parent.parent / "runtime_stateful_smoke").resolve()))
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    if workspace.exists() and not args.keep:
        shutil.rmtree(workspace)

    run(str(WORKSPACE_INIT), "--workspace", str(workspace), "--force")

    # First pass DISCOVERY to checkpoint, then force a rerun to validate checkpoint recovery.
    run(str(STAGE_EXECUTOR), "begin", "DISCOVERY", "--workspace", str(workspace))
    GENERATORS["DISCOVERY"](workspace)
    run(str(STAGE_EXECUTOR), "validate", "DISCOVERY", "--workspace", str(workspace))
    run(str(STAGE_EXECUTOR), "gate_check", "DISCOVERY", "--workspace", str(workspace))
    run(str(STAGE_EXECUTOR), "complete", "DISCOVERY", "--workspace", str(workspace), "--artifacts", "问题分析.md")
    assert_status(workspace, "DISCOVERY", "waiting_checkpoint")
    if not stage_gate_exists(workspace, "DISCOVERY"):
        raise RuntimeError("DISCOVERY gate report should exist before checkpoint rerun")
    run(str(STAGE_EXECUTOR), "checkpoint", "DISCOVERY", "--workspace", str(workspace), "--action", "rerun", "--note", "stateful smoke rerun")
    assert_status(workspace, "DISCOVERY", "pending")
    if stage_gate_exists(workspace, "DISCOVERY"):
        raise RuntimeError("DISCOVERY gate report should be cleared after checkpoint rerun")
    state = load_state(workspace)
    s1 = next(step for step in state["steps"] if step["stage_id"] == "DISCOVERY")
    if s1["artifacts"] or s1["last_gate"] is not None:
        raise RuntimeError("DISCOVERY artifacts and gate evidence should be cleared after rerun")

    # Re-run DISCOVERY and finish baseline.
    complete_stage(workspace, "DISCOVERY")
    for stage in ["FORMULATION", "COMPUTATION", "EVIDENCE", "SCHEMATICS", "MANUSCRIPT", "ASSURANCE"]:
        complete_stage(workspace, stage)

    run(str(PIPELINE_MANAGER), "set-phase", "enhancement", "--workspace", str(workspace))

    # Rework an upstream stage and ensure downstream completion evidence is invalidated.
    run(str(STAGE_EXECUTOR), "rework", "FORMULATION", "--workspace", str(workspace), "--reason", "enhancement tightening")
    state = load_state(workspace)
    expected_status = {
        "DISCOVERY": "completed",
        "FORMULATION": "pending",
        "COMPUTATION": "pending",
        "EVIDENCE": "pending",
        "SCHEMATICS": "pending",
        "MANUSCRIPT": "pending",
        "ASSURANCE": "pending",
    }
    for stage_id, status in expected_status.items():
        actual = next(step for step in state["steps"] if step["stage_id"] == stage_id)["status"]
        if actual != status:
            raise RuntimeError(f"Expected {stage_id} status {status} after upstream rework, got {actual}")
    for stage_id in ["FORMULATION", "COMPUTATION", "EVIDENCE", "SCHEMATICS", "MANUSCRIPT", "ASSURANCE"]:
        if stage_gate_exists(workspace, stage_id):
            raise RuntimeError(f"{stage_id} gate report should be removed after upstream rework")

    # Resume from FORMULATION inside enhancement, and make sure the enhancement packet is present.
    run(str(STAGE_EXECUTOR), "begin", "FORMULATION", "--workspace", str(workspace))
    ensure_exists(workspace / "当前任务" / "执行中" / "增强指南.md")
    GENERATORS["FORMULATION"](workspace)
    run(str(STAGE_EXECUTOR), "validate", "FORMULATION", "--workspace", str(workspace))
    run(str(STAGE_EXECUTOR), "gate_check", "FORMULATION", "--workspace", str(workspace))
    run(str(STAGE_EXECUTOR), "complete", "FORMULATION", "--workspace", str(workspace), "--artifacts", "建模报告.md")
    run(str(STAGE_EXECUTOR), "checkpoint", "FORMULATION", "--workspace", str(workspace), "--action", "feedback", "--note", "enhancement pass")

    nxt = run(str(PIPELINE_MANAGER), "next", "--workspace", str(workspace))
    next_payload = json.loads(nxt.stdout)
    if next_payload.get("kind") != "begin" or "COMPUTATION" not in next_payload.get("command", ""):
        raise RuntimeError(f"Expected COMPUTATION to be the next action after enhancement rerun of FORMULATION, got: {next_payload}")

    print(json.dumps({"workspace": str(workspace), "result": "ok"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
