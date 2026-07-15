from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from manifest import find_step


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_INIT = SCRIPT_DIR / "workspace_init.py"
STAGE_EXECUTOR = SCRIPT_DIR / "stage_executor.py"
PIPELINE_MANAGER = SCRIPT_DIR / "pipeline_manager.py"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, *args],
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(args)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    return proc


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Expected file missing: {path}")


def make_s1(workspace: Path) -> None:
    write_text(
        workspace / "问题分析.md",
        (
            textwrap.dedent(
            """
            # 问题情境解构报告

            本赛题共 3 个子问题。

            ## 一、赛题概述
            本题围绕复杂系统优化展开，需要在多重约束下提出可执行方案，并将题意拆解成三个彼此递进的核心子问题。题目中既有成本和效率目标，也包含容量、时间窗、公平性和推广性约束，因此不能只做静态单目标分析。

            ## 二、子问题拆解
            子问题一聚焦基线模型建立与关键指标识别；子问题二在此基础上引入资源、容量、时间窗或鲁棒机制；子问题三负责综合评价、比较与推广建议。各子问题之间存在明确的结果传递关系。

            ## 三、数据探索
            本题无附件数据。数据探索结论为：需要在建模阶段自行设定基础参数、约束阈值、场景扰动范围和评价指标，并在代码阶段把关键假设参数化，便于灵敏度分析和回滚。

            ## 四、变量定义与符号表
            | 符号 | 含义 | 单位 | 类型 |
            | --- | --- | --- | --- |
            | x_i | 第 i 个决策变量 | 依题设 | 决策变量 |
            | c_i | 第 i 个成本参数 | 元 | 参数 |
            | t_i | 第 i 个时间参数 | 小时 | 参数 |
            | y_i | 第 i 个状态变量 | 依题设 | 状态变量 |
            | z_i | 第 i 个评价指标 | 分值 | 输出变量 |

            ## 五、假设敏感性预检
            ### 模糊表述及解释
            1. "资源可重新分配"
               - 解释A: 只允许在阶段之间重新分配
               - 解释B: 允许在子任务之间动态重分配
               - 初步倾向: B，理由: 更符合后续递进问题的扩展空间
            2. "完成时间最短"
               - 解释A: 最后一个任务完成时刻最小
               - 解释B: 所有任务时间总和最小
               - 初步倾向: A，理由: 更符合并行调度场景

            ### 快速验算对比
            - 解释A: 问题一结果 = 118
            - 解释B: 问题一结果 = 132
            - 选择: 解释A，理由: 与问题二增加约束后的递进关系更清晰

            ### 问题递进性预判
            - 问题一（基础场景）→ 结果: 基准值
            - 问题二（增加约束）→ 结果应该比问题一更紧
            - 问题三（综合评价）→ 结果应该体现方案差异

            ## 六、建模思路
            先建立基础模型，再根据题目中的约束、不确定性和多阶段结构进行模型升级，避免把复杂机制无声丢失。若发现该题属于经典问题变体，需要在后续建模阶段显式说明升级方向。

            ## 七、图表预规划
            ### 数据图表清单
            - 结果总览图 — 分组柱状图 (basic #1) — 展示三个子问题的核心结果对比 — 章节: 结果分析

            ### DrawIO 架构图清单
            **语言: 中文**
            - DrawIO-1: 技术路线图 → 技术路线图.drawio → 问题重述章节末尾 [必须]
            - DrawIO-2: 问题一求解流程图 → 问题流程图_1.drawio → 问题一章节开头 [按需]
            - DrawIO-3: 问题二求解流程图 → 问题流程图_2.drawio → 问题二章节开头 [按需]
            - DrawIO-4: 问题三求解流程图 → 问题流程图_3.drawio → 问题三章节开头 [按需]

            ### 图表多样性检查
            - 分组柱状图: 1 次
            - DrawIO 流程图: 4 次

            ## 八、题目逐句拆解表
            | 句号 | 原文句子 | 句子类型 | 提取的要素 |
            | --- | --- | --- | --- |
            | DISCOVERY | 在预算约束下选择方案 | 约束 | 预算、选择、上限 |
            | FORMULATION | 评价整体效果并保持公平 | 目标 | 效果、公平、比较 |

            ## 九、句子级五问审查
            ### DISCOVERY: 在预算约束下选择方案
            1. 这句话提到了什么实体？预算、方案、约束
            2. 这些实体是否都出现在我的变量定义表中？是
            3. 这句话描述的机制/行为是否在我的模型中有对应表达？是，将转为预算约束
            4. 如果这句话有数值，是否代入了模型？预算阈值将在建模阶段参数化
            5. 这句话如果被完全忽略，会导致什么后果？严重，约束缺失

            ## 十、反向对照表
            | 我的模型中的组件 | 对应题目哪一句/哪几句 | 如果题目没说我为什么要加？ |
            | --- | --- | --- |
            | 预算约束 | DISCOVERY | 题目明确要求 |
            | 公平性指标 | FORMULATION | 题目明确要求 |

            ## 十一、经典问题升级判定表
            | 初步映射 | 题目关键句子触发的升级 | 最终模型 | 严重性 | 必须性 | 缺失影响 |
            | --- | --- | --- | --- | --- | --- |
            | 线性规划 | "资源可重新分配" → 多阶段 | 多阶段优化 | 🟡 重要 | 必须 | 无法反映阶段转移 |
            | 单目标评价 | "保持公平" → 多目标 | 多目标评价 | 🟡 重要 | 必须 | 无法解释方案差异 |

            ## 十二、工作计划
            工作流将先完成题意澄清，再推进建模、计算实验实现、证据图谱构建、论文撰写与编译合规检查。题目中的每个“不超过、至少、必须满足”条件都将在建模中转为显式约束表达式。
            """
            ).strip()
            + "\n"
            + ("补充分析：每个子问题都要写清楚输入、输出、约束来源、依赖关系、图表规划和升级判断。\n" * 8)
        )
        + "\n",
    )


