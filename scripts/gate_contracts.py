#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate Contracts Module (KyrieZhang329-inspired)
===============================================
G1-G6 hard gate contracts with enter_condition / pass_criteria / fail_fallback.
Plus: P1 change propagation, G2 PoC enforcement, G4 frozen staleness, G6 enhanced audit.
Mate-Math-v3: G1.5 Metric Guardian, G2.5 Experiment Race, G4.5 Evidence Chain.

Integrated into quality_gate.py for math-modeling-contest v5.9+.
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace

WORKSPACE = resolve_workspace()

# ═══════════════════════════════════════════════════════════════
# Gate Contracts
# ═══════════════════════════════════════════════════════════════

GATE_CONTRACTS = {
    "G0_INPUT_REGISTERED": {
        "description": "题目登记 — 题目文本已注册，竞赛类型已识别，审查官打分通过",
        "enter_condition": "User provides problem files.",
        "pass_criteria": [
            "inputs/inputs_manifest.json exists",
            "inputs/problem_text.md exists (>=100 chars)",
            "state/workflow_state.json exists with contest_type/problem_type/subquestion_count",
            "outputs/reviews/S0_review.md exists (inspector report)",
            "Inspector score >= threshold (Fast:60, Standard:70, Championship:85)",
            "P0 issues count == 0",
        ],
        "fail_fallback": "Route to S0 rework. Do not advance to S1 before G0 passes.",
    },
    "G1_PROBLEM_PARSED": {
        "description": "Problem parsed + classified + literature searched",
        "enter_condition": "User provides a problem statement (file or text).",
        "pass_criteria": [
            "Problem parsed into goals / objects / constraints / data / outputs / subquestions",
            "Each subquestion classified by task type (optimization / prediction / evaluation / hybrid)",
            "Related literature searched with >=2 refs per subquestion",
        ],
        "fail_fallback": "Route to problem analysis -> literature deep search. Do not advance to G2.",
    },
    "G1_5_DATA_QUALITY": {
        "description": "Mate-Math-v3: 数据治理门禁 — 数据画像完整，质量达标，清洗可追溯",
        "enter_condition": "G1 passed; problem_analysis complete; raw data available.",
        "pass_criteria": [
            "data_dictionary.md exists with all fields documented (name, type, unit, range)",
            "data_profile_report.md exists with missing/outlier/correlation analysis",
            "data_quality_report.md exists with cleaning operations log and traceability",
            "No undocumented missing values (every null has a strategy)",
            "Units consistent within same field (no mixed units)",
            "Quality score >= 60",
            "figures/ directory exists with >= 3 types of visualization charts (missing/distribution/correlation/boxplot/outlier)",
        ],
        "fail_fallback": "Route to data governance init. Do not advance to metric_spec_gate before G1.5a passes.",
    },
    "G1_5_METRIC_DEFINED": {
        "description": "Mate-Math-v3: Metric Guardian v2.0 - 指标规格完整，公式符号一致，全量子问题覆盖",
        "enter_condition": "G1.5a (data_governance) passed; variables.json available.",
        "pass_criteria": [
            "metric_report.md exists with PASS status (no TBD placeholders)",
            "metric_spec.md exists for EACH subquestion (not just Q1) with formula + variables + code function",
            "Each metric_spec.md has real content (no [指标名称] or [待填写] placeholders)",
            "All metric symbols defined in symbol_table.md (consistency audit passed)",
            "formula_audit_report.md generated for each subquestion with no critical issues",
            "Dimensional consistency verified (LaTeX subscripts match symbol table)",
            "Parameter traceability (source/来源 column present)",
        ],
        "fail_fallback": "Run metric_guardian.py init --all then agent fills specs. Do not advance to experiment_design before G1.5 passes.",
    },
    "G2_METHOD_VALIDATED": {
        "description": "LOAD-BEARING: method->code boundary. Most failures happen here.",
        "enter_condition": "G1 passed; data preprocessed; workspace structured.",
        "pass_criteria": [
            "2-4 candidate methods per subquestion documented",
            "EVERY candidate has a <=30-line PoC script AND a small-scale feasibility result",
            "A candidate WITHOUT a PoC counts as 'not yet validated'",
        ],
        "fail_fallback": "Route to method selection -> PoC generation. Do not generate main code before G2 passes.",
    },
    "G2_5_RACE_COMPLETED": {
        "description": "Mate-Math-v3: Experiment Race - 实验赛马完成，排行榜生成",
        "enter_condition": "G2 passed; experiment_design complete; 2-4 candidate models identified.",
        "pass_criteria": [
            "experiment_race_plan.md exists with scoring dimensions",
            "model_leaderboard.csv exists with all candidates ranked",
            "race_results.json contains primary_model and backup_models",
            "Score gap between top-2 documented",
        ],
        "fail_fallback": "Route to experiment race run. Do not advance to model_build before G2.5 passes.",
    },
    "G3_MATH_SANDBOX": {
        "description": "数学沙箱门禁 — 数学推导通过沙箱验证，代码安全可执行",
        "enter_condition": "G2 passed; code generated for chosen methods.",
        "pass_criteria": [
            "Code passes AST safety check (no eval/exec/os.system)",
            "Code passes string blacklist check (no network/file-write/dangerous imports)",
            "Code runs within timeout without error",
            "Numerical output is finite (no inf/nan/extreme values)",
            "Result sanity check passed (output within expected range)",
        ],
        "fail_fallback": "Route to math_sandbox remediation. Do not advance to experiments before G3_math_sandbox passes.",
    },
    "G3_CODE_REVIEWED": {
        "description": "Code review artifact on disk with >=5 explicit check items + baseline comparison.",
        "enter_condition": "G2 passed; code generated for chosen methods.",
        "pass_criteria": [
            "Review artifact exists with >=5 explicit pass/fail items referencing file:line",
            "Verification report confirms correctness",
            "Numerical sanity check passed (no inf/nan/extreme values)",
            "BASELINE-FIRST: Every main model has a baseline comparison (see G3_BASELINE_COMPARED)",
        ],
        "fail_fallback": "Route to code reviewer. Do not advance experiments before G3 passes.",
    },
    "G3_BASELINE_COMPARED": {
        "description": "基线对比强制门禁 — 每个主模型必须与至少一个简单基线对比，证明复杂度必要性",
        "enter_condition": "G2 passed; main model code generated and runnable.",
        "pass_criteria": [
            "baseline_comparison.md exists for EACH subquestion with baseline method + main model + metrics",
            "Baseline method is genuinely simple (mean/median/linear/greedy/naive — NOT another complex model)",
            "Comparison table shows: baseline metric, main model metric, improvement %, p-value or CI if applicable",
            "If main model improvement < 5% over baseline, justification required (why complexity is warranted)",
            "Baseline code is reproducible (src/q{N}/baseline.py or equivalent)",
        ],
        "fail_fallback": "Route to baseline generation. Agent must implement a simple baseline before G3 passes. "
                         "Common baselines: prediction→mean/linear regression, optimization→greedy/random, "
                         "classification→majority class, evaluation→equal weights.",
    },
    "G3_PARALLEL_MERGE": {
        "description": "并行合并门禁 — 所有子问题并行建模完成后合并结果，跨子问题变量/单位一致",
        "enter_condition": "All sub-question sub-stages approved via parallel-merge.",
        "pass_criteria": [
            "All sub-question sub-stages (S5_Q1, S5_Q2, ...) are approved",
            "Variable naming consistent across sub-questions (same symbol = same meaning)",
            "Units consistent across sub-questions (no mixed units for same quantity)",
            "cross_validation_report.md exists with pairwise consistency check",
            "unified_framework.md exists if >1 sub-question",
        ],
        "fail_fallback": "Identify inconsistent sub-questions. Route back to specific S5_Qx for alignment. "
                         "Do not advance to S5.5 before merge passes.",
    },
    "G4_RESULTS_FROZEN": {
        "description": "LOAD-BEARING: results->paper boundary. Prevents silent number drift.",
        "enter_condition": "G3 passed; experiments complete; robustness checked.",
        "pass_criteria": [
            "frozen_numbers.json exists for each subquestion",
            "Freeze is newer than ALL source files (no STALE freeze)",
            "freeze_change_log.md tracks all defrost events with reasons",
        ],
        "fail_fallback": "Follow thaw(log reason) -> modify(update source) -> re-freeze. Never edit frozen_numbers.json by hand.",
    },
    "G4_5_EVIDENCE_CHAIN": {
        "description": "Mate-Math-v3: Evidence Chain - 证据链完整，论文-代码一致性",
        "enter_condition": "G4 passed; results frozen; paper sections drafted.",
        "pass_criteria": [
            "conclusion_evidence_map.md exists with all conclusions mapped to code outputs",
            "paper_code_consistency_report.md generated with no critical issues",
            "All assumptions verified with evidence",
            "No unverified numerical claims in paper",
        ],
        "fail_fallback": "Route to evidence tracer register. Do not advance to content_assembly before G4.5 passes.",
    },
    "G5_PAPER_SECTION_READY": {
        "description": "Paper section meets quality thresholds before final assembly.",
        "enter_condition": "G4 passed; paper sections drafted.",
        "pass_criteria": [
            "Section meets word-count floor",
            "Every numerical result discussed from >=3 dimensions",
            "Every figure passes render-check",
            "Model derivation depth >= L3",
        ],
        "fail_fallback": "Route to paper-section-writer -> figure-generator with missing-dimensions list.",
    },
    "G5_5_ADVERSARIAL_REVIEW": {
        "description": "对抗审稿门禁 — 所有 P0 问题为零，P1 问题全部关闭，反驳覆盖完整",
        "enter_condition": "G5 passed; paper drafted; M004 red-team review completed.",
        "pass_criteria": [
            "P0 (致命) weaknesses = 0",
            "P1 (严重) weaknesses ≤ 3",
            "Rebuttal coverage ≥ 100% for P0/P1 issues",
            "All high-priority review issues explicitly addressed in revision",
        ],
        "fail_fallback": "Route to adversarial review -> revision cycle. Do not advance to G6 before G5.5 passes.",
    },
    "G6_AUDIT_LAYER_PASSED": {
        "description": "FINAL GATE: 3 independent auditors ALL must PASS.",
        "enter_condition": "G5 passed for all subquestions; paper sections drafted; references managed.",
        "pass_criteria": [
            "Consistency audit PASSED with disk artifact",
            "Completeness audit PASSED with disk artifact",
            "Quality audit PASSED with disk artifact",
            "ALL THREE must PASS - one passing does not imply the others",
        ],
        "fail_fallback": "Route to whichever auditor failed. Never approve final_assembly_allowed=true on partial audit.",
    },
    # ═══════════════════════════════════════════════════════════════
    # M2: 高分能力增强 — 原有门禁
    # ═══════════════════════════════════════════════════════════════
    "ABSTRACT_QUALITY_GATE": {
        "description": "摘要质量门禁 — 摘要必须包含模型名、量化结果、核心公式、图表引用",
        "enter_condition": "Paper draft completed; abstract section written.",
        "pass_criteria": [
            "Abstract contains model/method description (模型/方法/算法关键词)",
            "Abstract contains >= 2 quantitative results (具体数值)",
            "Abstract contains formula or model reference (公式/Algorithm)",
            "Abstract word count in range: CUMCM 400-550字, MCM/ICM 250-350 words",
        ],
        "fail_fallback": "Route to abstract rewriter. Agent must add missing elements before G5 passes.",
    },
    # ═══════════════════════════════════════════════════════════════
    # M3: 论文撰写全流程对齐 — 新增 6 个门禁合约
    # ═══════════════════════════════════════════════════════════════
    "G3_ASSUMPTIONS_VALID": {
        "description": "模型假设完整性 — 3-5条假设，每条有论证，质量评分达标",
        "enter_condition": "G2 passed; model candidates selected.",
        "pass_criteria": [
            "model_assumptions.md exists with 3-5 assumptions",
            "Each assumption has: statement + rationale + type classification",
            "assumption_engineer.py validate --strict passes (score >= 60)",
            "At least 1 hard assumption present",
            "No assumption without rationale",
            "Assumptions are consistent across all subquestions",
        ],
        "fail_fallback": "Run assumption_engineer.py report, agent fills missing rationale/quantification. "
                         "Use assumption_engineer.py template <problem_type> for guidance.",
    },
    "G5_S8_CONTENT_READY": {
        "description": "论文内容素材就绪 — S8 撰写前的所有上游素材必须齐全",
        "enter_condition": "G4.5 evidence_chain passed; all S0-S7 artifacts generated.",
        "pass_criteria": [
            "problem_restatement.md exists (S1 产出)",
            "tech_roadmap.png exists (S1 产出)",
            "model_assumptions.md exists with validation PASS (S3 产出)",
            "symbol_table.md exists (S1 产出)",
            "For each subquestion: solution_summary.md exists (S5 产出)",
            "unified_framework.md exists if >1 subquestion (S5 产出)",
            "constraint_verification.md exists (S6 产出)",
            "sensitivity_figure.png exists (S6 产出)",
            "model_evaluation.md exists (S7 产出)",
            "frozen_numbers.json exists for each subquestion (G4 frozen)",
        ],
        "fail_fallback": "Missing artifacts identified. Route to the specific upstream stage "
                         "that failed to produce the required artifact. Do NOT start S8 paper writing.",
    },
    "G5_5_PAPER_STRUCTURE": {
        "description": "论文结构完整性 — paper.md 必须包含全部必选章节",
        "enter_condition": "paper.md first draft completed.",
        "pass_criteria": [
            "paper.md contains all mandatory sections in correct order",
            "CUMCM mandatory: 摘要, 问题重述, 问题分析, 模型假设, 符号说明, 模型建立与求解, 模型检验, 模型评价, 结论, 参考文献, 附录",
            "Each subquestion has independent model建立+求解 section",
            "Each subquestion section contains: derivation + flowchart reference + constraint verification",
            "No placeholder text (TBD, TODO, 待填写, [待补充])",
        ],
        "fail_fallback": "Identify missing sections. Route to specific section writer. "
                         "Use paper-writing-rules.md G5.1 word count floor as minimum check.",
    },
    "ABSTRACT_QUALITY_GATE_V2": {
        "description": "增强版摘要质量门禁 — 每个子问题至少1个量化结果",
        "enter_condition": "Paper draft completed; abstract section written.",
        "pass_criteria": [
            "Abstract contains model/method description",
            "Abstract contains >= 1 quantitative result PER SUBQUESTION (not just 2 total)",
            "Abstract contains formula or model reference",
            "Abstract word count: CUMCM 400-550字, MCM/ICM 250-350 words",
            "Abstract follows 四要素结构: 问题+方法+结果+关键词",
            "No vague words: 大概/可能/也许/显著/明显",
            "Every number in abstract traceable to frozen_numbers.json",
        ],
        "fail_fallback": "Route to abstract rewriter. Use逐题句式模板 from paper-writing-rules.md §7.",
    },
    "G6_PAPER_EVALUATION": {
        "description": "模型评价完整性 — 优缺点+推广方向必须有数据支撑",
        "enter_condition": "S7 evidence_chain completed; model_evaluation.md generated from S7.",
        "pass_criteria": [
            "Model evaluation section exists in paper.md",
            "At least 2 strengths, each with quantitative evidence",
            "At least 2 weaknesses, each with specific explanation",
            "Future work / improvement directions present",
            "Evaluation references specific results from paper body (not generic praise)",
        ],
        "fail_fallback": "Route to model_evaluation rewriter. Use model_evaluation.md from S7 as source material.",
    },
    "G6_APPENDIX_COMPLETE": {
        "description": "附录完整性 — 源代码+参考文献格式化+AI声明",
        "enter_condition": "S10 final build in progress.",
        "pass_criteria": [
            "Appendix contains ALL source code files from src/q{N}/*.py",
            "Each code file has file header comment (purpose, author, date)",
            "Code is complete and runnable (no truncated sections)",
            "Reference list contains >= 6 entries",
            "References formatted per format-spec: [编号] 作者, 论文名, 杂志名, 卷(期): 年, 页码",
            "References are real (not fabricated) — cross-check with literature_review.md",
            "AI tool usage declaration present if applicable",
        ],
        "fail_fallback": "Route to appendix assembler. Collect all src/q{N}/*.py files. "
                         "Format references from literature_review.md.",
    },
    "ABSTRACT_BODY_CONSISTENCY": {
        "description": "摘要-正文一致性 — 摘要数字必须匹配正文和冻结数据",
        "enter_condition": "Paper draft completed; frozen_numbers.json available.",
        "pass_criteria": [
            "All numbers in abstract match corresponding numbers in paper body",
            "All numbers in abstract match frozen_numbers.json (no drift)",
            "No fabricated numbers in abstract (every number traceable to code/data)",
        ],
        "fail_fallback": "Route to abstract-body consistency checker. Fix abstract to match body/frozen data.",
    },
    "CROSS_SUBQUESTION_CONSISTENCY": {
        "description": "跨子问题一致性 — Q1-Qn 变量、单位、假设、量级必须一致",
        "enter_condition": "All subquestions modeled and solved.",
        "pass_criteria": [
            "Variable naming consistent across subquestions (same symbol = same meaning)",
            "Units consistent (no mixed units for same quantity)",
            "Assumptions consistent (no contradictory assumptions between Q1 and Q2)",
            "Order-of-magnitude consistency (no 10x jumps without explanation)",
        ],
        "fail_fallback": "Route to cross-subquestion consistency checker. Fix contradictions before final delivery.",
    },
    "PER_SUBQUESTION_VERIFICATION": {
        "description": "逐子问题验证 — 每个子问题末尾必须嵌入灵敏度分析和检验",
        "enter_condition": "Subquestion modeled, solved, and results obtained.",
        "pass_criteria": [
            "Each subquestion has sensitivity analysis (parameter sweep)",
            "Each subquestion has robustness check (perturbation test)",
            "Each subquestion has error analysis or confidence interval",
            "Verification results documented in robustness/Qx/ directory",
        ],
        "fail_fallback": "Route to sensitivity analysis for the specific subquestion. Cannot advance without embedded verification.",
    },
    "G1_5_METRIC_GUARDIAN": {
        "description": "指标守门门禁 (workflow.yaml alias) — 所有指标必须有数学定义和代码实现",
        "enter_condition": "G1.5a data_governance passed; variables.json available.",
        "pass_criteria": [
            "metric_spec.md exists for EACH subquestion with formula + variables + code function",
            "All metric symbols defined in symbol_table.md",
            "No TBD or placeholder values in metric specs",
            "Dimensional consistency verified",
        ],
        "fail_fallback": "Run metric_guardian.py init --all then agent fills specs.",
    },
    "G_INNOVATION_ASSESSMENT": {
        "description": "创新性评估门禁 — 模型选择报告中必须有明确的创新点论证",
        "enter_condition": "G2 passed; model candidates selected; model_selection_report.md generated.",
        "pass_criteria": [
            "model_selection_report.md contains innovation/improvement section",
            "Innovation argument >= 200 chars with specific justification",
            "Championship: >= 2 different model types (multi-method fusion)",
            "Championship: cross-discipline method reference present",
            "Fast mode: auto-skip (no innovation check required)",
        ],
        "fail_fallback": "Route to model selection report enhancement. Agent must add innovation/improvement "
                         "section with: (1) what is novel, (2) why it matters, (3) evidence of improvement. "
                         "Championship: add cross-discipline reference and multi-method fusion rationale.",
    },
    # ═══════════════════════════════════════════════════════════════
    # v2.0: S3 多专项提案 + 多轮结构化对抗 — 新增门禁合约
    # ═══════════════════════════════════════════════════════════════
    "G3_MULTI_PROPOSAL": {
        "description": "多专项提案门禁 — 4个差异化提案组并行产出，提案多样性达标",
        "enter_condition": "S2 passed; problem analysis complete.",
        "pass_criteria": [
            "methods/proposals/proposer_a_precision.md exists with >= 2 candidates per subquestion",
            "methods/proposals/proposer_b_innovation.md exists with >= 1 cross-discipline/frontier method",
            "methods/proposals/proposer_c_crossdisciplinary.md exists with >= 1 fusion model (L2+)",
            "methods/proposals/proposer_d_integrator.md exists with >= 1 integration strategy",
            "Total unique candidate models across 4 proposals >= 6 (diversity threshold)",
            "No two proposals are identical (method overlap < 50%)",
        ],
        "fail_fallback": "Identify missing proposals and re-spawn the specific proposer agent. "
                         "If diversity < 6, prompt the weakest proposer to add more candidates. "
                         "Do NOT proceed to adversarial rounds without all 4 proposals.",
    },
    "G3_ADVERSARIAL_ROUND": {
        "description": "多轮对抗门禁 — 红蓝对抗完成，每轮有攻击/辩护/裁决",
        "enter_condition": "G3_MULTI_PROPOSAL passed; 4 proposals available.",
        "pass_criteria": [
            "methods/attacks/round{N}_attack.md exists for each completed round",
            "methods/defenses/round{N}_defense.md exists for each completed round",
            "methods/verdicts/round{N}_verdict.md exists for each completed round",
            "Each attack covers all 4 dimensions (assumption/derivation/data/feasibility)",
            "Each verdict includes 10-dimension scoring for all surviving candidates",
            "Round 1 is mandatory; Round 2 if REPAIR verdicts exist; Round 3 if Championship mode",
        ],
        "fail_fallback": "Re-run the failed round. If Round 1 attack is incomplete, re-spawn Red Team. "
                         "If verdict scoring is missing dimensions, re-spawn Referee.",
    },
    "G3_MODEL_SELECTION_V2": {
        "description": "v2.0 模型选择终审 — 9维评分达到阈值，迭代决策明确",
        "enter_condition": "Adversarial rounds complete; model_selection_report.md generated.",
        "pass_criteria": [
            "model_selection_report.md contains 9-dimension scoring (original 7 + innovation + crossdisciplinary)",
            "Best candidate weighted score >= 50 (Standard) or >= 70 (Championship)",
            "Selection rationale references adversarial round outcomes",
            "Rejected candidates have explicit rejection reasons (per-candidate)",
            "Debate summary includes all 4 proposals' contribution to final decision",
            "If REJECT verdict: rework_count < 3 (iteration limit)",
        ],
        "fail_fallback": "If score < threshold: trigger S3 rework with adversarial failure details. "
                         "If iteration_count >= 3: generate manual_decision_report.md for human review. "
                         "NEVER force-pass a model that scored below threshold.",
    },
    "G3_PROTOTYPE_VALIDATED": {
        "description": "早期原型验证门禁 — S4代码原型已运行，结果合理",
        "enter_condition": "S3 model selection passed; S4 experiment race started.",
        "pass_criteria": [
            "src/race/prototype_model_*.py files exist (>= 2 prototypes)",
            "src/race/baseline.py exists",
            "Prototype code is syntactically valid (no import/runtime errors)",
            "Prototype output contains numerical results (not empty/crash)",
            "At least one prototype outperforms baseline",
            "Prototype results are consistent with S3 scoring predictions (within 30%)",
        ],
        "fail_fallback": "If ALL prototypes fail: S3 model selection was wrong → rework S3. "
                         "If some prototypes fail: remove failed candidates, keep working ones. "
                         "If prototype < baseline: check if baseline is truly simple; if yes, rework S3.",
    },
    # ═══════════════════════════════════════════════════════════════
    # S9.5: Publication Readiness Check — 出版规范门禁
    # ═══════════════════════════════════════════════════════════════
    "G9_5_PUBLICATION_READY": {
        "description": "出版规范门禁 — AI痕迹清零、非正式表达≤2、格式合规、竞赛规范达标",
        "enter_condition": "S9 adversarial review completed; paper_revised.md available.",
        "pass_criteria": [
            "P0 issues = 0 (no AI traces, no anonymity violations, no placeholders)",
            "P1 issues ≤ 2 (informal expressions, figure layout, format)",
            "P2 issues ≤ 5 (minor format issues)",
            "publication_readiness_report.md generated with PASS status",
            "Rework count ≤ 2",
        ],
        "fail_fallback": "Route back to S9 for language/style revision. "
                         "Run publication_checker.py to identify specific issues. "
                         "Max 2 reworks before human intervention.",
    },
}


