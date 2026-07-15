from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable

from manifest import competition_profile, find_step
from state_store import load_state


CN_DIGITS = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_bytes(path: Path) -> bytes:
    return path.read_bytes() if path.exists() else b""


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def cn_int(text: str) -> int | None:
    if text.isdigit():
        return int(text)
    return CN_DIGITS.get(text.strip())


def declared_problem_count(text: str) -> int | None:
    match = re.search(r"本赛题共\s*([0-9一二三四五六七八九十]+)\s*个子问题", text)
    if not match:
        return None
    return cn_int(match.group(1))


def heading_problem_count(text: str) -> int:
    patterns = [
        r"(?m)^##+\s*问题[一二三四五六七八九十0-9]+",
        r"(?m)^###\s*问题[一二三四五六七八九十0-9]+",
        r"(?m)^##+\s*Problem\s*[0-9]+",
        r"(?m)^问题[一二三四五六七八九十0-9]+",
    ]
    count = 0
    for pattern in patterns:
        count = max(count, len(re.findall(pattern, text, flags=re.IGNORECASE)))
    return count


def expected_problem_count(workspace: Path) -> int:
    candidates: list[int] = []
    for rel in ("问题分析.md", "建模报告.md"):
        text = read_text(workspace / rel)
        if not text:
            continue
        declared = declared_problem_count(text)
        if declared:
            candidates.append(declared)
        counted = heading_problem_count(text)
        if counted:
            candidates.append(counted)
    return max(candidates) if candidates else 0


def has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def planning_text(workspace: Path) -> str:
    return "\n".join(
        read_text(workspace / rel)
        for rel in ("问题分析.md", "建模报告.md", "论文规划.md")
    )


def recipe_matches(text: str) -> list[str]:
    return re.findall(r"\((?:basic|advanced|empirical|competition)\s*#\d+\)|\(custom\)", text, flags=re.IGNORECASE)


def planned_data_figure_stems(text: str) -> list[str]:
    stems: set[str] = set()
    for line in text.splitlines():
        if not recipe_matches(line):
            continue
        for stem in re.findall(r"\b(fig_[A-Za-z0-9_-]+)\b", line):
            if ".drawio" in line or stem.startswith("fig_flow_") or stem in {"技术路线图", "fig_pipeline", "fig_framework"}:
                continue
            stems.add(stem)
    return sorted(stems)


def planned_drawio_sources(text: str) -> list[str]:
    return sorted(set(re.findall(r"\b(fig_[A-Za-z0-9_-]+\.drawio)\b", text)))


def planned_tikz_sources(text: str) -> list[str]:
    return sorted(set(re.findall(r"\b(tikz(?:_diagrams)?[A-Za-z0-9_.-]*\.tex)\b", text)))


def planned_ai_image_files(text: str) -> list[str]:
    planned: set[str] = set()
    for line in text.splitlines():
        if "AIIMG" not in line and "AI Image" not in line:
            continue
        planned.update(re.findall(r"\b(fig_[A-Za-z0-9_-]+\.(?:png|jpg|jpeg))\b", line, flags=re.IGNORECASE))
    return sorted(planned)


def figure_asset_exists(workspace: Path, stem: str) -> bool:
    figures_dir = workspace / "图表"
    for suffix in (".pdf", ".png", ".jpg", ".jpeg"):
        if (figures_dir / f"{stem}{suffix}").exists():
            return True
    return False


def data_figure_assets(workspace: Path) -> list[Path]:
    figures_dir = workspace / "图表"
    assets = list(figures_dir.glob("fig_*.pdf")) + list(figures_dir.glob("fig_*.png")) + list(figures_dir.glob("fig_*.jpg")) + list(figures_dir.glob("fig_*.jpeg"))
    return [
        path
        for path in assets
        if path.stem not in {"技术路线图", "fig_pipeline", "fig_framework"}
        and not path.stem.startswith("fig_flow_")
    ]


def all_generated_figure_files(workspace: Path) -> list[Path]:
    figures_dir = workspace / "图表"
    files = list(figures_dir.glob("*.pdf")) + list(figures_dir.glob("*.png")) + list(figures_dir.glob("*.jpg")) + list(figures_dir.glob("*.jpeg"))
    return sorted(files)


def has_user_data_files(workspace: Path) -> bool:
    user_dir = workspace / "用户数据"
    return user_dir.exists() and any(path.is_file() for path in user_dir.iterdir())


def placeholder_patterns() -> list[str]:
    return [
        r"\[论文标题\]",
        r"\[中文摘要内容",
        r"\[关键词",
        r"\[English Abstract",
        r"\[Title",
        r"\[摘要待正文完成后填写\]",
        r"\[CONTROL NUMBER\]",
        r"\[PAPER TITLE\]",
        r"\[Write the English executive summary here\.\]",
        r"\[Reference entry\.\]",
        r"\[题号\]",
        r"\[报名号\]",
        r"\[(?:State|Restate|Enumerate|For every|Document|Implement|Derive|Compare|Answer|Independently|Interpret|List|complete identification|research/model/code|include the required|sources checked)[^\]]*\]",
        r"\[(?:基于|逐项|给出|分别|列出|填写|说明|按实际|由独立|报告|只写|明确|逐问|代码与|仅放|中文摘要)[^\]]*\]",
    ]


def latex_texts(workspace: Path) -> list[str]:
    texts: list[str] = []
    paper_dir = workspace / "论文"
    if not paper_dir.exists():
        return texts
    for path in sorted(paper_dir.rglob("*.tex")):
        texts.append(read_text(path))
    return texts


