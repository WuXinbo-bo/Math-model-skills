#!/bin/bash
# figure_check.sh — 数据图表代码质量自检
# 用法: bash 工具/figure_check.sh

echo "=== 图表代码质量自检 ==="
violations=0
for script in 图表/gen_fig*.py; do
    [ -f "$script" ] || continue
    bn=$(basename "$script")
    # 硬编码颜色 — 检测所有非 PALETTE 的颜色值
    hardcoded=$(grep -Pn "color\s*=\s*['\"]#[0-9a-fA-F]" "$script" 2>/dev/null | grep -v "PALETTE\|COLORS\[" | grep -v "edgecolor.*white\|facecolor.*white\|cmap\|linecolor" | head -5)
    if [ -n "$hardcoded" ]; then
        echo "CRITICAL $bn: 硬编码颜色 — FIX: 用 PALETTE[n] 或 COLORS['up/down/grid'] 替代"
        echo "$hardcoded" | head -3
        violations=$((violations+1))
    fi
    # 检测英文颜色名（grey, red, blue, green 等）
    named_colors=$(grep -Pn "color\s*=\s*['\"](?:grey|gray|red|blue|green|orange|purple|black|brown)['\"]" "$script" 2>/dev/null | grep -v "PALETTE\|COLORS\[" | head -3)
    if [ -n "$named_colors" ]; then
        echo "CRITICAL $bn: 使用了英文颜色名 — FIX: 用 PALETTE[n] 或 COLORS['ref_line/grid/text'] 替代"
        echo "$named_colors" | head -3
        violations=$((violations+1))
    fi
    # plt.title
    if grep -n 'plt\.title\|ax\.set_title' "$script" 2>/dev/null; then
        echo "WARNING $bn: plt.title/set_title，标题应只在 LaTeX caption 中"; violations=$((violations+1))
    fi
    # 没有 setup_style — CRITICAL: will produce ugly matplotlib default styling
    if ! grep -q 'setup_style' "$script" 2>/dev/null; then
        echo "CRITICAL $bn: missing setup_style() — figure will use ugly matplotlib defaults — FIX: add 'from 工具.plot_utils import setup_style; setup_style()' at top"; violations=$((violations+1))
    fi
    # 没有 PALETTE 引用 — likely using hardcoded or default colors
    if ! grep -q 'PALETTE' "$script" 2>/dev/null && ! grep -q 'setup_style' "$script" 2>/dev/null; then
        echo "CRITICAL $bn: no PALETTE and no setup_style — colors will be matplotlib default blue — FIX: add setup_style() and use PALETTE[0], PALETTE[1]"; violations=$((violations+1))
    fi
    # 默认蓝色
    if grep -n '1f77b4' "$script" 2>/dev/null; then
        echo "CRITICAL $bn: matplotlib 默认蓝色 #1f77b4 — FIX: replace with PALETTE[0]"; violations=$((violations+1))
    fi
    # 红绿灯配色 (RdYlGn)
    if grep -n 'RdYlGn' "$script" 2>/dev/null; then
        echo "CRITICAL $bn: RdYlGn colormap (traffic light) — FIX: use cmap='coolwarm' instead"; violations=$((violations+1))
    fi
    # RdBu_r 深沉配色
    if grep -n "cmap.*['\"]RdBu_r['\"]" "$script" 2>/dev/null; then
        echo "CRITICAL $bn: RdBu_r colormap is too dark — FIX: use cmap='coolwarm' instead"; violations=$((violations+1))
    fi
    # RdBu 也太重
    if grep -Pn "cmap\s*=\s*['\"]RdBu['\"]" "$script" 2>/dev/null; then
        echo "CRITICAL $bn: RdBu colormap is too dark — FIX: use cmap='coolwarm' instead"; violations=$((violations+1))
    fi
    # 深色背景主题
    if grep -n "dark_background\|darkgrid\|set_style.*dark" "$script" 2>/dev/null; then
        echo "CRITICAL $bn: dark background theme — FIX: use setup_style() which sets white background"; violations=$((violations+1))
    fi
    # .pdf 污染 — 路径/变量名被 .pdf 后缀污染
    if grep -n "setup_style.*\.pdf\|sys\.path.*\.pdf\|palette=.*\.pdf\|xlabel.*\.pdf\|ylabel.*\.pdf\|copy2.*\.pdf'" "$script" 2>/dev/null; then
        echo "CRITICAL $bn: .pdf suffix leaked into code (setup_style/path/label) — remove .pdf from non-filename strings"; violations=$((violations+1))
    fi
    # 深色/土色检测 — JAMA/Lancet/AAAS/Morandi 等土色配色，应改用 Soft/Tableau/NPG/NEJM
    if grep -Pn '#374E55|#00468B|#3B4992|#80796B|#1B1919|#631879|#AD002A|#96C0CE.*#C4956A|#2c3e50|#2C3E50|#34495e|#34495E' "$script" 2>/dev/null | grep -v '^#\|^\s*#' ; then
        echo "WARNING $bn: dark/earth tone colors detected — use PALETTE[n] or setup_style() instead"; violations=$((violations+1))
    fi
    # 已移除的土色配色方案名称检测
    if grep -n "palette='jama'\|palette='lancet'\|palette='aaas'\|palette='morandi'" "$script" 2>/dev/null; then
        echo "WARNING $bn: removed ugly palette — use setup_style() (Soft) or 'tableau'/'npg'/'nejm'/'science'/'colorblind'"; violations=$((violations+1))
    fi
    # colormap 渐变色
    if grep -n 'plt\.cm\.\|cm\.get_cmap\|LinearSegmentedColormap' "$script" 2>/dev/null | grep -v 'heatmap\|contour\|imshow\|pcolormesh' ; then
        echo "WARNING $bn: 柱状图/折线图不应用 colormap"; violations=$((violations+1))
    fi
    # ax.grid
    if grep -n 'ax\.grid\|plt\.grid' "$script" 2>/dev/null; then
        echo "WARNING $bn: 不要手动 ax.grid()"; violations=$((violations+1))
    fi
    # 空数值占位符
    if grep -n "= $\|= '\|= \"" "$script" 2>/dev/null | grep -i 'coef\|effect\|path\|a =\|b =\|c =' ; then
        echo "WARNING $bn: 空数值占位符"; violations=$((violations+1))
    fi
