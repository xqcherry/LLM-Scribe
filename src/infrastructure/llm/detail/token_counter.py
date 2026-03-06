import tiktoken
from typing import List, Dict


class TokenCounter:
    """Token 计算工具。"""

    def __init__(self) -> None:
        # 大多数 OpenAI/Claude 兼容模型使用 cl100k_base 编码
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """计算文本的 token 数量。"""
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def count_messages_tokens(self, messages: List[Dict]) -> int:
        """
        计算消息列表的 token 数量。
        """
        # 模拟模型输入格式进行拼接统计
        text = "\n".join(
            f"{m.get('sender_nickname', '')}: {m.get('raw_message', '')}"
            for m in messages
        )
        return self.count_tokens(text)

    def estimate_prompt_tokens(
            self,
            system_prompt: str,
            messages: List[Dict],
            memory_context: str = "",
    ) -> int:
        """估算完整提示词的 token 数量。"""
        total = self.count_tokens(system_prompt)
        total += self.count_messages_tokens(messages)
        if memory_context:
            # RAG 检索到的背景知识也计入总数
            total += self.count_tokens(memory_context)

        return total