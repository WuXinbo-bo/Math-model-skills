#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""学术级图表工具库 — 统一风格，Meta-model-agent 自由调用。



使用方式：

    from 工具.plot_utils import setup_style, heatmap, forest_plot, trend_plot

    setup_style()  # 初始化学术风格

    heatmap(corr_matrix, output='图表/fig_heatmap.pdf')

"""

import os

import sys

import platform

import numpy as np



# 延迟导入 matplotlib，避免在没有 GUI 的环境报错

_plt = None

_sns = None



def _get_plt():

    global _plt

    if _plt is None:

        import matplotlib

        matplotlib.use('Agg')

        import matplotlib.pyplot as plt

        _plt = plt

    return _plt



def _get_sns():

    global _sns

    if _sns is None:

        try:

            import seaborn as sns

            _sns = sns

        except ImportError:

            _sns = None

    return _sns





# ============================================================

# 学术配色方案

# ============================================================

PALETTES = {

    # ★ Soft（默认推荐）— 柔和明亮，纯白背景，大面积半透明渐变填充

    # 柔蓝 + 珊瑚粉 + 薄荷绿 + 浅灰 + 淡紫 + 暖杏

    'soft': ['#5B9BD5', '#ED7D7D', '#7BC8A4', '#B0B0B0', '#9B8EC4', '#F4A261'],



    # Tableau 10 — 现代清新，区分度高，适合多组对比

    'tableau': ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948', '#B07AA1', '#FF9DA7', '#9C755F', '#BAB0AC'],



    # NPG / Nature — 鲜明对比，适合生物/化学/自然科学

    'npg': ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4', '#91D1C2', '#DC0000', '#7E6148', '#B09C85'],



    # NEJM — 柔和优雅，适合统计/医学类

    'nejm': ['#BC3C29', '#0072B5', '#E18727', '#20854E', '#7876B1', '#6F99AD', '#FFDC91', '#EE4C97'],



    # SciencePlots — 经典学术，适合 IEEE/ACM/工程类论文

    'science': ['#0C5DA5', '#00B945', '#FF9500', '#FF2C00', '#845B97', '#474747', '#9e9e9e'],



    # 色盲友好 (Wong 2011, Nature Methods) — 无障碍首选

    'colorblind': ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#F0E442', '#56B4E9', '#E69F00', '#000000'],



    # 顶刊风格 (Water Research / Nature 级别) — 低饱和莫兰迪色调，SCI 投稿首选

    'journal': ['#4A90B8', '#E8927C', '#7BC8A4', '#B8B8B8', '#F7D097', '#9B8EC4', '#8DBFA3', '#D4A0A0'],



    # ★ Elegant — 柔和通透，清新淡雅，适合统计建模/经管类论文

    # 淡蓝灰 + 暖橙 + 薄荷绿 + 淡紫蓝 + 玫瑰粉 + 暖杏 + 灰蓝 + 淡青

    'elegant': ['#7AAEC8', '#E8945A', '#7BC8A4', '#9B8EC4', '#E0A0A0', '#F0C05A', '#8FAEC0', '#A8C4D8'],



    # ★ Nature — Nature/高影响因子期刊专用，深蓝主色+绿红对比+中性灰

    # 适合 Nature、NeurIPS、ICLR 等顶刊/顶会投稿

    'nature': ['#0F4D92', '#3775BA', '#8BCF8B', '#B64342', '#767676', '#42949E', '#9A4D8E', '#FFD700'],

}



# 默认配色（Journal — 低饱和、克制、适合论文印刷与投影）

PALETTE = PALETTES['journal']

PALETTE_LIGHT = None  # 延迟初始化，在 _lighten 定义后赋值



COLORS = {

    'primary': '#4A90B8',     # 稳健蓝（主色调）

    'secondary': '#E8927C',   # 低饱和暖红（对比色）

    'accent': '#7BC8A4',      # 薄荷绿

    'gray': '#B8B8B8',

    'light': '#F5F7FA',

    'dark': '#2D2D2D',

    # 语义颜色

    'up': '#7BC8A4',          # 上升/正向 — 薄荷绿

    'down': '#E0A0A0',        # 下降/负向 — 柔玫瑰

    'neutral': '#B8B8B8',     # 中性

    'highlight': '#E8945A',   # 高亮/强调 — 暖橙

    'ref_line': '#AAAAAA',    # 参考线

    'grid': '#E0E0E0',        # 网格线（很淡）

    'text': '#4A4A4A',        # 标注文字

    'bg_box': '#F5F7FA',      # 标注框背景

    'bg_fill': '#C8DFF0',     # 边际/背景填充 — 淡天蓝

    'bg_fill2': '#F0C8C8',    # 第二背景填充 — 淡粉

}





def setup_style(palette='auto'):

    """初始化学术论文图表风格。调用一次即可。



    Args:

        palette: 配色方案名称。可选值：

            'auto' — 默认 Journal（低饱和、适合学术出版）

            'elegant' — 柔和通透的备选方案，适合展示型图表

            'journal' — 顶刊风格，低饱和莫兰迪色调，SCI 投稿首选

            'soft' — 柔蓝+珊瑚粉+薄荷绿+浅灰+淡紫+暖杏

            'tableau' — Tableau 10 现代清新，适合多组对比

            'npg' — Nature 鲜明对比，适合自然科学

            'nejm' — 柔和优雅，适合统计/医学

            'science' — SciencePlots 经典，适合工程类

            'colorblind' — 色盲友好（备选）

            或直接传一个颜色列表 ['#xxx', '#yyy', ...]

    """

    plt = _get_plt()

    import matplotlib

    sns = _get_sns()



    # 选择配色

    if isinstance(palette, list):

        colors = palette

    elif palette == 'auto' or palette is None:

        colors = PALETTES['journal']

    elif palette in PALETTES:

        colors = PALETTES[palette]

    else:

        colors = PALETTES['journal']



    # 更新全局 PALETTE 供其他函数使用

    global PALETTE, PALETTE_LIGHT, COLORS

    PALETTE = colors

    PALETTE_LIGHT = [_lighten(c, 0.4) for c in colors]

    COLORS['primary'] = colors[0]

    COLORS['secondary'] = colors[1] if len(colors) > 1 else colors[0]

    COLORS['accent'] = colors[2] if len(colors) > 2 else colors[0]

    # 语义颜色跟随配色方案

    COLORS['up'] = colors[2] if len(colors) > 2 else '#7BC8A4'       # 上升 = accent 色

    COLORS['down'] = colors[1] if len(colors) > 1 else '#ED7D7D'     # 下降 = secondary 色

    COLORS['highlight'] = colors[4] if len(colors) > 4 else colors[0]  # 高亮



    # 尝试使用 SciencePlots（如果未安装则自动安装）

    _has_scienceplots = False

    try:

        import scienceplots

        _has_scienceplots = True

    except ImportError:

        try:

            import subprocess

            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'SciencePlots', '-q'],

                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            import scienceplots

            _has_scienceplots = True

        except Exception:

            pass

    if _has_scienceplots:

        try:

            plt.style.use(['science', 'no-latex'])

        except OSError:

            _has_scienceplots = False



    # ★ SciencePlots 会设置很小的 figure.figsize 和紧凑的 subplot margins

    # 这里强制重置，防止用户手动指定的 figsize 被 subplot 参数压缩子图

    if _has_scienceplots:

        matplotlib.rcParams.update({

            'figure.figsize': (8, 5),           # 恢复合理默认尺寸

            'figure.subplot.left': 0.1,

            'figure.subplot.right': 0.95,

            'figure.subplot.top': 0.92,

            'figure.subplot.bottom': 0.12,

            'figure.subplot.hspace': 0.3,

            'figure.subplot.wspace': 0.3,

            'figure.constrained_layout.use': False,  # 避免与 tight_layout 冲突

        })



    # 用 seaborn 主题（如果可用且没有 SciencePlots）

    if sns and not _has_scienceplots:
        theme_rc = {
            'axes.edgecolor': '#333333',
            'axes.linewidth': 0.8,
        }
        if hasattr(sns, 'set_theme'):
            sns.set_theme(style='ticks', font_scale=1.0, rc=theme_rc)
        else:
            sns.set_style('ticks', rc=theme_rc)
            sns.set_context('notebook', font_scale=1.0)

    if sns:

        sns.set_palette(colors)



    # 中文字体（带可用性检测，避免小方框□）

    from matplotlib.font_manager import fontManager

    available_fonts = {f.name for f in fontManager.ttflist}



    if platform.system() == 'Windows':

        zh_candidates = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong']

    elif platform.system() == 'Darwin':

        zh_candidates = ['PingFang SC', 'Heiti SC', 'STHeiti', 'STSong', 'Arial Unicode MS']

    else:

        zh_candidates = ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei',

                         'Droid Sans Fallback', 'SimHei', 'AR PL UMing CN']



    zh_fonts = [f for f in zh_candidates if f in available_fonts]



    if not zh_fonts:

        # 没有任何中文字体——尝试加载内置字体文件

        _bundled_font = None

        for search_dir in ['工具', 'skills/shared-scripts', '../skills/shared-scripts']:

            font_path = os.path.join(search_dir, 'NotoSansSC-Regular.ttf')

            if os.path.isfile(font_path):

                _bundled_font = os.path.abspath(font_path)

                break

        if _bundled_font:

            from matplotlib.font_manager import FontProperties

            fontManager.addfont(_bundled_font)

            fp = FontProperties(fname=_bundled_font)

            zh_fonts = [fp.get_name()]

            print(f"Using bundled Chinese font: {_bundled_font}")

        elif platform.system() == 'Linux':

            # Linux 上尝试自动安装

            try:

                import subprocess

                subprocess.run(['apt-get', 'install', '-y', 'fonts-noto-cjk-extra'],

                               capture_output=True, timeout=30)

                fontManager.__init__()

                available_fonts = {f.name for f in fontManager.ttflist}

                zh_fonts = [f for f in zh_candidates if f in available_fonts]

            except Exception:

                pass

        if not zh_fonts:

            print("WARNING: No Chinese fonts found — Chinese text will show as □")

            print("  Fix: place NotoSansSC-Regular.ttf in skills/shared-scripts/")

            print("  Or install: Windows=SimHei, Linux=fonts-noto-cjk-extra, macOS=built-in")

            zh_fonts = ['DejaVu Sans']



    matplotlib.rcParams.update({

        'font.size': 11,

        'font.family': 'sans-serif',

        'font.sans-serif': zh_fonts + ['Arial', 'Helvetica', 'DejaVu Sans'],

        'axes.unicode_minus': False,

        'axes.labelsize': 12,

        'axes.titlesize': 13,

        'axes.linewidth': 0.8,

        'xtick.labelsize': 10,

        'ytick.labelsize': 10,

        'legend.fontsize': 10,

        'legend.frameon': False,

        'figure.dpi': 300,

        'savefig.dpi': 350,

        'savefig.pad_inches': 0.15,

        'axes.grid': False,

        'axes.spines.top': False,

        'axes.spines.right': False,

        'axes.facecolor': 'white',

        'figure.facecolor': 'white',

        'text.usetex': False,

        'mathtext.fontset': 'stix',

        'lines.linewidth': 1.8,

        'lines.markersize': 6,

        'patch.edgecolor': 'white',       # 饼图/柱状图块之间白色分隔线

        'patch.linewidth': 1.0,

    })



    # 设置颜色循环 — 这是关键，防止 matplotlib 用默认丑蓝色

    matplotlib.rcParams['axes.prop_cycle'] = matplotlib.cycler(color=colors)



    # ★ Nature 专属参数覆盖（字号更大、轴线更粗，匹配 Nature 出版标准）

    _palette_name = palette if isinstance(palette, str) else None

    if _palette_name in ('nature', 'npg'):

        matplotlib.rcParams.update({

            'font.size': 16,            # Nature 标准：正文 16pt

            'axes.labelsize': 16,

            'axes.titlesize': 18,

            'axes.linewidth': 2.5,      # Nature 标准：粗轴线

            'xtick.labelsize': 14,

            'ytick.labelsize': 14,

            'legend.fontsize': 13,

            'lines.linewidth': 2.5,

            'lines.markersize': 8,

            'xtick.major.width': 2.0,

            'ytick.major.width': 2.0,

            'xtick.major.size': 6,

            'ytick.major.size': 6,

        })



    # ★ Hook plt.savefig — 即使不用 save_fig()，也能自动防遮挡

    _hook_savefig(plt)





def _hook_savefig(plt):

    """Hook plt.savefig 和 Figure.savefig，在保存前强制修复子图尺寸和文字重叠。"""

    import matplotlib.figure



    if getattr(matplotlib.figure.Figure, '_overlap_hooked', False):

        return  # 已经 hook 过了



    _original_savefig = matplotlib.figure.Figure.savefig



    def _hooked_savefig(self, *args, **kwargs):

        # ★ 强制修复子图尺寸（最高优先级，检测到问题必须修复）

        try:

            _guard_subplot_size(self)

        except Exception:

            pass

        # 防遮挡修复

        try:

            _auto_fix_overlaps(self)

        except Exception:

            pass

        # ★ 防遮挡可能又破坏了布局，再强制检查一次

        try:

            _guard_subplot_size(self)

        except Exception:

            pass

        return _original_savefig(self, *args, **kwargs)



    matplotlib.figure.Figure.savefig = _hooked_savefig

    matplotlib.figure.Figure._overlap_hooked = True





def _lighten(hex_color, amount=0.4):

    """将颜色变浅（用于填充区域）。amount=0 不变，amount=1 变白。"""

    hex_color = hex_color.lstrip('#')

    r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    r = int(r + (255 - r) * amount)

    g = int(g + (255 - g) * amount)

    b = int(b + (255 - b) * amount)

    return f'#{r:02x}{g:02x}{b:02x}'





# 初始化 PALETTE_LIGHT（必须在 _lighten 定义之后）

PALETTE_LIGHT = [_lighten(c, 0.4) for c in PALETTES['journal']]





def _save(fig, output):

    """保存图表到指定路径。savefig hook 会自动检测并修复文字重叠。



    PNG 输出强制 350 DPI（与 docx_export PDF→PNG 兜底链路一致），防止 Word 嵌入时中文标签糊。

    PDF/SVG 矢量输出不受 DPI 影响。

    """

    # ★ 子图尺寸防护：检测子图是否被压缩得过小，如果是则修复

    _guard_subplot_size(fig)

    try:

        fig.tight_layout(pad=0.5)

    except Exception:

        pass

    # ★ tight_layout 后再检查一次，防止 tight_layout 把子图压小

    _guard_subplot_size(fig)

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else '.', exist_ok=True)

    _ext = output.split('.')[-1].lower()

    _save_kwargs = {'format': _ext, 'bbox_inches': 'tight', 'pad_inches': 0.15}

    if _ext in ('png', 'jpg', 'jpeg'):

        _save_kwargs['dpi'] = 350  # 防中文标签糊（与 PDF→PNG 兜底链路一致）

    fig.savefig(output, **_save_kwargs)

    _get_plt().close(fig)

    print(f'Saved: {output}')





def _guard_subplot_size(fig):

    """防护：检测子图是否被压缩得过小，如果是则强制修复布局。

    

    常见原因：SciencePlots 的 subplot margins 过紧、tight_layout(pad) 过大、

    ax.text(transAxes) 标签被算入空间分配。

    

    强制修复策略：检测到问题 → 重置 margins → 重新 tight_layout(pad=0.3) → 再验证。

    """

    axes = [ax for ax in fig.get_axes() if ax.get_visible() and not ax.get_label().startswith('_')]

    if not axes:

        return

    

    fig_w, fig_h = fig.get_size_inches()

    if fig_w <= 0 or fig_h <= 0:

        return

    

    def _is_too_small():

        """检测是否有子图过小。"""

        for ax in axes:

            pos = ax.get_position()

            ax_w_inch = pos.width * fig_w

            ax_h_inch = pos.height * fig_h

            # 子图面积小于 1.5 平方英寸 → 肯定有问题

            if ax_w_inch * ax_h_inch < 1.5:

                return True

            # 子图高度小于 1 英寸 → 太扁了

            if ax_h_inch < 1.0:

                return True

            # 子图宽度小于 2 英寸 → 太窄了

            if ax_w_inch < 2.0:

                return True

        return False

    

    if not _is_too_small():

        return

    

    # ★ 强制修复第一步：重置 subplot margins

    n_axes = len(axes)

    if n_axes == 1:

        fig.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12)

    else:

        fig.subplots_adjust(left=0.10, right=0.95, top=0.93, bottom=0.10,

                            hspace=0.3, wspace=0.3)

    

    # ★ 强制修复第二步：用小 pad 重新 tight_layout 覆盖之前的大 pad

    try:

        fig.tight_layout(pad=0.3)

    except Exception:

        pass

    

    # ★ 强制修复第三步：如果还是太小，直接放弃 tight_layout，手动设置合理布局

    if _is_too_small():

        if n_axes == 1:

            fig.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12)

        elif n_axes <= 4:

            fig.subplots_adjust(left=0.08, right=0.96, top=0.94, bottom=0.08,

                                hspace=0.25, wspace=0.25)

        else:

            fig.subplots_adjust(left=0.06, right=0.97, top=0.95, bottom=0.06,

                                hspace=0.2, wspace=0.2)





def _clamp_texts_to_axes(ax, texts, renderer):

    """将超出 axes 边界的文字/标注拉回 axes 内部。



    帕累托图、灵敏度图等场景中，annotate 的 xytext 用硬编码偏移，

    如果数据点靠近边缘，标注就会超出 axes 区域。

    此函数检测每个 Text 的 bounding box 是否超出 axes 范围，

    如果超出就把它拉回来（保留 4px 内边距）。

    """

    try:

        ax_bbox = ax.get_window_extent(renderer=renderer)

    except Exception:

        return



    pad = 4  # 像素内边距

    inv = ax.transData.inverted()



    for t in texts:

        try:

            t_bbox = t.get_window_extent(renderer=renderer)

        except Exception:

            continue



        dx_px, dy_px = 0.0, 0.0



        # 右边超出

        if t_bbox.x1 > ax_bbox.x1 - pad:

            dx_px = ax_bbox.x1 - pad - t_bbox.x1

        # 左边超出

        if t_bbox.x0 < ax_bbox.x0 + pad:

            dx_px = ax_bbox.x0 + pad - t_bbox.x0

        # 上边超出

        if t_bbox.y1 > ax_bbox.y1 - pad:

            dy_px = ax_bbox.y1 - pad - t_bbox.y1

        # 下边超出

        if t_bbox.y0 < ax_bbox.y0 + pad:

            dy_px = ax_bbox.y0 + pad - t_bbox.y0



        if abs(dx_px) < 0.5 and abs(dy_px) < 0.5:

            continue



        # 像素偏移 → 数据坐标偏移

        x, y = t.get_position()

        p0 = inv.transform((0, 0))

        p1 = inv.transform((dx_px, dy_px))

        t.set_position((x + p1[0] - p0[0], y + p1[1] - p0[1]))





def _auto_fix_overlaps(fig):

    """自动检测并修复 fig 中所有 axes 上的文字重叠。



    策略：

    1. 收集每个 ax 上所有可见的 Text 对象（排除轴标签、标题等）

    2. 计算每对 Text 的 bounding box，检测是否重叠

    3. 如果有重叠，调用 adjustText 自动推开

    4. 同时检测图例是否遮挡数据，如果遮挡则移动图例

    5. 检测 y 轴标签是否被相邻 axes（如分组色条）遮挡

    """

    try:

        renderer = fig.canvas.get_renderer()

    except Exception:

        # 某些后端没有 renderer，跳过检测

        return



    for ax in fig.get_axes():

        # 收集用户添加的 Text 对象（排除轴标签、标题、tick labels）

        user_texts = []

        skip_texts = set()

        # 标记要跳过的系统文本

        if ax.xaxis.label:

            skip_texts.add(id(ax.xaxis.label))

        if ax.yaxis.label:

            skip_texts.add(id(ax.yaxis.label))

        if ax.title:

            skip_texts.add(id(ax.title))

        for t in ax.get_xticklabels() + ax.get_yticklabels():

            skip_texts.add(id(t))



        for t in ax.texts:

            if id(t) in skip_texts:

                continue

            if not t.get_visible():

                continue

            txt = t.get_text().strip()

            if not txt:

                continue

            user_texts.append(t)



        # ★ 边界裁剪：检测标注/文字是否超出 axes 范围，拉回来

        # 即使只有 1 个标注也需要检测（帕累托图等场景）

        if user_texts:

            _clamp_texts_to_axes(ax, user_texts, renderer)



        if len(user_texts) < 2:

            continue



        # 检测是否有重叠

        has_overlap = False

        bboxes = []

        for t in user_texts:

            try:

                bb = t.get_window_extent(renderer=renderer)

                bboxes.append(bb)

            except Exception:

                bboxes.append(None)



        for i in range(len(bboxes)):

            if bboxes[i] is None:

                continue

            for j in range(i + 1, len(bboxes)):

                if bboxes[j] is None:

                    continue

                if bboxes[i].overlaps(bboxes[j]):

                    has_overlap = True

                    break

            if has_overlap:

                break



        if not has_overlap:

            continue



        # 有重叠 → 尝试用 adjustText 修复

        adjust_text = _ensure_adjustText()

        if adjust_text:

            try:

                adjust_text(user_texts, ax=ax,

                            force_points=0.3, force_text=0.5,

                            expand_points=(1.5, 1.5),

                            arrowprops=dict(arrowstyle='', lw=0))

            except Exception:

                # adjustText 失败，尝试简易修复

                _simple_spread(ax, user_texts, bboxes, renderer)

        else:

            _simple_spread(ax, user_texts, bboxes, renderer)



        # adjustText 推开后可能又超出边界，再裁剪一次

        _clamp_texts_to_axes(ax, user_texts, renderer)



        # 检测图例是否遮挡数据

        legend = ax.get_legend()

        if legend and legend.get_visible():

            try:

                best_loc = check_legend_overlap(ax)

                legend.set_loc(best_loc)  # matplotlib 3.x

            except (AttributeError, Exception):

                try:

                    legend._loc = {

                        'upper right': 1, 'upper left': 2,

                        'lower left': 3, 'lower right': 4,

                        'center right': 7, 'center left': 6,

                    }.get(check_legend_overlap(ax), 1)

                except Exception:

                    pass



        # ★ 检测 user texts 是否和 tick labels 重叠（如标注和 X 轴刻度重叠）

        tick_bboxes = []

        for t in ax.get_xticklabels() + ax.get_yticklabels():

            if t.get_visible() and t.get_text().strip():

                try:

                    tick_bboxes.append(t.get_window_extent(renderer=renderer))

                except Exception:

                    pass

        for i, ut in enumerate(user_texts):

            if bboxes[i] is None:

                continue

            for tb in tick_bboxes:

                if bboxes[i].overlaps(tb):

                    # user text 和 tick label 重叠 → 把 user text 往上推

                    overlap_y = tb.y1 - bboxes[i].y0 + 4

                    inv = ax.transData.inverted()

                    p0 = inv.transform((0, 0))

                    p1 = inv.transform((0, overlap_y))

                    dy = p1[1] - p0[1]

                    x, y = ut.get_position()

                    ut.set_position((x, y + abs(dy)))

                    try:

                        bboxes[i] = ut.get_window_extent(renderer=renderer)

                    except Exception:

                        pass

                    break



    # ★ 也处理 annotate 创建的标注（ax.texts 不包含 annotate 的文本部分）

    for ax in fig.get_axes():

        annots = [child for child in ax.get_children()

                  if hasattr(child, 'xyann') or (hasattr(child, 'anncoords') and hasattr(child, 'get_text'))]

        if not annots:

            # annotate 创建的对象在 ax.texts 中（matplotlib 3.x），已经处理过

            # 但也检查 ax.patches 中的 FancyArrowPatch

            pass



    # ★ 检测 y 轴标签是否被相邻 axes（如分组色条）遮挡

    _fix_ylabel_overlap(fig, renderer)





def _fix_ylabel_overlap(fig, renderer):

    """检测并修复 y 轴标签被相邻 axes 遮挡的问题（如聚类热力图的左侧色条）。"""

    all_axes = fig.get_axes()

    if len(all_axes) < 2:

        return

    for ax in all_axes:

        ytick_labels = ax.get_yticklabels()

        if not ytick_labels:

            continue

        # 获取 y 轴标签的最左边界（display coords）

        leftmost = None

        for lbl in ytick_labels:

            if not lbl.get_visible() or not lbl.get_text().strip():

                continue

            try:

                bb = lbl.get_window_extent(renderer=renderer)

                if leftmost is None or bb.x0 < leftmost:

                    leftmost = bb.x0

            except Exception:

                continue

        if leftmost is None:

            continue

        # 检查是否有其他 axes 的区域覆盖了这些标签

        ax_bbox_disp = ax.get_window_extent(renderer=renderer)

        for other_ax in all_axes:

            if other_ax is ax:

                continue

            other_bbox = other_ax.get_window_extent(renderer=renderer)

            # 如果其他 axes 在当前 axes 左侧且与标签区域重叠

            if other_bbox.x1 > leftmost and other_bbox.x0 < ax_bbox_disp.x0:

                # 计算需要左移的量（figure fraction）

                fig_width = fig.get_window_extent(renderer=renderer).width

                overlap_px = other_bbox.x1 - leftmost + 8  # 8px 额外间距

                shift = overlap_px / fig_width

                # 把遮挡的 axes 往左推

                pos = other_ax.get_position()

                new_x0 = max(0.01, pos.x0 - shift)

                new_width = pos.width - (pos.x0 - new_x0) if new_x0 < pos.x0 else pos.width

                other_ax.set_position([new_x0, pos.y0, max(0.01, new_width), pos.height])





def _simple_spread(ax, texts, bboxes, renderer):

    """简易重叠修复：把重叠的文本沿 y 方向推开。"""

    if not texts or not bboxes:

        return



    # 按 y 坐标排序

    indexed = [(i, t) for i, t in enumerate(texts) if bboxes[i] is not None]

    indexed.sort(key=lambda x: x[1].get_position()[1])



    for k in range(1, len(indexed)):

        i_curr = indexed[k][0]

        i_prev = indexed[k - 1][0]

        bb_curr = bboxes[i_curr]

        bb_prev = bboxes[i_prev]

        if bb_curr is None or bb_prev is None:

            continue



        if bb_prev.overlaps(bb_curr):

            # 计算需要的最小偏移（像素）

            overlap_y = bb_prev.y1 - bb_curr.y0 + 2  # 2px padding

            # 转换为数据坐标

            inv = ax.transData.inverted()

            p0 = inv.transform((0, 0))

            p1 = inv.transform((0, overlap_y))

            dy = p1[1] - p0[1]

            # 把当前文本往上推

            x, y = texts[i_curr].get_position()

            texts[i_curr].set_position((x, y + dy))

            # 更新 bbox

            try:

                bboxes[i_curr] = texts[i_curr].get_window_extent(renderer=renderer)

            except Exception:

                pass



# 公开别名，供外部脚本调用

save_fig = _save





# ============================================================

# 标签防遮挡工具

# ============================================================



def _ensure_adjustText():

    """确保 adjustText 库可用，不可用时自动安装。"""

    try:

        from adjustText import adjust_text

        return adjust_text

    except ImportError:

        try:

            import subprocess

            subprocess.check_call(

                [sys.executable, '-m', 'pip', 'install', 'adjustText', '-q'],

                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            from adjustText import adjust_text

            return adjust_text

        except Exception:

            return None





def smart_labels(ax, xs, ys, texts, colors=None, fontsize=9, fontweight='normal',

                 offset=(8, 0), fmt=None, ha='left', va='center',

                 force_points=0.3, force_text=0.5, avoid_self=True,

                 bbox=None, arrowprops=None, max_labels=50):

    """智能标签标注 — 自动检测并推开重叠标签。



    优先使用 adjustText 库做物理模拟推开；如果不可用，退化为

    基于数据间距的简易偏移策略。



    Args:

        ax: matplotlib Axes 对象

        xs: 标签锚点 x 坐标列表

        ys: 标签锚点 y 坐标列表

        texts: 标签文本列表

        colors: 每个标签的颜色（None 则统一用深灰）

        fontsize: 字号

        fontweight: 字重（'bold' / 'normal'）

        offset: (dx, dy) 像素偏移，adjustText 模式下作为初始偏移

        fmt: 格式化字符串，如 '{:.3f}'，传入时 texts 应为数值列表

        ha/va: 水平/垂直对齐

        force_points: adjustText 的点斥力

        force_text: adjustText 的文本斥力

        avoid_self: 是否避免标签之间重叠

        bbox: 标签背景框样式 dict（如 dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7)）

        arrowprops: 箭头样式 dict（如 dict(arrowstyle='->', color='gray', lw=0.5)）

        max_labels: 超过此数量时跳过标注（数据太密集标注无意义）



    Returns:

        list of Text 对象



    用法示例::



        # 棒棒糖图标注

        smart_labels(ax, scores, y_pos, [f'{s:.3f}' for s in scores],

                     colors=[PALETTE[0]]*len(scores), fontweight='bold')



        # 散点图标注（带箭头）

        smart_labels(ax, x_outliers, y_outliers, gene_names,

                     arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))

    """

    if len(xs) > max_labels:

        return []



    plt = _get_plt()

    text_objs = []



    # 格式化文本

    if fmt is not None:

        display_texts = [fmt.format(t) for t in texts]

    else:

        display_texts = [str(t) for t in texts]



    default_color = '#333333'



    # 创建 Text 对象

    for i, (x, y, txt) in enumerate(zip(xs, ys, display_texts)):

        c = colors[i] if colors and i < len(colors) else default_color

        fw = fontweight if isinstance(fontweight, str) else (

            fontweight[i] if i < len(fontweight) else 'normal')

        t = ax.text(x, y, txt, fontsize=fontsize, fontweight=fw,

                    color=c, ha=ha, va=va,

                    bbox=bbox if bbox else None)

        text_objs.append(t)



    # 尝试用 adjustText 自动推开

    adjust_text = _ensure_adjustText()

    if adjust_text and avoid_self and len(text_objs) > 1:

        try:

            arrow_kw = arrowprops or dict(arrowstyle='-', color='#cccccc', lw=0.3)

            adjust_text(text_objs, ax=ax,

                        force_points=force_points,

                        force_text=force_text,

                        expand_points=(1.5, 1.5),

                        arrowprops=arrow_kw)

        except Exception:

            # adjustText 失败时退化为手动偏移

            _fallback_offset(ax, text_objs, xs, ys, offset)

    else:

        # 没有 adjustText，用简易偏移

        _fallback_offset(ax, text_objs, xs, ys, offset)



    return text_objs





def _fallback_offset(ax, text_objs, xs, ys, offset):

    """简易防遮挡：根据数据间距计算偏移方向，密集区域交替上下偏移。"""

    if not text_objs:

        return



    fig = ax.get_figure()

    renderer = fig.canvas.get_renderer() if hasattr(fig.canvas, 'get_renderer') else None



    # 获取数据坐标范围

    xlim = ax.get_xlim()

    ylim = ax.get_ylim()

    x_range = xlim[1] - xlim[0] if xlim[1] != xlim[0] else 1

    y_range = ylim[1] - ylim[0] if ylim[1] != ylim[0] else 1



    # 估算标签高度（数据坐标）

    label_height = y_range * 0.035  # 约 3.5% 的 y 轴范围



    # 按 y 坐标排序，检测相邻标签是否过近

    indices = list(range(len(text_objs)))

    indices.sort(key=lambda i: ys[i])



    for k in range(len(indices)):

        i = indices[k]

        # 基础偏移

        dx_data = offset[0] * x_range / 500  # 像素偏移转数据坐标（近似）

        dy_data = offset[1] * y_range / 500



        # 检查与前一个标签是否过近

        if k > 0:

            j = indices[k - 1]

            gap = abs(ys[i] - ys[j])

            if gap < label_height * 1.5:

                # 交替上下偏移

                direction = 1 if k % 2 == 0 else -1

                dy_data += direction * label_height * 0.8



        text_objs[i].set_position((xs[i] + dx_data, ys[i] + dy_data))





def check_legend_overlap(ax, preferred_locs=None):

    """自动选择不遮挡数据的图例位置。



    检测数据分布的稀疏区域，把图例放在最空的角落。



    Args:

        ax: matplotlib Axes 对象

        preferred_locs: 优先尝试的位置列表，默认 ['upper right', 'upper left',

                        'lower right', 'lower left', 'center right']



    Returns:

        最佳位置字符串（可直接传给 ax.legend(loc=...)）

    """

    if preferred_locs is None:

        preferred_locs = ['upper right', 'upper left', 'lower right',

                          'lower left', 'center right', 'center left']



    # 收集所有数据点

    all_x, all_y = [], []

    for line in ax.get_lines():

        xd, yd = line.get_xdata(), line.get_ydata()

        if len(xd) > 0:

            all_x.extend(xd)

            all_y.extend(yd)

    for coll in ax.collections:

        offsets = coll.get_offsets()

        if len(offsets) > 0:

            all_x.extend(offsets[:, 0])

            all_y.extend(offsets[:, 1])



    if not all_x:

        return preferred_locs[0]



    xlim = ax.get_xlim()

    ylim = ax.get_ylim()

    xmid = (xlim[0] + xlim[1]) / 2

    ymid = (ylim[0] + ylim[1]) / 2



    # 统计每个象限的数据点密度

    quadrant_counts = {

        'upper right': 0, 'upper left': 0,

        'lower right': 0, 'lower left': 0,

        'center right': 0, 'center left': 0,

    }

    for x, y in zip(all_x, all_y):

        if y >= ymid:

            if x >= xmid:

                quadrant_counts['upper right'] += 1

            else:

                quadrant_counts['upper left'] += 1

        else:

            if x >= xmid:

                quadrant_counts['lower right'] += 1

            else:

                quadrant_counts['lower left'] += 1

        # center 区域

        if abs(y - ymid) < (ylim[1] - ylim[0]) * 0.25:

            if x >= xmid:

                quadrant_counts['center right'] += 1

            else:

                quadrant_counts['center left'] += 1



    # 在 preferred_locs 中选密度最低的

    best_loc = min(preferred_locs, key=lambda loc: quadrant_counts.get(loc, 999))

    return best_loc





def auto_legend(ax, **kwargs):

    """智能图例：自动选择不遮挡数据的位置。



    用法：用 auto_legend(ax) 替代 ax.legend()



    Args:

        ax: matplotlib Axes 对象

        **kwargs: 传给 ax.legend() 的其他参数

    """

    loc = check_legend_overlap(ax)

    defaults = dict(frameon=True, edgecolor='#DDD', fontsize=9, fancybox=True, shadow=False)

    defaults.update(kwargs)

    defaults['loc'] = loc

    return ax.legend(**defaults)





# ============================================================

# 图表函数

# ============================================================



def heatmap(data, labels=None, output='图表/fig_heatmap.pdf', title=None,

            annot=True, fmt='.2f', cmap='coolwarm', figsize=(8, 6)):

    """相关性热力图（带数值标注）。

    

    Args:

        data: 2D array 或 DataFrame（相关系数矩阵）

        labels: 行列标签

        output: 输出路径

        annot: 是否标注数值

        fmt: 数值格式

    """

    plt = _get_plt()

    sns = _get_sns()

    setup_style()

    fig, ax = plt.subplots(1, 1, figsize=figsize)



    if sns:

        mask = np.triu(np.ones_like(data, dtype=bool), k=1)

        hm = sns.heatmap(data, mask=mask, annot=annot, fmt=fmt, cmap=cmap,

                    center=0, square=True, linewidths=0.5,

                    xticklabels=labels, yticklabels=labels, ax=ax,

                    cbar_kws={'shrink': 0.8})

        # 文字颜色自适应：深色格子用白字，浅色格子用黑字

        if annot and hasattr(hm, 'texts'):

            from matplotlib.colors import Normalize

            flat = np.array(data).flatten()

            flat = flat[~np.isnan(flat)]

            if len(flat) > 0:

                norm = Normalize(vmin=flat.min(), vmax=flat.max())

                for text in hm.texts:

                    try:

                        val = float(text.get_text())

                        text.set_color('white' if norm(abs(val)) > 0.6 else 'black')

                    except (ValueError, TypeError):

                        pass

    else:

        im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=-1, vmax=1)

        fig.colorbar(im, ax=ax, shrink=0.8)

        if annot:

            for i in range(data.shape[0]):

                for j in range(data.shape[1]):

                    if j <= i:

                        val = data[i, j]

                        color = 'white' if abs(val) > 0.6 else 'black'

                        ax.text(j, i, f'{val:{fmt[1:]}}', ha='center', va='center', fontsize=8, color=color)

        if labels is not None:

            ax.set_xticks(range(len(labels)))

            ax.set_xticklabels(labels, rotation=45, ha='right')

            ax.set_yticks(range(len(labels)))

            ax.set_yticklabels(labels)



    _save(fig, output)





def forest_plot(coefs, ci_lower, ci_upper, labels, output='图表/fig_forest.pdf',

                figsize=(6, None), xlabel='Coefficient'):

    """回归系数森林图（带置信区间）。

    

    Args:

        coefs: 系数数组

        ci_lower: 置信区间下界

        ci_upper: 置信区间上界

        labels: 变量名列表

        output: 输出路径

    """

    plt = _get_plt()

    setup_style()

    n = len(coefs)

    if figsize[1] is None:

        figsize = (figsize[0], max(3, n * 0.4 + 1))

    fig, ax = plt.subplots(1, 1, figsize=figsize)



    y_pos = np.arange(n)

    xerr = [np.array(coefs) - np.array(ci_lower), np.array(ci_upper) - np.array(coefs)]



    ax.errorbar(coefs, y_pos, xerr=xerr, fmt='o', color=COLORS['primary'],

                ecolor=COLORS['gray'], elinewidth=1.5, capsize=3, markersize=5)

    ax.axvline(x=0, color=COLORS['accent'], linestyle='--', linewidth=0.8, alpha=0.7)

    ax.set_yticks(y_pos)

    ax.set_yticklabels(labels)

    ax.set_xlabel(xlabel)

    ax.invert_yaxis()



    _save(fig, output)





def trend_plot(x, y, output='图表/fig_trend.pdf', ci=None,

               xlabel='', ylabel='', label=None, figsize=(7, 4)):

    """时间趋势图（可选置信带）。

    

    Args:

        x: x 轴数据

        y: y 轴数据

        ci: (lower, upper) 置信区间元组，可选

        output: 输出路径

    """

    plt = _get_plt()

    setup_style()

    fig, ax = plt.subplots(1, 1, figsize=figsize)



    ax.plot(x, y, color=COLORS['primary'], linewidth=1.5, label=label)

    if ci is not None:

        ax.fill_between(x, ci[0], ci[1], alpha=0.15, color=COLORS['secondary'])

    ax.set_xlabel(xlabel)

    ax.set_ylabel(ylabel)

    if label:

        ax.legend()



    _save(fig, output)





def bar_compare(categories, values_dict, output='图表/fig_bar.pdf',

                ylabel='', figsize=(7, 4), show_values=True):

    """分组柱状图（带误差棒，多组对比）。

    

    Args:

        categories: 类别列表 ['A', 'B', 'C']

        values_dict: {'方法1': [v1, v2, v3], '方法2': [v1, v2, v3]}

                     或 {'方法1': {'values': [...], 'errors': [...]}}

        output: 输出路径

    """

    plt = _get_plt()

    setup_style()

    fig, ax = plt.subplots(1, 1, figsize=figsize)



    n_groups = len(categories)

    n_bars = len(values_dict)

    bar_width = 0.8 / n_bars

    x = np.arange(n_groups)



    for i, (name, data) in enumerate(values_dict.items()):

        if isinstance(data, dict):

            vals = data['values']

            errs = data.get('errors', None)

        else:

            vals = data

            errs = None

        offset = (i - n_bars / 2 + 0.5) * bar_width

        bars = ax.bar(x + offset, vals, bar_width, label=name,

                       color=PALETTE[i % len(PALETTE)], yerr=errs,

                       capsize=3, error_kw={'linewidth': 0.8})

        if show_values:

            for bar, val in zip(bars, vals):

                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01 * max(vals),

                        f'{val:.2f}', ha='center', va='bottom', fontsize=7)



    ax.set_xticks(x)

    ax.set_xticklabels(categories)

    ax.set_ylabel(ylabel)

    ax.legend()



    _save(fig, output)





def distribution_plot(data, output='图表/fig_dist.pdf', xlabel='', bins=30, figsize=(6, 4)):

    """核密度 + 直方图。"""

    plt = _get_plt()

    sns = _get_sns()

    setup_style()

    fig, ax = plt.subplots(1, 1, figsize=figsize)



    if sns:

        sns.histplot(data, bins=bins, kde=True, color=COLORS['secondary'], ax=ax,

                     edgecolor='white', linewidth=0.5)

    else:

        ax.hist(data, bins=bins, density=True, color=COLORS['secondary'],

                edgecolor='white', linewidth=0.5, alpha=0.7)

    ax.set_xlabel(xlabel)

    ax.set_ylabel('Density')



    _save(fig, output)





def scatter_plot(x, y, output='图表/fig_scatter.pdf', xlabel='', ylabel='',

                 hue=None, fit_line=True, figsize=(6, 5)):

    """散点图（可选回归线）。"""

    plt = _get_plt()

    setup_style()

    fig, ax = plt.subplots(1, 1, figsize=figsize)



    if hue is not None:

        for i, (name, mask) in enumerate(hue.items()):

            ax.scatter(np.array(x)[mask], np.array(y)[mask], s=20, alpha=0.6,

                       color=PALETTE[i % len(PALETTE)], label=name)

        ax.legend()

    else:

        ax.scatter(x, y, s=20, alpha=0.6, color=COLORS['secondary'])



    if fit_line:

        z = np.polyfit(x, y, 1)

        p = np.poly1d(z)

        x_line = np.linspace(min(x), max(x), 100)

        ax.plot(x_line, p(x_line), color=COLORS['accent'], linewidth=1, linestyle='--')



    ax.set_xlabel(xlabel)

    ax.set_ylabel(ylabel)



    _save(fig, output)





def residual_diagnostic(y_true, y_pred, output='图表/fig_residual.pdf', figsize=(10, 8)):

    """残差诊断四图（QQ图、残差散点、残差直方图、拟合值vs残差）。"""

    plt = _get_plt()

    setup_style()

    fig, axes = plt.subplots(2, 2, figsize=figsize)

    residuals = np.array(y_true) - np.array(y_pred)

    std_resid = (residuals - residuals.mean()) / residuals.std()



    # 1. 残差 vs 拟合值

    ax = axes[0, 0]

    ax.scatter(y_pred, residuals, s=15, alpha=0.5, color=COLORS['secondary'])

    ax.axhline(y=0, color=COLORS['accent'], linestyle='--', linewidth=0.8)

    ax.set_xlabel('Fitted Values')

    ax.set_ylabel('Residuals')



    # 2. QQ 图

    ax = axes[0, 1]

    sorted_resid = np.sort(std_resid)

    n = len(sorted_resid)

    theoretical = np.array([_norm_ppf((i + 0.5) / n) for i in range(n)])

    ax.scatter(theoretical, sorted_resid, s=15, alpha=0.5, color=COLORS['secondary'])

    lim = max(abs(theoretical.min()), abs(theoretical.max())) * 1.1

    ax.plot([-lim, lim], [-lim, lim], color=COLORS['accent'], linestyle='--', linewidth=0.8)

    ax.set_xlabel('Theoretical Quantiles')

    ax.set_ylabel('Standardized Residuals')



    # 3. 残差直方图

    ax = axes[1, 0]

    ax.hist(residuals, bins=25, color=COLORS['secondary'], edgecolor='white', linewidth=0.5, density=True)

    ax.set_xlabel('Residuals')

    ax.set_ylabel('Density')



    # 4. Scale-Location

    ax = axes[1, 1]

    ax.scatter(y_pred, np.sqrt(np.abs(std_resid)), s=15, alpha=0.5, color=COLORS['secondary'])

    ax.set_xlabel('Fitted Values')

    ax.set_ylabel('sqrt(|Standardized Residuals|)')



    fig.tight_layout()

    _save(fig, output)





def _norm_ppf(p):

    """简易正态分位数函数（避免依赖 scipy）。"""

    # Abramowitz and Stegun approximation

    if p <= 0:

        return -4.0

    if p >= 1:

        return 4.0

    if p == 0.5:

        return 0.0

    if p > 0.5:

        return -_norm_ppf(1 - p)

    t = np.sqrt(-2 * np.log(p))

    c0, c1, c2 = 2.515517, 0.802853, 0.010328

    d1, d2, d3 = 1.432788, 0.189269, 0.001308

    return -(t - (c0 + c1 * t + c2 * t ** 2) / (1 + d1 * t + d2 * t ** 2 + d3 * t ** 3))





def multi_line_plot(x, ys, labels, output='图表/fig_multi_line.pdf',

                    xlabel='', ylabel='', figsize=(7, 4)):

    """多条线对比图（训练曲线、消融实验等）。



    Args:

        x: x 轴数据

        ys: list of y 数据序列

        labels: 每条线的标签

        output: 输出路径

    """

    plt = _get_plt()

    setup_style()

    fig, ax = plt.subplots(1, 1, figsize=figsize)



    for i, (y, label) in enumerate(zip(ys, labels)):

        ax.plot(x, y, color=PALETTE[i % len(PALETTE)], linewidth=1.5, label=label)



    ax.set_xlabel(xlabel)

    ax.set_ylabel(ylabel)

    ax.legend()

    _save(fig, output)





def box_plot(data_dict, output='图表/fig_box.pdf', ylabel='', figsize=(7, 4)):

    """箱线图（分布对比）。



    Args:

        data_dict: {'方法A': [values], '方法B': [values]}

        output: 输出路径

    """

    plt = _get_plt()

    setup_style()

    fig, ax = plt.subplots(1, 1, figsize=figsize)



    labels = list(data_dict.keys())

    data = list(data_dict.values())



    bp = ax.boxplot(data, labels=labels, patch_artist=True, widths=0.5,

                    medianprops={'color': COLORS['dark'], 'linewidth': 1.5})

    for i, patch in enumerate(bp['boxes']):

        patch.set_facecolor(PALETTE_LIGHT[i % len(PALETTE_LIGHT)])

        patch.set_edgecolor(PALETTE[i % len(PALETTE)])



    ax.set_ylabel(ylabel)

    _save(fig, output)





def radar_plot(categories, values_dict, output='图表/fig_radar.pdf', figsize=(6, 6)):

    """雷达图（多维度对比）。



    Args:

        categories: 维度名列表 ['Accuracy', 'Speed', 'Memory', ...]

        values_dict: {'方法A': [v1, v2, ...], '方法B': [v1, v2, ...]}

        output: 输出路径

    """

    plt = _get_plt()

    setup_style()

    fig, ax = plt.subplots(1, 1, figsize=figsize, subplot_kw=dict(polar=True))



    n = len(categories)

    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()

    angles += angles[:1]  # 闭合



    for i, (name, vals) in enumerate(values_dict.items()):

        values = list(vals) + [vals[0]]  # 闭合

        ax.plot(angles, values, 'o-', linewidth=1.5, color=PALETTE[i % len(PALETTE)], label=name)

        ax.fill(angles, values, alpha=0.1, color=PALETTE[i % len(PALETTE)])



    ax.set_xticks(angles[:-1])

    ax.set_xticklabels(categories)

    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

    _save(fig, output)





def subplot_grid(plot_funcs, nrows, ncols, output='图表/fig_grid.pdf',

                 figsize=None, titles=None):

    """多面板子图网格。



    Args:

        plot_funcs: list of callables, 每个接受 (ax,) 参数

        nrows, ncols: 网格尺寸

        output: 输出路径

        titles: 每个子图的标题列表（可选）

    """

    plt = _get_plt()

    setup_style()

    if figsize is None:

        figsize = (4 * ncols, 3.5 * nrows)

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)

    if nrows == 1 and ncols == 1:

        axes = np.array([axes])

    axes_flat = axes.flatten()



    for i, func in enumerate(plot_funcs):

        if i < len(axes_flat):

            func(axes_flat[i])

            if titles and i < len(titles):

                axes_flat[i].set_title(titles[i], fontsize=10)



    # 隐藏多余的子图

    for j in range(len(plot_funcs), len(axes_flat)):

        axes_flat[j].set_visible(False)



    fig.tight_layout()

    _save(fig, output)

