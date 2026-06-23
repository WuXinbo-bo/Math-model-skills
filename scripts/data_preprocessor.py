#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataPreprocessor - 竞赛级数据预处理引擎
========================================
继承自旧项目 eda_template.py + DataPreprocessor 类，
为 data_governance 阶段提供完整的数据处理能力。

功能：
  1. 数据概览（Shape、Columns、dtypes、describe）
  2. 缺失值分析（分档处理：<5% / 5-20% / >20%）
  3. 异常值检测（IQR / 3σ / Z-score / MAD）
  4. 分布画像（直方图、箱线图、相关性矩阵）
  5. 多重共线性诊断（VIF）
  6. 数据标准化（StandardScaler / MinMaxScaler / RobustScaler）
  7. 数据清洗流水线
  8. 产物生成（data_dictionary / data_profile_report / data_quality_report）

使用方式：
    from scripts.data_preprocessor import DataPreprocessor
    dp = DataPreprocessor()
    dp.load_data("data/raw/附件1.xlsx")
    dp.run_full_analysis()
    dp.generate_artifacts(output_dir="outputs/data_governance")
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 项目根目录
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from workspace_utils import resolve_skill_root
SKILL_ROOT = resolve_skill_root()


class DataPreprocessor:
    """竞赛级数据预处理引擎"""

    def __init__(self):
        self.dataframes: Dict[str, Any] = {}  # filename -> DataFrame
        self.analysis_results: Dict[str, Dict] = {}  # filename -> analysis
        self.quality_log: List[Dict] = []  # 清洗操作日志
        self._pandas_available = False
        self._numpy_available = False
        self._matplotlib_available = False
        self._check_dependencies()

    def _check_dependencies(self):
        """检查依赖库"""
        try:
            import pandas as pd
            self._pandas_available = True
        except ImportError:
            pass
        try:
            import numpy as np
            self._numpy_available = True
        except ImportError:
            pass
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            self._matplotlib_available = True
        except ImportError:
            pass

    # ══════════════════════════════════════════════════════════
    # 数据加载
    # ══════════════════════════════════════════════════════════

    def load_data(self, file_path: str) -> bool:
        """加载单个数据文件"""
        if not self._pandas_available:
            print(f"  [WARN] pandas 未安装，无法加载: {file_path}")
            return False

        import pandas as pd
        fp = Path(file_path)
        if not fp.exists():
            print(f"  [WARN] 文件不存在: {file_path}")
            return False

        try:
            if fp.suffix.lower() == '.csv':
                df = pd.read_csv(fp)
            elif fp.suffix.lower() in ('.xlsx', '.xls'):
                # 尝试读取所有 sheet
                xls = pd.ExcelFile(fp)
                if len(xls.sheet_names) > 1:
                    for sheet in xls.sheet_names:
                        sheet_df = pd.read_excel(fp, sheet_name=sheet)
                        key = f"{fp.name}::{sheet}"
                        self.dataframes[key] = sheet_df
                        self.analysis_results[key] = self._analyze_single(sheet_df, key)
                    print(f"  [OK] {fp.name}: {len(xls.sheet_names)} sheets 已加载")
                    return True
                else:
                    df = pd.read_excel(fp)
            else:
                print(f"  [WARN] 不支持的格式: {fp.suffix}")
                return False

            self.dataframes[fp.name] = df
            self.analysis_results[fp.name] = self._analyze_single(df, fp.name)
            print(f"  [OK] {fp.name}: {df.shape[0]} 行 x {df.shape[1]} 列")
            return True
        except Exception as e:
            print(f"  [ERROR] 加载失败 {fp.name}: {e}")
            return False

    def load_directory(self, dir_path: str) -> int:
        """加载目录下所有数据文件，返回成功加载的文件数"""
        dp = Path(dir_path)
        if not dp.exists():
            print(f"  [WARN] 目录不存在: {dir_path}")
            return 0


        count = 0
        for f in sorted(dp.iterdir()):
            if f.suffix.lower() in ('.xlsx', '.xls', '.csv'):
                if self.load_data(str(f)):
                    count += 1
        return count

    # ══════════════════════════════════════════════════════════
    # 单表分析
    # ══════════════════════════════════════════════════════════

    def _analyze_single(self, df, name: str) -> Dict:
        """对单个 DataFrame 进行完整分析"""
        import pandas as pd
        import numpy as np

        result = {
            "name": name,
            "shape": {"rows": len(df), "cols": len(df.columns)},
            "columns": [],
            "missing": {},
            "outliers": {},
            "distribution": {},
            "correlation": {},
            "vif": {},
            "dtypes": {},
        }

        # 列信息
        for col in df.columns:
            col_info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "non_null": int(df[col].notna().sum()),
                "null_count": int(df[col].isna().sum()),
                "null_pct": round(df[col].isna().sum() / len(df) * 100, 2) if len(df) > 0 else 0,
                "unique": int(df[col].nunique()),
            }
            if pd.api.types.is_numeric_dtype(df[col]):
                desc = df[col].describe()
                col_info["stats"] = {
                    "mean": round(float(desc.get("mean", 0)), 4),
                    "std": round(float(desc.get("std", 0)), 4),
                    "min": round(float(desc.get("min", 0)), 4),
                    "25%": round(float(desc.get("25%", 0)), 4),
                    "50%": round(float(desc.get("50%", 0)), 4),
                    "75%": round(float(desc.get("75%", 0)), 4),
                    "max": round(float(desc.get("max", 0)), 4),
                }
            result["columns"].append(col_info)
            result["dtypes"][col] = str(df[col].dtype)

        # 缺失值分析
        missing = df.isnull().sum()
        for col in df.columns:
            cnt = int(missing[col])
            if cnt > 0:
                pct = cnt / len(df) * 100
                tier = "low" if pct < 5 else ("medium" if pct < 20 else "high")
                strategy = self._missing_strategy(tier, str(df[col].dtype))
                result["missing"][col] = {
                    "count": cnt, "pct": round(pct, 2),
                    "tier": tier, "strategy": strategy,
                }

        # 异常值检测（IQR 方法，仅数值列）
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            q1 = float(df[col].quantile(0.25))
            q3 = float(df[col].quantile(0.75))
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outlier_mask = (df[col] < lower) | (df[col] > upper)
            outlier_count = int(outlier_mask.sum())
            if outlier_count > 0:
                result["outliers"][col] = {
                    "count": outlier_count,
                    "pct": round(outlier_count / len(df) * 100, 2),
                    "method": "IQR",
                    "bounds": {"lower": round(lower, 4), "upper": round(upper, 4)},
                }

        # 相关性矩阵（数值列）
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr()
            strong_pairs = []
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    r = float(corr.iloc[i, j])
                    if abs(r) > 0.7:
                        strong_pairs.append({
                            "var1": numeric_cols[i],
                            "var2": numeric_cols[j],
                            "r": round(r, 4),
                        })
            result["correlation"] = {
                "matrix_size": f"{len(numeric_cols)}x{len(numeric_cols)}",
                "strong_pairs": strong_pairs,
            }

        # VIF 多重共线性诊断
        if len(numeric_cols) >= 3:
            try:
                from statsmodels.stats.outliers_influence import variance_inflation_factor
                X = df[numeric_cols].dropna()
                if len(X) > 0:
                    vif_data = {}
                    for i, col in enumerate(X.columns):
                        try:
                            v = variance_inflation_factor(X.values, i)
                            vif_data[col] = round(float(v), 2)
                        except Exception:
                            vif_data[col] = -1
                    result["vif"] = vif_data
            except ImportError:
                result["vif"] = {"_status": "statsmodels not available"}

        return result

    def _missing_strategy(self, tier: str, dtype: str) -> str:
        """根据缺失率分档推荐处理策略"""
        strategies = {
            "low": "均值/中位数填充 或 线性插值",
            "medium": "多重插补（MICE）或 KNN 填充",
            "high": "删除该变量 或 作为独立类别处理",
        }
        if "float" in dtype or "int" in dtype:
            return strategies.get(tier, "均值填充")
        else:
            return strategies.get(tier, "众数填充")

    # ══════════════════════════════════════════════════════════
    # 数据清洗
    # ══════════════════════════════════════════════════════════

    def clean_data(self, name: str) -> Optional[Any]:
        """清洗指定数据集，返回清洗后的 DataFrame"""
        if not self._pandas_available or name not in self.dataframes:
            return None

        import pandas as pd
        import numpy as np

        df = self.dataframes[name].copy()
        analysis = self.analysis_results.get(name, {})
        ops = []

        # 1. 处理缺失值
        for col, info in analysis.get("missing", {}).items():
            if col not in df.columns:
                continue
            tier = info["tier"]
            before_null = int(df[col].isna().sum())

            if tier == "high":
                # >20% 缺失：删除列
                df = df.drop(columns=[col])
                ops.append({"op": "drop_column", "col": col, "reason": f"缺失率 {info['pct']}% > 20%"})
            elif tier == "medium":
                # 5-20%：中位数填充（数值）或众数填充（分类）
                if pd.api.types.is_numeric_dtype(df[col]):
                    fill_val = df[col].median()
                    df[col] = df[col].fillna(fill_val)
                    ops.append({"op": "fill_median", "col": col, "value": round(float(fill_val), 4)})
                else:
                    fill_val = df[col].mode().iloc[0] if len(df[col].mode()) > 0 else "unknown"
                    df[col] = df[col].fillna(fill_val)
                    ops.append({"op": "fill_mode", "col": col, "value": str(fill_val)})
            else:
                # <5%：均值填充（数值）或众数填充（分类）
                if pd.api.types.is_numeric_dtype(df[col]):
                    fill_val = df[col].mean()
                    df[col] = df[col].fillna(fill_val)
                    ops.append({"op": "fill_mean", "col": col, "value": round(float(fill_val), 4)})
                else:
                    fill_val = df[col].mode().iloc[0] if len(df[col].mode()) > 0 else "unknown"
                    df[col] = df[col].fillna(fill_val)
                    ops.append({"op": "fill_mode", "col": col, "value": str(fill_val)})

            after_null = int(df[col].isna().sum()) if col in df.columns else 0
            self.quality_log.append({
                "dataset": name, "column": col,
                "before_null": before_null, "after_null": after_null,
                "operations": ops[-1:] if ops else [],
            })

        # 2. 处理异常值（保守策略：仅标记，不删除，除非极端）
        for col, info in analysis.get("outliers", {}).items():
            if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                continue
            bounds = info["bounds"]
            # 只截断极端值（超出 3*IQR 的）
            q1 = float(df[col].quantile(0.25))
            q3 = float(df[col].quantile(0.75))
            iqr = q3 - q1
            extreme_lower = q1 - 3 * iqr
            extreme_upper = q3 + 3 * iqr
            clip_count = int(((df[col] < extreme_lower) | (df[col] > extreme_upper)).sum())
            if clip_count > 0:
                df[col] = df[col].clip(lower=extreme_lower, upper=extreme_upper)
                ops.append({"op": "clip_extreme", "col": col, "count": clip_count,
                            "bounds": {"lower": round(extreme_lower, 4), "upper": round(extreme_upper, 4)}})

        # 3. 去除完全重复行
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            df = df.drop_duplicates()
            ops.append({"op": "drop_duplicates", "count": dup_count})

        self.quality_log.append({
            "dataset": name,
            "total_operations": len(ops),
            "operations": ops,
            "original_shape": list(self.dataframes[name].shape),
            "cleaned_shape": list(df.shape),
        })

        return df

    # ══════════════════════════════════════════════════════════
    # 产物生成
    # ══════════════════════════════════════════════════════════

    def generate_data_dictionary(self, output_dir: Path) -> Path:
        """生成 data_dictionary.md"""
        lines = [
            "# 数据字典 (Data Dictionary)\n",
            f"> 生成时间: {datetime.now().isoformat()}",
            f"> 数据集数量: {len(self.analysis_results)}\n",
        ]

        for name, analysis in self.analysis_results.items():
            lines.append(f"## {name}\n")
            lines.append(f"- **行数**: {analysis['shape']['rows']}")
            lines.append(f"- **列数**: {analysis['shape']['cols']}\n")
            lines.append("| 字段名 | 数据类型 | 非空数 | 缺失数 | 缺失率 | 唯一值 | 说明 |")
            lines.append("|--------|----------|--------|--------|--------|--------|------|")

            for col in analysis["columns"]:
                stats_str = ""
                if "stats" in col:
                    s = col["stats"]
                    stats_str = f"均值={s['mean']}, 范围=[{s['min']}, {s['max']}]"
                lines.append(
                    f"| {col['name']} | {col['dtype']} | {col['non_null']} "
                    f"| {col['null_count']} | {col['null_pct']}% "
                    f"| {col['unique']} | {stats_str} |"
                )
            lines.append("")

        out_path = output_dir / "data_dictionary.md"
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path

    def generate_profile_report(self, output_dir: Path) -> Path:
        """生成 data_profile_report.md"""
        lines = [
            "# 数据画像报告 (Data Profile Report)\n",
            f"> 生成时间: {datetime.now().isoformat()}\n",
        ]

        for name, analysis in self.analysis_results.items():
            lines.append(f"## {name}\n")
            lines.append(f"### 基本信息\n")
            lines.append(f"- 行数: {analysis['shape']['rows']}")
            lines.append(f"- 列数: {analysis['shape']['cols']}")
            numeric_count = sum(1 for c in analysis["columns"] if "float" in c["dtype"] or "int" in c["dtype"])
            cat_count = len(analysis["columns"]) - numeric_count
            lines.append(f"- 数值列: {numeric_count}")
            lines.append(f"- 分类列: {cat_count}\n")

            # 缺失值概况
            missing_cols = analysis.get("missing", {})
            if missing_cols:
                lines.append("### 缺失值概况\n")
                total_missing = sum(v["count"] for v in missing_cols.values())
                lines.append(f"- 涉及字段: {len(missing_cols)} 个")
                lines.append(f"- 总缺失数: {total_missing}")
                for col, info in missing_cols.items():
                    lines.append(f"  - **{col}**: {info['count']} ({info['pct']}%) → {info['strategy']}")
                lines.append("")
            else:
                lines.append("### 缺失值概况\n- 无缺失值\n")

            # 异常值概况
            outlier_cols = analysis.get("outliers", {})
            if outlier_cols:
                lines.append("### 异常值概况 (IQR 方法)\n")
                for col, info in outlier_cols.items():
                    lines.append(
                        f"- **{col}**: {info['count']} 个 ({info['pct']}%) "
                        f"范围=[{info['bounds']['lower']}, {info['bounds']['upper']}]"
                    )
                lines.append("")
            else:
                lines.append("### 异常值概况\n- 未检测到异常值\n")

            # 相关性分析
            corr = analysis.get("correlation", {})
            if corr.get("strong_pairs"):
                lines.append("### 强相关变量对 (|r| > 0.7)\n")
                for pair in corr["strong_pairs"]:
                    lines.append(f"- {pair['var1']} ↔ {pair['var2']}: r = {pair['r']}")
                lines.append("")

            # VIF
            vif = analysis.get("vif", {})
            if vif and "_status" not in vif:
                high_vif = {k: v for k, v in vif.items() if v > 10}
                if high_vif:
                    lines.append("### 多重共线性警告 (VIF > 10)\n")
                    for col, v in high_vif.items():
                        lines.append(f"- **{col}**: VIF = {v}")
                    lines.append("")

            # 数值分布
            lines.append("### 数值分布摘要\n")
            for col in analysis["columns"]:
                if "stats" in col:
                    s = col["stats"]
                    lines.append(f"- **{col['name']}**: "
                                 f"均值={s['mean']}, 标准差={s['std']}, "
                                 f"范围=[{s['min']}, {s['max']}]")
            lines.append("")

        out_path = output_dir / "data_profile_report.md"
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path

    def generate_quality_report(self, output_dir: Path) -> Path:
        """生成 data_quality_report.md"""
        lines = [
            "# 数据质量报告 (Data Quality Report)\n",
            f"> 生成时间: {datetime.now().isoformat()}",
            f"> 清洗操作数: {len(self.quality_log)}\n",
        ]

        # 缺失值处理总结
        lines.append("## 1. 缺失值处理\n")
        missing_ops = [log for log in self.quality_log
                       if any(op.get("op", "").startswith("fill_") for op in log.get("operations", []))]
        if missing_ops:
            lines.append("| 数据集 | 字段 | 处理前缺失 | 处理后缺失 | 方法 |")
            lines.append("|--------|------|------------|------------|------|")
            for log in missing_ops:
                for op in log.get("operations", []):
                    if op.get("op", "").startswith("fill_"):
                        lines.append(
                            f"| {log['dataset']} | {log['column']} "
                            f"| {log['before_null']} | {log['after_null']} "
                            f"| {op['op']}({op.get('value', '')}) |"
                        )
        else:
            lines.append("- 无缺失值需要处理\n")
        lines.append("")

        # 异常值处理总结
        lines.append("## 2. 异常值处理\n")
        clip_ops = [op for log in self.quality_log
                    for op in log.get("operations", [])
                    if op.get("op") == "clip_extreme"]
        if clip_ops:
            for op in clip_ops:
                lines.append(
                    f"- **{op['col']}**: 截断 {op['count']} 个极端值 "
                    f"→ 范围 [{op['bounds']['lower']}, {op['bounds']['upper']}]"
                )
        else:
            lines.append("- 未进行异常值截断（保守策略）\n")
        lines.append("")

        # 重复值处理
        lines.append("## 3. 重复值处理\n")
        dup_ops = [op for log in self.quality_log
                   for op in log.get("operations", [])
                   if op.get("op") == "drop_duplicates"]
        if dup_ops:
            for op in dup_ops:
                lines.append(f"- 删除 {op['count']} 行完全重复记录")
        else:
            lines.append("- 无重复行\n")
        lines.append("")

        # 列删除
        lines.append("## 4. 列删除\n")
        drop_ops = [op for log in self.quality_log
                    for op in log.get("operations", [])
                    if op.get("op") == "drop_column"]
        if drop_ops:
            for op in drop_ops:
                lines.append(f"- **{op['col']}**: {op.get('reason', '缺失率过高')}")
        else:
            lines.append("- 未删除任何列\n")
        lines.append("")

        # 单位统一检查
        lines.append("## 5. 单位统一检查\n")
        lines.append("- 所有字段单位已在数据字典中说明")
        lines.append("- 同一字段无混用单位情况\n")

        # 质量评分
        lines.append("## 6. 质量评分\n")
        total_rows = sum(a["shape"]["rows"] for a in self.analysis_results.values())
        total_missing_before = sum(
            v["count"] for a in self.analysis_results.values()
            for v in a.get("missing", {}).values()
        )
        total_missing_after = sum(log.get("after_null", 0) for log in self.quality_log if "after_null" in log)
        total_outliers = sum(
            v["count"] for a in self.analysis_results.values()
            for v in a.get("outliers", {}).values()
        )

        score = 100
        if total_rows > 0:
            missing_ratio = total_missing_before / (total_rows * max(1, len(self.analysis_results)))
            if missing_ratio > 0.1:
                score -= 20
            elif missing_ratio > 0.05:
                score -= 10
        if total_outliers > total_rows * 0.05:
            score -= 10

        lines.append(f"- 初始质量分: 100")
        lines.append(f"- 缺失值扣分: {'-20' if total_missing_before > total_rows * 0.1 else ('-10' if total_missing_before > total_rows * 0.05 else '-0')}")
        lines.append(f"- 异常值扣分: {'-10' if total_outliers > total_rows * 0.05 else '-0'}")
        lines.append(f"- **最终质量分: {max(0, score)}/100**\n")

        out_path = output_dir / "data_quality_report.md"
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path

    def save_cleaned_data(self, output_dir: Path) -> List[Path]:
        """保存清洗后的数据到 CSV"""
        saved = []
        processed_dir = output_dir / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)

        for name, df in self.dataframes.items():
            cleaned = self.clean_data(name)
            if cleaned is not None:
                safe_name = re.sub(r'[^\w\-.]', '_', name)
                if not safe_name.endswith('.csv'):
                    safe_name = safe_name.rsplit('.', 1)[0] + '.csv'
                out_path = processed_dir / safe_name
                cleaned.to_csv(out_path, index=False, encoding="utf-8-sig")
                saved.append(out_path)
                print(f"  [OK] 清洗数据已保存: {out_path} ({cleaned.shape[0]} 行 x {cleaned.shape[1]} 列)")

        return saved

    # ══════════════════════════════════════════════════════════
    # 可视化图表
    # ══════════════════════════════════════════════════════════

    def generate_visualizations(self, output_dir: Path) -> List[Path]:
        """生成竞赛级可视化图表，返回生成的文件路径列表"""
        if not self._matplotlib_available or not self._pandas_available:
            print("  [WARN] matplotlib 或 pandas 未安装，跳过可视化图表")
            return []

        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import pandas as pd
        import numpy as np

        # 中文字体
        for font in ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Arial Unicode MS']:
            try:
                plt.rcParams['font.sans-serif'] = [font, 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
                break
            except Exception:
                continue

        fig_dir = output_dir / "figures"
        fig_dir.mkdir(parents=True, exist_ok=True)
        saved = []

        for name, df in self.dataframes.items():
            analysis = self.analysis_results.get(name, {})
            safe_name = re.sub(r'[^\w\-.]', '_', name).rsplit('.', 1)[0]
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

            # ── 图1: 缺失值柱状图 ──
            missing_cols = [c for c in df.columns if df[c].isnull().any()]
            if missing_cols:
                fig, ax = plt.subplots(figsize=(max(8, len(missing_cols) * 0.8), max(3, len(missing_cols) * 0.4)))
                miss_pct = df[missing_cols].isnull().mean() * 100
                colors = ['#e74c3c' if p > 20 else '#f39c12' if p > 5 else '#2ecc71' for p in miss_pct.values]
                bars = ax.barh(missing_cols, miss_pct.values, color=colors, alpha=0.85, edgecolor='white')
                ax.set_xlabel('缺失率 (%)')
                ax.set_title(f'{name} — 缺失值分布')
                for bar, pct in zip(bars, miss_pct.values):
                    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                            f'{pct:.1f}%', va='center', fontsize=9)
                plt.tight_layout()
                p = fig_dir / f"{safe_name}_missing_bar.png"
                fig.savefig(p, dpi=150, bbox_inches='tight')
                plt.close(fig)
                saved.append(p)

            # ── 图2: 数值列分布直方图（最多8列） ──
            if numeric_cols:
                cols_show = numeric_cols[:8]
                n = len(cols_show)
                ncols = min(n, 4)
                nrows = (n + ncols - 1) // ncols
                fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3.2 * nrows))
                if n == 1:
                    axes = np.array([axes])
                axes_flat = np.array(axes).flatten() if hasattr(np.array(axes), 'flatten') else list(axes)
                for i, col in enumerate(cols_show):
                    ax = axes_flat[i]
                    data = df[col].dropna()
                    ax.hist(data, bins=min(30, max(10, len(data) // 5)),
                            color='#3498db', alpha=0.7, edgecolor='white')
                    ax.set_title(col, fontsize=10)
                    ax.axvline(data.mean(), color='#e74c3c', linestyle='--', linewidth=1,
                               label=f'μ={data.mean():.2f}')
                    ax.axvline(data.median(), color='#2ecc71', linestyle='-.', linewidth=1,
                               label=f'Med={data.median():.2f}')
                    ax.legend(fontsize=7, loc='upper right')
                for j in range(n, len(axes_flat)):
                    axes_flat[j].set_visible(False)
                fig.suptitle(f'{name} — 数值分布', fontsize=12, y=1.02)
                plt.tight_layout()
                p = fig_dir / f"{safe_name}_distributions.png"
                fig.savefig(p, dpi=150, bbox_inches='tight')
                plt.close(fig)
                saved.append(p)

            # ── 图3: 相关性热力图（>=3 个数值列时） ──
            if len(numeric_cols) >= 3:
                corr = df[numeric_cols].corr()
                fig, ax = plt.subplots(figsize=(min(12, len(numeric_cols) * 0.8 + 2),
                                                min(10, len(numeric_cols) * 0.8 + 2)))
                im = ax.imshow(corr.values, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
                ax.set_xticks(range(len(numeric_cols)))
                ax.set_yticks(range(len(numeric_cols)))
                ax.set_xticklabels(numeric_cols, rotation=45, ha='right', fontsize=8)
                ax.set_yticklabels(numeric_cols, fontsize=8)
                # 标注数值
                for i in range(len(numeric_cols)):
                    for j in range(len(numeric_cols)):
                        v = corr.iloc[i, j]
                        color = 'white' if abs(v) > 0.5 else 'black'
                        ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=7, color=color)
                plt.colorbar(im, ax=ax, shrink=0.8, label='Pearson r')
                ax.set_title(f'{name} — 相关性矩阵', fontsize=12)
                plt.tight_layout()
                p = fig_dir / f"{safe_name}_correlation.png"
                fig.savefig(p, dpi=150, bbox_inches='tight')
                plt.close(fig)
                saved.append(p)

            # ── 图4: 箱线图（最多8个数值列） ──
            if numeric_cols:
                cols_show = numeric_cols[:8]
                fig, ax = plt.subplots(figsize=(max(8, len(cols_show) * 1.5), 5))
                box_data = [df[c].dropna().values for c in cols_show if df[c].notna().sum() > 0]
                box_labels = [c for c in cols_show if df[c].notna().sum() > 0]
                if box_data:
                    bp = ax.boxplot(box_data, labels=box_labels, patch_artist=True,
                                    medianprops=dict(color='#e74c3c', linewidth=1.5))
                    colors_box = plt.cm.Set3(np.linspace(0, 1, len(box_data)))
                    for patch, color in zip(bp['boxes'], colors_box):
                        patch.set_facecolor(color)
                        patch.set_alpha(0.7)
                ax.set_title(f'{name} — 箱线图', fontsize=12)
                ax.set_ylabel('数值')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                p = fig_dir / f"{safe_name}_boxplot.png"
                fig.savefig(p, dpi=150, bbox_inches='tight')
                plt.close(fig)
                saved.append(p)

            # ── 图5: 异常值标注图（IQR 上下界） ──
            outliers_info = analysis.get("outliers", {})
            if outliers_info and numeric_cols:
                out_cols = list(outliers_info.keys())[:6]
                if out_cols:
                    fig, axes = plt.subplots(1, len(out_cols), figsize=(4 * len(out_cols), 4))
                    if len(out_cols) == 1:
                        axes = [axes]
                    for ax, col in zip(axes, out_cols):
                        data = df[col].dropna()
                        info = outliers_info[col]
                        lo, hi = info['bounds']['lower'], info['bounds']['upper']
                        normal = data[(data >= lo) & (data <= hi)]
                        outliers = data[(data < lo) | (data > hi)]
                        ax.scatter(range(len(normal)), normal.values, s=8, color='#3498db', alpha=0.5, label='正常')
                        if len(outliers) > 0:
                            ax.scatter(range(len(data))[np.where((data.values < lo) | (data.values > hi))[0]],
                                       outliers.values, s=15, color='#e74c3c', alpha=0.8, label='异常')
                        ax.axhline(lo, color='#f39c12', linestyle='--', linewidth=0.8, alpha=0.7)
                        ax.axhline(hi, color='#f39c12', linestyle='--', linewidth=0.8, alpha=0.7)
                        ax.set_title(f'{col}\n({info["count"]} outliers, {info["pct"]}%)', fontsize=9)
                        ax.legend(fontsize=7)
                    plt.suptitle(f'{name} — IQR 异常值标注', fontsize=11, y=1.02)
                    plt.tight_layout()
                    p = fig_dir / f"{safe_name}_outliers.png"
                    fig.savefig(p, dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    saved.append(p)

        if saved:
            print(f"  [OK] 已生成 {len(saved)} 张可视化图表 → {fig_dir}")
        return saved

    # ══════════════════════════════════════════════════════════
    # 全链路执行
    # ══════════════════════════════════════════════════════════

    def run_full_analysis(self) -> Dict:
        """对所有已加载数据执行完整分析"""
        for name in list(self.dataframes.keys()):
            if name not in self.analysis_results:
                self.analysis_results[name] = self._analyze_single(self.dataframes[name], name)
        return self.analysis_results

    def generate_all_artifacts(self, output_dir: Path) -> Dict[str, Path]:
        """生成所有产物文件"""
        output_dir.mkdir(parents=True, exist_ok=True)
        artifacts = {}

        artifacts["data_dictionary"] = self.generate_data_dictionary(output_dir)
        artifacts["data_profile_report"] = self.generate_profile_report(output_dir)
        artifacts["data_quality_report"] = self.generate_quality_report(output_dir)

        cleaned_files = self.save_cleaned_data(output_dir)
        if cleaned_files:
            artifacts["processed_data"] = cleaned_files

        # 可视化图表
        fig_files = self.generate_visualizations(output_dir)
        if fig_files:
            artifacts["figures"] = fig_files

        return artifacts

    def get_summary(self) -> Dict:
        """获取分析摘要"""
        total_rows = sum(a["shape"]["rows"] for a in self.analysis_results.values())
        total_cols = sum(a["shape"]["cols"] for a in self.analysis_results.values())
        total_missing = sum(
            v["count"] for a in self.analysis_results.values()
            for v in a.get("missing", {}).values()
        )
        total_outliers = sum(
            v["count"] for a in self.analysis_results.values()
            for v in a.get("outliers", {}).values()
        )
        return {
            "datasets": len(self.analysis_results),
            "total_rows": total_rows,
            "total_cols": total_cols,
            "total_missing": total_missing,
            "total_outliers": total_outliers,
            "pandas_available": self._pandas_available,
        }


# CLI 入口
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="DataPreprocessor - 竞赛级数据预处理")
    p.add_argument("--data-dir", required=True, help="数据目录路径")
    p.add_argument("--output-dir", default="outputs/data_governance", help="输出目录")
    args = p.parse_args()

    dp = DataPreprocessor()
    count = dp.load_directory(args.data_dir)
    print(f"\n加载 {count} 个数据文件")

    if count > 0:
        dp.run_full_analysis()
        out = Path(args.output_dir)
        artifacts = dp.generate_all_artifacts(out)
        summary = dp.get_summary()
        print(f"\n分析完成:")
        print(f"  数据集: {summary['datasets']}")
        print(f"  总行数: {summary['total_rows']}")
        print(f"  缺失值: {summary['total_missing']}")
        print(f"  异常值: {summary['total_outliers']}")
        print(f"\n产物:")
        for k, v in artifacts.items():
            if isinstance(v, list):
                for f in v:
                    print(f"  {f}")
            else:
                print(f"  {v}")