def latest_mtime(paths: list[Path]) -> float:
    existing = [path.stat().st_mtime for path in paths if path.exists()]
    return max(existing) if existing else 0.0


def pdf_page_count(pdf_path: Path) -> int | None:
    if not pdf_path.exists():
        return None
    try:
        from PyPDF2 import PdfReader
    except Exception:
        try:
            from pypdf import PdfReader
        except Exception:
            pdf_bytes = read_bytes(pdf_path)
            rough = len(re.findall(rb"/Type\s*/Page\b", pdf_bytes))
            return rough if rough > 0 else None
    try:
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        pdf_bytes = read_bytes(pdf_path)
        rough = len(re.findall(rb"/Type\s*/Page\b", pdf_bytes))
        return rough if rough > 0 else None


def latex_label_page(workspace: Path, label: str) -> int | None:
    aux = read_text(workspace / "论文" / "论文正文.aux")
    match = re.search(r"\\newlabel\{" + re.escape(label) + r"\}\{\{[^}]*\}\{(\d+)\}", aux)
    return int(match.group(1)) if match else None


def anonymous_markers(text: str) -> list[str]:
    patterns = [
        r"队号",
        r"队员",
        r"指导老师",
        r"指导教师",
        r"所在学校",
        r"所在学院",
        r"Team\s*Number",
    ]
    found = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(pattern)
    return found


def citation_matches(text: str) -> list[str]:
    return re.findall(r"\\(?:up)?cite[tp]?\{[^}]+\}", text)


def citation_count(text: str) -> int:
    return len(citation_matches(text))


def has_superscript_citation_style(main_tex: str, corpus: str) -> bool:
    if re.search(r"gbt7714|setcitestyle\s*\{[^}]*super|numbers\s*,\s*square\s*,\s*super|superscript", main_tex, flags=re.IGNORECASE):
        return True
    return bool(re.search(r"\\textsuperscript\s*\{\s*\\cite|\\upcite\{", corpus))


def bibliography_entry_count(workspace: Path) -> int:
    bib_path = workspace / "论文" / "references.bib"
    if bib_path.exists():
        return len(re.findall(r"@\w+\s*\{", read_text(bib_path)))
    return len(re.findall(r"\\bibitem\{", "\n".join(latex_texts(workspace))))


def labels_in_text(text: str) -> list[str]:
    return re.findall(r"\\label\{([^}]+)\}", text)


def labels_in_file(path: Path) -> list[str]:
    return labels_in_text(read_text(path))


def figure_table_labels(workspace: Path) -> list[str]:
    labels: list[str] = []
    labels.extend(labels_in_file(workspace / "图表" / "图表引用.tex"))
    for path in sorted((workspace / "图表").glob("TABLE_*.tex")):
        labels.extend(labels_in_file(path))
    return sorted(set(labels))


def missing_embedded_labels(workspace: Path) -> list[str]:
    corpus = "\n".join(latex_texts(workspace))
    missing = [label for label in figure_table_labels(workspace) if label not in corpus]
    return missing


def section_char_counts(workspace: Path) -> list[int]:
    return [len(read_text(path)) for path in manuscript_section_files(workspace)]


def manuscript_section_files(workspace: Path, suffix: str = ".tex") -> list[Path]:
    paper_dir = workspace / "论文"
    files: list[Path] = []
    for dirname in ("章节", "sections"):
        files.extend(sorted((paper_dir / dirname).glob(f"*{suffix}")))
    return files


