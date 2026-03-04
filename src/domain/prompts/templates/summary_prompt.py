from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.domain.entities.summary import SummaryOutput


class SummaryPromptTemplate:
    """摘要提示词模板"""

    BASE_SYSTEM_PROMPT = """你是一个专业的群聊记录深度分析专家。
        请根据提供的聊天内容，将其拆解为若干个独立的话题区块，并进行结构化提取。

        核心任务：
        1. **识别独立话题**：将讨论内容按事件、项目或决策划分为不同话题。每个话题应具有完整性。
        2. **精炼话题摘要**：每个话题的 summary 字段要包含：[讨论背景] + [核心观点/争议] + [最终结论/行动项]。
        3. **参与者映射**：在每个话题中列出积极参与该讨论的成员昵称，必须使用真实昵称。
        4. **捕捉精彩瞬间**：从原始对话中筛选出 1-2 句最能体现群内氛围、有梗或有深度的原话。

        写作风格要求：
        - 摘要内容要干练，杜绝“大家讨论了...”这种废话，直接写讨论的具体内容。
        - 话题标题（topic）要具有吸引力且准确。
        - 严禁虚构事实，如果某个话题没有结论，请如实描述。"""

    def __init__(self):
        self.output_parser = PydanticOutputParser(pydantic_object=SummaryOutput)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.BASE_SYSTEM_PROMPT + "\n\n{format_instructions}"),
                ("human", "聊天内容：\n{messages}\n\n历史上下文：\n{memory_context}"),
            ]
        ).partial(
            format_instructions=self.output_parser.get_format_instructions()
        )

    def format(
        self,
        messages: str,
        memory_context: str = "",
    ) -> list:
        """格式化提示词"""
        return self.prompt.format_messages(
            messages=messages,
            memory_context=memory_context or "无历史上下文",
        )
