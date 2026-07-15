from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from gate_contracts import run_gate_check
from manifest import SKILL_ROOT, find_step, next_step, ordered_steps
from state_store import append_event, get_step_state, load_state, save_state


def copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def workspace_path(raw: str) -> Path:
    return Path(raw).resolve()


def resolve_stage(identifier: str) -> dict[str, Any]:
    step = find_step(identifier)
    if step is None:
        raise SystemExit(f"Unknown stage identifier: {identifier}")
    return step


def require_state(workspace: Path) -> dict[str, Any]:
    try:
        return load_state(workspace)
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing workflow state. Run workspace_init.py first. ({exc})") from exc


def stage_output_contract(state: dict[str, Any], step: dict[str, Any]) -> tuple[list[str], dict[str, int]]:
    outputs = list(step["output_files"])
    minimums = dict(step.get("min_output_bytes", {}))
    if state.get("output_format") == "docx" and step["stage_id"] == "MANUSCRIPT":
        return ["论文/论文正文.md"], {"论文/论文正文.md": 5000}
    if state.get("output_format") == "docx" and step["stage_id"] == "ASSURANCE":
        return ["论文/数模论文.docx", "论文/docx_report.json"], {"论文/数模论文.docx": 15000, "论文/docx_report.json": 100}
    return outputs, minimums


def prepare_stage_resources(workspace: Path, state: dict[str, Any], step: dict[str, Any]) -> None:
    refs_dir = workspace / "参考资料"
    tmpl_dir = workspace / "模板"
    stage_dir = workspace / "当前任务" / "执行中"
    if refs_dir.exists():
        shutil.rmtree(refs_dir)
    if tmpl_dir.exists():
        shutil.rmtree(tmpl_dir)
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    copy_tree(SKILL_ROOT / "assets" / "shared-scripts", workspace / "工具")
    shutil.copy2(SKILL_ROOT / "scripts" / "docx_export.py", workspace / "工具" / "docx_export.py")
    shutil.copy2(SKILL_ROOT / "scripts" / "build_code_appendix.py", workspace / "工具" / "build_code_appendix.py")
    source_dir = SKILL_ROOT / "references" / "stage_protocols" / step["skill_name"]
    copy_tree(source_dir / "references", refs_dir)
    if step["stage_id"] == "MANUSCRIPT":
        template_key = state.get("competition_profile", {}).get("template_dir", state.get("template_key", "cumcm"))
        copy_tree(source_dir / "templates" / template_key, tmpl_dir / "当前竞赛")
        if state.get("output_format", "pdf") == "docx":
            copy_tree(SKILL_ROOT / "assets" / "templates" / "docx" / state.get("competition", "cumcm"), tmpl_dir / "当前竞赛")
    else:
        copy_tree(source_dir / "templates", tmpl_dir)
    notes = state.get("competition_profile", {}).get("official_notes")
    if notes:
        note_path = SKILL_ROOT / notes
        if note_path.exists():
            refs_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(note_path, refs_dir / "竞赛规则.md")
    if step["stage_id"] in {"MANUSCRIPT", "ASSURANCE"}:
        copy_tree(SKILL_ROOT / "references" / "paper-layout", refs_dir / "paper-layout")


