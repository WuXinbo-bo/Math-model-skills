---
name: delivery-assurance
description: "Meta-model-agent 完成编译、版式、匿名、页数、引用与提交前合规验收。适用于提交质量验收。"
---

# 提交质量验收

## 必读的版面子协议

- 始终读取 `参考资料/paper-layout/core.md` 与 `body-density.md`。
- PDF/LaTeX 验收读取 `latex-figures.md`。
- DOCX 验收读取 `docx-figures.md`。
- 子协议中的尺寸和页数语义优先于本文件中的旧示例。

DOCX 路线使用 `python 工具/docx_export.py --workspace .` 生成 `论文/数模论文.docx` 和 `论文/docx_report.json`。不得对 DOCX 路线执行 XeLaTeX/BibTeX；验收以 Markdown 正文、DOCX 包、尺寸报告以及可选的 LibreOffice PDF 预览为准。

## 竞赛专用硬门禁

编译前必须读取 `状态/工作流状态.json` 中的竞赛 Profile 和 `参考资料/竞赛规则.md`：

- CUMCM：核验当届官方通知、匿名电子正文、模板、引用、图表及编号/附件要求。
- 51MCM：核验 `51mcmthesis`、`withoutpreface`、报名号/题号/组别字段，以及正文不存在学校、成员、邮箱和电话信息。
- MCM/ICM：核验全英文、12pt、Summary Sheet、已填写 Control Number、A--F 题号、无个人/学校身份信息，完整 PDF 不超过 25 页。

编译成功不能覆盖竞赛 Profile 门禁失败。

## 稳定执行契约

- **执行目标**：完成论文编译、版式、匿名、页数、引用与提交文件的终局验收。
- **调用参数**：[paper-directory]。
- **权威输入**：论文/论文正文.tex、论文/章节/、图表资产、模板规则与竞赛要求。
- **允许交付**：论文/数模论文.pdf、论文/编译日志.log及必要的验收记录；仅可做有边界的修复。
- **禁止写入**：不得越权修改已冻结的上游事实、用户原始文件或本协议未授权的目录。
- **可用工具边界**：Bash(*), Read, Write, Edit, Grep, Glob。
- **最小交付**：PDF可打开、编译无关键错误、引用闭合、模板完整、匿名与页数合规。
- **恢复入口**：优先读取当前工作、状态记录和已有产物，从最近一次通过门禁的位置继续。
- **失败回退**：最多按既定次数修复编译；模型或结果问题必须回退上游，不得在验收阶段擅改事实。
- **收口顺序**：先核对输入，再完成产物，再运行本环节门禁，最后登记状态；门禁未通过不得宣告完成。

Compile and validate: **$ARGUMENTS**

## 运行参数

- **ENGINE = `xelatex`**

- **MAX_COMPILE_ATTEMPTS = 3**

- **PAPER_DIR = `论文/`**

- **MAX_PAGES** / **COMPETITION** — From Additional Parameters.

## 执行流程

### 工作节点 1：Validate environment

```bash

if ! which xelatex 2>/dev/null; then

    echo "xelatex not found, attempting install..."

    if which miktex 2>/dev/null; then

        miktex packages install xetex ctex xecjk gbt7714 fontspec

        miktex fndb refresh

    elif which initexmf 2>/dev/null; then

        initexmf --set-config-value=[MPM]AutoInstall=1

    fi

fi

which xelatex && which bibtex && echo "ready" || echo "xelatex/bibtex not found"

fc-list :lang=zh | head -5

kpsewhich gbt7714.sty 2>/dev/null || echo "gbt7714.sty not found (will auto-install on first compile)"

```

### 工作节点 2：Pre-compile cleanup

```bash

if [ -f "工具/compile_utils.sh" ]; then

    bash 工具/compile_utils.sh 论文/

elif [ -f "skills/shared-scripts/compile_utils.sh" ]; then

    bash skills/shared-scripts/compile_utils.sh 论文/

else

    echo "compile_utils.sh not found, manual cleanup needed"

fi

```

This utility auto-handles: special chars cleanup, table format fixes, includegraphics path correction (`图表/` → `../图表/`), hidelinks, 图表/图表/ nesting, math_commands conflicts, wide table resizebox wrapping, narrow table resizebox removal, light-color text fixes, TikZ library injection.

If script not found, perform these steps manually.

**⛔ 表格行结束符修复（Misplaced \noalign 的根因）：**

```bash

# 检测并修复 tabular/longtable 中的单 \ 行结束符（应该是 \\）

# 这是 heredoc 不加引号导致 \\ 被转义为 \ 的常见问题

for f in 论文/章节/*.tex; do

    [ -f "$f" ] || continue

    # 检测：tabular 环境内，行末只有单个 \ 后跟换行（应该是 \\）

    if grep -P '(?<!\\)\\(?!\\)(?=\s*$)' "$f" | grep -v '\\begin\|\\end\|\\hline\|\\toprule\|\\midrule\|\\bottomrule\|\\caption\|\\label\|\\centering\|\\input\|\\include\|\\usepackage\|\\section\|\\subsection' > /dev/null 2>&1; then

        echo "⚠ $(basename $f): 可能有表格行结束符问题（单 \\ 应为 \\\\）"

        # 在 tabular/longtable 环境内，把行末的单 \ 替换为 \\

        python3 -c "

import re

with open('$f', 'r', encoding='utf-8') as fh:

    content = fh.read()

# 只在 tabular/longtable 环境内修复

def fix_table_endings(match):

    table = match.group(0)

    # 把数据行末尾的单 \ (后跟换行) 替换为 \\\\

    fixed = re.sub(r'(?<=&[^&\n]*)\\\s*\n', r'\\\\\\\\\n', table)

    return fixed

for env in ['tabular', 'longtable']:

    pattern = r'(\\\\begin\{' + env + r'[*]?\}.*?\\\\end\{' + env + r'[*]?\})'

    content = re.sub(pattern, fix_table_endings, content, flags=re.DOTALL)

with open('$f', 'w', encoding='utf-8') as fh:

    fh.write(content)

" 2>/dev/null

    fi

done

```

