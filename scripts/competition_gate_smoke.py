from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from gate_contracts import (  # noqa: E402
    GateResult,
    anonymous_markers,
    competition_source_checks,
    count_section_files,
    declared_base_font_pt,
    has_section_inputs,
)


def main() -> int:
    profiles = json.loads((ROOT / "assets" / "competition_profiles.json").read_text(encoding="utf-8"))
    base = ROOT.parent / "runtime_competition_gate_smoke"
    if base.exists():
        shutil.rmtree(base)
    results = {}
    for key, profile in profiles.items():
        source = ROOT / "assets" / "templates" / "manuscript-synthesis" / profile["template_dir"]
        paper = base / key / "论文"
        shutil.copytree(source, paper)
        main_tex = (paper / "main.tex").read_text(encoding="utf-8")
        class_text = (paper / profile["class_file"]).read_text(encoding="utf-8")
        font_pt = declared_base_font_pt(main_tex, class_text)
        missing_contracts = [term for term in profile["class_required_terms"] if term.lower() not in class_text.lower()]
        assert count_section_files(base / key) >= 9, key
        assert has_section_inputs(main_tex), key
        assert font_pt is not None and font_pt >= float(profile["minimum_font_pt"]), (key, font_pt)
        assert not missing_contracts, (key, missing_contracts)
        state_dir = base / key / "状态"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "工作流状态.json").write_text(json.dumps({"competition": key}), encoding="utf-8")
        if key == "mcm-icm":
            main_tex = main_tex.replace("\\controlnumber{[CONTROL NUMBER]}", "\\controlnumber{1234567}")
            main_tex = main_tex.replace("\\problemchoice{[A--F]}", "\\problemchoice{A}")
        corpus = main_tex + "\n" + "\n".join(path.read_text(encoding="utf-8") for path in (paper / "sections").glob("*.tex"))
        gate = GateResult("MANUSCRIPT", "competition-smoke")
        competition_source_checks(base / key, main_tex, corpus, gate)
        assert gate.to_dict()["passed"], (key, gate.to_dict()["issues"])
        results[key] = {"font_pt": font_pt, "sections": count_section_files(base / key), "class_contracts": "pass"}

    assert "University" not in anonymous_markers("Oxford University Press")
    assert "Advisor" not in anonymous_markers("Advisor-based optimization is discussed as a method name.")
    assert declared_base_font_pt("\\documentclass[10pt]{article}", "") == 10.0
    assert declared_base_font_pt("\\documentclass[12pt]{article}", "") == 12.0

    mcm_workspace = base / "mcm-icm"
    mcm_class = mcm_workspace / "论文" / "mcmicm.cls"
    original = mcm_class.read_text(encoding="utf-8")
    mcm_class.write_text(original.replace("LoadClass[12pt,letterpaper]", "LoadClass[10pt,letterpaper]"), encoding="utf-8")
    main_tex = (mcm_workspace / "论文" / "main.tex").read_text(encoding="utf-8").replace("\\controlnumber{[CONTROL NUMBER]}", "\\controlnumber{1234567}").replace("\\problemchoice{[A--F]}", "\\problemchoice{A}")
    corpus = main_tex + "\nReport on Use of AI Tools\nsummarysheet keywords thebibliography"
    negative = GateResult("MANUSCRIPT", "competition-smoke-negative")
    competition_source_checks(mcm_workspace, main_tex, corpus, negative)
    assert not negative.to_dict()["passed"]
    assert any("competition_minimum_font" in issue or "competition_class_contract" in issue for issue in negative.to_dict()["issues"])
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
