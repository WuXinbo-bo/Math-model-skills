#!/usr/bin/env python3
"""Workspace Initializer — 在用户项目目录中创建 CUMCM_Workspace 完整目录结构。

用法:
  python CUMCM_Workspace/_skill/scripts/workspace_init.py                          # 创建默认工作区
  python CUMCM_Workspace/_skill/scripts/workspace_init.py --path /path/to/project  # 指定项目路径
  python CUMCM_Workspace/_skill/scripts/workspace_init.py --subquestions 3          # 按子问题数创建 q1/q2/q3
  python CUMCM_Workspace/_skill/scripts/workspace_init.py --check                   # 检查目录完整性
  python CUMCM_Workspace/_skill/scripts/workspace_init.py --contest CUMCM           # 指定竞赛类型
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Required directory structure for all 14 stages
REQUIRED_DIRS = [
    # S0
    "inputs",
    # S1
    "outputs/problem_analysis",
    "outputs/reviews",
    "outputs/figures",
    # S2
    "data",
    "data/raw",
    "data/processed",
    # S3
    "methods",
    "methods/experiments",
    # S5.5
    "outputs/evolution",
    # S6
    "outputs/verification",
    # S7
    "outputs/evidence",
    # S7.5
    "outputs/kernel",
    # S8
    "outputs/paper",
    # S9
    "outputs/review",
    # S10
    "outputs/final",
    # State (core)
    "state",
    # Memory / evaluation logs
    "memory",
    # Models (S5.5 evolution)
    "models/evolution",
    # Appendix (S10)
    "appendix",
    # Scripts output
    "outputs/tables",
    # Literature (S1)
    "outputs/literature",
]


def ensure_workspace(base: Path, subquestions: int = 3, contest: str = "CUMCM") -> Path:
    """Create full workspace directory structure."""
    ws = base / "CUMCM_Workspace"

    # Create all required directories
    for d in REQUIRED_DIRS:
        (ws / d).mkdir(parents=True, exist_ok=True)

    # Create subquestion output dirs (dynamic based on subquestion count)
    for q in range(1, subquestions + 1):
        (ws / f"outputs/q{q}").mkdir(parents=True, exist_ok=True)

    # Create initial workflow_state.json if not present
    state_file = ws / "state" / "workflow_state.json"
    if not state_file.exists():
        state_file.write_text(json.dumps({
            "version": "1.0.0",
            "contest": contest.upper(),
            "subquestions": subquestions,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_stage": None,
            "stages": {},
        }, indent=2, ensure_ascii=False), encoding="utf-8")

    # Deploy skill assets to _skill/ (MANDATORY for AI to access scripts/stages/references)
    print("[workspace_init] 正在部署技能资产到 _skill/...")
    try:
        from skill_deployer import deploy_skill
        deploy_skill(project_root=base, force=False)
        print("[workspace_init] 技能资产部署完成")
    except Exception as e:
        print(f"[workspace_init] WARNING: 技能资产部署失败: {e}")
        print("  请手动运行: python scripts/skill_deployer.py deploy")

    return ws



def check_workspace(base: Path) -> dict:
    """Check workspace completeness, return dict of status."""
    ws = base / "CUMCM_Workspace"
    results = {"exists": ws.exists(), "missing_dirs": [], "missing_files": []}

    if not ws.exists():
        results["missing_dirs"] = REQUIRED_DIRS[:]
        return results

    for d in REQUIRED_DIRS:
        if not (ws / d).is_dir():
            results["missing_dirs"].append(d)

    state_file = ws / "state" / "workflow_state.json"
    if not state_file.exists():
        results["missing_files"].append("state/workflow_state.json")

    return results


def main():
    p = argparse.ArgumentParser(description="Workspace Initializer — 创建 CUMCM_Workspace 完整目录结构")
    p.add_argument("--path", default=".", help="Project root (default: cwd)")
    p.add_argument("--subquestions", type=int, default=3, help="Number of subquestions (default: 3)")
    p.add_argument("--contest", default="CUMCM", help="Competition type (default: CUMCM)")
    p.add_argument("--check", action="store_true", help="Only check completeness, do not create")
    p.add_argument("--force", action="store_true", help="Recreate even if exists")
    args = p.parse_args()

    from workspace_utils import resolve_project_root
    base = Path(args.path).resolve() if args.path != "." else resolve_project_root()

    if args.check:
        results = check_workspace(base)
        if results["exists"] and not results["missing_dirs"] and not results["missing_files"]:
            print("[workspace_init] Workspace complete at CUMCM_Workspace/")
            sys.exit(0)
        else:
            print("[workspace_init] Workspace incomplete:")
            if not results["exists"]:
                print("  CUMCM_Workspace/ directory does not exist")
            if results["missing_dirs"]:
                print(f"  Missing {len(results['missing_dirs'])} directories:")
                for d in results["missing_dirs"]:
                    print(f"    - {d}")
            if results["missing_files"]:
                print(f"  Missing files: {results['missing_files']}")
            sys.exit(1)

    ws = ensure_workspace(base, args.subquestions, args.contest)
    print(f"[workspace_init] Workspace created at {ws}")
    print(f"  Contest: {args.contest.upper()}")
    print(f"  Subquestions: {args.subquestions}")
    print(f"  Directories: {len(REQUIRED_DIRS) + args.subquestions} created")
    print(f"  Next step: python CUMCM_Workspace/_skill/scripts/stage_executor.py init --contest {args.contest} --subquestions {args.subquestions}")


if __name__ == "__main__":
    main()
