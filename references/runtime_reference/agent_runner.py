from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

from config import AGENT_BIN, PANDOC_BIN, PROJECT_ROOT, RUNTIME_PYTHON, SKILLS_DIR, TOOLS_DIR
from services.llm_client import get_env_for_subprocess
from services.state_store import append_log

log = logging.getLogger(__name__)

IGNORED_DIRS = {".git", "工具", "参考资料", "模板", "__pycache__"}
TOOL_COPIES = ("ai_image.py", "scholar_fetch.py", "tikz_vision_check.py")


def _scan_workspace(workspace: Path) -> dict[str, tuple[int, float]]:
    state: dict[str, tuple[int, float]] = {}
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(workspace).parts):
            continue
        rel = path.relative_to(workspace).as_posix()
        stat = path.stat()
        state[rel] = (stat.st_size, stat.st_mtime)
    return state


def _diff_workspace(before: dict[str, tuple[int, float]], after: dict[str, tuple[int, float]]) -> tuple[list[str], list[str]]:
    created = sorted(path for path in after if path not in before)
    modified = sorted(path for path in after if path in before and after[path] != before[path])
    return created, modified


def _copy_tree(src: Path, dst: Path):
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


def _workspace_summary(workspace: Path) -> str:
    lines = []
    for rel in (
        "问题分析.md",
        "建模报告.md",
        "计算结果.md",
        "图表/图表引用.tex",
        "论文/论文正文.tex",
    ):
        path = workspace / rel
        if path.exists():
            lines.append(f"- {rel} ({path.stat().st_size} bytes)")
    user_data = sorted(p.name for p in (workspace / "用户数据").glob("*") if p.is_file())
    if user_data:
        lines.append("- 用户数据：")
        lines.extend(f"  - {name}" for name in user_data[:20])
    return "\n".join(lines) if lines else "- (no upstream artifacts yet)"


def _build_agent_md(workspace: Path, workflow_title: str, skill_name: str, params: dict[str, Any], required_outputs: list[str]) -> str:
    lines = [
        f"# {workflow_title}",
        "",
        "## 参数",
        f"- competition: {params.get('competition', 'cumcm')}",
        f"- language: {params.get('language', 'zh')}",
        f"- output_format: {params.get('output_format', 'pdf')}",
        f"- max_pages: {params.get('max_pages', 30)}",
        f"- tools: {params.get('tools', 'python')}",
        "",
        "## 当前步骤",
        f"- skill: {skill_name}",
        f"- required_outputs: {', '.join(required_outputs) if required_outputs else '(none listed)'}",
        "",
        "## 工作区现状",
        _workspace_summary(workspace),
        "",
        "## 约束",
        "- 只在当前工作区内读写文件。",
        "- 优先复用上游产物，不要推倒重来。",
        "- 输出必须满足 skill 的 Output Contract 和当前步骤产物清单。",
        "",
    ]
    return "\n".join(lines)


def _load_skill_prompt(skill_name: str, arguments: str, extra_params: dict[str, Any] | None = None) -> str:
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    text = text.replace("$ARGUMENTS", arguments)
    if extra_params:
        lines = ["", "## Additional Parameters", ""]
        for key, value in extra_params.items():
            lines.append(f"- {key}: {value}")
        text += "\n".join(lines) + "\n"
    prelude = (
        "You are running inside an automated competition workflow.\n"
        "Do not ask the user interactive questions.\n"
        "Read the workspace files, follow the skill contract exactly, and produce the required artifacts.\n"
        "If a check fails, fix the workspace and continue until the current step is genuinely complete.\n"
    )
    return prelude + "\n\n" + text


