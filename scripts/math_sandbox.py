#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Math Sandbox - 数学验证沙箱
=============================

安全执行 Python 代码验证数学推导。

四层安全防护：
1. 字符串黑名单：禁止危险关键词
2. AST 静态分析：检查代码结构
3. 受限 builtins + 安全 __import__：限制可用函数
4. 线程级强制超时：防止无限循环

Usage:
  python math_sandbox.py run --code-file script.py
  python math_sandbox.py run --code "print(1+1)"
  python math_sandbox.py verify --subquestion Q1
"""

import argparse
import ast
import builtins
import json
import os
import signal
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

WORKSPACE = Path("outputs")
SANDBOX_DIR = WORKSPACE / "sandbox"

# ═══════════════════════════════════════════════════════════════
# 安全配置
# ═══════════════════════════════════════════════════════════════

# 第一层：字符串黑名单
DANGEROUS_KEYWORDS = [
    "os.system", "os.popen", "os.exec",
    "subprocess", "subprocess.call", "subprocess.run", "subprocess.Popen",
    "shutil",
    "eval", "exec",
    "__import__",
    "importlib",
    "open",  # 仅允许只读模式，需特殊处理
    "pathlib", "pathlib.Path",  # 限制路径操作
    "requests", "urllib", "http",
    "socket", "telnetlib", "ftplib", "smtplib",
    "pickle", "shelve", "marshal",
    "ctypes", "cffi",
    "threading", "multiprocessing",  # 防止 fork bomb
    "signal",  # 防止信号劫持
    "sys.exit", "os._exit",
    "__builtins__",
    "__subclasses__",
    "__bases__",
    "__mro__",
    "getattr",  # 防止反射攻击
    "setattr",
    "delattr",
    "globals",
    "locals",
    "vars",
    "dir",
    "type",
    "compile",
]

# 允许的安全 import
SAFE_MODULES = [
    "numpy", "np",
    "scipy", "scipy.stats", "scipy.optimize", "scipy.integrate",
    "pandas", "pd",
    "math",
    "cmath",
    "fractions",
    "decimal",
    "statistics",
    "random",
    "itertools",
    "functools",
    "collections",
    "re",
    "json",
    "csv",
    "io",
    "string",
    "textwrap",
    "copy",
    "pprint",
    "unittest.mock",
    "datetime",
    "time",
    "calendar",
    "enum",
    "dataclasses",
    "typing",
    "abc",
    "contextlib",
    "operator",
]

# 第二层：AST 黑名单节点类型
AST_BLACKLIST = (
    ast.ImportFrom,
)

# 允许的 builtins 子集
SAFE_BUILTINS_KEYS = [
    "abs", "all", "any", "bool", "bytearray", "bytes", "callable",
    "chr", "complex", "dict", "dir", "divmod", "enumerate", "filter",
    "float", "format", "frozenset", "getattr", "globals", "hasattr",
    "hash", "help", "hex", "id", "input", "int", "isinstance",
    "issubclass", "iter", "len", "list", "locals", "map", "max",
    "memoryview", "min", "next", "object", "oct", "ord", "pow",
    "print", "property", "range", "repr", "reversed", "round",
    "set", "setattr", "slice", "sorted", "staticmethod", "str",
    "sum", "super", "tuple", "type", "vars", "zip",
    # 安全扩展
    "np", "numpy",
    "pd", "pandas",
    "math",
    "inf", "nan",
]


# ═══════════════════════════════════════════════════════════════
# 第一层：字符串黑名单检查
# ═══════════════════════════════════════════════════════════════

def check_string_blacklist(code):
    """
    检查代码中是否包含危险关键词

    Returns:
        (safe, message)
    """
    code_lower = code.lower()
    for keyword in DANGEROUS_KEYWORDS:
        if keyword.lower() in code_lower:
            return False, f"检测到危险关键词: {keyword}"
    return True, "字符串黑名单检查通过"


# ═══════════════════════════════════════════════════════════════
# 第二层：AST 静态分析
# ═══════════════════════════════════════════════════════════════

def check_ast_safety(code):
    """
    AST 静态分析，检查代码结构安全性

    Returns:
        (safe, message)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"语法错误: {e}"

    # 检查是否使用了受限的 import
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod not in SAFE_MODULES:
                    return False, f"不允许的模块导入: {alias.name}"

        if isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod not in SAFE_MODULES:
                return False, f"不允许的 from-import: {node.module}"

        # 禁止 eval/exec
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in ("eval", "exec", "compile"):
                return False, f"不允许的函数调用: {func.id}"

        # 禁止 __import__
        if isinstance(node, ast.Name) and node.id == "__import__":
            return False, "不允许的 __import__ 调用"

    return True, "AST 静态分析通过"


