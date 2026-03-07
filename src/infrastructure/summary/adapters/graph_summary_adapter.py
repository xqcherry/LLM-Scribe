from __future__ import annotations

from src.application.ports.summary_generator_port import SummaryGeneratorPort
from src.domain.entities.analysis import ConversationAnalysisResult
from src.domain.entities.summary import TopicSummary
from src.domain.entities.summary_result import SummaryContext, SummaryResult
from src.infrastructure.summary.graph.summary_graph import SummaryGraph


class GraphSummaryAdapter(SummaryGeneratorPort):
    """基于 SummaryGraph 的摘要生成适配器。"""

    def __init__(self, graph: SummaryGraph | None = None) -> None:
        self._graph = graph or SummaryGraph()

    async def generate_summary(self, group_id: int, hours: int) -> SummaryResult:
        result = await self._graph.invoke(group_id, hours)

        raw_topics = result.get("topics", []) or []
        topics = [
            t if isinstance(t, TopicSummary) else TopicSummary.model_validate(t)
            for t in raw_topics
        ]

        raw_analysis = result.get("analysis")
        if isinstance(raw_analysis, ConversationAnalysisResult):
            analysis = raw_analysis
        elif raw_analysis:
            analysis = ConversationAnalysisResult.model_validate(raw_analysis)
        else:
            analysis = ConversationAnalysisResult(group_id=group_id)

        return SummaryResult(
            context=SummaryContext(group_id=group_id, hours=hours),
            summary_text=result.get("summary", ""),
            topics=topics,
            analysis=analysis,
            nickname_map=result.get("nickname_map", {}) or {},
        )
