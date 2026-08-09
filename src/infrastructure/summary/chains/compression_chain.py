from __future__ import annotations

from langchain_core.runnables import RunnablePassthrough

from ...prompts import CompressionPromptTemplate


class CompressionChain:
    """记忆压缩链：把摘要文本压缩成更简洁的历史上下文，用于滑动窗口。"""

    def __init__(self, llm):
        self.llm = llm
        self.prompt = CompressionPromptTemplate.PROMPT
        self.chain = RunnablePassthrough() | self.prompt | self.llm

    async def invoke(self, summaries: str) -> str:
        if not summaries:
            return ""
        result = await self.chain.ainvoke({"summaries": summaries})
        return result.content if hasattr(result, "content") else str(result)