# ═══════════════════════════════════════════════════════════════
# 第三层：受限 builtins + 安全 __import__
# ═══════════════════════════════════════════════════════════════

def create_safe_globals():
    """创建受限的全局命名空间"""
    safe_builtins = {}
    for key in SAFE_BUILTINS_KEYS:
        if hasattr(builtins, key):
            safe_builtins[key] = getattr(builtins, key)

    # 安全的 __import__
    def safe_import(name, *args, **kwargs):
        mod = name.split(".")[0]
        if mod not in SAFE_MODULES:
            raise ImportError(f"沙箱禁止导入模块: {name}")
        return __builtins__["__import__"](name, *args, **kwargs)

    safe_builtins["__import__"] = safe_import

    # 安全的 open（只读模式）
    def safe_open(file, mode="r", *args, **kwargs):
        if mode not in ("r", "rt", "rb"):
            raise IOError(f"沙箱只允许只读模式打开文件，当前模式: {mode}")
        return __builtins__["open"](file, mode, *args, **kwargs)

    safe_builtins["open"] = safe_open

    # 预导入常用模块
    ns = {"__builtins__": safe_builtins}
    for mod_name in ["numpy", "math", "json", "csv", "statistics", "random", "fractions"]:
        try:
            ns[mod_name] = __builtins__["__import__"](mod_name)
        except ImportError:
            pass

    return ns


# ═══════════════════════════════════════════════════════════════
# 第四层：线程级强制超时
# ═══════════════════════════════════════════════════════════════

def run_with_timeout(
    code: str,
    timeout_seconds: int = 30,
    max_memory_mb: int = 512,
) -> dict:
    """
    在受限环境中执行代码，带超时和内存限制

    Args:
        code: 要执行的 Python 代码
        timeout_seconds: 超时秒数
        max_memory_mb: 最大内存 MB（仅记录，不强制限制）

    Returns:
        {
            "success": bool,
            "stdout": str,
            "stderr": str,
            "result": Any,
            "execution_time_ms": float,
            "timed_out": bool,
        }
    """
    import io
    import time
    import threading
    import resource

    result = {
        "success": False,
        "stdout": "",
        "stderr": "",
        "result": None,
        "execution_time_ms": 0,
        "timed_out": False,
    }

    safe_globals = create_safe_globals()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    captured_out = io.StringIO()
    captured_err = io.StringIO()

    stop_event = threading.Event()

    def _worker():
        try:
            sys.stdout = captured_out
            sys.stderr = captured_err

            compiled = compile(code, "<sandbox>", "exec")
            exec(compiled, safe_globals)

            result["success"] = True
            # 尝试获取最后一个表达式的结果
            if "__result__" in safe_globals:
                result["result"] = safe_globals["__result__"]
        except Exception as e:
            result["stderr"] = traceback.format_exc()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            stop_event.set()

    worker = threading.Thread(target=_worker, daemon=True)
    start_time = time.monotonic()
    worker.start()
    worker.join(timeout=timeout_seconds)

    elapsed_ms = (time.monotonic() - start_time) * 1000
    result["execution_time_ms"] = round(elapsed_ms, 2)
    result["stdout"] = captured_out.getvalue()
    result["stderr"] = captured_err.getvalue()

    if worker.is_alive():
        result["timed_out"] = True
        result["stderr"] = f"执行超时 ({timeout_seconds}s)\n" + result["stderr"]

    return result


