#!/usr/bin/env python3
"""Workspace Sync — DEPRECATED (v2.0)

此脚本已被 skill_deployer.py 取代。

旧功能：将技能资产同步到 CUMCM_Workspace/_skill/
新方案：使用 skill_deployer.py 进行完整部署

迁移指南：
  旧: python CUMCM_Workspace/_skill/scripts/workspace_sync.py full
  新: python scripts/skill_deployer.py deploy

该脚本保留用于向后兼容，但不推荐使用。
"""
import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from workspace_utils import resolve_skill_root
# Default SKILL_ROOT for CLI mode (when functions called without explicit param)
SKILL_ROOT = resolve_skill_root()


def _deprecated_warning():
    """打印废弃警告。"""
    print("[workspace_sync] ⚠️  DEPRECATED: 此脚本已被 skill_deployer.py 取代")
    print("  推荐使用: python scripts/skill_deployer.py deploy")
    print()




def sync_scripts(skill_root: Path = None, workspace: Path = None) -> int:
    """同步 scripts/*.py 到 _skill/scripts/。"""
    _deprecated_warning()
    src = (skill_root or SKILL_ROOT) / "scripts"
    if not src.is_dir():
        print(f"[workspace_sync] scripts/ 目录不存在: {src}")
        return 0

    ws = workspace or Path("CUMCM_Workspace")
    dst = ws / "_skill" / "scripts"
    dst.mkdir(parents=True, exist_ok=True)

    count = 0
    total_size = 0
    for f in sorted(src.iterdir()):
        if f.is_file() and f.suffix == ".py" and not f.name.startswith("__"):
            data = f.read_bytes()
            (dst / f.name).write_bytes(data)
            count += 1
            total_size += len(data)

    print(f"[workspace_sync] 同步脚本 {count} 个到 {dst}/ ({total_size:,} bytes)")
    return count


def sync_stages(skill_root: Path = None, workspace: Path = None) -> int:
    """同步 stages/*.md 到 _skill/stages/。"""
    src = (skill_root or SKILL_ROOT) / "stages"
    if not src.is_dir():
        print(f"[workspace_sync] stages/ 目录不存在: {src}")
        return 0

    ws = workspace or Path("CUMCM_Workspace")
    dst = ws / "_skill" / "stages"
    dst.mkdir(parents=True, exist_ok=True)

    count = 0
    total_size = 0
    for f in sorted(src.iterdir()):
        if f.is_file() and f.suffix == ".md":
            data = f.read_bytes()
            (dst / f.name).write_bytes(data)
            count += 1
            total_size += len(data)

    print(f"[workspace_sync] 同步阶段指令 {count} 个到 {dst}/ ({total_size:,} bytes)")
    return count


def sync_config(skill_root: Path = None, workspace: Path = None) -> int:
    """同步 config/*.yaml 到 _skill/config/。"""
    src = (skill_root or SKILL_ROOT) / "config"
    if not src.is_dir():
        print(f"[workspace_sync] config/ 目录不存在: {src}")
        return 0

    ws = workspace or Path("CUMCM_Workspace")
    dst = ws / "_skill" / "config"
    dst.mkdir(parents=True, exist_ok=True)

    count = 0
    total_size = 0
    for f in sorted(src.rglob("*")):
        if f.is_file():
            rel = f.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            data = f.read_bytes()
            target.write_bytes(data)
            count += 1
            total_size += len(data)

    print(f"[workspace_sync] 同步配置 {count} 个到 {dst}/ ({total_size:,} bytes)")
    return count


def sync_refs(skill_root: Path = None, workspace: Path = None) -> int:
    """同步核心 references/*.md + *.json 到 _skill/references/（不含子目录）。"""
    src = (skill_root or SKILL_ROOT) / "references"
    if not src.is_dir():
        print(f"[workspace_sync] references/ 目录不存在: {src}")
        return 0

    ws = workspace or Path("CUMCM_Workspace")
    dst = ws / "_skill" / "references"
    dst.mkdir(parents=True, exist_ok=True)

    count = 0
    total_size = 0
    for f in sorted(src.iterdir()):
        if f.is_dir():
            continue  # 跳过子目录
        if f.suffix in (".md", ".json"):
            data = f.read_bytes()
            (dst / f.name).write_bytes(data)
            count += 1
            total_size += len(data)

    print(f"[workspace_sync] 同步引用文件 {count} 个到 {dst}/ ({total_size:,} bytes)")
    return count


