#!/usr/bin/env python3
"""Skill Asset Deployer v1.0 — 技能资产部署器

将 Meta-model-skills-max 的所有资产从安装目录部署到项目目录，
解决 AI 无法从项目根目录访问技能脚本/阶段文件/参考文件的问题。

部署目标：PROJECT_ROOT/CUMCM_Workspace/_skill/
  ├── scripts/      ← 56+ 个 .py 文件
  ├── stages/       ← 14 个 .md 文件
  ├── references/   ← 27+ 个 .md/.json 文件
  ├── config/       ← 4 个 .yaml 文件
  ├── templates/    ← agent_prompts + meeting_templates
  └── manifest.json ← 部署元数据

Commands:
  python skill_deployer.py deploy [--force] [--skill-root PATH]
  python skill_deployer.py check
  python skill_deployer.py status
  python skill_deployer.py version
"""
import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from workspace_utils import resolve_project_root, resolve_skill_root

VERSION = "1.0.0"


def compute_dir_hash(directory: Path, glob_pattern: str = "**/*") -> str:
    """计算目录下所有文件的 SHA-256 哈希（用于检测变更）。"""
    if not directory.is_dir():
        return ""
    
    hasher = hashlib.sha256()
    files = sorted(directory.glob(glob_pattern))
    
    for f in files:
        if f.is_file() and not f.name.startswith("."):
            hasher.update(f.name.encode())
            hasher.update(f.read_bytes())
    
    return hasher.hexdigest()[:16]


def deploy_skill(skill_root: Path = None, project_root: Path = None, force: bool = False) -> Path:
    """部署技能资产到项目目录。
    
    Args:
        skill_root: 技能安装目录（默认自动检测）
        project_root: 项目根目录（默认自动检测）
        force: 强制重新部署
    
    Returns:
        部署目标目录路径
    """
    skill_root = skill_root or resolve_skill_root()
    project_root = project_root or resolve_project_root()
    
    # 部署目标
    workspace = project_root / "CUMCM_Workspace"
    deploy_target = workspace / "_skill"
    manifest_file = deploy_target / "manifest.json"
    
    print(f"[skill_deployer] 技能根目录: {skill_root}")
    print(f"[skill_deployer] 项目根目录: {project_root}")
    print(f"[skill_deployer] 部署目标: {deploy_target}")
    
    # 检查是否已部署
    if manifest_file.exists() and not force:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        deployed_version = manifest.get("version", "unknown")
        deployed_hash = manifest.get("content_hash", "")
        
        # 计算当前技能的哈希
        current_hash = compute_dir_hash(skill_root / "scripts", "*.py")
        
        if deployed_version == VERSION and deployed_hash == current_hash:
            print(f"[skill_deployer] 已部署（版本 {VERSION}），跳过")
            return deploy_target
        else:
            print(f"[skill_deployer] 检测到版本变化，重新部署...")
    
    # 创建部署目录
    deploy_target.mkdir(parents=True, exist_ok=True)
    
    # 部署各个目录
    dirs_to_deploy = [
        ("scripts", "*.py"),
        ("stages", "*.md"),
        ("references", "*"),
        ("config", "*"),
        ("templates", "*"),
    ]
    
    total_files = 0
    total_size = 0
    deployment_summary = {}
    
    for dir_name, pattern in dirs_to_deploy:
        src_dir = skill_root / dir_name
        dst_dir = deploy_target / dir_name
        
        if not src_dir.is_dir():
            print(f"  [SKIP] {dir_name}/ (不存在)")
            continue
        
        # 清理旧文件
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        dst_dir.mkdir(parents=True, exist_ok=True)
        
        # 递归复制
        file_count = 0
        dir_size = 0
        
        if pattern == "*":
            # 递归复制所有文件
            for src_file in src_dir.rglob("*"):
                if src_file.is_file() and not src_file.name.startswith("."):
                    rel_path = src_file.relative_to(src_dir)
                    dst_file = dst_dir / rel_path
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                    file_count += 1
                    dir_size += src_file.stat().st_size
        else:
            # 只复制匹配的文件
            for src_file in src_dir.rglob(pattern):
                if src_file.is_file():
                    rel_path = src_file.relative_to(src_dir)
                    dst_file = dst_dir / rel_path
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                    file_count += 1
                    dir_size += src_file.stat().st_size
        
        total_files += file_count
        total_size += dir_size
        deployment_summary[dir_name] = {
            "file_count": file_count,
            "size_bytes": dir_size,
        }
        
        print(f"  [OK] {dir_name}/: {file_count} 文件, {dir_size:,} bytes")
    
    # 生成 manifest.json
    manifest = {
        "version": VERSION,
        "deployed_at": datetime.now().isoformat(),
        "skill_root": str(skill_root),
        "project_root": str(project_root),
        "total_files": total_files,
        "total_size": total_size,
        "content_hash": compute_dir_hash(skill_root / "scripts", "*.py"),
        "directories": deployment_summary,
    }
    
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[skill_deployer] 部署完成: {total_files} 文件, {total_size:,} bytes")
    print(f"[skill_deployer] Manifest: {manifest_file}")
    
    return deploy_target


