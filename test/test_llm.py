import asyncio
import json
from loguru import logger
import traceback
from src.application.graph.summary_graph import SummaryGraph
from src.infrastructure.persistence.message_repository_impl import MySQLMessageRepository


async def test():
    # 1. 初始化 (模拟应用服务层的初始化)
    repo = MySQLMessageRepository()
    graph = SummaryGraph(
        message_repository=repo,
        llm_cache=None,
        memory_manager=None
    )

    print("🚀 正在请求完整数据流水线...")

    try:
        # 2. 执行 Graph 调用
        state = await graph.invoke(group_id=1017750994, hours=24)

        # 3. 模拟 GroupSummaryApplicationService 的返回结构
        meta = state.get("metadata", {})
        result_dict = {
            "summary_text": state.get("summary", ""),
            "topics": state.get("topics", []),
            "analysis": meta.get("analysis_result"),  # 这是一个对象
            "metadata": meta,
        }

        # --- 开始展示 ---

        # A. 展示 topics (用于渲染卡片流)
        print("\n" + " 📅 结构化话题 (topics) ".center(60, "="))
        for i, topic in enumerate(result_dict["topics"], 1):
            # 注意：这里的 topic 已经是 generate_summary 里 model_dump 过的字典了
            print(f"{i}. 【{topic.get('topic')}】")
            print(f"   👥 参与者: {', '.join(map(str, topic.get('contributors', [])))}")
            print(f"   📝 内容: {topic.get('detail')}\n")

        # B. 展示 analysis (用于渲染顶部仪表盘)
        print("\n" + " 📈 核心统计 (analysis) ".center(60, "="))
        analysis = result_dict["analysis"]
        if analysis:
            stats = analysis.statistics
            usage = analysis.token_usage
            print(f"📊 基础数据:")
            print(f"  - 消息总数: {stats.message_count}")
            print(f"  - 活跃人数: {stats.participant_count}")
            print(f"  - 时间跨度: {stats.time_span}")
            print(f"  - 讨论时长: {stats.duration}")

            # 这里是画条形图的关键数据
            print(f"\n⏰ 24h分布 (用于渲染条形图):")
            print(stats.activity.hourly_distribution)

            print(f"\n💰 费用分析:")
            print(f"  - Token消耗: {usage.total_tokens}")
            print(f"  - 预估成本: ${usage.estimated_cost:.4f}")

        # C. 展示 metadata (用于排查其余辅助信息)
        print("\n" + " 📦 辅助元数据 (metadata) ".center(60, "="))
        # 过滤掉已经展示过的 analysis_result 以免刷屏
        display_meta = {k: v for k, v in result_dict["metadata"].items() if k != "analysis_result"}
        print(json.dumps(display_meta, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ 运行失败: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())