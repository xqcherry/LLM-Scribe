from typing import List, Dict, Any
from pydantic import BaseModel, Field

from langchain_core.output_parsers import JsonOutputParser
from src.prompts.templates import ExtractionPromptTemplate
from src.pipeline.cq_filter import cq_filter


class ExtractionResult(BaseModel):
    """提取结果模型"""
    concepts: List[str] = Field(default_factory=list, description="关键概念列表")
    events: List[str] = Field(default_factory=list, description="重要事件列表")
    quotes: List[str] = Field(default_factory=list, description="关键引用列表")


class ExtractionChain:
    """实体提取链"""

    def __init__(self, llm):
        self.llm = llm

        self.output_parser = JsonOutputParser(pydantic_object=ExtractionResult)
        self.prompt = ExtractionPromptTemplate().PROMPT

        self.chain = self.prompt | self.llm | self.output_parser

    async def invoke(
            self,
            messages: List[Dict[str, Any]]
    ) -> ExtractionResult:
        """异步提取实体"""
        if not messages:
            return ExtractionResult()

        lines = []
        for m in messages:
            nickname = m.get('sender_nickname', '未知')
            content = cq_filter(m.get('raw_message', ''))

            if content and content.strip():
                lines.append(f"{nickname}: {content.strip()}")

        if not lines:
            return ExtractionResult()
        messages_text = "\n".join(lines)

        try:
            result_data = await self.chain.ainvoke({
                "messages": messages_text,
                "format_instructions": self.output_parser.get_format_instructions()
            })

            if isinstance(result_data, dict):
                return ExtractionResult(**result_data)
            elif isinstance(result_data, ExtractionResult):
                return result_data

            return ExtractionResult()

        except Exception as e:
            print(f"ExtractionChain 运行异常: {e}")
            print(f"当前输入文本长度: {len(messages_text)}")
            return ExtractionResult()