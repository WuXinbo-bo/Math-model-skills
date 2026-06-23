# -*- coding: utf-8 -*-
"""Re-review of revised paper - comparative evaluation"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Previous review scores
prev = {
    "overall": 72,
    "originality": 14,
    "methodology": 13,
    "completeness": 17,
    "presentation": 15,
    "practical_value": 13,
    "critical": 0,
    "major": 3,
    "minor": 7
}

# Re-review after revisions
review_v2 = {
    "decision": "Minor Revision",
    "overall_score": 78,
    "previous_score": 72,
    "delta": "+6",
    "critical_count": 0,
    "major_count": 1,
    "minor_count": 4,
    "editorial_decision": "Minor Revision",
    "review_cycle": 2,
    "timestamp": "2026-05-31",
    "comparative_analysis": {
        "improvements_confirmed": [
            "摘要：覆盖面积表述从模糊的14,847m²修正为'理论覆盖面积14,844m²（经重叠校正后有效覆盖约10,000m²）'——原P2问题已解决",
            "摘要：新增'(训练集与CV的RMSE差距分析见4.1.4节)'引导语，诚实地指向差距分析——原P0问题部分解决",
            "§4.2标题：'灌溉管网优化模型'→'灌溉管网设计与成本估算模型'——原P0问题已解决，命名不再具有误导性",
            "§4.2.2：新增'由于相邻喷头间距15m等于覆盖半径，覆盖圆存在显著重叠。经几何校正后实际有效覆盖面积约等于农场总面积10,000m²，覆盖冗余约48%'——领域审稿人的覆盖面积质疑已回应",
            "§4.3.2：新增'(基于供水-需求平衡方程严格推导)'标注——旱灾线性关系已明确为推导结果而非人为假定",
            "§6.2：新增局限性#1'训练-验证性能差距需进一步诊断'，诚实讨论了6.3倍RMSE差距和消融实验的91%基线——方法论审稿人的核心关切已正面回应",
            "§5.1：已有消融实验表（表11），明确展示去掉滞后特征后R²从0.99降至0.91——这为'模型仍有独立预测能力'提供了数据支撑"
        ],
        "remaining_issues": [
            "§4.1.4的详细CV差距讨论（6.3倍来源分析、分布漂移讨论）尚未嵌入DOCX正文——当前仅依赖摘要的简短标注和§6.2的局限性条目",
            "超参数表（RF/GB完整配置）尚未出现在DOCX中——虽然§4.1.4表格中包含了(200棵树，深度10/4)等基础信息",
            "布局方案对比（网格vs三角排列）仅存在于Markdown修订版v2中，DOCX中未体现",
            "参考文献仍为9条，未增加2015年后新文献"
        ],
        "notes_on_in_place_editing": [
            "本次修订采用python-docx直接在DOCX上修改文本，成功保留了3张嵌入图片（445KB文件大小不变）",
            "文本替换类修改全部成功应用（6/6处）",
            "结构性新增内容（新段落、新表格）因in-place编辑的技术限制未能注入DOCX——这是v5.3.0工作流需要优化的点",
            "建议：后续如果评审要求结构性新增（如新表格、新段落段落），使用Markdown→build_docx流程但保留原DOCX中的图片文件路径映射"
        ]
    },
    "reviewer_reports": {
        "eic": {
            "score": 80,
            "decision": "Minor Revision",
            "summary": "作者认真回应了第一轮评审的核心关切。摘要中的覆盖面积修正和CV差距引导是实质性改进。§4.2标题重命名消除了'优化'的误导性。§6.2新增的局限性条目展现了诚实的学术态度。整体而言，论文在透明度和准确性方面有明显提升。剩余问题集中在：部分讨论的深度可以进一步加强（如4.1.4的CV差距详细分析），以及一些结构性补充（超参数表、布局对比）尚未完全呈现。",
            "key_improvements": ["覆盖面积表述准确化", "方法论局限性诚实披露", "旱灾推导来源明确化"],
            "remaining_concerns": ["CV差距的深入讨论可进一步充实正文"]
        },
        "methodology_reviewer": {
            "score": 75,
            "decision": "Minor Revision",
            "summary": "第一轮提出的数据泄露和过拟合问题已得到正面回应。§6.2新增的局限性#1明确承认了6.3倍RMSE差距，消融实验（表11）证实了仅气象特征R²=0.9127的基线性能。这些改进使模型评估从'过度乐观'转向'诚实且保守'。然而，正文4.1.4节尚未包含对差距来源（分布漂移、自回归衰减）的系统性讨论——目前仅靠摘要的简短标注和§6.2末尾的段落来承载。建议在4.1.4的模型评估段落中直接嵌入差距分析，使其成为读者阅读模型结果时的第一手信息。",
            "key_improvements": ["过拟合问题正面回应", "消融实验提供保守基线", "局限性条目具体化"],
            "remaining_concerns": ["4.1.4正文缺少差距的系统性讨论（目前分散在摘要+§6.2）"]
        },
        "domain_reviewer": {
            "score": 78,
            "decision": "Accept",
            "summary": "覆盖面积的重叠校正（14,844→10,000m²有效）解决了上一轮的核心领域关切。§4.3.2的'基于供水-需求平衡方程严格推导'标注使旱灾分析更加严谨。从农业工程角度看，论文的数值结果现在具有一致性和可追溯性。建议接受。",
            "key_improvements": ["覆盖面积校正准确", "旱灾推导透明化"],
            "remaining_concerns": []
        },
        "perspective_reviewer": {
            "score": 77,
            "decision": "Minor Revision",
            "summary": "论文的跨学科完整性良好。新增的消融分析和局限性讨论使模型解释更加完整。如果能补充超参数配置表和布局方案对比，将进一步提升可复现性和工程说服力。这些属于锦上添花而非必要条件。",
            "key_improvements": ["消融分析提供更完整的模型理解"],
            "remaining_concerns": ["超参数和布局对比可作为附录补充"]
        },
        "devils_advocate": {
            "score": 74,
            "decision": "Minor Revision",
            "summary": "上一轮我指出的三个核心问题中，两个已得到有效处理：§4.2的'优化'标签已更正，旱灾线性关系已标注为推导结果。第三个问题——'R²=0.9888高度可疑'——作者通过新增§6.2局限性条目和消融实验做出了诚实回应，但在正文模型评估部分的讨论仍显不足。我坚持认为：既然消融实验显示仅气象特征R²=0.9127才是更保守的性能估计，这个数字应该比0.9888更突出地呈现在正文中。目前0.9888仍然是摘要和正文中最显眼的数字，而0.9127只在灵敏度分析表中出现。",
            "key_improvements": ["优化标签已更正", "旱灾推导已标注来源", "局限性增加但力度可加强"],
            "remaining_concerns": ["保守性能估计(R²=0.91)的呈现位置不够显眼——建议在摘要或4.1.4结论中直接引用"]
        }
    },
    "consensus": {
        "agreement": "五位审稿人一致认为修订方向正确，论文质量从72分提升至78分。核心争议点（数据泄露、优化名不副实、旱灾假设）已得到正面回应。",
        "remaining_consensus_issue": "反方辩护人和方法论审稿人均指出：CV差距的系统性讨论在当前DOCX中分散在摘要和§6.2，建议在§4.1.4正文中集中呈现，并将保守性能估计(R²=0.91)在摘要或正文显眼位置引用。",
        "final_decision": "Minor Revision — 实质性改进已到位，1个Major + 4个Minor剩余问题均为加强性建议"
    },
    "score_breakdown": {
        "originality": "14→15/20 (+1) — 方法组合的论证更诚实，消融实验增加了方法学深度",
        "methodology": "13→15/20 (+2) — 过拟合问题得到正面回应，局限性讨论更加完整",
        "completeness": "17→18/20 (+1) — 覆盖面积修正和旱灾推导标注填补了领域空白",
        "presentation": "15→16/20 (+1) — 标题重命名消除了误导，摘要更准确",
        "practical_value": "13→14/20 (+1) — 保守性能估计使模型实用性评估更可信"
    },
    "revision_roadmap_v2": [
        {
            "priority": "P1 (Major)",
            "issue": "CV差距讨论分散",
            "action": "在§4.1.4模型评估段落后直接插入一段'训练-验证差异分析'，系统讨论6.3倍差距的来源（分布漂移+自回归衰减），引用消融实验中R²=0.9127作为保守性能基线"
        },
        {
            "priority": "P2 (Minor)",
            "issue": "保守性能数字不显眼",
            "action": "在§4.1.4结论句或摘要中将消融实验的R²=0.9127作为'仅使用气象特征时的模型性能'直接引用"
        },
        {
            "priority": "P2 (Minor)",
            "issue": "超参数配置",
            "action": "在§4.1.4表1后增加超参数表（RF:200树/深度10/min_samples=3, GB:200树/深度4/lr=0.05）"
        },
        {
            "priority": "P2 (Minor)",
            "issue": "布局方案对比",
            "action": "在§4.2.2末尾增加网格vs三角排列的简短对比（可精简为2-3句话而非完整表格）"
        },
        {
            "priority": "P2 (Minor)",
            "issue": "参考文献更新",
            "action": "增加2-3条2015年后文献"
        }
    ]
}

# Save
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace as _rw
out = str(_rw() / "state" / "review_verdict.json")
with open(out, 'w', encoding='utf-8') as f:
    json.dump(review_v2, f, ensure_ascii=False, indent=2)

print("=" * 60)
print("  RE-REVIEW: 农业灌溉系统优化研究")
print("=" * 60)
print(f"\n  上一轮: {prev['overall']}/100 (Major Revision)")
print(f"  本轮:   {review_v2['overall_score']}/100 (Minor Revision)  ▲+6")
print(f"\n  问题降级: Major {prev['major']}→{review_v2['major_count']}, Minor {prev['minor']}→{review_v2['minor_count']}")
print(f"\n  审稿人评分:")
print(f"    主编(EIC):        80/100  Minor Revision")
print(f"    方法论审稿人:      75/100  Minor Revision")
print(f"    领域审稿人:        78/100  Accept ✓")
print(f"    跨学科审稿人:      77/100  Minor Revision")
print(f"    反方辩护人:        74/100  Minor Revision")
print(f"\n  确认改进 ({len(review_v2['comparative_analysis']['improvements_confirmed'])}项):")
for imp in review_v2['comparative_analysis']['improvements_confirmed']:
    print(f"    ✓ {imp[:80]}...")
print(f"\n  剩余问题 ({len(review_v2['comparative_analysis']['remaining_issues'])}项):")
for rem in review_v2['comparative_analysis']['remaining_issues']:
    print(f"    ○ {rem[:80]}...")
