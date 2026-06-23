#!/usr/bin/env python3
"""
meeting_protocol.py - 会议协议引擎 (v3.0.0 -- Pure File Tool)

Architecture:
  - This script is a PURE FILE TOOL. It generates meeting minutes templates
    and manages meeting documents via the file system.
  - ALL meeting reasoning (proposals, reviews, decisions) is done by the main
    Codex agent or spawned subagents. This script never calls any LLM API.
  - The main agent calls this script to:
    1. Create meeting directory structure
    2. Generate minutes template
    3. Update meeting index
  - The main agent then fills in the meeting content itself or via subagents.
"""

import json
import re
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None

PROJECT_ROOT = Path(__file__).parent.parent
MEETINGS_DIR = PROJECT_ROOT / "docs" / "meetings"

# ---------------------------------------------------------------------------
# Fallback templates (used only when config/meeting_templates.yaml is missing)
# ---------------------------------------------------------------------------
_FALLBACK_TEMPLATES = {
    "M001_kickoff": {
        "name": "题意共识会",
        "type": "consensus",
        "judge": "reviewer",
        "participants": ["planner", "analyst", "reviewer"],
        "description": "明确题目要求、确认数据可用性、建立共识",
        "subagent_plan": {
            "parallel": [
                {"agent": "planner", "task": "解析赛题，拆解子问题，制定建模路线"},
                {"agent": "analyst", "task": "分析数据可用性，识别缺失数据，评估数据质量"},
            ],
            "sequential": [
                {"agent": "reviewer", "task": "审查规划组和分析组的结论，找遗漏和风险"},
            ],
        },
    },
    "M002_model_debate": {
        "name": "模型路线辩论会",
        "type": "debate",
        "judge": "reviewer",
        "participants": ["proposer", "analyst", "critic", "reviewer"],
        "description": "比较候选模型、确定主模型",
        "subagent_plan": {
            "parallel": [
                {"agent": "proposer", "task": "构建精度导向的主模型（精度视角）"},
                {"agent": "proposer", "task": "构建稳健导向的备选模型（稳健视角）"},
            ],
            "sequential": [
                {"agent": "reviewer", "task": "比较提案组的两套模型方案，裁决主模型选择"},
            ],
        },
    },
    "M003_experiment_review": {
        "name": "实验复盘会",
        "type": "review",
        "judge": "reviewer",
        "participants": ["builder", "analyst", "proposer", "critic"],
        "description": "检查实验结果、识别风险",
        "subagent_plan": {
            "parallel": [],
            "sequential": [
                {"agent": "builder", "task": "检查实验结果完整性"},
                {"agent": "proposer", "task": "确认模型精度指标"},
                {"agent": "critic", "task": "识别潜在风险"},
            ],
        },
    },
    "M004_paper_redteam": {
        "name": "论文红队审稿会",
        "type": "adversarial",
        "judge": "reviewer",
        "participants": ["writer", "critic", "reviewer"],
        "description": "找逻辑硬伤、格式错误",
        "subagent_plan": {
            "parallel": [
                {"agent": "critic", "task": "红队攻击：审查论文所有逻辑漏洞和错误"},
                {"agent": "reviewer", "task": "终审：验证所有修改到位"},
            ],
            "sequential": [
                {"agent": "writer", "task": "根据审稿意见修订论文"},
            ],
        },
    },
}


