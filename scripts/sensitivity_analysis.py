#!/usr/bin/env python3
"""
Sensitivity Analysis Engine — 嵌入式灵敏度检验工具 (M3)

为每个子问题执行参数扫描 (Parameter Sweep)，生成稳健性证据。

设计原则:
  - 纯工具脚本，不调用 LLM API
  - 读取模型代码中的参数，自动执行 ±10/20/50% 扫描
  - 输出结构化 JSON 结果 + Markdown 报告
  - 供 main.py CLI 调用

用法:
  python sensitivity_analysis.py init --subquestion Q1 --model-file model.py
  python sensitivity_analysis.py sweep --subquestion Q1 [--pct "10,20,50"]
  python sensitivity_analysis.py check --subquestion Q1
  python sensitivity_analysis.py report --subquestion Q1
"""

import argparse
import json
import math
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace

WORKSPACE = resolve_workspace()
SENSITIVITY_DIR = WORKSPACE / "sensitivity"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ═══════════════════════════════════════════════════════════════
# Parameter Extraction
# ═══════════════════════════════════════════════════════════════

def extract_params_from_code(code: str) -> list:
    """从模型代码中提取关键参数。

    识别模式:
      - 赋值语句: param_name = 数值
      - 函数参数默认值
      - numpy/linspace/arange 中的参数

    Returns:
        [{"name": str, "value": float, "line": int, "source": str}]
    """
    params = []
    seen = set()

    # Pattern 1: Simple assignment  param = value
    for m in re.finditer(r'^(\w+)\s*=\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)', code, re.MULTILINE):
        name = m.group(1)
        val = float(m.group(2))
        line_num = code[:m.start()].count('\n') + 1
        if name not in seen and not name.startswith('_') and name not in (
            'i', 'j', 'k', 'n', 'x', 'y', 't', 'df', 'np', 'pd', 'plt',
            'True', 'False', 'None', 'print', 'range', 'len', 'list', 'dict',
        ):
            seen.add(name)
            params.append({
                "name": name,
                "value": val,
                "line": line_num,
                "source": m.group(0).strip(),
            })

    # Pattern 2: np.linspace/arange bounds
    for m in re.finditer(
        r'(?:linspace|arange)\s*\(\s*([+-]?\d+\.?\d*)\s*,\s*([+-]?\d+\.?\d*)',
        code,
    ):
        for idx, val in enumerate([float(m.group(1)), float(m.group(2))]):
            name = f"_bound_{idx}"
            if name not in seen:
                seen.add(name)
                params.append({
                    "name": name,
                    "value": val,
                    "line": code[:m.start()].count('\n') + 1,
                    "source": m.group(0).strip(),
                })

    return params


