from src.application.graph.summary_graph import SummaryGraph
from src.domain.entities.analysis import ConversationAnalysisResult
from src.domain.entities.summary import TopicSummary
from src.domain.entities.summary_result import SummaryContext, SummaryResult


class GroupSummaryApplicationService:

    def __init__(self, graph: SummaryGraph | None = None) -> None:
        self._graph = graph or SummaryGraph()

    async def summarize_group(self, group_id: int, hours: int) -> SummaryResult:
        """返回统一的摘要结果对象。"""
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
