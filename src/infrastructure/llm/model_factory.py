"""
通用 LLM 提供方模型工厂实现。

默认使用 Moonshot Chat 模型，但通过命名与接口抽象，后续可以替换为任意
兼容的开源或云端大模型提供方。
"""

from typing import Optional

from langchain_community.chat_models.moonshot import MoonshotChat

from src.config import plugin_config as config
from src.infrastructure.llm.token_counter import TokenCounter


class LLMProviderFactory:
    """通用 LLM 提供方模型工厂。"""

    MODELS = {
        "moonshot-v1-8k": {"max_tokens": 8000, "cost_per_1k": 0.012},
        "moonshot-v1-32k": {"max_tokens": 32000, "cost_per_1k": 0.024},
        "moonshot-v1-128k": {"max_tokens": 128000, "cost_per_1k": 0.06},
    }

    def __init__(self) -> None:
        self.config = config
        self.token_counter = TokenCounter()
        # 兼容旧的 MOONSHOT_API_KEY，也支持更通用的 LLM_API_KEY
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
        """根据 token 数量选择模型。"""
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
        """创建模型实例。"""
        if model_name is None:
            if prompt_tokens is not None:
                model_name = self.select_model(prompt_tokens, max_tokens)
                print(f"自动选择模型: {model_name}")
            else:
                model_name = "moonshot-v1-32k"
                print(f"使用默认模型: {model_name}")

        return MoonshotChat(
            api_key=self.api_key,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def estimate_cost(self, model_name: str, tokens: int) -> float:
        """估算成本。"""
        cost_per_1k = self.MODELS[model_name]["cost_per_1k"]
        return (tokens / 1000) * cost_per_1k

