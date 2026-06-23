import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json
from pathlib import Path
import numpy as np

# ============================================================
# FIXED FONT: SimHei first, Arial fallback for Latin
# ============================================================
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial', 'DejaVu Sans']
plt.rcParams['svg.fonttype'] = 'none'
plt.rcParams['axes.unicode_minus'] = False

plt.rcParams.update({
    'axes.spines.right': False,
    'axes.spines.top': False,
    'legend.frameon': False,
    'axes.linewidth': 0.8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'font.size': 9,
    'axes.titlesize': 11,
    'axes.labelsize': 9,
    'legend.fontsize': 8,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'figure.facecolor': 'white',
    'savefig.facecolor': 'white',
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.12,
})

# ============================================================
# CONTEST LANGUAGE RULE (v5.3.3):
# CUMCM/51MCM -> ALL labels, titles, legends in CHINESE
# MCM/ICM/APMCM -> ALL labels, titles, legends in ENGLISH
# NO bilingual figures. NO default-English for domestic contests.
# ============================================================

# Nature palette
PALETTE = {
    "blue_main":      "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_3":        "#8BCF8B",
    "red_strong":     "#B64342",
    "neutral_light":  "#CFCECE",
    "neutral_mid":    "#767676",
    "neutral_dark":   "#4D4D4D",
    "neutral_black":  "#272727",
    "teal":           "#42949E",
    "violet":         "#9A4D8E",
}

EQUIP_COLORS = {
    '自动化输送臂': PALETTE['blue_secondary'],
    '工业清洗机':    PALETTE['teal'],
    '精密灌装机':    PALETTE['neutral_mid'],
    '自动传感多功能机': PALETTE['red_strong'],
    '高速抛光机':    PALETTE['violet'],
}

WS_COLORS = {
    'A': PALETTE['blue_main'],
    'B': PALETTE['teal'],
    'C': PALETTE['red_strong'],
    'D': PALETTE['violet'],
    'E': PALETTE['neutral_mid'],
}

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace
_WS = resolve_workspace()
OUTPUT_DIR = _WS / 'latex' / 'images'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load results - FIXED: handle missing fields
results = {}
for q in [1,2,3,4]:
    f = _WS / 'output' / f'q{q}_result.json'
    if f.exists():
        with open(f, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
            results[q] = data

print('='*60)
print('  FIGURE REGENERATION (Font fixed + Blank figures fixed)')
print('  Font: SimHei first, Arial fallback')
print('='*60)

# Fig 1: Workshop flow
fig, ax = plt.subplots(figsize=(12, 4.5))
workshops_data = [
    ('A车间', ['A1: 缺陷填补 (1.5h)', 'A2: 表面整平 (5.0h)', 'A3: 强度检测 (5.0h)'], 41400),
    ('B车间', ['B1: 表面清理 (1.2h)', 'B2: 垫层构筑 (7.5h)', 'B3: 表面密封 (1.0h)', 'B4: 表面整平 (3.6h)'], 47983),
    ('C车间', ['C1: 旧涂层剥离 (2.9h)', 'C2: 基底填充 (2.1h)', '(C3-C5)x3 密封+研磨+检测 (29.4h)'], 123614),
    ('D车间', ['D1: 碎屑清理 (2.4h)', 'D2: 基底固化 (4.0h)', 'D3: 表面密封 (1.3h)', 'D4: 表面整平 (12.5h)', 'D5: 承载检测 (5.0h)', 'D6: 边缘修整 (7.0h)'], 115869),
    ('E车间', ['E1: 基础处理 (4.0h)', 'E2: 表面密封 (1.7h)', 'E3: 稳定性检测 (6.0h)'], 42172),
]
y_positions = [4.5, 3.5, 2.5, 1.5, 0.5]
for (name, procs, total), y in zip(workshops_data, y_positions):
    color = WS_COLORS[name[0]]
    ax.text(-0.5, y, name, ha='right', va='center', fontsize=9, fontweight='bold', color=PALETTE['neutral_black'])
    x_start = 0
    for j, proc in enumerate(procs):
        ax.text(x_start + 0.05, y, proc, va='center', fontsize=5.8,
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.78, edgecolor='white', linewidth=0.6))
        if j < len(procs) - 1:
            ax.annotate('', xy=(x_start + 1.55, y), xytext=(x_start + 0.18, y),
                        arrowprops=dict(arrowstyle='->', lw=1.2, color=PALETTE['neutral_mid']))
        x_start += 1.6
    ax.text(x_start + 0.3, y, f'合计 {total/3600:.1f}h', fontsize=8, color=PALETTE['red_strong'], fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=PALETTE['red_strong'], linewidth=0.6))
