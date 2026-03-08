from __future__ import annotations

from typing import Optional

from ..ports.report_renderer_port import (
    AvatarGetter,
    NicknameGetter,
    ReportRendererPort,
)
from ..ports.summary_generator_port import SummaryGeneratorPort
from ...domain.entities.summary_result import SummaryResult
from ...infrastructure.reporting.adapters.html_report_adapter import HtmlReportAdapter
from ...infrastructure.summary.adapters.graph_summary_adapter import GraphSummaryAdapter


class SummaryReportApplicationService:
    """主链门面：摘要生成 + 报告渲染。"""

    def __init__(
        self,
        summary_generator: SummaryGeneratorPort | None = None,
        report_renderer: ReportRendererPort | None = None,
    ) -> None:
        self._summary_generator = summary_generator or GraphSummaryAdapter()
        self._report_renderer = report_renderer or HtmlReportAdapter()

    async def summarize_group(self, group_id: int, hours: int) -> SummaryResult:
        return await self._summary_generator.generate_summary(group_id, hours)

    async def summarize_and_render_image(
        self,
        group_id: int,
        hours: int,
        avatar_getter: AvatarGetter | None = None,
        nickname_getter: NicknameGetter | None = None,
    ) -> tuple[SummaryResult, Optional[bytes]]:
        summary_result = await self.summarize_group(group_id, hours)
        image_bytes = await self._report_renderer.render_summary_image(
            summary_result=summary_result,
            avatar_getter=avatar_getter,
            nickname_getter=nickname_getter,
        )
        return summary_result, image_bytes
