#!/bin/bash
# compile_utils.sh — 编译前自动清理和修复
# 用法: bash 工具/compile_utils.sh 论文/

PAPER_DIR="${1:-paper}"

echo "=== 编译前清理 ($PAPER_DIR) ==="

# 0. 杀掉残留的 XeLaTeX/pdflatex 进程（Windows 文件锁问题）
# 上一次编译可能没完全退出，导致字体文件被锁住 Permission denied
echo "--- 清理残留编译进程 ---"
if command -v taskkill &>/dev/null; then
    taskkill //F //IM xelatex.exe 2>/dev/null && echo "  killed xelatex.exe" || true
    taskkill //F //IM pdflatex.exe 2>/dev/null && echo "  killed pdflatex.exe" || true
elif command -v pkill &>/dev/null; then
    pkill -f xelatex 2>/dev/null || true
    pkill -f pdflatex 2>/dev/null || true
fi
sleep 1

# 1. 清理特殊 Unicode 字符（防止乱码）
echo "--- 清理特殊字符 ---"
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex; do
    [ -f "$f" ] || continue
    # 删除 emoji 和特殊符号
    sed -i 's/[✅❌⚠️⛔🔥💡📊📋🎯🔧✓✗♪ſ]//g' "$f" 2>/dev/null
    # 删除零宽字符
    sed -i 's/[\xE2\x80\x8B\xE2\x80\x8C\xE2\x80\x8D\xEF\xBB\xBF]//g' "$f" 2>/dev/null
    # Unicode 数学符号 → LaTeX 命令
    sed -i 's/→/$\\rightarrow$/g; s/←/$\\leftarrow$/g' "$f" 2>/dev/null
    sed -i 's/≥/$\\geq$/g; s/≤/$\\leq$/g; s/×/$\\times$/g; s/±/$\\pm$/g' "$f" 2>/dev/null
done
echo "  done"

# 2.5 修复封面 \cline{N-N} 被当文本渲染的问题
# Meta-model-agent 有时在封面 tabular 中把 \cline 写在文本位置而非行分隔符位置
echo "--- 修复封面 cline 问题 ---"
for f in "$PAPER_DIR"/论文正文.tex "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    # 只修复没有反斜杠前缀的 clineN-N（纯文本残留，如 "cline2-2"）
    # ⛔ 不要删除正常的 \cline{N-N}（tabular 中的合法命令）
    if grep -qP '(?<!\\)cline[0-9]' "$f" 2>/dev/null; then
        sed -i 's/\([^\\]\)cline\([0-9]*-[0-9]*\)/\1/g' "$f" 2>/dev/null
        echo "  $(basename $f): removed text 'clineN-N' artifacts (preserved \\cline)"
    fi
done
    fi
done

# 2.6 修复 \listoffigures 出现在摘要之前的问题
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    if grep -q '\\listoffigures' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        # 检查 \listoffigures 是否在 \begin{abstract} 之前
        LOF_LINE=$(grep -n '\\listoffigures' "$PAPER_DIR/论文正文.tex" | head -1 | cut -d: -f1)
        ABS_LINE=$(grep -n '\\begin{abstract}\|摘.*要' "$PAPER_DIR/论文正文.tex" | head -1 | cut -d: -f1)
        if [ -n "$LOF_LINE" ] && [ -n "$ABS_LINE" ] && [ "$LOF_LINE" -lt "$ABS_LINE" ]; then
            echo "  ⚠ \\listoffigures 在摘要之前，移除（不应出现在摘要前）"
            sed -i '/\\listof图表/d' "$PAPER_DIR/论文正文.tex"
            sed -i '/\\listoftables/d' "$PAPER_DIR/论文正文.tex"
        fi
    fi
fi

# 2.7 MathorCup 封面格式检查：如果是 MathorCup 论文但有独立封面页（\maketitle），删掉
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    # 只检查 \documentclass 行是否包含 MathorCup（不检查注释或正文）
    if grep -q '\\documentclass.*MathorCup' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        if grep -q '\\maketitle' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            echo "  ⚠ MathorCup 论文不应有 \\maketitle（官方格式无独立封面），移除"
            sed -i '/\\maketitle/d' "$PAPER_DIR/论文正文.tex"
        fi
    fi
fi

# 2. 修复 图表/图表/ 双层嵌套
if [ -d "图表/figures" ]; then

# 2.9 修复 babel[english] 导致中文论文的 Figure/Table 标签变英文
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    if grep -q 'ctex\|cumcmthesis\|gmcmthesis\|MathorCup\|xeCJK' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        if grep -q 'usepackage.*english.*babel\|usepackage\[english\]{babel}' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            echo "  ⚠ 中文论文加载了 babel[english]，移除（会导致 Figure/Table 变英文）"
            sed -i '/usepackage.*english.*babel/d' "$PAPER_DIR/论文正文.tex" 2>/dev/null
            sed -i '/usepackage\[english\]{babel}/d' "$PAPER_DIR/论文正文.tex" 2>/dev/null
        fi
        if ! grep -q 'renewcommand.*figurename' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            if ! grep -q 'cumcmthesis\|gmcmthesis' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
                sed -i '/\\begin{document}/i \\renewcommand{\\figurename}{图}' "$PAPER_DIR/论文正文.tex" 2>/dev/null
                sed -i '/\\begin{document}/i \\renewcommand{\\tablename}{表}' "$PAPER_DIR/论文正文.tex" 2>/dev/null
                echo "  注入 figurename=图, tablename=表"
            fi
        fi
    fi
