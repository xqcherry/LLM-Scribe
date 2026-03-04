from typing import List, Optional

from pydantic import BaseModel, Field


class MemoryState(BaseModel):
    """记忆状态。"""

    last_summary: str = Field(default="")
    last_window_hours: Optional[int] = Field(default=None)
    concepts: List[str] = Field(default_factory=list)
    events: List[str] = Field(default_factory=list)
    quotes: List[str] = Field(default_factory=list)

