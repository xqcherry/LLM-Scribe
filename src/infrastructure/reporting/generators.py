import asyncio
import base64
import html
import os, re

import aiohttp
from loguru import logger
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
from datetime import datetime

from src.domain.entities.summary_result import SummaryResult
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
            summary_result: SummaryResult,
            avatar_getter: Optional[Callable] = None,
            nickname_getter: Optional[Callable] = None,
    ) -> Tuple[Optional[bytes], str]:
        """生成图片格式分析报告"""

        if not self.html_renderer:
            logger.error("HTML 渲染器未初始化")
            return None, ""

        try:
            # 1. 调用数据适配器
            render_data = data_adapter(summary_result)

            # 2. 处理话题详情
            nickname_map = summary_result.nickname_map
            render_payload = await self._prepare_render_payload(
                render_data,
                avatar_getter,
                nickname_getter,
                nickname_map = nickname_map
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
            nickname_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """增强数据：并发处理胶囊映射"""

        # 1. 提取话题
        topics = render_data.get("topics", [])
        if not topics:
            logger.warning("⚠️ _prepare_render_payload: 接收到的 topics 为空")
            return render_data

        # 2. 【核心优化】并发处理所有话题的胶囊注入
        async def process_single_topic(topic):
            raw_detail = topic.get("detail", "")
            topic["detail_html"] = await self._inject_capsules(
                raw_detail,
                avatar_getter,
                nickname_getter,
                nickname_map=nickname_map
            )

            participants = topic.get("participants", []) or []
            topic["participants_html"] = await self._render_participants_capsules(
                participants,
                avatar_getter,
                nickname_getter,
                nickname_map=nickname_map,
            )
            return topic

        # 使用 asyncio.gather 并发执行
        await asyncio.gather(*[process_single_topic(t) for t in topics])

        # 3. 注入环境变量和元数据
        payload = {
            **render_data,
            "render_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "base_path": f"file://{self.html_templates.template_dir}/",
            "template_name": self.template_name
        }

        logger.info(f"✅ Payload 准备就绪，包含 {len(payload.get('topics', []))} 个已注入胶囊的话题")

        return payload


    async def _inject_capsules(
            self,
            text: str,
            avatar_getter: Optional[Callable],
            nickname_getter: Optional[Callable],
            nickname_map: Optional[Dict[str, str]] = None,
    ) -> str:
        """识别 [ID] 并转换为 HTML 胶囊"""

        pattern = r"\[(\d+)\]"
        matches = list(re.finditer(pattern, text))
        if not matches:
            return text

        # 异步收集所有用户信息，避免循环中等待
        user_ids = list(set(m.group(1) for m in matches))

        # 并发获取头像昵称
        tasks = [
            self._get_user_card(
                uid,
                avatar_getter,
                nickname_getter,
                nickname_map=nickname_map
            )
            for uid in user_ids
        ]
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


    async def _render_participants_capsules(
            self,
            participants: list,
            avatar_getter: Optional[Callable],
            nickname_getter: Optional[Callable],
            nickname_map: Optional[Dict[str, str]] = None,
    ) -> str:
        """将参与者列表渲染为胶囊 HTML"""
        if not participants:
            return ""

        user_ids = []
        for uid in participants:
            uid_str = str(uid).strip()
            if uid_str and uid_str not in user_ids:
                user_ids.append(uid_str)

        if not user_ids:
            return ""

        tasks = [
            self._get_user_card(
                uid,
                avatar_getter,
                nickname_getter,
                nickname_map=nickname_map,
            )
            for uid in user_ids
        ]
        infos = await asyncio.gather(*tasks)

        capsules = []
        for info in infos:
            capsules.append(
                f'<span class="user-capsule">'
                f'<img src="{info["avatar"]}" class="capsule-avatar">'
                f'<span class="capsule-name">{info["nickname"]}</span>'
                f'</span>'
            )

        return "".join(capsules)


    async def _get_user_card(
            self,
            user_id: str,
            a_getter: Optional[Callable],
            n_getter: Optional[Callable],
            nickname_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """获取用户头像昵称：统一转义与短路优化版"""

        user_id_str = str(user_id)
        nickname = user_id_str  # 初始兜底方案

        # 记录是否已经从可靠来源获取了昵称，用于短路判断
        found_reliable_name = False

        # 1. 尝试从 nickname_map 获取
        if nickname_map:
            mapped = nickname_map.get(user_id_str)
            if mapped and not self._is_placeholder_display_name(str(mapped), user_id_str):
                nickname = str(mapped)
                found_reliable_name = True

        # 2. 如果 map 没中，再尝试 n_getter
        if not found_reliable_name and n_getter:
            try:
                res = await asyncio.wait_for(n_getter(user_id_str), timeout=3.0)
                if res and not self._is_placeholder_display_name(str(res), user_id_str):
                    nickname = str(res)
            except asyncio.TimeoutError:
                logger.warning(f"获取昵称超时 [User: {user_id_str}]")
            except Exception as e:
                logger.debug(f"获取昵称失败 [User: {user_id_str}], Error: {type(e).__name__}: {e}")

        # 3. 统一获取头像
        avatar_b64 = await self._get_user_avatar_base64(user_id_str, a_getter)

        return {
            "nickname": html.escape(nickname),
            "avatar": avatar_b64
        }


    async def _get_user_avatar_base64(self, user_id: str, getter: Optional[Callable]) -> str:
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