def sync_algorithm_lib(skill_root: Path = None, workspace: Path = None) -> int:
    """按需同步 algorithm-library/ 到 _skill/references/algorithm-library/。"""
    src = (skill_root or SKILL_ROOT) / "references" / "algorithm-library"
    if not src.is_dir():
        print(f"[workspace_sync] algorithm-library/ 目录不存在: {src}")
        return 0

    ws = workspace or Path("CUMCM_Workspace")
    dst = ws / "_skill" / "references" / "algorithm-library"
    dst.mkdir(parents=True, exist_ok=True)

    count = 0
    total_size = 0
    for f in sorted(src.rglob("*")):
        if f.is_file():
            rel = f.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            data = f.read_bytes()
            target.write_bytes(data)
            count += 1
            total_size += len(data)

    print(f"[workspace_sync] 同步算法库 {count} 个到 {dst}/ ({total_size:,} bytes)")
    return count


def sync_templates(skill_root: Path = None, workspace: Path = None) -> int:
    """同步 templates/ 到 _skill/templates/。"""
    src = skill_root or SKILL_ROOT
    templates_src = src / "templates"
    if not templates_src.is_dir():
        print(f"[workspace_sync] templates/ 目录不存在: {templates_src}")
        return 0

    ws = workspace or Path("CUMCM_Workspace")
    dst = ws / "_skill" / "templates"
    dst.mkdir(parents=True, exist_ok=True)

    count = 0
    total_size = 0
    for f in sorted(templates_src.rglob("*")):
        if f.is_file() and f.suffix in (".md", ".json", ".yaml", ".yml"):
            rel = f.relative_to(templates_src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            data = f.read_bytes()
            target.write_bytes(data)
            count += 1
            total_size += len(data)

    print(f"[workspace_sync] 同步模板 {count} 个到 {dst}/ ({total_size:,} bytes)")
    return count


def check_sync(workspace: Path = None) -> bool:
    """检查 _skill/ 部署完整性。"""
    ws = workspace or Path("CUMCM_Workspace")
    skill_dir = ws / "_skill"

    if not skill_dir.exists():
        print(f"[workspace_sync] _skill/ 不存在 — 需要部署")
        return False

    checks = {
        "scripts": skill_dir / "scripts",
        "stages": skill_dir / "stages",
        "references": skill_dir / "references",
        "config": skill_dir / "config",
    }

    all_ok = True
    for name, path in checks.items():
        if not path.is_dir():
            print(f"  [MISSING] {name}/")
            all_ok = False
        else:
            count = sum(1 for _ in path.rglob("*") if _.is_file())
            print(f"  [OK] {name}/: {count} files")

    manifest = skill_dir / "manifest.json"
    if manifest.exists():
        print(f"  [OK] manifest.json exists")
    else:
        print(f"  [MISSING] manifest.json")
        all_ok = False

    return all_ok


def main():
    _deprecated_warning()
    
    p = argparse.ArgumentParser(description="Workspace Sync — 同步技能资产到工作区 (DEPRECATED)")
    p.add_argument("command",
                    choices=["scripts", "stages", "refs", "algo", "templates", "config", "full", "check"],
                    help="同步命令")
    p.add_argument("--workspace", default="CUMCM_Workspace", help="工作区路径")
    p.add_argument("--skill-root", default=None, help="SKILL_ROOT 路径（默认自动检测）")
    args = p.parse_args()

    skill_root = Path(args.skill_root) if args.skill_root else SKILL_ROOT
    workspace = Path(args.workspace)

    if args.command == "scripts":
        sync_scripts(skill_root, workspace)
    elif args.command == "stages":
        sync_stages(skill_root, workspace)
    elif args.command == "refs":
        sync_refs(skill_root, workspace)
    elif args.command == "algo":
        sync_algorithm_lib(skill_root, workspace)
    elif args.command == "templates":
        sync_templates(skill_root, workspace)
    elif args.command == "config":
        sync_config(skill_root, workspace)
    elif args.command == "full":
        print("  建议直接使用: python scripts/skill_deployer.py deploy")
        print()
        sync_scripts(skill_root, workspace)
        sync_stages(skill_root, workspace)
        sync_refs(skill_root, workspace)
        sync_algorithm_lib(skill_root, workspace)
        sync_templates(skill_root, workspace)
        sync_config(skill_root, workspace)
        print("[workspace_sync] 全量同步完成")
    elif args.command == "check":
        ok = check_sync(workspace)
        sys.exit(0 if ok else 1)



if __name__ == "__main__":
    main()
