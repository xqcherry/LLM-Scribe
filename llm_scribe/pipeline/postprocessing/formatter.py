"""摘要格式化器"""
from typing import Dict
from ...core.models.summary import SummaryOutput


class SummaryFormatter:
    """摘要格式化器"""
    
    def format(self, summary_output: SummaryOutput, metadata: Dict = None) -> str:
        """格式化摘要输出"""
        lines = []
        
        # 添加元数据（如果有）
        if metadata:
            lines.append("【摘要信息】")
            if metadata.get("model"):
                lines.append(f"模型：{metadata['model']}")
            if metadata.get("token_count"):
                lines.append(f"Token数：{metadata['token_count']}")
            lines.append("")
        
        # 整体摘要
        lines.append("【整体摘要】")
        lines.append(summary_output.overall_summary)
        lines.append("")
        
        # 话题总结
        if summary_output.topics:
            lines.append("【话题总结】")
            for topic in summary_output.topics:
                lines.append(f"\n话题：{topic.topic}")
                lines.append(f"摘要：{topic.summary}")
                if topic.participants:
                    lines.append(f"参与者：{', '.join(topic.participants)}")
                if topic.key_points:
                    lines.append(f"关键要点：")
                    for point in topic.key_points:
                        lines.append(f"  - {point}")
        
        # 关键引用
        if summary_output.key_quotes:
            lines.append("\n【关键引用】")
            for i, quote in enumerate(summary_output.key_quotes, 1):
                lines.append(f"{i}. {quote}")
        
        # 参与者
        if summary_output.participants:
            lines.append(f"\n【参与者】{', '.join(summary_output.participants)}")
        
        # 情感倾向
        lines.append(f"\n【情感倾向】{summary_output.sentiment}")
        
        return "\n".join(lines)
    
    def format_simple(self, summary_output: SummaryOutput) -> str:
        """简单格式化"""
        return summary_output.overall_summary