Additionally validate ref/label matching and embed missing visuals:

```bash

mkdir -p 临时文件

grep -oh '\\ref{[^}]*}' 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null | sort -u > 临时文件/_refs.txt

grep -oh '\\label{[^}]*}' 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null | sort -u > 临时文件/_labels.txt

comm -23 <(sed 's/\\ref/\\label/g' 临时文件/_refs.txt) 临时文件/_labels.txt > 临时文件/_missing_labels.txt

cat 临时文件/_missing_labels.txt

```

**⛔ 中文引号统一为全角引号（避免 PDF 出现 ''乱码或两个堆叠反引号）：**

中文论文用 xeCJK，全角引号 `"..."` 会自动化渲染为漂亮的对称弯引号。

LaTeX 风格 `` ``...'' `` 在中文字体下会呈现成两个堆叠的反引号，很丑。

ASCII 直引号 `"..."` 在 LaTeX 中渲染为右右引号 `''...''`。

统一替换为全角引号。

```bash

# 把所有错误引号统一为全角引号

for f in 论文/章节/*.tex; do

    [ -f "$f" ] || continue

    python3 -c "

import re

content = open('$f', 'r', encoding='utf-8').read()

# 保护数学环境

placeholders = []

def stash(m):

    placeholders.append(m.group(0)); return f'\\x00M{len(placeholders)-1}\\x00'

content = re.sub(r'\\\$[^\\\$]*\\\$', stash, content)

content = re.sub(r'\\\\\\[.*?\\\\\\]', stash, content, flags=re.DOTALL)

# 保护 \begin{verbatim}/lstlisting 等代码环境

content = re.sub(r'\\\\begin\{(verbatim|lstlisting|minted)\}.*?\\\\end\{\\1\}', stash, content, flags=re.DOTALL)

# 1. LaTeX 风格 ``...'' → 全角双引号

content = re.sub(r\"\`\`([^\`'\\\\n]+?)''\", '\u201c\\\\g<1>\u201d', content)

# 2. ASCII 直引号 \"...\" → 全角双引号（成对处理）

parts = content.split('\"')

if len(parts) > 2:

    result = parts[0]

    for i, p in enumerate(parts[1:], 1):

        result += ('\u201c' if i % 2 == 1 else '\u201d') + p

    content = result

# 还原

for i, ph in enumerate(placeholders):

    content = content.replace(f'\\x00M{i}\\x00', ph)

open('$f', 'w', encoding='utf-8').write(content)

" 2>/dev/null

done

```

If labels are missing, find corresponding figure/table code in `图表/*.tex` and embed into the correct section file.

Also verify compile_utils.sh output for "UNEMBEDDED" warnings — each one means a figure or table from `图表/` is not in any section.

**MANDATORY FIX LOOP — do NOT proceed to compilation until all figures AND tables are embedded:**

```bash

UNEMBED=0

# Validate PDF visuals

for pdf in 图表/*.pdf; do

    [ -f "$pdf" ] || continue

    bn=$(basename "$pdf")

    grep -rq "$bn" 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null || { echo "UNEMBEDDED PDF: $bn"; UNEMBED=$((UNEMBED+1)); }

done

# Validate TABLE_*.tex files

for tbl in 图表/TABLE_*.tex; do

    [ -f "$tbl" ] || continue

    bn=$(basename "$tbl")

    # Validate if any label from this table file appears in sections

    for lbl in $(grep -oh '\\label{[^}]*}' "$tbl" 2>/dev/null); do

        grep -rq "$lbl" 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null || { echo "UNEMBEDDED TABLE: $lbl (from $bn)"; UNEMBED=$((UNEMBED+1)); }

    done

done

# Validate 图表引用.tex labels

if [ -f 图表/图表引用.tex ]; then

    for lbl in $(grep -oh '\\label{[^}]*}' 图表/图表引用.tex 2>/dev/null); do

        grep -rq "$lbl" 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null || { echo "UNEMBEDDED: $lbl (from 图表引用.tex)"; UNEMBED=$((UNEMBED+1)); }

    done

fi

echo "Total unembedded: $UNEMBED"

```

If UNEMBED > 0, you MUST fix ALL of them before compiling. For each unembedded item:

- **PDF figure**: copy the `\begin{figure}...\end{figure}` block from `图表/图表引用.tex` into the target section

- **TABLE_*.tex**: copy the `\begin{table}...\end{table}` block from `图表/TABLE_*.tex` into the target section (use `\input{../图表/TABLE_xxx.tex}` or paste the tabular code directly)

- Add 1-2 sentences of lead-in text before and 3-5 sentences of analysis after each embedded item

- Re-run the count verify above — repeat until UNEMBED = 0

**Do NOT compile with unembedded figures or tables — the PDF will have missing content.**

```bash

# Validate all 图表/*.pdf are referenced in body

for pdf in 图表/*.pdf; do

    [ -f "$pdf" ] || continue

    bn=$(basename "$pdf")

    grep -rq "$bn" 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null || echo "⚠ $bn not referenced"

done

```

### 执行节点 3：Compile (manual steps, no latexmk)

```bash

cd 论文/

xelatex -interaction=nonstopmode 论文正文.tex

bibtex 论文正文

xelatex -interaction=nonstopmode 论文正文.tex

xelatex -interaction=nonstopmode 论文正文.tex

```

### 执行节点 4：Error fix loop (MANDATORY — do NOT skip)

After each compilation, verify `编译日志.log` for CRITICAL errors. **You MUST fix ALL errors before declaring compilation complete.**

