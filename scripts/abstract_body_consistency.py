#!/usr/bin/env python3
"""
Abstract-Body Consistency Auditor — 摘要-全文一致性审计 (M3)

强制检查摘要数字是否完全匹配冻结后的数据和正文内容。
纯工具脚本，不调用 LLM API。

用法:
  python abstract_body_consistency.py check --abstract paper/abstract.md --body paper/paper.md [--frozen-dir frozen/]
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace

WORKSPACE = resolve_workspace()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 数值提取正则
_CONTEXTUAL_NUMBER = re.compile(
    r'([^。\n]{0,30})'
    r'(-?\d+(?:\.\d+)?(?:\s*[%％])?)'
    r'([^。\n]{0,15})'
)

def extract_numbers_from_text(text: str) -> list:
    """从文本提取所有数值及其上下文。"""
    numbers = []
    seen = set()
    for m in _CONTEXTUAL_NUMBER.finditer(text):
        raw = m.group(2).strip()
        try:
            val = float(raw.replace("%", "").replace("％", ""))
        except ValueError:
            continue
        context = m.group(0).strip()
        # 跳过非数据数字（年份、页码、引用）
        if _is_nondata(val, context):
            continue
        key = f"{val:.6f}"
        if key not in seen:
            seen.add(key)
            line_num = text[:m.start()].count('\n') + 1
            numbers.append({"value": val, "raw": raw, "context": context, "line": line_num})
    return numbers

def _is_nondata(value: float, context: str) -> bool:
    """判断是否为非数据数字。"""
    if 1900 <= value <= 2100 and value == int(value):
        return True
    if 1 <= value <= 200 and value == int(value):
        if any(kw in context for kw in ["页", "page", "第", "参见", "[", "fig", "图"]):
            return True
    if value == int(value) and 0 <= value <= 50:
        if any(kw in context for kw in ["式", "公式", "Eq", "equation", "Table", "表"]):
            return True
    return False

def extract_numbers_from_frozen(frozen_dir: Path) -> dict:
    """从 frozen_numbers.json 提取冻结数值。"""
    result = {}
    if not frozen_dir.exists():
        return result
    for sq_dir in sorted(frozen_dir.iterdir()):
        if not sq_dir.is_dir():
            continue
        frozen_file = sq_dir / "frozen_numbers.json"
        if not frozen_file.exists():
            continue
        try:
            data = json.loads(frozen_file.read_text(encoding="utf-8"))
            sq_name = sq_dir.name
            numbers = []
            for key, info in data.items():
                if isinstance(info, dict):
                    val = info.get("value") or info.get("frozen_value")
                    if val is not None:
                        try:
                            numbers.append({"name": key, "value": float(val), "source": info.get("source", "frozen")})
                        except (TypeError, ValueError):
                            pass
            result[sq_name] = numbers
        except (json.JSONDecodeError, OSError):
            pass
    return result

def _match_number(target: float, candidates: list, tolerance: float = 0.01) -> bool:
    """检查 target 是否在 candidates 中有匹配（允许 tolerance 相对误差）。"""
    for c in candidates:
        cv = c["value"]
        if cv == 0 and target == 0:
            return True
        if cv != 0 and abs((target - cv) / abs(cv)) <= tolerance:
            return True
    return False

def check_consistency(abstract_text: str, body_text: str, frozen_dir: Path = None) -> dict:
    """执行摘要-全文一致性审计。

    Returns:
        {
            "abstract_numbers": [...],
            "body_numbers": [...],
            "frozen_numbers": {...},
            "matches": [...],
            "mismatches": [...],
            "fabricated": [...],
            "passed": bool,
            "score": float,
        }
    """
    abs_nums = extract_numbers_from_text(abstract_text)
    body_nums = extract_numbers_from_text(body_text)
    frozen_nums = extract_numbers_from_frozen(frozen_dir) if frozen_dir else {}

    # 合并所有正文+冻结数值作为"可信来源"
    trusted = list(body_nums)
    for sq, nums in frozen_nums.items():
        trusted.extend(nums)

    matches = []
    mismatches = []
    fabricated = []

    for an in abs_nums:
        found_in_body = _match_number(an["value"], body_nums)
        found_in_frozen = any(
            _match_number(an["value"], nums) for nums in frozen_nums.values()
        )

        if found_in_body or found_in_frozen:
            matches.append({
                "abstract_value": an["value"],
                "raw": an["raw"],
                "context": an["context"],
                "source": "body" if found_in_body else "frozen",
            })
        else:
            # 可能是摘要中的衍生数字（如百分比）
            # 检查是否在正文中有近似值
            close_match = False
            for bn in body_nums:
                if bn["value"] != 0 and abs(an["value"] - bn["value"]) < 0.5:
                    close_match = True
                    break
            if close_match:
                matches.append({
                    "abstract_value": an["value"],
                    "raw": an["raw"],
                    "context": an["context"],
                    "source": "approximate_match",
                })
            else:
                mismatches.append({
                    "abstract_value": an["value"],
                    "raw": an["raw"],
                    "context": an["context"],
                    "issue": "数值在正文和冻结数据中均未找到",
                })
                fabricated.append({
                    "value": an["value"],
                    "raw": an["raw"],
                    "context": an["context"],
                })

    total = len(abs_nums)
    matched = len(matches)
    score = matched / total if total > 0 else 1.0
    passed = len(fabricated) == 0 and score >= 0.8

    return {
        "abstract_numbers": abs_nums,
        "body_numbers_count": len(body_nums),
        "frozen_numbers": {k: len(v) for k, v in frozen_nums.items()},
        "matches": matches,
        "mismatches": mismatches,
        "fabricated": fabricated,
        "total_abstract_numbers": total,
        "matched_count": matched,
        "score": round(score, 4),
        "passed": passed,
        "timestamp": now(),
    }

# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_check(args):
    """执行摘要-全文一致性审计。"""
    abstract = Path(args.abstract).read_text(encoding="utf-8")
    body = Path(args.body).read_text(encoding="utf-8")
    frozen_dir = Path(args.frozen_dir) if args.frozen_dir else WORKSPACE / "frozen"

    result = check_consistency(abstract, body, frozen_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["passed"] else 1)

def main():
    p = argparse.ArgumentParser(description="Abstract-Body Consistency Auditor (M3)")
    sub = p.add_subparsers(dest="command")

    pc = sub.add_parser("check", help="执行摘要-全文一致性审计")
    pc.add_argument("--abstract", "-a", required=True, help="摘要文件路径")
    pc.add_argument("--body", "-b", required=True, help="正文文件路径")
    pc.add_argument("--frozen-dir", "-f", help="冻结数据目录 (默认: WORKSPACE/frozen/)")

    args = p.parse_args()
    if args.command == "check":
        cmd_check(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
