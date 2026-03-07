from __future__ import annotations

from typing import Optional

from src.application.ports.report_renderer_port import (
    AvatarGetter,
    NicknameGetter,
    ReportRendererPort,
)
from src.domain.entities.summary_result import SummaryResult
from src.infrastructure.reporting.generators import ReportGenerator
from src.infrastructure.reporting.html_render import HTMLRenderer


class HtmlReportAdapter(ReportRendererPort):
    """基于 HTML 渲染器的报告适配器。"""

    def __init__(self, report_generator: ReportGenerator | None = None) -> None:
        self._report_generator = report_generator or ReportGenerator(
            html_renderer=HTMLRenderer(),
            template_name="default",
            template_file="default.html",
        )

    async def render_summary_image(
        self,
        summary_result: SummaryResult,
        avatar_getter: AvatarGetter | None = None,
        nickname_getter: NicknameGetter | None = None,
    ) -> Optional[bytes]:
        image_bytes, _ = await self._report_generator.generate_image_report(
            summary_result=summary_result,
            avatar_getter=avatar_getter,
            nickname_getter=nickname_getter,
        )
        return image_bytes