def _load_meeting_templates():
    """Load meeting templates from config/meeting_templates.yaml (single source
    of truth).  Falls back to _FALLBACK_TEMPLATES when yaml is unavailable."""
    yaml_path = PROJECT_ROOT / "config" / "meeting_templates.yaml"
    if yaml is None or not yaml_path.exists():
        return dict(_FALLBACK_TEMPLATES)
    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if not data or "meetings" not in data:
            return dict(_FALLBACK_TEMPLATES)

        templates = {}
        for mid, mdata in data["meetings"].items():
            # Derive subagent_plan from process steps
            parallel = []
            sequential = []
            process = mdata.get("process", [])
            prev_step = None
            for step in process:
                actor_raw = step.get("actor", "")
                actors = [a.strip() for a in re.split(r"[,、]", actor_raw) if a.strip()]
                action = step.get("action", "")
                step_num = step.get("step")
                if len(actors) > 1 or (step_num is not None and step_num == prev_step):
                    for actor in actors:
                        parallel.append({"agent": actor, "task": action})
                else:
                    for actor in actors:
                        sequential.append({"agent": actor, "task": action})
                prev_step = step_num

            templates[mid] = {
                "name": mdata.get("name", mid),
                "type": mdata.get("type", "unknown"),
                "judge": mdata.get("judge", "reviewer"),
                "participants": mdata.get("participants", []),
                "description": mdata.get("objective", ""),
                "stage": mdata.get("stage", ""),
                "outputs": mdata.get("outputs", []),
                "subagent_plan": {"parallel": parallel, "sequential": sequential},
            }
        return templates
    except Exception:
        return dict(_FALLBACK_TEMPLATES)


MEETING_TEMPLATES = _load_meeting_templates()


def get_meeting_info(meeting_id):
    """Get meeting template info."""
    return MEETING_TEMPLATES.get(meeting_id, {})


def init_meeting_dir(meeting_id):
    """Create meeting directory and return it."""
    m_dir = MEETINGS_DIR / meeting_id
    m_dir.mkdir(parents=True, exist_ok=True)
    return m_dir


def write_minutes(meeting_id, stage_id, content):
    """Write meeting minutes file."""
    m_dir = init_meeting_dir(meeting_id)
    minutes_path = m_dir / (meeting_id + "_minutes.md")
    minutes_path.write_text(content, encoding="utf-8")
    return minutes_path


def write_consensus(meeting_id, content):
    """Write consensus document (M001 only)."""
    m_dir = init_meeting_dir(meeting_id)
    consensus_path = m_dir / (meeting_id + "_consensus.md")
    consensus_path.write_text(content, encoding="utf-8")
    return consensus_path


