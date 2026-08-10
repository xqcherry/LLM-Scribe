"""离线预览报告渲染：用已有 SummaryResult JSON 样本验证模板改动。

不依赖数据库，用 mock avatar_getter 避免联网。覆盖：
  - default 主题 / dark 主题
  - 有话题 / 空话题（空状态）
并断言页脚技术指标常显、空状态渲染、胶囊 [ID] 已被切分（无残留）。
"""
from __future__ import annotations

import asyncio
import base64
import json
import sys
from pathlib import Path

# Windows 控制台 emoji 兜底
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.domain.entities.summary_result import SummaryResult
from src.infrastructure.reporting.generators import ReportGenerator
from src.infrastructure.reporting.html_render import HTMLRenderer

SAMPLE_WITH_TOPICS = ROOT / "scripts" / "summary_first_1017750994_24h.json"
SAMPLE_EMPTY_TOPICS = ROOT / "scripts" / "summary_first_913914054_24h.json"
OUT_DIR = ROOT / "scripts" / "preview"

MOCK_AVATAR = (
    "data:image/svg+xml;base64,"
    + base64.b64encode(
        b'<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
        b'<circle cx="50" cy="50" r="50" fill="#cbd5e1"/></svg>'
    ).decode()
)


async def mock_avatar_getter(_uid: str) -> str:
    return MOCK_AVATAR


def load_sample(path: Path) -> SummaryResult:
    with open(path, encoding="utf-8") as f:
        return SummaryResult.model_validate(json.load(f))


async def render_one(
    renderer: HTMLRenderer,
    label: str,
    sample: SummaryResult,
    template_name: str,
) -> tuple[bytes | None, str]:
    gen = ReportGenerator(
        html_renderer=renderer,
        template_name=template_name,
        template_file="default.html",
    )
    img, html_content = await gen.generate_image_report(
        sample, avatar_getter=mock_avatar_getter
    )
    if img:
        (OUT_DIR / f"{label}.jpg").write_bytes(img)
    (OUT_DIR / f"{label}.html").write_text(html_content, encoding="utf-8")
    return img, html_content


def assert_contains(label: str, html: str, needle: str, expected: bool) -> None:
    actual = needle in html
    status = "OK" if actual == expected else "FAIL"
    print(f"  [{status}] {label}: 期望{'含' if expected else '不含'} {needle!r}, 实际{'含' if actual else '不含'}")
    if actual != expected:
        raise AssertionError(f"{label} 断言失败: {needle!r}")


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    renderer = HTMLRenderer()

    with_topics = load_sample(SAMPLE_WITH_TOPICS)
    empty_topics = load_sample(SAMPLE_EMPTY_TOPICS)

    cases = [
        ("default_with_topics", with_topics, "default"),
        ("default_empty", empty_topics, "default"),
        ("dark_with_topics", with_topics, "dark"),
    ]

    results: list[tuple[str, bytes | None, str]] = []
    for label, sample, theme in cases:
        print(f"\n=== 渲染 {label} (主题={theme}) ===")
        try:
            img, html_content = await render_one(renderer, label, sample, theme)
        except Exception as e:
            print(f"  渲染异常: {type(e).__name__}: {e}")
            raise
        img_size = len(img) if img else 0
        print(f"  图片: {img_size} bytes, html: {len(html_content)} chars")
        results.append((label, img, html_content))

    await renderer.close()

    print("\n=== 断言 ===")
    by_label = {r[0]: (r[1], r[2]) for r in results}

    # 页脚技术指标常显（model / tokens / cost）
    assert_contains("default_with_topics/含footer-debug", by_label["default_with_topics"][1], '<div class="footer-debug"', True)
    assert_contains("default_with_topics/含tokens", by_label["default_with_topics"][1], "tokens", True)

    # 空状态
    assert_contains("default_empty/空状态应渲染", by_label["default_empty"][1], '<div class="empty-state">', True)
    assert_contains("default_with_topics/不应有空状态", by_label["default_with_topics"][1], '<div class="empty-state">', False)

    # 胶囊解耦：正文 [数字] 应被切分为 mention（含头像），html 不应残留原始 [QQ号]
    assert_contains("default_with_topics/无[ID]残留", by_label["default_with_topics"][1], "[2986325137]", False)
    assert_contains("default_with_topics/含mention", by_label["default_with_topics"][1], '<span class="mention"', True)
    assert_contains("default_with_topics/mention含头像", by_label["default_with_topics"][1], '<img class="mention-avatar"', True)
    # 声音分布独立占比条
    assert_contains("default_with_topics/含声音分布条", by_label["default_with_topics"][1], '<div class="voice-fill"', True)
    # 话题编号
    assert_contains("default_with_topics/含话题编号", by_label["default_with_topics"][1], '<span class="topic-index"', True)
    # 活跃脉搏 SVG 面积图
    assert_contains("default_with_topics/含活跃脉搏图", by_label["default_with_topics"][1], '<path class="activity-line"', True)
    # 标题刊头装饰
    assert_contains("default_with_topics/含标题装饰线", by_label["default_with_topics"][1], '<div class="title-rule"', True)

    # 多主题：dark 目录生效（html 不报错且产出图片）
    assert by_label["dark_with_topics"][0], "dark 主题未产出图片"
    print("  [OK] dark 主题切换: 产出图片非空")

    print("\n=== 全部通过 ===")
    print(f"输出目录: {OUT_DIR}")
    for label, img, _ in results:
        print(f"  {label}.jpg ({len(img) if img else 0} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
