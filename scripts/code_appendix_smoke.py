from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from gate_contracts import code_appendix_contract_issues  # noqa: E402


def main() -> int:
    workspace = ROOT.parent / "runtime_code_appendix_smoke"
    if workspace.exists():
        shutil.rmtree(workspace)
    (workspace / "程序").mkdir(parents=True)
    (workspace / "论文" / "sections").mkdir(parents=True)
    (workspace / "状态").mkdir(parents=True)
    profiles = json.loads((ROOT / "assets" / "competition_profiles.json").read_text(encoding="utf-8"))
    state = {"competition": "cumcm", "competition_profile": profiles["cumcm"], "output_format": "pdf"}
    (workspace / "状态" / "工作流状态.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    (workspace / "程序" / "主程序.py").write_text("def main():\n    return 1\n\nif __name__ == '__main__':\n    main()\n" * 6, encoding="utf-8")
    (workspace / "程序" / "问题_1.py").write_text("def solve():\n    return {'value': 1}\n" * 6, encoding="utf-8")
    (workspace / "程序" / "数据清洗.py").write_text("def clean(value):\n    return value\n" * 6, encoding="utf-8")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_code_appendix.py"), "--workspace", str(workspace), "--format", "latex"],
        check=True,
        capture_output=True,
        text=True,
    )
    appendix = (workspace / "论文" / "sections" / "A_code.tex").read_text(encoding="utf-8")
    issues = code_appendix_contract_issues(workspace, appendix)
    assert not issues, issues
    assert appendix.count("\\lstinputlisting") == 2
    assert "main.py" in appendix and "problem\\_1.py" in appendix and "data\\_cleaning.py" in appendix
    assert "CODE_FILE: 程序/数据清洗.py" not in appendix
    assert "附录 1：附录目录" in appendix and "附录 4：复现说明" in appendix
    overembedded = code_appendix_contract_issues(workspace, appendix + "\n% CODE_FILE: 程序/数据清洗.py")
    assert any("must not be expanded" in item for item in overembedded), overembedded
    (workspace / "程序" / "问题_1.py").write_text("def solve():\n    return {'value': 2}\n", encoding="utf-8")
    stale = code_appendix_contract_issues(workspace, appendix)
    assert any("stale source hash" in item for item in stale), stale
    print(json.dumps({"embedded_files": 2, "stale_detection": stale}, ensure_ascii=False, indent=2))
    shutil.rmtree(workspace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
