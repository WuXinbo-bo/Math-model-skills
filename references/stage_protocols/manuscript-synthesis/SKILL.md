---
name: manuscript-synthesis
description: "Meta-model-agent 整合模型、程序、结果、图形与引用为完整中文竞赛文稿。适用于竞赛文稿集成。"
---

# 竞赛文稿集成

## 必读的版面子协议

只加载当前任务需要的规则：

- 始终读取 `参考资料/paper-layout/core.md` 与 `body-density.md`。
- PDF/LaTeX 路线读取 `latex-figures.md`。
- DOCX 路线读取 `docx-figures.md`。

这些文件中的版心、图片尺寸和正文密度合同优先于本文件中遗留的通用示例。

## 竞赛 Profile 是强制契约

写作前必须读取 `当前任务/执行中/任务包.json` 与 `参考资料/竞赛规则.md`，且只能使用 `模板/当前竞赛/`：

- `cumcm`：使用 `cumcmthesis` 的中文国赛论文。
- `51mcm`：使用 `51mcmthesis`；电子正文启用 `withoutpreface`，不得披露学校、队员或联系方式。
- `mcm-icm`：英文 COMAP 论文，至少 12pt，首页 Summary Sheet，仅保留 Control Number，并按完整稿 25 页设计。

不得把中文模板直接翻译成英文模板，也不得仅通过改名伪装竞赛模板。模板选择属于机器门禁。

## 稳定执行契约

- **执行目标**：将问题、模型、程序、结果和证据整合为结构完整、论证连贯的中文数模论文。
- **调用参数**：[competition-type]。
- **权威输入**：问题分析.md、建模报告.md、计算结果.md、图表资产、引用资料与竞赛模板。
- **允许交付**：论文/论文正文.tex、论文/章节/及必要的参考文献文件；不得改写冻结结果。
- **禁止写入**：不得越权修改已冻结的上游事实、用户原始文件或本协议未授权的目录。
- **可用工具边界**：Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch。
- **最小交付**：摘要、问题重述、假设、符号、模型、求解、结果、检验、评价、结论、参考文献和附录齐全。
- **恢复入口**：优先读取当前工作、状态记录和已有产物，从最近一次通过门禁的位置继续。
- **失败回退**：发现证据缺口时回退对应上游环节；禁止用未经计算的数字或虚构引用填充正文。
- **收口顺序**：先核对输入，再完成产物，再运行本环节门禁，最后登记状态；门禁未通过不得宣告完成。

Write a competition manuscript based on modeling outcomes: **$ARGUMENTS**

## 运行参数

- **COMPETITION** — `stats` = 统计建模, `huazhong` = 华中杯, `wuyi` = 五一杯, `mathorcup` = MathorCup, others = 数模竞赛 (cumcm/huawei/etc.)

- **MAX_PAGES** — 竞赛允许的总页数上限，不是正文必须达到的页数。任何正文、参考文献、附录和披露是否计入上限，按当前竞赛 Profile 执行。

- **BODY_DENSITY** — 正文充分性独立于页数判断。每个子问题必须包含数学机制或问题契约、必要推导、求解结果、独立验证和结果解释；不得因为接近页数上限而删除这些核心论证。

- **CUSTOM_REQUIREMENTS**

## 权威输入

1. 问题分析.md, 建模报告.md, 计算结果.md

2. 图表/, 程序/

## 图表嵌入尺寸硬规则

### LaTeX/PDF

- 普通单图默认：`\includegraphics[width=0.72\linewidth,height=0.70\textheight,keepaspectratio]{...}`，再根据最终可读性调整。
- 宽图最多使用 `width=\linewidth`；任何图、表、TikZ 或 DrawIO 导出物都不得超出 `\linewidth` 或页面高度。
- 不得使用无尺寸约束的 `\includegraphics{...}`，也不得用大于 `1.0\textwidth` 的缩放参数。
- 若图中文字因缩放后不可读，应重新绘图、减少面板、拆图或移附录，不能继续缩小。

### DOCX

- 先计算页面宽度减左右页边距得到可用版心。A4 常规页边距下，普通图推荐宽 13.5--15.0 cm，最大宽度不得超过版心。
- 保持纵横比；禁止同时强制指定不相容的宽高。图片高度过大时按页面可用高度二次缩放。
- 图题、编号、来源和正文解释必须与图片放在合理邻近位置，禁止图片单独占据大片页面而正文被挤掉。

### 页数不足与正文不足

- 页数限制是上限。不得再以“正文页数必须达到 MAX_PAGES”为目标。
- 正文不足时，应从上游证据扩充推导、实验设计、验证、结果解释、敏感性和局限性，不得用放大图表、重复图、空行或套话补页。
- 页数接近上限时，先压缩视觉资产和冗余内容，再决定是否精简文字；模型定义、公式逻辑、关键结果、验证和逐问结论属于不可删核心。

## 载入共享规则

```bash

cat 工具/writing_rules.md 2>/dev/null || cat skills/shared-scripts/writing_rules.md

```

<paper_structure>

## 按竞赛类型选择论文结构

### 数模竞赛 (cumcm/huawei/mathorcup/huazhong/etc.)

Template: `templates/cumcm/main.tex` (国赛/华为杯), `templates/mathorcup/main.tex` (MathorCup), `templates/huazhong/main.tex` (华中杯), `templates/wuyi/main.tex` (五一杯)

**⛔ MathorCup 必须使用 `MathorCupmodeling.cls` 文档类**（模板文件夹已包含 cls）。使用 `\bianhao{}`、`\tihao{}`、`\timu{}` 设置队伍信息，`\keyword{}` 设置关键词。摘要用 `\begin{abstract}...\end{abstract}` 环境。参考文献用 `\begin{thebibliography}` 环境。

**⛔ 华中杯必须使用 `cumcmthesis` 文档类**（模板文件夹 `huazhong/` 已包含 cls + 字体）。华中杯模板使用 `\begin{abstract}...\keywords{}\end{abstract}` 环境写摘要（不是手动排版），参考文献用 `\begin{thebibliography}` 环境（不是 `\bibliography{}`）。

```

摘要（~1页，含关键词）

1 问题重述

2 模型假设

3 符号说明

4 问题一的建模与求解（each sub-problem gets its own chapter）

5 问题二的建模与求解

6 问题三的建模与求解

7 灵敏度分析与模型检验

8 模型评价与推广

参考文献

附录 A：代码

```

### 统计建模 (stats)

Template: `templates/stats/main.tex`

**Chapter structure is driven by research content, not fixed templates.**

Award-winning stats modeling papers vary wildly in structure — some organize by model, some by analysis step, some by research question. There is no "standard structure". Meta-model-agent needs to design chapters autonomously based on the actual content in 选题规划.md / 建模报告.md.

#### 必须保留的固定骨架

```

表格清单

插图清单

摘要（中英文，分页）

一、绪论/前言（研究背景 + 文献综述/研究现状 + 研究目标/内容）

  ↓

  [Middle chapters: content-driven, Meta-model-agent designs autonomously, typically 3-5 chapters]

  ↓

N、结论与建议（结论 + 建议/展望 + 创新与不足）

参考文献

致谢

附录（代码）

```

#### 中间章节设计指引

Following reading 选题规划.md, design middle chapters following these principles:

**Principle 1: Chapter titles is expected to be specific, not generic**

- ✗ "四、模型构建" → ✓ "四、基于 CNN 的水质预测模型构建与评价"

- ✗ "五、实证分析" → ✓ "五、生育意愿的影响因素——集成学习模型"

**Principle 2: Organize by research logic chain, not by textbook methodology**

- If the research has multiple sub-problems/models, each model can be its own chapter

- If the research uses a single method with deep analysis, organize by analysis steps

**Principle 3: Data and method chapters can be merged or separated**

- Simple data (one dataset) → merge into "数据与方法"

- Complex data (multi-source, heavy preprocessing) → separate chapter "数据描述与预处理"

#### 高质量论文结构示例（仅作参考，禁止照搬）

**Example A — Classification + Path Analysis (fertility intention)**:

前言 → 模型构建 (introduce ensemble + Bayesian network) → 数据阐明和预处理 → 探索性特征分析 → 生育意愿的影响因素 (ensemble outcomes) → 生育意愿影响路线 (Bayesian network outcomes) → 结论与推荐

**Example B — Mixed Modeling (data factors & economic growth)**:

研究背景+文献 → 研究思路和模型介绍 → 理论分析 → 模型构建 (production function + regression + ARIMA, each a section) → 模型应用 (GDP prediction) → 总结与推荐 → 创新与不足

**Example C — DEA Evaluation (economic sustainability)**:

绪论 → 文献综述 → 研究区域概况 → 评价指标体系构建 → 数据优化处理 (normalization + PCA) → DEA 模型建立及求解 → 结论及推荐

**Example D — Deep Learning Prediction (water quality CNN)**:

