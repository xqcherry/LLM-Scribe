from __future__ import annotations

from typing import Protocol


class PromptProviderPort(Protocol):
    """提示词提供端口：用于按用途提供 Prompt 模板。"""

    def get_summary_prompt(self, max_topics: int = 5):
        """获取摘要 Prompt 模板对象。"""
        ...

    def get_extraction_prompt(self):
        """获取信息提取 Prompt 模板对象。"""
        ...

    def get_compression_prompt(self):
        """获取压缩 Prompt 模板对象。"""
        ...
