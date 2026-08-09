import json
from pathlib import Path
from typing import Optional


class AnchorStore:
    """按群持久化摘要锚点（上次摘要时间 + 压缩摘要），支撑滑动窗口增量合并。"""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        if base_dir is None:
            base_dir = (
                Path(__file__).resolve().parent.parent.parent.parent
                / "data"
                / "summary_anchors"
            )
        self._dir = base_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, group_id: int) -> Path:
        return self._dir / f"{group_id}.json"

    def get(self, group_id: int) -> Optional[dict]:
        p = self._path(group_id)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def save(self, group_id: int, anchor_time: int, compressed_summary: str) -> None:
        data = {"anchor_time": anchor_time, "compressed_summary": compressed_summary}
        self._path(group_id).write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

    def delete(self, group_id: int) -> None:
        p = self._path(group_id)
        if p.exists():
            p.unlink()