def effective_text_units(text: str) -> int:
    cleaned = re.sub(r"(?m)%.*$", " ", text)
    cleaned = re.sub(r"\\begin\{(?:figure|table|lstlisting|verbatim|equation\*?|align\*?)\}.*?\\end\{(?:figure|table|lstlisting|verbatim|equation\*?|align\*?)\}", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\$\$.*?\$\$|\\\[.*?\\\]|\$[^$]*\$", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^]]*\])?", " ", cleaned)
    cleaned = re.sub(r"[{}\\]", " ", cleaned)
    chinese = len(re.findall(r"[\u4e00-\u9fff]", cleaned))
    english = len(re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", cleaned))
    return chinese + english


def latex_figure_contract_issues(workspace: Path) -> list[str]:
    issues: list[str] = []
    corpus = "\n".join(latex_texts(workspace))
    for index, match in enumerate(re.finditer(r"\\includegraphics(?:\[([^]]*)\])?\{([^}]+)\}", corpus), 1):
        options = (match.group(1) or "").replace(" ", "")
        asset = match.group(2)
        if not options:
            issues.append(f"figure {index} ({asset}) has no size constraint")
            continue
        if "keepaspectratio" not in options:
            issues.append(f"figure {index} ({asset}) is missing keepaspectratio")
        if "width=" not in options and "height=" not in options:
            issues.append(f"figure {index} ({asset}) has no width/height")
        width = re.search(r"width=([0-9.]+)\\(?:textwidth|linewidth)", options)
        if width and float(width.group(1)) > 1.0:
            issues.append(f"figure {index} ({asset}) width exceeds line width: {width.group(1)}")
        height = re.search(r"height=([0-9.]+)\\textheight", options)
        if height and float(height.group(1)) > 0.70:
            issues.append(f"figure {index} ({asset}) height exceeds 0.70 textheight: {height.group(1)}")
    return issues


def body_density_contract(workspace: Path) -> tuple[int, list[str]]:
    key, profile = active_profile(workspace)
    files = manuscript_section_files(workspace)
    units = sum(effective_text_units(read_text(path)) for path in files)
    minimum = int(profile.get("minimum_body_units", 3500))
    issues: list[str] = []
    if units < minimum:
        issues.append(f"effective body units {units} < required {minimum}")
    expected = expected_problem_count(workspace)
    problem_files = [path for path in files if re.search(r"(?:problem|问题)[_-]?\d+", path.stem, flags=re.IGNORECASE)]
    aggregate_problem_sections = heading_problem_count("\n".join(read_text(path) for path in files))
    if expected and len(problem_files) < expected and aggregate_problem_sections < expected:
        issues.append(f"problem coverage {max(len(problem_files), aggregate_problem_sections)} < expected {expected}")
    for path in problem_files:
        text = read_text(path)
        path_units = effective_text_units(text)
        if path_units < 450:
            issues.append(f"{path.name} effective units {path_units} < 450")
        if not has_any(text.lower(), ["模型", "公式", "目标函数", "model", "equation", "objective", "constraint"]):
            issues.append(f"{path.name} lacks model/mechanism content")
        if not has_any(text.lower(), ["结果", "数值", "求解", "result", "solution", "estimate", "prediction"]):
            issues.append(f"{path.name} lacks result content")
    corpus = "\n".join(read_text(path) for path in files).lower()
    if not has_any(corpus, ["验证", "检验", "灵敏度", "鲁棒", "validation", "sensitivity", "robust"]):
        issues.append("manuscript lacks validation/sensitivity evidence")
    if not has_any(corpus, ["解释", "表明", "说明", "意味着", "interpret", "indicate", "imply", "discussion"]):
        issues.append("manuscript lacks result interpretation")
    return units, issues


class GateResult:
    def __init__(self, stage_id: str, skill_name: str) -> None:
        self.stage_id = stage_id
        self.skill_name = skill_name
        self.checks: list[dict[str, str]] = []
        self.issues: list[str] = []
        self.warnings: list[str] = []

    def require(self, condition: bool, name: str, detail: str) -> None:
        self.checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})
        if not condition:
            self.issues.append(f"{name}: {detail}")

    def warn_if(self, condition: bool, name: str, detail: str) -> None:
        self.checks.append({"name": name, "status": "warn" if condition else "pass", "detail": detail})
        if condition:
            self.warnings.append(f"{name}: {detail}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "skill_name": self.skill_name,
            "passed": not self.issues,
            "issues": self.issues,
            "warnings": self.warnings,
            "checks": self.checks,
        }


def base_output_checks(workspace: Path, step: dict[str, Any], result: GateResult) -> None:
    output_files = list(step["output_files"])
    minimums = dict(step.get("min_output_bytes", {}))
    try:
        output_format = load_state(workspace).get("output_format", "pdf")
    except FileNotFoundError:
        output_format = "pdf"
    if output_format == "docx" and step["stage_id"] == "MANUSCRIPT":
        output_files = ["论文/论文正文.md"]
        minimums = {"论文/论文正文.md": 5000}
    elif output_format == "docx" and step["stage_id"] == "ASSURANCE":
        output_files = ["论文/数模论文.docx", "论文/docx_report.json"]
        minimums = {"论文/数模论文.docx": 15000, "论文/docx_report.json": 100}
    for rel in output_files:
        path = workspace / rel
        minimum = minimums.get(rel, 1)
        result.require(path.exists(), f"output:{rel}", "required output exists")
        if path.exists():
            result.require(path.stat().st_size >= minimum, f"output_size:{rel}", f"size >= {minimum} bytes")
    for rel in step.get("companion_files", []):
        path = workspace / rel
        minimum = 1 if rel == "依赖清单.txt" else 50
        result.require(path.exists(), f"companion:{rel}", "required companion exists")
        if path.exists():
            result.require(path.stat().st_size >= minimum, f"companion_size:{rel}", f"companion size >= {minimum} bytes")


def check_s1(workspace: Path, step: dict[str, Any]) -> dict[str, Any]:
    result = GateResult(step["stage_id"], step["skill_name"])
    base_output_checks(workspace, step, result)
    text = read_text(workspace / "问题分析.md")
    result.require("子问题" in text, "subproblem_breakdown", "analysis mentions 子问题")
    result.require(has_any(text, ["变量", "符号"]), "variables", "analysis includes variables or symbols")
    result.require("建模" in text, "modeling_direction", "analysis includes modeling direction")
    result.require(has_any(text, ["图表", "流程图", "技术路线图"]), "figure_plan", "analysis includes figure or roadmap planning")
    result.require("数据探索" in text, "data_exploration", "analysis includes data exploration or no-data treatment")
    result.require("工作计划" in text, "work_plan", "analysis includes a work plan")
    result.require("假设敏感性预检" in text, "assumption_precheck", "analysis records assumption sensitivity precheck")
    result.require(has_any(text, ["题目逐句拆解表", "句子级五问审查"]), "sentence_audit", "analysis includes sentence-level audit tables")
    result.require(has_any(text, ["反向对照表", "经典问题升级"]), "enhancement_audit", "analysis includes reverse mapping or classic-problem enhancement audit")
    result.require(bool(recipe_matches(text)), "figure_recipe_ids", "analysis includes figure recipe ids or custom markers")
    result.require("技术路线图.drawio" in text, "roadmap_drawio_plan", "analysis plans 技术路线图.drawio")
    result.require(has_any(text, ["语言:", "语言："]), "diagram_language", "analysis states the diagram language")
    count = declared_problem_count(text)
    result.require(count is not None, "declared_problem_count", "analysis explicitly states the subproblem count")
    if count:
        for index in range(1, count + 1):
            result.require(
                f"问题流程图_{index}.drawio" in text,
                f"flow_plan_q{index}",
                f"analysis plans 问题流程图_{index}.drawio",
            )
    return result.to_dict()


