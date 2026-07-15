from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from manifest import SKILL_ROOT, load_manifest
from state_store import append_event, get_step_state, load_state, now_iso, save_state


PERSPECTIVES = {
    "mathematical": "数学与模型严谨性",
    "evidence": "证据链与可复现性",
    "judge": "竞赛评委与表达质量",
    "domain": "领域常识与反例攻击",
    "publication": "出版就绪与提交合规",
}
REQUIRED_ORDER = ["mathematical", "evidence", "judge"]


def workspace_path(raw: str) -> Path:
    return Path(raw).resolve()


def review_config() -> dict[str, Any]:
    return load_manifest()["quality_modes"]["championship"]


def require_state(workspace: Path) -> dict[str, Any]:
    path = workspace / "状态" / "工作流状态.json"
    if not path.exists():
        raise SystemExit("Missing workflow state. Run workspace_init.py first.")
    return load_state(workspace)


def require_championship(state: dict[str, Any]) -> None:
    if state.get("quality_mode") != "championship":
        raise SystemExit(
            "Championship mode is not active. Run pipeline_manager.py set-mode championship."
        )


def safe_workspace_file(workspace: Path, raw: str, minimum: int = 1) -> Path:
    path = (workspace / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    try:
        path.relative_to(workspace)
    except ValueError as exc:
        raise SystemExit(f"Review artifact must stay inside the workspace: {path}") from exc
    if not path.exists() or not path.is_file():
        raise SystemExit(f"Missing review artifact: {path}")
    if path.stat().st_size < minimum:
        raise SystemExit(f"Review artifact is too small: {path} < {minimum} bytes")
    return path


def round_dir(workspace: Path, number: int) -> Path:
    return workspace / "审查" / "冠军模式" / f"第{number:02d}轮"


def review_state_path(workspace: Path) -> Path:
    return workspace / "状态" / "冠军审稿.json"


def persist_review_state(workspace: Path, state: dict[str, Any]) -> None:
    review = state.setdefault("championship_review", {})
    review_state_path(workspace).write_text(
        json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    save_state(workspace, state)


def manuscript_completed(state: dict[str, Any]) -> bool:
    step = get_step_state(state, "MANUSCRIPT")
    return bool(step and step.get("status") == "completed")


def manuscript_relpath(state: dict[str, Any]) -> str:
    return "论文/论文正文.md" if state.get("output_format") == "docx" else "论文/论文正文.tex"


def manuscript_extension(state: dict[str, Any]) -> str:
    return ".md" if state.get("output_format") == "docx" else ".tex"


def latest_paper(workspace: Path, state: dict[str, Any]) -> Path:
    rounds = state.get("championship_review", {}).get("rounds", [])
    if rounds:
        return safe_workspace_file(workspace, rounds[-1]["论文"], minimum=5000)
    return safe_workspace_file(workspace, manuscript_relpath(state), minimum=5000)


def cmd_init(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    require_championship(state)
    if not manuscript_completed(state):
        raise SystemExit("MANUSCRIPT must be completed before championship review.")
    safe_workspace_file(workspace, manuscript_relpath(state), minimum=5000)
    review = state.setdefault("championship_review", {})
    if review.get("status") == "completed" and not args.force:
        print("[championship-review] already completed")
        return 0
    review.update(
        {
            "status": "in_progress",
            "rounds": [] if args.force or not review.get("rounds") else review["rounds"],
            "final_score": None,
            "final_paper": None,
            "completed_at": None,
            "started_at": review.get("started_at") or now_iso(),
        }
    )
    (workspace / "审查" / "冠军模式").mkdir(parents=True, exist_ok=True)
    protocol_dir = workspace / "审查" / "冠军模式" / "审稿协议"
    protocol_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        SKILL_ROOT / "references" / "stage_protocols" / "championship-review" / "SKILL.md",
        protocol_dir / "冠军审稿说明.md",
    )
    shutil.copy2(
        SKILL_ROOT / "references" / "championship-review-method.md",
        protocol_dir / "审稿方法.md",
    )
    persist_review_state(workspace, state)
    append_event(workspace, "championship_review_init", {"force": args.force})
    print("[championship-review] initialized")
    print("[next] start round 1 with perspective mathematical")
    return 0


def cmd_start_round(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    require_championship(state)
    review = state.get("championship_review", {})
    if review.get("status") not in {"in_progress", "needs_rework"}:
        raise SystemExit("Initialize championship review before starting a round.")
    config = review_config()
    if args.round < 1 or args.round > config["maximum_rounds"]:
        raise SystemExit(f"Round must be between 1 and {config['maximum_rounds']}.")
    recorded = review.get("rounds", [])
    if args.round != len(recorded) + 1:
        raise SystemExit(f"Expected round {len(recorded) + 1}, got {args.round}.")
    if args.round <= len(REQUIRED_ORDER) and args.perspective != REQUIRED_ORDER[args.round - 1]:
        raise SystemExit(
            f"Round {args.round} must use perspective {REQUIRED_ORDER[args.round - 1]}."
        )
    source = latest_paper(workspace, state)
    target = round_dir(workspace, args.round)
    target.mkdir(parents=True, exist_ok=True)
    brief = [
        f"# 冠军审稿第 {args.round} 轮",
        "",
        f"- 审稿视角：{PERSPECTIVES[args.perspective]}",
        f"- 待审论文：`{source.relative_to(workspace).as_posix()}`",
        "- 知识库：`references/championship-review-method.md`",
        "",
        "## 必须产出",
        "",
        "- `审稿报告.md`：分维度评分及带位置的 P0/P1/P2 问题清单",
        "- `修订计划.md`：问题、证据、修改动作与验收方式",
        f"- `修订论文{manuscript_extension(state)}`：完整修订论文",
        "- `修订复核.md`：逐项复核和剩余风险",
        "",
        "审稿者不得修改论文；修改者不得自行宣布问题已修复；复核者必须重新阅读完整修订稿。",
    ]
    (target / "审稿任务.md").write_text("\n".join(brief) + "\n", encoding="utf-8")
    append_event(
        workspace,
        "championship_round_started",
        {"round": args.round, "perspective": args.perspective, "source": str(source)},
    )
    print(f"[round {args.round}] packet: {target / '审稿任务.md'}")
    return 0


def cmd_record_round(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    require_championship(state)
    review = state.get("championship_review", {})
    recorded = review.get("rounds", [])
    if args.round != len(recorded) + 1:
        raise SystemExit(f"Expected round {len(recorded) + 1}, got {args.round}.")
    directory = round_dir(workspace, args.round)
    brief = safe_workspace_file(workspace, str(directory / "审稿任务.md"), minimum=100)
    brief_text = brief.read_text(encoding="utf-8")
    perspective = next(
        (key for key, label in PERSPECTIVES.items() if label in brief_text), "unknown"
    )
    paper = safe_workspace_file(workspace, args.paper, minimum=5000)
    report = safe_workspace_file(workspace, args.review, minimum=200)
    plan = safe_workspace_file(workspace, args.plan, minimum=150)
    verification = safe_workspace_file(workspace, args.verification, minimum=150)
    expected_dir = directory.resolve()
    for artifact in (paper, report, plan, verification):
        if artifact.parent != expected_dir:
            raise SystemExit(f"Round artifacts must be stored in {expected_dir}: {artifact}")
    entry = {
        "round": args.round,
        "perspective": perspective,
        "score": args.score,
        "p0": args.p0,
        "p1": args.p1,
        "p2": args.p2,
        "论文": paper.relative_to(workspace).as_posix(),
        "review": report.relative_to(workspace).as_posix(),
        "revision_plan": plan.relative_to(workspace).as_posix(),
        "verification": verification.relative_to(workspace).as_posix(),
        "recorded_at": now_iso(),
    }
    review.setdefault("rounds", []).append(entry)
    review["status"] = "in_progress"
    persist_review_state(workspace, state)
    append_event(workspace, "championship_round_recorded", entry)
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    payload = {
        "quality_mode": state.get("quality_mode", "standard"),
        "championship_review": state.get("championship_review", {}),
        "requirements": review_config(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    state = require_state(workspace)
    require_championship(state)
    config = review_config()
    review = state.get("championship_review", {})
    rounds = review.get("rounds", [])
    if len(rounds) < config["minimum_rounds"]:
        raise SystemExit(
            f"At least {config['minimum_rounds']} review rounds are required; got {len(rounds)}."
        )
    final = rounds[-1]
    failures = []
    if final["score"] < config["passing_score"]:
        failures.append(f"score {final['score']} < {config['passing_score']}")
    if final["p0"] > config["maximum_p0"]:
        failures.append(f"P0 {final['p0']} > {config['maximum_p0']}")
    if final["p1"] > config["maximum_p1"]:
        failures.append(f"P1 {final['p1']} > {config['maximum_p1']}")
    if failures:
        review["status"] = "needs_rework"
        persist_review_state(workspace, state)
        raise SystemExit("Championship review gate failed: " + "; ".join(failures))
    source = safe_workspace_file(workspace, final["论文"], minimum=5000)
    paper_dir = workspace / "论文"
    extension = manuscript_extension(state)
    final_path = paper_dir / f"冠军修订稿{extension}"
    shutil.copy2(source, final_path)
    main_path = safe_workspace_file(workspace, manuscript_relpath(state), minimum=5000)
    backup = paper_dir / f"冠军审稿前正文{extension}"
    if not backup.exists():
        shutil.copy2(main_path, backup)
    shutil.copy2(final_path, main_path)
    report_lines = [
        "# 冠军模式多轮审稿总报告",
        "",
        f"- 有效轮次：{len(rounds)}",
        f"- 最终得分：{final['score']}",
        f"- 最终剩余问题：P0={final['p0']}，P1={final['p1']}，P2={final['p2']}",
        f"- 冠军修订稿：`{final_path.relative_to(workspace).as_posix()}`",
        "- 结论：通过，可进入提交质量验收。",
        "",
        "## 轮次记录",
        "",
        "| 轮次 | 视角 | 得分 | P0 | P1 | P2 |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in rounds:
        report_lines.append(
            f"| {item['round']} | {item['perspective']} | {item['score']} | {item['p0']} | {item['p1']} | {item['p2']} |"
        )
    final_report = workspace / "审查" / "冠军模式" / "最终报告.md"
    final_report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    review.update(
        {
            "status": "completed",
            "final_score": final["score"],
            "final_paper": final_path.relative_to(workspace).as_posix(),
            "final_report": final_report.relative_to(workspace).as_posix(),
            "completed_at": now_iso(),
        }
    )
    persist_review_state(workspace, state)
    append_event(
        workspace,
        "championship_review_completed",
        {"rounds": len(rounds), "score": final["score"], "论文": str(final_path)},
    )
    print(f"[championship-review] completed with score {final['score']}")
    print(f"[paper] {final_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage Meta-model-agent championship multi-round paper review."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--workspace", default=".")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    start = sub.add_parser("start-round")
    start.add_argument("--workspace", default=".")
    start.add_argument("--round", type=int, required=True)
    start.add_argument("--perspective", choices=sorted(PERSPECTIVES), required=True)
    start.set_defaults(func=cmd_start_round)

    record = sub.add_parser("record-round")
    record.add_argument("--workspace", default=".")
    record.add_argument("--round", type=int, required=True)
    record.add_argument("--score", type=int, choices=range(0, 101), required=True)
    record.add_argument("--p0", type=int, required=True)
    record.add_argument("--p1", type=int, required=True)
    record.add_argument("--p2", type=int, default=0)
    record.add_argument("--paper", required=True)
    record.add_argument("--review", required=True)
    record.add_argument("--plan", required=True)
    record.add_argument("--verification", required=True)
    record.set_defaults(func=cmd_record_round)

    status = sub.add_parser("status")
    status.add_argument("--workspace", default=".")
    status.set_defaults(func=cmd_status)

    finalize = sub.add_parser("finalize")
    finalize.add_argument("--workspace", default=".")
    finalize.set_defaults(func=cmd_finalize)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