def update_index(meeting_id, stage_id, status="completed",
                 decision="", participants=None):
    """Update the meeting index JSON."""
    idx_file = MEETINGS_DIR / "meeting_index.json"
    idx = {"meetings": []}
    if idx_file.exists():
        try:
            idx = json.loads(idx_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            idx = {"meetings": []}

    idx["meetings"].append({
        "id": meeting_id,
        "type": MEETING_TEMPLATES.get(meeting_id, {}).get("type", "unknown"),
        "stage": stage_id,
        "status": status,
        "decision": decision,
        "participants": participants or [],
        "completed_at": datetime.now().isoformat(),
    })

    idx_file.parent.mkdir(parents=True, exist_ok=True)
    idx_file.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_minutes_template(meeting_id, stage_id):
    """Generate a meeting minutes template for the main agent to fill in."""
    tmpl = MEETING_TEMPLATES.get(meeting_id)
    if not tmpl:
        return "# Unknown Meeting: " + meeting_id + "\n"

    lines = [
        "# 会议纪要: " + tmpl["name"],
        "",
        "**会议ID**: " + meeting_id,
        "**阶段**: " + stage_id,
        "**类型**: " + tmpl["type"],
        "**参与者**: " + ", ".join(tmpl["participants"]),
        "**裁决者**: " + tmpl["judge"],
        "**时间**: " + datetime.now().isoformat(),
        "",
        "---",
        "",
        "## Subagent Spawn Plan",
        "",
    ]

    plan = tmpl.get("subagent_plan", {})
    if plan.get("parallel"):
        lines.append("### Parallel Spawn")
        for item in plan["parallel"]:
            lines.append("- Spawn `" + item["agent"] + "`: " + item["task"])
        lines.append("")
    if plan.get("sequential"):
        lines.append("### Sequential Spawn")
        for item in plan["sequential"]:
            lines.append("- Spawn `" + item["agent"] + "`: " + item["task"])
        lines.append("")

    lines.extend([
        "## 各方立场",
        "",
        "<!-- 主 Agent 或 Subagent 填写各方立场 -->",
        "",
        "## 裁决结果",
        "",
        "<!-- 主 Agent 填写裁决 -->",
        "",
        "## 行动项",
        "",
        "| # | 行动 | 负责人 | 优先级 |",
        "|---|------|--------|--------|",
        "<!-- 主 Agent 填写行动项 -->",
        "",
        "---",
        "*会议纪要模板生成于 " + datetime.now().isoformat() + "*",
    ])

    return "\n".join(lines)


def run(meeting_id, stage_id):
    """Generate meeting minutes template and initialize directory structure.

    This is a pure file tool -- it creates the template and structure.
    The main agent fills in the actual meeting content.

    Optionally generates SubagentRunner spawn instructions for all agents.
    """
    tmpl = MEETING_TEMPLATES.get(meeting_id)
    if not tmpl:
        return {"status": "error", "msg": "Unknown meeting: " + meeting_id}

    print("[Meeting] 初始化 " + tmpl["name"] + "...")
    print("[Meeting] 参与者: " + ", ".join(tmpl["participants"]))
    print("[Meeting] 裁决者: " + tmpl["judge"])

    # Generate and write minutes template
    template = generate_minutes_template(meeting_id, stage_id)
    minutes_path = write_minutes(meeting_id, stage_id, template)
    print("[Meeting] 会议纪要模板: " + str(minutes_path))

    # Generate consensus doc template for M001
    if tmpl["type"] == "consensus":
        consensus_template = (
            "# 题意共识文档\n\n"
            "> 会议: " + tmpl["name"] + "\n"
            "> 时间: " + datetime.now().isoformat() + "\n"
            "> 状态: 待填写\n\n"
            "---\n\n"
            "## 1. 共识确认\n\n"
            "<!-- 主 Agent 填写 -->\n\n"
            "## 2. 待确认事项\n\n"
            "<!-- 主 Agent 填写 -->\n\n"
            "## 3. 风险登记\n\n"
            "<!-- 主 Agent 填写 -->\n"
        )
        consensus_path = write_consensus(meeting_id, consensus_template)
        print("[Meeting] 共识文档: " + str(consensus_path))

    # Update index
    update_index(meeting_id, stage_id, status="template_ready")
    print("[Meeting] " + tmpl["name"] + " 模板已就绪")

    result = {
        "status": "template_ready",
        "meeting_id": meeting_id,
        "stage_id": stage_id,
        "minutes_path": str(minutes_path),
        "participants": tmpl["participants"],
        "judge": tmpl["judge"],
        "subagent_plan": tmpl.get("subagent_plan", {}),
    }

    # Optionally generate SubagentRunner spawns
    spawn_result = None
    try:
        from subagent_runner import prepare_meeting_spawns
        spawn_result = prepare_meeting_spawns(meeting_id, stage_id)
        if spawn_result.get("status") == "prepared":
            result["spawn_plan"] = {
                "total_agents": spawn_result.get("total_agents", 0),
                "parallel_spawns": [
                    {"agent_id": s["agent_id"], "spawn_file": s["spawn_file"]}
                    for s in spawn_result.get("parallel_spawns", [])
                ],
                "sequential_spawns": [
                    {"agent_id": s["agent_id"], "spawn_file": s["spawn_file"]}
                    for s in spawn_result.get("sequential_spawns", [])
                ],
                "instruction": spawn_result.get("instruction", ""),
            }
            result["spawn_generated"] = True
    except ImportError:
        result["spawn_generated"] = False

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Meeting Protocol -- Pure File Tool")
    parser.add_argument("--meeting-id", required=True, help="Meeting ID (e.g., M001_kickoff)")
    parser.add_argument("--stage-id", required=True, help="Stage ID (e.g., problem_analysis)")
    args = parser.parse_args()

    result = run(args.meeting_id, args.stage_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
