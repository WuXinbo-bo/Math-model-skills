#!/usr/bin/env python3
"""
HookEngine - 生命周期拦截器
提供零 Context 占用的自动化触发点，接管所有副作用。

Hook 点：
1. OnUserQuery - 用户输入到达时
2. PreToolUse - 工具调用前
3. PostToolUse - 工具调用后
4. PostSubAgentExecution - 子 Agent 执行完毕后
5. OnArtifactWrite - 产物写入时
6. OnStageTransition - 阶段切换时
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable

PROJECT_ROOT = Path(__file__).parent.parent

class HookEngine:
    def __init__(self):
        self.hooks: Dict[str, list] = {}
        self._register_default_hooks()
    
    def _register_default_hooks(self):
        self.register("PostSubAgentExecution", self._post_sub_agent_execution)
        self.register("OnArtifactWrite", self._on_artifact_write)
        self.register("OnStageTransition", self._on_stage_transition)
    
    def register(self, hook_name: str, callback: Callable):
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)
    
    def trigger(self, hook_name: str, context: Dict[str, Any]) -> Any:
        results = []
        for callback in self.hooks.get(hook_name, []):
            try:
                result = callback(context)
                results.append(result)
            except Exception as e:
                print(f"[HookEngine] Error in {hook_name}: {e}")
        return results
    
    # ── Default Hook Implementations ──────────────────────────
    def _post_sub_agent_execution(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = ctx.get("agent_id")
        task_id = ctx.get("task_id")
        meeting_id = ctx.get("meeting_id")
        
        if not agent_id or not task_id:
            return {"status": "skipped", "reason": "missing agent_id or task_id"}
        
        results = {"status": "completed", "steps": []}
        
        # Step 1: Validate output via SubagentWatchdog
        try:
            from subagent_watchdog import SubagentWatchdog
            watchdog = SubagentWatchdog()
            output_dir = ctx.get("output_dir", f"outputs/{meeting_id or 'standalone'}")
            output_files = ctx.get("output_files", [])
            quality_checks = ctx.get("quality_checks", ["min_length:500", "no_placeholders"])
            full_paths = [str(Path(output_dir) / f) for f in output_files]
            validation = watchdog.validate(agent_id, full_paths, quality_checks)
            results["steps"].append({
                "step": "validate",
                "passed": validation["passed"],
                "errors": validation.get("errors", []),
            })
            if not validation["passed"]:
                results["status"] = "validation_failed"
                results["validation_errors"] = validation["errors"]
                return results
        except ImportError:
            results["steps"].append({"step": "validate", "skipped": "watchdog not available"})
        
        # Step 2: Compress output for downstream agents
        compress_script = PROJECT_ROOT / "scripts" / "compress_agent_output.py"
        if compress_script.exists():
            import subprocess
            result = subprocess.run(
                ["python", str(compress_script), "--agent-id", agent_id, "--task-id", task_id],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                results["steps"].append({"step": "compress", "status": "ok"})
            else:
                results["steps"].append({"step": "compress", "status": "error", "stderr": result.stderr})
        else:
            # Fallback: use ContextBridge compression
            try:
                from context_bridge import compress_text
                results["steps"].append({"step": "compress", "status": "fallback_via_context_bridge"})
            except ImportError:
                results["steps"].append({"step": "compress", "status": "skipped"})
        
        # Step 3: Generate handoff for next agent (if meeting context)
        if meeting_id:
            try:
                from subagent_runner import _load_execution_log, _save_execution_log
                log = _load_execution_log(meeting_id)
                if agent_id in log.get("agents", {}):
                    log["agents"][agent_id]["status"] = "completed"
                    log["agents"][agent_id]["completed_at"] = datetime.now().isoformat()
                    _save_execution_log(meeting_id, log)
                results["steps"].append({"step": "log_update", "status": "ok"})
            except ImportError:
                pass
        
        return results
    
    def _on_artifact_write(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        file_path = ctx.get("file_path")
        created_by = ctx.get("created_by", "unknown")
        
        if not file_path:
            return {"status": "skipped", "reason": "missing file_path"}
        
        # 通过 StateManager 登记产物
        from state_manager import StateManager
        sm = StateManager()
        artifact_id = sm.register_artifact(file_path, created_by)
        
        return {"status": "registered", "artifact_id": artifact_id}
    
    def _on_stage_transition(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        from_stage = ctx.get("from_stage")
        to_stage = ctx.get("to_stage")
        gate_result = ctx.get("gate_result", "unknown")
        
        if gate_result == "failed":
            return {"status": "blocked", "reason": f"Gate failed at {from_stage}"}
        
        # 更新工作流状态
        from state_manager import StateManager
        sm = StateManager()
        sm.set_stage_status(to_stage, "in_progress")
        
        # Auto-checkpoint the completed stage
        if from_stage and gate_result == "passed":
            try:
                from recovery_manager import create_checkpoint
                cp_result = create_checkpoint(
                    from_stage,
                    meeting_id=ctx.get("meeting_id"),
                    agent_results=ctx.get("agent_results"),
                )
                return {
                    "status": "transitioned",
                    "from": from_stage,
                    "to": to_stage,
                    "checkpoint": cp_result.get("hash"),
                }
            except ImportError:
                pass
        
        return {"status": "transitioned", "from": from_stage, "to": to_stage}
    
    # ── Tool Result Truncation ────────────────────────────────
    @staticmethod
    def truncate_tool_result(content: str, max_chars: int = 2000) -> str:
        if len(content) <= max_chars:
            return content
        return f"[内容已截断，共 {len(content)} 字符。请使用 read_file 读取临时文件]\n\n前{max_chars}字符:\n{content[:max_chars]}"
    
    # ── Context Compression ───────────────────────────────────
    @staticmethod
    def build_sub_agent_summary(raw_output: str) -> str:
        lines = raw_output.split('\n')
        key_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if any(kw in line for kw in ['结论', '结果', '发现', '核心', '关键', '建议', '风险']):
                key_lines.append(line)
        
        if not key_lines:
            key_lines = [l for l in lines if l.strip()][:5]
        
        return "<SubAgentSummary>\n" + '\n'.join(key_lines) + "\n</SubAgentSummary>"


# CLI 入口
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="HookEngine - 生命周期拦截器")
    parser.add_argument("command", choices=["trigger", "truncate", "summary"])
    parser.add_argument("--hook", help="Hook 名称")
    parser.add_argument("--context", help="上下文 JSON")
    parser.add_argument("--content", help="内容")
    args = parser.parse_args()
    
    engine = HookEngine()
    
    if args.command == "trigger":
        ctx = json.loads(args.context) if args.context else {}
        results = engine.trigger(args.hook, ctx)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif args.command == "truncate":
        result = HookEngine.truncate_tool_result(args.content or "")
        print(result)
    elif args.command == "summary":
        result = HookEngine.build_sub_agent_summary(args.content or "")
        print(result)
