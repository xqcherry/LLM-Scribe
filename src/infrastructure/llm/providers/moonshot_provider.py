from __future__ import annotations

from typing import Optional

from langchain_community.chat_models.moonshot import MoonshotChat

from ....config import plugin_config as config
from ..tokenizers.token_counter import TokenCounter


class MoonshotProvider:
    """Moonshot 提供方实现，封装模型创建与计费信息。"""

    MODELS = {
        "moonshot-v1-8k": {"max_tokens": 8000, "cost_per_1k": 0.012},
        "moonshot-v1-32k": {"max_tokens": 32000, "cost_per_1k": 0.024},
        "moonshot-v1-128k": {"max_tokens": 128000, "cost_per_1k": 0.06},
    }

    def __init__(self) -> None:
        self.config = config
        self.token_counter = TokenCounter()
        self.api_key = (
            getattr(self.config, "llm_api_key", "") or self.config.moonshot_api_key
        )

        if not self.api_key:
            raise ValueError(
                "LLM API key is empty. "
                "请在环境变量中设置 LLM_API_KEY 或兼容的 MOONSHOT_API_KEY。"
            )

    def select_model(
        self,
        prompt_tokens: int,
        max_output_tokens: int = 2000,
        safety_margin: float = 0.8,
    ) -> str:
        total_tokens = prompt_tokens + max_output_tokens
        required_tokens = int(total_tokens / safety_margin)

        if required_tokens <= self.MODELS["moonshot-v1-8k"]["max_tokens"]:
            return "moonshot-v1-8k"
        if required_tokens <= self.MODELS["moonshot-v1-32k"]["max_tokens"]:
            return "moonshot-v1-32k"
        return "moonshot-v1-128k"

    def create_model(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        prompt_tokens: Optional[int] = None,
    ) -> MoonshotChat:
        if model_name is None:
            if prompt_tokens is not None:
                model_name = self.select_model(prompt_tokens, max_tokens)
            else:
                model_name = "moonshot-v1-32k"

        return MoonshotChat(
            api_key=self.api_key,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def estimate_cost(self, model_name: str, token_count: int) -> float:
        cost_per_1k = self.MODELS[model_name]["cost_per_1k"]
        return (token_count / 1000) * cost_per_1k
