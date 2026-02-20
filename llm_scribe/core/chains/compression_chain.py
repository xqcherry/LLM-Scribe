from typing import List
from langchain_core.output_parsers import StrOutputParser
from ...prompts.templates import CompressionPromptTemplate


class CompressionChain:
    """记忆压缩链，用于压缩旧记忆"""

    def __init__(self, llm):
        self.llm = llm

        prompt_template = CompressionPromptTemplate()
        prompt = prompt_template.PROMPT
        self.chain = prompt | self.llm | StrOutputParser()

    async def invoke(self, summaries: List[str]) -> str:
        """压缩摘要"""
        summaries_text = "\n\n---\n\n".join(summaries)
        result = await self.chain.ainvoke({"summaries": summaries_text})
        return result
