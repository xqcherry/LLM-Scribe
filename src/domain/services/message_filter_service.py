from __future__ import annotations

from typing import Any, Dict, List

from src.config import plugin_config as config
from src.infrastructure.pipeline.cq_filter import filter_msgs


class MessageFilterService:
    """负责对原始群消息进行噪音过滤与清洗。"""

    @staticmethod
    def filter(raw_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return filter_msgs(raw_messages, config.ignore_qq)

