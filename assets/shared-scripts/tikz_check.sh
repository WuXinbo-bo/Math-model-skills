#!/bin/bash
# tikz_check.sh — TikZ 架构图质量自检
# 用法: bash 工具/tikz_check.sh 图表/tikz_architecture_examples.tex

tikz_file="${1:-图表/tikz_architecture_examples.tex}"
[ -f "$tikz_file" ] || { echo "TikZ 文件不存在: $tikz_file，跳过"; exit 0; }

echo "=== TikZ 架构图质量自检: $tikz_file ==="
critical=0

# 模板配色检查（支持 5 套配色方案，检查是否使用了任意一套的 rgb 格式）
has_rgb_style=$(grep -c 'rgb,255:red,' "$tikz_file" 2>/dev/null || echo 0)
if [ "$has_rgb_style" -lt 2 ]; then
    echo "CRITICAL: 节点没有使用 rgb,255 格式的配色（应从 figure_style_guide.md 的 5 套方案中选一套）"; critical=$((critical+1))
fi
# 检查是否每个阶段用了不同颜色（应该统一用一套 main+sub 两色）
unique_fills=$(grep -oP 'fill=\{rgb,255:red,\d+;green,\d+;blue,\d+\}' "$tikz_file" 2>/dev/null | sort -u | wc -l)
if [ "$unique_fills" -gt 4 ]; then
    echo "CRITICAL: 发现 $unique_fills 种不同 rgb 填充色，应统一用一套配色方案（main+sub 两色 + dashbox 灰色）"; critical=$((critical+1))
fi
# Also check for named color rainbow (blue, red, green, orange, etc.)
named_fills=$(grep -oP 'fill=\w+!?\d*' "$tikz_file" 2>/dev/null | grep -v 'fill=none\|fill=white\|fill=gray\|fill=black' | sort -u | wc -l)
if [ "$named_fills" -gt 4 ]; then
    echo "CRITICAL: 发现 $named_fills 种不同命名填充色 — 彩虹效果！应统一用 Template 4 的双色方案"; critical=$((critical+1))
fi

# 禁止项检查
if grep -q '\\fill\[.*rgb.*rounded corners' "$tikz_file" 2>/dev/null; then
    echo "CRITICAL: 发现灰色大背景 \\fill，必须删除"; critical=$((critical+1))
fi
if grep -q 'on background layer' "$tikz_file" 2>/dev/null; then
    echo "CRITICAL: 发现 on background layer，必须删除"; critical=$((critical+1))
fi
if grep -q 'fit=(' "$tikz_file" 2>/dev/null; then
    echo "CRITICAL: 发现 fit=()，必须改用手动坐标 dashbox"; critical=$((critical+1))
fi
if grep -qP 'fill=(blue|red|green|black|gray![7-9]0|gray!100|dark)(?!\!)' "$tikz_file" 2>/dev/null; then
    echo "CRITICAL: 发现深色填充"; critical=$((critical+1))
fi

# 浅色文字
light_gray=$(grep -cP 'color=gray![3-6]0' "$tikz_file" 2>/dev/null || echo 0)
note_style=$(grep -c 'note/.style' "$tikz_file" 2>/dev/null || echo 0)
[ "$light_gray" -gt 0 ] && { echo "CRITICAL: $light_gray 处浅色文字(gray!30~60)"; critical=$((critical+1)); }
[ "$note_style" -gt 0 ] && { echo "CRITICAL: 发现 note/.style，禁止浅色注释"; critical=$((critical+1)); }

# 白色文字
grep -q 'text=white' "$tikz_file" 2>/dev/null && echo "WARNING: 发现白色文字"

# 旋转文字
grep -q 'rotate=90' "$tikz_file" 2>/dev/null && echo "WARNING: 发现 rotate=90，建议水平文字"

# 粗箭头
grep -q 'bigarrow\|line width=1.8pt\|line width=2pt' "$tikz_file" 2>/dev/null || echo "WARNING: 没有粗箭头"

# 圆角
grep -q 'rounded corners' "$tikz_file" 2>/dev/null || echo "WARNING: 没有圆角"

