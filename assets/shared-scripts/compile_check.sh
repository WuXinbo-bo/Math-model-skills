#!/bin/bash
# compile_check.sh — Post-compilation quality checks
# Usage: bash 工具/compile_check.sh 论文/
# Checks: PDF exists, undefined refs, TOC, abstracts, bibliography, unused figures, figure stacking

PAPER_DIR="${1:-paper}"
EXIT_CODE=0

echo "=== Post-compile checks ($PAPER_DIR) ==="

# 1. PDF existence and size
if [ -f "$PAPER_DIR/数模论文.pdf" ]; then
    pdf_size=$(wc -c < "$PAPER_DIR/数模论文.pdf")
    echo "  OK: 数模论文.pdf exists ($pdf_size bytes)"
    [ "$pdf_size" -lt 100000 ] && echo "  FAIL: PDF is small (<100KB), compilation likely failed" && EXIT_CODE=1
else
    echo "  FAIL: 数模论文.pdf not found" && EXIT_CODE=1
fi

# 2. Undefined references
undef_refs=$(grep -c '\[?\]' "$PAPER_DIR/编译日志.log" 2>/dev/null || echo 0)
echo "  Undefined references: $undef_refs"
[ "$undef_refs" -gt 0 ] && echo "  FAIL: $undef_refs undefined references — PDF shows [?]" && EXIT_CODE=1

# 2.5 LaTeX compilation errors (CRITICAL — must fix before accepting)
echo "--- LaTeX errors ---"
LATEX_ERRORS=0
if [ -f "$PAPER_DIR/编译日志.log" ]; then
    # Bad math environment delimiter
    bad_math=$(grep -c 'Bad math environment delimiter\|Missing \$ inserted\|Display math should end\|begin{document} ended by' "$PAPER_DIR/编译日志.log" 2>/dev/null || echo 0)
    [ "$bad_math" -gt 0 ] && echo "  CRITICAL: $bad_math math environment errors — fix \$...\$ delimiters in .tex files" && LATEX_ERRORS=$((LATEX_ERRORS + bad_math))

    # Not allowed in LR mode (usually math in wrong context)
    lr_mode=$(grep -c 'Not allowed in LR mode\|Not in outer par mode' "$PAPER_DIR/编译日志.log" 2>/dev/null || echo 0)
    [ "$lr_mode" -gt 0 ] && echo "  CRITICAL: $lr_mode LR mode errors — check math/float placement" && LATEX_ERRORS=$((LATEX_ERRORS + lr_mode))

    # Undefined control sequence (missing package or typo)
    undef_cs=$(grep -c 'Undefined control sequence' "$PAPER_DIR/编译日志.log" 2>/dev/null || echo 0)
    [ "$undef_cs" -gt 0 ] && echo "  WARN: $undef_cs undefined control sequences"

    # Missing package
    missing_pkg=$(grep -oP 'File .* not found\.|LaTeX Error: File .* not found' "$PAPER_DIR/编译日志.log" 2>/dev/null | head -5)
    [ -n "$missing_pkg" ] && echo "  CRITICAL: missing packages:" && echo "$missing_pkg" | sed 's/^/    /' && LATEX_ERRORS=$((LATEX_ERRORS + 1))

    # Font not found
    font_err=$(grep -c 'Font.*not found\|cannot find font' "$PAPER_DIR/编译日志.log" 2>/dev/null || echo 0)
    [ "$font_err" -gt 0 ] && echo "  WARN: $font_err font errors (check fc-list)"

    # Extract specific error locations for Meta-model-agent to fix
    if [ "$LATEX_ERRORS" -gt 0 ]; then
        echo ""
        echo "  ============================================================"
        echo "  CRITICAL: $LATEX_ERRORS LaTeX errors found — MUST FIX"
        echo "  ============================================================"
        echo "  Error locations (from 编译日志.log):"
        grep -B1 'Bad math\|Missing \$ inserted\|begin{document} ended\|Not allowed in LR mode' "$PAPER_DIR/编译日志.log" 2>/dev/null | grep -E '^\./|^l\.' | head -20 | sed 's/^/    /'
        echo "  ============================================================"
        echo ""
        EXIT_CODE=1
    fi