```bash

# Count critical errors

MATH_ERR=$(grep -c 'Bad math environment delimiter\|Missing \$ inserted\|begin{document} ended by' 论文/编译日志.log 2>/dev/null || echo 0)

LR_ERR=$(grep -c 'Not allowed in LR mode' 论文/编译日志.log 2>/dev/null || echo 0)

UNDEF_CS=$(grep -c 'Undefined control sequence' 论文/编译日志.log 2>/dev/null || echo 0)

TOTAL_ERR=$((MATH_ERR + LR_ERR))

echo "Math errors: $MATH_ERR, LR mode errors: $LR_ERR, Undefined CS: $UNDEF_CS"

if [ "$TOTAL_ERR" -gt 0 ]; then

    echo "CRITICAL: $TOTAL_ERR errors — MUST FIX prior to proceeding"

    # Show error locations

    grep -B2 'Bad math\|Missing \$ inserted\|begin{document} ended\|Not allowed in LR mode' 论文/编译日志.log | grep -E '^\./|^l\.' | head -20

fi

```

**Error fix rules (iterate up to 5 times, not 3):**

1. **Math environment errors** (`Bad math environment delimiter`, `Missing $ inserted`, `\begin{document} ended by \end{equation}`):

   - Read the error location from 编译日志.log (e.g., `./章节/3_model_theory.tex:42`)

   - Open the file and find the broken math: usually `\X(t)$` should be `$X(t)$`, or `\mu$` should be `$\mu$`

   - Common cause: a sed/cleanup script stripped the opening `$` but left the closing `$`

   - Fix: ensure every math expression has matching `$...$` or `\[...\]` delimiters

   - **Do NOT use broad sed patterns to fix math** — read each error location and fix individually

2. **LR mode errors** (`Not allowed in LR mode`):

   - Usually caused by `\begin{figure}` or `\begin{table}` inside a paragraph without proper separation

   - Fix: add `\par` or blank line before the float environment

3. **Undefined control sequence**:

   - Missing package → add `\usepackage{xxx}` to 论文正文.tex preamble

   - Typo in command → fix the command name

4. **BibTeX failures**:

   - If BibTeX fails because of earlier LaTeX errors, fix the LaTeX errors first, then recompile

   - Verify that `\bibliography{references}` and `\bibliographystyle{plainnat}` exist in 论文正文.tex

   - Verify that references.bib has no syntax errors (unmatched braces, missing commas)

**After each fix, recompile and reverify:**

```bash

cd 论文/

xelatex -interaction=nonstopmode 论文正文.tex

bibtex 论文正文 2>&1 | tail -5

xelatex -interaction=nonstopmode 论文正文.tex

xelatex -interaction=nonstopmode 论文正文.tex

cd ..

# Reverify

MATH_ERR=$(grep -c 'Bad math environment delimiter\|Missing \$ inserted' 论文/编译日志.log 2>/dev/null || echo 0)

echo "Remaining math errors: $MATH_ERR"

```

**⛔ Do NOT proceed to Step 5 until MATH_ERR = 0 and LR_ERR = 0.** BibTeX will also fail if there are LaTeX errors upstream — fix LaTeX first.

When fixing errors in 论文正文.tex, only fix the specific error (e.g., add a missing package, fix a typo). Avoid rewrite or restructure 论文正文.tex — the template's preamble, cover page, page margins, section numbering format, and header/footer settings must remain unchanged.

### 执行节点 5：Post-compile checks

```bash

bash 工具/compile_check.sh 论文/ 2>/dev/null || bash skills/shared-scripts/compile_check.sh 论文/

```

The script checks: PDF existence/size, undefined references, overfull hbox, TOC, abstracts, bibliography entries, citation count, citation format (上标/顺序/合并), unused figures, figure stacking, TikZ diagram presence.

**⛔ MANDATORY: 引用格式问题必须修复（不可忽略）：**

compile_check.sh 会检查 3 类引用格式问题，任何一类 FAIL/WARN 都必须修复：

1. **上标格式 FAIL** → 如果 bibliographystyle 是 `plain/plainnat/unsrt` 但 `\cite{}` 没有上标

   - 修复方法A：改 bibliographystyle 为 `gbt7714-numerical` 或 `plainnat` + `\usepackage[numbers,square,super]{natbib}`

   - 修复方法B：把正文里所有 `\cite{x}` 改为 `\upcite{x}` 或 `\textsuperscript{\cite{x}}`

2. **多引用顺序 WARN** → `\cite{c,a,b}` 但全文 a 先出现

   - 修复方法：改成 `\cite{a,b,c}`（按全文首次出现顺序）

   - 用以下 bash 找出所有需修复的位置：

     ```bash

     grep -rnP '\\(up)?cite\{[^}]+\}' 论文/章节/*.tex 论文/论文正文.tex

     ```

3. **连续引用未合并 WARN** → `\cite{a}\cite{b}` 或 `\cite{a} \cite{b}`

   - 修复方法：合并为 `\cite{a,b}`

   - 批量修复：

     ```bash

     # 找出全部需合并的位置

     grep -rnoP '\\(up)?cite\{[^}]+\}\s*\\(up)?cite\{[^}]+\}' 论文/章节/*.tex 论文/论文正文.tex

     ```

**⛔ 修复后必须重新编译验证：** `xelatex → bibtex → xelatex → xelatex`，然后重新运行 compile_check.sh 确认无 FAIL。

Additionally verify:

```bash

# List of visuals / list of tables (stats competition requirement)

[ -s 论文/论文正文.lof ] && echo "✅ 插图清单已产出" || echo "⚠ 插图清单为空"

[ -s 论文/论文正文.lot ] && echo "✅ 表格清单已产出" || echo "⚠ 表格清单为空"

```

**Template format verification (stats competition)**:

```bash

echo "=== 模板格式校验 ==="

if grep -q 'stats\|统计建模' 论文/论文正文.tex 2>/dev/null || [ "$COMPETITION" = "stats" ]; then

    # Validate page margins (is expected to be 2.54cm top/bottom, 3.17cm left/right)

    grep -q '2.54cm' 论文/论文正文.tex && echo "✅ 页边距无误" || echo "⚠ 页边距可能不对（应为上下2.54cm，左右3.17cm）"

    # Validate Chinese section numbering

    grep -q 'chinese{section}' 论文/论文正文.tex && echo "✅ 中文章节编号" || echo "⚠ 缺少中文章节编号（一、二、三...）"

    # Validate cover page

    grep -q '参赛学校\|参赛作品\|作品编号' 论文/论文正文.tex && echo "✅ 封面出现" || echo "⚠ 缺少封面"

    # Verify abstract format (should be \section*{摘要}, not \begin{abstract})

    grep -q 'section\*.*摘要' 论文/论文正文.tex && echo "✅ 摘要格式无误" || echo "⚠ 摘要格式可能不对"

    # Validate natbib (stats uses natbib, not gbt7714)

    grep -q 'natbib' 论文/论文正文.tex && echo "✅ natbib 引用格式" || echo "⚠ 缺少 natbib（统计建模应用 natbib）"

    # Validate no header line

    grep -q 'headrulewidth.*0pt' 论文/论文正文.tex && echo "✅ 无页眉线" || echo "⚠ 可能有页眉线"

    # Validate listoffigures / listoftables

    grep -q 'listoffigures' 论文/论文正文.tex && echo "✅ 插图清单命令" || echo "⚠ 缺少 \\listoffigures"

    grep -q 'listoftables' 论文/论文正文.tex && echo "✅ 表格清单命令" || echo "⚠ 缺少 \\listoftables"

fi

```

If any format checks fail, Meta-model-agent should fix 论文正文.tex to match the template format before recompiling.

### 执行节点 6：Competition compliance

Verify items:

1. **Page count**: determine which parts count under the active competition Profile and require the count to be `≤ MAX_PAGES`. Separately reject substantively incomplete chapters; never require the paper to fill the page ceiling.

2. **Anonymous**: no team info (队号, 队员, 指导老师)

3. **Abstract exists** (数模竞赛: at least Chinese; 统计建模: both Chinese and English)

4. **TOC exists** (required by MathorCup etc.)

5. **Code appendix exists**

6. **No undefined references/citations**

<page_diagnosis>

#### 正文充分性诊断（与页数上限分开）

不要再把“正文达到 MAX_PAGES 的 80%”作为硬目标。`MAX_PAGES` 只表示上限。即使页数较少，也只有在论证链缺失时才扩充正文。

```bash

echo "=== 页数不足诊断 ==="

echo "页数上限: MAX_PAGES；另行检查正文论证充分性"

echo ""

echo "=== 各章节字符数（找出最薄的章节）==="

for f in 论文/章节/*.tex; do

    chars=$(wc -c < "$f")

    echo "  $(basename $f): $chars 字符 (~$(echo "scale=1; $chars/900" | bc) 页)"

done

echo ""

echo "=== 推荐扩充的章节（字符数最少的 3 个）==="

for f in $(ls -S 论文/章节/*.tex | tail -3); do

    chars=$(wc -c < "$f")

    echo "  ⚠ $(basename $f): 仅 $chars 字符"

done

```

只有出现以下问题时才标记为 CRITICAL 并扩充：

- 某个子问题缺少模型机制或必要公式推导

- 结果只有数字或图表，没有验证和解释

- 摘要/结论中的关键主张无法在正文定位

扩充时只添加有证据来源的内容：

- Read 建模报告.md and 计算结果.md for detailed content

- Add unexpanded derivations, result analysis, validation, parameter discussions, and limitations

- Recompile after expansion

</page_diagnosis>

### 执行节点 7：⛔ FINAL QUALITY GATE (must ALL pass before finishing)

Run all checks and verify every item passes. **Do NOT output the report until all CRITICAL items are resolved.**

