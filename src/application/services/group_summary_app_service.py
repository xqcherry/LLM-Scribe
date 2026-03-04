"""
群聊摘要应用服务。

目前作为对 `SummaryGraph` 的薄封装，不改变任何业务行为，
仅提供一个语义清晰的用例入口
"""

from src.application.graph.summary_graph import SummaryGraph


class GroupSummaryApplicationService:
    """面向上层（如 bot 插件）的应用服务接口。"""

    def __init__(self, graph: SummaryGraph | None = None) -> None:
        # 默认直接使用现有的 SummaryGraph，实现零行为变化
        self._graph = graph or SummaryGraph()

    async def summarize_group(self, group_id: int, hours: int) -> str:
        """
        生成群聊摘要文本。

        当前实现直接委托给 `SummaryGraph.invoke`，保持现有逻辑与输出不变。
        """
        return await self._graph.invoke(group_id, hours)

