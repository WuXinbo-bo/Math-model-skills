from __future__ import annotations

import asyncio
import json
import logging
import secrets
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from config import WORKSPACES_DIR
from services.agent_runner import run_skill
from services.state_store import (
    append_log,
    create_checkpoint,
    create_workflow,
    get_current_checkpoint,
    get_db,
    get_step,
    get_workflow,
    get_workflow_steps,
    insert_workflow_steps,
    resolve_checkpoint as resolve_checkpoint_store,
    update_step,
    update_workflow,
)

log = logging.getLogger(__name__)

BroadcastFn = Callable[[str, dict[str, Any]], Awaitable[None]]
_broadcast: BroadcastFn | None = None


@dataclass
class StepDef:
    skill_name: str
    display_name: str
    output_files: list[str]
    has_checkpoint: bool = False
    checkpoint_type: str | None = None


@dataclass
class TemplateDef:
    key: str
    display_name: str
    pipeline_skill: str
    sub_steps: list[StepDef] = field(default_factory=list)


def _comp_zh_steps(first_skill: str = "problem-intelligence") -> list[StepDef]:
    steps = [
        StepDef(first_skill, "问题情境解构", ["问题分析.md"], True, "approve"),
        StepDef("model-formulation", "数学机制构造", ["建模报告.md"], True, "feedback"),
        StepDef("computational-realization", "计算实验实现", ["程序/主程序.py", "计算结果.md"], True, "approve"),
        StepDef("evidence-visualization", "证据图谱构建", ["图表/图表引用.tex"]),
        StepDef("systems-diagramming", "系统逻辑制图", ["图表/图表引用.tex"]),
        StepDef("manuscript-synthesis", "竞赛文稿集成", ["论文/论文正文.tex"], True, "approve"),
        StepDef("delivery-assurance", "提交质量验收", ["论文/数模论文.pdf"]),
    ]
    return steps


TEMPLATES: dict[str, TemplateDef] = {
    "comp_cumcm": TemplateDef(
        key="comp_cumcm",
        display_name="国赛数学建模 (CUMCM)",
        pipeline_skill="problem-intelligence",
        sub_steps=_comp_zh_steps(),
    )
}


MIN_OUTPUT_SIZE = {
    "problem-intelligence": 1500,
    "model-formulation": 2000,
    "computational-realization": 1000,
    "evidence-visualization": 500,
    "systems-diagramming": 500,
    "manuscript-synthesis": 5000,
    "delivery-assurance": 20000,
}

COMPANIONS = {
    "computational-realization": ["图表/全部结果.json"],
}


def set_broadcast(fn: BroadcastFn | None):
    global _broadcast
    _broadcast = fn


async def _notify(workflow_id: str, event: dict[str, Any]):
    if _broadcast is not None:
        await _broadcast(workflow_id, event)


def _min_size_for(skill_name: str, primary_output: str | None = None) -> int:
    return MIN_OUTPUT_SIZE.get(skill_name, 200)


def _required_companions_for(skill_name: str) -> list[str]:
    return COMPANIONS.get(skill_name, [])


def _check_step_companions(workspace: Path, skill_name: str) -> tuple[bool, list[str]]:
    missing = []
    for rel in _required_companions_for(skill_name):
        path = workspace / rel
        if not path.exists() or path.stat().st_size < 50:
            missing.append(rel)
    return (not missing, missing)


def _primary_output_for(step: dict[str, Any]) -> str | None:
    files = step.get("output_files") or []
    return files[0] if files else None


