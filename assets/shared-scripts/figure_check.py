#!/usr/bin/env python3

"""图表质量自检脚本 — Meta-model-agent 每生成一张图后运行此脚本检查代码质量。



用法：python 工具/figure_check.py 图表/gen_fig_xxx.py

输出：PASS 或 FAIL + 具体问题列表

"""

import sys

import re

from pathlib import Path





def check_figure_script(filepath: str) -> list:

    """检查单个图表脚本的质量问题，返回问题列表。"""

    issues = []

    path = Path(filepath)

    if not path.exists():

        return [f"文件不存在: {filepath}"]



    code = path.read_text(encoding="utf-8", errors="replace")

    lines = code.split("\n")



    # 1. 硬编码 hex 色值

    hex_pattern = re.compile(r"['\"]#[0-9A-Fa-f]{6}['\"]")

    allowed_hex_contexts = ["LinearSegmentedColormap", "from_list", "PALETTE", "COLORS", "_lighten"]

    for i, line in enumerate(lines, 1):

        if hex_pattern.search(line):

            if not any(ctx in line for ctx in allowed_hex_contexts):

                issues.append(f"L{i}: 硬编码色值 — 应使用 PALETTE[n]/COLORS['xxx']/_lighten()")



    # 2. set_title / plt.title

    for i, line in enumerate(lines, 1):

        stripped = line.strip()

        if stripped.startswith("#"):

            continue

        if "set_title(" in stripped or "plt.title(" in stripped:

            issues.append(f"L{i}: 使用了 set_title/plt.title — 标题应由 LaTeX caption 管理")



    # 3. 缺少 setup_style()

    if "setup_style()" not in code and "setup_style(" not in code:

        issues.append("缺少 setup_style() 调用 — 图表风格未初始化")



    # 4. save_fig 格式

    save_calls = re.findall(r"save_fig\(([^)]+)\)", code)

    for call in save_calls:

        args = [a.strip() for a in call.split(",")]

        if len(args) < 2:

            issues.append(f"save_fig 只有 {len(args)} 个参数 — 应为 save_fig(fig, 'path')")



    # 5. 缺少 spines 隐藏（热力图/3D/极坐标除外）

    is_heatmap = "heatmap" in code.lower() or "imshow" in code.lower() or "sns.heatmap" in code

    is_3d = "projection='3d'" in code or "Axes3D" in code

    is_polar = "polar=True" in code or "subplot_kw=dict(polar" in code

    if not is_heatmap and not is_3d and not is_polar:

        if "spines['top'].set_visible(False)" not in code and "spines['top']" not in code:

            issues.append("缺少 spines['top'].set_visible(False)")

        if "spines['right'].set_visible(False)" not in code and "spines['right']" not in code:

            issues.append("缺少 spines['right'].set_visible(False)")



    # 6. RdYlGn 交通灯色图

    if "RdYlGn" in code:

        issues.append("使用了 RdYlGn 交通灯色图 — 应改为 coolwarm/YlOrRd")



    # 7. gridspec 用于热力图+树状图（应该用 add_axes）

    if ("dendrogram" in code or "linkage" in code) and "GridSpec" in code:

        issues.append("热力图+树状图使用了 GridSpec — 应使用 fig.add_axes() 确保对齐")



    # 8. 密集标签未用 smart_labels

    text_calls = re.findall(r"ax\w*\.text\(", code)

    if len(text_calls) > 5 and "smart_labels" not in code:

        issues.append(f"有 {len(text_calls)} 个 ax.text() 调用但未使用 smart_labels() — 标签可能重叠")



    # 9. 中文内容但没有 setup_style

    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", code))

    if has_chinese and "setup_style" not in code:

        issues.append("包含中文但未调用 setup_style() — 中文可能显示为方块")



    # 10. 信息优先检查：不再用渐变、圆角标注框和多层叠加数量作为质量得分。

    style_score = 0  # legacy variable retained for compatibility; no longer used as a pass threshold

    style_missing = []



    # 是否有渐变填充 (fill_between / fill / alpha 填充)

    if "fill_between" in code or "fill(" in code or "axvspan" in code or "axhspan" in code:

        style_score += 1

    else:

        if "plot(" in code or "bar(" in code:

            style_missing.append("缺少渐变/半透明填充 — 配方用 fill_between/axvspan 增加层次感")



    # 是否有标注框 (bbox)

    if "bbox=dict(" in code or "bbox=" in code:

        style_score += 1

    else:

        if "annotate" in code or "ax.text(" in code:

            style_missing.append("标注文字缺少 bbox 背景框 — 配方用 bbox=dict(boxstyle='square,pad=0.3', facecolor='white', ...)")



    # 是否有 edgecolor='white' (柱子/散点的白色边框，增加层次)

    if "edgecolor='white'" in code or "edgecolors='white'" in code:

        style_score += 1

    else:

        if "bar(" in code or "scatter(" in code:

            style_missing.append("柱子/散点缺少 edgecolor='white' — 白色边框让元素更清晰")



    # 是否有 grid 设置

    if "grid(" in code or "grid=True" in code:

        style_score += 1

    else:

        if not is_heatmap and not is_polar:

            style_missing.append("缺少网格线 — 配方用 ax.grid(axis='y', alpha=0.15, linestyle='--')")



    # 是否有 tight_layout

    if "tight_layout" in code or "bbox_inches='tight'" in code:

        style_score += 1

    else:

        style_missing.append("缺少 fig.tight_layout() — 可能导致标签被裁切")



    # 是否有 zorder 控制图层

    if "zorder" in code:

        style_score += 1



    # 是否用了 _lighten() 做浅色变体

    if "_lighten(" in code:

        style_score += 1



    # 是否有 markeredgecolor='white' (散点/折线标记的白色边框)

    if "markeredgecolor='white'" in code:

        style_score += 1



    # 11. 组合图/多层叠加检测 — 高级图表应有多个视觉层

    layers = 0

    layer_details = []

    if "contour" in code or "contourf" in code:

        layers += 1; layer_details.append("KDE等高线")

    if "scatter(" in code:

        layers += 1; layer_details.append("散点")

    if "hexbin(" in code:

        layers += 1; layer_details.append("六边形分箱")

    if "fill_between" in code or "axvspan" in code:

        layers += 1; layer_details.append("区域填充")

    if "axhline" in code or "axvline" in code:

        layers += 1; layer_details.append("参考线")

    if "annotate(" in code:

        layers += 1; layer_details.append("箭头标注")

    if "colorbar" in code or "colorbar(" in code:

        layers += 1; layer_details.append("颜色条")

    if "legend(" in code or "auto_legend" in code:

        layers += 1; layer_details.append("图例")



    # 12. 边际分布检测（组合图标志）

    has_marginal = ("add_subplot(gs[0" in code or "ax_top" in code or

                    "ax_right" in code or "add_axes" in code)

    if has_marginal:

        layers += 1; layer_details.append("边际分布/多面板")



    # 13. 颜色映射检测（时间/类别维度编码）

    has_cmap = "cmap=" in code and ("scatter" in code or "hexbin" in code)

    if has_cmap:

        layers += 1; layer_details.append("颜色映射维度")



    # 简单图表（只有 1-2 层）给警告

    is_simple_type = ("barh(" in code and "scatter" not in code and

                      "contour" not in code)

    if layers < 2 and not is_simple_type and not is_heatmap and not is_3d:

        style_missing.append(

            f"视觉层次偏少（{layers} 层: {', '.join(layer_details) if layer_details else '无'}）"

            f"— 仅在额外图层编码数据、区间或基准时才允许叠加"

        )



    # 不因图形朴素而判失败；改为拒绝装饰性 AI 风格和无必要复杂度。
    rounded_boxes = len(re.findall(r"boxstyle\s*=\s*['\"]round", code, flags=re.IGNORECASE))
    if rounded_boxes:
        issues.append(f"检测到 {rounded_boxes} 个圆角标注框 — 默认改用无边框文字或直角框")

    decorative_tokens = [
        token for token in ("SimplePatchShadow", "patheffects", "set_path_effects", "shadow=True")
        if token.lower() in code.lower()
    ]
    if decorative_tokens:
        issues.append(f"检测到装饰性效果 {decorative_tokens} — 禁止用阴影或路径特效制造高级感")

    annotation_count = len(re.findall(r"(?:annotate|\.text)\(", code))
    if annotation_count > 8 and "smart_labels" not in code:
        issues.append(f"标注数量过多（{annotation_count}）— 只保留支持核心结论的标注")



    return issues





def main():

    if len(sys.argv) < 2:

        print("用法: python figure_check.py <script.py> [script2.py ...]")

        sys.exit(1)



    all_pass = True

    for filepath in sys.argv[1:]:

        issues = check_figure_script(filepath)

        name = Path(filepath).name

        if issues:

            print(f"FAIL: {name}")

            for issue in issues:

                print(f"  ✗ {issue}")

            all_pass = False

        else:

            print(f"PASS: {name}")



    sys.exit(0 if all_pass else 1)





if __name__ == "__main__":

    main()
