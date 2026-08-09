from __future__ import annotations

import os
import time
from typing import Tuple

from src.application.services.summary_report_app_service import (
    SummaryReportApplicationService,
)

GROUP_ID = 913914054  # TODO: 替换为你的群号
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


async def run_single_async(
    group_id: int, hours: int, output_dir: str, label: str
) -> Tuple[int, float]:
    service = SummaryReportApplicationService()
    summary_result, image_bytes = await service.summarize_and_render_image(
        group_id=group_id,
        hours=hours,
    )

    if not image_bytes:
        raise RuntimeError("未生成图片，请检查渲染环境")

    filename = f"summary_{label}_{group_id}_{hours}h.png"
    output_path = os.path.join(output_dir, filename)
    _save_image(image_bytes, output_path)

    total_tokens, estimated_cost = _extract_token_usage(summary_result)
    print(f"[{label}] 输出图片: {output_path}")
    print(f"[{label}] tokens={total_tokens}, cost={_format_cost(estimated_cost)}")

    return total_tokens, estimated_cost


async def main() -> None:
    _ensure_output_dir(OUTPUT_DIR)

    print("=== 运行第一次摘要 ===")
    tokens1, cost1 = await run_single_async(
        GROUP_ID, HOURS, OUTPUT_DIR, "first"
    )

    if SLEEP_SECONDS > 0:
        print(f"等待 {SLEEP_SECONDS}s 后进行第二次摘要...")
        time.sleep(SLEEP_SECONDS)

    print("=== 运行第二次摘要 ===")
    tokens2, cost2 = await run_single_async(
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
    print(f"第一次 tokens={tokens1}, cost={_format_cost(cost1)}")
    print(f"第二次 tokens={tokens2}, cost={_format_cost(cost2)}")
    print(f"节省 tokens={token_saved} ({token_saved_ratio:.2%})")
    print(f"节省 cost={_format_cost(cost_saved)} ({cost_saved_ratio:.2%})")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