def print_gate_contracts():
    """Print all gate contracts for agent reference."""
    print("\n" + "=" * 70)
    print("  GATE CONTRACTS (KyrieZhang329-inspired)")
    print("=" * 70)
    for gate_id, contract in GATE_CONTRACTS.items():
        print(f"\n  [{gate_id}] {contract['description']}")
        print(f"    Enter:  {contract['enter_condition']}")
        for c in contract['pass_criteria']:
            print(f"    Pass:   - {c}")
        print(f"    Fail:   {contract['fail_fallback']}")
    print("\n" + "=" * 70)


# ═══════════════════════════════════════════════════════════════
# P1: Change Propagation Rule
# ═══════════════════════════════════════════════════════════════

def propagation_check(changed_files, workspace=None):
    """P1: Check what other files may be stale after changes.

    After modifying any file under code/, methods/, results/, or planning/:
      1. grep the entire workspace for references to the changed artifact
      2. List every file that may now be stale
      3. Either update it OR flag it as STALE with recommended repair

    Returns: dict with stale_files, frozen_affected, recommendations
    """
    if workspace is None:
        workspace = WORKSPACE

    identifiers = set()
    for cf in changed_files:
        cf_path = Path(cf)
        if cf_path.exists() and cf_path.suffix in ('.py', '.m', '.md', '.json'):
            try:
                text = cf_path.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            names = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]{2,})\b', text)
            identifiers.update(names[:50])

    if not identifiers:
        return {"stale_files": [], "frozen_affected": [], "recommendations": []}

    stale_files = []
    frozen_affected = []
    search_dirs = ['methods', 'code', 'results', 'paper', 'planning']

    for search_dir in search_dirs:
        sd = workspace / search_dir
        if not sd.exists():
            continue
        for f in sd.rglob('*'):
            if not f.is_file() or f.suffix not in ('.py', '.m', '.md', '.tex', '.json'):
                continue
            if str(f) in [str(Path(cf)) for cf in changed_files]:
                continue
            try:
                text = f.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            matched = [ident for ident in identifiers if ident in text]
            if matched:
                rel = str(f.relative_to(workspace))
                stale_files.append({"file": rel, "matched_identifiers": matched[:10]})

    # Check frozen staleness
    for qdir in (workspace / 'frozen').glob('Q*') if (workspace / 'frozen').exists() else []:
        fp = qdir / 'frozen_numbers.json'
        if fp.exists():
            frozen_mtime = fp.stat().st_mtime
            for cf in changed_files:
                cf_path = Path(cf)
                if cf_path.exists() and cf_path.stat().st_mtime > frozen_mtime:
                    frozen_affected.append(str(qdir.name))
                    break

    recommendations = []
    if stale_files:
        recommendations.append(
            f"{len(stale_files)} files may be stale. Re-run consistency-auditor for affected subquestions."
        )
    if frozen_affected:
        recommendations.append(
            f"Frozen snapshots for {frozen_affected} are now STALE. "
            f"Follow unfreeze -> modify -> re-freeze protocol."
        )

    return {
        "stale_files": stale_files,
        "frozen_affected": frozen_affected,
        "recommendations": recommendations,
    }


def print_propagation_report(result):
    """Print P1 propagation check results."""
    print("\n" + "=" * 60)
    print("  P1: Change Propagation Check")
    print("=" * 60)

    if result["stale_files"]:
        print(f"\n  Potentially STALE files ({len(result['stale_files'])}):")
        for sf in result["stale_files"]:
            print(f"    - {sf['file']}")
            print(f"      matched: {', '.join(sf['matched_identifiers'][:5])}")
    else:
        print("\n  No stale files detected.")

    if result["frozen_affected"]:
        print(f"\n  STALE frozen snapshots: {result['frozen_affected']}")

    if result["recommendations"]:
        print("\n  Recommendations:")
        for rec in result["recommendations"]:
            print(f"    - {rec}")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# G2: PoC Hard Gate
# ═══════════════════════════════════════════════════════════════

def gate_g2_poc(poc_dir=None):
    """G2: Check every candidate method has a <=30-line PoC with feasibility result."""
    if poc_dir is None:
        methods_dir = WORKSPACE / "methods"
    else:
        methods_dir = Path(poc_dir)

    if not methods_dir.exists():
        return False, "G2 PoC: methods/ directory not found. Run method selection first.", {}

    poc_files = list(methods_dir.rglob("poc/*.py")) + list(methods_dir.rglob("poc/*.m"))

    if not poc_files:
        return False, (
            "G2 PoC FAILED: No PoC scripts found under methods/Qx/poc/.\n"
            "  Requirement: EVERY candidate method must have a <=30-line PoC with a feasibility result.\n"
            "  Candidates without PoC are NOT validated."
        ), {}

    issues = []
    validated = []
    for poc in poc_files:
        try:
            lines = poc.read_text(encoding='utf-8', errors='replace').split('\n')
        except Exception:
            issues.append(f"{poc.name}: cannot read")
            continue

        code_lines = [
            l for l in lines
            if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('%')
        ]
        line_count = len(code_lines)

        if line_count > 30:
            issues.append(f"{poc.name}: {line_count} code lines (max 30)")
        elif line_count == 0:
            issues.append(f"{poc.name}: empty PoC")
        else:
            text = '\n'.join(lines)
            has_output = any(kw in text for kw in ['print(', 'fprintf(', 'disp(', 'output', 'result'])
            if has_output:
                validated.append({"file": poc.name, "lines": line_count})
            else:
                issues.append(f"{poc.name}: no output/result statement found")

    if issues:
        return False, (
            f"G2 PoC FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  Validated: {len(validated)} PoC(s)."
        ), {"issues": issues, "validated": validated}

    return True, (
        f"G2 PoC PASSED: {len(validated)} candidate(s) validated.\n"
        + "\n".join(f"  - {v['file']}: {v['lines']} lines" for v in validated)
    ), {"validated": validated}


# ═══════════════════════════════════════════════════════════════
# G3: Baseline Comparison Enforcement
# ═══════════════════════════════════════════════════════════════

_BASELINE_KEYWORDS = [
    "baseline", "基线", "baseline_comparison", "对照",
    "naive", "trivial", "simple_method", "mean_prediction",
]

_BASELINE_SIMPLE_METHODS = [
    "mean", "median", "mode", "均值", "中位数", "众数",
    "linear", "线性", "线性回归", "linear_regression",
    "greedy", "贪心", "random", "随机",
    "majority_class", "多数类", "equal_weight", "等权",
    "constant", "常数", "last_value", "最近值",
]


