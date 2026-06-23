#!/usr/bin/env python3
"""Workspace & Skill path resolution utilities (v2.0).

Provides intelligent path resolution for both development mode
(scripts in original skill directory) and deployed mode
(scripts in CUMCM_Workspace/_skill/scripts/).

Key functions:
  resolve_project_root()  — Find the user's project directory
  resolve_skill_root()    — Find the skill assets directory
  resolve_workspace()     — Find the CUMCM_Workspace directory
"""
import os
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent


def resolve_project_root() -> Path:
    """Find PROJECT_ROOT — the directory containing CUMCM_Workspace/.

    Search strategy:
      1. Walk up from CWD to find a directory containing CUMCM_Workspace/
      2. Walk up from script location to find CUMCM_Workspace/
      3. Fall back to CWD
    """
    # From CWD upward
    current = Path.cwd()
    for _ in range(10):
        if (current / "CUMCM_Workspace").is_dir():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    # From script location upward (handles deployed mode)
    current = _SCRIPT_DIR
    for _ in range(10):
        if (current / "CUMCM_Workspace").is_dir():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    return Path.cwd()


def resolve_skill_root() -> Path:
    """Find SKILL_ROOT — the directory containing skill assets.

    Priority:
      1. SKILL_ROOT environment variable (if valid)
      2. Deployed: CUMCM_Workspace/_skill/ (if scripts/ is inside _skill/scripts/)
      3. Development: SCRIPT_DIR.parent (script in original skill dir)
      4. PROJECT_ROOT/CUMCM_Workspace/_skill/ (fallback)
    """
    # 1. Environment variable
    env_sr = os.environ.get("SKILL_ROOT")
    if env_sr:
        p = Path(env_sr)
        if p.is_dir() and (p / "scripts").is_dir():
            return p

    # 2. Deployed mode: script is at _skill/scripts/xxx.py
    if _SCRIPT_DIR.parent.name == "_skill":
        return _SCRIPT_DIR.parent

    # 3. Development mode: script is at SKILL_ROOT/scripts/xxx.py
    dev_root = _SCRIPT_DIR.parent
    if (dev_root / "SKILL.md").exists() and (dev_root / "stages").is_dir():
        return dev_root

    # 4. Fallback: deployed from project root
    project_root = resolve_project_root()
    deployed = project_root / "CUMCM_Workspace" / "_skill"
    if deployed.is_dir() and (deployed / "scripts").is_dir():
        return deployed

    return dev_root


def resolve_workspace() -> Path:
    """Smart workspace resolution with auto-creation.

    Priority:
      1. CUMCM_Workspace/ with state file (from project root)
      2. CWD has state file → use "."
      3. CUMCM_Workspace/ exists (even empty)
      4. Auto-create via workspace_init.ensure_workspace()
      5. Default to "."
    """
    project_root = resolve_project_root()

    ws_cumcm = project_root / "CUMCM_Workspace"
    ws_cwd = Path(".")

    has_cumcm = (ws_cumcm / "state" / "workflow_state.json").exists()
    has_cwd = (ws_cwd / "state" / "workflow_state.json").exists()

    if has_cumcm and not has_cwd:
        return ws_cumcm
    if has_cwd and not has_cumcm:
        return ws_cwd
    if has_cumcm and has_cwd:
        return ws_cumcm

    if ws_cumcm.exists():
        return ws_cumcm

    # Auto-create
    try:
        from workspace_init import ensure_workspace
        ws = ensure_workspace(project_root)
        return ws
    except Exception:
        pass

    return ws_cwd


def resolve_workspace_from_project(project_root: Path) -> Path:
    """Resolve workspace relative to project root."""
    ws_cumcm = project_root / "CUMCM_Workspace"
    ws_cwd = project_root

    has_cumcm = (ws_cumcm / "state" / "workflow_state.json").exists()
    has_cwd = (ws_cwd / "state" / "workflow_state.json").exists()

    if has_cumcm and not has_cwd:
        return ws_cumcm
    if has_cwd and not has_cumcm:
        return ws_cwd
    if has_cumcm and has_cwd:
        return ws_cumcm

    if ws_cumcm.exists():
        return ws_cumcm

    try:
        from workspace_init import ensure_workspace
        ensure_workspace(project_root)
        return ws_cumcm
    except Exception:
        pass

    return ws_cwd
