from typing import Any, List, Dict, Set

from src.application.ports.message_filter_port import MessageFilterPort
from src.config import plugin_config
from src.infrastructure.message_processing.filters.cq_filter import cq_filter


class MessageFilterImpl(MessageFilterPort):
    """MessageFilterInterface 的具体实现，执行物理过滤与内容清洗"""

    def __init__(self):
        # 从配置中读取黑名单
        self.ignore_ids: Set[int] = getattr(plugin_config, "ignore_qq", set())
        # 预定义指令前缀
        self.command_prefixes = ("/", "!", ".", "#", "。", "！")

    def filter_and_clean(self, raw_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行过滤流水线：黑名单 -> CQ清洗 -> 长度/指令过滤"""
        if not raw_messages:
            return []

        refined_msgs = []

        for msg in raw_messages:
            # 1. 物理过滤：黑名单用户
            if msg.get("user_id") in self.ignore_ids:
                continue

            # 2. 内容清洗：原子级 CQ 码转义
            raw_text = msg.get("raw_message", "")
            clean_text = cq_filter(raw_text).strip()

            # 3. 业务过滤：剔除过短消息或机器人指令
            if not clean_text or len(clean_text) < 2:
                continue
            if clean_text.startswith(self.command_prefixes):
                continue

            # 4. 结构化保留：克隆 Dict 并替换内容，保留原有的 user_id, time 等元数据
            new_msg = msg.copy()
            new_msg["raw_message"] = clean_text
            refined_msgs.append(new_msg)

        return refined_msgs