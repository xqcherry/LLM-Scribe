"""记忆压缩链"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import List


class CompressionChain:
    """记忆压缩链，用于压缩旧记忆"""
    
    def __init__(self, llm):
        self.llm = llm
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个记忆压缩助手。
请将多段历史摘要压缩成一段简洁的摘要，保留关键信息：
1. 保留重要的概念和事件
2. 去除重复信息
3. 保持时间顺序
4. 压缩后的摘要应该比原文更简洁但信息量不丢失"""),
            ("human", "历史摘要：\n{summaries}\n\n请生成压缩后的摘要：")
        ])
        
        self.chain = prompt | self.llm | StrOutputParser()
    
    async def invoke(self, summaries: List[str]) -> str:
        """压缩摘要"""
        summaries_text = "\n\n---\n\n".join(summaries)
        result = await self.chain.ainvoke({"summaries": summaries_text})
        return result
