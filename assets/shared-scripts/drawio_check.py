#!/usr/bin/env python3

"""drawio_check.py — DrawIO 技术路线图/求解流程图结构自检

用法: python3 工具/drawio_check.py 图表/技术路线图.drawio roadmap

      python3 工具/drawio_check.py 图表/问题流程图_1.drawio flow

"""

import re, sys



def check_roadmap(content, filename):

    """检查技术路线图的逻辑结构、直角矩形合同和克制的学术表达。"""

    issues = []



    # ===== 必须有顶部三栏表头（研究阶段/研究内容/研究方法）=====

    has_header = bool(re.search(r'研究阶段|研究内容|研究方法|研究框架', content))

    if not has_header:

        issues.append("CRITICAL: 缺少顶部三栏表头（研究阶段/研究内容/研究方法）")



    # ===== 必须有六边形或圆形/箭头编号的阶段节点形状 =====

    has_stage_shape = bool(re.search(r'shape=hexagon|shape=step|shape=mxgraph\.arrows2\.arrow|ellipse', content))

    if not has_stage_shape:

        issues.append("CRITICAL: 缺少阶段节点形状（应使用 shape=hexagon / shape=step / ellipse 表示阶段递进）")



    # ===== 必须有粗主流程箭头连接阶段 =====

    arrows = len(re.findall(r'edgeStyle|endArrow', content))

    if arrows < 3:

        issues.append("CRITICAL: 阶段节点间连接不足（至少 3 个箭头/连线）")



    # ===== 必须有右栏研究方法 =====

    has_right_col = bool(re.search(r'文献综述|相关分析|回归|熵权法|TOPSIS|NSGA|PyTorch|Gurobi|蒙特卡洛|可视化|Matplotlib|LaTeX|CiteSpace|Pandas|随机森林|XGBoost|EDA|K-fold|Bootstrap|ECharts|归纳总结', content))

    if not has_right_col:

        issues.append("WARNING: 可能缺少右栏研究方法卡片")



    # ===== 必须有虚线框分组 =====

    has_dashed = bool(re.search(r'dashed=1|dashPattern', content))

    if not has_dashed:

        issues.append("WARNING: 没有虚线框容器 — 中栏每阶段应使用虚线框分组")



    # ===== 通用检查 =====

    # 节点文字可按信息需要使用单行或双行，不以卡片化副标题作为质量目标。

    nodes_with_br = len(re.findall(r'&lt;br&gt;|<br>', content))

    total_nodes = len(re.findall(r'vertex="1"', content))

    if total_nodes > 5 and nodes_with_br < total_nodes * 0.3:

        issues.append("WARNING: 大部分节点只有单行文字；仅在需要补充关键参数时增加简短第二行")



    # 矩形节点必须为直角；带 shape= 的菱形、圆形、六边形等保持原形状。

    for cell in re.findall(r'<mxCell\b[^>]*vertex="1"[^>]*>', content):

        style_match = re.search(r'style="([^"]*)"', cell)

        if not style_match:

            continue

        style = style_match.group(1)

        is_plain_rectangle = "shape=" not in style or "swimlane" in style

        if is_plain_rectangle and "rounded=1" in style:

            issues.append("CRITICAL: 矩形节点使用 rounded=1 — 全部流程图矩形必须使用 rounded=0 直角")

    if 'gradientColor' in content:

        issues.append("WARNING: 检测到渐变填充 — 默认使用纯色或灰阶")

    if 'shadow=1' in content:

        issues.append("WARNING: 检测到阴影 — 学术流程图默认禁用装饰阴影")

    unique_fills = set(re.findall(r'fillColor=#[A-Fa-f0-9]{6}', content))

    if len(unique_fills) > 5:

        issues.append(f"WARNING: 填充色过多（{len(unique_fills)}）— 建议灰阶加一个低饱和强调色")



    # 不能有图内标题（只检查 mxCell 的 value 属性，不包含 diagram name 等元数据）

    cell_values = re.findall(r'<mxCell[^>]+value="([^"]*)"', content)

    cell_values_text = " ".join(cell_values)

    has_title_node = bool(re.search(r'技术路线图|整体求解思路|研究技术路线', cell_values_text))

    if has_title_node:

        issues.append("CRITICAL: 图内有标题文字 — 违反零容忍规则第 11 条（标题由 LaTeX caption 管理）")



    # 居中检测

    containers = {}

    for m in re.finditer(r'<mxCell[^>]*id="([^"]*)"[^>]*parent="([^"]*)"[^>]*vertex="1"[^>]*>.*?<mxGeometry[^>]*x="(\d+\.?\d*)"[^>]*width="(\d+\.?\d*)"', content, re.DOTALL):

        cell_id, parent_id, x, w = m.group(1), m.group(2), float(m.group(3)), float(m.group(4))

        if parent_id not in ("0", "1"):

            if parent_id not in containers:

                containers[parent_id] = []

            containers[parent_id].append((x, w))



    off_center_count = 0

    for parent_id, children in containers.items():

        if len(children) < 2:

            continue

        lefts = [x for x, w in children]

        rights = [x + w for x, w in children]

        min_left = min(lefts)

        max_right = max(rights)

        content_center = (min_left + max_right) / 2

        container_match = re.search(r'<mxCell[^>]*id="' + re.escape(parent_id) + r'"[^>]*>.*?<mxGeometry[^>]*width="(\d+\.?\d*)"', content, re.DOTALL)

        if container_match:

            container_width = float(container_match.group(1))

            container_center = container_width / 2

            offset = abs(content_center - container_center)

            if offset > 40:

                off_center_count += 1



    if off_center_count > 0:

        issues.append("CRITICAL: %d 个容器内的子节点未居中（偏移 >40px）" % off_center_count)



    # 报告检查结果

    if not issues:

        print("✅ 技术路线图结构合格")

    else:

        print(f"ℹ 发现 {len(issues)} 个问题")



    return issues