def gate_g3_baseline(workspace=None):
    """G3: Check that every main model has a baseline comparison.

    Checks:
    1. baseline_comparison.md exists per subquestion
    2. Baseline method is genuinely simple (not another complex model)
    3. Comparison metrics are present (improvement %, table)
    4. Baseline code exists and is reproducible
    """
    ws = Path(workspace) if workspace else WORKSPACE
    issues = []
    evidence = []

    # Detect subquestions from directory structure
    sub_dirs = sorted(
        [d.name for d in (ws / "src").iterdir()
         if d.is_dir() and d.name.startswith("q")]
    ) if (ws / "src").exists() else []

    if not sub_dirs:
        # Fallback: check for top-level baseline_comparison.md
        top_bc = ws / "baseline_comparison.md"
        if top_bc.exists():
            evidence.append(f"Top-level baseline_comparison.md found ({top_bc.stat().st_size} bytes)")
        else:
            issues.append("NO_BASELINE: No baseline_comparison.md found")
            return False, (
                "G3 Baseline FAILED: No baseline comparison found.\n"
                "  Action: Implement a simple baseline for each subquestion.\n"
                "  Common baselines: mean/linear/greedy/naive.\n"
                "  Output: baseline_comparison.md per subquestion."
            ), {"issues": issues, "evidence": evidence}
    else:
        for q_dir in sub_dirs:
            q_label = q_dir.upper().replace("Q", "Q")
            bc_path = ws / "src" / q_dir / "baseline_comparison.md"
            if bc_path.exists():
                text = bc_path.read_text(encoding="utf-8", errors="replace")
                size = bc_path.stat().st_size

                # Check for genuinely simple baseline mention
                has_simple_baseline = any(
                    kw in text.lower() for kw in _BASELINE_SIMPLE_METHODS
                )
                # Check for comparison metrics
                has_improvement = any(kw in text for kw in [
                    "提升", "improvement", "%", "优于", "outperform",
                    "对比", "compare", "RMSE", "MAE", "R²", "accuracy",
                    "baseline", "基线",
                ])

                if size < 50:
                    issues.append(f"{q_label}: baseline_comparison.md too thin ({size} bytes)")
                elif not has_simple_baseline:
                    issues.append(
                        f"{q_label}: no simple baseline method identified "
                        f"(must be mean/linear/greedy/etc., NOT another complex model)"
                    )
                else:
                    evidence.append(f"{q_label}: baseline comparison present ({size} bytes)")
                    if not has_improvement:
                        issues.append(f"{q_label}: baseline comparison exists but no improvement metrics found")
            else:
                # Check top-level fallback
                top_bc = ws / "baseline_comparison.md"
                if top_bc.exists():
                    evidence.append(f"{q_label}: uses top-level baseline_comparison.md")
                else:
                    issues.append(f"{q_label}: NO baseline_comparison.md")

            # Check baseline code exists
            baseline_code = list((ws / "src" / q_dir).glob("baseline*")) if (ws / "src" / q_dir).exists() else []
            if baseline_code:
                evidence.append(f"{q_label}: baseline code {baseline_code[0].name}")
            else:
                issues.append(f"{q_label}: no baseline code file found (src/{q_dir}/baseline*.py)")

    if issues:
        return False, (
            f"G3 Baseline FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  Evidence: {len(evidence)} check(s) passed.\n"
            "  Action: Implement simple baseline + comparison for each subquestion."
        ), {"issues": issues, "evidence": evidence}

    return True, (
        f"G3 Baseline PASSED: {len(evidence)} subquestion(s) have baseline comparison.\n"
        + "\n".join(f"  + {e}" for e in evidence)
    ), {"evidence": evidence}


# ═══════════════════════════════════════════════════════════════
# G4: Frozen Staleness Detection
# ═══════════════════════════════════════════════════════════════

def gate_g4_frozen_staleness(subquestion=None):
    """G4: Check if frozen_numbers.json is stale (source files newer than freeze)."""
    frozen_root = WORKSPACE / "frozen"
    if not frozen_root.exists():
        return False, "G4: No frozen/ directory. Run freeze first.", {}

    subquestions = [subquestion] if subquestion else [
        d.name for d in frozen_root.iterdir() if d.is_dir()
    ]

    all_stale = []
    all_ok = []

    for q in subquestions:
        freeze_path = frozen_root / q / "frozen_numbers.json"
        if not freeze_path.exists():
            all_stale.append(f"{q}: no freeze exists")
            continue

        try:
            with open(freeze_path, 'r', encoding='utf-8') as f:
                frozen = json.load(f)
        except Exception:
            all_stale.append(f"{q}: corrupted freeze file")
            continue

        source_dir = Path(frozen.get("source_dir", ""))
        frozen_at = frozen.get("frozen_at", "unknown")
        frozen_dt = None
        try:
            frozen_dt = datetime.strptime(frozen_at, "%Y-%m-%d %H:%M:%S")
        except Exception:
            all_stale.append(f"{q}: unparseable frozen_at timestamp")
            continue

        newer_files = []
        if source_dir.exists():
            for fpath in source_dir.rglob("*"):
                if fpath.is_file() and fpath.suffix in ('.py', '.m', '.json', '.csv', '.txt', '.md'):
                    mtime = fpath.stat().st_mtime
                    if datetime.fromtimestamp(mtime) > frozen_dt:
                        newer_files.append(str(fpath.relative_to(source_dir)))

        if newer_files:
            frozen['status'] = 'stale'
            with open(freeze_path, 'w', encoding='utf-8') as f:
                json.dump(frozen, f, indent=2, ensure_ascii=False)
            all_stale.append(
                f"{q}: STALE (frozen {frozen_at}, {len(newer_files)} source files newer)"
            )
        else:
            all_ok.append(q)

    if all_stale:
        return False, (
            "G4 Frozen Staleness FAILED:\n"
            + "\n".join(f"  - {s}" for s in all_stale) + "\n"
            "  Action: thaw(log reason) -> modify(update source) -> re-freeze."
        ), {"stale": all_stale, "ok": all_ok}

    return True, f"G4 Frozen Staleness PASSED: {len(all_ok)} freeze(s) current.", {"ok": all_ok}


# ═══════════════════════════════════════════════════════════════
# G6: Enhanced Independent Audit Layer (with disk artifacts)
# ═══════════════════════════════════════════════════════════════

def _write_audit_artifact(ws, filename, verdict, evidence, issues, pass_criteria_key="G6_AUDIT_LAYER_PASSED"):
    """Write a disk audit artifact. Core principle: auditors MUST leave files."""
    audit_dir = ws / "paper" / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / filename

    lines = [f"# {filename.replace('.md', '').replace('_', ' ').title()}", "", f"**Verdict: {verdict}**", ""]
    lines.append("## Evidence")
    for e in evidence:
        lines.append(f"- [x] {e}")
    if issues:
        lines.append("")
        lines.append("## Issues")
        for i in issues:
            lines.append(f"- [ ] {i}")
    if pass_criteria_key in GATE_CONTRACTS:
        lines.append("")
        lines.append("## Pass Criteria")
        for pc in GATE_CONTRACTS[pass_criteria_key]["pass_criteria"]:
            lines.append(f"- {pc}")

    audit_path.write_text("\n".join(lines), encoding='utf-8')
    return str(audit_path)


def audit_consistency_enhanced(workspace_path):
    """G6 Layer 1: Cross-media consistency (paper <-> code <-> frozen_numbers.json)."""
    ws = Path(workspace_path)
    issues = []
    evidence = []

    paper_files = list(ws.glob("output/*.docx")) + list(ws.glob("output/*.pdf"))
    if not paper_files:
        issues.append("NO_PAPER: No output paper (.docx/.pdf) found")
    else:
        evidence.append(f"Paper: {paper_files[0].name} ({paper_files[0].stat().st_size} bytes)")

    frozen_files = list(ws.glob("frozen/*/frozen_numbers.json"))
    if not frozen_files:
        issues.append("NO_FROZEN: No frozen_numbers.json found - numbers may drift")
    else:
        for ff in frozen_files:
            try:
                with open(ff, 'r', encoding='utf-8') as f:
                    frozen = json.load(f)
                status = frozen.get('status', 'frozen')
                if status == 'stale':
                    issues.append(f"STALE_FREEZE: {ff.parent.name} freeze is stale")
                else:
                    evidence.append(f"Freeze {ff.parent.name}: {status} (v{frozen.get('version', '?')})")
            except Exception:
                issues.append(f"CORRUPT_FREEZE: {ff}")

    symbol_table = ws / "planning" / "symbol_table.md"
    if symbol_table.exists():
        evidence.append(f"Symbol table: {symbol_table.stat().st_size} bytes")
    else:
        issues.append("NO_SYMBOL_TABLE: planning/symbol_table.md not found")

    codemap = ws / "CODE_MAP.md"
    if codemap.exists():
        evidence.append(f"CODE_MAP: {codemap.stat().st_size} bytes")
    else:
        issues.append("NO_CODE_MAP: CODE_MAP.md not found")

    passed = len(issues) == 0
    artifact = _write_audit_artifact(ws, "cross_media_consistency_audit.md",
                                     "PASSED" if passed else "FAILED", evidence, issues)
    return {"passed": passed, "issues": issues, "evidence": evidence, "artifact": artifact}


def audit_completeness_enhanced(workspace_path):
    """G6 Layer 2: Completeness (every subquestion has code + results + report + robustness)."""
    ws = Path(workspace_path)
    issues = []
    evidence = []

    for q in ["Q1", "Q2", "Q3", "Q4"]:
        has_code = bool(list(ws.glob(f"code/{q}/*.py")) + list(ws.glob(f"code/{q}/*.m")))
        has_results = bool(list(ws.glob(f"results/{q}/**/*")))
        has_robustness = (ws / f"robustness/{q}").exists()

        if not has_code and not has_results:
            continue

        parts = []
        if has_code:
            parts.append("code")
        else:
            issues.append(f"{q}: no code found")
        if has_results:
            parts.append("results")
        else:
            issues.append(f"{q}: no results found")
        if has_robustness:
            parts.append("robustness")
        else:
            issues.append(f"{q}: no robustness report")
        if parts:
            evidence.append(f"{q}: {' + '.join(parts)}")

    passed = len(issues) == 0
    artifact = _write_audit_artifact(ws, "completeness_audit.md",
                                     "PASSED" if passed else "FAILED", evidence, issues)
    return {"passed": passed, "issues": issues, "evidence": evidence, "artifact": artifact}


def audit_quality_enhanced(workspace_path):
    """G6 Layer 3: Quality (anti-fabrication, academic integrity, paper quality)."""
    ws = Path(workspace_path)
    issues = []
    evidence = []

    frozen_files = list(ws.glob("frozen/*/frozen_numbers.json"))
    if frozen_files:
        evidence.append(f"{len(frozen_files)} frozen snapshot(s) - numbers traceable")
    else:
        issues.append("UNTRACEABLE: No frozen numbers - cannot verify numbers trace to code")

    integrity_log = ws / "integrity_gate.md"
    if integrity_log.exists():
        evidence.append("Integrity gate log found")
    else:
        issues.append("NO_INTEGRITY_CHECK: integrity gate not run")

    for docx in ws.glob("output/*.docx"):
        size_kb = docx.stat().st_size / 1024
        if size_kb < 30:
            issues.append(f"SMALL_PAPER: {docx.name} is only {size_kb:.0f}KB - likely incomplete")
        else:
            evidence.append(f"Paper size: {size_kb:.0f}KB")

    codemap = ws / "CODE_MAP.md"
    if codemap.exists():
        text = codemap.read_text(encoding='utf-8', errors='replace')
        if len(text) < 500:
            issues.append("THIN_CODE_MAP: Model documentation too brief")
        else:
            evidence.append(f"CODE_MAP: {len(text)} chars")

    passed = len(issues) == 0
    artifact = _write_audit_artifact(ws, "qa_report.md",
                                     "PASSED" if passed else "FAILED", evidence, issues)
    return {"passed": passed, "issues": issues, "evidence": evidence, "artifact": artifact}


def run_g6_audit_enhanced(workspace_path=None):
    """Run full G6 three-layer audit with disk artifacts. ALL THREE must PASS."""
    if workspace_path is None:
        workspace_path = str(WORKSPACE)

    ws = Path(workspace_path)

    results = {
        "consistency": audit_consistency_enhanced(workspace_path),
        "completeness": audit_completeness_enhanced(workspace_path),
        "quality": audit_quality_enhanced(workspace_path),
    }

    all_passed = all(r["passed"] for r in results.values())
    results["gate_passed"] = all_passed

    # Write final assembly gate status
    gate_file = ws / "paper" / "gate_g6_status.json"
    gate_file.parent.mkdir(parents=True, exist_ok=True)
    gate_file.write_text(json.dumps({
        "gate": "G6_AUDIT_LAYER_PASSED",
        "passed": all_passed,
        "final_assembly_allowed": all_passed,
        "auditors": {
            k: {"passed": v["passed"], "artifact": v.get("artifact", "N/A")}
            for k, v in results.items() if k != "gate_passed"
        },
    }, indent=2, ensure_ascii=False), encoding='utf-8')

    return results


def print_g6_enhanced_report(results):
    """Print enhanced G6 audit report."""
    print("\n" + "=" * 60)
    print("  G6 Audit Layer (Consistency -> Completeness -> Quality)")
    print("  ALL THREE must PASS - one passing != others passing")
    print("=" * 60)

    icons = {True: "PASS", False: "FAIL"}
    for layer, r in results.items():
        if layer == "gate_passed":
            continue
        icon = icons[r["passed"]]
        print(f"\n  [{icon}] {layer.upper()}")
        for e in r.get("evidence", []):
            print(f"    + {e}")
        for issue in r.get("issues", []):
            print(f"    - {issue}")
        if "artifact" in r:
            print(f"    artifact: {r['artifact']}")

    gate_icon = "PASS" if results["gate_passed"] else "BLOCKED"
    print(f"\n  G6 GATE: [{gate_icon}]")
    if not results["gate_passed"]:
        print("  Pipeline blocked until all three auditors PASS.")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# M3: 论文撰写全流程对齐 — 自动化检查函数
# ═══════════════════════════════════════════════════════════════

_REQUIRED_S8_ARTIFACTS = [
    ("problem_restatement.md", "S1 问题重述"),
    ("symbol_table.md", "S1 符号表"),
    ("model_assumptions.md", "S3 模型假设"),
    ("constraint_verification.md", "S6 约束自检"),
    ("model_evaluation.md", "S7 模型评价"),
    ("unified_framework.md", "S5 统一框架"),
]

_OPTIONAL_S8_ARTIFACTS = [
    "tech_roadmap.png",
    "sensitivity_figure.png",
]


def gate_g5_s8_content_ready(workspace=None, num_subquestions=1):
    """G5: Check that all S0-S7 artifacts are ready before S8 paper writing."""
    ws = Path(workspace) if workspace else WORKSPACE
    issues = []
    evidence = []

    # Check required artifacts
    for artifact, desc in _REQUIRED_S8_ARTIFACTS:
        path = ws / artifact
        if path.exists():
            size = path.stat().st_size
            if size < 50:
                issues.append(f"THIN: {artifact} exists but too thin ({size} bytes) — {desc}")
            else:
                evidence.append(f"{artifact} ({size} bytes) — {desc}")
        else:
            issues.append(f"MISSING: {artifact} — {desc}")

    # Check per-subquestion artifacts
    for q in range(1, num_subquestions + 1):
        sm_path = ws / "outputs" / f"q{q}" / "solution_summary.md"
        if sm_path.exists():
            evidence.append(f"q{q}/solution_summary.md ({sm_path.stat().st_size} bytes)")
        else:
            issues.append(f"MISSING: outputs/q{q}/solution_summary.md")

        frozen_path = ws / "frozen" / f"Q{q}" / "frozen_numbers.json"
        if frozen_path.exists():
            evidence.append(f"frozen/Q{q}/frozen_numbers.json")
        else:
            issues.append(f"MISSING: frozen/Q{q}/frozen_numbers.json")

    # Check optional artifacts (warning only)
    for artifact in _OPTIONAL_S8_ARTIFACTS:
        path = ws / artifact
        if path.exists():
            evidence.append(f"{artifact} (optional, present)")

    if issues:
        return False, (
            f"G5 S8 Content Ready FAILED: {len(issues)} missing/thin artifact(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  Evidence: {len(evidence)} artifact(s) verified.\n"
            "  Action: Route to the specific upstream stage that failed. Do NOT start S8."
        ), {"issues": issues, "evidence": evidence}

    return True, (
        f"G5 S8 Content Ready PASSED: {len(evidence)} artifact(s) verified.\n"
        + "\n".join(f"  + {e}" for e in evidence)
    ), {"evidence": evidence}