ax.set_xlim(-2.5, 20)
ax.set_ylim(-0.3, 5.3)
ax.axis('off')
ax.set_title('图1  各车间工序流程图', fontsize=12, fontweight='bold', pad=14, color=PALETTE['neutral_black'])
plt.tight_layout(pad=1.5)
plt.savefig(OUTPUT_DIR / 'fig1_workshop_flow.png', dpi=300)
plt.close()
print('  Fig 1 done')

# Gantt function
def draw_gantt(schedule, title, filename, top_n=25):
    devices_seen = []
    for r in schedule:
        if r['device_id'] not in devices_seen:
            devices_seen.append(r['device_id'])
    devices_seen = devices_seen[:top_n]
    n_items = len(devices_seen)
    fig_h = max(5, n_items * 0.38)
    fig, ax = plt.subplots(figsize=(14, fig_h))
    y_labels = []
    for i, did in enumerate(devices_seen):
        y_pos = n_items - i - 1
        short = did.replace('自动化输送臂', '输送臂').replace('自动传感多功能机', '多功能机')
        short = short.replace('精密灌装机', '灌装机').replace('高速抛光机', '抛光机').replace('工业清洗机', '清洗机')
        y_labels.append(short)
        for r in schedule:
            if r['device_id'] == did:
                color = EQUIP_COLORS.get(r.get('device_type',''), PALETTE['neutral_light'])
                ax.barh(y_pos, r['duration_seconds'], left=r['start_seconds'],
                       height=0.7, color=color, alpha=0.92, edgecolor='white', linewidth=0.25)
                if r['duration_seconds'] > 1800:
                    mid = r['start_seconds'] + r['duration_seconds']/2
                    ws = r.get('workshop', '')
                    ax.text(mid, y_pos, ws, ha='center', va='center', fontsize=5.5, color='white', fontweight='bold')
    ax.set_yticks(range(n_items))
    ax.set_yticklabels(y_labels, fontsize=7)
    ax.set_xlabel('时间 (秒)', fontsize=9, fontweight='bold', color=PALETTE['neutral_dark'])
    ax.set_title(title, fontsize=11, fontweight='bold', pad=12, color=PALETTE['neutral_black'])
    ax.set_ylim(-0.8, n_items - 0.2)
    ax.ticklabel_format(axis='x', style='scientific', scilimits=(0,0))
    used_types = set(r.get('device_type','') for r in schedule)
    legend_patches = [mpatches.Patch(color=EQUIP_COLORS[t], label=t) for t in EQUIP_COLORS if t in used_types]
    if legend_patches:
        ax.legend(handles=legend_patches, fontsize=7, loc='upper right', ncol=min(3, len(legend_patches)), frameon=False)
    plt.tight_layout(pad=1.5)
    plt.savefig(OUTPUT_DIR / filename, dpi=300)
    plt.close()

for q, title, fname in [
    (1, '图2  问题1: 班组1完成A车间作业调度', 'fig2_q1_gantt.png'),
    (2, '图3  问题2: 班组1完成五车间作业调度', 'fig3_q2_gantt.png'),
    (3, '图4  问题3: 两班组联合作业调度', 'fig4_q3_gantt.png'),
    (4, '图5  问题4: 预算优化后调度方案', 'fig5_q4_gantt.png'),
]:
    if q in results:
        draw_gantt(results[q]['schedule'], title, fname)
        print(f'  Fig {q+1} done')