def check_s2(workspace: Path, step: dict[str, Any]) -> dict[str, Any]:
    result = GateResult(step["stage_id"], step["skill_name"])
    base_output_checks(workspace, step, result)
    text = read_text(workspace / "建模报告.md")
    expected = expected_problem_count(workspace)
    modeled = heading_problem_count(text)
    if expected:
        result.require(modeled >= expected, "problem_coverage", f"modeled subproblems {modeled} >= expected {expected}")
    result.require(has_any(text, ["目标函数", "min", "max", "\\begin{align}", "\\["]), "objective_or_formula", "report includes objective or formula markers")
    result.require(has_any(text, ["约束", "subject to", "s.t."]), "constraints", "report includes constraints")
    result.require(has_any(text, ["验证", "灵敏度", "鲁棒", "检验"]), "verification_plan", "report includes verification/sensitivity/robustness")
    result.require("假设" in text, "assumptions", "report includes assumptions")
    result.require("参数化:" in text, "parameterized_assumptions", "report includes parameterization markers")
    result.require("替代假设:" in text, "alternate_assumptions", "report includes alternate assumptions")
    result.require(has_any(text, ["经典问题升级", "升级建议", "覆盖度检查表", "反向对照"]), "enhancement_review", "report reviews enhancement suggestions from DISCOVERY")
    result.require("已对照防错手册审查" in text, "error_prevention_ack", "report acknowledges the error-prevention review")
    result.require("验证检查点" in text, "validation_checkpoints", "report includes validation checkpoints for computational-realization")
    result.require("图表预规划" in text, "figure_plan_carried", "report carries the figure plan forward")
    if has_any(text, ["优化", "线性规划", "整数规划", "目标函数", "最优"]):
        result.require("结构性验证输入" in text, "structural_validation_inputs", "optimization-like reports include structural validation inputs")
    return result.to_dict()


def problem_script_count(workspace: Path) -> int:
    return len(list((workspace / "程序").glob("问题_[0-9]*.py")))


def problem_json_count(workspace: Path) -> int:
    count = len(list((workspace / "图表").glob("问题_*_结果.json")))
    count = max(count, len(list((workspace / "图表").glob("problem_*_结果.json"))))
    return count


def contains_forbidden_figure_output(workspace: Path) -> bool:
    code_dir = workspace / "程序"
    if not code_dir.exists():
        return False
    pattern = re.compile(r"(savefig|save_fig)\s*\([^)]*\.pdf", re.IGNORECASE | re.DOTALL)
    for path in code_dir.rglob("*.py"):
        if pattern.search(read_text(path)):
            return True
    return False


def check_s3(workspace: Path, step: dict[str, Any]) -> dict[str, Any]:
    result = GateResult(step["stage_id"], step["skill_name"])
    base_output_checks(workspace, step, result)
    expected = expected_problem_count(workspace)
    scripts = problem_script_count(workspace)
    jsons = problem_json_count(workspace)
    results_text = read_text(workspace / "计算结果.md")
    main_text = read_text(workspace / "程序" / "主程序.py")
    requirements_text = read_text(workspace / "依赖清单.txt")
    if expected:
        result.require(scripts >= expected, "problem_scripts", f"problem scripts {scripts} >= expected {expected}")
        result.require(jsons >= expected, "problem_jsons", f"problem result json {jsons} >= expected {expected}")
        result.require(
            heading_problem_count(results_text) >= expected,
            "results_problem_sections",
            f"计算结果.md covers at least {expected} problems",
        )
    result.require((workspace / "图表" / "全部结果.json").exists(), "aggregate_json", "全部结果.json exists")
    result.require(bool(re.search(r"\d", results_text)), "numeric_results", "计算结果.md contains numeric results")
    result.require("全部结果.json" in main_text, "main_aggregates_results", "程序/主程序.py writes 全部结果.json")
    result.require(has_any(main_text, ["def main", "__main__"]), "main_entrypoint", "程序/主程序.py has a main entrypoint")
    result.require(
        has_any(requirements_text, ["numpy", "pandas", "scipy", "matplotlib", "scikit-learn", "statsmodels", "networkx"]),
        "scientific_requirements",
        "依赖清单.txt lists at least one scientific library",
    )
    result.require(not contains_forbidden_figure_output(workspace), "no_pdf_figure_output", "computational-realization does not save pdf figures")
    if has_user_data_files(workspace):
        result.require((workspace / "程序" / "数据校验.py").exists(), "data_check_script", "data-bearing workflows include 程序/数据校验.py")
    result.warn_if(not (workspace / "程序" / "通用工具.py").exists(), "utils_skeleton", "程序/通用工具.py is missing")
    return result.to_dict()


def paper_plan_allows_empty(workspace: Path) -> bool:
    text = read_text(workspace / "论文规划.md")
    return bool(text and ("无图表" in text or "图表清单为空" in text))


