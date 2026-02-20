"""摘要生成链"""
from langchain.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import List, Dict
from ..models.summary import SummaryOutput
from ...prompts.templates import SummaryPromptTemplate


class SummaryChain:
    """摘要生成链"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt_template = SummaryPromptTemplate()
        self.output_parser = PydanticOutputParser(pydantic_object=SummaryOutput)
        
        # 构建链
        self.chain = (
            RunnablePassthrough()
            | self.prompt_template.prompt
            | self.llm
            | self.output_parser
        )
    
    async def invoke(
        self,
        messages: List[Dict],
        memory_context: str = ""
    ) -> SummaryOutput:
        """生成摘要"""
        # 格式化消息
        messages_text = "\n".join(
            f"{m.get('sender_nickname', '')}: {m.get('raw_message', '')}"
            for m in messages
        )
        
        # 调用链
        result = await self.chain.ainvoke({
            "messages": messages_text,
            "memory_context": memory_context
        })
        
        return result
