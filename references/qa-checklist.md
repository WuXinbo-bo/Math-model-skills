# 数学建模竞赛 QA 检查清单 v4.0

> **来源**: KyrieZhang329/MathModeling-skills QA Checklist + 本技能定制
> **用法**: 终稿组装前逐项检查。任一 `failed` 阻断终稿。
> **输出**: `paper/qa_report.md`

---

## 一、最终决策
三种 QA 状态：`passed` 全部通过 | `passed_with_warnings` 通过有注意事项 | `failed` 阻断

## 二、工作流完整性（所有子问题必须通过）
每个子问题 Qx：
- [ ] 候选方法池存在 (`methods/Qx/qx_method_candidates.md`)
- [ ] 实验报告存在 (`results/Qx/experiments/roundN/`)
- [ ] 最终方法说明存在 (`methods/Qx/qx_final_method_explanation.md`)
- [ ] 最终结果分析存在 (`results/Qx/reports/qx_final_result_analysis.md`)
- [ ] 鲁棒性报告存在 (`robustness/Qx/qx_robustness_report.md`)
- [ ] 冻结数值存在 (`frozen/Qx/frozen_numbers.json`)

## 三、问题覆盖
- [ ] 每个原始子问题已列出，有对应回答
- [ ] 子问题间依赖关系已处理
- [ ] 最终结论映射回原题

## 四、方法一致性
- [ ] 任务类型与方法匹配
- [ ] 每个主模型有基线对比
- [ ] 改进模型明确标注为"可选"

## 五、数据一致性
- [ ] 原始数据未改动，清洗数据有文档
- [ ] 字段含义和单位清晰
- [ ] 缺失值和异常值已处理或讨论

## 六、代码与结果一致性
- [ ] 论文数值与冻结数值一致
- [ ] 随机种子已固定
- [ ] 论文中的数字可在输出文件中找到

## 七、基线对比与鲁棒性
- [ ] 主模型与基线已对比
- [ ] 鲁棒性或敏感性检查每子问题存在
- [ ] 脆弱结论已标注，结论边界已陈述

## 八、图表
- [ ] 每张引用的图/表存在
- [ ] 每张图/表有来源产物
- [ ] 图注解释核心发现

## 九、论文字数与质量
- [ ] 每节达到字数下限
- [ ] 每个数值结果三维讨论（≥3维度）
- [ ] 总字数 15,000-22,000
- [ ] 无 AI 填充语过度使用

## 十、模型建立质量
- [ ] 每个子问题明确声明模型类型
- [ ] 符号表完整（符号/含义/单位/类型）
- [ ] 假设区分为必要假设和简化假设
- [ ] 参数取值有来源依据

## 十一、反编造
- [ ] 无编造数据、参考文献、结果、图表、实验
- [ ] 无编造数值
- [ ] 无无证据的优越性声明

## 十二、产物可追溯性
每个主要声明至少对应一个支持产物，找不到产物→移除声明或标注不完整。

## 十三、修复路由表
| 问题 | 修复途径 |
|------|---------|
| 问题理解错误 | problem_analysis (pipeline stage) |
| 任务类型选错 | problem-classifier → model-formulation-guide.md |
| 缺失方法说明 | model_build (pipeline stage) |
| 缺失鲁棒性证据 | sensitivity_analysis (pipeline stage) |
| 文字问题或过度声明 | paper_review (pipeline stage) |
| 多项阻断 | pipeline_manager.py status → 逐项修复 |