def check_s4(workspace: Path, step: dict[str, Any]) -> dict[str, Any]:
    result = GateResult(step["stage_id"], step["skill_name"])
    figure_files = list((workspace / "图表").glob("*.pdf")) + list((workspace / "图表").glob("*.png"))
    includes = workspace / "图表" / "图表引用.tex"
    includes_text = read_text(includes)
    plan_text = planning_text(workspace)
    planned_data = planned_data_figure_stems(plan_text)
    planned_ai = planned_ai_image_files(plan_text)
    result.require(includes.exists(), "output:图表/图表引用.tex", "图表引用.tex exists")
    if figure_files:
        result.require(includes.exists() and includes.stat().st_size > 0, "latex_includes", "图表引用.tex is present for generated figures")
    else:
        result.require(
            paper_plan_allows_empty(workspace) or (includes.exists() and not includes_text.strip()),
            "empty_figure_placeholder",
            "empty figure case is explicitly handled",
        )
    if planned_data:
        for stem in planned_data:
            result.require(figure_asset_exists(workspace, stem), f"planned_figure:{stem}", f"{stem} planned in docs and generated in 图表/")
            result.require(stem in includes_text, f"latex_include:{stem}", f"{stem} is referenced from 图表引用.tex")
    if planned_ai:
        for name in planned_ai:
            result.require((workspace / "图表" / name).exists(), f"planned_ai_image:{name}", f"{name} planned in docs and generated")
    result.require((workspace / "图表" / "全部结果.json").exists(), "all_results_json", "figure stage has upstream aggregated json")
    return result.to_dict()


def no_diagram_plan(workspace: Path) -> bool:
    text = read_text(workspace / "论文规划.md")
    return bool(text and ("无架构图" in text or "无流程图" in text))


def check_s5(workspace: Path, step: dict[str, Any]) -> dict[str, Any]:
    result = GateResult(step["stage_id"], step["skill_name"])
    includes_path = workspace / "图表" / "图表引用.tex"
    result.require(includes_path.exists(), "output:图表/图表引用.tex", "图表引用.tex exists")
    drawios = list((workspace / "图表").glob("*.drawio"))
    tikz = list((workspace / "图表").glob("tikz_*.tex")) + list((workspace / "图表").glob("结构示意图*.tex"))
    includes_text = read_text(includes_path)
    plan_text = planning_text(workspace)
    planned_drawios = planned_drawio_sources(plan_text)
    planned_tikz = planned_tikz_sources(plan_text)
    if drawios or tikz or planned_drawios or planned_tikz:
        result.require(bool(drawios or tikz), "diagram_sources", "drawio or tikz source exists")
        expected_pdfs = []
        for path in drawios:
            expected_pdfs.append(path.with_suffix(".pdf"))
        for path in tikz:
            expected_pdfs.append(path.with_suffix(".pdf"))
        existing_expected = [path for path in expected_pdfs if path.exists()]
        result.require(bool(existing_expected), "diagram_pdfs", "diagram pdf exists")
        missing_refs = []
        for path in drawios + tikz:
            stem = path.stem
            if stem not in includes_text:
                missing_refs.append(stem)
        result.require(not missing_refs, "latex_includes_append", f"diagram entries referenced: {', '.join(missing_refs) if missing_refs else 'all ok'}")
        for rel in planned_drawios:
            source = workspace / "图表" / rel
            result.require(source.exists(), f"planned_drawio:{rel}", f"{rel} planned in docs and generated")
            result.require(source.with_suffix(".pdf").exists(), f"planned_drawio_pdf:{rel}", f"{source.with_suffix('.pdf').name} exists")
            result.require(source.stem in includes_text, f"planned_drawio_include:{rel}", f"{rel} is referenced from 图表引用.tex")
        for rel in planned_tikz:
            source = workspace / "图表" / rel
            result.require(source.exists(), f"planned_tikz:{rel}", f"{rel} planned in docs and generated")
            result.require(source.with_suffix(".pdf").exists(), f"planned_tikz_pdf:{rel}", f"{source.with_suffix('.pdf').name} exists")
            result.require(source.stem in includes_text or source.with_suffix(".pdf").name in includes_text, f"planned_tikz_include:{rel}", f"{rel} is referenced from 图表引用.tex")
    else:
        result.require(no_diagram_plan(workspace), "no_diagram_exception", "diagram-free run must be explicitly declared")
    return result.to_dict()


def count_section_files(workspace: Path) -> int:
    paper_dir = workspace / "论文"
    return sum(len(list((paper_dir / dirname).glob("*.tex"))) for dirname in ("章节", "sections"))


def has_section_inputs(main_tex: str) -> bool:
    return bool(re.search(r"\\(?:input|include)\{(?:章节|sections)/", main_tex))


def resolve_competition_class(workspace: Path, profile: dict[str, Any]) -> Path | None:
    class_file = profile.get("class_file")
    if not class_file:
        return None
    candidates = [
        workspace / "论文" / class_file,
        workspace / "模板" / "当前竞赛" / class_file,
        Path(__file__).resolve().parent.parent / "assets" / "templates" / "manuscript-synthesis" / profile.get("template_dir", "") / class_file,
    ]
    return next((path for path in candidates if path.exists()), None)


