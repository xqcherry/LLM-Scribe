from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from ....domain.entities.summary import SummaryOutput


class SummaryPromptTemplate:
    """摘要提示词模板"""

    BASE_SYSTEM_PROMPT = """你是一个帮我进行群聊信息总结的助手，生成总结内容时，你需要严格遵守下面的几个准则：
    请分析接下来提供的群聊记录，提取出最多 **{max_topics}** 个主要话题。根据实际聊天内容提取所有最有意义的话题。
    
    ## 对于每个话题，请提供：
    
    1. **话题名称**（突出主题内容，尽量简明扼要，控制在 10 字以内）
    2. **主要参与者的用户ID**（最多 5 人，按参与度排序）
    3. **话题详细描述**（包含关键信息和结论）
    
    ## 注意事项：
    
    - 对于比较有价值的点，稍微用一两句话详细讲讲，让读者能了解讨论的深度
    - 对于其中的部分信息，你需要特意提到主题施加的主体是谁，即明确指出"谁做了什么"
    - **用户引用**：在话题详情描述中，如果提到了具体用户，请使用 `[用户ID]` 的格式来指代（例如 `[123456]`）。不要只写昵称。我们会自动渲染头像。
    - 对于每一条总结，尽量讲清楚前因后果，不要只列出结论
    - 如果某个话题有明确的结论或共识，请在描述中体现
    - 忽略无意义的闲聊、灌水、单纯的表情回复等
    - 优先选择讨论深度较深、参与人数较多的话题
    - 如果消息太少或没有明确话题，可以返回空数组 []
    
    {format_instructions}"""

    def __init__(self, max_topics: int = 5):

        self.max_topics = max_topics
        self.output_parser = PydanticOutputParser(pydantic_object=SummaryOutput)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.BASE_SYSTEM_PROMPT),
                ("human", "群聊记录：\n{messages_text}\n\n历史上下文：\n{memory_context}"),
            ]
        ).partial(
            format_instructions=self.output_parser.get_format_instructions(),
            max_topics=max_topics,
        )

    def format(
        self,
        messages_text: str,
        memory_context: str = "",
    ) -> list:
        """格式化提示词"""
        return self.prompt.format_messages(
            messages_text=messages_text,
            memory_context=memory_context or "无历史上下文",
        )
