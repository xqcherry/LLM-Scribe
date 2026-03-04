"""
通用 LLM 模型选择策略。

从原先的 Moonshot 专用实现抽象而来，用于根据任务类型与 token 数量选择
合适的模型名称。
"""

from typing import Literal

from src.infrastructure.llm.detail.model_factory import LLMProviderFactory


class ModelSelector:
    """模型选择策略。"""

    def __init__(self, model_factory: LLMProviderFactory | None = None) -> None:
        self.model_factory = model_factory or LLMProviderFactory()

    def select_by_task(
        self,
        task_type: Literal["summary", "extraction", "compression"],
        token_count: int,
    ) -> str:
        """根据任务类型选择模型。"""
        if task_type == "summary":
            # 摘要任务：根据 token 数量选择
            return self.model_factory.select_model(token_count)
        if task_type == "extraction":
            # 提取任务：使用小模型
            return "moonshot-v1-8k"
        if task_type == "compression":
            # 压缩任务：使用中等模型
            return "moonshot-v1-32k"
        return "moonshot-v1-32k"  # 默认