fi

# 3. Overfull hbox
overfull=$(grep -c 'Overfull.*hbox' "$PAPER_DIR/编译日志.log" 2>/dev/null || echo 0)
echo "  Overfull hbox: $overfull"

# 3.5 Overfull vbox (table/figure overflow — content cut off at page bottom)
overfull_v=$(grep -c 'Overfull.*vbox' "$PAPER_DIR/编译日志.log" 2>/dev/null || echo 0)
if [ "$overfull_v" -gt 0 ]; then
    echo "  FAIL: $overfull_v overfull vbox — tables/figures cut off at page bottom"
    echo "  Fix: use longtable for tall tables, or split into smaller tables"
    EXIT_CODE=1
fi

# 3.6 Tall table detection (tables with many rows that might overflow)
echo "--- Tall table check ---"
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    echo "$bn" | grep -qi 'appendix\|附录\|A_code' && continue
    python3 -c "
import re, sys
with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:
    content = fh.read()
fail = False
for m in re.finditer(r'\\\\begin\{tabular\}.*?\\\\end\{tabular\}', content, re.DOTALL):
    block = m.group()
    rows = block.count('\\\\\\\\')
    if rows > 20:
        start = max(0, m.start() - 200)
        before = content[start:m.start()]
        cap = re.search(r'\\\\caption\{([^}]{0,50})', before)
        cap_text = cap.group(1) if cap else '(unknown)'
        print(f'  FAIL: $bn has {rows}-row table \"{cap_text}\" — must truncate to top5+bottom3, full table in appendix')
        fail = True
sys.exit(1 if fail else 0)
" 2>/dev/null
    [ $? -ne 0 ] && EXIT_CODE=1
done

# 4. TOC generation
if grep -q 'tableofcontents' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
    [ -s "$PAPER_DIR/论文正文.toc" ] && echo "  OK: TOC generated" || { echo "  FAIL: TOC empty or missing"; EXIT_CODE=1; }
fi

# 5. Abstract check — skipped (requirements vary by competition: Chinese-only, English-only, or both)