fi
    echo "--- 修复 图表/图表/ 双层嵌套 ---"
    mv 图表/图表/*.pdf 图表/图表/*.png 图表/ 2>/dev/null
    rmdir 图表/figures 2>/dev/null
    echo "  fixed"
fi

# 2.8 修复 caption 冒号问题（中文论文应该是空格分隔，不是冒号）
# ⛔ 跳过 cumcmthesis/gmcmthesis/MathorCup 等自带 caption 配置的 cls
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    if grep -q 'ctexart\|ctexbook' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        # 只对 ctexart/ctexbook 文档类生效（这些没有自带 caption 配置）
        # cumcmthesis/gmcmthesis/MathorCup 等 cls 已内置 labelsep=quad，不要重复加
        if ! grep -q 'cumcmthesis\|gmcmthesis\|MathorCup\|yrdmcm\|neepumcm\|nemcmthesis\|JXUSTmodeling' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            if ! grep -q 'labelsep' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
                echo "  ⚠ 中文论文缺少 labelsep 设置（图表标题会显示冒号），自动添加"
                sed -i '/\\usepackage{caption}/a \\captionsetup{labelsep=quad}' "$PAPER_DIR/论文正文.tex" 2>/dev/null
                # 如果没有 \usepackage{caption}，在 \begin{document} 前加
                if ! grep -q 'usepackage{caption}' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
                    sed -i '/\\begin{document}/i \\usepackage{caption}\n\\captionsetup{labelsep=quad}' "$PAPER_DIR/论文正文.tex" 2>/dev/null
                fi
            fi
        fi
    fi
fi

# 3. 检查 PDF 图片文件
echo "--- 检查 PDF 图片 ---"
PDF_COUNT=$(ls 图表/*.pdf 2>/dev/null | wc -l)
echo "  PDF 图片: $PDF_COUNT 个"
if [ "$PDF_COUNT" -eq 0 ]; then
    echo "  ⚠ 没有 PDF 图片，尝试运行生成脚本..."
    for script in 图表/gen_fig*.py; do
        [ -f "$script" ] || continue
        echo "  运行: $script"
        python3 "$script" 2>&1 | tail -3
    done
    PDF_COUNT=$(ls 图表/*.pdf 2>/dev/null | wc -l)
    echo "  重新检查: $PDF_COUNT 个"
fi

# 4. 修正图片路径（仅 章节/*.tex，不动 论文正文.tex 的 \graphicspath）
echo "--- 修正图片路径 ---"
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    # 只替换 \includegraphics 中的路径，不动 \graphicspath 等声明
    if grep -q 'includegraphics.*{图表/' "$f" 2>/dev/null; then
        sed -i 's|\\includegraphics\(.*\){图表/|\\includegraphics\1{../图表/|g' "$f"
        echo "  $(basename $f): 图表/ -> ../图表/"
    fi
    if grep -q 'includegraphics.*{../../图表/' "$f" 2>/dev/null; then
        sed -i 's|\\includegraphics\(.*\){../../图表/|\\includegraphics\1{../图表/|g' "$f"
        echo "  $(basename $f): ../../图表/ -> ../图表/"
    fi
done
# 论文正文.tex 单独处理：只修复 \includegraphics，不动 \graphicspath
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    if grep -q 'includegraphics.*{../../图表/' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        sed -i 's|\\includegraphics\(.*\){../../图表/|\\includegraphics\1{../图表/|g' "$PAPER_DIR/论文正文.tex"
        echo "  论文正文.tex: ../../图表/ -> ../图表/"
    fi
fi

# 5. 添加 hidelinks + 修复 colorlinks 冲突
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    if grep -q 'usepackage{hyperref}' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        if ! grep -q 'hidelinks' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            sed -i 's|\\usepackage{hyperref}|\\usepackage[hidelinks]{hyperref}|g' "$PAPER_DIR/论文正文.tex"
            echo "  added hidelinks"
        fi
    fi
    # 修复 colorlinks=true 和 hidelinks 的冲突（colorlinks 会覆盖 hidelinks）
    if grep -q 'colorlinks=true' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        echo "  ⚠ 发现 colorlinks=true，与 hidelinks 冲突，正在修复..."
        sed -i 's/colorlinks=true/colorlinks=false/g' "$PAPER_DIR/论文正文.tex"
        echo "  fixed: colorlinks=true -> colorlinks=false"
    fi
    # 修复 citecolor=blue（即使 colorlinks=false 也清理掉）
    if grep -q 'citecolor=blue' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        sed -i 's/citecolor=blue/citecolor=black/g' "$PAPER_DIR/论文正文.tex"
        echo "  fixed: citecolor=blue -> citecolor=black"
    fi
fi

# 6. 修复 math_commands.tex 中的命令冲突
if [ -f "$PAPER_DIR/math_commands.tex" ]; then
    echo "--- 检查 math_commands.tex ---"
    for cmd in tanh sinh cosh sin cos tan log ln exp max min sup inf lim det dim ker; do
        if grep -q "\\\\DeclareMathOperator.*\\\\$cmd" "$PAPER_DIR/math_commands.tex" 2>/dev/null; then
            echo "  删除对 \\$cmd 的重定义"
            sed -i "/\\\\DeclareMathOperator.*\\\\$cmd/d" "$PAPER_DIR/math_commands.tex"
        fi
    done
fi

# 6.5 自动为超宽表格添加 resizebox
echo "--- 检查超宽表格 ---"
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 图表/*.tex; do
    [ -f "$f" ] || continue
    python3 -c "
import re, sys
with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:
    content = fh.read()
changed = False
# 匹配未被 resizebox 包裹的 tabular 环境
pattern = r'(\\\\begin\{tabular\}\{([^}]*)\})'
for m in re.finditer(pattern, content):
    col_spec = m.group(2)
    col_count = len(re.findall(r'[lcrpXS]', col_spec))
    start = max(0, m.start() - 80)
    before = content[start:m.start()]
    if 'resizebox' in before or 'adjustbox' in before:
        continue
    # Find the full tabular block to check content width
    end_pattern = r'\\\\end\{tabular\}'
    end_m = re.search(end_pattern, content[m.start():])
    if not end_m:
        continue
    end_pos = m.start() + end_m.end()
    block = content[m.start():end_pos]
    # Check if table needs resizebox: >=6 cols OR wide content (long Chinese headers)
    needs_resize = col_count >= 6
    if not needs_resize and col_count >= 4:
        # Estimate width: find the widest row (by character count)
        rows = [r for r in block.split('\\\\\\\\') if '&' in r]
        if rows:
            max_row_chars = max(len(r.strip()) for r in rows)
            # Chinese chars are ~2x width of ASCII; rough threshold: >120 chars likely overflows
            if max_row_chars > 120:
                needs_resize = True
                print(f'  wrapping {col_count}-col table (wide content: {max_row_chars} chars)')
    if needs_resize:
        old_block = content[m.start():end_pos]
        new_block = '\\\\resizebox{\\\\textwidth}{!}{%\n' + old_block + '\n}'
        content = content[:m.start()] + new_block + content[end_pos:]
        changed = True
        if col_count >= 6:
            print(f'  wrapped {col_count}-col tabular in resizebox')
        break
if changed:
    with open('$f', 'w', encoding='utf-8') as fh:
        fh.write(content)
" 2>/dev/null
done

# 6.6 移除窄表（<5列）上多余的 resizebox（防止窄表被拉伸占满一页）
echo "--- 检查窄表 resizebox ---"
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 图表/*.tex; do
    [ -f "$f" ] || continue
    python3 -c "
import re
with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:
    content = fh.read()
changed = False
# 找到 resizebox 包裹的 tabular，检查列数和内容宽度
pattern = r'\\\\resizebox\{\\\\textwidth\}\{!\}\{%?\s*\n?(\\\\begin\{tabular\}\{([^}]*)\}.*?\\\\end\{tabular\})\s*\n?\}%?'
for m in re.finditer(pattern, content, re.DOTALL):
    col_spec = m.group(2)
    col_count = len(re.findall(r'[lcrpXS]', col_spec))
    block = m.group(1)
    # Check content width before removing
    rows = [r for r in block.split('\\\\\\\\') if '&' in r]
    max_row_chars = max((len(r.strip()) for r in rows), default=0)
    # Only remove resizebox if table is truly narrow (few cols AND short content)
    if col_count < 6 and max_row_chars < 100:
        print(f'  removing resizebox from {col_count}-col table ({max_row_chars} chars, too narrow)')
        content = content[:m.start()] + m.group(1) + content[m.end():]
        changed = True
        break
    elif col_count < 6:
        print(f'  keeping resizebox on {col_count}-col table ({max_row_chars} chars, wide content)')
if changed:
    with open('$f', 'w', encoding='utf-8') as fh:
        fh.write(content)
" 2>/dev/null
done

# 6.64 正文长表格自动转 longtable（>15 行的 tabular 在 table[H] 里会导致标题和表格分页）
echo "--- 长表格 → longtable ---"
LONGTABLE_FIXES=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    # 跳过符号说明（已在 9.8 步单独处理）和附录
    echo "$bn" | grep -qi 'symbol\|appendix\|A_code\|A_tables' && continue
    # 检查是否有超过 15 行的 tabular
    if grep -q '\\begin{tabular}' "$f" 2>/dev/null; then
        # 计算 tabular 内的数据行数（包含 & 的行）
        ROW_COUNT=$(awk '/\\begin\{tabular\}/,/\\end\{tabular\}/' "$f" 2>/dev/null | grep -c '&' || echo 0)
        if [ "$ROW_COUNT" -gt 15 ]; then
            echo "  $bn: $ROW_COUNT 行表格 → longtable（防止标题和表格分页）"
            # 和符号说明一样的转换逻辑
            sed -i '/\\begin{table}/d' "$f" 2>/dev/null
            sed -i '/\\end{table}/d' "$f" 2>/dev/null
            sed -i '/\\centering/d' "$f" 2>/dev/null
            sed -i 's/\\begin{tabular}/\\begin{longtable}/g' "$f" 2>/dev/null
            sed -i 's/\\end{tabular}/\\end{longtable}/g' "$f" 2>/dev/null
            # caption 移到 toprule 前
            CAPTION_LINE=$(grep '\\caption{' "$f" 2>/dev/null | head -1)
            if [ -n "$CAPTION_LINE" ]; then
                sed -i '/\\caption{/d' "$f" 2>/dev/null
                sed -i "/\\\\toprule/i ${CAPTION_LINE} \\\\\\\\" "$f" 2>/dev/null
            fi
            LONGTABLE_FIXES=$((LONGTABLE_FIXES+1))
        fi
    fi
done
[ "$LONGTABLE_FIXES" -gt 0 ] && echo "  $LONGTABLE_FIXES 个长表格转为 longtable" || echo "  无需转换"

# 6.65 自动截断超长表格（>20行的正文表格截断为前5+后3+省略号，完整表格移到附录）
echo "--- 检查超长表格 ---"
# 准备附录文件（用于存放完整表格）
APPENDIX_TABLES="$PAPER_DIR/章节/A_tables.tex"
TABLES_ADDED=0

for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    # 跳过附录文件（完整表放附录是正确的）
    echo "$bn" | grep -qi 'appendix\|附录\|A_code\|A_tables' && continue
    python3 -c "
import re, os

with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:
    content = fh.read()
original = content
appendix_tables = []

# Find all tabular environments
for m in re.finditer(r'(\\\\begin\{tabular\}\{[^}]*\})(.*?)(\\\\end\{tabular\})', content, re.DOTALL):
    header = m.group(1)
    body = m.group(2)
    footer = m.group(3)

    # Split into rows by \\\\
    parts = re.split(r'(\\\\\\\\)', body)
    rows = []
    i = 0
    while i < len(parts):
        if i + 1 < len(parts) and parts[i+1] == '\\\\\\\\':
            rows.append(parts[i] + parts[i+1])
            i += 2
        else:
            rows.append(parts[i])
            i += 1

    data_rows = [r for r in rows if '&' in r and 'toprule' not in r and 'midrule' not in r and 'bottomrule' not in r and 'vdots' not in r]

    if len(data_rows) <= 20:
        continue

    print(f'  ⛔ $bn: {len(data_rows)}-row table found, truncating + moving full table to appendix...')

    # 保存完整表格到附录
    full_block = m.group(0)
    # 提取 caption
    table_start = content.find(full_block)
    before = content[max(0, table_start-400):table_start]
    cap_match = re.search(r'\\\\caption\{([^}]*)\}', before)
    cap_text = cap_match.group(1) if cap_match else '完整结果'
    # 生成附录表格的 label
    safe_label = re.sub(r'[^a-zA-Z0-9]', '_', '$bn'.replace('.tex',''))
    appendix_label = f'tab:full_{safe_label}_{len(appendix_tables)}'

    appendix_entry = (
        f'\\\\begin{{table}}[H]\n'
        f'\\\\centering\n'
        f'\\\\caption{{{cap_text}（完整数据）}}\\\\label{{{appendix_label}}}\n'
        f'\\\\resizebox{{\\\\textwidth}}{{!}}{{% \n'
        f'{full_block}\n'
        f'}}\n'
        f'\\\\end{{table}}\n'
    )
    appendix_tables.append(appendix_entry)

    # 截断正文表格
    new_rows = []
    data_count = 0
    bottom_rows = data_rows[-3:]
    for r in rows:
        is_data = '&' in r and 'toprule' not in r and 'midrule' not in r and 'bottomrule' not in r and 'vdots' not in r
        if is_data:
            data_count += 1
            if data_count <= 5:
                new_rows.append(r)
            elif data_count == 6:
                col_count = header.count('c') + header.count('l') + header.count('r') + header.count('p') + header.count('X') + header.count('S')
                if col_count < 2:
                    col_count = r.count('&') + 1
                vdots_row = '\\\\multicolumn{' + str(col_count) + '}{c}{\$\\\\vdots\$} \\\\\\\\'
                new_rows.append(vdots_row)
            elif r in bottom_rows:
                new_rows.append(r)
        else:
            new_rows.append(r)

    new_body = ''.join(new_rows)
    new_block = header + new_body + footer
    content = content.replace(full_block, new_block, 1)

    # 更新 caption 加附录引用
    table_start = content.find(new_block)
    before = content[max(0, table_start-400):table_start]
    cap_match = re.search(r'\\\\caption\{([^}]*)\}', before)
    if cap_match and '部分' not in cap_match.group(1):
        old_cap = cap_match.group(0)
        new_cap = f'\\\\caption{{{cap_match.group(1)}（部分，完整结果见附录表\\\\ref{{{appendix_label}}}）}}'
        content = content[:max(0, table_start-400)] + content[max(0, table_start-400):table_start].replace(old_cap, new_cap, 1) + content[table_start:]
    break

if content != original:
    with open('$f', 'w', encoding='utf-8') as fh:
        fh.write(content)
    print(f'  ✓ $bn: table truncated')

# 写入附录文件
if appendix_tables:
    appendix_file = '$APPENDIX_TABLES'
    mode = 'a' if os.path.exists(appendix_file) else 'w'
    with open(appendix_file, mode, encoding='utf-8') as af:
        if mode == 'w':
            af.write('\\\\section{完整结果表格}\n\n')
        for entry in appendix_tables:
            af.write(entry + '\n')
    print(f'  ✓ 完整表格已追加到附录 ({len(appendix_tables)} 个)')
" 2>/dev/null
done

# 如果生成了附录表格文件，确保 论文正文.tex 引用了它
if [ -f "$APPENDIX_TABLES" ]; then
    if ! grep -q 'A_tables' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        # 在 A_code 的 \input 前面插入 A_tables 的 \input
        if grep -q 'A_code' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            sed -i '/\\input{章节\/A_code}/i \\\\input{章节/A_tables}' "$PAPER_DIR/论文正文.tex" 2>/dev/null
            echo "  ✓ 已在 论文正文.tex 中添加附录表格引用"
        fi
    fi
fi
" 2>/dev/null
done

# 6.7 修复数学环境错误（常见：反斜杠清理误伤导致 \X(t)$ 而非 $X(t)$）
echo "--- 修复数学环境错误 ---"
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex; do
    [ -f "$f" ] || continue
    python3 -c "
import re
with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:
    content = fh.read()
original = content
fixes = 0

# Pattern 1: \\X(t)$ → \$X(t)\$ (backslash before variable name + trailing $)
# Matches: \\varname$ where varname is a letter sequence (not a LaTeX command)
# But NOT \\alpha$, \\beta$, etc. (valid LaTeX commands)
latex_cmds = {'alpha','beta','gamma','delta','epsilon','zeta','eta','theta','iota','kappa',
    'lambda','mu','nu','xi','pi','rho','sigma','tau','upsilon','phi','chi','psi','omega',
    'Delta','Gamma','Lambda','Sigma','Theta','Phi','Psi','Omega',
    'sum','prod','int','frac','sqrt','partial','nabla','infty','cdot','times','pm','mp',
    'leq','geq','neq','approx','sim','equiv','subset','supset','in','notin',
    'left','right','big','Big','bigg','Bigg','text','mathrm','mathbf','mathcal',
    'hat','bar','tilde','vec','dot','ddot','overline','underline',
    'begin','end','label','ref','cite','caption','textbf','textit','emph'}

# Find patterns like \\X$ or \\X(...)$ or \\X_i$ that are NOT valid LaTeX commands
pattern = r'(?<!\\\\\$)\\\\([A-Za-z]+)([\(_\^][^$]*?)?\\\$'
for m in re.finditer(pattern, content):
    cmd = m.group(1)
    if cmd.lower() not in latex_cmds and len(cmd) <= 3:
        old = m.group(0)
        inner = cmd + (m.group(2) or '')
        new = '\$' + inner + '\$'
        content = content.replace(old, new, 1)
        fixes += 1
        print(f'  Fixed: {old!r} -> {new!r}')

# Pattern 2: lone \\$ at start of math (missing opening $)
# e.g., text \\mu$ should be text \$\\mu\$
# This is harder to detect reliably, skip for now

if fixes > 0:
    with open('$f', 'w', encoding='utf-8') as fh:
        fh.write(content)
    print(f'  Fixed {fixes} math environment errors in \$(basename $f)')
elif content != original:
    with open('$f', 'w', encoding='utf-8') as fh:
        fh.write(content)
" 2>/dev/null
done

# 6.75 确保 float 包已加载（[H] 需要 float 包，否则编译报错）
echo "--- 检查 float 包 ---"
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    # 检查 论文正文.tex 和 cls 文件中是否已有 float 包
    HAS_FLOAT=false
    if grep -q 'usepackage{float}\|usepackage\[.*\]{float}\|RequirePackage{float}' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        HAS_FLOAT=true
    fi
    # 检查 cls 文件
    for cls in "$PAPER_DIR"/*.cls; do
        [ -f "$cls" ] || continue
        if grep -q 'RequirePackage{float}' "$cls" 2>/dev/null; then
            HAS_FLOAT=true
            break
        fi
    done
    if [ "$HAS_FLOAT" = false ]; then
        echo "  ⚠ float 包缺失，自动注入（[H] 浮动符需要此包）"
        # 在 \usepackage{graphicx} 后面加，或在 \begin{document} 前加
        if grep -q 'usepackage{graphicx}\|usepackage\[.*\]{graphicx}' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            sed -i '/usepackage.*{graphicx}/a \\usepackage{float}' "$PAPER_DIR/论文正文.tex"
        else
            sed -i '/\\begin{document}/i \\usepackage{float}' "$PAPER_DIR/论文正文.tex"
        fi
        echo "  ✓ 已注入 \\usepackage{float}"
    else
        echo "  ✓ float 包已存在"
    fi
fi

# 6.8 规范浮动体：所有非 [htbp] 的浮动说明符 → [htbp]（让 LaTeX 合理利用页面空间）
# 符号说明和模型假设文件继续由 9.8 步单独处理。
echo "--- 规范浮动体 → [htbp] ---"
FLOAT_FIXES=0
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    # 跳过符号说明和模型假设，沿用其专用分页策略。
    if echo "$bn" | grep -qi 'symbol\|assumption'; then
        continue
    fi
    if grep -q '\\section{符号说明}\|\\section{模型假设}\|\\section.*假设\|\\section.*符号' "$f" 2>/dev/null; then
        continue
    fi
    # 修复 figure: [htbp] [tbp] [htp] [ht] [h] [t] [b] [p] [!h] [h!] [!ht] [!htbp] 等 → [htbp]
    # 但不动已经是 [htbp] 的
    if grep -qP '\\begin\{figure\}\[(?!htbp\])[^\]]*\]' "$f" 2>/dev/null; then
        sed -i -E 's/\\begin\{figure\}\[[^]]*\]/\\begin{figure}[htbp]/g' "$f"

        echo "  $bn: figure 浮动符 → [htbp]"
        FLOAT_FIXES=$((FLOAT_FIXES+1))
    fi
    # 修复没有方括号的 \begin{figure}（LaTeX 默认 [tbp]，也会浮动）
    if grep -qP '\\begin\{figure\}[^[\n]' "$f" 2>/dev/null || grep -qP '\\begin\{figure\}$' "$f" 2>/dev/null; then
        sed -i 's/\\begin{figure}$/\\begin{figure}[htbp]/g' "$f"
        # 处理 \begin{figure} 后面直接跟 \centering 等（同一行或下一行）
        sed -i 's/\\begin{figure}\\centering/\\begin{figure}[htbp]\\centering/g' "$f"
        sed -i -E 's/\\begin\{figure\}([^[\n])/\\begin{figure}[htbp]\1/g' "$f"
        echo "  $bn: figure 无浮动符 → [htbp]"
        FLOAT_FIXES=$((FLOAT_FIXES+1))
    fi
    # 同样修复 table 浮动体
    if grep -qP '\\begin\{table\}\[(?!htbp\])[^\]]*\]' "$f" 2>/dev/null; then
        sed -i -E 's/\\begin\{table\}\[[^]]*\]/\\begin{table}[htbp]/g' "$f"
        echo "  $bn: table 浮动符 → [htbp]"
        FLOAT_FIXES=$((FLOAT_FIXES+1))
    fi
    # 修复没有方括号的 \begin{table}
    if grep -qP '\\begin\{table\}[^[\n]' "$f" 2>/dev/null || grep -qP '\\begin\{table\}$' "$f" 2>/dev/null; then
        sed -i 's/\\begin{table}$/\\begin{table}[htbp]/g' "$f"
        sed -i -E 's/\\begin\{table\}([^[\n])/\\begin{table}[htbp]\1/g' "$f"
        echo "  $bn: table 无浮动符 → [htbp]"
        FLOAT_FIXES=$((FLOAT_FIXES+1))
    fi
    # 修复 algorithm 环境浮动（algorithm2e 的 \begin{algorithm} 也会浮动）
    if grep -qP '\\begin\{algorithm\}\[(?!htbp\])[^\]]*\]' "$f" 2>/dev/null; then
        sed -i -E 's/\\begin\{algorithm\}\[[^]]*\]/\\begin{algorithm}[htbp]/g' "$f"
        echo "  $bn: algorithm 浮动符 → [htbp]"
        FLOAT_FIXES=$((FLOAT_FIXES+1))
    fi
done
[ "$FLOAT_FIXES" -gt 0 ] && echo "  $FLOAT_FIXES 个文件修复了浮动体" || echo "  无需修复"

# 6.9 检测连续图表（两个 figure/table 之间文字不足 5 行）
echo "--- 检测连续图表 ---"
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    python3 -c "
import re
with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:
    content = fh.read()
# Find all figure/table environments
floats = list(re.finditer(r'\\\\end\{(figure|table)\}', content))
for i in range(len(floats)-1):
    end1 = floats[i].end()
    start2_match = re.search(r'\\\\begin\{(figure|table)\}', content[end1:])
    if start2_match:
        between = content[end1:end1+start2_match.start()]
        # Count non-empty, non-comment lines
        text_lines = [l for l in between.split('\n') if l.strip() and not l.strip().startswith('%')]
        if len(text_lines) < 5:
            line_num = content[:end1].count('\n') + 1
            print(f'  ⚠ $bn line ~{line_num}: 连续图表之间只有 {len(text_lines)} 行文字（需要 ≥5 行）')
" 2>/dev/null
done

# 7. 检查竖线表格（应该用三线表）+ 修复表格换行符
echo "--- 检查表格格式 ---"
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 图表/*.tex; do
    [ -f "$f" ] || continue
    if grep -q '{|.*|}' "$f" 2>/dev/null; then
        echo "  ⚠ $(basename $f) 中发现竖线表格，建议改为三线表"
    fi
    # 修复表格中单个 \ 换行（应该是 \\）
    # 匹配：行末是 " \" 但不是 " \\"（在 tabular 环境中）
    if grep -qP ' \\$' "$f" 2>/dev/null; then
        sed -i 's/ \\$/\\\\/g' "$f" 2>/dev/null
        echo "  修复 $(basename $f): 表格行末 \\ → \\\\"
    fi
done

# 7.2 修复 \[ 被误用为换行（应该是 \\[）
# 只修复 \[数字em] 或 \[数字pt] 或 \[数字cm] 模式，不动正常的数学 \[...\]
echo "--- 修复 \\[ 误用 ---"
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex; do
    [ -f "$f" ] || continue
    python3 -c "
import re
with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:
    content = fh.read()
# Match \[0.5em] or \[1pt] etc. but NOT \\[0.5em] (already correct)
# Also not \[ x^2 \] (math display mode)
pattern = r'(?<!\\\\)\\\\(?=\[\d+\.?\d*\s*(em|pt|cm|mm|ex)\])'
new_content = re.sub(pattern, r'\\\\\\\\', content)
if new_content != content:
    with open('$f', 'w', encoding='utf-8') as fh:
        fh.write(new_content)
    print(f'  Fixed \\\\[ -> \\\\\\\\[ in $(basename $f)')
" 2>/dev/null
done

# 7.5 检查中文论文是否错误使用 natbib（应该用 gbt7714）
echo "--- 检查引用格式 ---"
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    if grep -q 'ctex\|xelatex\|ctexart\|ctexbook' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        # 中文论文
        if grep -q 'usepackage.*natbib' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            # Exception: stats competition template uses natbib with [numbers,square] or [numbers,square,super] — this is correct
            if grep -q 'numbers.*square\|square.*numbers' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
                echo "  ✓ natbib with [numbers,square] (stats competition format)"
            elif ! grep -q 'gbt7714' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
                echo "  ⚠ 中文论文使用了 natbib 而非 gbt7714，引用格式将是 [Author, Year] 而非上标 [1]"
                echo "  建议替换为: \\usepackage[super,sort&compress]{gbt7714}"
            fi
        fi
    fi
fi

# 8. 检查 ref/label 匹配
echo "--- 检查 ref/label ---"
grep -oh '\\ref{[^}]*}' "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null | sort -u > /tmp/_refs.txt
grep -oh '\\label{[^}]*}' "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null | sort -u > /tmp/_labels.txt
MISSING=$(comm -23 <(sed 's/\\ref/\\label/g' /tmp/_refs.txt) /tmp/_labels.txt 2>/dev/null)
if [ -n "$MISSING" ]; then
    echo "  ⚠ 缺失的 label:"
    echo "$MISSING"
else
    echo "  all refs have matching labels"
fi

# 9. 删除 \input{../图表/图表引用*.tex} 行（禁止批量导入整个图表引用文件）
echo "--- 检查禁止的 \\input{figures} ---"
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    # 只删除批量导入图表引用文件的行，不删除单个 TikZ 图的 \input
    if grep -q '\\input.*图表引用' "$f" 2>/dev/null; then
        echo "  ⚠ $(basename $f) 中发现 \\input{图表引用}，已删除"
        sed -i '/\\input.*图表引用/d' "$f"
    fi
done

# 9.1 自动检测并报告未嵌入的图表（供 Meta-model-agent 编译步骤修复）
echo "--- 未嵌入图表检测 ---"
UNEMBED_COUNT=0
UNEMBED_LIST=""
# 检查图表目录中的 label 是否都在章节中出现
if ls 图表/*.tex 1>/dev/null 2>&1; then
    for fig_tex in 图表/*.tex; do
        [ -f "$fig_tex" ] || continue
        fig_labels=$(grep -oh '\\label{[^}]*}' "$fig_tex" 2>/dev/null)
        for lbl in $fig_labels; do
            if ! grep -rq "$lbl" "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null; then
                echo "  ⚠ UNEMBEDDED: $lbl (from $(basename $fig_tex)) — not found in any section"
                UNEMBED_COUNT=$((UNEMBED_COUNT + 1))
                UNEMBED_LIST="$UNEMBED_LIST $lbl"
            fi
        done
    done
fi
# 检查 图表/*.pdf 是否被 \includegraphics 引用
UNEMBED_PDFS=""
for pdf in 图表/*.pdf; do
    [ -f "$pdf" ] || continue
    bn=$(basename "$pdf")
    if ! grep -rq "$bn" "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null; then
        echo "  ⚠ UNEMBEDDED: $bn — PDF not referenced by any \\includegraphics"
        UNEMBED_COUNT=$((UNEMBED_COUNT + 1))
        UNEMBED_PDFS="$UNEMBED_PDFS $bn"
    fi
done
if [ "$UNEMBED_COUNT" -gt 0 ]; then
    echo ""
    echo "  ============================================================"
    echo "  ACTION REQUIRED: $UNEMBED_COUNT unembedded 图表/tables"
    echo "  ============================================================"
    echo "  The compile step MUST embed these before compilation."
    echo "  For each unembedded item:"
    echo "    1. Find the figure/table block in 图表/*.tex (match by label)"
    echo "    2. Determine which section it belongs to (by label name or caption)"
    echo "    3. Copy the complete \\begin{figure}...\\end{figure} block into that section"
    echo "    4. Add 1-2 sentences of lead-in text before and 3-5 sentences of analysis after"
    echo ""
    echo "  Unembedded labels: $UNEMBED_LIST"
    echo "  Unembedded PDFs: $UNEMBED_PDFS"
    echo "  ============================================================"
else
    echo "  ✓ 图表目录中的全部图表均已嵌入章节"
fi

# 9.2 检测空 figure 环境（有 caption 但没有 \includegraphics 或 tikzpicture）
echo "--- 空图表环境检测 ---"
EMPTY_FIG_COUNT=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    python3 -c "
import re
with open('$f', 'r', encoding='utf-8', errors='ignore') as fh:
    content = fh.read()
# Find all figure environments
fig_pattern = r'\\\\begin\{figure\}.*?\\\\end\{figure\}'
for m in re.finditer(fig_pattern, content, re.DOTALL):
    block = m.group()
    has_image = 'includegraphics' in block
    has_tikz = 'tikzpicture' in block
    has_tabular = 'tabular' in block
    if not has_image and not has_tikz and not has_tabular:
        # Extract caption for reporting
        cap = re.search(r'\\\\caption\{([^}]*)\}', block)
        cap_text = cap.group(1)[:50] if cap else '(no caption)'
        print(f'EMPTY_FIGURE in $bn: \"{cap_text}\" — has caption but no \\\\includegraphics or tikzpicture')
# Same for table environments
tab_pattern = r'\\\\begin\{table\}.*?\\\\end\{table\}'
for m in re.finditer(tab_pattern, content, re.DOTALL):
    block = m.group()
    if 'tabular' not in block and 'longtable' not in block:
        cap = re.search(r'\\\\caption\{([^}]*)\}', block)
        cap_text = cap.group(1)[:50] if cap else '(no caption)'
        print(f'EMPTY_TABLE in $bn: \"{cap_text}\" — has caption but no tabular content')
" 2>/dev/null | while read line; do
        echo "  ⚠ $line"
        EMPTY_FIG_COUNT=$((EMPTY_FIG_COUNT + 1))
    done
done
if [ "$EMPTY_FIG_COUNT" -gt 0 ]; then
    echo "  ACTION REQUIRED: Found empty figure/table environments."
    echo "  For each empty figure: find the matching PDF in 图表/ (by caption/label name) and add \\includegraphics{../图表/xxx.pdf}"
    echo "  For each empty table: find the matching table code in 图表/TABLE_*.tex and paste the tabular content"
fi

# 9.5 检查章节目录下的非 .tex 文件（不该存在）
echo "--- 检查章节目录杂文件 ---"
for f in "$PAPER_DIR"/章节/*; do
    [ -f "$f" ] || continue
    case "$f" in
        *.tex) ;;
        *) echo "  ⚠ 章节目录中发现非 .tex 文件: $(basename $f)，建议删除" ;;
    esac
done

# 9.6 检查并删除模板占位符残留
# ⛔ 注意：不能用 sed -i '/pattern/d' 删除整行，因为 \title{[论文标题]} 这种行
#    删掉整行会导致 \title 命令丢失，PDF 标题消失！
#    正确做法：只删除占位符文本，保留 LaTeX 命令结构
echo "--- 检查模板占位符 ---"
for f in "$PAPER_DIR"/论文正文.tex "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    if grep -q '\[中文摘要内容\]\|\[English abstract\]\|\[论文标题\]\|\[关键词1\]' "$f" 2>/dev/null; then
        echo "  ⚠ $(basename $f) 中发现模板占位符残留，正在清理..."
        # 对于 \title{[论文标题]}：替换为 \title{}（保留命令，清空内容）
        sed -i 's/\[论文标题\]//g' "$f"
        # 对于章节中的独立占位符行：直接删除整行（这些不包含 LaTeX 命令）
        sed -i '/^\[中文摘要内容.*\]$/d; /^\[English abstract.*\]$/d' "$f"
        # 对于内联占位符：替换为空
        sed -i 's/\[中文摘要内容[^]]*\]//g; s/\[English abstract[^]]*\]//g' "$f"
        sed -i 's/\[关键词1\]//g; s/\[关键词2\]//g; s/\[关键词3\]//g' "$f"
    fi
    # stats 模板封面特有占位符检查（不自动清理，必须由 Meta-model-agent 手动替换）
    if grep -q '\[学校名称\]\|\[队员1\]\|\[指导老师\]\|\[竞赛年份\]\|\[届数\]' "$f" 2>/dev/null; then
        echo "  ⚠ $(basename $f) 中发现 stats 封面占位符未替换：[学校名称]/[队员]/[指导老师]/[竞赛年份]"
        echo "    → 必须替换这些占位符，否则封面会显示方括号文字"
    fi
done

# 9.7 验证并自动修复 \title 命令（防止标题丢失）
# ⛔ 只对使用 \title{} + \maketitle 的模板生效
# 不处理：stats（手动排版标题）、dongsansheng（\ttle）、huashubei（\biaoti）、
#         diangongbei/changsanjiao（\mcmsetup{timu=}）、MathorCup（\timu）
echo "--- 检查 \\title 命令 ---"
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    # 检测是否是使用 \title{} 的模板（排除不用 \title 的特殊模板）
    USES_TITLE_CMD=false
    if grep -q '\\documentclass.*cumcmthesis\|\\documentclass.*gmcmthesis\|\\documentclass.*ctexart\|\\documentclass.*article' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        # 但 stats 模板虽然用 ctexart，却不用 \title，而是手动排版
        # 通过检查是否有 \maketitle 来判断
        if grep -q '\\maketitle' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            USES_TITLE_CMD=true
        fi
        # cumcmthesis/gmcmthesis 必须有 \maketitle，如果被误删了也要修复
        if grep -q 'cumcmthesis\|gmcmthesis' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            USES_TITLE_CMD=true
        fi
    fi
    # default 模板也用 \title + \maketitle
    if grep -q '\\title{' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        USES_TITLE_CMD=true
    fi

    if [ "$USES_TITLE_CMD" = true ]; then
        if grep -q '\\title{' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            TITLE_CONTENT=$(grep '\\title{' "$PAPER_DIR/论文正文.tex" | head -1 | sed 's/.*\\title{//;s/}.*//')
            # 去掉 \heiti\zihao{2} 等格式命令后再判断是否为空
            TITLE_CLEAN=$(echo "$TITLE_CONTENT" | sed 's/\\[a-zA-Z]*{[^}]*}//g; s/\\[a-zA-Z]*//g; s/[[:space:]]//g')
            if [ -z "$TITLE_CLEAN" ]; then
                echo "  ⛔ \\title{} 内容为空，尝试自动修复..."
                FALLBACK_TITLE=""
                if [ -f "META_MODEL_AGENT.md" ]; then
                    FALLBACK_TITLE=$(grep -oP '(?<=题目|赛题|title)[：:]\s*\K.+' META_MODEL_AGENT.md 2>/dev/null | head -1 | sed 's/[[:space:]]*$//')
                fi
                if [ -z "$FALLBACK_TITLE" ] && [ -f "问题分析.md" ]; then
                    FALLBACK_TITLE=$(head -5 问题分析.md | grep -oP '(?<=^# |^## ).+' | head -1)
                fi
                if [ -z "$FALLBACK_TITLE" ]; then
                    FALLBACK_TITLE="数学建模竞赛论文"
                fi
                # 保留原有格式命令，只填充标题文本
                if echo "$TITLE_CONTENT" | grep -q '\\heiti\|\\zihao'; then
                    # default 模板: \title{\heiti\zihao{2} }
                    sed -i "s|\\\\title{${TITLE_CONTENT}}|\\\\title{${TITLE_CONTENT}${FALLBACK_TITLE}}|" "$PAPER_DIR/论文正文.tex"
                else
                    sed -i "s|\\\\title{}|\\\\title{$FALLBACK_TITLE}|" "$PAPER_DIR/论文正文.tex"
                fi
                echo "  ✓ 已自动填充标题: $FALLBACK_TITLE"
            else
                echo "  ✓ \\title 存在: $TITLE_CONTENT"
            fi
        else
            echo "  ⛔ 论文正文.tex 中没有 \\title 命令，自动插入..."
            FALLBACK_TITLE="数学建模竞赛论文"
            if [ -f "META_MODEL_AGENT.md" ]; then
                FT=$(grep -oP '(?<=题目|赛题|title)[：:]\s*\K.+' META_MODEL_AGENT.md 2>/dev/null | head -1 | sed 's/[[:space:]]*$//')
                [ -n "$FT" ] && FALLBACK_TITLE="$FT"
            fi
            sed -i "/\\\\begin{document}/i \\\\title{$FALLBACK_TITLE}" "$PAPER_DIR/论文正文.tex"
            echo "  ✓ 已自动插入: \\title{$FALLBACK_TITLE}"
        fi
        # 检查并修复 \maketitle（cumcmthesis/gmcmthesis 需要，但五一杯例外）
        if grep -q 'cumcmthesis\|gmcmthesis' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
            if ! grep -q '\\maketitle' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
                # 五一杯模板有手动承诺书+封面，不需要 \maketitle
                # 检测方式：五一杯模板有"承诺书"或"五一数学建模"字样
                if grep -q '承诺书\|五一数学建模\|五一杯' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
                    echo "  ✓ 五一杯模板（手动封面），不需要 \\maketitle"
                else
                    echo "  ⛔ cumcmthesis/gmcmthesis 模板缺少 \\maketitle，自动插入..."
                    sed -i '/\\begin{document}/a \\\\maketitle' "$PAPER_DIR/论文正文.tex"
                    echo "  ✓ 已在 \\begin{document} 后插入 \\maketitle"
                fi
            fi
        fi
    else
        echo "  ✓ 非 \\title 模板（stats/dongsansheng/huashubei/diangongbei 等），跳过"
    fi
