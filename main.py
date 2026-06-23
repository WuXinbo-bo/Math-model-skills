#!/usr/bin/env python3
"""
Meta-model-skills-max — 统一入口 (main.py v3.0.0)

Architecture:
  - The main Codex agent is the sole LLM and orchestrator.
  - Python scripts are pure tooling (state machine, file I/O, DOCX, figures).
  - workflow.yaml is the SINGLE SOURCE OF TRUTH for pipeline configuration.
  - This entry point provides all CLI utilities for state management, gates,
    quality checks, and tooling. No more scattered script invocations.

用法:
    python main.py init              # 初始化项目（从 workflow.yaml 加载阶段定义）
    python main.py status            # 查看项目状态
    python main.py workflow          # 查看 workflow.yaml 解析结果
    python main.py gates             # 列出所有门禁合约
    python main.py check-gate <id>   # 检查指定门禁
    python main.py meeting <id>      # 初始化会议模板
    python main.py freeze <Q>        # 冻结指定子问题的结果
    python main.py verify-freeze <Q> # 验证冻结一致性
    python main.py sandbox <code>    # 沙箱执行代码
    python main.py evidence <Q>      # 检查证据链
    python main.py audit             # 运行 G6 三重审计
    python main.py check-abstract <file>   # 摘要质量门禁
    python main.py check-derivation <file> # 推导链检查
    python main.py check-matrix <file>     # 方法选择矩阵检查
    python main.py check-discussion <file> # 多维度讨论检查
    python main.py check-expression <file> # 学术表达检查
    python main.py check-consistency <file> # 跨子问题一致性
    python main.py sensitivity init|sweep|check|report -q Q1  # 灵敏度分析
    python main.py check-abstract-consistency -a abs.md -b body.md  # 摘要一致性
    python main.py check-verification -q Q1  # 逐子问题验证
    python main.py model-evolve init|evolve|status -q Q1  # 模型进化搜索
    python main.py adversarial-review generate|check-rebuttal|report  # 红队审稿
    python main.py check-figure-narrative scan|check-dac|report  # 图表叙事D-A-C
    python main.py review-stage score|report|check  # 闭环评分
    python main.py docx analyze|map|replace|diff|verify  # DOCX 修订工具链
    python main.py docx-to-latex paper.docx              # DOCX 转 LaTeX
    python main.py compile-pdf paper.tex                 # 编译 LaTeX 为 PDF
    python main.py test              # 运行端到端测试
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
TESTS_DIR = PROJECT_ROOT / "tests"

# Ensure scripts/ is importable
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# ── Pipeline Management ──────────────────────────────────────

def cmd_init(args):
    """初始化 pipeline 状态机（从 workflow.yaml 加载阶段）"""
    from pipeline_manager import cmd_init as pm_init
    pm_init(args)


def cmd_status(args):
    """查看 pipeline 状态"""
    from pipeline_manager import cmd_status as pm_status
    pm_status(args)


def cmd_workflow(_args):
    """查看 workflow.yaml 解析结果"""
    from pipeline_manager import cmd_workflow_info
    cmd_workflow_info()


def cmd_meeting(args):
    """初始化会议模板"""
    from meeting_protocol import run as mtg_run
    result = mtg_run(args.meeting_id, args.stage_id)
    print(f"[main] 会议模板已生成: {result.get('status')}")


# ── Gate & Quality Management ────────────────────────────────

def cmd_gates(_args):
    """列出所有门禁合约"""
    from gate_contracts import print_gate_contracts
    print_gate_contracts()


def cmd_check_gate(args):
    """检查指定门禁"""
    from pipeline_manager import cmd_check_gate
    # Reconstruct args namespace for pipeline_manager
    ns = argparse.Namespace(gate_id=args.gate_id)
    cmd_check_gate(ns)


# ── Frozen Numbers ───────────────────────────────────────────

def cmd_freeze(args):
    """冻结子问题结果"""
    from frozen_numbers import cmd_freeze as freeze_cmd
    ns = argparse.Namespace(subquestion=args.subquestion, source=args.source)
    freeze_cmd(ns)


def cmd_verify_freeze(args):
    """验证冻结一致性"""
    from frozen_numbers import cmd_verify as verify_cmd
    ns = argparse.Namespace(subquestion=args.subquestion, strict=True)
    verify_cmd(ns)


# ── Math Sandbox ─────────────────────────────────────────────

def cmd_sandbox(args):
    """沙箱执行代码"""
    from math_sandbox import verify_code
    import json
    if args.code_file:
        code = Path(args.code_file).read_text(encoding="utf-8")
    elif args.code:
        code = args.code
    else:
        print("[main] 请提供 --code 或 --code-file")
        sys.exit(1)
    result = verify_code(code, timeout=args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["execution"]["success"] else 1)


# ── Evidence Chain ───────────────────────────────────────────

def cmd_evidence(args):
    """检查证据链"""
    from evidence_tracer import check_evidence_chain
    passed, msg = check_evidence_chain(args.subquestion)
    print(msg)
    sys.exit(0 if passed else 1)


# ── G6 Audit ─────────────────────────────────────────────────

def cmd_audit(args):
    """运行 G6 三重审计"""
    from gate_contracts import run_g6_audit_enhanced, print_g6_enhanced_report
    results = run_g6_audit_enhanced(args.workspace)
    print_g6_enhanced_report(results)
    sys.exit(0 if results["gate_passed"] else 1)


# ── M2: 高分能力增强模块 ──────────────────────────────────

def cmd_check_abstract(args):
    """摘要质量门禁 — 检查摘要是否包含模型、结果、公式、引用"""
    from abstract_quality_gate import check_abstract
    import json
    text = Path(args.file).read_text(encoding="utf-8")
    competition = getattr(args, "competition", "CUMCM")
    result = check_abstract(text, competition)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["passed"] else 1)


def cmd_check_derivation(args):
    """推导链检查 — 检查数学模型推导链完整性"""
    from derivation_chain_checker import check_derivation_chain
    import json
    text = Path(args.file).read_text(encoding="utf-8")
    result = check_derivation_chain(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["chain_complete"] else 1)


def cmd_check_matrix(args):
    """方法选择矩阵检查 — 确保有备选方法对比和选择理由"""
    from method_selection_matrix import check_decision_matrix
    import json
    text = Path(args.file).read_text(encoding="utf-8")
    result = check_decision_matrix(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["passed"] else 1)


def cmd_check_discussion(args):
    """多维度讨论检查 — 确保结果讨论覆盖关键维度"""
    from discussion_enhancer import check_discussion
    import json
    text = Path(args.file).read_text(encoding="utf-8")
    result = check_discussion(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["passed"] else 1)


def cmd_check_expression(args):
    """学术表达检查 — 检测口语化和低信息量表达"""
    from academic_expression_checker import check_expression
    import json
    text = Path(args.file).read_text(encoding="utf-8")
    result = check_expression(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["passed"] else 1)


def cmd_check_consistency(args):
    """跨子问题一致性 — 检查变量、单位、假设一致性"""
    from cross_subquestion_consistency import check_consistency
    import json
    text = Path(args.file).read_text(encoding="utf-8")
    result = check_consistency(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["passed"] else 1)


# ── M3: 深度实验检验模块 ──────────────────────────────────

def cmd_sensitivity(args):
    """灵敏度分析 — 参数扫描 + 鲁棒性判定"""
    from sensitivity_analysis import cmd_init as sen_init, cmd_sweep as sen_sweep
    from sensitivity_analysis import cmd_check as sen_check, cmd_report as sen_report
    dispatch = {"init": sen_init, "sweep": sen_sweep, "check": sen_check, "report": sen_report}
    if args.sensitivity_cmd in dispatch:
        dispatch[args.sensitivity_cmd](args)
    else:
        print("[main] Unknown sensitivity subcommand. Use: init|sweep|check|report")


def cmd_check_abstract_consistency(args):
    """摘要-全文一致性审计 — 比对摘要数字与正文/frozen_numbers"""
    from abstract_body_consistency import cmd_check as abc_check
    abc_check(args)


def cmd_check_verification(args):
    """逐子问题验证 — 检查每个子问题是否嵌入灵敏度/鲁棒性/误差分析"""
    from per_subquestion_verification import cmd_check as psv_check, cmd_check_all as psv_check_all
    if hasattr(args, 'subquestions') and args.subquestions:
        psv_check_all(args)
    else:
        psv_check(args)


# ── Model Evolution ─────────────────────────────────────────

def cmd_model_evolve(args):
    """模型进化 — 对高潜力模型进行变异搜索"""
    from model_evolver import init_search_space, run_evolution
    import json

    if args.evolution_cmd == "init":
        data = init_search_space(args.subquestion, args.base_model)
        print(f"[model-evolve] 搜索空间已初始化: {data['subquestion']}")
        print(f"  基础模型: {args.base_model}")
        print(f"  变异类型: {', '.join(data['mutation_types'])}")

    elif args.evolution_cmd == "evolve":
        result = run_evolution(args.subquestion, args.generations, args.base_fitness)
        print(f"[model-evolve] 进化完成")
        print(f"  完成代数: {result['generations_completed']}")
        print(f"  最优模型: {result['best_model']}")
        print(f"  最优适应度: {result['best_fitness']:.4f}")
        print(f"  进化日志: {result['evolution_log']}")

    elif args.evolution_cmd == "status":
        from model_evolver import get_evolution_data_path
        data_path = get_evolution_data_path(args.subquestion)
        if not data_path.exists():
            print(f"[model-evolve] 未找到进化数据: {data_path}")
            sys.exit(1)
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"子问题: {args.subquestion}")
        print(f"状态: {data.get('status', 'unknown')}")
        print(f"已完成代数: {len(data.get('generations', []))}")
        if data.get("generations"):
            last_gen = data["generations"][-1]
            print(f"最后一代最佳适应度: {last_gen.get('best_fitness', 'N/A')}")

    else:
        print("[model-evolve] Unknown subcommand. Use: init|evolve|status")
        sys.exit(1)


# ── M4: 闭环审计模块 ──────────────────────────────────────

def cmd_adversarial_review(args):
    """红队对抗审稿 — 模拟评委找漏洞"""
    from adversarial_review import cmd_generate, cmd_check_rebuttal, cmd_report as ar_report
    dispatch = {"generate": cmd_generate, "check-rebuttal": cmd_check_rebuttal, "report": ar_report}
    if args.review_cmd in dispatch:
        dispatch[args.review_cmd](args)
    else:
        print("[main] Unknown adversarial-review subcommand. Use: generate|check-rebuttal|report")


def cmd_check_figure_narrative(args):
    """图表叙事 D-A-C 门禁 — 检查每个图表的描述-分析-结论"""
    from figure_narrative_gate import cmd_scan, cmd_check_dac, cmd_report as fn_report
    dispatch = {"scan": cmd_scan, "check-dac": cmd_check_dac, "report": fn_report}
    if args.figure_cmd in dispatch:
        dispatch[args.figure_cmd](args)
    else:
        print("[main] Unknown check-figure-narrative subcommand. Use: scan|check-dac|report")


def cmd_review_stage(args):
    """闭环评分 — 基于 rubric.yaml 自动评分"""
    from stage_reviewer import cmd_score, cmd_report as sr_report, cmd_check, cmd_competition
    dispatch = {"score": cmd_score, "report": sr_report, "check": cmd_check, "competition": cmd_competition}
    if args.review_cmd in dispatch:
        dispatch[args.review_cmd](args)
    else:
        print("[main] Unknown review-stage subcommand. Use: score|report|check|competition")


# ── DOCX Revision Toolkit ──────────────────────────────────

def cmd_docx(args):
    """DOCX 修订工具链 — 分析/映射/替换/比较/验证"""
    from docx_revision import cmd_analyze, cmd_map, cmd_replace, cmd_diff, cmd_verify
    dispatch = {"analyze": cmd_analyze, "map": cmd_map, "replace": cmd_replace, 
                "diff": cmd_diff, "verify": cmd_verify}
    if args.docx_cmd in dispatch:
        dispatch[args.docx_cmd](args)
    else:
        print("[main] Unknown docx subcommand. Use: analyze|map|replace|diff|verify")


# ── LaTeX/PDF Output ────────────────────────────────────────

def cmd_docx_to_latex(args):
    """DOCX 转 LaTeX — 将 Word 文档转为 LaTeX 源文件"""
    from docx_to_latex import cmd_docx_to_latex as convert_cmd
    convert_cmd(args)


def cmd_compile_pdf(args):
    """编译 LaTeX 为 PDF"""
    from compile_pdf import cmd_compile_pdf as compile_cmd
    compile_cmd(args)


# ── Auto Mode ──────────────────────────────────────────────────

def cmd_auto_start(args):
    """激活 Auto 模式（全自动执行）"""
    from auto_orchestrator import cmd_auto_start as auto_start
    auto_start(args)


def cmd_auto_next(args):
    """Auto 模式：获取下一步动作"""
    from auto_orchestrator import cmd_auto_next as auto_next
    auto_next(args)


def cmd_auto_decide(args):
    """Auto 模式：自动决策"""
    from auto_orchestrator import cmd_auto_decide as auto_decide
    auto_decide(args)


def cmd_auto_gate_verdict(args):
    """Auto 模式：门禁裁决"""
    from auto_orchestrator import cmd_auto_gate_verdict as auto_gv
    auto_gv(args)


def cmd_auto_pause(args):
    """Auto 模式：暂停"""
    from auto_orchestrator import cmd_auto_pause as auto_pause
    auto_pause(args)


def cmd_auto_resume(args):
    """Auto 模式：恢复"""
    from auto_orchestrator import cmd_auto_resume as auto_resume
    auto_resume(args)


def cmd_auto_log(args):
    """Auto 模式：查看决策日志"""
    from auto_orchestrator import cmd_auto_log as auto_log
    auto_log(args)


def cmd_auto_status(args):
    """Auto 模式：查看状态"""
    from auto_orchestrator import cmd_auto_status as auto_status
    auto_status(args)


# ── Test ─────────────────────────────────────────────────────

def cmd_test(_args):
    """运行端到端测试"""
    import subprocess
    test_script = TESTS_DIR / "test_e2e.py"
    if not test_script.exists():
        print("[main] 测试文件不存在!")
        return {"status": "error"}

    print("[main] 运行端到端测试...")
    result = subprocess.run(
        [sys.executable, str(test_script)],
        cwd=str(PROJECT_ROOT),
        capture_output=False,
    )
    return {"status": "completed", "exit_code": result.returncode}


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Meta-model-skills-max — 数学建模全流程工具集 (v3.0.0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py init --contest CUMCM --problems 3 --mode AP
  python main.py status
  python main.py workflow
  python main.py gates
  python main.py check-gate G1_problem_parsed
  python main.py meeting M001_kickoff S1_problem_analysis
  python main.py freeze --subquestion Q1
  python main.py verify-freeze --subquestion Q1
  python main.py sandbox --code "import numpy as np; print(np.array([1,2,3]).mean())"
  python main.py evidence --subquestion Q1
  python main.py audit
  python main.py check-abstract paper/abstract.md
  python main.py check-derivation paper/model_section.md
  python main.py check-matrix paper/model_selection.md
  python main.py check-discussion paper/results.md
  python main.py check-expression paper/paper.md
  python main.py check-consistency paper/paper.md
  python main.py sensitivity init -q Q1 --model-file CUMCM_Workspace/src/model_q1.py
  python main.py sensitivity sweep -q Q1
  python main.py sensitivity check -q Q1
  python main.py sensitivity report -q Q1
  python main.py check-abstract-consistency -a paper/abstract.md -b paper/paper.md
  python main.py check-verification -q Q1 --paper paper/paper.md
  python main.py check-verification --subquestions "Q1,Q2,Q3" --paper paper/paper.md

  # 模型进化搜索
  python main.py model-evolve init -q Q1 --base-model model_a
  python main.py model-evolve evolve -q Q1 --generations 3 --base-fitness 0.75
  python main.py model-evolve status -q Q1

  python main.py adversarial-review generate -f paper/paper.md
  python main.py adversarial-review check-rebuttal -f paper/paper.md
  python main.py check-figure-narrative report -f paper/paper.md
  python main.py review-stage score -f paper/paper.md
  python main.py review-stage check -f paper/paper.md -g G6_audit_layer_passed

  # DOCX 修订工具链
  python main.py docx analyze paper.docx
  python main.py docx map paper.docx --keywords "摘要,模型,结论"
  python main.py docx replace paper.docx --old "旧文本" --new "新文本"
  python main.py docx replace paper.docx --json-file revisions.json
  python main.py docx diff paper_v1.docx paper_v2.docx
  python main.py docx verify paper.docx

  # LaTeX/PDF 输出
  python main.py docx-to-latex paper.docx
  python main.py docx-to-latex paper.docx -o ./output --no-compile
  python main.py compile-pdf paper.tex
    python main.py compile-pdf paper.tex --engine xelatex

  # Auto 模式（全自动）
  python main.py auto-start --depth STANDARD
  python main.py auto-next
  python main.py auto-decide S3_model_selection
  python main.py auto-gate-verdict S5_modeling_and_solve
  python main.py auto-pause
  python main.py auto-resume
  python main.py auto-log
  python main.py auto-status

注意: 实际建模工作流由 SKILL.md 指导主 Agent 完成，本工具仅提供状态管理和文件工具。
        """,
    )
    sub = parser.add_subparsers(dest="command")

    # init
    p_init = sub.add_parser("init", help="初始化 pipeline 状态机（从 workflow.yaml 加载）")
    p_init.add_argument("--mode", required=True, choices=["ap", "AP", "manual", "MANUAL"])
    p_init.add_argument("--contest", required=True,
                        choices=["cumcm", "CUMCM", "mcm", "MCM", "icm", "ICM", "51mcm", "51MCM"])
    p_init.add_argument("--problems", type=int, default=1)
    p_init.add_argument("--max-reworks", type=int, default=5, dest="max_reworks")
    p_init.add_argument("--git", action="store_true")

    # status
    sub.add_parser("status", help="查看 pipeline 状态")

    # workflow
    sub.add_parser("workflow", help="查看 workflow.yaml 解析结果")

    # gates
    sub.add_parser("gates", help="列出所有门禁合约")

    # check-gate
    p_ck = sub.add_parser("check-gate", help="检查指定门禁")
    p_ck.add_argument("gate_id", help="门禁 ID (e.g., G1_problem_parsed)")

    # meeting
    p_mtg = sub.add_parser("meeting", help="初始化会议模板")
    p_mtg.add_argument("meeting_id", help="会议 ID (e.g., M001_kickoff)")
    p_mtg.add_argument("stage_id", help="阶段 ID (e.g., problem_analysis)")

    # freeze
    p_freeze = sub.add_parser("freeze", help="冻结子问题结果")
    p_freeze.add_argument("--subquestion", "-q", required=True, help="子问题 (e.g., Q1)")
    p_freeze.add_argument("--source", "-s", help="结果目录")

    # verify-freeze
    p_vf = sub.add_parser("verify-freeze", help="验证冻结一致性")
    p_vf.add_argument("--subquestion", "-q", required=True, help="子问题 (e.g., Q1)")

    # sandbox
    p_sb = sub.add_parser("sandbox", help="沙箱执行代码")
    p_sb.add_argument("--code", help="Python 代码字符串")
    p_sb.add_argument("--code-file", help="代码文件路径")
    p_sb.add_argument("--timeout", type=int, default=30, help="超时秒数")

    # evidence
    p_ev = sub.add_parser("evidence", help="检查证据链")
    p_ev.add_argument("--subquestion", "-q", required=True, help="子问题 (e.g., Q1)")

    # audit
    p_audit = sub.add_parser("audit", help="运行 G6 三重审计")
    p_audit.add_argument("--workspace", "-w", default=None, help="工作空间路径")

    # test
    sub.add_parser("test", help="运行端到端测试")

    # ── M2: 高分能力增强命令 ──
    p_abs = sub.add_parser("check-abstract", help="摘要质量门禁（模型/结果/公式/引用）")
    p_abs.add_argument("file", help="摘要文件路径")
    p_abs.add_argument("--competition", default="CUMCM", help="竞赛类型")

    p_der = sub.add_parser("check-derivation", help="推导链检查（背景/方程/约束/推导/终态）")
    p_der.add_argument("file", help="模型文档路径")

    p_mat = sub.add_parser("check-matrix", help="方法选择矩阵检查（备选方法/对比/选择理由）")
    p_mat.add_argument("file", help="方法选择文档路径")

    p_dis = sub.add_parser("check-discussion", help="多维度讨论检查（7维度覆盖）")
    p_dis.add_argument("file", help="讨论文档路径")

    p_exp = sub.add_parser("check-expression", help="学术表达检查（口语化/填充词）")
    p_exp.add_argument("file", help="论文文档路径")

    p_con = sub.add_parser("check-consistency", help="跨子问题一致性（变量/单位/假设）")
    p_con.add_argument("file", help="论文文档路径")

    # ── M3: 深度实验检验命令 ──
    p_sen = sub.add_parser("sensitivity", help="灵敏度分析（init/sweep/check/report）")
    p_sen.add_argument("sensitivity_cmd", choices=["init", "sweep", "check", "report"],
                       help="子命令")
    p_sen.add_argument("--subquestion", "-q", required=True, help="子问题编号 (e.g., Q1)")
    p_sen.add_argument("--model-file", "-m", help="模型 Python 文件路径 (init 用)")
    p_sen.add_argument("--pct", help="扫描百分比，逗号分隔 (默认: 10,20,50)")

    p_abc = sub.add_parser("check-abstract-consistency", help="摘要-全文一致性审计")
    p_abc.add_argument("--abstract", "-a", required=True, help="摘要文件路径")
    p_abc.add_argument("--body", "-b", required=True, help="正文文件路径")
    p_abc.add_argument("--frozen-dir", "-f", help="冻结数据目录")

    p_psv = sub.add_parser("check-verification", help="逐子问题验证检查")
    p_psv.add_argument("--subquestion", "-q", help="子问题编号 (e.g., Q1)")
    p_psv.add_argument("--subquestions", help="子问题列表，逗号分隔 (e.g., Q1,Q2,Q3)")
    p_psv.add_argument("--paper", help="论文文件路径 (可选)")

    # ── Model Evolution ──
    p_me = sub.add_parser("model-evolve", help="模型进化（init/evolve/status）")
    p_me.add_argument("evolution_cmd", choices=["init", "evolve", "status"], help="子命令")
    p_me.add_argument("--subquestion", "-q", required=True, help="子问题编号 (e.g., Q1)")
    p_me.add_argument("--base-model", "-m", help="基础模型名称 (init 用)")
    p_me.add_argument("--generations", "-g", type=int, default=3, help="进化代数 (evolve 用)")
    p_me.add_argument("--base-fitness", type=float, default=0.7, help="基础适应度 (evolve 用)")

    # ── M4: 闭环审计命令 ──
    p_ar = sub.add_parser("adversarial-review", help="红队对抗审稿（generate/check-rebuttal/report）")
    p_ar.add_argument("review_cmd", choices=["generate", "check-rebuttal", "report"], help="子命令")
    p_ar.add_argument("--file", "-f", help="论文文件路径")
    p_ar.add_argument("--title", default="论文", help="论文标题 (generate 用)")
    p_ar.add_argument("--review", "-r", help="审稿报告 JSON 路径 (check-rebuttal 用)")
    p_ar.add_argument("--output-dir", "-d", help="报告目录 (report 用)")

    p_fn = sub.add_parser("check-figure-narrative", help="图表叙事 D-A-C 门禁（scan/check-dac/report）")
    p_fn.add_argument("figure_cmd", choices=["scan", "check-dac", "report"], help="子命令")
    p_fn.add_argument("--file", "-f", required=True, help="论文文件路径")

    p_sr = sub.add_parser("review-stage", help="闭环评分（score/report/check/competition）")
    p_sr.add_argument("review_cmd", choices=["score", "report", "check", "competition"], help="子命令")
    p_sr.add_argument("--file", "-f", required=True, help="论文文件路径")
    p_sr.add_argument("--gate-id", "-g", help="门禁 ID (check 用)")
    p_sr.add_argument("--competition", "-c", default="CUMCM", help="竞赛类型 (competition 用)")
    p_sr.add_argument("--report", action="store_true", help="生成评分卡报告 (competition 用)")

    # ── DOCX Revision Toolkit ──
    p_docx = sub.add_parser("docx", help="DOCX 修订工具链（analyze/map/replace/diff/verify）")
    p_docx.add_argument("docx_cmd", choices=["analyze", "map", "replace", "diff", "verify"],
                        help="子命令")
    p_docx.add_argument("file", nargs="?", help="DOCX 文件路径")
    p_docx.add_argument("file_b", nargs="?", help="第二个 DOCX 文件（diff 用）")
    p_docx.add_argument("--keywords", help="搜索关键词，逗号分隔（map 用）")
    p_docx.add_argument("--old", help="要替换的旧文本（replace 用）")
    p_docx.add_argument("--new", help="新文本（replace 用）")
    p_docx.add_argument("--json-file", help="批量替换 JSON 文件（replace 用）")
    p_docx.add_argument("--output", "-o", help="输出路径（replace 用）")
    p_docx.add_argument("--files", nargs="+", help="多个文件（analyze 比较模式）")

    # ── LaTeX/PDF Output ──
    p_latex = sub.add_parser("docx-to-latex", help="DOCX 转 LaTeX 源文件")
    p_latex.add_argument("input", help="输入 .docx 文件路径")
    p_latex.add_argument("--output-dir", "-o", default=None, help="输出目录")
    p_latex.add_argument("--no-compile", action="store_true", help="仅生成 .tex，不编译 PDF")
    p_latex.add_argument("--cleanup", action="store_true", help="编译后清理中间文件")

    p_pdf = sub.add_parser("compile-pdf", help="编译 LaTeX 为 PDF")
    p_pdf.add_argument("file", help="输入 .tex 文件路径")
    p_pdf.add_argument("--engine", default="", help="LaTeX 引擎 (xelatex/pdflatex/lualatex)")
    p_pdf.add_argument("--output-dir", "-o", default=None, help="PDF 输出目录")

    # ── Auto Mode 命令 ──
    p_auto_start = sub.add_parser("auto-start", help="激活 Auto 全自动模式")
    p_auto_start.add_argument("--depth", default=None,
                              help="Depth mode: FAST/STANDARD/CHAMPIONSHIP")

    sub.add_parser("auto-next", help="Auto 模式：获取下一步动作")

    p_auto_decide = sub.add_parser("auto-decide", help="Auto 模式：自动决策")
    p_auto_decide.add_argument("decision_point", help="决策点 ID (e.g., S3_model_selection)")
    p_auto_decide.add_argument("--context", default=None, help="JSON 上下文")

    p_auto_gv = sub.add_parser("auto-gate-verdict", help="Auto 模式：门禁裁决")
    p_auto_gv.add_argument("stage", help="阶段 ID (e.g., S5_modeling_and_solve)")

    sub.add_parser("auto-pause", help="Auto 模式：暂停（请求人工介入）")
    sub.add_parser("auto-resume", help="Auto 模式：恢复")
    sub.add_parser("auto-log", help="Auto 模式：查看决策日志")
    sub.add_parser("auto-status", help="Auto 模式：查看状态与安全指标")

    args = parser.parse_args()

    dispatch = {
        "init": cmd_init,
        "status": cmd_status,
        "workflow": cmd_workflow,
        "gates": cmd_gates,
        "check-gate": cmd_check_gate,
        "meeting": cmd_meeting,
        "freeze": cmd_freeze,
        "verify-freeze": cmd_verify_freeze,
        "sandbox": cmd_sandbox,
        "evidence": cmd_evidence,
        "audit": cmd_audit,
        "check-abstract": cmd_check_abstract,
        "check-derivation": cmd_check_derivation,
        "check-matrix": cmd_check_matrix,
        "check-discussion": cmd_check_discussion,
        "check-expression": cmd_check_expression,
        "check-consistency": cmd_check_consistency,
        "model-evolve": cmd_model_evolve,
        "sensitivity": cmd_sensitivity,
        "check-abstract-consistency": cmd_check_abstract_consistency,
        "check-verification": cmd_check_verification,
        "adversarial-review": cmd_adversarial_review,
        "check-figure-narrative": cmd_check_figure_narrative,
        "review-stage": cmd_review_stage,
        "docx": cmd_docx,
        "docx-to-latex": cmd_docx_to_latex,
        "compile-pdf": cmd_compile_pdf,
        "test": cmd_test,
        "auto-start": cmd_auto_start,
        "auto-next": cmd_auto_next,
        "auto-decide": cmd_auto_decide,
        "auto-gate-verdict": cmd_auto_gate_verdict,
        "auto-pause": cmd_auto_pause,
        "auto-resume": cmd_auto_resume,
        "auto-log": cmd_auto_log,
        "auto-status": cmd_auto_status,
    }

    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
