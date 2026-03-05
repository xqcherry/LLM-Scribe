import asyncio
import base64
import os, re

import aiohttp
from loguru import logger
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
from datetime import datetime

from src.infrastructure.reporting.data_adapter import data_adapter
from src.infrastructure.reporting.html_render import HTMLRenderer
from src.infrastructure.reporting.templates import HTMLTemplates


class ReportGenerator:
    """报告生成器：负责业务逻辑调度、胶囊映射与最终渲染"""

    def __init__(
            self,
            html_renderer: HTMLRenderer,
            template_name: str = "default",
            template_file: str = "default.html",
    ):
        self.template_name = template_name
        self.template_file = template_file
        self.html_templates = HTMLTemplates(template_name)
        self.html_renderer = html_renderer

        # 路径配置
        current_dir = Path(os.path.abspath(__file__)).parent
        self.avatar_cache_dir = current_dir / "cache" / "avatars"
        self.avatar_cache_dir.mkdir(parents=True, exist_ok=True)


    async def generate_image_report(
            self,
            summary_result: Dict[str, Any],
            group_id: str,
            avatar_getter: Optional[Callable] = None,
            nickname_getter: Optional[Callable] = None,
    ) -> Tuple[Optional[bytes], str]:
        """生成图片格式分析报告"""

        if not self.html_renderer:
            logger.error("HTML 渲染器未初始化")
            return None, ""

        try:
            # 1. 调用数据适配器
            render_data = data_adapter(summary_result, group_id)

            # 2. 处理话题详情
            render_payload = await self._prepare_render_payload(
                render_data,
                avatar_getter,
                nickname_getter
            )

            # 3. 使用 HTMLTemplates 进行异步渲染
            html_content = await self.html_templates.render_async(self.template_file, **render_payload)

            # 4. 调用 HTMLRenderer 进行渲染
            image_bytes = await self.html_renderer.html_render_to_img(
                html_content,
                img_opt={
                    "type": "jpeg",
                    "quality": 95,
                    "width": 750,
                    "full_page": True
                }
            )

            return image_bytes, html_content

        except Exception as e:
            logger.error(f"生成图片报告链路失败: {e}", exc_info=True)
            return None, ""


    async def _prepare_render_payload(
        self,
        render_data: Dict[str, Any],
        avatar_getter: Optional[Callable],
        nickname_getter: Optional[Callable],
    ) -> Dict[str, Any]:
        """增强数据：处理话题列表、胶囊映射和图表数据"""
        # 处理话题：遍历话题详情，将 [ID] 替换为 HTML 胶囊
        topics = render_data.get("topics", [])
        for topic in topics:
            raw_detail = topic.get("detail", "")
            # 注入胶囊
            topic["detail_html"] = await self._inject_capsules(
                raw_detail,
                avatar_getter,
                nickname_getter
            )

        # 注入环境变量和元数据
        payload = {
            **render_data,
            "render_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "base_path": f"file://{self.html_templates.template_dir}/",  # 用于模板内引用本地资源
            "template_name": self.template_name
        }

        return payload


    async def _inject_capsules(
            self,
            text: str,
            avatar_getter: Callable,
            nickname_getter: Callable
    ) -> str:
        """识别 [ID] 并转换为 HTML 胶囊"""

        pattern = r"\[(\d+)\]"
        matches = list(re.finditer(pattern, text))
        if not matches:
            return text

        # 异步收集所有用户信息，避免循环中等待
        user_ids = list(set(m.group(1) for m in matches))

        # 并发获取头像昵称
        tasks = [self._get_user_card(uid, avatar_getter, nickname_getter) for uid in user_ids]
        results = await asyncio.gather(*tasks)
        user_info_map = dict(zip(user_ids, results))

        # 从后往前替换文本,防止偏移
        result_html = text
        for match in reversed(matches):
            uid = match.group(1)
            info = user_info_map.get(uid)

            capsule_html = (
                f'<span class="user-capsule">'
                f'<img src="{info["avatar"]}" class="capsule-avatar">'
                f'<span class="capsule-name">{info["nickname"]}</span>'
                f'</span>'
            )
            start, end = match.span()
            result_html = result_html[:start] + capsule_html + result_html[end:]

        return result_html


    async def _get_user_card(
            self,
            user_id: str,
            a_getter: Callable,
            n_getter: Callable
    ) -> Dict[str, str]:
        """获取用户头像昵称"""

        # 昵称
        nickname = str(user_id)
        if n_getter:
            try:
                res = await asyncio.wait_for(n_getter(user_id), timeout=3.0)
                if res and not self._is_placeholder_display_name(res, user_id):
                    nickname = str(res)
            except asyncio.TimeoutError:
                logger.warning(f"获取昵称超时 [User: {user_id}]")
            except Exception as e:
                logger.debug(f"获取昵称失败 [User: {user_id}], Error: {type(e).__name__}: {e}")

        # 头像
        avatar_b64 = await self._get_user_avatar_base64(user_id, a_getter)

        result = {
            "nickname": nickname,
            "avatar": avatar_b64
        }
        return result


    async def _get_user_avatar_base64(self, user_id: str, getter: Callable) -> str:
        """带缓存的头像获取"""
        cache_file = self.avatar_cache_dir / f"{user_id}.png"

        # 1. 命中缓存
        if cache_file.exists():
            data = cache_file.read_bytes()
            return f"data:image/png;base64,{base64.b64encode(data).decode()}"

        # 2. 获取 URL (优先使用 getter，后备 QQ)
        url = None
        if getter:
            url = await getter(user_id)
        if not url and user_id.isdigit():
            url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=100"

        # 3. 下载并存缓存
        if url:
            try:
                async with aiohttp.ClientSession() as sess:
                    async with sess.get(url, timeout=5) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            cache_file.write_bytes(content)
                            return f"data:image/png;base64,{base64.b64encode(content).decode()}"
            except Exception as e:
                logger.warning(f"下载头像失败 {user_id}: {e}")

        # 4. 默认头像
        return "data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMTAwIDEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI1MCIgZmlsbD0iI2RkZCIvPjwvc3ZnPg=="


    @staticmethod
    def _is_placeholder_display_name(name: str, user_id: str) -> bool:
        return name.strip() in {user_id, "Unknown", "None", ""}
