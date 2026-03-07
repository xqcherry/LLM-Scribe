from typing import Any, Dict, List, TypedDict

from src.domain.entities.analysis import ConversationAnalysisResult


class SummaryState(TypedDict):
    """摘要生成工作流状态。"""

    group_id: int
    hours: int
    raw_messages: List[Dict[str, Any]]
    filtered_messages: List[Dict[str, Any]]
    nickname_map: Dict[str, str]
    token_count: int
    selected_model: str
    summary: str
    topics: List[Any]
    analysis: ConversationAnalysisResult
    metadata: Dict[str, Any]
