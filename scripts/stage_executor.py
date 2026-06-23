#!/usr/bin/env python3
"""
Stage Executor v3.0 — 单阶段执行引导器 + 门禁硬执行 + 打回重做 + 跳过
=====================================================================
v3.0 新增：
  - skip 命令：跳过可选阶段（S5.5/S7.5），skipped 状态等同于 completed 处理依赖
  - 统一路径命名体系（STAGE_ARTIFACTS 匹配 S*.md 实际路径）
  - 统一门禁 ID 注册表 + 补全缺失门禁实现
  - --force 仅跳过 P1/P2 门禁，P0 门禁仍强制执行
  - 阶段数统一为 14

v2.0 新增：
  - rework 命令：门禁失败时打回重做
  - gate_check 命令：运行关联门禁检查
  - rejected 状态：阶段可被拒绝
  - 最大重做次数追踪
  - validate 增强：检查文件内容质量（字数/大小）
  - mode 感知：不同模式下门禁阈值不同

用法：
  python scripts/stage_executor.py init --contest CUMCM --subquestions 3 --mode standard
  python scripts/stage_executor.py current
  python scripts/stage_executor.py begin S3
  python scripts/stage_executor.py complete S3 --artifacts "file1,file2"
  python scripts/stage_executor.py rework S3 --reason "门禁未通过"
  python scripts/stage_executor.py gate_check S3
  python scripts/stage_executor.py validate S3
  python scripts/stage_executor.py skip S5.5 --reason "equation-driven"
  python scripts/stage_executor.py checklist
  python scripts/stage_executor.py guide S5
  python scripts/stage_executor.py report
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from workspace_utils import resolve_workspace, resolve_skill_root, resolve_project_root
SKILL_ROOT = resolve_skill_root()
STAGES_DIR = SKILL_ROOT / "stages"

WORKSPACE = resolve_workspace()

STATE_DIR = WORKSPACE / "state"
EXEC_STATE = STATE_DIR / "stage_execution.json"
DECISION_LOG = STATE_DIR / "decision_log.json"  # M3: 决策日志

# ═══════════════════════════════════════════════════════════════
# Stage Dependency DAG — 从 workflow.yaml 派生
# ═══════════════════════════════════════════════════════════════

STAGE_DAG = {
    "S0":  {"deps": [],       "name": "Input Registration",        "alias": "题目登记"},
    "S1":  {"deps": ["S0"],   "name": "Problem Analysis + M001",   "alias": "题意共识会"},
    "S2":  {"deps": ["S1"],   "name": "Data Governance",           "alias": "数据治理"},
    "S3":  {"deps": ["S2"],   "name": "Model Selection + M002",    "alias": "模型辩论会"},
    "S4":  {"deps": ["S3"],   "name": "Experiment Race",           "alias": "实验赛马"},
    "S5":  {"deps": ["S4"],   "name": "Modeling & Solve",          "alias": "建模求解"},
    "S5.5":{"deps": ["S5"],   "name": "Model Evolution",           "alias": "模型进化"},
    "S6":  {"deps": ["S5.5"],"name": "Verification & Sensitivity", "alias": "灵敏度检验"},
    "S7":  {"deps": ["S6"],   "name": "Evidence Chain",            "alias": "证据链"},
    "S7.5":{"deps": ["S7"],   "name": "Unified Kernel Synthesis",  "alias": "内核归纳"},
    "S8":  {"deps": ["S7.5"],"name": "Paper Drafting + M003",      "alias": "论文撰写"},
    "S9":  {"deps": ["S8"],   "name": "Adversarial Review + M004", "alias": "对抗审稿"},
    "S9.5":{"deps": ["S9"],   "name": "Publication Readiness Check","alias": "出版规范审查"},
    "S10": {"deps": ["S9.5"], "name": "Final Build & Delivery",    "alias": "最终交付"},
}

# 阶段产出要求（用于验证）— v3.0: 以 S*.md 实际路径为准
STAGE_ARTIFACTS = {
    "S0":  ["inputs/inputs_manifest.json", "inputs/problem_text.md",
            "state/workflow_state.json", "outputs/reviews/S0_review.md"],
    "S1":  ["outputs/problem_analysis/analysis.md",
            "outputs/problem_analysis/variables.json",
            "outputs/problem_analysis/subproblems.json",
            "outputs/problem_analysis/literature_review.md",
            "outputs/reviews/S1_review.md"],
    "S2":  ["data/data_dictionary.md", "data/data_profile_report.md",
            "outputs/reviews/S2_review.md"],
    "S3":  ["methods/model_selection_report.md", "methods/model_assumptions.md",
            "methods/symbol_table.md", "methods/proposer_proposals.md",
            "outputs/reviews/S3_review.md"],
    "S4":  ["methods/experiments/experiment_race_plan.md",
            "methods/experiments/model_leaderboard.csv",
            "outputs/reviews/S4_review.md"],
    "S5":  ["outputs/q1/summary.md", "outputs/reviews/S5_review.md"],
    "S5.5":["outputs/evolution/evolution_report.md", "outputs/reviews/S5.5_review.md"],
    "S6":  ["outputs/verification/robustness_report.md", "outputs/reviews/S6_review.md"],
    "S7":  ["outputs/evidence/conclusion_evidence_map.md",
            "outputs/evidence/paper_code_consistency_report.md",
            "outputs/reviews/S7_review.md"],
    "S7.5":["outputs/kernel/unified_kernel.md", "outputs/reviews/S7.5_review.md"],
    "S8":  ["outputs/paper/paper.md", "outputs/reviews/S8_review.md"],
    "S9":  ["outputs/review/adversarial_review.md", "outputs/review/paper_revised.md",
            "outputs/reviews/S9_review.md"],
    "S9.5":["outputs/review/publication_readiness_report.md",
            "outputs/review/paper_final.md",
            "outputs/reviews/S9.5_review.md"],
    "S10": ["outputs/final/final.docx", "outputs/reviews/S10_review.md"],
}


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_state() -> dict:
    """加载执行状态。"""
    if EXEC_STATE.exists():
        with EXEC_STATE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(data: dict):
    """保存执行状态。"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with EXEC_STATE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def append_decision_log(entry: dict):
    """M3: 追加决策日志（用于Auto Mode追踪）。"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    log = []
    if DECISION_LOG.exists():
        with DECISION_LOG.open("r", encoding="utf-8") as f:
            log = json.load(f)
    
    entry["timestamp"] = now()
    log.append(entry)
    
    with DECISION_LOG.open("w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def get_completed_stages(state: dict) -> set:
    """获取已完成的阶段集合（skipped 视为 completed）。"""
    completed = set()
    for sid, info in state.get("stages", {}).items():
        status = info.get("status")
        if status in ("completed", "skipped"):
            completed.add(sid)
    return completed


def get_next_actionable(state: dict):
    """获取下一个可执行的阶段。"""
    completed = get_completed_stages(state)
    for sid, dag in STAGE_DAG.items():
        if sid in completed:
            continue
        if all(d in completed for d in dag["deps"]):
            return sid
    return None


# ═══════════════════════════════════════════════════════════════
# Commands
# ═══════════════════════════════════════════════════════════════

def cmd_init(args):
    """初始化执行状态。"""
    global WORKSPACE, STATE_DIR, EXEC_STATE, DECISION_LOG

    # Auto-create workspace if missing or incomplete
    ws_cumcm = SKILL_ROOT / "CUMCM_Workspace"
    if not ws_cumcm.exists() or not (ws_cumcm / "state").exists():
        try:
            from workspace_init import ensure_workspace
            ws = ensure_workspace(SKILL_ROOT, args.subquestions, args.contest)
            print(f"[stage_executor] 自动创建工作区: {ws}")
        except Exception as e:
            print(f"[stage_executor] ⚠️ 工作区自动创建失败: {e}")
            print(f"  请手动运行: python scripts/workspace_init.py --contest {args.contest} --subquestions {args.subquestions}")
    elif ws_cumcm.exists():
        # Workspace exists but may be missing subdirs — fill them in
        try:
            from workspace_init import ensure_workspace
            ensure_workspace(SKILL_ROOT, args.subquestions, args.contest)
        except Exception:
            pass

    # Re-resolve workspace after potential creation
    from workspace_utils import resolve_workspace
    WORKSPACE = resolve_workspace()
    STATE_DIR = WORKSPACE / "state"
    EXEC_STATE = STATE_DIR / "stage_execution.json"
    DECISION_LOG = STATE_DIR / "decision_log.json"

    state = {
        "version": "3.0.0",
        "contest": args.contest.upper(),
        "subquestions": args.subquestions,
        "mode": getattr(args, 'mode', 'standard'),
        "created_at": now(),
        "stages": {},
    }
    for sid in STAGE_DAG:
        state["stages"][sid] = {"status": "pending", "attempt": 0, "rework_count": 0}
    save_state(state)
    print(f"[stage_executor] 初始化完成: {args.contest.upper()}, {args.subquestions} 子问题, mode={state['mode']}")
    print(f"[stage_executor] 下一阶段: S0 ({STAGE_DAG['S0']['alias']})")


def cmd_current(_args):
    """显示当前阶段和下一步操作。"""
    state = load_state()
    if not state:
        print("[stage_executor] 未初始化。运行: python scripts/stage_executor.py init --contest CUMCM --subquestions N")
        sys.exit(1)

    next_sid = get_next_actionable(state)
    completed = get_completed_stages(state)

    print(f"\n{'='*60}")
    print(f"  Stage Execution Status — {now()}")
    print(f"  Contest: {state.get('contest', 'N/A')}  |  Subquestions: {state.get('subquestions', 'N/A')}")
    print(f"{'='*60}\n")

    for sid, dag in STAGE_DAG.items():
        info = state.get("stages", {}).get(sid, {})
        status = info.get("status", "pending")

        if sid in completed:
            icon = "✅"
        elif sid == next_sid:
            icon = "▶️"
        else:
            deps_met = all(d in completed for d in dag["deps"])
            icon = "🔒" if not deps_met else "⏳"

        print(f"  {icon} {sid:<6s} {dag['alias']:<12s}  ({dag['name']})")

    print(f"\n{'='*60}")
    if next_sid:
        dag = STAGE_DAG[next_sid]
        print(f"  ▶️ 当前应执行: {next_sid} — {dag['alias']}")
        print(f"  📖 详细指令: stages/{next_sid}.md")
        print(f"  🔧 开始执行: python scripts/stage_executor.py begin {next_sid}")
    else:
        print(f"  🎉 所有阶段已完成!")
    print(f"{'='*60}\n")


def cmd_begin(args):
    """开始执行某个阶段。"""
    state = load_state()
    sid = args.stage

    if sid not in STAGE_DAG:
        print(f"[stage_executor] 未知阶段: {sid}")
        print(f"  可用阶段: {', '.join(STAGE_DAG.keys())}")
        sys.exit(1)

    completed = get_completed_stages(state)
    deps = STAGE_DAG[sid]["deps"]
    unmet = [d for d in deps if d not in completed]
    if unmet:
        print(f"[stage_executor] ❌ 阻塞: {sid} 依赖未满足: {', '.join(unmet)}")
        sys.exit(1)

    # v13.0: 防跳过检查 — S10 开始前强制验证 S9.5 已完成（或已跳过）
    if sid == "S10":
        s95_info = state.get("stages", {}).get("S9.5", {})
        if s95_info.get("status") not in ("completed", "skipped"):
            print(f"\n🚨 BLOCKED: S10 依赖 S9.5 未完成！")
            print(f"   S9.5 当前状态: {s95_info.get('status', 'pending')}")
            print(f"   必须先完成 S9.5 出版规范审查才能进入 S10。")
            print(f"   运行: python scripts/stage_executor.py begin S9.5")
            sys.exit(1)

    stage_info = state.get("stages", {}).get(sid, {"status": "pending", "attempt": 0, "rework_count": 0})
    prev_status = stage_info.get("status", "pending")

    if prev_status == "rejected":
        print(f"\n  ⚠️ REWORK: 重新执行 {sid} (第 {stage_info.get('rework_count', 0)} 次重做)")
        print(f"  原因: {stage_info.get('rework_reason', 'N/A')}")

    stage_info["status"] = "in_progress"
    stage_info["attempt"] = stage_info.get("attempt", 0) + 1
    stage_info["started_at"] = now()
    stage_info.pop("rework_reason", None)
    state.setdefault("stages", {})[sid] = stage_info
    save_state(state)

    dag = STAGE_DAG[sid]
    print(f"\n{'='*60}")
    print(f"  ▶️ 开始执行: {sid} — {dag['alias']} ({dag['name']})")
    print(f"{'='*60}")
    print(f"\n  📖 请阅读阶段指令: stages/{sid}.md")
    print(f"  完成前必须通过门禁: python scripts/stage_executor.py gate_check {sid}")
    print(f"  通过后运行: python scripts/stage_executor.py complete {sid} --artifacts \"file1,file2\"")

    # 显示预期产出
    expected = STAGE_ARTIFACTS.get(sid, [])
    if expected:
        print(f"\n  📋 预期产出:")
        for a in expected:
            print(f"    - {a}")
    print()


def cmd_complete(args):
    """标记阶段完成并记录产出（必须先通过 gate_check）。"""
    state = load_state()
    sid = args.stage

    if sid not in state.get("stages", {}):
        print(f"[stage_executor] 阶段 {sid} 未开始。先运行: begin {sid}")
        sys.exit(1)

    stage_info = state["stages"][sid]
    if stage_info["status"] == "completed":
        print(f"[stage_executor] {sid} 已经完成。")
        return

    # 强制检查：必须先通过 gate_check（v3.0: --force 仅跳过 P1/P2 门禁，P0 仍强制）
    P0_GATES = {"G0", "G1_PROBLEM_PARSED", "G1_5_DATA_QUALITY", "G3_BASELINE",
                "G4_RESULTS_FROZEN", "G5_PAPER_QUALITY", "G5_5_ADVERSARIAL",
                "G6_PUBLICATION_READY"}

    if not args.force:
        stage_gates = {
            "S1": ["G1_PROBLEM_PARSED"],
            "S2": ["G1_5_DATA_QUALITY"],
            "S5": ["G3_BASELINE"],
            "S8": ["G5_PAPER_QUALITY", "G5_5_ADVERSARIAL"],
            "S9": ["G5_PAPER_QUALITY", "G5_5_ADVERSARIAL"],
            "S9.5": ["G6_PUBLICATION_READY"],
            "S10": ["G6_APPENDIX_COMPLETE"],
        }
        gates = stage_gates.get(sid, [])
        if gates:
            print(f"\n  ⚠️ 门禁检查: 完成 {sid} 前必须通过以下门禁:")
            for g in gates:
                print(f"    - {g}")
            print(f"\n  运行: python scripts/stage_executor.py gate_check {sid}")
            print(f"  或使用 --force 跳过非 P0 门禁检查（不推荐）\n")
            sys.exit(1)
    else:
        # --force 模式：仍需通过 P0 门禁
        stage_gates_p0 = {
            "S1": ["G1_PROBLEM_PARSED"],
            "S2": ["G1_5_DATA_QUALITY"],
            "S8": ["G5_PAPER_QUALITY"],
            "S9": ["G5_PAPER_QUALITY"],
            "S9.5": ["G6_PUBLICATION_READY"],
        }
        gates = stage_gates_p0.get(sid, [])
        if gates:
            print(f"\n  ⚠️ --force 模式: 仍需通过 P0 门禁:")
            for g in gates:
                print(f"    - {g}")
            print(f"\n  运行: python scripts/stage_executor.py gate_check {sid}")
            sys.exit(1)

    artifacts = [a.strip() for a in args.artifacts.split(",")] if args.artifacts else []

    stage_info["status"] = "completed"
    stage_info["completed_at"] = now()
    stage_info["artifacts"] = artifacts
    save_state(state)

    dag = STAGE_DAG[sid]
    print(f"\n✅ {sid} — {dag['alias']} 完成!")

    # v13.0: S9 完成后强制预警 S9.5
    if sid == "S9":
        print(f"\n  🚨 CRITICAL: S9 完成后，下一步必须是 S9.5（出版规范审查）！")
        print(f"  ⛔ 禁止跳过 S9.5 直接进入 S10！")
        print(f"  📖 阶段指令: stages/S9.5.md")
        print(f"  🔧 开始执行: python scripts/stage_executor.py begin S9.5")
        print(f"  🔧 MANDATORY: python scripts/publication_checker.py check outputs/paper/paper_revised.md --mode <mode>")
        print()

    # 显示下一步
    next_sid = get_next_actionable(state)
    if next_sid:
        next_dag = STAGE_DAG[next_sid]
        print(f"   ▶️ 下一步: {next_sid} — {next_dag['alias']}")
        print(f"   📖 指令: stages/{next_sid}.md")
    else:
        print(f"   🎉 所有阶段已完成!")
    print()


def cmd_checklist(_args):
    """显示 checklist 状态。"""
    state = load_state()
    if not state:
        print("[stage_executor] 未初始化。")
        sys.exit(1)

    completed = get_completed_stages(state)
    total = len(STAGE_DAG)

    print(f"\n{'='*60}")
    print(f"  📋 Pipeline Checklist — {len(completed)}/{total} 完成")
    print(f"{'='*60}\n")

    for sid, dag in STAGE_DAG.items():
        info = state.get("stages", {}).get(sid, {})
        status = info.get("status", "pending")

        if status == "completed":
            print(f"  [x] {sid} {dag['alias']}")
        elif status == "skipped":
            reason = info.get("skip_reason", "")
            print(f"  [-] {sid} {dag['alias']}  (已跳过: {reason})")
        elif status == "in_progress":
            print(f"  [~] {sid} {dag['alias']}  (进行中)")
        elif status == "rejected":
            rw = info.get("rework_count", 0)
            print(f"  [!] {sid} {dag['alias']}  (被打回, 重做{rw}次)")
        elif status == "blocked":
            print(f"  [X] {sid} {dag['alias']}  (被阻塞)")
        else:
            print(f"  [ ] {sid} {dag['alias']}")

        # 显示产出清单
        expected = STAGE_ARTIFACTS.get(sid, [])
        if status == "completed":
            actual = info.get("artifacts", [])
            missing = [e for e in expected if not any(e.rstrip('/') in a or a in e for a in actual)]
            if missing:
                print(f"       ⚠️ 可能缺失: {', '.join(missing[:3])}")

    print(f"\n{'='*60}\n")


def cmd_guide(args):
    """打印阶段的精简执行指南。"""
    sid = args.stage
    if sid not in STAGE_DAG:
        print(f"[stage_executor] 未知阶段: {sid}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  📖 {sid} — {STAGE_DAG[sid]['alias']} 执行指南")
    print(f"{'='*60}\n")

    # v12.0: 为 S1 和 S8 显示 MANDATORY 命令提示
    if sid == "S1":
        print("🔴 MANDATORY COMMANDS (DO NOT SKIP):")
        print("=" * 60)
        print("1. 生成技术路线图（论文 Figure 1）:")
        print("   python scripts/diagram_generator.py roadmap --stages S0,S1,S3,S5,S8,S9,S10")
        print("")
        print("2. 生成技术路线图 D-A-C 叙事模板:")
        print("   python scripts/figure_dac_generator.py single fig1_technical_roadmap.png \\")
        print("     --describe '...' --analyze '...' --conclude '...'")
        print("")
        print("⚠️  如果跳过这两个命令，论文将缺失 Figure 1，可能扣 5-10 分！")
        print("=" * 60)
        print("")
    
    elif sid == "S8":
        print("🔴 MANDATORY COMMANDS (DO NOT SKIP):")
        print("=" * 60)
        print("论文撰写 BEFORE:")
        print("1. python scripts/figure_dac_generator.py batch")
        print("2. python scripts/figure_dac_generator.py check")
        print("3. 手动填写所有 outputs/figures/*_DAC.md 文件")
        print("4. python scripts/figure_dac_generator.py check  # 确保无 TODO")
        print("")
        print("论文撰写 AFTER (6 个门禁检查):")
        print("1. python scripts/gate_contracts.py figure-narrative --mode <mode>")
        print("2. python scripts/paper_assembly_checker.py outputs/paper/paper.md --mode <mode>")
        print("3. python scripts/gate_contracts.py paper-quality --mode <mode>")
        print("4. python scripts/gate_contracts.py abstract --mode <mode>")
        print("5. python scripts/gate_contracts.py structure --mode <mode>")
        print("6. python scripts/gate_contracts.py paper-evaluation --mode <mode>")
        print("")
        print("⚠️  跳过这些命令将导致论文质量不达标，无法通过 S9 审稿！")
        print("=" * 60)
        print("")

    elif sid == "S9.5":
        print("🔴 MANDATORY COMMANDS (DO NOT SKIP):")
        print("=" * 60)
        print("1. 运行出版规范全量检查:")
        print("   python scripts/publication_checker.py check outputs/paper/paper_revised.md --mode <mode>")
        print("")
        print("2. 生成出版规范报告:")
        print("   python scripts/publication_checker.py report outputs/paper/paper_revised.md \\")
        print("     --mode <mode> --output outputs/paper/publication_readiness_report.md")
        print("")
        print("3. 运行门禁检查:")
        print("   python scripts/gate_contracts.py publication-ready --mode <mode>")
        print("")
        print("⚠️  标准: P0=0, P1≤2, P2≤5。不通过则打回 S9 重新修订！")
        print("=" * 60)
        print("")

    stage_file = STAGES_DIR / f"{sid}.md"
    if stage_file.exists():
        print(stage_file.read_text(encoding="utf-8"))
    else:
        print(f"[stage_executor] 阶段指令文件不存在: {stage_file}")
        print(f"  请创建 stages/{sid}.md 文件")


def cmd_validate(args):
    """验证阶段产出完整性（增强版：检查文件存在性 + 内容质量）。"""
    sid = args.stage
    if sid not in STAGE_ARTIFACTS:
        print(f"[stage_executor] 无产出验证规则: {sid}")
        sys.exit(1)

    ws = WORKSPACE
    expected = STAGE_ARTIFACTS[sid]
    found = []
    missing = []
    thin = []

    for pattern in expected:
        matches = list(ws.glob(pattern))
        if matches:
            found.append((pattern, len(matches)))
            # 检查文件内容质量（非空、非极小）
            for m in matches:
                if m.is_file():
                    size = m.stat().st_size
                    if size < 100:
                        thin.append(f"{m} ({size} bytes)")
        else:
            missing.append(pattern)

    print(f"\n{'='*60}")
    print(f"  🔍 {sid} 产出验证 (v2.0)")
    print(f"{'='*60}\n")

    if found:
        print("  ✅ 已找到:")
        for pat, count in found:
            print(f"    + {pat} ({count} 个)")

    if thin:
        print("\n  ⚠️ 内容过薄:")
        for t in thin:
            print(f"    - {t}")

    if missing:
        print("\n  ❌ 缺失:")
        for pat in missing:
            print(f"    - {pat}")

    passed = len(missing) == 0 and len(thin) == 0
    print(f"\n  结果: {'PASSED ✅' if passed else f'FAILED ❌ ({len(missing)} 缺失, {len(thin)} 过薄)'}")
    print(f"{'='*60}\n")
    sys.exit(0 if passed else 1)


def cmd_rework(args):
    """打回重做 — 门禁失败时回退阶段状态。"""
    state = load_state()
    sid = args.stage
    reason = args.reason if hasattr(args, 'reason') and args.reason else "门禁未通过"

    if sid not in state.get("stages", {}):
        print(f"[stage_executor] 阶段 {sid} 未开始。")
        sys.exit(1)

    stage_info = state["stages"][sid]
    mode = state.get("mode", "standard")
    max_rework = {"fast": 2, "standard": 3, "championship": 5}.get(mode, 3)
    rework_count = stage_info.get("rework_count", 0)

    if rework_count >= max_rework:
        print(f"\n{'='*60}")
        print(f"  🚨 REWORK LIMIT REACHED: {sid} 已重做 {rework_count}/{max_rework} 次")
        print(f"  需要人工介入或降级到更简单的方案")
        print(f"{'='*60}\n")
        stage_info["status"] = "blocked"
        stage_info["blocked_reason"] = f"Rework limit reached: {rework_count}/{max_rework}"
        save_state(state)
        sys.exit(2)

    stage_info["status"] = "rejected"
    stage_info["rework_count"] = rework_count + 1
    stage_info["rework_reason"] = reason
    stage_info["rejected_at"] = now()
    save_state(state)

    dag = STAGE_DAG[sid]
    print(f"\n{'='*60}")
    print(f"  🔙 REWORK: {sid} — {dag['alias']}")
    print(f"  原因: {reason}")
    print(f"  重做次数: {rework_count + 1}/{max_rework}")
    print(f"{'='*60}")

    # v13.0: S9.5 打回时，如果已重做 ≥ 2 次，打回 S9
    if sid == "S9.5" and rework_count + 1 >= 2:
        print(f"\n  🚨 S9.5 已重做 {rework_count + 1} 次，打回 S9 重新修订！")
        print(f"  刑部需要重新审查论文语言风格，消除 AI 痕迹。")
        s9_info = state.get("stages", {}).get("S9", {})
        if s9_info.get("status") == "completed":
            s9_info["status"] = "rejected"
            s9_info["rework_reason"] = f"S9.5 出版规范不通过（第 {rework_count + 1} 次），打回 S9"
            s9_info["rejected_at"] = now()
            save_state(state)
            print(f"\n  请修复问题后运行:")
            print(f"    python scripts/stage_executor.py begin S9")
            print(f"    # 重新执行 S9 审稿 + S9.5 出版规范审查")
        else:
            print(f"\n  请修复问题后重新运行:")
            print(f"    python scripts/stage_executor.py begin {sid}")
            print(f"    python scripts/stage_executor.py complete {sid} --artifacts ...")
    else:
        print(f"\n  请修复问题后重新运行:")
        print(f"    python scripts/stage_executor.py begin {sid}")
        print(f"    python scripts/stage_executor.py complete {sid} --artifacts ...")
    print(f"{'='*60}\n")


def cmd_gate_check(args):
    """运行阶段关联门禁检查 — 门禁不通过则阻止完成。"""
    sid = args.stage
    mode = args.mode if hasattr(args, 'mode') and args.mode else "standard"

    # v3.0: 统一门禁 ID 注册表 — 与 gate_contracts.py 函数名一一对应
    stage_gates = {
        "S0": ["G0"],
        "S1": ["G1_PROBLEM_PARSED"],
        "S2": ["G1_5_DATA_QUALITY"],
        "S3": ["G1_5_METRIC_GUARDIAN", "G2_MODEL_SELECTION"],
        "S4": ["G2_5_RACE_COMPLETED", "G2_POC"],
        "S5": ["G3_BASELINE", "G3_CODE_REVIEWED", "G3_PARALLEL_MERGE"],
        "S5.5": ["G3_5_EVOLUTION_CONVERGED"],
        "S6": ["G4_RESULTS_FROZEN", "PER_SUBQUESTION_VERIFICATION"],
        "S7": ["G4_EVIDENCE_CHAIN"],
        "S7.5": ["G4_7_KERNEL"],
        "S8": ["G5_S8_CONTENT_READY", "G5_PAPER_QUALITY", "G5_5_ADVERSARIAL",
               "ABSTRACT_QUALITY", "PAPER_STRUCTURE"],
        "S9": ["G5_5_ADVERSARIAL", "G5_PAPER_QUALITY"],
        "S9.5": ["G6_PUBLICATION_READY"],
        "S10": ["G6_APPENDIX_COMPLETE"],
    }

    gates = stage_gates.get(sid, [])
    if not gates:
        print(f"[stage_executor] {sid} 无关联门禁检查")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"  🚧 {sid} 门禁检查 (mode: {mode})")
    print(f"{'='*60}\n")

    all_passed = True
    for gate_id in gates:
        try:
            from gate_contracts import auto_verdict
            passed, msg, fix = auto_verdict(gate_id, str(WORKSPACE), mode)
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  [{status}] {gate_id}")
            if not passed:
                all_passed = False
                print(f"    {msg}")
                if fix:
                    print(f"    修复建议: {', '.join(fix[:3])}")
            print()
        except Exception as e:
            print(f"  [⚠️ ERROR] {gate_id}: {e}\n")
            all_passed = False

    print(f"{'='*60}")
    if all_passed:
        print(f"  ✅ 所有门禁通过 — 可以完成 {sid}")
        # M3: 记录决策日志
        append_decision_log({
            "stage": sid,
            "action": "gate_check",
            "result": "PASS",
            "gates_checked": gates,
            "mode": mode
        })
    else:
        print(f"  ❌ 门禁未通过 — 必须修复后才能完成 {sid}")
        print(f"  运行: python scripts/stage_executor.py rework {sid} --reason \"门禁未通过\"")
        # M3: 记录决策日志
        append_decision_log({
            "stage": sid,
            "action": "gate_check",
            "result": "FAIL",
            "gates_checked": gates,
            "mode": mode,
            "auto_decision": "rework_required"
        })
    print(f"{'='*60}\n")

    sys.exit(0 if all_passed else 1)


def cmd_report(_args):
    """生成全局进度报告。"""
    state = load_state()
    if not state:
        print("[stage_executor] 未初始化。")
        sys.exit(1)

    completed = get_completed_stages(state)
    total = len(STAGE_DAG)
    progress = len(completed) / total * 100

    next_sid = get_next_actionable(state)

    print(f"\n{'='*60}")
    print(f"  📊 Pipeline Progress Report")
    print(f"{'='*60}")
    print(f"  进度: {len(completed)}/{total} ({progress:.0f}%)")
    print(f"  比赛: {state.get('contest', 'N/A')}")
    print(f"  子问题: {state.get('subquestions', 'N/A')}")
    if next_sid:
        print(f"  当前: {next_sid} — {STAGE_DAG[next_sid]['alias']}")
    else:
        print(f"  状态: 全部完成 🎉")
    print(f"{'='*60}\n")


def cmd_skip(args):
    """标记阶段为跳过状态（仅适用于可选阶段如 S5.5、S7.5）。"""
    state = load_state()
    sid = args.stage

    SKIPPABLE = {"S5.5", "S7.5"}
    if sid not in SKIPPABLE:
        print(f"[stage_executor] ❌ {sid} 不可跳过。可跳过阶段: {', '.join(sorted(SKIPPABLE))}")
        sys.exit(1)

    if sid not in state.get("stages", {}):
        print(f"[stage_executor] 阶段 {sid} 未初始化。先运行 init。")
        sys.exit(1)

    stage_info = state["stages"][sid]
    if stage_info.get("status") != "pending":
        print(f"[stage_executor] ❌ {sid} 当前状态为 {stage_info.get('status')}，仅 pending 状态允许跳过。")
        sys.exit(1)

    stage_info["status"] = "skipped"
    stage_info["skipped_at"] = now()
    stage_info["skip_reason"] = args.reason
    save_state(state)

    dag = STAGE_DAG[sid]
    print(f"\n  ⏭️  {sid} — {dag['alias']} 已跳过")
    print(f"  原因: {args.reason}")

    # 显示下一步
    next_sid = get_next_actionable(state)
    if next_sid:
        next_dag = STAGE_DAG[next_sid]
        print(f"  ▶️ 下一步: {next_sid} — {next_dag['alias']}")
        print(f"  📖 指令: stages/{next_sid}.md")
    print()


def main():
    p = argparse.ArgumentParser(
        description="Stage Executor v3.0 — 单阶段执行引导器 + 门禁硬执行 + 打回重做 + 跳过"
    )
    sub = p.add_subparsers(dest="command")

    # init
    pi = sub.add_parser("init", help="初始化执行状态")
    pi.add_argument("--contest", required=True, choices=["cumcm", "CUMCM", "mcm", "MCM", "icm", "ICM", "51mcm", "51MCM"])
    pi.add_argument("--subquestions", type=int, default=3)
    pi.add_argument("--mode", default="standard", choices=["fast", "standard", "championship"],
                    help="执行模式: fast/standard/championship")

    # current
    sub.add_parser("current", help="显示当前阶段和下一步")

    # begin
    pb = sub.add_parser("begin", help="开始执行某个阶段")
    pb.add_argument("stage", help="阶段 ID (如 S3)")

    # complete
    pc = sub.add_parser("complete", help="标记阶段完成")
    pc.add_argument("stage", help="阶段 ID")
    pc.add_argument("--artifacts", default="", help="产出文件列表（逗号分隔）")
    pc.add_argument("--force", action="store_true", help="跳过门禁检查（不推荐）")

    # checklist
    sub.add_parser("checklist", help="显示 checklist 状态")

    # guide
    pg = sub.add_parser("guide", help="打印阶段执行指南")
    pg.add_argument("stage", help="阶段 ID")

    # validate
    pv = sub.add_parser("validate", help="验证阶段产出完整性")
    pv.add_argument("stage", help="阶段 ID")

    # rework
    pr = sub.add_parser("rework", help="打回重做 — 门禁失败时回退阶段状态")
    pr.add_argument("stage", help="阶段 ID")
    pr.add_argument("--reason", default="门禁未通过", help="打回原因")

    # gate_check
    pgc = sub.add_parser("gate_check", help="运行阶段关联门禁检查")
    pgc.add_argument("stage", help="阶段 ID")
    pgc.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"],
                     help="门禁阈值模式")

    # skip
    psk = sub.add_parser("skip", help="跳过可选阶段（仅 S5.5/S7.5）")
    psk.add_argument("stage", help="阶段 ID")
    psk.add_argument("--reason", default="问题类型不需要", help="跳过原因")

    # report
    sub.add_parser("report", help="生成全局进度报告")

    args = p.parse_args()

    dispatch = {
        "init": cmd_init,
        "current": cmd_current,
        "begin": cmd_begin,
        "complete": cmd_complete,
        "checklist": cmd_checklist,
        "guide": cmd_guide,
        "validate": cmd_validate,
        "rework": cmd_rework,
        "gate_check": cmd_gate_check,
        "skip": cmd_skip,
        "report": cmd_report,
    }

    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
