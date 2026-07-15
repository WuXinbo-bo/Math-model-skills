from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from gate_contracts import body_density_contract, latex_figure_contract_issues, page_policy_measure  # noqa: E402


def write_state(workspace: Path, competition: str = "cumcm") -> None:
    state_dir = workspace / "状态"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "工作流状态.json").write_text(json.dumps({"competition": competition, "output_format": "pdf"}), encoding="utf-8")


def main() -> int:
    base = ROOT.parent / "runtime_paper_quality_gate_smoke"
    if base.exists():
        shutil.rmtree(base)
    good = base / "good"
    write_state(good)
    section_dir = good / "论文" / "章节"
    section_dir.mkdir(parents=True)
    paragraph = "模型机制与目标函数约束明确，求解结果为有效数值。独立验证与灵敏度检验表明结果稳定，并解释其现实意义和局限性。"
    (section_dir / "问题_1.tex").write_text("\\section{问题一模型与结果}\n" + paragraph * 70, encoding="utf-8")
    (section_dir / "validation.tex").write_text("\\section{验证与讨论}\n" + paragraph * 30, encoding="utf-8")
    (good / "论文" / "论文正文.tex").write_text(
        "\\documentclass{article}\n\\begin{document}\n"
        "\\includegraphics[width=0.72\\linewidth,height=0.70\\textheight,keepaspectratio]{fig.pdf}\n"
        "\\input{章节/问题_1}\\input{章节/validation}\\end{document}", encoding="utf-8"
    )
    units, body_issues = body_density_contract(good)
    assert units >= 3500 and not body_issues, (units, body_issues)
    assert not latex_figure_contract_issues(good)
    (good / "论文" / "论文正文.aux").write_text(
        "\\newlabel{AbstractStart}{{}{1}}\n"
        "\\newlabel{AbstractEnd}{{}{1}}\n"
        "\\newlabel{BodyStart}{{}{2}}\n"
        "\\newlabel{BodyEnd}{{}{31}}\n",
        encoding="utf-8",
    )
    measurement, page_issues = page_policy_measure(good, 44)
    assert measurement["counted_pages"] == 30 and not page_issues, (measurement, page_issues)

    (good / "论文" / "论文正文.aux").write_text(
        "\\newlabel{AbstractStart}{{}{1}}\n"
        "\\newlabel{AbstractEnd}{{}{1}}\n"
        "\\newlabel{BodyStart}{{}{2}}\n"
        "\\newlabel{BodyEnd}{{}{32}}\n",
        encoding="utf-8",
    )
    _, over_limit = page_policy_measure(good, 45)
    assert any("exceed limit" in item for item in over_limit), over_limit

    bad_figure = base / "bad_figure"
    shutil.copytree(good, bad_figure)
    (bad_figure / "论文" / "论文正文.tex").write_text(
        "\\includegraphics[width=1.20\\textwidth,height=0.85\\textheight]{fig.pdf}", encoding="utf-8"
    )
    figure_issues = latex_figure_contract_issues(bad_figure)
    assert any("width exceeds" in item for item in figure_issues)
    assert any("height exceeds" in item for item in figure_issues)
    assert any("missing keepaspectratio" in item for item in figure_issues)

    thin = base / "thin"
    write_state(thin)
    thin_dir = thin / "论文" / "sections"
    thin_dir.mkdir(parents=True)
    (thin_dir / "problem1.tex").write_text("model result validation interpretation", encoding="utf-8")
    thin_units, thin_issues = body_density_contract(thin)
    assert thin_units < 3500 and thin_issues
    print(json.dumps({"good_units": units, "page_measurement": measurement, "page_over_limit": over_limit, "bad_figure_issues": figure_issues, "thin_units": thin_units, "thin_issues": thin_issues}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