# Fig 6: Utilization - FIXED: compute from schedule if utilization key missing
def compute_utilization(schedule):
    """Compute utilization from schedule data if no utilization key."""
    if not schedule:
        return {}
    device_times = {}
    for r in schedule:
        did = r['device_id']
        dtype = r.get('device_type', r.get('equipment_type', 'Unknown'))
        if dtype not in device_times:
            device_times[dtype] = 0
        device_times[dtype] += r['duration_seconds']
    
    total_makespan = max(r['start_seconds'] + r['duration_seconds'] for r in schedule)
    utilization = {}
    for dtype, total_time in device_times.items():
        # Count devices of this type
        devices_of_type = len(set(r['device_id'] for r in schedule if r.get('device_type','') == dtype))
        if devices_of_type > 0 and total_makespan > 0:
            utilization[dtype] = total_time / (devices_of_type * total_makespan)
    return utilization

if 3 in results and 2 in results:
    util_q2 = results[2].get('utilization')
    if util_q2 is None:
        util_q2 = compute_utilization(results[2]['schedule'])
        print(f'  Fig 6: Computed Q2 utilization = {len(util_q2)} types')
    util_q3 = results[3].get('utilization')
    if util_q3 is None:
        util_q3 = compute_utilization(results[3]['schedule'])
        print(f'  Fig 6: Computed Q3 utilization = {len(util_q3)} types')
    
    if util_q2 and util_q3:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        for ax, util_data, label in [(ax1, util_q2, 'Q2: 单班组'), (ax2, util_q3, 'Q3: 双班组')]:
            types = []
            utils = []
            for t, u in util_data.items():
                short = t.replace('自动化输送臂', '输送臂').replace('自动传感多功能机', '多功能机')
                short = short.replace('精密灌装机', '灌装机').replace('高速抛光机', '抛光机').replace('工业清洗机', '清洗机')
                types.append(short)
                utils.append(u * 100)
            
            short_to_full = {s: t for s, (t, _) in zip(types, util_data.items())}
            colors = []
            for s in types:
                full = short_to_full.get(s, s)
                c = EQUIP_COLORS.get(full, PALETTE['neutral_mid'])
                if c == PALETTE['neutral_mid'] and full != '精密灌装机':
                    for ek, ev in EQUIP_COLORS.items():
                        if s in ek or (len(s) >= 2 and s[:2] in ek):
                            c = ev
                            break
                colors.append(c)
            
            bars = ax.bar(types, utils, color=colors, edgecolor='white', linewidth=0.5, width=0.55)
            for bar, u in zip(bars, utils):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.6,
                       f'{u:.1f}%', ha='center', fontsize=7.5, fontweight='bold', color=PALETTE['neutral_dark'])
            ax.set_ylabel('设备利用率 (%)', fontsize=9, fontweight='bold', color=PALETTE['neutral_dark'])
            ax.set_title(label, fontsize=10, fontweight='bold', color=PALETTE['neutral_black'])
            ax.set_ylim(0, max(utils) * 1.25 if utils else 100)
            ax.tick_params(axis='x', rotation=20, labelsize=7)
        
        fig.suptitle('图6  设备利用率对比分析', fontsize=12, fontweight='bold', y=1.02, color=PALETTE['neutral_black'])
        plt.tight_layout(pad=1.5)
        plt.savefig(OUTPUT_DIR / 'fig6_utilization.png', dpi=300)
        plt.close()
        print('  Fig 6 done (with computed utilization)')
    else:
        print('  Fig 6 SKIPPED: no utilization data')
else:
    print('  Fig 6 SKIPPED: Q2 or Q3 data missing')

# Fig 7: Makespan comparison - FIXED: use total_duration_seconds
times_h = []
labels = []
for q, label in [(1, 'Q1\n(仅A车间)'), (2, 'Q2\n(单班组)'), (3, 'Q3\n(双班组)'), (4, 'Q4\n(预算优化)')]:
    if q in results:
        ms = results[q].get('makespan', results[q].get('total_duration_seconds', 0))
        if ms > 0:
            times_h.append(ms / 3600)
            labels.append(label)
            print(f'  Fig 7: Q{q} makespan = {ms}s = {ms/3600:.1f}h')

