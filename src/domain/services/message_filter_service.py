"""
消息过滤领域服务。

目前内部仍然委托给 `pipeline.cq_filter.filter_msgs`，只是为其提供
一个领域层语义包装，便于后续替换实现或复用。
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.config import plugin_config as config
from src.infrastructure.pipeline.cq_filter import filter_msgs


class MessageFilterService:
    """负责对原始群消息进行噪音过滤与清洗。"""

    @staticmethod
    def filter(raw_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return filter_msgs(raw_messages, config.ignore_qq)

