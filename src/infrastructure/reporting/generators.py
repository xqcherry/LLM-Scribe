import asyncio
import base64
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import aiohttp
from loguru import logger

from ...domain.entities.summary_result import SummaryResult
from .data_adapter import data_adapter
from .html_render import HTMLRenderer
from .templates import HTMLTemplates


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
        """增强数据：并发解析胶囊为结构化片段，HTML 结构交给模板渲染"""

        topics = render_data.get("topics", [])
        if not topics:
            logger.warning("⚠️ _prepare_render_payload: 接收到的 topics 为空")

        async def process_single_topic(topic):
            raw_detail = topic.get("detail", "")
            topic["detail_segments"] = await self._build_detail_segments(
                raw_detail,
                avatar_getter,
                nickname_getter,
                nickname_map=nickname_map,
            )

            participants = topic.get("participants", []) or []
            topic["participants_resolved"] = await self._resolve_participants(
                participants,
                avatar_getter,
                nickname_getter,
                nickname_map=nickname_map,
            )
            return topic

        # 并发处理所有话题的胶囊解析
        if topics:
            await asyncio.gather(*[process_single_topic(t) for t in topics])

        hourly = (
            render_data.get("statistics", {})
            .get("activity_visualization", {})
            .get("hourly_activity")
        )
        activity_chart = self._build_activity_chart(hourly)

        payload = {
            **render_data,
            "render_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "base_path": f"file://{self.html_templates.template_dir}/",
            "template_name": self.template_name,
            "activity_chart": activity_chart,
        }

        logger.info(f"✅ Payload 准备就绪，包含 {len(payload.get('topics', []))} 个已注入胶囊的话题")

        return payload


    async def _build_detail_segments(
            self,
            text: str,
            avatar_getter: Optional[Callable],
            nickname_getter: Optional[Callable],
            nickname_map: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """识别 [ID] 并将正文切分为 文本段 / 胶囊段，结构交给模板渲染"""

        matches = list(re.finditer(r"\[(\d+)\]", text))
        if not matches:
            return [{"type": "text", "content": text}] if text else []

        user_ids = list({m.group(1) for m in matches})
        tasks = [
            self._get_user_card(uid, avatar_getter, nickname_getter, nickname_map=nickname_map)
            for uid in user_ids
        ]
        results = await asyncio.gather(*tasks)
        user_info_map = dict(zip(user_ids, results))

        segments: List[Dict[str, Any]] = []
        last = 0
        for m in matches:
            if m.start() > last:
                segments.append({"type": "text", "content": text[last:m.start()]})
            uid = m.group(1)
            info = user_info_map.get(uid)
            if info:
                segments.append({
                    "type": "capsule",
                    "user_id": uid,
                    "avatar": info["avatar"],
                    "nickname": info["nickname"],
                })
            else:
                segments.append({"type": "text", "content": m.group(0)})
            last = m.end()
        if last < len(text):
            segments.append({"type": "text", "content": text[last:]})
        return segments


    async def _resolve_participants(
            self,
            participants: list,
            avatar_getter: Optional[Callable],
            nickname_getter: Optional[Callable],
            nickname_map: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, str]]:
        """将参与者 ID 列表解析为 [{avatar, nickname}]，结构交给模板渲染"""

        if not participants:
            return []

        user_ids: List[str] = []
        for uid in participants:
            uid_str = str(uid).strip()
            if uid_str and uid_str not in user_ids:
                user_ids.append(uid_str)

        if not user_ids:
            return []

        tasks = [
            self._get_user_card(uid, avatar_getter, nickname_getter, nickname_map=nickname_map)
            for uid in user_ids
        ]
        infos = await asyncio.gather(*tasks)
        return [{"avatar": info["avatar"], "nickname": info["nickname"]} for info in infos]


    async def _get_user_card(
            self,
            user_id: str,
            a_getter: Optional[Callable],
            n_getter: Optional[Callable],
            nickname_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """获取用户头像昵称；昵称不再在此处转义，交由模板 autoescape 统一处理"""

        user_id_str = str(user_id)
        nickname = user_id_str  # 初始兜底方案

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

        return {"nickname": nickname, "avatar": avatar_b64}


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

    @staticmethod
    def _build_activity_chart(
            hourly_activity: Optional[list],
            width: int = 600,
            height: int = 92,
            pad: int = 6,
    ) -> Dict[str, Any]:
        """将 24 点活跃分布转为 SVG 平滑面积图路径（Catmull-Rom -> 三次贝塞尔）"""

        vals = list(hourly_activity) if hourly_activity else []
        if len(vals) < 2:
            vals = (vals + [0] * 24)[:24]
        n = len(vals)
        mx = max(vals) if vals else 0
        inner_w = width - 2 * pad
        inner_h = height - 2 * pad

        def pt(i: int) -> tuple:
            x = pad + i * inner_w / (n - 1)
            v = (vals[i] / mx) if mx > 0 else 0
            y = (height - pad) - v * inner_h
            return (x, y)

        pts = [pt(i) for i in range(n)]

        line = f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"
        for i in range(n - 1):
            p0 = pts[i - 1] if i > 0 else pts[0]
            p1 = pts[i]
            p2 = pts[i + 1]
            p3 = pts[i + 2] if i + 2 < n else pts[-1]
            c1x = p1[0] + (p2[0] - p0[0]) / 6
            c1y = p1[1] + (p2[1] - p0[1]) / 6
            c2x = p2[0] - (p3[0] - p1[0]) / 6
            c2y = p2[1] - (p3[1] - p1[1]) / 6
            line += f" C {c1x:.2f} {c1y:.2f} {c2x:.2f} {c2y:.2f} {p2[0]:.2f} {p2[1]:.2f}"

        fill = line + f" L {pts[-1][0]:.2f} {height - pad:.2f} L {pts[0][0]:.2f} {height - pad:.2f} Z"

        if mx > 0:
            peak_idx = vals.index(mx)
            peak = {"x": round(pts[peak_idx][0], 2), "y": round(pts[peak_idx][1], 2), "label": f"{peak_idx:02d}:00"}
        else:
            peak = None

        marks = [
            {"x": round(pts[i][0], 2), "label": f"{i:02d}"}
            for i in range(n) if i in (0, 6, 12, 18, 23)
        ]
        return {
            "line_path": line,
            "fill_path": fill,
            "peak": peak,
            "marks": marks,
            "width": width,
            "height": height,
        }
