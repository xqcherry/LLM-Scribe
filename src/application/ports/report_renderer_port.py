from __future__ import annotations

from typing import Awaitable, Callable, Optional, Protocol

from ...domain.entities.summary_result import SummaryResult


AvatarGetter = Callable[[str], Awaitable[Optional[str]]]
NicknameGetter = Callable[[str], Awaitable[Optional[str]]]


class ReportRendererPort(Protocol):
    """报告渲染端口：应用层依赖的抽象接口。"""

    async def render_summary_image(
        self,
        summary_result: SummaryResult,
        avatar_getter: AvatarGetter | None = None,
        nickname_getter: NicknameGetter | None = None,
    ) -> Optional[bytes]:
        """将摘要结果渲染为图片字节。"""
        ...
