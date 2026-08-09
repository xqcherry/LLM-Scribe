from langchain_core.prompts import ChatPromptTemplate


class ExtractionPromptTemplate:
    """分块信息提取提示词模板：从单块聊天提取关键信息用于后续汇总。"""

    PROMPT = ChatPromptTemplate.from_messages([
        ("system", """你是一个信息提取助手。请从下面这段群聊片段中提取关键信息，用于后续汇总：
1. 关键概念与主题（关键词）
2. 重要事件（发生了什么、谁做了什么、结论是什么）
3. 有代表性的发言要点

要求：
- 用简洁的条目式文本输出，不要额外寒暄
- 提到具体用户时使用 [用户ID] 格式
- 保留关键事实与因果，去掉灌水和无意义闲聊
- 如果片段内容空洞，输出"（无有效信息）" """),
        ("human", "群聊片段：\n{messages}")
    ])

    def format(self, messages: str) -> list:
        """格式化提示词"""
        return self.PROMPT.format_messages(messages=messages)
