---
name: computational-realization
description: "Meta-model-agent 将数学机制落地为可运行程序、数值实验、结果合同与可复核证据。适用于计算实验实现。"
---

# 计算实验工程实现

## 稳定执行契约

- **执行目标**：把建模报告中的每个子问题实现为可运行程序，并冻结真实计算结果与复核证据。
- **调用参数**：[modeling-report-or-topic]。
- **权威输入**：建模报告.md、问题分析.md、用户数据及已确认的参数。
- **允许交付**：程序/、计算结果.md、图表/全部结果.json、依赖清单.txt，以及必要的日志和状态记录。
- **禁止写入**：不得越权修改已冻结的上游事实、用户原始文件或本协议未授权的目录。
- **可用工具边界**：Bash(*), Read, Write, Edit, Grep, Glob, Agent。
- **最小交付**：逐问可执行程序、主程序.py、结果 JSON、运行记录、基线比较、稳定性检查与失败说明。
- **恢复入口**：优先读取当前工作、状态记录和已有产物，从最近一次通过门禁的位置继续。
- **失败回退**：执行失败时定位到数据、实现或模型层；只允许有证据的修复，模型根本失效时回退数学机制构造。
- **收口顺序**：先核对输入，再完成产物，再运行本环节门禁，最后登记状态；门禁未通过不得宣告完成。

依据建模报告编写代码并实施计算：**$ARGUMENTS**

## ⛔⛔⛔ 工作项规模警示（先读这段, 再读后面全部内容）

**这不是简单工作项。** 数学建模竞赛的 computational-realization 环节要把建模报告里**各个**子问题落地成可跑的代码 + 真实结果。

子问题数量由 建模报告.md 决定（一问也可能, 多问也可能）, 不是固定的。

⛔ **判定你是否真的做完了**, 在 `end_turn` 此前自问：

1. 建模报告.md 里有几问？你是不是真的为每问都写了独立的 .py？

2. `图表/` 下是不是每问都有相应的 `问题_*_结果.json` 且文件非空？

3. 计算结果.md 是不是已经出现, 涵盖每问的方法和数值结果？

4. 跑过完成铁律最后那段 bash 校验脚本了吗？

**任何一项答 "否" → 避免 `end_turn`, 继续干活。** 引擎会反复检测这些产物, 没产出会自动化重新拉你回来重做, 与其被动重做不如一次做完。

⛔ **避免用 "我已经做了重点工作, 剩下的晚点再说" 的心态退出**。

"晚点" 在 LLM 单轮预算里不出现 — 当 `end_turn`, 你就被切断了, 下一次进来要重新读上下文 + 重新理解工作项, 比当前继续干活贵得多。

## 输入

1. **建模报告.md** — 建模报告（务必出现）

2. **问题分析.md** — 问题情境解构报告

3. **选题规划.md** — 选题规划（统计建模，含图形与表格预规划）

