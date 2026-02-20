from typing import List, Dict
from pydantic import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser
from ...prompts.templates import ExtractionPromptTemplate


class ExtractionResult(BaseModel):
    """提取结果"""
    concepts: List[str] = Field(description="关键概念列表")
    events: List[str] = Field(description="重要事件列表")
    quotes: List[str] = Field(description="关键引用列表")


class ExtractionChain:
    """实体提取链"""

    def __init__(self, llm):
        self.llm = llm

        prompt_template = ExtractionPromptTemplate()
        prompt = prompt_template.PROMPT
        self.chain = prompt | self.llm | StrOutputParser()

    async def invoke(self, messages: List[Dict]) -> ExtractionResult:
        """提取实体"""
        messages_text = "\n".join(
            f"{m.get('sender_nickname', '')}: {m.get('raw_message', '')}"
            for m in messages
        )

        result_text = await self.chain.ainvoke({"messages": messages_text})

        # 解析 JSON（简化版，实际应该用 JSON parser）
        import json
        try:
            result_dict = json.loads(result_text)
            return ExtractionResult(**result_dict)
        except Exception as e:
            print(f"extract error: {e}")
            return ExtractionResult()