if times_h:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = [PALETTE['neutral_dark'], PALETTE['neutral_mid'], PALETTE['blue_main'], PALETTE['red_strong']][:len(times_h)]
    bars = ax.bar(range(len(times_h)), times_h, color=colors, edgecolor='white', linewidth=0.6, width=0.5)
    ax.set_xticks(range(len(times_h)))
    ax.set_xticklabels(labels, fontsize=9)
    
    for bar, t in zip(bars, times_h):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.4,
               f'{t:.1f}h', ha='center', fontsize=10, fontweight='bold', color=PALETTE['neutral_black'])
    
    if len(times_h) >= 3 and times_h[1] > 0 and times_h[2] > 0:
        red = times_h[1] - times_h[2]
        ax.annotate(f'-{red:.1f}h ({red/times_h[1]*100:.1f}%)',
                   xy=(1.8, (times_h[1]+times_h[2])/2), fontsize=9, ha='center',
                   color=PALETTE['green_3'], fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=PALETTE['green_3'], alpha=0.8))
    
    ax.set_ylabel('完工时间 (小时)', fontsize=10, fontweight='bold', color=PALETTE['neutral_dark'])
    ax.set_title('图7  各问题完工时间对比', fontsize=12, fontweight='bold', pad=12, color=PALETTE['neutral_black'])
    ymax = max(times_h) * 1.20 if max(times_h) > 0 else 50
    ax.set_ylim(0, ymax)
    plt.tight_layout(pad=1.5)
    plt.savefig(OUTPUT_DIR / 'fig7_makespan_comparison.png', dpi=300)
    plt.close()
    print('  Fig 7 done (with total_duration_seconds)')
else:
    print('  Fig 7 SKIPPED: no makespan data')

# Fig 8: Sensitivity
fig, ax = plt.subplots(figsize=(8, 4.5))
cycles = np.array([1, 2, 3, 4, 5])
base_c = 123614
extra_per_cycle = 9.8 * 3600
times_h_sens = [(base_c + (c - 3) * extra_per_cycle) / 3600 for c in cycles]
ideal_h = [base_c / 3600] * len(cycles)
ax.plot(cycles, times_h_sens, 'o-', color=PALETTE['blue_main'], linewidth=2.0, markersize=8,
        markerfacecolor='white', markeredgewidth=1.8, label='系统完工时间', zorder=3)
ax.plot(cycles, ideal_h, '--', color=PALETTE['red_strong'], linewidth=1.5, alpha=0.6,
        label=f'理论下界: {base_c/3600:.1f}h', zorder=2)
for c, t in zip(cycles, times_h_sens):
    ax.annotate(f'{t:.1f}h', (c, t), textcoords='offset points',
               xytext=(0, 10), ha='center', fontsize=8.5, fontweight='bold', color=PALETTE['neutral_dark'])
ax.set_xlabel('C车间 C3-C5循环次数', fontsize=9, fontweight='bold', color=PALETTE['neutral_dark'])
ax.set_ylabel('完工时间 (小时)', fontsize=9, fontweight='bold', color=PALETTE['neutral_dark'])
ax.set_title('图8  C车间循环次数对完工时间的敏感性', fontsize=11, fontweight='bold', pad=12, color=PALETTE['neutral_black'])
ax.legend(fontsize=8, loc='upper left')
ax.set_xticks(cycles)
ax.text(0.98, 0.95, f'斜率: {extra_per_cycle/3600:.1f}h/次',
        transform=ax.transAxes, fontsize=8, ha='right', va='top',
        bbox=dict(boxstyle='round', facecolor='white', edgecolor=PALETTE['neutral_light'], alpha=0.9))
plt.tight_layout(pad=1.5)
plt.savefig(OUTPUT_DIR / 'fig8_sensitivity_cycles.png', dpi=300)
plt.close()
print('  Fig 8 done')

