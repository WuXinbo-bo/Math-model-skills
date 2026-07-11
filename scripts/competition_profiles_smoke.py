from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INIT = ROOT / "scripts" / "workspace_init.py"


def run(*args: str) -> None:
    proc = subprocess.run([sys.executable, *args], text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(f"failed: {' '.join(args)}\n{proc.stdout}\n{proc.stderr}")


def main() -> int:
    base = ROOT.parent / "runtime_competition_profiles_smoke"
    if base.exists():
        shutil.rmtree(base)
    expected = {
        "cumcm": {"cumcmthesis.cls", "main.tex"},
        "51mcm": {"51mcmthesis.cls", "main.tex", "LICENSE-CC-BY-NC-4.0.txt", "simkai.ttf", "simsun.ttc", "51mcm.png"},
        "mcm-icm": {"mcmicm.cls", "main.tex"},
    }
    report = {}
    for key, required in expected.items():
        workspace = base / key
        run(str(INIT), "--workspace", str(workspace), "--competition", key)
        state = json.loads((workspace / "状态" / "工作流状态.json").read_text(encoding="utf-8"))
        actual = {path.name for path in (workspace / "模板" / "当前竞赛").iterdir() if path.is_file()}
        assert state["competition"] == key
        assert state["competition_profile"]["template_dir"] == key
        assert required <= actual, (key, required - actual)
        sections = workspace / "模板" / "当前竞赛" / "sections"
        assert sections.exists() and len(list(sections.glob("*.tex"))) >= 9, key
        report[key] = {
            "display_name": state["display_name"],
            "language": state["competition_profile"]["language"],
            "page_limit": state["competition_profile"]["page_limit"],
            "template_files": sorted(actual),
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
