from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough

from ....domain.entities.summary import SummaryOutput
from ...prompts import SummaryPromptTemplate


class SummaryChain:
    """摘要生成链：接收已格式化的消息文本，输出结构化话题摘要。"""

    def __init__(self, llm, max_topics: int = 5):
        self.llm = llm
        self.max_topics = max_topics
        self.prompt_template = SummaryPromptTemplate(max_topics=max_topics)
        self.output_parser = PydanticOutputParser(pydantic_object=SummaryOutput)

        self.chain = (
            RunnablePassthrough()
            | self.prompt_template.prompt
            | self.llm
            | self.output_parser
        )

    async def invoke(self, messages_text: str, memory_context: str = "") -> SummaryOutput:
        if not messages_text:
            return SummaryOutput(topics=[])

        result = await self.chain.ainvoke(
            {
                "messages_text": messages_text,
                "memory_context": memory_context,
            }
        )

        result.topics = [
            t
            for t in result.topics
            if (getattr(t, "topic", "") or "").strip()
            or (getattr(t, "detail", "") or "").strip()
        ]

        return result