def make_s2(workspace: Path) -> None:
    write_text(
        workspace / "建模报告.md",
        (
            textwrap.dedent(
            """
            # 建模报告

            ## 推荐方法与升级建议审视
            问题情境解构推荐使用多阶段优化与多目标评价。本报告接受该升级建议，并在问题二中加入阶段转移，在问题三中加入综合绩效与公平性目标。若某个候选方法未采用，会在对应问题的小节中给出选择理由和优势对比。

            ## 模型假设
            假设 1: 资源调度以离散阶段推进。
              - 理由: 题目强调阶段性资源约束与方案更新。
              - 参数化: STAGE_COUNT = 3
              - 替代假设: STAGE_COUNT = 2，用于稳健性对比。

            假设 2: 公平性通过标准化偏差衡量。
              - 理由: 便于和成本、效率共同进入综合评价。
              - 参数化: FAIRNESS_WEIGHT = 0.25
              - 替代假设: FAIRNESS_WEIGHT = 0.15。

            ## 问题一
            方法调研：线性规划与分层优化都适用，本题优先采用分层优化，因为需要为后续阶段扩展保留结构。
            模型选择与理由：选择基础分层优化模型，优势对比是可直接衔接问题二的阶段转移。
            目标函数：最小化总成本并最大化覆盖效率。
            约束：满足容量约束、预算约束与时间窗约束。
            建模表达：使用分层优化模型并给出核心公式。

            ## 问题二
            方法调研：多阶段规划优于静态线性规划。
            模型选择与理由：选择多阶段优化模型，因为问题情境解构中“资源可重新分配”触发升级。
            目标函数：在不确定场景下最小化风险暴露。
            约束：subject to 资源、稳定性与阶段转移约束。
            建模表达：引入鲁棒场景并比较两种候选方法。

            ## 问题三
            方法调研：综合评价模型适合方案排序。
            模型选择与理由：选择多指标综合评价，能够保留公平性与效率的权衡。
            目标函数：max 综合绩效得分。
            约束：约束包括公平性、总量和结构一致性。
            建模表达：建立评价模型并比较不同策略。

            ## 验证与检验
            对每个子问题安排验证、灵敏度分析、鲁棒性检验与结果一致性审查。

            ## 验证检查点
            - 检查点 1: 每个子问题都有独立求解脚本与结果 JSON
            - 检查点 2: 关键约束在代码结果中可回代验证
            - 检查点 3: 灵敏度分析至少扰动一个参数化假设

            ## 结构性验证输入
            - 问题一: 预算约束必须始终满足，效率随资源增加不应下降
            - 问题二: 多阶段转移必须至少出现 2 个阶段
            - 问题三: 综合评价权重和应为 1，排序应可复现

            ## 图表预规划
            - 结果总览图 — 分组柱状图 (basic #1) — 三个子问题结果对比 — 结果分析章节
            - DrawIO-1: 技术路线图.drawio
            - DrawIO-2: 问题流程图_1.drawio
            - DrawIO-3: 问题流程图_2.drawio
            - DrawIO-4: 问题流程图_3.drawio

            本题涉及题型：[优化, 评价, 鲁棒性分析]，已对照防错手册审查。
            """
            ).strip()
            + "\n"
            + ("扩展说明：写出目标函数、约束、主算法、验证算法、灵敏度分析和结果解释，避免子问题缺失。\n" * 12)
        )
        + "\n",
    )


