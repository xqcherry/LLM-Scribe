from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.core.models.summary import SummaryOutput


class SummaryPromptTemplate:
    """摘要提示词模板"""
    
    BASE_SYSTEM_PROMPT = """你是一个专业的群聊摘要助手。
        请分析聊天内容，生成结构化摘要。
        
        要求：
        1. 整体摘要要全面概括群聊的主要内容
        2. 话题总结要清晰分类，每个话题包含相关参与者和关键要点
        3. 关键引用要选择最有代表性的发言
        4. 情感倾向要准确判断整体氛围（positive/neutral/negative）
        5. 使用参与者的真实昵称，不要使用"有的成员"等模糊说法"""

    def __init__(self):
        self.output_parser = PydanticOutputParser(pydantic_object=SummaryOutput)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.BASE_SYSTEM_PROMPT + "\n\n{format_instructions}"),
            ("human", "聊天内容：\n{messages}\n\n历史上下文：\n{memory_context}")
        ]).partial(
            format_instructions=self.output_parser.get_format_instructions()
        )
    
    def format(
        self,
        messages: str,
        memory_context: str = ""
    ) -> list:
        """格式化提示词"""
        return self.prompt.format_messages(
            messages=messages,
            memory_context=memory_context or "无历史上下文"
        )
