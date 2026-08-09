from __future__ import annotations

from langchain_core.runnables import RunnablePassthrough

from ...prompts import ExtractionPromptTemplate


class ExtractionChain:
    """分块信息提取链：把单块聊天文本提取为关键信息文本。"""

    def __init__(self, llm):
        self.llm = llm
        self.prompt = ExtractionPromptTemplate.PROMPT
        self.chain = RunnablePassthrough() | self.prompt | self.llm

    async def invoke(self, messages_text: str) -> str:
        if not messages_text:
            return "（无有效信息）"
        result = await self.chain.ainvoke({"messages": messages_text})
        return result.content if hasattr(result, "content") else str(result)