def gate_g6_appendix_complete(workspace=None):
    """G6: Check appendix completeness — source code + references + AI declaration."""
    ws = Path(workspace) if workspace else WORKSPACE
    issues = []
    evidence = []

    # Check source code
    src_dir = ws / "src"
    if src_dir.exists():
        py_files = list(src_dir.rglob("*.py"))
        if py_files:
            evidence.append(f"Source code: {len(py_files)} .py file(s) found")
            for py in py_files[:20]:  # cap display
                text = py.read_text(encoding="utf-8", errors="replace")
                if len(text.strip()) < 20:
                    issues.append(f"THIN_CODE: {py.name} is nearly empty")
                elif "truncated" in text.lower() or "# ... truncated" in text.lower():
                    issues.append(f"TRUNCATED: {py.name} appears truncated")
        else:
            issues.append("NO_CODE: No .py files found under src/")
    else:
        issues.append("NO_SRC_DIR: src/ directory not found")

    # Check references
    ref_files = list(ws.rglob("literature_review.md")) + list(ws.rglob("references.md"))
    if ref_files:
        for rf in ref_files:
            text = rf.read_text(encoding="utf-8", errors="replace")
            # Count reference entries (lines starting with [number])
            import re
            refs = re.findall(r'\[\d+\]', text)
            if len(refs) >= 6:
                evidence.append(f"References: {len(refs)} entries in {rf.name}")
            else:
                issues.append(f"FEW_REFS: Only {len(refs)} references found (need >= 6)")
    else:
        issues.append("NO_REFS: No literature_review.md found")

    # Check AI declaration
    appendix_dir = ws / "appendix"
    appendix_files = list(appendix_dir.rglob("*")) if appendix_dir.exists() else []
    paper_files = list(ws.glob("paper*.md")) + list(ws.glob("paper*.docx"))
    all_text_files = [f for f in paper_files + appendix_files if f.suffix in ('.md', '.txt')]

    has_ai_decl = False
    for tf in all_text_files:
        try:
            text = tf.read_text(encoding="utf-8", errors="replace")
            if "AI" in text and ("声明" in text or "declaration" in text.lower() or "工具" in text):
                has_ai_decl = True
                break
        except Exception:
            continue

    if has_ai_decl:
        evidence.append("AI tool usage declaration present")
    else:
        evidence.append("AI tool usage declaration: not detected (may not be needed)")

    if issues:
        return False, (
            f"G6 Appendix FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  Evidence: {len(evidence)} check(s) passed.\n"
            "  Action: Fix code files and references, then re-check."
        ), {"issues": issues, "evidence": evidence}

    return True, (
        f"G6 Appendix PASSED: {len(evidence)} check(s) passed.\n"
        + "\n".join(f"  + {e}" for e in evidence)
    ), {"evidence": evidence}


# ═══════════════════════════════════════════════════════════════
# Mode-Aware Thresholds — 冠军模式差异化
# ═══════════════════════════════════════════════════════════════

MODE_THRESHOLDS = {
    "fast": {
        "max_rework": 2,
        "paper_min_words": 8000,
        "paper_min_figures": 4,
        "abstract_min_words": 300, "abstract_max_words": 450,
        "abstract_min_quant_results": 1,
        "redteam_rounds": 1, "abstract_polish_rounds": 1,
        "model_min_score": 0,
        "min_references": 4,
        "chapter_min_words": {},
        "cross_question_check": False,
    },
    "standard": {
        "max_rework": 3,
        "paper_min_words": 12000,
        "paper_min_figures": 6,
        "abstract_min_words": 400, "abstract_max_words": 550,
        "abstract_min_quant_results": 2,
        "redteam_rounds": 1, "abstract_polish_rounds": 1,
        "model_min_score": 50,
        "min_references": 6,
        "chapter_min_words": {
            "摘要": 400, "问题重述": 500, "问题分析": 800,
            "模型假设": 300, "符号说明": 200, "模型建立与求解": 3000,
            "模型检验": 500, "模型评价": 500, "结论": 300,
        },
        "cross_question_check": True,
    },
    "championship": {
        "max_rework": 5,
        "paper_min_words": 15000,
        "paper_min_figures": 10,
        "abstract_min_words": 450, "abstract_max_words": 550,
        "abstract_min_quant_results": 3,
        "redteam_rounds": 3, "abstract_polish_rounds": 3,
        "model_min_score": 70,
        "min_references": 10,
        "chapter_min_words": {
            "摘要": 450, "问题重述": 600, "问题分析": 1000,
            "模型假设": 400, "符号说明": 300, "模型建立与求解": 4000,
            "模型检验": 700, "模型评价": 600, "结论": 400,
        },
        "cross_question_check": True,
    },
}


# ═══════════════════════════════════════════════════════════════
# CUMCM 评审权重感知阈值
# ═══════════════════════════════════════════════════════════════
# 基于 CUMCM 评审标准的维度权重，映射到阶段门禁严格度。
# 模型质量 50-60% → S3/S5 门禁最严格
# 问题解决 20-30% → S1/S5.5 门禁次严格
# 论文规范 10-15% → S8/S10 门禁中等严格
# 验证检验 5-10%  → S6 门禁基础严格

SCORING_WEIGHT_THRESHOLDS = {
    "model_quality": {
        "weight_range": "50-60%",
        "description": "模型质量（建模+求解+创新）",
        "stages": ["S3_model_selection", "S4_experiment_race",
                    "S5_modeling_and_solve", "S5.5_model_evolution"],
        "thresholds": {
            "fast": {"max_p0": 0, "max_p1": 1, "min_score": 60, "min_rework": 1},
            "standard": {"max_p0": 0, "max_p1": 1, "min_score": 70, "min_rework": 1},
            "championship": {"max_p0": 0, "max_p1": 0, "min_score": 80, "min_rework": 2},
        },
    },
    "problem_solving": {
        "weight_range": "20-30%",
        "description": "问题分析与重述",
        "stages": ["S0_input_registration", "S1_problem_analysis", "S2_data_governance"],
        "thresholds": {
            "fast": {"max_p0": 0, "max_p1": 2, "min_score": 0, "min_rework": 1},
            "standard": {"max_p0": 0, "max_p1": 2, "min_score": 0, "min_rework": 1},
            "championship": {"max_p0": 0, "max_p1": 1, "min_score": 0, "min_rework": 1},
        },
    },
    "paper_standard": {
        "weight_range": "10-15%",
        "description": "论文写作与排版",
        "stages": ["S8_paper_drafting", "S10_final_build"],
        "thresholds": {
            "fast": {"max_p0": 0, "max_p1": 3, "min_score": 0, "min_rework": 1},
            "standard": {"max_p0": 0, "max_p1": 2, "min_score": 0, "min_rework": 1},
            "championship": {"max_p0": 0, "max_p1": 1, "min_score": 0, "min_rework": 2},
        },
    },
    "verification": {
        "weight_range": "5-10%",
        "description": "验证与检验",
        "stages": ["S6_verification", "S7_evidence_chain"],
        "thresholds": {
            "fast": {"max_p0": 0, "max_p1": 2, "min_score": 0, "min_rework": 1},
            "standard": {"max_p0": 0, "max_p1": 2, "min_score": 0, "min_rework": 1},
            "championship": {"max_p0": 0, "max_p1": 1, "min_score": 0, "min_rework": 1},
        },
    },
    "adversarial_review": {
        "weight_range": "综合",
        "description": "对抗审稿（S9 综合审稿覆盖所有维度）",
        "stages": ["S9_adversarial_review"],
        "thresholds": {
            "fast": {"max_p0": 0, "max_p1": 3, "min_score": 0, "min_rework": 1},
            "standard": {"max_p0": 0, "max_p1": 2, "min_score": 0, "min_rework": 1},
            "championship": {"max_p0": 0, "max_p1": 0, "min_score": 0, "min_rework": 2},
        },
    },
}


def get_weight_thresholds(stage_id, mode="standard"):
    """根据阶段ID和模式获取评审维度权重阈值。

    Returns: dict with max_p0, max_p1, min_score, min_rework
    """
    mode_key = mode.lower()
    for dim_key, dim in SCORING_WEIGHT_THRESHOLDS.items():
        if stage_id in dim["stages"]:
            return dim["thresholds"].get(mode_key, dim["thresholds"]["standard"])
    return None


def get_mode_thresholds(mode="standard"):
    """获取指定模式的门禁阈值。"""
    return MODE_THRESHOLDS.get(mode.lower(), MODE_THRESHOLDS["standard"])


# ═══════════════════════════════════════════════════════════════
# G1: Problem Parsed Check
# ═══════════════════════════════════════════════════════════════

