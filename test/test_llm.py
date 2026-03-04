import asyncio
import json
from src.application.graph.summary_graph import SummaryGraph
from src.infrastructure.persistence.message_repository_impl import MySQLMessageRepository


async def test():
    # 1. 初始化
    repo = MySQLMessageRepository()
    graph = SummaryGraph(
        message_repository=repo,
        llm_cache=None,
        memory_manager=None
    )

    print("🚀 正在从 MySQL 获取数据并请求 LLM...")

    # 2. 调用并获取完整 State
    try:
        state = await graph.invoke(group_id=1017750994, hours=24)

        # 3. 输出排版后的摘要
        print("\n" + "=" * 30 + " 摘要内容 " + "=" * 30)
        print(state["summary"])

        # 4. 输出元数据 (Metadata)
        print("\n" + "=" * 30 + " 元数据 (Meta) " + "=" * 30)
        meta = state["metadata"]

        # 打印关键统计信息
        if "analysis_result" in meta:
            analysis = meta["analysis_result"]
            stats = analysis.statistics
            usage = analysis.token_usage
            print(f"📊 统计概览:")
            print(f"  - 消息总数: {stats.message_count}")
            print(f"  - 参与人数: {stats.participant_count}")
            print(f"  - Token 消耗: {usage.total_tokens}")
            print(f"  - 预估成本: ${usage.estimated_cost:.4f}")
            print(f"  - 时间跨度: {stats.time_span}")

        print(f"\n🏷️  核心概念 (Concepts): {meta.get('concepts', [])}")

        print(f"\n📅 提取事件 (Events):")
        for event in meta.get("events", []):
            print(f"  - [{event['event']}] {event['summary'][:50]}...")

    except Exception as e:
        print(f"❌ 运行失败: {e}")


if __name__ == "__main__":
    asyncio.run(test())