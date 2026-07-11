from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from baseline_smoke import (
    CHECKPOINT_ACTION,
    GENERATORS,
    PIPELINE_MANAGER,
    STAGE_EXECUTOR,
    WORKSPACE_INIT,
    ensure_exists,
    run,
    write_text,
)


SCRIPT_DIR = Path(__file__).resolve().parent
CHAMPIONSHIP_REVIEW = SCRIPT_DIR / "championship_review.py"


def finish_stage(workspace: Path, stage: str) -> None:
    run(str(STAGE_EXECUTOR), "begin", stage, "--workspace", str(workspace))
    GENERATORS[stage](workspace)
    run(str(STAGE_EXECUTOR), "validate", stage, "--workspace", str(workspace))
    run(str(STAGE_EXECUTOR), "gate_check", stage, "--workspace", str(workspace))
    artifacts = {
        "DISCOVERY": "问题分析.md",
        "FORMULATION": "建模报告.md",
        "COMPUTATION": "程序/主程序.py,计算结果.md,图表/全部结果.json,依赖清单.txt",
        "EVIDENCE": "图表/图表引用.tex,图表/结果总览图.pdf",
        "SCHEMATICS": "图表/图表引用.tex,图表/技术路线图.drawio,图表/技术路线图.pdf",
        "MANUSCRIPT": "论文/论文正文.tex",
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
            "championship smoke",
        )


def create_round(workspace: Path, number: int, perspective: str, score: int, p0: int, p1: int) -> None:
    run(
        str(CHAMPIONSHIP_REVIEW),
        "start-round",
        "--workspace",
        str(workspace),
        "--round",
        str(number),
        "--perspective",
        perspective,
    )
    directory = workspace / "审查" / "冠军模式" / f"第{number:02d}轮"
    source = workspace / "论文" / "论文正文.tex" if number == 1 else workspace / "审查" / "冠军模式" / f"第{number - 1:02d}轮" / "修订论文.tex"
    revised = source.read_text(encoding="utf-8") + f"\n% championship review round {number}\n"
    write_text(directory / "审稿报告.md", (f"# Round {number} review\nP0={p0}, P1={p1}.\n" * 20))
    write_text(directory / "修订计划.md", (f"# Round {number} revision plan\nVerify every issue against evidence.\n" * 15))
    write_text(directory / "修订论文.tex", revised)
    write_text(directory / "修订复核.md", (f"# Round {number} verification\nAll recorded fixes were rechecked.\n" * 15))
    run(
        str(CHAMPIONSHIP_REVIEW),
        "record-round",
        "--workspace",
        str(workspace),
        "--round",
        str(number),
        "--score",
        str(score),
        "--p0",
        str(p0),
        "--p1",
        str(p1),
        "--p2",
        "1",
        "--paper",
        f"审查/冠军模式/第{number:02d}轮/修订论文.tex",
        "--review",
        f"审查/冠军模式/第{number:02d}轮/审稿报告.md",
        "--plan",
        f"审查/冠军模式/第{number:02d}轮/修订计划.md",
        "--verification",
        f"审查/冠军模式/第{number:02d}轮/修订复核.md",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test championship review and paper rewrite.")
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    if workspace.exists():
        shutil.rmtree(workspace)
    run(str(WORKSPACE_INIT), "--workspace", str(workspace), "--force")
    run(str(PIPELINE_MANAGER), "set-mode", "championship", "--workspace", str(workspace))
    for stage in ["DISCOVERY", "FORMULATION", "COMPUTATION", "EVIDENCE", "SCHEMATICS", "MANUSCRIPT"]:
        finish_stage(workspace, stage)
    blocked = run(str(STAGE_EXECUTOR), "begin", "ASSURANCE", "--workspace", str(workspace), check=False)
    if blocked.returncode == 0:
        raise RuntimeError("ASSURANCE should be blocked before championship review completion.")
    run(str(CHAMPIONSHIP_REVIEW), "init", "--workspace", str(workspace))
    create_round(workspace, 1, "mathematical", 78, 0, 5)
    create_round(workspace, 2, "evidence", 83, 0, 3)
    create_round(workspace, 3, "judge", 89, 0, 1)
    run(str(CHAMPIONSHIP_REVIEW), "finalize", "--workspace", str(workspace))
    ensure_exists(workspace / "论文" / "冠军修订稿.tex")
    ensure_exists(workspace / "论文" / "冠军审稿前正文.tex")
    ensure_exists(workspace / "审查" / "冠军模式" / "最终报告.md")
    ensure_exists(workspace / "状态" / "冠军审稿.json")
    run(str(STAGE_EXECUTOR), "begin", "ASSURANCE", "--workspace", str(workspace))
    print('{"championship_review_smoke": "ok"}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
