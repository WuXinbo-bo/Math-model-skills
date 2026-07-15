#!/bin/bash
# writing_check.sh — Post-writing quality checks
# Usage: bash 工具/writing_check.sh 论文/
# Checks: figure stacking, missing analysis, references, page estimate, unused figures

PAPER_DIR="${1:-paper}"
EXIT_CODE=0

echo "=== Writing quality checks ($PAPER_DIR) ==="

# 1. Figure-text interleaving: detect consecutive 图表/tables without text
echo "--- Figure stacking check ---"
total_stacking=0
total_no_analysis=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")

    # Detect consecutive figure/table environments with <3 lines of text between them
    s=$(awk '/\\end\{(figure|table)\}/{a=1;t=0;next} a&&/\\begin\{(figure|table)\}/{if(t<3)c++;a=0;next} a&&/[a-zA-Z\x80-\xff]{3,}/{t++} a&&t>=3{a=0} END{print c+0}' "$f")

    # Detect 图表/tables followed by <3 lines of analysis text
    n=$(awk '/\\end\{(figure|table)\}/{e=1;t=0;next} e&&/[a-zA-Z\x80-\xff]{10,}/{t++} e&&t>=3{e=0} e&&/\\(section|subsection|chapter|begin\{figure|begin\{table)/{if(t<3)c++;e=0} END{if(e&&t<3)c++;print c+0}' "$f")

    [ "$s" -gt 0 ] && echo "  FAIL $bn: $s figure stacking violations" && EXIT_CODE=1
    [ "$n" -gt 0 ] && echo "  FAIL $bn: $n 图表/tables missing analysis text" && EXIT_CODE=1
    total_stacking=$((total_stacking + s))
    total_no_analysis=$((total_no_analysis + n))
done
echo "  Total: $total_stacking stacking, $total_no_analysis missing analysis"
[ "$total_stacking" -eq 0 ] && [ "$total_no_analysis" -eq 0 ] && echo "  OK: figure-text interleaving passed"

# 2. References check
echo "--- References check ---"
if [ -f "$PAPER_DIR/references.bib" ]; then
    bib_count=$(grep -c '^@' "$PAPER_DIR/references.bib" 2>/dev/null || echo 0)
    echo "  references.bib: $bib_count entries"
    [ "$bib_count" -eq 0 ] && echo "  FAIL: references.bib is empty" && EXIT_CODE=1
else
    echo "  FAIL: references.bib not found" && EXIT_CODE=1
fi

# Collect cited keys
mkdir -p _tmp
grep -roh '\\cite[tp]*{[^}]*}' "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null \
  | grep -oP '\{[^}]+\}' | tr -d '{}' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort -u > _tmp/_cited_keys.txt 2>/dev/null
cited_count=$(wc -l < _tmp/_cited_keys.txt 2>/dev/null || echo 0)
echo "  Cited keys in text: $cited_count"