```bash

echo "=========================================="

echo "  FINAL QUALITY GATE"

echo "=========================================="

GATE_FAIL=0

# 1. PDF exists and non-trivial

if [ -f 论文/数模论文.pdf ] && [ $(wc -c < 论文/数模论文.pdf) -gt 100000 ]; then

    echo "✅ PDF exists ($(wc -c < 论文/数模论文.pdf) bytes)"

else

    echo "❌ PDF missing or too small"; GATE_FAIL=$((GATE_FAIL+1))

fi

# 2. No LaTeX errors

MATH_ERR=$(grep -c 'Bad math environment delimiter\|Missing \$ inserted' 论文/编译日志.log 2>/dev/null || echo 0)

LR_ERR=$(grep -c 'Not allowed in LR mode' 论文/编译日志.log 2>/dev/null || echo 0)

[ "$((MATH_ERR+LR_ERR))" -eq 0 ] && echo "✅ No LaTeX errors" || { echo "❌ $MATH_ERR math + $LR_ERR LR errors"; GATE_FAIL=$((GATE_FAIL+1)); }

# 3. Bibliography not empty

BBL_ENTRIES=$(grep -c '\\bibitem' 论文/论文正文.bbl 2>/dev/null || echo 0)

[ "$BBL_ENTRIES" -gt 0 ] && echo "✅ Bibliography: $BBL_ENTRIES entries" || { echo "❌ Bibliography empty (BibTeX failed)"; GATE_FAIL=$((GATE_FAIL+1)); }

# 4. No unembedded visuals

UNEMBED=0

for pdf in 图表/*.pdf; do

    [ -f "$pdf" ] || continue

    bn=$(basename "$pdf")

    grep -rq "$bn" 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null || UNEMBED=$((UNEMBED+1))

done

[ "$UNEMBED" -eq 0 ] && echo "✅ All visuals embedded" || { echo "❌ $UNEMBED visuals not embedded in manuscript"; GATE_FAIL=$((GATE_FAIL+1)); }

# 5. Page count

PAGE_EST=0

for f in 论文/章节/*.tex; do [ -f "$f" ] || continue; c=$(wc -c < "$f"); PAGE_EST=$((PAGE_EST + c)); done

PAGE_EST=$((PAGE_EST / 900))

echo "  Body estimate: ~$PAGE_EST pages; MAX_PAGES is the submission ceiling, not a fill target"

# 6. Overfull vbox (table/visual overflow)

VBOX_ERR=$(grep -c 'Overfull.*vbox' 论文/编译日志.log 2>/dev/null || echo 0)

[ "$VBOX_ERR" -eq 0 ] && echo "✅ No table/visual overflow" || { echo "❌ $VBOX_ERR overfull vbox — tables may be cut off"; GATE_FAIL=$((GATE_FAIL+1)); }

# 7. AI writing patterns (itemize in body)

AI_LISTS=0

for f in 论文/章节/*.tex; do

    [ -f "$f" ] || continue

    echo "$(basename $f)" | grep -qi 'appendix\|附录' && continue

    c=$(grep -c '\\begin{itemize}' "$f" 2>/dev/null || echo 0)

    AI_LISTS=$((AI_LISTS + c))

done

[ "$AI_LISTS" -eq 0 ] && echo "✅ No bullet lists in body" || { echo "❌ $AI_LISTS itemize — convert to prose"; GATE_FAIL=$((GATE_FAIL+1)); }

# 8. Template integrity — compare preamble against established template

echo "--- Template integrity ---"

TMPL=""

for t in 模板/stats_论文正文.tex 模板/cumcm_论文正文.tex 模板/mcm_论文正文.tex 模板/bachelor_论文正文.tex 模板/master_论文正文.tex 模板/journal_论文正文.tex; do

    [ -f "$t" ] && TMPL="$t" && break

done

if [ -n "$TMPL" ] && [ -f 论文/论文正文.tex ]; then

    # Extract preamble (before \begin{document}) from both files

    TMPL_PRE=$(sed -n '1,/\\begin{document}/p' "$TMPL" | grep '\\usepackage\|\\documentclass\|\\ctexset\|\\pagestyle\|\\renewcommand.*headrulewidth\|\\listoftables\|\\listoffigures\|\\cline\|\\bibliography' | sort)

    MAIN_PRE=$(sed -n '1,/\\begin{document}/p' 论文/论文正文.tex | grep '\\usepackage\|\\documentclass\|\\ctexset\|\\pagestyle\|\\renewcommand.*headrulewidth\|\\listoftables\|\\listoffigures\|\\cline\|\\bibliography' | sort)

    MISSING=$(comm -23 <(echo "$TMPL_PRE") <(echo "$MAIN_PRE") 2>/dev/null | head -5)

    if [ -z "$MISSING" ]; then

        echo "✅ Template preamble intact"

    else

        echo "❌ Template preamble was modified — these lines from template are missing in 论文正文.tex:"

        echo "$MISSING" | sed 's/^/    /'

        GATE_FAIL=$((GATE_FAIL+1))

    fi

    # Validate cover page structure (if template has one)

    if grep -q '参赛学校\|参赛作品' "$TMPL" 2>/dev/null; then

        grep -q '参赛学校\|参赛作品' 论文/论文正文.tex 2>/dev/null && echo "✅ Cover page present" || { echo "❌ Cover page missing/rewritten"; GATE_FAIL=$((GATE_FAIL+1)); }

        grep -q 'cline{2-2}' 论文/论文正文.tex 2>/dev/null && echo "✅ Cover underlines (cline)" || { echo "❌ Cover cline missing"; GATE_FAIL=$((GATE_FAIL+1)); }

    fi

    # Validate bracket placeholders not remaining

    if grep -q '\[论文标题\]\|\[学校名称\]\|\[队员1\]\|\[指导老师\]\|\[竞赛年份\]\|\[届数\]\|\[中文摘要内容\]' 论文/论文正文.tex 2>/dev/null; then

        echo "❌ Unreplaced bracket placeholders in 论文正文.tex"; GATE_FAIL=$((GATE_FAIL+1))

    else

        echo "✅ All placeholders replaced"

    fi

    # Validate hand-written visual/table list (anti-pattern)

    if grep -P '^(表|图)\d+\.' 论文/论文正文.tex 2>/dev/null | head -1 | grep -q '.'; then

        echo "❌ Hand-written figure/table list (use \\listoftables/\\listoffigures)"; GATE_FAIL=$((GATE_FAIL+1))

    fi

else

    echo "  (no template found for comparison, skipping)"

fi

# 9. Visual plan reconciliation (validate planning docs)

echo "--- Visual plan validate ---"

PLAN_FIGS=0; ACTUAL_FIGS=$(ls 图表/*.pdf 2>/dev/null | wc -l)

for plan in 选题规划.md 论文规划.md 问题分析.md; do

    [ -f "$plan" ] || continue

    pf=$(grep -ci 'fig_\|图.*：\|visual.*:' "$plan" 2>/dev/null || echo 0)

    [ "$pf" -gt "$PLAN_FIGS" ] && PLAN_FIGS=$pf

done

if [ "$PLAN_FIGS" -gt 0 ]; then

    echo "  Planned: ~$PLAN_FIGS visuals, Actual: $ACTUAL_FIGS PDFs"

    [ "$ACTUAL_FIGS" -ge "$PLAN_FIGS" ] && echo "✅ Visual count meets plan" || { echo "❌ Fewer visuals than planned ($ACTUAL_FIGS < $PLAN_FIGS)"; GATE_FAIL=$((GATE_FAIL+1)); }

else

    echo "  No visual plan found, actual: $ACTUAL_FIGS PDFs"

fi

# 10. TikZ 几何/算法/架构图

# TikZ 由 systems-diagramming 编译成 图表/结构示意图.pdf, 通过 \includegraphics 嵌入

# (不是 sections 里的裸 tikzpicture 代码)。两种形态都算已嵌入。

TIKZ_IN_PAPER=$(grep -rl 'tikzpicture\|结构示意图\|tikz_' 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null | wc -l)

# ⛔ 只在"真实产出了 tikz_*.pdf 产物"时才硬核对(避免规划提了但用 DrawIO 替代时误报失败)

TIKZ_PDF_TOTAL=0; TIKZ_PDF_MISSING=0

for tpdf in 图表/结构示意图.pdf 图表/结构示意图_*.pdf 图表/tikz_*.pdf; do

    [ -f "$tpdf" ] || continue

    TIKZ_PDF_TOTAL=$((TIKZ_PDF_TOTAL+1))

    grep -rq "$(basename "$tpdf")" 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null || TIKZ_PDF_MISSING=$((TIKZ_PDF_MISSING+1))

done

if [ "$TIKZ_PDF_TOTAL" -gt 0 ]; then

    # 有真实 TikZ 产物 → 务必全部嵌入

    if [ "$TIKZ_PDF_MISSING" -gt 0 ]; then

        echo "❌ $TIKZ_PDF_MISSING 张 TikZ PDF 未嵌入任何章节"; GATE_FAIL=$((GATE_FAIL+1))

    else

        echo "✅ TikZ diagrams embedded ($TIKZ_PDF_TOTAL)"

    fi

elif grep -qi 'tikz\|架构\|路线图\|几何示意\|算法流程' 论文规划.md 问题分析.md 2>/dev/null; then

    # 规划提到 TikZ 但没产出 tikz_*.pdf(可能已用 DrawIO 替代) → 仅提醒, 不判失败

    [ "$TIKZ_IN_PAPER" -gt 0 ] && echo "✅ TikZ embedded" || echo "  ⚠ 规划提到 TikZ 但未发现 tikz_*.pdf(可能已用 DrawIO 替代, 不阻塞)"

else

    [ "$TIKZ_IN_PAPER" -gt 0 ] && echo "✅ TikZ diagrams embedded ($TIKZ_IN_PAPER)" || echo "  (no TikZ planned)"

fi

# 11. Citations in body

CITE_COUNT=$(grep -roh '\\cite{' 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null | wc -l)

[ "$CITE_COUNT" -gt 0 ] && echo "✅ Citations: $CITE_COUNT" || { echo "❌ No citations in body text"; GATE_FAIL=$((GATE_FAIL+1)); }

# 12. No placeholders remaining

PLACEHOLDERS=$(grep -rl 'PLACEHOLDER\|待补充\|TODO\|\[论文标题\]\|\[中文摘要内容\]' 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null | wc -l)

[ "$PLACEHOLDERS" -eq 0 ] && echo "✅ No placeholders" || { echo "❌ $PLACEHOLDERS files have placeholders"; GATE_FAIL=$((GATE_FAIL+1)); }

# 13. Undefined references

UNDEF_REFS=$(grep -c 'LaTeX Warning.*Reference.*undefined' 论文/编译日志.log 2>/dev/null || echo 0)

[ "$UNDEF_REFS" -eq 0 ] && echo "✅ No undefined refs" || { echo "❌ $UNDEF_REFS undefined references"; GATE_FAIL=$((GATE_FAIL+1)); }

# 14. Overfull hbox (>5 = too many)

HBOX_ERR=$(grep -c 'Overfull.*hbox' 论文/编译日志.log 2>/dev/null || echo 0)

[ "$HBOX_ERR" -lt 5 ] && echo "✅ Overfull hbox: $HBOX_ERR" || { echo "❌ $HBOX_ERR overfull hbox — fix wide tables/formulas"; GATE_FAIL=$((GATE_FAIL+1)); }

# 15. Visual stacking

STACKING=0

for f in 论文/章节/*.tex; do [ -f "$f" ] || continue; s=$(awk '/\\end\{(figure|table)\}/{a=1;t=0;next} a&&/\\begin\{(figure|table)\}/{if(t<3)c++;a=0;next} a&&/[a-zA-Z\x80-\xff]{3,}/{t++} a&&t>=3{a=0} END{print c+0}' "$f" 2>/dev/null); STACKING=$((STACKING+s)); done

[ "$STACKING" -eq 0 ] && echo "✅ No visual stacking" || { echo "❌ $STACKING visual stacking — add analysis text between visuals"; GATE_FAIL=$((GATE_FAIL+1)); }

# 16. TOC

if grep -q 'tableofcontents' 论文/论文正文.tex 2>/dev/null; then

    [ -s 论文/论文正文.toc ] && echo "✅ TOC generated" || {

        echo "❌ TOC empty — running extra compile pass..."

        cd 论文/

        xelatex -interaction=nonstopmode 论文正文.tex > /dev/null 2>&1

        xelatex -interaction=nonstopmode 论文正文.tex > /dev/null 2>&1

        cd ..

        [ -s 论文/论文正文.toc ] && echo "✅ TOC generated following extra compile" || { echo "❌ TOC still empty"; GATE_FAIL=$((GATE_FAIL+1)); }

    }

fi

# 17. Abstracts (Chinese papers)

if grep -q 'ctex' 论文/论文正文.tex 2>/dev/null; then

    grep -rq '摘.*要' 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null && echo "✅ Chinese abstract" || { echo "❌ No Chinese abstract"; GATE_FAIL=$((GATE_FAIL+1)); }

    grep -rq 'Abstract' 论文/章节/*.tex 论文/论文正文.tex 2>/dev/null && echo "✅ English abstract" || { echo "❌ No English abstract"; GATE_FAIL=$((GATE_FAIL+1)); }

fi

# 18. Run compile_check.sh + writing_check.sh for full details

echo ""

echo "--- Full validate scripts ---"

bash 工具/compile_check.sh 论文/ 2>/dev/null || bash skills/shared-scripts/compile_check.sh 论文/ 2>/dev/null

bash 工具/writing_check.sh 论文/ 2>/dev/null || bash skills/shared-scripts/writing_check.sh 论文/ 2>/dev/null

WC_EXIT=$?

[ "$WC_EXIT" -eq 0 ] && echo "✅ Writing checks passed" || { echo "❌ Writing checks failed (exit=$WC_EXIT)"; GATE_FAIL=$((GATE_FAIL+1)); }

# 19. 符号阐明 longtable 核验

echo "--- Symbol table format ---"

for f in 论文/章节/*.tex; do

    [ -f "$f" ] || continue

    if grep -q '\\section{符号说明}\|\\section.*符号' "$f" 2>/dev/null; then

        if grep -q '\\begin{longtable}' "$f" 2>/dev/null; then

            echo "✅ 符号阐明采用 longtable"

        elif grep -q '\\begin{table}' "$f" 2>/dev/null; then

            echo "❌ 符号阐明仍用 table（应转 longtable 防分页）"; GATE_FAIL=$((GATE_FAIL+1))

        fi

    fi

done

# 20. 正文长表格核验（>15行应用 longtable）

echo "--- Long table validate ---"

for f in 论文/章节/*.tex; do

    [ -f "$f" ] || continue

    echo "$(basename $f)" | grep -qi 'symbol\|appendix\|A_code' && continue

    if grep -q '\\begin{tabular}' "$f" 2>/dev/null; then

        ROW_COUNT=$(awk '/\\begin\{tabular\}/,/\\end\{tabular\}/' "$f" 2>/dev/null | grep -c '&' || echo 0)

        [ "$ROW_COUNT" -gt 15 ] && { echo "❌ $(basename $f): $ROW_COUNT 行表格应转 longtable"; GATE_FAIL=$((GATE_FAIL+1)); }

    fi

done

# 21. babel[english] 冲突

echo "--- babel validate ---"

if grep -q 'ctex\|cumcmthesis\|gmcmthesis' 论文/论文正文.tex 2>/dev/null; then

    grep -q 'babel.*english' 论文/论文正文.tex 2>/dev/null && { echo "❌ 中文论文有 babel[english]"; GATE_FAIL=$((GATE_FAIL+1)); } || echo "✅ 无 babel 冲突"

fi

# 22. 数值一致性（JSON vs 论文）

echo "--- Numerical consistency ---"

if [ -f 图表/全部结果.json ]; then

    python3 -c "

import json, re, os

with open('图表/全部结果.json','r',encoding='utf-8') as f: outcomes=json.load(f)

def extract(obj,p=''):

    n={}

    if isinstance(obj,dict):

        for k,v in obj.items(): n.update(extract(v,f'{p}.{k}'))

    elif isinstance(obj,(int,float)) and not isinstance(obj,bool):

        if 0.001<abs(obj)<1e10: n[p]=obj

    return n

jn=extract(outcomes); pn=set()

for tf in sorted(os.listdir('论文/章节')):

    if not tf.endswith('.tex'): continue

    with open(f'论文/章节/{tf}','r',encoding='utf-8',errors='ignore') as f: t=f.read()

    for m in re.finditer(r'(?<![a-zA-Z])(\d+\.?\d+)(?![a-zA-Z_{}])',t):

        try: pn.add(float(m.group(1)))

        except: pass

miss=sum(1 for k,v in jn.items() if not any(abs(p-v)<abs(v)*0.01+0.001 for p in pn) and any(w in k.lower() for w in ['rmse','r2','accuracy','f1','objective','optimal','best']))

print(f'❌ {miss} key values missing in manuscript' if miss else '✅ Key values consistent')

import sys; sys.exit(1 if miss>3 else 0)

" 2>/dev/null

    [ $? -ne 0 ] && GATE_FAIL=$((GATE_FAIL+1))

fi

# 22.5 "太完美"结果检测（AI 编造或过拟合特征）

echo "--- Unrealistic values validate ---"

if [ -f 图表/全部结果.json ]; then

    python3 -c "

import json

with open('图表/全部结果.json','r',encoding='utf-8') as f: data=json.load(f)

suspicious = []

def validate(name, val):

    if not isinstance(val,(int,float)) or isinstance(val,bool): return

    key = name.lower()

    if any(w in key for w in ['r2','r_squared','accuracy','acc','precision','recall','f1','auc']) and val > 0.999:

        suspicious.append(f'{name}={val:.4f} 过于完美（>0.999）')

    if any(w in key for w in ['rmse','mae','mse','loss']) and val == 0:

        suspicious.append(f'{name}=0 完美误差')

    if ('p_value' in key or 'pvalue' in key) and val == 0:

        suspicious.append(f'{name}=0 完美显著')

    if any(w in key for w in ['improvement','speedup','gain','提升']) and val > 10:

        suspicious.append(f'{name}={val} 提升过大（{val*100:.0f}%）')

def walk(obj, path=''):

    if isinstance(obj,dict):

        for k,v in obj.items(): walk(v, f'{path}.{k}')

    elif isinstance(obj,list):

        for i,v in enumerate(obj): walk(v, f'{path}[{i}]')

    else: validate(path, obj)

walk(data)

if suspicious:

    print(f'🚩 {len(suspicious)} 处可疑的完美结果（可能过拟合或数值编造）:')

    for s in suspicious[:5]: print(f'    {s}')

    print('  需在论文中阐明合理性，或回到 computational-realization 核验数据泄漏')

else:

    print('✅ 数值合理性通过')

" 2>/dev/null

fi

# 22.6 合理性复核章节是否出现（务必）

echo "--- 合理性复核章节核验 ---"

if [ -f 计算结果.md ]; then

    if grep -q '合理性审查\|数值合理\|背景对照\|sanity.*verify' 计算结果.md 2>/dev/null; then

        echo "✅ 计算结果.md 涵盖合理性复核章节"

    else

        echo "❌ 计算结果.md 缺少合理性复核章节 — 回到 computational-realization Phase 1.7 补充"

        GATE_FAIL=$((GATE_FAIL+1))

    fi

fi

# 22.7 数据源时间戳一致性（代码 vs 图形与表格 vs 论文）

echo "--- 数据源时间戳一致性 ---"

if [ -f 图表/全部结果.json ]; then

    JSON_TIME=$(stat -c %Y 图表/全部结果.json 2>/dev/null || stat -f %m 图表/全部结果.json 2>/dev/null || echo 0)

    # 核验是否有 PDF 图形与表格比 JSON 旧（阐明代码重跑了但图没更新）

    STALE_FIGS=0

    for pdf in 图表/*.pdf; do

        [ -f "$pdf" ] || continue

        PDF_TIME=$(stat -c %Y "$pdf" 2>/dev/null || stat -f %m "$pdf" 2>/dev/null || echo 0)

        if [ "$JSON_TIME" -gt "$PDF_TIME" ] && [ "$((JSON_TIME - PDF_TIME))" -gt 60 ]; then

            echo "  ⚠ $(basename $pdf) 比 全部结果.json 旧 — 图形与表格数据可能过期"

            STALE_FIGS=$((STALE_FIGS+1))

        fi

    done

    if [ "$STALE_FIGS" -gt 0 ]; then

        echo "  ❌ $STALE_FIGS 张图形与表格可能采用了旧数据（JSON 更新后图形与表格未重新产出）"

        echo "  → 推荐重跑 evidence-visualization 环节更新图形与表格"

        GATE_FAIL=$((GATE_FAIL+1))

    else

        echo "✅ 数据源时间戳保持一致"

    fi

fi

# 22.8 正文长表格检测（>12 行的表格不应在正文中完整展开）

echo "--- 正文长表格检测 ---"

LONG_TABLES=0

for f in 论文/章节/*.tex; do

    [ -f "$f" ] || continue

    # 跳过附录文件

    echo "$(basename $f)" | grep -qi 'appendix\|附录\|A_code' && continue

    # 统计各个 tabular/longtable 环境内的数据行数（\\ 的数量）

    python3 -c "

import re

with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:

    content = fh.read()

# 找全部 tabular/longtable 环境

for env in ['tabular', 'longtable', 'tabular*']:

    pattern = r'\\\\begin\{' + env + r'[*]?\}.*?\\\\end\{' + env + r'[*]?\}'

    for match in re.finditer(pattern, content, re.DOTALL):

        table_text = match.group()

        row_count = table_text.count('\\\\\\\\') - table_text.count('\\\\hline') // 2

        if row_count > 12:

            print(f'$(basename $f): {env} 有 {row_count} 行（>12）')

" 2>/dev/null | while read line; do

        echo "  ❌ $line — 正文表格超过 12 行，应截断（前3+后3+省略），完整版放附录"

        LONG_TABLES=$((LONG_TABLES+1))

    done

done

[ "$LONG_TABLES" -eq 0 ] && echo "✅ 正文无超长表格" || GATE_FAIL=$((GATE_FAIL+1))

# 23. AI 写作痕迹（列表环境）

echo "--- AI writing patterns ---"

AI_LISTS=0

for f in 论文/章节/*.tex; do

    [ -f "$f" ] || continue

    echo "$(basename $f)" | grep -qi 'appendix\|A_code' && continue

    c=$(grep -c '\\begin{itemize}\|\\begin{enumerate}' "$f" 2>/dev/null || echo 0)

    AI_LISTS=$((AI_LISTS+c))

done

[ "$AI_LISTS" -le 3 ] && echo "✅ AI patterns: $AI_LISTS lists" || { echo "❌ $AI_LISTS lists in body — convert to prose"; GATE_FAIL=$((GATE_FAIL+1)); }

# 24. 元叙述泄露

echo "--- Meta content leak ---"

META=0

for f in 论文/章节/*.tex; do

    [ -f "$f" ] || continue

    l=$(grep -ci 'RESULTS\.md\|META_MODEL_AGENT\.md\|MODELING_REPORT\|PROBLEM_ANALYSIS\|latex_includes' "$f" 2>/dev/null || echo 0)

    META=$((META+l))

done

[ "$META" -eq 0 ] && echo "✅ No meta leaks" || { echo "❌ $META meta content leaks"; GATE_FAIL=$((GATE_FAIL+1)); }

# 25. 过度声称

echo "--- Overclaiming ---"

OC=0

for f in 论文/章节/*.tex; do

    [ -f "$f" ] || continue

    for w in "首次提出" "首次发现" "完美" "最优的" "无可比拟" "前所未有" "开创性" "革命性"; do

        c=$(grep -c "$w" "$f" 2>/dev/null || echo 0); OC=$((OC+c))

    done

done

[ "$OC" -eq 0 ] && echo "✅ No overclaiming" || echo "⚠ $OC overclaiming instances"

echo ""

echo "=========================================="

if [ "$GATE_FAIL" -eq 0 ]; then

    echo "  ✅ ALL CRITICAL CHECKS PASSED — ready to submit"

else

    echo "  ❌ $GATE_FAIL CRITICAL FAILURES — MUST FIX prior to finishing"

    echo "  Go back and fix each ❌ item, recompile, then re-run this gate."

fi

echo "=========================================="

```

**⛔ If GATE_FAIL > 0, you MUST go back and fix every ❌ item, recompile, and re-run this gate. Do NOT output the final report with any ❌ remaining. Repeat until GATE_FAIL = 0.**

### 执行节点 8：Output report

Competition name, status, PDF path, total pages, body pages, compliance pass/fail.

## 核心规则

- No latexmk — manual step-by-step compilation

- Avoid delete .bbl file after compilation (bibliography data)

- Figure paths auto-corrected by compile_utils.sh: `图表/` → `../图表/`

- Total/countable pages ≤ MAX_PAGES. Page count is a ceiling;正文充分性按逐问论证链独立检查。

- Every embedded LaTeX figure must stay within `\linewidth` and `0.70\textheight` with `keepaspectratio`; every DOCX image must stay within the computed page body width. Oversized or unreadably shrunken figures are gate failures.

- Anonymous: no team info in body

- Primary output: `论文/数模论文.pdf`, temp files: `临时文件/`

