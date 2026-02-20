"""实体提取链"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import List, Dict
from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    """提取结果"""
    concepts: List[str] = Field(description="关键概念列表")
    events: List[str] = Field(description="重要事件列表")
    quotes: List[str] = Field(description="关键引用列表")


class ExtractionChain:
    """实体提取链"""
    
    def __init__(self, llm):
        self.llm = llm
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个信息提取助手。
请从聊天内容中提取：
1. 关键概念（关键词、主题）
2. 重要事件（发生的事情）
3. 关键引用（有代表性的发言）

输出格式为 JSON：
{
    "concepts": ["概念1", "概念2"],
    "events": ["事件1", "事件2"],
    "quotes": ["引用1", "引用2"]
}"""),
            ("human", "聊天内容：\n{messages}")
        ])
        
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
        except:
            # 如果解析失败，返回空结果
            return ExtractionResult()