def make_s3(workspace: Path) -> None:
    write_text(workspace / "程序" / "通用工具.py", "def validate_constraints():\n    return True\n")
    for index in range(1, 4):
        write_text(
            workspace / "程序" / f"问题_{index}.py",
            textwrap.dedent(
                f"""
                from 通用工具 import validate_constraints

                def solve():
                    data = {{"problem": {index}, "score": {index * 10}, "feasible": True}}
                    assert validate_constraints()
                    return data
                """
            ).strip()
            + "\n",
        )
        write_text(workspace / "图表" / f"问题_{index}_结果.json", json.dumps({"problem": index, "value": index * 10}, ensure_ascii=False, indent=2))
    write_text(
        workspace / "程序" / "主程序.py",
        textwrap.dedent(
            """
            import json
            from pathlib import Path

            from 问题_1 import solve as solve1
            from 问题_2 import solve as solve2
            from 问题_3 import solve as solve3

            def main():
                results = [solve1(), solve2(), solve3()]
                out = Path("图表") / "全部结果.json"
                out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
                # baseline smoke keeps the structure close to the original workflow:
                # one main entrypoint orchestrates all sub-problems and writes
                # a single aggregated result file for the figure and paper stages.
                summary = {
                    "problem_count": len(results),
                    "feasible": all(item.get("feasible", False) for item in results),
                    "scores": [item.get("score", 0) for item in results],
                }
                (Path("图表") / "结果摘要.json").write_text(
                    json.dumps(summary, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                return results

            if __name__ == "__main__":
                main()
            """
        ).strip()
        + "\n",
    )
    write_text(
        workspace / "计算结果.md",
        (
            "# 结果汇总\n\n"
            "## 问题1\n采用分层优化模型，最优目标值 = 10，预算约束满足，关键结论是基线方案可行。\n\n"
            "## 问题2\n采用多阶段优化模型，风险暴露值 = 20，阶段转移后总成本下降 8%，说明升级机制有效。\n\n"
            "## 问题3\n采用综合评价模型，综合绩效得分 = 30，推荐方案在公平性和效率之间取得平衡。\n\n"
        )
        * 12,
    )
    write_text(workspace / "图表" / "全部结果.json", json.dumps([{"problem": i, "value": i * 10} for i in range(1, 4)], ensure_ascii=False, indent=2))
    write_text(workspace / "依赖清单.txt", "numpy\npandas\nmatplotlib\n")
    run(str(workspace / "工具" / "build_code_appendix.py"), "--workspace", str(workspace), "--manifest-only")


