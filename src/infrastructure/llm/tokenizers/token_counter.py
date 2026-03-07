from __future__ import annotations

from typing import Dict, List

import tiktoken


class TokenCounter:
    """Token 计算工具。"""

    def __init__(self) -> None:
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def count_messages_tokens(self, messages: List[Dict]) -> int:
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
        total = self.count_tokens(system_prompt)
        total += self.count_messages_tokens(messages)
        if memory_context:
            total += self.count_tokens(memory_context)
        return total