def _verify_step_outputs(workspace: Path, step: dict[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    for rel in step.get("output_files") or []:
        path = workspace / rel
        if not path.exists():
            issues.append(f"missing:{rel}")
            continue
        if path.is_file() and path.stat().st_size < _min_size_for(step["skill_name"], rel):
            issues.append(f"too_small:{rel}")
    ok_companions, missing = _check_step_companions(workspace, step["skill_name"])
    if not ok_companions:
        issues.extend(f"missing:{name}" for name in missing)
    return (not issues, issues)


def _default_params(params: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "competition": "cumcm",
        "language": "zh",
        "max_pages": 30,
        "output_format": "pdf",
        "tools": "python",
        "min_figures": "auto",
        "min_tables": "auto",
        "min_models": "auto",
        "problem_id": "",
        "custom_requirements": "",
    }
    merged.update(params or {})
    return merged


def _init_workspace(workspace: Path):
    for rel in ("用户数据", "程序", "图表", "论文", "_tmp", "工具", "参考资料", "模板"):
        (workspace / rel).mkdir(parents=True, exist_ok=True)
    git_dir = workspace / ".git"
    if not git_dir.exists():
        try:
            subprocess.run(["git", "init"], cwd=workspace, check=False, capture_output=True)
        except Exception:
            pass


def _build_arguments(workflow: dict[str, Any], workspace: Path) -> str:
    parts = [workflow["title"]]
    custom_req = workflow.get("params", {}).get("custom_requirements") or ""
    if custom_req:
        parts.append(custom_req)
    extracted_files = sorted((workspace / "用户数据").glob("*_extracted.txt"))
    if extracted_files:
        names = ", ".join(path.name for path in extracted_files[:10])
        parts.append(f"已在用户数据目录中检测到抽取后的赛题文本：{names}")
    return "\n\n".join(parts)


async def create_new_workflow(template: str, title: str, params: dict, enable_checkpoints: bool = False) -> str:
    if template not in TEMPLATES:
        raise ValueError(f"Unsupported template: {template}")
    wf_id = secrets.token_hex(6)
    workspace = WORKSPACES_DIR / wf_id
    _init_workspace(workspace)
    template_def = TEMPLATES[template]
    merged_params = _default_params(params)
    async with get_db() as db:
        await create_workflow(
            db,
            {
                "id": wf_id,
                "template": template,
                "title": title,
                "params": merged_params,
                "status": "pending",
                "current_step": template_def.sub_steps[0].skill_name,
                "workspace_dir": str(workspace),
                "enable_checkpoints": enable_checkpoints,
            },
        )
        await insert_workflow_steps(
            db,
            wf_id,
            [
                {
                    "skill_name": step.skill_name,
                    "display_name": step.display_name,
                    "step_order": idx,
                    "status": "pending",
                    "has_checkpoint": step.has_checkpoint,
                    "checkpoint_type": step.checkpoint_type,
                    "output_files": step.output_files,
                }
                for idx, step in enumerate(template_def.sub_steps)
            ],
        )
    await append_log(wf_id, f"Workflow created: {title}", "info")
    return wf_id


async def _complete_step(workflow_id: str, step: dict[str, Any], workflow: dict[str, Any]):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with get_db() as db:
        await update_step(
            db,
            workflow_id,
            step["skill_name"],
            status="completed",
            completed_at=now,
        )
        await update_workflow(
            db,
            workflow_id,
            current_step=step["skill_name"],
            status="running",
        )
    if step.get("has_checkpoint") and workflow.get("enable_checkpoints"):
        checkpoint = {
            "step_name": step["skill_name"],
            "display_name": step["display_name"],
            "checkpoint_type": step.get("checkpoint_type"),
            "output_files": step.get("output_files", []),
        }
        async with get_db() as db:
            await update_step(db, workflow_id, step["skill_name"], status="waiting_checkpoint")
            await update_workflow(db, workflow_id, status="paused")
        await create_checkpoint(workflow_id, step["skill_name"], step.get("checkpoint_type") or "approve", checkpoint)
        await append_log(workflow_id, f"Waiting for checkpoint: {step['skill_name']}", "info", step["skill_name"])
        await _notify(workflow_id, {"type": "checkpoint", "step": step["skill_name"], "data": checkpoint})


async def run_single_step(workflow_id: str, skill_name: str):
    async with get_db() as db:
        workflow = await get_workflow(db, workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")
        step = await get_step(db, workflow_id, skill_name)
        if step is None:
            raise ValueError(f"Step not found: {skill_name}")
        workspace = Path(workflow["workspace_dir"])
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await update_workflow(db, workflow_id, status="running", current_step=skill_name)
        await update_step(db, workflow_id, skill_name, status="running", started_at=now, error_message=None)
    await append_log(workflow_id, f"Executing step: {skill_name}", "info", skill_name)
    await _notify(workflow_id, {"type": "step_started", "step": skill_name})

    model_id = workflow["params"].get("executor_model_id") or "meta-model-agent-default"
    result = await run_skill(
        workflow_id=workflow_id,
        workspace=workspace,
        workflow_title=workflow["title"],
        skill_name=skill_name,
        arguments=_build_arguments(workflow, workspace),
        params=workflow["params"],
        required_outputs=step.get("output_files", []),
        model_id=model_id,
        notify=_notify,
    )
    ok, issues = _verify_step_outputs(workspace, step)
    if not ok:
        raise RuntimeError(f"Output verification failed for {skill_name}: {', '.join(issues)}")
    await append_log(
        workflow_id,
        json.dumps({"created": result["created"], "modified": result["modified"]}, ensure_ascii=False),
        "info",
        skill_name,
    )
    await _complete_step(workflow_id, step, workflow)
    await _notify(workflow_id, {"type": "step_completed", "step": skill_name, "result": result})


async def run_workflow(workflow_id: str):
    async with get_db() as db:
        workflow = await get_workflow(db, workflow_id)
        if workflow is None:
            return
        steps = await get_workflow_steps(db, workflow_id)

    workspace = Path(workflow["workspace_dir"])
    _init_workspace(workspace)

    running_steps = [step for step in steps if step["status"] == "running"]
    if running_steps:
        async with get_db() as db:
            for step in running_steps:
                await update_step(db, workflow_id, step["skill_name"], status="pending")
        await append_log(workflow_id, "Recovered stale running step(s) after restart", "warn")
        steps = await get_workflow_steps(db, workflow_id)

    active_skill: str | None = None
    try:
        async with get_db() as db:
            await update_workflow(db, workflow_id, status="running")
        for step in steps:
            active_skill = step["skill_name"]
            fresh_workflow: dict[str, Any]
            async with get_db() as db:
                fresh_workflow = await get_workflow(db, workflow_id) or workflow
            if fresh_workflow["status"] == "paused":
                return
            if step["status"] == "completed":
                ok, issues = _verify_step_outputs(workspace, step)
                if ok:
                    await append_log(workflow_id, f"Skipping completed step {step['skill_name']} (verified)", "info")
                    continue
                async with get_db() as db:
                    await update_step(db, workflow_id, step["skill_name"], status="pending")
                await append_log(workflow_id, f"Re-running invalid completed step {step['skill_name']}: {issues}", "warn")
            if step["status"] == "waiting_checkpoint":
                return
            await run_single_step(workflow_id, step["skill_name"])
            async with get_db() as db:
                refreshed = await get_step(db, workflow_id, step["skill_name"])
            if refreshed and refreshed["status"] == "waiting_checkpoint":
                return
        async with get_db() as db:
            await update_workflow(db, workflow_id, status="completed")
        await append_log(workflow_id, "Workflow completed", "info")
        await _notify(workflow_id, {"type": "workflow_completed"})
    except asyncio.CancelledError:
        async with get_db() as db:
            await update_workflow(db, workflow_id, status="paused")
        await append_log(workflow_id, "Workflow paused", "warn")
        raise
    except Exception as exc:
        async with get_db() as db:
            await update_workflow(db, workflow_id, status="failed")
            current = active_skill or (await get_workflow(db, workflow_id) or {}).get("current_step")
            if current:
                await update_step(db, workflow_id, current, status="failed", error_message=str(exc))
        await append_log(workflow_id, str(exc), "error")
        await _notify(workflow_id, {"type": "workflow_failed", "message": str(exc)})
        raise


async def resolve_checkpoint(workflow_id: str, response: dict[str, Any]):
    checkpoint = await get_current_checkpoint(workflow_id)
    if checkpoint is None:
        return
    await resolve_checkpoint_store(workflow_id, response)
    async with get_db() as db:
        await update_step(db, workflow_id, checkpoint["step_name"], status="completed")
        if response.get("action") == "rerun":
            await update_step(db, workflow_id, checkpoint["step_name"], status="pending")
        await update_workflow(db, workflow_id, status="running")


async def wait_checkpoint(workflow_id: str, timeout: int = 600) -> dict[str, Any]:
    for _ in range(timeout):
        checkpoint = await get_current_checkpoint(workflow_id)
        if checkpoint is not None:
            return checkpoint
        await asyncio.sleep(1)
    return {}
