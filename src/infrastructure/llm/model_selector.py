"""
Moonshot 模型选择策略。

从原先的 `src.llm.moonshot.model_selector` 迁移而来。
"""

from typing import Literal

from src.infrastructure.llm.model_factory import MoonshotFactory


class ModelSelector:
    """模型选择策略。"""

    def __init__(self, model_factory: MoonshotFactory | None = None) -> None:
        self.model_factory = model_factory or MoonshotFactory()

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

