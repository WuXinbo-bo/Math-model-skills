from __future__ import annotations

import argparse
import re
from pathlib import Path


START = "% META_QUESTION_INPUTS_START"
END = "% META_QUESTION_INPUTS_END"
CN_NUMBERS = {char: index + 1 for index, char in enumerate("一二三四五六七八九十")}


def declared_problem_count(text: str) -> int:
    match = re.search(r"本赛题共\s*(\d+)\s*个子问题", text)
    if match:
        return int(match.group(1))
    numbers = [int(item) for item in re.findall(r"(?mi)^##+\s*(?:问题|Problem)\s*(\d+)", text)]
    numbers.extend(CN_NUMBERS[item] for item in re.findall(r"(?mi)^##+\s*问题\s*([一二三四五六七八九十])", text))
    return max(numbers, default=0)


def expected_problem_count(workspace: Path) -> int:
    counts = []
    for name in ("问题分析.md", "建模报告.md"):
        path = workspace / name
        if path.exists():
            counts.append(declared_problem_count(path.read_text(encoding="utf-8", errors="replace")))
    return max(counts, default=0)


def section_name(index: int) -> str:
    return {1: "5_problem1", 2: "6_problem2", 3: "7_problem3"}.get(index, f"problem{index}")


def section_template(index: int) -> str:
    return f"""\\section{{问题{index}的建模与求解}}
\\subsection{{问题角色与继承关系}}
[说明本问在整篇研究链中的作用、继承的机制以及相对前问的真实增量。]
\\subsection{{变量、机制与数学表达}}
[按机制引入、编号公式、符号与单位、公式作用的顺序建立本问数学关系。]
\\subsection{{求解方法与结果证据}}
[从发布声明账本提取真实结果，给出图表、约束回代和机制解释。]
\\subsection{{差异化验证与本问小结}}
[验证本问新增机制，报告适用边界、失败情形和可执行结论。]
"""


def sync(workspace: Path, expected: int = 0) -> list[Path]:
    main_path = workspace / "论文" / "论文正文.tex"
    if not main_path.exists():
        raise FileNotFoundError(f"missing manuscript source: {main_path}")
    main = main_path.read_text(encoding="utf-8")
    if START not in main or END not in main:
        raise ValueError("manuscript lacks META_QUESTION_INPUTS markers; copy the v1.3 CUMCM template first")
    expected = expected or expected_problem_count(workspace)
    if expected < 1:
        raise ValueError("cannot infer problem count; declare it in 问题分析.md or pass --count")
    directory = "章节" if re.search(r"\\input\{章节/", main) else "sections"
    section_dir = workspace / "论文" / directory
    section_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    inputs: list[str] = []
    for index in range(1, expected + 1):
        stem = section_name(index)
        path = section_dir / f"{stem}.tex"
        if not path.exists():
            path.write_text(section_template(index), encoding="utf-8")
            created.append(path)
        inputs.append(f"\\input{{{directory}/{stem}}}")
    replacement = START + "\n" + "\n".join(inputs) + "\n" + END
    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        lambda _match: replacement,
        main,
        flags=re.DOTALL,
    )
    main_path.write_text(updated, encoding="utf-8")
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize CUMCM question sections with the actual problem count.")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--count", type=int, default=0)
    args = parser.parse_args()
    created = sync(Path(args.workspace).resolve(), args.count)
    print(f"question sections synchronized; created={len(created)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
