from __future__ import annotations

import json
import os
import sys
import time
from typing import Tuple

from src.application.services.summary_report_app_service import (
    SummaryReportApplicationService,
)

# Windows 控制台默认 GBK，打印 emoji 会崩；强制 utf-8 + 替换不可编码字符
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

GROUP_ID = 1017750994  # TODO: 替换为你的群号
HOURS = 24  # TODO: 替换为你的窗口小时数
OUTPUT_DIR = "."  # 当前目录
SLEEP_SECONDS = 5  # TODO: 如需等待可改


def _ensure_output_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def _save_image(image_bytes: bytes, output_path: str) -> None:
    with open(output_path, "wb") as f:
        f.write(image_bytes)


def _format_cost(value: float) -> str:
    return f"${value:.6f}" if value else "$0.000000"


def _extract_token_usage(summary_result) -> Tuple[int, float]:
    usage = getattr(summary_result, "analysis", None)
    if not usage:
        return 0, 0.0
    token_usage = getattr(usage, "token_usage", None)
    if not token_usage:
        return 0, 0.0
    total_tokens = int(getattr(token_usage, "total_tokens", 0) or 0)
    estimated_cost = float(getattr(token_usage, "estimated_cost", 0.0) or 0.0)
    return total_tokens, estimated_cost


def _save_summary_data(summary_result, output_dir: str, label: str, group_id: int, hours: int) -> str:
    """把未渲染的 SummaryResult 落盘成 JSON，便于排查摘要是否为空。"""
    try:
        data = summary_result.model_dump(mode="json")
    except TypeError:
        data = summary_result.model_dump()
    except Exception as e:
        data = {"error": f"{type(e).__name__}: {e}", "repr": repr(summary_result)}

    output_path = os.path.join(output_dir, f"summary_{label}_{group_id}_{hours}h.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    return output_path


def _print_summary_diag(summary_result, label: str) -> None:
    stats = getattr(getattr(summary_result, "analysis", None), "statistics", None)
    msg_count = getattr(stats, "message_count", 0) if stats else 0
    participant_count = getattr(stats, "participant_count", 0) if stats else 0
    time_span = getattr(stats, "time_span", "") if stats else ""
    summary_text = getattr(summary_result, "summary_text", "") or ""
    topics = getattr(summary_result, "topics", []) or []
    nickname_map = getattr(summary_result, "nickname_map", {}) or {}
    total_tokens, estimated_cost = _extract_token_usage(summary_result)

    print(f"[{label}] === 未渲染数据诊断 ===")
    print(f"[{label}] message_count={msg_count}, participant_count={participant_count}, time_span={time_span!r}")
    print(f"[{label}] summary_text 长度={len(summary_text)}")
    if summary_text:
        print(f"[{label}] summary_text 预览: {summary_text[:200].replace(chr(10), ' ')}")
    print(f"[{label}] topics 数量={len(topics)}")
    for i, t in enumerate(topics):
        topic_title = getattr(t, "topic", "") or ""
        detail = (getattr(t, "detail", "") or "").replace("\n", " ")
        print(f"[{label}]   topic[{i}]: {topic_title} | {detail[:80]}")
    print(f"[{label}] nickname_map 数量={len(nickname_map)}")
    print(f"[{label}] tokens={total_tokens}, cost={_format_cost(estimated_cost)}")


async def run_single_async(
    group_id: int, hours: int, output_dir: str, label: str
) -> Tuple[int, float, float]:
    service = SummaryReportApplicationService()

    # 1. 先只生成摘要（未渲染），保存原始数据用于排查
    t0 = time.monotonic()
    summary_result = await service.summarize_group(group_id, hours)
    summary_secs = time.monotonic() - t0

    data_path = _save_summary_data(summary_result, output_dir, label, group_id, hours)
    _print_summary_diag(summary_result, label)
    print(f"[{label}] 摘要耗时={summary_secs:.2f}s, 未渲染数据已保存: {data_path}")

    # 2. 再渲染图片（失败不致命，摘要数据已留存）
    t1 = time.monotonic()
    try:
        image_bytes = await service._report_renderer.render_summary_image(
            summary_result=summary_result
        )
    except Exception as e:
        print(f"[{label}] 渲染异常: {type(e).__name__}: {e}")
        image_bytes = None
    render_secs = time.monotonic() - t1

    if image_bytes:
        output_path = os.path.join(output_dir, f"summary_{label}_{group_id}_{hours}h.png")
        _save_image(image_bytes, output_path)
        print(f"[{label}] 输出图片: {output_path} ({len(image_bytes)} bytes, 渲染耗时={render_secs:.2f}s)")
    else:
        print(f"[{label}] 未生成图片 (渲染耗时={render_secs:.2f}s)")

    total_tokens, estimated_cost = _extract_token_usage(summary_result)
    return total_tokens, estimated_cost, summary_secs


async def main() -> None:
    _ensure_output_dir(OUTPUT_DIR)

    print("=== 运行第一次摘要 ===")
    tokens1, cost1, secs1 = await run_single_async(
        GROUP_ID, HOURS, OUTPUT_DIR, "first"
    )

    if SLEEP_SECONDS > 0:
        print(f"等待 {SLEEP_SECONDS}s 后进行第二次摘要...")
        time.sleep(SLEEP_SECONDS)

    print("=== 运行第二次摘要 ===")
    tokens2, cost2, secs2 = await run_single_async(
        GROUP_ID, HOURS, OUTPUT_DIR, "second"
    )

    if tokens1 > 0:
        token_saved = tokens1 - tokens2
        token_saved_ratio = token_saved / tokens1
    else:
        token_saved = 0
        token_saved_ratio = 0

    if cost1 > 0:
        cost_saved = cost1 - cost2
        cost_saved_ratio = cost_saved / cost1
    else:
        cost_saved = 0
        cost_saved_ratio = 0

    print("=== 对比结果 ===")
    print(f"第一次 tokens={tokens1}, cost={_format_cost(cost1)}, 耗时={secs1:.2f}s")
    print(f"第二次 tokens={tokens2}, cost={_format_cost(cost2)}, 耗时={secs2:.2f}s")
    print(f"节省 tokens={token_saved} ({token_saved_ratio:.2%})")
    print(f"节省 cost={_format_cost(cost_saved)} ({cost_saved_ratio:.2%})")
    # 第二次耗时远小于第一次 -> 命中 L1 缓存（未调 LLM）
    print(f"耗时差: {secs1 - secs2:.2f}s (正值≈第二次走了缓存)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
