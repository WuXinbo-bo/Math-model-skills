from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INIT = ROOT / "scripts" / "workspace_init.py"
EXPORT = ROOT / "scripts" / "docx_export.py"
sys.path.insert(0, str(ROOT / "scripts"))
from gate_contracts import run_gate_check  # noqa: E402


def run(*args: str) -> None:
    proc = subprocess.run([sys.executable, *args], text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(proc.stdout + "\n" + proc.stderr)


def dense_sentence(competition: str) -> str:
    if competition == "mcm-icm":
        return "The model mechanism, objective, constraints, validated results, sensitivity analysis, interpretation, and limitations establish a robust recommendation. "
    return "模型机制、目标函数和约束已经推导，求解得到可靠结果；独立验证、灵敏度分析和结果解释说明方案稳定且具有现实意义。"


def valid_markdown(competition: str) -> str:
    sentence = dense_sentence(competition)
    if competition == "mcm-icm":
        return (
            "# Complete Modeling Paper\n\n**Control Number:** 1234567　　**Problem:** A\n\n"
            "## Summary\n" + sentence * 35 + "\n\n**Keywords:** model; validation; optimization\n\n"
            "## 1 Model Development, Results, and Validation\n" + sentence * 125 +
            "\n\n## 2 Discussion and Interpretation\n" + sentence * 30 +
            "\n\n## References\n[1] Test reference.\n\n## Report on Use of AI Tools\nNo AI-generated claim was accepted without human verification."
        )
    header = "**题号：** A　　**报名号：** 51001234　　**组别：** 本科\n\n" if competition == "51mcm" else ""
    return (
        "# 完整数学建模论文\n\n" + header + "## 摘要\n" + sentence * 20 +
        "\n\n**关键词：** 模型；验证；优化\n\n## 问题一模型、结果与验证\n" + sentence * 90 +
        "\n\n## 结论与解释\n" + sentence * 20 + "\n\n## 参考文献\n[1] 测试文献。"
    )


def assert_competition_contract(competition: str) -> dict:
    workspace = ROOT.parent / f"runtime_docx_{competition}_smoke"
    if workspace.exists():
        shutil.rmtree(workspace)
    run(str(INIT), "--workspace", str(workspace), "--competition", competition, "--output-format", "docx")
    source = workspace / "论文" / "论文正文.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(valid_markdown(competition), encoding="utf-8")
    good = run_gate_check(workspace, "MANUSCRIPT")
    assert good["passed"], good["issues"]
    original = source.read_text(encoding="utf-8")
    if competition == "51mcm":
        source.write_text(original.replace("51001234", "[报名号]"), encoding="utf-8")
        bad = run_gate_check(workspace, "MANUSCRIPT")
        assert not bad["passed"] and any("docx_51mcm_registration" in issue or "docx_placeholders" in issue for issue in bad["issues"]), bad
    else:
        source.write_text(original.replace("1234567", "[CONTROL NUMBER]"), encoding="utf-8")
        missing_number = run_gate_check(workspace, "MANUSCRIPT")
        assert not missing_number["passed"] and any("docx_control_number" in issue or "docx_placeholders" in issue for issue in missing_number["issues"]), missing_number
        source.write_text(original + "\n中文混入。", encoding="utf-8")
        chinese = run_gate_check(workspace, "MANUSCRIPT")
        assert not chinese["passed"] and any("docx_english_only" in issue for issue in chinese["issues"]), chinese
    source.write_text(original, encoding="utf-8")
    return {"competition": competition, "valid_gate": "pass", "negative_gate": "pass"}


def main() -> int:
    from PIL import Image
    workspace = ROOT.parent / "runtime_docx_route_smoke"
    if workspace.exists():
        shutil.rmtree(workspace)
    run(str(INIT), "--workspace", str(workspace), "--competition", "cumcm", "--output-format", "docx")
    source = workspace / "论文" / "论文正文.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    image_path = workspace / "论文" / "oversized_source.png"
    Image.new("RGB", (6000, 4000), "white").save(image_path)
    source.write_text(valid_markdown("cumcm").replace("\n\n## 结论与解释", "\n\n![超大原始图](oversized_source.png)\n\n## 结论与解释"), encoding="utf-8")
    run(str(EXPORT), "--workspace", str(workspace))
    report = json.loads((workspace / "论文" / "docx_report.json").read_text(encoding="utf-8"))
    assert (workspace / "论文" / "数模论文.docx").stat().st_size >= 15000
    assert report["effective_body_units"] >= 3500
    assert report["images"]
    assert all(item["width_cm"] <= report["usable_width_cm"] for item in report["images"])
    manuscript_gate = run_gate_check(workspace, "MANUSCRIPT")
    assurance_gate = run_gate_check(workspace, "ASSURANCE")
    assert manuscript_gate["passed"], manuscript_gate["issues"]
    assert assurance_gate["passed"], assurance_gate["issues"]
    tampered = dict(report)
    tampered["images"] = [dict(report["images"][0], width_cm=report["usable_width_cm"] + 5)]
    (workspace / "论文" / "docx_report.json").write_text(json.dumps(tampered, ensure_ascii=False, indent=2), encoding="utf-8")
    rejected = run_gate_check(workspace, "ASSURANCE")
    assert not rejected["passed"] and any("docx_image_size_contract" in issue for issue in rejected["issues"])
    (workspace / "论文" / "docx_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    source.write_text(source.read_text(encoding="utf-8") + "\n新增但尚未导出的解释。", encoding="utf-8")
    stale = run_gate_check(workspace, "ASSURANCE")
    assert not stale["passed"] and any("docx_source_freshness" in issue or "docx_output_freshness" in issue for issue in stale["issues"]), stale
    run(str(EXPORT), "--workspace", str(workspace))
    report = json.loads((workspace / "论文" / "docx_report.json").read_text(encoding="utf-8"))
    assert run_gate_check(workspace, "ASSURANCE")["passed"]
    report["competition_contracts"] = [assert_competition_contract("51mcm"), assert_competition_contract("mcm-icm")]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