绪论 → 模型构建思路与创新 → 数据描述及预处理 → 主成分分析 → CNN 模型构建与评价 (with model comparison) → 结论与展望

**Key observations**:

- No award-winning manuscript uses the "baseline regression → robustness → heterogeneity" causal inference structure (unless the topic IS causal inference)

- Chapter count varies from 5-7, determined by content

- "Model introduction / theoretical basis" can come prior to or following the data chapter

- "Innovation & limitations" can be inside the conclusion or a standalone chapter

#### 章节设计检查表（写作前自检）

- [ ] Does every chapter title include specific research content (not generic "模型构建")?

- [ ] Does the chapter order follow the research logic chain (reader can follow naturally)?

- [ ] Do core analysis chapters (model outcomes) occupy 40-50% of the manuscript?

- [ ] Is there a dedicated data description / exploratory analysis chapter (reviewers value data understanding)?

- [ ] Does the conclusion include "innovation" and "limitations" (reviewer bonus points)?

Use Chinese numbering (一、二、三...) with sub-sections (一)(二)(三). Avoid use 1、2、3 or 1.1、1.2 format.

Fixed sections that is expected to be kept: 表格清单, 插图清单, 中英文摘要, 绪论, 结论, 参考文献, 致谢.

</paper_structure>

## ⛔⛔⛔ 完成铁律（最高优先级）

**依据 `params.output_format` 决定主产物**：

- **PDF 模式（默认）**：`论文/论文正文.tex`（≥ 5KB）+ `论文/章节/*.tex` + `论文/references.bib`

- **docx 模式**：`论文/论文正文.md`（单文件，≥ 5KB）。**禁止产 论文/论文正文.tex**

⛔ **结束前必跑产出校验**：

```bash

MODE=$(python -c "import json; print(json.load(open('状态/工作流状态.json',encoding='utf-8')).get('output_format','pdf'))")

echo "MODE: $MODE"

PASS=true

if [ "$MODE" = "docx" ]; then

    [ -f 论文/论文正文.md ] && SZ=$(wc -c < 论文/论文正文.md) || SZ=0

    [ "$SZ" -ge 5120 ] && echo "✅ 论文/论文正文.md ($SZ)" || { echo "❌ 论文/论文正文.md 缺失或过小"; PASS=false; }

else

    [ -f 论文/论文正文.tex ] && SZ=$(wc -c < 论文/论文正文.tex) || SZ=0

    [ "$SZ" -ge 5120 ] && echo "✅ 论文/论文正文.tex ($SZ)" || { echo "❌ 论文/论文正文.tex 缺失或过小"; PASS=false; }

    SECT_COUNT=$(ls 论文/章节/*.tex 2>/dev/null | wc -l)

    [ "$SECT_COUNT" -ge 3 ] && echo "✅ sections ($SECT_COUNT)" || { echo "❌ 章节过少"; PASS=false; }

fi

[ "$PASS" != true ] && echo "⛔ 产出验证失败 — 必须补全后重新跑验证, 不要结束本步骤"

```

## 执行流程

### 工作节点 0：Backup + resume validate + upstream validation

**⛔ 上游交付完整性核验（写论文前必做）：**

```bash

echo "=== 上游输出完整性检查 ==="

UPSTREAM_OK=true

# 1. 核心文件是否存在

for f in 问题分析.md 建模报告.md 计算结果.md; do

    if [ -f "$f" ]; then

        sz=$(wc -c < "$f")

        echo "✅ $f ($sz 字符)"

        [ "$sz" -lt 500 ] && echo "  ⚠ 文件过小，内容可能不完整"

    else

        echo "❌ $f 不存在！"

        UPSTREAM_OK=false

    fi

done

# 2. 子问题覆盖度：问题情境解构 vs 建模报告 vs 代码结果

PROB_COUNT=$(grep -c '问题[一二三四五六七八九十]' 问题分析.md 2>/dev/null || echo 0)

MODEL_COUNT=$(grep -c '问题[一二三四五六七八九十]' 建模报告.md 2>/dev/null || echo 0)

RESULT_FILES=$(ls 图表/problem_*_结果.json 2>/dev/null | wc -l)

echo "子问题数: 分析=$PROB_COUNT, 建模=$MODEL_COUNT, 代码结果=$RESULT_FILES"

[ "$MODEL_COUNT" -lt "$PROB_COUNT" ] && echo "⚠ 建模报告覆盖子问题数少于问题情境解构"

[ "$RESULT_FILES" -lt "$PROB_COUNT" ] && echo "⚠ 代码结果文件数少于子问题数"

# 3. 图表文件是否存在

PDF_COUNT=$(ls 图表/*.pdf 2>/dev/null | wc -l)

echo "PDF 图表: $PDF_COUNT 个"

[ "$PDF_COUNT" -eq 0 ] && echo "⚠ 没有 PDF 图表，论文将缺少图片"

# 4. 全部结果.json 是否存在

[ -f 图表/全部结果.json ] && echo "✅ 全部结果.json 存在" || echo "⚠ 全部结果.json 不存在，论文数值可能不准确"

# 5. 图表引用.tex 是否存在

[ -f 图表/图表引用.tex ] && echo "✅ 图表引用.tex 存在" || echo "⚠ 图表引用.tex 不存在，图表嵌入代码缺失"

echo "=== 上游检查完成 ==="

```

Back up existing `论文/`. Validate for incomplete sections from previous runs:

```bash

echo "=== 断点续写检查 ==="

if [ -d "论文/章节" ]; then

    for f in 论文/章节/*.tex; do

        [ -f "$f" ] || continue

        chars=$(wc -c < "$f")

        if [ "$chars" -lt 500 ]; then

            echo "⚠ 占位符: $(basename $f) ($chars 字符) — 需要续写"

        else

            echo "✅ 已完成: $(basename $f) ($chars 字符)"

        fi

    done

fi

```

Resume rules: only write placeholder sections (<500 chars or covers "待补充"/"placeholder"), skip completed ones (>2000 chars). Save each chapter immediately — avoid accumulate in memory.

### 工作节点 1：Copy template (based on COMPETITION type)

```bash

mkdir -p 论文/章节

# Select template based on competition type — copy entire folder (tex + cls + fonts)

TMPL_BASE="模板"

[ -d "$TMPL_BASE" ] || TMPL_BASE="templates"

if [ "$COMPETITION" = "stats" ] || echo "$ARGUMENTS" | grep -qi "统计建模\|stats"; then

    echo "Using stats template"

    cp "$TMPL_BASE/stats/"* 论文/ 2>/dev/null

elif echo "$ARGUMENTS" | grep -qi "apmcm_zh\|亚太.*中文\|亚太赛中文" || grep -qi "apmcm_zh\|亚太.*中文\|亚太赛中文" META_MODEL_AGENT.md 2>/dev/null; then

    echo "Using APMCM (Chinese) template — based on CUMCM Chinese template"

    cp "$TMPL_BASE/cumcm/"* 论文/ 2>/dev/null

elif echo "$ARGUMENTS" | grep -qi "mathorcup\|MathorCup\|mathor" || grep -qi "mathorcup" META_MODEL_AGENT.md 2>/dev/null; then

    echo "Using MathorCup template"

    cp "$TMPL_BASE/mathorcup/"* 论文/ 2>/dev/null

elif echo "$ARGUMENTS" | grep -qi "huazhong\|华中杯" || grep -qi "huazhong\|华中杯" META_MODEL_AGENT.md 2>/dev/null; then

    echo "Using huazhong template"

    cp "$TMPL_BASE/huazhong/"* 论文/ 2>/dev/null

elif echo "$ARGUMENTS" | grep -qi "huawei\|华为杯" || grep -qi "huawei\|华为杯" META_MODEL_AGENT.md 2>/dev/null; then

    echo "Using huawei template"

    cp "$TMPL_BASE/huawei/"* 论文/ 2>/dev/null

elif echo "$ARGUMENTS" | grep -qi "wuyi\|五一杯" || grep -qi "wuyi\|五一杯" META_MODEL_AGENT.md 2>/dev/null; then

    echo "Using wuyi template"

    cp "$TMPL_BASE/wuyi/"* 论文/ 2>/dev/null

elif echo "$ARGUMENTS" | grep -qi "cumcm\|国赛" || grep -qi "cumcm\|国赛" META_MODEL_AGENT.md 2>/dev/null; then

    echo "Using cumcm template"

    cp "$TMPL_BASE/cumcm/"* 论文/ 2>/dev/null

elif echo "$ARGUMENTS" | grep -qi "changsanjiao\|长三角" || grep -qi "changsanjiao\|长三角" META_MODEL_AGENT.md 2>/dev/null; then

    echo "Using changsanjiao template"

    cp "$TMPL_BASE/changsanjiao/"* 论文/ 2>/dev/null

elif echo "$ARGUMENTS" | grep -qi "huashu\|华数杯" || grep -qi "huashu\|华数杯" META_MODEL_AGENT.md 2>/dev/null; then

    echo "Using huashubei template"

    cp "$TMPL_BASE/huashubei/"* 论文/ 2>/dev/null

elif echo "$ARGUMENTS" | grep -qi "diangong\|电工杯" || grep -qi "diangong\|电工杯" META_MODEL_AGENT.md 2>/dev/null; then

    echo "Using diangongbei template"

    cp "$TMPL_BASE/diangongbei/"* 论文/ 2>/dev/null

elif echo "$ARGUMENTS" | grep -qi "dongsansheng\|东三省\|辽宁" || grep -qi "dongsansheng\|东三省\|辽宁" META_MODEL_AGENT.md 2>/dev/null; then

    echo "Using dongsansheng template"

    cp "$TMPL_BASE/dongsansheng/"* 论文/ 2>/dev/null

elif echo "$ARGUMENTS" | grep -qi "shuwei\|数维杯" || grep -qi "shuwei\|数维杯" META_MODEL_AGENT.md 2>/dev/null; then

    echo "Using shuweibei template"

    cp "$TMPL_BASE/shuweibei/"* 论文/ 2>/dev/null

else

    echo "Using default template"

    cp "$TMPL_BASE/default/"* 论文/ 2>/dev/null

fi

# 模板资产内部固定使用 main.tex；复制到运行工作区后立即改为中文交付名

if [ -f 论文/main.tex ] && [ ! -f 论文/论文正文.tex ]; then
    mv 论文/main.tex 论文/论文正文.tex
fi

[ -f 论文/论文正文.tex ] && echo "模板已复制：$(wc -l < 论文/论文正文.tex) 行" || echo "错误：未找到模板！"

```