def declared_base_font_pt(main_tex: str, class_text: str) -> float | None:
    combined = main_tex + "\n" + class_text
    match = re.search(r"\\(?:documentclass|LoadClass)\[([^]]*)\]", combined, flags=re.IGNORECASE)
    if match:
        size = re.search(r"(?:^|,)\s*(\d+(?:\.\d+)?)pt(?:\s*,|$)", match.group(1), flags=re.IGNORECASE)
        if size:
            return float(size.group(1))
    size = re.search(r"\\@setfontsize\\normalsize\{(\d+(?:\.\d+)?)\}", class_text)
    return float(size.group(1)) if size else None


def referenced_figure_basenames(workspace: Path) -> set[str]:
    corpus = "\n".join(latex_texts(workspace))
    refs: set[str] = set()
    for path in (workspace / "图表").glob("*.pdf"):
        if path.name in corpus:
            refs.add(path.name)
    return refs


def placeholders_present(workspace: Path) -> list[str]:
    corpus = "\n".join(latex_texts(workspace))
    found = []
    for pattern in placeholder_patterns():
        if re.search(pattern, corpus):
            found.append(pattern)
    return found


def active_profile(workspace: Path) -> tuple[str, dict[str, Any]]:
    try:
        state = load_state(workspace)
        key = state.get("competition", "cumcm")
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        key = "cumcm"
    return key, competition_profile(key)


def competition_source_checks(workspace: Path, main_tex: str, corpus: str, result: GateResult) -> None:
    key, profile = active_profile(workspace)
    result.require(bool(profile), "competition_profile", f"active competition profile: {key}")
    for term in profile.get("required_source_terms", []):
        result.require(term.lower() in main_tex.lower(), f"competition_source:{term}", f"required template marker present: {term}")
    for term in profile.get("required_content_terms", []):
        result.require(term.lower() in corpus.lower(), f"competition_content:{term}", f"required paper content present: {term}")
    forbidden = [term for term in profile.get("forbidden_identity_terms", []) if term.lower() in corpus.lower()]
    result.require(not forbidden, "competition_identity", f"forbidden identity fields absent: {forbidden or 'none'}")
    class_path = resolve_competition_class(workspace, profile)
    result.require(class_path is not None, "competition_class_file", f"competition class is available: {profile.get('class_file')}")
    class_text = read_text(class_path) if class_path else ""
    for term in profile.get("class_required_terms", []):
        result.require(term.lower() in class_text.lower(), f"competition_class_contract:{term}", f"class preserves required layout contract: {term}")
    minimum_font = float(profile.get("minimum_font_pt", 0))
    declared_font = declared_base_font_pt(main_tex, class_text)
    result.require(declared_font is not None, "competition_font_detected", f"base font size detected: {declared_font}")
    if declared_font is not None:
        result.require(declared_font >= minimum_font, "competition_minimum_font", f"base font {declared_font}pt >= required {minimum_font}pt")
    if key == "mcm-icm":
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", corpus))
        result.require(chinese_chars == 0, "english_only", f"MCM/ICM paper contains no Chinese characters ({chinese_chars} found)")
        result.require(bool(re.search(r"\\problemchoice\{[A-F]\}", main_tex, flags=re.IGNORECASE)), "mcm_problem_choice", "MCM/ICM problem choice A-F is populated")
        result.require(bool(re.search(r"\\controlnumber\{(?!\[)[^}]+\}", main_tex, flags=re.IGNORECASE)), "mcm_control_number", "Control Number is populated")