# 6. Bibliography
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    # 5.5 Template integrity check — auto-detect template type and check its specific features
    echo "--- Template integrity (auto-detect) ---"

    # Detect template type from documentclass
    TMPL_TYPE="unknown"
    grep -q 'cumcmthesis' "$PAPER_DIR/论文正文.tex" 2>/dev/null && TMPL_TYPE="cumcm"
    grep -q 'gmcmthesis' "$PAPER_DIR/论文正文.tex" 2>/dev/null && TMPL_TYPE="huawei"
    grep -q 'MathorCupmodeling' "$PAPER_DIR/论文正文.tex" 2>/dev/null && TMPL_TYPE="mathorcup"
    grep -q 'JXUSTmodeling' "$PAPER_DIR/论文正文.tex" 2>/dev/null && TMPL_TYPE="huashubei"
    grep -q 'yrdmcm' "$PAPER_DIR/论文正文.tex" 2>/dev/null && TMPL_TYPE="changsanjiao"
    grep -q 'neepumcm' "$PAPER_DIR/论文正文.tex" 2>/dev/null && TMPL_TYPE="diangongbei"
    grep -q 'nemcmthesis' "$PAPER_DIR/论文正文.tex" 2>/dev/null && TMPL_TYPE="dongsansheng"
    grep -q 'mcmthesis' "$PAPER_DIR/论文正文.tex" 2>/dev/null && [ "$TMPL_TYPE" = "unknown" ] && TMPL_TYPE="mcm"
    grep -q '51mcmthesis' "$PAPER_DIR/论文正文.tex" 2>/dev/null && TMPL_TYPE="wuyi"
    grep -q 'mcmicm' "$PAPER_DIR/论文正文.tex" 2>/dev/null && TMPL_TYPE="mcm"
    grep -q 'apmcmthesis' "$PAPER_DIR/论文正文.tex" 2>/dev/null && TMPL_TYPE="apmcm"
    grep -qi '统计建模\|natbib.*numbers.*square.*super\|listoftables' "$PAPER_DIR/论文正文.tex" 2>/dev/null && TMPL_TYPE="stats"
    # 五一杯：cumcmthesis + withoutpreface + 承诺书
    if [ "$TMPL_TYPE" = "cumcm" ] && grep -q 'withoutpreface' "$PAPER_DIR/论文正文.tex" 2>/dev/null && grep -q '五一' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        TMPL_TYPE="wuyi"
    fi
    # 华中杯：cumcmthesis + withoutpreface（无五一杯标识）
    if [ "$TMPL_TYPE" = "cumcm" ] && grep -q 'withoutpreface' "$PAPER_DIR/论文正文.tex" 2>/dev/null && ! grep -q '五一' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        TMPL_TYPE="huazhong"
    fi
    echo "  Detected template: $TMPL_TYPE"

    # --- Package conflict check (all templates) ---
    echo "--- Package conflict check ---"
    if grep -q '\\usepackage{cite}' "$PAPER_DIR/论文正文.tex" 2>/dev/null && grep -q '\\usepackage.*{natbib}' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        echo "  CRITICAL: cite + natbib both loaded — these packages CONFLICT, remove \\usepackage{cite}"
        EXIT_CODE=1
    fi
    # Check for packages duplicated between 论文正文.tex and cls
    for pkg in subcaption float graphicx booktabs caption; do
        if grep -q "\\\\usepackage.*{.*$pkg.*}" "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            case "$TMPL_TYPE" in
                cumcm|wuyi|huazhong) # cumcmthesis.cls loads subcaption, float, graphicx, booktabs
                    case "$pkg" in subcaption|float|graphicx|booktabs)
                        echo "  WARN: $pkg duplicated (cls already loads it)" ;;
                    esac ;;
                huashubei) # JXUSTmodeling.cls loads subcaption, caption, booktabs, multirow, graphicx, placeins
                    case "$pkg" in subcaption|caption|booktabs|graphicx)
                        echo "  WARN: $pkg duplicated (cls already loads it)" ;;
                    esac ;;
                changsanjiao|diangongbei) # yrdmcm/neepumcm.cls loads graphicx, booktabs, colortbl, xcolor
                    case "$pkg" in graphicx|booktabs)
                        echo "  WARN: $pkg duplicated (cls already loads it)" ;;
                    esac ;;
            esac
        fi
    done

    # --- Per-template specific checks ---
    case "$TMPL_TYPE" in
        wuyi)
            echo "--- 五一杯 specific checks ---"
            grep -q '承诺书' "$PAPER_DIR/论文正文.tex" && echo "  OK: 承诺书页存在" || { echo "  CRITICAL: 五一杯缺少承诺书页"; EXIT_CODE=1; }
            grep -q 'image2' "$PAPER_DIR/论文正文.tex" && echo "  OK: 封面 logo (image2) 存在" || { echo "  CRITICAL: 五一杯缺少封面 logo"; EXIT_CODE=1; }
            grep -q '关键词' "$PAPER_DIR/论文正文.tex" && echo "  OK: 关键词位置存在" || { echo "  CRITICAL: 五一杯缺少关键词"; EXIT_CODE=1; }
            grep -q 'withoutpreface' "$PAPER_DIR/论文正文.tex" && echo "  OK: withoutpreface 选项存在" || { echo "  CRITICAL: 缺少 withoutpreface（会出现国赛承诺书）"; EXIT_CODE=1; }
            grep -q '\\maketitle' "$PAPER_DIR/论文正文.tex" && { echo "  CRITICAL: 五一杯不应有 \\maketitle（会和手写承诺书冲突）"; EXIT_CODE=1; } || echo "  OK: 无 \\maketitle"
            grep -q '五一数学建模竞赛' "$PAPER_DIR/论文正文.tex" && echo "  OK: 五一杯标题存在" || { echo "  CRITICAL: 缺少'五一数学建模竞赛'标题 — 论文正文.tex 可能被重写了"; EXIT_CODE=1; }
            # 检查 image2 文件是否存在
            if [ -f "$PAPER_DIR/image2.png" ] || [ -f "$PAPER_DIR/image2.jpg" ] || [ -f "图表/image2.png" ]; then
                echo "  OK: image2 图片文件存在"
            else
                echo "  CRITICAL: image2 图片文件不存在 — 封面 logo 会显示为空"
                EXIT_CODE=1
            fi
            ;;
        huazhong)
            echo "--- 华中杯 specific checks ---"
            grep -q 'cumcmthesis' "$PAPER_DIR/论文正文.tex" && echo "  OK: 使用 cumcmthesis cls" || { echo "  CRITICAL: 华中杯未使用 cumcmthesis"; EXIT_CODE=1; }
            grep -q 'withoutpreface' "$PAPER_DIR/论文正文.tex" && echo "  OK: withoutpreface 选项存在" || { echo "  CRITICAL: 缺少 withoutpreface"; EXIT_CODE=1; }
            grep -q '\\begin{abstract}' "$PAPER_DIR/论文正文.tex" && echo "  OK: 使用 abstract 环境" || echo "  WARN: 华中杯应使用 \\begin{abstract} 环境"
            grep -q 'thebibliography' "$PAPER_DIR/论文正文.tex" && echo "  OK: 使用 thebibliography" || echo "  WARN: 华中杯应使用 thebibliography 环境"
            ;;
        mathorcup)
            echo "--- MathorCup specific checks ---"
            grep -q 'MathorCupmodeling' "$PAPER_DIR/论文正文.tex" && echo "  OK: 使用 MathorCupmodeling cls" || { echo "  CRITICAL: MathorCup 未使用正确 cls"; EXIT_CODE=1; }
            grep -q '\\bianhao\|\\tihao\|\\timu' "$PAPER_DIR/论文正文.tex" && echo "  OK: 队伍信息命令存在" || { echo "  CRITICAL: MathorCup 缺少队伍信息"; EXIT_CODE=1; }
            grep -q '\\maketitle' "$PAPER_DIR/论文正文.tex" && { echo "  CRITICAL: MathorCup 不应有独立封面 \\maketitle"; EXIT_CODE=1; } || echo "  OK: 无独立封面"
            ;;
        stats)
            echo "--- 统计建模 specific checks ---"
            grep -q 'listoftables' "$PAPER_DIR/论文正文.tex" && echo "  OK: \\listoftables present" || { echo "  CRITICAL: \\listoftables missing — template was rewritten!"; EXIT_CODE=1; }
            grep -q 'listoffigures' "$PAPER_DIR/论文正文.tex" && echo "  OK: \\listoffigures present" || { echo "  CRITICAL: \\listoffigures missing — template was rewritten!"; EXIT_CODE=1; }
            grep -q 'cline{2-2}' "$PAPER_DIR/论文正文.tex" && echo "  OK: cover page \\cline present" || echo "  WARN: cover page \\cline missing"
            if grep -P '^(表|图)\d+\.' "$PAPER_DIR/论文正文.tex" 2>/dev/null | head -3 | grep -q '.'; then
                echo "  CRITICAL: hand-written figure/table list detected — must use \\listoftables/\\listoffigures"
                EXIT_CODE=1
            fi
            ;;
        dongsansheng)
            echo "--- 东三省 specific checks ---"
            grep -q 'nemcmthesis' "$PAPER_DIR/论文正文.tex" && echo "  OK: 使用 nemcmthesis cls" || { echo "  CRITICAL: 未使用 nemcmthesis"; EXIT_CODE=1; }
            grep -q '\\ttle\|\\title' "$PAPER_DIR/论文正文.tex" && echo "  OK: 标题命令存在" || echo "  WARN: 缺少标题"
            grep -q '\\makecoverpage' "$PAPER_DIR/论文正文.tex" && echo "  OK: 封面生成命令存在" || echo "  WARN: 缺少 \\makecoverpage"
            ;;
        huawei)
            echo "--- 华为杯 specific checks ---"
            grep -q 'gmcmthesis' "$PAPER_DIR/论文正文.tex" && echo "  OK: 使用 gmcmthesis cls" || { echo "  CRITICAL: 华为杯未使用 gmcmthesis"; EXIT_CODE=1; }
            ;;
        *)
            echo "  (no template-specific checks for $TMPL_TYPE)"
            ;;
    esac

    grep -q '\\bibliography' "$PAPER_DIR/论文正文.tex" 2>/dev/null && echo "  OK: \\bibliography command present" || { echo "  FAIL: no \\bibliography in 论文正文.tex"; EXIT_CODE=1; }
    if [ -f "$PAPER_DIR/references.bib" ]; then
        bib_entries=$(grep -c '^@' "$PAPER_DIR/references.bib" 2>/dev/null || echo 0)
        echo "  OK: references.bib ($bib_entries entries)"
    else
        echo "  FAIL: references.bib not found" && EXIT_CODE=1
    fi
    bbl_entries=$(grep -c '\\bibitem' "$PAPER_DIR/论文正文.bbl" 2>/dev/null || echo 0)
    echo "  Bibliography entries in PDF: $bbl_entries"
    [ "$bbl_entries" -eq 0 ] && echo "  FAIL: bibliography is empty in compiled PDF" && EXIT_CODE=1
