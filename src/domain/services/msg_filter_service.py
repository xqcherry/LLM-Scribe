from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class MessageFilterInterface(ABC):
    """定义消息处理的契约，规定了如何从原始数据中提取有效信息。"""

    @abstractmethod
    def filter_and_clean(
            self,
            raw_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """清洗原始消息列表并返回结构化 Dict。"""
        pass

class MessageFilter:
    """
    领域服务：消息清洗的统一入口。
    """

    def __init__(self, processor: MessageFilterInterface | None = None):
        if processor:
            self._processor = processor
        else:
            from src.infrastructure.pipeline.msg_filter_impl import MessageFilterImpl
            self._processor = MessageFilterImpl()

    def get_cleaned_messages(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        业务逻辑入口：执行黑名单过滤、CQ码转换和噪音剔除。
        返回干干净净的过滤信息（List[Dict]）
        """
        if not raw_data:
            return []
        return self._processor.filter_and_clean(raw_data)