cite_in_body=$(grep -roh '\\cite' "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null | wc -l)
[ "$cite_in_body" -eq 0 ] && echo "  FAIL: no \\cite{} found in body text" && EXIT_CODE=1

# 3. Section character counts + page estimate
echo "--- Section sizes ---"
total_chars=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    chars=$(wc -c < "$f")
    total_chars=$((total_chars + chars))
    echo "  $(basename $f): $chars chars"
done
echo "  Total: $total_chars chars"

# 4. Unused PDF figures
echo "--- Unused figures ---"
unused=0
for pdf in 图表/*.pdf; do
    [ -f "$pdf" ] || continue
    bn=$(basename "$pdf")
    grep -rq "$bn" "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null || { echo "  WARN: $bn not referenced"; unused=$((unused + 1)); }
done
[ "$unused" -eq 0 ] && echo "  OK: all PDF figures referenced"

# 5. Placeholder check
echo "--- Placeholder check ---"
placeholders=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    if grep -qi 'PLACEHOLDER\|待补充\|TODO\|待续写' "$f" 2>/dev/null; then
        echo "  WARN: $(basename $f) contains placeholder markers"
        placeholders=$((placeholders + 1))
    fi
done
[ "$placeholders" -eq 0 ] && echo "  OK: no placeholders found"

# 6. Forbidden patterns
echo "--- Forbidden patterns ---"
grep -rn '\\input{.*figures' "$PAPER_DIR"/章节/*.tex 2>/dev/null && echo "  FAIL: \\input{图表/...} found" && EXIT_CODE=1
grep -rn 'colorlinks=true' "$PAPER_DIR"/*.tex "$PAPER_DIR"/章节/*.tex 2>/dev/null && echo "  FAIL: colorlinks=true found" && EXIT_CODE=1

# 7. AI writing pattern detection (itemize/enumerate in body text)
echo "--- AI writing patterns ---"
ai_patterns=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    # Skip appendix files
    echo "$bn" | grep -qi 'appendix\|附录\|code' && continue
    # Count itemize environments
    item_count=$(grep -c '\\begin{itemize}' "$f" 2>/dev/null || echo 0)
    enum_count=$(grep -c '\\begin{enumerate}' "$f" 2>/dev/null || echo 0)
    total_list=$((item_count + enum_count))
    if [ "$total_list" -gt 0 ]; then
        echo "  WARN $bn: $total_list bullet/numbered lists (itemize=$item_count, enumerate=$enum_count) — convert to flowing prose"
        ai_patterns=$((ai_patterns + total_list))
    fi
done
if [ "$ai_patterns" -gt 3 ]; then
    echo "  FAIL: $ai_patterns total lists in body text — strong AI writing signal, must convert to paragraphs"
    EXIT_CODE=1
elif [ "$ai_patterns" -gt 0 ]; then
    echo "  WARN: $ai_patterns lists found — consider converting to prose"
fi

# 7b. Figure-as-subject detection (段落以"图X展示了"开头 = AI 痕迹)
echo "--- Figure-as-subject check ---"
fig_subject=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    echo "$bn" | grep -qi 'appendix\|附录\|code\|symbol' && continue
    # 检测以图/表引用开头的段落（中文）
    hits=$(grep -cP '^\s*(如图|由图|从图|图\s*\\|图\d|如表|由表|从表|表\s*\\|表\d)' "$f" 2>/dev/null || echo 0)
    # 检测英文 "Figure X shows/presents/illustrates" 开头
    hits_en=$(grep -ciP '^\s*(Figure|Table|Fig\.|Tab\.)\s*\\' "$f" 2>/dev/null || echo 0)
    total_hits=$((hits + hits_en))
    if [ "$total_hits" -ge 3 ]; then
        echo "  WARN $bn: $total_hits 段以图/表引用开头 — 图表应作旁证融入论证，不要做段落主语"
        fig_subject=$((fig_subject + total_hits))
    fi
done
if [ "$fig_subject" -ge 5 ]; then
    echo "  FAIL: $fig_subject 处图表做主语 — 严重 AI 写作痕迹，需重写图文衔接"
    EXIT_CODE=1
elif [ "$fig_subject" -gt 0 ]; then
    echo "  WARN: $fig_subject 处图表做主语 — 建议改为括号旁注形式"
fi

# 7c. Meta-content leak detection (内部指令/文件名泄露到论文正文)
echo "--- Meta-content leak check ---"
meta_leaks=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    leaks=$(grep -ciP 'RESULTS\.md|META_MODEL_AGENT\.md|MODELING_REPORT|PROBLEM_ANALYSIS|图表/\*\.json|latex_includes|参赛者|参赛队伍|参赛选手' "$f" 2>/dev/null || echo 0)
    if [ "$leaks" -gt 0 ]; then
        echo "  FAIL $bn: $leaks 处内部指令/文件名泄露到正文"
        meta_leaks=$((meta_leaks + leaks))
        EXIT_CODE=1
    fi
done
[ "$meta_leaks" -eq 0 ] && echo "  OK: 无元叙述泄露"

# 8. Citation format check (Chinese papers: one cite per \cite{}, no multi-cite stacking)
echo "--- Citation format ---"
multi_cite=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    # Detect \cite{key1,key2,key3} — multiple keys in one cite
    mc=$(grep -oP '\\cite\{[^}]*,[^}]*\}' "$f" 2>/dev/null | wc -l)
    if [ "$mc" -gt 0 ]; then
        echo "  WARN $bn: $mc multi-cite instances (\\cite{a,b,c}) — split into separate \\cite{a}\\cite{b}\\cite{c}"
        multi_cite=$((multi_cite + mc))
    fi
done
[ "$multi_cite" -eq 0 ] && echo "  OK: all citations are single-key"

# 9. Symbol/assumptions page break check
echo "--- Symbol/assumptions page break ---"
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    is_target=false
    echo "$bn" | grep -qi 'symbol\|assumption' && is_target=true
    grep -q '\\section{符号说明}\|\\section{模型假设}' "$f" 2>/dev/null && is_target=true
    if [ "$is_target" = true ]; then
        # 符号说明：检查 \clearpage
        if grep -q '\\section{符号说明}\|\\section.*符号' "$f" 2>/dev/null; then
            if grep -B2 '\\section{' "$f" 2>/dev/null | grep -q '\\clearpage'; then
                echo "  OK $bn: has \\clearpage before symbol section"
            else
                echo "  WARN $bn: missing \\clearpage — compile_utils.sh will auto-fix"
            fi
        fi
        # 模型假设：检查 \needspace + \nopagebreak
        if grep -q '\\section{模型假设}\|\\section.*假设' "$f" 2>/dev/null; then
            if grep -B2 '\\section{' "$f" 2>/dev/null | grep -q '\\needspace\|\\clearpage'; then
                echo "  OK $bn: has page break control"
            else
                echo "  WARN $bn: missing \\needspace — compile_utils.sh will auto-fix"
            fi
        fi
    fi
done

echo "=== Writing checks done (exit code: $EXIT_CODE) ==="

# ==================== 新增检查（图表质量 + 数据一致性） ====================

# 10. 图片尺寸检查（太大溢出 / 太小看不清）
echo "--- 图片尺寸检查 ---"
size_issues=0
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    python3 -c "
import re
with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:
    content = fh.read()
for m in re.finditer(r'\\\\includegraphics\[([^\]]*)\]\{([^}]*)\}', content):
    opts, path = m.group(1), m.group(2)
    # 检查 width
    w = re.search(r'width\s*=\s*([\d.]+)\\\\textwidth', opts)
    if w:
        val = float(w.group(1))
        if val > 1.0:
            print(f'  WARN $bn: {path} width={val}\\\\textwidth > 1.0 — 图片溢出页面')
        elif val < 0.3:
            print(f'  WARN $bn: {path} width={val}\\\\textwidth < 0.3 — 图片可能太小')
    # 检查 scale
    s = re.search(r'scale\s*=\s*([\d.]+)', opts)
    if s:
        val = float(s.group(1))
        if val > 1.2:
            print(f'  WARN $bn: {path} scale={val} > 1.2 — 图片可能溢出')
" 2>/dev/null
done

# 11. 图片文件存在性检查
echo "--- 图片文件存在性检查 ---"
missing_figs=0
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    grep -oP '\\includegraphics\[[^\]]*\]\{([^}]+)\}' "$f" 2>/dev/null | grep -oP '\{[^}]+\}' | tr -d '{}' | while read -r figpath; do
        # 尝试从 论文/ 目录和根目录解析路径
        resolved=""
        for try_path in "$PAPER_DIR/$figpath" "$figpath" "图表/$(basename $figpath)"; do
            [ -f "$try_path" ] && resolved="$try_path" && break
        done
        if [ -z "$resolved" ]; then
            echo "  FAIL $bn: 引用的图片不存在: $figpath"
            missing_figs=$((missing_figs + 1))
        fi
    done
done
[ "$missing_figs" -eq 0 ] && echo "  OK: 所有引用的图片文件都存在"

# 12. 空的 figure/table 环境检查（有 caption 但没有 includegraphics/tabular）
echo "--- 空图表环境检查 ---"
empty_envs=0
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    python3 -c "
import re
with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:
    content = fh.read()
# 检查 figure 环境
for m in re.finditer(r'\\\\begin\{figure\}.*?\\\\end\{figure\}', content, re.DOTALL):
    block = m.group()
    has_image = 'includegraphics' in block
    has_tikz = 'tikzpicture' in block
    has_input = '\\\\input' in block
    if not has_image and not has_tikz and not has_input:
        cap = re.search(r'\\\\caption\{([^}]{0,50})', block)
        cap_text = cap.group(1) if cap else '(no caption)'
        print(f'  FAIL $bn: 空 figure 环境 \"{cap_text}\" — 缺少 includegraphics')
# 检查 table 环境
for m in re.finditer(r'\\\\begin\{table\}.*?\\\\end\{table\}', content, re.DOTALL):
    block = m.group()
    has_tabular = 'tabular' in block or 'longtable' in block
    has_input = '\\\\input' in block
    if not has_tabular and not has_input:
        cap = re.search(r'\\\\caption\{([^}]{0,50})', block)
        cap_text = cap.group(1) if cap else '(no caption)'
        print(f'  FAIL $bn: 空 table 环境 \"{cap_text}\" — 缺少 tabular')
" 2>/dev/null
done

# 13. 图表浮动位置检查（数模竞赛必须用 [H] 或 [htbp]，不能没有位置参数）
echo "--- 图表浮动位置检查 ---"
float_issues=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    # 检查 \begin{figure} 后面没有 [H] 或 [htbp] 的情况
    no_pos=$(grep -cP '\\begin\{figure\}\s*$' "$f" 2>/dev/null || echo 0)
    if [ "$no_pos" -gt 0 ]; then
        echo "  WARN $bn: $no_pos 个 figure 环境没有位置参数 — 建议加 [H] 或 [htbp]"
        float_issues=$((float_issues + no_pos))
    fi
    no_pos_t=$(grep -cP '\\begin\{table\}\s*$' "$f" 2>/dev/null || echo 0)
    if [ "$no_pos_t" -gt 0 ]; then
        echo "  WARN $bn: $no_pos_t 个 table 环境没有位置参数 — 建议加 [H] 或 [htbp]"
        float_issues=$((float_issues + no_pos_t))
    fi
done
[ "$float_issues" -eq 0 ] && echo "  OK: 所有图表都有浮动位置参数"

# 14. Caption 长度检查（≤15 个中文字 / ≤10 个英文单词）
echo "--- Caption 长度检查 ---"
long_captions=0
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    python3 -c "
import re
with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:
    content = fh.read()
for m in re.finditer(r'\\\\caption\{([^}]+)\}', content):
    cap = m.group(1).strip()
    # 计算中文字符数
    zh_chars = len(re.findall(r'[\u4e00-\u9fff]', cap))
    total_len = len(cap)
    if zh_chars > 0 and zh_chars > 20:
        print(f'  WARN $bn: caption 过长（{zh_chars}字）: \"{cap[:30]}...\"')
    elif zh_chars == 0 and len(cap.split()) > 15:
        print(f'  WARN $bn: caption too long ({len(cap.split())} words): \"{cap[:40]}...\"')
" 2>/dev/null
done

# 15. 图文数值一致性检查
echo "--- 图文数值一致性检查 ---"
consistency_issues=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    fig_claims=$(grep -n '\\ref{fig' "$f" 2>/dev/null | grep -oP '\d+\.\d+' | head -20)
    if [ -n "$fig_claims" ]; then
        not_found=0
        for num in $fig_claims; do
            if ! grep -rq "$num" 计算结果.md 图表/*.json 2>/dev/null; then
                not_found=$((not_found+1))
            fi
        done
        if [ "$not_found" -gt 0 ]; then
            echo "  WARN $bn: $not_found 个数值在 \\ref{fig} 附近但不在 计算结果.md/JSON 中"
            consistency_issues=$((consistency_issues + not_found))
        fi
    fi
done
[ "$consistency_issues" -eq 0 ] && echo "  OK: 图文数值一致性通过"

# === NEW: 数值一致性检查 ===
echo "--- 数值一致性检查 ---"
if [ -f 图表/全部结果.json ]; then
    python3 -c "
import json, re, sys, os

# 读取 JSON 结果
with open('图表/全部结果.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# 提取 JSON 中的所有数值（递归）
def extract_numbers(obj, prefix=''):
    nums = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            nums.update(extract_numbers(v, f'{prefix}.{k}'))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            nums.update(extract_numbers(v, f'{prefix}[{i}]'))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        if abs(obj) > 0.001 and abs(obj) < 1e10:  # 忽略极小和极大值
            nums[prefix] = obj
    return nums

json_nums = extract_numbers(results)
if not json_nums:
    print('  (JSON 中无有效数值，跳过)')
    sys.exit(0)

# 扫描论文中的数字
paper_dir = '$PAPER_DIR'
paper_nums = set()
for tex_file in sorted(os.listdir(os.path.join(paper_dir, '章节'))):
    if not tex_file.endswith('.tex'):
        continue
    with open(os.path.join(paper_dir, '章节', tex_file), 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    # 提取所有小数（如 0.023, 95.6, 12345）
    for m in re.finditer(r'(?<![a-zA-Z])(\d+\.?\d+)(?![a-zA-Z_{}])', text):
        try:
            paper_nums.add(float(m.group(1)))
        except ValueError:
            pass

# 检查关键 JSON 数值是否在论文中出现
missing = 0
for key, val in json_nums.items():
    # 检查精确匹配或近似匹配（±1%）
    found = False
    for pn in paper_nums:
        if abs(pn - val) < abs(val) * 0.01 + 0.001:
            found = True
            break
    if not found and 'round' not in key.lower() and 'time' not in key.lower():
        # 只报告可能重要的数值（跳过时间、轮次等）
        if any(kw in key.lower() for kw in ['rmse', 'r2', 'mse', 'accuracy', 'f1', 'auc', 'objective', 'optimal', 'best', 'result', 'score']):
            print(f'  ⚠ JSON {key}={val} 未在论文中找到匹配数值')
            missing += 1

if missing > 0:
    print(f'  共 {missing} 个关键数值可能不一致')
else:
    print('  ✅ 关键数值一致性检查通过')
" 2>/dev/null || echo "  (Python 不可用，跳过数值一致性检查)"
else
    echo "  (图表/全部结果.json 不存在，跳过)"
fi

# === NEW: 过度声称检测 ===
echo "--- 过度声称检测 ---"
OVERCLAIM=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    # 检测中文过度声称
    for word in "首次提出" "首次发现" "完美" "最优的" "最好的" "证明了" "无可比拟" "前所未有" "开创性" "革命性"; do
        count=$(grep -c "$word" "$f" 2>/dev/null || echo 0)
        if [ "$count" -gt 0 ]; then
            echo "  ⚠ $bn: 发现过度声称 \"$word\" ($count 次) — 建议改为更谨慎的表述"
            OVERCLAIM=$((OVERCLAIM + count))
        fi
    done
done
[ "$OVERCLAIM" -eq 0 ] && echo "  ✅ 无过度声称"

# === NEW: 内容覆盖度检查 ===
echo "--- 内容覆盖度检查 ---"
if [ -f 问题分析.md ]; then
    PROB_COUNT=$(grep -c '问题[一二三四五六七八九十]' 问题分析.md 2>/dev/null || echo 0)
    # 检查论文是否每个子问题都有对应章节
    CHAPTER_COUNT=0
    for f in "$PAPER_DIR"/章节/*.tex; do
        [ -f "$f" ] || continue
        grep -q '\\section{.*问题[一二三四五六七八九十0-9]\|\\section{.*Problem' "$f" 2>/dev/null && CHAPTER_COUNT=$((CHAPTER_COUNT + 1))
    done
    echo "  赛题子问题数: $PROB_COUNT, 论文子问题章节数: $CHAPTER_COUNT"
    [ "$CHAPTER_COUNT" -lt "$PROB_COUNT" ] && echo "  ⚠ 论文可能遗漏了部分子问题的章节" && EXIT_CODE=1
fi

# === NEW: 引用完整性检查 ===
echo "--- 引用完整性检查 ---"
if [ -f "$PAPER_DIR/references.bib" ]; then
    # 提取论文中所有 \cite{} 的 key
    CITED_KEYS=$(grep -roh '\\cite{[^}]*}' "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null | grep -oP '\{[^}]+\}' | tr -d '{}' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort -u)
    # 提取 bib 文件中所有条目 key
    BIB_KEYS=$(grep -oP '^\s*@\w+\{([^,]+)' "$PAPER_DIR/references.bib" 2>/dev/null | sed 's/.*{//' | sort -u)
    MISSING_BIB=0
    for key in $CITED_KEYS; do
        if ! echo "$BIB_KEYS" | grep -qx "$key" 2>/dev/null; then
            echo "  ⚠ \\cite{$key} 在 references.bib 中无对应条目"
            MISSING_BIB=$((MISSING_BIB + 1))
        fi
    done
    [ "$MISSING_BIB" -eq 0 ] && echo "  ✅ 所有引用都有对应 bib 条目"
elif [ -f "$PAPER_DIR/论文正文.tex" ] && grep -q 'thebibliography' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
    echo "  (使用 thebibliography 环境，跳过 bib 文件检查)"
else
    echo "  ⚠ 未找到 references.bib"
fi

echo ""
echo "=== Writing check complete (exit=$EXIT_CODE) ==="
exit $EXIT_CODE