**⛔ 模板复制后立即校验（务必通过才能继续）：**

```bash

echo "=== 模板完整性验证 ==="

if [ ! -f 论文/论文正文.tex ]; then

    echo "❌ CRITICAL: 论文/论文正文.tex 不存在！模板复制失败"

else

    # 通用检查

    grep -q 'documentclass' 论文/论文正文.tex && echo "✅ documentclass 存在" || echo "❌ 缺少 documentclass"

    grep -q '\\input{章节/' 论文/论文正文.tex && echo "✅ sections input 存在" || echo "❌ 缺少 sections input"

    grep -q 'thebibliography\|bibliography{' 论文/论文正文.tex && echo "✅ 参考文献结构存在" || echo "❌ 缺少参考文献"

    grep -q 'appendices\|\\appendix' 论文/论文正文.tex && echo "✅ 附录结构存在" || echo "❌ 缺少附录"

    # ⛔ 模板指纹校验：对比 论文/论文正文.tex 和模板原文，确认是复制的不是 Meta-model-agent 自己写的

    TMPL_BASE="模板"

    [ -d "$TMPL_BASE" ] || TMPL_BASE="templates"

    # 找到当前使用的模板原文

    TMPL_MAIN=""

    for d in "$TMPL_BASE"/*/; do

        [ -f "${d}main.tex" ] || continue

        # 用 documentclass 行匹配

        TMPL_CLS=$(grep 'documentclass' "${d}main.tex" 2>/dev/null | head -1)

        PAPER_CLS=$(grep 'documentclass' 论文/论文正文.tex 2>/dev/null | head -1)

        if [ "$TMPL_CLS" = "$PAPER_CLS" ]; then

            TMPL_MAIN="${d}main.tex"

            break

        fi

    done

    if [ -n "$TMPL_MAIN" ]; then

        echo "模板原文: $TMPL_MAIN"

        # 对比前 20 行（preamble 部分），如果差异超过 5 行说明被重写了

        DIFF_COUNT=$(diff <(head -20 "$TMPL_MAIN") <(head -20 论文/论文正文.tex) 2>/dev/null | grep -c '^[<>]')

        if [ "$DIFF_COUNT" -gt 10 ]; then

            echo "❌ CRITICAL: 论文/论文正文.tex 的 preamble 和模板差异过大（$DIFF_COUNT 行不同）— 可能被重写了！"

            echo "⛔ 强制从模板重新复制..."

            cp 论文/论文正文.tex 论文/论文正文.tex.broken 2>/dev/null

            TMPL_DIR=$(dirname "$TMPL_MAIN")

            cp "$TMPL_DIR"/* 论文/ 2>/dev/null

            [ -f 论文/main.tex ] && mv -f 论文/main.tex 论文/论文正文.tex

            echo "✅ 模板已重新复制（旧文件备份为 论文正文.tex.broken）"

        else

            echo "✅ 模板指纹校验通过（preamble 差异 $DIFF_COUNT 行，在允许范围内）"

        fi

    else

        echo "⚠ 未找到匹配的模板原文，跳过指纹校验"

    fi

fi

```

Consult the copied template to understand its structure prior to writing:

```bash

cat 论文/论文正文.tex

```