def load_params_from_file(params_file: Path) -> list:
    """从 JSON 文件加载手动指定的参数列表。

    格式:
    [
      {"name": "alpha", "value": 0.5, "description": "扩散系数"},
      {"name": "beta", "value": 1.2, "description": "衰减率"}
    ]
    """
    if not params_file.exists():
        return []
    data = json.loads(params_file.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


# ═══════════════════════════════════════════════════════════════
# Parameter Sweep Engine
# ═══════════════════════════════════════════════════════════════

def run_sweep(model_code: str, params: list, pcts: list = None) -> dict:
    """执行参数扫描。

    对每个参数，应用 ±pct% 变化，重新执行模型代码，捕获输出变化。

    Args:
        model_code: 模型 Python 代码
        params: 参数列表
        pcts: 扫描百分比列表，默认 [10, 20, 50]

    Returns:
        {
            "parameters": [...],
            "sweep_results": [...],
            "robustness_verdict": str,
            "sensitivity_score": float,
        }
    """
    if pcts is None:
        pcts = [10, 20, 50]

    sweep_results = []
    sensitivity_scores = []

    for param in params:
        param_name = param["name"]
        base_value = param["value"]

        if base_value == 0:
            # 无法对 0 值做百分比扫描，改用 ±1, ±5, ±10 绝对值
            abs_deltas = [1, 5, 10]
            deltas = [(-d, base_value - d) for d in abs_deltas] + [(d, base_value + d) for d in abs_deltas]
        else:
            deltas = []
            for pct in pcts:
                delta = base_value * pct / 100
                deltas.append((-pct, base_value - delta))
                deltas.append((+pct, base_value + delta))

        param_result = {
            "param_name": param_name,
            "base_value": base_value,
            "sweep_points": [],
        }

        # 执行基准
        base_output = _execute_with_param(model_code, param_name, base_value)

        for pct_label, new_value in deltas:
            modified_output = _execute_with_param(model_code, param_name, new_value)

            # 计算输出变化率
            if base_output["success"] and modified_output["success"]:
                change_ratio = _compute_change_ratio(base_output, modified_output)
                stable = abs(change_ratio) < 0.3  # 30% 以内视为稳定
            else:
                change_ratio = None
                stable = False

            param_result["sweep_points"].append({
                "pct_change": f"{pct_label:+g}%" if isinstance(pct_label, (int, float)) else str(pct_label),
                "param_value": new_value,
                "output": modified_output.get("output_summary", ""),
                "change_ratio": change_ratio,
                "stable": stable,
                "error": modified_output.get("error"),
            })

        # 计算该参数的敏感性得分
        ratios = [p["change_ratio"] for p in param_result["sweep_points"] if p["change_ratio"] is not None]
        avg_sensitivity = sum(abs(r) for r in ratios) / len(ratios) if ratios else 1.0
        param_result["avg_sensitivity"] = avg_sensitivity
        sensitivity_scores.append(avg_sensitivity)

        sweep_results.append(param_result)

    # 综合稳健性判定
    avg_all = sum(sensitivity_scores) / len(sensitivity_scores) if sensitivity_scores else 1.0
    if avg_all < 0.1:
        verdict = "ROBUST — 模型对参数变化高度稳定"
    elif avg_all < 0.3:
        verdict = "MODERATE — 模型对部分参数敏感，建议关注"
    elif avg_all < 0.5:
        verdict = "SENSITIVE — 模型对参数较敏感，需要详细讨论"
    else:
        verdict = "FRAGILE — 模型对参数高度敏感，需要替代方案或约束"

    return {
        "parameters": params,
        "sweep_results": sweep_results,
        "robustness_verdict": verdict,
        "sensitivity_score": round(avg_all, 4),
        "pcts_scanned": pcts,
        "timestamp": now(),
    }


def _execute_with_param(model_code: str, param_name: str, param_value: float) -> dict:
    """在隔离环境中执行模型代码，替换指定参数值。

    安全限制:
      - 禁止 import os/subprocess/sys
      - 禁止文件操作
      - 超时 10 秒
    """
    # 安全检查
    blacklist = ['import os', 'import subprocess', 'import sys', 'exec(', 'eval(',
                 '__import__', 'open(', 'os.', 'subprocess.', 'shutil.', 'pathlib.']
    for bl in blacklist:
        if bl in model_code:
            return {"success": False, "error": f"Security: blacklisted pattern '{bl}'"}

    # 构建执行代码
    safe_code = model_code.replace("\r\n", "\n")

    # 注入参数覆盖
    inject = f"\n# --- sensitivity sweep override ---\n{param_name} = {param_value}\n"

    full_code = safe_code + inject

    try:
        import threading
        result = {"output": None, "success": False, "error": None}

        def _run():
            try:
                exec_globals = {"__builtins__": _safe_builtins()}
                exec(compile(full_code, "<sensitivity_sweep>", "exec"), exec_globals)
                # 提取输出
                output_val = exec_globals.get("_output", exec_globals.get("result", exec_globals.get("output", None)))
                result["output"] = output_val
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=10)

        if t.is_alive():
            return {"success": False, "error": "Timeout (10s) exceeded"}

        if result["success"] and result["output"] is not None:
            return {
                "success": True,
                "output_summary": str(result["output"])[:200],
                "output_value": _to_float(result["output"]),
            }
        elif result["success"]:
            return {"success": True, "output_summary": "(no output captured)", "output_value": None}
        else:
            return {"success": False, "error": result["error"]}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _safe_builtins():
    """受限 builtins 白名单。"""
    import builtins
    safe = {}
    allowed = (
        'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'filter', 'float',
        'frozenset', 'hash', 'int', 'isinstance', 'issubclass', 'len', 'list',
        'map', 'max', 'min', 'next', 'print', 'range', 'round', 'set', 'sorted',
        'str', 'sum', 'tuple', 'type', 'zip', 'zip_longest',
        'True', 'False', 'None',
    )
    for name in allowed:
        if hasattr(builtins, name):
            safe[name] = getattr(builtins, name)
    # 允许 numpy/math 常用函数
    try:
        import numpy as np
        safe['np'] = np
    except ImportError:
        pass
    try:
        import math
        safe['math'] = math
    except ImportError:
        pass
    return safe


