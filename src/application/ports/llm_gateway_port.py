from __future__ import annotations

from typing import Any, Optional, Protocol


class LLMGatewayPort(Protocol):
    """统一 LLM 能力入口端口。"""

    @property
    def token_counter(self) -> Any:
        """用于统计 token 的计数器对象。"""
        ...

    def select_model(
        self,
        prompt_tokens: int,
        max_output_tokens: int = 2000,
        safety_margin: float = 0.8,
    ) -> str:
        """根据 token 数量选择合适模型名称。"""
        ...

    def create_model(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        prompt_tokens: Optional[int] = None,
    ) -> Any:
        """创建底层 LLM 实例。"""
        ...

    def estimate_cost(self, model_name: str, token_count: int) -> float:
        """根据模型名称和 token 数量预估费用。"""
        ...