done
echo "自检完成: $violations 个违规"


# === Chart type anti-pattern detection ===
echo ""
echo "=== 图表类型反模式检测 ==="
type_violations=0
for script in 图表/gen_fig*.py; do
    [ -f "$script" ] || continue
    bn=$(basename "$script")
    # Detect plain bar charts — only warn if it's the 4th+ bar chart in the project
    bar_count=$(grep -rl 'ax\.bar\b\|plt\.bar\b' 图表/gen_fig*.py 2>/dev/null | wc -l)
    if grep -n 'ax\.bar\b\|plt\.bar\b' "$script" 2>/dev/null | grep -v 'bar3d\|barh\|waterfall\|stacked' > /dev/null; then
        if [ "$bar_count" -gt 3 ]; then
            echo "ENHANCEMENT $bn: 第 ${bar_count} 个柱状图 → 同类型不超过 3 次，考虑换其他图表类型"
            type_violations=$((type_violations+1))
        fi
    fi
    # Detect plain box plots (should be Rain Cloud)
    if grep -n 'boxplot\|box_plot' "$script" 2>/dev/null | grep -v 'rain\|violin\|strip\|swarm' > /dev/null; then
        echo "ENHANCEMENT $bn: plain box plot → use Rain Cloud Plot (violin + box + strip)"
        type_violations=$((type_violations+1))
    fi
    # Detect pie charts (should be Donut/Waffle)
    if grep -n 'plt\.pie\|ax\.pie' "$script" 2>/dev/null | grep -v 'donut\|waffle\|wedgeprops' > /dev/null; then
        echo "ENHANCEMENT $bn: pie chart → use Donut Chart (add wedgeprops + pctdistance)"
        type_violations=$((type_violations+1))
    fi
    # Detect plain horizontal bar for importance (should be SHAP)
    if grep -n 'barh' "$script" 2>/dev/null | grep -qi 'importance\|feature\|variable' 2>/dev/null; then
        echo "ENHANCEMENT $bn: horizontal bar for feature importance → use SHAP Summary Plot"
        type_violations=$((type_violations+1))
    fi
    # Detect plain heatmap without dendrogram
    if grep -n 'heatmap\|imshow' "$script" 2>/dev/null | grep -qi 'corr\|matrix' 2>/dev/null; then
        if ! grep -q 'dendrogram\|clustermap\|linkage' "$script" 2>/dev/null; then
            echo "ENHANCEMENT $bn: plain correlation heatmap → add dendrogram clustering"
            type_violations=$((type_violations+1))
        fi
    fi
    # Detect heatmap/imshow with very few rows (≤3 models → should be table or dumbbell)
    if grep -q 'heatmap\|imshow' "$script" 2>/dev/null; then
        # Check if data array has ≤3 rows
        few_rows=$(python3 -c "
import re
with open('$script') as f: c = f.read()
# Find array definitions like np.array([[...],[...],...])
for m in re.finditer(r'np\.array\(\[(\[.*?\](?:,\s*\[.*?\])*)\]\)', c, re.DOTALL):
    rows = m.group(1).count('[')
    if rows <= 3: print('FEW_ROWS'); break
" 2>/dev/null)
        if [ "$few_rows" = "FEW_ROWS" ]; then
            echo "ENHANCEMENT $bn: heatmap with ≤3 rows → use Dumbbell Chart or Three-line table instead"
            type_violations=$((type_violations+1))
        fi
    fi
done
echo "图表类型检测: $type_violations 个可升级"

total=$((violations + type_violations))
echo ""
echo "=== 总计: $violations 个违规 + $type_violations 个可升级 ==="

# === 配方使用检测 ===
echo ""
echo "=== 配方代码使用检测 ==="
recipe_issues=0
for script in 图表/gen_fig*.py; do
    [ -f "$script" ] || continue
    bn=$(basename "$script")
    # 检查是否用了 save_fig（配方标准保存方式）
    if ! grep -q 'save_fig\|savefig' "$script" 2>/dev/null; then
        echo "WARNING $bn: 没有 save_fig/savefig 调用"; recipe_issues=$((recipe_issues+1))
    fi
    # 检查是否用了 seaborn 高级 API 而不是配方代码
    if grep -q 'sns\.barplot\|sns\.boxplot\|sns\.violinplot\|sns\.lineplot\|sns\.scatterplot' "$script" 2>/dev/null; then
        if ! grep -q 'figure_recipes\|recipe\|配方' "$script" 2>/dev/null; then
            echo "ENHANCEMENT $bn: 使用了 seaborn 高级 API — 应参考配方代码获得更好的视觉效果（渐变填充、标注框等）"
            recipe_issues=$((recipe_issues+1))
        fi
    fi
    # 检查是否有 smart_labels（标签密集的图应该用）
    text_count=$(grep -c 'ax\.text\|ax\.annotate' "$script" 2>/dev/null || echo 0)
    if [ "$text_count" -gt 3 ] && ! grep -q 'smart_labels\|adjust_text\|adjustText' "$script" 2>/dev/null; then
        echo "WARNING $bn: $text_count 个文字标注但没用 smart_labels — 可能有重叠"
        recipe_issues=$((recipe_issues+1))
    fi
    # 检查是否有 auto_legend
    if grep -q 'ax\.legend\|plt\.legend' "$script" 2>/dev/null && ! grep -q 'auto_legend' "$script" 2>/dev/null; then
        echo "INFO $bn: 使用了 ax.legend() — 建议改用 auto_legend(ax) 自动选位"
    fi
done
echo "配方检测: $recipe_issues 个问题"

# === 规划对照检测 ===
echo ""
echo "=== 规划对照检测 ==="
plan_file=""
for pf in 选题规划.md 问题分析.md 论文规划.md; do
    [ -f "$pf" ] && plan_file="$pf" && break
done
if [ -n "$plan_file" ]; then
    echo "规划文档: $plan_file"
    # 提取规划中的图表文件名
    planned=$(grep -oP 'fig_\w+' "$plan_file" 2>/dev/null | sort -u)
    generated=$(ls 图表/gen_fig_*.py 2>/dev/null | sed 's|图表/gen_||;s|\.py||' | sort -u)
    plan_count=$(echo "$planned" | grep -c . 2>/dev/null || echo 0)
    gen_count=$(echo "$generated" | grep -c . 2>/dev/null || echo 0)
    echo "规划图表: $plan_count 个 | 已生成脚本: $gen_count 个"
    # 检查缺失
    missing=0
    for fig in $planned; do
        if ! ls 图表/gen_${fig}*.py 2>/dev/null > /dev/null; then
            echo "MISSING: $fig — 规划中有但未生成脚本"
            missing=$((missing+1))
        fi
    done
    if [ "$missing" -eq 0 ]; then
        echo "✅ 所有规划图表都有对应脚本"
    else
        echo "❌ $missing 个规划图表缺失脚本"
    fi
else
    echo "⚠ 未找到规划文档（选题规划.md / 问题分析.md / 论文规划.md）"
fi

total=$((violations + type_violations + recipe_issues))
echo ""
echo "=========================================="
echo "  总计: $violations 违规 + $type_violations 可升级 + $recipe_issues 配方问题"
echo "=========================================="
exit $violations