def check_flow(content, filename):

    """检查求解流程图是否满足最低要求"""

    issues = []



    # 1. 必须有判断分支（菱形节点）

    has_diamond = bool(re.search(r'rhombus|shape=diamond', content))

    if not has_diamond:

        issues.append("CRITICAL: 没有判断分支（菱形节点）— 求解流程图必须至少有 1 个判断分支")



    # 2. 必须有是/否标签

    has_yes_no = bool(re.search(r'[是否]|Yes|No|yes|no', content))

    if has_diamond and not has_yes_no:

        issues.append("WARNING: 有判断分支但缺少是/否标签")



    # 3. 节点文字应简洁；不强制卡片式双行副标题。

    nodes_with_br = len(re.findall(r'&lt;br&gt;|<br>', content))

    total_nodes = len(re.findall(r'vertex="1"', content))

    if total_nodes > 3 and nodes_with_br < total_nodes * 0.3:

        issues.append("WARNING: 大部分节点只有单行文字 — 若步骤含关键参数，可补一行简短说明；不得为装饰强制双行")



    # 4. 颜色应克制，以灰阶和一个强调色为默认。

    fills = set(re.findall(r'fillColor=#([A-Fa-f0-9]{6})', content))

    strokes = set(re.findall(r'strokeColor=#([A-Fa-f0-9]{6})', content))

    fills.discard('FFFFFF')

    strokes.discard('999999')  # 排除灰色连线

    strokes.discard('000000')

    all_colors = fills | strokes

    if len(all_colors) > 5:

        issues.append("WARNING: 颜色种类过多（%d 种）— 默认使用灰阶和一个低饱和强调色" % len(all_colors))



    # 5. 不能有图内标题

    cell_values = " ".join(re.findall(r'<mxCell[^>]+value="([^"]*)"', content))

    has_title = bool(re.search(r'求解流程图|问题[一二三四五]求解流程图', cell_values))

    if has_title:

        issues.append("CRITICAL: 图内有标题文字 — 违反零容忍规则第 11 条")



    # 6. 检查是否只是一条直线（没有分叉）— 边数应该 > 节点数-1

    edges = len(re.findall(r'edge="1"', content))

    vertices = len(re.findall(r'vertex="1"', content))

    if vertices > 4 and edges <= vertices - 1:

        issues.append("WARNING: 流程图可能是纯线性链（无分叉/循环）— 建议增加并行分叉或循环反馈")



    # 7. 求解流程图绝对不能有「工具与方法」独立侧栏，副标题里也不能写工具/库名

    # 检测三种征兆：

    #   a) 节点 value 含 "工具与方法" 标题 → CRITICAL（一定是侧栏）

    #   b) 副标题/节点文本中出现 ≥2 个 Python 库 / 算法库名 → CRITICAL（写进副标题也不行）

    #   c) ≥4 个工具名密集出现 → CRITICAL（更明显的侧栏特征）

    has_tool_panel_title = re.search(r'工具与方法|工具/?\s*方法|tool.{0,5}method', content, re.IGNORECASE)

    if has_tool_panel_title:

        issues.append(

            "CRITICAL: 求解流程图含「工具与方法」侧栏 — 这是技术路线图专属，必须删除该节点。"

            "副标题也不要写工具/库名。"

        )

    else:

        # 工具/库名清单

        TOOL_PATTERN = (

            r'pandas|matplotlib|seaborn|scipy|SciPy|numpy|NumPy|sklearn|scikit-learn|'

            r'openpyxl|DEAP|Gurobi|PuLP|GeoPandas|OSMnx|TensorFlow|tensorflow|PyTorch|pytorch|'

            r'XGBoost|xgboost|LightGBM|lightgbm|statsmodels|networkx|NetworkX|'

            r'minimize|optimize|fit_transform'

        )

        tool_libs = re.findall(TOOL_PATTERN, content)

        if len(tool_libs) >= 4:

            issues.append(

                "CRITICAL: 求解流程图疑似含右侧工具/方法注释栏（检测到 %d 个工具/库名密集出现）— "

                "求解流程图禁止单独开侧栏列工具" % len(tool_libs)

            )

        elif len(tool_libs) >= 2:

            uniq = sorted(set(tool_libs))[:5]

            issues.append(

                "CRITICAL: 求解流程图节点文本含 %d 个工具/库名（%s）— "

                "求解流程图副标题应描述步骤本身做什么（如「最短路径目标函数」），"

                "禁止写「SciPy minimize」「scikit-learn KDE」等技术实现细节"

                % (len(tool_libs), ", ".join(uniq))

            )



    # 8. 节点间距不能太大（y 间距 > 100px 说明太稀疏）

    y_coords = [float(m.group(1)) for m in re.finditer(r'<mxGeometry[^>]*y="(\d+\.?\d*)"', content)]

    if len(y_coords) >= 3:

        y_sorted = sorted(set(y_coords))

        gaps = [y_sorted[i+1] - y_sorted[i] for i in range(len(y_sorted)-1)]

        avg_gap = sum(gaps) / len(gaps) if gaps else 0

        if avg_gap > 100:

            issues.append("WARNING: 节点间距过大（平均 %.0fpx）— 建议缩小到 60-80px，图会更紧凑" % avg_gap)



    # 9. 字号不能太大

    large_fonts = re.findall(r'fontSize=(\d+)', content)

    if large_fonts and max(int(f) for f in large_fonts) > 12:

        issues.append("WARNING: 字号过大（最大 %spx）— 流程图建议 9-11px" % max(large_fonts))



    # 10. html=1 检查

    cells_without_html1 = 0

    for m in re.finditer(r'<mxCell[^>]*value="[^"]*&lt;[^>]*style="([^"]*)"', content):

        if 'html=1' not in m.group(1):

            cells_without_html1 += 1

    if cells_without_html1 > 0:

        issues.append("CRITICAL: %d 个含 HTML 标签的节点缺少 html=1 — 导出后会显示原始 HTML 代码" % cells_without_html1)



    # 11. 检查长距离循环箭头是否可能穿过节点

    # 找所有 edge 的 source/target 坐标，如果 y 跨度 > 300px 且没有 waypoints，可能穿过中间节点

    long_edges = []

    for m in re.finditer(r'<mxCell[^>]*edge="1"[^>]*>', content):

        cell_str = m.group(0)

        # 检查是否有 curved=1 但没有 mxPoint waypoints

        if 'curved=1' in cell_str or 'curved' in cell_str:

            # 找对应的 mxGeometry 里的 sourcePoint/targetPoint

            cell_end = content.find('</mxCell>', m.end())

            if cell_end > 0:

                geo_block = content[m.start():cell_end]

                src_y = re.findall(r'sourcePoint[^/]*y="(\d+\.?\d*)"', geo_block)

                tgt_y = re.findall(r'targetPoint[^/]*y="(\d+\.?\d*)"', geo_block)

                if src_y and tgt_y:

                    span = abs(float(src_y[0]) - float(tgt_y[0]))

                    has_waypoints = 'Array' in geo_block or geo_block.count('mxPoint') > 2

                    if span > 300 and not has_waypoints:

                        long_edges.append(span)

    if long_edges:

        issues.append("CRITICAL: %d 条长距离循环箭头（跨度 >300px）没有 waypoints — 可能穿过中间节点。必须添加 waypoints 让箭头走图的左侧或右侧边缘绕行" % len(long_edges))



    # 12. 检查 shape=line（fork/join 横线）— CLI 导出可能不稳定

    line_shapes = len(re.findall(r'shape=line', content))

    if line_shapes > 0:

        issues.append("WARNING: %d 个 shape=line 元素（fork/join 横线）— CLI 导出可能渲染不稳定，建议用细长矩形（height=2, fillColor=#333）替代" % line_shapes)



    # 全部求解流程图同样执行直角矩形合同；其他 shape 保持不变。

    for cell in re.findall(r'<mxCell\b[^>]*vertex="1"[^>]*>', content):

        style_match = re.search(r'style="([^"]*)"', cell)

        if not style_match:

            continue

        style = style_match.group(1)

        is_plain_rectangle = "shape=" not in style or "swimlane" in style

        if is_plain_rectangle and "rounded=1" in style:

            issues.append("CRITICAL: 矩形节点使用 rounded=1 — 全部流程图矩形必须使用 rounded=0 直角")

    if 'gradientColor' in content:

        issues.append("WARNING: 检测到渐变填充 — 默认使用纯色或灰阶")

    if 'shadow=1' in content:

        issues.append("WARNING: 检测到阴影 — 学术流程图默认禁用装饰阴影")



    return issues



