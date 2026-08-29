from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from gate_contracts import (  # noqa: E402
    figure_table_labels,
    latex_semantic_issues,
    publication_claim_issues,
    published_table_entries,
    question_input_issues,
)
from sync_question_sections import sync  # noqa: E402


def main() -> int:
    workspace = ROOT.parent / "runtime_high_quality_contracts_smoke"
    if workspace.exists():
        shutil.rmtree(workspace)
    (workspace / "论文" / "sections").mkdir(parents=True)
    (workspace / "图表").mkdir(parents=True)
    (workspace / "问题分析.md").write_text(
        "本赛题共 5 个子问题。\n" + "\n".join(f"## 问题{i}" for i in range(1, 6)), encoding="utf-8"
    )
    main = (ROOT / "assets" / "templates" / "manuscript-synthesis" / "cumcm" / "main.tex").read_text(encoding="utf-8")
    (workspace / "论文" / "论文正文.tex").write_text(main, encoding="utf-8")
    template_sections = ROOT / "assets" / "templates" / "manuscript-synthesis" / "cumcm" / "sections"
    for source in template_sections.iterdir():
        if source.is_file():
            shutil.copy2(source, workspace / "论文" / "sections" / source.name)
    created = sync(workspace, 5)
    assert {path.name for path in created} == {"problem4.tex", "problem5.tex"}
    updated_main = (workspace / "论文" / "论文正文.tex").read_text(encoding="utf-8")
    assert not question_input_issues(workspace, updated_main, 5)
    broken_main = updated_main.replace("\\input{sections/problem5}\n", "")
    assert any("Q5" in issue for issue in question_input_issues(workspace, broken_main, 5))

    claims = {
        "publication_claims": {
            f"C-Q{index}-01": {
                "question": f"Q{index}",
                "statement": f"question {index} result",
                "display_value": str(index * 10),
                "source_key": f"Q{index}.result",
                "derivation": "direct",
                "required_in": ["body"],
            }
            for index in range(1, 6)
        }
    }
    (workspace / "图表" / "全部结果.json").write_text(json.dumps(claims, ensure_ascii=False), encoding="utf-8")
    assert not publication_claim_issues(workspace, 5, "10 20 30 40 50")
    claims["publication_claims"].pop("C-Q5-01")
    (workspace / "图表" / "全部结果.json").write_text(json.dumps(claims, ensure_ascii=False), encoding="utf-8")
    assert any("Q5" in issue for issue in publication_claim_issues(workspace, 5))

    published_table = workspace / "图表" / "TABLE_q1.tex"
    diagnostic_table = workspace / "图表" / "TABLE_diagnostic.tex"
    published_table.write_text("\\begin{table}\\label{tab:q1}published\\end{table}", encoding="utf-8")
    diagnostic_table.write_text("\\begin{table}\\label{tab:diagnostic}diagnostic\\end{table}", encoding="utf-8")
    manifest = {
        "version": 1,
        "figures": [],
        "tables": [
            {"path": "图表/TABLE_q1.tex", "label": "tab:q1", "publish": True},
            {"path": "图表/TABLE_diagnostic.tex", "label": "tab:diagnostic", "publish": False},
        ],
    }
    (workspace / "图表" / "figure_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    assert len(published_table_entries(workspace)) == 1
    assert figure_table_labels(workspace) == ["tab:q1"]

    clean = workspace / "论文" / "sections" / "reference_test.tex"
    clean.write_text("见图~\\ref{fig:test}。\\begin{equation}x=1\\end{equation}", encoding="utf-8")
    assert not any("reference_test.tex" in issue for issue in latex_semantic_issues(workspace))
    clean.write_text("如图 3 所示，结果成立。", encoding="utf-8")
    assert any("hard-coded" in issue for issue in latex_semantic_issues(workspace))

    shutil.rmtree(workspace)
    print("high-quality contracts passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
