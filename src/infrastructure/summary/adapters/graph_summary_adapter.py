from __future__ import annotations

from ....application.ports.summary_generator_port import SummaryGeneratorPort
from ....domain.entities.analysis import ConversationAnalysisResult
from ....domain.entities.summary import TopicSummary
from ....domain.entities.summary_result import SummaryContext, SummaryResult
from ...cache import TTLCache
from ..graph.summary_graph import SummaryGraph


class GraphSummaryAdapter(SummaryGeneratorPort):
    """基于 SummaryGraph 的摘要生成适配器，带 L1 结果缓存。"""

    def __init__(
        self,
        graph: SummaryGraph | None = None,
        result_cache: TTLCache | None = None,
    ) -> None:
        self._graph = graph or SummaryGraph()
        self._result_cache = result_cache or TTLCache(default_ttl=600.0)

    async def generate_summary(self, group_id: int, hours: int) -> SummaryResult:
        cache_key = f"result:{group_id}:{hours}"

        cached = self._result_cache.get(cache_key)
        if cached is not None:
            return cached

        result = await self._graph.invoke(group_id, hours)
        summary_result = self._build_summary_result(group_id, hours, result)

        if summary_result.topics or summary_result.summary_text:
            self._result_cache.set(cache_key, summary_result)
        return summary_result

    @staticmethod
    def _build_summary_result(group_id: int, hours: int, result: dict) -> SummaryResult:
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
