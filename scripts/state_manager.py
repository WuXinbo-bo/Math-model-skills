#!/usr/bin/env python3
"""
StateManager - 状态与资产管理层
统一管理 workflow_state.json、task_board.json、artifact_manifest.json

核心职责：
1. DAG 任务调度：基于拓扑排序决定下一个可执行任务
2. 状态流转管理：pending → ready → executing → completed / blocked / rejected
3. 产物登记与血缘追踪：SHA-256 Hash + parent_hash 追溯链
4. 质询状态机：管理独立的质询/澄清通道
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
COMMAND_DIR = DOCS_DIR / "command"

class StateManager:
    def __init__(self):
        self.workflow_file = COMMAND_DIR / "workflow_state.json"
        self.task_board_file = COMMAND_DIR / "task_board.json"
        self.manifest_file = COMMAND_DIR / "artifact_manifest.json"
        
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    
    # ── Workflow State ────────────────────────────────────────
    def get_workflow_state(self) -> Dict[str, Any]:
        if self.workflow_file.exists():
            return json.loads(self.workflow_file.read_text(encoding='utf-8'))
        return {"status": "uninitialized", "current_stage": None, "stages": {}}
    
    def update_workflow_state(self, updates: Dict[str, Any]):
        state = self.get_workflow_state()
        state.update(updates)
        state["last_updated"] = datetime.now().isoformat()
        self.workflow_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    
    def set_stage_status(self, stage_id: str, status: str):
        state = self.get_workflow_state()
        if "stages" not in state:
            state["stages"] = {}
        state["stages"][stage_id] = status
        state["current_stage"] = stage_id
        self.update_workflow_state(state)
    
    # ── Task Board (DAG) ──────────────────────────────────────
    def get_task_board(self) -> Dict[str, Any]:
        if self.task_board_file.exists():
            return json.loads(self.task_board_file.read_text(encoding='utf-8'))
        return {"tasks": []}
    
    def save_task_board(self, board: Dict[str, Any]):
        self.task_board_file.write_text(json.dumps(board, ensure_ascii=False, indent=2), encoding='utf-8')
    
    def get_ready_tasks(self) -> List[Dict[str, Any]]:
        """获取所有依赖已满足的就绪任务"""
        board = self.get_task_board()
        ready = []
        
        for task in board.get("tasks", []):
            if task.get("status") != "pending":
                continue
            
            deps = task.get("dependencies", [])
            if not deps:
                ready.append(task)
                continue
            
            all_deps_met = all(
                self._get_task_status(board, dep) == "completed"
                for dep in deps
            )
            
            if all_deps_met:
                ready.append(task)
        
        return ready
    
    def _get_task_status(self, board: Dict, task_id: str) -> str:
        for task in board.get("tasks", []):
            if task.get("id") == task_id:
                return task.get("status", "unknown")
        return "unknown"
    
    def update_task_status(self, task_id: str, status: str):
        board = self.get_task_board()
        for task in board.get("tasks", []):
            if task.get("id") == task_id:
                task["status"] = status
                task["updated_at"] = datetime.now().isoformat()
                break
        self.save_task_board(board)
    
    def add_task(self, task: Dict[str, Any]):
        board = self.get_task_board()
        if "tasks" not in board:
            board["tasks"] = []
        board["tasks"].append(task)
        self.save_task_board(board)
    
    # ── Artifact Manifest ─────────────────────────────────────
    def get_manifest(self) -> Dict[str, Any]:
        if self.manifest_file.exists():
            return json.loads(self.manifest_file.read_text(encoding='utf-8'))
        return {"artifacts": []}
    
    def save_manifest(self, manifest: Dict[str, Any]):
        self.manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    
    def register_artifact(self, name: str, created_by: str, parent_name: Optional[str] = None) -> str:
        """登记新产物，返回 artifact_id"""
        manifest = self.get_manifest()
        
        # 计算 Hash
        file_path = PROJECT_ROOT / name
        file_hash = "pending"
        if file_path.exists():
            file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()[:16]
        
        # 查找 parent_hash
        parent_hash = None
        if parent_name:
            for art in manifest.get("artifacts", []):
                if art.get("name") == parent_name:
                    parent_hash = art.get("hash")
                    break
        
        artifact_id = f"A{len(manifest.get('artifacts', [])) + 1:03d}"
        
        manifest.setdefault("artifacts", []).append({
            "id": artifact_id,
            "name": name,
            "hash": file_hash,
            "parent_hash": parent_hash,
            "created_by": created_by,
            "version": 1,
            "created_at": datetime.now().isoformat()
        })
        
        self.save_manifest(manifest)
        return artifact_id
    
    # ── Clarification State ───────────────────────────────────
    def get_clarification_state(self) -> Dict[str, Any]:
        state = self.get_workflow_state()
        return state.get("clarification_state", {"status": "NONE", "pending_questions": [], "history": []})
    
    def set_clarification_state(self, status: str, questions: List[str] = None):
        state = self.get_workflow_state()
        state["clarification_state"] = {
            "status": status,
            "pending_questions": questions or [],
            "updated_at": datetime.now().isoformat()
        }
        self.update_workflow_state(state)
    
    # ── Summary Compression ───────────────────────────────────
    def get_agent_summary(self, agent_id: str, task_id: str) -> Optional[str]:
        summary_file = PROJECT_ROOT / "agents" / agent_id / "summaries" / f"{task_id}_summary.md"
        if summary_file.exists():
            return summary_file.read_text(encoding='utf-8')
        return None


# CLI 入口
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="StateManager - 状态管理器")
    parser.add_argument("command", choices=["status", "ready", "add-task", "update-task", "register-artifact"])
    parser.add_argument("--task-id", help="任务 ID")
    parser.add_argument("--status", help="新状态")
    parser.add_argument("--task-json", help="任务 JSON")
    parser.add_argument("--artifact-name", help="产物名称")
    parser.add_argument("--created-by", help="创建者")
    args = parser.parse_args()
    
    sm = StateManager()
    
    if args.command == "status":
        print(json.dumps(sm.get_workflow_state(), ensure_ascii=False, indent=2))
    elif args.command == "ready":
        ready = sm.get_ready_tasks()
        print(json.dumps(ready, ensure_ascii=False, indent=2))
    elif args.command == "add-task":
        task = json.loads(args.task_json)
        sm.add_task(task)
        print(f"Task added: {task.get('id')}")
    elif args.command == "update-task":
        sm.update_task_status(args.task_id, args.status)
        print(f"Task {args.task_id} -> {args.status}")
    elif args.command == "register-artifact":
        aid = sm.register_artifact(args.artifact_name, args.created_by)
        print(f"Artifact registered: {aid}")