# 节点重叠检测
echo "--- 重叠检测 ---"
python3 -c "
import re
with open('$tikz_file', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
all_nodes = []
for m in re.finditer(r'\\\\node\[([^\]]*)\].*?at\s*\(([^,]+),\s*([^)]+)\)', content):
    try:
        style = m.group(1)
        x, y = float(m.group(2).strip()), float(m.group(3).strip())
        w, h = 2.0, 0.6
        wm = re.search(r'minimum width=(\d+\.?\d*)cm', style)
        hm = re.search(r'minimum height=(\d+\.?\d*)cm', style)
        sm = re.search(r'minimum size=(\d+\.?\d*)cm', style)
        if wm: w = float(wm.group(1))
        if hm: h = float(hm.group(1))
        if sm: w = h = float(sm.group(1))
        is_box = 'dash' in style or 'dashed' in style
        all_nodes.append({'x':x,'y':y,'w':w,'h':h,'box':is_box})
    except: pass
overlaps = 0
for i in range(len(all_nodes)):
    a = all_nodes[i]
    for j in range(i+1, len(all_nodes)):
        b = all_nodes[j]
        if a['box'] != b['box']: continue
        if (a['x']-a['w']/2 < b['x']+b['w']/2 and b['x']-b['w']/2 < a['x']+a['w']/2 and
            a['y']-a['h']/2 < b['y']+b['h']/2 and b['y']-b['h']/2 < a['y']+a['h']/2):
            label = '虚线框' if a['box'] else '节点'
            print(f'CRITICAL: {label}重叠! ({a[\"x\"]},{a[\"y\"]}) vs ({b[\"x\"]},{b[\"y\"]})')
            overlaps += 1
if overlaps == 0 and all_nodes: print(f'OK: {len(all_nodes)} 个节点无重叠')
elif not all_nodes: print('INFO: 未检测到节点')
else: exit(1)
" 2>/dev/null
[ $? -ne 0 ] && critical=$((critical+1))

# 中文节点宽度检测（防文字溢出）
echo "--- 中文节点宽度检测 ---"
python3 -c "
import re
with open('$tikz_file', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
issues = 0
# 匹配 \node[...]{文字内容}
for m in re.finditer(r'\\\\node\[([^\]]*)\]\s*(?:\([^)]*\)\s*)?(?:at\s*\([^)]*\)\s*)?\{([^}]*)\}', content):
    style = m.group(1)
    text = m.group(2).strip()
    if not text or text == '': continue
    # 跳过纯 LaTeX 命令节点
    if text.startswith('\\\\') and len(text) < 5: continue
    # 计算中文字符数
    cn_chars = len([c for c in text if '\\u4e00' <= c <= '\\u9fff' or '\\u3000' <= c <= '\\u303f'])
    en_chars = len([c for c in text if c.isascii() and c.isalpha()])
    if cn_chars == 0: continue
    # 需要的最小宽度
    needed_w = cn_chars * 0.7 + en_chars * 0.35 + 1.0
    # 提取实际 minimum width
    wm = re.search(r'minimum width=(\d+\.?\d*)cm', style)
    twm = re.search(r'text width=(\d+\.?\d*)cm', style)
    actual_w = float(wm.group(1)) if wm else (float(twm.group(1)) if twm else 2.0)
    if actual_w < needed_w - 0.3:
        clean_text = text[:20].replace('\\\\\\\\', '/').replace('\\\\', '')
        print(f'WARNING: \"{clean_text}\" ({cn_chars}中+{en_chars}英) 需要 {needed_w:.1f}cm 但只有 {actual_w:.1f}cm')
        issues += 1
if issues == 0: print('OK: 中文节点宽度检查通过')
" 2>/dev/null

# 连线穿过节点检测（近似：检测 \draw 路径中间是否经过其他节点的坐标区域）
echo "--- 连线路径检测 ---"
python3 -c "
import re, math
with open('$tikz_file', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
# 收集所有节点位置
nodes = {}
for m in re.finditer(r'\\\\node\[([^\]]*)\]\s*\(([^)]*)\)\s*at\s*\(([^,]+),\s*([^)]+)\)', content):
    name = m.group(2).strip()
    try:
        x, y = float(m.group(3).strip()), float(m.group(4).strip())
        style = m.group(1)
        wm = re.search(r'minimum width=(\d+\.?\d*)cm', style)
        w = float(wm.group(1)) if wm else 2.0
        nodes[name] = (x, y, w/2)
    except: pass
# 检测 \draw 中的 -- 连接是否穿过中间节点
issues = 0
for m in re.finditer(r'\\\\draw.*?\(([^)]+)\).*?--.*?\(([^)]+)\)', content):
    src_name = m.group(1).strip().split('.')[0]
    dst_name = m.group(2).strip().split('.')[0]
    if src_name not in nodes or dst_name not in nodes: continue
    sx, sy, _ = nodes[src_name]
    dx, dy, _ = nodes[dst_name]
    # 检查是否有其他节点在连线路径上
    for name, (nx, ny, nr) in nodes.items():
        if name == src_name or name == dst_name: continue
        # 点到线段的距离
        line_len = math.sqrt((dx-sx)**2 + (dy-sy)**2)
        if line_len < 0.1: continue
        t = max(0, min(1, ((nx-sx)*(dx-sx) + (ny-sy)*(dy-sy)) / (line_len**2)))
        closest_x = sx + t * (dx - sx)
        closest_y = sy + t * (dy - sy)
        dist = math.sqrt((nx - closest_x)**2 + (ny - closest_y)**2)
        if dist < nr + 0.3 and 0.1 < t < 0.9:
            print(f'CRITICAL: 连线 {src_name}→{dst_name} 可能穿过节点 {name} (距离={dist:.2f}cm)')
            issues += 1
if issues == 0 and nodes: print(f'OK: {len(nodes)} 个节点，连线路径无穿过')
elif not nodes: print('INFO: 未检测到带名称的节点')
" 2>/dev/null
[ $? -ne 0 ] && critical=$((critical+1))

# 编译 overfull 检测（如果 .log 文件存在）
echo "--- Overfull 检测 ---"
log_file="${tikz_file%.tex}.log"
main_log="论文/编译日志.log"
for lf in "$log_file" "$main_log"; do
    [ -f "$lf" ] || continue
    overfull=$(grep -c 'Overfull.*hbox\|Overfull.*vbox' "$lf" 2>/dev/null || echo 0)
    if [ "$overfull" -gt 0 ]; then
        echo "WARNING: $overfull 个 Overfull 警告 (in $(basename $lf)) — 可能有文字溢出节点"
        grep 'Overfull' "$lf" 2>/dev/null | head -5
    else
        echo "OK: 无 Overfull 警告 (in $(basename $lf))"
    fi
    break
done

echo "=== 自检完成: $critical 个 CRITICAL ==="
exit $critical
