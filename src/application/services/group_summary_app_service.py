from src.application.graph.summary_graph import SummaryGraph


class GroupSummaryApplicationService:

    def __init__(self, graph: SummaryGraph | None = None) -> None:
        self._graph = graph or SummaryGraph()

    async def summarize_group(self, group_id: int, hours: int) -> dict:
        """新：返回完整结构化结果"""
        result = await self._graph.invoke(group_id, hours)
        # 这里可以按需只挑你关心的字段
        return {
            "summary_text": result.get("summary", ""),
            "topics": result.get("topics", []),
            "analysis": result.get("metadata", {}).get("analysis_result"),
            "metadata": result.get("metadata", {}),
        }