def check_s6(workspace: Path, step: dict[str, Any]) -> dict[str, Any]:
    result = GateResult(step["stage_id"], step["skill_name"])
    base_output_checks(workspace, step, result)
    try:
        state = load_state(workspace)
    except FileNotFoundError:
        state = {"output_format": "pdf"}
    if state.get("output_format") == "docx":
        markdown = read_text(workspace / "论文" / "论文正文.md")
        units = effective_text_units(markdown)
        _, profile = active_profile(workspace)
        minimum = int(profile.get("minimum_body_units", 3500))
        result.require(units >= minimum, "docx_body_density", f"effective body units {units} >= {minimum}")
        result.require(bool(re.search(r"(?m)^#\s+\S+", markdown)), "docx_title", "Markdown manuscript has a title")
        result.require(has_any(markdown, ["摘要", "Summary", "Abstract"]), "docx_abstract", "DOCX source includes abstract/summary")
        result.require(has_any(markdown, ["关键词", "Keywords"]), "docx_keywords", "DOCX source includes keywords")
        result.require(has_any(markdown, ["参考文献", "References"]), "docx_references", "DOCX source includes references")
        result.require(has_any(markdown, ["验证", "检验", "灵敏度", "鲁棒", "Validation", "Sensitivity", "Robustness"]), "docx_validation", "DOCX source includes validation")
        result.require(has_any(markdown, ["解释", "表明", "说明", "意味着", "interpret", "indicate", "discussion"]), "docx_interpretation", "DOCX source includes result interpretation")
        key, profile = active_profile(workspace)
        forbidden = [term for term in profile.get("forbidden_identity_terms", []) if term.lower() in markdown.lower()]
        result.require(not forbidden, "docx_identity", f"forbidden identity fields absent: {forbidden or 'none'}")
        if key == "mcm-icm":
            result.require(not re.search(r"[\u4e00-\u9fff]", markdown), "docx_english_only", "MCM/ICM DOCX source is English-only")
            result.require(bool(re.search(r"Control\s*Number\s*\*{0,2}:\*{0,2}\s*(?!\[)\S+", markdown, flags=re.IGNORECASE)), "docx_control_number", "Control Number is populated")
            result.require(bool(re.search(r"Problem\s*\*{0,2}:\*{0,2}\s*[A-F]\b", markdown, flags=re.IGNORECASE)), "docx_problem_choice", "Problem A-F is populated")
            result.require("Report on Use of AI Tools" in markdown, "docx_ai_report", "AI use report is present")
        if key == "51mcm":
            result.require(bool(re.search(r"报名号[：:]\s*(?!\[)\S+", markdown)), "docx_51mcm_registration", "51MCM registration number is populated")
        result.require(not any(re.search(pattern, markdown) for pattern in placeholder_patterns()), "docx_placeholders", "DOCX source contains no template placeholders")
        return result.to_dict()
    main_tex = read_text(workspace / "论文" / "论文正文.tex")
    corpus = "\n".join(latex_texts(workspace))
    result.require("documentclass" in main_tex, "template_documentclass", "论文正文.tex uses a LaTeX template")
    result.require(count_section_files(workspace) >= 3, "section_files", "论文/章节 or 论文/sections has at least 3 files")
    result.require(has_section_inputs(main_tex), "section_inputs", "论文正文.tex inputs 章节/ or sections/ files")
    result.require(has_any(main_tex, ["thebibliography", "bibliography{"]), "bibliography", "bibliography exists")
    result.require(has_any(main_tex, ["appendix", "\\appendix"]), "appendix", "appendix exists")
    result.require(has_any(corpus, ["摘要", "Abstract"]), "abstract", "paper includes an abstract section")
    result.require(has_any(corpus, ["关键词", "Keywords"]), "keywords", "paper includes keywords")
    result.require(has_any(corpus, ["结论", "结语", "总结"]), "conclusion", "paper includes a conclusion-like section")
    result.require(citation_count(corpus) > 0, "citations_in_body", "paper body includes citations")
    result.require(bibliography_entry_count(workspace) > 0, "bibliography_entries", "paper has bibliography entries")
    key, _ = active_profile(workspace)
    if key != "mcm-icm":
        result.require(has_superscript_citation_style(main_tex, corpus), "superscript_citations", "Chinese competition paper uses superscript-style citations")
    competition_source_checks(workspace, main_tex, corpus, result)
    figure_contract_issues = latex_figure_contract_issues(workspace)
    result.require(not figure_contract_issues, "figure_size_contract", f"LaTeX figures fit the page body: {figure_contract_issues or 'all ok'}")
    body_units, body_issues = body_density_contract(workspace)
    result.require(not body_issues, "body_density_contract", f"effective body units={body_units}; issues={body_issues or 'none'}")
    result.require(has_any(corpus, ["代码", "程序", "Code Appendix"]), "code_appendix", "appendix mentions code or program materials")
    missing_placeholders = placeholders_present(workspace)
    result.require(not missing_placeholders, "template_placeholders", f"placeholders removed: {missing_placeholders or 'none'}")
    figure_files = all_generated_figure_files(workspace)
    if figure_files:
        missing_refs = [path.name for path in figure_files if path.name not in corpus]
        result.require(not missing_refs, "embedded_figures", f"all generated figures are embedded: {', '.join(missing_refs) if missing_refs else 'all ok'}")
    missing_labels = missing_embedded_labels(workspace)
    if figure_table_labels(workspace):
        result.require(not missing_labels, "embedded_labels", f"all figure/table labels from figures are embedded: {', '.join(missing_labels) if missing_labels else 'all ok'}")
    section_sizes = section_char_counts(workspace)
    if section_sizes:
        result.warn_if(min(section_sizes) < 1200, "thin_section_warning", f"smallest section has {min(section_sizes)} raw chars")
    return result.to_dict()


