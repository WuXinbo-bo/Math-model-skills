from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from gate_contracts import data_preparation_contract_issues, manuscript_data_preparation_issues
from state_store import refresh_data_preparation_state


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_data_workspace(root: Path) -> tuple[Path, Path]:
    source = root / "用户数据" / "observations.csv"
    processed = root / "数据" / "processed" / "model_input.csv"
    write(source, "x,y\n1,2\n3,4\n")
    write(processed, "x,y\n1,2\n3,4\n")
    write(root / "问题分析.md", "数据模式: supplied\n数据预处理计划与冻结模型输入\n")
    write(root / "建模报告.md", "预处理合同：缺失值、异常值、编码、标准化；先划分后拟合；冻结模型输入。\n")
    write(root / "程序" / "data_preprocessing.py", "OUTPUT = '数据/processed/model_input.csv'\n")
    write(root / "程序" / "问题_1.py", "MODEL_INPUT = '数据/processed/model_input.csv'\n")
    payload = {
        "mode": "supplied",
        "status": "completed",
        "source_files": [{"path": "用户数据/observations.csv", "sha256": sha256(source)}],
        "processed_file": {"path": "数据/processed/model_input.csv", "sha256": sha256(processed)},
        "steps": ["schema audit", "missing-value review", "freeze input"],
        "quality_before": {"rows": 2, "missing": 0},
        "quality_after": {"rows": 2, "missing": 0},
        "leakage_control": {"applicable": True, "split_before_fit": True, "train_only_fit": True},
    }
    write(root / "图表" / "全部结果.json", json.dumps({"data_preparation": payload}, ensure_ascii=False, indent=2))
    return source, processed


def expect_ok(root: Path) -> None:
    issues = data_preparation_contract_issues(root)
    assert not issues, issues


def expect_issue(root: Path, needle: str) -> None:
    issues = data_preparation_contract_issues(root)
    assert any(needle in issue for issue in issues), issues


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="metalab-data-prep-") as temp:
        root = Path(temp)
        source, processed = make_data_workspace(root)
        expect_ok(root)

        script = root / "程序" / "data_preprocessing.py"
        script.unlink()
        expect_issue(root, "missing 程序/data_preprocessing.py")
        write(script, "OUTPUT = '数据/processed/model_input.csv'\n")

        source.write_text("x,y\n1,9\n", encoding="utf-8")
        expect_issue(root, "source file paths or hashes")
        source.write_text("x,y\n1,2\n3,4\n", encoding="utf-8")

        processed.write_text("x,y\n5,6\n", encoding="utf-8")
        expect_issue(root, "processed model input hash is stale")
        processed.write_text("x,y\n1,2\n3,4\n", encoding="utf-8")

        model = root / "程序" / "问题_1.py"
        model.write_text("def solve(): return 1\n", encoding="utf-8")
        expect_issue(root, "model programs do not reference")
        model.write_text("MODEL_INPUT = '数据/processed/model_input.csv'\n", encoding="utf-8")

        aggregate_path = root / "图表" / "全部结果.json"
        aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
        aggregate["data_preparation"]["leakage_control"]["split_before_fit"] = False
        write(aggregate_path, json.dumps(aggregate, ensure_ascii=False, indent=2))
        expect_issue(root, "split before fitting")

        manuscript = "# 模型准备\n## 数据预处理\n数据来源清楚；缺失值处理前统计与处理后统计形成质量对比；先划分并仅在训练集拟合，形成冻结模型输入。\n"
        assert not manuscript_data_preparation_issues(root, manuscript)
        hollow_manuscript = "# 模型准备\n来源、缺失值、处理前统计、处理后统计、先划分、冻结模型输入。\n## 数据预处理\n仅作标题。\n"
        assert manuscript_data_preparation_issues(root, hollow_manuscript)

        state = {"data_preparation": {"status": "completed", "detected_files": ["用户数据/observations.csv"]}}
        refresh_data_preparation_state(root, state)
        assert state["data_preparation"]["status"] == "completed"
        assert state["data_preparation"]["mode"] == "supplied"
        write(root / "问题分析.md", "数据模式: collected\n数据预处理计划与冻结模型输入\n")
        refresh_data_preparation_state(root, state)
        assert state["data_preparation"]["mode"] == "collected"
        write(root / "用户数据" / "additional.csv", "z\n1\n")
        refresh_data_preparation_state(root, state)
        assert state["data_preparation"]["status"] == "pending"

    with tempfile.TemporaryDirectory(prefix="metalab-no-data-") as temp:
        root = Path(temp)
        write(root / "问题分析.md", "数据模式: none\n预处理: skipped\n本题无附件数据。\n")
        expect_ok(root)
        write(root / "问题分析.md", "数据探索尚未确定。\n")
        expect_issue(root, "explicit preprocessing waiver")

    print("data preparation smoke passed")


if __name__ == "__main__":
    main()
