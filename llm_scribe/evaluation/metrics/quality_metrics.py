from typing import List, Dict


class QualityMetrics:
    """摘要质量评估指标"""

    @staticmethod
    def evaluate_completeness(
        summary: str,
        original_messages: List[Dict]
    ) -> float:
        """评估完整性"""
        # 简化实现：检查摘要是否包含关键信息
        if not summary or not original_messages:
            return 0.0
        
        # 提取参与者
        participants = set(
            m.get("sender_nickname", "")
            for m in original_messages
            if m.get("sender_nickname")
        )
        
        # 检查摘要中是否提到参与者
        mentioned = sum(1 for p in participants if p in summary)
        completeness = mentioned / len(participants) if participants else 0.0
        
        return min(completeness, 1.0)

    @staticmethod
    def evaluate_length(
        summary: str,
        min_length: int = 50,
        max_length: int = 2000
    ) -> float:
        """评估长度合理性"""
        length = len(summary)
        
        if length < min_length:
            return 0.5  # 太短
        elif length > max_length:
            return 0.8  # 太长但可接受
        else:
            return 1.0  # 合理
    
    def evaluate_all(
        self,
        summary: str,
        original_messages: List[Dict]
    ) -> Dict[str, float]:
        """评估所有指标"""
        return {
            "completeness": self.evaluate_completeness(summary, original_messages),
            "length": self.evaluate_length(summary),
            "overall": (
                self.evaluate_completeness(summary, original_messages) +
                self.evaluate_length(summary)
            ) / 2
        }
