from typing import TypedDict, List, Dict, Literal, Any


class SummaryState(TypedDict):
    """摘要生成工作流状态。"""

    group_id: int
    hours: int
    raw_messages: List[Dict]
    filtered_messages: List[Dict]
    token_count: int
    selected_model: str
    memory_context: str
    summary: str
    topics: List[Any]
    metadata: Dict
    refresh_mode: Literal["high", "delta", "low"]
    cache_hit: bool
    cache_similarity: float