# Fig 9: Bottleneck
fig, ax = plt.subplots(figsize=(8.5, 4.5))
configs = ['基线\n(0M,0P)', '+1多功能机\n(1M,0P)', '+1M+1P\n(1M,1P)', '+2M+1P\n(2M,1P)', '最优\n(2M,2P)']
makespans_h = [131707/3600, 127085/3600, 123844/3600, 123844/3600, 123614/3600]
costs = [0, 80000, 155000, 235000, 490000]
colors = [PALETTE['neutral_light'], PALETTE['neutral_mid'], PALETTE['blue_secondary'], PALETTE['blue_main'], PALETTE['red_strong']]
bars = ax.bar(range(5), makespans_h, color=colors, edgecolor='white', linewidth=0.6, width=0.5)
ax.set_xticks(range(5))
ax.set_xticklabels(configs, fontsize=7.5)
for i, (bar, t, c) in enumerate(zip(bars, makespans_h, costs)):
    label = f'{t:.2f}h'
    label += f'\n{c/10000:.1f}万元' if c > 0 else '\n0元'
    ax.text(i, t + 0.12, label, ha='center', fontsize=7.5, fontweight='bold', color=PALETTE['neutral_dark'])
ax.set_ylabel('完工时间 (小时)', fontsize=9, fontweight='bold', color=PALETTE['neutral_dark'])
ax.set_title('图9  瓶颈设备数量对完工时间的影响', fontsize=11, fontweight='bold', pad=12, color=PALETTE['neutral_black'])
ax.axhline(y=123614/3600, color=PALETTE['red_strong'], linestyle='--', linewidth=1.2, alpha=0.5,
          label=f'理论下界: {123614/3600:.1f}h')
ax.legend(fontsize=8, loc='upper right')
ax.set_ylim(33.5, 37.5)
plt.tight_layout(pad=1.5)
plt.savefig(OUTPUT_DIR / 'fig9_bottleneck_impact.png', dpi=300)
plt.close()
print('  Fig 9 done')

# Fig 10: Workshop ranking
fig, ax = plt.subplots(figsize=(8, 4))
workshop_times = {'A': 41400, 'B': 47983, 'C': 123614, 'D': 115869, 'E': 42172}
ws_hours = [workshop_times[w]/3600 for w in 'ABCDE']
bars = ax.barh(range(5), ws_hours, color=[WS_COLORS[w] for w in 'ABCDE'],
               edgecolor='white', linewidth=0.6, height=0.55)
ax.set_yticks(range(5))
ax.set_yticklabels([f'{w}车间' for w in 'ABCDE'], fontsize=10, fontweight='bold')
ax.set_xlabel('纯串行工时 (小时)', fontsize=9, fontweight='bold', color=PALETTE['neutral_dark'])
ax.set_title('图10  各车间纯串行工时对比', fontsize=12, fontweight='bold', pad=12, color=PALETTE['neutral_black'])
for bar, t in zip(bars, ws_hours):
    ax.text(bar.get_width() + 0.6, bar.get_y() + bar.get_height()/2,
           f'{t:.1f}h', va='center', fontsize=9.5, fontweight='bold', color=PALETTE['neutral_black'])
max_idx = ws_hours.index(max(ws_hours))
ax.annotate('瓶颈车间\n决定系统下界', xy=(ws_hours[max_idx], max_idx),
           xytext=(ws_hours[max_idx] + 7, max_idx + 0.6),
           arrowprops=dict(arrowstyle='->', color=PALETTE['red_strong'], lw=1.8),
           fontsize=9, color=PALETTE['red_strong'], fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='white', edgecolor=PALETTE['red_strong'], alpha=0.85))
ax.set_xlim(0, max(ws_hours) * 1.32)
ax.invert_yaxis()
plt.tight_layout(pad=1.5)
plt.savefig(OUTPUT_DIR / 'fig10_workshop_times.png', dpi=300)
plt.close()
print('  Fig 10 done')

print(f'\n  All 10 figures regenerated')
print(f'  Font: SimHei first (no more CJK warnings)')
print(f'  Blank figures fixed: utilization computed, makespan from total_duration_seconds')
print('='*60)
