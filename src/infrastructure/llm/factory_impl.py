from __future__ import annotations

from typing import Any, Optional

from src.domain.services.llm_service import LLMModelFactoryInterface
from src.infrastructure.llm.detail.model_factory import LLMProviderFactory


class LLMProviderFactoryAdapter(LLMModelFactoryInterface):
    """将 detail 适配为领域层可依赖的工厂接口"""

    def __init__(self, inner: LLMProviderFactory | None = None) -> None:
        self._inner = inner or LLMProviderFactory()


    @property
    def token_counter(self) -> Any:
        return self._inner.token_counter


    def select_model(
        self,
        prompt_tokens: int,
        max_output_tokens: int = 2000,
        safety_margin: float = 0.8,
    ) -> str:
        return self._inner.select_model(
            prompt_tokens=prompt_tokens,
            max_output_tokens=max_output_tokens,
            safety_margin=safety_margin,
        )


    def create_model(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        prompt_tokens: Optional[int] = None,
    ) -> Any:
        return self._inner.create_model(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_tokens=prompt_tokens,
        )

    def estimate_cost(
            self,
            model_name: str,
            token_count: int
    ) -> float:
        """计费预估"""
        try:
            return self._inner.estimate_cost(model_name, token_count)
        except (AttributeError, Exception):
            return 0.0