async def _prepare_workspace_resources(workspace: Path, skill_name: str, settings_env: dict[str, str]):
    utils_dir = workspace / "工具"
    refs_dir = workspace / "参考资料"
    templates_dir = workspace / "模板"
    _copy_tree(SKILLS_DIR / "shared-scripts", utils_dir)

    for name in TOOL_COPIES:
        src = TOOLS_DIR / name
        if src.exists():
            shutil.copy2(src, utils_dir / name)

    skill_ref_dir = SKILLS_DIR / skill_name / "references"
    if skill_ref_dir.exists():
        _copy_tree(skill_ref_dir, refs_dir)

    template_root = SKILLS_DIR / skill_name / "templates"
    if template_root.exists():
        _copy_tree(template_root, templates_dir)

    image_cfg = {}
    if settings_env.get("AI_IMAGE_API_KEY"):
        image_cfg["api_key"] = settings_env["AI_IMAGE_API_KEY"]
    if settings_env.get("AI_IMAGE_BASE_URL"):
        image_cfg["base_url"] = settings_env["AI_IMAGE_BASE_URL"]
    if image_cfg:
        (utils_dir / "_ai_image_config.json").write_text(
            json.dumps(image_cfg, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


async def run_skill(
    workflow_id: str,
    workspace: Path,
    workflow_title: str,
    skill_name: str,
    arguments: str,
    params: dict[str, Any],
    required_outputs: list[str],
    model_id: str,
    notify,
) -> dict[str, Any]:
    workspace.mkdir(parents=True, exist_ok=True)
    session_id = str(uuid4())
    settings_env = await get_env_for_subprocess()
    await _prepare_workspace_resources(workspace, skill_name, settings_env)

    agent_md = _build_agent_md(workspace, workflow_title, skill_name, params, required_outputs)
    (workspace / "META_MODEL_AGENT.md").write_text(agent_md, encoding="utf-8")

    env = os.environ.copy()
    env.update(settings_env)
    env["MH_PYTHON"] = str(RUNTIME_PYTHON or sys.executable)
    env["SCHOLAR_SCRIPT"] = str(workspace / "工具" / "scholar_fetch.py")
    if PANDOC_BIN:
        env["PANDOC_BIN"] = str(PANDOC_BIN)
    env["META_MODEL_AGENT_SIMPLE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    prompt = _load_skill_prompt(
        skill_name,
        arguments,
        {
            "competition": params.get("competition", "cumcm"),
            "problem_id": params.get("problem_id", ""),
            "language": params.get("language", "zh"),
            "custom_requirements": params.get("custom_requirements", ""),
        },
    )

    before = _scan_workspace(workspace)
    cmd = [
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        "bypassPermissions",
        "--session-id",
        session_id,
        "--model",
        model_id,
    ]
    launcher = str(AGENT_BIN)
    if launcher.lower().endswith((".cmd", ".bat")):
        exec_args = ["cmd.exe", "/d", "/s", "/c", launcher, *cmd]
    else:
        exec_args = [launcher, *cmd]

    log.info("Running skill %s with %s in %s", skill_name, launcher, workspace)
    proc = await asyncio.create_subprocess_exec(
        *exec_args,
        cwd=str(workspace),
        env=env,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    assert proc.stdin is not None
    proc.stdin.write(prompt.encode("utf-8"))
    await proc.stdin.drain()
    proc.stdin.close()

    async def _stream_stdout():
        assert proc.stdout is not None
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip()
            if not text:
                continue
            await append_log(workflow_id, text, "info", skill_name)
            event: dict[str, Any]
            try:
                event = json.loads(text)
            except Exception:
                event = {"type": "raw", "message": text}
            await notify(workflow_id, {"type": "agent_event", "step": skill_name, "event": event})

    async def _stream_stderr():
        assert proc.stderr is not None
        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip()
            if not text:
                continue
            await append_log(workflow_id, text, "warn", skill_name)
            await notify(workflow_id, {"type": "stderr", "step": skill_name, "message": text})

    await asyncio.gather(_stream_stdout(), _stream_stderr())
    returncode = await proc.wait()
    after = _scan_workspace(workspace)
    created, modified = _diff_workspace(before, after)

    result = {
        "session_id": session_id,
        "created": created,
        "modified": modified,
        "returncode": returncode,
    }
    if returncode != 0:
        raise RuntimeError(f"Meta-model-agent runner failed for {skill_name} with exit code {returncode}")
    return result