# ═══════════════════════════════════════════════════════════════
# 沙箱验证
# ═══════════════════════════════════════════════════════════════

def verify_code(code: str, timeout: int = 30) -> dict:
    """
    完整的代码安全验证流程

    Returns:
        完整验证结果
    """
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    verification = {
        "timestamp": datetime.now().isoformat(),
        "code_length": len(code),
        "checks": {},
        "execution": None,
    }

    # 第一层
    safe1, msg1 = check_string_blacklist(code)
    verification["checks"]["string_blacklist"] = {"passed": safe1, "message": msg1}

    # 第二层
    safe2, msg2 = check_ast_safety(code)
    verification["checks"]["ast_analysis"] = {"passed": safe2, "message": msg2}

    # 如果前两层未通过，不执行
    if not safe1 or not safe2:
        verification["execution"] = {
            "success": False,
            "stdout": "",
            "stderr": f"安全检查未通过，跳过执行\n  - {msg1}\n  - {msg2}",
            "timed_out": False,
        }
        return verification

    # 第三+四层：实际执行
    exec_result = run_with_timeout(code, timeout_seconds=timeout)
    verification["execution"] = exec_result

    return verification


def verify_subquestion(subquestion):
    """
    验证子问题的代码文件

    Returns:
        (passed, message)
    """
    sandbox_dir = WORKSPACE / "models" / subquestion
    if not sandbox_dir.exists():
        # 回退到 src/q{N}/ 目录
        q_num = subquestion.lower().replace("q", "")
        sandbox_dir = WORKSPACE.parent / "src" / f"q{q_num}"
        if not sandbox_dir.exists():
            return False, f"模型目录不存在: outputs/models/{subquestion} 或 src/q{q_num}/"

    code_files = list(sandbox_dir.glob("*.py"))
    if not code_files:
        return False, f"未找到 Python 代码文件: {sandbox_dir}"

    all_passed = True
    results = []

    for cf in code_files:
        code = cf.read_text(encoding="utf-8")
        v = verify_code(code)
        passed = v["execution"]["success"] and not v["execution"]["timed_out"]
        results.append({
            "file": str(cf),
            "passed": passed,
            "checks": v["checks"],
        })
        if not passed:
            all_passed = False

    # 保存验证结果
    results_path = SANDBOX_DIR / f"{subquestion}_verification.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    if all_passed:
        return True, (
            f"数学沙箱验证通过\n"
            f"- 验证文件数: {len(code_files)}\n"
            f"- 全部通过\n"
            f"- 结果: {results_path}"
        )
    else:
        failed = [r["file"] for r in results if not r["passed"]]
        return False, (
            f"数学沙箱验证未通过\n"
            f"- 失败文件: {', '.join(failed)}\n"
            f"- 详细结果: {results_path}"
        )


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Math Sandbox - 数学验证沙箱")
    sub = parser.add_subparsers(dest="command", help="子命令")

    p_run = sub.add_parser("run", help="执行代码")
    p_run.add_argument("--code", help="要执行的 Python 代码")
    p_run.add_argument("--code-file", help="代码文件路径")
    p_run.add_argument("--timeout", type=int, default=30, help="超时秒数")

    p_verify = sub.add_parser("verify", help="验证子问题代码")
    p_verify.add_argument("--subquestion", required=True)

    args = parser.parse_args()

    if args.command == "run":
        if args.code_file:
            code = Path(args.code_file).read_text(encoding="utf-8")
        elif args.code:
            code = args.code
        else:
            print("❌ 请提供 --code 或 --code-file")
            sys.exit(1)

        result = verify_code(code, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["execution"]["success"] else 1)

    elif args.command == "verify":
        passed, msg = verify_subquestion(args.subquestion)
        print(msg)
        sys.exit(0 if passed else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()