def main():

    if len(sys.argv) < 3:

        print("用法: python3 drawio_check.py <file.drawio> <roadmap|flow>")

        sys.exit(0)



    filepath = sys.argv[1]

    check_type = sys.argv[2]



    try:

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:

            content = f.read()

    except FileNotFoundError:

        print(f"文件不存在: {filepath}")

        sys.exit(0)



    if check_type == 'roadmap':

        issues = check_roadmap(content, filepath)

    elif check_type == 'flow':

        issues = check_flow(content, filepath)

    else:

        print(f"未知检查类型: {check_type}，支持 roadmap 或 flow")

        sys.exit(0)



    critical = sum(1 for i in issues if i.startswith('CRITICAL'))

    warning = sum(1 for i in issues if i.startswith('WARNING'))



    print(f"=== DrawIO 结构自检: {filepath} ({check_type}) ===")

    for issue in issues:

        print(f"  {issue}")



    if not issues:

        print(f"  ✅ 通过（{check_type} 结构检查无问题）")

    else:

        print(f"\n  {critical} CRITICAL, {warning} WARNING")

        if critical > 0:

            print(f"  ⛔ 必须修复所有 CRITICAL 后重新导出")



    sys.exit(1 if critical > 0 else 0)



if __name__ == '__main__':

    main()