def _to_float(val) -> float:
    """尝试将输出转为 float。"""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, (list, tuple)) and len(val) > 0:
        return _to_float(val[0])
    if isinstance(val, dict):
        for v in val.values():
            return _to_float(v)
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _compute_change_ratio(base: dict, modified: dict) -> float:
    """计算基准输出与修改后输出的变化率。"""
    b = base.get("output_value")
    m = modified.get("output_value")
    if b is None or m is None:
        return None
    if b == 0:
        return float('inf') if m != 0 else 0.0
    return (m - b) / abs(b)


# ═══════════════════════════════════════════════════════════════
# CLI Commands
# ═══════════════════════════════════════════════════════════════

def cmd_init(args):
    """初始化灵敏度分析配置。"""
    sq = args.subquestion
    sq_dir = SENSITIVITY_DIR / sq
    sq_dir.mkdir(parents=True, exist_ok=True)

    # 如果指定了模型文件，提取参数
    params = []
    if args.model_file:
        model_path = Path(args.model_file)
        if model_path.exists():
            code = model_path.read_text(encoding="utf-8")
            params = extract_params_from_code(code)
            print(f"[sensitivity] Extracted {len(params)} parameters from {model_path}")
        else:
            print(f"[sensitivity] Model file not found: {model_path}")

    # 保存配置
    config = {
        "subquestion": sq,
        "model_file": str(args.model_file) if args.model_file else None,
        "params": params,
        "pcts": [10, 20, 50],
        "created_at": now(),
    }
    config_path = sq_dir / "sensitivity_config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    # 生成参数模板（如果需要手动补充）
    if not params:
        template = [
            {"name": "param1", "value": 1.0, "description": "参数描述1"},
            {"name": "param2", "value": 0.5, "description": "参数描述2"},
        ]
        template_path = sq_dir / "params_template.json"
        template_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[sensitivity] No auto-extracted params. Template saved to {template_path}")
        print("[sensitivity] Edit the template with your model's key parameters, then run 'sweep'.")
    else:
        for p in params:
            print(f"  {p['name']}: {p['value']} (line {p['line']})")

    print(f"[sensitivity] Config saved to {config_path}")


def cmd_sweep(args):
    """执行参数扫描。"""
    sq = args.subquestion
    sq_dir = SENSITIVITY_DIR / sq

    config_path = sq_dir / "sensitivity_config.json"
    if not config_path.exists():
        sys.exit(f"[sensitivity] Config not found for {sq}. Run 'init' first.")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    params = config.get("params", [])

    # 加载手动参数（如果有）
    manual_path = sq_dir / "params.json"
    if manual_path.exists():
        params = load_params_from_file(manual_path)

    # 从模板加载（如果存在）
    template_path = sq_dir / "params_template.json"
    if template_path.exists() and not params:
        params = load_params_from_file(template_path)

    if not params:
        sys.exit("[sensitivity] No parameters to sweep. Edit params.json or params_template.json.")

    # 解析百分比
    pcts = [10, 20, 50]
    if args.pct:
        pcts = [int(x.strip()) for x in args.pct.split(",")]

    # 加载模型代码
    model_code = ""
    model_file = config.get("model_file")
    if model_file and Path(model_file).exists():
        model_code = Path(model_file).read_text(encoding="utf-8")
    else:
        # 尝试在 src/ 目录下查找子问题对应代码
        src_dir = WORKSPACE / "src"
        candidates = list(src_dir.glob(f"*{sq.lower()}*.py")) + list(src_dir.glob(f"*{sq.upper()}*.py"))
        if candidates:
            model_code = candidates[0].read_text(encoding="utf-8")
            print(f"[sensitivity] Auto-detected model file: {candidates[0]}")
        else:
            sys.exit(f"[sensitivity] No model code found. Specify --model-file or place code in src/.")

    print(f"[sensitivity] Running sweep for {sq} with {len(params)} params, pcts={pcts}...")

    result = run_sweep(model_code, params, pcts)

    # 保存结果
    result_path = sq_dir / "sweep_results.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # 生成 Markdown 报告
    report = _generate_report(sq, result)
    report_path = sq_dir / "sensitivity_report.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"[sensitivity] Results saved to {result_path}")
    print(f"[sensitivity] Report saved to {report_path}")
    print(f"[sensitivity] Verdict: {result['robustness_verdict']}")
    print(f"[sensitivity] Sensitivity score: {result['sensitivity_score']}")

    return result