**⛔ 你务必完整查阅 论文正文.tex 模板内容。后续写章节时，只调整 章节/*.tex 文件，避免重写 论文正文.tex。**

Apply the template as-is. Exclusively modify:

- Replace bracket placeholders (`[论文标题]`, `[中文摘要内容]`, etc.) with actual content

- Replace `\input{章节/...}` filenames if your section files have different names

- Fill in the abstract and keywords

**⛔ CRITICAL TEMPLATE RULES (violation = broken PDF):**

1. **NEVER rewrite 论文正文.tex from scratch** — the template has 100+ lines of carefully tuned preamble (fonts, margins, section numbering, citation format). Writing from scratch will break fonts, margins, and formatting.

2. **NEVER replace `\listoftables`/`\listoffigures` with hand-written text lists** — the template uses LaTeX auto-generated lists. If you write "表1.xxx\n表2.yyy" manually, the list won't update when tables change.

3. **NEVER add a separate cover page for MathorCup** — MathorCup 官方格式没有独立封面。队伍编号表格+标题+摘要都在第一页。避免自己加 `\maketitle` 或写一个大标题封面。直接用模板里的格式：表格 → 分隔线 → 标题 → 摘要。

4. **NEVER change the cover page year/届数 format** — replace `[竞赛年份]` with the actual year (e.g., `2026`), `[届数]` with the actual number (e.g., `十二`).

5. **Validate following writing**: `diff 论文/论文正文.tex` against the template — only bracket placeholders and `\input` lines is expected to differ.

6. **MathorCup 模板验证**：检查 论文正文.tex 使用 `\documentclass{MathorCupmodeling}`，`\bianhao{}`/`\tihao{}`/`\timu{}` 已填写。

7. **华中杯模板验证**：检查 `\documentclass[withoutpreface,bwprint]{cumcmthesis}` 未被修改，摘要使用 `\begin{abstract}...\keywords{}\end{abstract}` 环境，参考文献使用 `\begin{thebibliography}{99}...\end{thebibliography}`，附录使用 `\begin{appendices}...\end{appendices}`，不要自己加 `\usepackage{geometry}`。

8. **五一杯模板验证**：检查承诺书页完整保留，摘要使用手动排版（`\noindent \textbf{关键词：}` 在上，`\noindent \textbf{摘\quad 要：}` 在下，不用 `\begin{abstract}` 环境），参考文献使用 `\begin{thebibliography}`，附录第一节是文件列表表格。**⛔ 五一杯额外检查**：(a) 不要加 `\usepackage{cite}`（和 natbib 冲突会导致编译错误），(b) 不要重复加载 `\usepackage{subcaption}` 和 `\usepackage{float}`（cls 已包含），(c) 不要加 `\maketitle`（五一杯用手写承诺书页，不用 cls 的 maketitle），(d) 不要删除 `withoutpreface` 选项。

The cover page uses `\fzxbsong` (方正小标宋) and `\fsgb` (仿宋GB2312) fonts with `\cline{2-2}` underlines in a tabular. These fonts have fallback definitions — if the .ttf files are not installed, they fall back to `\heiti` and `\fangsong`.

When replacing cover page placeholders, ONLY change the text inside `[...]` brackets. Do NOT touch `\cline{2-2}`, `\\`, `&`, or any LaTeX commands:

```latex

% Template has (和 cover station.tex 格式一致):

参赛学校：&[学校名称]\\\cline{2-2}

% Replace ONLY the bracket text:

参赛学校：&某某大学\\\cline{2-2}

% NEVER remove \cline{2-2} (creates underline) or & (column separator)

```

Do NOT modify:

- `\documentclass` line (font size, manuscript size)

- `\usepackage[...]{geometry}` (page margins)

- `\ctexset{section=...}` (chapter numbering format)

- `\pagestyle` / `\fancyhf` (header/footer)

- `\usepackage[...]{natbib}` or `\usepackage[...]{gbt7714}` (citation format)

- Cover page structure (封面布局)

- `\listoftables` / `\listoffigures` (表格与插图清单 — 自动化产出，避免手写)

- Anything before `\begin{document}` (preamble)

- The cover page, abstract, TOC, and bibliography sections in 论文正文.tex — only replace placeholder text within them

Write all chapter content in separate `论文/章节/*.tex` files. The 论文正文.tex `\input{章节/...}` lines load them automatically. Avoid paste chapter content directly into 论文正文.tex.

If you need to add packages, add them after the existing `\usepackage` block, before `\begin{document}`.

Avoid write 论文正文.tex from scratch — the template handles fonts, spacing, margins, citation format, headers/footers.

Note: the stats template uses `natbib` with `[numbers, square, super]` format (superscript `[1]`), while the cumcm template uses `gbt7714` with superscript format. Use whichever the template provides. In body text, use `\cite{key}` — the `super` option automatically renders it as superscript.

Avoid redefine LaTeX built-in commands (`\sin`, `\cos`, `\tanh`, `\log`, `\exp`, `\max`, `\min`, etc.) in math_commands.tex.

### 工作节点 2：Abstracts

**⛔ CRITICAL: Do NOT write the abstract now.** Skip this step entirely. Write a placeholder `[摘要待正文完成后填写]` in the abstract section. The abstract MUST be written LAST (following Phase 5) because it needs specific numerical outcomes from all chapters. Writing it first = making up numbers.

Come back to fill the abstract in Phase 5 (concluding validate), following all body chapters are full. At that point, read 计算结果.md and all section .tex files to extract the actual numbers.

<abstract_format>

The template uses manual typesetting for abstracts. Avoid use two `\begin{abstract}` environments — ctexart shows "摘要" as title for both.

**⛔ 华中杯例外**：华中杯模板基于 `cumcmthesis` 文档类，使用 `\begin{abstract}...\keywords{}\end{abstract}` 环境。不要改成手动排版格式。正确写法：

```latex

\begin{abstract}

[中文摘要内容，400-600字]

\keywords{[关键词1]\quad [关键词2]\quad [关键词3]}

\end{abstract}

```

**⛔ 五一杯说明**：五一杯模板有承诺书页（第一页）和封面页（第二页）。**五一杯摘要使用手动排版（不用 `\begin{abstract}` 环境）**：关键词在上（`\noindent \textbf{关键词：}...`），摘要在下（`\noindent \textbf{摘\quad 要：}`）。这是五一杯官方格式，跟国赛/华中杯不同。承诺书页不要删除。

Valid format for cumcm/stats templates (already in template):

```latex

% === 中文摘要 ===

\begin{center}

{\zihao{3}\heiti 摘\hspace{2em}要}

\end{center}

\zihao{-4}\songti

[中文摘要内容，600-800字，写满一整页]

\noindent\textbf{关键词：}...

% === 英文摘要（新页）===

\newpage

\begin{center}

{\zihao{3}\bfseries Abstract}

\end{center}

[English abstract, 400-600 words, faithful translation]

\noindent\textbf{Keywords:} ...

```

**数模竞赛摘要**: 400-600 字, every sub-problem is expected to include specific numerical outcomes. **⛔ 务必按问题分段**：第1段背景概述，第2-4段分别针对问题一/二/三（方法+数值结果），第5段模型评价。每段用 LaTeX 空行分隔。五一杯虽然是人工排版摘要，分段准则同理适用。

**统计建模摘要**: 500-700 字, aim to fill most of one page but leave 3-4 lines margin at bottom — overflowing onto a second page looks worse than being slightly short. Content chain: 研究背景与意义 → 现有方法不足 → 本文方法 → 数据来源与处理 → 关键数值结果 → 应用价值与政策推荐. English abstract: 350-500 words, same structure and all numerical outcomes, also fit on one page.

</abstract_format>

### 工作节点 3：Visual inventory + mandatory embedding plan

Prior to writing any chapter, build a full inventory of available visuals:

```bash

echo "=== Available PDF figures ==="

ls -la 图表/*.pdf 2>/dev/null || echo "No PDF figures found"

echo ""

echo "=== Available table files (PDF模式: .tex / Word模式: .md) ==="

ls -la 图表/TABLE_*.tex 图表/TABLE_*.md 2>/dev/null || echo "No TABLE files found"

echo ""

echo "=== 图表引用.tex content (figure→PDF mapping) ==="

cat 图表/图表引用.tex 2>/dev/null || echo "No 图表引用.tex"

echo ""

echo "=== TikZ 几何/算法/架构图 ==="

# TikZ 由 systems-diagramming 生成为 图表/结构示意图.tex → 编译成 图表/结构示意图.pdf（多图则 tikz_*.pdf / 结构示意图_N.pdf）

# 它们的 \includegraphics 图块已写进 图表引用.tex，按 图表引用.tex 嵌入即可。

ls 图表/tikz_*.pdf 2>/dev/null && echo "→ 有 TikZ 图，必须嵌入" || echo "No TikZ diagrams"

```

**⛔ MANDATORY: Build a FIGURE EMBEDDING PLAN prior to writing any chapter:**

```

FIGURE EMBEDDING PLAN:

1. fig_desc_stats.pdf → 第三章 描述性统计 → caption: "图X 核心变量描述性统计分布"

2. fig_model_comparison.pdf → 第四章 模型对比 → caption: "图X 模型性能对比雷达图"

3. TABLE_regression.tex(PDF模式) / TABLE_regression.md(Word模式) → 第四章 回归分析 → caption: "表X 回归分析结果"

4. 结构示意图.pdf (几何/算法/架构 TikZ, from 图表引用.tex) → 对应章节 → caption: "图X 弦长递推几何关系示意"

```

> 表格按输出模式选格式：PDF 模式 `\input{图表/TABLE_*.tex}`；Word/docx 模式 `cat 图表/TABLE_*.md`。图表/ 里有几个 TABLE 文件就嵌入几个，一张不漏。

**Rules:**

- **⛔ 图形与表格 caption 务必是中文**（中文论文）。若 `图表引用.tex` 里的 caption 是英文，嵌入时务必翻译成中文

- **⛔ 必须使用 `图表引用.tex` 里的 figure 代码块**，不要自己写 `\includegraphics`。直接复制整个 `\begin{figure}...\end{figure}` 块，只改 caption 为中文

- **⛔ TikZ 图必须嵌入**：`图表引用.tex` 里每个引用 `结构示意图.pdf` / `tikz_*.pdf` 的 `\begin{figure}...\end{figure}` 块都要复制到对应章节，一张都不能漏

- **⛔ 图片路线务必是 `../图表/xxx.pdf`**（由于 章节/ 在 论文/ 下面）

- Exclusively embed visuals whose PDF files actually exist — avoid build visual environments for PDFs that don't exist

**⛔⛔⛔ DrawIO 图嵌入准则（最容易被遗漏，务必逐条核验）：**

DrawIO 图（技术路线图、求解流程图、Pipeline 图等）的 `\begin{figure}...\end{figure}` 代码块在 `图表引用.tex` 的**末尾部分**（由 systems-diagramming 步骤追加）。你必须把它们嵌入到正确的章节：

| DrawIO 图类别 | 嵌入位置 | 章节文件 |

|--------------|---------|---------|

| 技术路线图 (技术路线图) | 问题重述章节末尾 | `1_restatement.tex` 或 `1_introduction.tex` |

| 子问题求解过程图 (问题流程图_1/q2/q3) | 相应子问题的"模型建立"小节开头，先写 2-3 句引导文字（概述本问题的求解思路和重点环节），再放过程图 | `5_problem1.tex`、`6_problem2.tex` 等 |

| 数据处理 Pipeline (fig_pipeline) | 数据预处理章节 | 数据处理有关章节 |

| TikZ 几何/算法图 (结构示意图.pdf) | 几何示意图→相应子问题章节开头；算法过程图→模型建立小节 | 相应子问题/模型章节 |

**写完全部章节后，务必运行以下核验确认 DrawIO/TikZ 图全部嵌入：**

```bash

echo "=== DrawIO/TikZ 嵌入检查 ==="

for pdf in 图表/技术路线图.pdf 图表/fig_flow_*.pdf 图表/fig_pipeline*.pdf 图表/fig_framework*.pdf; do

    [ -f "$pdf" ] || continue

    bn=$(basename "$pdf")

    if grep -rq "$bn" 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null; then

        echo "✅ $bn 已嵌入"

    else

        echo "❌ $bn 未嵌入 — 必须立即修复！"

    fi

done

# ⛔ TikZ 图检查（按 PDF 文件名核对，最可靠）

for tpdf in 图表/结构示意图.pdf 图表/结构示意图_*.pdf 图表/tikz_*.pdf; do

    [ -f "$tpdf" ] || continue

    tbn=$(basename "$tpdf")

    if grep -rq "$tbn" 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null; then

        echo "✅ TikZ $tbn 已嵌入"

    else

        echo "❌ TikZ $tbn 未嵌入 — 必须立即修复！"

    fi

done

```

**若有任何 ❌，务必立即修复后再继续写下一章。避免等到最后才修复。**

Also scan `图表/*.tex` for all `\begin{figure}` / `\begin{table}` blocks with their `\label{}`. After writing, verify all are embedded:

```bash

grep -oh '\\label{[^}]*}' 图表/*.tex 2>/dev/null | sort -u > 临时文件/all_fig_labels.txt

grep -oh '\\label{[^}]*}' 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null | sort -u > 临时文件/embedded_labels.txt

comm -23 临时文件/all_fig_labels.txt 临时文件/embedded_labels.txt  # should be empty

```

TikZ 图通过 `图表引用.tex` 里的 `\includegraphics[width=0.75\linewidth,height=0.70\textheight,keepaspectratio]{结构示意图.pdf}` 图块嵌入（不要用无尺寸约束的 `\includegraphics`，也不要用 `\input`）。按图的内容映射到章节：

- 技术路线图/研究框架图/问题关系图 → 问题重述章节末尾（`1_restatement.tex`），避免放到后面的子问题章节

- 各子问题求解过程图/几何示意图 → 相应子问题章节开头（`4_problem1.tex`、`5_problem2.tex`、`6_problem3.tex` 等）

- 模型架构图 → 相应模型章节

### 工作节点 3.5：文献预检索（写正文此前务必落实）

**⛔ 在写任何 \cite{} 之前，必须先建立已验证的文献池。**

```bash

PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)

mkdir -p 临时文件

# 根据论文主题搜索真实论文，建立引用池

# 示例（根据实际选题调整）：

#   $PYTHON "$SCHOLAR_SCRIPT" bibtex "你的核心方法关键词" --max 5

#   $PYTHON "$SCHOLAR_SCRIPT" bibtex "你的研究领域关键词" --max 5

```

搜索后建立 `临时文件/_verified_refs.txt`，写正文时只引用池子里的论文。需新引用时先搜索校验再加入池子。

**兜底**：若 `scholar_fetch.py` 搜不到或 `match_label="low"`，用 WebSearch 在 Google Scholar / Semantic Scholar 网站上搜索，人工核实标题+作者+年份后再加入池子。

### 工作节点 4：Write each chapter

**⛔ CRITICAL: ALL numerical outcomes in the manuscript MUST come from `图表/*.json` or `计算结果.md`.** Prior to writing any outcome chapter, run:

```bash

cat 图表/全部结果.json

cat 计算结果.md

```

Copy the exact numbers from JSON into the LaTeX text. Do NOT round differently, do NOT estimate, do NOT make up numbers that "look reasonable". If a number is not in the JSON, it cannot appear in the manuscript.

**⛔ 数模竞赛（cumcm/huawei/mathorcup）务必严格按模板的章节次序写：**

```

1_restatement.tex  — 问题重述（用自己的话重述，不是抄题目）

2_assumptions.tex  — 模型假设（5-7 条，每条有内容+合理性说明）

3_symbols.tex      — 符号说明（⛔ 见下方格式规则）

4_problem1.tex     — 问题一的建模与求解

5_problem2.tex     — 问题二的建模与求解

6_problem3.tex     — 问题三的建模与求解

7_sensitivity.tex  — 灵敏度分析与模型检验

8_evaluation.tex   — 模型评价与推广

A_code.tex         — 附录：代码

```

**⛔ 模型假设必须在符号说明之前。** 不要合并成一个章节，不要调换顺序。文件名必须和模板 `\input{章节/...}` 一致。

**⛔ 模型假设数量控制**：4-5 条，避免超过 6 条。每条假设 1-2 句话（假设内容 + 合理性阐明），避免写成长段落。假设太多阐明问题没简化好。

**⛔ 符号阐明表格控制**：15-20 个变量以内。只列正文中真实采用的关键变量，避免把全部中间变量都列进去。

**⛔ 分页准则（全部章节通用）：**

- **不要在 section 文件内部加 `\newpage`、`\clearpage` 或 `\nopagebreak`** — 让 LaTeX 自动分页，手动干预容易产生空白页

- 论文正文.tex 里只在摘要后和目录后用分页，正文章节之间避免加

- compile_utils.sh 会自动移除 section 文件里的 `\newpage`/`\clearpage`/`\nopagebreak`

- **例外**：符号阐明文件（compile_utils.sh 会自动化转成 longtable 支撑跨页）

**⛔ 符号阐明表格格式（务必用 longtable，避免用 table+tabular）：**

- 符号说明必须用 `longtable` 环境，不要用 `\begin{table}...\begin{tabular}`

- longtable 天然支撑跨页，标题永远在表格开头，不会出现标题和表格分离的问题

- 不需 `\centering`（longtable 自带居中）

- 不需引导文字（"本文所用重点符号..."），标题直接紧跟表格

- compile_utils.sh 会自动化把 table+tabular 转成 longtable（兜底），但最好从源头写对

- 无误写法：

```latex

\section{符号说明}

\begin{longtable}{clc}

\caption{主要符号说明}\label{tab:symbols} \\

\toprule

符号 & 含义 & 单位 \\

\midrule

\endfirsthead

\toprule

符号 & 含义 & 单位 \\

\midrule

\endhead

$N$ & 总数量 & 个 \\

$x_i$ & 第$i$个变量 & --- \\

... \\

\bottomrule

\end{longtable}

```

- 符号控制在 15-20 个以内，表格控制在半页以内

**⛔ 写每个章节前，先读 建模报告.md 和 计算结果.md 对应部分的内容。** 不要凭记忆写——数值结果、公式推导、算法步骤都必须从这些文档中提取。

Read 计算结果.md for exact numbers — ensure paper numbers match computation results.

**⛔ 图文数值一致性规则：** 描述图表内容时（如"从图X可以看出，模型A的RMSE为0.023"），数值必须从 `图表/*.json` 或 `计算结果.md` 中读取，不要凭记忆编写。写完后用 `bash 工具/writing_check.sh 论文/` 检查一致性。

**⛔ 长表格处理规则（>12 行的数据表格）：**

正文中**禁止**直接放超过 12 行的表格（调度方案、完整数据列表、逐步迭代结果等）。处理方式：

1. **正文：只放缩略版**（前 3 行 + 后 3 行 + 中间 `$\vdots$` 省略），底部注明"完整结果见附录 X"

2. **附录：放完整表格**（用 longtable 环境，允许跨页）

示例（正文缩略版）：

```latex

\begin{table}[H]

\centering

\caption{问题一调度方案（部分）}

\begin{tabular}{cccc}

\toprule

工作项 & 设备 & 启动时间 & 结束时间 \\

\midrule

1 & A & 0 & 5 \\

2 & B & 2 & 8 \\

3 & A & 5 & 12 \\

\multicolumn{4}{c}{$\vdots$} \\

28 & C & 45 & 52 \\

29 & A & 48 & 55 \\

30 & B & 50 & 58 \\

\bottomrule

\end{tabular}

\label{tab:q1_schedule_short}

\footnotesize 注：完整调度方案（30 条登记）见附录 B。

\end{table}

```

**判断标准：** 如果 `图表/TABLE_*.tex` 文件超过 12 行数据行，必须自动生成缩略版 + 附录完整版。不要把 100+ 行的 longtable 直接嵌入正文章节。

Follow the interleaving, embedding, and LaTeX rules from `工具/writing_rules.md`.

**⛔ 图文并茂硬规则（每个章节都必须遵守）：**

- 普通图表使用 `[htbp]`，在章节边界用 `\FloatBarrier` 收束；禁止全篇强制 `[H]` 造成大块空白和页数膨胀

- 每张图/表后面必须有 ≥5 行分析文字（数值解读+对比+结论），然后才能放下一张图

- 绝对禁止两张图连续出现中间没有分析段落

- 图片按内容自适应缩放，推荐 `\includegraphics[width=0.72\linewidth,height=0.70\textheight,keepaspectratio]`；宽幅时序图/热力图可用 `0.80--0.90\linewidth`，方形或纵向图通常使用 `0.55--0.72\linewidth`。

- **⛔ 竞赛论文默认避免 subfigure/subcaption 并排图片。** 每张核心证据图优先独占一个 `figure`；但独占不等于必须铺满版心，应根据图中文字和纵横比选择最小可读尺寸。确需对比时可合成为一张经过统一排版的复合图，而不是在 LaTeX 中机械并排两张超小图。

- **⛔ 不设置统一图片宽度下限。** 判断标准是最终 100% 显示时文字是否清晰以及是否浪费页面。简单示意图可小于 `0.7\linewidth`；复杂数据图可适当放大，但任何图片不得超过 `\linewidth` 或 `0.70\textheight`。

**⛔ 超长表格处理规则（>15 行的结果表格必须遵守）：**

如果某个结果表格超过 15 行数据（如调度方案、路径规划、逐日预测值等），**不要把完整表格放在正文里**——会占好几页，挤压正文空间。正确做法：

1. **正文放摘要表**：只展示前 5 行 + 后 3 行 + 汇总统计（均值/最优/总计），caption 标注"（部分，完整结果见附录表 X）"

2. **附录放完整表**：在 `章节/A_code.tex`（或新建 `章节/A_tables.tex`）里放完整表格

```latex

% === 正文中的摘要表 ===

\begin{table}[H]

\centering

\caption{问题一调度方案（部分，完整结果见附录表\ref{tab:full_schedule}）}

\begin{tabular}{cccc}

\toprule

车间 & 设备 & 启动时间 & 结束时间 \\

\midrule

1 & A-1 & 0 & 1200 \\

1 & A-2 & 1200 & 2400 \\

\multicolumn{4}{c}{$\vdots$} \\

3 & C-4 & 8400 & 9600 \\

3 & C-5 & 9600 & 10800 \\

\midrule

\multicolumn{2}{c}{总计} & \multicolumn{2}{c}{Makespan = 10800s} \\

\bottomrule

\end{tabular}

\end{table}

% === 附录中的完整表 ===

% 在 A_code.tex 或 A_tables.tex 中：

\section{完整结果表格}

\begin{table}[H]

\centering

\caption{问题一完整调度方案}\label{tab:full_schedule}

\begin{longtable}{cccc}

% ... 完整数据 ...

\end{longtable}

\end{table}

```

**判断标准：** 写表格前先数数据行数。≤15 行直接放正文，>15 行用摘要+附录方案。compile_utils.sh 也会自动检测并截断超长表格，但最好在写的时候就处理好。

After each chapter, verify character count:

```bash

chars=$(wc -c < "论文/章节/当前章节.tex")

echo "当前章节: $chars 字符 (~$(echo "scale=1; $chars/900" | bc) 页)"

# Chinese LaTeX ≈ 800-1000 chars per page

# If chapter expected 5 pages but only 2000 chars (~2.5 pages), expand immediately

```

<exemplar_depth>

#### 写作深度参照

**国赛高质量论文（正文上限 30 页，不设填满目标，3 个子问题示例）**:

- 问题重述+分析 (2-3p): restate in own words, extract core problems — not copying the problem statement

- 模型假设+符号说明 (2p): 5-7 assumptions (each with content + justification, not too many not too few), one complete symbol table with 15-25 variables (符号/含义/单位 three columns, avoid split into multiple tables)

- Each sub-problem (5-7p): model formulation (2p, with derivation and physical meaning) + solution method (1.5p, with algorithm steps) + results with table+figure (1p) + analysis (0.5-1.5p, numerical meaning + comparison with expectations + reasoning)

- 灵敏度分析 (2-3p): ≥2 key parameters, each with variation curve plot + analysis paragraph

- 模型评价 (2p): 3-4 strengths + 2-3 weaknesses + generalization directions. Pure text discussion, no figures or tables needed

**华为杯一等奖 (40-50 pages)**: deeper derivations, more thorough analysis per sub-problem (8-10p each), 灵敏度分析 (4-5p), 模型评价 (3p, pure text, no figures) with comparison to other methods

**统计建模获奖 (35-40 pages)** — chapter structure is content-driven, page allocation reference:

- 绪论/前言 (4-8p): research background + literature review (grouped by 3-4 themes, 3-5 papers per theme with detailed discussion) + research objectives

- 数据描述与预处理 (6-8p): data source + variable description table + descriptive statistics table + exploratory analysis (distribution / trend / cross-tabulation plots)

- 模型/方法 chapters (6-10p): theoretical basis + formula derivation + parameter settings + implementation details (adjust by actual number of models)

- Core results analysis (10-16p): the most important part of the paper — every result needs 2-3 paragraphs of interpretation, not just "as shown in Table X"

- 结论与建议 (3-5p): conclusions + recommendations + innovation points + limitations and future work

Common traits of award-winning papers:

- Solid exploratory analysis (cross-tabulation, group comparisons, rich visualization)

- Core analysis chapters occupy 40-50% of total pages, every numerical result has deep interpretation

- Specific chapter titles ("基于集成学习的生育意愿影响因素分析" not "模型构建")

- Include "innovation & limitations" discussion (reviewer bonus points)

| Type | Pages | Characters | References |

|------|-------|-----------|------------|

| 数模国赛（正文上限 30 页） | 以论证完整为准，不设下限目标 | 以有效论证为准 | ≥10 |

| 华为杯 | 40-50 | 30000-40000 | ≥15 |

| MathorCup | 35-40 | 25000-35000 | ≥10 |

| 华中杯 | 25-30 | 18000-25000 | ≥10 |

| 五一杯 | 25-30 | 18000-25000 | ≥10 |

| 统计建模 | 35-40 | 25000-35000 | ≥20 |

</exemplar_depth>

<figure_usage_principles>

#### 不同竞赛类型的图表使用准则

**统计建模**: Figures first, tables second. Figure/table selection is driven by the actual analysis methods used — regression uses forest plots + regression tables, prediction uses prediction comparison plots + accuracy tables, classification uses confusion matrices + ROC, evaluation uses radar charts + ranking tables. Every analysis step should have a corresponding figure or table.

**数模竞赛**: "字不如表，表不如图". Every sub-problem must have independent result display (table + figure). Comprehensive comparison figures are additional supplements. Reviewers value information density and aesthetics.

Do not force figures where they are not needed (pure literature review, theoretical derivation). Meta-model-agent decides figure count and placement based on content needs.

</figure_usage_principles>

<stats_figure_placement>

#### 统计建模论文图表布置准则

Figure/table selection is driven by research content, not fixed type templates. Below are figures mapped to analysis methods:

**Data description stage** (almost all papers need these):

- Descriptive statistics table (required), data distribution plots / boxplots, correlation heatmap, time series trend plots

**Model results stage** (select based on actual methods used):

- Regression: regression result table + coefficient forest plot

- Prediction: prediction comparison plot (actual vs predicted) + model accuracy table (MAE/RMSE/R²) + error distribution plot

- Classification: confusion matrix + ROC curve + model comparison table (Accuracy/F1/AUC)

- Clustering: cluster scatter plot / t-SNE + silhouette score table

- Evaluation: comprehensive score ranking table + radar chart

- Causal inference: baseline regression table + robustness verify table + heterogeneity comparison plot

**Model interpretation / diagnostics stage** (select as needed):

- Feature importance / SHAP plot, residual diagnostics, sensitivity analysis plot, ablation table

**Principle**: Core result 图表/tables go in the body text. Appendix only for code and very long auxiliary tables.

</stats_figure_placement>

<chapter_writing_points>

#### 章节写作要点（按研究逻辑调整）

**⛔ 写作风格铁律（所有章节都必须遵守）：**

- **禁止在正文中使用 `\begin{itemize}` 或 `\begin{enumerate}` 列表。** 黑点/编号列表是最明显的 AI 写作痕迹。必须用连贯的段落叙述。

  - 需要列举时用行内编号："（1）...（2）...（3）..."或"首先...其次...最后..."

  - 例外：模型假设列表（可用编号）、附录

- **每段至少 3-5 句话。** 不要写只有 1-2 句的短段落。

- **连续段落不能以相同句式开头。** 如连续三段都以"本文..."开头，必须改。

- **图表是论据不是主语。** 段落不能以"图X展示了"、"如图X所示"、"由图X可知"开头。图表引用用括号旁注 `（图X）` 融入论证链条：先论点 → 图表作旁证 → 推论。详见 `工具/writing_rules.md` 的"图表是论据"规则。

- **禁止元叙述和内部指令泄露。** 正文中不能出现"参赛者"、"参赛队伍"、"计算结果.md"、"图表/*.json"、"META_MODEL_AGENT.md"等内部文件名或工作流术语。用"本文"代替"我们团队"，论文是独立学术文档。

**绪论/前言** (all papers):

- Research background (why this problem matters) → Literature review / research status (what others did, what gaps remain) → Research objectives / content / contributions → Paper structure overview

- Literature review organized by theme (≥15 citations), not chronologically listed

**数据与预处理** (almost all papers need this):

- Data source → Sample description (time range / sample size / variable count) → Variable definition / coding table → Missing value / outlier handling → Exploratory analysis (distribution plots / trend plots / cross-tabulation)

- Exploratory analysis is a key capability demonstration for reviewers — avoid skip

**模型/方法 chapters** (organize by actual research content):

- Each model/method: theoretical basis (1-2 paragraphs) → mathematical formulas → parameter setting rationale → implementation details

- Multiple models: can introduce all models first then show results (Example B style), or give each model its own chapter with results (Example A style)

**结果分析 chapters** (core, should occupy 40-50% of paper):

- Every result must have: numerical presentation (table/figure) → interpretation (2-3 paragraphs, not just "as shown in Table X") → comparison with expectations / other methods → reasoning

- Multi-model comparison: horizontal comparison table + rationale for selecting the best model

**结论与建议**:

- Main conclusions (echo research objectives) → Policy / application recommendations (specific and actionable) → Innovation points → Limitations and future work

- "Innovation & limitations" can be inside the conclusion or a standalone chapter (Example B style)

</chapter_writing_points>

**Expansion strategies** when content is thin (not padding — substantive content):

- Formula listed without derivation → add step-by-step derivation with physical meaning explanation

- Result with only "如表所示" → add 2-3 paragraphs of interpretation (numerical meaning, comparison with expectations, reasoning, comparison with other methods)

- Assumptions as bare list → add justification for each assumption

- Algorithm as pseudocode only → add explanation of key steps, complexity analysis, convergence discussion

- Literature review only lists papers → add method summary for each and connection to this work

### 执行节点 5：References

Follow the `<references_workflow>` in `工具/writing_rules.md`.

Stats papers: ≥20 references. The stats template uses `natbib` with `[numbers, square, super]` — use `\cite{key}` in body text (auto-superscript) + `\bibliography{references}` + `\bibliographystyle{plainnat}`. The cumcm template uses `gbt7714` — only need `\bibliography{references}`. The huazhong template uses `\begin{thebibliography}{99}...\end{thebibliography}` — manually add `\bibitem` entries (avoid use `\bibliography{}`). The wuyi template uses `gbt7714-numerical` — use `\bibliography{references}` (same as cumcm).

**⛔ 使用 scholar_fetch.py 工具获取所有参考文献的 BibTeX。禁止凭记忆编造 BibTeX。**

**⛔ 引用编号必须按正文出现顺序排列（1, 2, 3, 4...），不能跳着来。** 使用 `\begin{thebibliography}` 的模板：`\bibitem` 的排列顺序必须跟正文中 `\cite{}` 首次出现的顺序一致。使用 `\bibliography{references}` 的模板：BibTeX 会自动按引用顺序编号（gbt7714-numerical / plainnat 都支持）。写完所有章节后，检查引用编号是否连续递增，如果不是，调整 `\bibitem` 顺序或 `.bib` 文件中的条目顺序。

**⛔⛔ 正文中引用编号必须全局递增出现（严格，不可违反）：**

写正文时每个引用编号必须比之前所有已出现的编号大（即首次引用必须按 [1], [2], [3], [4]... 顺序）：

- ✅ 正确：全文第一个引用 [1]，第二个 [2]，第三个 [3]...

- ❌ 错误：正文中先出现 [3]，然后出现 [8]，又回到 [1] — 引用编号跳跃

- ❌ 错误：前文已出现 [5]，后文再出现新引用为 [3] — 编号回退

**如何保证递增：**

- 所有引用的 key 在 .bib 文件或 thebibliography 环境中的排列顺序 = 它们在正文中首次出现的顺序

- 如果写作时发现某处需要一个新引用，它的编号会自动是当前已用编号的最大值+1

- 写完所有章节后，逐段扫描正文，确认引用编号 [N] 严格递增（只允许重复已出现的编号）

**⛔ 引用格式规则（中文竞赛论文必须上标）：**

- 必须用上标引用样式：`\bibliographystyle{gbt7714-numerical}` 或 natbib 的 `super` 选项

- 如果模板用的是 `plain/plainnat/unsrt`（非上标），正文中必须用 `\upcite{}` 或 `\textsuperscript{\cite{}}` 而不是 `\cite{}`

- 禁止：非上标样式 + 直接 `\cite{}` → 引用会显示为 `[1]` 而非上标 `¹`

**⛔ 多引用合并规则（合并必须按编号升序）：**

同一处引用多篇文献时：

- ✅ 正确：`方法A\cite{a,b,c}` — 一个 \cite 命令，多个 key 用逗号分隔，**且 a,b,c 对应的编号必须升序**（如 [1,2,5]）

- ✅ 正确：`方法A\cite{a}\cite{b}` — 如果 a,b 编号不相邻（如 [3] 和 [7]），也可以分开写

- ❌ 错误：`方法A\cite{a}\cite{b}\cite{c}` — 多个连续 \cite 且编号相邻，必须合并成 `\cite{a,b,c}`

- ❌ 错误：`方法A\cite{c,a,b}` — 编号顺序错乱（如 [5,1,2]），必须改成 `\cite{a,b,c}`（[1,2,5]）

- ❌ 错误：`方法A\cite{a,b}` 但 a=[3]、b=[1] — 编号降序，必须改成 `\cite{b,a}`（[1,3]）

**合并的判定规则（严格）：**

1. 多引用里的 key 必须按其编号升序排列 → 如 [1,2,5] 对应 `\cite{key_of_1, key_of_2, key_of_5}`

2. 如果两个引用编号不相邻（中间差 > 1），建议合并为一个 `\cite{}` 保持整洁

3. 如果不能保证升序，**宁愿分开写** `\cite{a}\cite{b}` 也不要错序合并

4. 写作时难以预知最终编号，可先按 key 的出现逻辑合并，编译后用 compile_check.sh 检查并调整

**⛔ 引用写法规则：写正文时，citation key 必须包含描述性关键词，格式为 `作者姓_年份_主题关键词`。**

例如：`\cite{wang_2023_supply_chain_resilience}` 而不是 `\cite{wang2023supply}`。

不确定作者/年份时用 `TODO__` 前缀：`\cite{TODO__digital_economy_spatial_spillover}`。

```bash

# Step 5a: 收集全部引用 key

grep -roh '\\cite[tp]*{[^}]*}' 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null \

  | grep -oP '\{[^}]+\}' | tr -d '{}' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort -u > 临时文件/_cited_keys.txt

echo "引用 key 数量: $(wc -l < 临时文件/_cited_keys.txt)"

# Step 5b: 逐个搜索并获取 BibTeX（用描述性关键词搜索）

PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)

while IFS= read -r key; do

    query=$(echo "$key" | sed 's/^TODO__//; s/_/ /g')

    echo "--- 获取: $key (搜索: $query) ---"

    $PYTHON "$SCHOLAR_SCRIPT" bibtex "$query" --max 3

    sleep 0.5

done < 临时文件/_cited_keys.txt

```

处理每个搜索结果：

1. 检查 `match_label`：`"good"` → 直接使用。`"partial"` → 核实标题。`"low"` → 很可能搜错了，换关键词或用 WebSearch。

2. `match_score` < 0.3 说明大概率不是目标论文，不要盲目使用。

3. 将 .tex 中的 citation key 替换为 BibTeX 条目中的实际 key。

4. `bibtex_source=auto` 的条目加 `% [VERIFY]`。`match_label="low"` 的加 `% [LOW_MATCH]`。

### 执行节点 5.5：De-AI polish

See `<de_ai_polish>` in `工具/writing_rules.md`.

### 执行节点 5.6：Write abstract NOW (after all chapters are complete)

**⛔ MANDATORY: NOW write the abstract.** Read 计算结果.md and all section .tex files. Extract the actual numerical results from each sub-problem. The abstract must contain ONLY numbers that appear in the body text — do NOT invent or round differently.

**⛔ 统计建模必须写中英文两个摘要**：先写中文摘要（500-700字），然后将中文摘要忠实翻译为英文摘要（350-500 words），所有数值结果、方法名称、结论必须一一对应。数模竞赛（国赛/五一杯/MathorCup/华中杯等）只写中文摘要。

For math modeling competitions: each sub-problem must have its specific result in the abstract (e.g., "问题一采用XX算法，最优解为YY，空间利用率达ZZ%")。

Read `工具/writing_rules.md` for abstract format rules (分段、首行缩进、长度).

### 执行节点 6：Final verification

```bash

bash 工具/writing_check.sh 论文/ 2>/dev/null || bash skills/shared-scripts/writing_check.sh 论文/

```

Also verify:

```bash

source .env_skill 2>/dev/null || true  # 加载 MAX_PAGES 等数值参数

echo "=== 各章节字符数 ==="

total=0

for f in 论文/章节/*.tex; do

    chars=$(wc -c < "$f")

    total=$((total + chars))

    echo "  $(basename $f): $chars 字符 (~$(echo "scale=1; $chars/900" | bc) 页)"

done

echo "  总计: $total 字符 (~$(echo "scale=1; $total/900" | bc) 页)"

echo "  提示: MAX_PAGES 是页数上限；字符数仅用于发现异常薄弱章节"

```

- 不以 `MAX_PAGES × 800` 作为机械字数目标。检查每个子问题是否完整覆盖机制、推导、结果、验证和解释。

- Any sub-problem chapter <3500 chars (~4 pages) needs expansion

- All 图表/*.pdf and TABLE files (PDF模式 .tex / Word模式 .md) referenced in 章节/正文

- No template bracket placeholders remaining (`[论文标题]`, `[中文摘要内容]`, etc.)

**⛔ Constraint consistency verify (MUST do before finishing):**

Read 问题分析.md (or the established problem statement in 用户数据/) and verify every numerical result in the paper against the problem's constraints:

```

=== 论文-题目约束一致性核验 ===

1. 查阅题目中的全部约束条件（容量、预算、时间窗、数量限制等）

2. 逐个核验论文正文中的结果是否满足这些约束

3. 举例而言：题目说"车辆载重上限 6000kg"，论文写"装载 7344kg" → 矛盾，务必修正

4. 举例而言：题目说"30 个省份"，论文分析了 28 个 → 不完整，务必补充

5. 摘要中的数字是否与正文保持一致？

6. 不同章节引用同一个结果时数字是否保持一致？（如问题一的最优解在摘要、正文、结论中出现 3 次，务必完全相同）

```

如果发现矛盾，修改论文正文（不是修改约束）。如果是代码结果本身违反约束，说明代码有 bug，需要回到 computational-realization 修复。

**⛔ Page count pre-verify (MUST pass before finishing — do NOT rely on character estimates):**

```bash

source .env_skill 2>/dev/null || true  # 加载 MAX_PAGES 等数值参数

echo "=== 页数预检 ==="

total_chars=0

for f in 论文/章节/*.tex; do

    [ -f "$f" ] || continue

    chars=$(wc -c < "$f")

    total_chars=$((total_chars + chars))

done

est_pages=$((total_chars / 900))

echo "总字符: $total_chars, 估算正文页数: ~$est_pages 页, 总页数上限: ${MAX_PAGES:-30} 页"

echo "不得仅因估算页数低于上限的 80% 就扩写；只有论证链缺失才扩充。"

```

字符估算只用于发现异常薄弱章节。必须在章节骨架完成、图表嵌入完成和终稿完成后三次实际编译，并依据竞赛 Profile 的页码标签读取摘要、正文和附录页数。CUMCM 摘要不得超过 1 页，正文不得超过 30 页，附录单独计数且页数不限。若章节实质不完整，再从建模报告和计算结果补充必要论证；不得为了接近上限扩写。

**⛔ 代码附录生成（完成正文后、最终门禁前必须执行）：**

```bash
python 工具/build_code_appendix.py --workspace . --format latex
```

CUMCM 必须把 `程序/code_manifest.json` 登记的全部源程序通过 `\lstinputlisting` 直接嵌入附录；51MCM 与 MCM/ICM 按竞赛 Profile 嵌入主程序和逐问核心实现。DOCX 路线执行：

```bash
python 工具/build_code_appendix.py --workspace . --format markdown --insert-into 论文/论文正文.md
```

严禁只写“代码见支撑材料”或手工复制一份可能过期的代码。

**Figure embedding verification (must pass before finishing)**:

```bash

echo "=== 图形与表格嵌入核验 ==="

missing=0

for pdf in 图表/*.pdf; do

    [ -f "$pdf" ] || continue

    bn=$(basename "$pdf")

    if ! grep -rq "$bn" 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null; then

        echo "MISSING: $bn 未嵌入任何章节"

        missing=$((missing + 1))

    fi

done

for fig_tex in 图表/*.tex; do

    [ -f "$fig_tex" ] || continue

    for lbl in $(grep -oh '\\label{[^}]*}' "$fig_tex" 2>/dev/null); do

        if ! grep -rq "$lbl" 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null; then

            echo "MISSING: $lbl (from $(basename $fig_tex)) 未嵌入"

            missing=$((missing + 1))

        fi

    done

done

echo "缺失: $missing"

```

If any figures are missing, go back and embed them into the appropriate sections before finishing. **⛔ Do NOT proceed to Step 7 until missing = 0.** Repeat the verify after each fix.

**⛔ 模板完整性自检（写完所有章节后必须检查 论文正文.tex 没有被破坏）：**

```bash

echo "=== 论文正文.tex 模板完整性核验 ==="

TMPL_OK=0

TMPL_FAIL=0

# 通用核验（全部模板）

grep -q 'documentclass' 论文/论文正文.tex && { echo "✅ documentclass"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 缺少 documentclass"; TMPL_FAIL=$((TMPL_FAIL+1)); }

grep -q '\\input{章节/' 论文/论文正文.tex && { echo "✅ sections input"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 缺少 sections input"; TMPL_FAIL=$((TMPL_FAIL+1)); }

grep -q 'thebibliography\|bibliography{' 论文/论文正文.tex && { echo "✅ 参考文献"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 缺少参考文献"; TMPL_FAIL=$((TMPL_FAIL+1)); }

grep -q 'appendices\|\\\\appendix' 论文/论文正文.tex && { echo "✅ 附录"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 缺少附录"; TMPL_FAIL=$((TMPL_FAIL+1)); }

grep -q 'superscript\|\\@cite\|setcitestyle.*super' 论文/论文正文.tex && { echo "✅ 上标引用"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 缺少上标引用定义"; TMPL_FAIL=$((TMPL_FAIL+1)); }

# 五一杯特有核验

if grep -qi 'wuyi\|五一杯' META_MODEL_AGENT.md 2>/dev/null; then

    grep -q '承诺书' 论文/论文正文.tex && { echo "✅ 五一杯承诺书页"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 五一杯缺少承诺书页"; TMPL_FAIL=$((TMPL_FAIL+1)); }

    grep -q 'image2' 论文/论文正文.tex && { echo "✅ 五一杯封面logo"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 五一杯缺少封面logo"; TMPL_FAIL=$((TMPL_FAIL+1)); }

    grep -q '关键词' 论文/论文正文.tex && { echo "✅ 五一杯关键词"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 五一杯缺少关键词"; TMPL_FAIL=$((TMPL_FAIL+1)); }

fi

# MathorCup 特有核验

if grep -qi 'mathorcup' META_MODEL_AGENT.md 2>/dev/null; then

    grep -q 'MathorCupmodeling' 论文/论文正文.tex && { echo "✅ MathorCup cls"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ MathorCup 未采用无误 cls"; TMPL_FAIL=$((TMPL_FAIL+1)); }

    grep -q '\\bianhao\|\\tihao\|\\timu' 论文/论文正文.tex && { echo "✅ MathorCup 队伍信息"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ MathorCup 缺少队伍信息"; TMPL_FAIL=$((TMPL_FAIL+1)); }

fi

# 华中杯特有核验

if grep -qi 'huazhong\|华中杯' META_MODEL_AGENT.md 2>/dev/null; then

    grep -q 'cumcmthesis' 论文/论文正文.tex && { echo "✅ 华中杯 cls"; TMPL_OK=$((TMPL_OK+1)); } || { echo "❌ 华中杯未采用 cumcmthesis"; TMPL_FAIL=$((TMPL_FAIL+1)); }

fi

echo ""

echo "模板核验: $TMPL_OK 通过, $TMPL_FAIL 失败"

[ "$TMPL_FAIL" -gt 0 ] && echo "⛔ 务必修复全部失败项！可能是 论文正文.tex 被意外重写了，请从模板重新复制并只替换占位符。"

```

### 执行节点 7：Output

数模竞赛: 章节/ numbered by sub-problem (4_problem1.tex, 5_problem2.tex...)

统计建模: 章节/ by academic structure (1_introduction.tex, 2_data_method.tex...)

## 核心规则

- Use templates from `templates/`, avoid write 论文正文.tex from scratch

- Chinese/English abstracts: manual typesetting, not two `\begin{abstract}` environments

- Citation format: use whichever the template provides (stats: natbib `[1]`, cumcm: gbt7714 superscript, huazhong: thebibliography manual entries, wuyi: gbt7714-numerical)

- No `\hypersetup{colorlinks=true}` — conflicts with hidelinks

- Countable pages must not exceed MAX_PAGES. A shorter paper is acceptable only when every required argument and evidence chain is complete.

- No team info — use placeholders

- Tables: three-line style (booktabs)

- Primary output: `论文/` directory, temp files: `临时文件/`

- ⛔ **本步骤只写论文 .tex 文件，不要重新生成图表 PDF、不要修改 程序/*.py、不要重新运行分析代码。** 图表和数据已由前序步骤（evidence-visualization / computational-realization）生成完毕，直接引用即可

- Large files: Bash heredoc

- ⛔ **Bash heredoc 必须用带引号的 `'EOF'`（防止 `\\` 被转义）：**

  - ✅ 正确：`cat << 'EOF' > 论文/章节/4_problem1.tex`（引号内 `\\` 原样保留）

  - ❌ 错误：`cat << EOF > 论文/章节/4_problem1.tex`（无引号，`\\` 变成 `\`，导致表格 `Misplaced \noalign` 错误）

  - 这是表格编译失败的最常见原因——40+ 处 `\\` 全部变成 `\`，编译器只报第一个错就停了