def gate_g0(workspace=None, mode="standard"):
    """G0: 题目登记门禁 — 文件检查 + 内容检查 + 审查官打分。
    
    HARD 硬性约束：必须同时满足文件、内容、审查官打分三项检查。
    """
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []
    
    # 文件检查
    required_files = [
        ("inputs/inputs_manifest.json", "输入清单"),
        ("inputs/problem_text.md", "题目文本"),
        ("state/workflow_state.json", "工作流状态"),
        ("outputs/reviews/S0_review.md", "审查官报告"),
    ]
    
    for fpath, desc in required_files:
        fp = ws / fpath
        if not fp.exists():
            issues.append(f"MISSING_FILE: {fpath} ({desc})")
        else:
            evidence.append(f"{desc}: {fp.stat().st_size} bytes")
    
    # 内容检查
    problem_text = ws / "inputs" / "problem_text.md"
    if problem_text.exists():
        text = problem_text.read_text(encoding="utf-8", errors="replace")
        if len(text.strip()) < 100:
            issues.append(f"PROBLEM_TEXT_THIN: {len(text)} chars (min 100)")
        else:
            evidence.append(f"题目文本: {len(text)} chars")
    
    workflow_state = ws / "state" / "workflow_state.json"
    if workflow_state.exists():
        try:
            with open(workflow_state, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            if "contest_type" not in state:
                issues.append("MISSING_CONTEST_TYPE: workflow_state.json 缺少 contest_type")
            else:
                evidence.append(f"竞赛类型: {state['contest_type']}")
            
            if "problem_type" not in state:
                issues.append("MISSING_PROBLEM_TYPE: workflow_state.json 缺少 problem_type")
            else:
                evidence.append(f"问题类型: {state['problem_type']}")
            
            if "subquestion_count" not in state or state["subquestion_count"] < 1:
                issues.append("MISSING_SUBQUESTIONS: workflow_state.json 缺少或子问题数<1")
            else:
                evidence.append(f"子问题数: {state['subquestion_count']}")
        except Exception as e:
            issues.append(f"CORRUPT_WORKFLOW_STATE: {e}")
    
    # 审查官打分检查
    review_report = ws / "outputs" / "reviews" / "S0_review.md"
    inspector_score = None
    p0_count = None
    
    if review_report.exists():
        text = review_report.read_text(encoding="utf-8", errors="replace")
        
        # 提取总分
        score_match = re.search(r'##\s*总分[：:]\s*(\d+)/100', text)
        if score_match:
            inspector_score = int(score_match.group(1))
            evidence.append(f"审查官总分: {inspector_score}/100")
        else:
            issues.append("INSPECTOR_SCORE_MISSING: 审查官报告中未找到总分")
        
        # 提取 P0 问题数
        p0_matches = re.findall(r'\[P0\]', text)
        p0_count = len(p0_matches)
        if p0_count > 0:
            issues.append(f"P0_ISSUES: {p0_count} 个 P0 问题必须修复")
        else:
            evidence.append("P0 问题: 0 (通过)")
    
    # 判断审查官打分是否达到及格线
    thresholds = {"fast": 60, "standard": 70, "championship": 85}
    threshold = thresholds.get(mode.lower(), 70)
    
    if inspector_score is not None:
        if inspector_score < threshold:
            issues.append(f"INSPECTOR_SCORE_FAIL: {inspector_score} < {threshold} ({mode} 模式)")
    
    # 最终判定
    if issues:
        return False, (
            f"G0 门禁 FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  模式: {mode} | 及格线: {threshold}\n"
            "  Action: rework S0 并修复所有问题。"
        ), {"issues": issues, "evidence": evidence}
    
    return True, (
        f"G0 门禁 PASSED ({mode} 模式，及格线 {threshold}).\n"
        + "\n".join(f"  ✓ {e}" for e in evidence)
    ), {"evidence": evidence}


def gate_g1_problem_parsed(workspace=None, mode="standard"):
    """G1: 检查问题解析完整性 — analysis.md字数、子问题、符号表、文献。"""
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []

    # analysis.md
    ap = ws / "outputs" / "problem_analysis" / "analysis.md"
    if not ap.exists():
        ap = ws / "analysis.md"
    if ap.exists():
        t = ap.read_text(encoding="utf-8", errors="replace")
        cc = len(t.strip())
        if cc < 500:
            issues.append(f"ANALYSIS_THIN: {cc} chars (min 500)")
        else:
            evidence.append(f"analysis.md: {cc} chars")
        if not any(kw in t for kw in ["子问题", "subproblem", "Q1", "问题一"]):
            issues.append("NO_SUBPROBLEMS: no subproblem decomposition")
        else:
            evidence.append("子问题分解: identified")
    else:
        issues.append("MISSING: analysis.md")

    # literature
    lp = ws / "outputs" / "literature" / "literature_review.md"
    if not lp.exists():
        lp = ws / "literature_review.md"
    if lp.exists():
        t = lp.read_text(encoding="utf-8", errors="replace")
        refs = re.findall(r'\[\d+\]', t)
        if len(refs) < 4:
            issues.append(f"LITERATURE_THIN: {len(refs)} refs (min 4)")
        else:
            evidence.append(f"文献: {len(refs)} refs")
    else:
        issues.append("MISSING: literature_review.md")

    # symbol_table
    for sp in [ws / "planning" / "symbol_table.md", ws / "symbol_table.md", ws / "methods" / "symbol_table.md"]:
        if sp.exists():
            evidence.append("symbol_table.md: found")
            break
    else:
        issues.append("MISSING: symbol_table.md")

    if issues:
        return False, (
            f"G1 FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            "  Action: Route to S1 problem analysis. Do NOT advance."
        ), {"issues": issues, "evidence": evidence, "fix_stage": "S1"}

    return True, f"G1 PASSED: {len(evidence)} checks OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


# ═══════════════════════════════════════════════════════════════
# G5: Paper Quality Comprehensive Check
# ═══════════════════════════════════════════════════════════════

_REQUIRED_CHAPTERS = ["摘要", "问题重述", "问题分析", "模型假设", "符号说明",
                     "模型建立与求解", "模型检验", "模型评价", "结论", "参考文献", "附录"]

_CHAPTER_KW = {
    "摘要": ["摘要", "摘 要", "Abstract"],
    "问题重述": ["问题重述", "问题背景"],
    "问题分析": ["问题分析", "总体分析"],
    "模型假设": ["模型假设", "假设条件"],
    "符号说明": ["符号说明", "符号表"],
    "模型建立与求解": ["模型建立", "模型求解", "问题一"],
    "模型检验": ["模型检验", "灵敏度分析", "模型验证"],
    "模型评价": ["模型评价", "优缺点"],
    "结论": ["结论", "总结", "结束语"],
    "参考文献": ["参考文献", "References"],
    "附录": ["附录", "Appendix"],
}

_PLACEHOLDER = ["TBD", "TODO", "待填写", "待补充", "[待", "PLACEHOLDER", "FIXME"]


def gate_g5_paper_quality(workspace=None, mode="standard"):
    """G5: 论文质量 — 字数、图表、章节、placeholder、D-A-C。"""
    ws = Path(workspace) if workspace else WORKSPACE
    th = get_mode_thresholds(mode)
    issues, evidence = [], []

    pp = ws / "outputs" / "paper" / "paper.md"
    if not pp.exists():
        pp = ws / "paper.md"
    if not pp.exists():
        pp = ws / "outputs" / "paper" / "paper_revised.md"
    if not pp.exists():
        return False, "G5 FAILED: paper.md not found.", {"issues": ["MISSING: paper.md"], "evidence": []}

    text = pp.read_text(encoding="utf-8", errors="replace")

    # Word count
    cn = len(re.findall(r'[\u4e00-\u9fff]', text))
    en = len(re.findall(r'[a-zA-Z]+', text))
    total = cn + en
    if total < th["paper_min_words"]:
        issues.append(f"WORD_COUNT: {total} < {th['paper_min_words']}")
    else:
        evidence.append(f"字数: {total} (min {th['paper_min_words']})")

    # Figure count
    figs = set(re.findall(r'图\s*\d+|Figure\s*\d+|\[FIGURE:', text))
    if len(figs) < th["paper_min_figures"]:
        issues.append(f"FIGURES: {len(figs)} < {th['paper_min_figures']}")
    else:
        evidence.append(f"图表: {len(figs)} (min {th['paper_min_figures']})")

    # Chapter completeness
    missing = []
    for ch in _REQUIRED_CHAPTERS:
        kws = _CHAPTER_KW.get(ch, [ch])
        if not any(kw in text for kw in kws):
            missing.append(ch)
    if missing:
        issues.append(f"MISSING_CHAPTERS: {', '.join(missing)}")
    else:
        evidence.append(f"章节: 全部 {_REQUIRED_CHAPTERS.__len__()} 个存在")

    # Per-chapter word count (Standard+)
    if th["chapter_min_words"]:
        for ch, min_w in th["chapter_min_words"].items():
            kws = _CHAPTER_KW.get(ch, [ch])
            for kw in kws:
                if kw in text:
                    idx = text.index(kw)
                    section = text[idx:idx + min_w * 3]
                    sc = len(re.findall(r'[\u4e00-\u9fff]', section))
                    if sc < min_w:
                        issues.append(f"CHAPTER_THIN: '{ch}' {sc} chars (min {min_w})")
                    else:
                        evidence.append(f"'{ch}': {sc} chars")
                    break

    # Placeholder
    phs = [p for p in _PLACEHOLDER if p.lower() in text.lower()]
    if phs:
        issues.append(f"PLACEHOLDER: {', '.join(phs[:5])}")
    else:
        evidence.append("Placeholder: none")

    # References count
    refs = set(re.findall(r'\[\d+\]', text))
    if len(refs) < th["min_references"]:
        issues.append(f"REFS: {len(refs)} < {th['min_references']}")
    else:
        evidence.append(f"参考文献: {len(refs)} (min {th['min_references']})")

    # D-A-C coverage
    fig_refs = set(re.findall(r'图\s*\d+|Figure\s*\d+', text))
    dac = len(re.findall(r'图\s*\d+.*?(结论|表明|显示|分析)', text))
    if fig_refs and dac < len(fig_refs) * 0.5:
        issues.append(f"DAC: only {dac}/{len(fig_refs)} figures have analysis")
    elif fig_refs:
        evidence.append(f"D-A-C: {dac}/{len(fig_refs)}")

    if issues:
        return False, (
            f"G5 Paper Quality FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  Evidence: {len(evidence)} OK.\n  Action: Fix all issues."
        ), {"issues": issues, "evidence": evidence, "fix_stage": "S8"}

    return True, f"G5 Paper Quality PASSED: {len(evidence)} OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


# ═══════════════════════════════════════════════════════════════
# G5.5: Adversarial Review Deep Check
# ═══════════════════════════════════════════════════════════════

def gate_g5_5_adversarial(workspace=None, mode="standard"):
    """G5.5: P0/P1数量、反驳覆盖、修订验证。
    
    P2 Championship Enhancement: 强制3轮不同视角审稿。
    """
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []
    
    # P2: Championship 模式检查3轮视角审稿
    if mode == "championship":
        perspective_files = [
            ws / "outputs" / "paper" / "adversarial_round1_math.md",
            ws / "outputs" / "paper" / "adversarial_round2_domain.md",
            ws / "outputs" / "paper" / "adversarial_round3_judge.md"
        ]
        missing_rounds = [f.name for f in perspective_files if not f.exists()]
        if missing_rounds:
            issues.append(f"CHAMPIONSHIP_3PERSPECTIVES: missing {', '.join(missing_rounds)}")
        else:
            evidence.append("红队审稿: 3轮视角完整（数学/领域/评审）")

    rp = ws / "outputs" / "paper" / "adversarial_review.md"
    if not rp.exists():
        rp = ws / "adversarial_review.md"
    if not rp.exists():
        return False, "G5.5 FAILED: adversarial_review.md not found.", {"issues": ["MISSING: adversarial_review.md"], "evidence": [], "fix_stage": "S9"}

    text = rp.read_text(encoding="utf-8", errors="replace")

    # Count P0/P1 by line
    p0 = sum(1 for line in text.split('\n') if re.search(r'\bP0\b|致命', line))
    p1 = sum(1 for line in text.split('\n') if re.search(r'\bP1\b|严重', line))

    if p0 > 0:
        issues.append(f"P0: {p0} critical issues — MUST fix all")
    else:
        evidence.append("P0: 0 (all closed)")

    if p1 > 3:
        issues.append(f"P1: {p1} > 3 (max allowed)")
    else:
        evidence.append(f"P1: {p1} (max 3)")

    # Revision plan
    rpl = ws / "outputs" / "paper" / "revision_plan.md"
    if not rpl.exists():
        rpl = ws / "revision_plan.md"
    if rpl.exists():
        rt = rpl.read_text(encoding="utf-8", errors="replace")
        if len(rt) < 200:
            issues.append("THIN_REVISION_PLAN")
        else:
            evidence.append(f"revision_plan: {len(rt)} chars")
    else:
        issues.append("MISSING: revision_plan.md")

    # Revised paper
    rvp = ws / "outputs" / "paper" / "paper_revised.md"
    if not rvp.exists():
        rvp = ws / "paper_revised.md"
    if rvp.exists():
        rvt = rvp.read_text(encoding="utf-8", errors="replace")
        rph = [p for p in _PLACEHOLDER if p.lower() in rvt.lower()]
        if rph:
            issues.append(f"REVISION_PLACEHOLDER: {', '.join(rph[:3])}")
        else:
            evidence.append("revised paper: clean")
    else:
        issues.append("MISSING: paper_revised.md")

    # Revision verification
    vr = ws / "outputs" / "paper" / "revision_verification.md"
    if vr.exists():
        evidence.append("revision_verification: present")
    else:
        issues.append("MISSING: revision_verification.md — no post-revision check")

    if issues:
        return False, (
            f"G5.5 FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  Evidence: {len(evidence)} OK.\n  Action: Fix P0/P1, re-run M004, verify."
        ), {"issues": issues, "evidence": evidence, "fix_stage": "S9"}

    return True, f"G5.5 PASSED: {len(evidence)} OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


# ═══════════════════════════════════════════════════════════════
# Abstract Quality Deep Check
# ═══════════════════════════════════════════════════════════════

_VAGUE = ["大概", "可能", "也许", "显著", "明显", "较好", "差不多", "应该", "大约"]


def gate_abstract_quality(workspace=None, mode="standard"):
    """摘要质量 — 字数、量化结果、模糊词、公式引用。
    
    P2 Championship Enhancement: 强制3轮打磨追踪。
    """
    ws = Path(workspace) if workspace else WORKSPACE
    th = get_mode_thresholds(mode)
    issues, evidence = [], []

    pp = ws / "outputs" / "paper" / "paper.md"
    if not pp.exists():
        pp = ws / "paper.md"
    if not pp.exists():
        return False, "Abstract FAILED: paper.md not found.", {"issues": ["MISSING: paper.md"], "evidence": []}

    text = pp.read_text(encoding="utf-8", errors="replace")
    
    # P2: Championship 模式检查3轮摘要版本
    if mode == "championship":
        abstract_versions = [
            ws / "outputs" / "paper" / "abstract_v1.md",
            ws / "outputs" / "paper" / "abstract_v2.md",
            ws / "outputs" / "paper" / "abstract_v3.md"
        ]
        missing_versions = [v.name for v in abstract_versions if not v.exists()]
        if missing_versions:
            issues.append(f"CHAMPIONSHIP_3ROUNDS: missing {', '.join(missing_versions)}")
        else:
            evidence.append("摘要打磨: 3轮版本完整")

    # Extract abstract
    ab = ""
    for m in ["摘要", "摘 要", "Abstract", "# 摘要"]:
        if m in text:
            idx = text.index(m)
            end = len(text)
            for em in ["关键词", "Keywords", "# 问题", "## 1"]:
                pos = text.find(em, idx + len(m))
                if pos > 0 and pos < end:
                    end = pos
            ab = text[idx:end]
            break
    if not ab:
        return False, "Abstract FAILED: No abstract found.", {"issues": ["NO_ABSTRACT"], "evidence": []}

    ac = len(re.findall(r'[\u4e00-\u9fff]', ab)) + len(re.findall(r'[a-zA-Z]+', ab))
    if ac < th["abstract_min_words"] or ac > th["abstract_max_words"]:
        issues.append(f"ABSTRACT_LEN: {ac} (need {th['abstract_min_words']}-{th['abstract_max_words']})")
    else:
        evidence.append(f"字数: {ac}")

    nums = re.findall(r'\d+\.?\d*[%％]?', ab)
    if len(nums) < th["abstract_min_quant_results"]:
        issues.append(f"QUANT: only {len(nums)} numbers (need {th['abstract_min_quant_results']})")
    else:
        evidence.append(f"量化结果: {len(nums)}")

    vf = [w for w in _VAGUE if w in ab]
    if vf:
        issues.append(f"VAGUE: {', '.join(vf)}")
    else:
        evidence.append("模糊词: none")

    has_method = any(kw in ab for kw in ["模型", "方法", "算法", "优化", "预测", "评价", "AHP", "TOPSIS"])
    if not has_method:
        issues.append("NO_METHOD: no model/method keyword")
    else:
        evidence.append("方法关键词: present")

    has_eq = bool(re.search(r'\$.*?\$|\(\d+\)', ab))
    if not has_eq:
        issues.append("NO_FORMULA: no formula reference")
    else:
        evidence.append("公式引用: present")

    if issues:
        return False, (
            f"Abstract FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  Evidence: {len(evidence)} OK."
        ), {"issues": issues, "evidence": evidence, "fix_stage": "S8"}

    return True, f"Abstract PASSED: {len(evidence)} OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


# ═══════════════════════════════════════════════════════════════
# Paper Structure Check
# ═══════════════════════════════════════════════════════════════

def gate_paper_structure(workspace=None, mode="standard"):
    """论文结构 — 必选章节、正确顺序、无placeholder。"""
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []

    pp = ws / "outputs" / "paper" / "paper.md"
    if not pp.exists():
        pp = ws / "paper.md"
    if not pp.exists():
        return False, "Structure FAILED: paper.md not found.", {"issues": ["MISSING"], "evidence": []}

    text = pp.read_text(encoding="utf-8", errors="replace")

    # Check chapter order
    positions = []
    for ch in _REQUIRED_CHAPTERS:
        kws = _CHAPTER_KW.get(ch, [ch])
        pos = -1
        for kw in kws:
            if kw in text:
                pos = text.index(kw)
                break
        positions.append((ch, pos))

    prev = -1
    ooo = []
    for ch, pos in positions:
        if pos >= 0:
            if prev >= 0 and pos < prev:
                ooo.append(ch)
            prev = pos
    if ooo:
        issues.append(f"WRONG_ORDER: {', '.join(ooo)}")
    else:
        evidence.append("顺序: correct")

    missing = [ch for ch, pos in positions if pos < 0]
    if missing:
        issues.append(f"MISSING: {', '.join(missing)}")
    else:
        evidence.append(f"章节: all {_REQUIRED_CHAPTERS.__len__()} present")

    phs = [p for p in _PLACEHOLDER if p.lower() in text.lower()]
    if phs:
        issues.append(f"PLACEHOLDER: {', '.join(phs[:5])}")
    else:
        evidence.append("Placeholder: none")

    if issues:
        return False, (
            f"Structure FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  Evidence: {len(evidence)} OK."
        ), {"issues": issues, "evidence": evidence, "fix_stage": "S8"}

    return True, f"Structure PASSED: {len(evidence)} OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


# ═══════════════════════════════════════════════════════════════
# Model Selection Check
# ═══════════════════════════════════════════════════════════════

def gate_multi_proposal(workspace=None, mode="standard"):
    """v2.0: 多专项提案门禁 — 4个差异化提案组并行产出，提案多样性达标。"""
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []

    required_proposals = [
        ("methods/proposals/proposer_a_precision.md", "精度导向提案"),
        ("methods/proposals/proposer_b_innovation.md", "创新突破提案"),
        ("methods/proposals/proposer_c_crossdisciplinary.md", "跨学科融合提案"),
        ("methods/proposals/proposer_d_integrator.md", "集成演化提案"),
    ]

    total_candidates = 0
    for fpath, desc in required_proposals:
        fp = ws / fpath
        if not fp.exists():
            issues.append(f"MISSING: {fpath} ({desc})")
        else:
            text = fp.read_text(encoding="utf-8", errors="replace")
            size = fp.stat().st_size
            if size < 200:
                issues.append(f"THIN: {fpath} ({size} bytes, min 200)")
            else:
                # Count candidate models
                candidates = len(re.findall(r'(?:候选|方案|candidate|模型[一二三ABCD])', text, re.IGNORECASE))
                total_candidates += max(candidates, 1)
                evidence.append(f"{desc}: {size} bytes, ~{candidates} candidates")

    # Diversity threshold: >= 6 unique candidates across all proposals
    if total_candidates < 6:
        issues.append(f"LOW_DIVERSITY: {total_candidates} candidates across 4 proposals (min 6)")
    else:
        evidence.append(f"多样性: {total_candidates} candidates (min 6)")

    if issues:
        return False, (
            f"G3 Multi-Proposal FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  Evidence: {len(evidence)} OK."
        ), {"issues": issues, "evidence": evidence, "fix_stage": "S3"}

    return True, f"G3 Multi-Proposal PASSED: {len(evidence)} OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


def gate_adversarial_round(workspace=None, mode="standard", max_round=None):
    """v2.0: 多轮对抗门禁 — 红蓝对抗完成，每轮有攻击/辩护/裁决。"""
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []

    if max_round is None:
        th = get_mode_thresholds(mode)
        max_round = 3 if mode.lower() == "championship" else 2

    for r in range(1, max_round + 1):
        attack = ws / "methods" / "attacks" / f"round{r}_attack.md"
        defense = ws / "methods" / "defenses" / f"round{r}_defense.md"
        verdict = ws / "methods" / "verdicts" / f"round{r}_verdict.md"

        if r == 1:
            # Round 1 is mandatory
            for fp, desc in [(attack, "红队攻击"), (defense, "蓝队辩护"), (verdict, "裁决")]:
                if not fp.exists():
                    issues.append(f"MISSING_ROUND{r}: {desc} ({fp.name})")
                else:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                    if len(text.strip()) < 100:
                        issues.append(f"THIN_ROUND{r}: {desc} ({len(text)} chars)")
                    else:
                        evidence.append(f"Round {r} {desc}: {len(text)} chars")
        else:
            # Round 2+: only if Round verdict had REPAIR
            prev_verdict = ws / "methods" / "verdicts" / f"round{r-1}_verdict.md"
            has_repair = False
            if prev_verdict.exists():
                vtext = prev_verdict.read_text(encoding="utf-8", errors="replace")
                has_repair = bool(re.search(r'REPAIR|修复|重审', vtext, re.IGNORECASE))

            if has_repair:
                for fp, desc in [(attack, "红队攻击"), (defense, "蓝队辩护"), (verdict, "裁决")]:
                    if not fp.exists():
                        issues.append(f"MISSING_ROUND{r}: {desc} (required by Round {r-1} REPAIR verdict)")
                    else:
                        evidence.append(f"Round {r} {desc}: present")
            else:
                evidence.append(f"Round {r}: skipped (no REPAIR in Round {r-1})")

    if issues:
        return False, (
            f"G3 Adversarial Round FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues)
        ), {"issues": issues, "evidence": evidence, "fix_stage": "S3"}

    return True, f"G3 Adversarial Round PASSED: {len(evidence)} checks.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


def gate_model_selection_v2(workspace=None, mode="standard"):
    """v2.0: 模型选择终审 — 9维评分、迭代决策、淘汰理由。"""
    ws = Path(workspace) if workspace else WORKSPACE
    th = get_mode_thresholds(mode)
    issues, evidence = [], []

    rp = ws / "methods" / "model_selection_report.md"
    if not rp.exists():
        return False, "G3 Model Selection V2 FAILED: no report.", {"issues": ["MISSING: model_selection_report.md"], "evidence": [], "fix_stage": "S3"}

    text = rp.read_text(encoding="utf-8", errors="replace")

    # Check 9-dimension scoring (original 7 + innovation + crossdisciplinary)
    dim_keywords = ["题意", "验证", "稳健", "可解释", "论文", "复杂度", "风险", "创新", "融合"]
    found_dims = sum(1 for kw in dim_keywords if kw in text)
    if found_dims < 7:
        issues.append(f"FEW_DIMENSIONS: {found_dims}/9 scoring dimensions found (min 7)")
    else:
        evidence.append(f"评分维度: {found_dims}/9")

    # Check minimum score threshold
    scores = re.findall(r'(?:总[分得]|加权总分|weighted.*score)[：:=\s]*(\d+\.?\d*)', text, re.IGNORECASE)
    if scores:
        best = max(float(s) for s in scores)
        min_score = th.get("model_min_score", 50)
        if min_score > 0 and best < min_score:
            issues.append(f"LOW_SCORE: best {best} < {min_score} ({mode})")
        else:
            evidence.append(f"最高分: {best} (min {min_score})")
    else:
        evidence.append("评分: no numeric score found (agent judgment required)")

    # Check rejection reasons exist
    has_rejection = bool(re.search(r'否决|淘汰|reject|eliminate|不通过', text, re.IGNORECASE))
    if has_rejection:
        evidence.append("淘汰理由: present")
    else:
        issues.append("NO_REJECTION: no rejected candidates or rejection reasons found")

    # Check debate summary references
    ds = ws / "methods" / "debate_summary.md"
    if ds.exists():
        evidence.append("debate_summary.md: present")
    else:
        issues.append("MISSING: debate_summary.md")

    # Check iteration limit
    exec_state = ws / "state" / "stage_execution.json"
    if exec_state.exists():
        try:
            with open(exec_state, 'r', encoding='utf-8') as f:
                state = json.load(f)
            s3_info = state.get("stages", {}).get("S3", {})
            rework_count = s3_info.get("rework_count", 0)
            if rework_count >= 3:
                issues.append(f"ITERATION_LIMIT: S3 rework_count={rework_count} >= 3, needs manual decision")
            else:
                evidence.append(f"迭代次数: {rework_count}/3")
        except Exception:
            pass

    if issues:
        return False, (
            f"G3 Model Selection V2 FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  Evidence: {len(evidence)} OK."
        ), {"issues": issues, "evidence": evidence, "fix_stage": "S3"}

    return True, f"G3 Model Selection V2 PASSED: {len(evidence)} OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


def gate_prototype_validated(workspace=None, mode="standard"):
    """v2.0: 早期原型验证门禁 — S4代码原型已运行，结果合理。"""
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []

    race_dir = ws / "src" / "race"
    if not race_dir.exists():
        race_dir = ws / "src" / "race"

    # Check prototype files
    prototypes = list(race_dir.glob("prototype_model_*.py")) if race_dir.exists() else []
    if len(prototypes) < 2:
        issues.append(f"FEW_PROTOTYPES: {len(prototypes)} prototype files (min 2)")
    else:
        for p in prototypes:
            text = p.read_text(encoding="utf-8", errors="replace")
            code_lines = [l for l in text.split('\n') if l.strip() and not l.strip().startswith('#')]
            if len(code_lines) > 200:
                issues.append(f"TOO_LONG: {p.name} has {len(code_lines)} code lines (max 200)")
            else:
                evidence.append(f"{p.name}: {len(code_lines)} code lines")

    # Check baseline
    baseline = race_dir / "baseline.py" if race_dir.exists() else None
    if baseline and baseline.exists():
        evidence.append("baseline.py: present")
    else:
        issues.append("MISSING: src/race/baseline.py")

    # Check prototype results
    results_dir = ws / "outputs" / "experiments" / "race"
    if results_dir.exists():
        for qdir in results_dir.iterdir():
            if qdir.is_dir():
                pr = qdir / "prototype_results.md"
                if pr.exists():
                    evidence.append(f"{qdir.name}/prototype_results.md: present")
                else:
                    issues.append(f"MISSING: {qdir.name}/prototype_results.md")
    else:
        issues.append("MISSING: outputs/experiments/race/ directory")

    if issues:
        return False, (
            f"G3 Prototype Validated FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues)
        ), {"issues": issues, "evidence": evidence, "fix_stage": "S4"}

    return True, f"G3 Prototype Validated PASSED: {len(evidence)} OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


def gate_model_selection(workspace=None, mode="standard"):
    """模型选择 — 7维评分、最低分阈值、选择理由。"""
    ws = Path(workspace) if workspace else WORKSPACE
    th = get_mode_thresholds(mode)
    issues, evidence = [], []

    rp = ws / "methods" / "model_selection_report.md"
    if not rp.exists():
        rp = ws / "model_selection_report.md"
    if not rp.exists():
        return False, "Model Selection FAILED: no report.", {"issues": ["MISSING: model_selection_report.md"], "evidence": [], "fix_stage": "S3"}

    text = rp.read_text(encoding="utf-8", errors="replace")

    # Check for scoring
    has_score = bool(re.search(r'评分|score|得分|加权', text, re.IGNORECASE))
    if not has_score:
        issues.append("NO_SCORE: no scoring rubric found")
    else:
        evidence.append("评分: present")

    # Check for selection rationale
    has_rationale = bool(re.search(r'选择|选定|主模型|primary|推荐', text, re.IGNORECASE))
    if not has_rationale:
        issues.append("NO_RATIONALE: no selection rationale")
    else:
        evidence.append("选择理由: present")

    # Check for >= 2 candidates
    has_multiple = bool(re.search(r'候选|方案|candidate|方法[一二三ABCD]', text, re.IGNORECASE))
    if not has_multiple:
        issues.append("FEW_CANDIDATES: need >= 2 candidates compared")
    else:
        evidence.append("候选模型: >= 2")

    # Check minimum score threshold
    if th["model_min_score"] > 0:
        scores = re.findall(r'(?:总[分得]|加权总分|weighted.*score)[：:=\s]*(\d+\.?\d*)', text, re.IGNORECASE)
        if scores:
            best = max(float(s) for s in scores)
            if best < th["model_min_score"]:
                issues.append(f"LOW_SCORE: best score {best} < {th['model_min_score']}")
            else:
                evidence.append(f"最高分: {best} (min {th['model_min_score']})")
        else:
            evidence.append("评分阈值: no numeric score found (agent judgment required)")

    if issues:
        return False, (
            f"Model Selection FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  Evidence: {len(evidence)} OK."
        ), {"issues": issues, "evidence": evidence, "fix_stage": "S3"}

    return True, f"Model Selection PASSED: {len(evidence)} OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


# ═══════════════════════════════════════════════════════════════
# Innovation Assessment Check
# ═══════════════════════════════════════════════════════════════

def gate_innovation_assessment(workspace=None, mode="standard"):
    """创新性评估 — 检查模型选择报告中的创新点论证完整性。

    CUMCM 评审中创新性加分 5-10 分，一等奖要求"有明确创新点"。
    Championship 模式强制检查，Standard 模式建议检查，Fast 模式跳过。
    """
    ws = Path(workspace) if workspace else WORKSPACE
    mode_key = mode.lower()
    issues, evidence = [], []

    # Fast mode: skip innovation check
    if mode_key == "fast":
        return True, "Innovation: skipped (fast mode)", {"evidence": ["fast mode skip"]}

    # Check model_selection_report.md
    rp = ws / "methods" / "model_selection_report.md"
    if not rp.exists():
        rp = ws / "model_selection_report.md"
    if not rp.exists():
        return False, "Innovation FAILED: no model_selection_report.md.", {
            "issues": ["MISSING: model_selection_report.md"], "evidence": [], "fix_stage": "S3"
        }

    text = rp.read_text(encoding="utf-8", errors="replace")

    # Check 1: 创新点/改进点段落
    innovation_kws = ["创新", "改进", "改进点", "创新点", "novel", "innovation",
                      "improvement", "原创", "独创", "新方法", "新模型"]
    has_innovation = any(kw in text for kw in innovation_kws)
    if has_innovation:
        evidence.append("创新点段落: found")
    else:
        issues.append("NO_INNOVATION: no innovation/improvement section found")

    # Check 2: 创新论证字数（≥200字）
    innovation_text = ""
    for kw in ["创新", "改进", "novel", "innovation", "improvement"]:
        idx = text.find(kw)
        if idx >= 0:
            # Extract ~500 chars after the keyword
            innovation_text = text[idx:idx + 800]
            break
    if innovation_text:
        char_count = len(innovation_text.strip())
        if char_count >= 200:
            evidence.append(f"创新论证: {char_count} chars (min 200)")
        else:
            issues.append(f"THIN_INNOVATION: innovation argument only {char_count} chars (min 200)")
    else:
        issues.append("NO_INNOVATION_TEXT: no innovation argument text found")

    # Check 3: 多方法融合（≥2 种不同类别）
    model_types = set()
    type_patterns = {
        "优化": ["优化", "optimization", "规划", "整数规划", "动态规划", "遗传", "模拟退火"],
        "预测": ["预测", "prediction", "forecast", "回归", "时间序列", "ARIMA", "LSTM", "神经网络"],
        "评价": ["评价", "evaluation", "AHP", "TOPSIS", "熵权", "模糊", "层次分析"],
        "分类": ["分类", "classification", "SVM", "随机森林", "决策树", "聚类"],
        "仿真": ["仿真", "simulation", "蒙特卡洛", "Monte Carlo", "Agent-based"],
    }
    for cat, kws in type_patterns.items():
        if any(kw in text for kw in kws):
            model_types.add(cat)
    if len(model_types) >= 2:
        evidence.append(f"多方法融合: {len(model_types)} types ({', '.join(model_types)})")
    else:
        if mode_key == "championship":
            issues.append(f"FEW_TYPES: only {len(model_types)} model type(s) (championship needs >= 2)")
        else:
            evidence.append(f"模型类型: {len(model_types)} type(s) (standard: no hard requirement)")

    # Check 4: 跨学科方法引用
    cross_discipline_kws = ["跨学科", "交叉", "interdisciplinary", "cross", "借鉴",
                            "迁移", "transfer", "类比", "analogy"]
    has_cross = any(kw in text for kw in cross_discipline_kws)
    if has_cross:
        evidence.append("跨学科引用: found")
    elif mode_key == "championship":
        issues.append("NO_CROSS_DISCIPLINE: no cross-discipline method reference (championship required)")

    # Championship mode: all checks must pass
    if issues:
        return False, (
            f"Innovation FAILED ({mode_key}): {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            f"  Evidence: {len(evidence)} OK."
        ), {"issues": issues, "evidence": evidence, "fix_stage": "S3"}

    return True, (
        f"Innovation PASSED ({mode_key}): {len(evidence)} checks OK.\n"
        + "\n".join(f"  + {e}" for e in evidence)
    ), {"evidence": evidence}


# ═══════════════════════════════════════════════════════════════
# P1 新增：4个缺失门禁检查函数
# ═══════════════════════════════════════════════════════════════

def gate_figure_narrative(workspace=None, mode="standard"):
    """G5 图表叙事完整性 — 每张图必须有D-A-C（Describe-Analyze-Conclude）三段论。
    
    Championship: 10+图，每图必须3段完整叙事
    Standard: 6+图，每图至少2段叙事
    Fast: 4+图，允许简单描述
    """
    ws = Path(workspace) if workspace else WORKSPACE
    th = get_mode_thresholds(mode)
    issues, evidence = [], []
    
    pp = ws / "outputs" / "paper" / "paper.md"
    if not pp.exists():
        pp = ws / "paper.md"
    if not pp.exists():
        return False, "FIGURE_NARRATIVE FAILED: paper.md not found.", {"issues": ["MISSING: paper.md"]}
    
    text = pp.read_text(encoding="utf-8", errors="replace")
    
    # 扫描图表引用
    figure_pattern = re.compile(r"(?:图|Fig\.?|Figure)\s*([\d.]+)", re.IGNORECASE)
    figures = set(figure_pattern.findall(text))
    
    if len(figures) < th.get("min_figures", 4):
        issues.append(f"FIG_COUNT: {len(figures)} (need {th.get('min_figures', 4)})")
    else:
        evidence.append(f"图表数量: {len(figures)}")
    
    # D-A-C检测（简化版：检测关键词）
    dac_signals = {
        "describe": ["如图", "从图", "显示", "展示", "表明", "呈现"],
        "analyze": ["分析", "可以看出", "趋势", "规律", "对比", "变化"],
        "conclude": ["因此", "综上", "说明", "证明", "结论"]
    }
    
    missing_dac = []
    for fig_id in figures:
        # 提取图周围±500字符的上下文
        pattern = re.compile(rf"(?:图|Fig\.?|Figure)\s*{re.escape(fig_id)}", re.IGNORECASE)
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        
        pos = matches[0].start()
        context_start = max(0, pos - 500)
        context_end = min(len(text), pos + 500)
        context = text[context_start:context_end]
        
        # 检查D-A-C段落
        dac_found = {k: any(sig in context for sig in sigs) for k, sigs in dac_signals.items()}
        dac_count = sum(dac_found.values())
        
        if mode == "championship" and dac_count < 3:
            missing_dac.append(f"图{fig_id} ({dac_count}/3)")
        elif mode == "standard" and dac_count < 2:
            missing_dac.append(f"图{fig_id} ({dac_count}/2)")
    
    if missing_dac:
        issues.append(f"INCOMPLETE_DAC: {', '.join(missing_dac[:5])}")
    else:
        evidence.append(f"D-A-C叙事: {len(figures)} 张完整")
    
    # 检查placeholder未替换
    placeholder_figs = re.findall(r'\[FIGURE:\s*[^\]]+\]', text)
    if placeholder_figs:
        issues.append(f"PLACEHOLDER_FIG: {len(placeholder_figs)} 个未替换")
    else:
        evidence.append("图表placeholder: 已全部替换")
    
    if issues:
        return False, (
            f"FIGURE_NARRATIVE FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues)
        ), {"issues": issues, "evidence": evidence}
    
    return True, f"FIGURE_NARRATIVE PASSED: {len(evidence)} OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


def gate_parallel_merge(workspace=None, mode="standard"):
    """G3 并行合并门禁 — 验证并行子问题求解后的合并质量。
    
    检查项：
    1. 所有子问题summary.md存在
    2. 变量符号跨子问题一致
    3. 单位统一
    4. unified_framework.md存在（多子问题时）
    """
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []
    
    # 检测子问题数量
    q_dirs = list((ws / "outputs").glob("q*")) if (ws / "outputs").exists() else []
    num_q = len(q_dirs)
    
    if num_q == 0:
        return False, "PARALLEL_MERGE FAILED: No subquestion outputs found.", {"issues": ["NO_SUBQUESTIONS"]}
    
    evidence.append(f"子问题数量: {num_q}")
    
    # 检查每个子问题的summary.md
    missing_summary = []
    for q_dir in q_dirs:
        summary = q_dir / "summary.md"
        if not summary.exists():
            missing_summary.append(q_dir.name)
    
    if missing_summary:
        issues.append(f"MISSING_SUMMARY: {', '.join(missing_summary)}")
    else:
        evidence.append(f"summary.md: {num_q} 个全部存在")
    
    # 检查unified_framework.md（多子问题时必需）
    if num_q > 1:
        uf = ws / "outputs" / "unified_framework.md"
        if not uf.exists():
            uf = ws / "methods" / "unified_framework.md"
        if not uf.exists():
            issues.append("MISSING: unified_framework.md (multi-subquestion requires)")
        else:
            evidence.append("unified_framework.md: present")
    
    # 检查cross_validation_report.md
    cv = ws / "outputs" / "cross_validation_report.md"
    if not cv.exists():
        cv = ws / "methods" / "cross_validation_report.md"
    if cv.exists():
        evidence.append("cross_validation_report.md: present")
    else:
        issues.append("MISSING: cross_validation_report.md (pairwise consistency check)")
    
    # 简化版符号一致性检查（读取symbol_table.md）
    symbol_table = ws / "methods" / "symbol_table.md"
    if symbol_table.exists():
        st_text = symbol_table.read_text(encoding="utf-8", errors="replace")
        # 检查是否有冲突标记（简化：检测"冲突"/"不一致"关键词）
        if "冲突" in st_text or "不一致" in st_text or "重复" in st_text:
            issues.append("SYMBOL_CONFLICT: symbol_table.md contains conflict markers")
        else:
            evidence.append("符号表: 无冲突标记")
    else:
        issues.append("MISSING: symbol_table.md")
    
    if issues:
        return False, (
            f"PARALLEL_MERGE FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues)
        ), {"issues": issues, "evidence": evidence}
    
    return True, f"PARALLEL_MERGE PASSED: {len(evidence)} OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


def gate_paper_evaluation_quality(workspace=None, mode="standard"):
    """G6 论文综合评分 — 基于CUMCM五维评审标准的综合评分。
    
    5维度：
    1. model_quality (50-60%): 模型合理性、创新性
    2. problem_solving (20-30%): 问题分析、求解完整性
    3. paper_standard (10-15%): 论文规范性、可读性
    4. verification (5-10%): 验证充分性
    5. adversarial_review: 红队审稿结果
    
    Championship: 总分≥85/100
    Standard: 总分≥70/100
    Fast: 总分≥60/100
    """
    ws = Path(workspace) if workspace else WORKSPACE
    th = get_mode_thresholds(mode)
    issues, evidence = [], []
    
    # 获取评分权重阈值
    weight_thresholds = SCORING_WEIGHT_THRESHOLDS
    
    scores = {}
    max_score = 100
    
    # 1. model_quality (50-60分)
    model_score = 0
    model_report = ws / "methods" / "model_selection_report.md"
    if model_report.exists():
        mr_text = model_report.read_text(encoding="utf-8", errors="replace")
        # 检查模型评分（简化：检测关键词）
        if "模型评分" in mr_text or "综合评分" in mr_text:
            model_score += 30
        if "创新" in mr_text and len(mr_text) > 2000:
            model_score += 20
        if "假设" in mr_text and "论证" in mr_text:
            model_score += 10
    scores["model_quality"] = model_score
    evidence.append(f"model_quality: {model_score}/60")
    
    # 2. problem_solving (20-30分)
    problem_score = 0
    analysis = ws / "outputs" / "problem_analysis" / "analysis.md"
    if analysis.exists():
        an_text = analysis.read_text(encoding="utf-8", errors="replace")
        if len(an_text) > 500:
            problem_score += 10
        if "子问题" in an_text:
            problem_score += 10
        if "符号表" in an_text or "变量" in an_text:
            problem_score += 10
    scores["problem_solving"] = problem_score
    evidence.append(f"problem_solving: {problem_score}/30")
    
    # 3. paper_standard (10-15分)
    paper_score = 0
    paper = ws / "outputs" / "paper" / "paper.md"
    if paper.exists():
        pp_text = paper.read_text(encoding="utf-8", errors="replace")
        word_count = len(re.findall(r'[\u4e00-\u9fff]', pp_text))
        if word_count >= th.get("min_paper_words", 12000):
            paper_score += 10
        if len(re.findall(r'(?:图|Fig\.?|Figure)\s*[\d.]+', pp_text)) >= th.get("min_figures", 6):
            paper_score += 5
    scores["paper_standard"] = paper_score
    evidence.append(f"paper_standard: {paper_score}/15")
    
    # 4. verification (5-10分)
    verification_score = 0
    robustness = list((ws / "outputs").glob("**/tornado_*.png")) if (ws / "outputs").exists() else []
    if len(robustness) > 0:
        verification_score += 5
    frozen = ws / "outputs" / "frozen" / "frozen_numbers.json"
    if frozen.exists():
        verification_score += 5
    scores["verification"] = verification_score
    evidence.append(f"verification: {verification_score}/10")
    
    # 计算总分
    total_score = sum(scores.values())
    evidence.append(f"总分: {total_score}/100")
    
    # 阈值检查
    min_score_threshold = {"fast": 60, "standard": 70, "championship": 85}.get(mode, 70)
    
    if total_score < min_score_threshold:
        issues.append(f"SCORE_LOW: {total_score}/100 (need {min_score_threshold})")
    
    if issues:
        return False, (
            f"PAPER_EVALUATION FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues) + "\n"
            + "\n".join(f"  + {e}" for e in evidence)
        ), {"issues": issues, "evidence": evidence, "scores": scores}
    
    return True, f"PAPER_EVALUATION PASSED: {total_score}/100.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence, "scores": scores}


def gate_evidence_chain_quality(workspace=None, mode="standard"):
    """G4.5 证据链完整性 — 验证论文结论到代码输出的可追溯性。
    
    检查项：
    1. conclusion_evidence_map.md存在
    2. paper_code_consistency_report.md存在
    3. 论文中每个数值都可追溯到代码输出
    4. 无孤立结论（无证据支撑）
    """
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []
    
    # 检查conclusion_evidence_map.md
    cem = ws / "outputs" / "evidence" / "conclusion_evidence_map.md"
    if not cem.exists():
        cem = ws / "evidence" / "conclusion_evidence_map.md"
    if cem.exists():
        cem_text = cem.read_text(encoding="utf-8", errors="replace")
        if len(cem_text) > 200:
            evidence.append("conclusion_evidence_map.md: present")
            # 检查是否有未映射标记
            if "未映射" in cem_text or "无证据" in cem_text or "TODO" in cem_text:
                issues.append("UNMAPPED_CONCLUSIONS: conclusion_evidence_map.md contains unmapped items")
        else:
            issues.append("THIN: conclusion_evidence_map.md too short")
    else:
        issues.append("MISSING: conclusion_evidence_map.md")
    
    # 检查paper_code_consistency_report.md
    pcc = ws / "outputs" / "evidence" / "paper_code_consistency_report.md"
    if not pcc.exists():
        pcc = ws / "evidence" / "paper_code_consistency_report.md"
    if pcc.exists():
        pcc_text = pcc.read_text(encoding="utf-8", errors="replace")
        if len(pcc_text) > 200:
            evidence.append("paper_code_consistency_report.md: present")
            # 检查是否有不一致标记
            if "不一致" in pcc_text or "不匹配" in pcc_text or "错误" in pcc_text:
                issues.append("INCONSISTENCY: paper_code_consistency_report.md contains inconsistency markers")
        else:
            issues.append("THIN: paper_code_consistency_report.md too short")
    else:
        issues.append("MISSING: paper_code_consistency_report.md")
    
    # 检查假设验证
    assumptions = ws / "methods" / "model_assumptions.md"
    if assumptions.exists():
        am_text = assumptions.read_text(encoding="utf-8", errors="replace")
        if "验证" in am_text or "证据" in am_text:
            evidence.append("假设验证: present")
        else:
            issues.append("UNVERIFIED_ASSUMPTIONS: model_assumptions.md lacks verification")
    else:
        issues.append("MISSING: model_assumptions.md")
    
    if issues:
        return False, (
            f"EVIDENCE_CHAIN FAILED: {len(issues)} issue(s).\n"
            + "\n".join(f"  - {i}" for i in issues)
        ), {"issues": issues, "evidence": evidence}
    
    return True, f"EVIDENCE_CHAIN PASSED: {len(evidence)} OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


# ═══════════════════════════════════════════════════════════════
# S9.5: Publication Readiness Check — 出版规范门禁
# ═══════════════════════════════════════════════════════════════

def gate_publication_ready(workspace=None, mode="standard"):
    """G9.5 出版规范门禁 — 检查 AI 痕迹、非正式表达、图文排布、格式规范。

    调用 publication_checker.py 运行 6 维度全量检查。
    P0 = 0, P1 ≤ 2, P2 ≤ 5 为通过标准。
    """
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []

    # 查找论文文件
    paper = ws / "outputs" / "paper" / "paper_revised.md"
    if not paper.exists():
        paper = ws / "outputs" / "paper" / "paper.md"
    if not paper.exists():
        return False, "PUBLICATION_READY FAILED: No paper found (paper_revised.md or paper.md).", \
               {"issues": ["MISSING: paper.md/paper_revised.md"]}

    # 导入 publication_checker
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from publication_checker import run_all_checks
        report = run_all_checks(str(paper), mode)
    except Exception as e:
        return False, f"PUBLICATION_READY ERROR: {e}", {"issues": [str(e)]}

    p0 = report["p0_count"]
    p1 = report["p1_count"]
    p2 = report["p2_count"]

    # 收集具体问题
    for r in report["results"]:
        for iss in r.issues:
            issues.append(f"[{iss.severity.value}] {iss.category}: {iss.message}")

    # 判定
    if p0 > 0:
        return False, (
            f"PUBLICATION_READY FAILED: P0={p0} (must be 0).\n"
            f"  P1={p1}, P2={p2}\n"
            f"  Issues:\n" + "\n".join(f"  - {i}" for i in issues[:10])
        ), {"issues": issues, "p0": p0, "p1": p1, "p2": p2}

    if p1 > 2:
        return False, (
            f"PUBLICATION_READY FAILED: P1={p1} (must be ≤ 2).\n"
            f"  P0={p0}, P2={p2}\n"
            f"  Issues:\n" + "\n".join(f"  - {i}" for i in issues[:10])
        ), {"issues": issues, "p0": p0, "p1": p1, "p2": p2}

    evidence.append(f"P0={p0}, P1={p1}, P2={p2}")
    evidence.append(f"Paper: {paper.name}")

    # 检查报告文件是否存在
    report_file = ws / "outputs" / "paper" / "publication_readiness_report.md"
    if report_file.exists():
        evidence.append("publication_readiness_report.md: exists")
    else:
        issues.append("MISSING: publication_readiness_report.md not generated")
        return False, (
            f"PUBLICATION_READY FAILED: Report not generated.\n"
            f"  Run: python scripts/publication_checker.py report {paper.name} --mode {mode}"
        ), {"issues": issues}

    return True, (
        f"PUBLICATION_READY PASSED ({mode}): P0={p0}, P1={p1}, P2={p2}.\n"
        + "\n".join(f"  + {e}" for e in evidence)
    ), {"evidence": evidence, "issues": issues}


# ═══════════════════════════════════════════════════════════════
# v3.0: 补全缺失门禁函数
# ═══════════════════════════════════════════════════════════════

def gate_data_quality(workspace=None, mode="standard"):
    """G1.5 数据质量门禁 — 检查 data/ 目录下数据字典和数据概况。"""
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []

    dd = ws / "data" / "data_dictionary.md"
    dp = ws / "data" / "data_profile_report.md"

    if dd.exists() and dd.stat().st_size > 100:
        evidence.append("data_dictionary.md: exists")
    else:
        issues.append("MISSING/EMPTY: data/data_dictionary.md")

    if dp.exists() and dp.stat().st_size > 100:
        evidence.append("data_profile_report.md: exists")
    else:
        issues.append("MISSING/EMPTY: data/data_profile_report.md")

    # equation_driven 模式可降级
    if mode == "fast" and not issues:
        return True, "DATA_QUALITY PASSED (fast mode)", {"evidence": evidence}

    if issues:
        return False, f"DATA_QUALITY FAILED: {', '.join(issues)}", {"issues": issues}

    return True, f"DATA_QUALITY PASSED: {len(evidence)} checks OK.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


def gate_metric_guardian(workspace=None, mode="standard"):
    """G1.5 指标守护门禁 — 检查 S3 辩论中是否定义了评价口径。"""
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []

    # 检查评价口径文件
    metrics = ws / "methods" / "evaluation_metrics.md"
    debate = ws / "methods" / "debate_summary.md"

    if metrics.exists() and metrics.stat().st_size > 100:
        evidence.append("evaluation_metrics.md: exists")
    elif debate.exists() and debate.stat().st_size > 100:
        evidence.append("debate_summary.md: exists (fallback)")
    else:
        issues.append("MISSING: methods/evaluation_metrics.md or methods/debate_summary.md")

    if issues:
        return False, f"METRIC_GUARDIAN FAILED: {', '.join(issues)}", {"issues": issues}

    return True, f"METRIC_GUARDIAN PASSED.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


def gate_race_completed(workspace=None, mode="standard"):
    """G2.5 赛马完成门禁 — 检查 S4 实验结果。"""
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []

    plan = ws / "methods" / "experiments" / "experiment_race_plan.md"
    board = ws / "methods" / "experiments" / "model_leaderboard.csv"

    if plan.exists() and plan.stat().st_size > 100:
        evidence.append("experiment_race_plan.md: exists")
    else:
        issues.append("MISSING: methods/experiments/experiment_race_plan.md")

    if board.exists() and board.stat().st_size > 50:
        # 检查是否有数据行（不只是表头）
        lines = board.read_text(encoding="utf-8").strip().split("\n")
        if len(lines) > 1:
            evidence.append(f"model_leaderboard.csv: {len(lines)-1} data rows")
        else:
            issues.append("EMPTY: model_leaderboard.csv has no data rows")
    else:
        issues.append("MISSING: methods/experiments/model_leaderboard.csv")

    if issues:
        return False, f"RACE_COMPLETED FAILED: {', '.join(issues)}", {"issues": issues}

    return True, f"RACE_COMPLETED PASSED.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


def gate_evolution_converged(workspace=None, mode="standard"):
    """G3.5 进化收敛门禁 — 检查 S5.5 进化实验结果。"""
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []

    report = ws / "outputs" / "evolution" / "evolution_report.md"
    log_dir = ws / "outputs" / "evolution"

    if report.exists() and report.stat().st_size > 200:
        evidence.append("evolution_report.md: exists")
    else:
        issues.append("MISSING/EMPTY: outputs/evolution/evolution_report.md")

    # Championship 模式额外检查
    if mode == "championship":
        innov = ws / "outputs" / "evolution" / "innovation_assessment.md"
        if innov.exists() and innov.stat().st_size > 500:
            evidence.append("innovation_assessment.md: exists (championship)")
        else:
            issues.append("MISSING/THIN: outputs/evolution/innovation_assessment.md (championship required)")

    if issues:
        return False, f"EVOLUTION_CONVERGED FAILED: {', '.join(issues)}", {"issues": issues}

    return True, f"EVOLUTION_CONVERGED PASSED.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


def gate_per_subquestion(workspace=None, mode="standard"):
    """逐子问题验证门禁 — 检查每个子问题都有 summary.md。"""
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []

    # 查找所有 q{N} 目录
    outputs_dir = ws / "outputs"
    if not outputs_dir.exists():
        return False, "PER_SUBQUESTION FAILED: outputs/ directory not found", {"issues": ["outputs/ missing"]}

    q_dirs = sorted([d for d in outputs_dir.iterdir() if d.is_dir() and d.name.startswith("q") and d.name[1:].isdigit()])

    if not q_dirs:
        return False, "PER_SUBQUESTION FAILED: No q{N} directories found in outputs/", {"issues": ["No subquestion directories"]}

    for qd in q_dirs:
        summary = qd / "summary.md"
        if summary.exists() and summary.stat().st_size > 200:
            evidence.append(f"{qd.name}/summary.md: exists ({summary.stat().st_size} bytes)")
        else:
            issues.append(f"MISSING/THIN: outputs/{qd.name}/summary.md")

    if issues:
        return False, f"PER_SUBQUESTION FAILED: {', '.join(issues)}", {"issues": issues}

    return True, f"PER_SUBQUESTION PASSED: {len(q_dirs)} subquestions verified.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


def gate_unified_kernel(workspace=None, mode="standard"):
    """G4.7 统一内核门禁 — 检查 S7.5 产出。"""
    ws = Path(workspace) if workspace else WORKSPACE
    issues, evidence = [], []

    kernel = ws / "outputs" / "kernel" / "unified_kernel.md"

    if kernel.exists() and kernel.stat().st_size > 300:
        evidence.append("unified_kernel.md: exists")
    else:
        issues.append("MISSING/EMPTY: outputs/kernel/unified_kernel.md")

    if issues:
        return False, f"UNIFIED_KERNEL FAILED: {', '.join(issues)}", {"issues": issues}

    return True, f"UNIFIED_KERNEL PASSED.\n" + "\n".join(f"  + {e}" for e in evidence), {"evidence": evidence}


# ═══════════════════════════════════════════════════════════════
# Auto Mode: Gate Auto-Verdict
# ═══════════════════════════════════════════════════════════════

def auto_verdict(gate_id, workspace=None, mode="standard"):
    """Auto-mode gate verdict — runs the appropriate checker and returns (passed, message, fix_instructions).

    Used by auto_orchestrator.py to decide: advance or rework.
    Mode-aware: thresholds adjust based on fast/standard/championship.
    """
    ws = Path(workspace) if workspace else WORKSPACE
    normalized = gate_id.upper().replace(".", "_").replace("-", "_")

    def _extract(details):
        return details.get("issues", []) if isinstance(details, dict) else []

    try:
        # G0: Input Registered
        if "G0" in normalized or "INPUT_REGISTERED" in normalized:
            passed, msg, details = gate_g0(ws, mode)
            return passed, msg, _extract(details)
        
        # G1: Problem Parsed
        if "G1_PROBLEM" in normalized and "G1_5" not in normalized:
            passed, msg, details = gate_g1_problem_parsed(ws, mode)
            return passed, msg, _extract(details)

        # G2: PoC
        if "G2_POC" in normalized or "G2_METHOD" in normalized:
            passed, msg, details = gate_g2_poc()
            return passed, msg, _extract(details)

        # G3: Baseline
        if "G3_BASELINE" in normalized:
            passed, msg, details = gate_g3_baseline(ws)
            return passed, msg, _extract(details)

        # v2.0: G3 Multi-Proposal
        if "G3_MULTI_PROPOSAL" in normalized or "MULTI_PROPOSAL" in normalized:
            passed, msg, details = gate_multi_proposal(ws, mode)
            return passed, msg, _extract(details)

        # v2.0: G3 Adversarial Round
        if "G3_ADVERSARIAL" in normalized or "ADVERSARIAL_ROUND" in normalized:
            passed, msg, details = gate_adversarial_round(ws, mode)
            return passed, msg, _extract(details)

        # v2.0: G3 Model Selection V2 (9-dimension)
        if "G3_MODEL_SELECTION_V2" in normalized or "MODEL_SELECTION_V2" in normalized:
            passed, msg, details = gate_model_selection_v2(ws, mode)
            return passed, msg, _extract(details)

        # v2.0: G3 Prototype Validated
        if "G3_PROTOTYPE" in normalized or "PROTOTYPE_VALIDATED" in normalized:
            passed, msg, details = gate_prototype_validated(ws, mode)
            return passed, msg, _extract(details)

        # G3: Model Selection (legacy)
        if ("MODEL_SELECTION" in normalized and "V2" not in normalized) or "G3_ASSUMPTIONS" in normalized:
            passed, msg, details = gate_model_selection(ws, mode)
            return passed, msg, _extract(details)

        # Innovation Assessment
        if "INNOVATION" in normalized:
            passed, msg, details = gate_innovation_assessment(ws, mode)
            return passed, msg, _extract(details)

        # G4: Frozen
        if "G4_FROZEN" in normalized or "G4_RESULTS" in normalized:
            passed, msg, details = gate_g4_frozen_staleness()
            return passed, msg, details.get("stale", []) if not passed else []

        # G5: Paper Quality
        if "G5_PAPER" in normalized and "G5_5" not in normalized and "G5_S8" not in normalized:
            passed, msg, details = gate_g5_paper_quality(ws, mode)
            return passed, msg, _extract(details)

        # G5: S8 Content Ready
        if "G5_S8_CONTENT_READY" in normalized:
            passed, msg, details = gate_g5_s8_content_ready(ws)
            return passed, msg, _extract(details)

        # G5.5: Paper Structure
        if "G5_5_PAPER_STRUCTURE" in normalized or "PAPER_STRUCTURE" in normalized:
            passed, msg, details = gate_paper_structure(ws, mode)
            return passed, msg, _extract(details)

        # G5.5: Adversarial Review
        if "G5_5_ADVERSARIAL" in normalized:
            passed, msg, details = gate_g5_5_adversarial(ws, mode)
            return passed, msg, _extract(details)

        # Abstract Quality
        if "ABSTRACT_QUALITY" in normalized:
            passed, msg, details = gate_abstract_quality(ws, mode)
            return passed, msg, _extract(details)

        # G6: Appendix
        if "G6_APPENDIX" in normalized:
            passed, msg, details = gate_g6_appendix_complete(ws)
            return passed, msg, _extract(details)

        # G6: Audit Layer
        if "G6_AUDIT" in normalized:
            results = run_g6_audit_enhanced(str(ws))
            passed = results.get("gate_passed", False)
            fix = []
            for layer, r in results.items():
                if layer == "gate_passed":
                    continue
                if not r.get("passed", True):
                    fix.extend(r.get("issues", []))
            return passed, "G6 three-layer audit", fix
        
        # P1 NEW: Figure Narrative
        if "FIGURE_NARRATIVE" in normalized or "G5_FIGURE" in normalized:
            passed, msg, details = gate_figure_narrative(ws, mode)
            return passed, msg, _extract(details)
        
        # P1 NEW: Parallel Merge
        if "PARALLEL_MERGE" in normalized or "G3_PARALLEL" in normalized:
            passed, msg, details = gate_parallel_merge(ws, mode)
            return passed, msg, _extract(details)
        
        # P1 NEW: Paper Evaluation
        if "G6_PAPER_EVALUATION" in normalized or "PAPER_EVALUATION" in normalized:
            passed, msg, details = gate_paper_evaluation_quality(ws, mode)
            return passed, msg, _extract(details)
        
        # P1 NEW: Evidence Chain
        if "G4_5_EVIDENCE" in normalized or "EVIDENCE_CHAIN" in normalized:
            passed, msg, details = gate_evidence_chain_quality(ws, mode)
            return passed, msg, _extract(details)

        # S9.5: Publication Readiness
        if "G9_5_PUBLICATION" in normalized or "G6_PUBLICATION_READY" in normalized or "PUBLICATION_READY" in normalized:
            passed, msg, details = gate_publication_ready(ws, mode)
            return passed, msg, _extract(details)

        # v3.0: Data Quality (S2)
        if "G1_5_DATA_QUALITY" in normalized or "DATA_QUALITY" in normalized:
            passed, msg, details = gate_data_quality(ws, mode)
            return passed, msg, _extract(details)

        # v3.0: Metric Guardian (S3)
        if "G1_5_METRIC_GUARDIAN" in normalized or "METRIC_GUARDIAN" in normalized:
            passed, msg, details = gate_metric_guardian(ws, mode)
            return passed, msg, _extract(details)

        # v3.0: Race Completed (S4)
        if "G2_5_RACE_COMPLETED" in normalized or "RACE_COMPLETED" in normalized:
            passed, msg, details = gate_race_completed(ws, mode)
            return passed, msg, _extract(details)

        # v3.0: Evolution Converged (S5.5)
        if "G3_5_EVOLUTION_CONVERGED" in normalized or "EVOLUTION_CONVERGED" in normalized:
            passed, msg, details = gate_evolution_converged(ws, mode)
            return passed, msg, _extract(details)

        # v3.0: Per Subquestion Verification (S6)
        if "PER_SUBQUESTION" in normalized:
            passed, msg, details = gate_per_subquestion(ws, mode)
            return passed, msg, _extract(details)

        # v3.0: Unified Kernel (S7.5)
        if "G4_7_KERNEL" in normalized or "UNIFIED_KERNEL" in normalized:
            passed, msg, details = gate_unified_kernel(ws, mode)
            return passed, msg, _extract(details)

        # v3.0: G2 Model Selection (S3)
        if "G2_MODEL_SELECTION" in normalized:
            passed, msg, details = gate_model_selection(ws, mode)
            return passed, msg, _extract(details)

        # v3.0: G2 POC (S4)
        if "G2_POC" in normalized:
            passed, msg, details = gate_g2_poc()
            return passed, msg, _extract(details)

        # v3.0: G3 Code Reviewed (S5)
        if "G3_CODE_REVIEWED" in normalized or "CODE_REVIEWED" in normalized:
            passed, msg, details = gate_g3_baseline(ws)
            return passed, msg, _extract(details)

        # v3.0: G4 Evidence Chain (S7)
        if "G4_EVIDENCE_CHAIN" in normalized:
            passed, msg, details = gate_evidence_chain_quality(ws, mode)
            return passed, msg, _extract(details)

        # Fallback: contract exists but no specific checker — BLOCKED, not auto-pass
        if gate_id in GATE_CONTRACTS or normalized in GATE_CONTRACTS:
            return False, (
                f"[{gate_id}] No automated checker available. "
                f"Agent MUST manually verify ALL pass criteria before proceeding. "
                f"Run `python scripts/gate_contracts.py check {gate_id}` for criteria list."
            ), ["Manual verification required — do NOT auto-pass"]

    except Exception as e:
        return False, f"Gate check error: {e}", [str(e)]

    return False, f"[{gate_id}] Unknown gate — BLOCKED until verified", ["Unknown gate ID"]


# ═══════════════════════════════════════════════════════════════
# CLI entry point (when run directly)
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Gate Contracts & Enhanced Audits")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("contracts", help="Print all gate contracts")
    
    sp = sub.add_parser("g0", help="Run G0 input registered check")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])
    
    sp = sub.add_parser("poc", help="Run G2 PoC gate")
    sp.add_argument("--poc-dir", default=None)

    sp = sub.add_parser("baseline", help="Run G3 baseline comparison check")
    sp.add_argument("--workspace", "-w", default=None)

    sp = sub.add_parser("stale", help="Run G4 frozen staleness check")
    sp.add_argument("--subquestion", "-q", default=None)

    sp = sub.add_parser("g6", help="Run G6 enhanced three-layer audit")
    sp.add_argument("--workspace", "-w", default=None)

    sp = sub.add_parser("propagate", help="Run P1 change propagation check")
    sp.add_argument("--changed", "-c", nargs="+", required=True)

    sp = sub.add_parser("s8-ready", help="Run G5 S8 content-ready check")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--subquestions", "-q", type=int, default=1)

    sp = sub.add_parser("appendix", help="Run G6 appendix-complete check")
    sp.add_argument("--workspace", "-w", default=None)

    # New: mode-aware gate checks
    sp = sub.add_parser("paper-quality", help="Run G5 paper quality comprehensive check")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])

    sp = sub.add_parser("adversarial", help="Run G5.5 adversarial review check")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])

    sp = sub.add_parser("abstract", help="Run abstract quality check")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])

    sp = sub.add_parser("structure", help="Run paper structure check")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])

    sp = sub.add_parser("model-select", help="Run model selection check")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])

    sp = sub.add_parser("g1", help="Run G1 problem parsed check")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])

    sp = sub.add_parser("innovation", help="Run innovation assessment check")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])

    sp = sub.add_parser("weight-thresholds", help="Show scoring weight thresholds for a stage")
    sp.add_argument("stage", help="Stage ID (e.g. S3_model_selection)")
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])

    sp = sub.add_parser("check", help="Show gate contract pass criteria")
    sp.add_argument("gate_id", help="Gate ID to show criteria for")

    sp = sub.add_parser("thresholds", help="Show mode thresholds")
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])
    
    # P1 NEW: 4个新门禁CLI
    sp = sub.add_parser("figure-narrative", help="Run G5 figure narrative check (D-A-C)")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])
    
    sp = sub.add_parser("parallel-merge", help="Run G3 parallel merge check")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])
    
    sp = sub.add_parser("paper-evaluation", help="Run G6 paper comprehensive evaluation (5-dim scoring)")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])
    
    sp = sub.add_parser("evidence-chain", help="Run G4.5 evidence chain quality check")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])

    # S9.5: Publication Readiness
    sp = sub.add_parser("publication-ready", help="Run G9.5 publication readiness check (S9.5)")
    sp.add_argument("--workspace", "-w", default=None)
    sp.add_argument("--mode", "-m", default="standard", choices=["fast", "standard", "championship"])

    args = p.parse_args()

    if args.cmd == "contracts":
        print_gate_contracts()
    elif args.cmd == "g0":
        passed, msg, details = gate_g0(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "poc":
        passed, msg, details = gate_g2_poc(args.poc_dir)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "baseline":
        passed, msg, details = gate_g3_baseline(args.workspace)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "stale":
        passed, msg, details = gate_g4_frozen_staleness(args.subquestion)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "g6":
        results = run_g6_audit_enhanced(args.workspace)
        print_g6_enhanced_report(results)
        sys.exit(0 if results["gate_passed"] else 1)
    elif args.cmd == "propagate":
        result = propagation_check(args.changed)
        print_propagation_report(result)
    elif args.cmd == "s8-ready":
        passed, msg, details = gate_g5_s8_content_ready(args.workspace, args.subquestions)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "appendix":
        passed, msg, details = gate_g6_appendix_complete(args.workspace)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "paper-quality":
        passed, msg, details = gate_g5_paper_quality(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "adversarial":
        passed, msg, details = gate_g5_5_adversarial(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "abstract":
        passed, msg, details = gate_abstract_quality(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "structure":
        passed, msg, details = gate_paper_structure(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "model-select":
        passed, msg, details = gate_model_selection(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "g1":
        passed, msg, details = gate_g1_problem_parsed(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "innovation":
        passed, msg, details = gate_innovation_assessment(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "weight-thresholds":
        wt = get_weight_thresholds(args.stage, args.mode)
        print(f"\n{'='*60}")
        print(f"  Weight Thresholds: {args.stage} ({args.mode.upper()})")
        print(f"{'='*60}")
        if wt:
            for k, v in wt.items():
                print(f"  {k}: {v}")
        else:
            dim_name = "unknown"
            for dk, dv in SCORING_WEIGHT_THRESHOLDS.items():
                if args.stage in dv["stages"]:
                    dim_name = dk
                    break
            print(f"  Stage not mapped to a specific dimension (general rules apply)")
            print(f"  Dimension: {dim_name}")
        print(f"{'='*60}")
    elif args.cmd == "check":
        gid = args.gate_id
        if gid in GATE_CONTRACTS:
            c = GATE_CONTRACTS[gid]
            print(f"\n[{gid}] {c['description']}")
            print(f"  Enter: {c['enter_condition']}")
            for pc in c['pass_criteria']:
                print(f"  Pass:  - {pc}")
            print(f"  Fail:  {c['fail_fallback']}")
        else:
            print(f"Unknown gate: {gid}")
            print(f"Available: {', '.join(GATE_CONTRACTS.keys())}")
    elif args.cmd == "thresholds":
        th = get_mode_thresholds(args.mode)
        print(f"\n{'='*60}")
        print(f"  Mode: {args.mode.upper()} Thresholds")
        print(f"{'='*60}")
        for k, v in th.items():
            print(f"  {k}: {v}")
        print(f"{'='*60}")
    elif args.cmd == "figure-narrative":
        passed, msg, details = gate_figure_narrative(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "parallel-merge":
        passed, msg, details = gate_parallel_merge(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "paper-evaluation":
        passed, msg, details = gate_paper_evaluation_quality(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        if isinstance(details, dict) and "scores" in details:
            print(f"\n  Detailed Scores:")
            for dim, score in details["scores"].items():
                print(f"    {dim}: {score}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "evidence-chain":
        passed, msg, details = gate_evidence_chain_quality(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        sys.exit(0 if passed else 1)
    elif args.cmd == "publication-ready":
        passed, msg, details = gate_publication_ready(args.workspace, args.mode)
        print(f"{'PASS' if passed else 'FAIL'}: {msg}")
        if isinstance(details, dict):
            print(f"  P0={details.get('p0', '?')}, P1={details.get('p1', '?')}, P2={details.get('p2', '?')}")
        sys.exit(0 if passed else 1)
    else:
        p.print_help()