fi

# 9.8 符号说明/模型假设分页处理
# 策略：
#   - 模型假设（assumption）：用 \needspace{20\baselineskip}，够放就不换页
#   - 符号说明（symbol）：用 \needspace{15\baselineskip}，确保标题和表格在同一页
echo "--- 修复符号说明/模型假设分页 ---"
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    is_assumption=false
    is_symbol=false

    if echo "$bn" | grep -qi 'assumption'; then
        is_assumption=true
    elif grep -q '\\section{模型假设}\|\\section.*假设' "$f" 2>/dev/null; then
        is_assumption=true
    fi

    if echo "$bn" | grep -qi 'symbol'; then
        is_symbol=true
    elif grep -q '\\section{符号说明}\|\\section.*符号' "$f" 2>/dev/null; then
        is_symbol=true
    fi

    if [ "$is_assumption" = true ]; then
        # 模型假设：移除 \clearpage，改用 \needspace + \nopagebreak
        if grep -q '\\clearpage' "$f" 2>/dev/null; then
            echo "  $bn: 移除 \\clearpage，改用 \\needspace + \\nopagebreak"
            sed -i '/\\clearpage/d' "$f" 2>/dev/null
        fi
        if ! grep -B2 '\\section{' "$f" 2>/dev/null | grep -q '\\needspace'; then
            echo "  $bn: 在 \\section 前添加 \\needspace{20\\baselineskip}"
            # 用 sed 的 i 命令在匹配行前插入（避免 \n 兼容性问题）
            sed -i '/\\section{模型假设}/i \\needspace{20\\baselineskip}' "$f" 2>/dev/null
            if ! grep -q '\\section{模型假设}' "$f" 2>/dev/null; then
                sed -i '/\\section{.*假设.*}/i \\needspace{20\\baselineskip}' "$f" 2>/dev/null
            fi
        fi
        # 在 \section 后插入 \nopagebreak[4]，防止标题和内容分页
        if ! grep -A1 '\\section{' "$f" 2>/dev/null | grep -q '\\nopagebreak'; then
            echo "  $bn: 在 \\section 后添加 \\nopagebreak[4]（防止标题和内容分离）"
            sed -i '/\\section{模型假设}/a \\nopagebreak[4]' "$f" 2>/dev/null
            if ! grep -q '\\section{模型假设}' "$f" 2>/dev/null; then
                sed -i '/\\section{.*假设.*}/a \\nopagebreak[4]' "$f" 2>/dev/null
            fi
        fi
    fi

    if [ "$is_symbol" = true ]; then
        # 符号说明：用 longtable 替代 table+tabular，自动跨页
        # longtable 天然支持跨页，标题永远在表格开头，不存在分离问题

        # 移除之前可能加的分页控制
        sed -i '/\\clearpage/d' "$f" 2>/dev/null
        sed -i '/\\needspace.*baselineskip/d' "$f" 2>/dev/null
        sed -i '/\\nopagebreak/d' "$f" 2>/dev/null

        # 删引导文字
        sed -i '/本文所用主要符号/d' "$f" 2>/dev/null
        sed -i '/本文.*符号.*含义.*表/d' "$f" 2>/dev/null
        sed -i '/主要符号.*如.*所示/d' "$f" 2>/dev/null

        # table+tabular → longtable（简单可靠的 sed 方案）
        if grep -q '\\begin{table}' "$f" 2>/dev/null; then
            echo "  $bn: table+tabular → longtable"
            # 删 \begin{table}[任何参数] 和 \end{table}
            sed -i '/\\begin{table}/d' "$f" 2>/dev/null
            sed -i '/\\end{table}/d' "$f" 2>/dev/null
            # 删 \centering（longtable 自带居中）
            sed -i '/\\centering/d' "$f" 2>/dev/null
            # \begin{tabular} → \begin{longtable}
            sed -i 's/\\begin{tabular}/\\begin{longtable}/g' "$f" 2>/dev/null
            # \end{tabular} → \end{longtable}
            sed -i 's/\\end{tabular}/\\end{longtable}/g' "$f" 2>/dev/null
            # \caption 移到 \toprule 前面（longtable 的 caption 必须在表格内部第一行）
            # 先提取 caption 行，删掉原位置，插入到 \toprule 前
            CAPTION_LINE=$(grep '\\caption{' "$f" 2>/dev/null | head -1)
            if [ -n "$CAPTION_LINE" ]; then
                sed -i '/\\caption{/d' "$f" 2>/dev/null
                # 在 \toprule 前插入 caption + \\
                sed -i "/\\\\toprule/i ${CAPTION_LINE} \\\\\\\\" "$f" 2>/dev/null
            fi
            # 确保 论文正文.tex 有 longtable 包
            if [ -f "$PAPER_DIR/论文正文.tex" ] && ! grep -q 'usepackage.*longtable' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
                sed -i '/\\begin{document}/i \\usepackage{longtable}' "$PAPER_DIR/论文正文.tex" 2>/dev/null
            fi
        fi
        echo "  $bn: 符号说明修复完成（longtable 自动跨页）"
    fi