def write_stage_packet(workspace: Path, state: dict[str, Any], step: dict[str, Any]) -> None:
    stage_dir = workspace / "当前任务" / "执行中"
    stage_dir.mkdir(parents=True, exist_ok=True)

    source_prompt_path = SKILL_ROOT / step["source_prompt"]
    stage_guide_path = SKILL_ROOT / step["stage_guide"] if step.get("stage_guide") else None
    subagent_arch_path = SKILL_ROOT / "references" / "subagent-architecture.md"
    enhancement_guide_path = SKILL_ROOT / "references" / "enhancement-operations.md"
    prompt_text = source_prompt_path.read_text(encoding="utf-8")
    guide_text = stage_guide_path.read_text(encoding="utf-8") if stage_guide_path and stage_guide_path.exists() else ""
    subagent_arch_text = subagent_arch_path.read_text(encoding="utf-8") if subagent_arch_path.exists() else ""
    enhancement_guide_text = (
        enhancement_guide_path.read_text(encoding="utf-8")
        if state["phase"] == "enhancement" and enhancement_guide_path.exists()
        else ""
    )

    output_files, _ = stage_output_contract(state, step)
    packet = {
        "phase": state["phase"],
        "competition": state.get("competition", "cumcm"),
        "competition_profile": state.get("competition_profile", {}),
        "workflow_status": state["workflow_status"],
        "stage_id": step["stage_id"],
        "skill_name": step["skill_name"],
        "display_name": step["display_name"],
        "stage_guide": step.get("stage_guide"),
        "source_prompt": step["source_prompt"],
        "output_format": state.get("output_format", "pdf"),
        "output_files": output_files,
        "checkpoint_type": step.get("checkpoint_type"),
        "gates": step.get("gates", []),
        "subagents": step.get("subagents", []),
    }

    (stage_dir / "任务包.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    (stage_dir / "执行协议.md").write_text(prompt_text, encoding="utf-8")
    if guide_text:
        (stage_dir / "工作指南.md").write_text(guide_text, encoding="utf-8")
    if subagent_arch_text:
        (stage_dir / "协作架构.md").write_text(subagent_arch_text, encoding="utf-8")
    if enhancement_guide_text:
        (stage_dir / "增强指南.md").write_text(enhancement_guide_text, encoding="utf-8")
    (stage_dir / "协作角色.json").write_text(
        json.dumps(step.get("subagents", []), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    review_lines = [
        "# 复核闭环",
        "",
        "1. 主控角色读取任务包、执行协议、工作指南和协作角色清单。",
        "2. 执行角色只处理当前工作范围，并把证据写入工作区。",
        "3. 质量复核先逐项检查门禁，再由主控角色运行门禁校验。",
        "4. 任一产物或门禁不完整时，在当前工作内返工，不得提前推进。",
        "5. 仅在校验、门禁和检查点全部通过后进入下一项工作。",
        "",
        "## 当前门禁",
    ]
    review_lines.extend(f"- {gate}" for gate in step.get("gates", []))
    review_lines.extend(
        [
            "",
            f"## Phase Notes: {state['phase']}",
            "- `baseline`: preserve stage protocols, outputs, and stage boundaries exactly.",
            "- `enhancement`: keep the baseline baseline intact, but tighten evidence, critique, and recovery loops.",
        ]
    )
    (stage_dir / "复核闭环.md").write_text("\n".join(review_lines), encoding="utf-8")

    summary_lines = [
        f"# {step['stage_id']} {step['display_name']}",
        "",
        f"- phase: {state['phase']}",
        f"- skill_name: {step['skill_name']}",
        f"- checkpoint_type: {step.get('checkpoint_type') or 'none'}",
        f"- source_prompt: {step['source_prompt']}",
        f"- stage_guide: {step.get('stage_guide') or '(none)'}",
        f"- outputs: {', '.join(output_files)}",
        "",
        "## Gates",
    ]
    summary_lines.extend(f"- {gate}" for gate in step.get("gates", []))
    summary_lines.append("")
    summary_lines.append("## Subagents")
    if step.get("subagents"):
        summary_lines.extend(f"- {item['name']}: {item['objective']}" for item in step["subagents"])
    else:
        summary_lines.append("- (none)")
    (workspace / "当前工作.md").write_text("\n".join(summary_lines), encoding="utf-8")


def ensure_previous_completed(state: dict[str, Any], stage_id: str) -> None:
    for step_state in state["steps"]:
        if step_state["stage_id"] == stage_id:
            return
        if step_state["status"] != "completed":
            raise SystemExit(
                f"Cannot start {stage_id}: previous stage {step_state['stage_id']} is {step_state['status']}."
            )


def artifact_issues(workspace: Path, state: dict[str, Any], step: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    output_files, minimums = stage_output_contract(state, step)
    for rel in output_files:
        path = workspace / rel
        minimum = minimums.get(rel, 1)
        if not path.exists():
            issues.append(f"missing:{rel}")
            continue
        if path.stat().st_size < minimum:
            issues.append(f"too_small:{rel}:{path.stat().st_size}<{minimum}")
    for rel in step.get("companion_files", []):
        path = workspace / rel
        minimum = 1 if rel == "依赖清单.txt" else 50
        if not path.exists():
            issues.append(f"missing:{rel}")
            continue
        if path.stat().st_size < minimum:
            issues.append(f"too_small:{rel}:{path.stat().st_size}<{minimum}")
    return issues


def record_gate(state: dict[str, Any], workspace: Path, step: dict[str, Any], passed: bool, issues: list[str]) -> dict[str, Any]:
    step_state = get_step_state(state, step["stage_id"])
    assert step_state is not None
    report = {
        "passed": passed,
        "issues": issues,
        "checked_at": state["updated_at"]
    }
    step_state["last_gate"] = report
    save_state(workspace, state)
    append_event(workspace, "gate_check", {"stage_id": step["stage_id"], "passed": passed, "issues": issues})
    return report


def cmd_current(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    step = resolve_stage(state["current_stage_id"])
    step_state = get_step_state(state, step["stage_id"])
    assert step_state is not None
    payload = {
        "phase": state["phase"],
        "workflow_status": state["workflow_status"],
        "current_stage_id": step["stage_id"],
        "skill_name": step["skill_name"],
        "display_name": step["display_name"],
        "status": step_state["status"],
        "stage_guide": step.get("stage_guide"),
        "source_prompt": step["source_prompt"],
        "checkpoint_type": step.get("checkpoint_type"),
        "subagents": step.get("subagents", [])
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def cmd_begin(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    step = resolve_stage(args.stage)
    ensure_previous_completed(state, step["stage_id"])
    if (
        step["stage_id"] == "ASSURANCE"
        and state.get("quality_mode") == "championship"
        and state.get("championship_review", {}).get("status") != "completed"
    ):
        raise SystemExit(
            "Championship review is incomplete. Run championship_review.py before ASSURANCE."
        )
    if state.get("active_checkpoint"):
        raise SystemExit("An active checkpoint exists. Resolve it before starting another stage.")

    prepare_stage_resources(workspace, state, step)
    step_state = get_step_state(state, step["stage_id"])
    assert step_state is not None
    step_state["status"] = "running"
    step_state["attempts"] += 1
    if step_state["started_at"] is None:
        step_state["started_at"] = state["updated_at"]
    state["workflow_status"] = "running"
    state["current_stage_id"] = step["stage_id"]
    write_stage_packet(workspace, state, step)
    save_state(workspace, state)
    append_event(
        workspace,
        "begin",
        {
            "stage_id": step["stage_id"],
            "skill_name": step["skill_name"],
            "source_prompt": step["source_prompt"],
            "stage_guide": step.get("stage_guide"),
        }
    )

    print(f"[begin] {step['stage_id']} {step['skill_name']} -> {step['display_name']}")
    print(f"[begin] source_prompt: {step['source_prompt']}")
    outputs, _ = stage_output_contract(state, step)
    print(f"[begin] output_files: {', '.join(outputs)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    step = resolve_stage(args.stage)
    issues = artifact_issues(workspace, state, step)
    result = {
        "stage_id": step["stage_id"],
        "skill_name": step["skill_name"],
        "passed": not issues,
        "issues": issues
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


def cmd_gate_check(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    step = resolve_stage(args.stage)
    report = run_gate_check(workspace, step["stage_id"])
    passed = bool(report["passed"])
    step_state = get_step_state(state, step["stage_id"])
    assert step_state is not None
    step_state["last_gate"] = {
        "passed": passed,
        "issues": report["issues"],
        "warnings": report.get("warnings", []),
        "checks": report.get("checks", []),
        "checked_at": state["updated_at"]
    }
    gate_dir = workspace / "审查" / "门禁"
    gate_dir.mkdir(parents=True, exist_ok=True)
    (gate_dir / f"{step['display_name']}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    save_state(workspace, state)
    append_event(workspace, "gate_check", {"stage_id": step["stage_id"], "passed": passed, "issues": report["issues"], "warnings": report.get("warnings", [])})
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


def advance_after_completion(state: dict[str, Any], step: dict[str, Any]) -> None:
    next_def = next_step(step["stage_id"])
    if next_def is None:
        state["workflow_status"] = "completed"
        state["current_stage_id"] = step["stage_id"]
        return
    state["workflow_status"] = "ready"
    state["current_stage_id"] = next_def["stage_id"]
    next_state = get_step_state(state, next_def["stage_id"])
    assert next_state is not None
    if next_state["status"] == "pending":
        next_state["status"] = "ready"


def reset_step_runtime(step_state: dict[str, Any], reason: str, keep_rework_count: bool = False) -> None:
    step_state["status"] = "pending"
    step_state["completed_at"] = None
    step_state["artifacts"] = []
    step_state["last_gate"] = None
    if not keep_rework_count:
        step_state["reworks"] += 1
    step_state["notes"].append(reason)


def invalidate_downstream(workspace: Path, state: dict[str, Any], stage_id: str, reason: str) -> list[str]:
    impacted: list[str] = []
    seen_target = False
    for step_def in ordered_steps():
        step_state = get_step_state(state, step_def["stage_id"])
        assert step_state is not None
        if step_def["stage_id"] == stage_id:
            seen_target = True
            reset_step_runtime(step_state, reason)
            impacted.append(step_def["stage_id"])
            continue
        if not seen_target:
            continue
        if step_state["status"] in {"completed", "ready", "running", "waiting_checkpoint"}:
            reset_step_runtime(step_state, f"invalidated by upstream rework: {stage_id}", keep_rework_count=True)
            impacted.append(step_def["stage_id"])
        elif step_state["status"] == "pending":
            step_state["notes"].append(f"upstream rework requires rerun from {stage_id}")
            impacted.append(step_def["stage_id"])

    gate_dir = workspace / "审查" / "门禁"
    for impacted_stage in impacted:
        impacted_def = find_step(impacted_stage)
        gate_name = impacted_def["display_name"] if impacted_def else impacted_stage
        gate_file = gate_dir / f"{gate_name}.json"
        if gate_file.exists():
            gate_file.unlink()
    return impacted


def cmd_complete(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    step = resolve_stage(args.stage)
    step_state = get_step_state(state, step["stage_id"])
    assert step_state is not None
    last_gate = step_state.get("last_gate")
    if not last_gate or not last_gate.get("passed"):
        raise SystemExit("Gate check has not passed for this stage.")

    artifacts = [item.strip() for item in args.artifacts.split(",") if item.strip()]
    step_state["artifacts"] = artifacts

    if step.get("checkpoint_type"):
        checkpoint = {
            "stage_id": step["stage_id"],
            "skill_name": step["skill_name"],
            "checkpoint_type": step["checkpoint_type"],
            "artifacts": artifacts
        }
        state["active_checkpoint"] = checkpoint
        state["workflow_status"] = "paused"
        step_state["status"] = "waiting_checkpoint"
        save_state(workspace, state)
        append_event(workspace, "checkpoint_opened", checkpoint)
        print(json.dumps(checkpoint, ensure_ascii=False, indent=2))
        return 0

    step_state["status"] = "completed"
    step_state["completed_at"] = state["updated_at"]
    advance_after_completion(state, step)
    save_state(workspace, state)
    append_event(workspace, "completed", {"stage_id": step["stage_id"], "artifacts": artifacts})
    print(f"[complete] {step['stage_id']} completed")
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    step = resolve_stage(args.stage)
    step_state = get_step_state(state, step["stage_id"])
    assert step_state is not None
    active = state.get("active_checkpoint")
    if not active or active.get("stage_id") != step["stage_id"]:
        raise SystemExit("No active checkpoint for this stage.")

    resolution = {"action": args.action, "note": args.note}
    step_state["checkpoint_history"].append(resolution)
    state["active_checkpoint"] = None

    if args.action == "rerun":
        reset_step_runtime(step_state, f"checkpoint rerun: {args.note or 'no note'}")
        gate_file = workspace / "审查" / "门禁" / f"{step['display_name']}.json"
        if gate_file.exists():
            gate_file.unlink()
        state["workflow_status"] = "paused"
        save_state(workspace, state)
        append_event(workspace, "checkpoint_rerun", {"stage_id": step["stage_id"], "note": args.note})
        print(f"[checkpoint] {step['stage_id']} -> rerun")
        return 0

    step_state["status"] = "completed"
    step_state["completed_at"] = state["updated_at"]
    advance_after_completion(state, step)
    save_state(workspace, state)
    append_event(workspace, "checkpoint_resolved", {"stage_id": step["stage_id"], "action": args.action, "note": args.note})
    print(f"[checkpoint] {step['stage_id']} -> {args.action}")
    return 0


def cmd_rework(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    step = resolve_stage(args.stage)
    impacted = invalidate_downstream(workspace, state, step["stage_id"], args.reason)
    state["workflow_status"] = "paused"
    state["current_stage_id"] = step["stage_id"]
    state["active_checkpoint"] = None
    save_state(workspace, state)
    append_event(workspace, "rework", {"stage_id": step["stage_id"], "reason": args.reason, "invalidated": impacted})
    print(f"[rework] {step['stage_id']} -> {args.reason}")
    if impacted:
        print(f"[rework] invalidated downstream: {', '.join(impacted)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Meta-model-agent evidence-driven research stage machine.")
    sub = parser.add_subparsers(dest="command", required=True)

    current = sub.add_parser("current")
    current.add_argument("--workspace", default=".")
    current.set_defaults(func=cmd_current)

    status = sub.add_parser("status")
    status.add_argument("--workspace", default=".")
    status.set_defaults(func=cmd_status)

    begin = sub.add_parser("begin")
    begin.add_argument("stage")
    begin.add_argument("--workspace", default=".")
    begin.set_defaults(func=cmd_begin)

    validate = sub.add_parser("validate")
    validate.add_argument("stage")
    validate.add_argument("--workspace", default=".")
    validate.set_defaults(func=cmd_validate)

    gate = sub.add_parser("gate_check")
    gate.add_argument("stage")
    gate.add_argument("--workspace", default=".")
    gate.set_defaults(func=cmd_gate_check)

    complete = sub.add_parser("complete")
    complete.add_argument("stage")
    complete.add_argument("--workspace", default=".")
    complete.add_argument("--artifacts", default="")
    complete.set_defaults(func=cmd_complete)

    checkpoint = sub.add_parser("checkpoint")
    checkpoint.add_argument("stage")
    checkpoint.add_argument("--workspace", default=".")
    checkpoint.add_argument("--action", choices=["approve", "feedback", "rerun"], required=True)
    checkpoint.add_argument("--note", default="")
    checkpoint.set_defaults(func=cmd_checkpoint)

    rework = sub.add_parser("rework")
    rework.add_argument("stage")
    rework.add_argument("--workspace", default=".")
    rework.add_argument("--reason", required=True)
    rework.set_defaults(func=cmd_rework)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