def make_s4(workspace: Path) -> None:
    write_text(
        workspace / "论文规划.md",
        "## 图表预规划\n- 结果总览图 — 分组柱状图 (basic #1) — 三个子问题结果对比 — 结果分析章节\n"
    )
    (workspace / "图表" / "结果总览图.pdf").write_bytes(b"%PDF-1.4\n% fake data figure pdf\n")
    latex = (
        "\n".join(
            [
                f"\\begin{{figure}}[H]\n\\centering\n\\includegraphics[width=0.72\\linewidth,height=0.70\\textheight,keepaspectratio]{{../图表/结果总览图.pdf}}\n\\caption{{图{i} 数据结果图}}\n\\label{{fig:result{i}}}\n\\end{{figure}}"
                for i in range(1, 5)
            ]
        )
        + "\n"
    )
    write_text(workspace / "图表" / "图表引用.tex", latex)
    write_text(
        workspace / "图表" / "figure_manifest.json",
        json.dumps(
            {
                "version": 1,
                "figures": [
                    {
                        "path": "图表/结果总览图.pdf",
                        "claim": "三个子问题的核心结果均满足可行性约束",
                        "source": "图表/全部结果.json",
                        "reader_task": "比较三个子问题结果",
                        "publish": True,
                        "placement": "body",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
    )


def make_s5(workspace: Path) -> None:
    for name in ["技术路线图", "问题流程图_1", "问题流程图_2", "问题流程图_3"]:
        write_text(workspace / "图表" / f"{name}.drawio", f"<mxfile><diagram>{name}</diagram></mxfile>\n")
        (workspace / "图表" / f"{name}.pdf").write_bytes(b"%PDF-1.4\n% fake drawio pdf\n")
    with (workspace / "图表" / "图表引用.tex").open("a", encoding="utf-8") as handle:
        handle.write(
            "\\begin{figure}[H]\n\\centering\n\\includegraphics[width=0.72\\linewidth,height=0.70\\textheight,keepaspectratio]{../图表/技术路线图.pdf}\n\\caption{技术路线图}\n\\label{fig:roadmap}\n\\end{figure}\n"
        )
        for index in range(1, 4):
            handle.write(
                f"\\begin{{figure}}[H]\n\\centering\n\\includegraphics[width=0.72\\linewidth,height=0.70\\textheight,keepaspectratio]{{../图表/问题流程图_{index}.pdf}}\n\\caption{{问题{index}求解流程图}}\n\\label{{fig:flow{index}}}\n\\end{{figure}}\n"
            )


def make_s6(workspace: Path) -> None:
    sections = workspace / "论文" / "章节"
    write_text(
        sections / "1_问题重述.tex",
        ("问题重述与技术路线图说明。技术路线图.pdf 在本章展示整体求解路径，摘要之后先给出技术路线，再过渡到子问题；相关研究背景与流程设计可参考经典竞赛论文写法\\textsuperscript{\\cite{ref1}}。\n" * 80)
        + "\\begin{figure}[H]\n\\centering\n\\includegraphics[width=0.72\\linewidth,height=0.70\\textheight,keepaspectratio]{../图表/技术路线图.pdf}\n\\caption{技术路线图}\n\\label{fig:roadmap}\n\\end{figure}\n",
    )
    write_text(
        sections / "2_模型构建.tex",
        (
            "问题一、问题二、问题三的模型推导、约束表达、验证方法与灵敏度分析。问题流程图_1.pdf、问题流程图_2.pdf、问题流程图_3.pdf 分别用于说明三问的求解流程，算法设计与参数化假设均依据建模报告与相关文献\\textsuperscript{\\cite{ref1}}展开。\n" * 80
        )
        + "\\begin{figure}[H]\n\\centering\n\\includegraphics[width=0.72\\linewidth,height=0.70\\textheight,keepaspectratio]{../图表/问题流程图_1.pdf}\n\\caption{问题1求解流程图}\n\\label{fig:flow1}\n\\end{figure}\n"
        + "\\begin{figure}[H]\n\\centering\n\\includegraphics[width=0.72\\linewidth,height=0.70\\textheight,keepaspectratio]{../图表/问题流程图_2.pdf}\n\\caption{问题2求解流程图}\n\\label{fig:flow2}\n\\end{figure}\n"
        + "\\begin{figure}[H]\n\\centering\n\\includegraphics[width=0.72\\linewidth,height=0.70\\textheight,keepaspectratio]{../图表/问题流程图_3.pdf}\n\\caption{问题3求解流程图}\n\\label{fig:flow3}\n\\end{figure}\n",
    )
    write_text(
        sections / "3_结果分析.tex",
        ("结果分析、对比讨论、模型评价与推广建议。结果总览图.pdf 展示三个子问题的核心结果，结论部分据此给出方案总结；所有数值结果都与 计算结果.md 保持一致，并结合参考方法\\textsuperscript{\\cite{ref1}}做对照解释。\n" * 80)
        + "\\begin{figure}[H]\n\\centering\n\\includegraphics[width=0.72\\linewidth,height=0.70\\textheight,keepaspectratio]{../图表/结果总览图.pdf}\n\\caption{图1 数据结果图}\n\\label{fig:result1}\n\\end{figure}\n"
        + "\\begin{figure}[H]\n\\centering\n\\includegraphics[width=0.72\\linewidth,height=0.70\\textheight,keepaspectratio]{../图表/结果总览图.pdf}\n\\caption{图2 数据结果图}\n\\label{fig:result2}\n\\end{figure}\n"
        + "\\begin{figure}[H]\n\\centering\n\\includegraphics[width=0.72\\linewidth,height=0.70\\textheight,keepaspectratio]{../图表/结果总览图.pdf}\n\\caption{图3 数据结果图}\n\\label{fig:result3}\n\\end{figure}\n"
        + "\\begin{figure}[H]\n\\centering\n\\includegraphics[width=0.72\\linewidth,height=0.70\\textheight,keepaspectratio]{../图表/结果总览图.pdf}\n\\caption{图4 数据结果图}\n\\label{fig:result4}\n\\end{figure}\n"
        + "\\section*{结论}\n本文通过三个子问题完成建模、求解与综合评价，给出可解释的结论与推广建议。\n",
    )
    padding = ("% 长注释填充，模拟完整模板与长篇正文入口说明。\n" * 120)
    write_text(
        workspace / "论文" / "论文正文.tex",
        textwrap.dedent(
            r"""
            \documentclass[withoutpreface,bwprint]{cumcmthesis}
            \usepackage{graphicx}
            \usepackage{float}
            \begin{document}
            \section*{摘要}
            \label{AbstractStart}
            本文针对三个子问题展开建模、求解与分析，并在结果部分给出明确的数值结论。
            \noindent\textbf{关键词：} 多阶段优化；综合评价；鲁棒性分析
            \label{AbstractEnd}
            \label{BodyStart}
            \input{章节/1_问题重述.tex}
            \input{章节/2_模型构建.tex}
            \input{章节/3_结果分析.tex}
            \begin{thebibliography}{9}
            \bibitem{ref1} Example Reference
            \end{thebibliography}
            \label{BodyEnd}
            \appendix
            \input{章节/A_code.tex}
            \end{document}
            """
        ).strip()
        + "\n结果总览图.pdf\n技术路线图.pdf\n"
        + padding,
    )
    run(
        str(workspace / "工具" / "build_code_appendix.py"),
        "--workspace",
        str(workspace),
        "--format",
        "latex",
        "--output",
        "论文/章节/A_code.tex",
    )


def make_s7(workspace: Path) -> None:
    pdf = workspace / "论文" / "数模论文.pdf"
    page_objects = b"\n".join(b"<< /Type /Page >>" for _ in range(8))
    pdf.write_bytes(b"%PDF-1.4\n" + page_objects + b"\n% smoke padding\n" + b"x" * 25000)
    write_text(
        workspace / "论文" / "论文正文.aux",
        "\\newlabel{AbstractStart}{{}{1}}\n"
        "\\newlabel{AbstractEnd}{{}{1}}\n"
        "\\newlabel{BodyStart}{{}{2}}\n"
        "\\newlabel{BodyEnd}{{}{7}}\n",
    )
    write_text(
        workspace / "论文" / "编译日志.log",
        "This is XeTeX, Version mock\nCompilation successful\nUndefined references: 0\nUndefined citations: 0\n",
    )


GENERATORS = {
    "DISCOVERY": make_s1,
    "FORMULATION": make_s2,
    "COMPUTATION": make_s3,
    "EVIDENCE": make_s4,
    "SCHEMATICS": make_s5,
    "MANUSCRIPT": make_s6,
    "ASSURANCE": make_s7,
}


CHECKPOINT_ACTION = {
    "DISCOVERY": "approve",
    "FORMULATION": "feedback",
    "COMPUTATION": "approve",
    "MANUSCRIPT": "approve",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a repeatable baseline smoke workflow across all seven stages.")
    parser.add_argument("--workspace", default=str((SCRIPT_DIR.parent.parent / "runtime_smoke_full").resolve()))
    parser.add_argument("--keep", action="store_true", help="Keep any existing workspace instead of recreating it.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    if workspace.exists() and not args.keep:
        shutil.rmtree(workspace)

    run(str(WORKSPACE_INIT), "--workspace", str(workspace), "--force")
    failed_enhancement = run(str(PIPELINE_MANAGER), "set-phase", "enhancement", "--workspace", str(workspace), check=False)
    if failed_enhancement.returncode == 0:
        raise RuntimeError("Enhancement phase should not be allowed before baseline completion.")

    for stage in ["DISCOVERY", "FORMULATION", "COMPUTATION", "EVIDENCE", "SCHEMATICS", "MANUSCRIPT", "ASSURANCE"]:
        run(str(STAGE_EXECUTOR), "begin", stage, "--workspace", str(workspace))
        ensure_exists(workspace / "当前工作.md")
        ensure_exists(workspace / "当前任务" / "执行中" / "任务包.json")
        ensure_exists(workspace / "当前任务" / "执行中" / "执行协议.md")
        GENERATORS[stage](workspace)
        run(str(STAGE_EXECUTOR), "validate", stage, "--workspace", str(workspace))
        run(str(STAGE_EXECUTOR), "gate_check", stage, "--workspace", str(workspace))
        step = find_step(stage)
        ensure_exists(workspace / "审查" / "门禁" / f"{step['display_name']}.json")

        artifacts = {
            "DISCOVERY": "问题分析.md",
            "FORMULATION": "建模报告.md",
            "COMPUTATION": "程序/主程序.py,计算结果.md,图表/全部结果.json,依赖清单.txt",
            "EVIDENCE": "图表/图表引用.tex,图表/结果总览图.pdf",
            "SCHEMATICS": "图表/图表引用.tex,图表/技术路线图.drawio,图表/技术路线图.pdf",
            "MANUSCRIPT": "论文/论文正文.tex",
            "ASSURANCE": "论文/数模论文.pdf",
        }[stage]
        run(str(STAGE_EXECUTOR), "complete", stage, "--workspace", str(workspace), "--artifacts", artifacts)
        if stage in CHECKPOINT_ACTION:
            run(
                str(STAGE_EXECUTOR),
                "checkpoint",
                stage,
                "--workspace",
                str(workspace),
                "--action",
                CHECKPOINT_ACTION[stage],
                "--note",
                "baseline smoke",
            )

    run(str(PIPELINE_MANAGER), "set-phase", "enhancement", "--workspace", str(workspace))
    final_status = run(str(STAGE_EXECUTOR), "status", "--workspace", str(workspace))
    print(final_status.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