def check_s7(workspace: Path, step: dict[str, Any]) -> dict[str, Any]:
    result = GateResult(step["stage_id"], step["skill_name"])
    base_output_checks(workspace, step, result)
    try:
        state = load_state(workspace)
    except FileNotFoundError:
        state = {"output_format": "pdf"}
    if state.get("output_format") == "docx":
        report_path = workspace / "论文" / "docx_report.json"
        report = load_json(report_path) if report_path.exists() else {}
        docx_path = workspace / "论文" / "数模论文.docx"
        source_path = workspace / "论文" / "论文正文.md"
        result.require(docx_path.exists() and docx_path.stat().st_size >= 15000, "docx_output", "DOCX output exists and is non-trivial")
        current_source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest() if source_path.exists() else ""
        result.require(bool(current_source_hash) and report.get("source_sha256") == current_source_hash, "docx_source_freshness", "DOCX report matches the current Markdown source hash")
        if source_path.exists() and docx_path.exists():
            result.require(docx_path.stat().st_mtime_ns >= source_path.stat().st_mtime_ns, "docx_output_freshness", "DOCX output is not older than the Markdown source")
        usable_width = float(report.get("usable_width_cm") or 0)
        image_issues = []
        for item in report.get("images", []):
            width = float(item.get("width_cm") or 0)
            height = float(item.get("height_cm") or 0)
            if width <= 0 or width > usable_width + 0.01:
                image_issues.append(f"{item.get('path')}: width {width}>{usable_width}")
            if height <= 0 or height > 20.0:
                image_issues.append(f"{item.get('path')}: height {height}>20")
        result.require(not image_issues, "docx_image_size_contract", f"DOCX images fit page body: {image_issues or 'all ok'}")
        _, profile = active_profile(workspace)
        minimum = int(profile.get("minimum_body_units", 3500))
        units = int(report.get("effective_body_units") or 0)
        result.require(units >= minimum, "docx_body_density", f"effective body units {units} >= {minimum}")
        limit = profile.get("page_limit")
        if limit:
            pages = report.get("page_count")
            result.require(pages is not None, "docx_page_count", "page-limited DOCX requires LibreOffice PDF preview for page counting")
            if pages is not None:
                result.require(int(pages) <= int(limit), "docx_page_limit", f"DOCX preview has {pages}/{limit} pages")
        return result.to_dict()
    pdf_path = workspace / "论文" / "数模论文.pdf"
    main_tex = workspace / "论文" / "论文正文.tex"
    corpus = "\n".join(latex_texts(workspace))
    log_text = read_text(workspace / "论文" / "编译日志.log")
    if pdf_path.exists() and main_tex.exists():
        result.require(pdf_path.stat().st_mtime >= main_tex.stat().st_mtime, "pdf_freshness", "数模论文.pdf is newer than 论文正文.tex")
    pages = pdf_page_count(pdf_path)
    if pages is not None:
        result.require(pages > 0, "pdf_pages", f"pdf has {pages} pages")
        key, profile = active_profile(workspace)
        limit = profile.get("page_limit")
        if limit:
            marker = profile.get("page_limit_marker")
            counted_pages = latex_label_page(workspace, marker) if marker else pages
            if marker:
                result.require(counted_pages is not None, "competition_page_marker", f"compiled aux records {marker}")
            if counted_pages is not None:
                result.require(counted_pages <= int(limit), "competition_page_limit", f"{key} counted solution has {counted_pages}/{limit} pages (PDF total {pages})")
    else:
        key, profile = active_profile(workspace)
        if profile.get("page_limit"):
            result.require(False, "pdf_pages_required", f"{key} requires a readable PDF page count")
        else:
            result.warn_if(True, "pdf_pages_unknown", "PyPDF2 unavailable or page count unreadable")
    result.require((workspace / "论文" / "编译日志.log").exists(), "compile_log", "论文/编译日志.log exists after compile")
    if log_text:
        result.require("undefined" not in log_text.lower() or "undefined references: 0" in log_text.lower(), "no_undefined_refs", "compile log has no undefined references or citations")
        fatal_patterns = [
            r"Bad math environment delimiter",
            r"Missing \$ inserted",
            r"Not allowed in LR mode",
            r"Undefined control sequence",
            r"Fatal error",
        ]
        fatal_hits = [pattern for pattern in fatal_patterns if re.search(pattern, log_text, flags=re.IGNORECASE)]
        result.require(not fatal_hits, "compile_log_health", f"compile log free of critical latex errors: {fatal_hits or 'none'}")
    results_json = workspace / "图表" / "全部结果.json"
    if pdf_path.exists() and results_json.exists():
        result.warn_if(pdf_path.stat().st_mtime < results_json.stat().st_mtime, "stale_pdf", "pdf is older than 全部结果.json")
        stale_figures = [path.name for path in (workspace / "图表").glob("*.pdf") if path.stat().st_mtime < results_json.stat().st_mtime]
        result.warn_if(bool(stale_figures), "stale_figures", f"figure pdf older than 全部结果.json: {', '.join(stale_figures) if stale_figures else 'none'}")
    missing_placeholders = placeholders_present(workspace)
    result.require(not missing_placeholders, "template_placeholders", f"placeholders removed: {missing_placeholders or 'none'}")
    key, _ = active_profile(workspace)
    generic_markers = anonymous_markers(corpus)
    if key == "mcm-icm":
        generic_markers = [marker for marker in generic_markers if marker not in {r"Team\s*Number"}]
    result.require(not generic_markers, "anonymous_compliance", f"anonymous markers removed: {generic_markers or 'none'}")
    competition_source_checks(workspace, read_text(main_tex), corpus, result)
    figure_contract_issues = latex_figure_contract_issues(workspace)
    result.require(not figure_contract_issues, "figure_size_contract", f"LaTeX figures fit the page body: {figure_contract_issues or 'all ok'}")
    body_units, body_issues = body_density_contract(workspace)
    result.require(not body_issues, "body_density_contract", f"effective body units={body_units}; issues={body_issues or 'none'}")
    result.require(citation_count(corpus) > 0, "citations_present", "compiled paper source still contains citations")
    result.require(bibliography_entry_count(workspace) > 0, "bibliography_entries", "compiled paper has bibliography entries")
    return result.to_dict()


CHECKERS: dict[str, Callable[[Path, dict[str, Any]], dict[str, Any]]] = {
    "DISCOVERY": check_s1,
    "FORMULATION": check_s2,
    "COMPUTATION": check_s3,
    "EVIDENCE": check_s4,
    "SCHEMATICS": check_s5,
    "MANUSCRIPT": check_s6,
    "ASSURANCE": check_s7,
}


def run_gate_check(workspace: Path, stage_identifier: str) -> dict[str, Any]:
    step = find_step(stage_identifier)
    if step is None:
        raise SystemExit(f"Unknown stage: {stage_identifier}")
    checker = CHECKERS.get(step["stage_id"])
    if checker is None:
        raise SystemExit(f"No checker for stage: {stage_identifier}")
    return checker(workspace, step)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Meta-model-agent research, evidence, and paper quality contracts.")
    parser.add_argument("stage")
    parser.add_argument("--workspace", default=".")
    args = parser.parse_args()
    report = run_gate_check(Path(args.workspace).resolve(), args.stage)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