def check_deployment(project_root: Path = None) -> dict:
    """检查部署状态和完整性。"""
    project_root = project_root or resolve_project_root()
    deploy_target = project_root / "CUMCM_Workspace" / "_skill"
    manifest_file = deploy_target / "manifest.json"
    
    if not deploy_target.exists():
        return {
            "deployed": False,
            "message": "未部署（_skill/ 目录不存在）",
        }
    
    if not manifest_file.exists():
        return {
            "deployed": True,
            "complete": False,
            "message": "部署不完整（manifest.json 缺失）",
        }
    
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    
    # 检查必需目录
    required_dirs = ["scripts", "stages", "references", "config"]
    missing_dirs = []
    
    for dir_name in required_dirs:
        if not (deploy_target / dir_name).is_dir():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        return {
            "deployed": True,
            "complete": False,
            "message": f"部署不完整（缺失目录: {', '.join(missing_dirs)}）",
            "manifest": manifest,
        }
    
    return {
        "deployed": True,
        "complete": True,
        "message": "部署完整",
        "manifest": manifest,
        "version": manifest.get("version", "unknown"),
        "deployed_at": manifest.get("deployed_at", "unknown"),
    }


def print_status(project_root: Path = None):
    """打印部署状态信息。"""
    status = check_deployment(project_root)
    
    print(f"[skill_deployer] 部署状态: {status['message']}")
    
    if status.get("complete"):
        manifest = status["manifest"]
        print(f"  版本: {manifest.get('version', 'unknown')}")
        print(f"  部署时间: {manifest.get('deployed_at', 'unknown')}")
        print(f"  文件总数: {manifest.get('total_files', 0)}")
        print(f"  总大小: {manifest.get('total_size', 0):,} bytes")
        print(f"\n  目录详情:")
        for dir_name, info in manifest.get("directories", {}).items():
            print(f"    {dir_name}/: {info['file_count']} 文件, {info['size_bytes']:,} bytes")


def main():
    parser = argparse.ArgumentParser(description="Skill Asset Deployer — 技能资产部署器")
    parser.add_argument("command", choices=["deploy", "check", "status", "version"],
                        help="部署命令")
    parser.add_argument("--force", action="store_true",
                        help="强制重新部署（即使已部署）")
    parser.add_argument("--skill-root", type=str,
                        help="技能根目录路径（默认自动检测）")
    parser.add_argument("--project-root", type=str,
                        help="项目根目录路径（默认自动检测）")
    
    args = parser.parse_args()
    
    skill_root = Path(args.skill_root) if args.skill_root else None
    project_root = Path(args.project_root) if args.project_root else None
    
    if args.command == "deploy":
        deploy_skill(skill_root, project_root, args.force)
    
    elif args.command == "check":
        status = check_deployment(project_root)
        print(f"[skill_deployer] {status['message']}")
        if not status.get("complete", False):
            sys.exit(1)
    
    elif args.command == "status":
        print_status(project_root)
    
    elif args.command == "version":
        print(f"skill_deployer v{VERSION}")


if __name__ == "__main__":
    main()
