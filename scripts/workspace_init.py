from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from manifest import SKILL_ROOT, competition_profile, load_competition_profiles, load_manifest
from state_store import ensure_workspace_dirs, init_state


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a Meta-model-agent mathematical modeling research workspace.")
    parser.add_argument("--workspace", default=".", help="Target workspace directory. Default: current directory.")
    parser.add_argument("--title", default="Meta-model-agent", help="Human-readable workflow title.")
    parser.add_argument("--competition", choices=sorted(load_competition_profiles()), default="cumcm", help="Strict competition template/profile.")
    parser.add_argument("--output-format", choices=["pdf", "docx"], default="pdf", help="Final paper artifact format.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing 工作流状态.json.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    ensure_workspace_dirs(workspace)
    copy_tree(SKILL_ROOT / "assets" / "shared-scripts", workspace / "工具")
    shutil.copy2(SKILL_ROOT / "scripts" / "docx_export.py", workspace / "工具" / "docx_export.py")
    shutil.copy2(SKILL_ROOT / "scripts" / "build_code_appendix.py", workspace / "工具" / "build_code_appendix.py")
    profile = competition_profile(args.competition)
    template_source = SKILL_ROOT / "assets" / "templates" / "manuscript-synthesis" / profile["template_dir"]
    copy_tree(template_source, workspace / "模板" / "当前竞赛")
    if args.output_format == "docx":
        copy_tree(SKILL_ROOT / "assets" / "templates" / "docx" / args.competition, workspace / "模板" / "当前竞赛")
    state = init_state(workspace, title=args.title, competition=args.competition, output_format=args.output_format, force=args.force)

    print(f"[init] workspace: {workspace}")
    print(f"[init] phase: {state['phase']}")
    print(f"[init] competition: {state['competition']} ({state['display_name']})")
    print(f"[init] output format: {state['output_format']}")
    print(f"[init] current stage: {state['current_stage_id']}")
    print("[init] directories:")
    for rel in load_manifest()["workspace_dirs"]:
        print(f"  - {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
