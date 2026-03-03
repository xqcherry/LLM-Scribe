"""
LLM 工厂领域接口。

用于将具体的大模型提供方（如 Moonshot）隔离在基础设施层。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class LLMModelFactoryInterface(ABC):
    """LLM 模型工厂抽象接口。"""

    @property
    @abstractmethod
    def token_counter(self) -> Any:
        """用于统计 token 的计数器对象。"""

    @abstractmethod
    def select_model(
        self,
        prompt_tokens: int,
        max_output_tokens: int = 2000,
        safety_margin: float = 0.8,
    ) -> str:
        """根据 token 数量选择合适模型名称。"""

    @abstractmethod
    def create_model(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        prompt_tokens: Optional[int] = None,
    ) -> Any:
        """创建底层 LLM 实例。"""

