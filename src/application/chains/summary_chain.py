from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import List, Dict

from src.domain.entities.summary import SummaryOutput
from src.domain.prompts import SummaryPromptTemplate
from src.infrastructure.pipeline.detail.format_messages import format_messages


class SummaryChain:
    """摘要生成链"""

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


    async def invoke(
        self,
        messages: List[Dict],
        memory_context: str = "",
    ) -> SummaryOutput:

        messages_text = format_messages(messages)

        if not messages_text:
            # 如果没有有效消息，返回空话题列表
            return SummaryOutput(topics=[])

        result = await self.chain.ainvoke(
            {
                "messages_text": messages_text,
                "memory_context": memory_context,
            }
        )

        return result

