"""实体提取提示词模板"""
from langchain_core.prompts import ChatPromptTemplate


class ExtractionPromptTemplate:
    """实体提取提示词模板"""
    
    PROMPT = ChatPromptTemplate.from_messages([
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
    
    def format(self, messages: str) -> list:
        """格式化提示词"""
        return self.PROMPT.format_messages(messages=messages)
