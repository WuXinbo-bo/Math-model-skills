from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from manifest import competition_profile, load_manifest


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def state_path(workspace: Path) -> Path:
    return workspace / "状态" / "工作流状态.json"


def event_log_path(workspace: Path) -> Path:
    return workspace / "状态" / "事件日志.jsonl"


def ensure_workspace_dirs(workspace: Path) -> None:
    manifest = load_manifest()
    for rel in manifest["workspace_dirs"]:
        (workspace / rel).mkdir(parents=True, exist_ok=True)


def default_state(workspace: Path, title: str = "Meta-model-agent", competition: str = "cumcm", output_format: str = "pdf") -> dict[str, Any]:
    manifest = load_manifest()
    profile = competition_profile(competition)
    steps = []
    for index, step in enumerate(manifest["steps"]):
        steps.append(
            {
                "stage_id": step["stage_id"],
                "skill_name": step["skill_name"],
                "display_name": step["display_name"],
                "status": "ready" if index == 0 else "pending",
                "attempts": 0,
                "reworks": 0,
                "started_at": None,
                "completed_at": None,
                "artifacts": [],
                "last_gate": None,
                "checkpoint_history": [],
                "notes": []
            }
        )
    return {
        "version": 1,
        "template_key": profile["template_dir"],
        "competition": competition,
        "competition_profile": profile,
        "output_format": output_format,
        "display_name": profile["display_name"],
        "title": title,
        "phase": "baseline",
        "quality_mode": "standard",
        "championship_review": {
            "status": "not_required",
            "rounds": [],
            "final_score": None,
            "final_paper": None,
            "completed_at": None
        },
        "workflow_status": "initialized",
        "workspace_dir": str(workspace.resolve()),
        "current_stage_id": manifest["steps"][0]["stage_id"],
        "active_checkpoint": None,
        "steps": steps,
        "created_at": now_iso(),
        "updated_at": now_iso()
    }


def init_state(workspace: Path, title: str = "Meta-model-agent", competition: str = "cumcm", output_format: str = "pdf", force: bool = False) -> dict[str, Any]:
    ensure_workspace_dirs(workspace)
    path = state_path(workspace)
    if path.exists() and not force:
        return load_state(workspace)
    state = default_state(workspace, title=title, competition=competition, output_format=output_format)
    save_state(workspace, state)
    append_event(workspace, "init", {"title": title, "competition": competition, "output_format": output_format, "force": force})
    manifest_snapshot = workspace / "状态" / "工作流清单快照.json"
    manifest_snapshot.write_text(json.dumps(load_manifest(), ensure_ascii=False, indent=2), encoding="utf-8")
    return state


def load_state(workspace: Path) -> dict[str, Any]:
    return json.loads(state_path(workspace).read_text(encoding="utf-8"))


def save_state(workspace: Path, state: dict[str, Any]) -> None:
    state = deepcopy(state)
    state["updated_at"] = now_iso()
    path = state_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def append_event(workspace: Path, event_type: str, payload: dict[str, Any]) -> None:
    path = event_log_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": now_iso(),
        "event_type": event_type,
        "payload": payload
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def get_step_state(state: dict[str, Any], stage_id: str) -> Optional[dict[str, Any]]:
    for step in state["steps"]:
        if step["stage_id"] == stage_id:
            return step
    return None
