"""LangSmith 监控追踪"""
from typing import Optional, Dict, List
from langsmith import traceable, Client
from langchain.callbacks import LangChainTracer
from ...config import get_config


class LangSmithTracer:
    """LangSmith 监控服务"""
    
    def __init__(self, api_key: Optional[str] = None):
        config = get_config()
        self.api_key = api_key or config.langsmith_api_key
        
        if self.api_key:
            self.client = Client(api_key=self.api_key)
            self.tracer = LangChainTracer()
        else:
            self.client = None
            self.tracer = None
    
    @traceable(name="generate_summary")
    def trace_summary_generation(
        self,
        group_id: int,
        hours: int,
        messages_count: int
    ):
        """追踪摘要生成"""
        # LangSmith 会自动记录
        pass
    
    def evaluate_summary_quality(
        self,
        summary: str,
        original_messages: List[Dict]
    ) -> Optional[Dict]:
        """评估摘要质量"""
        if not self.client:
            return None
        
        try:
            # 使用 LangSmith 评估器
            evaluator = self.client.evaluate(
                data=[{
                    "inputs": {"messages": original_messages},
                    "outputs": {"summary": summary}
                }],
                evaluators=[
                    "qa_score",
                    "relevance",
                    "coherence"
                ]
            )
            return evaluator
        except Exception as e:
            print(f"LangSmith evaluation error: {e}")
            return None