fi

# 7. Citation count in body
cite_count=$(grep -roh '\\cite{' "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null | wc -l)
echo "  Citations in body: $cite_count"
[ "$cite_count" -eq 0 ] && echo "  FAIL: no citations in body text" && EXIT_CODE=1

# 7.5 Citation format check (上标/顺序)
echo "--- Citation format check ---"
# 7.5.1 检查是否有 \cite{} 被标点符号包围但没有上标（GB/T 7714 要求上标）
# 中文论文要求引用用上标，所以 \cite{} 前面应该是 \upcite{} 或 \textsuperscript{\cite{}}
# 检查 论文正文.tex 的 bibliographystyle 和 \cite 用法
if grep -q '\\bibliographystyle{gbt7714\|plainnat.*super\|natbib.*super' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
    echo "  OK: 使用上标引用样式 (gbt7714-numerical / natbib super)"
elif grep -q '\\bibliographystyle{plainnat}\|\\bibliographystyle{plain}\|\\bibliographystyle{unsrt}' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
    # 非上标样式 - 检查是否手动用 \upcite 或 \textsuperscript
    upcite_count=$(grep -roh '\\upcite{\|\\textsuperscript{\\cite' "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null | wc -l)
    plain_cite_count=$(grep -roh '[^t]\\cite{' "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null | wc -l)
    if [ "$upcite_count" -eq 0 ] && [ "$plain_cite_count" -gt 0 ]; then
        echo "  FAIL: $plain_cite_count citations not using superscript format"
        echo "  Fix: 改用 \\bibliographystyle{gbt7714-numerical} 或把 \\cite{x} 改为 \\upcite{x} / \\textsuperscript{\\cite{x}}"
        EXIT_CODE=1
    else
        echo "  OK: citations use superscript ($upcite_count superscript, $plain_cite_count plain)"
    fi
fi

# 7.5.2 单处多引用检查（[1,3,5] 是否按顺序 + 是否合并）
echo "--- Citation order and merging ---"
python3 -c "
import re, sys
from pathlib import Path

paper_dir = Path('$PAPER_DIR')
tex_files = list(paper_dir.glob('章节/*.tex')) + [paper_dir / '论文正文.tex']

all_errors = []
cite_order_global = []  # 记录全文 cite 首次出现顺序（这就是最终编号顺序）

# 第一遍：收集所有 cite key 的全局首次出现顺序（这就是它们的最终编号）
for f in tex_files:
    if not f.exists(): continue
    try:
        content = f.read_text(encoding='utf-8', errors='ignore')
    except: continue
    for m in re.finditer(r'\\\\(up)?cite\{([^}]+)\}', content):
        keys = [k.strip() for k in m.group(2).split(',')]
        for k in keys:
            if k not in cite_order_global:
                cite_order_global.append(k)

# 第二遍：检查每处 \cite 的内部顺序 + 编号全局递增跳跃
prev_max_num = 0
for f in tex_files:
    if not f.exists(): continue
    try:
        content = f.read_text(encoding='utf-8', errors='ignore')
    except: continue
    
    for m in re.finditer(r'\\\\(up)?cite\{([^}]+)\}', content):
        keys = [k.strip() for k in m.group(2).split(',')]
        nums = [cite_order_global.index(k)+1 if k in cite_order_global else 999 for k in keys]
        line_num = content[:m.start()].count('\n') + 1
        snippet = m.group(0)
        
        # 检查1: 多引用内部必须升序（如 [1,2,5] 不能写成 [5,1,2]）
        if len(nums) > 1 and nums != sorted(nums):
            all_errors.append(f'  FAIL {f.name}:{line_num}: 多引用编号不是升序 {nums}: {snippet}')
        
        # 检查2: 新引用编号跳跃（如之前最大是3，新引用直接是[8]）
        cur_max = max(nums) if nums else 0
        if cur_max > prev_max_num + 1:
            # 新引用应该紧接在 prev_max_num+1，但出现了更大的编号
            new_keys = [k for k, n in zip(keys, nums) if n > prev_max_num]
            if new_keys:
                all_errors.append(f'  WARN {f.name}:{line_num}: 引用编号跳跃 (之前最大={prev_max_num}, 当前新引用={max(n for n in nums if n > prev_max_num)}): {snippet}')
        prev_max_num = max(prev_max_num, cur_max)

if all_errors:
    print('\n'.join(all_errors[:15]))
    if len(all_errors) > 15:
        print(f'  ... and {len(all_errors)-15} more')
    sys.exit(1)
else:
    print('  OK: 引用编号全局递增且多引用内部升序')
" 2>/dev/null
[ $? -ne 0 ] && echo "  (see above)" && EXIT_CODE=1

# 7.5.3 连续单引用合并检查（如 \cite{a}\cite{b} 应合并为 \cite{a,b}）
echo "--- Consecutive citation merging ---"
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    # 检查 \cite{x}\cite{y} 或 \cite{x} \cite{y} 这种相邻引用
    consec=$(grep -oE '\\(up)?cite\{[^}]+\}[[:space:]]*\\(up)?cite\{[^}]+\}' "$f" 2>/dev/null | wc -l)
    if [ "$consec" -gt 0 ]; then
        echo "  WARN $bn: $consec consecutive \\cite{} should merge to \\cite{a,b}"
    fi
done

# 8. Unused PDF figures
echo "--- Unused figures ---"
unused=0
for pdf in 图表/*.pdf; do
    [ -f "$pdf" ] || continue
    bn=$(basename "$pdf")
    grep -rq "$bn" "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null || { echo "  WARN: $bn not referenced"; unused=$((unused + 1)); }
done
[ "$unused" -eq 0 ] && echo "  OK: all figures referenced"

# 8.5 Missing figure files (referenced but not found)
echo "--- Missing figure files ---"
missing=0
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    grep -oP '\\includegraphics\[[^\]]*\]\{([^}]+)\}' "$f" 2>/dev/null | grep -oP '\{[^}]+\}' | tr -d '{}' | while read -r figpath; do
        resolved=""
        for try_path in "$PAPER_DIR/$figpath" "$figpath" "图表/$(basename $figpath)"; do
            [ -f "$try_path" ] && resolved="$try_path" && break
        done
        if [ -z "$resolved" ]; then
            echo "  FAIL $bn: missing figure: $figpath"
            missing=$((missing + 1))
            EXIT_CODE=1
        fi
    done
done
[ "$missing" -eq 0 ] && echo "  OK: all referenced figures exist"

# 8.6 Empty figure/table environments
echo "--- Empty figure/table environments ---"
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    python3 -c "
import re
with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:
    content = fh.read()
for m in re.finditer(r'\\\\begin\{figure\}.*?\\\\end\{figure\}', content, re.DOTALL):
    block = m.group()
    if 'includegraphics' not in block and 'tikzpicture' not in block and '\\\\input' not in block:
        cap = re.search(r'\\\\caption\{([^}]{0,50})', block)
        cap_text = cap.group(1) if cap else '(no caption)'
        print(f'  FAIL $bn: empty figure \"{cap_text}\"')
for m in re.finditer(r'\\\\begin\{table\}.*?\\\\end\{table\}', content, re.DOTALL):
    block = m.group()
    if 'tabular' not in block and 'longtable' not in block and '\\\\input' not in block:
        cap = re.search(r'\\\\caption\{([^}]{0,50})', block)
        cap_text = cap.group(1) if cap else '(no caption)'
        print(f'  FAIL $bn: empty table \"{cap_text}\"')
" 2>/dev/null
done

# 9. Figure stacking (same check as writing_check.sh)
echo "--- Figure stacking ---"
total_stacking=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    count=$(awk '/\\end\{(figure|table)\}/{a=1;t=0;next} a&&/\\begin\{(figure|table)\}/{if(t<3){c++}a=0;next} a&&/[a-zA-Z\x80-\xff]{3,}/{t++} a&&t>=3{a=0} END{print c+0}' "$f")
    [ "$count" -gt 0 ] && echo "  FAIL: $bn has $count figure stacking violations — add analysis text between figures" && EXIT_CODE=1
    total_stacking=$((total_stacking + count))
done
[ "$total_stacking" -eq 0 ] && echo "  OK: no figure stacking"

# 9.5 Subfigure abuse and small figure width detection
echo "--- Subfigure / small figure check ---"
subfig_abuse=0
small_width=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    # Check for subfigure usage (forbidden in competition papers)
    sf_count=$(grep -c '\\begin{subfigure}' "$f" 2>/dev/null || echo 0)
    if [ "$sf_count" -gt 0 ]; then
        echo "  FAIL: $bn uses subfigure ($sf_count times) — competition papers must use independent figure environments, not subfigure"
        subfig_abuse=$((subfig_abuse + sf_count))
        EXIT_CODE=1
    fi
    # Check for small figure widths (< 0.7\textwidth)
    small=$(grep -oP 'width\s*=\s*0\.\d+\\textwidth' "$f" 2>/dev/null | grep -oP '0\.\d+' | awk '$1 < 0.7 {print}' | wc -l)
    if [ "$small" -gt 0 ]; then
        echo "  FAIL: $bn has $small figures with width < 0.7\\textwidth — figures too small, use ≥ 0.85\\textwidth"
        small_width=$((small_width + small))
        EXIT_CODE=1
    fi
done
[ "$subfig_abuse" -eq 0 ] && [ "$small_width" -eq 0 ] && echo "  OK: no subfigure abuse or small figures"

# 10. TikZ architecture diagram check (against plan)
tikz_exists=$([ -s 图表/tikz_architecture_examples.tex ] && echo "YES" || echo "NO")
echo "  TikZ architecture diagram: $tikz_exists"
if [ "$tikz_exists" = "NO" ]; then
    for plan in 论文规划.md 问题分析.md 选题规划.md; do
        if [ -f "$plan" ] && grep -qi 'tikz\|架构图\|技术路线\|研究框架\|流程图\|关系图\|architecture.*diagram\|roadmap\|framework.*diagram' "$plan" 2>/dev/null; then
            echo "  WARN: plan mentions TikZ diagrams but 图表/tikz_architecture_examples.tex not found"
            break
        fi
    done
fi

echo "=== Compile checks done (exit code: $EXIT_CODE) ==="

# 11. Title existence check
echo "--- Title check ---"
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    if grep -q '\\title{' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        TITLE_CONTENT=$(grep '\\title{' "$PAPER_DIR/论文正文.tex" | head -1 | sed 's/.*\\title{//;s/}.*//')
        TITLE_CLEAN=$(echo "$TITLE_CONTENT" | sed 's/\\[a-zA-Z]*{[^}]*}//g; s/\\[a-zA-Z]*//g; s/[[:space:]]//g')
        if [ -z "$TITLE_CLEAN" ]; then
            echo "  FAIL: \\title{} is empty — PDF has no title" && EXIT_CODE=1
        else
            echo "  OK: title present"
        fi
    elif grep -q '\\timu{\|\\ttle{\|\\biaoti{' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        echo "  OK: title present (non-standard command)"
    elif grep -q 'MathorCup\|nemcmthesis\|JXUSTmodeling\|neepumcm' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        echo "  OK: special template (title in cls-specific command)"
    else
        echo "  FAIL: no \\title command found — PDF has no title" && EXIT_CODE=1
    fi
fi

# 12. Symbol table / assumptions needspace check
echo "--- Symbol/assumptions page break ---"
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    is_target=false
    echo "$bn" | grep -qi 'symbol\|assumption' && is_target=true
    grep -q '\\section{符号说明}\|\\section{模型假设}' "$f" 2>/dev/null && is_target=true
    if [ "$is_target" = true ]; then
        # 符号说明：检查 \clearpage（确保从新页开始）
        if grep -q '\\section{符号说明}\|\\section.*符号' "$f" 2>/dev/null; then
            if grep -B2 '\\section{' "$f" 2>/dev/null | grep -q '\\clearpage'; then
                echo "  OK: $bn has \\clearpage before \\section"
            else
                echo "  WARN $bn: missing \\clearpage before symbol section — title and table may split. Re-run compile_utils.sh."
            fi
            # 检查表格不是 [H]（[H] 会导致分页）
            if grep -q '\\begin{table}\[H\]' "$f" 2>/dev/null; then
                echo "  WARN $bn: table uses [H] — may cause title-table split. Should be [htbp]."
            fi
        fi
        # 模型假设：检查 \needspace + \nopagebreak
        if grep -q '\\section{模型假设}\|\\section.*假设' "$f" 2>/dev/null; then
            if grep -B2 '\\section{' "$f" 2>/dev/null | grep -q '\\needspace\|\\clearpage'; then
                echo "  OK: $bn has page break control before \\section"
            else
                echo "  WARN $bn: missing \\needspace before assumption section. Re-run compile_utils.sh."
            fi
            if grep -A1 '\\section{' "$f" 2>/dev/null | grep -q '\\nopagebreak'; then
                echo "  OK: $bn has \\nopagebreak after \\section"
            else
                echo "  WARN $bn: missing \\nopagebreak after assumption section."
            fi
        fi
    fi
done

echo "=== All checks done (exit code: $EXIT_CODE) ==="
exit $EXIT_CODE