done

echo "=== 清理完成 ==="

# ============================================================
# 编译后检查（编译完成后执行）
# ============================================================

# 10. 检查目录是否生成
echo "--- 检查目录 ---"
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    if grep -q 'tableofcontents' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        if [ ! -f "$PAPER_DIR/论文正文.toc" ]; then
            echo "  ⚠ 论文正文.tex 有 \\tableofcontents 但 论文正文.toc 不存在，目录可能未生成（需要编译两遍）"
        elif [ ! -s "$PAPER_DIR/论文正文.toc" ]; then
            echo "  ⚠ 论文正文.toc 为空，目录未正确生成（需要完整 4 步编译）"
        else
            echo "  ✓ 论文正文.toc 存在"
        fi
    fi
fi

# 11. 检查中英文摘要是否都存在（中文论文）
echo "--- 检查摘要 ---"
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    if grep -q 'ctex\|ctexart\|ctexbook' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        ZH_ABSTRACT=$(grep -rl '摘.*要' "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null | wc -l)
        EN_ABSTRACT=$(grep -rl 'Abstract' "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null | wc -l)
        [ "$ZH_ABSTRACT" -gt 0 ] && echo "  ✓ 中文摘要存在" || echo "  ⚠ 未找到中文摘要"
        [ "$EN_ABSTRACT" -gt 0 ] && echo "  ✓ 英文摘要存在" || echo "  ⚠ 未找到英文摘要"
    fi
fi

# 12. 检查 \bibliography{references} 是否存在
echo "--- 检查参考文献配置 ---"
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    if grep -q '\\bibliography' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        echo "  ✓ \\bibliography 命令存在"
    else
        echo "  ⚠ 论文正文.tex 中没有 \\bibliography 命令，参考文献不会出现在 PDF 中！"
    fi
    if [ -f "$PAPER_DIR/references.bib" ]; then
        BIB_ENTRIES=$(grep -c '^@' "$PAPER_DIR/references.bib" 2>/dev/null)
        echo "  ✓ references.bib 存在（$BIB_ENTRIES 条）"
    else
        echo "  ⚠ references.bib 不存在！"
    fi
fi

# 13. 检查生成的 PDF 图是否都被正文引用
echo "--- 检查未引用的 PDF 图 ---"
UNUSED_FIGS=0
for pdf in 图表/*.pdf; do
    [ -f "$pdf" ] || continue
    basename=$(basename "$pdf")
    if ! grep -rq "$basename" "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 2>/dev/null; then
        echo "  ⚠ $basename 未被正文引用"
        UNUSED_FIGS=$((UNUSED_FIGS + 1))
    fi
done
[ "$UNUSED_FIGS" -eq 0 ] && echo "  ✓ 所有 PDF 图都已引用" || echo "  共 $UNUSED_FIGS 个 PDF 图未引用"

echo "=== 全部检查完成 ==="

# 图片宽度统一化（防止图大小不一致）
# 规则：所有 \includegraphics 的 width 统一为 0.85\textwidth
# 过小（<0.7）会导致图太小看不清，过大（>0.95）会导致图撑满页面
echo "--- 图片宽度统一化 ---"
FIG_WIDTH_FIXES=0
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 图表/图表引用.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    # 把 width=0.3~0.69\textwidth 的改成 0.85\textwidth（太小）
    if grep -qP 'width\s*=\s*0\.[0-6]\d*\\textwidth' "$f" 2>/dev/null; then
        sed -i -E 's/width\s*=\s*0\.[0-6][0-9]*\\textwidth/width=0.85\\textwidth/g' "$f" 2>/dev/null
        echo "  $bn: 过小图片 width → 0.85\\textwidth"
        FIG_WIDTH_FIXES=$((FIG_WIDTH_FIXES+1))
    fi
    # 把 width=\textwidth（1.0）改成 0.85\textwidth（太大，撑满页面不好看）
    # 但保留 width=\textwidth 在 resizebox 内部的（那是表格缩放，不是图片）
    if grep -qP 'includegraphics\[.*width\s*=\s*\\textwidth' "$f" 2>/dev/null; then
        sed -i 's/\(includegraphics\[.*\)width\s*=\s*\\textwidth/\1width=0.85\\textwidth/g' "$f" 2>/dev/null
        echo "  $bn: 满宽图片 width → 0.85\\textwidth"
        FIG_WIDTH_FIXES=$((FIG_WIDTH_FIXES+1))
    fi
done
[ "$FIG_WIDTH_FIXES" -gt 0 ] && echo "  $FIG_WIDTH_FIXES 个文件修复了图片宽度" || echo "  图片宽度正常"

# TikZ resizebox auto-wrap (prevent tikzpicture from exceeding page width/height)
echo "--- TikZ resizebox check ---"

# 先修复浅色注释文字（gray!30~gray!70 改成 black）
for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 图表/*.tex; do
    [ -f "$f" ] || continue
    if grep -qP 'color=gray![3-6]0' "$f" 2>/dev/null; then
        echo "  Fixing light gray text in $(basename $f) -> black"
        sed -i 's/color=gray![3-6]0/color=black/g' "$f" 2>/dev/null
    fi
    # 也修复 note 样式定义中的浅色
    if grep -q 'note/.style.*color=gray' "$f" 2>/dev/null; then
        echo "  Fixing note style in $(basename $f) -> black"
        sed -i 's/\(note\/\.style.*\)color=gray![0-9]*/\1color=black/' "$f" 2>/dev/null
    fi
    # 删除 on background layer（会导致黑底）
    if grep -q 'on background layer' "$f" 2>/dev/null; then
        echo "  Removing 'on background layer' from $(basename $f)"
        sed -i '/begin{scope}\[on background layer\]/d' "$f" 2>/dev/null
        sed -i '/end{scope}.*background/d' "$f" 2>/dev/null
        # 清理残留的空 scope（删了 begin 和 end 后可能留下孤立的 end{scope}）
    fi
done

for f in "$PAPER_DIR"/章节/*.tex "$PAPER_DIR"/论文正文.tex 图表/*.tex; do
    [ -f "$f" ] || continue
    if grep -q '\\begin{tikzpicture}' "$f" 2>/dev/null; then
        if ! grep -q 'adjustbox{max width' "$f" 2>/dev/null; then
            echo "  Wrapping tikzpicture in $(basename $f) with adjustbox"
            sed -i 's/\\begin{tikzpicture}/\\adjustbox{max width=\\textwidth}{%\n\\begin{tikzpicture}/' "$f" 2>/dev/null
            sed -i 's/\\end{tikzpicture}/\\end{tikzpicture}\n}%/' "$f" 2>/dev/null
        fi
    fi
done
# Ensure adjustbox package is loaded
if [ -f "$PAPER_DIR/论文正文.tex" ]; then
    if grep -q 'adjustbox' "$PAPER_DIR"/章节/*.tex 2>/dev/null && ! grep -q 'usepackage.*adjustbox' "$PAPER_DIR/论文正文.tex" 2>/dev/null; then
        echo "  Adding \\usepackage{adjustbox} to 论文正文.tex"
        sed -i '/\\begin{document}/i \\\\usepackage{adjustbox}' "$PAPER_DIR/论文正文.tex" 2>/dev/null
    fi
fi

# TikZ library auto-inject
echo "--- TikZ library check ---"
MAIN_TEX="$PAPER_DIR/论文正文.tex"
if [ -f "$MAIN_TEX" ]; then
    # Check if any section uses tikzpicture
    has_tikz=$(grep -rl 'tikzpicture\|\\begin{tikzpicture}' "$PAPER_DIR"/章节/*.tex 2>/dev/null | wc -l)
    if [ "$has_tikz" -gt 0 ]; then
        # Ensure tikz package is loaded
        if ! grep -q 'usepackage{tikz}' "$MAIN_TEX" 2>/dev/null; then
            echo "  Adding \\usepackage{tikz} to 论文正文.tex"
            sed -i '/\\begin{document}/i \\\\usepackage{tikz}\n\\\\usetikzlibrary{arrows.meta, positioning, shapes.geometric, calc, decorations.pathreplacing, shadows, fit, backgrounds}' "$MAIN_TEX" 2>/dev/null
        fi
        # Ensure tikz libraries are loaded
        if ! grep -q 'usetikzlibrary' "$MAIN_TEX" 2>/dev/null; then
            echo "  Adding \\usetikzlibrary to 论文正文.tex"
            sed -i '/usepackage{tikz}/a \\\\usetikzlibrary{arrows.meta, positioning, shapes.geometric, calc, decorations.pathreplacing, shadows, fit, backgrounds}' "$MAIN_TEX" 2>/dev/null
        fi
        # Ensure backgrounds and fit libraries are present (may have been injected without them)
        if grep -q 'usetikzlibrary' "$MAIN_TEX" 2>/dev/null; then
            if ! grep -q 'backgrounds' "$MAIN_TEX" 2>/dev/null; then
                echo "  Adding missing 'backgrounds' library"
                sed -i 's/\\usetikzlibrary{/\\usetikzlibrary{backgrounds, fit, /' "$MAIN_TEX" 2>/dev/null
            elif ! grep -q '\bfit\b' "$MAIN_TEX" 2>/dev/null; then
                echo "  Adding missing 'fit' library"
                sed -i 's/\\usetikzlibrary{/\\usetikzlibrary{fit, /' "$MAIN_TEX" 2>/dev/null
            fi
        fi
        echo "  TikZ libraries ensured"
    else
        echo "  No TikZ content found, skipping"
    fi
fi

# 10. 移除所有 section 文件中的 \nopagebreak（实践证明弊大于利，会导致空白页）
# ⛔ 跳过符号说明和模型假设文件（9.8 步刚加了 \nopagebreak[4]）
echo "--- 移除 nopagebreak ---"
NOPAGEBREAK_FIXES=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    # 跳过符号说明和模型假设（9.8 步需要保留 \nopagebreak[4]）
    if echo "$bn" | grep -qi 'symbol\|assumption'; then
        continue
    fi
    if grep -q '\\section{符号说明}\|\\section{模型假设}\|\\section.*假设\|\\section.*符号' "$f" 2>/dev/null; then
        continue
    fi
    if grep -q '\\nopagebreak' "$f" 2>/dev/null; then
        sed -i '/\\nopagebreak/d' "$f" 2>/dev/null
        echo "  removed nopagebreak from $(basename $f)"
        NOPAGEBREAK_FIXES=$((NOPAGEBREAK_FIXES + 1))
    fi
done
[ "$NOPAGEBREAK_FIXES" -gt 0 ] && echo "  $NOPAGEBREAK_FIXES 个文件移除了 nopagebreak" || echo "  无需修复"

# 11. 移除正文中多余的 \newpage 和 \clearpage（section 文件内部不应有手动分页）
# ⛔ 跳过符号说明和模型假设文件（9.8 步刚加了 \clearpage）
echo "--- 移除正文多余 newpage/clearpage ---"
NEWPAGE_FIXES=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    # 跳过符号说明和模型假设（有 \needspace 需要保留）
    if echo "$bn" | grep -qi 'symbol\|assumption'; then
        continue
    fi
    if grep -q '\\section{符号说明}\|\\section{模型假设}' "$f" 2>/dev/null; then
        continue
    fi
    if grep -q '\\newpage\|\\clearpage' "$f" 2>/dev/null; then
        sed -i '/\\newpage/d; /\\clearpage/d' "$f" 2>/dev/null
        echo "  removed newpage/clearpage from $bn"
        NEWPAGE_FIXES=$((NEWPAGE_FIXES + 1))
    fi
done
[ "$NEWPAGE_FIXES" -gt 0 ] && echo "  $NEWPAGE_FIXES 个文件移除了 newpage/clearpage" || echo "  无需修复"

# 11.5 检测章节末尾空白（最后一页内容太少）
echo "--- 检测章节末尾空白 ---"
THIN_ENDINGS=0
for f in "$PAPER_DIR"/章节/*.tex; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    echo "$bn" | grep -qi 'symbol\|assumption\|appendix\|A_code' && continue
    chars=$(wc -c < "$f" 2>/dev/null || echo 0)
    est_pages=$((chars / 900))
    tail_content=$(tail -c 300 "$f" 2>/dev/null | grep -v '^\s*$' | grep -v '^\\' | wc -c)
    if [ "$est_pages" -ge 2 ] && [ "$tail_content" -lt 50 ]; then
        echo "  ⚠ $bn: 章节末尾可能有空白（最后300字节实质内容仅 ${tail_content} 字节）"
        echo "    → 建议在章节末尾添加'本章小结'段落（2-3句话总结本章并预告下章）"
        THIN_ENDINGS=$((THIN_ENDINGS+1))
    fi
done
[ "$THIN_ENDINGS" -gt 0 ] && echo "  $THIN_ENDINGS 个章节末尾可能有空白" || echo "  无需修复"

echo "=== compile_utils.sh done ==="
