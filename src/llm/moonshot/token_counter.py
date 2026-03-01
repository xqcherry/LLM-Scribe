import tiktoken
from typing import List, Dict
from llm_scribe.pipeline.cq_filter import cq_filter


class TokenCounter:
    """Token 计算工具"""

    def __init__(self):
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """计算文本的 token 数量"""
        return len(self.encoding.encode(text))

    def count_messages_tokens(self, messages: List[dict]) -> int:
        """计算消息列表的 token 数量"""
        text = "\n".join(
            f"{m.get('sender_nickname', '')}: {cq_filter(m.get('raw_message', ''))}"
            for m in messages
        )
        return self.count_tokens(text)

    def estimate_prompt_tokens(
        self,
        system_prompt: str,
        messages: List[Dict],
        memory_context: str = ""
    ) -> int:
        """估算完整提示词的 token 数量"""
        total = self.count_tokens(system_prompt)
        total += self.count_messages_tokens(messages)
        if memory_context:
            total += self.count_tokens(memory_context)
        return total