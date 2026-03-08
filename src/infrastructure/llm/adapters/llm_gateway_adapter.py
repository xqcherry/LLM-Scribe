from __future__ import annotations

from typing import Any, Optional

from ....application.ports.llm_gateway_port import LLMGatewayPort
from ..providers.moonshot_provider import MoonshotProvider


class LLMGatewayAdapter(LLMGatewayPort):
    """统一 LLM 能力适配器。"""

    def __init__(self, provider: MoonshotProvider | None = None) -> None:
        self._provider = provider or MoonshotProvider()

    @property
    def token_counter(self) -> Any:
        return self._provider.token_counter

    def select_model(
        self,
        prompt_tokens: int,
        max_output_tokens: int = 2000,
        safety_margin: float = 0.8,
    ) -> str:
        return self._provider.select_model(
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
        return self._provider.create_model(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_tokens=prompt_tokens,
        )

    def estimate_cost(self, model_name: str, token_count: int) -> float:
        try:
            return self._provider.estimate_cost(model_name, token_count)
        except (AttributeError, Exception):
            return 0.0
