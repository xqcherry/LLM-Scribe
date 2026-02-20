from langchain_core.prompts import ChatPromptTemplate


class CompressionPromptTemplate:
    """记忆压缩提示词模板"""
    
    PROMPT = ChatPromptTemplate.from_messages([
        ("system", """你是一个记忆压缩助手。
            请将多段历史摘要压缩成一段简洁的摘要，保留关键信息：
            1. 保留重要的概念和事件
            2. 去除重复信息
            3. 保持时间顺序
            4. 压缩后的摘要应该比原文更简洁但信息量不丢失"""),
        ("human", "历史摘要：\n{summaries}\n\n请生成压缩后的摘要：")
    ])
    
    def format(self, summaries: str) -> list:
        """格式化提示词"""
        return self.PROMPT.format_messages(summaries=summaries)
