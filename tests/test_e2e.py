#!/usr/bin/env python3
"""
端到端测试 v3.0.0 — 验证 Codex 原生架构 (workflow.yaml driven)

Architecture: 所有推理由主 Agent 完成，Python 脚本仅做工具性工作。
本测试验证:
1. 核心文件存在性（AGENTS.md, SKILL.md, stages/S*.md, config/）
2. pipeline_manager.py 纯状态机（无 LLM 调用）
3. meeting_protocol.py 纯文件工具（无 LLM 调用）
4. 工具脚本可导入
5. 无 llm_client 残留
6. workflow.yaml 一致性
7. gate_contracts.py 合约完整性
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


def test_core_files_exist():
    """测试核心架构文件存在"""
    print("[TEST] 1. 测试核心架构文件...")
    required_files = [
        "AGENTS.md",
        "SKILL.md",
        "main.py",
        "requirements.txt",
        "config/workflow.yaml",
        "config/agents.yaml",
        "config/meeting_templates.yaml",
        "config/rubric.yaml",
        "stages/S0.md",
        "stages/S1.md",
        "stages/S2.md",
        "stages/S3.md",
        "stages/S4.md",
        "stages/S5.md",
        "stages/S5.5.md",
        "stages/S6.md",
        "stages/S7.md",
        "stages/S7.5.md",
        "stages/S8.md",
        "stages/S9.md",
        "stages/S9.5.md",
        "stages/S10.md",
        "scripts/stage_executor.py",
        "scripts/gate_contracts.py",
        "scripts/pipeline_manager.py",
    ]
    missing = [f for f in required_files if not (PROJECT_ROOT / f).exists()]
    if missing:
        print(f"  [FAIL] 缺失文件: {missing}")
        return False
    print(f"  [PASS] 所有 {len(required_files)} 个核心文件存在")
    return True


def test_no_llm_client():
    """测试无 LLM 客户端残留"""
    print("[TEST] 2. 测试无 llm_client 残留...")
    src_dir = PROJECT_ROOT / "src"
    if src_dir.exists():
        py_files = list(src_dir.glob("*.py"))
        if py_files:
            print(f"  [FAIL] src/ 仍有 Python 文件: {[f.name for f in py_files]}")
            return False

    test_file = Path(__file__).resolve()
    skip_files = {test_file}

    import re
    llm_import_pat = re.compile(
        r"(?:import\s+.*(?:llm_client|LLMClient)"
        r"|from\s+src\s*\."
        r"|from\s+scripts\.(?:chief_orchestrator|auto_max_pipeline|sub_agent_runner|poc_runner))"
    )

    for py_file in PROJECT_ROOT.rglob("*.py"):
        if py_file in skip_files:
            continue
        if ".codebuddy" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            if llm_import_pat.search(content):
                print(f"  [FAIL] {py_file.relative_to(PROJECT_ROOT)} 仍有 LLM 引用")
                return False
        except (UnicodeDecodeError, OSError):
            pass

    print("  [PASS] 无 llm_client 残留")
    return True


def test_pipeline_manager():
    """测试 pipeline_manager.py 纯状态机"""
    print("[TEST] 3. 测试 pipeline_manager.py...")
    try:
        from scripts.pipeline_manager import (
            STAGE_ORDER, PARALLEL_GROUPS, STATUS_ICONS,
            cmd_status, cmd_init, cmd_start_stage, cmd_advance,
            cmd_rework, cmd_request_review, cmd_check_approval,
            cmd_parallel_start, cmd_parallel_status, cmd_parallel_all_done,
            cmd_suggest_parallel, cmd_checkpoint_banner,
            cmd_parallel_merge_status, cmd_parallel_merge,
            cmd_workflow_info, cmd_check_gate,
            save_stage_output, save_pipeline_state,
        )

        # 验证阶段顺序完整（workflow.yaml 当前有 14 个阶段）
        assert len(STAGE_ORDER) >= 14, f"阶段数不足: {len(STAGE_ORDER)}"

        # 验证无 LLM 导入
        import inspect
        source = inspect.getsource(sys.modules["scripts.pipeline_manager"])
        assert "llm_client" not in source, "pipeline_manager.py 仍包含 llm_client"
        assert "LLMClient" not in source, "pipeline_manager.py 仍包含 LLMClient"

        # 验证关键阶段存在
        stage_ids = [s for s in STAGE_ORDER]
        assert any("input" in s for s in stage_ids), "缺少 input_registration 阶段"
        assert any("problem" in s for s in stage_ids), "缺少 problem_analysis 阶段"
        assert any("paper" in s for s in stage_ids), "缺少 paper_drafting 阶段"
        assert any("final" in s for s in stage_ids), "缺少 final_build 阶段"

        print(f"  [PASS] pipeline_manager.py 纯状态机, {len(STAGE_ORDER)} 个阶段")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_meeting_protocol():
    """测试 meeting_protocol.py 纯文件工具"""
    print("[TEST] 4. 测试 meeting_protocol.py...")
    try:
        from scripts.meeting_protocol import (
            MEETING_TEMPLATES, run, get_meeting_info,
            init_meeting_dir, write_minutes, update_index,
            generate_minutes_template,
        )

        # 验证 4 个会议模板
        assert len(MEETING_TEMPLATES) == 4, f"会议模板数: {len(MEETING_TEMPLATES)}"
        assert "M001_kickoff" in MEETING_TEMPLATES
        assert "M002_model_debate" in MEETING_TEMPLATES
        assert "M003_experiment_review" in MEETING_TEMPLATES
        assert "M004_paper_redteam" in MEETING_TEMPLATES

        # 验证无 LLM 导入
        import inspect
        source = inspect.getsource(sys.modules["scripts.meeting_protocol"])
        assert "llm_client" not in source, "meeting_protocol.py 仍包含 llm_client"
        assert "LLMClient" not in source, "meeting_protocol.py 仍包含 LLMClient"

        # 验证 subagent_plan 存在
        for mid, tmpl in MEETING_TEMPLATES.items():
            assert "subagent_plan" in tmpl, f"{mid} 缺少 subagent_plan"
            assert "parallel" in tmpl["subagent_plan"], f"{mid} 缺少 parallel"
            assert "sequential" in tmpl["subagent_plan"], f"{mid} 缺少 sequential"

        print(f"  [PASS] meeting_protocol.py 纯文件工具, {len(MEETING_TEMPLATES)} 个会议模板")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_tool_scripts():
    """测试工具脚本可导入"""
    print("[TEST] 5. 测试工具脚本可导入...")
    try:
        from scripts.state_manager import StateManager
        from scripts.hook_engine import HookEngine
        from scripts.meeting_protocol import run, get_meeting_info, MEETING_TEMPLATES
        print("  [PASS] 核心工具脚本可导入 (state_manager, hook_engine, meeting_protocol)")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_stage_agent_instructions():
    """测试 stages/S*.md 包含子Agent调用指令"""
    print("[TEST] 6. 测试阶段文件子Agent指令...")
    try:
        stages_dir = PROJECT_ROOT / "stages"
        stage_files = sorted(stages_dir.glob("S*.md"))
        assert len(stage_files) >= 13, f"期望至少 13 个阶段文件, 实际 {len(stage_files)}"

        # 检查关键阶段文件包含子Agent调用指令
        key_stages = {
            "S0.md": ["审查官", "Inspector"],
            "S1.md": ["Planner", "Analyst"],
            "S3.md": ["Proposer", "Red Team", "Blue Team", "Referee"],
            "S5.md": ["Proposer", "Builder"],
            "S8.md": ["Writer"],
            "S9.md": ["Critic", "Reviewer"],
        }
        for stage_name, keywords in key_stages.items():
            content = (stages_dir / stage_name).read_text(encoding="utf-8")
            found = [kw for kw in keywords if kw in content]
            assert len(found) >= 1, f"{stage_name} 缺少子Agent指令（期望含: {keywords}）"

        print(f"  [PASS] {len(stage_files)} 个阶段文件, 关键阶段包含子Agent指令")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_skill_md():
    """测试 SKILL.md 内容完整"""
    print("[TEST] 7. 测试 SKILL.md...")
    try:
        skill_file = PROJECT_ROOT / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        required_sections = [
            "14 阶段",
            "S0",
            "S10",
            "Planner",
            "Analyst",
            "Proposer",
            "Builder",
            "Critic",
            "Reviewer",
            "Writer",
            "Inspector",
            "stage_executor.py",
            "gate_contracts.py",
            "Fast 模式",
            "Championship",
        ]
        missing = [s for s in required_sections if s not in content]
        if missing:
            print(f"  [FAIL] SKILL.md 缺少: {missing}")
            return False
        print(f"  [PASS] SKILL.md 内容完整, {len(content)} 字符")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_workflow_yaml():
    """测试 workflow.yaml 一致性"""
    print("[TEST] 8. 测试 workflow.yaml 一致性...")
    try:
        from scripts.pipeline_manager import (
            STAGE_ORDER, STAGE_GATES, STAGE_DEPS, STAGE_AGENTS,
            STAGE_MEETINGS, WORKFLOW_GATES,
        )

        # 验证阶段数量
        assert len(STAGE_ORDER) >= 12, f"阶段数不足: {len(STAGE_ORDER)}"

        # 验证依赖链无循环
        visited = set()
        for stage in STAGE_ORDER:
            deps = STAGE_DEPS.get(stage, [])
            for dep in deps:
                assert dep in visited, f"依赖 {dep} 在 {stage} 之前未出现（DAG 断裂）"
            visited.add(stage)

        # 验证门禁定义存在
        assert len(WORKFLOW_GATES) >= 24, f"门禁定义不足: {len(WORKFLOW_GATES)}"

        # 验证关键门禁已挂载
        all_gates = set()
        for gates in STAGE_GATES.values():
            all_gates.update(gates)
        assert "G5_S8_CONTENT_READY" in all_gates, "S8 缺少 G5_S8_CONTENT_READY 门禁"
        assert "G3_parallel_merge" in all_gates, "S5 缺少 G3_parallel_merge 门禁"

        print(f"  [PASS] workflow.yaml 一致: {len(STAGE_ORDER)} stages, {len(WORKFLOW_GATES)} gates, DAG 无环")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_gate_contracts():
    """测试 gate_contracts.py 合约完整性"""
    print("[TEST] 9. 测试 gate_contracts.py 合约完整性...")
    try:
        from scripts.gate_contracts import GATE_CONTRACTS

        # 验证合约数量
        assert len(GATE_CONTRACTS) >= 20, f"合约数不足: {len(GATE_CONTRACTS)}"

        # 验证无重复键（Python dict 自动去重，但检查是否有 alias 遗漏）
        required_contracts = [
            "G1_PROBLEM_PARSED",
            "G2_METHOD_VALIDATED",
            "G3_CODE_REVIEWED",
            "G3_BASELINE_COMPARED",
            "G3_PARALLEL_MERGE",
            "G4_RESULTS_FROZEN",
            "G5_S8_CONTENT_READY",
            "G6_AUDIT_LAYER_PASSED",
            "G6_APPENDIX_COMPLETE",
            "ABSTRACT_QUALITY_GATE_V2",
        ]
        missing = [c for c in required_contracts if c not in GATE_CONTRACTS]
        if missing:
            print(f"  [FAIL] 缺少合约: {missing}")
            return False

        # 验证每个合约有必需字段
        for gate_id, contract in GATE_CONTRACTS.items():
            assert "description" in contract, f"{gate_id} 缺少 description"
            assert "enter_condition" in contract, f"{gate_id} 缺少 enter_condition"
            assert "pass_criteria" in contract, f"{gate_id} 缺少 pass_criteria"
            assert "fail_fallback" in contract, f"{gate_id} 缺少 fail_fallback"

        print(f"  [PASS] gate_contracts.py 完整: {len(GATE_CONTRACTS)} 个合约, 无缺失字段")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


if __name__ == "__main__":
    tests = [
        test_core_files_exist,
        test_no_llm_client,
        test_pipeline_manager,
        test_meeting_protocol,
        test_tool_scripts,
        test_stage_agent_instructions,
        test_skill_md,
        test_workflow_yaml,
        test_gate_contracts,
    ]
    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n{'='*50}")
    print(f"结果: {passed}/{total} 通过")
    if passed == total:
        print("全部通过！v3.0.0 Codex 原生架构验证成功。")
    else:
        print("有测试失败，请检查。")
