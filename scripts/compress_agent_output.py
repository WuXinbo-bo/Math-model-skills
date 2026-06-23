#!/usr/bin/env python3
"""
compress_agent_output.py - Agent 输出摘要压缩脚本
从 Agent 的 output/ 目录提取核心结论，生成压缩摘要到 summaries/ 目录。

压缩策略：
1. 提取文件标题和核心结论
2. 识别关键数值结果
3. 生成 3 条核心结论 + 1 个最终结果 + 关键风险点
4. 丢弃中间试错过程和调试日志

使用方式：
    python scripts/compress_agent_output.py --agent-id proposer --task-id T005
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

class OutputCompressor:
    """Agent 输出压缩器"""
    
    def __init__(self):
        self.max_conclusions = 3
        self.max_risks = 3
    
    def compress(
        self,
        agent_id: str,
        task_id: str,
        output_dir: Optional[Path] = None,
        summary_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        压缩 Agent 的输出文件
        
        Args:
            agent_id: Agent ID
            task_id: 任务 ID
            output_dir: 输出目录（默认为 agents/{agent_id}/output/）
            summary_dir: 摘要目录（默认为 agents/{agent_id}/summaries/）
            
        Returns:
            压缩结果字典
        """
        # 设置目录
        if output_dir is None:
            output_dir = PROJECT_ROOT / "agents" / agent_id / "output"
        if summary_dir is None:
            summary_dir = PROJECT_ROOT / "agents" / agent_id / "summaries"
        
        summary_dir.mkdir(parents=True, exist_ok=True)
        
        # 查找任务相关的输出文件
        output_files = list(output_dir.glob(f"{task_id}_*.md"))
        output_files.extend(output_dir.glob(f"{task_id}_*.txt"))
        output_files.extend(output_dir.glob(f"{task_id}_*.json"))
        
        if not output_files:
            return {
                "status": "warning",
                "message": f"未找到任务 {task_id} 的输出文件",
                "summary": ""
            }
        
        # 读取所有输出文件内容
        all_content = []
        for file_path in output_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    all_content.append({
                        "file": file_path.name,
                        "content": content
                    })
            except Exception as e:
                print(f"[Compressor] 读取文件失败 {file_path}: {e}")
        
        if not all_content:
            return {
                "status": "error",
                "message": "无法读取任何输出文件",
                "summary": ""
            }
        
        # 执行压缩
        summary = self._extract_summary(all_content)
        
        # 生成摘要文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = summary_dir / f"{task_id}_summary.md"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"[Compressor] 摘要已生成: {summary_file}")
        
        return {
            "status": "completed",
            "summary_file": str(summary_file),
            "summary": summary,
            "source_files": [item["file"] for item in all_content]
        }
    
    def _extract_summary(self, contents: List[Dict[str, str]]) -> str:
        """从内容中提取摘要"""
        combined_text = "\n\n".join([item["content"] for item in contents])
        
        # 提取核心结论
        conclusions = self._extract_conclusions(combined_text)
        
        # 提取关键数值
        key_values = self._extract_key_values(combined_text)
        
        # 提取风险点
        risks = self._extract_risks(combined_text)
        
        # 生成摘要
        summary_lines = [
            f"# 执行摘要\n",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"## 核心结论\n"
        ]
        
        for i, conclusion in enumerate(conclusions[:self.max_conclusions], 1):
            summary_lines.append(f"{i}. {conclusion}")
        
        if key_values:
            summary_lines.append(f"\n## 关键结果\n")
            for key, value in key_values[:5]:  # 最多5个关键值
                summary_lines.append(f"- **{key}**: {value}")
        
        if risks:
            summary_lines.append(f"\n## 关键风险\n")
            for risk in risks[:self.max_risks]:
                summary_lines.append(f"- {risk}")
        
        return "\n".join(summary_lines)
    
    def _extract_conclusions(self, text: str) -> List[str]:
        """提取核心结论"""
        conclusions = []
        
        # 寻找明确标记的结论
        conclusion_patterns = [
            r"结论[：:]\s*(.+?)(?:\n|$)",
            r"核心结论[：:]\s*(.+?)(?:\n|$)",
            r"总结[：:]\s*(.+?)(?:\n|$)",
            r"结果[：:]\s*(.+?)(?:\n|$)"
        ]
        
        for pattern in conclusion_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            conclusions.extend(matches)
        
        # 如果没有明确标记，提取前几个完整句子
        if not conclusions:
            sentences = re.split(r'[。！？]', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10 and any(keyword in sentence for keyword in 
                    ["模型", "结果", "分析", "方案", "预测", "拟合", "误差"]):
                    conclusions.append(sentence)
        
        return conclusions[:self.max_conclusions]
    
    def _extract_key_values(self, text: str) -> List[tuple]:
        """提取关键数值结果"""
        key_values = []
        
        # 寻找带单位的数值
        value_patterns = [
            r"([A-Za-z_]+)\s*[=＝]\s*([\d.]+)\s*([\w%℃m]+)",
            r"(误差|准确率|精度|R²|RMSE|MAE|MRE)\s*[=：:]\s*([\d.]+)",
            r"([\d.]+)\s*[%℃m]"
        ]
        
        seen_keys = set()
        for pattern in value_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 3:
                    key, value, unit = match
                    if key not in seen_keys:
                        key_values.append((key, f"{value} {unit}"))
                        seen_keys.add(key)
                elif len(match) == 2:
                    key, value = match
                    if key not in seen_keys:
                        key_values.append((key, value))
                        seen_keys.add(key)
        
        return key_values
    
    def _extract_risks(self, text: str) -> List[str]:
        """提取关键风险点"""
        risks = []
        
        risk_patterns = [
            r"风险[：:]\s*(.+?)(?:\n|$)",
            r"注意[：:]\s*(.+?)(?:\n|$)",
            r"警告[：:]\s*(.+?)(?:\n|$)",
            r"问题[：:]\s*(.+?)(?:\n|$)"
        ]
        
        for pattern in risk_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            risks.extend(matches)
        
        # 通用风险关键词检测
        risk_keywords = ["过拟合", "外推", "异常", "不确定", "偏差", "失效"]
        sentences = re.split(r'[。！？]', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence for keyword in risk_keywords):
                if len(sentence) > 5 and sentence not in risks:
                    risks.append(sentence)
        
        return risks[:self.max_risks]


# CLI 入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 输出摘要压缩脚本")
    parser.add_argument("--agent-id", required=True, help="Agent ID")
    parser.add_argument("--task-id", required=True, help="任务 ID")
    parser.add_argument("--output-dir", help="输出目录")
    parser.add_argument("--summary-dir", help="摘要目录")
    
    args = parser.parse_args()
    
    compressor = OutputCompressor()
    
    output_dir = Path(args.output_dir) if args.output_dir else None
    summary_dir = Path(args.summary_dir) if args.summary_dir else None
    
    result = compressor.compress(
        agent_id=args.agent_id,
        task_id=args.task_id,
        output_dir=output_dir,
        summary_dir=summary_dir
    )
    
    print("\n=== 压缩结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