def cmd_check(args):
    """检查灵敏度分析是否完成。"""
    sq = args.subquestion
    sq_dir = SENSITIVITY_DIR / sq

    checks = {
        "config_exists": (sq_dir / "sensitivity_config.json").exists(),
        "results_exist": (sq_dir / "sweep_results.json").exists(),
        "report_exists": (sq_dir / "sensitivity_report.md").exists(),
        "has_params": False,
        "has_robustness_verdict": False,
        "all_params_swept": False,
    }

    if checks["results_exist"]:
        results = json.loads((sq_dir / "sweep_results.json").read_text(encoding="utf-8"))
        checks["has_params"] = len(results.get("sweep_results", [])) > 0
        checks["has_robustness_verdict"] = bool(results.get("robustness_verdict"))

        # 检查所有参数是否都已扫描
        sweep = results.get("sweep_results", [])
        if sweep:
            checks["all_params_swept"] = all(
                len(p.get("sweep_points", [])) > 0 for p in sweep
            )

    passed = all(checks.values())
    result = {
        "subquestion": sq,
        "checks": checks,
        "passed": passed,
        "timestamp": now(),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if passed else 1)


def cmd_report(args):
    """生成/显示灵敏度分析报告。"""
    sq = args.subquestion
    sq_dir = SENSITIVITY_DIR / sq

    report_path = sq_dir / "sensitivity_report.md"
    if report_path.exists():
        print(report_path.read_text(encoding="utf-8"))
    else:
        results_path = sq_dir / "sweep_results.json"
        if results_path.exists():
            results = json.loads(results_path.read_text(encoding="utf-8"))
            report = _generate_report(sq, results)
            report_path.write_text(report, encoding="utf-8")
            print(report)
        else:
            sys.exit(f"[sensitivity] No results found for {sq}. Run 'sweep' first.")


def _generate_report(sq: str, result: dict) -> str:
    """生成 Markdown 格式的灵敏度分析报告。"""
    lines = [
        f"# 灵敏度分析报告 — {sq}",
        f"",
        f"**生成时间:** {result.get('timestamp', now())}",
        f"**扫描百分比:** {result.get('pcts_scanned', [10, 20, 50])}",
        f"**综合稳健性判定:** {result.get('robustness_verdict', 'N/A')}",
        f"**综合敏感性得分:** {result.get('sensitivity_score', 'N/A')}",
        f"",
        f"## 参数扫描结果",
        f"",
    ]

    for param_result in result.get("sweep_results", []):
        name = param_result.get("param_name", "?")
        base = param_result.get("base_value", "?")
        avg = param_result.get("avg_sensitivity", 0)

        lines.append(f"### 参数: `{name}` (基准值: {base})")
        lines.append(f"")
        lines.append(f"| 扫描变化 | 参数值 | 输出 | 变化率 | 稳定 |")
        lines.append(f"|----------|--------|------|--------|------|")

        for point in param_result.get("sweep_points", []):
            pct = point.get("pct_change", "?")
            pv = point.get("param_value", "?")
            out = point.get("output", "N/A")
            cr = point.get("change_ratio")
            cr_str = f"{cr:.4f}" if cr is not None else "N/A"
            stable = "✅" if point.get("stable") else "❌"
            err = point.get("error")
            if err:
                out = f"ERROR: {err[:50]}"
            lines.append(f"| {pct} | {pv} | {out} | {cr_str} | {stable} |")

        lines.append(f"")
        lines.append(f"**平均敏感性:** {avg:.4f} {'(稳定)' if avg < 0.3 else '(敏感)' if avg < 0.5 else '(脆弱)'}")
        lines.append(f"")

    lines.append(f"## 结论")
    lines.append(f"")
    lines.append(f"{result.get('robustness_verdict', 'N/A')}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"*Generated by sensitivity_analysis.py (M3 — 嵌入式灵敏度检验)*")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description="Sensitivity Analysis Engine (M3)")
    sub = p.add_subparsers(dest="command")

    # init
    pi = sub.add_parser("init", help="初始化灵敏度分析配置")
    pi.add_argument("--subquestion", "-q", required=True, help="子问题编号 (e.g., Q1)")
    pi.add_argument("--model-file", "-m", help="模型 Python 文件路径")

    # sweep
    ps = sub.add_parser("sweep", help="执行参数扫描")
    ps.add_argument("--subquestion", "-q", required=True, help="子问题编号")
    ps.add_argument("--pct", help="扫描百分比，逗号分隔 (默认: 10,20,50)")

    # check
    pc = sub.add_parser("check", help="检查灵敏度分析是否完成")
    pc.add_argument("--subquestion", "-q", required=True, help="子问题编号")

    # report
    pr = sub.add_parser("report", help="生成/显示灵敏度分析报告")
    pr.add_argument("--subquestion", "-q", required=True, help="子问题编号")

    args = p.parse_args()
    dispatch = {
        "init": cmd_init,
        "sweep": cmd_sweep,
        "check": cmd_check,
        "report": cmd_report,
    }

    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