4. **用户数据/** — 赛题附件数据

## ⛔⛔⛔ 完成铁律（最高优先级，违反则当前环节失败）

**当前环节务必产出 `计算结果.md`（≥ 1KB）+ `程序/主程序.py`（≥ 500 字节）+ 不少于 1 个 `图表/*.json`**。

⛔ **结束前必跑产出校验**：

```bash

PASS=true

[ -f 计算结果.md ] && SZ=$(wc -c < 计算结果.md) || SZ=0

[ "$SZ" -ge 1024 ] && echo "✅ 计算结果.md ($SZ)" || { echo "❌ 计算结果.md 缺失或过小"; PASS=false; }

[ -f 程序/主程序.py ] && CSZ=$(wc -c < 程序/主程序.py) || CSZ=0

[ "$CSZ" -ge 500 ] && echo "✅ 程序/主程序.py ($CSZ)" || { echo "❌ 程序/主程序.py 缺失"; PASS=false; }

JSON_COUNT=$(ls 图表/*.json 2>/dev/null | wc -l)

[ "$JSON_COUNT" -ge 1 ] && echo "✅ 图表/*.json ($JSON_COUNT)" || { echo "❌ 图表/*.json 缺失"; PASS=false; }

# 子问题数对照: 建模报告里有几问, 程序/ 和 图表/ 就要有几份对应产出

EXPECTED_PROBS=$(grep -cE '^##\s*问题[一二三四五六七八九十0-9]|^###\s*问题[一二三四五六七八九十0-9]|^##\s*Problem\s*[0-9]' 建模报告.md 2>/dev/null || echo 0)

ACTUAL_CODE=$(ls 程序/problem*.py 2>/dev/null | wc -l)

ACTUAL_JSON=$(ls 图表/问题_*_结果.json 2>/dev/null | wc -l)

[ "$EXPECTED_PROBS" -gt 0 ] && {

  [ "$ACTUAL_CODE" -ge "$EXPECTED_PROBS" ] || { echo "❌ 建模报告 $EXPECTED_PROBS 问, 但只有 $ACTUAL_CODE 个 problem*.py"; PASS=false; }

  [ "$ACTUAL_JSON" -ge "$EXPECTED_PROBS" ] || { echo "❌ 建模报告 $EXPECTED_PROBS 问, 但只有 $ACTUAL_JSON 个 问题_*_结果.json"; PASS=false; }

}

[ "$PASS" != true ] && echo "⛔ 产出验证失败 — 必须补全所有缺失项后重新跑验证, 禁止 end_turn 结束本步骤"

```

## 工作过程

### 工作节点 0：恢复核验

核验 `计算结果.md`、`程序/*.py`、`图表/*_结果.json` 是否已出现：

- 计算结果.md 完整（>1KB）-> 跳到结果校验

- 程序/*.py 出现但无 计算结果.md -> 直接运行已有代码

- 什么都没有 -> 从头启动

### 工作节点 1：查阅建模报告 + 建立实现清单 + 防错复核

从 建模报告.md 提取各个子问题的求解算法、数学公式、输入交付标准、所需 Python 库。

**⛔ 防错复核（必做）：** 查阅 `references/error_prevention_code.md`，依据 建模报告.md 末尾标注的题型，对照相应章节的"务必校验"和"常见 Bug"条目。编码过程中按项核验。

**⛔ MANDATORY: 交付实现清单，后续逐项打勾：**

```

IMPLEMENTATION CHECKLIST (from 建模报告.md):

[ ] 问题1: [算法名] — 输入: [xxx], 输出: [yyy], 库: [zzz]

[ ] 问题2: [算法名] — 输入: [xxx], 输出: [yyy], 库: [zzz]

[ ] 问题3: [算法名] — 输入: [xxx], 输出: [yyy], 库: [zzz]

[ ] 灵敏度分析: [参数列表]

```

每完成一个子问题，更新清单运行状态。

### 工作节点 1.5：提取图形与表格预规划

**⛔ MANDATORY: 查阅规划文档的图形与表格预规划，了解下一步 evidence-visualization 需产出哪些图形与表格。**

computational-realization 不产出 PDF 图形与表格，但需保证交付的 JSON 数据能支撑这些图形与表格。

```bash

echo "=== 图表预规划 ==="

for plan in 选题规划.md 问题分析.md 建模报告.md; do

    [ -f "$plan" ] || continue

    echo "--- $plan ---"

    grep -i 'fig_\|图表\|TABLE_\|TikZ\|预规划\|figure' "$plan" | head -30

done

```

登记规划中的图形与表格清单，保证各个图形与表格相应的数据都会在分析过程中交付到 JSON。

**⛔ 图形与表格语言准则：** 中文论文（统计建模/数模竞赛）的图形与表格 axis label、legend、annotation 务必用中文。举例而言 `ax.set_xlabel('迭代次数')` 而不是 `ax.set_xlabel('Iterations')`。但这是 evidence-visualization 的事——computational-realization 只需保证 JSON 数据的 key 名有意义即可。

### 工作节点 2：环境准备

核验 Python，安装必要库（numpy, pandas, scipy, matplotlib, scikit-learn, statsmodels, networkx）。

### 工作节点 2.5：数据查阅校验（有附件数据时必做）

**⛔ 写任何求解代码此前，先写一个独立的数据校验脚本，确认数据查阅无误：**

```python

# 程序/data_verify.py — 数据读取验证（先跑这个，再写求解代码）

import pandas as pd

import os, glob

data_files = glob.glob('用户数据/*.csv') + glob.glob('用户数据/*.xlsx') + glob.glob('用户数据/*.xls')

print(f"找到 {len(data_files)} 个数据文件")

for f in data_files:

    print(f"\n=== {os.path.basename(f)} ===")

    try:

        if f.endswith('.csv'):

            # 尝试多种编码

            for enc in ['utf-8', 'gbk', 'gb2312', 'latin-1']:

                try:

                    df = pd.read_csv(f, encoding=enc)

                    print(f"  编码: {enc}")

                    break

                except UnicodeDecodeError:

                    continue

        else:

            df = pd.read_excel(f)

        print(f"  形状: {df.shape}")

        print(f"  列名: {list(df.columns)}")

        print(f"  数据类型:\n{df.dtypes}")

        print(f"  缺失值:\n{df.isnull().sum()[df.isnull().sum() > 0]}")

        print(f"  前3行:\n{df.head(3)}")

        # 数值列的基本统计

        num_cols = df.select_dtypes(include='number').columns

        if len(num_cols) > 0:

            print(f"  数值统计:\n{df[num_cols].describe()}")

            # 检查异常值

            for col in num_cols:

                if df[col].min() < 0 and '价格' in col or '数量' in col or '距离' in col:

                    print(f"  ⚠ {col} 有负值（{df[col].min()}），检查是否合理")

                if df[col].isnull().sum() > len(df) * 0.5:

                    print(f"  ⚠ {col} 缺失率 > 50%")

    except Exception as e:

        print(f"  ❌ 读取失败: {e}")

```

**实施 data_verify.py 后，确认以下几点再继续：**

1. 全部数据文件都能无误查阅（编码、分隔符无误）

2. 列名和题目描述保持一致（不是乱码或错位）

3. 数据规模和题目描述保持一致（行数、列数）

4. 缺失值和异常值已识别，后续代码中有处理方案

### 工作节点 3：代码目录结构

```

程序/

  main.py          # 主程序（串联所有子问题）

  problem1.py      # 子问题 1

  problem2.py      # 子问题 2

  通用工具.py         # 公共工具

  依赖清单.txt

```

### 工作节点 3.0：⛔⛔⛔ 模块导入铁律（违反必失败）

**问题本质：** 程序/ 下的脚本互相 `import` 时，从不同目录调用会导致 sys.path 不涵盖 `程序/`，

报 `ModuleNotFoundError: No module named 'utils'` / `'problem1'` 等。这是历史上最高频的失败缘由。

**⛔ 准则 1：各个 .py 文件顶部务必有自举 import 头（在全部 import 此前）：**

```python

# ⛔ 自举模块路径（让 sibling import 不依赖调用方式）

import os, sys

_HERE = os.path.dirname(os.path.abspath(__file__))

if _HERE not in sys.path:

    sys.path.insert(0, _HERE)

# 之后才能写其它 import

import numpy as np

import 通用工具 as u   # 现在 通用工具.py 跟当前文件同目录就一定能 import 到

```

**⛔ 准则 2：实施任何 程序/ 下的脚本务必 `cd code && python xxx.py`，禁止 `python 程序/xxx.py`**

```bash

# ✅ 正确（无论 utils 在不在都能跑）

cd code && python data_verify.py && cd ..

cd code && python problem1.py && cd ..

cd code && python main.py && cd ..

# ❌ 错误：sys.path 不含 程序/，sibling import 会爆 ModuleNotFoundError

python 程序/problem1.py

python -m code.problem1

```

**⛔ 准则 3：写入子问题脚本前先写 `程序/通用工具.py` 雏形（哪怕暂时为空），避免"先写 problem1 → import utils → utils 还没建立"的瞬时错。**

**⛔ 准则 4：跑代码务必用 `set -e` + 明示核验 exit code，不可在脚本失败后假装结果有效：**

```bash

cd code

set -e

python data_verify.py 2>&1 | tee ../临时文件/data_verify.log

python problem1.py 2>&1 | tee ../临时文件/problem1.log

[ -f ../图表/问题_1_结果.json ] || { echo "❌ problem1 未产出结果 JSON"; exit 1; }

cd ..

```

### 工作节点 4：逐子问题编写和实施

**务必按次序逐问求解：编写 -> 实施 -> 校验 -> 下一问。**

**⛔ Phase 4.0: 上游一致性核验（启动编码前必做）：**

```bash

echo "=== 上游一致性检查 ==="

# 检查 建模报告.md 是否存在

[ -f 建模报告.md ] && echo "✅ 建模报告.md 存在" || { echo "❌ 建模报告.md 不存在！"; exit 1; }

# 提取子问题数量

PROB_COUNT=$(grep -c '问题[一二三四五六七八九十0-9]' 问题分析.md 2>/dev/null || echo 0)

MODEL_COUNT=$(grep -c '问题[一二三四五六七八九十0-9]' 建模报告.md 2>/dev/null || echo 0)

echo "问题情境解构子问题数: $PROB_COUNT, 建模报告子问题数: $MODEL_COUNT"

[ "$MODEL_COUNT" -lt "$PROB_COUNT" ] && echo "⚠ 建模报告覆盖的子问题数少于问题情境解构，请检查是否遗漏"

# 提取建模报告推荐的方法

echo "--- 建模报告推荐方法 ---"

grep -i '算法\|方法\|模型.*选择\|求解.*策略' 建模报告.md 2>/dev/null | head -10

echo "--- 计算实验实现时必须使用上述方法，或明确说明替代理由 ---"

```

代码性能要求：

- 优先采用 numpy 向量化运算，避免 Python 原生 for 循环遍历大数据

- 数据量大（>1000 行）务必用向量化或矩阵运算

- 各个脚本实施前后打印进度信息

- 若代码跑超过 3 分钟，立即重写优化版本

自主判定数据来源：

- 有附件数据（`用户数据/*.csv` 出现）：从文件查阅

- 无附件数据（纯建模题）：依据 建模报告.md 自行构造参数

各个子问题：

1. 编写独立 Python 文件

2. 实施并核验交付

3. 校验结果合理性

4. 留存结果到 `图表/问题_N_结果.json`

5. 结果异常则调整代码重跑

---

### 工作节点 4.5：⛔⛔⛔ 每问跑完后的自检过程（关键，各个子问题都务必做）

**这是当前环节防失败的关键。每完成一问的代码 + JSON 后，务必按下面过程做自检，

满足要求才能转入下一问。** 避免写完全部问题再统一自检 — 那样发现问题要回头改, 浪费 turn 预算。

各个子问题跑完, 立即按以下次序 Read 自检文件并按其要求校验：

**第 1 步：必读（全部题型）**

```

Read references/checks/_index.md         # 自检总索引（仅第 1 问读, 后续可跳过）

Read references/checks/consistency.md    # 建模-代码契约 + 物理参数引用 + 自动化约束验证代码

Read references/checks/sanity_check.md   # 自动数值审查 + 9 问背景审查 + 编程 Bug 排查

```

**第 2 步：依据本问的题型选读 1 个分类自检文件**

| 本问类别 | Read 哪个 |

|---|---|

| 优化类（调度/选址/路线/分配/规划/求最优值）| `references/checks/optimization.md`（含 5 层求解 + 结构性校验）|

| 预测类（时间序列/回归/分类）| `references/checks/prediction.md` |

| 评价类（TOPSIS/AHP/熵权法/排名打分）| `references/checks/evaluation.md` |

| 物理/几何（碰撞检测/动力学/ODE/SAT 检测）| `references/checks/physical.md` |

| 统计/实证/图论 | `references/checks/sanity_check.md` 末尾的 S/G 区段已涵盖 |

**第 3 步：把自检结论写到 `临时文件/问题_N_复核.md`，每条 ✅/⚠️/❌**

**第 4 步：处理 ❌**

- 任何 ❌ → 修代码 → 重跑 → 重新自检

- 同一问最多修 3 轮，3 轮还不通过 → 在 计算结果.md 中标注"建模需修正"，继续下一问

**第 5 步：全部 ✅ 或最多 ⚠️ → 把本问的方法 + 关键结果写到 计算结果.md 相应章节，立即下一问**

⛔ **关键纪律**：

- 自检时**不可依赖记忆里的准则**，务必明示 Read 上面列出的 .md 文件 — 这是本拆分设计的目的

- 每问都要走完 Phase 4.5 才能启动下一问，避免跳过、避免合并、避免等到全部问都跑完再统一自检

### 工作节点 5：编写主程序

`程序/主程序.py` 串联全部子问题，汇总结果到 `图表/全部结果.json`。

### 工作节点 5.5：模型检验（依据题型自主判定）

依据题目类别，选取合适的模型检验方式。不是全部题都需灵敏度分析 — 自己判定：

- **优化类**（调度/选址/路线）→ 灵敏度分析：关键参数 ±20% 对目标函数的影响

- **预测类**（时间序列/回归）→ 交叉校验 + 残差分析 + 多模型对比

- **评价类**（TOPSIS/AHP/熵权法）→ 权重稳定性分析：微调权重看排名是否变化

- **图论/网络类** → 参数灵敏度（边权/容量变化对最优解的影响）

- **统计/实证类** → 稳健性检验（替换变量、子样本、工具变量）

若判定需灵敏度分析，实施下列环节：

Read 建模报告.md for the sensitivity analysis plan. For every key parameter identified:

1. Write `程序/sensitivity_analysis.py` that varies the parameter across a range (e.g., ±20% in 10 steps)

2. For every parameter value, re-run the model and record the objective function value

3. Save outcomes to `图表/灵敏度结果.json`:

```json

{

  "parameter_name": {"values": [...], "objective": [...]},

  "parameter_name2": {"values": [...], "objective": [...]}

}

```

4. Execute the script and validate outcomes are reasonable

This data is required by evidence-visualization to produce tornado charts and sensitivity curves, and by manuscript-synthesis for the 灵敏度分析 chapter.

### 工作节点 6：结果校验 + 实现清单对照

- 数值界限：概率在[0,1]、非负数、非 NaN/Inf

- 一致性：子问题间不矛盾

- 收敛性：优化器是否收敛

- 统计检验：R2在[0,1]、p值在[0,1]

**⛔ MANDATORY: 对照 Phase 1 的实现清单，逐项校验：**

```bash

echo "=== 实现清单对照 ==="

echo "检查每个子问题的结果文件是否存在且非空："

for f in 图表/问题_*_结果.json 图表/全部结果.json; do

    if [ -f "$f" ] && [ -s "$f" ]; then

        echo "  ✅ $f ($(wc -c < "$f") bytes)"

    else

        echo "  ❌ $f — MISSING or EMPTY"

    fi

done

# 灵敏度分析数据是软性要求(优化类必做, 其他题型可选)

if [ -f 图表/灵敏度结果.json ]; then

    echo "  ✅ 图表/灵敏度结果.json (灵敏度分析数据)"

elif [ -f 建模报告.md ] && grep -qE '灵敏度|sensitivity' 建模报告.md; then

    echo "  ⚠ 图表/灵敏度结果.json — 建模报告提到灵敏度但未产出, 优化类必须补"

fi

echo ""

echo "检查代码文件是否存在："

for f in 程序/*.py; do

    [ -f "$f" ] && echo "  ✅ $(basename $f)" || echo "  ❌ $(basename $f)"

done

```

**若有 ❌，务必回去补完再继续。** 尤其注意：

- `图表/全部结果.json` 务必出现（evidence-visualization 依赖它画图）

- 各个子问题的 `图表/问题_N_结果.json` 务必出现

- `图表/灵敏度结果.json` 仅当题目/建模报告涉及灵敏度分析时务必（优化类必做）

### 工作节点 7：结果汇总

留存到 `计算结果.md`：各个子问题的方法、关键结果、数据文件路线、代码文件清单。

### 工作节点 7.5：数据交付完整性核验（⛔ 务必通过）

保证全部分析结果都留存为 JSON/CSV，供下一步 evidence-visualization 查阅画图：

```bash

echo "=== 数据输出完整性检查 ==="

echo ""

echo "JSON 数据文件（evidence-visualization 的输入）："

ls -la 图表/*.json 2>/dev/null || echo "  (无)"

echo ""

echo "TABLE 文件："

ls -la 图表/TABLE_*.tex 2>/dev/null || echo "  (无)"

```

**⛔ MANDATORY：**

```bash

MISSING=0

# 全部结果.json 必须存在

if [ -f 图表/全部结果.json ] && [ -s 图表/全部结果.json ]; then

    echo "  ✅ 图表/全部结果.json"

else

    echo "  ❌ 图表/全部结果.json — MISSING or EMPTY"

    MISSING=$((MISSING+1))

fi

# 灵敏度分析数据（数模竞赛必须）

if [ -f 图表/灵敏度结果.json ]; then

    echo "  ✅ 图表/灵敏度结果.json"

else

    echo "  ⚠ 图表/灵敏度结果.json — not found (required for sensitivity chapter)"

fi

echo "Missing: $MISSING"

```

**若 ❌，务必回去补完再继续。**

**⛔ 避免在这一步产出 PDF 图形与表格或 图表引用.tex——那是 evidence-visualization 的职责。**

## 关键准则

- **computational-realization 只负责数据采集、统计分析、交付结果数据（JSON/CSV）。不画图。**

- **⛔ 禁止在分析代码中产出 PDF 图形与表格。** 全部 `plt.savefig()`、`save_fig()` 调用都不应出现在 computational-realization 的代码里。若分析过程中需可视化校验结果，用 `plt.show()` 看一眼就行，避免留存 PDF。

- **图形与表格 PDF 全部由下一步 evidence-visualization 产出。** evidence-visualization 会查阅 computational-realization 交付的 JSON 数据，按 recipe 系统产出高质量 PDF。

- **⛔ 求解器/优化器超时设定：** 避免设太短的超时（如 120 秒）。竞赛数据量可能很大，求解器需充足时间。推荐设定：

  - 小规模问题（变量 <100）：`timeout=300`（5 分钟）

  - 中规模问题（变量 100-1000）：`timeout=600`（10 分钟）

  - 大规模问题（变量 >1000）：`timeout=1200`（20 分钟）

  - 全部求解器都务必打印进度（每 30 秒输出一次当前最优解），防止无交付超时被系统杀掉

- 主交付文件：`计算结果.md` + `图表/*.json`

- 临时文件放 `临时文件/` 目录

- 代码务必能运行：写完务必实施校验

- 结果务必留存为 JSON/CSV 文件（供 evidence-visualization 查阅画图）

<data_quality>

### 无用户数据时的数据生成质量要求

When no user data is available and you need to produce or simulate data:

1. **Realistic ranges**: values needs to match the problem domain — e.g., temperature in °C not arbitrary 0-1, population in millions not random integers

2. **Meaningful patterns**: data is expected to show the trends/relationships the model is designed to capture — e.g., if modeling seasonal demand, the data is expected to have seasonal patterns

3. **Visualization-friendly**: design data so the resulting visuals look informative and professional:

   - Avoid extreme outliers that compress the primary data into a tiny range

   - Confirm different methods/groups have visible but not identical differences (5-20% gaps, not 0.1% or 500%)

   - Cover enough data points for smooth curves (≥50 for line plots, ≥200 for distributions)

   - For method comparison: the proposed method is expected to be best but not unrealistically dominant — other methods is expected to have their own strengths on some metrics

4. **Consistent with problem statement**: all generated numbers are expected to be traceable to the problem description — if the problem says "30 provinces", produce 30 data points, not 10

5. **Reproducible**: set random seeds (`np.random.seed(42)`) so outcomes are deterministic

</data_quality>

#### 画图配色准则（任何 matplotlib/seaborn 图都务必遵守）

**依据论文类别选取配色方案（整篇论文统一一套）：**

| 论文类别 | 推荐配色 | 调用方式 |

|----------|---------|---------|

| 竞赛论文 / 经管 / 统计建模 | Soft（默认） | `setup_style()` |

| 多组对比（>6 组） | Tableau | `setup_style('tableau')` |

| 自然科学 / 生物 / 化学 | NPG | `setup_style('npg')` |

| 医学 / 统计分析 | NEJM | `setup_style('nejm')` |

| IEEE / ACM / 工程类 | Science | `setup_style('science')` |

| 无障碍要求 | Colorblind | `setup_style('colorblind')` |

**在任何画图代码的开头，务必先初始化配色：**

```python

import os, sys, shutil

if not os.path.isdir('工具'):

    os.makedirs('工具', exist_ok=True)

    for src in ['plot_utils.py', 'stats_utils.py']:

        for search in ['skills/shared-scripts', '../skills/shared-scripts']:

            p = os.path.join(search, src)

            if os.path.isfile(p):

                shutil.copy2(p, f'工具/{src}'); break

sys.path.insert(0, '.')

try:

    from 工具.plot_utils import setup_style, save_fig, PALETTE

    setup_style()

except ImportError:

    import matplotlib; matplotlib.use('Agg')

    import matplotlib.pyplot as plt

    PALETTE = ['#5B9BD5','#ED7D7D','#7BC8A4','#B0B0B0','#9B8EC4','#F4A261']

    matplotlib.rcParams['axes.prop_cycle'] = matplotlib.cycler(color=PALETTE)

import seaborn as sns

```

**单组柱状图务必明示传颜色：**

```python

# 正确：ax.bar(x, y, color=PALETTE[:len(x)], edgecolor='white')

# 或用 seaborn：sns.barplot(data=df, x='col', y='val', palette=PALETTE)

```

**各个画图脚本写完后自检：** 核验是否有硬编码颜色、plt.title()、缺少 setup_style。发现就立即修复。

- 代码要有注释（附录评审加分项）

- 数据路线用相对路线

- 基本异常处理，一个子问题失败不可全崩

- 依赖清单.txt 务必产出

- 大文件用 Bash heredoc 分块写入

## 详细参考（按需 Read，避免一次全读）

主过程已在 Phase 0–7.5。以下是按主题搬到 `references/checks/` 的深度参考，按 Phase 4.5 的指引在每问跑完时打开：

| 触发场景 | Read 哪个文件 |

|---|---|

| 第 1 问启动前（仅 1 次）| `references/checks/_index.md` |

| 任何子问题跑完 | `references/checks/consistency.md` |

| 任何子问题跑完 | `references/checks/sanity_check.md` |

| 优化类子问题 | `references/checks/optimization.md`（含 5 层求解 + 结构性校验）|

| 预测类子问题 | `references/checks/prediction.md` |

| 评价类子问题 | `references/checks/evaluation.md` |

| 物理/几何题 | `references/checks/physical.md` |

| 写代码遇到具体 bug | `references/error_prevention_code.md`（按题型查防错条目）|

⛔ **每问的自检过程见 Phase 4.5，不可跳过、不可合并、不可等到全部问跑完才统一自检。**

